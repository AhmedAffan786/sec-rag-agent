"""
Stage 1 — Ingestion.

Reads SEC filing PDFs, chunks the text, embeds it with a local
sentence-transformers model, and saves everything into the local
NumPy-based vector store (see vector_store.py).

No metadata.csv is used — company, form type, and CIK/date (where
present) are parsed directly from the filename, which follows this
pattern (confirmed from your actual files):

    <3-digit-index>_<COMPANY_NAME>_Form_<form_type>_<suffix>.pdf

Examples:
    001_Global_X_Funds_Form_497_ck0001432353-20260305.pdf
    004_BANK_OF_AMERICA_CORP_DE_Form_424B2_exfilingfees.pdf

Run this ONCE (or whenever your data changes):
    python ingest.py

INTEGRATION CONTRACT (read this before touching later stages):
  Every chunk stored carries this metadata dict — downstream nodes
  (Search Agent, Peer Selector, Comparator) rely on these exact keys:
      text            (str, the chunk content)
      company         (str)
      cik             (str, blank if not parseable from filename)
      form_type       (str)
      filing_date     (str, "YYYY-MM-DD", blank if not parseable)
      source_file     (str, PDF filename)
  Do not rename these keys in later stages without updating everything
  that reads them.
"""

import re
import sys
from pathlib import Path

import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

sys.path.append(str(Path(__file__).parent))
import config
import vector_store

# Matches: 001_Global_X_Funds_Form_497_ck0001432353-20260305.pdf
#          004_BANK_OF_AMERICA_CORP_DE_Form_424B2_exfilingfees.pdf
FILENAME_PATTERN = re.compile(
    r"^\d{3}_(?P<company>.+?)_Form_(?P<form_type>[A-Za-z0-9\-]+)_(?P<suffix>.+)$",
    re.IGNORECASE,
)

# Matches a CIK + date embedded in some suffixes, e.g. "ck0001432353-20260305"
CIK_DATE_PATTERN = re.compile(r"ck(?P<cik>\d+)-(?P<date>\d{8})", re.IGNORECASE)


def parse_filename_metadata(pdf_stem: str) -> dict:
    """Best-effort metadata extraction from the filename alone.
    Never raises — falls back to blanks for anything it can't parse,
    so ingestion never crashes on an unexpected filename."""
    match = FILENAME_PATTERN.match(pdf_stem)
    if not match:
        print(f"  [warn] filename didn't match expected pattern: {pdf_stem}")
        return {"company": "", "form_type": "", "cik": "", "filing_date": ""}

    company = match.group("company").replace("_", " ").replace(".", "").strip()
    form_type = match.group("form_type").strip()
    suffix = match.group("suffix")

    cik, filing_date = "", ""
    cik_match = CIK_DATE_PATTERN.search(suffix)
    if cik_match:
        cik = cik_match.group("cik")
        raw_date = cik_match.group("date")  # YYYYMMDD
        filing_date = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

    return {
        "company": company,
        "form_type": form_type,
        "cik": cik,
        "filing_date": filing_date,
    }


def simple_chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Plain sliding-window chunker — no extra dependency needed."""
    if not text.strip():
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def build_chunks() -> list[dict]:
    pdf_files = sorted(config.PDF_DIR.glob("*.pdf"))  # .html files are ignored — non-recursive glob, extension-filtered
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {config.PDF_DIR}")

    print(f"Found {len(pdf_files)} PDFs to ingest (any .html files in the same folder are skipped).")
    all_chunks: list[dict] = []

    for pdf_path in pdf_files:
        print(f"Processing {pdf_path.name} ...")
        try:
            reader = PdfReader(str(pdf_path))
            full_text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"  [error] failed to load {pdf_path.name}: {e}")
            continue

        meta = parse_filename_metadata(pdf_path.stem)
        chunks = simple_chunk_text(full_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)

        for i, chunk_text in enumerate(chunks):
            all_chunks.append({
                "text": chunk_text,
                "company": meta["company"],
                "cik": meta["cik"],
                "form_type": meta["form_type"],
                "filing_date": meta["filing_date"],
                "source_file": pdf_path.name,
                "chunk_index": i,
            })

    print(f"Built {len(all_chunks)} chunks from {len(pdf_files)} PDFs.")
    return all_chunks


def main():
    chunks = build_chunks()

    print(f"Loading embedding model: {config.EMBEDDING_MODEL_NAME} ...")
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)

    print(f"Embedding {len(chunks)} chunks (this may take a few minutes) ...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(
        texts, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True
    ).astype(np.float32)

    vector_store.save(embeddings, chunks)

    print(f"Done. Vector store saved to: {config.VECTOR_STORE_DIR}")
    print(f"{len(chunks)} chunks embedded and stored.")

    # Quick sanity summary
    companies = sorted(set(c["company"] for c in chunks if c["company"]))
    print(f"\nParsed {len(companies)} distinct companies, e.g.: {companies[:5]}")


if __name__ == "__main__":
    main()