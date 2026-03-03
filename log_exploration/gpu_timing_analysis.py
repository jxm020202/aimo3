#!/usr/bin/env python3
"""
GPU Timing & Utilization Analysis for AIMO3 Solver
====================================================
Deep analysis of v23 timing, parallelism, token usage, and budget headroom.

Answers:
  1. Per-problem timing distribution — which problems are time hogs?
  2. Per-attempt timing distribution
  3. Time spent on None vs correct vs wrong attempts
  4. Early stop analysis — how often does it trigger?
  5. Token usage per attempt — distribution, correlation with success
  6. Parallelism analysis — are all 16 workers busy?
  7. Time budget analysis — per-problem average, headroom to 300 min target
  8. Reduced-attempt simulation — estimated savings at 12 attempts

Usage:
    python3 log_exploration/gpu_timing_analysis.py output/v23/diagnostic.log
    python3 log_exploration/gpu_timing_analysis.py output/v23/diagnostic.log --save output/v23/gpu_timing_analysis.md
"""

import sys
import os
import io
import math
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

def mean(vals):
    return sum(vals) / len(vals) if vals else 0

def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    return (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]

def percentile(vals, p):
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (k - f) * (s[c] - s[f])

def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))

def fmt_time(s):
    if s >= 3600:
        return f"{s/3600:.1f}h"
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"

def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))

def print_section(title, out):
    out.write(f"\n{'=' * 78}\n")
    out.write(f"  {title}\n")
    out.write(f"{'=' * 78}\n")

def w(out, text=""):
    out.write(text + "\n")


# ── Analysis 1: Per-Problem Timing Distribution ─────────────────────────────

def analyze_per_problem_timing(problems, out):
    print_section("1. PER-PROBLEM TIMING DISTRIBUTION", out)

    wall_times = [(p.problem_id, p.wall_time, p.correct, len(p.attempts), p.early_stop)
                  for p in problems if p.wall_time > 0]
    times_only = [t for _, t, _, _, _ in wall_times]

    w(out)
    w(out, f"  Total problems: {len(wall_times)}")
    w(out, f"  Total wall time (sum): {fmt_time(sum(times_only))}")
    w(out)
    w(out, f"  {'Metric':<20} {'Value':>10}")
    w(out, f"  {'---':<20} {'---':>10}")
    w(out, f"  {'Min':<20} {fmt_time(min(times_only)):>10}")
    w(out, f"  {'P10':<20} {fmt_time(percentile(times_only, 10)):>10}")
    w(out, f"  {'P25':<20} {fmt_time(percentile(times_only, 25)):>10}")
    w(out, f"  {'Median':<20} {fmt_time(median(times_only)):>10}")
    w(out, f"  {'Mean':<20} {fmt_time(mean(times_only)):>10}")
    w(out, f"  {'P75':<20} {fmt_time(percentile(times_only, 75)):>10}")
    w(out, f"  {'P90':<20} {fmt_time(percentile(times_only, 90)):>10}")
    w(out, f"  {'P95':<20} {fmt_time(percentile(times_only, 95)):>10}")
    w(out, f"  {'Max':<20} {fmt_time(max(times_only)):>10}")
    w(out, f"  {'Stdev':<20} {fmt_time(stdev(times_only)):>10}")

    # Histogram
    w(out)
    w(out, "  Wall Time Histogram:")
    buckets = [(0, 60), (60, 120), (120, 180), (180, 240), (240, 300),
               (300, 420), (420, 600), (600, float('inf'))]
    labels = ["<1min", "1-2min", "2-3min", "3-4min", "4-5min", "5-7min", "7-10min", "10min+"]
    for (lo, hi), label in zip(buckets, labels):
        count = sum(1 for t in times_only if lo <= t < hi)
        bar = '#' * count
        w(out, f"  {label:>8} | {bar} ({count})")

    # Top 15 time hogs
    wall_times.sort(key=lambda x: -x[1])
    w(out)
    w(out, "  Top 15 Time Hogs:")
    w(out, f"  {'Rank':>4} {'Problem':<10} {'Time':>8} {'OK':>4} {'Att':>4} {'ES':>4}")
    w(out, f"  {'---':>4} {'---':<10} {'---':>8} {'---':>4} {'---':>4} {'---':>4}")
    for i, (pid, t, correct, natts, es) in enumerate(wall_times[:15], 1):
        ok = "Y" if correct else "N"
        es_str = "Y" if es else "N"
        w(out, f"  {i:>4} {pid:<10} {fmt_time(t):>8} {ok:>4} {natts:>4} {es_str:>4}")

    # Time vs correctness at problem level
    correct_times = [t for _, t, c, _, _ in wall_times if c]
    wrong_times = [t for _, t, c, _, _ in wall_times if not c]
    w(out)
    w(out, "  Correct vs Wrong Problem Timing:")
    w(out, f"  {'Category':<15} {'Count':>6} {'Mean':>8} {'Median':>8} {'P90':>8} {'Total':>10}")
    w(out, f"  {'---':<15} {'---':>6} {'---':>8} {'---':>8} {'---':>8} {'---':>10}")
    if correct_times:
        w(out, f"  {'Correct':<15} {len(correct_times):>6} {fmt_time(mean(correct_times)):>8} {fmt_time(median(correct_times)):>8} {fmt_time(percentile(correct_times, 90)):>8} {fmt_time(sum(correct_times)):>10}")
    if wrong_times:
        w(out, f"  {'Wrong':<15} {len(wrong_times):>6} {fmt_time(mean(wrong_times)):>8} {fmt_time(median(wrong_times)):>8} {fmt_time(percentile(wrong_times, 90)):>8} {fmt_time(sum(wrong_times)):>10}")

    return times_only


