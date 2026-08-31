# Load Test Results

**Total queries:** 60  
**Total wall-clock time:** 3107.4s  
**Errors:** 0

## Overall Latency
- Mean: 51.79s
- Median: 33.60s
- P95: 136.59s
- Min: 19.03s
- Max: 144.42s

## Latency by Intent Type
| Intent | Count | Mean (s) | Median (s) | P95 (s) |
|---|---|---|---|---|
| lookup | 36 | 36.67 | 29.97 | 72.22 |s
| draft_new | 8 | 131.58 | 134.81 | 140.69 |
| draft_adapt | 8 | 31.03 | 31.37 | 36.25 |
| compare | 8 | 60.80 | 59.66 | 69.08 |

## Bottleneck Analysis

The dominant cost in every request is **local LLM inference via Ollama** (qwen2.5:7b running on CPU/GPU) — each Manager, Drafter, or Comparator step requires at least one LLM call, and `compare` queries require up to 6 sequential LLM calls (embedding + reranking + gap-analysis, per dimension, per company) plus their own retrieval, making them the clear worst case as the table above shows.

Retrieval itself (NumPy cosine similarity over a few hundred vectors, plus the cross-encoder reranker) is comparatively fast and is NOT the bottleneck — LLM generation time dominates total latency by a wide margin.

### Optimization recommendations

1. **Use GPU acceleration for Ollama** (if not already active) or a smaller/more heavily quantized model for latency-sensitive paths — the Manager's routing call, in particular, is a simple classification task that doesn't need a full 7B model's reasoning depth and could run on a much smaller/faster model.

2. **Parallelize the Comparator's LLM calls, not just its retrieval** — currently each dimension's target/peer retrieval runs sequentially inside `compare_dimension` even though the 3 dimensions run in parallel; batching the gap-analysis LLM calls (or using async calls) would reduce the `compare` intent's latency further.
