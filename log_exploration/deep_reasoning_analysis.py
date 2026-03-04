#!/usr/bin/env python3
"""
Deep Reasoning Analysis — Read full reasoning for specific attempts on specific problems.
==========================================================================================
Shows the problem text, vote distribution, and full reasoning for selected attempts.
Designed for understanding WHY the model got wrong answers.

Usage:
    python3 log_exploration/deep_reasoning_analysis.py <logfile> <problem_id>
    python3 log_exploration/deep_reasoning_analysis.py output/v31/diagnostic.log dbbfe8
"""

import sys
import os
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


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


def print_overview(problem):
    """Print problem overview with vote distribution."""
    p = problem
    print(f"\n{'=' * 80}")
    print(f"  PROBLEM: {p.problem_id}")
    print(f"  Expected: {p.expected}  |  Voted: {p.predicted}  |  Correct: {p.correct}")
    print(f"{'=' * 80}")

    # Vote distribution
    vote_counts = Counter()
    none_count = 0
    for a in p.attempts:
        if a.answer is None or a.is_none:
            none_count += 1
        else:
            vote_counts[a.answer] += 1

    print(f"\n  VOTE DISTRIBUTION:")
    for ans, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
        marker = " <<<CORRECT" if ans == p.expected else (" <<<VOTED" if ans == p.predicted else "")
        print(f"    {ans:>10} x {count}{marker}")
    if none_count:
        print(f"    {'None':>10} x {none_count}")

    # Per-attempt table
    print(f"\n  ATTEMPT TABLE:")
    print(f"  {'#':>3} {'Answer':>10} {'Temp':>5} {'Turns':>5} {'Entropy':>8} {'Time':>8} {'Errors':>6} {'Status':>8}")
    print(f"  {'─'*3} {'─'*10} {'─'*5} {'─'*5} {'─'*8} {'─'*8} {'─'*6} {'─'*8}")
    for a in sorted(p.attempts, key=lambda x: x.attempt_num):
        ans = str(a.answer) if a.answer is not None else "None"
        status = ""
        if a.answer is not None and p.expected is not None:
            status = "CORRECT" if a.answer == p.expected else "WRONG"
        elif a.is_none:
            status = "NONE"
        time_str = f"{a.time_s:.0f}s" if a.time_s < 60 else f"{a.time_s/60:.1f}m"
        print(f"  {a.attempt_num:>3} {ans:>10} {a.temperature:>5.2f} {len(a.turns):>5} {a.entropy:>8.3f} {time_str:>8} {a.errors:>6} {status:>8}")


def print_attempt_reasoning(problem, attempt, max_reasoning_chars=None):
    """Print full reasoning for one attempt."""
    a = attempt
    p = problem
    ans = str(a.answer) if a.answer is not None else "None"
    status = ""
    if a.answer is not None and p.expected is not None:
        status = "CORRECT" if a.answer == p.expected else "WRONG"
    elif a.is_none:
        status = "NONE"

    print(f"\n{'─' * 80}")
    print(f"  ATTEMPT {a.attempt_num} — Answer: {ans} ({status}) — Temp: {a.temperature} — Turns: {len(a.turns)}")
    print(f"{'─' * 80}")

    for t in sorted(a.turns, key=lambda x: x.turn_num):
        error_flag = " [ERROR]" if t.is_error else ""
        print(f"\n  --- Turn {t.turn_num}{error_flag} ---")

        # Reasoning
        if t.reasoning_text and t.reasoning_text.strip():
            text = t.reasoning_text.strip()
            if max_reasoning_chars and len(text) > max_reasoning_chars:
                text = text[:max_reasoning_chars] + f"\n... [TRUNCATED at {max_reasoning_chars} chars, total {len(t.reasoning_text)} chars]"
            print(f"\n  [REASONING]")
            for line in text.split('\n'):
                print(f"    {line}")

        # Code
        if t.code and t.code.strip():
            code_text = t.code.strip()
            if max_reasoning_chars and len(code_text) > max_reasoning_chars:
                code_text = code_text[:max_reasoning_chars] + f"\n... [TRUNCATED]"
            print(f"\n  [CODE]")
            for line in code_text.split('\n'):
                print(f"    {line}")

        # Output
        if t.output and t.output.strip():
            out_text = t.output.strip()
            if max_reasoning_chars and len(out_text) > max_reasoning_chars:
                out_text = out_text[:max_reasoning_chars] + f"\n... [TRUNCATED]"
            label = "[OUTPUT]" if not t.is_error else "[OUTPUT - ERROR]"
            print(f"\n  {label}")
            for line in out_text.split('\n'):
                print(f"    {line}")


def main():
    parser = argparse.ArgumentParser(
        description="Deep reasoning analysis for a specific problem.",
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("problem_id", help="Problem ID (full or prefix)")
    parser.add_argument("--attempts", type=str, default=None,
                        help="Comma-separated attempt numbers to show (default: all)")
    parser.add_argument("--correct-only", action="store_true",
                        help="Show only correct attempts")
    parser.add_argument("--wrong-only", action="store_true",
                        help="Show only wrong attempts (non-None, non-correct)")
    parser.add_argument("--answer", type=int, default=None,
                        help="Show only attempts with this answer")
    parser.add_argument("--max-chars", type=int, default=None,
                        help="Max chars per reasoning/code/output block")
    parser.add_argument("--overview-only", action="store_true",
                        help="Show only the overview, no reasoning")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    problems = parse_log(args.logfile)
    problem = find_problem(problems, args.problem_id)

    print_overview(problem)

    if args.overview_only:
        return

    # Filter attempts
    attempts = sorted(problem.attempts, key=lambda x: x.attempt_num)

    if args.attempts:
        nums = [int(x) for x in args.attempts.split(',')]
        attempts = [a for a in attempts if a.attempt_num in nums]
    elif args.correct_only:
        attempts = [a for a in attempts if a.answer is not None and a.answer == problem.expected]
    elif args.wrong_only:
        attempts = [a for a in attempts if a.answer is not None and a.answer != problem.expected and not a.is_none]
    elif args.answer is not None:
        attempts = [a for a in attempts if a.answer == args.answer]

    if not attempts:
        print("\n  No attempts match the filter criteria.")
        return

    for a in attempts:
        print_attempt_reasoning(problem, a, max_reasoning_chars=args.max_chars)


if __name__ == "__main__":
    main()
