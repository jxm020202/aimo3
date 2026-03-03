# Pass@100 Analysis — Host Data
**Tags**: #model-capability #strategy #official #game-changer
**Thread**: [#679559](https://www.kaggle.com/competitions/ai-mathematical-olympiad-progress-prize-3/discussion/679559)
**Author**: Simon Frieder (competition host) | **Date**: 2026-03-02

## Key Chart Data (from OP)

Two unnamed models tested on AIMO3's 50 public + 50 private problems.
No tool calling, no fine-tuning, no optimizations. Pure text reasoning.
Pass@N bootstrapped from pass@100 samples.

### Model A (likely GPT-OSS-20B or smaller)
| Pass@N | Private | Public |
|--------|---------|--------|
| 1      | ~18.5   | ~17    |
| 3      | ~25     | ~24    |
| 5      | ~27     | ~27.5  |
| 20     | ~31.5   | ~35    |
| 100    | ~37     | ~39    |

### Model B (likely GPT-OSS-120B)
| Pass@N | Private | Public |
|--------|---------|--------|
| 1      | ~27.5   | ~26.5  |
| 3      | ~37.5   | ~37.5  |
| 5      | ~40     | ~41.5  |
| 20     | ~46     | ~48    |
| 100    | **~50** | **~50**|

## THE INSIGHT

**Model B at pass@100 solves essentially ALL 50 problems on both public AND private sets.**

This means:
1. GPT-OSS-120B HAS the capability to solve every problem
2. The competition is NOT about model capability — it's about **variance reduction**
3. The gap between pass@5 (~40) and pass@100 (~50) is 10 problems — those are solvable but need more attempts
4. The gap between pass@1 (~27) and pass@5 (~40) is 13 problems — huge gains from just 5 parallel attempts

## Strategic Implications

- **More attempts = more points**: Going 8→16 attempts would move us toward pass@16-20 territory (~46-48/50)
- **We have time budget**: Our v21 used 64 min for 50 problems. 5hr budget = 300 min. We can 2x-3x our compute.
- **Dual run is sequential**: Each run gets its own 5hr. So time is NOT the bottleneck at all.
- **Consistency matters more than capability**: The dual-run scoring (both correct=1, one=0.5) penalizes variance. More attempts + majority voting = more consistent.
- **Tool calling is the secret sauce**: Model A pass@100 only reaches ~37-39. Model B reaches ~50. But with TIR (code execution), the baseline already gets 44/50 with just 8 attempts. TIR closes the gap that raw pass@N can't.

## Community Reactions

> "If nearly all problems can be solved at pass@100 without finetuning or tool calling, does this mean that this year's competition is primarily measuring true model reasoning capability, or rather the ability to control randomness and reduce variance?"

> "gpt-oss-120b could not even score 32 with pass@5 without tool calling" — Note: with TIR, baseline gets 44/50 at ~pass@8. TIR is worth +12 points.

> "pass@100 means it is considered correct if any of the 100 submissions is correct" — This is NOT how the competition works (majority vote, not any-correct), but shows the theoretical ceiling.

## What This Means for v22+

Priority 1: **More attempts** (8→16 or even 24). We have the time budget.
Priority 2: **Better voting** (GenSelect, reward model). Extract signal from noisy attempts.
Priority 3: **Reduce None rate** (44.5% of attempts return no answer). Each None is a wasted attempt.
Priority 4: **Fix error cascades** (120 errors waste time and corrupt answers).
