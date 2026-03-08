# Handover Document — March 8, 2026 (Session 15, continued)

## Where We Stopped

Working on `notebooks/aimo3-no-wave1.ipynb` — Wave 2 only notebook with 120B-only GenSelect.
v5 pushed to Kaggle on set_c (4 problems).

**Active kernel**: `jxm222/aimo3-no-wave1` — v5 running on set_c

## No-Wave1 Notebook Structure

```
notebooks/aimo3-no-wave1.ipynb   <-- EDIT THIS (source of truth for no-wave1)
push-nowave1/
  kernel-metadata.json            (mounts gpt-oss-120b ONLY — no 7B)
  aimo3-no-wave1.ipynb            (copy, NOT symlink — must cp after edits)
```

**To push**: `cp notebooks/aimo3-no-wave1.ipynb push-nowave1/ && kaggle kernels push -p push-nowave1/`
**To edit cells**: `python3 scripts/nb2.py read CELL notebooks/aimo3-no-wave1.ipynb > /tmp/cell.py`

## v5 Changes (120B-Only GenSelect)

### Why: GPU Memory Reality
- H100 = 79.18G. Baseline uses 0.96 for vLLM alone → only 3.2G free
- 7B BNB-4bit needs ~6G. Cannot coexist with 120B at any safe utilization split
- v4 crashed at 0.87 (vLLM only got 0.88G KV cache, needed 1.27G)
- v3 OOMed during 7B generation (vLLM reserved 73G, only 0.06G free for activations)
- Decision: drop 7B from this push, use 120B-only GenSelect. Plan sleep mode for future 7B.

### Config
- **gpu_memory_utilization = 0.96** (matching baseline, all GPU for 120B)
- **24 agents, 24 workers** (restored from 18)
- **Rerun threshold**: ceil(24/3) = 8
- 7B model removed from kernel-metadata.json (code stays, gracefully skips)

### GenSelect: 120B Only
- 2-way decision: majority vote + 120B GenSelect
- Agree → CONFIRMED. Disagree → rerun.
- Post-rerun: if still disagree, 120B gets final say
- ReasoningEffort.HIGH for GenSelect judge (kept)
- max_tokens = self.cfg.context_tokens (65536) — no artificial cap

### Summarizer
- ReasoningEffort.MEDIUM (kept)
- max_tokens = self.cfg.context_tokens (65536) — was 2048, likely root cause of 0/12 clean summaries
- Harmony channels: analysis channel was consuming all 2048 tokens before final channel with \boxed{}
- Append fallback still in place as safety net

### Temperature (unchanged from v4)
- R1: 0.6 flat. Rerun: 0.3 flat. GenSelect: 0.6. Summarizer: 0.3.

## v4 Result: CRASHED
- vLLM couldn't start at gpu_memory_utilization=0.87
- `ValueError: KV cache memory (0.88 GiB) < required (1.27 GiB) for max_model_len 65536`

## v3 Results (set_d, 1 problem)
- 7B loaded (53s) but OOMed on all 8 GenSelect passes
- 120B GenSelect: 0/5 valid judgments (solved instead of judging — ReasoningEffort.HIGH + max_tokens issue)
- Summaries: 0/12 clean (analysis channel ate all 2048 max_tokens)

## Key Findings This Session

### Harmony API Channels (NOT <think> tags)
- GPT-OSS uses Harmony channel format: `<|channel|>analysis` then `<|channel|>final`
- R1 solver works because `encoding.parse_messages_from_completion_tokens()` separates channels
- Summarizer/GenSelect use raw `response.choices[0].text` — both channels concatenated
- With small max_tokens, analysis channel consumes budget before final channel outputs \boxed{}
- Fix: increase max_tokens generously (now 65536)

### GPU Memory Math
- 120B model weights: ~65.97G
- vLLM overhead (torch.compile, CUDA graphs): ~2G
- At 0.96: KV cache ≈ 76.0 - 66.0 - 2.0 = 8.0G (very generous)
- System/CUDA overhead: ~3.2G (the remaining 4%)
- No room for 7B without eating into system overhead or KV cache

### Sleep Mode (Next Step)
- vLLM sleep mode: models time-share GPU, only one loaded at a time
- Level 1: weights → CPU pinned memory, wake in 0.1-6s (needs CPU RAM = model size)
- Level 2: everything discarded, wake in 0.8-2.6s (minimal CPU RAM)
- Plan: 120B runs R1 → sleep → wake 7B for GenSelect → sleep → wake 120B for rerun
- Requires vLLM >= 0.10.2, experimental feature
- MXFP4 + sleep mode untested

## Known Issues (Priority Order)

1. **120B GenSelect quality** — v3 showed 0/5 valid judgments. Increased max_tokens should fix (analysis channel no longer truncated). v5 will validate.
2. **Summary quality** — 0/12 clean in v3. max_tokens increase should fix. v5 will validate.
3. **Sleep mode for 7B** — planned but not implemented. Research done.
4. **Deadline overshoot** — attempts can run up to 30s past problem_timeout
5. **fp8 + prefix caching** — possibly incompatible per vLLM issues

## Key Commands

```bash
python3 scripts/nb2.py read CELL notebooks/aimo3-no-wave1.ipynb > /tmp/cell.py
python3 scripts/nb2.py write CELL /tmp/cell.py notebooks/aimo3-no-wave1.ipynb
cp notebooks/aimo3-no-wave1.ipynb push-nowave1/
kaggle kernels push -p push-nowave1/
kaggle kernels status jxm222/aimo3-no-wave1
kaggle kernels output jxm222/aimo3-no-wave1 -p output/nowave1-v5
```

## Kaggle State

- **no-wave1 kernel**: `jxm222/aimo3-no-wave1` — v5 running on set_c
- **Main kernel 120B**: `jxm222/aimo3-solver` — v20 last good (44/50)
- **DB dataset**: `jxm222/aimo3-problem-db` (public, 374 entries, v12)
- **Test data**: `jxm222/aimo3-test-data` (has set_a/b/c/d)
- **7B model**: `jxm222/openreasoningnemotron-7b-bnb4` (uploaded, not mounted in v5)
