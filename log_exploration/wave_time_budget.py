#!/usr/bin/env python3
"""
Wave Time Budget Analysis
=========================
Core query for Wave 1+16+1+16 architecture planning.
Shows time distributions by tier group (T≤1 vs T2) and correctness.

Usage:
    python3 log_exploration/wave_time_budget.py output/v31/diagnostic.log
    python3 log_exploration/wave_time_budget.py output/v23/diagnostic.log output/v31/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log

# ── Tier mapping (hardcoded known tiers) ──
KNOWN_TIERS = {
    'dbbfe8': 'T0', '3b88b3': 'T0',
    '86e8e5': 'T0.5',
}

# T1 problems (wrong in v31 + monitor + dodgy)
T1_IDS = {
    '1ec970', '23586c', '26bee3', '29714f', '3980cd', '3b88b3',
    '414a5b', '673b29', '9010d9', 'a824c1', 'a9dbc8', 'ae2add',
    'aff75c', 'dbbfe8',
    # monitor
    '21fb4e', '89c921',
    # dodgy
    '32690e',
}


def get_tier(pid_short):
    if pid_short in KNOWN_TIERS:
        return KNOWN_TIERS[pid_short]
    if pid_short in T1_IDS:
        return 'T1'
    return 'T2'


def tier_group(tier):
    return 'T≤1' if tier in ('T0', 'T0.5', 'T1') else 'T2'


def percentiles(values, pcts=(10, 25, 50, 75, 90, 95, 99)):
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    result = {}
    for p in pcts:
        k = (p / 100) * (n - 1)
        f, c = math.floor(k), math.ceil(k)
        result[p] = s[int(k)] if f == c else s[f] * (c - k) + s[c] * (k - f)
    return result


def print_dist(label, values, indent=4):
    pad = ' ' * indent
    if not values:
        print(f'{pad}{label}: no data')
        return
    pcts = percentiles(values)
    print(f'{pad}{label}: n={len(values)}  '
          f'mean={sum(values)/len(values):.0f}s  '
          f'P25={pcts[25]:.0f}s  P50={pcts[50]:.0f}s  '
          f'P75={pcts[75]:.0f}s  P90={pcts[90]:.0f}s  '
          f'P95={pcts[95]:.0f}s  max={max(values):.0f}s')


def analyze_log(logfile, label):
    problems = parse_log(logfile)
    if not problems:
        print(f'  No problems found in {logfile}')
        return

    print(f'\n{"=" * 75}')
    print(f'  {label}: {logfile}')
    print(f'  {len(problems)} problems')
    print(f'{"=" * 75}')

    # Classify all problems
    by_group = defaultdict(list)
    for p in problems:
        pid = p.problem_id[:6]
        tier = get_tier(pid)
        grp = tier_group(tier)
        by_group[grp].append((p, tier))

    for grp in ['T2', 'T≤1']:
        items = by_group.get(grp, [])
        if not items:
            continue

        n_correct = sum(1 for p, _ in items if p.correct)
        n_total = len(items)
        print(f'\n{"─" * 60}')
        print(f'  {grp}: {n_correct}/{n_total} problems correct')
        print(f'{"─" * 60}')

        # Problem-level: wall time (time the problem actually consumed)
        wall_correct = [p.wall_time for p, _ in items if p.correct]
        wall_wrong = [p.wall_time for p, _ in items if not p.correct]
        print(f'\n  PROBLEM-LEVEL WALL TIME (actual budget consumed):')
        print_dist('Correct problems', wall_correct)
        print_dist('Wrong problems  ', wall_wrong)

        # Attempt-level: individual attempt times
        correct_times = []
        wrong_times = []
        none_times = []
        for p, _ in items:
            for a in p.attempts:
                if a.answer is None:
                    none_times.append(a.time_s)
                elif p.expected is not None and str(a.answer) == str(p.expected):
                    correct_times.append(a.time_s)
                else:
                    wrong_times.append(a.time_s)

        print(f'\n  ATTEMPT-LEVEL TIME:')
        print_dist('Correct attempts', correct_times)
        print_dist('Wrong attempts  ', wrong_times)
        print_dist('None attempts   ', none_times)

        # Fastest correct attempt per problem (Wave 1 needs at least 1 correct)
        fastest_correct = []
        for p, _ in items:
            if not p.correct:
                continue
            fc = min(
                (a.time_s for a in p.attempts
                 if a.answer is not None and p.expected is not None
                 and str(a.answer) == str(p.expected)),
                default=None
            )
            if fc is not None:
                fastest_correct.append(fc)

        print(f'\n  FASTEST CORRECT ATTEMPT PER PROBLEM (minimum needed):')
        print_dist('Fastest correct', fastest_correct)

        # Timeout simulation: what score at different caps
        caps = [60, 90, 120, 150, 180, 240, 300, 360, 420, 480, 600, 720, 900]
        print(f'\n  SCORE vs TIMEOUT CAP (majority vote among attempts finishing within cap):')
        print(f'    {"Cap":>6}  {"Score":>7}  {"Rate":>6}')
        for cap in caps:
            score = 0
            for p, _ in items:
                valid = [a for a in p.attempts if a.time_s <= cap and a.answer is not None]
                if not valid:
                    continue
                votes = defaultdict(int)
                for a in valid:
                    votes[a.answer] += 1
                best_ans = max(votes, key=votes.get)
                if p.expected is not None and str(best_ans) == str(p.expected):
                    score += 1
            print(f'    {cap:>5}s  {score:>3}/{n_total}    {100*score/n_total:>5.1f}%')

        # Per-problem detail
        print(f'\n  PER-PROBLEM DETAIL:')
        print(f'    {"PID":<8} {"Tier":<5} {"Wall":>6} {"Fast✓":>6} {"✓/N":>5} {"Result":<7}')
        print(f'    {"─" * 50}')
        sorted_items = sorted(items, key=lambda x: x[0].wall_time, reverse=True)
        for p, tier in sorted_items:
            pid = p.problem_id[:6]
            fc_times = [a.time_s for a in p.attempts
                        if a.answer is not None and p.expected is not None
                        and str(a.answer) == str(p.expected)]
            fc_str = f'{min(fc_times):.0f}s' if fc_times else '  --'
            n_corr = len(fc_times)
            status = 'OK' if p.correct else 'WRONG'
            print(f'    {pid:<8} {tier:<5} {p.wall_time:>5.0f}s {fc_str:>6} {n_corr:>2}/{len(p.attempts):<2} {status:<7}')

    # Summary: total time consumed
    total_wall = sum(p.wall_time for p in problems)
    t2_wall = sum(p.wall_time for p, _ in by_group.get('T2', []))
    t1_wall = sum(p.wall_time for p, _ in by_group.get('T≤1', []))
    print(f'\n{"─" * 60}')
    print(f'  TOTAL WALL TIME: {total_wall/60:.1f} min')
    print(f'    T2:  {t2_wall/60:.1f} min ({len(by_group.get("T2", []))} problems)')
    print(f'    T≤1: {t1_wall/60:.1f} min ({len(by_group.get("T≤1", []))} problems)')
    print(f'  Avg per T2 problem:  {t2_wall/max(1,len(by_group.get("T2",[]))):.0f}s')
    print(f'  Avg per T≤1 problem: {t1_wall/max(1,len(by_group.get("T≤1",[]))):.0f}s')


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 log_exploration/wave_time_budget.py LOG1 [LOG2 ...]')
        sys.exit(1)

    for logfile in sys.argv[1:]:
        label = os.path.basename(os.path.dirname(logfile))
        analyze_log(logfile, label)


if __name__ == '__main__':
    main()
