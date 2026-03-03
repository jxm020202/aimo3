#!/usr/bin/env python3
"""
AIMO3 Run Comparison Tool
===========================
Compare two diagnostic.log files side-by-side.
Shows: score diff, time diff, which problems flipped, per-problem delta table.

Usage:
    python log_exploration/compare_runs.py <log1> <log2>
    python log_exploration/compare_runs.py output/v21/diagnostic.log output/v22/diagnostic.log
    python log_exploration/compare_runs.py --help
"""

import sys
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def compare(problems_a, problems_b, label_a, label_b):
    """Compare two sets of parsed problems."""

    # Build lookup by problem_id
    lookup_a = {p.problem_id: p for p in problems_a}
    lookup_b = {p.problem_id: p for p in problems_b}
    all_ids = sorted(set(lookup_a.keys()) | set(lookup_b.keys()))
    common_ids = sorted(set(lookup_a.keys()) & set(lookup_b.keys()))

    # ── Header ──
    print(f"\n{'=' * 75}")
    print(f"  RUN COMPARISON")
    print(f"  A: {label_a}")
    print(f"  B: {label_b}")
    print(f"{'=' * 75}")

    # ── Score Summary ──
    score_a = sum(1 for p in problems_a if p.correct)
    score_b = sum(1 for p in problems_b if p.correct)
    total_a = len(problems_a)
    total_b = len(problems_b)
    time_a = sum(p.wall_time for p in problems_a)
    time_b = sum(p.wall_time for p in problems_b)

    print(f"\n  {'Metric':<25} {'A':>12} {'B':>12} {'Delta':>10}")
    print(f"  {'─'*25} {'─'*12} {'─'*12} {'─'*10}")
    print(f"  {'Score':<25} {score_a:>8}/{total_a:<3} {score_b:>8}/{total_b:<3} {score_b - score_a:>+10}")
    print(f"  {'Accuracy':<25} {score_a/max(total_a,1)*100:>11.1f}% {score_b/max(total_b,1)*100:>11.1f}% {(score_b/max(total_b,1) - score_a/max(total_a,1))*100:>+9.1f}%")
    print(f"  {'Total time':<25} {time_a:>11.0f}s {time_b:>11.0f}s {time_b - time_a:>+10.0f}s")
    print(f"  {'Avg time/problem':<25} {time_a/max(total_a,1):>11.0f}s {time_b/max(total_b,1):>11.0f}s {time_b/max(total_b,1) - time_a/max(total_a,1):>+10.0f}s")
    print(f"  {'Problems':<25} {total_a:>12} {total_b:>12} {total_b - total_a:>+10}")
    print(f"  {'Common problems':<25} {len(common_ids):>12}")

    total_att_a = sum(len(p.attempts) for p in problems_a)
    total_att_b = sum(len(p.attempts) for p in problems_b)
    nones_a = sum(1 for p in problems_a for a in p.attempts if a.is_none)
    nones_b = sum(1 for p in problems_b for a in p.attempts if a.is_none)
    errs_a = sum(a.errors for p in problems_a for a in p.attempts)
    errs_b = sum(a.errors for p in problems_b for a in p.attempts)

    print(f"  {'Total attempts':<25} {total_att_a:>12} {total_att_b:>12} {total_att_b - total_att_a:>+10}")
    print(f"  {'None rate':<25} {nones_a/max(total_att_a,1)*100:>11.1f}% {nones_b/max(total_att_b,1)*100:>11.1f}% {(nones_b/max(total_att_b,1) - nones_a/max(total_att_a,1))*100:>+9.1f}%")
    print(f"  {'Total errors':<25} {errs_a:>12} {errs_b:>12} {errs_b - errs_a:>+10}")

    # ── Flipped Problems ──
    gained = []  # wrong in A → correct in B
    lost = []    # correct in A → wrong in B
    stable_ok = []
    stable_wrong = []

    for pid in common_ids:
        pa = lookup_a.get(pid)
        pb = lookup_b.get(pid)
        if pa and pb:
            if not pa.correct and pb.correct:
                gained.append(pid)
            elif pa.correct and not pb.correct:
                lost.append(pid)
            elif pa.correct and pb.correct:
                stable_ok.append(pid)
            else:
                stable_wrong.append(pid)

    print(f"\n  PROBLEM FLIPS (on {len(common_ids)} common problems):")
    print(f"    Gained (A wrong → B correct): {len(gained)}")
    for pid in gained:
        pa, pb = lookup_a[pid], lookup_b[pid]
        print(f"      {pid}: A predicted {pa.predicted} (exp {pa.expected}), B predicted {pb.predicted}")
    print(f"    Lost (A correct → B wrong):   {len(lost)}")
    for pid in lost:
        pa, pb = lookup_a[pid], lookup_b[pid]
        print(f"      {pid}: A predicted {pa.predicted}, B predicted {pb.predicted} (exp {pb.expected})")
    print(f"    Stable correct:               {len(stable_ok)}")
    print(f"    Stable wrong:                 {len(stable_wrong)}")
    for pid in stable_wrong:
        pa, pb = lookup_a[pid], lookup_b[pid]
        print(f"      {pid}: A={pa.predicted} B={pb.predicted} (exp {pa.expected})")

    # ── Per-Problem Delta Table ──
    print(f"\n  PER-PROBLEM COMPARISON (common problems, sorted by time delta):")
    print(f"  {'ID':<8} {'A':>3} {'B':>3} {'Flip':<6} {'TimeA':>6} {'TimeB':>6} {'dTime':>7} {'AttA':>5} {'AttB':>5} {'NoneA':>6} {'NoneB':>6}")
    print(f"  {'─'*8} {'─'*3} {'─'*3} {'─'*6} {'─'*6} {'─'*6} {'─'*7} {'─'*5} {'─'*5} {'─'*6} {'─'*6}")

    rows = []
    for pid in common_ids:
        pa, pb = lookup_a[pid], lookup_b[pid]
        ok_a = 'Y' if pa.correct else 'N'
        ok_b = 'Y' if pb.correct else 'N'
        flip = ''
        if not pa.correct and pb.correct: flip = '++'
        elif pa.correct and not pb.correct: flip = '--'
        dt = pb.wall_time - pa.wall_time
        att_a = len(pa.attempts)
        att_b = len(pb.attempts)
        none_a = sum(1 for a in pa.attempts if a.is_none)
        none_b = sum(1 for a in pb.attempts if a.is_none)
        rows.append((pid, ok_a, ok_b, flip, pa.wall_time, pb.wall_time, dt, att_a, att_b, none_a, none_b))

    rows.sort(key=lambda r: r[6])
    for pid, ok_a, ok_b, flip, t_a, t_b, dt, att_a, att_b, n_a, n_b in rows:
        print(f"  {pid:<8} {ok_a:>3} {ok_b:>3} {flip:<6} {t_a:>5.0f}s {t_b:>5.0f}s {dt:>+6.0f}s {att_a:>5} {att_b:>5} {n_a:>6} {n_b:>6}")

    # ── Only-in-A / Only-in-B ──
    only_a = set(lookup_a.keys()) - set(lookup_b.keys())
    only_b = set(lookup_b.keys()) - set(lookup_a.keys())
    if only_a:
        print(f"\n  Problems only in A ({len(only_a)}): {', '.join(sorted(only_a)[:10])}")
    if only_b:
        print(f"  Problems only in B ({len(only_b)}): {', '.join(sorted(only_b)[:10])}")

    print()


def main():
    if len(sys.argv) < 3 or '--help' in sys.argv:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    log_a, log_b = sys.argv[1], sys.argv[2]
    for f in [log_a, log_b]:
        if not os.path.exists(f):
            print(f"Error: {f} not found")
            sys.exit(1)

    problems_a = parse_log(log_a)
    problems_b = parse_log(log_b)

    compare(problems_a, problems_b, log_a, log_b)


if __name__ == '__main__':
    main()
