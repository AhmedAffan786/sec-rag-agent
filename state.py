"""
Shared state schema for the MAIN agent graph (Manager -> Search/Drafter/
Comparator/Peer Selector). Separate from RAGState in rag_subgraph.py.

INTEGRATION CONTRACT — every node in every stage reads/writes this same
shape. Do not rename or remove a key without checking every node that
uses it. `total=False` means a key can be absent until a node fills it in.

NOTE (Stage 4): gaps_found uses Annotated[..., operator.add] because the
Disclosure Comparator fans out into parallel branches (one per
dimension) using LangGraph's Send API — each branch returns its own
partial list, and this annotation tells LangGraph to CONCATENATE those
lists together instead of overwriting each other. Every other field is
written by only one node at a time, so they don't need this.
"""

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    query: str                  # the user's raw question/request

    intent: str                 # set by Manager: "draft_new" | "draft_adapt" | "compare" | "lookup"

    draft_mode: str              # used by Drafter: "new" | "adapt"
    peer_ciks: list[str]         # filled by Peer Selector tool when relevant

    target_company: str          # Comparator: the company being evaluated
    peer_company: str            # Comparator: the peer being compared against
    subtasks: list[str]          # Comparator's fixed dimensions when it fans out:
                                  # ["risk_factors", "forward_looking_statements", "financial_metrics"]
    current_dimension: str       # transient — set inside each parallel Comparator branch

    search_results: list[dict]   # accumulated results from Search Agent / RAG subgraph calls
    gaps_found: Annotated[list[dict], operator.add]  # Comparator's per-dimension findings (merged across parallel branches)
    draft_output: str            # Drafter's generated text

    final_answer: str            # what actually gets shown to the user at the end