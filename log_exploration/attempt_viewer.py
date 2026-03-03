#!/usr/bin/env python3
"""
Attempt Viewer — Replay one specific attempt turn-by-turn.
============================================================
Shows reasoning text, code, output, and errors for a single attempt
on a single problem. Like watching the model think.

Usage:
    python3 log_exploration/attempt_viewer.py <logfile> <problem_id> <attempt_num>
    python3 log_exploration/attempt_viewer.py output/v22/diagnostic.log 86e8e5 3

Options:
    --code-only     Show only code turns (skip reasoning)
    --errors-only   Show only turns with errors
    --summary       Just show turn summary table, no content
    --help          Show this help
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def fmt_time(s):
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


def fmt_tokens(n):
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


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
    print(f"  Problem '{pid}' not found.")
    sys.exit(1)


def find_attempt(problem, attempt_num):
    """Find an attempt by number."""
    for a in problem.attempts:
        if a.attempt_num == attempt_num:
            return a
    available = sorted(a.attempt_num for a in problem.attempts)
    print(f"  Attempt {attempt_num} not found for problem {problem.problem_id}.")
    print(f"  Available attempts: {available}")
    sys.exit(1)


def view_attempt(problem, attempt, code_only=False, errors_only=False, summary_only=False):
    p = problem
    a = attempt

    ans_str = str(a.answer) if a.answer is not None else "None"
    ok_str = ""
    if a.answer is not None and p.expected is not None:
        ok_str = " CORRECT" if a.answer == p.expected else " WRONG"
    elif a.is_none:
        ok_str = " NONE"

    print(f"\n{'=' * 72}")
    print(f"  ATTEMPT VIEWER: Problem {p.problem_id} / Attempt {a.attempt_num}")
    print(f"{'=' * 72}")

    # Attempt header
    print(f"\n  Answer:      {ans_str}{ok_str}")
    print(f"  Expected:    {p.expected}")
    print(f"  Entropy:     {a.entropy:.3f}")
    print(f"  Temperature: {a.temperature}")
    print(f"  Time:        {fmt_time(a.time_s)}")
    print(f"  Tokens:      {fmt_tokens(a.tokens)}")
    print(f"  Code Calls:  {a.code_calls}")
    print(f"  Errors:      {a.errors}")
    print(f"  Turns:       {len(a.turns)}")
    if a.libraries:
        print(f"  Libraries:   {', '.join(a.libraries)}")

    if not a.turns:
        print(f"\n  (no turn data available)")
        return

    # Turn summary table
    print(f"\n  {'─' * 60}")
    print(f"  TURN SUMMARY")
    print(f"  {'─' * 60}")
    print(f"  {'#':>4} {'Reasoning':>12} {'Code':>10} {'Output':>10} {'Error':>6}")
    print(f"  {'─'*4} {'─'*12} {'─'*10} {'─'*10} {'─'*6}")

    for t in sorted(a.turns, key=lambda x: x.turn_num):
        r_len = len(t.reasoning_text) if t.reasoning_text else t.reasoning_chars
        c_len = len(t.code) if t.code else 0
        o_len = len(t.output) if t.output else 0
        err = "YES" if t.is_error else ""
        print(f"  {t.turn_num:>4} {r_len:>10} ch {c_len:>8} ch {o_len:>8} ch {err:>6}")

    if summary_only:
        return

    # Full turn replay
    print(f"\n  {'─' * 60}")
    print(f"  TURN-BY-TURN REPLAY")
    print(f"  {'─' * 60}")

    turns = sorted(a.turns, key=lambda x: x.turn_num)
    if errors_only:
        turns = [t for t in turns if t.is_error]
        if not turns:
            print(f"\n  No error turns in this attempt.")
            return

    for t in turns:
        error_flag = " [ERROR]" if t.is_error else ""
        print(f"\n  {'~' * 60}")
        print(f"  Turn {t.turn_num}{error_flag}")
        print(f"  {'~' * 60}")

        # Reasoning
        if not code_only and t.reasoning_text.strip():
            print(f"\n  [REASONING] ({len(t.reasoning_text)} chars)")
            print(f"  {'.' * 40}")
            for line in t.reasoning_text.strip().split('\n'):
                print(f"    {line}")

        # Code
        if t.code.strip():
            print(f"\n  [CODE] ({len(t.code)} chars)")
            print(f"  {'.' * 40}")
            for line in t.code.strip().split('\n'):
                print(f"    {line}")

        # Output
        if t.output.strip():
            label = "[OUTPUT]" if not t.is_error else "[OUTPUT - ERROR]"
            print(f"\n  {label} ({len(t.output)} chars)")
            print(f"  {'.' * 40}")
            for line in t.output.strip().split('\n'):
                print(f"    {line}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="View a single attempt turn-by-turn — like replaying the model's reasoning.",
        usage="python3 log_exploration/attempt_viewer.py <logfile> <problem_id> <attempt_num> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("problem_id", help="Problem ID (full or prefix)")
    parser.add_argument("attempt_num", type=int, help="Attempt number (1-based)")
    parser.add_argument("--code-only", action="store_true", help="Show only code/output turns")
    parser.add_argument("--errors-only", action="store_true", help="Show only turns with errors")
    parser.add_argument("--summary", action="store_true", help="Show turn summary table only")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    problems = parse_log(args.logfile)
    problem = find_problem(problems, args.problem_id)
    attempt = find_attempt(problem, args.attempt_num)

    view_attempt(problem, attempt,
                 code_only=args.code_only,
                 errors_only=args.errors_only,
                 summary_only=args.summary)


if __name__ == "__main__":
    main()
