"""
LLM & Prompt-Focused Evaluation Set (secondary, deeper eval).

The original eval_set.py (15 questions) tests ROUTING accuracy — does
the Manager pick the right intent. This set tests something different:
does each PROMPT actually produce correct behavior once routed —
refusal on missing info, paraphrase robustness, and structural
correctness (e.g. all 3 comparator dimensions actually firing).

Each case has an automatable `check` function alongside the expected
intent, so results aren't just "did it run" but "did it behave right."
"""

CASES = [
    {
        "name": "Refusal on missing info",
        "query": "What blockchain risks does Bank of America disclose?",
        "expected_intent": "lookup",
        "check": lambda r: any(
            phrase in r.get("final_answer", "").lower()
            for phrase in ["does not contain", "no information", "not mention", "does not disclose", "not found"]
        ),
        "check_description": "Answer should say the info isn't in the context, not invent an answer.",
    },
    {
        "name": "Paraphrase robustness — draft_new",
        "query": "I want to create fresh AI disclosure text for a healthcare startup",
        "expected_intent": "draft_new",
        "check": lambda r: "[Your Company]" in r.get("final_answer", ""),
        "check_description": "Should use the placeholder, confirming it drafted from scratch correctly.",
    },
    {
        "name": "Paraphrase robustness — draft_adapt",
        "query": "Use NOCERA INC's filing as a base and rewrite it for us",
        "expected_intent": "draft_adapt",
        "check": lambda r: len(r.get("search_results", [])) > 0,
        "check_description": "Should have actually retrieved NOCERA's text, not fallen back to a blank draft.",
    },
    {
        "name": "Paraphrase robustness — compare",
        "query": "How does Eightco Holdings Inc's AI disclosure differ from Cuentas Inc's?",
        "expected_intent": "compare",
        "check": lambda r: len(r.get("gaps_found", [])) == 3,
        "check_description": "All 3 fixed dimensions should produce a finding — tests the Send fan-out actually completed.",
    },
    {
        "name": "Typo / casual phrasing robustness",
        "query": "wut did hoth therapeutics say in their 8-K filing",
        "expected_intent": "lookup",
        "check": lambda r: len(r.get("final_answer", "")) > 20,
        "check_description": "Should still classify and answer correctly despite typos/casual tone.",
    },
    {
        "name": "Draft structural correctness",
        "query": "Write a new AI cybersecurity risk disclosure",
        "expected_intent": "draft_new",
        "check": lambda r: "[Your Company]" in r.get("final_answer", ""),
        "check_description": "Placeholder convention should be followed consistently across draft_new calls.",
    },
    {
        "name": "Comparator structural correctness (2nd case)",
        "query": "Compare Hoth Therapeutics AI disclosure against NOCERA INC and identify gaps",
        "expected_intent": "compare",
        "check": lambda r: len(r.get("gaps_found", [])) == 3,
        "check_description": "Confirms Send fan-out reliability across a different company pair.",
    },
    {
        "name": "Grounded citation check",
        "query": "What did Eightco Holdings Inc report in their filing?",
        "expected_intent": "lookup",
        "check": lambda r: any(
            src.get("company", "").lower() in r.get("final_answer", "").lower()
            or "eightco" in r.get("final_answer", "").lower()
            for src in r.get("search_results", [])
        ) or len(r.get("search_results", [])) > 0,
        "check_description": "Answer should be traceable to an actually-retrieved source.",
    },
]