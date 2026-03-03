#!/usr/bin/env python3
"""
Code Quality Analyzer for AIMO3 Logs
=====================================
Analyzes generated Python code patterns to find what distinguishes successful from failed attempts.

Usage: python3 log_exploration/code_quality.py output/v22/diagnostic.log
"""

import sys
import re
from collections import Counter, defaultdict

sys.path.insert(0, '/Users/intern/Desktop/sideprojects/aimo3')
from log_exploration.log_query import parse_log


def classify_attempt(attempt, problem):
    if attempt.is_none:
        return "none"
    if problem.expected is not None and attempt.answer == problem.expected:
        return "correct"
    return "wrong"


def get_all_code(attempt):
    """Concatenate all code blocks across turns."""
    return "\n".join(t.code for t in attempt.turns if t.code)


def library_analysis(problems):
    """Analyze library usage frequency and correlation with outcomes."""
    print("=" * 80)
    print("LIBRARY USAGE ANALYSIS")
    print("=" * 80)

    # Count libraries from attempt metadata
    lib_counts = {"correct": Counter(), "wrong": Counter(), "none": Counter()}
    cat_totals = {"correct": 0, "wrong": 0, "none": 0}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            cat_totals[cat] += 1
            if a.libraries:
                for lib in a.libraries:
                    lib_counts[cat][lib.strip()] += 1

    # Also scan code blocks for import statements
    import_counts = {"correct": Counter(), "wrong": Counter(), "none": Counter()}
    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            code = get_all_code(a)
            imports = re.findall(r'(?:from|import)\s+([\w.]+)', code)
            for imp in imports:
                top_level = imp.split('.')[0]
                import_counts[cat][top_level] += 1

    print(f"\n  FROM METADATA (attempt.libraries):")
    print(f"  {'Library':<25} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8}")
    print("  " + "-" * 55)

    all_libs = set()
    for c in lib_counts.values():
        all_libs.update(c.keys())
    for lib in sorted(all_libs, key=lambda l: sum(lib_counts[c][l] for c in lib_counts), reverse=True):
        c = lib_counts["correct"][lib]
        w = lib_counts["wrong"][lib]
        n = lib_counts["none"][lib]
        total = c + w + n
        if total >= 3:
            print(f"  {lib:<25} {c:>8} {w:>8} {n:>8} {total:>8}")

    print(f"\n  FROM CODE IMPORTS (scanned code blocks):")
    print(f"  {'Library':<25} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8}")
    print("  " + "-" * 55)

    all_imports = set()
    for c in import_counts.values():
        all_imports.update(c.keys())
    for lib in sorted(all_imports, key=lambda l: sum(import_counts[c][l] for c in import_counts), reverse=True):
        c = import_counts["correct"][lib]
        w = import_counts["wrong"][lib]
        n = import_counts["none"][lib]
        total = c + w + n
        if total >= 5:
            print(f"  {lib:<25} {c:>8} {w:>8} {n:>8} {total:>8}")


