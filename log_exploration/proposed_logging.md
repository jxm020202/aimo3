# Proposed Logging Enhancements for v24

> Based on gap analysis of v22/v23 diagnostic.log. Each proposal includes exact format, code location, and priority.

---

## Per-Attempt Logging

### [Per-Attempt] Temperature Tracking
- **WHAT**: Log the temperature used for each attempt
- **WHY**: #1 blind spot in v22. Can't correlate temperature with accuracy. The temp_schedule is our most important hyperparameter and we're tuning it blind.
- **WHERE**: `_print_attempt_full()` in cell 17. Also `_process_attempt()` return dict already has `Temperature` field.
- **FORMAT**: Already fixed in v23. v23 logs: `--- Attempt N [STATUS] answer=X expected=Y temp=T entropy=E ---`
- **PRIORITY**: High (fixed in v23)

### [Per-Attempt] Stop Reason
- **WHAT**: Log WHY the attempt stopped: `answer_found`, `deadline_exceeded`, `stop_event`, `context_exhausted`, `no_tokens`, `max_turns`
- **WHY**: 21% of Nones are "no-code-generated" — could be context exhaustion, early termination, or model simply not writing code. Without stop_reason we can't tell.
- **WHERE**: `_process_attempt()` in cell 13. Add `stop_reason` to the return dict. Multiple break points exist in the turn loop; each should set a reason.
- **FORMAT**:
  ```
  --- Attempt N [STATUS] answer=X expected=Y temp=T entropy=E stop=answer_found ---
  ```
  Stop reasons: `answer_found`, `answer_final_channel`, `deadline`, `stop_event`, `context_exhausted`, `no_tokens`, `max_turns`, `exception`
- **PRIORITY**: High

### [Per-Attempt] Extraction Method
- **WHAT**: Log which regex pattern in `_scan_for_answer()` actually matched (or that none matched)
- **WHY**: 40% of Nones are extraction failures. We need to know if `\boxed{}` is working or if we're relying on fallbacks. Also need to know when ALL patterns fail despite the model having an answer.
- **WHERE**: `_scan_for_answer()` in cell 13. Return `(answer, method)` tuple instead of just `answer`. Methods: `boxed`, `final_answer_is`, `answer_is`, `answer_colon`, `none`.
- **FORMAT**:
  ```
  --- Attempt N [STATUS] answer=X expected=Y temp=T entropy=E extract=boxed ---
  ```
- **PRIORITY**: High

### [Per-Attempt] Failed Extraction Text
- **WHAT**: When `_scan_for_answer()` returns None, log the last 200 chars of reasoning text that was searched
- **WHY**: If the model said "the answer is 42" but our regex missed it, we can fix the regex. Currently invisible.
- **WHERE**: `_process_attempt()` in cell 13, after the streaming loop. When `final_answer is None`, log the search window.
- **FORMAT**:
  ```
  [EXTRACTION FAILED] Last 200 chars: "...therefore the final answer is forty-two"
  ```
- **PRIORITY**: High

### [Per-Attempt] Answer Seed
- **WHAT**: Log the `attempt_seed` used for the vLLM random seed
- **WHY**: Enables reproduction of specific attempts for debugging
- **WHERE**: `_process_attempt()` in cell 13. Already computed: `attempt_seed = int(math.pow(self.cfg.seed + attempt_index, 2))`
- **FORMAT**: `seed=N` appended to attempt stats line
- **PRIORITY**: Low

### [Per-Attempt] Is Retry
- **WHAT**: Boolean flag indicating if this attempt is from the retry block (all-None retry)
- **WHY**: Can't distinguish first-round attempts from retry attempts. Retry uses different temp. Need to measure retry success rate.
- **WHERE**: `solve_problem()` retry block in cell 13. Add `'is_retry': True` to the result dict.
- **FORMAT**: `retry=True` appended to attempt header
- **PRIORITY**: Medium

---

## Per-Turn Logging

### [Per-Turn] Turn Timing
- **WHAT**: Wall clock time for each turn, broken into: (a) LLM inference time, (b) code execution time
- **WHY**: Can't optimize the right bottleneck. "Is this problem slow because of thinking or code execution?" Currently impossible to answer.
- **WHERE**: `_process_attempt()` turn loop in cell 13. Wrap the streaming section and the `process_sync_plus()` call with `time.time()`.
- **FORMAT**:
  ```
  [Turn N REASONING] (2581 chars, 3.2s inference)
  [Turn N CODE] (exec=1.8s)
  ```
