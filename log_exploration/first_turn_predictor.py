#!/usr/bin/env python3
"""
First Turn Outcome Predictor
=============================
Does the first turn predict attempt success?
- First-turn length vs outcome
- First-turn code presence vs outcome
- First-turn error vs outcome
- Can we detect "doomed" attempts early?

Also: Temperature schedule optimization via detailed per-temp/per-difficulty analysis.
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log
from collections import defaultdict


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 first_turn_predictor.py <logfile>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])

    # ── 1. First Turn Length vs Outcome ──
    print("=" * 80)
    print("  FIRST TURN REASONING LENGTH vs OUTCOME")
    print("  (Does a long first turn predict failure?)")
    print("=" * 80)
    print()

    ft_data = []
    for p in problems:
        for a in p.attempts:
            if not a.turns:
                continue
            ft = a.turns[0]
            is_correct = a.answer is not None and a.answer == p.expected
            is_none = a.answer is None
            ft_data.append({
                'pid': p.problem_id,
                'att': a.attempt_num,
                'ft_len': ft.reasoning_chars,
                'ft_has_code': len(ft.code.strip()) > 0,
                'ft_is_error': ft.is_error,
                'total_turns': len(a.turns),
                'is_correct': is_correct,
                'is_none': is_none,
                'outcome': 'correct' if is_correct else ('none' if is_none else 'wrong'),
            })

    # Bucket by first-turn length
    buckets = {
        "0-2K": (0, 2000),
        "2-5K": (2000, 5000),
        "5-10K": (5000, 10000),
        "10-20K": (10000, 20000),
        "20-40K": (20000, 40000),
        "40K+": (40000, 999999),
    }

    print(f"  {'Bucket':<12} {'Total':<8} {'Correct':<10} {'Wrong':<8} {'None':<8} {'Acc%':<8} {'NoneR%':<8}")
    print("  " + "-" * 62)
    for label, (lo, hi) in buckets.items():
        subset = [d for d in ft_data if lo <= d['ft_len'] < hi]
        if not subset:
            continue
        correct = sum(1 for d in subset if d['is_correct'])
        wrong = sum(1 for d in subset if not d['is_correct'] and not d['is_none'])
        none = sum(1 for d in subset if d['is_none'])
        total = len(subset)
        acc = correct / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        none_r = none / total * 100
        print(f"  {label:<12} {total:<8} {correct:<10} {wrong:<8} {none:<8} {acc:>5.1f}%  {none_r:>5.1f}%")

    # ── 2. First Turn Has Code vs Not ──
    print()
    print("=" * 80)
    print("  FIRST TURN: CODE PRESENT vs PURE REASONING")
    print("=" * 80)
    print()

    for has_code in [True, False]:
        subset = [d for d in ft_data if d['ft_has_code'] == has_code]
        if not subset:
            continue
        correct = sum(1 for d in subset if d['is_correct'])
        wrong = sum(1 for d in subset if not d['is_correct'] and not d['is_none'])
        none = sum(1 for d in subset if d['is_none'])
        total = len(subset)
        acc = correct / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        label = "WITH code" if has_code else "NO code"
        print(f"  {label}: {total} attempts | {correct} correct | {wrong} wrong | {none} none | acc={acc:.1f}%")

    # ── 3. Doomed Attempts: Characteristics ──
    print()
    print("=" * 80)
    print("  DOOMED ATTEMPT SIGNALS")
    print("  (What distinguishes attempts that produce None?)")
    print("=" * 80)
    print()

    # Compare correct vs none attempts
    correct_attempts = [d for d in ft_data if d['is_correct']]
    none_attempts = [d for d in ft_data if d['is_none']]
    wrong_attempts = [d for d in ft_data if not d['is_correct'] and not d['is_none']]

    for label, subset in [("CORRECT", correct_attempts), ("WRONG", wrong_attempts), ("NONE", none_attempts)]:
        if not subset:
            continue
        avg_ft_len = sum(d['ft_len'] for d in subset) / len(subset)
        avg_turns = sum(d['total_turns'] for d in subset) / len(subset)
        pct_ft_code = sum(1 for d in subset if d['ft_has_code']) / len(subset) * 100
        pct_ft_error = sum(1 for d in subset if d['ft_is_error']) / len(subset) * 100
        print(f"  {label} ({len(subset)} attempts):")
        print(f"    Avg first-turn reasoning: {avg_ft_len:.0f} chars")
        print(f"    Avg total turns:          {avg_turns:.1f}")
        print(f"    First turn has code:      {pct_ft_code:.1f}%")
        print(f"    First turn has error:     {pct_ft_error:.1f}%")
        print()

    # ── 4. Flat 0.3 Simulation Impact ──
    print("=" * 80)
    print("  FLAT 0.3 TEMPERATURE SIMULATION")
    print("  (The temp analysis suggested flat 0.3 solves 44 vs current 38)")
    print("=" * 80)
    print()

    # For each problem, count how many 0.3-temp attempts got it right
    problems_by_temp03 = defaultdict(lambda: {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0})
    for p in problems:
        for a in p.attempts:
            if a.temperature is not None and abs(a.temperature - 0.3) < 0.01:
                key = p.problem_id
                problems_by_temp03[key]['total'] += 1
                if a.answer is not None and a.answer == p.expected:
                    problems_by_temp03[key]['correct'] += 1
                elif a.answer is None:
                    problems_by_temp03[key]['none'] += 1
                else:
                    problems_by_temp03[key]['wrong'] += 1

    # Which problems are ONLY solved by non-0.3 temps?
    currently_correct_only_by_non03 = []
    for p in problems:
        if not p.correct:
            continue
        pid = p.problem_id
        has_03_correct = problems_by_temp03[pid]['correct'] > 0
        has_any_correct = any(a.answer == p.expected for a in p.attempts if a.answer is not None)
        if has_any_correct and not has_03_correct:
            currently_correct_only_by_non03.append(p)

    print(f"  Problems currently correct but with 0 correct at temp=0.3:")
    for p in currently_correct_only_by_non03:
        temps_that_solved = []
        for a in p.attempts:
            if a.answer is not None and a.answer == p.expected:
                temps_that_solved.append(a.temperature)
        print(f"    {p.problem_id}: solved at temps {temps_that_solved}")

    # Which problems would we GAIN with flat 0.3?
    currently_wrong_but_03_correct = []
    for p in problems:
        if p.correct:
            continue
        pid = p.problem_id
        if problems_by_temp03[pid]['correct'] > 0:
            currently_wrong_but_03_correct.append(p)

    print()
    print(f"  Problems currently WRONG but have correct answer at temp=0.3:")
    for p in currently_wrong_but_03_correct:
        ct = problems_by_temp03[p.problem_id]
        print(f"    {p.problem_id}: {ct['correct']}/{ct['total']} correct at 0.3 (expected={p.expected})")

    # ── 5. Outvoted Analysis Deep Dive ──
    print()
    print("=" * 80)
    print("  OUTVOTED DEEP DIVE")
    print("  (Problems where correct answer exists but loses the vote)")
    print("=" * 80)
    print()

    from collections import Counter
    for p in problems:
        if p.correct:
            continue
        if p.expected is None:
            continue

        answers = [a.answer for a in p.attempts if a.answer is not None]
        correct_count = sum(1 for a in answers if a == p.expected)
        if correct_count == 0:
            continue

        votes = Counter(answers)
        winner, winner_count = votes.most_common(1)[0]

        print(f"  {p.problem_id}: Expected={p.expected}, Predicted={p.predicted}")
        print(f"    Correct answer appeared {correct_count}x, winner ({winner}) appeared {winner_count}x")
        print(f"    Full votes: {dict(votes.most_common())}")

        # What temps produced correct answers?
        correct_temps = [a.temperature for a in p.attempts if a.answer == p.expected]
        wrong_winner_temps = [a.temperature for a in p.attempts if a.answer == winner]
        print(f"    Correct at temps: {correct_temps}")
        print(f"    Winner at temps:  {wrong_winner_temps}")

        # Could different voting help?
        # Entropy-weighted
        correct_entropies = [a.entropy for a in p.attempts if a.answer == p.expected]
        winner_entropies = [a.entropy for a in p.attempts if a.answer == winner]
        if correct_entropies and winner_entropies:
            avg_correct_entropy = sum(correct_entropies) / len(correct_entropies)
            avg_winner_entropy = sum(winner_entropies) / len(winner_entropies)
            print(f"    Correct avg entropy: {avg_correct_entropy:.3f}, Winner avg entropy: {avg_winner_entropy:.3f}")
            if avg_correct_entropy < avg_winner_entropy:
                print(f"    >>> Entropy-weighting would HELP (correct has lower entropy)")
            else:
                print(f"    >>> Entropy-weighting would NOT help")
        print()


if __name__ == "__main__":
    main()
