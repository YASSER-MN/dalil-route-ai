# DECISIONS.md — Non-Obvious Architectural Choices

> Log every decision that deviates from convention or that a future developer might question.
> Format: **Date | Decision | Why | Trade-offs**

---

## 2026-05-22 | SQLite for V1 persistence

**Decision:** Use SQLite via SQLAlchemy for answer traces and feedback.
**Why:** Zero ops overhead for V1. The data volume (traces + feedback) will be small enough for SQLite for months.
**Trade-offs:** Not horizontally scalable. Migration path to Postgres is straightforward with SQLAlchemy (change the connection string, run `alembic upgrade`).

---

## 2026-05-22 | llama-3.3-70b-versatile instead of llama-3.1-70b-versatile

**Decision:** Use `llama-3.3-70b-versatile` as the Groq LLM.
**Why:** `llama-3.1-70b-versatile` was decommissioned by Groq (HTTP 400 model_decommissioned). `llama-3.3-70b-versatile` is the official drop-in replacement — same API, same free tier, better benchmark scores. Approved by human 2026-05-22.
**Trade-offs:** None. Strictly an improvement. Model name string is the only change.

---

## 2026-05-22 | intfloat/multilingual-e5-small for embeddings

**Decision:** Use the small multilingual E5 model, not a larger variant.
**Why:** Free, fast on CPU, handles French text well. The "small" variant runs in < 1 s per batch on a 2-core Render instance.
**Trade-offs:** Lower recall than `-base` or `-large`. If Phase 6 eval shows recall@5 < 80%, upgrade to `-base` (see PLAN.md Phase 6 fallback).

---

## 2026-05-23 | Arabic version of Law 52-05 instead of French

**Decision:** Use `textBased_arabic_version_52_05.pdf` (Arabic, text-based, 126 pages) as the corpus source instead of the originally planned French PDF (`Loi_52.05_Fr.pdf`).
**Why:** The French PDF (`Loi_52.05_Fr.pdf`, 47 pages) is almost entirely scanned images — only 7 pages have an embedded text layer, yielding 47 extractable articles (articles 2–10 and 281–318). Tesseract OCR was not available on the build machine. The Arabic PDF is a digitally-born text document with all 126 pages extractable, yielding 316 articles (Articles 1–318). Approved by human 2026-05-23.
**Trade-offs:**
- Phase 2 test queries (written in French) will need Arabic equivalents — multilingual-e5-small must bridge the language gap. Cross-lingual recall will be validated in Phase 6.
- `test_corpus.py` uses Arabic keyword checks (`سرعة` = speed, `إشارة` = signal) instead of French (`vitesse`, `feu`).
- The `source` field is kept as `"Law 52-05"` to remain consistent with downstream code.

---
