#!/usr/bin/env python3
"""
Extract sample code from timed-out cells to understand WHAT the model is computing.
Focus on the worst offenders and the most common patterns.
"""

import sys
import os
import re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 timeout_code_samples.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.\n")

    # Collect all timeout code cells with context
    timeout_cells = []
    for prob in problems:
        for att in prob.attempts:
            for turn in att.turns:
                if turn.is_error and 'timed out' in turn.output.lower():
                    timeout_cells.append({
                        'pid': prob.problem_id,
                        'att': att.attempt_num,
                        'turn': turn.turn_num,
                        'code': turn.code,
                        'total_turns': len(att.turns),
                        'correct': prob.correct,
                        'reasoning': turn.reasoning_text[:500] if hasattr(turn, 'reasoning_text') else '',
                    })

    # ── 1. Most common timeout code patterns (by de-duplicating structure) ──
    print("=" * 80)
    print("1. TIMEOUT CODE CATEGORIES (manual classification)")
    print("=" * 80)

    categories = defaultdict(list)
    for cell in timeout_cells:
        code = cell['code']
        code_lower = code.lower()

        # Classify
        if re.search(r'range\(\s*\d{6,}\)', code):
            categories['giant_range_1M+'].append(cell)
        elif re.search(r'range\(\s*\d{5}\)', code):
            categories['large_range_10K-100K'].append(cell)
        elif 'itertools.product' in code and re.search(r'repeat\s*=\s*\d+', code):
            categories['itertools_product_repeat'].append(cell)
        elif 'itertools.product' in code:
            categories['itertools_product'].append(cell)
        elif 'itertools.permutations' in code or 'itertools.combinations' in code:
            categories['itertools_comb_perm'].append(cell)
        elif '.solve(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
            categories['sympy_solve'].append(cell)
        elif '.simplify(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
            categories['sympy_simplify'].append(cell)
        elif '.expand(' in code and ('sympy' in code_lower or 'sp.' in code_lower):
            categories['sympy_expand'].append(cell)
        elif '.integrate(' in code:
            categories['sympy_integrate'].append(cell)
        elif 'milp(' in code:
            categories['scipy_milp'].append(cell)
        elif 'linprog(' in code:
            categories['scipy_linprog'].append(cell)
        elif re.search(r'while\s+True|while\s+1\b', code):
            categories['while_true_loop'].append(cell)
        elif 'random.' in code_lower and ('for' in code_lower or 'while' in code_lower):
            categories['monte_carlo_sampling'].append(cell)
        elif 'lru_cache' in code or '@cache' in code:
            categories['memoized_recursion'].append(cell)
        elif code.count('for ') >= 3:
            categories['triple_nested_loop'].append(cell)
        elif code.count('for ') >= 2:
            categories['double_nested_loop'].append(cell)
        elif 'for ' in code:
            categories['single_loop'].append(cell)
        else:
            categories['other'].append(cell)

    sorted_cats = sorted(categories.items(), key=lambda x: -len(x[1]))
    total = len(timeout_cells)
    print(f"\n  Total timeout cells: {total}\n")
    print(f"  {'Category':<30} {'Count':>8} {'% of all':>10}")
    print(f"  {'─'*30} {'─'*8} {'─'*10}")
    for cat, cells in sorted_cats:
        print(f"  {cat:<30} {len(cells):>8} {len(cells)/total*100:>9.1f}%")

    # ── 2. Show sample code for top categories ──
    print("\n" + "=" * 80)
    print("2. SAMPLE CODE FROM TOP TIMEOUT CATEGORIES")
    print("=" * 80)

    for cat, cells in sorted_cats[:8]:
        print(f"\n  ── {cat} ({len(cells)} timeouts) ──")
        for cell in cells[:3]:
            code_lines = cell['code'].split('\n')[:15]
            code_preview = '\n    '.join(code_lines)
            print(f"  Problem {cell['pid']}, Att {cell['att']}, Turn {cell['turn']}:")
            print(f"    {code_preview}")
            print()

    # ── 3. Timeout concentration: which problems waste the most time? ──
    print("=" * 80)
    print("3. TIME WASTED PER PROBLEM (sorted by timeout count)")
    print("=" * 80)

    prob_stats = defaultdict(lambda: {'timeouts': 0, 'timeout_turns': [], 'total_turns': 0, 'correct': False, 'attempts': 0})
    for prob in problems:
        pid = prob.problem_id
        prob_stats[pid]['correct'] = prob.correct
        prob_stats[pid]['attempts'] = len(prob.attempts)
        for att in prob.attempts:
            for turn in att.turns:
                prob_stats[pid]['total_turns'] += 1
                if turn.is_error and 'timed out' in turn.output.lower():
                    prob_stats[pid]['timeouts'] += 1
                    prob_stats[pid]['timeout_turns'].append(turn.turn_num)

    sorted_probs = sorted(prob_stats.items(), key=lambda x: -x[1]['timeouts'])

    print(f"\n  {'Problem':<10} {'TOs':>5} {'Turns':>7} {'TO%':>6} {'Wasted':>10} {'Correct':>9} {'Median TO turn':>16}")
    print(f"  {'─'*10} {'─'*5} {'─'*7} {'─'*6} {'─'*10} {'─'*9} {'─'*16}")
    for pid, stats in sorted_probs[:25]:
        pct = stats['timeouts'] / stats['total_turns'] * 100 if stats['total_turns'] > 0 else 0
        wasted = stats['timeouts'] * 30  # 30s per timeout
        turns = sorted(stats['timeout_turns'])
        median_turn = turns[len(turns)//2] if turns else 0
        c = 'Yes' if stats['correct'] else 'No'
        print(f"  {pid:<10} {stats['timeouts']:>5} {stats['total_turns']:>7} {pct:>5.1f}% {wasted:>9}s {c:>9} {median_turn:>16}")

    # ── 4. "Doom" analysis: if attempt has N timeouts, what % produce None? ──
    print("\n" + "=" * 80)
    print("4. DOOM ANALYSIS: Timeouts vs None rate (per attempt)")
    print("=" * 80)

    buckets = defaultdict(lambda: {'total': 0, 'none': 0, 'correct': 0, 'wrong': 0})
    for prob in problems:
        for att in prob.attempts:
            n_to = sum(1 for t in att.turns if t.is_error and 'timed out' in t.output.lower())
            n_turns = len(att.turns)
            if n_turns == 0:
                continue

            bucket = f"{n_to} timeouts"
            if n_to > 8:
                bucket = "9+ timeouts"

            buckets[bucket]['total'] += 1
            if att.answer is None:
                buckets[bucket]['none'] += 1
            elif att.answer == prob.expected:
                buckets[bucket]['correct'] += 1
            else:
                buckets[bucket]['wrong'] += 1

    print(f"\n  {'Timeouts':<15} {'Total':>7} {'None':>7} {'Correct':>9} {'Wrong':>7} {'None%':>8} {'Correct%':>10}")
    print(f"  {'─'*15} {'─'*7} {'─'*7} {'─'*9} {'─'*7} {'─'*8} {'─'*10}")
    for i in range(9):
        bucket = f"{i} timeouts"
        d = buckets[bucket]
        if d['total'] == 0:
            continue
        none_pct = d['none'] / d['total'] * 100
        answered = d['correct'] + d['wrong']
        correct_pct = d['correct'] / answered * 100 if answered > 0 else 0
        print(f"  {bucket:<15} {d['total']:>7} {d['none']:>7} {d['correct']:>9} {d['wrong']:>7} {none_pct:>7.1f}% {correct_pct:>9.1f}%")
    d = buckets["9+ timeouts"]
    if d['total'] > 0:
        none_pct = d['none'] / d['total'] * 100
        answered = d['correct'] + d['wrong']
        correct_pct = d['correct'] / answered * 100 if answered > 0 else 0
        print(f"  {'9+ timeouts':<15} {d['total']:>7} {d['none']:>7} {d['correct']:>9} {d['wrong']:>7} {none_pct:>7.1f}% {correct_pct:>9.1f}%")

    # ── 5. Recovery patterns: after a timeout, does the next cell succeed? ──
    print("\n" + "=" * 80)
    print("5. RECOVERY: What happens in the turn AFTER a timeout?")
    print("=" * 80)

    after_stats = {'success': 0, 'timeout_again': 0, 'other_error': 0, 'no_next': 0}
    for prob in problems:
        for att in prob.attempts:
            for i, turn in enumerate(att.turns):
                if turn.is_error and 'timed out' in turn.output.lower():
                    if i + 1 < len(att.turns):
                        next_turn = att.turns[i + 1]
                        if not next_turn.is_error:
                            after_stats['success'] += 1
                        elif 'timed out' in next_turn.output.lower():
                            after_stats['timeout_again'] += 1
                        else:
                            after_stats['other_error'] += 1
                    else:
                        after_stats['no_next'] += 1

    total_after = sum(after_stats.values())
    print(f"\n  After a timeout, the NEXT code cell is:")
    for key, count in sorted(after_stats.items(), key=lambda x: -x[1]):
        print(f"    {key:<20} {count:>6} ({count/total_after*100:.1f}%)")

    # ── 6. The "testing the sandbox" pattern ──
    print("\n" + "=" * 80)
    print("6. 'TESTING THE SANDBOX' PATTERN")
    print("=" * 80)

    sandbox_test_cells = 0
    for cell in timeout_cells:
        code = cell['code'].strip()
        # Very short cells that are just testing execution
        if len(code) < 100 and ('range(1000000)' in code or 'sum(' in code and 'range' in code):
            sandbox_test_cells += 1

    print(f"\n  Timeout cells that appear to be sandbox tests: {sandbox_test_cells}")
    print(f"  (Short cells with range(1000000) etc.)")

    # Show examples
    print("\n  Examples:")
    shown = 0
    for cell in timeout_cells:
        code = cell['code'].strip()
        if len(code) < 150 and ('range(1000000)' in code or ('sum(' in code and 'range' in code)):
            print(f"    Problem {cell['pid']}, Att {cell['att']}, Turn {cell['turn']}: {code}")
            shown += 1
            if shown >= 10:
                break


if __name__ == '__main__':
    main()