def function_usage_analysis(problems):
    """Find most commonly called library functions."""
    print("\n" + "=" * 80)
    print("FUNCTION USAGE ANALYSIS")
    print("=" * 80)

    # Common patterns: sympy.solve, itertools.combinations, etc.
    func_counts = {"correct": Counter(), "wrong": Counter(), "none": Counter()}

    sympy_funcs = [
        r'sympy\.\w+', r'sp\.\w+', r'solve\s*\(', r'simplify\s*\(',
        r'factor\s*\(', r'expand\s*\(', r'symbols?\s*\(', r'Eq\s*\(',
        r'sqrt\s*\(', r'Rational\s*\(', r'Mod\s*\(', r'gcd\s*\(',
        r'lcm\s*\(', r'isprime\s*\(', r'factorint\s*\(', r'nextprime\s*\(',
        r'nsolve\s*\(', r'Matrix\s*\(', r'binomial\s*\(', r'factorial\s*\(',
        r'summation\s*\(', r'product\s*\(', r'limit\s*\(',
    ]

    itertools_funcs = [
        r'combinations\s*\(', r'permutations\s*\(', r'product\s*\(',
        r'combinations_with_replacement\s*\(', r'chain\s*\(',
    ]

    other_funcs = [
        r'range\s*\(', r'print\s*\(', r'len\s*\(', r'sum\s*\(',
        r'min\s*\(', r'max\s*\(', r'sorted\s*\(', r'enumerate\s*\(',
        r'zip\s*\(', r'map\s*\(', r'filter\s*\(', r'set\s*\(',
        r'list\s*\(', r'int\s*\(', r'float\s*\(', r'abs\s*\(',
        r'pow\s*\(', r'divmod\s*\(', r'math\.\w+',
    ]

    all_funcs = sympy_funcs + itertools_funcs + other_funcs

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            code = get_all_code(a)
            for pattern in all_funcs:
                matches = re.findall(pattern, code)
                for m in matches:
                    func_counts[cat][m.rstrip('(')] += 1

    print(f"\n  {'Function':<35} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Err%':>8}")
    print("  " + "-" * 75)

    all_funcs_found = set()
    for c in func_counts.values():
        all_funcs_found.update(c.keys())
    for func in sorted(all_funcs_found,
                       key=lambda f: sum(func_counts[c][f] for c in func_counts), reverse=True)[:30]:
        c = func_counts["correct"][func]
        w = func_counts["wrong"][func]
        n = func_counts["none"][func]
        total = c + w + n
        err_rate = (w + n) / total * 100 if total else 0
        if total >= 5:
            print(f"  {func:<35} {c:>8} {w:>8} {n:>8} {total:>8} {err_rate:>7.1f}%")


def code_length_analysis(problems):
    """Analyze code length per turn and per attempt vs correctness."""
    print("\n" + "=" * 80)
    print("CODE LENGTH ANALYSIS")
    print("=" * 80)

    # Per-attempt total code length
    lengths = {"correct": [], "wrong": [], "none": []}
    per_turn = {"correct": [], "wrong": [], "none": []}
    lines_per_attempt = {"correct": [], "wrong": [], "none": []}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            total_code = get_all_code(a)
            lengths[cat].append(len(total_code))
            lines_per_attempt[cat].append(total_code.count('\n') + 1 if total_code else 0)
            for t in a.turns:
                if t.code:
                    per_turn[cat].append(len(t.code))

    for cat in ["correct", "wrong", "none"]:
        vals = lengths[cat]
        line_vals = lines_per_attempt[cat]
        turn_vals = per_turn[cat]
        if not vals:
            continue
        print(f"\n  {cat.upper()} ({len(vals)} attempts):")
        print(f"    Total code chars:  avg={sum(vals)/len(vals):,.0f}  "
              f"median={sorted(vals)[len(vals)//2]:,.0f}  "
              f"range={min(vals):,}-{max(vals):,}")
        print(f"    Total code lines:  avg={sum(line_vals)/len(line_vals):.0f}  "
              f"median={sorted(line_vals)[len(line_vals)//2]}")
        if turn_vals:
            print(f"    Per-turn chars:    avg={sum(turn_vals)/len(turn_vals):,.0f}  "
                  f"({len(turn_vals)} code turns)")

    # Code length buckets
    print(f"\n  CODE LENGTH BUCKETS (total chars per attempt):")
    print(f"  {'Bucket':<20} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Corr%':>8}")
    print("  " + "-" * 50)
    buckets = [(0, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, 10000), (10000, 999999)]
    labels = ["0-500", "500-1K", "1K-2K", "2K-5K", "5K-10K", "10K+"]
    for (lo, hi), label in zip(buckets, labels):
        c = sum(1 for v in lengths["correct"] if lo <= v < hi)
        w = sum(1 for v in lengths["wrong"] if lo <= v < hi)
        n = sum(1 for v in lengths["none"] if lo <= v < hi)
        total = c + w + n
        if total:
            print(f"  {label:<20} {c:>8} {w:>8} {n:>8} {c/total*100:>7.1f}%")


