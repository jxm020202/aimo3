#!/usr/bin/env python3
"""
Code Strategy Classification for AIMO3 Solver
================================================
Classifies each attempt's approach (brute-force, algebraic, numerical,
symbolic, etc.), measures success rates per strategy, and detects
strategy switching across turns.

Usage: python3 log_exploration/code_strategy.py <logfile>

Options:
    --verbose   Show per-problem strategy details
    --help      Show this help
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


# Strategy detection rules: (regex_pattern, strategy_name, weight)
STRATEGY_RULES = [
    # Brute force
    (r'for\s+\w+\s+in\s+range\(\d{4,}', 'brute_force', 3),
    (r'for\s+\w+\s+in\s+range\(\d+\):\s*\n\s*for\s+\w+\s+in\s+range', 'brute_force', 2),
    (r'itertools\.(combinations|permutations|product)', 'brute_force', 2),
    (r'while\s+True.*break', 'brute_force', 1),
    (r'brute.?force', 'brute_force', 3),
    (r'exhaustive|enumerate.*all', 'brute_force', 2),

    # Algebraic / symbolic
    (r'sympy\.(solve|simplify|factor|expand|collect|cancel|apart)', 'algebraic', 3),
    (r'sympy\.(Symbol|symbols|Eq|Rational)', 'algebraic', 2),
    (r'sympy\.Poly\(', 'algebraic', 2),
    (r'algebra|algebraic', 'algebraic', 1),

    # Number theory
    (r'sympy\.(factorint|isprime|nextprime|totient|divisors|divisor_count)', 'number_theory', 3),
    (r'sympy\.(gcd|lcm|mod_inverse|primitive_root|is_primitive_root)', 'number_theory', 2),
    (r'math\.gcd|math\.lcm', 'number_theory', 1),
    (r'prime|sieve|euler.*phi|totient|modular', 'number_theory', 1),

    # Combinatorics
    (r'math\.(comb|perm|factorial)', 'combinatorics', 2),
    (r'sympy\.(binomial|Bell|stirling|catalan)', 'combinatorics', 2),
    (r'combinat|binom|choose|pascal', 'combinatorics', 1),

    # Dynamic programming
    (r'dp\[|dp\s*=\s*\[|memo|cache|lru_cache', 'dynamic_programming', 2),
    (r'dynamic.?program|memoiz', 'dynamic_programming', 3),
    (r'@cache|@lru_cache', 'dynamic_programming', 2),

    # Recursive
    (r'def\s+\w+\([^)]*\).*\n(?:.*\n)*?\s+return\s+\w+\(', 'recursive', 1),
    (r'recursion|recursive', 'recursive', 2),

    # Numerical / approximation
    (r'numpy|np\.(array|linspace|arange|zeros|ones)', 'numerical', 2),
    (r'scipy\.(optimize|integrate|interpolate)', 'numerical', 3),
    (r'float|decimal\.Decimal|\.0+\d|1e\d', 'numerical', 1),

    # Matrix / linear algebra
    (r'sympy\.(Matrix|det|eigenvals|rank|nullspace)', 'matrix', 3),
    (r'numpy\.linalg|np\.linalg', 'matrix', 2),
    (r'matrix|determinant|eigen', 'matrix', 1),

    # Geometric
    (r'geometry|triangle|circle|polygon|angle|distance|area|perimeter', 'geometric', 1),
    (r'sympy\.geometry', 'geometric', 3),

    # Graph theory
    (r'graph|vertex|edge|adjacen|networkx|bfs|dfs|dijkstra', 'graph', 2),

    # Constructive / pattern
    (r'pattern|construct|build|generate', 'constructive', 1),
]


def classify_attempt(attempt):
    """Classify an attempt's strategy based on all its code."""
    all_code = '\n'.join(t.code for t in attempt.turns if t.code)
    all_reasoning = '\n'.join(t.reasoning_text for t in attempt.turns if t.reasoning_text)
    combined = all_code + '\n' + all_reasoning

    scores = defaultdict(int)
    for pattern, strategy, weight in STRATEGY_RULES:
        matches = len(re.findall(pattern, combined, re.IGNORECASE | re.MULTILINE))
        if matches > 0:
            scores[strategy] += weight * min(matches, 5)  # Cap contribution

    if not scores:
        if all_code.strip():
            return ["basic_python"]
        return ["pure_reasoning"]

    # Return top strategies (those with score > 0)
    sorted_strategies = sorted(scores.items(), key=lambda x: -x[1])
    # Return primary strategy and any with score >= half of primary
    primary_score = sorted_strategies[0][1]
    return [s for s, score in sorted_strategies if score >= primary_score * 0.5]


