from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AnswerTrace(Base):
    __tablename__ = "answer_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question_hash: Mapped[str] = mapped_column(String(64), index=True)
    question_redacted: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[str] = mapped_column(Text)
    valid: Mapped[bool] = mapped_column(Boolean, default=True)
    pii_types_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    feedbacks: Mapped[list[Feedback]] = relationship("Feedback", back_populates="trace")


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trace_id: Mapped[str] = mapped_column(String(36), ForeignKey("answer_traces.id"), index=True)
    rating: Mapped[str] = mapped_column(String(16))  # helpful | wrong | unsafe
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    trace: Mapped[AnswerTrace] = relationship("AnswerTrace", back_populates="feedbacks")
