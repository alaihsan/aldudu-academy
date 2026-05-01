import os
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Optional

from werkzeug.utils import secure_filename

from app.helpers import sanitize_rich_text
from app.models import Option, Question, QuestionType, db


DOCX_NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
}


@dataclass
class ParsedQuestion:
    text_parts: List[str] = field(default_factory=list)
    question_type: Optional[QuestionType] = None
    options: List[str] = field(default_factory=list)
    image_rel_id: Optional[str] = None

    @property
    def text(self) -> str:
        return '\n'.join(part for part in self.text_parts if part).strip()


def create_sample_docx_bytes() -> bytes:
    """Create a small DOCX example without third-party dependencies."""
    from io import BytesIO

    paragraphs = [
        '1. Perhatikan gambar berikut!',
        '[gambar opsional ditempatkan di bawah teks soal]',
        'A. Router',
        'B. Switch',
        'C. Server',
        'D. Modem',
        '',
        '2. Pilih perangkat jaringan berikut.',
        '[checkbox]',
        'A. Router',
        'B. Switch',
        'C. Monitor',
        'D. Keyboard',
        '',
        '3. Pilih protokol yang digunakan untuk web.',
        '[dropdown]',
        'A. HTTP',
        'B. FTP',
        'C. SMTP',
        '',
        '4. Internet adalah jaringan global.',
        '[benar/salah]',
        '',
        '5. Jelaskan fungsi router.',
        '[jawaban singkat]',
        '',
        '6. Jodohkan istilah berikut.',
        '[menjodohkan]',
        'CPU = Otak komputer',
        'RAM = Memori sementara',
        'Harddisk = Penyimpanan data',
    ]
    body = ''.join(
        '<w:p><w:r><w:t xml:space="preserve">{}</w:t></w:r></w:p>'.format(_xml_escape(p))
        for p in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:body>{body}<w:sectPr/></w:body></w:document>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>'
    )
    document_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
    )

    stream = BytesIO()
    with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as docx:
        docx.writestr('[Content_Types].xml', content_types)
        docx.writestr('_rels/.rels', root_rels)
        docx.writestr('word/document.xml', document_xml)
        docx.writestr('word/_rels/document.xml.rels', document_rels)
    return stream.getvalue()


def import_questions_from_docx(file_storage, quiz) -> dict:
    with zipfile.ZipFile(file_storage.stream) as docx:
        rels = _read_relationships(docx)
        blocks = _read_document_blocks(docx)
        parsed_questions, warnings = _parse_question_blocks(blocks)
        if not parsed_questions:
            return {'success': False, 'message': 'Tidak ada soal yang terbaca dari file Word.'}

        upload_folder = os.path.join(os.getcwd(), 'instance', 'uploads', str(quiz.course_id))
        os.makedirs(upload_folder, exist_ok=True)

        last_q = quiz.questions.order_by(Question.order.desc()).first()
        next_order = (last_q.order + 1) if last_q else 1
        created = []

        for parsed in parsed_questions:
            question_type = _resolve_question_type(parsed)
            question = Question(
                quiz_id=quiz.id,
                question_text=sanitize_rich_text(parsed.text),
                question_type=question_type,
                order=next_order,
                points=quiz.default_points,
                is_required=quiz.required_by_default
            )
            next_order += 1
            db.session.add(question)
            db.session.flush()

            if parsed.image_rel_id:
                filename = _save_question_image(docx, rels, parsed.image_rel_id, upload_folder, question.id)
                if filename:
                    question.image = filename
                else:
                    warnings.append(f'Gambar untuk soal {len(created) + 1} tidak bisa disimpan.')

            if question_type == QuestionType.TRUE_FALSE:
                question.options.append(Option(option_text='Benar', order=1))
                question.options.append(Option(option_text='Salah', order=2))
            elif question_type in (QuestionType.MULTIPLE_CHOICE, QuestionType.CHECKBOX, QuestionType.DROPDOWN, QuestionType.MATCHING):
                for order, option_text in enumerate(parsed.options, start=1):
                    question.options.append(Option(option_text=sanitize_rich_text(option_text, max_len=500), order=order))

            created.append(question)

        db.session.commit()

    return {
        'success': True,
        'imported_count': len(created),
        'warnings': warnings,
    }