def coding_strategy_analysis(problems):
    """Classify coding strategies and their success rates."""
    print("\n" + "=" * 80)
    print("CODING STRATEGY ANALYSIS")
    print("=" * 80)

    strategies = {
        "brute_force": [r"for .+ in range\(\d{3,}", r"for .+ in range\(.+\d{3,}", r"brute",
                        r"enumerate.*all", r"exhaustive"],
        "sympy_algebraic": [r"import sympy", r"from sympy", r"sp\.", r"sympy\.",
                            r"solve\s*\(", r"Eq\s*\("],
        "itertools_combinatorial": [r"import itertools", r"from itertools",
                                     r"combinations\(", r"permutations\("],
        "dynamic_programming": [r"dp\[", r"dp =", r"memo", r"@cache", r"@lru_cache",
                                r"dynamic prog"],
        "recursive": [r"def \w+\(.+\):", r"recursion", r"recursive"],
        "number_theory": [r"mod\s", r"% \d+", r"gcd\(", r"lcm\(", r"isprime\(",
                          r"factorint\(", r"sieve"],
        "matrix_linear_algebra": [r"Matrix\(", r"numpy", r"np\.", r"linalg",
                                   r"eigenvalue", r"det\("],
        "search_optimization": [r"binary.search", r"bisect", r"while .+ < .+:",
                                r"lo\s*,\s*hi", r"left\s*,\s*right"],
        "string_parsing": [r"str\(", r"\.split\(", r"\.join\(", r"regex",
                           r"re\.\w+\("],
    }

    print(f"\n  {'Strategy':<30} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Corr%':>8}")
    print("  " + "-" * 70)

    strategy_data = []
    for strat_name, patterns in strategies.items():
        counts = {"correct": 0, "wrong": 0, "none": 0}
        for p in problems:
            for a in p.attempts:
                cat = classify_attempt(a, p)
                code = get_all_code(a)
                if any(re.search(pat, code, re.IGNORECASE) for pat in patterns):
                    counts[cat] += 1
        total = sum(counts.values())
        corr_rate = counts["correct"] / total * 100 if total else 0
        strategy_data.append((strat_name, counts, total, corr_rate))

    strategy_data.sort(key=lambda x: x[2], reverse=True)
    for name, counts, total, corr_rate in strategy_data:
        if total >= 3:
            print(f"  {name:<30} {counts['correct']:>8} {counts['wrong']:>8} "
                  f"{counts['none']:>8} {total:>8} {corr_rate:>7.1f}%")


def code_reuse_analysis(problems):
    """Check if models re-define the same function across turns."""
    print("\n" + "=" * 80)
    print("CODE REUSE / REDEFINITION ANALYSIS")
    print("=" * 80)

    redef_counts = {"correct": [], "wrong": [], "none": []}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            func_defs = Counter()
            for t in a.turns:
                if t.code:
                    defs = re.findall(r'def\s+(\w+)\s*\(', t.code)
                    for d in defs:
                        func_defs[d] += 1

            redefs = sum(1 for c in func_defs.values() if c > 1)
            redef_counts[cat].append(redefs)

    for cat in ["correct", "wrong", "none"]:
        vals = redef_counts[cat]
        if not vals:
            continue
        any_redef = sum(1 for v in vals if v > 0)
        avg = sum(vals) / len(vals)
        print(f"\n  {cat.upper()} ({len(vals)} attempts):")
        print(f"    Attempts with redefined functions: {any_redef}/{len(vals)} ({any_redef/len(vals)*100:.0f}%)")
        print(f"    Avg redefinitions: {avg:.2f}")

    # Most commonly redefined functions
    redef_names = Counter()
    for p in problems:
        for a in p.attempts:
            func_turns = defaultdict(list)
            for t in a.turns:
                if t.code:
                    for d in re.findall(r'def\s+(\w+)\s*\(', t.code):
                        func_turns[d].append(t.turn_num)
            for fname, turns in func_turns.items():
                if len(turns) > 1:
                    redef_names[fname] += 1

    if redef_names:
        print(f"\n  MOST REDEFINED FUNCTION NAMES:")
        for name, count in redef_names.most_common(15):
            print(f"    {name}: {count} times")


