"""
Stage 5 — Streamlit UI.

Shows the agent's routing decision, which nodes ran, and the final
result — satisfies the assignment's UI requirement to "demonstrate the
key steps of the agent's operation."

Run: streamlit run app.py
"""

import streamlit as st
from main_graph import run_query

st.set_page_config(page_title="SEC Disclosure Assistant", layout="wide")
st.title("SEC AI-Disclosure Drafting & Gap-Analysis Assistant")
st.caption("Agentic RAG prototype — LangGraph + local Ollama (qwen2.5:7b)")

STEP_MAP = {
    "draft_new": ["Manager → classified as **draft_new**", "Drafter (writing from scratch, no search needed)"],
    "draft_adapt": ["Manager → classified as **draft_adapt**", "Drafter (found peer company, retrieved their text via RAG, adapted it)"],
    "compare": ["Manager → classified as **compare**", "Comparator: fan-out into 3 parallel branches (risk factors, forward-looking statements, financial metrics)", "Comparator: aggregate merged findings"],
    "lookup": ["Manager → classified as **lookup**", "Search Agent (RAG retrieval + grounded answer generation)"],
}

query = st.text_area(
    "Ask a question, request a draft, or ask for a comparison:",
    height=100,
    placeholder="e.g. Compare Artificial Intelligence Technology Solutions Inc's AI disclosure against Bank of America",
)

if st.button("Run", type="primary"):
    if not query.strip():
        st.warning("Please enter a request.")
    else:
        with st.spinner("Running agent..."):
            result = run_query(query)

        intent = result.get("intent", "unknown")

        st.subheader("Agent Steps")
        for step in STEP_MAP.get(intent, ["Manager", "..."]):
            st.markdown(f"- {step}")

        st.divider()
        st.subheader("Result")

        if intent == "compare" and result.get("gaps_found"):
            st.markdown(f"**Comparing:** {result.get('target_company', '?')} vs {result.get('peer_company', '?')}")
            for gap in result["gaps_found"]:
                with st.expander(gap["dimension_label"]):
                    st.write(gap["finding"])
        elif intent in ("draft_new", "draft_adapt") and result.get("draft_output"):
            st.text_area("Draft", result["draft_output"], height=400)
        else:
            st.write(result.get("final_answer", "(no answer produced)"))

        if result.get("search_results"):
            with st.expander("Sources used"):
                for i, r in enumerate(result["search_results"], 1):
                    st.markdown(
                        f"**{i}. {r['company']} | {r['form_type']} | "
                        f"{r.get('filing_date') or 'date unknown'}** (score: {r['score']:.2f})"
                    )
                    st.caption(r["text"][:300] + "...")
else:
    st.info("Enter a request above and click Run.")