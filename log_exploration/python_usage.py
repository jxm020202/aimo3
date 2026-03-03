#!/usr/bin/env python3
"""
Python Code Execution Patterns for AIMO3 Solver
=================================================
Analyzes code usage patterns: turns with code vs pure reasoning,
code cell sizes, code reuse, and brute-force vs algebraic detection.

Usage: python3 log_exploration/python_usage.py <logfile>

Options:
    --help    Show this help
"""

import sys
import os
import re
import argparse
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def percentile(vals, p):
    if not vals:
        return 0
    s = sorted(vals)
    k = (len(s) - 1) * p / 100
    f = int(k)
    c = f + 1 if f + 1 < len(s) else f
    return s[f] + (k - f) * (s[c] - s[f])


def print_section(title):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}")


def analyze_code_vs_reasoning(problems):
    """How many turns use Python vs pure reasoning."""
    print_section("CODE vs PURE REASONING TURNS")

    total_turns = 0
    code_turns = 0
    reasoning_only_turns = 0
    code_with_error_turns = 0

    by_outcome = defaultdict(lambda: {"code": 0, "reasoning_only": 0, "total": 0})

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            for t in a.turns:
                total_turns += 1
                by_outcome[outcome]["total"] += 1
                if t.code.strip():
                    code_turns += 1
                    by_outcome[outcome]["code"] += 1
                    if t.is_error:
                        code_with_error_turns += 1
                else:
                    reasoning_only_turns += 1
                    by_outcome[outcome]["reasoning_only"] += 1

    print(f"\n  {'Category':<25} {'Count':>6} {'%':>8}")
    print(f"  {'─' * 25} {'─' * 6} {'─' * 8}")
    print(f"  {'Total turns':<25} {total_turns:>6}")
    print(f"  {'Turns with code':<25} {code_turns:>6} {100*code_turns/total_turns:>7.1f}%")
    print(f"  {'Pure reasoning turns':<25} {reasoning_only_turns:>6} {100*reasoning_only_turns/total_turns:>7.1f}%")
    print(f"  {'Code turns with errors':<25} {code_with_error_turns:>6} {100*code_with_error_turns/code_turns if code_turns else 0:>7.1f}%")

    print(f"\n  By Outcome:")
    print(f"  {'Outcome':<15} {'Code Turns':>12} {'Reasoning':>12} {'Total':>8} {'Code%':>8}")
    print(f"  {'─' * 15} {'─' * 12} {'─' * 12} {'─' * 8} {'─' * 8}")
    for outcome in ["correct", "wrong", "none"]:
        o = by_outcome[outcome]
        code_pct = 100 * o["code"] / o["total"] if o["total"] > 0 else 0
        print(f"  {outcome:<15} {o['code']:>12} {o['reasoning_only']:>12} {o['total']:>8} {code_pct:>7.1f}%")


def analyze_code_calls_distribution(problems):
    """Code calls per attempt distribution."""
    print_section("CODE CALLS PER ATTEMPT")

    correct_calls = []
    wrong_calls = []
    none_calls = []

    for p in problems:
        for a in p.attempts:
            if a.is_none:
                none_calls.append(a.code_calls)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_calls.append(a.code_calls)
            elif a.answer is not None:
                wrong_calls.append(a.code_calls)

    print(f"\n  {'Outcome':<15} {'Count':>6} {'Mean':>8} {'Median':>8} {'Min':>6} {'Max':>6} {'P90':>8}")
    print(f"  {'─' * 15} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 8}")
    for label, calls in [("Correct", correct_calls), ("Wrong", wrong_calls), ("None", none_calls)]:
        if calls:
            print(f"  {label:<15} {len(calls):>6} {mean(calls):>8.1f} {median(calls):>8.0f} {min(calls):>6} {max(calls):>6} {percentile(calls, 90):>8.0f}")

    # Distribution histogram
    print(f"\n  Code Calls Histogram (all attempts):")
    all_calls = correct_calls + wrong_calls + none_calls
    buckets = [(0, 0), (1, 2), (3, 5), (6, 10), (11, 20), (21, 40), (41, 100)]
    labels = ["0", "1-2", "3-5", "6-10", "11-20", "21-40", "41+"]
    for (lo, hi), label in zip(buckets, labels):
        count = sum(1 for c in all_calls if lo <= c <= hi)
        bar = '#' * min(count, 60)
        print(f"  {label:>6} | {bar} ({count})")


