# Changelog: aimo3-solver.ipynb vs baseline-44-50.ipynb

Exhaustive cell-by-cell comparison. Baseline = `baseline-44-50.ipynb` (17 cells). Solver = `notebooks/aimo3-solver.ipynb` (18 cells).

---

## Cells 0-4: IDENTICAL

No changes in pip uninstall, warnings, os/sys/subprocess imports, `set_env()`, or `set_env()` call.

---

## Cell 5 (tiktoken ls + model discovery)

**Baseline:** Single line — `subprocess.run(['ls', '/kaggle/tmp/setup/tiktoken_encodings'])`

**Solver:** Same line PLUS a large addition:

- ADDED: `find_model_path()` function (~40 lines) that auto-discovers the model path from `/kaggle/input/` by:
  1. Checking 4 hardcoded candidate paths (danielhanchen, openai, dataset-style)
  2. Fallback: glob search for any `config.json` with `.safetensors` or `.bin` siblings
  3. Debug dump of `/kaggle/input/` directory tree (5 levels deep) on failure
  4. Raises `RuntimeError` if not found
- ADDED: `MODEL_PATH = find_model_path()` — executes at import time
- ADDED: `print(f'\nUsing model path: {MODEL_PATH}')` debug line

---

## Cell 6 (environment variables): IDENTICAL

## Cell 7 (imports): IDENTICAL

---

## Cell 8 (CFG class) — MAJOR CHANGES

### system_prompt

- CHANGED: Final sentence `'is as important as the final answer.'` now ends with `\n\n` instead of `.` (no newlines)
- ADDED: New section at end of system_prompt:
  ```
  # Efficiency:
  If the problem has an obvious, immediate answer (e.g. direct computation,
  well-known identity, or trivial formula application), state the answer
  directly with brief justification. Do not use Python for problems you can
  solve in 3 lines of reasoning.
  ```

### tool_prompt

- IDENTICAL (no changes)

### preference_prompt

- CHANGED: Last line `'- Validate computational results against known cases or theoretical bounds'` now ends with `\n` (added newline) and continues with new content
- ADDED: New line appended to existing best practices:
  ```
  - For very large exponents (e.g. a^(n!)), use pow(base, exp, mod) or analytical methods -- never materialize the full number
  ```
- ADDED: Entirely new section `# Code Robustness Rules:` with 9 rules:
  1. Self-contained code cells (re-import/re-define everything)
  2. Avoid sympy expressions > few hundred chars; switch to numerical
  3. Geometry: prefer numpy coordinate models over pure symbolic
  4. Combinatorics: verify no duplicates, check injectivity
  5. If 5+ code cells without progress, STOP and restart differently
  6. Never enumerate > 10^6 cases without feasibility check
  7. Convert sympy expressions to `int()` before passing to Python builtins
  8. Common import note: `from sympy.ntheory.modular import crt` (not `sympy.crt`)
  9. If a code cell fails, re-import necessary libraries in next cell

### Config attributes

| Attribute | Baseline | Solver | Notes |
|-----------|----------|--------|-------|
| `model_path` | `'/kaggle/input/gpt-oss-120b/transformers/default/1'` | `MODEL_PATH` | Now uses dynamic discovery from cell 5 |
| `jupyter_timeout` | `6` | `30` | 5x increase |
| `early_stop` | `4` | `5` | +1 |
| `attempts` | `8` | `16` | 2x increase |
| `temp_schedule` | *(not present)* | `[0.1, 0.2, 0.3, 0.4, 0.4, 0.5, 0.5, 0.6, 0.6, 0.7, 0.7, 0.8, 0.8, 0.9, 0.9, 1.0]` | NEW attribute: 16-element list, one temperature per attempt |

All other CFG attributes are IDENTICAL:
- `served_model_name = 'gpt-oss'`
- `kv_cache_dtype = 'fp8_e4m3'`, `dtype = 'auto'`
- `high_problem_timeout = 900`, `base_problem_timeout = 300`
- `notebook_limit = 17400`, `server_timeout = 180`
- `session_timeout = 960`, `sandbox_timeout = 3`
- `stream_interval = 200`, `context_tokens = 65536`, `buffer_tokens = 512`
- `search_tokens = 32`, `top_logprobs = 5`, `batch_size = 256`
- `workers = 16`, `turns = 128`, `seed = 42`
- `gpu_memory_utilization = 0.96`, `temperature = 0.5`, `min_p = 0.02`

---

## Cell 9 (set_seed): IDENTICAL

## Cell 10 (AIMO3Template): IDENTICAL

---

## Cell 11 (AIMO3Sandbox)

- ADDED: Two extra imports in the kernel init code (appears in BOTH `__init__` and `reset` methods):
  ```python
  'import functools\n'
  'import fractions\n'
  ```
  These are inserted between `'import collections\n'` and `'import mpmath\n'`.

All other Sandbox logic is IDENTICAL (port allocation, execute, format_error, close, reset, __del__).

---

