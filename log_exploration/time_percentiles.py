#!/usr/bin/env python3
"""
Time distribution by percentile, broken down by tier.

Usage:
    python3 log_exploration/time_percentiles.py <diagnostic.log>
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
import numpy as np


def get_tier(problem):
    """Extract tier from problem's batch label."""
    batch = getattr(problem, 'batch', '') or ''
    if not batch:
        # Try to infer from the raw tier field
        tier = getattr(problem, 'tier', '') or ''
        batch = tier
    return batch


def analyze_time_percentiles(logfile):
    problems = parse_log(logfile)

    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    # Group by tier
    tier_groups = {}
    hard_group = []  # Combined <2 tiers

    for p in problems:
        batch = get_tier(p)

        # Collect per-attempt times
        attempt_times = []
        for a in p.attempts:
            t = getattr(a, 'time_s', None)
            if t is not None and t > 0:
                attempt_times.append(t)

        # Also get problem-level time if available
        problem_time = getattr(p, 'time_s', None) or getattr(p, 'total_time', None)
        if problem_time is None and attempt_times:
            # Estimate: max attempt time (they run in parallel)
            problem_time = max(attempt_times)

        entry = {
            'id': p.problem_id,
            'batch': batch,
            'problem_time': problem_time,
            'attempt_times': attempt_times,
            'correct': (p.predicted == p.expected) if p.expected is not None else None,
            'n_attempts': len(p.attempts),
            'n_nones': sum(1 for a in p.attempts if a.answer is None),
        }

        # Categorize using batch_name
        batch = getattr(p, 'batch_name', '') or ''
        entry['batch'] = batch

        if 'TIER 2' in batch or 'VAL BENCH' in batch:
            tier_groups.setdefault('Tier 2 (Val Bench)', []).append(entry)
        elif 'TIER 0' in batch or 'TIER 0.5' in batch or 'TIER 1' in batch or 'SANITY' in batch:
            hard_group.append(entry)
            tier_groups.setdefault('Tier <2 (Hard)', []).append(entry)
        elif batch == '':
            # Check if problem is in known tier 0 (first batch has no name sometimes)
            hard_group.append(entry)
            tier_groups.setdefault('Tier <2 (Hard)', []).append(entry)
        else:
            tier_groups.setdefault('Unknown Tier', []).append(entry)

    percentiles = [5, 10, 25, 50, 75, 90, 95, 99]

    print(f"{'='*90}")
    print(f"  TIME DISTRIBUTION BY PERCENTILE (per-attempt times)")
    print(f"{'='*90}")

    # All problems combined
    all_times = []
    for p in problems:
        for a in p.attempts:
            t = getattr(a, 'time_s', None)
            if t is not None and t > 0:
                all_times.append(t)

    print(f"\n  ALL ATTEMPTS (n={len(all_times)})")
    print(f"  {'Percentile':>12}  {'Time (s)':>10}  {'Time (min)':>10}")
    print(f"  {'─'*12}  {'─'*10}  {'─'*10}")
    for pct in percentiles:
        val = np.percentile(all_times, pct)
        print(f"  {f'P{pct}':>12}  {val:>10.1f}  {val/60:>10.1f}")
    print(f"  {'mean':>12}  {np.mean(all_times):>10.1f}  {np.mean(all_times)/60:>10.1f}")
    print(f"  {'std':>12}  {np.std(all_times):>10.1f}  {np.std(all_times)/60:>10.1f}")

    # By tier
    for tier_name in ['Tier 2 (Val Bench)', 'Tier <2 (Hard)', 'Unknown Tier']:
        entries = tier_groups.get(tier_name, [])
        if not entries:
            continue

        times = []
        correct_times = []
        wrong_times = []
        for e in entries:
            for t in e['attempt_times']:
                times.append(t)
                if e['correct']:
                    correct_times.append(t)
                else:
                    wrong_times.append(t)

        n_correct = sum(1 for e in entries if e['correct'])
        n_wrong = sum(1 for e in entries if not e['correct'])

        print(f"\n  {'─'*86}")
        print(f"  {tier_name.upper()} — {len(entries)} problems ({n_correct} correct, {n_wrong} wrong)")
        print(f"  Per-attempt times (n={len(times)})")
        print(f"  {'─'*86}")

        print(f"\n  {'Percentile':>12}  {'All (s)':>10}  {'Correct (s)':>12}  {'Wrong (s)':>12}  {'All (min)':>10}")
        print(f"  {'─'*12}  {'─'*10}  {'─'*12}  {'─'*12}  {'─'*10}")
        for pct in percentiles:
            val = np.percentile(times, pct)
            c_val = np.percentile(correct_times, pct) if correct_times else 0
            w_val = np.percentile(wrong_times, pct) if wrong_times else 0
            print(f"  {f'P{pct}':>12}  {val:>10.1f}  {c_val:>12.1f}  {w_val:>12.1f}  {val/60:>10.1f}")
        print(f"  {'mean':>12}  {np.mean(times):>10.1f}  "
              f"{np.mean(correct_times) if correct_times else 0:>12.1f}  "
              f"{np.mean(wrong_times) if wrong_times else 0:>12.1f}  "
              f"{np.mean(times)/60:>10.1f}")

    # Per-PROBLEM times (wall clock = max attempt)
    print(f"\n\n{'='*90}")
    print(f"  TIME DISTRIBUTION BY PERCENTILE (per-problem wall clock)")
    print(f"{'='*90}")

    for tier_name in ['Tier 2 (Val Bench)', 'Tier <2 (Hard)', 'Unknown Tier']:
        entries = tier_groups.get(tier_name, [])
        if not entries:
            continue

        ptimes = [e['problem_time'] for e in entries if e['problem_time']]
        correct_ptimes = [e['problem_time'] for e in entries if e['problem_time'] and e['correct']]
        wrong_ptimes = [e['problem_time'] for e in entries if e['problem_time'] and not e['correct']]

        if not ptimes:
            continue

        n_correct = len(correct_ptimes)
        n_wrong = len(wrong_ptimes)

        print(f"\n  {'─'*86}")
        print(f"  {tier_name.upper()} — {len(entries)} problems ({n_correct} correct, {n_wrong} wrong)")
        print(f"  Per-problem wall clock (n={len(ptimes)})")
        print(f"  {'─'*86}")

        print(f"\n  {'Percentile':>12}  {'All (s)':>10}  {'Correct (s)':>12}  {'Wrong (s)':>12}  {'All (min)':>10}")
        print(f"  {'─'*12}  {'─'*10}  {'─'*12}  {'─'*12}  {'─'*10}")
        for pct in percentiles:
            val = np.percentile(ptimes, pct)
            c_val = np.percentile(correct_ptimes, pct) if correct_ptimes else 0
            w_val = np.percentile(wrong_ptimes, pct) if wrong_ptimes else 0
            print(f"  {f'P{pct}':>12}  {val:>10.1f}  {c_val:>12.1f}  {w_val:>12.1f}  {val/60:>10.1f}")
        print(f"  {'mean':>12}  {np.mean(ptimes):>10.1f}  "
              f"{np.mean(correct_ptimes) if correct_ptimes else 0:>12.1f}  "
              f"{np.mean(wrong_ptimes) if wrong_ptimes else 0:>12.1f}  "
              f"{np.mean(ptimes)/60:>10.1f}")
        print(f"  {'total':>12}  {sum(ptimes):>10.1f}  "
              f"{sum(correct_ptimes) if correct_ptimes else 0:>12.1f}  "
              f"{sum(wrong_ptimes) if wrong_ptimes else 0:>12.1f}  "
              f"{sum(ptimes)/60:>10.1f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    analyze_time_percentiles(sys.argv[1])
