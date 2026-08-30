"""
Stage 3 — Search Agent Node.

Replaces the Stage 2 stub with real logic: calls the Stage 1 RAG
subgraph to retrieve relevant chunks, then asks the LLM to synthesize
a grounded answer FROM those chunks only (not from the model's own
general knowledge) — this is what makes it "RAG" and not just a raw
LLM call.

This is a SHARED node — Manager can route here directly for plain
lookups, and Drafter/Comparator (Stage 4) will also call this same
function whenever they need retrieved context.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from state import AgentState
from llm import get_llm
from rag_subgraph import run_rag_subgraph

ANSWER_PROMPT = """You are an assistant answering questions about SEC filings, using ONLY the context below. Do not use any outside knowledge.

If the context does not contain enough information to answer, say so plainly — do not guess or make up information.

When you state a fact, mention which company and filing it came from.

Context:
{context}

Question: {query}

Answer:"""


def _format_context(results: list[dict]) -> str:
    """Turn RAG subgraph results into a labeled context block the LLM
    can cite from."""
    if not results:
        return "(No relevant filing text was found.)"

    blocks = []
    for i, r in enumerate(results, 1):
        blocks.append(
            f"[Source {i} — {r['company']} | {r['form_type']} | {r['filing_date'] or 'date unknown'}]\n"
            f"{r['text']}"
        )
    return "\n\n".join(blocks)


def search_agent_node(state: AgentState) -> AgentState:
    """Real Search Agent — retrieves via the RAG subgraph, then
    generates a grounded answer from the retrieved chunks."""
    query = state["query"]
    print(f"  [Search Agent] retrieving for: '{query}'")

    rag_output = run_rag_subgraph(query)
    results = rag_output["results"]

    context = _format_context(results)
    llm = get_llm(temperature=0.1)  # low but not zero — natural language synthesis, still grounded
    prompt = ANSWER_PROMPT.format(context=context, query=query)

    response = llm.invoke(prompt)
    answer = response.content.strip()

    print(f"  [Search Agent] generated answer ({len(results)} sources used)")

    return {
        **state,
        "search_results": results,
        "final_answer": answer,
    }