def _read_relationships(docx: zipfile.ZipFile) -> dict:
    try:
        root = ET.fromstring(docx.read('word/_rels/document.xml.rels'))
    except KeyError:
        return {}

    rels = {}
    for rel in root.findall('rel:Relationship', DOCX_NS):
        rel_id = rel.attrib.get('Id')
        target = rel.attrib.get('Target', '')
        if rel_id and target:
            rels[rel_id] = target if target.startswith('word/') else f'word/{target}'
    return rels


def _read_document_blocks(docx: zipfile.ZipFile) -> list:
    root = ET.fromstring(docx.read('word/document.xml'))
    numbering_formats = _read_numbering_formats(docx)
    blocks = []
    for paragraph in root.findall('.//w:body/w:p', DOCX_NS):
        texts = [node.text or '' for node in paragraph.findall('.//w:t', DOCX_NS)]
        text = ''.join(texts).strip()
        list_level, number_format = _paragraph_numbering(paragraph, numbering_formats)
        image_ids = [
            blip.attrib.get(f'{{{DOCX_NS["r"]}}}embed')
            for blip in paragraph.findall('.//a:blip', DOCX_NS)
        ]
        if text:
            blocks.append({
                'type': 'text',
                'text': text,
                'list_level': list_level,
                'number_format': number_format,
            })
        for rel_id in image_ids:
            if rel_id:
                blocks.append({'type': 'image', 'rel_id': rel_id})
    return blocks


def _read_numbering_formats(docx: zipfile.ZipFile) -> dict:
    try:
        root = ET.fromstring(docx.read('word/numbering.xml'))
    except KeyError:
        return {}

    abstract_formats = {}
    for abstract_num in root.findall('w:abstractNum', DOCX_NS):
        abstract_id = abstract_num.attrib.get(f'{{{DOCX_NS["w"]}}}abstractNumId')
        if abstract_id is None:
            continue
        abstract_formats[abstract_id] = {}
        for level in abstract_num.findall('w:lvl', DOCX_NS):
            ilvl = level.attrib.get(f'{{{DOCX_NS["w"]}}}ilvl')
            num_fmt = level.find('w:numFmt', DOCX_NS)
            if ilvl is not None and num_fmt is not None:
                abstract_formats[abstract_id][int(ilvl)] = num_fmt.attrib.get(f'{{{DOCX_NS["w"]}}}val')

    formats = {}
    for num in root.findall('w:num', DOCX_NS):
        num_id = num.attrib.get(f'{{{DOCX_NS["w"]}}}numId')
        abstract_ref = num.find('w:abstractNumId', DOCX_NS)
        if num_id is None or abstract_ref is None:
            continue
        abstract_id = abstract_ref.attrib.get(f'{{{DOCX_NS["w"]}}}val')
        formats[num_id] = abstract_formats.get(abstract_id, {})
    return formats


def _paragraph_numbering(paragraph, numbering_formats: dict) -> tuple:
    num_pr = paragraph.find('w:pPr/w:numPr', DOCX_NS)
    if num_pr is None:
        return None, None

    ilvl_el = num_pr.find('w:ilvl', DOCX_NS)
    num_id_el = num_pr.find('w:numId', DOCX_NS)
    level = int(ilvl_el.attrib.get(f'{{{DOCX_NS["w"]}}}val', 0)) if ilvl_el is not None else 0
    num_id = num_id_el.attrib.get(f'{{{DOCX_NS["w"]}}}val') if num_id_el is not None else None
    return level, numbering_formats.get(num_id, {}).get(level)