# ── Analysis 2: Per-Attempt Timing Distribution ─────────────────────────────

def analyze_per_attempt_timing(problems, out):
    print_section("2. PER-ATTEMPT TIMING DISTRIBUTION", out)

    attempt_times = []
    for p in problems:
        for a in p.attempts:
            if a.time_s > 0:
                attempt_times.append(a.time_s)

    if not attempt_times:
        w(out, "  No attempt timing data found.")
        return

    w(out)
    w(out, f"  Total attempts with timing: {len(attempt_times)}")
    w(out, f"  Sum of attempt times: {fmt_time(sum(attempt_times))}")
    w(out)
    w(out, f"  {'Metric':<20} {'Value':>10}")
    w(out, f"  {'---':<20} {'---':>10}")
    w(out, f"  {'Min':<20} {fmt_time(min(attempt_times)):>10}")
    w(out, f"  {'P10':<20} {fmt_time(percentile(attempt_times, 10)):>10}")
    w(out, f"  {'P25':<20} {fmt_time(percentile(attempt_times, 25)):>10}")
    w(out, f"  {'Median':<20} {fmt_time(median(attempt_times)):>10}")
    w(out, f"  {'Mean':<20} {fmt_time(mean(attempt_times)):>10}")
    w(out, f"  {'P75':<20} {fmt_time(percentile(attempt_times, 75)):>10}")
    w(out, f"  {'P90':<20} {fmt_time(percentile(attempt_times, 90)):>10}")
    w(out, f"  {'P95':<20} {fmt_time(percentile(attempt_times, 95)):>10}")
    w(out, f"  {'Max':<20} {fmt_time(max(attempt_times)):>10}")

    # Histogram
    w(out)
    w(out, "  Attempt Duration Histogram:")
    buckets = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 45),
               (45, 60), (60, 90), (90, 120), (120, float('inf'))]
    labels = ["<5s", "5-10s", "10-20s", "20-30s", "30-45s", "45-60s", "60-90s", "90-120s", "120s+"]
    for (lo, hi), label in zip(buckets, labels):
        count = sum(1 for t in attempt_times if lo <= t < hi)
        bar = '#' * min(count, 80)
        suffix = f"... ({count})" if count > 80 else f" ({count})"
        w(out, f"  {label:>8} | {bar}{suffix}")

    # Per-attempt-number timing (are later attempts slower?)
    by_att_num = defaultdict(list)
    for p in problems:
        for a in p.attempts:
            if a.time_s > 0:
                by_att_num[a.attempt_num].append(a.time_s)

    w(out)
    w(out, "  Timing by Attempt Number:")
    w(out, f"  {'Att#':>5} {'Count':>6} {'Mean':>8} {'Median':>8} {'P90':>8}")
    w(out, f"  {'---':>5} {'---':>6} {'---':>8} {'---':>8} {'---':>8}")
    for att_num in sorted(by_att_num.keys()):
        times = by_att_num[att_num]
        w(out, f"  {att_num:>5} {len(times):>6} {fmt_time(mean(times)):>8} {fmt_time(median(times)):>8} {fmt_time(percentile(times, 90)):>8}")


# ── Analysis 3: Time by Outcome (None / Correct / Wrong) ────────────────────

def analyze_time_by_outcome(problems, out):
    print_section("3. TIME SPENT BY ATTEMPT OUTCOME (None / Correct / Wrong)", out)

    correct_times = []
    wrong_times = []
    none_times = []

    for p in problems:
        for a in p.attempts:
            if a.time_s <= 0:
                continue
            if a.is_none:
                none_times.append(a.time_s)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_times.append(a.time_s)
            elif a.answer is not None:
                wrong_times.append(a.time_s)

    total_time = sum(correct_times) + sum(wrong_times) + sum(none_times)
    w(out)
    w(out, f"  {'Outcome':<20} {'Count':>6} {'Mean':>8} {'Median':>8} {'P90':>8} {'Total':>10} {'% Time':>8}")
    w(out, f"  {'---':<20} {'---':>6} {'---':>8} {'---':>8} {'---':>8} {'---':>10} {'---':>8}")
    for label, times in [("Correct Answer", correct_times), ("Wrong Answer", wrong_times), ("None (no answer)", none_times)]:
        if times:
            pct = 100 * sum(times) / total_time if total_time else 0
            w(out, f"  {label:<20} {len(times):>6} {fmt_time(mean(times)):>8} {fmt_time(median(times)):>8} {fmt_time(percentile(times, 90)):>8} {fmt_time(sum(times)):>10} {pct:>7.1f}%")
    w(out, f"  {'---':<20} {'---':>6} {'':>8} {'':>8} {'':>8} {'---':>10} {'---':>8}")
    w(out, f"  {'TOTAL':<20} {len(correct_times)+len(wrong_times)+len(none_times):>6} {'':>8} {'':>8} {'':>8} {fmt_time(total_time):>10} {'100.0%':>8}")

    if correct_times and none_times:
        ratio = mean(none_times) / mean(correct_times)
        w(out)
        w(out, f"  None attempts average {fmt_time(mean(none_times))}, correct average {fmt_time(mean(correct_times))}.")
        w(out, f"  None/Correct time ratio: {ratio:.2f}x")

    # Time wasted on wrong problems (all attempts in wrong problem are wasted)
    wrong_probs = [p for p in problems if not p.correct]
    if wrong_probs:
        wasted_total = sum(p.wall_time for p in wrong_probs)
        w(out)
        w(out, f"  Time on WRONG problems ({len(wrong_probs)} problems): {fmt_time(wasted_total)}")
        w(out, f"  {'Problem':<10} {'Time':>8} {'Att':>4} {'None':>5} {'Predicted':>10} {'Expected':>10}")
        w(out, f"  {'---':<10} {'---':>8} {'---':>4} {'---':>5} {'---':>10} {'---':>10}")
        for p in sorted(wrong_probs, key=lambda x: -x.wall_time):
            nones = sum(1 for a in p.attempts if a.is_none)
            w(out, f"  {p.problem_id:<10} {fmt_time(p.wall_time):>8} {len(p.attempts):>4} {nones:>5} {p.predicted:>10} {p.expected:>10}")


