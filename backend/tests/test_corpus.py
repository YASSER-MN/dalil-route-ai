from __future__ import annotations

import json
from pathlib import Path

ARTICLES_PATH = Path("backend/data/articles.json")


def _load() -> list[dict]:
    return json.loads(ARTICLES_PATH.read_text(encoding="utf-8"))


def test_file_exists_and_parses() -> None:
    assert ARTICLES_PATH.exists(), "articles.json not found"
    data = _load()
    assert isinstance(data, list)


def test_minimum_count() -> None:
    data = _load()
    assert len(data) >= 100, f"Expected ≥ 100 articles, got {len(data)}"


def test_schema_valid() -> None:
    data = _load()
    for art in data:
        assert isinstance(art["number"], int), f"'number' not int in {art}"
        assert isinstance(art["text"], str), f"'text' not str in {art}"
        assert len(art["text"]) >= 50, (
            f"article {art['number']} body too short: {len(art['text'])} chars"
        )


def test_traffic_keywords() -> None:
    # Arabic equivalents: سرعة = speed (vitesse), إشارة = signal/light (feu)
    data = _load()
    hits = [a for a in data if "سرعة" in a["text"] or "إشارة" in a["text"]]
    assert len(hits) >= 2, (
        f"Expected ≥ 2 articles mentioning speed/signals, got {len(hits)}"
    )
