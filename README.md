# SEC AI-Disclosure Drafting & Gap-Analysis Assistant

An agentic RAG chatbot prototype built with LangGraph, backed by a local
open-source LLM (Ollama), that helps draft SEC AI-related disclosure
sections and compare a company's disclosure against peers to find gaps.

## 1. Problem & Objectives

**Problem:** Compliance and legal teams drafting SEC disclosures about
AI-related risks currently do this by manually reading and
cross-referencing peer companies' 10-K/10-Q/8-K filings — slow,
inconsistent, and easy to miss emerging disclosure norms as regulatory
attention on AI risk increases.

**Why it's relevant:** AI risk disclosure is a fast-moving area of SEC
reporting; there's no established template, so companies benchmark
against peers constantly. This is a genuine, recurring drafting/review
task, not a toy problem.

**User need addressed:** Given a request, the assistant either (a)
drafts a new AI-related disclosure section from scratch, (b) adapts an
existing peer company's disclosure language for a different company, or
(c) compares a company's disclosure against a peer's across 3 fixed
dimensions and reports what's missing.

**Why agentic RAG (not plain RAG):** A single RAG call can retrieve
relevant text, but it can't *decide* whether a request needs fresh
drafting, peer-based adaptation, or comparison, and it can't
autonomously break a comparison into independent sub-comparisons
(risk factors vs. forward-looking statements vs. financial metrics) and
retrieve for each separately. That routing and decomposition is the
reason an agent is used here instead of one RAG call.

## 2. Architecture

```
                         ┌─────────────┐
                         │   MANAGER    │  routes by intent (LLM classification)
                         └──────┬───────┘
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
     ┌────────────────┐  ┌────────────────┐  ┌───────────────┐
     │ SEARCH AGENT    │  │ DRAFTER        │  │ COMPARATOR    │
     │ (RAG subgraph)  │  │ new / adapt    │  │ fans out into │
     │                 │  │ modes          │  │ 3 parallel    │
     └─────────────────┘  └───────┬────────┘  │ branches      │
                                   │            └──────┬────────┘
                                   ▼                    ▼
                          (calls Search Agent   compare_dimension x3
                           when it needs peer   (parallel, via
                           text)                 LangGraph Send)
                                                       │
                                                       ▼
                                              comparator_aggregate
                                              (merges findings)
```

### The 5 main LangGraph nodes
1. **Manager** — classifies the query's intent (`draft_new`, `draft_adapt`,
   `compare`, `lookup`) using the local LLM. This is the required
   **autonomous decision-making / conditional routing**.
2. **Search Agent** — shared node, invoked by Manager (plain lookups) or
   by Drafter/Comparator (when they need retrieved text). Calls the
   separate RAG subgraph and generates a grounded answer.
3. **Drafter** — two modes: `new` (drafts from scratch, no search needed —
   demonstrates the agent deciding for itself whether search is
   necessary) and `adapt` (finds a peer company mentioned in the query,
   retrieves their text via RAG, rewrites it for the user).
4. **Peer Selector** — the required **non-retrieval tool**. Structured
   filtering over filing metadata (company, form type, CIK, date) —
   no embeddings involved — used to find comparable peer companies.
5. **Disclosure Comparator** — fans out into **3 independent parallel
   branches** (one per fixed dimension: risk factors, forward-looking
   statements, financial metrics) using LangGraph's `Send` API. This is
   the required **decomposition into subtasks with independent
   execution**. Each branch retrieves and analyzes independently; a
   final aggregation node merges the 3 findings.

### RAG Subgraph (separate, does not count toward the 5 nodes)
`embed_query → retrieve (company-filterable) → rerank (cross-encoder) →
contextualize (attach source metadata)`. Invoked by Search Agent,
Drafter, and Comparator alike.

### Tools (2, satisfying "at least one non-retrieval")
1. **RAG retrieval** (via the RAG subgraph) — vector search
2. **Peer Selector** — structured metadata filtering, no embeddings

### State management
A shared `AgentState` (TypedDict) carries query, intent, draft
mode/output, target/peer companies, subtasks, search results, and
comparator findings across every node. The Comparator's parallel
branches merge their results via a `operator.add`-annotated field,
since LangGraph requires an explicit reducer when multiple parallel
branches write to the same state key.

