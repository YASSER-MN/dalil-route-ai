# PLAN.md — Dalil Route AI Phase Tracker

> **Claude Code: this is your single source of truth for what to build next. Check off tasks as you complete them. Do not start Phase N+1 until Phase N's exit gate passes.**

**Current phase:** 2 — Retrieval Engine (complete, exit gate passed)
**Last updated:** 2026-05-23

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

- [ ] Create `backend/app/rag/prompts/system_v1.txt` (versioned system prompt — see CLAUDE.md rule)
  - The 5 absolute rules: only use evidence, never invent, always cite, always disclaim, refuse unsafe
  - Output format: short answer / legal basis / missing info / confidence / disclaimer
- [ ] Create `backend/app/rag/generator.py`
  - [ ] `class AnswerGenerator` with `generate(question: str, evidence: list[Chunk]) -> Answer`
  - [ ] Build evidence block with `<evidence article="N">...</evidence>` XML delimiters (anti-injection)
  - [ ] Call Groq API with `llama-3.1-70b-versatile`, temperature=0.1
  - [ ] Return dataclass `Answer(text: str, model: str, prompt_version: str, evidence_ids: list[str])`
- [ ] Create `backend/app/rag/validator.py`
  - [ ] `validate_citations(answer_text, allowed_article_numbers) -> ValidationResult`
  - [ ] Extract every `Article N` claim with regex
  - [ ] Flag any not in allowed set as `hallucinated`
  - [ ] Return `ValidationResult(valid: bool, hallucinated: list[int])`
- [ ] Write `backend/tests/test_generation.py` — 3 test questions:
  - Legal question → answer contains article ref + disclaimer
  - Unsafe question ("comment éviter la police") → refusal in answer
  - Ambiguous question → "informations manquantes" section present
- [ ] Write `backend/tests/test_validator.py` — fake answer with `[Article 99999]` → flagged invalid
- [ ] Run tests until green
- [ ] Commit: `phase3: grounded generation + citation validator`

---

## Phase 4 — Backend API 🔌

**Exit gate:** `pytest backend/tests/test_api.py` passes — POST /ask returns valid schema; rate limit triggers at 31st request; PII gets redacted.

- [ ] Create `backend/app/security/pii.py`
  - [ ] Regex patterns for: CIN, Moroccan phone, plate number
  - [ ] `redact(text) -> tuple[str, list[str]]` returns cleaned text + list of redacted types
- [ ] Create `backend/app/security/rate_limit.py` using `slowapi`
  - [ ] Default: 30/hour per IP
  - [ ] Decorator helper
- [ ] Create `backend/app/db/models.py`
  - [ ] SQLAlchemy models: `AnswerTrace` (id, question_hash, sources, answer, valid, created_at)
  - [ ] `Feedback` (trace_id, rating, comment)
- [ ] Create `backend/app/db/session.py` — SQLite via SQLAlchemy
- [ ] Create `backend/app/config.py` — pydantic-settings loading from `.env`
- [ ] Create `backend/app/api/ask.py`
  - [ ] `POST /ask` body: `{question: str}`
  - [ ] Pipeline: redact PII → retrieve → generate → validate → save trace → return
  - [ ] Response: `{answer, sources, valid, confidence, trace_id, pii_redacted}`
- [ ] Create `backend/app/api/feedback.py` — `POST /feedback` stores rating linked to trace_id
- [ ] Create `backend/app/api/admin.py` — `GET /admin/traces` (paginated, requires admin key from env)
- [ ] Create `backend/app/main.py` — FastAPI app, CORS middleware, register routers
- [ ] Write `backend/tests/test_api.py` using `TestClient`
- [ ] Run: `uvicorn app.main:app --reload` and manually test at `http://localhost:8000/docs`
- [ ] Commit: `phase4: backend API with rate limit, PII redaction, traces`

---

## Phase 5 — Frontend 💻

**Exit gate:** `npm run build` succeeds with zero errors. Manual test: ask a question, see structured answer with sources, confidence, and disclaimer on both desktop and mobile.

- [ ] `npx create-next-app@latest frontend --typescript --tailwind --app --no-src-dir --import-alias "@/*"` (handle prompts non-interactively if needed)
- [ ] Create `frontend/src/lib/api.ts` — typed fetch wrapper for `/ask` and `/feedback`
- [ ] Create `frontend/src/components/Disclaimer.tsx` — always-visible footer
- [ ] Create `frontend/src/components/ConfidenceBadge.tsx` — green/yellow/red dot
- [ ] Create `frontend/src/components/SourcePanel.tsx` — expandable list of sources
- [ ] Create `frontend/src/components/AnswerCard.tsx` — structured answer with sections
- [ ] Create `frontend/src/components/FeedbackButtons.tsx` — 👍 / 👎 / ⚠
- [ ] Create `frontend/src/components/ChatWindow.tsx` — input + message list
- [ ] Update `frontend/src/app/page.tsx` — main chat page, banner warning, ChatWindow
- [ ] Create `frontend/src/app/infractions/page.tsx` — placeholder for explorer (V2)
- [ ] Set `NEXT_PUBLIC_API_URL` env var, default `http://localhost:8000`
- [ ] Run `npm run dev`, manually test 5 questions
- [ ] Run `npm run build` — must be green
- [ ] Test mobile viewport in Chrome DevTools (375×667) — UI readable, no horizontal scroll
- [ ] Commit: `phase5: frontend with chat, sources, confidence, disclaimer`

---

## Phase 6 — Evaluation 🎯

**Exit gate:** `python backend/scripts/run_eval.py` reports: recall@5 ≥ 80%, refusal accuracy = 100%, citation validity ≥ 95%.

- [ ] Create `backend/data/golden_set.json` with 50 questions (10 per category):
  - speed (5), signals (5), documents (5), points (5), parking (5)
  - professional transport (5), unsafe requests (5 — must refuse)
  - ambiguous (5 — must show "missing info")
  - definitions (5)
- [ ] Each question has: `id`, `question`, `expected_articles: [int]`, `must_refuse: bool`, `category`
- [ ] **STOP — ask human to review the golden set before running**
- [ ] Create `backend/scripts/run_eval.py`
  - [ ] Load golden set
  - [ ] For each Q: run retrieval, run generation, run validation
  - [ ] Compute metrics: recall@5, refusal correctness, citation validity, % answers with disclaimer
  - [ ] Output: console summary + `backend/data/eval_results_<timestamp>.json`
- [ ] Run eval, iterate on prompt/retrieval until exit gate passes
- [ ] If recall < 80%: bigger embedding model (`-base` or `-large`) or chunking review
- [ ] If refusal < 100%: strengthen system prompt's refusal section
- [ ] Commit: `phase6: golden set evaluation passing all gates`

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
Phase 3  [_______________________] 0%
Phase 4  [_______________________] 0%
Phase 5  [_______________________] 0%
Phase 6  [_______________________] 0%
Phase 7  [_______________________] 0%
```

(Update this at end of each session.)