def classify_turn(turn):
    """Classify a single turn's strategy."""
    combined = (turn.code or '') + '\n' + (turn.reasoning_text or '')
    scores = defaultdict(int)
    for pattern, strategy, weight in STRATEGY_RULES:
        if re.search(pattern, combined, re.IGNORECASE | re.MULTILINE):
            scores[strategy] += weight
    if not scores:
        return "basic" if turn.code.strip() else "reasoning"
    return max(scores, key=scores.get)


def analyze_strategy_distribution(problems):
    """Classify each attempt and show strategy distribution."""
    print_section("STRATEGY DISTRIBUTION")

    strategy_counter = Counter()
    strategy_by_outcome = defaultdict(lambda: defaultdict(int))
    total_by_outcome = defaultdict(int)

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            strategies = classify_attempt(a)
            total_by_outcome[outcome] += 1
            for s in strategies:
                strategy_counter[s] += 1
                strategy_by_outcome[outcome][s] += 1

    print(f"\n  {'Strategy':<22} {'Count':>6} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Acc%':>7}")
    print(f"  {'─' * 22} {'─' * 6} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 7}")

    for strategy, count in strategy_counter.most_common():
        c = strategy_by_outcome["correct"].get(strategy, 0)
        w = strategy_by_outcome["wrong"].get(strategy, 0)
        n = strategy_by_outcome["none"].get(strategy, 0)
        non_none = c + w
        acc = 100 * c / non_none if non_none > 0 else 0
        print(f"  {strategy:<22} {count:>6} {c:>8} {w:>6} {n:>6} {acc:>6.0f}%")


def analyze_strategy_success(problems):
    """Success rate per strategy."""
    print_section("STRATEGY SUCCESS RATE")

    # Primary strategy per attempt
    primary_by_outcome = defaultdict(lambda: defaultdict(int))

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            strategies = classify_attempt(a)
            primary = strategies[0] if strategies else "unknown"
            primary_by_outcome[outcome][primary] += 1

    all_strategies = set()
    for outcomes in primary_by_outcome.values():
        all_strategies.update(outcomes.keys())

    print(f"\n  Primary strategy accuracy (highest-scoring strategy per attempt):")
    print(f"  {'Strategy':<22} {'Correct':>8} {'Wrong':>6} {'None':>6} {'Total':>6} {'Acc%':>7} {'None%':>7}")
    print(f"  {'─' * 22} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 6} {'─' * 7} {'─' * 7}")

    for strategy in sorted(all_strategies, key=lambda s: -(primary_by_outcome["correct"].get(s, 0) + primary_by_outcome["wrong"].get(s, 0) + primary_by_outcome["none"].get(s, 0))):
        c = primary_by_outcome["correct"].get(strategy, 0)
        w = primary_by_outcome["wrong"].get(strategy, 0)
        n = primary_by_outcome["none"].get(strategy, 0)
        total = c + w + n
        non_none = c + w
        acc = 100 * c / non_none if non_none > 0 else 0
        none_rate = 100 * n / total if total > 0 else 0
        print(f"  {strategy:<22} {c:>8} {w:>6} {n:>6} {total:>6} {acc:>6.0f}% {none_rate:>6.0f}%")


def analyze_strategy_switching(problems):
    """Does the model change strategy across turns within an attempt?"""
    print_section("STRATEGY SWITCHING WITHIN ATTEMPTS")

    switch_counts = []
    switch_by_outcome = defaultdict(list)

    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            turn_strategies = [classify_turn(t) for t in a.turns if t.code.strip() or t.reasoning_text.strip()]
            if len(turn_strategies) < 2:
                continue

            switches = sum(1 for i in range(1, len(turn_strategies)) if turn_strategies[i] != turn_strategies[i-1])
            switch_counts.append(switches)
            switch_by_outcome[outcome].append(switches)

    print(f"\n  Strategy switches per attempt (change of primary strategy between turns):")
    print(f"  {'Outcome':<15} {'Count':>6} {'Mean Switches':>15} {'Median':>8} {'Max':>6}")
    print(f"  {'─' * 15} {'─' * 6} {'─' * 15} {'─' * 8} {'─' * 6}")

    from statistics import median as stat_median
    for outcome in ["correct", "wrong", "none"]:
        vals = switch_by_outcome.get(outcome, [])
        if vals:
            print(f"  {outcome:<15} {len(vals):>6} {mean(vals):>15.1f} {stat_median(vals):>8.0f} {max(vals):>6}")

    if switch_counts:
        print(f"\n  Overall: mean={mean(switch_counts):.1f} switches, max={max(switch_counts)}")

    # Show examples of high-switch attempts
    print(f"\n  High-switch attempts (5+ strategy changes):")
    high_switch = []
    for p in problems:
        for a in p.attempts:
            turn_strategies = [(t.turn_num, classify_turn(t)) for t in a.turns if t.code.strip() or t.reasoning_text.strip()]
            if len(turn_strategies) < 2:
                continue
            switches = sum(1 for i in range(1, len(turn_strategies)) if turn_strategies[i][1] != turn_strategies[i-1][1])
            if switches >= 5:
                ok = "Y" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else ("N" if a.answer is not None else "-")
                high_switch.append((p.problem_id, a.attempt_num, switches, ok, turn_strategies))

    if high_switch:
        for pid, anum, sw, ok, strats in sorted(high_switch, key=lambda x: -x[2])[:10]:
            strat_str = " -> ".join(s for _, s in strats[:10])
            if len(strats) > 10:
                strat_str += f" ... (+{len(strats)-10})"
            print(f"    {pid} Att#{anum} [{ok}] {sw} switches: {strat_str}")
    else:
        print(f"    None found.")


