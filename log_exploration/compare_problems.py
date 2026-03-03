#!/usr/bin/env python3
"""
Compare Problems — Side-by-side comparison of two problems.
=============================================================
Shows stats, votes, attempt patterns, and highlights differences.
Useful for understanding why one problem was solved and another wasn't.

Usage:
    python3 log_exploration/compare_problems.py <logfile> <pid1> <pid2>
    python3 log_exploration/compare_problems.py output/v22/diagnostic.log 86e8e5 76aef9

Options:
    --all       Compare all problems against each other (summary matrix)
    --correct-vs-wrong   Compare all correct vs all wrong problems (aggregate)
    --help      Show this help
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def fmt_time(s):
    if s >= 3600:
        return f"{s/3600:.1f}h"
    if s >= 60:
        return f"{s/60:.1f}m"
    return f"{s:.1f}s"


def fmt_tokens(n):
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def find_problem(problems, pid):
    """Find a problem by ID (prefix match)."""
    exact = [p for p in problems if p.problem_id == pid]
    if exact:
        return exact[0]
    prefix = [p for p in problems if p.problem_id.startswith(pid)]
    if len(prefix) == 1:
        return prefix[0]
    if len(prefix) > 1:
        print(f"  Ambiguous prefix '{pid}'. Matches: {', '.join(p.problem_id for p in prefix)}")
        sys.exit(1)
    print(f"  Problem '{pid}' not found.")
    sys.exit(1)


def problem_stats(p):
    """Extract key stats from a problem."""
    nones = sum(1 for a in p.attempts if a.is_none)
    answered = len(p.attempts) - nones
    correct_att = sum(1 for a in p.attempts if a.answer is not None and a.answer == p.expected) if p.expected else 0
    wrong_att = answered - correct_att
    total_tokens = sum(a.tokens for a in p.attempts)
    total_errors = sum(a.errors for a in p.attempts)
    total_code_calls = sum(a.code_calls for a in p.attempts)
    unique_answers = len(set(a.answer for a in p.attempts if a.answer is not None))
    avg_turns = mean([len(a.turns) for a in p.attempts])
    avg_entropy = mean([a.entropy for a in p.attempts])
    avg_reasoning = mean([sum(len(t.reasoning_text) for t in a.turns) for a in p.attempts])

    # First correct attempt
    first_correct = None
    if p.expected:
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer == p.expected:
                first_correct = a.attempt_num
                break

    return {
        "status": "CORRECT" if p.correct else "WRONG",
        "predicted": p.predicted,
        "expected": p.expected,
        "wall_time": p.wall_time,
        "budget": p.budget,
        "budget_util": f"{100*p.wall_time/p.budget:.1f}%" if p.budget > 0 else "N/A",
        "early_stop": "Yes" if p.early_stop else "No",
        "attempts": len(p.attempts),
        "answered": answered,
        "nones": nones,
        "none_rate": f"{100*nones/len(p.attempts):.0f}%" if p.attempts else "N/A",
        "correct_att": correct_att,
        "wrong_att": wrong_att,
        "unique_answers": unique_answers,
        "tokens": total_tokens,
        "errors": total_errors,
        "code_calls": total_code_calls,
        "avg_turns": avg_turns,
        "avg_entropy": avg_entropy,
        "avg_reasoning": avg_reasoning,
        "first_correct": first_correct,
        "batch": p.batch_name,
        "votes": p.votes,
    }


def compare_two(problems_list, pid1, pid2):
    """Side-by-side comparison of two problems."""
    p1 = find_problem(problems_list, pid1)
    p2 = find_problem(problems_list, pid2)

    s1 = problem_stats(p1)
    s2 = problem_stats(p2)

    print(f"\n{'=' * 72}")
    print(f"  PROBLEM COMPARISON: {p1.problem_id} vs {p2.problem_id}")
    print(f"{'=' * 72}")

    # Side-by-side stats
    w = 18  # column width
    print(f"\n  {'Metric':<22} {p1.problem_id:>{w}} {p2.problem_id:>{w}} {'Delta':>{w}}")
    print(f"  {'─' * 22} {'─' * w} {'─' * w} {'─' * w}")

    rows = [
        ("Status", s1["status"], s2["status"], ""),
        ("Batch", s1["batch"][:w], s2["batch"][:w], ""),
        ("Predicted", str(s1["predicted"]), str(s2["predicted"]), ""),
        ("Expected", str(s1["expected"]), str(s2["expected"]), ""),
        ("Wall Time", fmt_time(s1["wall_time"]), fmt_time(s2["wall_time"]),
         f"{'+' if s1['wall_time'] > s2['wall_time'] else ''}{fmt_time(s1['wall_time'] - s2['wall_time'])}"),
        ("Budget Util", s1["budget_util"], s2["budget_util"], ""),
        ("Early Stop", s1["early_stop"], s2["early_stop"], ""),
        ("Attempts", str(s1["attempts"]), str(s2["attempts"]), ""),
        ("Answered", str(s1["answered"]), str(s2["answered"]),
         f"{s1['answered'] - s2['answered']:+d}"),
        ("Nones", f"{s1['nones']} ({s1['none_rate']})", f"{s2['nones']} ({s2['none_rate']})", ""),
        ("Correct Attempts", str(s1["correct_att"]), str(s2["correct_att"]),
         f"{s1['correct_att'] - s2['correct_att']:+d}"),
        ("Wrong Attempts", str(s1["wrong_att"]), str(s2["wrong_att"]),
         f"{s1['wrong_att'] - s2['wrong_att']:+d}"),
        ("Unique Answers", str(s1["unique_answers"]), str(s2["unique_answers"]),
         f"{s1['unique_answers'] - s2['unique_answers']:+d}"),
        ("Tokens", fmt_tokens(s1["tokens"]), fmt_tokens(s2["tokens"]),
         f"{'+' if s1['tokens'] > s2['tokens'] else ''}{fmt_tokens(s1['tokens'] - s2['tokens'])}"),
        ("Errors", str(s1["errors"]), str(s2["errors"]),
         f"{s1['errors'] - s2['errors']:+d}"),
        ("Code Calls", str(s1["code_calls"]), str(s2["code_calls"]),
         f"{s1['code_calls'] - s2['code_calls']:+d}"),
        ("Avg Turns", f"{s1['avg_turns']:.1f}", f"{s2['avg_turns']:.1f}",
         f"{s1['avg_turns'] - s2['avg_turns']:+.1f}"),
        ("Avg Entropy", f"{s1['avg_entropy']:.3f}", f"{s2['avg_entropy']:.3f}",
         f"{s1['avg_entropy'] - s2['avg_entropy']:+.3f}"),
        ("Avg Reasoning", f"{s1['avg_reasoning']:.0f} ch", f"{s2['avg_reasoning']:.0f} ch", ""),
        ("1st Correct At", str(s1["first_correct"] or "Never"), str(s2["first_correct"] or "Never"), ""),
    ]

    for metric, v1, v2, delta in rows:
        # Highlight differences
        marker = ""
        if v1 != v2 and metric in ("Status", "Early Stop"):
            marker = " <--"
        print(f"  {metric:<22} {v1:>{w}} {v2:>{w}} {delta:>{w}}{marker}")

    # Votes comparison
    print(f"\n  Votes:")
    all_answers = set(list(s1["votes"].keys()) + list(s2["votes"].keys()))
    print(f"  {'Answer':>12} {p1.problem_id:>12} {p2.problem_id:>12}")
    print(f"  {'─' * 12} {'─' * 12} {'─' * 12}")
    for ans in sorted(all_answers):
        v1 = s1["votes"].get(ans, 0)
        v2 = s2["votes"].get(ans, 0)
        mark1 = " *" if ans == p1.expected else ""
        mark2 = " *" if ans == p2.expected else ""
        print(f"  {ans:>12} {v1:>10}{mark1} {v2:>10}{mark2}")
    print(f"  (* = expected answer)")

    # Attempt-by-attempt comparison
    print(f"\n  {'─' * 60}")
    print(f"  ATTEMPT-BY-ATTEMPT COMPARISON")
    print(f"  {'─' * 60}")
    max_att = max(len(p1.attempts), len(p2.attempts))
    print(f"  {'#':>3} {'Ans (P1)':>10} {'OK':>3} {'Time':>6} {'Ent':>6}  |  {'Ans (P2)':>10} {'OK':>3} {'Time':>6} {'Ent':>6}")
    print(f"  {'─'*3} {'─'*10} {'─'*3} {'─'*6} {'─'*6}  |  {'─'*10} {'─'*3} {'─'*6} {'─'*6}")

    atts1 = {a.attempt_num: a for a in p1.attempts}
    atts2 = {a.attempt_num: a for a in p2.attempts}
    for n in range(1, max_att + 1):
        a1 = atts1.get(n)
        a2 = atts2.get(n)

        if a1:
            ans1 = str(a1.answer)[:10] if a1.answer is not None else "None"
            ok1 = "Y" if a1.answer == p1.expected else ("N" if a1.answer is not None else "-")
            t1 = fmt_time(a1.time_s)
            e1 = f"{a1.entropy:.3f}"
        else:
            ans1 = ok1 = t1 = e1 = ""

        if a2:
            ans2 = str(a2.answer)[:10] if a2.answer is not None else "None"
            ok2 = "Y" if a2.answer == p2.expected else ("N" if a2.answer is not None else "-")
            t2 = fmt_time(a2.time_s)
            e2 = f"{a2.entropy:.3f}"
        else:
            ans2 = ok2 = t2 = e2 = ""

        print(f"  {n:>3} {ans1:>10} {ok1:>3} {t1:>6} {e1:>6}  |  {ans2:>10} {ok2:>3} {t2:>6} {e2:>6}")

    # Key differences summary
    print(f"\n  {'─' * 60}")
    print(f"  KEY DIFFERENCES")
    print(f"  {'─' * 60}")

    diffs = []
    if s1["status"] != s2["status"]:
        diffs.append(f"  Outcome: {p1.problem_id} is {s1['status']}, {p2.problem_id} is {s2['status']}")
    if abs(s1["wall_time"] - s2["wall_time"]) > 60:
        slower = p1.problem_id if s1["wall_time"] > s2["wall_time"] else p2.problem_id
        diffs.append(f"  Time: {slower} is significantly slower ({fmt_time(abs(s1['wall_time'] - s2['wall_time']))} difference)")
    if s1["nones"] != s2["nones"]:
        more_nones = p1.problem_id if s1["nones"] > s2["nones"] else p2.problem_id
        diffs.append(f"  Nones: {more_nones} has more Nones ({max(s1['nones'], s2['nones'])} vs {min(s1['nones'], s2['nones'])})")
    if s1["unique_answers"] != s2["unique_answers"]:
        more_div = p1.problem_id if s1["unique_answers"] > s2["unique_answers"] else p2.problem_id
        diffs.append(f"  Diversity: {more_div} has more unique answers ({max(s1['unique_answers'], s2['unique_answers'])} vs {min(s1['unique_answers'], s2['unique_answers'])})")
    if abs(s1["errors"] - s2["errors"]) > 5:
        more_err = p1.problem_id if s1["errors"] > s2["errors"] else p2.problem_id
        diffs.append(f"  Errors: {more_err} has significantly more errors ({max(s1['errors'], s2['errors'])} vs {min(s1['errors'], s2['errors'])})")

    if diffs:
        for d in diffs:
            print(d)
    else:
        print("  No major differences found.")
    print()


def compare_correct_vs_wrong(problems):
    """Aggregate comparison of all correct vs all wrong problems."""
    correct = [p for p in problems if p.correct]
    wrong = [p for p in problems if not p.correct]

    print(f"\n{'=' * 72}")
    print(f"  CORRECT vs WRONG PROBLEMS (AGGREGATE)")
    print(f"{'=' * 72}")

    print(f"\n  {'Metric':<25} {f'Correct (n={len(correct)})':>20} {f'Wrong (n={len(wrong)})':>20}")
    print(f"  {'─' * 25} {'─' * 20} {'─' * 20}")

    def agg(ps, fn):
        vals = [fn(p) for p in ps]
        return mean(vals) if vals else 0

    metrics = [
        ("Avg Wall Time", lambda p: p.wall_time, fmt_time),
        ("Avg Tokens", lambda p: sum(a.tokens for a in p.attempts), fmt_tokens),
        ("Avg None Rate", lambda p: sum(1 for a in p.attempts if a.is_none) / len(p.attempts) * 100 if p.attempts else 0, lambda x: f"{x:.0f}%"),
        ("Avg Errors", lambda p: sum(a.errors for a in p.attempts), lambda x: f"{x:.1f}"),
        ("Avg Code Calls", lambda p: sum(a.code_calls for a in p.attempts), lambda x: f"{x:.1f}"),
        ("Avg Turns/Attempt", lambda p: mean([len(a.turns) for a in p.attempts]), lambda x: f"{x:.1f}"),
        ("Avg Entropy", lambda p: mean([a.entropy for a in p.attempts]), lambda x: f"{x:.3f}"),
        ("Avg Unique Answers", lambda p: len(set(a.answer for a in p.attempts if a.answer is not None)), lambda x: f"{x:.1f}"),
        ("Avg Reasoning Chars", lambda p: mean([sum(len(t.reasoning_text) for t in a.turns) for a in p.attempts]), lambda x: f"{x:.0f}"),
    ]

    for name, fn, fmt in metrics:
        v_correct = agg(correct, fn)
        v_wrong = agg(wrong, fn)
        print(f"  {name:<25} {fmt(v_correct):>20} {fmt(v_wrong):>20}")

    # List wrong problems
    if wrong:
        print(f"\n  Wrong problems:")
        for p in wrong:
            print(f"    {p.problem_id}: predicted={p.predicted}, expected={p.expected}, time={fmt_time(p.wall_time)}, votes={p.votes}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare two AIMO3 problems side-by-side, or compare correct vs wrong aggregates.",
        usage="python3 log_exploration/compare_problems.py <logfile> <pid1> <pid2> [options]"
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("pid1", nargs="?", help="First problem ID")
    parser.add_argument("pid2", nargs="?", help="Second problem ID")
    parser.add_argument("--correct-vs-wrong", action="store_true", help="Compare all correct vs wrong (aggregate)")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    problems = parse_log(args.logfile)

    if args.correct_vs_wrong:
        compare_correct_vs_wrong(problems)
    elif args.pid1 and args.pid2:
        compare_two(problems, args.pid1, args.pid2)
    else:
        parser.print_help()
        print(f"\n  Available problem IDs:")
        for p in problems:
            ok = "Y" if p.correct else "N"
            print(f"    {p.problem_id} [{ok}] {p.batch_name}")


if __name__ == "__main__":
    main()