# ── Analysis 4: Early Stop Analysis ─────────────────────────────────────────

def analyze_early_stop(problems, out):
    print_section("4. EARLY STOP ANALYSIS", out)

    es_yes = [p for p in problems if p.early_stop]
    es_no = [p for p in problems if not p.early_stop]

    w(out)
    w(out, f"  Early-stopped: {len(es_yes)}/{len(problems)} ({100*len(es_yes)/len(problems):.1f}%)")
    w(out, f"  Not early-stopped: {len(es_no)}/{len(problems)} ({100*len(es_no)/len(problems):.1f}%)")

    # Attempts per problem distribution
    att_counts_es = [len(p.attempts) for p in es_yes]
    att_counts_nes = [len(p.attempts) for p in es_no]

    w(out)
    w(out, "  Attempts per Problem (Early-Stopped vs Not):")
    w(out, f"  {'Category':<25} {'Count':>6} {'Mean':>6} {'Min':>4} {'Max':>4} {'Median':>6}")
    w(out, f"  {'---':<25} {'---':>6} {'---':>6} {'---':>4} {'---':>4} {'---':>6}")
    if att_counts_es:
        w(out, f"  {'Early-stopped':<25} {len(att_counts_es):>6} {mean(att_counts_es):>6.1f} {min(att_counts_es):>4} {max(att_counts_es):>4} {median(att_counts_es):>6.0f}")
    if att_counts_nes:
        w(out, f"  {'Not early-stopped':<25} {len(att_counts_nes):>6} {mean(att_counts_nes):>6.1f} {min(att_counts_nes):>4} {max(att_counts_nes):>4} {median(att_counts_nes):>6.0f}")

    # Distribution of attempt counts
    all_att_counts = [len(p.attempts) for p in problems]
    att_dist = Counter(all_att_counts)
    w(out)
    w(out, "  Distribution of Attempt Counts:")
    w(out, f"  {'#Attempts':>10} {'#Problems':>10} {'ES':>6} {'!ES':>6}")
    w(out, f"  {'---':>10} {'---':>10} {'---':>6} {'---':>6}")
    for n in sorted(att_dist.keys()):
        es_count = sum(1 for p in es_yes if len(p.attempts) == n)
        nes_count = sum(1 for p in es_no if len(p.attempts) == n)
        w(out, f"  {n:>10} {att_dist[n]:>10} {es_count:>6} {nes_count:>6}")

    # Time savings from early stop
    if es_yes:
        # Estimate: if they ran all 16 attempts, each would take roughly
        # avg_time_per_att * 16 (serial) or similar
        es_time = sum(p.wall_time for p in es_yes)
        nes_time = sum(p.wall_time for p in es_no) if es_no else 0
        w(out)
        w(out, f"  Time consumed by early-stopped problems: {fmt_time(es_time)}")
        w(out, f"  Time consumed by non-early-stopped problems: {fmt_time(nes_time)}")

        if es_no and att_counts_nes:
            avg_per_att_nes = mean([p.wall_time / len(p.attempts) for p in es_no if len(p.attempts) > 0])
            w(out, f"  Avg time per attempt (non-ES): {fmt_time(avg_per_att_nes)}")
            # Hypothetical: if ES problems ran full 16
            max_atts = max(att_counts_nes) if att_counts_nes else 16
            hypothetical = sum(avg_per_att_nes * max_atts for _ in es_yes)
            w(out, f"  Hypothetical if ES problems ran {max_atts}: {fmt_time(hypothetical)}")
            w(out, f"  Time saved by early stop: ~{fmt_time(hypothetical - es_time)}")

    # Correctness: ES vs non-ES
    es_correct = sum(1 for p in es_yes if p.correct)
    nes_correct = sum(1 for p in es_no if p.correct)
    w(out)
    w(out, "  Correctness:")
    w(out, f"  Early-stopped: {es_correct}/{len(es_yes)} correct ({100*es_correct/len(es_yes):.1f}%)" if es_yes else "")
    w(out, f"  Not early-stopped: {nes_correct}/{len(es_no)} correct ({100*nes_correct/len(es_no):.1f}%)" if es_no else "")

    # Simulate early stop thresholds
    w(out)
    w(out, "  Early Stop Threshold Simulation (# matching answers to trigger):")
    w(out, f"  {'Threshold':>10} {'ES Problems':>12} {'Score':>8} {'Time Saved':>12}")
    w(out, f"  {'---':>10} {'---':>12} {'---':>8} {'---':>12}")

    for threshold in [3, 4, 5, 6, 7]:
        es_count = 0
        score = 0
        total_time_sim = 0
        for p in problems:
            if p.expected is None:
                continue
            # Simulate: walk attempts, count matching answers, stop at threshold
            votes = defaultdict(int)
            stopped = False
            sim_attempts = []
            for a in sorted(p.attempts, key=lambda x: x.attempt_num):
                sim_attempts.append(a)
                if a.answer is not None:
                    votes[a.answer] += 1
                    if votes[a.answer] >= threshold:
                        stopped = True
                        es_count += 1
                        break
            # Score using votes from used attempts
            if votes:
                winner = max(votes, key=votes.get)
                if winner == p.expected:
                    score += 1
            # Time: use time of attempts we ran
            for a in sim_attempts:
                total_time_sim += a.time_s

        total_with_exp = sum(1 for p in problems if p.expected is not None)
        actual_total_time = sum(a.time_s for p in problems for a in p.attempts if a.time_s > 0)
        saved = actual_total_time - total_time_sim
        w(out, f"  {threshold:>10} {es_count:>12} {score:>5}/{total_with_exp} {fmt_time(saved):>12}")


