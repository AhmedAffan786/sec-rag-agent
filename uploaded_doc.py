"""
Runtime document upload — lets the user upload a SEC filing PDF at
query time, chunk + embed it ON THE FLY (in memory only, nothing saved
to disk or added to the permanent vector store), and question or draft
from that single document specifically.

This is fully separate from the main 79-filing corpus — a fresh,
temporary, per-session index, not persisted anywhere.
"""

import io
import numpy as np
import pdfplumber
from sentence_transformers import SentenceTransformer

import config

CHUNK_SIZE = config.CHUNK_SIZE
CHUNK_OVERLAP = config.CHUNK_OVERLAP

_embedding_model = None


def _get_embedding_model():
    # Reuses the SAME model as the main corpus (same embedding space),
    # loaded once and cached — no need to load it twice.
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _embedding_model


def extract_text(uploaded_file) -> str:
    """uploaded_file is a Streamlit UploadedFile object (file-like).
    Uses pdfplumber with layout=True, which respects visual column
    order much better than a raw stream-order extractor — important
    for multi-column documents (resumes, some academic papers) where
    naive extraction interleaves left/right column text mid-sentence."""
    with pdfplumber.open(io.BytesIO(uploaded_file.getvalue())) as pdf:
        pages_text = [page.extract_text(layout=True) or "" for page in pdf.pages]
    return "\n".join(pages_text)


def chunk_text(text: str) -> list[str]:
    """Same simple sliding-window chunker used in ingest.py."""
    if not text.strip():
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed_and_index(uploaded_file, filename: str) -> dict:
    """Extracts, chunks, and embeds an uploaded PDF. Returns a small
    in-memory index dict — nothing is written to disk."""
    text = extract_text(uploaded_file)
    chunks = chunk_text(text)

    if not chunks:
        return {"filename": filename, "chunks": [], "embeddings": None}

    model = _get_embedding_model()
    embeddings = model.encode(chunks, convert_to_numpy=True, normalize_embeddings=True).astype(np.float32)

    return {"filename": filename, "chunks": chunks, "embeddings": embeddings}


def search(index: dict, query: str, k: int = 4) -> list[dict]:
    """Search within ONE uploaded document's temporary index.

    Two-stage, same as the main RAG subgraph: broad cosine-similarity
    retrieval first, THEN rerank with a cross-encoder for precision.
    Plain cosine similarity alone is not precise enough — especially
    on short documents, where the right chunk can rank just outside a
    narrow top-k cutoff. For a small uploaded doc, this effectively
    considers nearly the whole document before narrowing down.
    """
    if not index["chunks"]:
        return []

    model = _get_embedding_model()
    query_vec = model.encode(query, normalize_embeddings=True)

    matrix = index["embeddings"]
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    matrix_norms = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10)
    scores = matrix_norms @ query_norm

    retrieve_n = min(len(index["chunks"]), max(k * 3, 10))
    top_indices = np.argsort(scores)[::-1][:retrieve_n]
    candidates = [(idx, index["chunks"][idx]) for idx in top_indices]

    from rag_subgraph import _get_reranker  # reuse the same cached model, don't load twice
    reranker = _get_reranker()
    pairs = [(query, text) for _, text in candidates]
    rerank_scores = reranker.predict(pairs)

    ranked = sorted(zip(candidates, rerank_scores), key=lambda x: x[1], reverse=True)[:k]

    results = []
    for (idx, text), score in ranked:
        results.append({
            "text": text,
            "score": float(score),
            "company": "Uploaded document",
            "form_type": index["filename"],
            "filing_date": "",
            "source_file": index["filename"],
        })
    return results