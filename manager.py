"""
Stage 2 — Manager Node.

The entry point of the main agent graph. Classifies the user's query
into one of four intents, which drives conditional routing to the
downstream nodes (Search Agent, Drafter, Disclosure Comparator).

This is the "autonomous decision-making / conditional routing"
requirement from the assignment brief.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from state import AgentState
from llm import get_llm

VALID_INTENTS = {"draft_new", "draft_adapt", "compare", "lookup"}

CLASSIFY_PROMPT = """You are a routing classifier for an SEC disclosure assistant.
Read the user's request and classify it into EXACTLY ONE of these categories:

- draft_new: user wants a brand new disclosure section written from scratch
- draft_adapt: user wants a disclosure adapted/rewritten from a peer company's example
- compare: user wants their disclosure compared against peers to find gaps or missing content
- lookup: user just wants information retrieved/answered, no drafting or comparison

Respond with ONLY the category name, nothing else. No punctuation, no explanation.

User request: {query}

Category:"""


def classify_intent(state: AgentState) -> AgentState:
    """Manager node — calls the local LLM to classify intent, with a
    strict fallback if the model returns something unexpected."""
    llm = get_llm(temperature=0.0)
    prompt = CLASSIFY_PROMPT.format(query=state["query"])

    response = llm.invoke(prompt)
    raw_intent = response.content.strip().lower()

    # Strip any stray punctuation/quotes the model might add despite instructions
    cleaned = "".join(ch for ch in raw_intent if ch.isalnum() or ch == "_")

    if cleaned in VALID_INTENTS:
        intent = cleaned
    else:
        print(f"  [warn] Manager got unexpected intent '{raw_intent}' — defaulting to 'lookup'")
        intent = "lookup"

    print(f"  [Manager] query classified as: {intent}")
    return {**state, "intent": intent}


def route_from_manager(state: AgentState) -> str:
    """Conditional edge function — tells LangGraph which node to go to
    next based on the Manager's classification."""
    intent = state.get("intent", "lookup")
    if intent in ("draft_new", "draft_adapt"):
        return "drafter"
    elif intent == "compare":
        return "comparator"
    else:
        return "search_agent"