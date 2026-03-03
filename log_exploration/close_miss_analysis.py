#!/usr/bin/env python3
"""
Close Miss Analysis — Find and classify problems where |predicted - expected| < threshold.
==========================================================================================
Automatically identifies "almost correct" problems and classifies the error type.

Usage:
    python3 log_exploration/close_miss_analysis.py <logfile>
    python3 log_exploration/close_miss_analysis.py <logfile> --threshold 100
    python3 log_exploration/close_miss_analysis.py <logfile> --verbose

Options:
    --threshold N   Maximum absolute difference to consider (default: 50)
    --verbose       Show per-attempt details and vote distributions
    --json          Output as JSON for programmatic use
"""

import sys
import os
import json
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def classify_error(problem, threshold=50):
    """Classify the type of close-miss error for a problem."""
    pred = problem.predicted
    exp = problem.expected
    if pred is None or exp is None:
        return None

    diff = pred - exp
    abs_diff = abs(diff)
    if abs_diff == 0 or abs_diff >= threshold:
        return None

    classification = {
        "problem_id": problem.problem_id,
        "predicted": pred,
        "expected": exp,
        "diff": diff,
        "abs_diff": abs_diff,
        "problem_text": problem.problem_text[:200] if problem.problem_text else "",
        "wall_time": problem.wall_time,
        "total_attempts": len(problem.attempts),
        "answered_attempts": sum(1 for a in problem.attempts if not a.is_none),
        "none_attempts": sum(1 for a in problem.attempts if a.is_none),
        "total_errors": problem.total_errors,
        "avg_entropy": problem.avg_entropy,
        "early_stop": problem.early_stop,
        "votes": dict(problem.votes),
    }

    # Check if correct answer ever found
    correct_attempts = [
        a for a in problem.attempts
        if a.answer is not None and a.answer == exp
    ]
    classification["correct_found"] = len(correct_attempts) > 0
    classification["correct_count"] = len(correct_attempts)
    if correct_attempts:
        classification["correct_temps"] = [a.temperature for a in correct_attempts]
        classification["correct_attempt_nums"] = [a.attempt_num for a in correct_attempts]

    # Check if the wrong answer is systematic (same wrong answer repeated)
    wrong_answers = [
        a.answer for a in problem.attempts
        if a.answer is not None and a.answer != exp
    ]
    answer_counts = Counter(wrong_answers)
    most_common_wrong = answer_counts.most_common(1)
    if most_common_wrong:
        top_wrong, top_count = most_common_wrong[0]
        classification["systematic"] = top_count >= 3
        classification["most_common_wrong"] = top_wrong
        classification["most_common_wrong_count"] = top_count
    else:
        classification["systematic"] = False

    # Classify error type
    if abs_diff == 1:
        classification["error_type"] = "off_by_one"
        classification["error_description"] = (
            "Off-by-one error: could be boundary condition, "
            "fencepost, rounding, or floor/ceil mismatch"
        )
    elif abs_diff <= 5:
        classification["error_type"] = "small_counting_error"
        classification["error_description"] = (
            f"Small counting error (off by {abs_diff}): "
            "likely edge case in combinatorics or boundary"
        )
    elif abs_diff <= 20:
        classification["error_type"] = "moderate_error"
        classification["error_description"] = (
            f"Moderate error (off by {abs_diff}): "
            "possible formula error or missed constraint"
        )
    else:
        classification["error_type"] = "large_near_miss"
        classification["error_description"] = (
            f"Large near-miss (off by {abs_diff}): "
            "likely wrong approach that happens to give close answer"
        )

    # Check vote margin
    if problem.votes:
        sorted_votes = sorted(problem.votes.items(), key=lambda x: -x[1])
        if len(sorted_votes) >= 2:
            winner_votes = sorted_votes[0][1]
            runner_up_votes = sorted_votes[1][1]
            classification["vote_margin"] = winner_votes - runner_up_votes
        else:
            classification["vote_margin"] = sorted_votes[0][1]

        # Was correct answer the runner-up?
        if exp in problem.votes:
            correct_rank = 1
            for ans, count in sorted_votes:
                if ans == exp:
                    break
                correct_rank += 1
            classification["correct_vote_rank"] = correct_rank
            classification["correct_vote_count"] = problem.votes[exp]
        else:
            classification["correct_vote_rank"] = None
            classification["correct_vote_count"] = 0

    # Could a verify prompt help?
    # Heuristic: if correct answer was found in some attempts, verification could help
    # Also if the error is systematic (same wrong answer every time), verification less likely to help
    if classification["correct_found"]:
        classification["verify_potential"] = "HIGH"
        classification["verify_reason"] = (
            f"Correct answer found in {classification['correct_count']} attempts "
            f"but outvoted by wrong answer"
        )
    elif classification["systematic"] and abs_diff <= 5:
        classification["verify_potential"] = "MEDIUM"
        classification["verify_reason"] = (
            "Systematic small error - verification might catch boundary/rounding issues"
        )
    elif classification["systematic"]:
        classification["verify_potential"] = "LOW"
        classification["verify_reason"] = (
            "Systematic error with consistent wrong reasoning - model confidently wrong"
        )
    else:
        classification["verify_potential"] = "MEDIUM"
        classification["verify_reason"] = (
            "Non-systematic error with scattered answers - more attempts might help"
        )

    return classification


