#!/usr/bin/env python3
"""
Find problems from diagnostic logs that should be in the problem knowledge DB but aren't.

Scans v23 and v31 logs for problems NOT already in the DB that meet any of:
1. Wrong answer - voted answer != expected answer
2. Close vote - correct answer won but a competing wrong answer got significant votes
3. Many code failures - AND the problem had issues (high none, close vote)
4. High None rate - majority of attempts returned None in v31 (no ES)
5. Timeout-dominated - majority of attempts hit time limit AND problem was close/wrong

Priority ordering: wrong > close_vote > high_none > code_failures > timeout

Usage:
    python3 log_exploration/find_missing_problems.py output/v23/diagnostic.log output/v31/diagnostic.log
"""

import sys
import json
import os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# Current DB problem IDs (first 6 chars)
DB_PROBLEM_IDS = {
    "06788e", "0c55f3", "0ef1f6", "1ec970", "23586c", "2e21c9", "32690e",
    "3980cd", "3b88b3", "3c5c22", "427478", "44fdc2", "4878ca", "4f0aa0",
    "547696", "5de0ad", "65c16c", "676ce2", "6c27f2", "768cce", "86e8e5",
    "8fea51", "946bc5", "9aee32", "a824c1", "b4ec47", "ba89f9", "bad5bf",
    "bc6f0d", "d1b534", "dbbfe8", "dc57de", "e32781", "e79a0f", "f01e57",
}


def is_in_db(problem_id):
    prefix = problem_id[:6]
    return prefix in DB_PROBLEM_IDS


