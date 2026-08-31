"""
Runs llm_eval_set.py — the secondary, prompt/behavior-focused eval.

Different from run_eval.py (which only checks routing accuracy): this
checks whether each prompt actually behaves correctly once routed —
refusal on missing info, paraphrase robustness, and structural
correctness of the Comparator's parallel fan-out.

Run:  python run_llm_eval.py
Writes a report to llm_eval_results.md.
"""

import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src") if (Path(__file__).parent / "src").exists() else str(Path(__file__).parent))

from llm_eval_set import CASES
from main_graph import run_query


def main():
    results = []
    routing_correct = 0
    check_passed = 0

    for i, case in enumerate(CASES, 1):
        print(f"[{i}/{len(CASES)}] {case['name']}: {case['query']}")
        start = time.time()
        try:
            result = run_query(case["query"])
            elapsed = time.time() - start
            actual_intent = result.get("intent", "ERROR")
            routing_ok = actual_intent == case["expected_intent"]
            behavior_ok = case["check"](result)
            error = None
        except Exception as e:
            elapsed = time.time() - start
            actual_intent = "ERROR"
            routing_ok = False
            behavior_ok = False
            result = {}
            error = str(e)

        if routing_ok:
            routing_correct += 1
        if behavior_ok:
            check_passed += 1

        results.append({
            "name": case["name"],
            "query": case["query"],
            "expected_intent": case["expected_intent"],
            "actual_intent": actual_intent,
            "routing_ok": routing_ok,
            "behavior_ok": behavior_ok,
            "check_description": case["check_description"],
            "elapsed_sec": round(elapsed, 2),
            "answer": result.get("final_answer", ""),
            "error": error,
        })
        print(f"  -> intent={actual_intent} routing={'OK' if routing_ok else 'MISMATCH'} "
              f"| behavior_check={'PASS' if behavior_ok else 'FAIL'} | {elapsed:.1f}s")

    n = len(CASES)
    print(f"\nRouting accuracy: {routing_correct}/{n} ({routing_correct/n*100:.0f}%)")
    print(f"Behavior checks passed: {check_passed}/{n} ({check_passed/n*100:.0f}%)")

    lines = [
        "# LLM & Prompt-Focused Evaluation Results\n",
        "Secondary eval — tests refusal behavior, paraphrase robustness, and "
        "structural correctness (not just routing).\n",
        f"**Routing accuracy:** {routing_correct}/{n} ({routing_correct/n*100:.0f}%)  ",
        f"**Behavior checks passed:** {check_passed}/{n} ({check_passed/n*100:.0f}%)\n",
        "| # | Test | Expected Intent | Actual | Routing | Behavior Check | Latency (s) |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(results, 1):
        lines.append(
            f"| {i} | {r['name']} | {r['expected_intent']} | {r['actual_intent']} | "
            f"{'✅' if r['routing_ok'] else '❌'} | {'✅' if r['behavior_ok'] else '❌'} | {r['elapsed_sec']} |"
        )

    lines.append("\n## Details\n")
    for i, r in enumerate(results, 1):
        lines.append(f"### {i}. {r['name']}")
        lines.append(f"*Query: {r['query']}*  ")
        lines.append(f"*Check: {r['check_description']}*\n")
        if r["error"]:
            lines.append(f"**ERROR:** {r['error']}\n")
        else:
            lines.append(f"{r['answer']}\n")

    with open("llm_eval_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\nFull report written to llm_eval_results.md")


if __name__ == "__main__":
    main()