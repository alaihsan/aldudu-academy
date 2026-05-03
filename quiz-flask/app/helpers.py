import html
import re
from datetime import datetime, timedelta, timezone


def now_jakarta():
    return datetime.now(timezone(timedelta(hours=7)))


def sanitize_text(value, max_len=200):
    if value is None:
        return ""
    text = re.sub(r"<[^>]*?>", "", str(value).strip())
    text = html.escape(text)
    return text[:max_len]


def sanitize_rich_text(value, max_len=5000):
    if value is None:
        return ""
    text = html.unescape(str(value).strip())
    allowed = {"b", "i", "u", "strong", "em", "ol", "ul", "li", "br", "p", "div"}

    def replace_tag(match):
        raw = match.group(1)
        tag = re.match(r"\s*(/)?\s*(\w+)", raw)
        if tag and tag.group(2).lower() in allowed:
            name = tag.group(2).lower()
            if name == "br":
                return "<br>"
            return f"</{name}>" if tag.group(1) else f"<{name}>"
        return ""

    text = re.sub(r"<([^>]*?)>", replace_tag, text)
    return text[:max_len]


def plain_text(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<\s*br\s*/?\s*>", "\n", text, flags=re.I)
    text = re.sub(r"</\s*(p|div|li)\s*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]*?>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def matching_pair(value):
    text = plain_text(value)
    for separator in ("::", "=>", "->", "=", "|"):
        if separator in text:
            left, right = text.split(separator, 1)
            return left.strip(), right.strip()
    return text, ""
