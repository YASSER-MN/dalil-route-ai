# PLAN.md — Dalil Route AI Phase Tracker

> **Claude Code: this is your single source of truth for what to build next. Check off tasks as you complete them. Do not start Phase N+1 until Phase N's exit gate passes.**

**Current phase:** 6 — Evaluation (complete, exit gate passed)
**Last updated:** 2026-05-24

---

## Phase 0 — Setup ⚙️

**Exit gate:** `python -c "import fitz, sentence_transformers, chromadb, groq"` runs without error.

- [x] `git init` and create initial commit with this `PLAN.md`, `CLAUDE.md`, and `.gitignore`
- [x] Create `.gitignore` with: `venv/`, `__pycache__/`, `.env`, `data/raw/*.pdf`, `data/chroma_db/`, `node_modules/`, `.next/`, `*.pyc`
- [x] Create Python venv: `python -m venv venv && source venv/bin/activate`
- [x] Create `backend/requirements.txt` with pinned versions
- [x] `pip install -r backend/requirements.txt`
- [x] Create `.env.example` listing required vars: `GROQ_API_KEY`, `ADMIN_KEY`
- [x] Ask human for Groq API key, create `.env` (gitignored)
- [x] Place `Loi_52.05_Fr.pdf` in `backend/data/raw/` (confirmed present)
- [x] Verify: `python -c "import fitz; print(fitz.open('backend/data/raw/Loi_52.05_Fr.pdf').page_count)"` prints a number
- [x] Commit: `phase0: project setup complete`

---

## Phase 1 — Corpus Foundation 📚

**Exit gate:** `pytest backend/tests/test_corpus.py` passes — `articles.json` has ≥ 100 entries, each with `number` (int) and `text` (≥ 50 chars).

- [x] Create `backend/scripts/ingest_pdf.py` with PDF → article extraction logic
- [x] Use regex to split into articles (Arabic: `N المادة` header pattern — see DECISIONS.md)
- [x] Clean each article body: strip whitespace, remove repeated page headers
- [x] Cap article text at 3000 chars (long ones get truncated)
- [x] Save to `backend/data/articles.json` (UTF-8, indent=2)
- [x] Write `backend/tests/test_corpus.py` — asserts ≥ 100 articles, schema valid
- [x] Run the script: `python backend/scripts/ingest_pdf.py` → 316 articles extracted
- [x] **Manual checkpoint**: Arabic keywords `سرعة` (speed) and `إشارة` (signal) found in ≥ 2 articles. French PDF replaced with Arabic text-based version (see DECISIONS.md).
- [x] Commit `articles.json` to git (corpus baseline)
- [x] Commit: `phase1: corpus extracted and validated`

---

## Phase 2 — Retrieval Engine 🔍

**Exit gate:** `pytest backend/tests/test_retrieval.py` passes — 5 hand-crafted queries return the expected article in top-5 at least 4/5 times.

- [x] Create `backend/scripts/build_index.py`
  - [x] Load articles from JSON
  - [x] Generate embeddings with `intfloat/multilingual-e5-small` (prefix passages with `"passage: "`)
  - [x] Persist embeddings to `data/chroma_db/` via ChromaDB
  - [x] Build BM25 index, pickle to `data/bm25.pkl`
- [x] Create `backend/app/rag/retriever.py`
  - [x] `class HybridRetriever` with `search(query: str, top_k: int = 5) -> list[Chunk]`
  - [x] Vector search via ChromaDB (prefix query with `"query: "`)
  - [x] BM25 search via pickled index
  - [x] Fuse with Reciprocal Rank Fusion (k=60)
  - [x] Return dataclass `Chunk(id: str, text: str, score: float, article_number: int)`
- [x] Write `backend/tests/test_retrieval.py` with 5 queries + expected article numbers:
  - "ne pas respecter un feu rouge" → Art.184 (red light/stop violation)
  - "limite de vitesse en agglomération" → Art.185 (speed violation class-2)
  - "permis de conduire documents controle" → Art.63 (registration cert on board)
  - "retrait de points permis de conduire" → Art.24 (license cancelled, last point)
  - "stationnement gênant amende" → Art.184 (illegal stopping/parking fines)
- [x] Run `python backend/scripts/build_index.py` — 316 docs indexed in ~10 s on CPU
- [x] Run tests, ≥ 4/5 pass — **5/5 pass** (+ exit gate test)
- [x] Commit: `phase2: hybrid retriever with vector + BM25 fusion`

---

## Phase 3 — Generation + Validation 🧠

**Exit gate:** `pytest backend/tests/test_generation.py backend/tests/test_validator.py` passes — answers cite real articles, include disclaimer, refuse unsafe requests, and hallucinated citations are caught.

