from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("CIN", re.compile(r"\b[A-Z]{1,2}\d{4,7}\b")),
    ("PHONE", re.compile(r"\b0[5-7]\d{8}\b")),
    ("PLATE", re.compile(r"\b\d{1,5}\s*[A-Z؀-ۿ]\s*\d{1,2}\b")),
]


def redact(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    result = text
    for label, pattern in _PATTERNS:
        if pattern.search(result):
            found.append(label)
            result = pattern.sub(f"[{label}_REDACTED]", result)
    return result, found
