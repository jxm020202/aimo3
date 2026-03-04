#!/usr/bin/env python3
"""
Deep analysis of timeout patterns in AIMO3 diagnostic logs.

Questions answered:
1. Which libraries/functions appear most in timed-out code cells?
2. Timeout cascades: if first N cells timeout, is the attempt doomed?
3. Turn-level timeout distribution (early vs late)
4. Code patterns in timed-out cells (brute force, symbolic, combinatorial)
5. Time wasted on timeout cascades
6. Per-problem timeout concentration
"""

import sys
import os
import re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def classify_timeout_code(code):
    """Classify what kind of computation a timed-out code cell is doing."""
    patterns = {
        'nested_for_loops': r'for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in',
        'triple_nested_loops': r'for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in',
        'itertools.product': r'itertools\.product',
        'itertools.combinations': r'itertools\.combinations',
        'itertools.permutations': r'itertools\.permutations',
        'sp.solve': r'sp\.solve|sympy\.solve|solve\(',
        'sp.simplify': r'sp\.simplify|simplify\(',
        'sp.expand': r'sp\.expand|expand\(',
        'sp.integrate': r'sp\.integrate|integrate\(',
        'sp.factor': r'sp\.factor\b',
        'sp.series': r'sp\.series|\.series\(',
        'milp': r'milp\(',
        'linprog': r'linprog\(',
        'scipy.optimize': r'scipy\.optimize',
        'numpy_linalg': r'np\.linalg|numpy\.linalg',
        'large_range': r'range\(\s*\d{5,}\s*\)|range\(\s*\d+\s*\*\*\s*\d+\s*\)',
        'while_true': r'while\s+True|while\s+1\b',
        'recursive_def': r'lru_cache|@cache|recursion|recursive',
        'factorial': r'factorial\(|math\.factorial',
        'pow_large': r'pow\(\s*\d+\s*,\s*\d{4,}|pow\(\s*\w+\s*,\s*\d{4,}',
        'brute_force_comment': r'brute.?force|exhaustive|enumerate all|try all',
        'backtracking': r'backtrack|DFS|dfs|BFS|bfs',
        'random_sampling': r'random\.',
    }
    found = []
    for name, pat in patterns.items():
        if re.search(pat, code, re.IGNORECASE | re.MULTILINE):
            found.append(name)
    return found


def extract_imports(code):
    """Extract library imports from code."""
    imports = []
    for line in code.split('\n'):
        line = line.strip()
        if line.startswith('import ') or line.startswith('from '):
            imports.append(line)
        # Also detect usage patterns
    libs = set()
    if 'sympy' in code or 'sp.' in code:
        libs.add('sympy')
    if 'numpy' in code or 'np.' in code:
        libs.add('numpy')
    if 'scipy' in code:
        libs.add('scipy')
    if 'itertools' in code:
        libs.add('itertools')
    if 'milp' in code:
        libs.add('milp')
    if 'networkx' in code or 'nx.' in code:
        libs.add('networkx')
    if 'random' in code:
        libs.add('random')
    if 'math.' in code or 'import math' in code:
        libs.add('math')
    if 'fractions' in code or 'Fraction' in code:
        libs.add('fractions')
    if 'mpmath' in code or 'mp.' in code:
        libs.add('mpmath')
    if 'collections' in code:
        libs.add('collections')
    if 'functools' in code or 'lru_cache' in code:
        libs.add('functools')
    return libs


