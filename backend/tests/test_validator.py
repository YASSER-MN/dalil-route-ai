from __future__ import annotations

from backend.app.rag.validator import validate_citations


def test_hallucinated_article_flagged() -> None:
    answer = "Voir [Article 99999] et [Article 5] pour plus de détails."
    result = validate_citations(answer, allowed_article_numbers={5, 7, 10})

    assert 99999 in result.hallucinated
    assert result.valid is False


def test_valid_citations_pass() -> None:
    answer = "Conformément à [Article 7] et [Article 10], l'infraction est sanctionnée."
    result = validate_citations(answer, allowed_article_numbers={5, 7, 10})

    assert result.hallucinated == []
    assert result.valid is True


def test_no_citations() -> None:
    answer = "Cette réponse ne contient aucune référence d'article."
    result = validate_citations(answer, allowed_article_numbers={5, 7, 10})

    assert result.cited == []
    assert result.valid is True


def test_multiple_hallucinations() -> None:
    answer = "Selon Article 1, Article 2 et [Article 7]."
    result = validate_citations(answer, allowed_article_numbers={7})

    assert 1 in result.hallucinated
    assert 2 in result.hallucinated
    assert 7 not in result.hallucinated
    assert result.valid is False
