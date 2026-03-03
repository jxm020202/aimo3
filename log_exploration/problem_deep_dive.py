#!/usr/bin/env python3
"""
Problem Deep Dive — Show EVERYTHING about one problem.
========================================================
All attempts, all turns, all reasoning, all code, all errors,
votes, timing, tokens. A full dump for debugging.

Usage:
    python3 log_exploration/problem_deep_dive.py <logfile> <problem_id>
    python3 log_exploration/problem_deep_dive.py output/v22/diagnostic.log 86e8e5

Options:
    --no-reasoning    Skip reasoning text (show summary only)
    --no-code         Skip code blocks (show summary only)
    --compact         Compact mode (no reasoning or code, just stats)
    --help            Show this help
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


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


def truncate(text, max_len=200):
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"... [{len(text) - max_len} more chars]"


def find_problem(problems, pid):
    """Find a problem by ID (prefix match)."""
    exact = [p for p in problems if p.problem_id == pid]
    if exact:
        return exact[0]
    prefix = [p for p in problems if p.problem_id.startswith(pid)]
    if len(prefix) == 1:
        return prefix[0]
    if len(prefix) > 1:
        print(f"  Ambiguous prefix '{pid}'. Matches: {', '.join(p.problem_id for p in prefix)}")
        sys.exit(1)
    print(f"  Problem '{pid}' not found. Available IDs:")
    for p in problems:
        print(f"    {p.problem_id}")
    sys.exit(1)


def deep_dive(problem, show_reasoning=True, show_code=True):
    p = problem

    print(f"\n{'=' * 72}")
    print(f"  PROBLEM DEEP DIVE: {p.problem_id}")
    print(f"{'=' * 72}")

    # Header
    status = "CORRECT" if p.correct else "WRONG"
    print(f"\n  Status:     {status}")
    print(f"  Batch:      {p.batch_name} [{p.batch_idx}/{p.batch_total}]")
    print(f"  Predicted:  {p.predicted}")
    print(f"  Expected:   {p.expected}")
    print(f"  Wall Time:  {fmt_time(p.wall_time)}")
    print(f"  Budget:     {fmt_time(p.budget)}" if p.budget > 0 else "")
    print(f"  Deadline:   {fmt_time(p.deadline)}" if p.deadline > 0 else "")
    print(f"  Early Stop: {'Yes' if p.early_stop else 'No'} (threshold={p.early_stop_threshold})" if p.early_stop_threshold else f"  Early Stop: {'Yes' if p.early_stop else 'No'}")
    print(f"  Avg Entropy:{p.avg_entropy:.3f}")

    # Problem text
    if p.problem_text:
        print(f"\n  Problem Text:")
        print(f"    {p.problem_text}")

    # Aggregate stats
    total_att = len(p.attempts)
    nones = sum(1 for a in p.attempts if a.is_none)
    answered = total_att - nones
    correct_att = sum(1 for a in p.attempts if a.answer is not None and a.answer == p.expected) if p.expected else 0
    wrong_att = answered - correct_att
    total_tokens = sum(a.tokens for a in p.attempts)
    total_errors = sum(a.errors for a in p.attempts)
    total_code_calls = sum(a.code_calls for a in p.attempts)

    print(f"\n  {'─' * 50}")
    print(f"  AGGREGATE STATS")
    print(f"  {'─' * 50}")
    print(f"  Attempts:    {total_att} total, {answered} answered, {nones} None")
    print(f"  Correct:     {correct_att} | Wrong: {wrong_att}")
    print(f"  Tokens:      {fmt_tokens(total_tokens)}")
    print(f"  Code Calls:  {total_code_calls}")
    print(f"  Errors:      {total_errors}")

    # Votes
    if p.votes:
        print(f"\n  Votes:")
        for answer, count in sorted(p.votes.items(), key=lambda x: -x[1]):
            marker = " <-- CORRECT" if answer == p.expected else ""
            winner = " (winner)" if count == max(p.votes.values()) else ""
            print(f"    {answer}: {count} vote(s){winner}{marker}")

    # Attempt summary table
    print(f"\n  {'─' * 50}")
    print(f"  ATTEMPT SUMMARY")
    print(f"  {'─' * 50}")
    print(f"  {'#':>3} {'Answer':>10} {'OK':>4} {'Entropy':>8} {'Temp':>6} {'Turns':>6} {'Code':>5} {'Err':>4} {'Tokens':>8} {'Time':>8}")
    print(f"  {'─'*3} {'─'*10} {'─'*4} {'─'*8} {'─'*6} {'─'*6} {'─'*5} {'─'*4} {'─'*8} {'─'*8}")

    for a in sorted(p.attempts, key=lambda x: x.attempt_num):
        ans = str(a.answer) if a.answer is not None else "None"
        if len(ans) > 10:
            ans = ans[:8] + ".."
        ok = ""
        if a.answer is not None and p.expected is not None:
            ok = "Y" if a.answer == p.expected else "N"
        elif a.is_none:
            ok = "-"
        temp = f"{a.temperature:.1f}" if a.temperature is not None else "?"
        turns = len(a.turns)
        print(f"  {a.attempt_num:>3} {ans:>10} {ok:>4} {a.entropy:>8.3f} {temp:>6} {turns:>6} {a.code_calls:>5} {a.errors:>4} {fmt_tokens(a.tokens):>8} {fmt_time(a.time_s):>8}")

    # Detailed attempt dump
    for a in sorted(p.attempts, key=lambda x: x.attempt_num):
        print(f"\n  {'=' * 68}")
        ans_str = str(a.answer) if a.answer is not None else "None"
        ok_str = ""
        if a.answer is not None and p.expected is not None:
            ok_str = " [CORRECT]" if a.answer == p.expected else " [WRONG]"
        elif a.is_none:
            ok_str = " [NONE]"
        print(f"  ATTEMPT {a.attempt_num}{ok_str} | answer={ans_str} | entropy={a.entropy:.3f} | time={fmt_time(a.time_s)}")
        print(f"  code_calls={a.code_calls} | errors={a.errors} | tokens={fmt_tokens(a.tokens)} | temp={a.temperature}")
        if a.libraries:
            print(f"  libraries: {', '.join(a.libraries)}")
        print(f"  {'=' * 68}")

        if not a.turns:
            print(f"    (no turn data)")
            continue

        for t in sorted(a.turns, key=lambda x: x.turn_num):
            error_flag = " [ERROR]" if t.is_error else ""
            print(f"\n    --- Turn {t.turn_num}{error_flag} ---")

            # Reasoning
            if t.reasoning_text.strip():
                if show_reasoning:
                    print(f"    [Reasoning] ({len(t.reasoning_text)} chars)")
                    for line in t.reasoning_text.strip().split('\n'):
                        print(f"      {line}")
                else:
                    print(f"    [Reasoning] ({len(t.reasoning_text)} chars) {truncate(t.reasoning_text.strip(), 100)}")
            elif t.reasoning_chars > 0:
                print(f"    [Reasoning] ({t.reasoning_chars} chars, text not captured)")

            # Code
            if t.code.strip():
                if show_code:
                    print(f"    [Code] ({len(t.code)} chars)")
                    for line in t.code.strip().split('\n'):
                        print(f"      {line}")
                else:
                    print(f"    [Code] ({len(t.code)} chars) {truncate(t.code.strip(), 100)}")

            # Output
            if t.output.strip():
                output_lines = t.output.strip().split('\n')
                if len(output_lines) <= 10 or show_code:
                    print(f"    [Output]{error_flag} ({len(t.output)} chars)")
                    for line in output_lines:
                        print(f"      {line}")
                else:
                    print(f"    [Output]{error_flag} ({len(t.output)} chars, {len(output_lines)} lines)")
                    for line in output_lines[:5]:
                        print(f"      {line}")
                    print(f"      ... [{len(output_lines) - 10} more lines] ...")
                    for line in output_lines[-5:]:
                        print(f"      {line}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Deep dive into a single AIMO3 problem — shows all attempts, turns, reasoning, code, errors.",
        usage="python3 log_exploration/problem_deep_dive.py <logfile> <problem_id> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("problem_id", help="Problem ID (full or prefix)")
    parser.add_argument("--no-reasoning", action="store_true", help="Skip full reasoning text")
    parser.add_argument("--no-code", action="store_true", help="Skip full code blocks")
    parser.add_argument("--compact", action="store_true", help="Compact mode (stats only, no reasoning/code)")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    problems = parse_log(args.logfile)
    problem = find_problem(problems, args.problem_id)

    show_reasoning = not (args.no_reasoning or args.compact)
    show_code = not (args.no_code or args.compact)

    deep_dive(problem, show_reasoning=show_reasoning, show_code=show_code)


if __name__ == "__main__":
    main()
