#!/usr/bin/env python3
"""
Vboxed vs Boxed Checkpoint Analysis
====================================
Checks if vboxed checkpoints ever captured answers that the final boxed extraction missed.
Looks at the raw log for checkpoint patterns.
"""

import sys
import os
import re
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 vboxed_vs_boxed.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    # Read raw log to find vboxed/boxed patterns
    with open(logfile, 'r', errors='replace') as f:
        content = f.read()

    print("=" * 80)
    print("  VBOXED vs BOXED CHECKPOINT ANALYSIS")
    print("=" * 80)
    print()

    # Look for checkpoint-related patterns in the log
    vboxed_pattern = re.compile(r'\\vboxed\{(\d+)\}')
    boxed_pattern = re.compile(r'\\boxed\{(\d+)\}')
    checkpoint_pattern = re.compile(r'[Cc]heckpoint.*?(\d+)')
    vboxed_checkpoint_pattern = re.compile(r'vboxed.*?checkpoint|checkpoint.*?vboxed', re.IGNORECASE)

    # Search in reasoning text of all attempts
    vboxed_in_reasoning = 0
    boxed_in_reasoning = 0
    vboxed_only_correct = 0
    boxed_only_correct = 0
    both_correct = 0

    problems_with_vboxed = []

    for p in problems:
        for a in p.attempts:
            all_text = " ".join(t.reasoning_text for t in a.turns)
            all_code_output = " ".join(t.output for t in a.turns)
            combined = all_text + " " + all_code_output

            vboxed_matches = vboxed_pattern.findall(combined)
            boxed_matches = boxed_pattern.findall(combined)

            if vboxed_matches:
                vboxed_in_reasoning += 1
                vboxed_ints = set(int(v) for v in vboxed_matches)
                boxed_ints = set(int(v) for v in boxed_matches)

                if p.expected in vboxed_ints and p.expected not in boxed_ints:
                    vboxed_only_correct += 1
                    problems_with_vboxed.append((p, a, vboxed_ints, boxed_ints))
                elif p.expected in vboxed_ints and p.expected in boxed_ints:
                    both_correct += 1
                elif p.expected in boxed_ints and p.expected not in vboxed_ints:
                    boxed_only_correct += 1

            if boxed_matches:
                boxed_in_reasoning += 1

    print(f"  Attempts with \\vboxed in text: {vboxed_in_reasoning}")
    print(f"  Attempts with \\boxed in text:  {boxed_in_reasoning}")
    print()
    print(f"  Correct in vboxed ONLY (not boxed): {vboxed_only_correct}")
    print(f"  Correct in boxed ONLY (not vboxed): {boxed_only_correct}")
    print(f"  Correct in BOTH:                    {both_correct}")
    print()

    if problems_with_vboxed:
        print("  VBOXED-ONLY CORRECT CASES (would be rescued by vboxed extraction):")
        for p, a, vb, bb in problems_with_vboxed:
            print(f"    Problem {p.problem_id} attempt {a.attempt_num}: vboxed={vb}, boxed={bb}, expected={p.expected}")
    else:
        print("  No cases where vboxed had correct answer that boxed missed.")

    # ── Also: look for answer patterns in reasoning of None attempts ──
    print()
    print("=" * 80)
    print("  ANSWERS HIDING IN NONE ATTEMPTS")
    print("  (Correct answer appears in reasoning/code but was not extracted)")
    print("=" * 80)
    print()

    rescued = 0
    rescue_details = []
    for p in problems:
        for a in p.attempts:
            if a.answer is not None:
                continue
            if p.expected is None:
                continue

            # Check if expected answer appears in reasoning or code output
            all_text = " ".join(t.reasoning_text for t in a.turns)
            all_output = " ".join(t.output for t in a.turns)

            expected_str = str(p.expected)

            # Look for boxed{expected}
            in_boxed = f"\\boxed{{{expected_str}}}" in all_text
            in_vboxed = f"\\vboxed{{{expected_str}}}" in all_text

            # Look for "answer is expected" or "= expected" patterns
            answer_pattern = re.search(
                rf'(?:answer\s*(?:is|=|:)\s*{re.escape(expected_str)}|'
                rf'result\s*(?:is|=|:)\s*{re.escape(expected_str)}|'
                rf'\\boxed\{{{re.escape(expected_str)}\}}|'
                rf'\\vboxed\{{{re.escape(expected_str)}\}})',
                all_text, re.IGNORECASE
            )

            # Look for bare expected number in last output line
            in_output = False
            for t in reversed(a.turns):
                if t.output.strip():
                    last_line = t.output.strip().split('\n')[-1].strip()
                    if last_line == expected_str:
                        in_output = True
                    break

            if in_boxed or in_vboxed or answer_pattern or in_output:
                rescued += 1
                how = []
                if in_boxed: how.append("boxed")
                if in_vboxed: how.append("vboxed")
                if answer_pattern and not in_boxed and not in_vboxed: how.append("text_pattern")
                if in_output: how.append("output")
                rescue_details.append((p, a, how))

    print(f"  None attempts where correct answer appears: {rescued}/{sum(1 for p in problems for a in p.attempts if a.answer is None)}")
    print()

    # Group by problem
    by_problem = defaultdict(list)
    for p, a, how in rescue_details:
        by_problem[p.problem_id].append((a, how))

    for pid in sorted(by_problem.keys()):
        items = by_problem[pid]
        p = next(p for p in problems if p.problem_id == pid)
        print(f"  Problem {pid} (expected={p.expected}, correct={p.correct})")
        for a, how in items:
            print(f"    Attempt {a.attempt_num}: found via {', '.join(how)} (current answer: {a.answer})")

    # ── Impact analysis ──
    print()
    print("=" * 80)
    print("  IMPACT: IF WE RESCUED ALL EXTRACTABLE NONE ANSWERS")
    print("=" * 80)
    print()

    from collections import Counter
    score_current = sum(1 for p in problems if p.correct)
    flipped = 0
    for p in problems:
        if p.correct:
            continue
        # Count current votes + rescued votes
        votes = Counter()
        for a in p.attempts:
            if a.answer is not None:
                votes[a.answer] += 1
        # Add rescued nones
        rescued_for_this = sum(1 for pp, aa, hh in rescue_details if pp.problem_id == p.problem_id)
        if p.expected:
            votes[p.expected] = votes.get(p.expected, 0) + rescued_for_this
        if votes:
            winner = votes.most_common(1)[0][0]
            if winner == p.expected:
                flipped += 1
                print(f"  Would FLIP: {p.problem_id} (expected={p.expected})")
                print(f"    Current votes: {dict(Counter(a.answer for a in p.attempts if a.answer is not None).most_common())}")
                print(f"    + {rescued_for_this} rescued None attempts")
                new_votes = dict(votes.most_common())
                print(f"    New votes: {new_votes}")
                print()

    print(f"  Current score: {score_current}/{len(problems)}")
    print(f"  Would flip: {flipped} problems")
    print(f"  Potential score: {score_current + flipped}/{len(problems)}")


if __name__ == "__main__":
    main()
