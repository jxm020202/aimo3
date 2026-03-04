#!/usr/bin/env python3
"""
Extract correct vs wrong reasoning for specific problems.
Shows what correct attempts did differently from wrong ones.

Usage:
    python3 log_exploration/extract_approaches.py
"""

import sys
import os
import json
import textwrap

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# Problems to analyze
TARGETS = {
    '21fb4e': {'expected': 16, 'logs': ['output/v23/diagnostic.log']},
    '26bee3': {'expected': 108, 'logs': ['output/v23/diagnostic.log', 'output/v31/diagnostic.log']},
    '29714f': {'expected': 297, 'logs': ['output/v23/diagnostic.log', 'output/v31/diagnostic.log']},
    '414a5b': {'expected': 42, 'logs': ['output/v23/diagnostic.log', 'output/v31/diagnostic.log']},
    '673b29': {'expected': 3, 'logs': ['output/v23/diagnostic.log', 'output/v31/diagnostic.log']},
}


def find_problem(problems, pid):
    for p in problems:
        if p.problem_id.startswith(pid):
            return p
    return None


def get_attempt_reasoning(attempt):
    """Get full reasoning text from all turns of an attempt."""
    parts = []
    for turn in attempt.turns:
        if turn.reasoning_text:
            parts.append(f"[Turn {turn.turn_num} Reasoning]\n{turn.reasoning_text}")
        if turn.code:
            parts.append(f"[Turn {turn.turn_num} Code]\n{turn.code}")
        if turn.output:
            label = "ERROR" if turn.is_error else "Output"
            parts.append(f"[Turn {turn.turn_num} {label}]\n{turn.output}")
    return '\n\n'.join(parts)


def truncate_reasoning(text, max_chars=8000):
    """Truncate reasoning to a reasonable length, keeping beginning and end."""
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + f"\n\n... [{len(text) - max_chars} chars truncated] ...\n\n" + text[-half:]


def main():
    # Parse logs once
    print("Parsing v23 log...", file=sys.stderr)
    v23 = parse_log('output/v23/diagnostic.log')
    print("Parsing v31 log...", file=sys.stderr)
    v31 = parse_log('output/v31/diagnostic.log')

    log_data = {
        'output/v23/diagnostic.log': v23,
        'output/v31/diagnostic.log': v31,
    }

    for pid, info in TARGETS.items():
        expected = info['expected']
        print(f"\n{'='*80}")
        print(f"PROBLEM: {pid} (expected={expected})")
        print(f"{'='*80}")

        for logfile in info['logs']:
            problems = log_data[logfile]
            prob = find_problem(problems, pid)
            if not prob:
                print(f"  Not found in {logfile}")
                continue

            version = "v23" if "v23" in logfile else "v31"
            print(f"\n  --- {version} ({logfile}) ---")
            print(f"  Problem text: {prob.problem_text[:300]}...")
            print(f"  Predicted: {prob.predicted}, Expected: {prob.expected}, Correct: {prob.correct}")
            print(f"  Votes: {prob.votes}")

            correct_attempts = []
            wrong_attempts = []
            none_attempts = []

            for a in prob.attempts:
                if a.answer is not None and a.answer == expected:
                    correct_attempts.append(a)
                elif a.answer is not None and a.answer != expected:
                    wrong_attempts.append(a)
                else:
                    none_attempts.append(a)

            print(f"  Correct attempts: {len(correct_attempts)} (nums: {[a.attempt_num for a in correct_attempts]})")
            print(f"  Wrong attempts: {len(wrong_attempts)} (nums: {[a.attempt_num for a in wrong_attempts]}, answers: {[a.answer for a in wrong_attempts]})")
            print(f"  None attempts: {len(none_attempts)}")

            # Print CORRECT attempt reasoning
            for a in correct_attempts[:2]:  # Show up to 2 correct
                reasoning = get_attempt_reasoning(a)
                print(f"\n  === CORRECT Attempt {a.attempt_num} (answer={a.answer}, temp={a.temperature}, turns={len(a.turns)}) ===")
                print(truncate_reasoning(reasoning, 12000))

            # Print WRONG attempt reasoning (show top 2 most common wrong answers)
            wrong_by_answer = {}
            for a in wrong_attempts:
                wrong_by_answer.setdefault(a.answer, []).append(a)

            for ans, attempts in sorted(wrong_by_answer.items(), key=lambda x: -len(x[1]))[:2]:
                a = attempts[0]  # Show first attempt with this answer
                reasoning = get_attempt_reasoning(a)
                print(f"\n  === WRONG Attempt {a.attempt_num} (answer={a.answer}, temp={a.temperature}, turns={len(a.turns)}) ===")
                print(truncate_reasoning(reasoning, 8000))


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
