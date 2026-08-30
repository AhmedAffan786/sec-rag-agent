"""
Stage 1 — RAG Subgraph.

This is the "dedicated, modular RAG subgraph" required by the assignment.
It does NOT count toward the main graph's 5-node minimum — it is invoked
BY the main graph's Search Agent node (built in Stage 3).

Pipeline: embed_query -> retrieve -> rerank -> contextualize -> return

Uses the local NumPy-based vector store (vector_store.py) instead of
Chroma/FAISS — see that file's docstring for why.

INTEGRATION CONTRACT (read this before building Stage 2+):
  from rag_subgraph import run_rag_subgraph
  result = run_rag_subgraph("What AI risk factors does Company X disclose?")
  # result is a dict: {"query": str, "results": list[dict]}
  # each item in result["results"] has:
  #     "text": str
  #     "score": float          (rerank score, higher = more relevant)
  #     "company": str
  #     "filing_date": str
  #     "form_type": str
  #     "source_file": str

  This shape must NOT change without updating every node that calls it.
"""

import sys
from pathlib import Path
from typing import TypedDict

from sentence_transformers import SentenceTransformer, CrossEncoder
from langgraph.graph import StateGraph, END

sys.path.append(str(Path(__file__).parent))
import config
import vector_store

# -----------------------------------------------------------------------
# Lazy-loaded singletons
# -----------------------------------------------------------------------
_embedding_model = None
_reranker = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _embedding_model


def _get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


# -----------------------------------------------------------------------
# Subgraph state
# -----------------------------------------------------------------------
class RAGState(TypedDict):
    query: str
    company_filter: str | None
    retrieved: list
    reranked: list
    results: list


# -----------------------------------------------------------------------
# Nodes
# -----------------------------------------------------------------------
def embed_and_retrieve(state: RAGState) -> RAGState:
    model = _get_embedding_model()
    query_embedding = model.encode(state["query"], normalize_embeddings=True)
    docs = vector_store.search(
        query_embedding,
        k=config.RETRIEVE_TOP_K,
        company_filter=state.get("company_filter"),
    )
    return {**state, "retrieved": docs}


def rerank(state: RAGState) -> RAGState:
    docs = state["retrieved"]
    if not docs:
        return {**state, "reranked": []}

    reranker = _get_reranker()
    pairs = [(state["query"], d["text"]) for d in docs]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
    top = ranked[: config.RERANK_TOP_N]
    return {**state, "reranked": top}


def contextualize(state: RAGState) -> RAGState:
    """Attach source metadata to each surviving chunk. The relevance
    floor (MIN_RERANK_SCORE) is only applied when there's NO company
    filter — that's the scenario where a low score can mean "wrong
    company got matched." When a company_filter IS set, we've already
    guaranteed correctness of source (only that company's chunks were
    searched), so a mediocre score just means the fixed query phrasing
    wasn't a perfect match — not a reason to discard the company's own
    text entirely."""
    apply_floor = not state.get("company_filter")
    results = []
    for doc, score in state["reranked"]:
        if apply_floor and score < config.MIN_RERANK_SCORE:
            continue
        results.append({
            "text": doc["text"],
            "score": float(score),
            "company": doc.get("company", ""),
            "filing_date": doc.get("filing_date", ""),
            "form_type": doc.get("form_type", ""),
            "source_file": doc.get("source_file", ""),
        })
    return {**state, "results": results}


# -----------------------------------------------------------------------
# Build the subgraph
# -----------------------------------------------------------------------
def build_rag_subgraph():
    graph = StateGraph(RAGState)
    graph.add_node("embed_and_retrieve", embed_and_retrieve)
    graph.add_node("rerank", rerank)
    graph.add_node("contextualize", contextualize)

    graph.set_entry_point("embed_and_retrieve")
    graph.add_edge("embed_and_retrieve", "rerank")
    graph.add_edge("rerank", "contextualize")
    graph.add_edge("contextualize", END)

    return graph.compile()


_compiled_subgraph = None


def run_rag_subgraph(query: str, company_filter: str | None = None) -> dict:
    """Public entry point — this is what Stage 3's Search Agent (and
    Drafter/Comparator) call. Pass company_filter to restrict retrieval
    to one specific company's chunks only."""
    global _compiled_subgraph
    if _compiled_subgraph is None:
        _compiled_subgraph = build_rag_subgraph()

    final_state = _compiled_subgraph.invoke({
        "query": query,
        "company_filter": company_filter,
        "retrieved": [],
        "reranked": [],
        "results": [],
    })
    return {"query": query, "results": final_state["results"]}


if __name__ == "__main__":
    test_query = "What risks does the company disclose related to artificial intelligence?"
    output = run_rag_subgraph(test_query)
    print(f"\nQuery: {output['query']}\n")
    for i, r in enumerate(output["results"], 1):
        print(f"--- Result {i} (score={r['score']:.3f}) ---")
        print(f"Company: {r['company']} | Date: {r['filing_date']} | Form: {r['form_type']}")
        print(r["text"][:300], "...\n")