## 3. Data Source

SEC EDGAR full-text search, keyword `"artificial intelligence"`,
filings dated Jan–Aug 2026. 79 filings downloaded as PDFs, chunked into
713 pieces. No metadata.csv was available, so company/form-type/CIK/date
metadata is parsed directly from each filename via regex (filenames
follow a consistent `<index>_<COMPANY>_Form_<type>_<suffix>.pdf`
pattern).

**Known limitation:** most of the 79 filings are `8-K` (short,
press-release-style disclosures), not full `10-K` filings with dedicated
narrative "Risk Factors" sections — so some queries about deep AI-risk
narrative language correctly return "not found" rather than hallucinated
content, since that content genuinely isn't present in this dataset.

## 4. Model Choice

**LLM:** Qwen2.5 7B Instruct, served locally via Ollama (no paid APIs).
Chosen over Llama 3.1 8B for its stronger adherence to structured output
instructions (important for the Manager's intent classification and the
Comparator's constrained gap-analysis prompts), and it comfortably fits
a 16GB RAM / NVIDIA GPU machine at 4-bit quantization.

**Trade-off:** a 7B model is fast enough for local, single-user
prototyping but is the dominant cost in every request (see load test
below) — a larger model would likely improve gap-analysis reasoning
quality at the cost of latency; a smaller model could speed up the
Manager's simple routing decision specifically.

**Embeddings:** `BAAI/bge-small-en-v1.5` (local, CPU, sentence-transformers).
**Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (local, CPU).
**Vector store:** FAISS (`IndexFlatIP`, exact cosine-similarity search)
for general/unfiltered queries, with a small NumPy brute-force search
kept for company-filtered queries (used by Drafter's adapt mode and the
Comparator, where the searchable subset is already tiny — a handful of
chunks per company — so FAISS adds no benefit there).

*Trade-off note:* earlier in development, Chroma and FAISS both had
unresolved Python 3.14 Windows wheel gaps, so the vector store started
as pure NumPy brute-force search — genuinely fine at this corpus size
(~700 chunks). `faiss-cpu` has since shipped a Python-3.14-compatible
wheel, so the unfiltered search path was migrated to FAISS; the
NumPy path was kept where it already worked well.

## 5. Evaluation & Performance

### Functional evaluation
15 questions spanning all 4 intents (`eval_set.py`). Run with:
```
python run_eval.py
```
Produces `eval_results.md` with per-question routing accuracy, latency,
and full answer text for manual quality review (drafting/comparison
tasks have no single "correct" answer to check automatically).

**Results:** Routing accuracy: **15/15 (100%)** across all 4 intent
types. Average latency: **63.9s per query** on local CPU/GPU inference.
Full per-question answers are in `eval_results.md`.

### Load test
Fires 60 queries (weighted toward realistic usage — mostly `lookup`,
with `draft`/`compare` mixed in) through the full graph. Run with:
```
python load_test.py 60
```
(Increase the number, up to 200, if your hardware allows — 60 keeps
total runtime manageable on a local 7B CPU/GPU setup.)

Produces `load_test_results.md` with mean/median/p95 latency overall
and broken down by intent type, plus the bottleneck analysis below.

**Results:** 60 queries, 0 errors, total wall-clock time 3107s (~52 min).
Mean latency **51.8s**, median **33.6s**, P95 **136.6s**, min 19.0s, max
144.4s. Full breakdown by intent type is in `load_test_results.md`.

### Secondary evaluation — LLM & prompt behavior

`eval_set.py` above tests routing accuracy. `llm_eval_set.py` tests a
different, complementary thing: whether each prompt actually *behaves*
correctly once routed — not just "did it run," but "did it refuse when
it should, generalize past exact training phrasing, and stay
structurally correct."

8 cases, each with an automated check function:
- **Refusal on missing info** — does the answer admit the context doesn't
  cover it, instead of inventing a plausible-sounding answer?
- **Paraphrase robustness** — do reworded / typo'd / casually-phrased
  versions of the original eval questions still route and behave
  correctly (not just exact phrasings the original 15 happened to use)?
- **Structural correctness** — for `compare` queries, did all 3 fixed
  dimensions actually produce a finding (confirms the `Send` fan-out
  reliably completes, not just that it started)?
- **Grounded citation** — is the answer traceable back to an actually
  retrieved source, not free-floating text?

Run with:
```
python run_llm_eval.py
```
Produces `llm_eval_results.md` with a pass/fail table per check plus
full answer text.

**Results:** *(fill in after running)*

**Bottleneck:** local LLM inference (Ollama) dominates latency in every
request. `draft_new` is the slowest intent (108-146s) since it's one
long, uninterrupted generation with no retrieval shortcuts. `lookup` is
fastest (19-42s) — a single retrieval plus one grounded answer.
`compare` sits in between (51-73s) despite doing more total work,
because its 3 dimension branches genuinely run in parallel via
LangGraph's `Send` rather than stacking sequentially. Vector retrieval
itself (NumPy + reranker) is fast and not the bottleneck anywhere.

**Optimization recommendations:**
1. Use a smaller/faster model specifically for the Manager's routing
   classification (a simple 4-way categorization doesn't need a full 7B
   model's reasoning depth), reserving the larger model for
   drafting/comparison quality.
2. Parallelize the Comparator's LLM gap-analysis calls (not just its
   retrieval) — currently each dimension's target/peer retrieval and
   analysis runs sequentially inside one branch even though the 3
   dimensions run in parallel with each other.

## 6. Installation & Running

### Prerequisites
- Python 3.11+ (or your working environment — see note below on 3.14)
- [Ollama](https://ollama.com/download), with `qwen2.5:7b` pulled:
  ```
  ollama pull qwen2.5:7b
  ```
- Docker Desktop (for containerized run)

### Local (no Docker)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python ingest.py                # builds the local vector store from Data/*.pdf
streamlit run app.py            # opens the UI at localhost:8501
```

### Docker
Ollama runs on the **host machine**, not inside the container — set
`OLLAMA_HOST=0.0.0.0` as an environment variable before starting Ollama,
so the container can reach it via `host.docker.internal`:
```bash
docker compose up --build
```
or without compose:
```bash
docker build -t sec-rag-agent .
docker run -p 8501:8501 -e OLLAMA_BASE_URL=http://host.docker.internal:11434 sec-rag-agent
```
Then open `http://localhost:8501`.

### Running the evaluation and load test
```bash
python run_eval.py       # writes eval_results.md
python load_test.py 60   # writes load_test_results.md
```

## 7. Additional Features (Beyond Assignment Scope)

Built after the core submission, as extra usability layers on top of
the required agent — none of these change or risk the graded pipeline
above.

**Regenerate from selected sources.** After any query that retrieves
sources, they appear with checkboxes (pre-checked). You can adjust the
selection and click "Regenerate using selected sources only" to redo
the answer from exactly the sources you choose, instead of the agent's
automatic selection.

**Upload your own SEC filing.** A separate section lets you upload a
PDF at runtime — it's chunked and embedded on the fly (in memory only,
per-session, never written to disk or added to the main corpus), then
you can ask questions or draft from it, using the same grounded-answer
and drafting logic as the main pipeline (`uploaded_doc.py`).

*Bug found and fixed during testing:* the upload feature initially used
`pypdf` for extraction and no reranking. Testing with a real
multi-column resume PDF revealed two problems: (1) `pypdf` reads text
in raw stream order, which interleaves left/right column text
mid-sentence on multi-column layouts, and (2) plain cosine-similarity
search without reranking wasn't precise enough even on the correctly-
extracted text, missing the right chunk on an 11-chunk document. Fixed
by switching to `pdfplumber` (layout-aware extraction) and adding the
same retrieve-then-rerank pattern already used in the main RAG
subgraph. Confirmed fixed by retesting the same document and question.

## 8. Known Limitations
- Retrieval quality is bounded by corpus composition — most filings are
  short 8-K items rather than narrative 10-K risk sections, so some
  legitimate "not found" answers reflect the dataset, not a bug.
- Peer/company name detection in Drafter/Comparator matches against
  known company names appearing in the query text (with prefix
  matching for dropped corporate suffixes like "Corp DE") — it does not
  handle company names never seen in the ingested dataset.
- No conversation memory — each query is handled independently, by design
  (not required by the assignment's scope).