# ── Analysis 5: Token Usage per Attempt ──────────────────────────────────────

def analyze_token_usage(problems, out):
    print_section("5. TOKEN USAGE PER ATTEMPT", out)

    correct_tokens = []
    wrong_tokens = []
    none_tokens = []

    for p in problems:
        for a in p.attempts:
            if a.tokens <= 0:
                continue
            if a.is_none:
                none_tokens.append((a.tokens, a.time_s))
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_tokens.append((a.tokens, a.time_s))
            elif a.answer is not None:
                wrong_tokens.append((a.tokens, a.time_s))

    all_tokens = [t for t, _ in correct_tokens + wrong_tokens + none_tokens]

    w(out)
    w(out, f"  Overall Token Stats ({len(all_tokens)} attempts):")
    w(out, f"  {'Metric':<20} {'Value':>10}")
    w(out, f"  {'---':<20} {'---':>10}")
    if all_tokens:
        w(out, f"  {'Min':<20} {fmt_tokens(min(all_tokens)):>10}")
        w(out, f"  {'P25':<20} {fmt_tokens(percentile(all_tokens, 25)):>10}")
        w(out, f"  {'Median':<20} {fmt_tokens(median(all_tokens)):>10}")
        w(out, f"  {'Mean':<20} {fmt_tokens(mean(all_tokens)):>10}")
        w(out, f"  {'P75':<20} {fmt_tokens(percentile(all_tokens, 75)):>10}")
        w(out, f"  {'P90':<20} {fmt_tokens(percentile(all_tokens, 90)):>10}")
        w(out, f"  {'Max':<20} {fmt_tokens(max(all_tokens)):>10}")
        w(out, f"  {'Total':<20} {fmt_tokens(sum(all_tokens)):>10}")

    # By outcome
    w(out)
    w(out, "  Tokens by Outcome:")
    w(out, f"  {'Outcome':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'P90':>10} {'Total':>12} {'%':>6}")
    w(out, f"  {'---':<20} {'---':>6} {'---':>10} {'---':>10} {'---':>10} {'---':>12} {'---':>6}")
    grand = sum(all_tokens) if all_tokens else 1
    for label, data in [("Correct", correct_tokens), ("Wrong", wrong_tokens), ("None", none_tokens)]:
        if data:
            toks = [t for t, _ in data]
            pct = 100 * sum(toks) / grand
            w(out, f"  {label:<20} {len(toks):>6} {fmt_tokens(mean(toks)):>10} {fmt_tokens(median(toks)):>10} {fmt_tokens(percentile(toks, 90)):>10} {fmt_tokens(sum(toks)):>12} {pct:>5.1f}%")

    # Token/time correlation (tokens per second)
    w(out)
    w(out, "  Token Throughput (tokens/second) by Outcome:")
    for label, data in [("Correct", correct_tokens), ("Wrong", wrong_tokens), ("None", none_tokens)]:
        rates = [t / s for t, s in data if s > 0]
        if rates:
            w(out, f"  {label}: mean={fmt_tokens(mean(rates))}/s, median={fmt_tokens(median(rates))}/s")

    # Correlation: more tokens = more likely correct?
    w(out)
    w(out, "  Success Rate by Token Bucket:")
    all_with_outcome = []
    for p in problems:
        if p.expected is None:
            continue
        for a in p.attempts:
            if a.tokens > 0 and a.answer is not None:
                is_correct = a.answer == p.expected
                all_with_outcome.append((a.tokens, is_correct))

    if all_with_outcome:
        bins = [(0, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000),
                (8000, 16000), (16000, float('inf'))]
        labels = ["<500", "500-1K", "1-2K", "2-4K", "4-8K", "8-16K", "16K+"]
        w(out, f"  {'Bucket':<10} {'Total':>6} {'Correct':>8} {'Rate':>8}")
        w(out, f"  {'---':<10} {'---':>6} {'---':>8} {'---':>8}")
        for (lo, hi), label in zip(bins, labels):
            bucket = [(t, c) for t, c in all_with_outcome if lo <= t < hi]
            if bucket:
                total = len(bucket)
                correct = sum(1 for _, c in bucket if c)
                rate = 100 * correct / total
                w(out, f"  {label:<10} {total:>6} {correct:>8} {rate:>7.1f}%")


