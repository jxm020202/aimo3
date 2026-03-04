#!/usr/bin/env python3
"""
Deep dive into two specific wrong problems from v31:
  a9dbc8 (expected 15744, voted 15743 — off by one)
  9010d9 (expected 10320, voted 6400 — systematic wrong answer)

Extracts full reasoning text, code, and output for correct and wrong attempts.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def dump_attempt(problem, attempt, label=""):
    """Print full details of a single attempt."""
    print(f"\n{'='*80}")
    print(f"  {label}")
    print(f"  Problem {problem.problem_id} | Attempt #{attempt.attempt_num}")
    print(f"  Answer: {attempt.answer} | Temp: {attempt.temperature} | "
          f"Entropy: {attempt.entropy:.3f} | Code calls: {attempt.code_calls} | "
          f"Errors: {attempt.errors} | Time: {attempt.time_s:.0f}s | Tokens: {attempt.tokens}")
    print(f"{'='*80}")

    for turn in attempt.turns:
        print(f"\n--- Turn {turn.turn_num} ---")
        if turn.reasoning_text:
            text = turn.reasoning_text
            # Show full text, but truncate at 8000 chars if very long
            if len(text) > 8000:
                text = text[:8000] + f"\n... [TRUNCATED, {len(turn.reasoning_text)} chars total]"
            print(f"[REASONING] ({len(turn.reasoning_text)} chars):")
            print(text)
        if turn.code:
            code = turn.code
            if len(code) > 5000:
                code = code[:5000] + f"\n... [TRUNCATED, {len(turn.code)} chars total]"
            print(f"\n[CODE]:")
            print(code)
        if turn.output:
            output = turn.output
            if len(output) > 3000:
                output = output[:3000] + f"\n... [TRUNCATED, {len(turn.output)} chars total]"
            print(f"\n[OUTPUT]:")
            print(output)
        if turn.is_error:
            print(f"[ERROR FLAG SET]")


def analyze_problem(problems, pid, expected):
    """Full analysis of a specific problem."""
    entries = [p for p in problems if p.problem_id == pid]
    if not entries:
        print(f"Problem {pid} not found in log!")
        return

    for entry in entries:
        print(f"\n{'#'*80}")
        print(f"# PROBLEM {pid}")
        print(f"# Expected: {expected} | Predicted: {entry.predicted} | "
              f"Correct: {entry.correct}")
        print(f"# Votes: {dict(entry.votes)}")
        print(f"# Wall time: {entry.wall_time:.0f}s | Attempts: {len(entry.attempts)}")
        print(f"# Problem text: {entry.problem_text[:500]}")
        print(f"{'#'*80}")

        # Categorize attempts
        correct_attempts = [a for a in entry.attempts if a.answer == expected]
        wrong_with_answer = [a for a in entry.attempts if a.answer is not None and a.answer != expected]
        none_attempts = [a for a in entry.attempts if a.answer is None]

        print(f"\n  Correct attempts: {len(correct_attempts)}")
        print(f"  Wrong (with answer): {len(wrong_with_answer)}")
        print(f"  None attempts: {len(none_attempts)}")

        # Show attempt summary table
        print(f"\n  {'Att#':>4} {'Temp':>5} {'Answer':>10} {'Entropy':>8} {'Code':>5} {'Err':>4} {'Time':>6}")
        print(f"  {'-'*4} {'-'*5} {'-'*10} {'-'*8} {'-'*5} {'-'*4} {'-'*6}")
        for a in entry.attempts:
            marker = " [C]" if a.answer == expected else ""
            ans_str = str(a.answer) if a.answer is not None else "None"
            print(f"  {a.attempt_num:>4} {a.temperature:>5.1f} {ans_str:>10}{marker} "
                  f"{a.entropy:>8.3f} {a.code_calls:>5} {a.errors:>4} {a.time_s:>5.0f}s")

        return entry, correct_attempts, wrong_with_answer, none_attempts


def main():
    logfile = sys.argv[1] if len(sys.argv) > 1 else "output/v31/diagnostic.log"

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems\n")

    # ── Problem a9dbc8: Off by one (15743 vs 15744) ──
    print("\n" + "="*80)
    print("PART 1: Problem a9dbc8 — OFF BY ONE (15743 vs 15744)")
    print("="*80)

    result = analyze_problem(problems, "a9dbc8", 15744)
    if result:
        entry, correct, wrong, nones = result

        # Show 1-2 correct attempts in full
        print(f"\n\n{'*'*80}")
        print("CORRECT ATTEMPTS (answer = 15744)")
        print(f"{'*'*80}")
        for a in correct[:2]:
            dump_attempt(entry, a, label="CORRECT ATTEMPT")

        # Show 1-2 wrong attempts that answered 15743 (the off-by-one)
        print(f"\n\n{'*'*80}")
        print("WRONG ATTEMPTS (answer = 15743, the off-by-one)")
        print(f"{'*'*80}")
        off_by_one = [a for a in wrong if a.answer == 15743]
        for a in off_by_one[:2]:
            dump_attempt(entry, a, label="WRONG (OFF-BY-ONE) ATTEMPT")

        # Show any other wrong answers
        other_wrong = [a for a in wrong if a.answer != 15743]
        if other_wrong:
            print(f"\n\n{'*'*80}")
            print("OTHER WRONG ATTEMPTS")
            print(f"{'*'*80}")
            for a in other_wrong[:1]:
                dump_attempt(entry, a, label="OTHER WRONG ATTEMPT")

    # ── Problem 9010d9: 6400 vs 10320 ──
    print("\n\n" + "="*80)
    print("PART 2: Problem 9010d9 — SYSTEMATIC WRONG (6400 vs 10320)")
    print("="*80)

    result = analyze_problem(problems, "9010d9", 10320)
    if result:
        entry, correct, wrong, nones = result

        # Show 1-2 correct attempts in full
        print(f"\n\n{'*'*80}")
        print("CORRECT ATTEMPTS (answer = 10320)")
        print(f"{'*'*80}")
        for a in correct[:2]:
            dump_attempt(entry, a, label="CORRECT ATTEMPT")

        # Show 1-2 wrong attempts that answered 6400
        print(f"\n\n{'*'*80}")
        print("WRONG ATTEMPTS (answer = 6400, the systematic wrong)")
        print(f"{'*'*80}")
        wrong_6400 = [a for a in wrong if a.answer == 6400]
        for a in wrong_6400[:2]:
            dump_attempt(entry, a, label="WRONG (6400) ATTEMPT")

        # Show any other wrong answers
        other_wrong = [a for a in wrong if a.answer != 6400]
        if other_wrong:
            print(f"\n\n{'*'*80}")
            print("OTHER WRONG ATTEMPTS")
            print(f"{'*'*80}")
            for a in other_wrong[:1]:
                dump_attempt(entry, a, label="OTHER WRONG ATTEMPT")


if __name__ == "__main__":
    main()