def detect_topic(problem_text):
    text = problem_text.lower()
    geo_words = ["triangle", "circle", "angle", "polygon", "perpendicular", "parallel",
                 "inscribed", "circumscribed", "tangent", "midpoint", "bisect",
                 "quadrilateral", "diameter", "radius", "area", "perimeter",
                 "rectangle", "square", "rhombus", "hexagon", "pentagon",
                 "ellipse", "parabola", "line segment", "vertex", "altitude",
                 "median", "centroid", "incircle", "circumcircle", "chord", "arc"]
    comb_words = ["how many", "number of ways", "count", "permutation", "combination",
                  "subset", "arrangement", "probability", "expected value",
                  "coloring", "graph", "path", "tournament", "grid", "board",
                  "tile", "domino", "chess", "dice", "card", "choose",
                  "distribute", "partition", "paint", "color", "stone", "coin",
                  "piece", "game", "player"]
    nt_words = ["prime", "divisor", "divisible", "gcd", "lcm", "modulo", "mod ",
                "remainder", "congruent", "factor", "coprime", "euler", "fermat",
                "diophantine", "integer solution", "residue", "perfect square",
                "perfect cube", "digit sum", "lattice point"]
    alg_words = ["polynomial", "equation", "root", "coefficient", "function",
                 "inequality", "minimum", "maximum", "sum of", "product of",
                 "real number", "complex number", "matrix", "determinant",
                 "recurrence", "series", "converge", "limit", "maximal value",
                 "minimal value", "find the"]

    scores = {
        "geometry": sum(1 for w in geo_words if w in text),
        "combinatorics": sum(1 for w in comb_words if w in text),
        "number_theory": sum(1 for w in nt_words if w in text),
        "algebra": sum(1 for w in alg_words if w in text),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "unknown"


def build_vote_distribution(prob):
    total_attempts = len(prob.attempts)
    if prob.votes:
        vote_dist = {}
        for ans, count in prob.votes.items():
            vote_dist[str(ans)] = count
        nones = total_attempts - sum(prob.votes.values())
        if nones > 0:
            vote_dist["None"] = nones
        return vote_dist
    vote_dist = {}
    none_count = 0
    for att in prob.attempts:
        if att.answer is None:
            none_count += 1
        else:
            key = str(att.answer)
            vote_dist[key] = vote_dist.get(key, 0) + 1
    if none_count > 0:
        vote_dist["None"] = none_count
    return vote_dist


def analyze_problem(prob, version):
    """Check if problem qualifies. Returns info dict or None.

    Strict criteria to avoid flooding with ES artifacts:
    - Wrong answers: ALWAYS qualify
    - Close votes: correct won but competing answer got significant votes
    - High None in v31: 8+ Nones out of 16 (no ES, so these are real failures)
    - Timeout issues: only if combined with wrong/close
    """
    qualifications = []
    total_attempts = len(prob.attempts)
    if total_attempts == 0:
        return None

    vote_dist = build_vote_distribution(prob)
    none_count = sum(1 for att in prob.attempts if att.answer is None)
    error_attempts = sum(1 for att in prob.attempts if att.errors > 0)

    timeout_attempts = 0
    for att in prob.attempts:
        for turn in att.turns:
            if turn.is_error and ("timeout" in turn.output.lower() or
                                   "time limit" in turn.output.lower() or
                                   "timed out" in turn.output.lower()):
                timeout_attempts += 1
                break

    # --- 1. Wrong answer (ALWAYS qualifies) ---
    if not prob.correct and prob.expected is not None:
        qualifications.append("wrong_answer")

    # --- 2. Close vote ---
    # Correct answer won but a SPECIFIC wrong answer got significant support
    if prob.correct and prob.expected is not None and prob.votes:
        correct_votes = prob.votes.get(prob.expected, 0)
        # Get the strongest competing answer
        other_answers = {k: v for k, v in prob.votes.items() if k != prob.expected}
        max_competing = max(other_answers.values()) if other_answers else 0

        if version == "v31":
            # v31: 16 attempts, no ES. Close if competing answer got >= 3 votes
            if max_competing >= 3:
                qualifications.append("close_vote")
        else:
            # v23: ES=5. Close only if competing answers are nearly as strong as correct
            if max_competing >= 3 and correct_votes - max_competing <= 2:
                qualifications.append("close_vote")

    # --- 3. High None rate (v31 only, since v23 Nones are ES artifacts) ---
    if version == "v31" and none_count >= 8:
        qualifications.append("high_none")

    # --- 4. Timeout-dominated (v31: majority timed out, or any version if wrong) ---
    if timeout_attempts >= total_attempts // 2:
        qualifications.append("timeout")

    # --- 5. Code failures: only flag if ALSO has another qualification ---
    # (pure code failures in correct problems aren't interesting enough)
    if error_attempts >= 5:
        if qualifications:  # Only add if already qualifies on another criterion
            qualifications.append("code_failures")

    if not qualifications:
        return None

    return {
        "problem_id": prob.problem_id,
        "expected_answer": prob.expected,
        "predicted_answer": prob.predicted,
        "correct": prob.correct,
        "question": prob.problem_text if prob.problem_text else "",
        "category": detect_topic(prob.problem_text or ""),
        "qualification": qualifications,
        "vote_distribution": vote_dist,
        "total_attempts": total_attempts,
        "none_count": none_count,
        "error_attempts": error_attempts,
        "timeout_attempts": timeout_attempts,
        "source_version": "",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 find_missing_problems.py <log1> [log2] ...")
        sys.exit(1)

    log_files = sys.argv[1:]
    all_problems = {}

    for log_file in log_files:
        version = "unknown"
        parts = log_file.replace("\\", "/").split("/")
        for p in parts:
            if p.startswith("v"):
                version = p
                break

        print(f"\n{'='*70}")
        print(f"Parsing {log_file} ({version})...")
        problems = parse_log(log_file)
        print(f"  Found {len(problems)} problems")

        in_db = 0
        not_in_db = 0
        qualifying = 0

        for prob in problems:
            if is_in_db(prob.problem_id):
                in_db += 1
                continue
            not_in_db += 1

            result = analyze_problem(prob, version)
            if result:
                result["source_version"] = version
                qualifying += 1
                pid = prob.problem_id

                if pid in all_problems:
                    existing = all_problems[pid]
                    for q in result["qualification"]:
                        if q not in existing["qualification"]:
                            existing["qualification"].append(q)
                    if len(result["question"]) > len(existing["question"]):
                        existing["question"] = result["question"]
                    if version not in existing["source_version"]:
                        existing["source_version"] += f",{version}"
                    # Track per-version votes
                    if "per_version" not in existing:
                        existing["per_version"] = {}
                    existing["per_version"][version] = {
                        "votes": result["vote_distribution"],
                        "correct": result["correct"],
                        "predicted": result["predicted_answer"],
                    }
                    # Prefer v31 vote distribution (16 attempts, no ES)
                    if version == "v31":
                        existing["vote_distribution"] = result["vote_distribution"]
                        existing["predicted_answer"] = result["predicted_answer"]
                        existing["correct"] = result["correct"]
                        existing["total_attempts"] = result["total_attempts"]
                        existing["none_count"] = result["none_count"]
                        existing["error_attempts"] = result["error_attempts"]
                        existing["timeout_attempts"] = result["timeout_attempts"]
                else:
                    all_problems[pid] = result

        print(f"  Already in DB: {in_db}")
        print(f"  Not in DB: {not_in_db}")
        print(f"  Qualifying (not in DB + meets criteria): {qualifying}")

    # Separate by type
    wrong = {k: v for k, v in all_problems.items() if "wrong_answer" in v["qualification"]}
    close = {k: v for k, v in all_problems.items()
             if "close_vote" in v["qualification"] and "wrong_answer" not in v["qualification"]}
    other = {k: v for k, v in all_problems.items()
             if "wrong_answer" not in v["qualification"] and "close_vote" not in v["qualification"]}

    print(f"\n{'='*70}")
    print(f"TOTAL: {len(all_problems)} problems ({len(wrong)} wrong, {len(close)} close vote, {len(other)} other)")
    print(f"{'='*70}")

    print(f"\n=== WRONG ANSWERS ({len(wrong)}) ===")
    for pid in sorted(wrong):
        info = wrong[pid]
        print(f"\n  {info['problem_id']}")
        print(f"  Expected={info['expected_answer']}  Predicted={info['predicted_answer']}")
        print(f"  Category: {info['category']}  Source: {info['source_version']}")
        print(f"  Qualifies: {', '.join(info['qualification'])}")
        print(f"  Votes: {info['vote_distribution']}")
        if info['question']:
            print(f"  Q: {info['question'][:150]}...")

    print(f"\n=== CLOSE VOTES ({len(close)}) ===")
    for pid in sorted(close):
        info = close[pid]
        print(f"\n  {info['problem_id']}")
        print(f"  Expected={info['expected_answer']}  Predicted={info['predicted_answer']}")
        print(f"  Category: {info['category']}  Source: {info['source_version']}")
        print(f"  Qualifies: {', '.join(info['qualification'])}")
        print(f"  Votes: {info['vote_distribution']}")
        if info['question']:
            print(f"  Q: {info['question'][:150]}...")

    if other:
        print(f"\n=== OTHER (high_none / timeout) ({len(other)}) ===")
        for pid in sorted(other):
            info = other[pid]
            print(f"\n  {info['problem_id']}")
            print(f"  Expected={info['expected_answer']}  Predicted={info['predicted_answer']}")
            print(f"  Category: {info['category']}  Source: {info['source_version']}")
            print(f"  Qualifies: {', '.join(info['qualification'])}")
            print(f"  Votes: {info['vote_distribution']}")
            if info['question']:
                print(f"  Q: {info['question'][:150]}...")

    # Build JSON output
    results = []
    for pid, info in sorted(all_problems.items()):
        primary_qual = info["qualification"][0]
        entry = {
            "problem_id": info["problem_id"],
            "expected_answer": info["expected_answer"],
            "question": info["question"],
            "category": info["category"],
            "qualification": primary_qual,
            "all_qualifications": info["qualification"],
            "vote_distribution": info["vote_distribution"],
            "source_version": info["source_version"],
            "correct": info["correct"],
            "none_count": info["none_count"],
            "error_attempts": info["error_attempts"],
        }
        # Include per-version data if problem appeared in multiple versions
        if "per_version" in info and len(info.get("per_version", {})) > 0:
            entry["per_version"] = info["per_version"]
        results.append(entry)

    output_path = "/tmp/additional_problems.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {output_path}")
    print(f"Total: {len(results)} problems")


if __name__ == "__main__":
    main()