def analyze_per_problem_strategy(problems, verbose):
    """Which strategies are used for which problems."""
    print_section("STRATEGY BY PROBLEM")

    problem_strategies = []
    for p in problems:
        if p.expected is None:
            continue
        all_strategies = Counter()
        for a in p.attempts:
            for s in classify_attempt(a):
                all_strategies[s] += 1
        primary = all_strategies.most_common(1)[0][0] if all_strategies else "unknown"
        ok = "Y" if p.correct else "N"
        problem_strategies.append((p.problem_id, primary, all_strategies, ok, p.wall_time))

    # Group by primary strategy
    by_strategy = defaultdict(list)
    for pid, primary, _, ok, wt in problem_strategies:
        by_strategy[primary].append((pid, ok, wt))

    print(f"\n  {'Strategy':<22} {'Problems':>8} {'Correct':>8} {'Avg Time':>10}")
    print(f"  {'─' * 22} {'─' * 8} {'─' * 8} {'─' * 10}")

    for strategy in sorted(by_strategy, key=lambda s: -len(by_strategy[s])):
        problems_list = by_strategy[strategy]
        correct = sum(1 for _, ok, _ in problems_list if ok == "Y")
        avg_time = mean([wt for _, _, wt in problems_list])
        print(f"  {strategy:<22} {len(problems_list):>8} {correct:>8} {avg_time:>9.0f}s")

    if verbose:
        print(f"\n  Detailed per-problem:")
        for pid, primary, all_strats, ok, wt in sorted(problem_strategies, key=lambda x: x[1]):
            strat_str = ", ".join(f"{s}({c})" for s, c in all_strats.most_common(3))
            print(f"    {pid} [{ok}] {wt:>5.0f}s: {strat_str}")


def print_actionable_insights(problems):
    print_section("ACTIONABLE INSIGHTS")

    # Collect strategy stats
    strategy_acc = defaultdict(lambda: {"correct": 0, "wrong": 0, "none": 0})
    for p in problems:
        for a in p.attempts:
            outcome = "none" if a.is_none else ("correct" if (a.answer is not None and p.expected is not None and a.answer == p.expected) else "wrong")
            strategies = classify_attempt(a)
            primary = strategies[0] if strategies else "unknown"
            strategy_acc[primary][outcome] += 1

    # Best strategy
    best_acc = 0
    best_strategy = "unknown"
    for s, counts in strategy_acc.items():
        non_none = counts["correct"] + counts["wrong"]
        if non_none >= 10:
            acc = counts["correct"] / non_none
            if acc > best_acc:
                best_acc = acc
                best_strategy = s

    print(f"""
  1. BEST STRATEGY: '{best_strategy}' has highest accuracy ({100*best_acc:.0f}%)
     among strategies with 10+ non-None attempts.
     RECOMMENDATION: Prompt the model to prefer this approach when possible.

  2. STRATEGY SWITCHING: Excessive strategy switching (5+ changes per attempt)
     often indicates the model is struggling. Consider adding a prompt hint:
     'Commit to one approach for at least 3 turns before switching.'

  3. BRUTE FORCE: Brute-force approaches work well for competition math when
     the search space is small. For hard problems, algebraic/symbolic approaches
     tend to be more reliable.

  4. NONE REDUCTION: Check which strategies have the highest None rate.
     Strategies that often lead to Nones may benefit from better prompting
     or explicit answer extraction reminders.
""")


def main():
    parser = argparse.ArgumentParser(
        description="Classify solving strategies in AIMO3 solver logs.",
        usage="python3 log_exploration/code_strategy.py <logfile> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("--verbose", action="store_true", help="Show per-problem strategy details")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_strategy_distribution(problems)
    analyze_strategy_success(problems)
    analyze_strategy_switching(problems)
    analyze_per_problem_strategy(problems, args.verbose)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
