"""
Stage 3 — Peer Selector Tool.

This is the assignment's REQUIRED non-retrieval tool: a structured
filter over filing metadata (company, form type, CIK, date) — no
embeddings, no vector search, just plain filtering logic. This is what
Drafter and Comparator (Stage 4) will call to find "peer" companies
before asking Search Agent to retrieve their actual filing text.

Since there's no metadata.csv, this reuses the same metadata that
ingest.py already parsed from filenames and saved into the vector
store's chunk_metadata.pkl — no new data source needed.

INTEGRATION CONTRACT:
  from peer_selector import select_peers, list_companies
  peers = select_peers(company="Bank Of America Corp De", max_peers=3)
  # -> list[dict], each: {"company": str, "form_type": str,
  #                        "cik": str, "filing_date": str, "source_file": str}
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
import vector_store


def load_filing_index() -> list[dict]:
    """Deduplicate the per-chunk metadata down to one entry per filing
    (per source_file), since ingest.py stores metadata redundantly on
    every chunk of the same PDF."""
    _, _, metadatas = vector_store.load()

    seen_files = set()
    index = []
    for m in metadatas:
        source_file = m.get("source_file", "")
        if source_file in seen_files:
            continue
        seen_files.add(source_file)
        index.append({
            "company": m.get("company", ""),
            "form_type": m.get("form_type", ""),
            "cik": m.get("cik", ""),
            "filing_date": m.get("filing_date", ""),
            "source_file": source_file,
        })
    return index


def list_companies() -> list[str]:
    """All distinct company names in the dataset."""
    index = load_filing_index()
    return sorted(set(entry["company"] for entry in index if entry["company"]))


def _prefix_variants(company: str) -> list[str]:
    """Progressively shorter prefixes of a company name, so 'Bank of
    America' still matches the stored 'BANK OF AMERICA CORP DE' even
    though the corporate suffix was dropped in casual phrasing."""
    words = company.lower().split()
    return [" ".join(words[:n]) for n in range(len(words), 1, -1)]


def find_companies_in_text(text: str) -> list[tuple[int, str]]:
    """Find every known company mentioned in the given text, matching
    on the full name OR a shortened prefix (handles dropped suffixes
    like 'Corp DE', 'Inc.'). Returns (position, company) tuples sorted
    by where they first appear in the text — used by Drafter and
    Comparator to figure out which companies the user is talking about."""
    text_lower = text.lower()
    found = []
    for company in list_companies():
        best_pos = None
        for variant in _prefix_variants(company):
            idx = text_lower.find(variant)
            if idx != -1 and (best_pos is None or idx < best_pos):
                best_pos = idx
        if best_pos is not None:
            found.append((best_pos, company))
    found.sort(key=lambda x: x[0])
    return found


def select_peers(
    company: str,
    form_type: str | None = None,
    max_peers: int = 5,
) -> list[dict]:
    """Find peer filings — same form_type if given, excluding the
    target company itself. Deduplicated by company (one representative
    filing per peer company).

    This is the non-retrieval tool: pure structured filtering over
    metadata, no embeddings or similarity search involved.
    """
    index = load_filing_index()
    company_lower = company.strip().lower()

    candidates = [
        entry for entry in index
        if entry["company"].strip().lower() != company_lower
        and entry["company"]  # skip blanks
    ]

    if form_type:
        form_type_lower = form_type.strip().lower()
        filtered = [c for c in candidates if c["form_type"].strip().lower() == form_type_lower]
        # Fall back to unfiltered candidates if the form_type filter is too narrow
        candidates = filtered if filtered else candidates

    seen_companies = set()
    peers = []
    for entry in candidates:
        if entry["company"] in seen_companies:
            continue
        seen_companies.add(entry["company"])
        peers.append(entry)
        if len(peers) >= max_peers:
            break

    return peers


if __name__ == "__main__":
    # Quick manual test — run: python peer_selector.py
    companies = list_companies()
    print(f"Found {len(companies)} distinct companies in the dataset:")
    for c in companies:
        print(f"  - {c}")

    if companies:
        target = companies[0]
        print(f"\nFinding peers for: '{target}'")
        peers = select_peers(target, max_peers=3)
        for p in peers:
            print(f"  - {p['company']} (form: {p['form_type']}, file: {p['source_file']})")