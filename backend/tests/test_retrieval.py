from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.retriever import HybridRetriever

# Shared retriever instance — initialised once per test session
@pytest.fixture(scope="session")
def retriever() -> HybridRetriever:
    return HybridRetriever()


# (query, expected_article_number)
CASES = [
    # Art.184 item-4: "عدم احترام الوقوف المفروض بعلامة قف أو بضوء التشوير الأحمر"
    ("ne pas respecter un feu rouge", 184),
    # Art.185: speed violations 20-30 km/h over limit — Classe-2 offences
    ("limite de vitesse en agglomération", 185),
    # Art.63: registration certificate must be on board the vehicle at all times
    ("permis de conduire documents controle", 63),
    # Art.24: license cancelled when last point is lost during probationary period
    ("retrait de points permis de conduire", 24),
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