def analyze_code_cell_size(problems):
    """Average code cell size (lines, chars)."""
    print_section("CODE CELL SIZE ANALYSIS")

    code_lines = []
    code_chars = []
    by_outcome = defaultdict(lambda: {"lines": [], "chars": []})

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            for t in a.turns:
                if t.code.strip():
                    lines = len(t.code.strip().split('\n'))
                    chars = len(t.code.strip())
                    code_lines.append(lines)
                    code_chars.append(chars)
                    by_outcome[outcome]["lines"].append(lines)
                    by_outcome[outcome]["chars"].append(chars)

    print(f"\n  Overall Code Cell Stats ({len(code_lines)} code cells):")
    print(f"  {'Metric':<20} {'Mean':>8} {'Median':>8} {'P25':>8} {'P75':>8} {'P90':>8} {'Max':>8}")
    print(f"  {'─' * 20} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 8}")
    print(f"  {'Lines':<20} {mean(code_lines):>8.1f} {median(code_lines):>8.0f} {percentile(code_lines, 25):>8.0f} {percentile(code_lines, 75):>8.0f} {percentile(code_lines, 90):>8.0f} {max(code_lines):>8}")
    print(f"  {'Characters':<20} {mean(code_chars):>8.0f} {median(code_chars):>8.0f} {percentile(code_chars, 25):>8.0f} {percentile(code_chars, 75):>8.0f} {percentile(code_chars, 90):>8.0f} {max(code_chars):>8}")

    print(f"\n  By Outcome:")
    print(f"  {'Outcome':<15} {'Avg Lines':>10} {'Avg Chars':>10} {'Cells':>6}")
    print(f"  {'─' * 15} {'─' * 10} {'─' * 10} {'─' * 6}")
    for outcome in ["correct", "wrong", "none"]:
        o = by_outcome[outcome]
        if o["lines"]:
            print(f"  {outcome:<15} {mean(o['lines']):>10.1f} {mean(o['chars']):>10.0f} {len(o['lines']):>6}")


def analyze_code_reuse(problems):
    """Does the model copy-paste from previous turns?"""
    print_section("CODE REUSE ANALYSIS")

    reuse_count = 0
    total_code_pairs = 0
    reuse_by_outcome = defaultdict(int)
    total_by_outcome = defaultdict(int)

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            code_turns = [t for t in a.turns if t.code.strip()]
            for i in range(1, len(code_turns)):
                total_code_pairs += 1
                total_by_outcome[outcome] += 1
                prev = code_turns[i - 1].code.strip()
                curr = code_turns[i].code.strip()
                # Check overlap: if >50% of lines are shared
                prev_lines = set(prev.split('\n'))
                curr_lines = set(curr.split('\n'))
                if prev_lines and curr_lines:
                    overlap = len(prev_lines & curr_lines) / min(len(prev_lines), len(curr_lines))
                    if overlap > 0.5:
                        reuse_count += 1
                        reuse_by_outcome[outcome] += 1

    print(f"\n  Code reuse (>50% line overlap with previous code turn):")
    print(f"  {'Metric':<30} {'Count':>6} {'%':>8}")
    print(f"  {'─' * 30} {'─' * 6} {'─' * 8}")
    print(f"  {'Total consecutive pairs':<30} {total_code_pairs:>6}")
    print(f"  {'Pairs with >50% overlap':<30} {reuse_count:>6} {100*reuse_count/total_code_pairs if total_code_pairs else 0:>7.1f}%")

    print(f"\n  By Outcome:")
    for outcome in ["correct", "wrong", "none"]:
        total = total_by_outcome.get(outcome, 0)
        reuse = reuse_by_outcome.get(outcome, 0)
        if total > 0:
            print(f"    {outcome}: {reuse}/{total} ({100*reuse/total:.0f}%) reuse")


