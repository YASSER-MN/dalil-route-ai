# CLAUDE.md — Dalil Route AI

> **You are building an evidence-first LegalTech RAG system for the Moroccan Code de la Route. Every architectural decision in this document is non-negotiable. Do not over-engineer. Do not add features beyond `PLAN.md`. Do not skip tests.**

---

## 1. The One Rule That Overrides Everything

**No source = no answer.** Every legal claim in any generated answer must be traceable to a retrieved chunk from a validated source. If you find yourself writing code that lets the LLM answer without retrieved evidence, **stop and re-read this file**. The corpus is in Arabic (official consolidated text). Queries arrive in French today, Darija tomorrow. All queries are translated to Arabic before retrieval. Citations always trace back to the official Arabic source.

---

## 2. Build Order (STRICTLY ENFORCED)

You will build the system in this exact order. **You may not start a phase until the previous phase has all its tests passing.** This is enforced by `PLAN.md`.

```
Phase 0  Setup ───▶  Phase 1  Corpus ───▶  Phase 2  Retrieval
                                                  │
                                                  ▼
Phase 5  Frontend  ◀───  Phase 4  Backend  ◀───  Phase 3  Generation+Validation
   │
   ▼
Phase 6  Evaluation ───▶  Phase 7  Deploy
```

If you feel tempted to "just sketch out the frontend while I think about retrieval" — **do not**. The frontend phase is gated on the backend test suite passing. Building UI on a broken backend is the #1 failure mode of LegalTech projects.

---

## 3. Tech Stack (FIXED — DO NOT SUBSTITUTE)

| Concern         | Use                                    | NOT                          |
| --------------- | -------------------------------------- | ---------------------------- |
| Language        | Python 3.11+ (backend), TypeScript (UI)| —                            |
| PDF parsing     | `pymupdf` (fitz)                       | pdfplumber, pypdf2 (slower)  |
| Embeddings      | `sentence-transformers` + `intfloat/multilingual-e5-base` | OpenAI ada (paid)            |
| Query translation | Groq `llama-3.3-70b-versatile`        | —                            |
| Vector store    | `chromadb` (persistent, local)         | Pinecone (paid), Weaviate (overkill) |
| Keyword search  | `rank-bm25`                            | Elasticsearch (overkill)     |
| LLM             | Groq API + `llama-3.3-70b-versatile`   | OpenAI (paid), local llama (too slow) |
| Backend         | FastAPI + uvicorn + slowapi            | Flask, Django                |
| Persistence     | SQLite (V1) — Postgres only if needed  | Postgres from day 1          |
| Frontend        | Next.js 14 (app router) + TailwindCSS  | Pure React, Vue, vanilla     |
| Deploy          | Render (backend) + Vercel (frontend)   | AWS, GCP, Docker             |

**If you think the project needs a different tool, write your reasoning to `DECISIONS.md` and ask the human before changing the stack.**

---

## 4. Workflow Rules

### Every session starts with:

```bash
git status                      # see what's pending
cat PLAN.md | head -60          # see current phase + open tasks
git log --oneline -10           # see recent commits
```

### Every task ends with:

```bash
# 1. Run the test that proves the task is done
python -m pytest tests/test_<area>.py -v
# 2. If green, commit
git add -A && git commit -m "phase<N>: <what changed>"
# 3. Update PLAN.md — check off the task
# 4. Move to next task
```

### Commit cadence

- One logical change = one commit.
- Commit message format: `phase<N>: <imperative summary>` (e.g. `phase2: add hybrid retriever with RRF fusion`).
- **Never commit broken code.** If tests fail, fix them or revert.

---

## 5. Testing Requirements (NON-NEGOTIABLE)

Every Python module under `backend/app/` must have a sibling test file under `backend/tests/`. Minimum coverage per phase:

| Phase | Test that must pass before phase completes |
| ----- | ------------------------------------------ |
| 1     | `test_corpus.py` — extracts ≥ 100 articles from the PDF, each has `number` and `text ≥ 50 chars` |
| 2     | `test_retrieval.py` — given 5 hand-crafted queries, expected article appears in top-5 ≥ 4/5 times |
| 3     | `test_generation.py` — 3 questions produce answers that (a) cite an article, (b) include disclaimer, (c) refuse unsafe request |
| 3     | `test_validator.py` — fake answer with `[Article 99999]` is flagged as hallucinated |
| 4     | `test_api.py` — POST /ask returns 200 with valid schema; rate limit triggers at 31st request |
| 6     | `test_golden_set.py` — 50-question set runs end-to-end, recall@5 ≥ 80%, refusal accuracy 100% |

If you cannot pass these tests, **do not move on**. Debug. Ask the human if blocked > 30 minutes.

---

## 6. Code Style

- **Python**: type hints on all public functions. `dataclasses` over dicts for structured data. `pathlib.Path` over string paths. `from __future__ import annotations` at top of every file.
- **Async**: only in FastAPI route handlers. Keep RAG logic sync — easier to debug.
- **No premature abstraction**. If you have one implementation, write a function not a class. If you have two, write a class. Three+, write an interface.
- **No comments that restate the code**. Comments explain *why*, never *what*.
- **TypeScript**: strict mode on. `interface` over `type` for object shapes. No `any`.