def print_classification(c, verbose=False):
    """Print a single close-miss classification."""
    print(f"\n{'=' * 70}")
    print(f"  Problem: {c['problem_id']}")
    print(f"  Predicted: {c['predicted']}  |  Expected: {c['expected']}  |  Diff: {c['diff']:+d}")
    print(f"  Error Type: {c['error_type']}")
    print(f"  {c['error_description']}")
    print(f"{'=' * 70}")

    print(f"\n  Attempts: {c['total_attempts']} total, {c['answered_attempts']} answered, {c['none_attempts']} None")
    print(f"  Errors: {c['total_errors']}  |  Avg Entropy: {c['avg_entropy']:.3f}")
    print(f"  Early Stop: {'Yes' if c['early_stop'] else 'No'}")
    print(f"  Wall Time: {c['wall_time']:.0f}s")

    if "systematic" in c:
        sys_str = "YES" if c["systematic"] else "No"
        print(f"\n  Systematic Error: {sys_str}")
        if c.get("most_common_wrong") is not None:
            print(f"  Most Common Wrong Answer: {c['most_common_wrong']} ({c['most_common_wrong_count']} times)")

    print(f"\n  Correct Answer Found in Attempts: {'YES' if c['correct_found'] else 'NO'}")
    if c["correct_found"]:
        print(f"  Correct Attempts: {c['correct_count']} (attempts {c.get('correct_attempt_nums', [])})")
        print(f"  Correct Temps: {c.get('correct_temps', [])}")

    if c.get("votes"):
        print(f"\n  Votes:")
        for ans, count in sorted(c["votes"].items(), key=lambda x: -x[1]):
            marker = " <-- CORRECT" if ans == c["expected"] else ""
            winner = " (winner)" if count == max(c["votes"].values()) else ""
            print(f"    {ans}: {count} vote(s){winner}{marker}")
        if "vote_margin" in c:
            print(f"  Vote Margin: {c['vote_margin']}")
        if c.get("correct_vote_rank"):
            print(f"  Correct Answer Rank: #{c['correct_vote_rank']} with {c['correct_vote_count']} votes")

    print(f"\n  Verify Prompt Potential: {c['verify_potential']}")
    print(f"  Reason: {c['verify_reason']}")

    if verbose and c.get("problem_text"):
        print(f"\n  Problem Text: {c['problem_text']}")


def main():
    parser = argparse.ArgumentParser(
        description="Find and classify close-miss problems (|predicted - expected| < threshold).",
        usage="python3 log_exploration/close_miss_analysis.py <logfile> [options]",
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument(
        "--threshold", type=int, default=50,
        help="Maximum absolute difference to consider (default: 50)",
    )
    parser.add_argument("--verbose", action="store_true", help="Show extra details")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not os.path.exists(args.logfile):
        print(f"Error: File not found: {args.logfile}")
        sys.exit(1)

    problems = parse_log(args.logfile)

    # Find all close misses
    close_misses = []
    for p in problems:
        c = classify_error(p, threshold=args.threshold)
        if c is not None:
            close_misses.append(c)

    # Sort by absolute difference
    close_misses.sort(key=lambda x: x["abs_diff"])

    if args.json:
        # Convert int keys in votes to strings for JSON
        for c in close_misses:
            c["votes"] = {str(k): v for k, v in c["votes"].items()}
        print(json.dumps(close_misses, indent=2))
        return

    # Summary header
    total = len(problems)
    wrong = sum(1 for p in problems if not p.correct and p.predicted is not None and p.expected is not None)
    print(f"\n{'=' * 70}")
    print(f"  CLOSE MISS ANALYSIS")
    print(f"  Threshold: |diff| < {args.threshold}")
    print(f"{'=' * 70}")
    print(f"\n  Total problems: {total}")
    print(f"  Wrong problems: {wrong}")
    print(f"  Close misses found: {len(close_misses)}")

    if not close_misses:
        print("\n  No close misses found.\n")
        return

    # Classification summary
    by_type = Counter(c["error_type"] for c in close_misses)
    print(f"\n  By Error Type:")
    for etype, count in by_type.most_common():
        print(f"    {etype}: {count}")

    by_verify = Counter(c["verify_potential"] for c in close_misses)
    print(f"\n  By Verify Potential:")
    for vp, count in by_verify.most_common():
        print(f"    {vp}: {count}")

    correct_found_count = sum(1 for c in close_misses if c["correct_found"])
    systematic_count = sum(1 for c in close_misses if c.get("systematic"))
    print(f"\n  Correct answer found in some attempts: {correct_found_count}/{len(close_misses)}")
    print(f"  Systematic errors: {systematic_count}/{len(close_misses)}")

    # Potential score recovery
    print(f"\n  Potential score recovery if all close misses fixed: +{len(close_misses)} problems")

    # Detailed per-problem output
    for c in close_misses:
        print_classification(c, verbose=args.verbose)

    print()


if __name__ == "__main__":
    main()