## Cell 12 (AIMO3Tool): IDENTICAL

---

## Cell 13 (AIMO3Solver) — MAJOR CHANGES

### `__init__`

- ADDED: `self._start_gpu_monitor()` call between `_wait_for_server()` and `_initialize_kernels()`.

### NEW METHOD: `_start_gpu_monitor()`

- ADDED: ~75 lines. Background thread that polls vLLM `/metrics` endpoint every 5 seconds.
- Logs to `gpu_metrics.log` (CSV: timestamp, elapsed_s, running, waiting, cache_pct, preemptions)
- Tracks: `_peak_running`, `_peak_waiting`, `_peak_cache`, `_total_samples`, `_sum_running`, `_sum_waiting`, `_wait_samples`
- Imports `requests` inside the method

### NEW METHOD: `print_gpu_summary()`

- ADDED: ~20 lines. Prints GPU metrics summary (peak concurrent running/waiting, peak KV cache, averages).
- Provides capacity recommendations based on queuing observed.

### `_process_attempt()` — signature and logging changes

- CHANGED: Added `temperature: float = None` parameter
- CHANGED: Early-return dict now includes `'Temperature': temperature`, `'Conversation': []`, `'Time': 0` (3 new keys)
- ADDED: `conversation_log = []` list
- ADDED: `turn_num = 0` counter
- ADDED: `attempt_start = time.time()` timer
- CHANGED: `turn_num += 1` at start of each turn loop iteration
- CHANGED: Temperature in API call: `self.cfg.temperature` -> `(temperature if temperature is not None else self.cfg.temperature)`
- ADDED: After stream close, log reasoning text to `conversation_log`:
  ```python
  turn_text = ''.join(text_chunks)
  if turn_text.strip():
      conversation_log.append({'turn': turn_num, 'type': 'reasoning', 'text': turn_text})
  ```
- ADDED: When recipient is python, capture `raw_code = last_message.content[0].text` and log code call:
  ```python
  conversation_log.append({
      'turn': turn_num, 'type': 'code_call',
      'code': raw_code, 'output': response_text,
      'error': response_text.startswith('[ERROR]') or 'Traceback' in response_text or 'Error:' in response_text
  })
  ```
- ADDED: `attempt_elapsed = time.time() - attempt_start` at end
- CHANGED: Return dict adds 3 new keys: `'Temperature': temperature`, `'Conversation': conversation_log`, `'Time': round(attempt_elapsed, 1)`

### `_select_answer()` — tie-breaking

- CHANGED: Sort key from `key=lambda x: x['score'], reverse=True` to `key=lambda x: (x['score'], x['votes'], x['answer']), reverse=True`
- This adds deterministic tie-breaking: score (desc), then votes (desc), then answer value (desc)

### `solve_problem()` — temperature schedule, retry logic, early-stop behavior

- CHANGED: Task creation now uses temperature schedule:
  ```python
  # Baseline:
  tasks.append((self.cfg.system_prompt, attempt_index))

  # Solver:
  if hasattr(self.cfg, 'temp_schedule') and self.cfg.temp_schedule and attempt_index < len(self.cfg.temp_schedule):
      temp = self.cfg.temp_schedule[attempt_index]
  else:
      temp = self.cfg.temperature
  tasks.append((self.cfg.system_prompt, attempt_index, temp))
  ```
- CHANGED: Task unpacking from `(system_prompt, attempt_index)` to `(system_prompt, attempt_index, attempt_temp)`
- CHANGED: `_process_attempt` call now passes `attempt_temp` as `temperature` argument
- CHANGED: Early-stop behavior fundamentally reworked:
  - **Baseline:** On early stop, sets stop_event, cancels futures, and `break`s out of the `as_completed` loop (stops collecting results)
  - **Solver:** On early stop, sets stop_event but does NOT break or cancel futures. Collects ALL results. Comment: "Collect ALL results -- don't break on early stop. Early stop signals remaining attempts to exit quickly, but we still gather everything for a robust vote."
  - Also wrapped the early-stop check in `if not stop_event.is_set():` guard to avoid re-triggering
- CHANGED: `self.problems_remaining` decrement moved outside the `finally` block (was inside in baseline)
- ADDED: `self._last_detailed_results = detailed_results` — stores results for test framework access
- ADDED: All-None retry logic (~30 lines): If no valid answers and >30s remain before deadline, retries with `cfg.attempts` more attempts at `min(temp + 0.2, 1.0)` temperature. Uses separate `retry_stop` event and `retry_executor`.
- CHANGED: Results display now filters columns:
  ```python
  # Baseline: display(results_dataframe) with all columns
  # Solver: display only specific columns
  display_cols = ['Attempt', 'Answer', 'Python Calls', 'Python Errors', 'Response Length', 'Entropy', 'Time']
  display_df = results_dataframe[[c for c in display_cols if c in results_dataframe.columns]].copy()
  ```
  This hides `Conversation` and `Temperature` from the display output.

