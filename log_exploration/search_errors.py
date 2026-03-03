#!/usr/bin/env python3
"""
AIMO3 Error Output Search
============================
Search error output/tracebacks for a regex pattern.
Useful for finding: specific error types, hallucinated APIs, timeout patterns.

Usage:
    python log_exploration/search_errors.py <logfile> <regex>
    python log_exploration/search_errors.py output/v22/diagnostic.log "has no attribute"
    python log_exploration/search_errors.py output/v22/diagnostic.log "timed out"
    python log_exploration/search_errors.py output/v22/diagnostic.log "MemoryError|RecursionError"
    python log_exploration/search_errors.py --help

Options:
    --count       Just show count of matches
    --problems    Show which problems matched (no detail)
    --with-code   Also show the code that caused the error
"""

import sys
import os
import re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    if '--help' in sys.argv or len(sys.argv) < 3:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    pattern = sys.argv[2]
    count_only = '--count' in sys.argv
    problems_only = '--problems' in sys.argv
    with_code = '--with-code' in sys.argv

    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        print(f"Invalid regex: {e}")
        sys.exit(1)

    problems = parse_log(logfile)

    matches = []
    matched_problems = Counter()

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if not t.output or not t.is_error:
                    continue
                for m in regex.finditer(t.output):
                    start = max(0, m.start() - 80)
                    end = min(len(t.output), m.end() + 80)
                    context = t.output[start:end].replace('\n', ' | ')
                    matches.append((p.problem_id, a.attempt_num, t.turn_num, context, t.code if with_code else None))
                    matched_problems[p.problem_id] += 1

    if count_only:
        print(f"{len(matches)} matches across {len(matched_problems)} problems")
        return

    if problems_only:
        print(f"{len(matches)} matches across {len(matched_problems)} problems:")
        for pid, count in matched_problems.most_common():
            print(f"  {pid}: {count} matches")
        return

    print(f"Pattern: /{pattern}/i")
    print(f"Matches: {len(matches)} across {len(matched_problems)} problems\n")

    for pid, att, turn, context, code in matches[:50]:
        print(f"  {pid} att={att} turn={turn}: {context}")
        if code:
            code_lines = code.split('\n')
            print(f"    Code ({len(code_lines)} lines):")
            for line in code_lines[:5]:
                print(f"      {line}")
            if len(code_lines) > 5:
                print(f"      ... ({len(code_lines)} lines total)")
        print()

    if len(matches) > 50:
        print(f"  ... showing 50/{len(matches)}. Use --count or --problems for summary.")


if __name__ == '__main__':
    main()
