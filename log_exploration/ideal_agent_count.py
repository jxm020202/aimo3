#!/usr/bin/env python3
"""Ideal agent (attempt) count analysis — score, time, parallelism tradeoffs.

Answers: What's the ideal number of Wave 2 attempts?

Sections:
1. Score vs attempt count (majority vote simulation at N=8,12,16,20,24,28,32,40,48)
2. Per-problem: minimum attempts needed for correct majority vote
3. Wall time model: how wall time scales with attempt count (from actual data)
4. Effective parallelism at current count + extrapolation
5. Time budget simulation: can we fit 50/110 problems at N attempts?
6. Attempt time distribution: fast vs slow attempts (queue pressure)
7. Per-problem marginal value: which problems NEED more attempts?
8. Recommendation

Usage:
    python3 log_exploration/ideal_agent_count.py output/shiv-latest-2/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict, Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log


def fmt(s):
    if s >= 3600: return f"{s/3600:.1f}h"
    if s >= 60: return f"{s/60:.1f}m"
    return f"{s:.0f}s"


def percentile(vals, p):
    if not vals: return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (k - f) * (s[c] - s[f])


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    n = len(problems)
    actual_att = max(len(p.attempts) for p in problems)
    total_correct = sum(1 for p in problems if p.correct)

    print("=" * 95)
    print(f"  IDEAL AGENT COUNT ANALYSIS — {n} problems, {total_correct}/{n} correct, {actual_att} attempts/problem")
    print("=" * 95)

    # ═══════════════════════════════════════════════════════════════
    # Section 1: Score vs attempt count
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 1: SCORE vs ATTEMPT COUNT (majority vote simulation)")
    print(f"  {'─'*80}")
    print(f"  {'Attempts':>8} {'Score':>8} {'Delta':>6} {'Nones':>6} {'DistinctAns':>12} {'MajorityPct':>12}")
    print(f"  {'─'*8} {'─'*8} {'─'*6} {'─'*6} {'─'*12} {'─'*12}")

    test_counts = [4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32]
    test_counts = [c for c in test_counts if c <= actual_att]

    score_at_n = {}
    for max_n in test_counts:
        score = 0
        total_nones = 0
        total_distinct = 0
        majority_pcts = []
        for p in problems:
            atts = sorted(p.attempts, key=lambda a: a.attempt_num)[:max_n]
            votes = Counter(a.answer for a in atts if a.answer is not None)
            n_none = sum(1 for a in atts if a.answer is None)
            total_nones += n_none
            total_distinct += len(votes)
            if votes:
                winner, winner_v = votes.most_common(1)[0]
                total_votes = sum(votes.values())
                majority_pcts.append(winner_v / total_votes * 100)
                if p.expected is not None and str(winner) == str(p.expected):
                    score += 1
        avg_maj = sum(majority_pcts) / len(majority_pcts) if majority_pcts else 0
        delta = score - total_correct
        delta_s = f"+{delta}" if delta > 0 else str(delta)
        score_at_n[max_n] = score
        print(f"  {max_n:>8} {score:>5}/{n} {delta_s:>6} {total_nones:>6} "
              f"{total_distinct/n:>11.1f} {avg_maj:>11.1f}%")

    # ═══════════════════════════════════════════════════════════════
    # Section 2: Per-problem minimum attempts for correct vote
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 2: MINIMUM ATTEMPTS NEEDED FOR CORRECT MAJORITY VOTE")
    print(f"  {'─'*80}")

    min_needed = {}
    for p in problems:
        if p.expected is None:
            continue
        atts = sorted(p.attempts, key=lambda a: a.attempt_num)
        found_at = None
        for cutoff in range(1, len(atts) + 1):
            votes = Counter(a.answer for a in atts[:cutoff] if a.answer is not None)
            if votes:
                winner = votes.most_common(1)[0][0]
                if str(winner) == str(p.expected):
                    found_at = cutoff
                    break
        min_needed[p.problem_id] = found_at  # None = never correct

    # Distribution
    found_counts = [v for v in min_needed.values() if v is not None]
    never_found = sum(1 for v in min_needed.values() if v is None)

    print(f"  Problems that achieve correct vote:")
    buckets = [(1, 4), (4, 8), (8, 12), (12, 16), (16, 20), (20, 24), (24, 28), (28, 33)]
    for lo, hi in buckets:
        count = sum(1 for v in found_counts if lo <= v < hi)
        bar = '█' * count
        print(f"    {lo:>2}-{hi-1:<2} attempts: {count:>3} {bar}")
    print(f"    Never correct: {never_found:>3} {'█' * never_found}")

    if found_counts:
        print(f"\n  Stats: mean={sum(found_counts)/len(found_counts):.1f}, "
              f"median={sorted(found_counts)[len(found_counts)//2]}, "
              f"P90={sorted(found_counts)[int(len(found_counts)*0.9)]}")

    # ═══════════════════════════════════════════════════════════════
    # Section 3: Wall time model
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 3: WALL TIME MODEL — how does wall time scale with attempts?")
    print(f"  {'─'*80}")

    # For each problem, compute wall time at different attempt counts
    # Wall time ≈ max(attempt_times[:N]) since they run in parallel
    print(f"  {'Attempts':>8} {'EstWall':>10} {'vsActual':>10} {'AvgPerProb':>12} {'For50prob':>10} {'For110prob':>11}")
    print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*12} {'─'*10} {'─'*11}")

    actual_wall = sum(p.wall_time for p in problems if p.wall_time)
    for max_n in test_counts:
        est_wall = 0
        for p in problems:
            atts = sorted(p.attempts, key=lambda a: a.attempt_num)[:max_n]
            times = [a.time_s for a in atts if a.time_s > 0]
            est_wall += max(times) if times else 0
        vs_actual = est_wall / actual_wall * 100 if actual_wall else 0
        avg_pp = est_wall / n
        for_50 = avg_pp * 50
        for_110 = avg_pp * 110
        print(f"  {max_n:>8} {fmt(est_wall):>10} {vs_actual:>9.1f}% {fmt(avg_pp):>12} {fmt(for_50):>10} {fmt(for_110):>11}")

    # ═══════════════════════════════════════════════════════════════
    # Section 4: Effective parallelism
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 4: EFFECTIVE PARALLELISM AT DIFFERENT ATTEMPT COUNTS")
    print(f"  {'─'*80}")

    print(f"  {'Attempts':>8} {'SumAtt':>10} {'SumWall':>10} {'EffParallel':>12} {'Utilization':>12}")
    print(f"  {'─'*8} {'─'*10} {'─'*10} {'─'*12} {'─'*12}")

    for max_n in test_counts:
        sum_att = 0
        sum_wall = 0
        for p in problems:
            atts = sorted(p.attempts, key=lambda a: a.attempt_num)[:max_n]
            times = [a.time_s for a in atts if a.time_s > 0]
            sum_att += sum(times)
            sum_wall += max(times) if times else 0
        eff = sum_att / sum_wall if sum_wall > 0 else 0
        util = eff / max_n * 100
        print(f"  {max_n:>8} {fmt(sum_att):>10} {fmt(sum_wall):>10} {eff:>11.1f}x {util:>11.1f}%")

    # ═══════════════════════════════════════════════════════════════
    # Section 5: Time budget simulation
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 5: TIME BUDGET SIMULATION — can we fit within limits?")
    print(f"  {'─'*90}")

    # Assumptions: notebook_limit=17400s (4.83h), reserved_per_problem=150s, problem_timeout=400s
    # Wave 1 overhead ≈ 50s per problem
    notebook_limit = 17400
    wave1_overhead = 50  # seconds per problem

    print(f"  Assumptions: notebook_limit={notebook_limit}s ({notebook_limit/3600:.1f}h), "
          f"wave1={wave1_overhead}s/prob")
    print(f"  {'Attempts':>8} {'ProbCount':>9} {'AvgWall':>8} {'W1+W2':>8} "
          f"{'Total50':>9} {'Total110':>10} {'Fit50?':>7} {'Fit110?':>8}")
    print(f"  {'─'*8} {'─'*9} {'─'*8} {'─'*8} {'─'*9} {'─'*10} {'─'*7} {'─'*8}")

    for max_n in test_counts:
        # Avg wall time per problem at this attempt count
        walls = []
        for p in problems:
            atts = sorted(p.attempts, key=lambda a: a.attempt_num)[:max_n]
            times = [a.time_s for a in atts if a.time_s > 0]
            walls.append(max(times) if times else 0)
        avg_wall = sum(walls) / len(walls) if walls else 0
        total_per_prob = avg_wall + wave1_overhead
        total_50 = total_per_prob * 50
        total_110 = total_per_prob * 110
        fit_50 = "YES" if total_50 < notebook_limit else "NO"
        fit_110 = "YES" if total_110 < notebook_limit else "NO"
        print(f"  {max_n:>8} {n:>9} {fmt(avg_wall):>8} {fmt(total_per_prob):>8} "
              f"{fmt(total_50):>9} {fmt(total_110):>10} {fit_50:>7} {fit_110:>8}")

    # ═══════════════════════════════════════════════════════════════
    # Section 6: Attempt time distribution (queue pressure)
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 6: ATTEMPT TIME DISTRIBUTION — fast vs slow (queue pressure)")
    print(f"  {'─'*80}")

    all_att_times = [a.time_s for p in problems for a in p.attempts if a.time_s > 0]
    if all_att_times:
        print(f"  Total attempts: {len(all_att_times)}")
        print(f"  Mean: {fmt(sum(all_att_times)/len(all_att_times))}, "
              f"Median: {fmt(sorted(all_att_times)[len(all_att_times)//2])}, "
              f"P10: {fmt(percentile(all_att_times, 10))}, "
              f"P90: {fmt(percentile(all_att_times, 90))}")

        # Histogram
        hist_buckets = [(0, 15), (15, 30), (30, 60), (60, 120), (120, 180),
                        (180, 240), (240, 300), (300, 400), (400, 9999)]
        hist_labels = ["<15s", "15-30s", "30-60s", "1-2m", "2-3m", "3-4m", "4-5m", "5-6.7m", "6.7m+"]
        print(f"\n  {'Bucket':<10} {'Count':>6} {'Pct':>6}  Bar")
        for (lo, hi), label in zip(hist_buckets, hist_labels):
            count = sum(1 for t in all_att_times if lo <= t < hi)
            pct = count * 100 / len(all_att_times)
            bar = '█' * int(pct)
            print(f"  {label:<10} {count:>6} {pct:>5.1f}%  {bar}")

        # Spread within each problem: stdev of attempt times
        print(f"\n  Per-problem attempt time spread (stdev):")
        spreads = []
        for p in problems:
            times = [a.time_s for a in p.attempts if a.time_s > 0]
            if len(times) >= 2:
                m = sum(times) / len(times)
                sd = math.sqrt(sum((t - m) ** 2 for t in times) / (len(times) - 1))
                spreads.append((p.problem_id[:8], sd, m, max(times) - min(times)))
        spreads.sort(key=lambda x: -x[1])
        print(f"  {'PID':<10} {'Stdev':>8} {'Mean':>8} {'Range':>8}")
        print(f"  {'─'*10} {'─'*8} {'─'*8} {'─'*8}")
        for pid, sd, m, rng in spreads[:10]:
            print(f"  {pid:<10} {fmt(sd):>8} {fmt(m):>8} {fmt(rng):>8}")
        avg_sd = sum(s for _, s, _, _ in spreads) / len(spreads) if spreads else 0
        print(f"  Average stdev: {fmt(avg_sd)}")
        print(f"  → High stdev means uneven attempt durations → GPU idle while waiting for slowest")

    # ═══════════════════════════════════════════════════════════════
    # Section 7: Which problems NEED more attempts?
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 7: PROBLEMS THAT BENEFIT FROM MORE ATTEMPTS")
    print(f"  {'─'*90}")

    # Vote stability: at what N does the winner stabilize?
    print(f"  {'PID':<10} {'Status':<6} {'StableAt':>8} {'TopV@16':>8} {'TopV@24':>8} {'TopV@32':>8} "
          f"{'Correct@16':>10} {'Correct@32':>10}")
    print(f"  {'─'*10} {'─'*6} {'─'*8} {'─'*8} {'─'*8} {'─'*8} {'─'*10} {'─'*10}")

    for p in problems:
        atts = sorted(p.attempts, key=lambda a: a.attempt_num)

        # Find when winner stabilizes (winner at N == winner at final)
        final_votes = Counter(a.answer for a in atts if a.answer is not None)
        final_winner = final_votes.most_common(1)[0][0] if final_votes else None

        stable_at = None
        for cutoff in range(1, len(atts) + 1):
            votes = Counter(a.answer for a in atts[:cutoff] if a.answer is not None)
            if votes and votes.most_common(1)[0][0] == final_winner:
                if stable_at is None:
                    stable_at = cutoff
            else:
                stable_at = None  # reset

        # Top votes at different counts
        def top_v_at(n):
            v = Counter(a.answer for a in atts[:n] if a.answer is not None)
            return v.most_common(1)[0][1] if v else 0

        def correct_at(n):
            v = Counter(a.answer for a in atts[:n] if a.answer is not None)
            if v:
                w = v.most_common(1)[0][0]
                return "YES" if p.expected is not None and str(w) == str(p.expected) else "NO"
            return "?"

        tv16 = top_v_at(min(16, len(atts)))
        tv24 = top_v_at(min(24, len(atts)))
        tv32 = top_v_at(min(32, len(atts)))
        c16 = correct_at(min(16, len(atts)))
        c32 = correct_at(min(32, len(atts)))
        status = "OK" if p.correct else "WRONG"

        # Only show interesting problems (unstable or changed between 16 and 32)
        if stable_at is None or stable_at > 12 or c16 != c32 or not p.correct:
            print(f"  {p.problem_id[:8]:<10} {status:<6} {stable_at or 'never':>8} "
                  f"{tv16:>8} {tv24:>8} {tv32:>8} {c16:>10} {c32:>10}")

    # ═══════════════════════════════════════════════════════════════
    # Section 8: Recommendation
    # ═══════════════════════════════════════════════════════════════
    print(f"\n  SECTION 8: RECOMMENDATION")
    print(f"  {'─'*80}")

    # Find sweet spot: max score with time budget
    best_n = actual_att
    best_score = score_at_n.get(actual_att, total_correct)
    for max_n in test_counts:
        s = score_at_n.get(max_n, 0)
        if s >= best_score:
            best_n = max_n
            best_score = s

    # Find minimum N that achieves best score
    min_for_best = min(c for c in test_counts if score_at_n.get(c, 0) >= best_score)

    print(f"  Current: {actual_att} attempts → {total_correct}/{n}")
    print(f"  Best score achievable: {best_score}/{n}")
    print(f"  Minimum attempts for best score: {min_for_best}")

    # Score at key points
    for c in [16, 24, 32, 48]:
        if c in score_at_n:
            print(f"  Score at {c}: {score_at_n[c]}/{n}")

    # Time tradeoff
    print(f"\n  Time tradeoff (estimated wall time for 50 problems):")
    for max_n in [16, 24, 32, 48]:
        if max_n > actual_att:
            continue
        walls = []
        for p in problems:
            atts = sorted(p.attempts, key=lambda a: a.attempt_num)[:max_n]
            times = [a.time_s for a in atts if a.time_s > 0]
            walls.append(max(times) if times else 0)
        avg_w = sum(walls) / len(walls)
        total_50 = (avg_w + 50) * 50  # +50 for wave1
        print(f"    {max_n} att: avg_wall={fmt(avg_w)}/prob, 50 prob={fmt(total_50)} "
              f"({'within' if total_50 < 17400 else 'OVER'} 4.8h limit)")

    print(f"\n{'='*95}")


if __name__ == '__main__':
    main()
