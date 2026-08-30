"""
Stage 5 — Functional Evaluation Runner.

Runs every question in eval_set.py through the full agent graph,
records: whether Manager's intent classification matched what we
expected (routing accuracy — automatable), timing, and the actual
answer text (quality — read manually, since drafting/comparison tasks
have no single "correct" answer to check automatically against).

Run:  python run_eval.py

Writes a report to eval_results.md.
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src") if (Path(__file__).parent / "src").exists() else str(Path(__file__).parent))

from eval_set import EVAL_QUESTIONS
from main_graph import run_query


def main():
    results = []
    correct_routing = 0

    for i, item in enumerate(EVAL_QUESTIONS, 1):
        query = item["query"]
        expected = item["expected_intent"]

        print(f"[{i}/{len(EVAL_QUESTIONS)}] {query}")
        start = time.time()
        try:
            result = run_query(query)
            elapsed = time.time() - start
            actual_intent = result.get("intent", "ERROR")
            answer = result.get("final_answer", "(no answer)")
            error = None
        except Exception as e:
            elapsed = time.time() - start
            actual_intent = "ERROR"
            answer = ""
            error = str(e)

        routing_ok = actual_intent == expected
        if routing_ok:
            correct_routing += 1

        results.append({
            "query": query,
            "expected_intent": expected,
            "actual_intent": actual_intent,
            "routing_ok": routing_ok,
            "elapsed_sec": round(elapsed, 2),
            "answer": answer,
            "error": error,
        })
        print(f"  -> intent={actual_intent} (expected={expected}) {'OK' if routing_ok else 'MISMATCH'} | {elapsed:.1f}s")

    accuracy = correct_routing / len(EVAL_QUESTIONS) * 100
    avg_latency = sum(r["elapsed_sec"] for r in results) / len(results)

    print(f"\nRouting accuracy: {correct_routing}/{len(EVAL_QUESTIONS)} ({accuracy:.0f}%)")
    print(f"Average latency: {avg_latency:.1f}s per query")

    # Write markdown report
    lines = [
        "# Functional Evaluation Results\n",
        f"**Routing accuracy:** {correct_routing}/{len(EVAL_QUESTIONS)} ({accuracy:.0f}%)  ",
        f"**Average latency:** {avg_latency:.1f}s per query\n",
        "| # | Query | Expected Intent | Actual Intent | Routing OK | Latency (s) |",
        "|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['query'][:60]} | {r['expected_intent']} | {r['actual_intent']} | "
            f"{'✅' if r['routing_ok'] else '❌'} | {r['elapsed_sec']} |"
        )

    lines.append("\n## Full Answers (for manual quality review)\n")
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r['query']}")
        lines.append(f"*Intent: {r['actual_intent']} | Latency: {r['elapsed_sec']}s*\n")
        if r["error"]:
            lines.append(f"**ERROR:** {r['error']}\n")
        else:
            lines.append(f"{r['answer']}\n")

    with open("eval_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\nFull report written to eval_results.md")


if __name__ == "__main__":
    main()