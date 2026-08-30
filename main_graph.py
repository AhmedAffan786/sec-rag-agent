"""
Stage 4 — Main Agent Graph (now complete — all 5 nodes are real).

Manager -> (conditional routing) -> Search Agent / Drafter / Comparator

Comparator itself fans out internally into 3 independent parallel
branches (one per fixed dimension) via LangGraph's Send API, then
fans back in through comparator_aggregate before reaching END.

Run this file directly to test all 4 intent paths end-to-end:
    python main_graph.py

Requires Ollama running locally with qwen2.5:7b pulled.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from langgraph.graph import StateGraph, END

from state import AgentState
from manager import classify_intent, route_from_manager
from search_agent import search_agent_node
from drafter import drafter_node
from comparator import comparator_entry, dispatch_dimensions, compare_dimension, comparator_aggregate


def build_main_graph():
    graph = StateGraph(AgentState)

    graph.add_node("manager", classify_intent)
    graph.add_node("search_agent", search_agent_node)
    graph.add_node("drafter", drafter_node)
    graph.add_node("comparator", comparator_entry)
    graph.add_node("compare_dimension", compare_dimension)
    graph.add_node("comparator_aggregate", comparator_aggregate)

    graph.set_entry_point("manager")

    # Manager's top-level routing (Stage 2)
    graph.add_conditional_edges(
        "manager",
        route_from_manager,
        {
            "search_agent": "search_agent",
            "drafter": "drafter",
            "comparator": "comparator",
        },
    )

    # Comparator's internal fan-out (Stage 4): dispatch_dimensions returns
    # either a list of Send objects (parallel branches) or a plain string
    # (fallback straight to aggregation if no comparison is possible).
    graph.add_conditional_edges(
        "comparator",
        dispatch_dimensions,
        ["compare_dimension", "comparator_aggregate"],
    )

    # Fan-in: every compare_dimension branch feeds into the same aggregate node
    graph.add_edge("compare_dimension", "comparator_aggregate")

    graph.add_edge("search_agent", END)
    graph.add_edge("drafter", END)
    graph.add_edge("comparator_aggregate", END)

    return graph.compile()


_compiled_graph = None


def run_query(query: str) -> dict:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_main_graph()

    result = _compiled_graph.invoke({"query": query})
    return result


if __name__ == "__main__":
    test_queries = [
        "Write a new AI risk disclosure section for a fintech company",
        "Rewrite Bank of America's AI risk section for my company",
        "Compare Artificial Intelligence Technology Solutions Inc's AI disclosure against Bank of America and tell me what's missing",
        "What AI risks does Artificial Intelligence Technology Solutions Inc disclose in their filings?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"QUERY: {q}")
        print('='*70)
        result = run_query(q)
        print(f"Intent classified: {result.get('intent')}")
        print(f"\nFinal answer:\n{result.get('final_answer')}")