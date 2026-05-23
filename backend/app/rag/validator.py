from __future__ import annotations

import re
from dataclasses import dataclass, field

_CITATION_RE = re.compile(r"\[?Article\s+(\d+)\]?", re.IGNORECASE)


@dataclass
class ValidationResult:
    valid: bool
    cited: list[int]
    hallucinated: list[int]


def validate_citations(
    answer_text: str,
    allowed_article_numbers: set[int],
) -> ValidationResult:
    cited = [int(m) for m in _CITATION_RE.findall(answer_text)]
    hallucinated = [n for n in cited if n not in allowed_article_numbers]
    return ValidationResult(
        valid=len(hallucinated) == 0,
        cited=cited,
        hallucinated=hallucinated,
    )