- **PRIORITY**: High

### [Per-Turn] Remaining Context Window
- **WHAT**: Log `max_tokens` (remaining context) at the start of each turn
- **WHY**: Shows context window consumption rate. If max_tokens drops below buffer, the attempt is about to be context-killed. Currently: the attempt just silently stops.
- **WHERE**: `_process_attempt()` turn loop in cell 13. Already computed: `max_tokens = self.cfg.context_tokens - len(prompt_ids)`
- **FORMAT**: `[Turn N] ctx_remaining=12345`
- **PRIORITY**: Medium

### [Per-Turn] Code Cell Length
- **WHAT**: Character count and line count of the code cell
- **WHY**: Correlate code complexity with errors. Long code cells might be more error-prone.
- **WHERE**: `_process_attempt()` in cell 13, in the `if last_message.recipient == 'python':` block.
- **FORMAT**: `[Turn N CODE] (42 lines, 1234 chars)`
- **PRIORITY**: Low

### [Per-Turn] Is Error Recovery
- **WHAT**: Flag indicating this code cell is a retry after a previous error in the same attempt
- **WHY**: Error cascade analysis is approximate. Knowing "this is a retry of failed code" enables measuring recovery rate.
- **WHERE**: `_process_attempt()` in cell 13. Track `last_error = True` state and check on next code turn.
- **FORMAT**: `[Turn N CODE] [RETRY after error]`
- **PRIORITY**: Medium

---

## Per-Problem Logging

### [Per-Problem] Topic Classification
- **WHAT**: Auto-classify problems by mathematical topic based on keywords in problem text
- **WHY**: Can't identify weak areas. "Are we bad at geometry?" is unanswerable.
- **WHERE**: `run_test_batch()` in cell 17. Add a lightweight classifier using keyword matching.
- **FORMAT**:
  ```
  [1/60] Problem abc123 | Expected: 42 | Topic: number-theory
  ```
  Topics: `algebra`, `number-theory`, `combinatorics`, `geometry`, `probability`, `calculus`, `mixed`
  Keyword rules:
  - geometry: polygon, triangle, circle, angle, area, perpendicular, circumscribe
  - number-theory: prime, divisor, modular, gcd, remainder, coprime, factorial
  - combinatorics: permutation, combination, counting, arrangement, subset, partition
  - algebra: polynomial, equation, inequality, function, sequence, series
  - probability: probability, expected value, random, dice, coin
- **PRIORITY**: High

### [Per-Problem] Answer Evolution
- **WHAT**: Track ALL `\boxed{}` values found during each attempt, not just the final one
- **WHY**: Detect "overthinking" — model finds correct answer then changes it. This is recoverable with a "first-answer" strategy.
- **WHERE**: `_process_attempt()` in cell 13. Instead of immediately breaking on `final_answer`, append to a list: `answer_history.append((turn_num, answer))`.
- **FORMAT**:
  ```
  answer_history: [(1, 42), (3, 42), (5, 17)]  <- changed answer at turn 5
  ```
- **PRIORITY**: High

### [Per-Problem] Vote Weights
- **WHAT**: Log the entropy-weighted vote scores alongside raw vote counts
- **WHY**: Vote margin tells us if more attempts could flip the result. Currently only visible in notebook DataFrame output, not in diagnostic.log.
- **WHERE**: `_select_answer()` in cell 13. Already computed: `scored_answers` list with weights.
- **FORMAT**:
  ```
  Votes: {42: 5, 17: 2} | Scores: {42: 12.5, 17: 3.1} | Margin: 9.4
  ```
- **PRIORITY**: High

### [Per-Problem] Difficulty Estimate
- **WHAT**: After N attempts, estimate problem difficulty based on: none rate, error rate, answer diversity, and time consumed
- **WHY**: Difficulty correlates with whether to spend more budget. Easy problem (early stop at 3) vs hard problem (needs all 16 attempts).
- **WHERE**: `solve_problem()` in cell 13, after collecting results.
- **FORMAT**:
  ```
  Difficulty: HARD (5/8 none, 3 unique answers, 0 early stop)
  ```
  Levels: `TRIVIAL` (early stop + high consensus), `EASY` (early stop, some nones), `MODERATE` (no early stop, correct found), `HARD` (many nones, diverse answers), `UNSOLVABLE` (all none or all wrong)
