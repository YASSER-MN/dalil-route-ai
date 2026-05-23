from __future__ import annotations

import json
import re
from pathlib import Path

import fitz

PDF_PATH = Path("backend/data/raw/textBased_arabic_version_52_05.pdf")
OUTPUT_PATH = Path("backend/data/articles.json")
SOURCE = "Law 52-05"
MAX_BODY_CHARS = 3000

# Both ligature and non-ligature forms of "المادة" appear in this PDF
_MADDA = r"(?:المادة|املادة)"
# Article header: a line containing only "N المادة" (number before the word, RTL extraction artifact)
_HEADER = re.compile(r"(?:^|\n)\s*(\d+)\s+" + _MADDA + r"\s*\n", re.MULTILINE)
# Per-page artifacts: standalone page number then government header on next line
_PAGE_NUM = re.compile(r"(?m)^\d{1,3}\n")
_GOV_HEADER = re.compile(r"[^\n]*للحكومة[^\n]*\n")


def _extract_raw(pdf_path: Path) -> str:
    doc = fitz.open(str(pdf_path))
    return "\n".join(page.get_text() for page in doc)


def _clean(text: str) -> str:
    text = _PAGE_NUM.sub("", text)
    text = _GOV_HEADER.sub("", text)
    return text


def _parse_articles(text: str) -> list[dict]:
    headers = list(_HEADER.finditer(text))
    articles: list[dict] = []
    for i, m in enumerate(headers):
        number = int(m.group(1))
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[start:end]
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\n{3,}", "\n\n", body)
        body = body.strip()[:MAX_BODY_CHARS]
        if len(body) >= 50:
            articles.append({"number": number, "text": body, "source": SOURCE})
    return articles


def main() -> None:
    text = _extract_raw(PDF_PATH)
    text = _clean(text)
    articles = _parse_articles(text)
    OUTPUT_PATH.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Extracted {len(articles)} articles -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