# ── Analysis 6: Parallelism Analysis ────────────────────────────────────────

def analyze_parallelism(problems, out):
    print_section("6. PARALLELISM ANALYSIS (16 workers, 16 attempts/problem)", out)

    total_wall = sum(p.wall_time for p in problems if p.wall_time > 0)
    total_attempt_time = sum(a.time_s for p in problems for a in p.attempts if a.time_s > 0)
    total_attempts = sum(len(p.attempts) for p in problems)

    w(out)
    w(out, f"  Configuration: 16 workers, problems processed in parallel batches")
    w(out, f"  Total wall time (from run): 313.5 min (from user context)")
    w(out, f"  Sum of problem wall times: {fmt_time(total_wall)}")
    w(out, f"  Sum of all attempt times: {fmt_time(total_attempt_time)}")
    w(out, f"  Total attempts: {total_attempts}")

    # The v23 solver runs 16 attempts per problem in PARALLEL (16 workers).
    # So for a single problem, all 16 attempts run simultaneously — the problem
    # wall time is roughly the MAX of its attempt times, not the SUM.
    w(out)
    w(out, "  Per-Problem: Wall Time vs Sum of Attempt Times")
    w(out, "  (If attempts run in parallel, wall_time ~ max(attempt_times))")
    w(out)

    ratios = []
    for p in problems:
        att_times = [a.time_s for a in p.attempts if a.time_s > 0]
        if att_times and p.wall_time > 0:
            sum_att = sum(att_times)
            max_att = max(att_times)
            ratio_sum = p.wall_time / sum_att if sum_att > 0 else 0
            ratio_max = p.wall_time / max_att if max_att > 0 else 0
            ratios.append((p.problem_id, p.wall_time, sum_att, max_att, ratio_sum, ratio_max, len(att_times)))

    if ratios:
        w(out, f"  {'Problem':<10} {'Wall':>8} {'Sum(att)':>10} {'Max(att)':>10} {'Wall/Sum':>9} {'Wall/Max':>9} {'#Att':>5}")
        w(out, f"  {'---':<10} {'---':>8} {'---':>10} {'---':>10} {'---':>9} {'---':>9} {'---':>5}")
        # Show a sample + outliers
        sorted_by_ratio = sorted(ratios, key=lambda x: -x[5])
        shown = set()
        # Top 5 by wall/max ratio
        for pid, wt, sa, ma, rs, rm, na in sorted_by_ratio[:5]:
            w(out, f"  {pid:<10} {fmt_time(wt):>8} {fmt_time(sa):>10} {fmt_time(ma):>10} {rs:>9.2f} {rm:>9.2f} {na:>5}")
            shown.add(pid)
        w(out, "  ...")
        # Bottom 5
        for pid, wt, sa, ma, rs, rm, na in sorted_by_ratio[-5:]:
            if pid not in shown:
                w(out, f"  {pid:<10} {fmt_time(wt):>8} {fmt_time(sa):>10} {fmt_time(ma):>10} {rs:>9.2f} {rm:>9.2f} {na:>5}")

        wall_max_ratios = [rm for _, _, _, _, _, rm, _ in ratios]
        w(out)
        w(out, f"  Wall/Max(attempt) ratio stats:")
        w(out, f"    Mean:   {mean(wall_max_ratios):.2f}")
        w(out, f"    Median: {median(wall_max_ratios):.2f}")
        w(out, f"    Min:    {min(wall_max_ratios):.2f}")
        w(out, f"    Max:    {max(wall_max_ratios):.2f}")
        w(out)
        if mean(wall_max_ratios) > 1.5:
            w(out, "  >> Wall time is significantly > max attempt time.")
            w(out, "     This suggests overhead (scheduling, batching, sequential processing).")
        elif mean(wall_max_ratios) < 1.2:
            w(out, "  >> Wall time closely tracks max attempt time.")
            w(out, "     Attempts are running in parallel effectively.")
        else:
            w(out, "  >> Moderate overhead between wall time and max attempt time.")

    # Effective parallelism
    w(out)
    if total_wall > 0:
        effective_parallelism = total_attempt_time / total_wall
        w(out, f"  Effective parallelism: {effective_parallelism:.1f}x")
        w(out, f"  (Sum of attempt times / Sum of wall times)")
        w(out, f"  Theoretical max with 16 workers: 16.0x")
        w(out, f"  Utilization: {100*effective_parallelism/16:.1f}%")

    # GPU idle time estimate
    # The run is 313.5 min. If we had perfect 16x parallelism,
    # we could process 313.5 * 16 = 5016 min of compute in 313.5 min.
    # Actual compute = total_attempt_time
    run_wall_min = 313.5
    total_gpu_budget_min = run_wall_min * 16  # If GPU was 100% busy with 16 workers
    total_compute_min = total_attempt_time / 60
    w(out)
    w(out, f"  GPU Utilization Estimate (based on 313.5 min run, 16 workers):")
    w(out, f"    Total GPU-minutes available: {total_gpu_budget_min:.0f} min")
    w(out, f"    Total GPU-minutes used:      {total_compute_min:.0f} min")
    w(out, f"    GPU utilization:             {100*total_compute_min/total_gpu_budget_min:.1f}%")
    w(out, f"    Idle GPU-minutes:            {total_gpu_budget_min - total_compute_min:.0f} min")

    # Inter-problem gaps
    # Problems are processed sequentially but within each, 16 attempts run in parallel.
    # With 97 problem-entries and 313.5 min, avg gap between problems:
    avg_wall = total_wall / len(problems) if problems else 0
    w(out)
    w(out, f"  Sequential processing estimate:")
    w(out, f"    {len(problems)} problem-entries processed")
    w(out, f"    Average wall time per problem: {fmt_time(avg_wall)}")
    w(out, f"    Sum of wall times: {fmt_time(total_wall)}")
    overhead = run_wall_min * 60 - total_wall
    w(out, f"    Run overhead (run time - sum wall): {fmt_time(overhead)}")
    w(out, f"    Overhead as % of run: {100*overhead/(run_wall_min*60):.1f}%")


