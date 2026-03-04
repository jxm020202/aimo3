#!/usr/bin/env python3
"""
Math Topic Analysis for AIMO3 Diagnostic Logs
===============================================
Categorizes each problem by math topic based on keywords in the problem text,
then shows per-topic accuracy and per-problem topic assignments.

A problem can belong to multiple categories if its text matches keywords from
multiple topics.

Usage: python3 log_exploration/topic_analysis.py output/v31/diagnostic.log
"""

import sys
import re
from collections import defaultdict

sys.path.insert(0, '/Users/intern/Desktop/sideprojects/aimo3')
from log_exploration.log_query import parse_log


# ── Topic definitions: (category_name, keyword_patterns) ────────────────────
# Patterns are matched case-insensitively against the problem text.
# We use word-boundary-aware patterns where appropriate.

TOPIC_DEFINITIONS = {
    "Number Theory": [
        r"prime", r"divis", r"modular", r"modulo", r"\bmod\b", r"congruen",
        r"\bgcd\b", r"\blcm\b", r"euler", r"fermat", r"coprime", r"residue",
        r"diophantine", r"factor", r"digit", r"multiple", r"remainder",
        r"perfect\s+(square|number|power)", r"square-free", r"squarefree",
    ],
    "Combinatorics": [
        r"count", r"permut", r"combin", r"arrange", r"\bways\b", r"choose",
        r"path", r"binomial", r"selection", r"pigeonhole", r"inclusion",
        r"catalan", r"colou?ring", r"subset", r"partition", r"distribut",
        r"board", r"grid", r"tile", r"tiling", r"domino", r"place",
        r"chessboard", r"distinct",
    ],
    "Algebra": [
        r"polynomial", r"equation", r"function", r"\broots?\b", r"inequalit",
        r"sequence", r"series", r"coefficient", r"quadratic", r"cubic",
        r"linear", r"recurren", r"sum\b", r"product", r"minimum", r"maximum",
        r"real\s+number", r"integer.*satisf", r"solve", r"expression",
        r"floor", r"ceil",
    ],
    "Geometry": [
        r"triangle", r"circle", r"angle", r"\barea\b", r"perimeter",
        r"polygon", r"coordinate", r"distance", r"point", r"line\b",
        r"parallel", r"perpendicular", r"tangent", r"inscribe", r"circumscri",
        r"convex", r"hexagon", r"pentagon", r"square", r"rectangle",
        r"ellipse", r"diameter", r"radius", r"midpoint", r"vertex",
        r"vertices",
    ],
    "Game Theory / Strategy": [
        r"\bgame\b", r"\bplayer", r"strateg", r"\bwins?\b", r"\bmoves?\b",
        r"optimal", r"alice", r"\bbob\b", r"first\s+player", r"second\s+player",
        r"turn", r"token",
    ],
    "Probability / Statistics": [
        r"probabilit", r"expected", r"random", r"\bdice\b", r"\bcard",
        r"fair\s+coin", r"\bflip", r"independen", r"conditional",
    ],
    "Graph Theory": [
        r"\bgraph\b", r"vertices", r"vertex", r"\bedges?\b", r"connected",
        r"\btree\b", r"\bcycle\b", r"degree", r"adjacent", r"bipartite",
        r"planar", r"chromatic", r"clique",
    ],
    "Linear Algebra / Matrix": [
        r"matrix", r"matrices", r"determinant", r"eigenvalue", r"vector",
        r"linear\s+(map|transform|operator)", r"rank\b",
    ],
    "Analysis": [
        r"\blimit\b", r"integral", r"derivative", r"continuous", r"convergent",
        r"differentiable", r"infimum", r"supremum", r"cauchy",
    ],
}


