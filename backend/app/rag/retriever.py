from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer

if TYPE_CHECKING:
    from app.rag.query_translator import QueryTranslator

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
BM25_PATH = DATA_DIR / "bm25.pkl"
COLLECTION_NAME = "dalil_articles"
MODEL_NAME = "intfloat/multilingual-e5-base"
RERANKER_NAME = "BAAI/bge-reranker-v2-m3"

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    score: float
    article_number: int
    query_fr: str = ""
    query_ar: str = ""


def _rrf_score(rank: int, k: int = 60) -> float:
    return 1.0 / (rank + k)


class HybridRetriever:
    def __init__(
        self,
        translator: QueryTranslator | None = None,
        use_reranker: bool = True,
    ) -> None:
        self._translator = translator
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

        self._reranker: CrossEncoder | None = None
        if use_reranker:
            self._reranker = CrossEncoder(RERANKER_NAME, max_length=512)
            log.debug("Reranker loaded: %s", RERANKER_NAME)

    def search(
        self,
        query: str,
        top_k: int = 5,
        translate_query: bool = True,
    ) -> list[Chunk]:
        query_fr = query
        query_ar = query

        if translate_query and self._translator is not None:
            query_ar = self._translator.to_arabic(query)
            log.debug("Query translation: %r -> %r", query_fr, query_ar)

        # Fetch a wider candidate pool when reranking; 4× gives 20 for k=5
        fetch_k = top_k * 4 if self._reranker is not None else 10

        # Vector search — e5 requires "query: " prefix; use Arabic query
        vec = self._model.encode(
            f"query: {query_ar}",
            normalize_embeddings=True,
        ).tolist()
        vec_results = self._collection.query(
            query_embeddings=[vec],
            n_results=fetch_k,
            include=["metadatas", "distances"],
        )
        vec_ids: list[str] = vec_results["ids"][0]

        # BM25 — use Arabic query tokens so they match the Arabic corpus
        query_tokens = query_ar.split()
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

        fused = sorted(rrf.items(), key=lambda x: x[1], reverse=True)

        # Build candidate chunks from fused results
        candidates: list[Chunk] = []
        for article_id_str, score in fused:
            article_number = int(article_id_str)
            text = self._documents.get(article_number, "")
            candidates.append(
                Chunk(
                    id=article_id_str,
                    text=text,
                    score=score,
                    article_number=article_number,
                    query_fr=query_fr,
                    query_ar=query_ar,
                )
            )

        if self._reranker is None:
            return candidates[:top_k]

        # Cross-encoder reranking: score each (arabic_query, article_text) pair
        pairs = [(query_ar, chunk.text) for chunk in candidates]
        rerank_scores: list[float] = self._reranker.predict(pairs).tolist()

        reranked = sorted(
            zip(candidates, rerank_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [
            Chunk(
                id=c.id,
                text=c.text,
                score=float(s),
                article_number=c.article_number,
                query_fr=c.query_fr,
                query_ar=c.query_ar,
            )
            for c, s in reranked[:top_k]
        ]
