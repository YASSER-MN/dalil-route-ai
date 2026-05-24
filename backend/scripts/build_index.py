from __future__ import annotations

import json
import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_PATH = DATA_DIR / "articles.json"
CHROMA_DIR = DATA_DIR / "chroma_db"
BM25_PATH = DATA_DIR / "bm25.pkl"
COLLECTION_NAME = "dalil_articles"
MODEL_NAME = "intfloat/multilingual-e5-base"
BATCH_SIZE = 64


def load_articles() -> list[dict]:
    with open(ARTICLES_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_chroma_index(articles: list[dict], model: SentenceTransformer) -> None:
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Drop and recreate to allow idempotent re-runs
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict] = []

    for a in articles:
        ids.append(str(a["number"]))
        texts.append(a["text"])
        metadatas.append({"number": a["number"], "source": a["source"]})

    print(f"Encoding {len(texts)} passages with '{MODEL_NAME}'…")
    # e5 requires "passage: " prefix for documents
    prefixed = [f"passage: {t}" for t in texts]

    embeddings = model.encode(
        prefixed,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        normalize_embeddings=True,
    ).tolist()

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"ChromaDB: {collection.count()} vectors stored -> {CHROMA_DIR}")


def build_bm25_index(articles: list[dict]) -> None:
    corpus_tokens: list[list[str]] = []
    article_ids: list[int] = []

    for a in articles:
        tokens = a["text"].split()
        corpus_tokens.append(tokens)
        article_ids.append(a["number"])

    bm25 = BM25Okapi(corpus_tokens)

    payload = {
        "bm25": bm25,
        "corpus_tokens": corpus_tokens,
        "article_ids": article_ids,
    }
    with open(BM25_PATH, "wb") as f:
        pickle.dump(payload, f)
    print(f"BM25: index pickled -> {BM25_PATH}")


def _index_already_built(expected_count: int) -> bool:
    """Return True if ChromaDB and BM25 already match the corpus — skip rebuild."""
    if not CHROMA_DIR.exists() or not BM25_PATH.exists():
        return False
    try:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = client.get_collection(COLLECTION_NAME)
        return collection.count() == expected_count
    except Exception:
        return False


def main() -> None:
    articles = load_articles()
    print(f"Loaded {len(articles)} articles from {ARTICLES_PATH}")

    if _index_already_built(len(articles)):
        print(f"Index already built ({len(articles)} docs in ChromaDB + BM25 present) — skipping.")
        return

    model = SentenceTransformer(MODEL_NAME)
    print(f"Model loaded: {MODEL_NAME}")

    build_chroma_index(articles, model)
    build_bm25_index(articles)

    print("Done — index build complete.")


if __name__ == "__main__":
    main()
