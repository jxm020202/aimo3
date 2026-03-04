#!/usr/bin/env python3
"""
Deep dive into WRONG problems where the model overwhelmingly votes wrong
but at least 1 attempt got the right answer.

Shows:
- Problem text (from first attempt's reasoning)
- The correct attempt's full reasoning/code/output
- 2-3 wrong attempts' full reasoning/code/output
- Analysis of the difference

Usage:
    python3 log_exploration/deep_dive_wrong_with_correct.py <logfile> <problem_id>
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def show_attempt(attempt, label=""):
    """Show full turn-by-turn detail for an attempt."""
    print(f"\n{'='*80}")
    print(f"  {label} — Attempt #{attempt.attempt_num}")
    print(f"  Answer: {attempt.answer} | Temp: {attempt.temperature} | "
          f"Turns: {len(attempt.turns)} | Time: {attempt.time_s:.0f}s | "
          f"Errors: {attempt.errors} | Code calls: {attempt.code_calls}")
    print(f"{'='*80}")

    for turn in attempt.turns:
        print(f"\n--- Turn {turn.turn_num} ---")
        if turn.reasoning_text:
            # Show full reasoning but truncate if extremely long
            text = turn.reasoning_text
            if len(text) > 8000:
                text = text[:4000] + f"\n\n... [TRUNCATED {len(turn.reasoning_text)} chars total] ...\n\n" + text[-4000:]
            print(f"[REASONING] ({len(turn.reasoning_text)} chars):")
            print(text)
        if turn.code:
            code = turn.code
            if len(code) > 5000:
                code = code[:2500] + f"\n\n# ... [TRUNCATED {len(turn.code)} chars total] ...\n\n" + code[-2500:]
            print(f"\n[CODE] ({len(turn.code)} chars):")
            print(code)
        if turn.output:
            output = turn.output
            if len(output) > 3000:
                output = output[:1500] + f"\n\n... [TRUNCATED {len(turn.output)} chars total] ...\n\n" + output[-1500:]
            print(f"\n[OUTPUT] ({len(turn.output)} chars):")
            print(output)
        if turn.is_error:
            print("[ERROR FLAG SET]")


def analyze_problem(problems, pid):
    """Deep dive into a specific problem."""
    # Find the problem
    prob = None
    for p in problems:
        if p.problem_id.startswith(pid):
            prob = p
            break

    if not prob:
        print(f"Problem {pid} not found!")
        return

    print(f"\n{'#'*80}")
    print(f"  PROBLEM: {prob.problem_id}")
    print(f"  Expected: {prob.expected} | Predicted (voted): {prob.predicted} | Correct: {prob.correct}")
    print(f"  Wall time: {prob.wall_time:.0f}s | Attempts: {prob.total_attempts}")
    print(f"{'#'*80}")

    # Vote distribution
    from collections import Counter
    votes = Counter()
    correct_attempts = []
    wrong_attempts = []
    none_attempts = []

    for att in prob.attempts:
        if att.answer is None:
            none_attempts.append(att)
            votes[None] += 1
        elif att.answer == prob.expected:
            correct_attempts.append(att)
            votes[att.answer] += 1
        else:
            wrong_attempts.append(att)
            votes[att.answer] += 1

    print(f"\nVote Distribution:")
    for ans, count in votes.most_common():
        marker = " <<<CORRECT" if ans == prob.expected else ""
        print(f"  {ans}: {count} votes{marker}")

    print(f"\nCorrect attempts: {len(correct_attempts)}")
    print(f"Wrong attempts: {len(wrong_attempts)}")
    print(f"None attempts: {len(none_attempts)}")

    # Show ALL correct attempts (there's usually just 1)
    for att in correct_attempts:
        show_attempt(att, f"CORRECT ATTEMPT")

    # Show 3 wrong attempts (pick varied ones)
    shown = 0
    for att in wrong_attempts:
        if shown >= 3:
            break
        show_attempt(att, f"WRONG ATTEMPT (answered {att.answer})")
        shown += 1

    # Summary: what answers appear in code outputs of wrong attempts?
    print(f"\n{'#'*80}")
    print(f"  CODE OUTPUT ANALYSIS")
    print(f"{'#'*80}")
    for att in prob.attempts:
        for turn in att.turns:
            if turn.output and str(prob.expected) in turn.output:
                print(f"  Attempt #{att.attempt_num} Turn {turn.turn_num}: "
                      f"Expected value {prob.expected} appears in output! "
                      f"Final answer: {att.answer}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 deep_dive_wrong_with_correct.py <logfile> <problem_id>")
        sys.exit(1)

    logfile = sys.argv[1]
    pid = sys.argv[2]

    problems = parse_log(logfile)
    analyze_problem(problems, pid)
