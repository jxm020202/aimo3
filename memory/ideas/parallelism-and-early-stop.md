# Parallelism, Early Stop & Adaptive Batching

## Key Discovery: Early Stop Never Actually Worked

Both baseline and our code launch all attempts simultaneously via ThreadPoolExecutor. `stop_event.set()` fires when N attempts agree, but by then ALL attempts are already running on the GPU. The `f.cancel()` in baseline is a no-op for running futures. `stream.close()` tells vLLM to abort, but the GPU has already done the work.

**Early stop is a voting confidence threshold, not a time optimization.**

Evidence from v22 (8 attempts, ES=3):
- 92ba6a: 3 correct answers, but all 8 attempts ran 17-32s (no short exits)
- 9c1c5f: 3 correct answers, but all 8 attempts ran 52-68s
- a295e9: 3 correct answers, but all 8 attempts ran 135-153s
- No problem shows any attempt exiting early due to stop_event

## GPU KV Cache Constraints (from v22 vLLM log)

```
Available KV cache memory: 8.01 GiB
GPU KV cache size: 233,296 tokens
Maximum concurrency for 65,536 tokens per request: 6.32x
```

### Concurrency at different token usage levels

| Attempt tokens | Per attempt (+ ~1500 prompt) | Max concurrent |
|---|---|---|
| P25 (1,201) | 2,701 | 86 |
| Median (3,643) | 5,143 | 45 |
| P75 (7,222) | 8,722 | 26 |
| P90 (14,450) | 15,950 | 14 |
| Max (35,425) | 36,925 | 6.3 |

### But these numbers are biased!

Token stats are from v22 test set (58/60 correct). The hardest competition problems (12/50 wrong) generate far more tokens:
- 86e8e5 (always wrong): 27K-35K tokens per attempt
- Hard problems average 330s vs 29s clean (11x penalty) — from v21 error analysis
- 50 private problems are unseen and likely harder

The "tokens" logged is generated tokens only. Actual KV cache stores full context (prompt + all turns + code outputs). A 10-turn attempt could use 40K+ KV tokens while showing "15K generated."

### Concurrency reality for hard problems

| Config | At P75 (7K tokens) | At P90 (14K) | At Max (35K) |
|---|---|---|---|
| 8 parallel | 70K/233K = fits | 128K/233K = fits | barely fits |
| 16 parallel | 140K/233K = fits | 255K/233K = **QUEUING** | impossible |
| 6 parallel | 52K/233K = fits | 96K/233K = fits | 222K/233K = barely fits |
| 4 parallel | 35K/233K = fits | 64K/233K = fits | 148K/233K = fits |

## Proposed: Adaptive Batched Execution (v24)

Instead of launching all attempts at once, run in waves:

```python
BATCH_SIZE = 6  # or 4 for safety
for wave in range(3):
    # Launch wave
    futures = [submit(attempt) for _ in range(BATCH_SIZE)]
    # Wait for wave to complete
    for future in as_completed(futures):
        collect(result)
    # REAL early stop — between waves
    if consensus_reached(early_stop):
        break  # Actually prevents new GPU work
```

### Benefits
- Easy problems: 1 wave (6 attempts), early stop fires → ~T/3 wall time vs ~T
- Medium: 2 waves (12 attempts)
- Hard: 3 waves (18 attempts), never queues
- No KV cache pressure — 6 at a time always fits

### Trade-off
- Hard problems take longer (sequential waves vs all-parallel)
- But hard problems were queuing anyway with 16 parallel → net neutral or better
- Easy problems are MUCH faster → time saved for hard problems

### Even Better: Adaptive with KV monitoring
Poll `gpu_cache_usage_perc` from vLLM `/metrics` between waves. Only launch next wave if KV cache has headroom. Dynamically size waves based on actual GPU state.

## What v23 GPU Monitor Will Tell Us

v23 added a background thread polling vLLM /metrics every 5s. Key metrics:
- `num_requests_running` — how many actually on GPU
- `num_requests_waiting` — queued (KV cache full) → if >0, we've hit the limit
- `gpu_cache_usage_perc` — KV saturation
- `num_preemptions_total` — requests evicted → very bad sign

### Decision matrix from v23 results:
- peak_waiting = 0, cache < 80% → GPU handles 16, keep it
- peak_waiting = 0, cache > 90% → tight but OK, consider 12
- peak_waiting > 0 occasionally → drop to 12 or implement batching
- peak_waiting > 0 frequently → implement batched execution for v24

## Temperature Schedule (settled)

Bell curve centered on baseline 0.5:
```
[0.1, 0.3, 0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.7, 0.7, 0.7, 0.7, 0.9]
```
- 0.1: 1 attempt (safety net)
- 0.3: 4 attempts (conservative)
- 0.5: 6 attempts (baseline, most weight)
- 0.7: 4 attempts (exploratory)
- 0.9: 1 attempt (lottery ticket)

With batched execution, temperature schedule would be split across waves:
- Wave 1: [0.1, 0.3, 0.5, 0.5, 0.5, 0.7] — covers full range
- Wave 2: [0.3, 0.3, 0.5, 0.5, 0.7, 0.9] — more weight on diversity
- Wave 3: [0.3, 0.5, 0.7, 0.7] — fill remaining
