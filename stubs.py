"""
Stage 2 — Temporary stub nodes.

These stand in for Search Agent (Stage 3), Drafter (Stage 4), and
Disclosure Comparator (Stage 4) so the FULL graph can run end-to-end
today and prove the Manager's routing actually works, before we build
each node's real logic.

Each stub just records that it was reached and produces a placeholder
final_answer. They will be replaced node-by-node in later stages —
their function names ("search_agent", "drafter", "comparator") are
already the real node names the main graph will keep using, so nothing
about the graph wiring changes later, only what's inside each function.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from state import AgentState


def search_agent_stub(state: AgentState) -> AgentState:
    print("  [STUB] search_agent reached")
    answer = f"[STUB: search_agent] Would run RAG retrieval for: '{state['query']}'"
    return {**state, "final_answer": answer}


def drafter_stub(state: AgentState) -> AgentState:
    print("  [STUB] drafter reached")
    mode = "adapt" if state.get("intent") == "draft_adapt" else "new"
    answer = f"[STUB: drafter, mode={mode}] Would draft a disclosure for: '{state['query']}'"
    return {**state, "draft_mode": mode, "final_answer": answer}


def comparator_stub(state: AgentState) -> AgentState:
    print("  [STUB] comparator reached")
    answer = f"[STUB: comparator] Would run 3-dimension gap analysis for: '{state['query']}'"
    return {**state, "final_answer": answer}