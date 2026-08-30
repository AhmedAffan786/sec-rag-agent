"""
Lightweight local vector store — NumPy only, no C-extension vector DB.

Why this exists instead of Chroma/FAISS: as of this writing, ChromaDB
cannot install cleanly on Python 3.14 (its onnxruntime/hnswlib dependencies
don't yet ship 3.14 wheels), and FAISS has no confirmed cp314 Windows wheel
either. For a corpus of this size (a few thousand chunks from ~79 filings),
a brute-force cosine-similarity search in NumPy is more than fast enough
and has zero compiled-dependency risk.

INTEGRATION CONTRACT — do not change these shapes without updating callers:
  - save(embeddings, metadatas) persists to disk
  - load() returns (embeddings: np.ndarray [N, D], metadatas: list[dict])
  - search(query_embedding, k) returns list[dict] with a "score" key added,
    sorted descending by score (cosine similarity)
"""

import pickle
import numpy as np

import config


def save(embeddings: np.ndarray, metadatas: list[dict]) -> None:
    """Persist embeddings + their metadata to disk."""
    np.savez_compressed(config.EMBEDDINGS_FILE, embeddings=embeddings)
    with open(config.METADATA_FILE, "wb") as f:
        pickle.dump(metadatas, f)


def load() -> tuple[np.ndarray, list[dict]]:
    """Load embeddings + metadata from disk. Raises FileNotFoundError if
    ingestion hasn't been run yet."""
    if not config.EMBEDDINGS_FILE.exists() or not config.METADATA_FILE.exists():
        raise FileNotFoundError(
            "No vector store found. Run `python ingest.py` first."
        )
    data = np.load(config.EMBEDDINGS_FILE)
    embeddings = data["embeddings"]
    with open(config.METADATA_FILE, "rb") as f:
        metadatas = pickle.load(f)
    return embeddings, metadatas


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Vectorized cosine similarity between one query vector and every
    row in the matrix. Returns a 1D array of scores."""
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norms = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return matrix_norms @ query_norm


def search(query_embedding: np.ndarray, k: int, company_filter: str | None = None) -> list[dict]:
    """Return the top-k most similar chunks to the query embedding.

    If company_filter is given, ONLY searches chunks belonging to that
    company (case-insensitive exact match on the stored 'company'
    metadata) — this prevents a dominant company in the dataset from
    "winning" retrieval for a query that's actually about someone else.
    Returns an empty list if the filter matches nothing, rather than
    silently falling back to unrelated companies.
    """
    embeddings, metadatas = load()

    if company_filter:
        target = company_filter.strip().lower()
        keep_indices = [
            i for i, m in enumerate(metadatas)
            if m.get("company", "").strip().lower() == target
        ]
        if not keep_indices:
            return []
        embeddings = embeddings[keep_indices]
        metadatas = [metadatas[i] for i in keep_indices]

    scores = _cosine_similarity(query_embedding, embeddings)
    top_indices = np.argsort(scores)[::-1][:k]

    results = []
    for idx in top_indices:
        item = dict(metadatas[idx])
        item["score"] = float(scores[idx])
        results.append(item)
    return results