"""
FAISS-based local vector store.

Uses faiss.IndexFlatIP (exact inner-product search — equivalent to
cosine similarity since all embeddings are L2-normalized before being
stored/queried) for the UNFILTERED search case (general lookups across
the whole corpus) — this is where FAISS's speed actually helps.

For company-FILTERED searches (used heavily by Drafter/Comparator),
we still do a small brute-force NumPy search over just that company's
vectors — the filtered subset is tiny (a handful of chunks per
company), so FAISS adds no benefit there and this keeps the exact
same filtering logic that was already tested and fixed.

INTEGRATION CONTRACT — unchanged from the NumPy version:
  save(embeddings, metadatas) / load() / search(query_embedding, k, company_filter=None)
  same signatures, same return shape. ingest.py and rag_subgraph.py
  require NO changes because of this.
"""

import pickle
import numpy as np
import faiss

import config

_FAISS_INDEX_FILE = None  # set below, derived from config


def _faiss_index_path():
    return config.EMBEDDINGS_FILE.with_suffix(".faiss")


def save(embeddings: np.ndarray, metadatas: list[dict]) -> None:
    """Persist embeddings + metadata to disk — both a FAISS index (for
    fast unfiltered search) and the raw embeddings array (for
    company-filtered brute-force search)."""
    embeddings = embeddings.astype(np.float32)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, str(_faiss_index_path()))

    np.savez_compressed(config.EMBEDDINGS_FILE, embeddings=embeddings)
    with open(config.METADATA_FILE, "wb") as f:
        pickle.dump(metadatas, f)


def load() -> tuple:
    """Returns (faiss_index, embeddings_array, metadatas_list)."""
    if not config.METADATA_FILE.exists() or not _faiss_index_path().exists():
        raise FileNotFoundError(
            "No vector store found. Run `python ingest.py` first."
        )
    index = faiss.read_index(str(_faiss_index_path()))
    data = np.load(config.EMBEDDINGS_FILE)
    embeddings = data["embeddings"]
    with open(config.METADATA_FILE, "rb") as f:
        metadatas = pickle.load(f)
    return index, embeddings, metadatas


def _cosine_similarity(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """Used only for the company-filtered brute-force path."""
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norms = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    return matrix_norms @ query_norm


def search(query_embedding: np.ndarray, k: int, company_filter: str | None = None) -> list[dict]:
    index, embeddings, metadatas = load()

    if company_filter:
        target = company_filter.strip().lower()
        keep_indices = [
            i for i, m in enumerate(metadatas)
            if m.get("company", "").strip().lower() == target
        ]
        if not keep_indices:
            return []

        sub_matrix = embeddings[keep_indices]
        scores = _cosine_similarity(query_embedding, sub_matrix)
        top_local = np.argsort(scores)[::-1][:k]

        results = []
        for local_idx in top_local:
            global_idx = keep_indices[local_idx]
            item = dict(metadatas[global_idx])
            item["score"] = float(scores[local_idx])
            results.append(item)
        return results

    # Unfiltered — use FAISS for the full-corpus search
    q = query_embedding.astype(np.float32).reshape(1, -1)
    faiss.normalize_L2(q)  # safety net; embeddings are already normalized at encode time
    scores, indices = index.search(q, k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        item = dict(metadatas[idx])
        item["score"] = float(score)
        results.append(item)
    return results