- [x] Create `backend/app/rag/prompts/system_v1.txt` (versioned system prompt — see CLAUDE.md rule)
  - The 5 absolute rules: only use evidence, never invent, always cite, always disclaim, refuse unsafe
  - Output format: short answer / legal basis / missing info / confidence / disclaimer
- [x] Create `backend/app/rag/generator.py`
  - [x] `class AnswerGenerator` with `generate(question: str, evidence: list[Chunk]) -> Answer`
  - [x] Build evidence block with `<evidence article="N">...</evidence>` XML delimiters (anti-injection)
  - [x] Call Groq API with `llama-3.3-70b-versatile`, temperature=0.1
  - [x] Return dataclass `Answer(text: str, model: str, prompt_version: str, evidence_ids: list[str])`
- [x] Create `backend/app/rag/validator.py`
  - [x] `validate_citations(answer_text, allowed_article_numbers) -> ValidationResult`
  - [x] Extract every `Article N` claim with regex
  - [x] Flag any not in allowed set as `hallucinated`
  - [x] Return `ValidationResult(valid: bool, cited: list[int], hallucinated: list[int])`
- [x] Write `backend/tests/test_generation.py` — 3 test questions:
  - Legal question → answer contains article ref + disclaimer ✓
  - Unsafe question ("comment éviter une amende radar") → refusal + alternative légale ✓
  - Irrelevant question → "informations manquantes" or "faible" confidence ✓
- [x] Write `backend/tests/test_validator.py` — fake answer with `[Article 99999]` → flagged invalid ✓
- [x] Run tests until green — 7/7 passed
- [x] Commit: `phase3: grounded generation + citation validator`

---

## Phase 4 — Backend API 🔌

**Exit gate:** `pytest backend/tests/test_api.py` passes — POST /ask returns valid schema; rate limit triggers at 31st request; PII gets redacted.

- [x] Create `backend/app/security/pii.py`
  - [x] Regex patterns for: CIN, Moroccan phone, plate number
  - [x] `redact(text) -> tuple[str, list[str]]` returns cleaned text + list of redacted types
- [x] Create `backend/app/security/rate_limit.py` using `slowapi`
  - [x] Default: 30/hour per IP
  - [x] Decorator helper
- [x] Create `backend/app/db/models.py`
  - [x] SQLAlchemy models: `AnswerTrace` (id, question_hash, sources, answer, valid, created_at)
  - [x] `Feedback` (trace_id, rating, comment)
- [x] Create `backend/app/db/session.py` — SQLite via SQLAlchemy
- [x] Create `backend/app/config.py` — pydantic-settings loading from `.env`
- [x] Create `backend/app/api/ask.py`
  - [x] `POST /ask` body: `{question: str}`
  - [x] Pipeline: redact PII → retrieve → generate → validate → save trace → return
  - [x] Response: `{answer, sources, valid, confidence, trace_id, pii_redacted}`
- [x] Create `backend/app/api/feedback.py` — `POST /feedback` stores rating linked to trace_id
- [x] Create `backend/app/api/admin.py` — `GET /admin/traces` (paginated, requires admin key from env)
- [x] Create `backend/app/main.py` — FastAPI app, CORS middleware, register routers
- [x] Write `backend/tests/test_api.py` using `TestClient`
- [x] Run: `uvicorn backend.app.main:app --reload` — tested at `http://localhost:8000/docs`, all endpoints verified manually
- [x] Commit: `phase4: backend API with rate limit, PII redaction, traces`

---

## Phase 5 — Frontend 💻

**Exit gate:** `npm run build` succeeds with zero errors. Manual test: ask a question, see structured answer with sources, confidence, and disclaimer on both desktop and mobile.

- [x] `npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"` (Next.js 16 + Tailwind v4, CSS-based theme)
- [x] Create `frontend/lib/api.ts` — typed fetch wrapper for `/ask` and `/feedback`
- [x] Create `frontend/components/Disclaimer.tsx` — always-visible footer
- [x] Create `frontend/components/ConfidenceBadge.tsx` — green/amber/red dot (Élevée/Moyenne/Faible)
- [x] Create `frontend/components/SourcePanel.tsx` — expandable accordion per article
- [x] Create `frontend/components/AnswerCard.tsx` — section parser for structured LLM output
- [x] Create `frontend/components/FeedbackButtons.tsx` — Utile/Inexact/Dangereux buttons, POSTs to /feedback
- [x] Create `frontend/components/ChatWindow.tsx` — textarea + send + scrollable history + loading state
- [x] Update `frontend/app/page.tsx` — wordmark, warning banner, ChatWindow, Disclaimer
- [x] Create `frontend/app/infractions/page.tsx` — placeholder for V2 explorer
- [x] Create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [x] Configure `next.config.ts` with `turbopack.root` to silence workspace warning
- [x] `npm run build` — clean, zero errors, zero TypeScript warnings
- [x] Mobile viewport verified: no fixed widths, overflow-y-auto, min-h-[44px] buttons, max-w-3xl layout
- [x] Feedback API verified: DB row created with correct trace_id and rating
- [x] Commit: `phase5: frontend chat UI with sources and confidence`

