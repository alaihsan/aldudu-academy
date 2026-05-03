import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from io import BytesIO
from typing import List, Optional

from flask import current_app
from werkzeug.utils import secure_filename

from app.extensions import db
from app.helpers import sanitize_rich_text
from app.models import Option, Question, QuestionType


DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass
class ParsedQuestion:
    text_parts: List[str] = field(default_factory=list)
    question_type: Optional[QuestionType] = None
    options: List[str] = field(default_factory=list)
    correct_keys: List[str] = field(default_factory=list)
    image_rel_id: Optional[str] = None

    @property
    def text(self) -> str:
        return "\n".join(part for part in self.text_parts if part).strip()


def create_sample_docx_bytes() -> bytes:
    paragraphs = [
        "1. Ibukota Indonesia adalah ...",
        "A. Jakarta",
        "B. Bandung",
        "C. Surabaya",
        "D. Medan",
        "Kunci: A",
        "",
        "2. Pilih format gambar yang valid.",
        "[checkbox]",
        "A. JPG",
        "B. PNG",
        "C. DOCX",
        "D. HEIC",
        "Kunci: A, B, D",
        "",
        "3. Pilih tingkat kepuasan.",
        "[skala likert]",
        "",
        "4. Jodohkan pasangan berikut.",
        "[menjodohkan]",
        "HTTP = Web",
        "SMTP = Email",
        "",
        "5. Jelaskan alasan jawabanmu.",
        "[jawaban singkat]",
    ]
    body = "".join(
        f'<w:p><w:r><w:t xml:space="preserve">{_xml_escape(paragraph)}</w:t></w:r></w:p>'
        for paragraph in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", content_types)
        docx.writestr("_rels/.rels", root_rels)
        docx.writestr("word/document.xml", document_xml)
        docx.writestr("word/_rels/document.xml.rels", document_rels)
    return stream.getvalue()


def import_questions_from_docx(file_storage, quiz) -> dict:
    with zipfile.ZipFile(file_storage.stream) as docx:
        rels = _read_relationships(docx)
        blocks = _read_document_blocks(docx)
        parsed_questions, warnings = _parse_question_blocks(blocks)
        if not parsed_questions:
            return {"success": False, "message": "Tidak ada soal yang terbaca dari file Word."}

        next_order = (max((question.order for question in quiz.questions), default=0) + 1)
        created = []
        for parsed in parsed_questions:
            question_type = _resolve_question_type(parsed)
            question = Question(
                quiz_id=quiz.id,
                question_text=sanitize_rich_text(parsed.text),
                question_type=question_type,
                order=next_order,
                points=0 if question_type == QuestionType.LIKERT_SCALE else quiz.default_points,
                is_required=quiz.required_by_default,
            )
            next_order += 1
            db.session.add(question)
            db.session.flush()

            if parsed.image_rel_id:
                filename = _save_question_image(docx, rels, parsed.image_rel_id, question.id)
                if filename:
                    question.image = filename
                else:
                    warnings.append(f"Gambar untuk soal {len(created) + 1} tidak bisa disimpan.")

            _add_options(question, parsed)
            created.append(question)

        db.session.commit()

    return {"success": True, "imported_count": len(created), "warnings": warnings}


def _add_options(question: Question, parsed: ParsedQuestion):
    if question.question_type == QuestionType.TRUE_FALSE:
        labels = ["Benar", "Salah"]
    elif question.question_type == QuestionType.LIKERT_SCALE:
        labels = ["Sangat tidak setuju", "Tidak setuju", "Netral", "Setuju", "Sangat setuju"]
    else:
        labels = parsed.options

    correct_indexes = _correct_indexes(parsed.correct_keys)
    for order, option_text in enumerate(labels, start=1):
        question.options.append(
            Option(
                option_text=sanitize_rich_text(option_text, max_len=500),
                order=order,
                is_correct=(order - 1) in correct_indexes or str(order) in parsed.correct_keys,
            )
        )


def _correct_indexes(keys: List[str]) -> set:
    result = set()
    for key in keys:
        cleaned = key.strip().upper()
        if re.fullmatch(r"[A-Z]", cleaned):
            result.add(ord(cleaned) - ord("A"))
    return result


def _read_relationships(docx: zipfile.ZipFile) -> dict:
    try:
        root = ET.fromstring(docx.read("word/_rels/document.xml.rels"))
    except KeyError:
        return {}
    rels = {}
    for rel in root.findall("rel:Relationship", DOCX_NS):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if rel_id and target:
            rels[rel_id] = target if target.startswith("word/") else f"word/{target}"
    return rels


def _read_document_blocks(docx: zipfile.ZipFile) -> list:
    root = ET.fromstring(docx.read("word/document.xml"))
    blocks = []
    for paragraph in root.findall(".//w:body/w:p", DOCX_NS):
        texts = [node.text or "" for node in paragraph.findall(".//w:t", DOCX_NS)]
        text = "".join(texts).strip()
        image_ids = [
            blip.attrib.get(f"{{{DOCX_NS['r']}}}embed")
            for blip in paragraph.findall(".//a:blip", DOCX_NS)
        ]
        if text:
            blocks.append({"type": "text", "text": text})
        for rel_id in image_ids:
            if rel_id:
                blocks.append({"type": "image", "rel_id": rel_id})
    return blocks


def _parse_question_blocks(blocks: list) -> tuple:
    questions = []
    warnings = []
    current = None

    for block in blocks:
        if block["type"] == "image":
            if current and not current.image_rel_id:
                current.image_rel_id = block["rel_id"]
            elif current:
                warnings.append(f"Lebih dari satu gambar ditemukan pada soal {len(questions) + 1}; hanya gambar pertama yang digunakan.")
            continue

        raw_text = block["text"].strip()
        tag_type = _detect_type_tag(raw_text)
        clean_text = _remove_type_tag(raw_text).strip()
        question_match = re.match(r"^\s*(?:soal\s*)?\d+[\.)]\s*(.+)$", clean_text, re.I)
        option_match = re.match(r"^\s*([A-Za-z])[\.)]\s+(.+)$", clean_text)
        bullet_match = re.match(r"^\s*[•·◦▪▫\-]\s+(.+)$", clean_text)
        key_match = re.match(r"^\s*(?:kunci|jawaban|answer)\s*[:=]\s*(.+)$", clean_text, re.I)

        if question_match:
            if current and current.text:
                questions.append(current)
            current = ParsedQuestion(text_parts=[question_match.group(1).strip()])
            if tag_type:
                current.question_type = tag_type
            continue

        if current is None:
            current = ParsedQuestion()

        if tag_type:
            current.question_type = tag_type
            if not clean_text:
                continue

        if key_match:
            current.correct_keys = [item.strip() for item in re.split(r"[,;/]", key_match.group(1)) if item.strip()]
        elif current.question_type == QuestionType.MATCHING and _looks_like_matching_pair(clean_text):
            current.options.append(clean_text)
        elif option_match and current.text:
            current.options.append(option_match.group(2).strip())
        elif bullet_match and current.text:
            current.options.append(bullet_match.group(1).strip())
        elif clean_text:
            current.text_parts.append(clean_text)

    if current and current.text:
        questions.append(current)
    return questions, warnings


def _detect_type_tag(text: str) -> Optional[QuestionType]:
    lowered = text.lower()
    if "[checkbox]" in lowered or "[kotak centang]" in lowered:
        return QuestionType.CHECKBOX
    if "[dropdown]" in lowered:
        return QuestionType.DROPDOWN
    if "[benar/salah]" in lowered or "[true/false]" in lowered:
        return QuestionType.TRUE_FALSE
    if "[jawaban singkat]" in lowered or "[jawaban pendek]" in lowered or "[esai]" in lowered:
        return QuestionType.LONG_TEXT
    if "[menjodohkan]" in lowered or "[matching]" in lowered:
        return QuestionType.MATCHING
    if "[skala likert]" in lowered or "[likert]" in lowered:
        return QuestionType.LIKERT_SCALE
    return None


def _remove_type_tag(text: str) -> str:
    return re.sub(
        r"\[(checkbox|kotak centang|dropdown|benar/salah|true/false|jawaban singkat|jawaban pendek|esai|menjodohkan|matching|skala likert|likert)\]",
        "",
        text,
        flags=re.IGNORECASE,
    )


def _looks_like_matching_pair(text: str) -> bool:
    return any(separator in text for separator in ("::", "=", "=>", "->", "|"))


def _resolve_question_type(question: ParsedQuestion) -> QuestionType:
    if question.question_type:
        return question.question_type
    if len(question.options) == 2 and {item.strip().lower() for item in question.options} == {"benar", "salah"}:
        return QuestionType.TRUE_FALSE
    return QuestionType.MULTIPLE_CHOICE if question.options else QuestionType.LONG_TEXT


def _save_question_image(docx: zipfile.ZipFile, rels: dict, rel_id: str, question_id: int) -> Optional[str]:
    path = rels.get(rel_id)
    if not path:
        return None
    try:
        image_bytes = docx.read(path)
    except KeyError:
        return None
    ext = os.path.splitext(path)[1].lower() or ".png"
    filename = secure_filename(f"q{question_id}_docx_{int(time.time() * 1000)}{ext}")
    with open(os.path.join(current_app.config["UPLOAD_FOLDER"], filename), "wb") as image_file:
        image_file.write(image_bytes)
    return filename


def _xml_escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
