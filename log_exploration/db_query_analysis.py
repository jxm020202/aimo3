#!/usr/bin/env python3
"""
Deep analysis of whether attempts queried the SQLite problem DB,
what they found, and how it affected their approach.

Specifically designed for analyzing confidently-wrong problems.

Usage:
    python3 log_exploration/db_query_analysis.py output/v33/diagnostic.log 23586c 673b29
"""

import sys
import re
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def find_problem(problems, pid_prefix):
    """Find problem by ID prefix."""
    for p in problems:
        if p.problem_id.startswith(pid_prefix):
            return p
    return None


def analyze_db_queries(problem, verbose_attempts=None):
    """Analyze all attempts for DB query patterns."""

    db_patterns = [
        r'sqlite3',
        r'problems\.db',
        r'_db',
        r'SELECT\b',
        r'\.execute\(',
        r'cursor',
        r'conn\s*=',
        r'database',
        r'\.fetchone',
        r'\.fetchall',
        r'problem_db',
        r'hint',
        r'approach',
        r'known_answer',
    ]

    pid = problem.problem_id
    print(f"\n{'='*100}")
    print(f"PROBLEM {pid}")
    print(f"Expected: {problem.expected}, Predicted: {problem.predicted}, Correct: {problem.correct}")
    print(f"Total attempts: {len(problem.attempts)}")
    print(f"Votes: {problem.votes}")
    print(f"{'='*100}")

    # Count answers
    answer_counts = {}
    for att in problem.attempts:
        ans = att.answer
        answer_counts[ans] = answer_counts.get(ans, 0) + 1
    print(f"\nAnswer distribution: {answer_counts}")

    # Identify correct attempts
    correct_attempts = [a for a in problem.attempts if a.answer == problem.expected]
    wrong_attempts = [a for a in problem.attempts if a.answer is not None and a.answer != problem.expected]
    none_attempts = [a for a in problem.attempts if a.answer is None]

    print(f"Correct: {len(correct_attempts)} attempts ({[a.attempt_num for a in correct_attempts]})")
    print(f"Wrong: {len(wrong_attempts)} attempts")
    print(f"None: {len(none_attempts)} attempts")

    # Analyze each attempt for DB queries
    print(f"\n{'─'*80}")
    print(f"DB QUERY ANALYSIS")
    print(f"{'─'*80}")

    for att in problem.attempts:
        db_found = False
        db_evidence = []

        for turn in att.turns:
            # Check code cells
            if turn.code:
                for pattern in db_patterns:
                    matches = re.findall(pattern, turn.code, re.IGNORECASE)
                    if matches:
                        db_found = True
                        db_evidence.append(f"Turn {turn.turn_num} CODE: pattern '{pattern}' found ({len(matches)}x)")

            # Check output
            if turn.output:
                for pattern in db_patterns:
                    matches = re.findall(pattern, turn.output, re.IGNORECASE)
                    if matches:
                        db_found = True
                        db_evidence.append(f"Turn {turn.turn_num} OUTPUT: pattern '{pattern}' found ({len(matches)}x)")

        marker = "CORRECT" if att.answer == problem.expected else ("WRONG" if att.answer is not None else "NONE")
        db_marker = " [QUERIED DB]" if db_found else ""
        print(f"\n  Attempt {att.attempt_num:2d} (T={att.temperature}, ans={att.answer}, {marker}){db_marker}")
        if db_found:
            for ev in db_evidence:
                print(f"    {ev}")
        else:
            print(f"    No DB query detected")

    # Detailed turn-by-turn for selected attempts
    if verbose_attempts is None:
        # Auto-select: first 2 correct, first 2 wrong, first 1 none
        verbose_attempts = []
        for a in correct_attempts[:2]:
            verbose_attempts.append(a.attempt_num)
        for a in wrong_attempts[:3]:
            verbose_attempts.append(a.attempt_num)
        for a in none_attempts[:1]:
            verbose_attempts.append(a.attempt_num)
        if not verbose_attempts:
            verbose_attempts = [a.attempt_num for a in problem.attempts[:4]]

    print(f"\n{'─'*80}")
    print(f"DETAILED TURN-BY-TURN FOR ATTEMPTS: {verbose_attempts}")
    print(f"{'─'*80}")

    for att in problem.attempts:
        if att.attempt_num not in verbose_attempts:
            continue

        marker = "CORRECT" if att.answer == problem.expected else ("WRONG" if att.answer is not None else "NONE")
        print(f"\n{'*'*80}")
        print(f"ATTEMPT {att.attempt_num} — Temperature {att.temperature} — Answer: {att.answer} — {marker}")
        print(f"Turns: {len(att.turns)}, Errors: {att.errors}, Time: {att.time_s:.0f}s")
        print(f"{'*'*80}")

        for turn in att.turns:
            print(f"\n  ── Turn {turn.turn_num} ──")

            # Reasoning (truncated)
            if turn.reasoning_text:
                reasoning = turn.reasoning_text.strip()
                # Show first 1500 chars and last 500 chars if long
                if len(reasoning) > 2500:
                    print(f"  REASONING ({len(reasoning)} chars):")
                    print(f"    {reasoning[:1500]}")
                    print(f"    [...{len(reasoning)-2000} chars omitted...]")
                    print(f"    {reasoning[-500:]}")
                else:
                    print(f"  REASONING ({len(reasoning)} chars):")
                    for line in reasoning.split('\n'):
                        print(f"    {line}")

            # Code (full)
            if turn.code:
                code = turn.code.strip()
                print(f"  CODE ({len(code)} chars):")
                for line in code.split('\n'):
                    print(f"    | {line}")

            # Output (truncated)
            if turn.output:
                output = turn.output.strip()
                if len(output) > 2000:
                    print(f"  OUTPUT ({len(output)} chars):")
                    print(f"    {output[:1000]}")
                    print(f"    [...{len(output)-1500} chars omitted...]")
                    print(f"    {output[-500:]}")
                else:
                    print(f"  OUTPUT ({len(output)} chars):")
                    for line in output.split('\n'):
                        print(f"    {line}")

                if turn.is_error:
                    print(f"  ** ERROR **")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 db_query_analysis.py <logfile> <pid1> [pid2] ...")
        sys.exit(1)

    logfile = sys.argv[1]
    pids = sys.argv[2:]

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems")

    for pid_prefix in pids:
        problem = find_problem(problems, pid_prefix)
        if problem is None:
            print(f"\nWARNING: Problem {pid_prefix} not found!")
            # List available problems
            print(f"Available: {[p.problem_id[:6] for p in problems]}")
            continue

        analyze_db_queries(problem)


if __name__ == '__main__':
    main()
