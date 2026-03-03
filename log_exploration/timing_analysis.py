#!/usr/bin/env python3
"""
Timing Analysis for AIMO3 Solver
=================================
Analyzes time distribution, time-vs-correctness correlation,
wasted time on None attempts, diminishing returns, and budget utilization.

Usage: python3 log_exploration/timing_analysis.py output/v22/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def fmt_time(s):
    """Format seconds as human-readable."""
    if s >= 3600:
        return f"{s/3600:.1f}h"
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


def percentile(vals, p):
    """Compute p-th percentile."""
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f])


def median(vals):
    return percentile(vals, 50)


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def analyze_time_distribution(problems):
    """Time distribution: per-problem, per-attempt, per-turn."""
    print_section("TIME DISTRIBUTION")

    # Per-problem wall time
    wall_times = [p.wall_time for p in problems if p.wall_time > 0]
    print(f"\n  Per-Problem Wall Time ({len(wall_times)} problems)")
    print(f"  {'Metric':<20} {'Value':>10}")
    print(f"  {'─' * 20} {'─' * 10}")
    print(f"  {'Min':<20} {fmt_time(min(wall_times)):>10}")
    print(f"  {'Max':<20} {fmt_time(max(wall_times)):>10}")
    print(f"  {'Mean':<20} {fmt_time(mean(wall_times)):>10}")
    print(f"  {'Median':<20} {fmt_time(median(wall_times)):>10}")
    print(f"  {'Stdev':<20} {fmt_time(stdev(wall_times)):>10}")
    print(f"  {'P25':<20} {fmt_time(percentile(wall_times, 25)):>10}")
    print(f"  {'P75':<20} {fmt_time(percentile(wall_times, 75)):>10}")
    print(f"  {'P90':<20} {fmt_time(percentile(wall_times, 90)):>10}")
    print(f"  {'P95':<20} {fmt_time(percentile(wall_times, 95)):>10}")
    print(f"  {'Total':<20} {fmt_time(sum(wall_times)):>10}")

    # Histogram of wall times
    print(f"\n  Wall Time Distribution:")
    buckets = [(0, 10), (10, 30), (30, 60), (60, 120), (120, 300), (300, 600), (600, float('inf'))]
    labels = ["0-10s", "10-30s", "30-60s", "1-2min", "2-5min", "5-10min", "10min+"]
    for (lo, hi), label in zip(buckets, labels):
        count = sum(1 for t in wall_times if lo <= t < hi)
        bar = '#' * count
        print(f"  {label:>8} | {bar} ({count})")

    # Per-attempt time
    attempt_times = []
    for p in problems:
        for a in p.attempts:
            if a.time_s > 0:
                attempt_times.append(a.time_s)

    if attempt_times:
        print(f"\n  Per-Attempt Time ({len(attempt_times)} attempts)")
        print(f"  {'Metric':<20} {'Value':>10}")
        print(f"  {'─' * 20} {'─' * 10}")
        print(f"  {'Min':<20} {fmt_time(min(attempt_times)):>10}")
        print(f"  {'Max':<20} {fmt_time(max(attempt_times)):>10}")
        print(f"  {'Mean':<20} {fmt_time(mean(attempt_times)):>10}")
        print(f"  {'Median':<20} {fmt_time(median(attempt_times)):>10}")
        print(f"  {'P90':<20} {fmt_time(percentile(attempt_times, 90)):>10}")

    # Per-turn time (estimated from attempt time / turns)
    turn_counts = []
    for p in problems:
        for a in p.attempts:
            if a.turns:
                turn_counts.append(len(a.turns))

    if turn_counts:
        print(f"\n  Turns per Attempt ({len(turn_counts)} attempts with turn data)")
        print(f"  {'Metric':<20} {'Value':>10}")
        print(f"  {'─' * 20} {'─' * 10}")
        print(f"  {'Min':<20} {min(turn_counts):>10}")
        print(f"  {'Max':<20} {max(turn_counts):>10}")
        print(f"  {'Mean':<20} {mean(turn_counts):>10.1f}")
        print(f"  {'Median':<20} {median(turn_counts):>10.0f}")


def analyze_time_vs_correctness(problems):
    """Correlation: time vs correctness."""
    print_section("TIME vs CORRECTNESS")

    correct_times = [p.wall_time for p in problems if p.correct and p.wall_time > 0]
    wrong_times = [p.wall_time for p in problems if not p.correct and p.wall_time > 0]

    print(f"\n  {'Category':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'Min':>8} {'Max':>8} {'Total':>10}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 8} {'─' * 8} {'─' * 10}")
    if correct_times:
        print(f"  {'Correct':<20} {len(correct_times):>6} {fmt_time(mean(correct_times)):>10} {fmt_time(median(correct_times)):>10} {fmt_time(min(correct_times)):>8} {fmt_time(max(correct_times)):>8} {fmt_time(sum(correct_times)):>10}")
    if wrong_times:
        print(f"  {'Wrong':<20} {len(wrong_times):>6} {fmt_time(mean(wrong_times)):>10} {fmt_time(median(wrong_times)):>10} {fmt_time(min(wrong_times)):>8} {fmt_time(max(wrong_times)):>8} {fmt_time(sum(wrong_times)):>10}")

    # Per-attempt: correct vs wrong vs None
    correct_att_times = []
    wrong_att_times = []
    none_att_times = []
    for p in problems:
        for a in p.attempts:
            if a.time_s <= 0:
                continue
            if a.is_none:
                none_att_times.append(a.time_s)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_att_times.append(a.time_s)
            elif a.answer is not None:
                wrong_att_times.append(a.time_s)

    print(f"\n  Per-Attempt Time by Outcome:")
    print(f"  {'Outcome':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'P90':>10} {'Total':>10}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")
    for label, times in [("Correct Answer", correct_att_times), ("Wrong Answer", wrong_att_times), ("None (no answer)", none_att_times)]:
        if times:
            print(f"  {label:<20} {len(times):>6} {fmt_time(mean(times)):>10} {fmt_time(median(times)):>10} {fmt_time(percentile(times, 90)):>10} {fmt_time(sum(times)):>10}")

    if correct_att_times and none_att_times:
        ratio = mean(none_att_times) / mean(correct_att_times) if mean(correct_att_times) > 0 else float('inf')
        print(f"\n  None attempts take {ratio:.1f}x the time of correct attempts on average.")


def analyze_wasted_time(problems):
    """Time on None attempts vs productive attempts."""
    print_section("WASTED TIME ANALYSIS")

    total_time = sum(p.wall_time for p in problems)
    total_none_time = 0
    total_wrong_time = 0
    total_correct_time = 0

    for p in problems:
        for a in p.attempts:
            if a.is_none:
                total_none_time += a.time_s
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                total_correct_time += a.time_s
            elif a.answer is not None:
                total_wrong_time += a.time_s

    total_att_time = total_none_time + total_wrong_time + total_correct_time
    print(f"\n  Time Breakdown by Attempt Outcome:")
    print(f"  {'Category':<25} {'Time':>10} {'% of Total':>10}")
    print(f"  {'─' * 25} {'─' * 10} {'─' * 10}")
    if total_att_time > 0:
        print(f"  {'Correct answers':<25} {fmt_time(total_correct_time):>10} {100*total_correct_time/total_att_time:>9.1f}%")
        print(f"  {'Wrong answers':<25} {fmt_time(total_wrong_time):>10} {100*total_wrong_time/total_att_time:>9.1f}%")
        print(f"  {'None (wasted)':<25} {fmt_time(total_none_time):>10} {100*total_none_time/total_att_time:>9.1f}%")
        print(f"  {'─' * 25} {'─' * 10} {'─' * 10}")
        print(f"  {'Total attempt time':<25} {fmt_time(total_att_time):>10} {'100.0%':>10}")

    # Problems where all time was wasted (wrong final answer)
    wrong_problems = [p for p in problems if not p.correct]
    if wrong_problems:
        wasted = sum(p.wall_time for p in wrong_problems)
        print(f"\n  Time on WRONG problems (entire problem wasted):")
        for p in wrong_problems:
            none_count = sum(1 for a in p.attempts if a.is_none)
            ans_count = sum(1 for a in p.attempts if not a.is_none)
            print(f"    {p.problem_id}: {fmt_time(p.wall_time)} | {ans_count} answers, {none_count} Nones | Predicted: {p.predicted}, Expected: {p.expected}")
        print(f"    Total wasted: {fmt_time(wasted)} ({100*wasted/total_time:.1f}% of total)")

    # Top 10 time-consuming None attempts
    none_attempts = []
    for p in problems:
        for a in p.attempts:
            if a.is_none:
                none_attempts.append((p.problem_id, a.attempt_num, a.time_s, a.errors, a.tokens))
    none_attempts.sort(key=lambda x: -x[2])
    if none_attempts:
        print(f"\n  Top 10 Most Expensive None Attempts:")
        print(f"  {'Problem':<10} {'Att#':>4} {'Time':>8} {'Errors':>7} {'Tokens':>8}")
        print(f"  {'─' * 10} {'─' * 4} {'─' * 8} {'─' * 7} {'─' * 8}")
        for pid, anum, t, errs, toks in none_attempts[:10]:
            print(f"  {pid:<10} {anum:>4} {fmt_time(t):>8} {errs:>7} {toks:>8}")


def analyze_diminishing_returns(problems):
    """After N correct answers seen, what's the value of attempt N+1?"""
    print_section("DIMINISHING RETURNS ANALYSIS")

    # For each problem, track when correct answers appear across attempts
    first_correct_by_attempt = defaultdict(int)  # attempt_num -> how many problems first got correct here
    cumulative_correct = defaultdict(int)  # attempt_num -> how many problems had at least one correct by this attempt

    for p in problems:
        if p.expected is None:
            continue
        seen_correct = False
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer == p.expected and not seen_correct:
                first_correct_by_attempt[a.attempt_num] += 1
                seen_correct = True

    # Cumulative: how many problems solved if we run up to N attempts
    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)
    solved_by_n = {}
    for n in range(1, max_att + 1):
        count = 0
        for p in problems:
            if p.expected is None:
                continue
            for a in p.attempts:
                if a.attempt_num <= n and a.answer == p.expected:
                    count += 1
                    break
        solved_by_n[n] = count

    total_with_expected = sum(1 for p in problems if p.expected is not None)
    print(f"\n  Marginal Value of Each Attempt (out of {total_with_expected} problems with expected answers):")
    print(f"  {'Attempt #':<12} {'First Correct':>15} {'Cumulative Solved':>20} {'% Solved':>10}")
    print(f"  {'─' * 12} {'─' * 15} {'─' * 20} {'─' * 10}")
    prev = 0
    for n in range(1, max_att + 1):
        solved = solved_by_n.get(n, 0)
        marginal = solved - prev
        pct = 100 * solved / total_with_expected if total_with_expected > 0 else 0
        marker = " <-- diminishing" if marginal == 0 and n > 1 else ""
        print(f"  {n:<12} {first_correct_by_attempt.get(n, 0):>15} {solved:>20} {pct:>9.1f}%{marker}")
        prev = solved

    # Simulate: if we ran only N attempts, what would the score be?
    # (Using voting among only the first N attempts)
    print(f"\n  Simulated Score with Fewer/More Attempts:")
    print(f"  {'Max Attempts':<15} {'Score':>8} {'Notes':<30}")
    print(f"  {'─' * 15} {'─' * 8} {'─' * 30}")
    for max_n in [1, 2, 3, 4, 5, 6, 7, 8]:
        score = 0
        for p in problems:
            if p.expected is None:
                continue
            # Simulate voting with only first max_n attempts
            votes = defaultdict(int)
            for a in p.attempts:
                if a.attempt_num <= max_n and a.answer is not None:
                    votes[a.answer] = votes.get(a.answer, 0) + 1
            if votes:
                winner = max(votes, key=votes.get)
                if winner == p.expected:
                    score += 1
        pct = 100 * score / total_with_expected if total_with_expected else 0
        actual = " (actual)" if max_n == 8 else ""
        print(f"  {max_n:<15} {score:>5}/{total_with_expected}{actual:<30}")


