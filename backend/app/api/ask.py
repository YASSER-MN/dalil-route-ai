import hashlib
import json
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import AnswerTrace
from app.db.session import get_db
from app.rag.generator import AnswerGenerator
from app.rag.query_translator import QueryTranslator
from app.rag.retriever import HybridRetriever
from app.rag.validator import validate_citations
from app.security.pii import redact
from app.security.rate_limit import limiter

router = APIRouter()

_translator: QueryTranslator | None = None
_retriever: HybridRetriever | None = None
_generator: AnswerGenerator | None = None


def get_translator() -> QueryTranslator | None:
    global _translator
    if _translator is None and settings.groq_api_key:
        _translator = QueryTranslator(api_key=settings.groq_api_key)
    return _translator


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(translator=get_translator())
    return _retriever


def get_generator() -> AnswerGenerator:
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator


# ── Scope filter ──────────────────────────────────────────────────────────────

_SCOPE_REDIRECT_TEXT = (
    "Bonjour. Je suis Dalil Route, assistant sur le Code de la Route marocain. "
    "Posez-moi une question concernant la circulation, les infractions, les documents requis, "
    "ou toute autre disposition légale.\n\n"
    "Exemples :\n"
    "- Quelle est la sanction pour brûler un feu rouge ?\n"
    "- Quels documents dois-je avoir dans ma voiture ?\n"
    "- Comment fonctionne le système de points ?"
)

# Exact phrases (after lowercasing and stripping trailing punctuation/spaces)
# that should trigger a scope redirect instead of retrieval.
_OUT_OF_SCOPE_PHRASES: frozenset[str] = frozenset({
    # French greetings
    "bonjour", "bonsoir", "salut", "bonne journée", "bonne soirée",
    # English greetings
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    # Arabic / transliterated greetings
    "salam", "salam alaikum", "السلام عليكم", "سلام", "مرحبا", "أهلا", "أهلاً",
    "ahlan", "ahlan wa sahlan", "wesh", "labas",
    # Acknowledgments
    "merci", "shukran", "thanks", "thank you",
    "ok", "okay", "oui", "non", "yes", "no", "si",
    "d'accord", "bien", "bien sûr",
    # Test inputs
    "test", "testing",
})


def _is_out_of_scope(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 10:
        return True
    normalized = stripped.lower().strip(".,!?¿¡ ")
    return normalized in _OUT_OF_SCOPE_PHRASES


# ── Confidence extraction from LLM output ────────────────────────────────────

_CONFIDENCE_MAP: dict[str, str] = {
    "élevée": "élevée",
    "elevée": "élevée",
    "moyenne": "moyenne",
    "faible": "faible",
}


def _extract_confidence(text: str) -> str:
    m = re.search(r"\*\*Confiance[^*]*\*\*[:\s]*(\S+)", text, re.IGNORECASE)
    if not m:
        return "moyenne"
    return _CONFIDENCE_MAP.get(m.group(1).lower(), "moyenne")


# ── Pydantic models ───────────────────────────────────────────────────────────

class QuestionIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class SourceOut(BaseModel):
    article_number: int
    text: str
    score: float


class AnswerOut(BaseModel):
    answer: str
    sources: list[SourceOut]
    valid: bool
    confidence: str
    trace_id: str
    pii_redacted: list[str]


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post("/ask", response_model=AnswerOut)
@limiter.limit("30/hour")
async def ask(
    request: Request,
    body: QuestionIn,
    db: Annotated[Session, Depends(get_db)],
) -> AnswerOut:
    question_hash = hashlib.sha256(body.question.encode()).hexdigest()

    if _is_out_of_scope(body.question):
        trace = AnswerTrace(
            question_hash=question_hash,
            question_redacted=body.question.strip(),
            answer_text=_SCOPE_REDIRECT_TEXT,
            sources_json="[]",
            valid=True,
            pii_types_json="[]",
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)
        return AnswerOut(
            answer=_SCOPE_REDIRECT_TEXT,
            sources=[],
            valid=True,
            confidence="info",
            trace_id=trace.id,
            pii_redacted=[],
        )

    redacted_question, pii_types = redact(body.question)

    retriever = get_retriever()
    generator = get_generator()

    chunks = retriever.search(redacted_question, top_k=5)
    answer = generator.generate(redacted_question, chunks)

    allowed = {chunk.article_number for chunk in chunks}
    validation = validate_citations(answer.text, allowed)

    sources = [
        SourceOut(article_number=c.article_number, text=c.text, score=c.score)
        for c in chunks
    ]

    trace = AnswerTrace(
        question_hash=question_hash,
        question_redacted=redacted_question,
        answer_text=answer.text,
        sources_json=json.dumps([s.model_dump() for s in sources]),
        valid=validation.valid,
        pii_types_json=json.dumps(pii_types),
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)

    return AnswerOut(
        answer=answer.text,
        sources=sources,
        valid=validation.valid,
        confidence=_extract_confidence(answer.text),
        trace_id=trace.id,
        pii_redacted=pii_types,
    )