def _parse_question_blocks(blocks: list) -> tuple:
    questions = []
    warnings = []
    current = None

    for block in blocks:
        if block['type'] == 'image':
            if current and not current.image_rel_id:
                current.image_rel_id = block['rel_id']
            elif current:
                warnings.append(f'Lebih dari satu gambar ditemukan pada soal {len(questions) + 1}; hanya gambar pertama yang digunakan.')
            continue

        raw_text = block['text'].strip()
        tag_type = _detect_type_tag(raw_text)
        clean_text = _remove_type_tag(raw_text).strip()
        list_level = block.get('list_level')
        number_format = block.get('number_format')
        is_auto_question = list_level == 0 and number_format in {'decimal', 'decimalZero', 'ordinal'}
        is_auto_option = (
            list_level is not None
            and not is_auto_question
            and (list_level > 0 or number_format in {'upperLetter', 'lowerLetter', 'bullet'})
        )
        question_match = re.match(r'^\s*\d+[\.)]\s*(.+)$', clean_text)
        option_match = re.match(r'^\s*(?:[A-Za-z]|\d+)[\.)]\s+(.+)$', clean_text)
        bullet_match = re.match(r'^\s*[•·◦▪▫\-]\s+(.+)$', clean_text)

        if question_match or is_auto_question:
            if current and current.text:
                questions.append(current)
            current = ParsedQuestion(text_parts=[(question_match.group(1) if question_match else clean_text).strip()])
            if tag_type:
                current.question_type = tag_type
            continue

        if current is None:
            current = ParsedQuestion()

        if tag_type:
            current.question_type = tag_type
            if not clean_text:
                continue

        if current.question_type == QuestionType.MATCHING and _looks_like_matching_pair(clean_text):
            current.options.append(clean_text)
        elif is_auto_option and current.text:
            current.options.append(clean_text)
        elif option_match and current.text:
            current.options.append(option_match.group(1).strip())
        elif bullet_match and current.text:
            current.options.append(bullet_match.group(1).strip())
        elif clean_text:
            current.text_parts.append(clean_text)

    if current and current.text:
        questions.append(current)

    return questions, warnings


def _detect_type_tag(text: str) -> Optional[QuestionType]:
    lowered = text.lower()
    if '[checkbox]' in lowered or '[kotak centang]' in lowered:
        return QuestionType.CHECKBOX
    if '[dropdown]' in lowered:
        return QuestionType.DROPDOWN
    if '[benar/salah]' in lowered or '[true/false]' in lowered:
        return QuestionType.TRUE_FALSE
    if '[jawaban singkat]' in lowered or '[jawaban pendek]' in lowered:
        return QuestionType.LONG_TEXT
    if '[menjodohkan]' in lowered or '[matching]' in lowered:
        return QuestionType.MATCHING
    return None


def _looks_like_matching_pair(text: str) -> bool:
    return any(separator in text for separator in ('::', '=', '=>', '->', '|'))


def _remove_type_tag(text: str) -> str:
    return re.sub(
        r'\[(checkbox|kotak centang|dropdown|benar/salah|true/false|jawaban singkat|jawaban pendek|menjodohkan|matching)\]',
        '',
        text,
        flags=re.IGNORECASE
    )


def _resolve_question_type(question: ParsedQuestion) -> QuestionType:
    if question.question_type:
        return question.question_type
    return QuestionType.MULTIPLE_CHOICE if question.options else QuestionType.LONG_TEXT


def _save_question_image(docx: zipfile.ZipFile, rels: dict, rel_id: str, upload_folder: str, question_id: int) -> Optional[str]:
    path = rels.get(rel_id)
    if not path:
        return None
    try:
        image_bytes = docx.read(path)
    except KeyError:
        return None

    ext = os.path.splitext(path)[1].lower() or '.png'
    filename = secure_filename(f'q_{question_id}_docx_{int(time.time() * 1000)}{ext}')
    with open(os.path.join(upload_folder, filename), 'wb') as image_file:
        image_file.write(image_bytes)
    return filename


def _xml_escape(value: str) -> str:
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )
