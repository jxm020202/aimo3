# Runtime & Dual-Run Scoring
**Tags**: #runtime #scoring #official #confirmed
**Threads**: #635859 (welcome), #679451 (runtime Q), #639476 (rules), gateway source code

## Time Limits

| Type | Limit | Source |
|------|-------|--------|
| GPU notebook | **5 hours per run** | CompeteHub mirror of AIMO3 rules |
| CPU notebook | 9 hours per run | CompeteHub mirror |
| Gateway timeout | 9 hours (effectively no timeout) | `aimo_3_gateway.py:21` |
| Displayed times | Obfuscated by up to 30 min | Discussion #679451 reply |

## Dual-Run Scoring

Each submission is run **TWICE**, sequentially, as completely independent notebook executions.

| Outcome | Points |
|---------|--------|
| Both runs correct | 1.0 |
| One correct, one wrong | 0.5 |
| Both wrong | 0.0 |

**This is a consistency penalty.** Stochastic solutions lose 0.5 points on problems where they're inconsistent.

## Sequential, Not Parallel

Evidence:
- `KAGGLE_IS_COMPETITION_RERUN` env var triggers `serve()` — each run is a fresh container
- Gateway uses `os.urandom(4)` for seed — different problem ordering each run
- Discussion #635859: "Anyone know if the 2 private set runs will be completely independent runs (ie different orders)?"
- Each container gets the full H100 GPU — can't share it across parallel runs

**Total time available: 2 x 5hr = 10 hours.**

## Our Runtime (v21)

| Tier | Problems | Time | Avg/problem |
|------|----------|------|-------------|
| Reference | 10 | 31.3 min | 188s |
| Hard diagnostic | 10 | 14.0 min | 84s |
| AIME benchmark | 10 | 6.3 min | 38s |
| Comprehensive | 20 | 12.3 min | 37s |
| **Total** | **50** | **63.8 min** | **77s** |

**Headroom: 236 min unused per run.** We're using 21% of our time budget.

## Implications

- Can safely increase per-problem budget from 900s → 2000-2500s
- Can increase parallel attempts from 8 → 16 or even 24
- vLLM startup cost (~3-5 min) is paid twice (once per run), but negligible vs 5hr budget
- Problem ordering differs between runs, so time management must handle any order
