#!/usr/bin/env python3
"""
Time Distribution Analysis
==========================
Comprehensive timing distributions for AIMO3 diagnostic logs.

Sections:
1. Overall attempt time distribution (correct vs wrong vs none)
2. Histogram buckets with cumulative %
3. Per-tier time distributions
4. Per-topic time distributions (reuses topic_analysis.classify_problem)
5. Optimal timeout analysis (score vs timeout cap)
6. Per-problem wall time breakdown

Usage:
    python3 log_exploration/time_distribution.py output/v31/diagnostic.log
    python3 log_exploration/time_distribution.py output/v31/diagnostic.log --tier T1
    python3 log_exploration/time_distribution.py output/v31/diagnostic.log --topic "Number Theory"
"""

import sys
import os
import math
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log
from log_exploration.topic_analysis import classify_problem

# ── Tier mapping ──
KNOWN_TIERS = {
    'dbbfe8': 'T0', '3b88b3': 'T0',
    '86e8e5': 'T0.5',
}


def get_tier(pid_short, problem_correct):
    if pid_short in KNOWN_TIERS:
        return KNOWN_TIERS[pid_short]
    return 'T2' if problem_correct else 'T1'


def percentiles(values, pcts=[10, 25, 50, 75, 90, 95, 99]):
    if not values:
        return {}
    s = sorted(values)
    n = len(s)
    result = {}
    for p in pcts:
        k = (p / 100) * (n - 1)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            result[p] = s[int(k)]
        else:
            result[p] = s[f] * (c - k) + s[c] * (k - f)
    return result


def histogram(values, bucket_size=30, max_val=None):
    """Return list of (bucket_start, count) tuples."""
    if not values:
        return []
    if max_val is None:
        max_val = max(values)
    buckets = []
    start = 0
    while start <= max_val:
        count = sum(1 for v in values if start <= v < start + bucket_size)
        buckets.append((start, count))
        start += bucket_size
    return buckets


def print_distribution(label, values, bucket_size=30):
    """Print a text histogram with percentiles."""
    if not values:
        print(f"  {label}: no data")
        return

    print(f"\n  {label}: n={len(values)}, mean={sum(values)/len(values):.1f}s, "
          f"min={min(values):.1f}s, max={max(values):.1f}s")

    pcts = percentiles(values)
    pct_str = "  ".join(f"P{p}={v:.0f}s" for p, v in pcts.items())
    print(f"  {pct_str}")

    buckets = histogram(values, bucket_size)
    max_count = max(c for _, c in buckets) if buckets else 1
    bar_width = 40
    cumulative = 0
    total = len(values)

    print(f"  {'Time (s)':<12} {'Count':>6} {'Cum%':>6}  Bar")
    for start, count in buckets:
        if count == 0 and start > max(values):
            break
        cumulative += count
        pct = 100 * cumulative / total
        bar_len = int(bar_width * count / max_count) if max_count > 0 else 0
        bar = '█' * bar_len
        print(f"  {start:>4}-{start+bucket_size:<5}s {count:>6} {pct:>5.1f}%  {bar}")


