#!/usr/bin/env python3
"""
Dump all attempts for a problem to a file for agent analysis.

Usage:
    python3 log_exploration/dump_all_attempts.py <logfile> <problem_id> [output_file]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log


def dump_all_attempts(logfile, problem_id, output_file=None):
    problems = parse_log(logfile)

    # Find the problem
    target = None
    for p in problems:
        if p.problem_id.startswith(problem_id):
            target = p
            break

    if not target:
        print(f"Problem {problem_id} not found")
        sys.exit(1)

    lines = []
    lines.append(f"{'='*80}")
    lines.append(f"PROBLEM: {target.problem_id}")
    lines.append(f"Expected: {target.expected}")
    lines.append(f"Predicted: {target.predicted}")
    lines.append(f"Correct: {target.predicted == target.expected}")
    lines.append(f"Total attempts: {len(target.attempts)}")
    lines.append(f"{'='*80}\n")

    # Vote summary
    from collections import Counter
    votes = Counter()
    for a in target.attempts:
        if a.answer is not None:
            votes[a.answer] += 1
    lines.append(f"VOTE DISTRIBUTION: {dict(votes.most_common())}")
    lines.append(f"None count: {sum(1 for a in target.attempts if a.answer is None)}\n")

    for a in target.attempts:
        lines.append(f"\n{'─'*80}")
        lines.append(f"ATTEMPT {a.attempt_num} | answer={a.answer} | expected={target.expected} | "
                     f"{'CORRECT' if a.answer == target.expected else 'WRONG' if a.answer is not None else 'NONE'}")
        lines.append(f"temp={getattr(a, 'temperature', '?')} | entropy={a.entropy} | "
                     f"time={getattr(a, 'time_s', 0):.1f}s | tokens={a.tokens} | code_calls={getattr(a, 'code_calls', 0)} | errors={a.errors}")
        lines.append(f"{'─'*80}")

        for t in a.turns:
            # Print reasoning
            if hasattr(t, 'reasoning_text') and t.reasoning_text:
                text = t.reasoning_text.strip()
                if text:
                    lines.append(f"\n[REASONING] (turn {t.turn_num}):")
                    lines.append(text)

            # Print code
            if hasattr(t, 'code') and t.code:
                text = t.code.strip()
                if text:
                    lines.append(f"\n[CODE] (turn {t.turn_num}):")
                    lines.append(text)

            # Print output
            if hasattr(t, 'output') and t.output:
                text = t.output.strip()
                if text:
                    # Truncate very long outputs
                    if len(text) > 2000:
                        text = text[:2000] + f"\n... [TRUNCATED {len(text)} chars total]"
                    lines.append(f"\n[OUTPUT] (turn {t.turn_num}):")
                    lines.append(text)

            # Print error (output with is_error flag)
            if hasattr(t, 'is_error') and t.is_error and hasattr(t, 'output') and t.output:
                text = t.output.strip()
                if text:
                    if len(text) > 1000:
                        text = text[:1000] + f"\n... [TRUNCATED]"
                    lines.append(f"\n[ERROR] (turn {t.turn_num}):")
                    lines.append(text)

    content = '\n'.join(lines)

    if output_file:
        with open(output_file, 'w') as f:
            f.write(content)
        print(f"Wrote {len(lines)} lines to {output_file}")
    else:
        print(content)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <logfile> <problem_id> [output_file]")
        sys.exit(1)

    logfile = sys.argv[1]
    problem_id = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    dump_all_attempts(logfile, problem_id, output_file)
