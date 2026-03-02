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

2. (add more as we go)
