#!/usr/bin/env python3
"""
AIMO3 Reasoning Text Search
==============================
Search all reasoning text across all problems/attempts for a regex pattern.
Shows context: problem ID, attempt, turn, match preview.

Usage:
    python log_exploration/search_reasoning.py <logfile> <regex>
    python log_exploration/search_reasoning.py output/v22/diagnostic.log "overthink"
    python log_exploration/search_reasoning.py output/v22/diagnostic.log "therefore.*answer.*\d+"
    python log_exploration/search_reasoning.py output/v22/diagnostic.log "I made (an error|a mistake)"
    python log_exploration/search_reasoning.py --help

Options:
    --count       Just show count of matches
    --problems    Show which problems matched (no detail)
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
                if not t.reasoning_text:
                    continue
                for m in regex.finditer(t.reasoning_text):
                    start = max(0, m.start() - 60)
                    end = min(len(t.reasoning_text), m.end() + 60)
                    context = t.reasoning_text[start:end].replace('\n', ' ')
                    # Highlight match
                    match_text = m.group(0)
                    matches.append((p.problem_id, a.attempt_num, t.turn_num, context, match_text))
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

    for pid, att, turn, context, match_text in matches[:50]:
        print(f"  {pid} att={att} turn={turn}: ...{context}...")

    if len(matches) > 50:
        print(f"\n  ... showing 50/{len(matches)}. Use --count or --problems for summary.")


if __name__ == '__main__':
    main()
