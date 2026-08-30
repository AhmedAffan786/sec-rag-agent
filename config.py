"""
Shared configuration for the whole project.
Every stage imports from here so paths/model names only need to change in ONE place.
"""

from pathlib import Path

# -----------------------------------------------------------------------
# DATA PATHS
# -----------------------------------------------------------------------
# Folder containing the SEC filing PDFs (and .html files, which are
# ignored — ingest.py only globs *.pdf). No metadata.csv is used —
# company/form-type/CIK are parsed directly from filenames instead.
PDF_DIR = Path(__file__).parent / "Data"

# Where the local NumPy-based vector store persists its data.
VECTOR_STORE_DIR = Path(__file__).parent / "Data" / "vector_store"
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
EMBEDDINGS_FILE = VECTOR_STORE_DIR / "embeddings.npz"
METADATA_FILE = VECTOR_STORE_DIR / "chunk_metadata.pkl"

# -----------------------------------------------------------------------
# MODELS
# -----------------------------------------------------------------------
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

OLLAMA_MODEL_NAME = "qwen2.5:7b"
# "host.docker.internal" lets a container reach services running on the
# host machine (your Windows PC, where Ollama runs). Set via an
# environment variable so it still works with plain `python` outside
# Docker too (falls back to localhost).
import os
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

# -----------------------------------------------------------------------
# CHUNKING
# -----------------------------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# -----------------------------------------------------------------------
# RETRIEVAL
# -----------------------------------------------------------------------
RETRIEVE_TOP_K = 8
RERANK_TOP_N = 4

# Below this reranker score, a result is treated as "not actually
# relevant" and dropped rather than used anyway. The cross-encoder
# reranker centers roughly around 0; negative scores mean the model
# judged the text as a poor match for the query.
MIN_RERANK_SCORE = 0.0