def analyze_budget_utilization(problems):
    """Budget given vs time actually used per problem."""
    print_section("BUDGET UTILIZATION")

    budgets = [(p.problem_id, p.budget, p.wall_time, p.correct, p.early_stop) for p in problems if p.budget > 0]
    if not budgets:
        print("  No budget data found.")
        return

    print(f"\n  {'Problem':<10} {'Budget':>8} {'Used':>8} {'Util%':>7} {'OK':>4} {'ES':>4} {'Remaining':>10}")
    print(f"  {'─' * 10} {'─' * 8} {'─' * 8} {'─' * 7} {'─' * 4} {'─' * 4} {'─' * 10}")

    total_budget = 0
    total_used = 0
    for pid, budget, used, correct, es in sorted(budgets, key=lambda x: x[2] / x[1] if x[1] > 0 else 0, reverse=True):
        util = 100 * used / budget if budget > 0 else 0
        remaining = budget - used
        ok = "Y" if correct else "N"
        es_str = "Y" if es else "N"
        print(f"  {pid:<10} {fmt_time(budget):>8} {fmt_time(used):>8} {util:>6.1f}% {ok:>4} {es_str:>4} {fmt_time(remaining):>10}")
        total_budget += budget
        total_used += used

    total_util = 100 * total_used / total_budget if total_budget > 0 else 0
    print(f"  {'─' * 10} {'─' * 8} {'─' * 8} {'─' * 7}")
    print(f"  {'TOTAL':<10} {fmt_time(total_budget):>8} {fmt_time(total_used):>8} {total_util:>6.1f}%")
    print(f"\n  Average utilization: {total_util:.1f}%")
    print(f"  Unused budget: {fmt_time(total_budget - total_used)} ({100 - total_util:.1f}%)")

    # Early stop savings
    es_problems = [p for p in problems if p.early_stop]
    non_es = [p for p in problems if not p.early_stop and p.budget > 0]
    if es_problems:
        es_saved = sum(p.budget - p.wall_time for p in es_problems if p.budget > 0)
        print(f"\n  Early-stopped problems: {len(es_problems)}")
        print(f"  Time saved by early stop: {fmt_time(es_saved)}")
        avg_es_util = mean([p.wall_time / p.budget for p in es_problems if p.budget > 0]) * 100
        print(f"  Avg utilization (early-stopped): {avg_es_util:.1f}%")
    if non_es:
        avg_nes_util = mean([p.wall_time / p.budget for p in non_es]) * 100
        print(f"  Avg utilization (not early-stopped): {avg_nes_util:.1f}%")