### All other methods IDENTICAL:
- `_preload_model_weights`, `_start_server`, `_wait_for_server`, `_initialize_kernels`, `_scan_for_answer`, `_compute_mean_entropy`, `__del__`

---

## Cell 14 (solver instantiation): IDENTICAL

## Cell 15 (predict function): IDENTICAL

---

## Cell 16 (inference server) — test CSV discovery

- CHANGED: Added dynamic test CSV path discovery:
  ```python
  # Baseline: hardcoded path
  inference_server.run_local_gateway(
      ('/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv',)
  )

  # Solver: tries multiple candidates
  test_csv_candidates = [
      '/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv',
      '/kaggle/input/competitions/ai-mathematical-olympiad-progress-prize-3/test.csv',
  ]
  test_csv = next((p for p in test_csv_candidates if os.path.isfile(p)), test_csv_candidates[0])
  print(f'Using test CSV: {test_csv}')
  inference_server.run_local_gateway((test_csv,))
  ```
- CHANGED: Minor whitespace: blank line after `inference_server.serve()` removed

---

## Cell 17 (SOLVER ONLY — NEW CELL)

Entirely new cell (~25,164 chars). **Enhanced Test Framework with Maximum Diagnostic Logging.**

Only runs when `not os.getenv('KAGGLE_IS_COMPETITION_RERUN')` (i.e., test runs only).

### TeeLogger class
- Writes to both stdout and `/kaggle/working/diagnostic.log` (and stderr to `diagnostic_stderr.log`)
- Replaces `sys.stdout` and `sys.stderr` at module level

### `_print_attempt_full(r, expected)`
- Prints complete diagnostic for one attempt: answer, temperature, entropy, code calls, errors, tokens, time
- Extracts all import statements from conversation log
- Prints full conversation flow: reasoning text (every char) and code calls with output

### `_get_gpu_stats()`
- Returns GPU memory stats via PyTorch CUDA if available

### `run_test_batch(name, problems, solver)`
- Runs a batch of problems with full diagnostic output per problem
- Per-problem diagnostics: status, vote distribution, wrong-answer analysis, full attempt logs, running totals
- Batch summary: score, timing stats (min, max, median)

### `load_csv_problems(problems_csv, answers_csv)`
- Loads problems/answers from separate CSV files for Tier 2

### TIER 0: Priority Debug (4 problem slots)
Two problems, each run TWICE (duplicate entries):
1. **86e8e5** (Norwegian numbers / 3^{2025!}) — answer: 8687
2. **76aef9** (Players A and B game / 1997 copies) — answer: 8

### TIER 1: At-Risk Problems (6 problems)
1. **424e18** (Tournament with 2^20 runners) — answer: 21818
2. **dd7f5e** (Shifty functions / F set) — answer: 160
3. **b4ec47** (Rectangles in dodecagon) — answer: 315
4. **2d282e** (Partition students into groups) — answer: 117
5. **8fea51** (Base-7 representation) — answer: 42
6. **269012** (Cube-shaped container / water volume) — answer: 751

### TIER 2: Val Bench
Loaded from CSV at `/kaggle/input/aimo3-test-data/test_problems.csv` and `test_answers.csv`. Skipped if files not found.

### Double-Run Retry
Re-runs all failed problems and computes double-run scoring simulation (1.0 pts if both correct, 0.5 if one correct, 0.0 if both wrong).

### GPU Metrics Summary
Calls `solver.print_gpu_summary()` from the new method added in cell 13.

### Final Summary
Displays overall score, timing, summary DataFrame, wrong-answer breakdown, correct-answer average time.

---

## Summary of All Changes

| Category | Count | Description |
|----------|-------|-------------|
| New cells | 1 | Cell 17: Full test framework |
| Modified cells | 5 | Cells 5, 8, 11, 13, 16 |
| Identical cells | 12 | Cells 0-4, 6-7, 9-10, 12, 14-15 |

### Key Behavioral Differences

1. **Model path**: Hardcoded -> dynamic discovery via `find_model_path()`
2. **Attempts**: 8 -> 16 (doubled)
3. **Early stop threshold**: 4 -> 5
4. **Jupyter timeout**: 6s -> 30s (5x increase)
5. **Temperature**: Single value (0.5) -> per-attempt schedule (0.1 to 1.0 in 16 steps)
6. **Early-stop behavior**: Now collects ALL results instead of breaking on early stop
7. **All-None retry**: New fallback that retries all attempts at higher temperature if first pass gets no valid answers
8. **Vote tie-breaking**: Now deterministic (score, votes, answer value)
9. **Conversation logging**: Full turn-by-turn logging of reasoning and code calls
10. **GPU monitoring**: Background vLLM metrics polling every 5s
11. **Sandbox imports**: Added `functools` and `fractions` to kernel init
12. **Prompt additions**: Efficiency directive + 9 code robustness rules + bigint hint
13. **Test framework**: 3-tier test suite with full diagnostic logging and double-run retry scoring
14. **Test CSV path**: Dynamic discovery across multiple Kaggle path patterns
