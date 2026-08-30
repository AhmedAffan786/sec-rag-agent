"""
Stage 5 — Mini Evaluation Set (15 questions).

Covers all 4 intents so the eval exercises the whole agentic workflow,
not just one node. expected_intent is used to check routing accuracy;
answer quality itself is judged by reading the actual output (see
run_eval.py's output file) since there's no labeled "correct answer"
for open-ended drafting/comparison tasks.
"""

EVAL_QUESTIONS = [
    # --- lookup (factual retrieval) ---
    {"query": "What did Catalyst Crew Technologies Corp announce in their 8-K filing?", "expected_intent": "lookup"},
    {"query": "What AI risks does Artificial Intelligence Technology Solutions Inc disclose in their filings?", "expected_intent": "lookup"},
    {"query": "What did Hoth Therapeutics disclose in their 8-K?", "expected_intent": "lookup"},
    {"query": "What investment strategy does Global X Funds describe?", "expected_intent": "lookup"},
    {"query": "What did Eightco Holdings Inc report in their filing?", "expected_intent": "lookup"},

    # --- draft_new (write from scratch) ---
    {"query": "Write a new AI risk disclosure section for a fintech company", "expected_intent": "draft_new"},
    {"query": "Draft a new AI governance risk disclosure for a healthcare technology company", "expected_intent": "draft_new"},
    {"query": "Create a fresh disclosure section about AI-related cybersecurity risks", "expected_intent": "draft_new"},
    {"query": "Write a forward-looking statements section about our company's AI plans", "expected_intent": "draft_new"},

    # --- draft_adapt (adapt a peer's language) ---
    {"query": "Rewrite Bank of America's AI risk section for my company", "expected_intent": "draft_adapt"},
    {"query": "Adapt Royal Bank of Canada's AI disclosure language for my own company", "expected_intent": "draft_adapt"},
    {"query": "Base a new disclosure on NOCERA INC's filing language", "expected_intent": "draft_adapt"},

    # --- compare (gap analysis) ---
    {"query": "Compare Artificial Intelligence Technology Solutions Inc's AI disclosure against Bank of America and tell me what's missing", "expected_intent": "compare"},
    {"query": "Compare Bank of America's AI disclosure against Royal Bank of Canada and identify gaps", "expected_intent": "compare"},
    {"query": "Compare Cuentas Inc's disclosure to Eva Live Inc and tell me what's missing", "expected_intent": "compare"},
]