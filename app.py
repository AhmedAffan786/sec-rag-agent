"""
Stage 5 — Streamlit UI (single unified flow).

1. User asks a question / requests a draft / comparison — the agent
   runs automatically exactly as before (Manager decides everything).
2. If the agent used retrieved sources, they appear below the result
   with checkboxes, pre-checked. The user can adjust the selection and
   click "Regenerate using selected sources only" to redo the answer
   using exactly the sources they picked — same page, no separate mode.

Run: streamlit run app.py
"""

import streamlit as st
from main_graph import run_query
from drafter import draft_from_selected
from search_agent import ANSWER_PROMPT, _format_context
from llm import get_llm
import uploaded_doc

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
    key="query",
)

if st.button("Run", type="primary"):
    if not query.strip():
        st.warning("Please enter a request.")
    else:
        with st.spinner("Running agent..."):
            result = run_query(query)
        st.session_state["last_result"] = result

result = st.session_state.get("last_result")

if result:
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

    sources = result.get("search_results")
    if sources:
        st.divider()
        st.subheader("Sources used")
        st.caption("Adjust the selection below and regenerate if you want the answer built from different sources.")

        for i, r in enumerate(sources):
            label = f"{r['company']} | {r['form_type']} | {r.get('filing_date') or 'date unknown'} (score: {r['score']:.2f})"
            st.checkbox(label, value=True, key=f"src_{i}")
            st.caption(r["text"][:300] + "...")

        refine_instruction = st.text_input(
            "Instruction for the regenerated version (optional — leave blank to reuse your original request)",
            key="refine_instruction",
        )

        if st.button("Regenerate using selected sources only"):
            chosen = [r for i, r in enumerate(sources) if st.session_state.get(f"src_{i}", True)]
            if not chosen:
                st.warning("Select at least one source first.")
            else:
                instruction = refine_instruction.strip() or query
                with st.spinner("Regenerating from your selected sources..."):
                    regenerated = draft_from_selected(chosen, instruction)
                st.subheader("Regenerated Result")
                st.text_area("Result", regenerated, height=400, key="regenerated_output")
else:
    st.info("Enter a request above and click Run.")

# ---------------------------------------------------------------------
# Upload your own document — separate from the main 79-filing corpus.
# Embeddings are created on the fly, in memory only, per session.
# ---------------------------------------------------------------------
st.divider()
st.subheader("Or: upload your own SEC filing")
st.caption("Runtime embeddings, created just for this session — not saved to the main dataset.")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"], key="uploaded_pdf")

if uploaded_file is not None:
    if st.session_state.get("uploaded_doc_name") != uploaded_file.name:
        with st.spinner(f"Reading and embedding {uploaded_file.name}..."):
            st.session_state["uploaded_doc_index"] = uploaded_doc.embed_and_index(uploaded_file, uploaded_file.name)
        st.session_state["uploaded_doc_name"] = uploaded_file.name

    doc_index = st.session_state.get("uploaded_doc_index")
    if doc_index and doc_index["chunks"]:
        st.success(f"'{uploaded_file.name}' indexed — {len(doc_index['chunks'])} chunks ready to question.")

        doc_query = st.text_input("Ask a question about this document, or describe what to draft from it:", key="doc_query")

        col1, col2 = st.columns(2)
        with col1:
            ask_clicked = st.button("Ask about this document")
        with col2:
            draft_clicked = st.button("Draft from this document")

        if (ask_clicked or draft_clicked) and doc_query.strip():
            with st.spinner("Searching the document..."):
                doc_results = uploaded_doc.search(doc_index, doc_query, k=4)

            if not doc_results:
                st.warning("Couldn't extract readable text from this PDF.")
            elif ask_clicked:
                context = _format_context(doc_results)
                llm = get_llm(temperature=0.1)
                prompt = ANSWER_PROMPT.format(context=context, query=doc_query)
                with st.spinner("Generating answer..."):
                    answer = llm.invoke(prompt).content.strip()
                st.subheader("Answer")
                st.write(answer)
                with st.expander("Chunks used"):
                    for i, r in enumerate(doc_results, 1):
                        st.caption(f"{i}. (score: {r['score']:.2f}) {r['text'][:300]}...")
            elif draft_clicked:
                with st.spinner("Drafting..."):
                    draft = draft_from_selected(doc_results, doc_query)
                st.subheader("Draft")
                st.text_area("Result", draft, height=400, key="uploaded_doc_draft")
        elif (ask_clicked or draft_clicked):
            st.warning("Enter a question or instruction first.")
    else:
        st.warning("Couldn't extract any text from this PDF — it may be a scanned image without selectable text.")