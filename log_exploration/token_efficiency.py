#!/usr/bin/env python3
"""
Token Efficiency Analysis for AIMO3 Solver
============================================
Analyzes tokens per correct/wrong/None, code-to-reasoning ratio,
reasoning length vs correctness, token waste, and per-turn breakdown.

Usage: python3 log_exploration/token_efficiency.py output/v22/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def percentile(vals, p):
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f])


def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def analyze_tokens_by_outcome(problems):
    """Tokens per correct answer vs wrong vs None."""
    print_section("TOKENS BY OUTCOME")

    correct_tokens = []
    wrong_tokens = []
    none_tokens = []

    for p in problems:
        for a in p.attempts:
            if a.tokens <= 0:
                continue
            if a.is_none:
                none_tokens.append(a.tokens)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_tokens.append(a.tokens)
            elif a.answer is not None:
                wrong_tokens.append(a.tokens)

    print(f"\n  Per-Attempt Tokens:")
    print(f"  {'Outcome':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'P90':>10} {'Total':>12} {'% of All':>8}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 12} {'─' * 8}")

    grand_total = sum(correct_tokens) + sum(wrong_tokens) + sum(none_tokens)
    for label, tokens in [("Correct", correct_tokens), ("Wrong", wrong_tokens), ("None", none_tokens)]:
        if tokens:
            pct = 100 * sum(tokens) / grand_total if grand_total > 0 else 0
            print(f"  {label:<20} {len(tokens):>6} {fmt_tokens(mean(tokens)):>10} {fmt_tokens(median(tokens)):>10} {fmt_tokens(percentile(tokens, 90)):>10} {fmt_tokens(sum(tokens)):>12} {pct:>7.1f}%")

    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 12} {'─' * 8}")
    print(f"  {'TOTAL':<20} {len(correct_tokens)+len(wrong_tokens)+len(none_tokens):>6} {'':>10} {'':>10} {'':>10} {fmt_tokens(grand_total):>12} {'100.0%':>8}")

    # Problem-level tokens
    print(f"\n  Per-Problem Total Tokens:")
    correct_prob_tokens = [p.total_tokens for p in problems if p.correct and p.total_tokens > 0]
    wrong_prob_tokens = [p.total_tokens for p in problems if not p.correct and p.total_tokens > 0]

    print(f"  {'Category':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'Total':>12}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 12}")
    if correct_prob_tokens:
        print(f"  {'Correct problems':<20} {len(correct_prob_tokens):>6} {fmt_tokens(mean(correct_prob_tokens)):>10} {fmt_tokens(median(correct_prob_tokens)):>10} {fmt_tokens(sum(correct_prob_tokens)):>12}")
    if wrong_prob_tokens:
        print(f"  {'Wrong problems':<20} {len(wrong_prob_tokens):>6} {fmt_tokens(mean(wrong_prob_tokens)):>10} {fmt_tokens(median(wrong_prob_tokens)):>10} {fmt_tokens(sum(wrong_prob_tokens)):>12}")

    # Token cost per correct answer (efficiency)
    if correct_tokens:
        token_per_correct = grand_total / len(correct_tokens)
        print(f"\n  Token Cost per Correct Answer: {fmt_tokens(token_per_correct)}")
        print(f"  (Total tokens / number of correct attempts)")


def analyze_code_reasoning_ratio(problems):
    """Code-to-reasoning ratio and its correlation with correctness."""
    print_section("CODE vs REASONING ANALYSIS")

    # Collect code chars and reasoning chars per attempt
    correct_data = []  # (reasoning_chars, code_chars)
    wrong_data = []
    none_data = []

    for p in problems:
        for a in p.attempts:
            reasoning_chars = sum(len(t.reasoning_text) for t in a.turns)
            code_chars = sum(len(t.code) for t in a.turns)
            entry = (reasoning_chars, code_chars, a.code_calls)

            if a.is_none:
                none_data.append(entry)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_data.append(entry)
            elif a.answer is not None:
                wrong_data.append(entry)

    print(f"\n  {'Category':<20} {'Count':>6} {'Reasoning':>12} {'Code':>12} {'Code Calls':>12} {'Code/Reason':>12}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 12} {'─' * 12} {'─' * 12} {'─' * 12}")

    for label, data in [("Correct", correct_data), ("Wrong", wrong_data), ("None", none_data)]:
        if data:
            avg_reason = mean([d[0] for d in data])
            avg_code = mean([d[1] for d in data])
            avg_calls = mean([d[2] for d in data])
            ratio = avg_code / avg_reason if avg_reason > 0 else float('inf')
            print(f"  {label:<20} {len(data):>6} {avg_reason:>12.0f} {avg_code:>12.0f} {avg_calls:>12.1f} {ratio:>12.2f}")

    # Code calls distribution
    print(f"\n  Code Calls per Attempt by Outcome:")
    for label, data in [("Correct", correct_data), ("Wrong", wrong_data), ("None", none_data)]:
        if data:
            calls = [d[2] for d in data]
            print(f"  {label}: min={min(calls)}, max={max(calls)}, mean={mean(calls):.1f}, median={median(calls):.0f}")


def analyze_reasoning_length(problems):
    """Reasoning length analysis: is longer reasoning better?"""
    print_section("REASONING LENGTH vs CORRECTNESS")

    # Reasoning chars per attempt
    correct_lens = []
    wrong_lens = []
    none_lens = []

    for p in problems:
        for a in p.attempts:
            total_reason = sum(len(t.reasoning_text) for t in a.turns)
            if a.is_none:
                none_lens.append(total_reason)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_lens.append(total_reason)
            elif a.answer is not None:
                wrong_lens.append(total_reason)

    print(f"\n  Total Reasoning Characters per Attempt:")
    print(f"  {'Category':<20} {'Count':>6} {'Mean':>10} {'Median':>10} {'P25':>10} {'P75':>10} {'P90':>10}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")
    for label, lens in [("Correct", correct_lens), ("Wrong", wrong_lens), ("None", none_lens)]:
        if lens:
            print(f"  {label:<20} {len(lens):>6} {mean(lens):>10.0f} {median(lens):>10.0f} {percentile(lens, 25):>10.0f} {percentile(lens, 75):>10.0f} {percentile(lens, 90):>10.0f}")

    # Turn count vs correctness
    correct_turns = []
    wrong_turns = []
    none_turns = []
    for p in problems:
        for a in p.attempts:
            tc = len(a.turns) if a.turns else 0
            if a.is_none:
                none_turns.append(tc)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_turns.append(tc)
            elif a.answer is not None:
                wrong_turns.append(tc)

    if correct_turns or wrong_turns:
        print(f"\n  Turn Count per Attempt:")
        print(f"  {'Category':<20} {'Count':>6} {'Mean':>8} {'Median':>8} {'Max':>6}")
        print(f"  {'─' * 20} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 6}")
        for label, turns in [("Correct", correct_turns), ("Wrong", wrong_turns), ("None", none_turns)]:
            if turns:
                print(f"  {label:<20} {len(turns):>6} {mean(turns):>8.1f} {median(turns):>8.0f} {max(turns):>6}")

    # Bin reasoning length and check accuracy per bin
    all_attempts = []
    for p in problems:
        if p.expected is None:
            continue
        for a in p.attempts:
            if a.answer is not None:
                total_reason = sum(len(t.reasoning_text) for t in a.turns)
                is_correct = a.answer == p.expected
                all_attempts.append((total_reason, is_correct))

    if all_attempts:
        print(f"\n  Accuracy by Reasoning Length Bucket:")
        bins = [(0, 1000), (1000, 3000), (3000, 5000), (5000, 10000), (10000, 20000), (20000, float('inf'))]
        labels = ["<1K", "1-3K", "3-5K", "5-10K", "10-20K", "20K+"]
        print(f"  {'Bucket':<10} {'Total':>6} {'Correct':>8} {'Accuracy':>10}")
        print(f"  {'─' * 10} {'─' * 6} {'─' * 8} {'─' * 10}")
        for (lo, hi), label in zip(bins, labels):
            bucket = [(r, c) for r, c in all_attempts if lo <= r < hi]
            if bucket:
                total = len(bucket)
                correct = sum(1 for _, c in bucket if c)
                acc = 100 * correct / total
                bar = '#' * int(acc / 5)
                print(f"  {label:<10} {total:>6} {correct:>8} {acc:>9.1f}% {bar}")


def analyze_token_waste(problems):
    """Token waste: tokens spent on None attempts and wrong problems."""
    print_section("TOKEN WASTE")

    total_tokens = sum(p.total_tokens for p in problems)
    none_tokens = sum(a.tokens for p in problems for a in p.attempts if a.is_none)
    wrong_prob_tokens = sum(p.total_tokens for p in problems if not p.correct)

    print(f"\n  Token Waste Summary:")
    print(f"  {'Category':<30} {'Tokens':>12} {'% of Total':>10}")
    print(f"  {'─' * 30} {'─' * 12} {'─' * 10}")
    print(f"  {'Total tokens':<30} {fmt_tokens(total_tokens):>12} {'100.0%':>10}")
    print(f"  {'Tokens on None attempts':<30} {fmt_tokens(none_tokens):>12} {100*none_tokens/total_tokens if total_tokens else 0:>9.1f}%")
    print(f"  {'Tokens on wrong problems':<30} {fmt_tokens(wrong_prob_tokens):>12} {100*wrong_prob_tokens/total_tokens if total_tokens else 0:>9.1f}%")
    productive = total_tokens - none_tokens - wrong_prob_tokens
    # Technically wrong_prob_tokens includes None attempts within wrong problems, handle overlap
    none_in_correct = sum(a.tokens for p in problems if p.correct for a in p.attempts if a.is_none)
    none_in_wrong = sum(a.tokens for p in problems if not p.correct for a in p.attempts if a.is_none)
    wrong_answers_in_correct = sum(a.tokens for p in problems if p.correct for a in p.attempts if not a.is_none and a.answer is not None and a.answer != p.expected)

    print(f"\n  Detailed Breakdown:")
    print(f"  {'Category':<35} {'Tokens':>12} {'% of Total':>10}")
    print(f"  {'─' * 35} {'─' * 12} {'─' * 10}")

    correct_in_correct = sum(a.tokens for p in problems if p.correct for a in p.attempts if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected)
    print(f"  {'Correct ans in correct problems':<35} {fmt_tokens(correct_in_correct):>12} {100*correct_in_correct/total_tokens if total_tokens else 0:>9.1f}%")
    print(f"  {'Wrong ans in correct problems':<35} {fmt_tokens(wrong_answers_in_correct):>12} {100*wrong_answers_in_correct/total_tokens if total_tokens else 0:>9.1f}%")
    print(f"  {'None in correct problems':<35} {fmt_tokens(none_in_correct):>12} {100*none_in_correct/total_tokens if total_tokens else 0:>9.1f}%")
    print(f"  {'All tokens in wrong problems':<35} {fmt_tokens(wrong_prob_tokens):>12} {100*wrong_prob_tokens/total_tokens if total_tokens else 0:>9.1f}%")

    # Per-problem token ranking
    print(f"\n  Top 10 Most Token-Hungry Problems:")
    print(f"  {'Problem':<10} {'Tokens':>10} {'OK':>4} {'Att':>4} {'None':>5} {'Time':>8}")
    print(f"  {'─' * 10} {'─' * 10} {'─' * 4} {'─' * 4} {'─' * 5} {'─' * 8}")
    for p in sorted(problems, key=lambda p: -p.total_tokens)[:10]:
        nones = sum(1 for a in p.attempts if a.is_none)
        ok = "Y" if p.correct else "N"
        print(f"  {p.problem_id:<10} {fmt_tokens(p.total_tokens):>10} {ok:>4} {len(p.attempts):>4} {nones:>5} {p.wall_time:>7.0f}s")


def analyze_per_turn_breakdown(problems):
    """Per-turn token/reasoning breakdown."""
    print_section("PER-TURN BREAKDOWN")

    # Aggregate stats by turn number
    turn_stats = defaultdict(lambda: {"count": 0, "reasoning_chars": 0, "code_chars": 0, "errors": 0, "has_code": 0})

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                ts = turn_stats[t.turn_num]
                ts["count"] += 1
                ts["reasoning_chars"] += len(t.reasoning_text)
                ts["code_chars"] += len(t.code)
                ts["errors"] += 1 if t.is_error else 0
                ts["has_code"] += 1 if t.code.strip() else 0

    if not turn_stats:
        print("  No turn data available.")
        return

    print(f"\n  Aggregated Stats by Turn Number:")
    print(f"  {'Turn':>6} {'Count':>6} {'Avg Reason':>12} {'Avg Code':>12} {'Has Code%':>10} {'Error%':>8}")
    print(f"  {'─' * 6} {'─' * 6} {'─' * 12} {'─' * 12} {'─' * 10} {'─' * 8}")

    for turn_num in sorted(turn_stats.keys()):
        ts = turn_stats[turn_num]
        count = ts["count"]
        avg_reason = ts["reasoning_chars"] / count
        avg_code = ts["code_chars"] / count
        has_code_pct = 100 * ts["has_code"] / count
        error_pct = 100 * ts["errors"] / count
        print(f"  {turn_num:>6} {count:>6} {avg_reason:>12.0f} {avg_code:>12.0f} {has_code_pct:>9.1f}% {error_pct:>7.1f}%")

    # Error rate by turn: does later turns = more errors?
    print(f"\n  Observation: Later turns tend to have {'higher' if turn_stats.get(max(turn_stats), {}).get('errors', 0) > turn_stats.get(1, {}).get('errors', 0) else 'similar'} error rates.")


def print_actionable_insights(problems):
    """Summarize key findings."""
    print_section("ACTIONABLE INSIGHTS")

    total_tokens = sum(p.total_tokens for p in problems)
    none_tokens = sum(a.tokens for p in problems for a in p.attempts if a.is_none)
    wrong_prob_tokens = sum(p.total_tokens for p in problems if not p.correct)

    insights = []

    # 1. Token waste from Nones
    none_pct = 100 * none_tokens / total_tokens if total_tokens else 0
    insights.append(
        f"1. TOKEN WASTE FROM NONES: {fmt_tokens(none_tokens)} tokens ({none_pct:.0f}%) spent on None attempts. "
        f"Each None attempt consumes tokens but produces no vote. "
        f"RECOMMENDATION: Better answer extraction and error recovery to reduce None rate."
    )

    # 2. Reasoning length
    correct_lens = [sum(len(t.reasoning_text) for t in a.turns) for p in problems for a in p.attempts
                    if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected]
    none_lens = [sum(len(t.reasoning_text) for t in a.turns) for p in problems for a in p.attempts if a.is_none]
    if correct_lens and none_lens:
        insights.append(
            f"2. REASONING LENGTH: Correct attempts average {mean(correct_lens):.0f} reasoning chars, "
            f"None attempts average {mean(none_lens):.0f}. "
            f"{'Longer reasoning correlates with Nones (model gets stuck).' if mean(none_lens) > mean(correct_lens) else 'Shorter reasoning in Nones suggests the model gives up early.'}"
        )

    # 3. Code vs reasoning
    correct_code_calls = [a.code_calls for p in problems for a in p.attempts
                          if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected]
    none_code_calls = [a.code_calls for p in problems for a in p.attempts if a.is_none]
    if correct_code_calls and none_code_calls:
        insights.append(
            f"3. CODE USAGE: Correct attempts average {mean(correct_code_calls):.1f} code calls, "
            f"None attempts average {mean(none_code_calls):.1f}. "
            f"RECOMMENDATION: {'Encourage more code execution for better answer extraction.' if mean(correct_code_calls) > mean(none_code_calls) else 'Code execution alone does not guarantee answers.'}"
        )

    # 4. Overall efficiency
    correct_count = sum(1 for p in problems for a in p.attempts if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected)
    if correct_count > 0:
        cost_per_correct = total_tokens / correct_count
        insights.append(
            f"4. EFFICIENCY: {fmt_tokens(cost_per_correct)} tokens per correct attempt. "
            f"With {none_pct:.0f}% token waste on Nones, reducing Nones by half could save ~{fmt_tokens(none_tokens/2)} tokens."
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

    analyze_tokens_by_outcome(problems)
    analyze_code_reasoning_ratio(problems)
    analyze_reasoning_length(problems)
    analyze_token_waste(problems)
    analyze_per_turn_breakdown(problems)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
