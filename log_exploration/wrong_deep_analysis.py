#!/usr/bin/env python3
"""
Deep analysis of specific wrong problems — extracts full reasoning and code
for selected attempts to understand failure modes.

Usage:
    python3 log_exploration/wrong_deep_analysis.py <logfile> <problem_id> [attempt_nums...]

    If no attempt_nums given, shows the correct attempt and 2 wrong ones.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def find_problem(problems, pid):
    exact = [p for p in problems if p.problem_id == pid]
    if exact:
        return exact[0]
    prefix = [p for p in problems if p.problem_id.startswith(pid)]
    if len(prefix) == 1:
        return prefix[0]
    if len(prefix) > 1:
        print(f"Ambiguous: {[p.problem_id for p in prefix]}")
        sys.exit(1)
    print(f"Not found: {pid}")
    sys.exit(1)


def show_attempt_full(problem, attempt):
    a = attempt
    ans_str = str(a.answer) if a.answer is not None else "None"
    ok_str = ""
    if a.answer is not None and problem.expected is not None:
        ok_str = " [CORRECT]" if a.answer == problem.expected else " [WRONG]"
    elif a.is_none:
        ok_str = " [NONE]"

    print(f"\n{'='*80}")
    print(f"  ATTEMPT {a.attempt_num}{ok_str} | answer={ans_str} | temp={a.temperature}")
    print(f"  turns={len(a.turns)} | code_calls={a.code_calls} | errors={a.errors} | tokens={a.tokens}")
    print(f"{'='*80}")

    if not a.turns:
        print("  (no turn data)")
        return

    for t in sorted(a.turns, key=lambda x: x.turn_num):
        error_flag = " [ERROR]" if t.is_error else ""
        print(f"\n  --- Turn {t.turn_num}{error_flag} ---")

        if t.reasoning_text.strip():
            print(f"  [Reasoning] ({len(t.reasoning_text)} chars)")
            for line in t.reasoning_text.strip().split('\n'):
                print(f"    {line}")

        if t.code.strip():
            print(f"  [Code] ({len(t.code)} chars)")
            for line in t.code.strip().split('\n'):
                print(f"    {line}")

        if t.output.strip():
            print(f"  [Output]{error_flag} ({len(t.output)} chars)")
            out_lines = t.output.strip().split('\n')
            if len(out_lines) > 30:
                for line in out_lines[:15]:
                    print(f"    {line}")
                print(f"    ... [{len(out_lines)-30} more lines] ...")
                for line in out_lines[-15:]:
                    print(f"    {line}")
            else:
                for line in out_lines:
                    print(f"    {line}")


def main():
    logfile = sys.argv[1]
    pid = sys.argv[2]
    attempt_nums = [int(x) for x in sys.argv[3:]] if len(sys.argv) > 3 else None

    problems = parse_log(logfile)
    p = find_problem(problems, pid)

    print(f"Problem: {p.problem_id}")
    print(f"Expected: {p.expected}, Predicted: {p.predicted}")
    if p.problem_text:
        print(f"\nProblem Text:\n  {p.problem_text}")

    if attempt_nums:
        for num in attempt_nums:
            att = [a for a in p.attempts if a.attempt_num == num]
            if att:
                show_attempt_full(p, att[0])
            else:
                print(f"\nAttempt {num} not found!")
    else:
        # Show the correct attempt + 2 wrong ones
        correct = [a for a in p.attempts if a.answer is not None and a.answer == p.expected]
        wrong = [a for a in p.attempts if a.answer is not None and a.answer != p.expected]
        nones = [a for a in p.attempts if a.is_none]

        if correct:
            print(f"\n\n{'#'*80}")
            print(f"  CORRECT ATTEMPT(S)")
            print(f"{'#'*80}")
            for a in correct[:1]:
                show_attempt_full(p, a)

        if wrong:
            print(f"\n\n{'#'*80}")
            print(f"  WRONG ATTEMPT(S) — showing 2")
            print(f"{'#'*80}")
            # Show the most common wrong answer
            from collections import Counter
            wrong_answers = Counter(a.answer for a in wrong)
            most_common_wrong = wrong_answers.most_common(1)[0][0]
            common_wrong = [a for a in wrong if a.answer == most_common_wrong]
            show_attempt_full(p, common_wrong[0])
            # Show a different wrong answer if exists
            other_wrong = [a for a in wrong if a.answer != most_common_wrong]
            if other_wrong:
                show_attempt_full(p, other_wrong[0])

        if nones:
            print(f"\n\n{'#'*80}")
            print(f"  NONE ATTEMPT(S) — showing 1")
            print(f"{'#'*80}")
            show_attempt_full(p, nones[0])


if __name__ == "__main__":
    main()