- **PRIORITY**: Medium

---

## Aggregate / Session-Level Logging

### [Aggregate] Per-Temperature Accuracy Table
- **WHAT**: At the end of each batch, print accuracy broken down by temperature
- **WHY**: Direct comparison: "temp=0.3 → 45% correct, temp=0.7 → 30% correct". The single most actionable insight for tuning.
- **WHERE**: `run_test_batch()` in cell 17, in the batch summary section.
- **FORMAT**:
  ```
  Temperature Accuracy:
    temp=0.1:  12/60 correct (20.0%)  12 wrong  36 none
    temp=0.3:  45/240 correct (18.8%)  30 wrong  165 none
    temp=0.5:  ...
  ```
- **PRIORITY**: High (v23 has per-attempt temp, but no aggregate table)

### [Aggregate] Error Recovery Rate
- **WHAT**: How often does the model successfully produce output after a code error?
- **WHY**: Measures whether error tolerance (continuing after errors) is worth the token cost.
- **WHERE**: `run_test_batch()` summary in cell 17.
- **FORMAT**:
  ```
  Error Recovery: 45/120 errors recovered (37.5%) | Avg recovery turns: 1.3
  ```
- **PRIORITY**: Medium

### [Aggregate] Time Budget Efficiency
- **WHAT**: For each batch, how much of the allocated time budget was actually used?
- **WHY**: Underutilization means we could run more attempts. Over-budget means we're stealing from later problems.
- **WHERE**: `run_test_batch()` in cell 17.
- **FORMAT**:
  ```
  Budget Utilization: 3200/5400s used (59.3%) | 2200s unused
  Per-problem: avg 53s used of 90s budget (59%)
  ```
- **PRIORITY**: Medium

### [Aggregate] KV Cache Pressure
- **WHAT**: Correlate gpu_metrics.log timestamps with problem boundaries to show per-problem cache usage
- **WHY**: KV cache is THE binding constraint. High cache pressure = degraded generation quality.
- **WHERE**: `run_test_batch()` in cell 17. Read gpu_metrics.log timestamps and match to problem start/end times.
- **FORMAT**:
  ```
  KV Cache: peak=87.3% at problem 45 | avg=62.1% | pressure events (>90%): 3
  ```
- **PRIORITY**: Medium

### [Aggregate] Extraction Failure Summary
- **WHAT**: Breakdown of which `_scan_for_answer()` regex matched across all attempts
- **WHY**: Shows if our extraction is fragile. If 80% use `\boxed{}` and 20% fall through, that's fine. If 50% rely on fallbacks, we need better prompting.
- **WHERE**: End of `run_test_batch()` in cell 17.
- **FORMAT**:
  ```
  Extraction Methods: boxed=310 (65%) | final_answer_is=45 (9%) | answer_is=20 (4%) | FAILED=105 (22%)
  ```
- **PRIORITY**: High

---

## Implementation Priority

### Must-have for v24 (6 items):
1. **Stop reason** per attempt — explains 21% of Nones
2. **Extraction method + failed text** — explains 40% of Nones
3. **Per-turn timing** (inference vs code) — identifies bottleneck
4. **Answer evolution** (all boxed values) — detects overthinking
5. **Vote weights + margin** in diagnostic.log — measures vote robustness
6. **Per-temperature accuracy table** in batch summary — guides temp tuning

### Should-have for v24 (5 items):
7. Topic classification
8. Difficulty estimate
9. Remaining context window per turn
10. Is-retry flag
11. Error recovery rate

### Nice-to-have (4 items):
12. Code cell length
13. Attempt seed
14. KV cache per-problem correlation
15. Is-error-recovery flag per turn

### Estimated code changes:
- Cell 13 (`AIMO3Solver`): ~60 lines of changes across `_process_attempt()`, `_scan_for_answer()`, `_select_answer()`
- Cell 17 (test framework): ~40 lines in `_print_attempt_full()` and `run_test_batch()` summary
- Total: ~100 lines. Low risk, high diagnostic value.