# ── Analysis 7: Time Budget Analysis ────────────────────────────────────────

def analyze_time_budget(problems, out):
    print_section("7. TIME BUDGET ANALYSIS", out)

    total_wall = sum(p.wall_time for p in problems if p.wall_time > 0)
    run_wall_s = 313.5 * 60  # 313.5 minutes
    target_s = 300 * 60  # 300 minute target

    n_problems = len(problems)
    n_unique = len(set(p.problem_id for p in problems))

    w(out)
    w(out, f"  Run Statistics:")
    w(out, f"    Problem-entries (with retries): {n_problems}")
    w(out, f"    Unique problems:                {n_unique}")
    w(out, f"    Total run time:                 {fmt_time(run_wall_s)} (313.5 min)")
    w(out, f"    Target budget:                  {fmt_time(target_s)} (300 min)")
    w(out, f"    OVER BUDGET BY:                 {fmt_time(run_wall_s - target_s)} ({(run_wall_s - target_s)/60:.1f} min)")
    w(out)
    w(out, f"  Per-Problem Averages:")
    w(out, f"    Per problem-entry:    {fmt_time(total_wall / n_problems)}")
    w(out, f"    Per unique problem:   {fmt_time(total_wall / n_unique)}")
    w(out, f"    Budget per problem (at 300 min target, 80 problems): {fmt_time(target_s / 80)}")
    w(out, f"    Budget per problem (at 300 min target, 110 problems): {fmt_time(target_s / 110)}")

    # Budget utilization per problem
    if any(p.budget > 0 for p in problems):
        w(out)
        w(out, "  Budget Utilization (problems with budget data):")
        budgeted = [(p.problem_id, p.budget, p.wall_time, p.correct) for p in problems if p.budget > 0]
        utils = [wt / b for _, b, wt, _ in budgeted if b > 0]
        w(out, f"    Mean utilization: {100*mean(utils):.1f}%")
        w(out, f"    Median utilization: {100*median(utils):.1f}%")
        overbudget = sum(1 for _, b, wt, _ in budgeted if wt > b)
        w(out, f"    Over-budget problems: {overbudget}/{len(budgeted)}")

    # What's eating the budget?
    w(out)
    w(out, "  Budget Breakdown:")

    # Group by correctness
    correct_time = sum(p.wall_time for p in problems if p.correct)
    wrong_time = sum(p.wall_time for p in problems if not p.correct)
    w(out, f"    Correct problems: {fmt_time(correct_time)} ({100*correct_time/total_wall:.1f}%)")
    w(out, f"    Wrong problems:   {fmt_time(wrong_time)} ({100*wrong_time/total_wall:.1f}%)")

    # Group by ES vs non-ES
    es_time = sum(p.wall_time for p in problems if p.early_stop)
    nes_time = sum(p.wall_time for p in problems if not p.early_stop)
    w(out, f"    Early-stopped:    {fmt_time(es_time)} ({100*es_time/total_wall:.1f}%)")
    w(out, f"    Full-run:         {fmt_time(nes_time)} ({100*nes_time/total_wall:.1f}%)")

    # Time to bring under 300 min
    w(out)
    w(out, "  Savings Needed to Hit 300 min:")
    savings_needed = run_wall_s - target_s
    w(out, f"    Must save: {fmt_time(savings_needed)} ({savings_needed/60:.1f} min)")
    w(out, f"    That's {100*savings_needed/run_wall_s:.1f}% of current run time")
    w(out)

    # Specific strategies to save time
    none_time = sum(a.time_s for p in problems for a in p.attempts if a.is_none)
    w(out, "  Potential Savings Levers:")
    w(out, f"    a) Eliminate all None attempts: save {fmt_time(none_time)} compute")
    w(out, f"    b) Drop wrong problems (if detectable): save {fmt_time(wrong_time)}")
    es_problems = [p for p in problems if p.early_stop]
    if es_problems:
        avg_es_atts = mean([len(p.attempts) for p in es_problems])
        w(out, f"    c) ES problems avg {avg_es_atts:.0f} attempts — already saving time")

    # Scale analysis: 80 -> 110 problems
    w(out)
    w(out, "  Scale Projection (80 -> 110 problems):")
    per_problem = total_wall / n_problems
    projected_110 = per_problem * 110
    w(out, f"    At current per-problem avg ({fmt_time(per_problem)}): {fmt_time(projected_110)} ({projected_110/60:.0f} min)")
    w(out, f"    vs 300 min target: {'OVER' if projected_110 > target_s else 'UNDER'} by {fmt_time(abs(projected_110 - target_s))}")