def classify_problem(problem_text: str) -> list[str]:
    """Classify a problem into math topics based on keyword matches in problem text.

    Returns list of (topic, match_count) sorted by match count descending.
    If no topic matches, returns ["Other"].
    """
    text = problem_text.lower()
    matched = []

    for topic, patterns in TOPIC_DEFINITIONS.items():
        match_count = 0
        for pat in patterns:
            hits = len(re.findall(pat, text))
            match_count += hits
        if match_count >= 1:
            matched.append((topic, match_count))

    matched.sort(key=lambda x: x[1], reverse=True)
    return matched if matched else [("Other", 0)]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/topic_analysis.py <diagnostic.log>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    if not problems:
        print("No problems found in log.")
        sys.exit(1)

    # ── Classify each problem ──
    problem_topics = {}  # pid -> list of topic names
    problem_matches = {}  # pid -> list of (topic, count) for display

    for p in problems:
        matches = classify_problem(p.problem_text)
        topic_names = [t[0] for t in matches]
        problem_topics[p.problem_id] = topic_names
        problem_matches[p.problem_id] = matches

    # ── Aggregate stats per topic ──
    topic_stats = defaultdict(lambda: {"total": 0, "correct": 0, "wrong_pids": [], "correct_pids": []})

    for p in problems:
        for topic in problem_topics[p.problem_id]:
            ts = topic_stats[topic]
            ts["total"] += 1
            if p.correct:
                ts["correct"] += 1
                ts["correct_pids"].append(p.problem_id)
            else:
                ts["wrong_pids"].append(p.problem_id)

    # ── Overall summary ──
    total = len(problems)
    correct = sum(1 for p in problems if p.correct)
    wrong = total - correct

    print("=" * 90)
    print("MATH TOPIC ANALYSIS")
    print("=" * 90)
    print(f"\nOverall: {correct}/{total} correct ({correct/total*100:.1f}%), {wrong} wrong\n")

    # ── Per-topic table ──
    print(f"{'Topic':<30} {'Total':>6} {'Correct':>8} {'Wrong':>6} {'Accuracy':>9}")
    print("-" * 65)

    sorted_topics = sorted(topic_stats.keys(), key=lambda t: topic_stats[t]["total"], reverse=True)
    for topic in sorted_topics:
        ts = topic_stats[topic]
        n = ts["total"]
        c = ts["correct"]
        w = n - c
        acc = c / n * 100 if n > 0 else 0
        print(f"  {topic:<28} {n:>6} {c:>8} {w:>6} {acc:>8.1f}%")

    print("-" * 65)

    # ── Wrong problems per topic ──
    print("\n" + "=" * 90)
    print("WRONG PROBLEMS BY TOPIC")
    print("=" * 90)

    for topic in sorted_topics:
        ts = topic_stats[topic]
        if ts["wrong_pids"]:
            print(f"\n  {topic} ({len(ts['wrong_pids'])} wrong):")
            for pid in ts["wrong_pids"]:
                p = next(prob for prob in problems if prob.problem_id == pid)
                text_preview = p.problem_text[:80] + "..." if len(p.problem_text) > 80 else p.problem_text
                print(f"    {pid}: predicted={p.predicted}, expected={p.expected}")
                print(f"           {text_preview}")

    # ── Per-problem detail ──
    print("\n" + "=" * 90)
    print("PER-PROBLEM TOPIC ASSIGNMENTS")
    print("=" * 90)
    print(f"\n  {'PID':<10} {'Status':<8} {'Topics':<50} {'Problem Text (first 100 chars)'}")
    print("  " + "-" * 120)

    for p in problems:
        status = "OK" if p.correct else "WRONG"
        topics = problem_topics[p.problem_id]
        topic_str = ", ".join(topics)
        text_preview = p.problem_text[:100].replace("\n", " ") if p.problem_text else "(no text)"
        print(f"  {p.problem_id:<10} {status:<8} {topic_str:<50} {text_preview}")

    # ── Topic co-occurrence ──
    print("\n" + "=" * 90)
    print("TOPIC CO-OCCURRENCE (problems with multiple topics)")
    print("=" * 90)

    multi_count = 0
    for p in problems:
        topics = problem_topics[p.problem_id]
        if len(topics) > 1:
            multi_count += 1
            status = "OK" if p.correct else "WRONG"
            print(f"  {p.problem_id} [{status}]: {', '.join(topics)}")

    if multi_count == 0:
        print("  (none)")
    else:
        print(f"\n  {multi_count}/{total} problems have multiple topic assignments")


if __name__ == "__main__":
    main()