def analyze_strategy_patterns(problems):
    """Brute-force vs algebraic strategy detection."""
    print_section("STRATEGY PATTERN DETECTION")

    # Strategy indicators
    brute_force_patterns = [
        (r'for\s+\w+\s+in\s+range\(.*\d{4,}', 'large range loop'),
        (r'itertools\.(combinations|permutations|product)', 'combinatorial search'),
        (r'brute.?force', 'explicit brute force'),
        (r'for\s+\w+\s+in\s+range.*for\s+\w+\s+in\s+range', 'nested loops'),
        (r'while\s+True', 'infinite loop search'),
    ]
    algebraic_patterns = [
        (r'sympy\.(solve|simplify|factor|expand)', 'symbolic algebra'),
        (r'sympy\.Eq\(', 'equation solving'),
        (r'sympy\.(Matrix|det|eigenvals)', 'linear algebra'),
        (r'modular|mod\s*\(|%\s*\d+', 'modular arithmetic'),
        (r'polynomial|Poly\(', 'polynomial operations'),
    ]
    numerical_patterns = [
        (r'numpy|np\.', 'numpy operations'),
        (r'scipy', 'scipy operations'),
        (r'float\(|decimal|\.0+\d', 'floating point'),
    ]

    strategy_by_outcome = defaultdict(lambda: defaultdict(int))
    total_by_outcome = defaultdict(int)

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code:
                strategy_by_outcome[outcome]["no_code"] += 1
                total_by_outcome[outcome] += 1
                continue

            total_by_outcome[outcome] += 1
            strategies = set()
            for pattern, name in brute_force_patterns:
                if re.search(pattern, all_code, re.IGNORECASE):
                    strategies.add("brute_force")
                    break
            for pattern, name in algebraic_patterns:
                if re.search(pattern, all_code, re.IGNORECASE):
                    strategies.add("algebraic")
                    break
            for pattern, name in numerical_patterns:
                if re.search(pattern, all_code, re.IGNORECASE):
                    strategies.add("numerical")
                    break

            if not strategies:
                strategies.add("basic_python")

            for s in strategies:
                strategy_by_outcome[outcome][s] += 1

    # Display
    all_strategies = set()
    for outcomes in strategy_by_outcome.values():
        all_strategies.update(outcomes.keys())
    all_strategies = sorted(all_strategies)

    print(f"\n  Strategy counts by outcome (an attempt can have multiple strategies):")
    print(f"  {'Strategy':<20} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Total':>6} {'Correct%':>9}")
    print(f"  {'─' * 20} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 9}")

    for s in all_strategies:
        c = strategy_by_outcome["correct"].get(s, 0)
        w = strategy_by_outcome["wrong"].get(s, 0)
        n = strategy_by_outcome["none"].get(s, 0)
        total = c + w + n
        non_none = c + w
        acc = 100 * c / non_none if non_none > 0 else 0
        print(f"  {s:<20} {c:>8} {w:>6} {n:>6} {total:>6} {acc:>8.0f}%")

    # Detailed brute force analysis
    print(f"\n  Brute Force Pattern Detection:")
    for pattern, name in brute_force_patterns:
        count = 0
        for p in problems:
            for a in p.attempts:
                all_code = '\n'.join(t.code for t in a.turns if t.code)
                if re.search(pattern, all_code, re.IGNORECASE):
                    count += 1
                    break
        if count > 0:
            print(f"    {name:<30} found in {count} attempts")


def print_actionable_insights(problems):
    print_section("ACTIONABLE INSIGHTS")

    # Code usage rate
    total_turns = sum(len(a.turns) for p in problems for a in p.attempts)
    code_turns = sum(1 for p in problems for a in p.attempts for t in a.turns if t.code.strip())

    correct_code_calls = [a.code_calls for p in problems for a in p.attempts if not a.is_none and a.answer is not None and p.expected is not None and a.answer == p.expected]
    none_code_calls = [a.code_calls for p in problems for a in p.attempts if a.is_none]

    print(f"""
  1. CODE USAGE: {100*code_turns/total_turns:.0f}% of turns include Python code.
     The model uses code extensively for computation verification.

  2. CODE CALLS: Correct attempts average {mean(correct_code_calls):.1f} code calls,
     None attempts average {mean(none_code_calls):.1f}.
     {'More code calls does not guarantee answers.' if mean(none_code_calls) >= mean(correct_code_calls) else 'More code calls correlates with finding answers.'}

  3. STRATEGY: Most attempts use a mix of brute-force and algebraic approaches.
     Consider prompting the model to prefer algebraic solutions for hard problems
     and brute-force for easier ones where exhaustive search is feasible.

  4. CODE REUSE: High reuse between consecutive turns suggests the model iterates
     on the same approach. Low reuse suggests strategy switching.
     Consider adding a prompt hint: 'If your approach is not working after 3 turns,
     try a completely different method.'
""")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Python code execution patterns in AIMO3 solver logs.",
        usage="python3 log_exploration/python_usage.py <logfile>"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_code_vs_reasoning(problems)
    analyze_code_calls_distribution(problems)
    analyze_code_cell_size(problems)
    analyze_code_reuse(problems)
    analyze_strategy_patterns(problems)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