def error_prone_patterns(problems):
    """Find code patterns that frequently produce errors."""
    print("\n" + "=" * 80)
    print("ERROR-PRONE CODE PATTERNS")
    print("=" * 80)

    patterns_to_check = {
        "while True": r"while\s+True",
        "recursion": r"def\s+\w+.*:.*(?:return\s+\w+\()",
        "large range": r"range\(\d{5,}\)",
        "nested loops (3+)": r"for .+:\s*\n\s+for .+:\s*\n\s+for",
        "eval()": r"eval\s*\(",
        "exec()": r"exec\s*\(",
        "try/except": r"try\s*:",
        "float division": r"/ (?!/)[\d]",
        "list comprehension": r"\[.+for .+ in .+\]",
        "dictionary comprehension": r"\{.+:.+for .+ in .+\}",
        "lambda": r"lambda\s+",
        "global": r"global\s+",
        "class definition": r"class\s+\w+",
        "assert": r"assert\s+",
        "timeout signal": r"signal\.",
    }

    print(f"\n  {'Pattern':<30} {'Total':>7} {'ErrorTurns':>10} {'ErrRate':>8}")
    print("  " + "-" * 60)

    for pname, pattern in patterns_to_check.items():
        total_turns = 0
        error_turns = 0
        for p in problems:
            for a in p.attempts:
                for t in a.turns:
                    if t.code and re.search(pattern, t.code, re.MULTILINE):
                        total_turns += 1
                        if t.is_error:
                            error_turns += 1
        if total_turns >= 3:
            err_rate = error_turns / total_turns * 100
            print(f"  {pname:<30} {total_turns:>7} {error_turns:>10} {err_rate:>7.1f}%")


def code_evolution_analysis(problems):
    """Track how code changes across turns within an attempt."""
    print("\n" + "=" * 80)
    print("CODE EVOLUTION ACROSS TURNS")
    print("=" * 80)

    # Does code get longer or shorter as turns progress?
    turn_code_lens = defaultdict(lambda: {"correct": [], "wrong": [], "none": []})
    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            for t in a.turns:
                if t.code:
                    turn_code_lens[t.turn_num][cat].append(len(t.code))

    print(f"\n  Average code length by turn number:")
    print(f"  {'Turn':>6} {'Correct':>12} {'Wrong':>12} {'None':>12}")
    print("  " + "-" * 45)
    for turn_num in sorted(turn_code_lens.keys()):
        if turn_num > 10:
            break
        data = turn_code_lens[turn_num]
        c = sum(data["correct"]) / len(data["correct"]) if data["correct"] else 0
        w = sum(data["wrong"]) / len(data["wrong"]) if data["wrong"] else 0
        n = sum(data["none"]) / len(data["none"]) if data["none"] else 0
        c_count = len(data["correct"])
        w_count = len(data["wrong"])
        n_count = len(data["none"])
        print(f"  {turn_num:>6} {c:>7.0f} ({c_count:>3}) {w:>7.0f} ({w_count:>3}) {n:>7.0f} ({n_count:>3})")

    # Error cascades: does an error in turn N predict error in turn N+1?
    print(f"\n  ERROR CASCADE ANALYSIS:")
    cascades = 0
    recoveries = 0
    for p in problems:
        for a in p.attempts:
            for i in range(len(a.turns) - 1):
                if a.turns[i].is_error:
                    if a.turns[i + 1].is_error:
                        cascades += 1
                    else:
                        recoveries += 1
    total = cascades + recoveries
    if total:
        print(f"    After an error turn:")
        print(f"      Next turn also error:    {cascades}/{total} ({cascades/total*100:.0f}%)")
        print(f"      Next turn recovered:     {recoveries}/{total} ({recoveries/total*100:.0f}%)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/code_quality.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    print(f"Loaded {len(problems)} problems with {sum(len(p.attempts) for p in problems)} total attempts")
    total_code_turns = sum(1 for p in problems for a in p.attempts for t in a.turns if t.code)
    print(f"Total code turns: {total_code_turns}")
    print()

    library_analysis(problems)
    function_usage_analysis(problems)
    code_length_analysis(problems)
    coding_strategy_analysis(problems)
    code_reuse_analysis(problems)
    error_prone_patterns(problems)
    code_evolution_analysis(problems)


if __name__ == "__main__":
    main()
