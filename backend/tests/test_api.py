from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.rag.retriever import Chunk
from backend.app.rag.generator import Answer

# ── Shared fake pipeline responses ───────────────────────────────────────────

_FAKE_CHUNKS = [
    Chunk(id="184", text="Article 184: Le non-respect d'un feu rouge est une infraction.", score=0.9, article_number=184),
    Chunk(id="185", text="Article 185: La limite de vitesse en agglomération est 50 km/h.", score=0.8, article_number=185),
]

_FAKE_ANSWER = Answer(
    text=(
        "Selon l'Article 185, la limite de vitesse en agglomération est 50 km/h. "
        "**Avertissement**: Cette information est fournie à titre indicatif uniquement."
    ),
    model="llama-3.3-70b-versatile",
    prompt_version="v1",
    evidence_ids=["184", "185"],
)


def _make_mock_retriever() -> MagicMock:
    m = MagicMock()
    m.search.return_value = _FAKE_CHUNKS
    return m


def _make_mock_generator() -> MagicMock:
    m = MagicMock()
    m.generate.return_value = _FAKE_ANSWER
    return m


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    """Clear in-memory rate limit counts before each test."""
    from backend.app.security.rate_limit import limiter
    limiter._storage.reset()


# ── Tests — non-rate-limit first ─────────────────────────────────────────────

@patch("backend.app.api.ask.get_retriever", return_value=_make_mock_retriever())
@patch("backend.app.api.ask.get_generator", return_value=_make_mock_generator())
def test_ask_legal_question_returns_valid_schema(mock_gen: MagicMock, mock_ret: MagicMock) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post("/ask", json={"question": "Quelle est la limite de vitesse en agglomération?"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "answer" in data
    assert "sources" in data
    assert "trace_id" in data
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0


@patch("backend.app.api.ask.get_retriever", return_value=_make_mock_retriever())
@patch("backend.app.api.ask.get_generator", return_value=_make_mock_generator())
def test_ask_redacts_cin(mock_gen: MagicMock, mock_ret: MagicMock) -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.post("/ask", json={"question": "My CIN is AB1234567, what is the speed limit?"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "CIN" in data["pii_redacted"]


def test_admin_traces_requires_key() -> None:
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/admin/traces")
    assert resp.status_code == 401


def test_admin_traces_with_correct_key() -> None:
    from backend.app.config import settings
    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/admin/traces", headers={"x-admin-key": settings.admin_key})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


# ── Rate limit test last — exhausts the quota ─────────────────────────────────

@patch("backend.app.api.ask.get_retriever", return_value=_make_mock_retriever())
@patch("backend.app.api.ask.get_generator", return_value=_make_mock_generator())
def test_ask_rate_limit_triggers(mock_gen: MagicMock, mock_ret: MagicMock) -> None:
    triggered = False
    with TestClient(app, raise_server_exceptions=False) as client:
        for _ in range(31):
            resp = client.post("/ask", json={"question": "Quelle est la limite de vitesse?"})
            if resp.status_code == 429:
                triggered = True
                break
    assert triggered, "Expected a 429 after 30 requests but never received one"
