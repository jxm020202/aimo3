#!/usr/bin/env python3
"""
AIMO3 Code Block Search
=========================
Search all generated code blocks for a regex pattern.
Useful for finding: specific library calls, code patterns, hallucinated APIs.

Usage:
    python log_exploration/search_code.py <logfile> <regex>
    python log_exploration/search_code.py output/v22/diagnostic.log "sympy\.crt"
    python log_exploration/search_code.py output/v22/diagnostic.log "brute.force|enumerate"
    python log_exploration/search_code.py output/v22/diagnostic.log "import (scipy|networkx)"
    python log_exploration/search_code.py --help

Options:
    --count       Just show count of matches
    --problems    Show which problems matched (no detail)
    --errors-only Only search code blocks that produced errors
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
    errors_only = '--errors-only' in sys.argv

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
                if not t.code:
                    continue
                if errors_only and not t.is_error:
                    continue
                for m in regex.finditer(t.code):
                    # Show the matching line plus context
                    lines = t.code.split('\n')
                    match_pos = m.start()
                    char_count = 0
                    for line_num, line in enumerate(lines):
                        if char_count + len(line) + 1 > match_pos:
                            # Found the line
                            start_line = max(0, line_num - 1)
                            end_line = min(len(lines), line_num + 2)
                            context = '\n'.join(f'    {lines[i]}' for i in range(start_line, end_line))
                            matches.append((p.problem_id, a.attempt_num, t.turn_num, t.is_error, context))
                            matched_problems[p.problem_id] += 1
                            break
                        char_count += len(line) + 1

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

    for pid, att, turn, is_err, context in matches[:50]:
        err_marker = " [ERROR]" if is_err else ""
        print(f"  {pid} att={att} turn={turn}{err_marker}:")
        print(f"{context}")
        print()

    if len(matches) > 50:
        print(f"  ... showing 50/{len(matches)}. Use --count or --problems for summary.")


if __name__ == '__main__':
    main()
