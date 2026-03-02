# Notes & Future Improvements

## Test Data

We have two test tiers:

**Tier 1: Reference (10 problems)** — `data/reference.csv`
- Official AIMO3 reference problems with known answers
- 4 easy (AIMO2-level), 6 hard (AIMO3/IMO-level)
- Best signal for actual competition performance

**Tier 2: Extended (~4,000+ problems)** — `data/test_sets/`
- AIME 1983-2024: 933 problems (integer answers 0-999)
- AIME+IMO with answers: 1,648 problems (1,447 integer answers)
- AIMO external: 21,292 problems (MATH dataset, various levels)
- Use for stress-testing, regression testing, ablation studies

## Improvement List

1. Get as many test questions as possible from as many sources
   - [x] AIME 1983-2024 (933 problems)
   - [x] AIME+IMO dataset (1,648 problems)
   - [x] AIMO external / MATH dataset (21,292 problems)
   - [ ] Art of Problem Solving (AoPS) parsed dataset
   - [ ] OlympiadBench
   - [ ] MATH Level 5 specifically (hardest, most relevant)
   - [ ] Past AIMO1/AIMO2 public problems if available
   - [ ] IMO Shortlist problems with numerical answers

2. Fix double-run determinism (seed per problem+attempt, not global)
   - Baseline uses `set_seed(42)` globally but vLLM sampling is still stochastic
   - Per-attempt seed: `hash(f"{problem_id}_{attempt_index}") % 2**32`
   - Could recover 1-3 points from 0.5→1.0 on borderline problems
   - Pure engineering, no model change needed

3. Study the "Condition Mining" approach (39/50 notebook)
   - `[39/50] AIMO3: Condition Mining + TIR w/ python` by parthenos
   - Mines constraints/conditions from problem FIRST, then uses TIR
   - Pull notebook: `kaggle kernels pull parthenos/<slug>`

4. Investigate SymPy-first deterministic solver
   - "AIMO 3 Submission Evolved" notebook — skips LLM reasoning, uses SymPy directly
   - Fully deterministic = no double-run penalty
   - Won't solve hard problems alone, but could complement LLM approach
   - Hybrid: use SymPy for problems it can solve, LLM for the rest

5. Answer verification step
   - After majority voting picks an answer, ask model: "verify this answer satisfies all constraints"
   - Cheap (one inference call per problem), catches obvious errors
   - Not in baseline

6. Adaptive compute reallocation
   - Baseline does early-stop if 4/8 agree but doesn't reallocate saved compute
   - Use saved time to run MORE attempts on problems with no consensus
   - Could flip borderline problems

7. Track leaderboard daily
   - `kaggle competitions leaderboard -c ai-mathematical-olympiad-progress-prize-3`
   - Log to CSV to track movement over time

8. need to focus on running it locally as close as possible, like idk some simulation for time?
9. write out steps first and then execute? have 2 of them working together? well for that we really need to understand how the llm even works
