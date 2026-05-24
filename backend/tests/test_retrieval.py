from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env so GROQ_API_KEY is available when pytest is not invoked via the shell
_env_file = ROOT / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

from app.rag.query_translator import QueryTranslator
from app.rag.retriever import HybridRetriever


@pytest.fixture(scope="session")
def retriever() -> HybridRetriever:
    key = os.getenv("GROQ_API_KEY", "")
    translator = QueryTranslator(api_key=key) if key else None
    # use_reranker=False preserves Phase 2 rank assertions (reranker changes order)
    return HybridRetriever(translator=translator, use_reranker=False)


# (query, expected_article_number)
CASES = [
    # Art.184 item-4: "عدم احترام الوقوف المفروض بعلامة قف أو بضوء التشوير الأحمر"
    ("ne pas respecter un feu rouge", 184),
    # Art.175: excessive speed (≥50 km/h over limit) — Classe-1 offences in urban areas
    ("limite de vitesse en agglomération", 175),
    # Art.63: registration certificate (شهادة التسجيل) must be on board the vehicle
    ("justificatif immatriculation vehicule route", 63),
    # Art.24: license cancelled when all points are lost — directly about total point loss
    ("perte totale points conduit", 24),
    # Art.184 covers illegal stopping / parking violations with 700-1400 DH fines
    ("stationnement gênant amende", 184),
]


@pytest.mark.parametrize("query,expected_article", CASES)
def test_expected_article_in_top5(
    retriever: HybridRetriever, query: str, expected_article: int
) -> None:
    results = retriever.search(query, top_k=5)
    found_numbers = [c.article_number for c in results]
    assert expected_article in found_numbers, (
        f"Query '{query}': expected article {expected_article} in top-5, "
        f"got {found_numbers}"
    )


def test_at_least_4_of_5_pass(retriever: HybridRetriever) -> None:
    """Exit-gate check: ≥ 4/5 queries return their expected article in top-5."""
    hits = 0
    for query, expected in CASES:
        results = retriever.search(query, top_k=5)
        if expected in [c.article_number for c in results]:
            hits += 1
    assert hits >= 4, f"Only {hits}/5 queries hit their expected article (need ≥ 4)"
