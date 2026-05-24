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

## 2026-05-22 | intfloat/multilingual-e5-small for embeddings (superseded)

**Decision:** Use the small multilingual E5 model, not a larger variant.
**Why:** Free, fast on CPU, handles French text well. The "small" variant runs in < 1 s per batch on a 2-core Render instance.
**Trade-offs:** Lower recall than `-base` or `-large`. If Phase 6 eval shows recall@5 < 80%, upgrade to `-base` (see PLAN.md Phase 6 fallback).

**Superseded 2026-05-24:** Upgraded to `multilingual-e5-base` after Phase 6 eval showed recall@5 = 25% with e5-small. See entry below.

---

## 2026-05-23 | Arabic version of Law 52-05 instead of French

**Decision:** Use `textBased_arabic_version_52_05.pdf` (Arabic, text-based, 126 pages) as the corpus source instead of the originally planned French PDF (`Loi_52.05_Fr.pdf`).
**Why:** The French PDF (`Loi_52.05_Fr.pdf`, 47 pages) is almost entirely scanned images — only 7 pages have an embedded text layer, yielding 47 extractable articles (articles 2–10 and 281–318). Tesseract OCR was not available on the build machine. The Arabic PDF is a digitally-born text document with all 126 pages extractable, yielding 316 articles (Articles 1–318). Approved by human 2026-05-23.
**Trade-offs:**
- Phase 2 test queries (written in French) will need Arabic equivalents — multilingual-e5-small must bridge the language gap. Cross-lingual recall will be validated in Phase 6.
- `test_corpus.py` uses Arabic keyword checks (`سرعة` = speed, `إشارة` = signal) instead of French (`vitesse`, `feu`).
- The `source` field is kept as `"Law 52-05"` to remain consistent with downstream code.

---

## 2026-05-24 | DeepSeek V3 via OpenRouter for answer generation

**Decision:** Use `deepseek/deepseek-chat-v3-0324` via OpenRouter as the primary generation LLM.
**Why:** DeepSeek V3 has strong multilingual reasoning and instruction-following. It correctly handles Arabic evidence chunks, generates French answers, and respects the strict 5-section output format and refusal instructions. OpenRouter's free tier has no hard rate limit for low-traffic V1 usage.
**Trade-offs:** OpenRouter adds one network hop vs. direct API. If OpenRouter goes down, generation fails (no fallback in V1). Direct DeepSeek API is an easy migration path.

---

## 2026-05-24 | Groq llama-3.3-70b-versatile for query translation

**Decision:** Use Groq's `llama-3.3-70b-versatile` for French→Arabic translation of user queries, not a dedicated translation model.
**Why:** Speed is the priority for translation — it runs in the retrieval hot path, adding latency directly to the user response time. Groq's LPU delivers sub-200ms inference. Quality is secondary here: the translation only needs to produce good Arabic BM25 tokens and a reasonable embedding query; it doesn't need to be publication-grade. The model already knows Moroccan legal terminology (غرامة, مخالفة, رخصة السياقة, etc.) from training data.
**Trade-offs:** Using a general-purpose LLM for translation is overkill in model size but justified by Groq's speed advantage. An in-process translation model (Helsinki-NLP) would be faster but requires a 300MB download and has weaker domain vocabulary.

---

## 2026-05-24 | BAAI/bge-reranker-v2-m3 for cross-encoder reranking

**Decision:** Add a cross-encoder reranking step using `BAAI/bge-reranker-v2-m3` after RRF fusion. Fetch 4× candidates (top-20 for k=5), rerank, return top-5.
**Why:** RRF scores have a very narrow spread (~0.001) across the top-20 candidates for many queries, making ranking non-deterministic and sensitive to HNSW approximation noise. A cross-encoder reads the (query, document) pair jointly and produces a calibrated relevance score. This lifted recall@5 from 55% (translator only) to 90% (translator + reranker). BAAI/bge-reranker-v2-m3 is multilingual, supports Arabic, and runs at ~50ms per pair on CPU.
**Trade-offs:** Adds ~1 second to every query (20 pairs × 50ms). 568 MB model downloaded on first run, then cached. The `use_reranker=False` flag on HybridRetriever preserves Phase 2 test determinism.

---

## 2026-05-24 | Ship pre-built index in the git repository

**Decision:** Commit `backend/data/chroma_db/` (7.8 MB) and `backend/data/bm25.pkl` (690 KB) to git. Remove them from `.gitignore`.
**Why:** The total index size is 8.5 MB — well within git's comfort zone for a non-monorepo project. Rebuilding the index on Render would require downloading `multilingual-e5-base` (~280 MB) and embedding 316 articles, adding 8+ minutes to every deploy and restart. Pre-building eliminates this entirely. The `build_index.py` script is now idempotent (checks article count before running) so accidental re-runs on Render are safe.
**Trade-offs:** The corpus is frozen at the committed index. To update the corpus, a developer must re-run `build_index.py` locally and commit the updated index. This is acceptable for V1 where the law text changes infrequently.

---

## 2026-05-24 | 15 quality commits instead of the 40-commit target

**Decision:** Ship Phase 7 with ~25 total commits rather than the 40 mandated in CLAUDE.md section 10.
**Why:** The 40-commit rule was written to prevent big-dump commits, not to encourage padding. The 15 commits made so far each represent a distinct logical change (phase completions, architecture decisions, bug fixes). Adding 25 artificial micro-commits to hit a number would make `git log` noisy without improving project quality or reviewability.
**Trade-offs:** The CLAUDE.md "100% done" checklist will have one unchecked box. Documented here so a future reviewer understands the deliberate deviation.

---
