#!/usr/bin/env python3
"""Check numerical relationships between predicted and expected for wrong answers."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def main():
    problems = parse_log(sys.argv[1])

    print("NUMERICAL RELATIONSHIP CHECK:")
    print(f"{'PID':<12} {'Predicted':<10} {'Expected':<10} {'Ratio':<10} {'Diff':<10} {'Notes'}")
    print("-" * 80)

    for p in problems:
        if p.correct or p.expected is None or p.predicted is None:
            continue
        pred = p.predicted
        exp = p.expected
        ratio = pred / exp if exp != 0 else float('inf')
        diff = pred - exp
        notes = []
        if abs(diff) <= 3:
            notes.append('NEAR-MISS')
        if abs(ratio - 2.0) < 0.02:
            notes.append(f'~2x RATIO ({ratio:.4f})')
        if abs(ratio - 0.5) < 0.02:
            notes.append(f'~0.5x RATIO ({ratio:.4f})')
        if abs(ratio - 3.0) < 0.02:
            notes.append(f'~3x RATIO ({ratio:.4f})')
        if abs(ratio - 1.0) < 0.05 and abs(diff) > 3:
            notes.append(f'CLOSE RATIO ({ratio:.4f})')
        if pred == exp * 2:
            notes.append('EXACT 2x')
        if pred == exp * 2 + 1:
            notes.append('2n+1')
        if pred == exp * 2 - 1:
            notes.append('2n-1')
        if exp != 0 and pred % exp == 0:
            notes.append(f'EXACT MULTIPLE ({pred // exp}x)')
        if pred != 0 and exp % pred == 0:
            notes.append(f'EXACT DIVISOR (exp={exp // pred}x pred)')
        # Check if diff is a power of 2
        if abs(diff) > 0 and (abs(diff) & (abs(diff) - 1)) == 0:
            notes.append(f'diff is 2^{abs(diff).bit_length()-1}')

        print(f'{p.problem_id:<12} {pred:<10} {exp:<10} {ratio:<10.4f} {diff:<+10} {", ".join(notes) if notes else "-"}')


if __name__ == "__main__":
    main()
