# DECISIONS.md — Non-Obvious Architectural Choices

> Log every decision that deviates from convention or that a future developer might question.
> Format: **Date | Decision | Why | Trade-offs**

---

## 2026-05-22 | SQLite for V1 persistence

**Decision:** Use SQLite via SQLAlchemy for answer traces and feedback.
**Why:** Zero ops overhead for V1. The data volume (traces + feedback) will be small enough for SQLite for months.
**Trade-offs:** Not horizontally scalable. Migration path to Postgres is straightforward with SQLAlchemy (change the connection string, run `alembic upgrade`).

---

## 2026-05-22 | intfloat/multilingual-e5-small for embeddings

**Decision:** Use the small multilingual E5 model, not a larger variant.
**Why:** Free, fast on CPU, handles French text well. The "small" variant runs in < 1 s per batch on a 2-core Render instance.
**Trade-offs:** Lower recall than `-base` or `-large`. If Phase 6 eval shows recall@5 < 80%, upgrade to `-base` (see PLAN.md Phase 6 fallback).

---