def simulate_timeout_scores(problems, timeout_caps):
    """Simulate score at different timeout caps."""
    results = []

    for cap in timeout_caps:
        score = 0
        for p in problems:
            # Filter attempts that finish within cap
            valid = [a for a in p.attempts if a.time_s <= cap and a.answer is not None]
            if not valid:
                continue

            # Majority vote among valid attempts
            vote_counts = defaultdict(int)
            for a in valid:
                vote_counts[a.answer] += 1

            if vote_counts:
                best = max(vote_counts.items(), key=lambda x: (x[1], x[0]))
                predicted = best[0]
                if p.expected is not None and str(predicted) == str(p.expected):
                    score += 1

        results.append((cap, score))
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('logfile')
    parser.add_argument('--tier', help='Filter to specific tier')
    parser.add_argument('--topic', help='Filter to specific topic')
    parser.add_argument('--bucket', type=int, default=30, help='Histogram bucket size in seconds')
    args = parser.parse_args()

    problems = parse_log(args.logfile)
    if not problems:
        print("No problems found.")
        sys.exit(1)

    # Classify topics
    problem_topics = {}
    for p in problems:
        matches = classify_problem(p.problem_text)
        problem_topics[p.problem_id] = [t[0] for t in matches]

    # Assign tiers
    problem_tiers = {}
    for p in problems:
        pid = p.problem_id[:8]
        problem_tiers[p.problem_id] = get_tier(pid, p.correct)

    # Apply filters
    filtered = problems
    if args.tier:
        filtered = [p for p in filtered if problem_tiers[p.problem_id] == args.tier]
    if args.topic:
        filtered = [p for p in filtered if args.topic in problem_topics[p.problem_id]]

    if not filtered:
        print(f"No problems match filter (tier={args.tier}, topic={args.topic})")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════════════════
    # Section 1: Overall attempt time distribution
    # ═══════════════════════════════════════════════════════════════════
    print("=" * 70)
    print("SECTION 1: ATTEMPT TIME DISTRIBUTION (correct vs wrong vs none)")
    print("=" * 70)

    correct_times = []
    wrong_times = []
    none_times = []

    for p in filtered:
        for a in p.attempts:
            if a.answer is None:
                none_times.append(a.time_s)
            elif p.expected is not None and str(a.answer) == str(p.expected):
                correct_times.append(a.time_s)
            else:
                wrong_times.append(a.time_s)

    print_distribution("CORRECT attempts", correct_times, args.bucket)
    print_distribution("WRONG attempts", wrong_times, args.bucket)
    print_distribution("NONE (no answer)", none_times, args.bucket)

    # ═══════════════════════════════════════════════════════════════════
    # Section 2: Per-tier distributions
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION 2: PER-TIER TIME DISTRIBUTIONS")
    print("=" * 70)

    tiers = sorted(set(problem_tiers[p.problem_id] for p in filtered))
    for tier in tiers:
        tier_problems = [p for p in filtered if problem_tiers[p.problem_id] == tier]
        n_correct = sum(1 for p in tier_problems if p.correct)
        n_total = len(tier_problems)
        print(f"\n{'─' * 50}")
        print(f"  TIER {tier}: {n_correct}/{n_total} problems correct")
        print(f"{'─' * 50}")

        tc = []
        tw = []
        tn = []
        for p in tier_problems:
            for a in p.attempts:
                if a.answer is None:
                    tn.append(a.time_s)
                elif p.expected is not None and str(a.answer) == str(p.expected):
                    tc.append(a.time_s)
                else:
                    tw.append(a.time_s)

        print_distribution("Correct", tc, args.bucket)
        print_distribution("Wrong", tw, args.bucket)
        print_distribution("None", tn, args.bucket)

    # ═══════════════════════════════════════════════════════════════════
    # Section 3: Per-topic distributions
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION 3: PER-TOPIC TIME DISTRIBUTIONS")
    print("=" * 70)

    all_topics = set()
    for p in filtered:
        all_topics.update(problem_topics[p.problem_id])

    for topic in sorted(all_topics):
        topic_problems = [p for p in filtered if topic in problem_topics[p.problem_id]]
        n_correct = sum(1 for p in topic_problems if p.correct)
        n_total = len(topic_problems)
        print(f"\n{'─' * 50}")
        print(f"  {topic}: {n_correct}/{n_total} problems correct")
        print(f"{'─' * 50}")

        tc = []
        tw = []
        for p in topic_problems:
            for a in p.attempts:
                if a.answer is None:
                    continue
                if p.expected is not None and str(a.answer) == str(p.expected):
                    tc.append(a.time_s)
                else:
                    tw.append(a.time_s)

        print_distribution("Correct", tc, args.bucket)
        print_distribution("Wrong", tw, args.bucket)

    # ═══════════════════════════════════════════════════════════════════
    # Section 4: Optimal timeout (score vs cap)
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION 4: SCORE vs TIMEOUT CAP")
    print("=" * 70)

    # Overall
    caps = list(range(30, 901, 30))
    results = simulate_timeout_scores(filtered, caps)

    total_problems = len(filtered)
    print(f"\n  {'Timeout':>8}  {'Score':>6}  {'Pct':>6}  Bar")
    max_score = max(s for _, s in results) if results else 1
    for cap, score in results:
        bar_len = int(30 * score / max_score) if max_score > 0 else 0
        bar = '█' * bar_len
        print(f"  {cap:>6}s  {score:>6}  {100*score/total_problems:>5.1f}%  {bar}")

    # Per-tier timeout
    print(f"\n  Per-tier score vs timeout:")
    print(f"  {'Timeout':>8}", end="")
    for tier in tiers:
        print(f"  {tier:>6}", end="")
    print()

    for cap in [60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 720, 900]:
        print(f"  {cap:>6}s", end="")
        for tier in tiers:
            tier_problems = [p for p in filtered if problem_tiers[p.problem_id] == tier]
            tier_results = simulate_timeout_scores(tier_problems, [cap])
            if tier_results:
                _, score = tier_results[0]
                total = len(tier_problems)
                print(f"  {score:>2}/{total:<2}", end="")
            else:
                print(f"  {'--':>6}", end="")
        print()

    # ═══════════════════════════════════════════════════════════════════
    # Section 5: Per-problem wall time
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION 5: PER-PROBLEM WALL TIME (sorted by time)")
    print("=" * 70)

    prob_data = []
    for p in filtered:
        pid = p.problem_id[:8]
        tier = problem_tiers[p.problem_id]
        topics = problem_topics[p.problem_id]
        attempt_times = [a.time_s for a in p.attempts]
        correct_attempt_times = [a.time_s for a in p.attempts
                                  if a.answer is not None and p.expected is not None
                                  and str(a.answer) == str(p.expected)]

        prob_data.append({
            'pid': pid,
            'tier': tier,
            'topics': topics,
            'wall_time': p.wall_time,
            'correct': p.correct,
            'max_attempt': max(attempt_times) if attempt_times else 0,
            'median_attempt': sorted(attempt_times)[len(attempt_times)//2] if attempt_times else 0,
            'fastest_correct': min(correct_attempt_times) if correct_attempt_times else None,
            'n_correct': len(correct_attempt_times),
            'n_attempts': len(p.attempts),
        })

    prob_data.sort(key=lambda x: x['wall_time'], reverse=True)

    print(f"\n  {'PID':<10} {'Tier':<5} {'Wall':>6} {'Max':>6} {'Med':>5} {'FastC':>6} {'C/N':>5} {'Status':<7} Topics")
    print("  " + "─" * 90)
    for d in prob_data:
        fc = f"{d['fastest_correct']:.0f}s" if d['fastest_correct'] is not None else "  --"
        status = "OK" if d['correct'] else "WRONG"
        topics = ", ".join(d['topics'][:2])
        print(f"  {d['pid']:<10} {d['tier']:<5} {d['wall_time']:>5.0f}s {d['max_attempt']:>5.0f}s "
              f"{d['median_attempt']:>4.0f}s {fc:>6} {d['n_correct']:>2}/{d['n_attempts']:<2} "
              f"{status:<7} {topics}")

    # ═══════════════════════════════════════════════════════════════════
    # Section 6: Key recommendations
    # ═══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("SECTION 6: TIMEOUT RECOMMENDATION")
    print("=" * 70)

    # Find the timeout that maximizes score
    best_cap, best_score = max(results, key=lambda x: x[1])
    # Find the MINIMUM timeout that achieves best_score
    min_optimal = min(cap for cap, score in results if score == best_score)

    print(f"\n  Best score: {best_score}/{total_problems}")
    print(f"  Achieved at: {min_optimal}s (first cap reaching max score)")
    print(f"  Score at 240s: {next(s for c,s in results if c==240)}/{total_problems}")
    print(f"  Score at 300s: {next(s for c,s in results if c==300)}/{total_problems}")
    print(f"  Score at 420s: {next(s for c,s in results if c==420)}/{total_problems}")
    print(f"  Score at 600s: {next(s for c,s in results if c==600)}/{total_problems}")
    print(f"  Score at 900s: {next(s for c,s in results if c==900)}/{total_problems}")

    # Efficiency: time saved
    total_time_900 = sum(min(a.time_s, 900) for p in filtered for a in p.attempts)
    total_time_opt = sum(min(a.time_s, min_optimal) for p in filtered for a in p.attempts)
    saved = total_time_900 - total_time_opt
    print(f"\n  Total attempt-time at 900s cap: {total_time_900/60:.0f} min")
    print(f"  Total attempt-time at {min_optimal}s cap: {total_time_opt/60:.0f} min")
    print(f"  Time saved: {saved/60:.0f} min ({100*saved/total_time_900:.1f}%)")


if __name__ == '__main__':
    main()
