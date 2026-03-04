#!/usr/bin/env python3
"""
Time cutoff analysis: What's the optimal per-problem time budget?

Answers:
1. After what time does accuracy drop to ~0?
2. What % of correct answers are found within T seconds?
3. What's the optimal max time per problem?

Usage:
    python3 log_exploration/time_cutoff_analysis.py <diagnostic.log>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
import numpy as np


def analyze_cutoffs(logfile):
    problems = parse_log(logfile)

    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    # Collect per-attempt data
    all_attempts = []
    for p in problems:
        for a in p.attempts:
            t = getattr(a, 'time_s', None)
            if t is None or t <= 0:
                continue
            correct = (a.answer == p.expected) if a.answer is not None and p.expected is not None else False
            is_none = a.answer is None
            all_attempts.append({
                'pid': p.problem_id,
                'time': t,
                'correct': correct,
                'is_none': is_none,
                'answer': a.answer,
                'expected': p.expected,
            })

    print(f"{'='*90}")
    print(f"  TIME CUTOFF ANALYSIS — {len(all_attempts)} attempts across {len(problems)} problems")
    print(f"{'='*90}")

    # 1. Accuracy by time bucket
    print(f"\n  {'─'*86}")
    print(f"  1. ACCURACY BY TIME BUCKET")
    print(f"  {'─'*86}")
    buckets = [(0, 30), (30, 60), (60, 90), (90, 120), (120, 150), (150, 180),
               (180, 210), (210, 240), (240, 270), (270, 300), (300, 330), (330, 360), (360, 600)]

    print(f"  {'Bucket':>12} {'Total':>7} {'Correct':>8} {'Wrong':>7} {'None':>7} {'Acc%':>7} {'AccExNone':>10}")
    print(f"  {'─'*12} {'─'*7} {'─'*8} {'─'*7} {'─'*7} {'─'*7} {'─'*10}")

    for lo, hi in buckets:
        in_bucket = [a for a in all_attempts if lo <= a['time'] < hi]
        n = len(in_bucket)
        if n == 0:
            continue
        correct = sum(1 for a in in_bucket if a['correct'])
        nones = sum(1 for a in in_bucket if a['is_none'])
        wrong = n - correct - nones
        acc = correct / n * 100 if n > 0 else 0
        acc_ex = correct / (n - nones) * 100 if (n - nones) > 0 else 0
        label = f"{lo}-{hi}s"
        bar = '#' * int(acc_ex / 3)
        print(f"  {label:>12} {n:>7} {correct:>8} {wrong:>7} {nones:>7} {acc:>6.1f}% {acc_ex:>9.1f}% {bar}")

    # 2. Cumulative: what % of correct answers found by time T?
    print(f"\n  {'─'*86}")
    print(f"  2. CUMULATIVE CORRECT FOUND BY TIME T")
    print(f"  {'─'*86}")

    correct_times = sorted([a['time'] for a in all_attempts if a['correct']])
    total_correct = len(correct_times)

    print(f"  Total correct attempts: {total_correct}")
    print(f"\n  {'Time (s)':>10} {'Time (min)':>10} {'Found':>7} {'Cumul%':>8} {'Remaining':>10}")
    print(f"  {'─'*10} {'─'*10} {'─'*7} {'─'*8} {'─'*10}")

    for t in [30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 420, 480, 540, 600]:
        found = sum(1 for ct in correct_times if ct <= t)
        pct = found / total_correct * 100 if total_correct > 0 else 0
        remaining = total_correct - found
        print(f"  {t:>10} {t/60:>10.1f} {found:>7} {pct:>7.1f}% {remaining:>10}")

    # 3. Per-problem: earliest correct attempt time
    print(f"\n  {'─'*86}")
    print(f"  3. PER-PROBLEM: EARLIEST CORRECT ATTEMPT")
    print(f"  {'─'*86}")

    problem_first_correct = {}
    for a in all_attempts:
        if a['correct']:
            pid = a['pid']
            if pid not in problem_first_correct or a['time'] < problem_first_correct[pid]:
                problem_first_correct[pid] = a['time']

    if problem_first_correct:
        first_times = sorted(problem_first_correct.values())
        total_solvable = len(first_times)

        print(f"  Problems with at least 1 correct attempt: {total_solvable}/{len(problems)}")
        print(f"\n  {'Budget (s)':>10} {'Budget (min)':>12} {'Solved':>7} {'of {0}'.format(len(problems)):>7} {'%':>7} {'Lost':>6}")
        print(f"  {'─'*10} {'─'*12} {'─'*7} {'─'*7} {'─'*7} {'─'*6}")

        for t in [60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 420, 480, 540, 600]:
            solved = sum(1 for ft in first_times if ft <= t)
            lost = total_solvable - solved
            pct = solved / len(problems) * 100
            print(f"  {t:>10} {t/60:>12.1f} {solved:>7} {len(problems):>7} {pct:>6.1f}% {lost:>6}")

    # 4. Score simulation: what score would we get with budget T?
    print(f"\n  {'─'*86}")
    print(f"  4. SCORE SIMULATION: If we cap per-problem time at T")
    print(f"     (Only count attempts that finish within T seconds)")
    print(f"  {'─'*86}")

    from collections import Counter

    for t_budget in [60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 420, 480, 600]:
        score = 0
        for p in problems:
            votes = Counter()
            for a in p.attempts:
                at = getattr(a, 'time_s', None)
                if at is not None and at <= t_budget and a.answer is not None:
                    votes[a.answer] += 1
            if votes:
                winner = votes.most_common(1)[0][0]
                if winner == p.expected:
                    score += 1
        pct = score / len(problems) * 100
        print(f"  Budget {t_budget:>4}s ({t_budget/60:>5.1f} min): {score:>3}/{len(problems)} ({pct:.1f}%)")

    # 5. Time budget vs number of problems tradeoff
    print(f"\n  {'─'*86}")
    print(f"  5. BUDGET TRADEOFF: With total 290 min, how many problems at each budget?")
    print(f"  {'─'*86}")

    total_budget_s = 290 * 60  # 290 min in seconds

    print(f"  {'Per-prob (s)':>12} {'Per-prob (min)':>14} {'Max problems':>13} {'Expected score':>15}")
    print(f"  {'─'*12} {'─'*14} {'─'*13} {'─'*15}")

    for t_budget in [90, 120, 150, 180, 210, 240, 270, 300, 360, 420, 480, 600]:
        max_problems = int(total_budget_s / t_budget)
        # Estimate score: use accuracy at that budget level × min(max_problems, 110)
        n_problems = min(max_problems, 110)

        # Simulate accuracy at this budget
        correct_at_budget = 0
        total_at_budget = 0
        for p in problems:
            votes = Counter()
            for a in p.attempts:
                at = getattr(a, 'time_s', None)
                if at is not None and at <= t_budget and a.answer is not None:
                    votes[a.answer] += 1
            if votes:
                winner = votes.most_common(1)[0][0]
                if winner == p.expected:
                    correct_at_budget += 1
            total_at_budget += 1

        acc = correct_at_budget / total_at_budget if total_at_budget > 0 else 0
        expected_score = int(acc * n_problems)

        print(f"  {t_budget:>12} {t_budget/60:>14.1f} {max_problems:>13} {expected_score:>15} "
              f"({acc*100:.0f}% × {n_problems})")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    analyze_cutoffs(sys.argv[1])