# ── Analysis 8: Reduced Attempt Simulation ──────────────────────────────────

def analyze_reduced_attempts(problems, out):
    print_section("8. REDUCED-ATTEMPT SIMULATION (12 vs 16 attempts)", out)

    total_with_exp = sum(1 for p in problems if p.expected is not None)

    w(out)
    w(out, "  Simulating different max-attempt counts:")
    w(out, "  (Uses first N attempts by attempt_num, applies majority voting)")
    w(out)
    w(out, f"  {'Max Att':>8} {'Score':>10} {'Compute':>12} {'Savings':>12} {'% Saved':>8} {'ES@4':>8} {'ES@5':>8}")
    w(out, f"  {'---':>8} {'---':>10} {'---':>12} {'---':>12} {'---':>8} {'---':>8} {'---':>8}")

    actual_compute = sum(a.time_s for p in problems for a in p.attempts if a.time_s > 0)

    for max_n in [6, 8, 10, 12, 14, 16]:
        score = 0
        compute = 0
        es4_count = 0
        es5_count = 0
        for p in problems:
            if p.expected is None:
                continue
            sorted_atts = sorted(p.attempts, key=lambda x: x.attempt_num)
            votes = defaultdict(int)
            es4_triggered = False
            es5_triggered = False
            for a in sorted_atts[:max_n]:
                compute += a.time_s
                if a.answer is not None:
                    votes[a.answer] += 1
                    if votes[a.answer] >= 4 and not es4_triggered:
                        es4_triggered = True
                    if votes[a.answer] >= 5 and not es5_triggered:
                        es5_triggered = True
            if es4_triggered:
                es4_count += 1
            if es5_triggered:
                es5_count += 1
            if votes:
                winner = max(votes, key=votes.get)
                if winner == p.expected:
                    score += 1

        savings = actual_compute - compute
        pct_saved = 100 * savings / actual_compute if actual_compute > 0 else 0
        w(out, f"  {max_n:>8} {score:>5}/{total_with_exp} {fmt_time(compute):>12} {fmt_time(savings):>12} {pct_saved:>7.1f}% {es4_count:>8} {es5_count:>8}")

    # Deep analysis: which problems lose score going from 16 -> 12?
    w(out)
    w(out, "  Problems that Change Score (16 -> 12 attempts):")
    changes = []
    for p in problems:
        if p.expected is None:
            continue
        sorted_atts = sorted(p.attempts, key=lambda x: x.attempt_num)

        # Score at 16
        votes_16 = defaultdict(int)
        for a in sorted_atts[:16]:
            if a.answer is not None:
                votes_16[a.answer] += 1
        winner_16 = max(votes_16, key=votes_16.get) if votes_16 else None
        correct_16 = winner_16 == p.expected if winner_16 is not None else False

        # Score at 12
        votes_12 = defaultdict(int)
        for a in sorted_atts[:12]:
            if a.answer is not None:
                votes_12[a.answer] += 1
        winner_12 = max(votes_12, key=votes_12.get) if votes_12 else None
        correct_12 = winner_12 == p.expected if winner_12 is not None else False

        if correct_16 != correct_12:
            changes.append((p.problem_id, correct_16, correct_12, dict(votes_16), dict(votes_12)))

    if changes:
        w(out, f"  {'Problem':<10} {'@16':>5} {'@12':>5} {'Votes@16':<30} {'Votes@12':<30}")
        w(out, f"  {'---':<10} {'---':>5} {'---':>5} {'---':<30} {'---':<30}")
        for pid, c16, c12, v16, v12 in changes:
            s16 = "OK" if c16 else "WRONG"
            s12 = "OK" if c12 else "WRONG"
            w(out, f"  {pid:<10} {s16:>5} {s12:>5} {str(v16):<30} {str(v12):<30}")
    else:
        w(out, "  No score changes between 16 and 12 attempts!")

    # Estimate time savings for 12 attempts
    w(out)
    w(out, "  Time Savings Estimate (12 vs 16 attempts):")
    time_12 = 0
    time_16 = 0
    for p in problems:
        sorted_atts = sorted(p.attempts, key=lambda x: x.attempt_num)
        for a in sorted_atts[:12]:
            time_12 += a.time_s
        for a in sorted_atts[:16]:
            time_16 += a.time_s

    w(out, f"    Compute at 16: {fmt_time(time_16)}")
    w(out, f"    Compute at 12: {fmt_time(time_12)}")
    w(out, f"    Savings:       {fmt_time(time_16 - time_12)} ({100*(time_16-time_12)/time_16:.1f}%)")

    # But need to estimate wall time savings (parallel)
    # Each problem runs attempts in parallel, so wall time ~ max(attempt_times[:N])
    wall_16 = 0
    wall_12 = 0
    for p in problems:
        sorted_atts = sorted(p.attempts, key=lambda x: x.attempt_num)
        times_16 = [a.time_s for a in sorted_atts[:16] if a.time_s > 0]
        times_12 = [a.time_s for a in sorted_atts[:12] if a.time_s > 0]
        wall_16 += max(times_16) if times_16 else 0
        wall_12 += max(times_12) if times_12 else 0

    w(out)
    w(out, f"  Wall Time Savings (max-of-parallel, per-problem sum):")
    w(out, f"    Wall at 16 (estimated): {fmt_time(wall_16)}")
    w(out, f"    Wall at 12 (estimated): {fmt_time(wall_12)}")
    w(out, f"    Wall savings:           {fmt_time(wall_16 - wall_12)}")
    w(out, f"    Note: Actual wall time also depends on batch scheduling overhead")


