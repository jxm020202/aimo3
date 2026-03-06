#!/usr/bin/env python3
"""Simulate multiple voting strategies beyond entropy vs majority.

Strategies: plurality, entropy-weighted, time-weighted, error-penalized,
combined, low-entropy-only, top-k-fastest, code-success-weighted.

Usage: python3 log_exploration/voting_strategies.py <diagnostic.log>
"""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def plurality_vote(attempts):
    votes = Counter(a.answer for a in attempts if a.answer is not None)
    return votes.most_common(1)[0][0] if votes else None


def entropy_weighted_vote(attempts):
    weighted = defaultdict(float)
    for a in attempts:
        if a.answer is not None:
            w = 1.0 / max(a.entropy or 1.0, 1e-9)
            weighted[a.answer] += w
    return max(weighted, key=weighted.get) if weighted else None


def time_weighted_vote(attempts):
    weighted = defaultdict(float)
    for a in attempts:
        if a.answer is not None and a.time_s:
            w = 1.0 / max(a.time_s, 30)
            weighted[a.answer] += w
    return max(weighted, key=weighted.get) if weighted else None


def error_penalized_vote(attempts):
    weighted = defaultdict(float)
    for a in attempts:
        if a.answer is not None:
            n_errors = sum(1 for t in a.turns if t.is_error)
            w = 1.0 / (1.0 + n_errors)
            weighted[a.answer] += w
    return max(weighted, key=weighted.get) if weighted else None


def combined_vote(attempts):
    weighted = defaultdict(float)
    for a in attempts:
        if a.answer is not None:
            entropy_w = 1.0 / max(a.entropy or 1.0, 1e-9)
            n_errors = sum(1 for t in a.turns if t.is_error)
            error_w = 1.0 / (1.0 + n_errors)
            w = entropy_w * error_w
            weighted[a.answer] += w
    return max(weighted, key=weighted.get) if weighted else None


def low_entropy_only(attempts):
    entropies = [(a, a.entropy) for a in attempts if a.answer is not None and a.entropy is not None]
    if not entropies:
        return plurality_vote(attempts)
    entropies.sort(key=lambda x: x[1])
    cutoff = len(entropies) // 2
    filtered = [a for a, _ in entropies[:max(cutoff, 1)]]
    votes = Counter(a.answer for a in filtered)
    return votes.most_common(1)[0][0] if votes else None


def top_k_fastest(attempts, k=16):
    timed = [(a, a.time_s) for a in attempts if a.answer is not None and a.time_s]
    timed.sort(key=lambda x: x[1])
    filtered = [a for a, _ in timed[:k]]
    votes = Counter(a.answer for a in filtered)
    return votes.most_common(1)[0][0] if votes else None


def code_success_weighted(attempts):
    weighted = defaultdict(float)
    for a in attempts:
        if a.answer is not None:
            n_errors = sum(1 for t in a.turns if t.is_error)
            code_calls = a.code_calls or 0
            if code_calls > 0:
                success_rate = max(0, code_calls - n_errors) / code_calls
            else:
                success_rate = 1.0
            w = 0.5 + success_rate  # base 0.5 + up to 1.0
            weighted[a.answer] += w
    return max(weighted, key=weighted.get) if weighted else None


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    n = len(problems)
    baseline = sum(1 for p in problems if p.correct)

    strategies = {
        'Plurality (current)': plurality_vote,
        'Entropy-weighted (1/e)': entropy_weighted_vote,
        'Time-weighted (1/t)': time_weighted_vote,
        'Error-penalized': error_penalized_vote,
        'Combined (ent×err)': combined_vote,
        'Low-entropy-only (p50)': low_entropy_only,
        'Top-16 fastest': lambda a: top_k_fastest(a, 16),
        'Top-8 fastest': lambda a: top_k_fastest(a, 8),
        'Code-success-weighted': code_success_weighted,
    }

    print(f"{'='*72}")
    print(f"  VOTING STRATEGY SIMULATION — {n} problems, baseline {baseline}/{n}")
    print(f"{'='*72}")

    all_results = {}
    for name, fn in strategies.items():
        correct = 0
        flips_gained = []
        flips_lost = []
        for p in problems:
            pred = fn(p.attempts)
            is_correct = pred == p.expected
            if is_correct:
                correct += 1
            if is_correct and not p.correct:
                flips_gained.append(p.problem_id)
            elif not is_correct and p.correct:
                flips_lost.append(p.problem_id)
        all_results[name] = (correct, flips_gained, flips_lost)

    print(f"\n  {'Strategy':35s} {'Score':>8s} {'Delta':>6s} {'Gained':>8s} {'Lost':>6s}")
    print(f"  {'─'*35} {'─'*8} {'─'*6} {'─'*8} {'─'*6}")
    for name, (score, gained, lost) in sorted(all_results.items(), key=lambda x: -x[1][0]):
        delta = score - baseline
        delta_str = f"+{delta}" if delta > 0 else str(delta)
        print(f"  {name:35s} {score:3d}/{n}    {delta_str:>4s} {len(gained):>8d} {len(lost):>6d}")

    # Show flips
    print(f"\n  {'─'*72}")
    print(f"  FLIP DETAILS")
    print(f"  {'─'*72}")
    for name, (score, gained, lost) in all_results.items():
        if gained or lost:
            delta = score - baseline
            print(f"\n  {name} (delta={delta:+d}):")
            for pid in gained:
                p = next(pp for pp in problems if pp.problem_id == pid)
                print(f"    GAINED: {pid} (exp={p.expected})")
            for pid in lost:
                p = next(pp for pp in problems if pp.problem_id == pid)
                print(f"    LOST:   {pid} (exp={p.expected})")

    # Wrong problems: which strategies fix them?
    print(f"\n  {'─'*72}")
    print(f"  WRONG PROBLEMS — FIXABILITY")
    print(f"  {'─'*72}")
    wrong = [p for p in problems if not p.correct]
    for p in wrong:
        fixed_by = []
        for name, fn in strategies.items():
            pred = fn(p.attempts)
            if pred == p.expected:
                fixed_by.append(name)
        tag = f"FIXED by: {', '.join(fixed_by)}" if fixed_by else "NOT fixable by any strategy"
        print(f"  {p.problem_id} (exp={p.expected}, pred={p.predicted}): {tag}")

    print(f"\n{'='*72}")


if __name__ == '__main__':
    main()
