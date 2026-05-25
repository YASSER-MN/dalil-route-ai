import hashlib
import json
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

# Module-level singletons — loaded once at startup
_retriever: HybridRetriever | None = None
_generator: AnswerGenerator | None = None


def _get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        translator = QueryTranslator(api_key=settings.groq_api_key) if settings.groq_api_key else None
        _retriever = HybridRetriever(translator=translator)
    return _retriever


def _get_generator() -> AnswerGenerator:
    global _generator
    if _generator is None:
        _generator = AnswerGenerator()
    return _generator


class QuestionIn(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class SourceOut(BaseModel):
    article_number: int
    text: str
    score: float


class AnswerOut(BaseModel):
    answer: str
    sources: list[SourceOut]
    valid: bool
    trace_id: str
    pii_redacted: list[str]


@router.post("/ask", response_model=AnswerOut)
@limiter.limit("30/hour")
async def ask(
    request: Request,
    body: QuestionIn,
    db: Annotated[Session, Depends(get_db)],
) -> AnswerOut:
    question_hash = hashlib.sha256(body.question.encode()).hexdigest()
    redacted_question, pii_types = redact(body.question)

    retriever = _get_retriever()
    generator = _get_generator()

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
        trace_id=trace.id,
        pii_redacted=pii_types,
    )
