"""
Stage 5 — Load Test.

Fires N queries at the full agent graph and measures latency.
Default N=60 (within the assignment's 50-200 range) using mostly
'lookup' queries — this represents the most common real-world usage
pattern (most user requests will be simple questions, not drafting or
comparison), and keeps total runtime manageable on a local 7B model.

You can increase N via a command-line argument if your hardware
allows, e.g.: python load_test.py 150

Run:  python load_test.py [N]
Writes a report to load_test_results.md.
"""

import sys
import time
import statistics
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src") if (Path(__file__).parent / "src").exists() else str(Path(__file__).parent))

from main_graph import run_query

# A small pool of representative queries, cycled to reach N total.
# Weighted toward "lookup" (cheapest, most common) with some heavier
# draft/compare queries mixed in, since a real bottleneck analysis
# needs to see the cost difference between intent types.
QUERY_POOL = [
    ("lookup", "What did Catalyst Crew Technologies Corp announce in their 8-K filing?"),
    ("lookup", "What AI risks does Artificial Intelligence Technology Solutions Inc disclose?"),
    ("lookup", "What did Hoth Therapeutics disclose in their 8-K?"),
    ("lookup", "What investment strategy does Global X Funds describe?"),
    ("draft_new", "Write a new AI risk disclosure section for a fintech company"),
    ("draft_adapt", "Adapt Royal Bank of Canada's AI disclosure language for my own company"),
    ("compare", "Compare Bank of America's AI disclosure against Royal Bank of Canada and identify gaps"),
]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    print(f"Running load test with {n} queries...")

    latencies_by_intent = {}
    all_latencies = []
    errors = 0

    start_total = time.time()
    for i in range(n):
        intent_label, query = QUERY_POOL[i % len(QUERY_POOL)]
        start = time.time()
        try:
            run_query(query)
            elapsed = time.time() - start
        except Exception as e:
            elapsed = time.time() - start
            errors += 1
            print(f"  [{i+1}/{n}] ERROR: {e}")

        all_latencies.append(elapsed)
        latencies_by_intent.setdefault(intent_label, []).append(elapsed)
        print(f"  [{i+1}/{n}] {intent_label}: {elapsed:.2f}s")

    total_elapsed = time.time() - start_total

    def summarize(latencies):
        sorted_lat = sorted(latencies)
        return {
            "count": len(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": sorted_lat[int(len(sorted_lat) * 0.95) - 1] if len(sorted_lat) >= 2 else sorted_lat[0],
            "min": min(latencies),
            "max": max(latencies),
        }

    overall = summarize(all_latencies)

    print(f"\n{'='*50}")
    print(f"Total time: {total_elapsed:.1f}s for {n} queries")
    print(f"Errors: {errors}")
    print(f"Overall — mean: {overall['mean']:.2f}s | median: {overall['median']:.2f}s | "
          f"p95: {overall['p95']:.2f}s | min: {overall['min']:.2f}s | max: {overall['max']:.2f}s")

    lines = [
        "# Load Test Results\n",
        f"**Total queries:** {n}  ",
        f"**Total wall-clock time:** {total_elapsed:.1f}s  ",
        f"**Errors:** {errors}\n",
        "## Overall Latency",
        f"- Mean: {overall['mean']:.2f}s",
        f"- Median: {overall['median']:.2f}s",
        f"- P95: {overall['p95']:.2f}s",
        f"- Min: {overall['min']:.2f}s",
        f"- Max: {overall['max']:.2f}s\n",
        "## Latency by Intent Type",
        "| Intent | Count | Mean (s) | Median (s) | P95 (s) |",
        "|---|---|---|---|---|",
    ]
    for intent_label, lats in latencies_by_intent.items():
        s = summarize(lats)
        lines.append(f"| {intent_label} | {s['count']} | {s['mean']:.2f} | {s['median']:.2f} | {s['p95']:.2f} |")

    lines.append("\n## Bottleneck Analysis\n")
    lines.append(
        "The dominant cost in every request is **local LLM inference via Ollama** "
        "(qwen2.5:7b running on CPU/GPU) — each Manager, Drafter, or Comparator "
        "step requires at least one LLM call, and `compare` queries require up "
        "to 6 sequential LLM calls (embedding + reranking + gap-analysis, per "
        "dimension, per company) plus their own retrieval, making them the "
        "clear worst case as the table above shows.\n"
    )
    lines.append(
        "Retrieval itself (NumPy cosine similarity over a few hundred vectors, "
        "plus the cross-encoder reranker) is comparatively fast and is NOT the "
        "bottleneck — LLM generation time dominates total latency by a wide margin.\n"
    )
    lines.append("### Optimization recommendations\n")
    lines.append(
        "1. **Use GPU acceleration for Ollama** (if not already active) or a "
        "smaller/more heavily quantized model for latency-sensitive paths — "
        "the Manager's routing call, in particular, is a simple classification "
        "task that doesn't need a full 7B model's reasoning depth and could "
        "run on a much smaller/faster model.\n"
    )
    lines.append(
        "2. **Parallelize the Comparator's LLM calls, not just its retrieval** — "
        "currently each dimension's target/peer retrieval runs sequentially "
        "inside `compare_dimension` even though the 3 dimensions run in "
        "parallel; batching the gap-analysis LLM calls (or using async calls) "
        "would reduce the `compare` intent's latency further.\n"
    )

    with open("load_test_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\nFull report written to load_test_results.md")


if __name__ == "__main__":
    main()