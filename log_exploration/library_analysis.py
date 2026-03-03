#!/usr/bin/env python3
"""
Library Usage Analysis for AIMO3 Solver
=========================================
Analyzes which Python libraries are imported, which functions are called,
correlations with correctness, and co-occurrence patterns.

Usage: python3 log_exploration/library_analysis.py <logfile>

Options:
    --top N       Show top N results (default: 20)
    --help        Show this help
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


def print_section(title):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}")


def extract_imports(code):
    """Extract imported libraries from code."""
    imports = set()
    for line in code.split('\n'):
        line = line.strip()
        # import X
        m = re.match(r'^import\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
        # from X import ...
        m = re.match(r'^from\s+(\w+)', line)
        if m:
            imports.add(m.group(1))
        # from X.Y import ...
        m = re.match(r'^from\s+(\w+\.\w+)', line)
        if m:
            imports.add(m.group(1))
    return imports


def extract_function_calls(code, known_modules=None):
    """Extract function calls like module.function() from code."""
    calls = []
    # Match patterns like sympy.factorint(, math.gcd(, etc.
    for m in re.finditer(r'(\w+)\.(\w+)\s*\(', code):
        module = m.group(1)
        func = m.group(2)
        # Skip common non-module prefixes
        if module in ('self', 'cls', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple', 'np', 'pd', 'plt', 'result', 'answer', 'x', 'y', 'n', 'p', 'q', 'r', 's', 'f', 'g'):
            if module == 'np':
                calls.append(('numpy', func))
            elif module == 'pd':
                calls.append(('pandas', func))
            elif module == 'sp':
                calls.append(('sympy', func))
            continue
        calls.append((module, func))
    # Also catch direct function calls from known modules
    if known_modules:
        for m in re.finditer(r'(?<!\w)(\w+)\s*\(', code):
            func = m.group(1)
            if func in known_modules:
                calls.append(('builtin', func))
    return calls


def analyze_library_imports(problems, top_n):
    """Which libraries are imported most."""
    print_section("LIBRARY IMPORT FREQUENCY")

    lib_counter = Counter()
    lib_by_outcome = defaultdict(lambda: {"correct": 0, "wrong": 0, "none": 0, "total": 0})

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code:
                continue
            libs = extract_imports(all_code)
            # Also check the libraries field from the parser
            for lib_str in a.libraries:
                for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                    libs.add(part)

            for lib in libs:
                lib_counter[lib] += 1
                lib_by_outcome[lib]["total"] += 1
                if a.is_none:
                    lib_by_outcome[lib]["none"] += 1
                elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                    lib_by_outcome[lib]["correct"] += 1
                elif a.answer is not None:
                    lib_by_outcome[lib]["wrong"] += 1

    total_attempts = sum(len(p.attempts) for p in problems)
    print(f"\n  {'Library':<20} {'Count':>6} {'%Attempts':>10} {'Correct':>8} {'Wrong':>6} {'None':>6}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 10} {'─' * 8} {'─' * 6} {'─' * 6}")

    for lib, count in lib_counter.most_common(top_n):
        pct = 100 * count / total_attempts
        c = lib_by_outcome[lib]["correct"]
        w = lib_by_outcome[lib]["wrong"]
        n = lib_by_outcome[lib]["none"]
        print(f"  {lib:<20} {count:>6} {pct:>9.1f}% {c:>8} {w:>6} {n:>6}")


def analyze_function_calls(problems, top_n):
    """Which library FUNCTIONS are called most."""
    print_section("FUNCTION CALL FREQUENCY")

    func_counter = Counter()
    func_by_outcome = defaultdict(lambda: {"correct": 0, "wrong": 0, "none": 0})

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            if not all_code:
                continue
            calls = extract_function_calls(all_code)
            seen = set()
            for module, func in calls:
                key = f"{module}.{func}"
                if key not in seen:
                    func_counter[key] += 1
                    seen.add(key)
                    if a.is_none:
                        func_by_outcome[key]["none"] += 1
                    elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                        func_by_outcome[key]["correct"] += 1
                    elif a.answer is not None:
                        func_by_outcome[key]["wrong"] += 1

    print(f"\n  {'Function':<30} {'Count':>6} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Correct%':>9}")
    print(f"  {'─' * 30} {'─' * 6} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 9}")

    for func, count in func_counter.most_common(top_n):
        c = func_by_outcome[func]["correct"]
        w = func_by_outcome[func]["wrong"]
        n = func_by_outcome[func]["none"]
        non_none = c + w
        acc = 100 * c / non_none if non_none > 0 else 0
        print(f"  {func:<30} {count:>6} {c:>8} {w:>6} {n:>6} {acc:>8.0f}%")


def analyze_library_correctness(problems):
    """Which libraries correlate with correct answers vs wrong vs None."""
    print_section("LIBRARY vs CORRECTNESS CORRELATION")

    lib_outcomes = defaultdict(lambda: {"correct": 0, "wrong": 0, "none": 0})
    total_correct = 0
    total_wrong = 0
    total_none = 0

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            libs = extract_imports(all_code)
            for lib_str in a.libraries:
                for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                    libs.add(part)

            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            if outcome == "correct":
                total_correct += 1
            elif outcome == "wrong":
                total_wrong += 1
            else:
                total_none += 1

            for lib in libs:
                lib_outcomes[lib][outcome] += 1

    # Compute "lift" — how much more/less likely to be correct with this library
    base_correct_rate = total_correct / (total_correct + total_wrong) if (total_correct + total_wrong) > 0 else 0

    print(f"\n  Base correct rate (of non-None): {100*base_correct_rate:.1f}%")
    print(f"\n  {'Library':<20} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Correct%':>9} {'Lift':>8} {'None%':>8}")
    print(f"  {'─' * 20} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 9} {'─' * 8} {'─' * 8}")

    for lib in sorted(lib_outcomes, key=lambda l: -(lib_outcomes[l]["correct"] + lib_outcomes[l]["wrong"] + lib_outcomes[l]["none"])):
        o = lib_outcomes[lib]
        total = o["correct"] + o["wrong"] + o["none"]
        if total < 5:
            continue
        non_none = o["correct"] + o["wrong"]
        acc = o["correct"] / non_none if non_none > 0 else 0
        lift = acc / base_correct_rate if base_correct_rate > 0 else 0
        none_rate = 100 * o["none"] / total
        lift_str = f"{lift:.2f}x"
        marker = " +" if lift > 1.1 else (" -" if lift < 0.9 else "")
        print(f"  {lib:<20} {o['correct']:>8} {o['wrong']:>6} {o['none']:>6} {100*acc:>8.0f}% {lift_str:>8}{marker} {none_rate:>7.0f}%")


def analyze_library_failures(problems, top_n):
    """Which library functions FAIL most (cause errors)."""
    print_section("LIBRARY FUNCTIONS THAT FAIL")

    error_funcs = Counter()
    error_libs = Counter()

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error and t.code.strip():
                    calls = extract_function_calls(t.code)
                    seen_libs = set()
                    seen_funcs = set()
                    for module, func in calls:
                        key = f"{module}.{func}"
                        if key not in seen_funcs:
                            error_funcs[key] += 1
                            seen_funcs.add(key)
                        if module not in seen_libs:
                            error_libs[module] += 1
                            seen_libs.add(module)

    print(f"\n  Libraries present in error turns:")
    print(f"  {'Library':<20} {'Error Turns':>12}")
    print(f"  {'─' * 20} {'─' * 12}")
    for lib, count in error_libs.most_common(top_n):
        print(f"  {lib:<20} {count:>12}")

    print(f"\n  Functions present in error turns:")
    print(f"  {'Function':<30} {'Error Turns':>12}")
    print(f"  {'─' * 30} {'─' * 12}")
    for func, count in error_funcs.most_common(top_n):
        print(f"  {func:<30} {count:>12}")


def analyze_cooccurrence(problems, top_n):
    """Which libraries are used together."""
    print_section("LIBRARY CO-OCCURRENCE")

    pair_counter = Counter()

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            libs = sorted(extract_imports(all_code))
            for lib_str in a.libraries:
                for part in re.findall(r'(?:import|from)\s+(\w+)', lib_str):
                    if part not in libs:
                        libs.append(part)
            libs = sorted(set(libs))

            for i in range(len(libs)):
                for j in range(i + 1, len(libs)):
                    pair_counter[(libs[i], libs[j])] += 1

    print(f"\n  {'Library Pair':<35} {'Count':>6}")
    print(f"  {'─' * 35} {'─' * 6}")
    for (l1, l2), count in pair_counter.most_common(top_n):
        print(f"  {l1} + {l2:<25} {count:>6}")


def print_actionable_insights(problems):
    print_section("ACTIONABLE INSIGHTS")

    # Count sympy usage
    sympy_correct = 0
    sympy_wrong = 0
    sympy_none = 0
    non_sympy_correct = 0
    non_sympy_wrong = 0

    for p in problems:
        for a in p.attempts:
            all_code = '\n'.join(t.code for t in a.turns if t.code)
            libs = extract_imports(all_code)
            uses_sympy = 'sympy' in libs

            if a.is_none:
                if uses_sympy:
                    sympy_none += 1
                continue
            is_correct = a.answer is not None and p.expected is not None and a.answer == p.expected
            if uses_sympy:
                if is_correct:
                    sympy_correct += 1
                else:
                    sympy_wrong += 1
            else:
                if is_correct:
                    non_sympy_correct += 1
                else:
                    non_sympy_wrong += 1

    sympy_total = sympy_correct + sympy_wrong
    non_sympy_total = non_sympy_correct + non_sympy_wrong

    insights = []

    if sympy_total > 0 and non_sympy_total > 0:
        sympy_acc = 100 * sympy_correct / sympy_total
        non_sympy_acc = 100 * non_sympy_correct / non_sympy_total
        insights.append(
            f"1. SYMPY USAGE: {sympy_acc:.0f}% accuracy with sympy vs {non_sympy_acc:.0f}% without. "
            f"Sympy Nones: {sympy_none}. "
            f"{'Sympy helps.' if sympy_acc > non_sympy_acc else 'Sympy does not improve accuracy.'}"
        )

    insights.append(
        f"2. LIBRARY DIVERSITY: Math competition problems primarily use math, sympy, itertools, "
        f"fractions. Heavy library usage (many imports) may indicate the model is searching "
        f"for the right tool rather than solving directly."
    )

    insights.append(
        f"3. ERROR CORRELATION: Check which library functions appear in error turns. "
        f"If a specific function consistently fails, consider adding it to the prompt "
        f"blacklist or providing usage hints."
    )

    for insight in insights:
        print(f"\n  {insight}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze library usage patterns in AIMO3 solver logs.",
        usage="python3 log_exploration/library_analysis.py <logfile> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("--top", type=int, default=20, help="Number of top results to show (default: 20)")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_library_imports(problems, args.top)
    analyze_function_calls(problems, args.top)
    analyze_library_correctness(problems)
    analyze_library_failures(problems, args.top)
    analyze_cooccurrence(problems, args.top)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