def estimate_search_space(code):
    """Try to estimate the search space size from range() calls and loops."""
    # Find range() calls with numeric args
    ranges = re.findall(r'range\(\s*(\d+)\s*(?:,\s*(\d+)\s*)?\)', code)
    sizes = []
    for r in ranges:
        if r[1]:
            sizes.append(int(r[1]) - int(r[0]))
        else:
            sizes.append(int(r[0]))
    return sizes


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 timeout_deep_dive.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.\n")

    # Collect all timeout turns
    timeout_turns = []  # (problem_id, attempt_num, turn_num, code, total_turns_in_attempt)
    all_attempts = []  # (problem_id, attempt_num, turns, timeout_turns_list, answer, correct)

    for prob in problems:
        for att in prob.attempts:
            att_timeouts = []
            for turn in att.turns:
                is_timeout = turn.is_error and 'timed out' in turn.output.lower()
                if is_timeout:
                    timeout_turns.append((prob.problem_id, att.attempt_num, turn.turn_num,
                                         turn.code, len(att.turns), prob.correct))
                    att_timeouts.append(turn.turn_num)
            all_attempts.append((prob.problem_id, att.attempt_num, len(att.turns),
                                 att_timeouts, att.answer, prob.correct, att.time_s))

    print("=" * 80)
    print("  TIMEOUT DEEP DIVE ANALYSIS")
    print("=" * 80)

    # ── 1. Libraries in timed-out code ──
    print("\n" + "─" * 70)
    print("1. LIBRARIES PRESENT IN TIMED-OUT CODE CELLS")
    print("─" * 70)

    lib_counter = Counter()
    for pid, anum, tnum, code, total, correct in timeout_turns:
        libs = extract_imports(code)
        for lib in libs:
            lib_counter[lib] += 1

    print(f"\n  Total timeout cells: {len(timeout_turns)}\n")
    print(f"  {'Library':<20} {'Timeouts':>10} {'% of timeouts':>15}")
    print(f"  {'─'*20} {'─'*10} {'─'*15}")
    for lib, count in lib_counter.most_common(20):
        pct = count / len(timeout_turns) * 100
        print(f"  {lib:<20} {count:>10} {pct:>14.1f}%")

    # ── 2. Code patterns in timed-out cells ──
    print("\n" + "─" * 70)
    print("2. CODE PATTERNS IN TIMED-OUT CELLS")
    print("─" * 70)

    pattern_counter = Counter()
    for pid, anum, tnum, code, total, correct in timeout_turns:
        patterns = classify_timeout_code(code)
        for p in patterns:
            pattern_counter[p] += 1

    print(f"\n  {'Pattern':<30} {'Count':>8} {'% of timeouts':>15}")
    print(f"  {'─'*30} {'─'*8} {'─'*15}")
    for pat, count in pattern_counter.most_common(25):
        pct = count / len(timeout_turns) * 100
        print(f"  {pat:<30} {count:>8} {pct:>14.1f}%")

    # ── 3. Timeout distribution by turn number ──
    print("\n" + "─" * 70)
    print("3. TIMEOUTS BY TURN NUMBER")
    print("─" * 70)

    turn_timeouts = Counter()
    turn_totals = Counter()

    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                turn_totals[turn.turn_num] += 1
                if turn.is_error and 'timed out' in turn.output.lower():
                    turn_timeouts[turn.turn_num] += 1

    print(f"\n  {'Turn':<8} {'Timeouts':>10} {'Total':>10} {'Timeout%':>10} {'Visual'}")
    print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*10} {'─'*30}")

    # Show first 20 turns and summarize rest
    early_to = sum(turn_timeouts[t] for t in range(1, 6))
    early_total = sum(turn_totals[t] for t in range(1, 6))
    mid_to = sum(turn_timeouts[t] for t in range(6, 16))
    mid_total = sum(turn_totals[t] for t in range(6, 16))
    late_to = sum(turn_timeouts[t] for t in turn_timeouts if t >= 16)
    late_total = sum(turn_totals[t] for t in turn_totals if t >= 16)

    for t in sorted(turn_totals.keys())[:25]:
        to = turn_timeouts.get(t, 0)
        tot = turn_totals[t]
        pct = to / tot * 100 if tot > 0 else 0
        bar = '#' * int(pct / 2)
        print(f"  {t:<8} {to:>10} {tot:>10} {pct:>9.1f}% {bar}")

    print(f"\n  Summary:")
    print(f"  Turns 1-5 (early):  {early_to:>5} timeouts / {early_total:>5} total = {early_to/early_total*100:.1f}%")
    print(f"  Turns 6-15 (mid):   {mid_to:>5} timeouts / {mid_total:>5} total = {mid_to/mid_total*100:.1f}%")
    print(f"  Turns 16+ (late):   {late_to:>5} timeouts / {late_total:>5} total = {late_to/late_total*100:.1f}%")

    # ── 4. Timeout cascades ──
    print("\n" + "─" * 70)
    print("4. TIMEOUT CASCADES: Does early timeout doom the attempt?")
    print("─" * 70)

    # For each attempt, check: if first N code cells timeout, what's the success rate?
    first_n_timeout_success = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})

    for pid, anum, total_turns, att_timeouts, answer, correct, time_s in all_attempts:
        # Check if first 1, 2, 3 code cells are timeouts
        if not att_timeouts:
            first_n_timeout_success['0_timeouts_early']['total'] += 1
            if answer is not None and correct:
                first_n_timeout_success['0_timeouts_early']['correct'] += 1
            elif answer is not None:
                first_n_timeout_success['0_timeouts_early']['wrong'] += 1
            else:
                first_n_timeout_success['0_timeouts_early']['none'] += 1
            continue

        # Count timeouts in first 5 turns
        early_timeouts = sum(1 for t in att_timeouts if t <= 5)
        key = f'{early_timeouts}_timeouts_in_first5'
        first_n_timeout_success[key]['total'] += 1
        if answer is not None and correct:
            first_n_timeout_success[key]['correct'] += 1
        elif answer is not None:
            first_n_timeout_success[key]['wrong'] += 1
        else:
            first_n_timeout_success[key]['none'] += 1

    print(f"\n  {'Early timeout pattern':<30} {'Total':>7} {'Correct':>9} {'Wrong':>7} {'None':>7} {'Correct%':>10}")
    print(f"  {'─'*30} {'─'*7} {'─'*9} {'─'*7} {'─'*7} {'─'*10}")
    for key in sorted(first_n_timeout_success.keys()):
        d = first_n_timeout_success[key]
        answered = d['correct'] + d['wrong']
        pct = d['correct'] / answered * 100 if answered > 0 else 0
        print(f"  {key:<30} {d['total']:>7} {d['correct']:>9} {d['wrong']:>7} {d['none']:>7} {pct:>9.1f}%")

    # ── 5. Total timeout count per attempt vs success ──
    print("\n" + "─" * 70)
    print("5. TOTAL TIMEOUTS PER ATTEMPT vs SUCCESS RATE")
    print("─" * 70)

    timeout_count_buckets = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0, 'time': 0})

    for pid, anum, total_turns, att_timeouts, answer, correct, time_s in all_attempts:
        n_to = len(att_timeouts)
        if n_to == 0:
            bucket = '0'
        elif n_to <= 2:
            bucket = '1-2'
        elif n_to <= 5:
            bucket = '3-5'
        elif n_to <= 10:
            bucket = '6-10'
        else:
            bucket = '11+'
        timeout_count_buckets[bucket]['total'] += 1
        timeout_count_buckets[bucket]['time'] += time_s
        if answer is not None and correct:
            timeout_count_buckets[bucket]['correct'] += 1
        elif answer is not None:
            timeout_count_buckets[bucket]['wrong'] += 1
        else:
            timeout_count_buckets[bucket]['none'] += 1

    print(f"\n  {'Timeouts/attempt':<20} {'Total':>7} {'Correct':>9} {'Wrong':>7} {'None':>7} {'Correct%':>10} {'Avg Time':>10}")
    print(f"  {'─'*20} {'─'*7} {'─'*9} {'─'*7} {'─'*7} {'─'*10} {'─'*10}")
    for bucket in ['0', '1-2', '3-5', '6-10', '11+']:
        d = timeout_count_buckets[bucket]
        if d['total'] == 0:
            continue
        answered = d['correct'] + d['wrong']
        pct = d['correct'] / answered * 100 if answered > 0 else 0
        avg_time = d['time'] / d['total']
        print(f"  {bucket:<20} {d['total']:>7} {d['correct']:>9} {d['wrong']:>7} {d['none']:>7} {pct:>9.1f}% {avg_time:>9.0f}s")

    # ── 6. Consecutive timeout streaks ──
    print("\n" + "─" * 70)
    print("6. CONSECUTIVE TIMEOUT STREAKS")
    print("─" * 70)

    streak_counter = Counter()
    max_streaks = []

    for pid, anum, total_turns, att_timeouts, answer, correct, time_s in all_attempts:
        if not att_timeouts:
            continue
        # Find consecutive timeout streaks
        att_timeouts_sorted = sorted(att_timeouts)
        streak = 1
        max_streak = 1
        for i in range(1, len(att_timeouts_sorted)):
            if att_timeouts_sorted[i] == att_timeouts_sorted[i-1] + 1:
                streak += 1
                max_streak = max(max_streak, streak)
            elif att_timeouts_sorted[i] == att_timeouts_sorted[i-1] + 2:
                # Allow 1 gap (non-code turn between)
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak_counter[streak] += 1
                streak = 1
        streak_counter[streak] += 1
        max_streak = max(max_streak, streak)
        if max_streak >= 3:
            max_streaks.append((pid, anum, max_streak, len(att_timeouts), total_turns, correct, answer))

    print(f"\n  {'Streak length':<15} {'Count':>8}")
    print(f"  {'─'*15} {'─'*8}")
    for length in sorted(streak_counter.keys()):
        print(f"  {length:<15} {streak_counter[length]:>8}")

    print(f"\n  Attempts with 3+ consecutive timeouts: {len(max_streaks)}")
    if max_streaks:
        max_streaks.sort(key=lambda x: -x[2])
        print(f"\n  {'Problem':<10} {'Att':>5} {'MaxStreak':>10} {'TotalTO':>9} {'Turns':>7} {'Answer':>10}")
        print(f"  {'─'*10} {'─'*5} {'─'*10} {'─'*9} {'─'*7} {'─'*10}")
        for pid, anum, ms, nto, turns, correct, answer in max_streaks[:20]:
            ans_str = str(answer) if answer is not None else 'None'
            print(f"  {pid:<10} {anum:>5} {ms:>10} {nto:>9} {turns:>7} {ans_str:>10}")

    # ── 7. Time wasted on timeout cascades ──
    print("\n" + "─" * 70)
    print("7. TIME COST OF TIMEOUTS")
    print("─" * 70)

    # Each timeout wastes 30 seconds
    total_timeout_time = len(timeout_turns) * 30
    total_attempt_time = sum(time_s for _, _, _, _, _, _, time_s in all_attempts)

    print(f"\n  Total timeouts:       {len(timeout_turns)}")
    print(f"  Time per timeout:     30s (hard limit)")
    print(f"  Total timeout time:   {total_timeout_time}s ({total_timeout_time/60:.0f} min)")
    print(f"  Total attempt time:   {total_attempt_time:.0f}s ({total_attempt_time/60:.0f} min)")
    print(f"  Timeout % of total:   {total_timeout_time/total_attempt_time*100:.1f}%")
    print(f"\n  If we halved timeouts, we'd save: {total_timeout_time/2/60:.0f} min")
    print(f"  That's roughly {total_timeout_time/2/200:.0f} extra clean attempts")

    # ── 8. Per-problem timeout concentration ──
    print("\n" + "─" * 70)
    print("8. PER-PROBLEM TIMEOUT CONCENTRATION")
    print("─" * 70)

    prob_timeouts = defaultdict(lambda: {'timeouts': 0, 'total_turns': 0, 'correct': False, 'problem_id': ''})
    for prob in problems:
        pid = prob.problem_id
        prob_timeouts[pid]['problem_id'] = pid
        prob_timeouts[pid]['correct'] = prob.correct
        for att in prob.attempts:
            for turn in att.turns:
                prob_timeouts[pid]['total_turns'] += 1
                if turn.is_error and 'timed out' in turn.output.lower():
                    prob_timeouts[pid]['timeouts'] += 1

    sorted_probs = sorted(prob_timeouts.values(), key=lambda x: -x['timeouts'])

    print(f"\n  {'Problem':<10} {'Timeouts':>10} {'Turns':>8} {'TO%':>8} {'Correct':>9}")
    print(f"  {'─'*10} {'─'*10} {'─'*8} {'─'*8} {'─'*9}")
    for p in sorted_probs[:20]:
        pct = p['timeouts'] / p['total_turns'] * 100 if p['total_turns'] > 0 else 0
        c = 'Yes' if p['correct'] else 'No'
        print(f"  {p['problem_id']:<10} {p['timeouts']:>10} {p['total_turns']:>8} {pct:>7.1f}% {c:>9}")

    # ── 9. Search space analysis ──
    print("\n" + "─" * 70)
    print("9. SEARCH SPACE SIZE IN TIMED-OUT CODE")
    print("─" * 70)

    large_range_examples = []
    for pid, anum, tnum, code, total, correct in timeout_turns:
        sizes = estimate_search_space(code)
        if sizes:
            max_size = max(sizes)
            if max_size >= 10000:
                large_range_examples.append((pid, anum, tnum, max_size, code[:200]))

    large_range_examples.sort(key=lambda x: -x[3])
    print(f"\n  Timeout cells with range() >= 10,000:")
    print(f"  Found: {len(large_range_examples)} cells\n")

    print(f"  {'Problem':<10} {'Att':>5} {'Turn':>6} {'Max range()':>12} {'Code snippet (first 120 chars)'}")
    print(f"  {'─'*10} {'─'*5} {'─'*6} {'─'*12} {'─'*50}")
    for pid, anum, tnum, maxr, snippet in large_range_examples[:20]:
        snippet_clean = snippet.replace('\n', ' | ')[:80]
        print(f"  {pid:<10} {anum:>5} {tnum:>6} {maxr:>12,} {snippet_clean}")

    # ── 10. What does the model do AFTER a timeout? ──
    print("\n" + "─" * 70)
    print("10. MODEL BEHAVIOR AFTER TIMEOUT")
    print("─" * 70)

    after_timeout = {'retries_same': 0, 'switches_approach': 0, 'reduces_scope': 0,
                     'gives_up': 0, 'no_next_turn': 0, 'total': 0}

    for prob in problems:
        for att in prob.attempts:
            for i, turn in enumerate(att.turns):
                if turn.is_error and 'timed out' in turn.output.lower():
                    after_timeout['total'] += 1
                    if i + 1 < len(att.turns):
                        next_turn = att.turns[i + 1]
                        next_code = next_turn.code.lower()
                        next_reasoning = next_turn.reasoning_text.lower() if hasattr(next_turn, 'reasoning_text') else ''

                        # Check if they reduced scope
                        if any(w in next_reasoning for w in ['smaller', 'reduce', 'simpler', 'fewer', 'limit', 'optimize']):
                            after_timeout['reduces_scope'] += 1
                        elif any(w in next_reasoning for w in ['different approach', 'alternative', 'instead', 'try another']):
                            after_timeout['switches_approach'] += 1
                        else:
                            after_timeout['retries_same'] += 1
                    else:
                        after_timeout['no_next_turn'] += 1

    print(f"\n  Total timeouts analyzed: {after_timeout['total']}")
    print(f"  Model reduces scope:    {after_timeout['reduces_scope']:>5} ({after_timeout['reduces_scope']/after_timeout['total']*100:.1f}%)")
    print(f"  Model switches approach:{after_timeout['switches_approach']:>5} ({after_timeout['switches_approach']/after_timeout['total']*100:.1f}%)")
    print(f"  Model retries similar:  {after_timeout['retries_same']:>5} ({after_timeout['retries_same']/after_timeout['total']*100:.1f}%)")
    print(f"  Last turn (no next):    {after_timeout['no_next_turn']:>5} ({after_timeout['no_next_turn']/after_timeout['total']*100:.1f}%)")

    # ── 11. scipy.milp specific analysis ──
    print("\n" + "─" * 70)
    print("11. SCIPY.MILP TIMEOUT ANALYSIS")
    print("─" * 70)

    milp_timeouts = 0
    milp_total = 0
    milp_errors_other = 0
    milp_success = 0

    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if 'milp' in turn.code.lower():
                    milp_total += 1
                    if turn.is_error:
                        if 'timed out' in turn.output.lower():
                            milp_timeouts += 1
                        else:
                            milp_errors_other += 1
                    else:
                        milp_success += 1

    print(f"\n  MILP code cells:    {milp_total}")
    print(f"  MILP timeouts:      {milp_timeouts} ({milp_timeouts/milp_total*100:.1f}%)" if milp_total else "  No MILP cells found")
    print(f"  MILP other errors:  {milp_errors_other} ({milp_errors_other/milp_total*100:.1f}%)" if milp_total else "")
    print(f"  MILP successes:     {milp_success} ({milp_success/milp_total*100:.1f}%)" if milp_total else "")

    # ── 12. sympy.solve specific analysis ──
    print("\n" + "─" * 70)
    print("12. SYMPY.SOLVE TIMEOUT ANALYSIS")
    print("─" * 70)

    solve_timeouts = 0
    solve_total = 0
    solve_success = 0

    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if re.search(r'\.solve\(|sp\.solve|sympy\.solve', turn.code):
                    solve_total += 1
                    if turn.is_error and 'timed out' in turn.output.lower():
                        solve_timeouts += 1
                    elif not turn.is_error:
                        solve_success += 1

    print(f"\n  solve() code cells: {solve_total}")
    print(f"  solve() timeouts:   {solve_timeouts} ({solve_timeouts/solve_total*100:.1f}%)" if solve_total else "  No solve() cells found")
    print(f"  solve() successes:  {solve_success} ({solve_success/solve_total*100:.1f}%)" if solve_total else "")

    print("\n" + "=" * 80)
    print("  ACTIONABLE RECOMMENDATIONS")
    print("=" * 80)
    print("""
  Based on the analysis:

  1. TOP TIMEOUT CAUSES: Check sections 1-2 for which libraries and code patterns
     dominate timeouts. If itertools.product / nested loops dominate, add a prompt:
     "Before using itertools.product or nested loops, estimate the search space.
      If > 10^6, use a mathematical shortcut."

  2. CASCADE ANALYSIS: Check section 4. If attempts with 2+ early timeouts have
     <30% success rate, consider a prompt rule:
     "If your first two code cells time out, step back and use pure math reasoning
      before writing more code."

  3. MILP/SOLVE: Sections 11-12 show scipy.milp and sympy.solve timeout rates.
     If high (>30%), add specific guidance: "For MILP, ensure the problem has
     < 1000 variables. For sympy.solve, avoid systems with > 5 unknowns."

  4. SEARCH SPACE: Section 9 shows literal range() values in timed-out code.
     Large values indicate the model isn't estimating complexity before coding.
""")


if __name__ == '__main__':
    main()
