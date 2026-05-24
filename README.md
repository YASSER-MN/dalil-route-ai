# Dalil Route AI

> Evidence-first RAG assistant for the Moroccan Code de la Route (Law 52-05). Every legal claim traces back to a retrieved article from the official Arabic corpus. No source = no answer.

**Live demo:** TBD (deploying to Render + Vercel)

---

## Architecture

```
User (French question)
        │
        ▼
┌───────────────────┐
│  PII Redaction    │  CIN / phone / plate → [REDACTED]
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Query Translation │  Groq llama-3.3-70b-versatile
│  FR → Arabic      │  "feu rouge amende" → "غرامة إشارة المرور الحمراء"
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────┐
│         Hybrid Retrieval              │
│  Vector (multilingual-e5-base)        │  ChromaDB, top-20
│  + BM25 (Arabic tokens)               │  rank-bm25, top-20
│  → Reciprocal Rank Fusion             │  RRF k=60
│  → Cross-Encoder Reranker             │  BAAI/bge-reranker-v2-m3, top-5
└────────┬──────────────────────────────┘
         │ 5 evidence chunks
         ▼
┌───────────────────┐
│    Generation     │  DeepSeek V3 via OpenRouter
│  (grounded only)  │  temperature=0.1, evidence-only prompt
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│Citation Validator │  Any [Article N] not in retrieved set → hallucination
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│  Trace & Return   │  SQLite trace, answer + sources + validity flag
└───────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, uvicorn, slowapi |
| Embeddings | `intfloat/multilingual-e5-base` (local CPU) |
| Query translation | Groq `llama-3.3-70b-versatile` |
| Vector store | ChromaDB (persistent, local) |
| Keyword search | `rank-bm25` |
| Reranker | `BAAI/bge-reranker-v2-m3` (local CPU) |
| LLM generation | DeepSeek V3 via OpenRouter |
| Persistence | SQLite via SQLAlchemy |
| Frontend | Next.js 14 (App Router), TailwindCSS |
| Deploy | Render (backend) + Vercel (frontend) |

---

## Design Philosophy

**No source = no answer.** The system will never generate a legal claim that is not grounded in a retrieved article from the official corpus. The LLM receives only the retrieved evidence chunks — it cannot draw on training-data knowledge of Moroccan law. Every answer includes article citations that are validated against the retrieved set before the response is returned to the user.

This design choice prevents the single most dangerous failure mode in LegalTech AI: confident hallucination of law that does not exist or has been misquoted. A system that says "I don't have enough evidence to answer this" is safer than one that fabricates a plausible-sounding article number. The disclaimer on every answer reinforces that this is an informational tool, not a substitute for a licensed legal professional.

---

## Evaluation Results

Latest eval: [`backend/data/eval_results_20260524_104343.json`](backend/data/eval_results_20260524_104343.json)

| Metric | Result | Gate |
|--------|--------|------|
| recall@5 | **90.00%** (36/40) | ≥ 80% |
| refusal accuracy | **100.00%** (5/5) | = 100% |
| citation validity | **97.78%** (44/45) | ≥ 95% |
| disclaimer rate | **100.00%** (50/50) | — |

Evaluated on a 50-question golden set covering: speed infractions, traffic signals, documents, points system, parking, professional transport, unsafe requests (all correctly refused), ambiguous queries, and legal definitions.

---

## Known Limitations

1. **Adjacent article misses (4 of 40 recall questions):** The corpus articles 22–35 (points system) and 63/9 (documents) use overlapping vocabulary. The reranker occasionally ranks a sibling article above the most precise one.
2. **Penalty vs. rule-article ambiguity:** Some questions about prohibited behaviors (e.g. parking on bridges) return the rule-defining article rather than the penalty article. Both are legally correct answers; the golden set flags only one.
3. **Arabic corpus only:** The official text is in Arabic. French queries are translated before retrieval. Darija (Moroccan dialect) queries are not yet supported.
4. **General information only:** Answers are based on Law 52-05 as of the corpus snapshot. Regulatory amendments after the PDF publication date are not reflected.

---

## Quick Start

**Prerequisites:** Python 3.11+, Node.js 18+, Groq API key (free), OpenRouter API key (free).

1. **Clone and set up environment**
   ```bash
   git clone <repo-url> && cd dalil-route-ai
   python -m venv venv && venv/Scripts/activate  # Windows
   pip install -r backend/requirements.txt
   ```

2. **Configure secrets**
   ```bash
   cp .env.example .env
   # Edit .env: add OPENROUTER_API_KEY, GROQ_API_KEY, ADMIN_KEY
   ```

3. **Start the backend** (index is pre-built — no rebuild needed)
   ```bash
   uvicorn backend.app.main:app --reload
   # API docs: http://localhost:8000/docs
   ```

4. **Start the frontend**
   ```bash
   cd frontend
   # Create frontend/.env.local with: NEXT_PUBLIC_API_URL=http://localhost:8000
   npm install && npm run dev
   # UI: http://localhost:3000
   ```

5. **Ask a question**
   ```bash
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "Quelle est l'\''amende pour brûler un feu rouge ?"}'
   ```

---

## License

MIT

---

## Acknowledgments

- **Secrétariat Général du Gouvernement (SGG), Royaume du Maroc** — official Arabic text of Law 52-05 on road traffic
- **Ministère du Transport et de la Logistique** — regulatory context
- Corpus source: *القانون رقم 52-05 المتعلق بمدونة السير على الطرق* (Arabic consolidated text, 316 articles)
