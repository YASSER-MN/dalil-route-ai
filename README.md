# Dalil Route AI

An evidence-first LegalTech RAG system for the Moroccan Code de la Route (Law 52-05).

> **Disclaimer:** This tool provides general legal information only. It is not legal advice. Always consult an official source or qualified professional for binding legal guidance.

---

## What it does

Dalil Route AI lets you ask questions about Moroccan traffic law in French and get answers grounded in specific articles from Law 52-05. Every answer cites the exact article(s) it draws from — no hallucinated references.

---

## Setup (developer)

_Full setup instructions will be completed in Phase 7. See `PLAN.md` for current status._

---

## Architecture

```
PDF → Parser → ChromaDB + BM25 → Hybrid Retriever → Groq LLM → Validator → FastAPI → Next.js
```

See `CLAUDE.md` for the full tech stack and `PLAN.md` for build status.