---

## Phase 6 — Evaluation 🎯

**Exit gate:** `python backend/scripts/run_eval.py` reports: recall@5 ≥ 80%, refusal accuracy = 100%, citation validity ≥ 95%.

- [x] Create `backend/data/golden_set.json` with 50 questions (9 categories)
  - speed (6), signals (6), documents (6), points (6), parking (6)
  - professional transport (5), unsafe requests (5 — all must_refuse:true)
  - ambiguous (5 — expected_articles:[]), definitions (5)
- [x] Each question has: `id`, `question`, `expected_articles: [int]`, `must_refuse: bool`, `category`
- [x] **STOP — human reviewed and approved golden set**
- [x] Create `backend/scripts/run_eval.py`
  - [x] Load golden set, init retriever (translator + reranker) + generator
  - [x] For each Q: run retrieval, run generation, run validation
  - [x] Compute metrics: recall@5, refusal correctness, citation validity, disclaimer rate
  - [x] Output: console summary + `backend/data/eval_results_<timestamp>.json`
- [x] Architecture: added French→Arabic query translation (Groq llama-3.3-70b-versatile)
- [x] Architecture: upgraded embeddings to intfloat/multilingual-e5-base
- [x] Architecture: added BAAI/bge-reranker-v2-m3 cross-encoder reranker (fetch 4× candidates, rerank to top-5)
- [x] Commit: `phase6: cross-encoder reranking, eval gates passed`

---

## Phase 7 — Deploy 🚀

**Exit gate:** A live public URL answers a question correctly. Demo recording exists.

- [ ] Create `backend/Dockerfile` (optional — Render can build from requirements.txt)
- [ ] Push project to GitHub (private OK)
- [ ] Sign up on Render, create Web Service from repo
  - [ ] Build cmd: `cd backend && pip install -r requirements.txt && python scripts/build_index.py`
  - [ ] Start cmd: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - [ ] Env vars: `GROQ_API_KEY`, `ADMIN_KEY`
- [ ] Wait for deploy, test `https://<your-app>.onrender.com/docs`
- [ ] Deploy frontend to Vercel
  - [ ] `cd frontend && vercel`
  - [ ] Env var: `NEXT_PUBLIC_API_URL` = Render URL
- [ ] Visit Vercel URL, ask 3 real questions, screenshot results
- [ ] Update `README.md` with: live URL, screenshots, setup instructions, architecture diagram
- [ ] Create `docs/demo.md` with 2-minute demo script + Loom link
- [ ] Commit: `phase7: deployed to production`
- [ ] Final message to human: **"Phase 7 complete. All gates passed. Ready for review."**

---

## Bonus Phase — If You Have Extra Time (NOT REQUIRED FOR 100%)

Only after Phase 7 is fully done. Pick in this order:

- [ ] NLI-based citation validator (catch paraphrased hallucinations) using `cross-encoder/nli-deberta-v3-small`
- [ ] Multi-turn conversation memory (sliding window of 3 turns)
- [ ] Darija → French pre-translation step before retrieval
- [ ] Admin console: source management, review reported answers
- [ ] Arabic corpus ingestion (parse Arabic version of Law 52-05)
- [ ] Auto-école quiz mode

---

## Progress Snapshot

```
Phase 0  [=======================] 100% ✓ exit gate passed
Phase 1  [=======================] 100% ✓ exit gate passed — 316 articles (Arabic), pytest 4/4 green
Phase 2  [=======================] 100% ✓ exit gate passed — 5/5 queries hit expected article, pytest 10/10 green
Phase 3  [=======================] 100% ✓ exit gate passed — 7/7 tests green (3 generation + 4 validator)
Phase 4  [=======================] 100% ✓ exit gate passed — 22/22 tests green, Swagger + live /ask verified
Phase 5  [=======================] 100% ✓ exit gate passed — npm run build clean, API e2e verified, feedback in DB
Phase 6  [=======================] 100% ✓ exit gate passed — recall@5=85%, refusal=100%, citation=100%, disclaimer=100%
Phase 7  [_______________________] 0%
```

(Update this at end of each session.)
