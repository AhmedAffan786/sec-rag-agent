"""
Stage 4 — Drafter Node.

Two modes, decided by the Manager's intent classification:
  - "new"   : draft a disclosure section from scratch. No peer basis
              needed, so this mode SKIPS Search entirely — this is the
              "Drafter autonomously decides whether it needs to search"
              behavior described in the architecture.
  - "adapt" : find a peer company mentioned in the query, retrieve their
              comparable disclosure via the RAG subgraph (Search Agent's
              underlying subgraph), and adapt/rewrite it for the user's
              own company.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from state import AgentState
from llm import get_llm
from rag_subgraph import run_rag_subgraph
from peer_selector import find_companies_in_text

DRAFT_NEW_PROMPT = """You are a legal/compliance drafting assistant helping write an SEC disclosure section.

Write a new, professional disclosure section addressing the following request. 
Follow standard SEC disclosure conventions (clear, factual, hedged language for forward-looking statements). 

Use "[Your Company]" as a placeholder for the company name since none was given.

Request: {query}

Draft:"""

DRAFT_ADAPT_PROMPT = """You are a legal/compliance drafting assistant. Below is disclosure language from a peer 
company's SEC filing. 
Adapt and rewrite it as a new disclosure section for a different company, based on the user's request. 
Keep the professional SEC disclosure tone and structure, but do not simply copy verbatim — reword it 
and use "[Your Company]" as a placeholder for the company name.

Peer company reference text ({peer_company}):
{peer_text}

User's request: {query}

Adapted draft:"""

DRAFT_FROM_SELECTED_PROMPT = """You are a legal/compliance drafting assistant. 
Below are one or more excerpts the user hand-picked from SEC filings as reference material.
 Use ONLY these excerpts as your source — draft a new disclosure section based on the user's instruction, 
 in professional SEC disclosure tone. Reword rather than copy verbatim, and use "[Your Company]" as a placeholder 
 for the company name.

Selected reference excerpts:
{snippets}

User's instruction: {instruction}

Draft:"""


def _find_mentioned_company(query: str) -> str | None:
    """Best-effort match: does any known company name appear in the
    user's query (full name or a shortened prefix)? Used to figure out
    which peer to base an 'adapt' draft on."""
    found = find_companies_in_text(query)
    return found[0][1] if found else None


def drafter_node(state: AgentState) -> AgentState:
    query = state["query"]
    mode = "adapt" if state.get("intent") == "draft_adapt" else "new"
    llm = get_llm(temperature=0.4)  # a bit of creativity is appropriate for drafting

    if mode == "new":
        print("  [Drafter] mode=new — skipping search, drafting directly")
        prompt = DRAFT_NEW_PROMPT.format(query=query)
        response = llm.invoke(prompt)
        draft = response.content.strip()
        return {**state, "draft_mode": mode, "draft_output": draft, "final_answer": draft}

    # mode == "adapt"
    peer_company = _find_mentioned_company(query)

    if not peer_company:
        print("  [Drafter] mode=adapt, but no peer company found in query — falling back to new-draft style")
        prompt = DRAFT_NEW_PROMPT.format(query=query)
        response = llm.invoke(prompt)
        draft = response.content.strip()
        note = "(No specific peer company was recognized in the request, so this was drafted from scratch.)\n\n"
        return {**state, "draft_mode": mode, "draft_output": draft, "final_answer": note + draft}

    print(f"  [Drafter] mode=adapt — found peer '{peer_company}', retrieving their disclosure text (filtered to this company only)")
    rag_output = run_rag_subgraph(
        f"artificial intelligence disclosure risk",
        company_filter=peer_company,
    )
    results = rag_output["results"]

    if not results:
        print(f"  [Drafter] no relevant text found for '{peer_company}' — falling back to new-draft style")
        prompt = DRAFT_NEW_PROMPT.format(query=query)
        response = llm.invoke(prompt)
        draft = response.content.strip()
        note = f"(No sufficiently relevant disclosure text was found for {peer_company}, so this was drafted from scratch instead.)\n\n"
        return {**state, "draft_mode": mode, "draft_output": draft, "final_answer": note + draft}

    prompt = DRAFT_ADAPT_PROMPT.format(peer_company=peer_company, peer_text=results[0]["text"], query=query)
    response = llm.invoke(prompt)
    draft = response.content.strip()

    return {
        **state,
        "draft_mode": mode,
        "peer_ciks": [r.get("cik", "") for r in results if r.get("cik")],
        "search_results": results,
        "draft_output": draft,
        "final_answer": draft,
    }


def draft_from_selected(snippets: list[dict], instruction: str) -> str:
    """User-driven drafting: instead of the agent automatically deciding
    what to retrieve, the user has already picked specific snippets from
    a search (via the UI's checkbox selection) and this drafts using
    ONLY those, ignoring anything else in the corpus."""
    llm = get_llm(temperature=0.4)

    snippet_text = "\n\n".join(
        f"[{s['company']} | {s['form_type']}]\n{s['text']}"
        for s in snippets
    )

    prompt = DRAFT_FROM_SELECTED_PROMPT.format(snippets=snippet_text, instruction=instruction)
    response = llm.invoke(prompt)
    return response.content.strip()