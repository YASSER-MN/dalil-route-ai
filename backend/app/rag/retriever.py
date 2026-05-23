from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
BM25_PATH = DATA_DIR / "bm25.pkl"
COLLECTION_NAME = "dalil_articles"
MODEL_NAME = "intfloat/multilingual-e5-small"


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    score: float
    article_number: int


def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (rank + k)


class HybridRetriever:
    def __init__(self) -> None:
        self._model = SentenceTransformer(MODEL_NAME)

        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self._collection = client.get_collection(COLLECTION_NAME)

        with open(BM25_PATH, "rb") as f:
            payload: dict[str, Any] = pickle.load(f)
        self._bm25 = payload["bm25"]
        self._corpus_tokens: list[list[str]] = payload["corpus_tokens"]
        self._article_ids: list[int] = payload["article_ids"]
        self._documents: dict[int, str] = {}

        results = self._collection.get(include=["documents", "metadatas"])
        for doc, meta in zip(results["documents"], results["metadatas"]):
            self._documents[meta["number"]] = doc

    def search(self, query: str, top_k: int = 5) -> list[Chunk]:
        fetch_k = 10

        # Vector search — e5 requires "query: " prefix
        vec = self._model.encode(
            f"query: {query}",
            normalize_embeddings=True,
        ).tolist()
        vec_results = self._collection.query(
            query_embeddings=[vec],
            n_results=fetch_k,
            include=["metadatas", "distances"],
        )
        vec_ids: list[str] = vec_results["ids"][0]

        # BM25 search — only include articles with a positive score so that
        # zero-score ties (e.g. French query vs Arabic corpus) don't pollute RRF
        query_tokens = query.split()
        bm25_scores = self._bm25.get_scores(query_tokens)
        top_bm25_indices = sorted(
            range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
        )[:fetch_k]
        bm25_ids: list[str] = [
            str(self._article_ids[i])
            for i in top_bm25_indices
            if bm25_scores[i] > 0
        ]

        # Reciprocal Rank Fusion
        rrf: dict[str, float] = {}
        for rank, article_id in enumerate(vec_ids):
            rrf[article_id] = rrf.get(article_id, 0.0) + _rrf_score(rank)
        for rank, article_id in enumerate(bm25_ids):
            rrf[article_id] = rrf.get(article_id, 0.0) + _rrf_score(rank)

        ranked = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]

        chunks: list[Chunk] = []
        for article_id_str, score in ranked:
            article_number = int(article_id_str)
            text = self._documents.get(article_number, "")
            chunks.append(
                Chunk(
                    id=article_id_str,
                    text=text,
                    score=score,
                    article_number=article_number,
                )
            )
        return chunks
