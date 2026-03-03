#!/usr/bin/env python3
"""
AIMO3 One-Page Dashboard
=========================
Text-based executive summary of any diagnostic.log run.
Fits in a single terminal window (~50 lines).

Usage:
    python log_exploration/dashboard_prototype.py [logfile]
    (default: output/v22/diagnostic.log)
"""

import sys
import os
import re
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def make_bar(value, max_val, width=30, fill='#', empty='.'):
    """Create a text progress bar."""
    if max_val <= 0:
        return empty * width
    filled = int(value / max_val * width)
    filled = min(filled, width)
    return fill * filled + empty * (width - filled)


def make_spark(values, width=20):
    """Create a mini sparkline from a list of values."""
    if not values:
        return ''
    blocks = ' _.,:-=+*#@'
    mn, mx = min(values), max(values)
    rng = mx - mn if mx > mn else 1
    # Bin values into width buckets
    bucket_size = max(1, len(values) // width)
    buckets = []
    for i in range(0, len(values), bucket_size):
        chunk = values[i:i+bucket_size]
        avg = sum(chunk) / len(chunk)
        idx = int((avg - mn) / rng * (len(blocks) - 1))
        buckets.append(blocks[idx])
    return ''.join(buckets[:width])


def dashboard(problems):
    """Print one-page executive summary."""
    total = len(problems)
    correct = sum(1 for p in problems if p.correct)
    wrong = [p for p in problems if not p.correct]
    total_time = sum(p.wall_time for p in problems)
    total_budget = sum(p.budget for p in problems if p.budget > 0)
    total_att = sum(len(p.attempts) for p in problems)
    total_nones = sum(1 for p in problems for a in p.attempts if a.is_none)
    total_errors = sum(a.errors for p in problems for a in p.attempts)
    total_tokens = sum(a.tokens for p in problems for a in p.attempts)
    es_count = sum(1 for p in problems if p.early_stop)

    # Header
    print()
    print(f"  {'='*68}")
    print(f"  AIMO3 DASHBOARD")
    print(f"  {'='*68}")

    # Score bar
    score_pct = correct / max(total, 1) * 100
    bar = make_bar(correct, total, width=40)
    print(f"  Score: {correct}/{total} ({score_pct:.0f}%)  [{bar}]")

    # Batch breakdown (one line each)
    batches = defaultdict(list)
    for p in problems:
        batches[p.batch_name or 'unknown'].append(p)

    for bname, bprobs in batches.items():
        bc = sum(1 for p in bprobs if p.correct)
        bt = len(bprobs)
        bar = make_bar(bc, bt, width=15)
        short_name = bname[:25].ljust(25)
        print(f"    {short_name} {bc:>2}/{bt:<2} [{bar}]")

    # Time budget
    print(f"\n  {'─'*68}")
    budget_util = total_time / max(total_budget, 1) * 100
    time_bar = make_bar(total_time, total_budget, width=40)
    print(f"  Time:   {total_time/60:.1f}min / {total_budget/60:.1f}min budget ({budget_util:.0f}%) [{time_bar}]")
    times = sorted([p.wall_time for p in problems if p.wall_time > 0])
    if times:
        median_t = times[len(times)//2]
        print(f"  Per-problem: min={times[0]:.0f}s  median={median_t:.0f}s  max={times[-1]:.0f}s")

    # Key stats
    print(f"\n  {'─'*68}")
    none_pct = total_nones / max(total_att, 1) * 100
    err_pct = total_errors / max(total_att, 1) * 100
    es_pct = es_count / max(total, 1) * 100
    print(f"  Attempts: {total_att}  |  Nones: {total_nones} ({none_pct:.0f}%)  |  Errors: {total_errors}")
    print(f"  Early stops: {es_count}/{total} ({es_pct:.0f}%)  |  Tokens: {total_tokens:,}")

    # Error rate trend (across problems in order)
    print(f"\n  {'─'*68}")
    error_rates = []
    for p in problems:
        att_count = len(p.attempts)
        if att_count == 0:
            error_rates.append(0)
            continue
        err_rate = sum(a.errors for a in p.attempts) / att_count
        error_rates.append(err_rate)

    if error_rates:
        spark = make_spark(error_rates, width=40)
        # Trend: compare first half vs second half
        mid = len(error_rates) // 2
        first_half = sum(error_rates[:mid]) / max(mid, 1)
        second_half = sum(error_rates[mid:]) / max(len(error_rates) - mid, 1)
        if second_half < first_half * 0.8:
            trend = "IMPROVING"
        elif second_half > first_half * 1.2:
            trend = "WORSENING"
        else:
            trend = "STABLE"
        print(f"  Error trend: [{spark}] {trend}")
        print(f"    (first half avg: {first_half:.2f} err/att, second half: {second_half:.2f} err/att)")

    # None rate trend
    none_rates = []
    for p in problems:
        att_count = len(p.attempts)
        if att_count == 0:
            none_rates.append(0)
            continue
        none_rate = sum(1 for a in p.attempts if a.is_none) / att_count
        none_rates.append(none_rate)

    if none_rates:
        spark = make_spark(none_rates, width=40)
        mid = len(none_rates) // 2
        first_half = sum(none_rates[:mid]) / max(mid, 1)
        second_half = sum(none_rates[mid:]) / max(len(none_rates) - mid, 1)
        if second_half < first_half * 0.8:
            trend = "IMPROVING"
        elif second_half > first_half * 1.2:
            trend = "WORSENING"
        else:
            trend = "STABLE"
        print(f"  None trend:  [{spark}] {trend}")

    # Top 3 worst performers
    print(f"\n  {'─'*68}")
    print(f"  TOP 3 PROBLEMS TO INVESTIGATE:")

    # Score each problem: wrong = 100, close vote = 80, many nones = 60, high errors = 40
    problem_scores = []
    for p in problems:
        score = 0
        details = []
        if not p.correct:
            score += 100
            details.append(f"WRONG (pred={p.predicted}, exp={p.expected})")
            # Check if correct answer existed in votes
            if p.expected is not None and p.votes.get(p.expected, 0) > 0:
                score += 50
                details.append(f"correct was outvoted ({p.votes.get(p.expected, 0)} votes)")
        else:
            # Close vote even though correct
            if p.votes and len(p.votes) >= 2:
                sorted_v = sorted(p.votes.values(), reverse=True)
                margin = sorted_v[0] - sorted_v[1]
                if margin <= 1:
                    score += 60
                    details.append(f"close vote margin={margin}")

        none_count = sum(1 for a in p.attempts if a.is_none)
        att_count = len(p.attempts)
        if att_count > 0:
            none_rate = none_count / att_count
            if none_rate > 0.7:
                score += 40
                details.append(f"high none rate {none_count}/{att_count}")

        err_count = sum(a.errors for a in p.attempts)
        if err_count > 5:
            score += 30
            details.append(f"{err_count} errors")

        if p.wall_time > 300:
            score += 20
            details.append(f"slow ({p.wall_time:.0f}s)")

        if score > 0:
            problem_scores.append((p, score, details))

    problem_scores.sort(key=lambda x: -x[1])
    for rank, (p, score, details) in enumerate(problem_scores[:3], 1):
        status = "WRONG" if not p.correct else "OK"
        print(f"  {rank}. [{status}] {p.problem_id} ({p.batch_name or '?'})")
        for d in details:
            print(f"       - {d}")

    # Top 3 actionable improvements
    print(f"\n  {'─'*68}")
    print(f"  TOP 3 ACTIONABLE IMPROVEMENTS:")

    improvements = []

    # 1. Extraction failures
    extraction_nones = 0
    for p in problems:
        for a in p.attempts:
            if a.is_none and a.turns:
                all_text = ' '.join(t.reasoning_text or '' for t in a.turns)
                if any(kw in all_text.lower() for kw in ['the answer is', 'boxed', 'final answer', 'therefore']):
                    extraction_nones += 1
    if extraction_nones > 0:
        recovered_pct = extraction_nones / max(total_nones, 1) * 100
        improvements.append((
            extraction_nones * 3,  # priority score
            f"Fix extraction: {extraction_nones} attempts had answer text but returned None ({recovered_pct:.0f}% of all Nones)",
            f"Improve _scan_for_answer() regex. Log failed extraction text to diagnose."
        ))

    # 2. None rate optimization
    if total_nones > total_att * 0.4:
        improvements.append((
            total_nones,
            f"Reduce None rate: {total_nones}/{total_att} ({none_pct:.0f}%) attempts produced no answer",
            f"Top causes: extraction failure, no code generated, timeout. Log stop_reason."
        ))

    # 3. Error reduction
    error_attempts = sum(1 for p in problems for a in p.attempts if a.errors > 0)
    if error_attempts > 0:
        improvements.append((
            error_attempts,
            f"Reduce errors: {error_attempts} attempts had code errors ({total_errors} total errors)",
            f"Top: see errors-by-type query. Add self-contained code cell rule to prompt."
        ))

    # 4. Token waste
    wrong_tokens = sum(a.tokens for p in problems for a in p.attempts
                       if a.answer is not None and a.answer != p.expected)
    none_tokens = sum(a.tokens for p in problems for a in p.attempts if a.is_none)
    wasted = wrong_tokens + none_tokens
    if wasted > 0:
        waste_pct = wasted / max(total_tokens, 1) * 100
        improvements.append((
            int(waste_pct),
            f"Token waste: {wasted:,} tokens ({waste_pct:.0f}%) on wrong/none answers",
            f"Earlier stopping of hopeless attempts could save time for more attempts."
        ))

    # 5. Early stop tuning
    es_correct = sum(1 for p in problems if p.early_stop and p.correct)
    es_wrong = sum(1 for p in problems if p.early_stop and not p.correct)
    if es_wrong > 0:
        improvements.append((
            es_wrong * 50,
            f"Early stop false positives: {es_wrong} problems early-stopped on wrong answer",
            f"Increase early_stop threshold or add entropy check before stopping."
        ))

    # 6. Outvoted correct answers
    outvoted = 0
    for p in wrong:
        if p.expected is not None and p.votes.get(p.expected, 0) > 0:
            outvoted += 1
    if outvoted > 0:
        improvements.append((
            outvoted * 100,
            f"Outvoted: {outvoted} problems had correct answer but wrong answer won the vote",
            f"Improve vote weighting (per-answer entropy instead of global) or add more attempts."
        ))

    improvements.sort(key=lambda x: -x[0])
    for rank, (_, title, action) in enumerate(improvements[:3], 1):
        print(f"  {rank}. {title}")
        print(f"     Action: {action}")

    # Footer
    print(f"\n  {'='*68}")
    print()


def main():
    logfile = sys.argv[1] if len(sys.argv) > 1 else 'output/v22/diagnostic.log'
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    problems = parse_log(logfile)
    dashboard(problems)


if __name__ == '__main__':
    main()
