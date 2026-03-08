#!/usr/bin/env python3
"""
GenSelect Trace Analysis
========================
Analyzes solution traces for wrong vs correct problems to inform GenSelect judge design.
Specifically examines what truncation to 2000 chars (500+1500) loses.

Usage:
    python3 log_exploration/genselect_trace_analysis.py output/120b-v38/diagnostic.log
"""

import sys
import os
import re
import textwrap
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

def build_full_trace(attempt):
    """Reconstruct the full conversation trace from an attempt's turns."""
    parts = []
    for turn in attempt.turns:
        if turn.reasoning_text:
            parts.append(f"[REASONING Turn {turn.turn_num}]\n{turn.reasoning_text}")
        if turn.code:
            parts.append(f"[CODE Turn {turn.turn_num}]\n{turn.code}")
        if turn.output:
            label = "[OUTPUT Turn {} ERROR]" if turn.is_error else "[OUTPUT Turn {}]"
            parts.append(f"{label.format(turn.turn_num)}\n{turn.output}")
    return "\n\n".join(parts)


def truncate_trace(trace, first_n=500, last_n=1500):
    """Simulate the 500+1500 truncation used in GenSelect."""
    if len(trace) <= first_n + last_n:
        return trace, False  # No truncation needed
    first = trace[:first_n]
    last = trace[-last_n:]
    return first + "\n\n... [TRUNCATED] ...\n\n" + last, True


def trace_stats(attempt):
    """Compute trace composition stats."""
    total_reasoning = 0
    total_code = 0
    total_output = 0
    code_blocks = 0
    error_turns = 0

    for turn in attempt.turns:
        total_reasoning += len(turn.reasoning_text)
        total_code += len(turn.code)
        total_output += len(turn.output)
        if turn.code:
            code_blocks += 1
        if turn.is_error:
            error_turns += 1

    total = total_reasoning + total_code + total_output
    return {
        'turns': len(attempt.turns),
        'reasoning_chars': total_reasoning,
        'code_chars': total_code,
        'output_chars': total_output,
        'total_chars': total,
        'code_blocks': code_blocks,
        'error_turns': error_turns,
        'pct_reasoning': total_reasoning / max(total, 1) * 100,
        'pct_code': total_code / max(total, 1) * 100,
        'pct_output': total_output / max(total, 1) * 100,
    }


def has_verification_pattern(attempt):
    """Check if an attempt includes computational verification of its answer."""
    patterns = [
        r'verify', r'check', r'confirm', r'validate',
        r'let me test', r'double.check', r'sanity check',
        r'assert', r'== \d+', r'answer is \d+',
    ]
    for turn in attempt.turns:
        text = (turn.reasoning_text + " " + turn.code + " " + turn.output).lower()
        for pat in patterns:
            if re.search(pat, text):
                return True
    return False


def detect_approach(attempt):
    """Detect the solution approach (analytical vs computational)."""
    total_code = sum(len(t.code) for t in attempt.turns)
    total_reasoning = sum(len(t.reasoning_text) for t in attempt.turns)
    code_blocks = sum(1 for t in attempt.turns if t.code)

    if code_blocks == 0:
        return "pure_analytical"
    elif total_code > total_reasoning:
        return "computational_heavy"
    else:
        return "mixed"


def show_trace_excerpt(trace, label, max_show=3000):
    """Print a trace excerpt with clear formatting."""
    print(f"\n{'─'*70}")
    print(f"  {label}")
    print(f"{'─'*70}")
    if len(trace) <= max_show:
        print(trace)
    else:
        print(trace[:max_show])
        print(f"\n... [{len(trace) - max_show} more chars] ...")
    print(f"{'─'*70}")


