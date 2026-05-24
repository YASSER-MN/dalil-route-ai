from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.app.rag.query_translator import QueryTranslator


@pytest.fixture(scope="module")
def translator() -> QueryTranslator:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        pytest.skip("GROQ_API_KEY not set")
    return QueryTranslator(api_key=key)


def test_red_light_fine(translator: QueryTranslator) -> None:
    result = translator.to_arabic("Quelle est l'amende pour brûler un feu rouge ?")
    lower = result.lower()
    assert "غرامة" in result, f"Expected 'غرامة' in: {result}"
    assert "إشارة" in result or "ضوء" in result or "إشارة المرور" in result, (
        f"Expected traffic light term in: {result}"
    )


def test_recover_points(translator: QueryTranslator) -> None:
    result = translator.to_arabic("Comment récupérer des points ?")
    assert "نقط" in result or "نقاط" in result, f"Expected 'نقط' in: {result}"
    assert "استرجاع" in result or "استرداد" in result or "استعادة" in result, (
        f"Expected recovery term in: {result}"
    )


def test_mandatory_documents(translator: QueryTranslator) -> None:
    result = translator.to_arabic("Documents obligatoires pour conduire")
    assert "وثائق" in result or "وثيقة" in result or "مستندات" in result, (
        f"Expected documents term in: {result}"
    )
    assert "سياقة" in result or "قيادة" in result, (
        f"Expected driving term in: {result}"
    )