---

## 7. Forbidden Patterns

These are bugs waiting to happen. Never:

- ❌ Call the LLM without retrieved evidence in the prompt.
- ❌ Use string `.format()` or f-strings to inject untrusted user input into prompts. Use a templating library with sandboxed variables.
- ❌ Store API keys in code. Always `os.getenv()`.
- ❌ Catch `except Exception` without re-raising or logging. Specific exceptions only.
- ❌ Write `TODO` comments without a corresponding task in `PLAN.md`.
- ❌ Add a new dependency without justifying it in `DECISIONS.md`.
- ❌ Modify the file structure in section 8 without updating this file.
- ❌ Build frontend components for a backend endpoint that doesn't exist yet.
- ❌ Skip the disclaimer in any user-facing answer.
- ❌ Log user questions verbatim. Hash them or redact PII first.

---

## 8. Canonical File Structure

```
dalil-route-ai/
├── CLAUDE.md              ← this file
├── PLAN.md                ← phase tracker (you update this)
├── DECISIONS.md           ← log non-obvious choices here
├── .env.example           ← template, no real secrets
├── .gitignore             ← must exclude .env, venv/, data/chroma_db/
├── README.md              ← human-facing project intro
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py        ← FastAPI entry
│   │   ├── config.py      ← settings via pydantic-settings
│   │   ├── rag/
│   │   │   ├── retriever.py
│   │   │   ├── generator.py
│   │   │   ├── validator.py
│   │   │   └── prompts/
│   │   │       └── system_v1.txt
│   │   ├── security/
│   │   │   ├── pii.py
│   │   │   └── rate_limit.py
│   │   ├── db/
│   │   │   ├── models.py     ← SQLAlchemy
│   │   │   └── session.py
│   │   └── api/
│   │       ├── ask.py
│   │       ├── feedback.py
│   │       └── admin.py
│   ├── scripts/
│   │   ├── ingest_pdf.py     ← run once per source
│   │   ├── build_index.py    ← embeddings + chroma + bm25
│   │   └── run_eval.py       ← golden set runner
│   ├── tests/
│   │   ├── test_corpus.py
│   │   ├── test_retrieval.py
│   │   ├── test_generation.py
│   │   ├── test_validator.py
│   │   ├── test_api.py
│   │   └── test_golden_set.py
│   └── data/
│       ├── raw/              ← original PDFs (gitignored)
│       ├── articles.json     ← parsed corpus (committed)
│       ├── golden_set.json   ← test questions (committed)
│       └── chroma_db/        ← vector store (gitignored)
└── frontend/
    ├── package.json
    ├── next.config.js
    ├── tailwind.config.js
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx           ← chat UI
        │   └── infractions/
        │       └── page.tsx
        ├── components/
        │   ├── ChatWindow.tsx
        │   ├── AnswerCard.tsx
        │   ├── SourcePanel.tsx
        │   ├── ConfidenceBadge.tsx
        │   ├── Disclaimer.tsx
        │   └── FeedbackButtons.tsx
        └── lib/
            └── api.ts            ← typed fetch wrapper
```

If a file you need to create isn't in this list, add it to `PLAN.md` and explain why in your commit message.

---

## 9. Stop Conditions (ASK THE HUMAN)

You stop and ask the user — never decide unilaterally — when:

1. A test has been red for more than 30 minutes of attempts.
2. You want to add a paid service (anything that isn't free-tier).
3. You want to change the tech stack in section 3.
4. You're about to delete more than 50 lines of working code.
5. You hit a question about **legal interpretation** — you are not a jurist.
6. The PDF parsing produces fewer than 100 articles — quality is at risk.
7. The golden set falls below 75% recall — something regressed.
8. You need an API key the human hasn't provided.

When you stop, write a brief message: *what's blocking, what you tried, what you recommend*.

---

## 10. Definition of "100% Done"

The project is 100% complete when ALL of these are true:

- [ ] All 7 phases in `PLAN.md` show every task checked off.
- [ ] `pytest backend/tests/` runs all tests green.
- [ ] `python backend/scripts/run_eval.py` reports recall@5 ≥ 80%, refusal accuracy = 100%.
- [ ] Frontend builds with `npm run build` without errors or warnings.
- [ ] Backend starts with `uvicorn app.main:app` and `/ask` returns a sourced answer.
- [ ] `README.md` has setup instructions a new developer can follow in < 15 minutes.
- [ ] `git log --oneline | wc -l` shows ≥ 40 commits (one per logical change).
- [ ] The deployed URL (Render + Vercel) answers a real question in production.
- [ ] A 2-minute demo recording exists at `docs/demo.md` (script + link).

When all of these are true, write a final message to the human: *"Phase 7 complete. All gates passed. Ready for review."*

---

## 11. When You're Confused

Re-read this file. Then re-read `PLAN.md`. Then look at the last 3 commits. The answer is usually in one of those three places.

If still stuck after 10 minutes, **ask the human**. Don't guess.