def show_truncated_trace(trace, label):
    """Show what the 500+1500 truncation produces."""
    truncated, was_truncated = truncate_trace(trace)
    print(f"\n{'='*70}")
    print(f"  TRUNCATED VIEW: {label}")
    print(f"  Full trace: {len(trace)} chars | Truncated: {len(truncated)} chars | Lost: {max(0, len(trace) - 2000)} chars ({max(0, len(trace) - 2000) / max(len(trace),1) * 100:.1f}%)")
    print(f"{'='*70}")

    if not was_truncated:
        print("[No truncation needed — trace fits in 2000 chars]")
        print(truncated)
    else:
        # Show first 500
        print(f"\n--- FIRST 500 CHARS ---")
        print(trace[:500])
        print(f"\n--- [MIDDLE OMITTED: {len(trace) - 2000} chars] ---")
        print(f"\n--- LAST 1500 CHARS ---")
        print(trace[-1500:])

    print(f"{'='*70}")


def analyze_problem(problem, is_wrong=True):
    """Full analysis of a problem's attempts and traces."""
    pid = problem.problem_id
    expected = problem.expected
    predicted = problem.predicted

    print(f"\n{'#'*80}")
    print(f"##  PROBLEM {pid}")
    if is_wrong:
        print(f"##  WRONG: predicted={predicted}, expected={expected}")
    else:
        print(f"##  CORRECT: predicted={predicted}")
    print(f"{'#'*80}")

    # ── Vote distribution ──
    print(f"\n  VOTE DISTRIBUTION ({sum(problem.votes.values())} total votes):")
    sorted_votes = sorted(problem.votes.items(), key=lambda x: x[1], reverse=True)
    for ans, count in sorted_votes:
        marker = ""
        if ans == expected:
            marker = " <-- CORRECT"
        elif ans == predicted:
            marker = " <-- PREDICTED (wrong)" if is_wrong else " <-- PREDICTED"
        print(f"    {ans:>8}: {count:>3} votes ({count/sum(problem.votes.values())*100:.1f}%){marker}")

    none_count = sum(1 for a in problem.attempts if a.is_none)
    print(f"    {'None':>8}: {none_count:>3} attempts (no answer)")

    # ── Group attempts by answer ──
    answer_groups = defaultdict(list)
    none_attempts = []
    for att in problem.attempts:
        if att.is_none:
            none_attempts.append(att)
        else:
            answer_groups[att.answer].append(att)

    # Pick top 3 answer clusters + correct answer if not in top 3
    top_answers = sorted(answer_groups.keys(), key=lambda a: len(answer_groups[a]), reverse=True)[:3]
    if expected is not None and expected not in top_answers and expected in answer_groups:
        top_answers.append(expected)

    print(f"\n  TOP ANSWER CLUSTERS FOR DETAILED ANALYSIS: {top_answers}")

    # ── Aggregate stats per answer cluster ──
    print(f"\n{'='*70}")
    print(f"  CLUSTER COMPARISON")
    print(f"{'='*70}")
    print(f"  {'Answer':>8} | {'Count':>5} | {'Avg Turns':>9} | {'Avg Chars':>10} | {'Avg Code':>8} | {'Approach':>18} | {'Verify':>6}")
    print(f"  {'-'*8} | {'-'*5} | {'-'*9} | {'-'*10} | {'-'*8} | {'-'*18} | {'-'*6}")

    for ans in top_answers:
        atts = answer_groups[ans]
        stats_list = [trace_stats(a) for a in atts]
        avg_turns = sum(s['turns'] for s in stats_list) / len(stats_list)
        avg_chars = sum(s['total_chars'] for s in stats_list) / len(stats_list)
        avg_code = sum(s['code_blocks'] for s in stats_list) / len(stats_list)
        approaches = Counter(detect_approach(a) for a in atts)
        verify_count = sum(1 for a in atts if has_verification_pattern(a))
        top_approach = approaches.most_common(1)[0][0]
        marker = " *" if ans == expected else ""
        print(f"  {ans:>8}{marker} | {len(atts):>5} | {avg_turns:>9.1f} | {avg_chars:>10.0f} | {avg_code:>8.1f} | {top_approach:>18} | {verify_count:>3}/{len(atts)}")

    # ── Detailed trace analysis for each cluster ──
    for ans in top_answers:
        atts = answer_groups[ans]
        # Pick a representative: the one with median trace length
        atts_with_len = [(a, trace_stats(a)['total_chars']) for a in atts]
        atts_with_len.sort(key=lambda x: x[1])
        representative = atts_with_len[len(atts_with_len)//2][0]

        label_suffix = "[CORRECT ANSWER]" if ans == expected else "[WRONG ANSWER]" if ans == predicted and is_wrong else ""

        print(f"\n\n{'*'*80}")
        print(f"**  REPRESENTATIVE TRACE: answer={ans} (attempt #{representative.attempt_num}) {label_suffix}")
        print(f"**  temp={representative.temperature} | time={representative.time_s:.1f}s | code_calls={representative.code_calls}")
        print(f"{'*'*80}")

        stats = trace_stats(representative)
        full_trace = build_full_trace(representative)

        print(f"\n  TRACE COMPOSITION:")
        print(f"    Total chars: {stats['total_chars']:,}")
        print(f"    Reasoning:   {stats['reasoning_chars']:,} chars ({stats['pct_reasoning']:.1f}%)")
        print(f"    Code:        {stats['code_chars']:,} chars ({stats['pct_code']:.1f}%)")
        print(f"    Output:      {stats['output_chars']:,} chars ({stats['pct_output']:.1f}%)")
        print(f"    Turns:       {stats['turns']}")
        print(f"    Code blocks: {stats['code_blocks']}")
        print(f"    Error turns: {stats['error_turns']}")
        print(f"    Approach:    {detect_approach(representative)}")
        print(f"    Verifies:    {has_verification_pattern(representative)}")

        # Show turn-by-turn breakdown
        print(f"\n  TURN-BY-TURN BREAKDOWN:")
        for turn in representative.turns:
            r_len = len(turn.reasoning_text)
            c_len = len(turn.code)
            o_len = len(turn.output)
            err_mark = " [ERROR]" if turn.is_error else ""
            print(f"    Turn {turn.turn_num}: reasoning={r_len:,} code={c_len:,} output={o_len:,}{err_mark}")

        # Show full trace (capped for readability)
        show_trace_excerpt(full_trace, f"FULL TRACE (answer={ans}, attempt #{representative.attempt_num})", max_show=8000)

        # Show truncated version
        show_truncated_trace(full_trace, f"answer={ans}, attempt #{representative.attempt_num}")

        # Analyze what's in the middle (what truncation loses)
        if stats['total_chars'] > 2000:
            middle = full_trace[500:-1500]
            print(f"\n  MIDDLE SECTION ANALYSIS (the {len(middle):,} chars lost to truncation):")

            # Count code blocks in middle
            code_blocks_in_middle = len(re.findall(r'\[CODE Turn \d+\]', middle))
            reasoning_blocks_in_middle = len(re.findall(r'\[REASONING Turn \d+\]', middle))
            output_blocks_in_middle = len(re.findall(r'\[OUTPUT Turn \d+\]', middle))

            print(f"    Reasoning blocks in middle: {reasoning_blocks_in_middle}")
            print(f"    Code blocks in middle:      {code_blocks_in_middle}")
            print(f"    Output blocks in middle:    {output_blocks_in_middle}")

            # Check for key patterns in middle
            key_patterns = {
                'answer_mention': r'\b(?:answer is|= \d{1,5}\b|result[: ])',
                'verification': r'(?:verify|check|confirm|validate|assert)',
                'error_recovery': r'(?:error|traceback|fix|retry|instead)',
                'key_insight': r'(?:notice|observe|key|insight|crucial|therefore|thus|hence)',
                'final_computation': r'(?:final|total|sum|product|result)',
            }
            for name, pat in key_patterns.items():
                matches = len(re.findall(pat, middle, re.IGNORECASE))
                print(f"    '{name}' patterns in middle: {matches}")


def analyze_truncation_quality(problems):
    """Cross-problem analysis of truncation quality."""
    print(f"\n\n{'#'*80}")
    print(f"##  CROSS-PROBLEM TRUNCATION ANALYSIS")
    print(f"{'#'*80}")

    all_stats = []
    for p in problems:
        for a in p.attempts:
            if a.is_none:
                continue
            stats = trace_stats(a)
            full_trace = build_full_trace(a)
            is_correct_vote = (a.answer == p.expected)
            all_stats.append({
                'problem': p.problem_id,
                'answer': a.answer,
                'is_correct': is_correct_vote,
                'is_problem_correct': p.correct,
                'chars': stats['total_chars'],
                'turns': stats['turns'],
                'code_blocks': stats['code_blocks'],
                'pct_reasoning': stats['pct_reasoning'],
                'pct_code': stats['pct_code'],
                'pct_output': stats['pct_output'],
                'approach': detect_approach(a),
                'verifies': has_verification_pattern(a),
                'trace': full_trace,
            })

    # Compare correct vs wrong answers
    correct_stats = [s for s in all_stats if s['is_correct']]
    wrong_stats = [s for s in all_stats if not s['is_correct']]

    print(f"\n  CORRECT ANSWER ATTEMPTS: {len(correct_stats)}")
    if correct_stats:
        avg_c = sum(s['chars'] for s in correct_stats) / len(correct_stats)
        avg_t = sum(s['turns'] for s in correct_stats) / len(correct_stats)
        avg_cb = sum(s['code_blocks'] for s in correct_stats) / len(correct_stats)
        avg_r = sum(s['pct_reasoning'] for s in correct_stats) / len(correct_stats)
        verify_r = sum(1 for s in correct_stats if s['verifies']) / len(correct_stats)
        approaches = Counter(s['approach'] for s in correct_stats)
        print(f"    Avg chars:    {avg_c:,.0f}")
        print(f"    Avg turns:    {avg_t:.1f}")
        print(f"    Avg code blocks: {avg_cb:.1f}")
        print(f"    Avg % reasoning: {avg_r:.1f}%")
        print(f"    Verification rate: {verify_r:.1%}")
        print(f"    Approaches: {dict(approaches)}")
        print(f"    Traces > 2000 chars: {sum(1 for s in correct_stats if s['chars'] > 2000)}/{len(correct_stats)}")
        print(f"    Traces > 5000 chars: {sum(1 for s in correct_stats if s['chars'] > 5000)}/{len(correct_stats)}")
        print(f"    Traces > 10000 chars: {sum(1 for s in correct_stats if s['chars'] > 10000)}/{len(correct_stats)}")

    print(f"\n  WRONG ANSWER ATTEMPTS: {len(wrong_stats)}")
    if wrong_stats:
        avg_c = sum(s['chars'] for s in wrong_stats) / len(wrong_stats)
        avg_t = sum(s['turns'] for s in wrong_stats) / len(wrong_stats)
        avg_cb = sum(s['code_blocks'] for s in wrong_stats) / len(wrong_stats)
        avg_r = sum(s['pct_reasoning'] for s in wrong_stats) / len(wrong_stats)
        verify_r = sum(1 for s in wrong_stats if s['verifies']) / len(wrong_stats)
        approaches = Counter(s['approach'] for s in wrong_stats)
        print(f"    Avg chars:    {avg_c:,.0f}")
        print(f"    Avg turns:    {avg_t:.1f}")
        print(f"    Avg code blocks: {avg_cb:.1f}")
        print(f"    Avg % reasoning: {avg_r:.1f}%")
        print(f"    Verification rate: {verify_r:.1%}")
        print(f"    Approaches: {dict(approaches)}")
        print(f"    Traces > 2000 chars: {sum(1 for s in wrong_stats if s['chars'] > 2000)}/{len(wrong_stats)}")
        print(f"    Traces > 5000 chars: {sum(1 for s in wrong_stats if s['chars'] > 5000)}/{len(wrong_stats)}")
        print(f"    Traces > 10000 chars: {sum(1 for s in wrong_stats if s['chars'] > 10000)}/{len(wrong_stats)}")

    # Truncation loss analysis
    print(f"\n  TRUNCATION LOSS BY CATEGORY:")
    for label, stats_group in [("Correct answers", correct_stats), ("Wrong answers", wrong_stats)]:
        if not stats_group:
            continue
        losses = []
        for s in stats_group:
            trace = s['trace']
            if len(trace) > 2000:
                middle = trace[500:-1500]
                # Count what's lost
                code_lost = len(re.findall(r'\[CODE Turn \d+\]', middle))
                reasoning_lost = len(re.findall(r'\[REASONING Turn \d+\]', middle))
                losses.append({
                    'chars_lost': len(middle),
                    'pct_lost': len(middle) / len(trace) * 100,
                    'code_blocks_lost': code_lost,
                    'reasoning_blocks_lost': reasoning_lost,
                })

        if losses:
            avg_lost = sum(l['chars_lost'] for l in losses) / len(losses)
            avg_pct = sum(l['pct_lost'] for l in losses) / len(losses)
            avg_code_lost = sum(l['code_blocks_lost'] for l in losses) / len(losses)
            avg_reason_lost = sum(l['reasoning_blocks_lost'] for l in losses) / len(losses)
            print(f"\n    {label} (truncated traces: {len(losses)}/{len(stats_group)}):")
            print(f"      Avg chars lost:           {avg_lost:,.0f}")
            print(f"      Avg % lost:               {avg_pct:.1f}%")
            print(f"      Avg code blocks lost:     {avg_code_lost:.1f}")
            print(f"      Avg reasoning blocks lost: {avg_reason_lost:.1f}")

    # Specific analysis: For wrong problems where correct answer was outvoted,
    # can we distinguish correct from wrong traces with truncated content?
    print(f"\n  DISTINGUISHABILITY ANALYSIS (wrong problems only):")
    wrong_problems = [p for p in problems if not p.correct]
    for p in wrong_problems:
        correct_atts = [a for a in p.attempts if a.answer == p.expected]
        wrong_atts = [a for a in p.attempts if a.answer == p.predicted]

        if not correct_atts or not wrong_atts:
            continue

        print(f"\n    Problem {p.problem_id} (correct={p.expected}, predicted={p.predicted}):")

        # Build truncated traces and compare
        for label, att_group in [("Correct answer traces", correct_atts), ("Wrong majority traces", wrong_atts[:3])]:
            print(f"      {label} ({len(att_group)}):")
            for att in att_group:
                trace = build_full_trace(att)
                trunc, was_trunc = truncate_trace(trace)
                stats = trace_stats(att)

                # Check if key features survive truncation
                has_code_in_first500 = bool(re.search(r'\[CODE', trace[:500]))
                has_code_in_last1500 = bool(re.search(r'\[CODE', trace[-1500:]))
                has_answer_in_last1500 = bool(re.search(rf'\b{att.answer}\b', trace[-1500:])) if att.answer is not None else False
                has_verify_in_last1500 = bool(re.search(r'(?:verify|check|confirm)', trace[-1500:], re.IGNORECASE))

                print(f"        Attempt #{att.attempt_num}: {stats['total_chars']:,} chars, {stats['turns']} turns, {stats['code_blocks']} code blocks")
                print(f"          Approach: {detect_approach(att)} | Verifies: {has_verification_pattern(att)}")
                if was_trunc:
                    print(f"          After truncation: code in first500={has_code_in_first500}, code in last1500={has_code_in_last1500}")
                    print(f"          Answer mention in last1500={has_answer_in_last1500}, verification in last1500={has_verify_in_last1500}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/genselect_trace_analysis.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    if not problems:
        print(f"No problems parsed from {logfile}")
        sys.exit(1)

    print(f"Parsed {len(problems)} problems from {logfile}")
    print(f"Correct: {sum(1 for p in problems if p.correct)}/{len(problems)}")

    # Separate wrong and correct
    wrong = [p for p in problems if not p.correct]
    correct = [p for p in problems if p.correct]

    # ── WRONG PROBLEMS: Full analysis ──
    print(f"\n\n{'#'*80}")
    print(f"##  SECTION 1: WRONG PROBLEMS ({len(wrong)})")
    print(f"{'#'*80}")

    for p in wrong:
        analyze_problem(p, is_wrong=True)

    # ── CORRECT PROBLEMS: Brief analysis ──
    print(f"\n\n{'#'*80}")
    print(f"##  SECTION 2: CORRECT PROBLEMS ({len(correct)}) — BRIEF")
    print(f"{'#'*80}")

    for p in correct:
        pid = p.problem_id
        print(f"\n{'='*60}")
        print(f"  PROBLEM {pid} — CORRECT (predicted={p.predicted})")
        print(f"{'='*60}")

        # Vote distribution
        print(f"\n  VOTE DISTRIBUTION ({sum(p.votes.values())} total):")
        sorted_votes = sorted(p.votes.items(), key=lambda x: x[1], reverse=True)
        for ans, count in sorted_votes:
            marker = " <-- PREDICTED" if ans == p.predicted else ""
            print(f"    {ans:>8}: {count:>3} votes ({count/sum(p.votes.values())*100:.1f}%){marker}")
        none_count = sum(1 for a in p.attempts if a.is_none)
        print(f"    {'None':>8}: {none_count:>3} attempts")

        # Trace length stats
        traced = [(a, trace_stats(a)) for a in p.attempts if not a.is_none]
        if traced:
            chars = [s['total_chars'] for _, s in traced]
            turns = [s['turns'] for _, s in traced]
            code_blocks = [s['code_blocks'] for _, s in traced]
            print(f"\n  TRACE STATS:")
            print(f"    Chars: min={min(chars):,} max={max(chars):,} avg={sum(chars)/len(chars):,.0f}")
            print(f"    Turns: min={min(turns)} max={max(turns)} avg={sum(turns)/len(turns):.1f}")
            print(f"    Code blocks: min={min(code_blocks)} max={max(code_blocks)} avg={sum(code_blocks)/len(code_blocks):.1f}")
            over_2k = sum(1 for c in chars if c > 2000)
            print(f"    Traces > 2000 chars: {over_2k}/{len(chars)} ({over_2k/len(chars)*100:.0f}%)")

    # ── CROSS-PROBLEM ANALYSIS ──
    analyze_truncation_quality(problems)

    # ── FINAL SUMMARY / RECOMMENDATIONS ──
    print(f"\n\n{'#'*80}")
    print(f"##  ANALYSIS SUMMARY & RECOMMENDATIONS")
    print(f"{'#'*80}")

    # Compute aggregate stats
    all_traces = []
    for p in problems:
        for a in p.attempts:
            if a.is_none:
                continue
            trace = build_full_trace(a)
            all_traces.append({
                'chars': len(trace),
                'is_correct': a.answer == p.expected,
                'problem_correct': p.correct,
            })

    if all_traces:
        total = len(all_traces)
        over_2k = sum(1 for t in all_traces if t['chars'] > 2000)
        over_5k = sum(1 for t in all_traces if t['chars'] > 5000)
        over_10k = sum(1 for t in all_traces if t['chars'] > 10000)
        avg_chars = sum(t['chars'] for t in all_traces) / total
        median_chars = sorted(t['chars'] for t in all_traces)[total // 2]

        print(f"\n  TRACE LENGTH DISTRIBUTION ({total} non-None attempts):")
        print(f"    Average:  {avg_chars:,.0f} chars")
        print(f"    Median:   {median_chars:,} chars")
        print(f"    > 2000:   {over_2k}/{total} ({over_2k/total*100:.0f}%)")
        print(f"    > 5000:   {over_5k}/{total} ({over_5k/total*100:.0f}%)")
        print(f"    > 10000:  {over_10k}/{total} ({over_10k/total*100:.0f}%)")
        print(f"    2000-char window captures: {2000/avg_chars*100:.1f}% of average trace")
        print(f"    2000-char window captures: {2000/median_chars*100:.1f}% of median trace")

    # Histogram
    print(f"\n  TRACE LENGTH HISTOGRAM:")
    buckets = [0, 1000, 2000, 3000, 5000, 7500, 10000, 15000, 20000, 50000]
    for i in range(len(buckets)-1):
        lo, hi = buckets[i], buckets[i+1]
        count = sum(1 for t in all_traces if lo <= t['chars'] < hi)
        bar = '#' * (count * 2)
        print(f"    {lo:>6}-{hi:>6}: {count:>3} {bar}")
    count = sum(1 for t in all_traces if t['chars'] >= buckets[-1])
    if count:
        print(f"    {buckets[-1]:>6}+     : {count:>3} {'#' * (count * 2)}")


if __name__ == '__main__':
    main()