def print_actionable_insights(problems):
    """Summarize key findings and recommendations."""
    print_section("ACTIONABLE INSIGHTS")

    total_time = sum(p.wall_time for p in problems)
    none_time = sum(a.time_s for p in problems for a in p.attempts if a.is_none)
    wrong_time = sum(p.wall_time for p in problems if not p.correct)
    correct_att_times = [a.time_s for p in problems for a in p.attempts if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected]
    none_att_times = [a.time_s for p in problems for a in p.attempts if a.is_none and a.time_s > 0]

    # Count Nones
    total_none = sum(1 for p in problems for a in p.attempts if a.is_none)
    total_att = sum(len(p.attempts) for p in problems)

    # Early stop rate
    es_count = sum(1 for p in problems if p.early_stop)

    insights = []

    # 1. None waste
    if none_att_times:
        none_ratio = mean(none_att_times) / mean(correct_att_times) if correct_att_times and mean(correct_att_times) > 0 else 0
        insights.append(
            f"1. NONE WASTE: {total_none}/{total_att} attempts ({100*total_none/total_att:.0f}%) returned None, "
            f"consuming {fmt_time(none_time)}. "
            f"None attempts average {fmt_time(mean(none_att_times))}, "
            f"{none_ratio:.1f}x {'more' if none_ratio > 1 else 'less'} than correct attempts ({fmt_time(mean(correct_att_times))}). "
            f"RECOMMENDATION: Reduce None rate via better answer extraction or timeout management."
        )

    # 2. Early stop
    insights.append(
        f"2. EARLY STOP: {es_count}/{len(problems)} problems ({100*es_count/len(problems):.0f}%) triggered early stop. "
        f"Budget utilization is very low — most problems solve well before deadline. "
        f"RECOMMENDATION: Consider more aggressive early stop (threshold 3 instead of 5) to save budget for harder problems."
    )

    # 3. Wrong problems
    wrong_problems = [p for p in problems if not p.correct]
    if wrong_problems:
        insights.append(
            f"3. WRONG PROBLEMS: {len(wrong_problems)} problems answered incorrectly, using {fmt_time(wrong_time)} "
            f"({100*wrong_time/total_time:.1f}% of total time). "
            f"These problems may benefit from more attempts or different strategies."
        )

    # 4. Diminishing returns
    # Check if all problems already solved by attempt 3
    solved_by_3 = 0
    total_with_exp = sum(1 for p in problems if p.expected is not None)
    for p in problems:
        if p.expected is None:
            continue
        for a in p.attempts:
            if a.attempt_num <= 3 and a.answer == p.expected:
                solved_by_3 += 1
                break
    insights.append(
        f"4. ATTEMPT COUNT: {solved_by_3}/{total_with_exp} problems have at least one correct answer in first 3 attempts. "
        f"Running 8 attempts with early stop at 5 matching provides redundancy for voting. "
        f"Consider: running 4 fast attempts for easy problems, 16 for hard ones (adaptive)."
    )

    for insight in insights:
        print(f"\n  {insight}")
    print()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: File not found: {logfile}")
        sys.exit(1)

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_time_distribution(problems)
    analyze_time_vs_correctness(problems)
    analyze_wasted_time(problems)
    analyze_diminishing_returns(problems)
    analyze_budget_utilization(problems)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