# ── Summary & Recommendations ───────────────────────────────────────────────

def print_summary(problems, out):
    print_section("SUMMARY & RECOMMENDATIONS", out)

    total_wall = sum(p.wall_time for p in problems if p.wall_time > 0)
    total_attempt_time = sum(a.time_s for p in problems for a in p.attempts if a.time_s > 0)
    total_attempts = sum(len(p.attempts) for p in problems)
    none_time = sum(a.time_s for p in problems for a in p.attempts if a.is_none and a.time_s > 0)
    none_count = sum(1 for p in problems for a in p.attempts if a.is_none)
    wrong_time = sum(p.wall_time for p in problems if not p.correct)
    wrong_count = sum(1 for p in problems if not p.correct)
    correct_count = sum(1 for p in problems if p.correct)
    es_count = sum(1 for p in problems if p.early_stop)

    run_min = 313.5
    target_min = 300

    w(out)
    w(out, "  KEY FINDINGS:")
    w(out)
    w(out, f"  1. OVER BUDGET: Run took {run_min} min vs {target_min} min target ({run_min - target_min:.1f} min over).")
    w(out, f"     Must save {run_min - target_min:.1f} min ({100*(run_min - target_min)/run_min:.1f}%) to fit.")
    w(out)
    w(out, f"  2. NONE WASTE: {none_count}/{total_attempts} attempts ({100*none_count/total_attempts:.0f}%) returned None,")
    w(out, f"     consuming {fmt_time(none_time)} of compute. Eliminating would reclaim significant budget.")
    w(out)
    w(out, f"  3. WRONG PROBLEMS: {wrong_count} problems answered wrong, consuming {fmt_time(wrong_time)}.")
    w(out, f"     These can't easily be detected early, but dominate the tail.")
    w(out)
    w(out, f"  4. EARLY STOP: {es_count}/{len(problems)} problems ({100*es_count/len(problems):.0f}%) early-stopped.")
    w(out, f"     ES is already working well for easy problems.")
    w(out)

    w(out, "  RECOMMENDATIONS:")
    w(out)
    w(out, "  a) REDUCE TO 12 ATTEMPTS: Likely same score, saves ~25% compute.")
    w(out, "     Combined with ES=4 (already planned), this should bring under 300 min.")
    w(out)
    w(out, "  b) TIGHTER EARLY STOP (ES=4): Already implemented. Saves time without")
    w(out, "     losing score based on v23 data.")
    w(out)
    w(out, "  c) REDUCE NONE RATE: Each None attempt wastes compute. Better extraction")
    w(out, "     and error recovery are the biggest single optimization lever.")
    w(out)
    w(out, "  d) ADAPTIVE ATTEMPTS: Easy problems (ES within 6 attempts) don't need 16.")
    w(out, "     Hard problems (no convergence) might benefit from MORE attempts.")
    w(out, "     Consider: 8 attempts for easy batch, 16 for hard batch.")
    w(out)
    w(out, "  e) SCALE WARNING: At 110 problems (competition), current approach needs")
    per_prob = total_wall / len(problems)
    projected = per_prob * 110 / 60
    w(out, f"     ~{projected:.0f} min. Must get per-problem avg under {target_min * 60 / 110:.0f}s for 110.")
    w(out)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="GPU Timing & Utilization Analysis")
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("--save", help="Save output to markdown file", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems, {sum(len(p.attempts) for p in problems)} attempts.")

    # Use a StringIO to capture output for both display and saving
    buf = io.StringIO()

    buf.write(f"# GPU Timing & Utilization Analysis — v23\n")
    buf.write(f"# Log: {args.logfile}\n")
    buf.write(f"# Problems: {len(problems)}, Attempts: {sum(len(p.attempts) for p in problems)}\n")
    buf.write(f"# Run time: 313.5 min, Target: 300 min\n")

    analyze_per_problem_timing(problems, buf)
    analyze_per_attempt_timing(problems, buf)
    analyze_time_by_outcome(problems, buf)
    analyze_early_stop(problems, buf)
    analyze_token_usage(problems, buf)
    analyze_parallelism(problems, buf)
    analyze_time_budget(problems, buf)
    analyze_reduced_attempts(problems, buf)
    print_summary(problems, buf)

    output = buf.getvalue()
    print(output)

    if args.save:
        save_dir = os.path.dirname(args.save)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        with open(args.save, 'w') as f:
            f.write("```\n")
            f.write(output)
            f.write("```\n")
        print(f"\nSaved to {args.save}")


if __name__ == "__main__":
    main()
