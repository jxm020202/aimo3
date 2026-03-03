#!/usr/bin/env python3
"""
Problem Difficulty Scoring for AIMO3 Logs
==========================================
Builds a difficulty scoring system combining multiple signals.
Classifies problems and compares successful vs failed attempts on hard problems.

Usage: python3 log_exploration/problem_difficulty.py output/v22/diagnostic.log
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


def compute_difficulty_scores(problems):
    """Compute a multi-factor difficulty score for each problem."""
    scores = {}

    for p in problems:
        total_att = len(p.attempts)
        if total_att == 0:
            continue

        # Factor 1: Error rate (what fraction of attempts returned wrong answer)
        wrong = sum(1 for a in p.attempts if classify_attempt(a, p) == "wrong")
        error_rate = wrong / total_att

        # Factor 2: None rate (what fraction of attempts produced no answer)
        nones = sum(1 for a in p.attempts if a.is_none)
        none_rate = nones / total_att

        # Factor 3: Time (normalized wall time)
        time_norm = min(p.wall_time / 600.0, 1.0)  # Cap at 600s

        # Factor 4: Vote margin (lower = harder, less agreement)
        if p.votes and len(p.votes) >= 2:
            sv = sorted(p.votes.values(), reverse=True)
            vote_margin = (sv[0] - sv[1]) / total_att
        elif p.votes:
            vote_margin = 1.0
        else:
            vote_margin = 0.0

        # Factor 5: Unique answer count (more = harder)
        unique_answers = len(set(a.answer for a in p.attempts if a.answer is not None))
        answer_diversity = min(unique_answers / 8.0, 1.0)

        # Factor 6: Average turns needed
        avg_turns = sum(len(a.turns) for a in p.attempts) / total_att
        turn_pressure = min(avg_turns / 10.0, 1.0)

        # Factor 7: Total errors in code
        total_errors = sum(a.errors for a in p.attempts)
        error_pressure = min(total_errors / (total_att * 3), 1.0)

        # Composite score: weighted combination (0-100, higher = harder)
        # Note: many problems have high None rate due to early stopping (3/8 answer).
        # We focus on signals that differentiate beyond base None rate.
        base_none_rate = 0.625  # Expected None rate when early stop triggers at 3 answers
        excess_none = max(0, none_rate - base_none_rate)

        score = (
            excess_none * 25 +         # None beyond expected
            error_rate * 30 +          # Wrong answers (strongest signal)
            (1 - vote_margin) * 15 +   # Low consensus
            answer_diversity * 15 +    # Many different answers
            turn_pressure * 10 +       # More turns needed
            error_pressure * 5         # More code errors
        ) * 100

        scores[p.problem_id] = {
            "score": score,
            "error_rate": error_rate,
            "none_rate": none_rate,
            "time": p.wall_time,
            "vote_margin": vote_margin,
            "unique_answers": unique_answers,
            "avg_turns": avg_turns,
            "total_errors": total_errors,
            "correct": p.correct,
            "predicted": p.predicted,
            "expected": p.expected,
        }

    return scores


def difficulty_classification(problems, scores):
    """Classify each problem into difficulty tiers."""
    print("=" * 80)
    print("PROBLEM DIFFICULTY CLASSIFICATION")
    print("=" * 80)

    # Sort by difficulty score
    sorted_probs = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    # Classify using percentile-based thresholds
    classifications = {}
    all_scores_sorted = sorted(s["score"] for s in scores.values())
    n = len(all_scores_sorted)
    p90 = all_scores_sorted[int(n * 0.90)] if n > 0 else 0
    p75 = all_scores_sorted[int(n * 0.75)] if n > 0 else 0
    p50 = all_scores_sorted[int(n * 0.50)] if n > 0 else 0

    for pid, s in sorted_probs:
        if s["score"] >= p90:
            classifications[pid] = "IMPOSSIBLE"
        elif s["score"] >= p75:
            classifications[pid] = "HARD"
        elif s["score"] >= p50:
            classifications[pid] = "MEDIUM"
        else:
            classifications[pid] = "EASY"

    # Print table
    print(f"\n  {'PID':<10} {'Diff':>6} {'Class':<12} {'Correct':>8} {'ErrR':>6} {'NoneR':>6} "
          f"{'VoteM':>6} {'Uniq':>5} {'Turns':>6} {'Time':>7}")
    print("  " + "-" * 90)

    for pid, s in sorted_probs:
        cls = classifications[pid]
        correct_mark = "YES" if s["correct"] else "NO"
        print(f"  {pid:<10} {s['score']:>5.1f} {cls:<12} {correct_mark:>8} "
              f"{s['error_rate']:>5.0%} {s['none_rate']:>5.0%} "
              f"{s['vote_margin']:>5.2f} {s['unique_answers']:>5} "
              f"{s['avg_turns']:>5.1f} {s['time']:>6.0f}s")

    # Summary by tier
    print(f"\n  TIER SUMMARY:")
    tier_order = ["EASY", "MEDIUM", "HARD", "IMPOSSIBLE"]
    for tier in tier_order:
        pids = [pid for pid, cls in classifications.items() if cls == tier]
        correct_in_tier = sum(1 for pid in pids if scores[pid]["correct"])
        if pids:
            avg_score = sum(scores[pid]["score"] for pid in pids) / len(pids)
            print(f"    {tier:<12}: {len(pids):>3} problems | "
                  f"{correct_in_tier}/{len(pids)} correct | "
                  f"avg score: {avg_score:.1f}")

    return classifications


def hard_problem_comparison(problems, scores, classifications):
    """For hard/impossible problems, compare successful vs failed attempts."""
    print("\n" + "=" * 80)
    print("HARD PROBLEM DEEP DIVE")
    print("=" * 80)

    hard_pids = {pid for pid, cls in classifications.items() if cls in ("HARD", "IMPOSSIBLE")}
    hard_problems = [p for p in problems if p.problem_id in hard_pids]

    if not hard_problems:
        print("  No hard/impossible problems found.")
        return

    for p in hard_problems:
        s = scores[p.problem_id]
        cls = classifications[p.problem_id]
        print(f"\n  Problem {p.problem_id} [{cls}] (score={s['score']:.1f})")
        print(f"  Text: {p.problem_text[:120]}...")
        print(f"  Expected: {p.expected} | Predicted: {p.predicted} | Correct: {p.correct}")

        # Categorize attempts
        correct_atts = [a for a in p.attempts if classify_attempt(a, p) == "correct"]
        wrong_atts = [a for a in p.attempts if classify_attempt(a, p) == "wrong"]
        none_atts = [a for a in p.attempts if a.is_none]

        print(f"  Attempts: {len(correct_atts)} correct, {len(wrong_atts)} wrong, {len(none_atts)} none")

        if p.votes:
            print(f"  Votes: {dict(sorted(p.votes.items(), key=lambda x: x[1], reverse=True))}")

        # Compare correct vs failed
        if correct_atts and (wrong_atts or none_atts):
            c_turns = sum(len(a.turns) for a in correct_atts) / len(correct_atts)
            f_atts = wrong_atts + none_atts
            f_turns = sum(len(a.turns) for a in f_atts) / len(f_atts)
            c_errors = sum(a.errors for a in correct_atts) / len(correct_atts)
            f_errors = sum(a.errors for a in f_atts) / len(f_atts)
            c_code = sum(sum(len(t.code) for t in a.turns) for a in correct_atts) / len(correct_atts)
            f_code = sum(sum(len(t.code) for t in a.turns) for a in f_atts) / len(f_atts)

            print(f"    Correct vs Failed:")
            print(f"      Avg turns:     {c_turns:.1f} vs {f_turns:.1f}")
            print(f"      Avg errors:    {c_errors:.1f} vs {f_errors:.1f}")
            print(f"      Avg code len:  {c_code:.0f} vs {f_code:.0f}")


def topic_detection(problems):
    """Detect mathematical topic from reasoning text."""
    print("\n" + "=" * 80)
    print("TOPIC DETECTION AND ERROR RATES")
    print("=" * 80)

    topic_patterns = {
        "Number Theory": [r"modular", r"modulo", r"mod\s+\d", r"prime", r"divisib",
                          r"gcd", r"lcm", r"congruence", r"residue", r"euler",
                          r"fermat", r"diophantine", r"coprime"],
        "Algebra": [r"polynomial", r"equation", r"solve", r"root", r"coefficient",
                    r"quadratic", r"linear system", r"matrix", r"determinant",
                    r"eigenvalue", r"inequalit"],
        "Combinatorics": [r"combin", r"permut", r"binomial", r"choose", r"counting",
                          r"arrangement", r"selection", r"pigeonhole",
                          r"inclusion.exclusion", r"catalan", r"recurrence"],
        "Geometry": [r"triangle", r"circle", r"angle", r"polygon", r"area",
                     r"perimeter", r"coordinate", r"distance", r"point",
                     r"parallel", r"perpendicular", r"tangent", r"inscribe"],
        "Functions": [r"function", r"injective", r"surjective", r"bijective",
                      r"functional equation", r"composition", r"inverse"],
        "Sequences": [r"sequence", r"series", r"arithmetic", r"geometric",
                      r"fibonacci", r"recurrence relation", r"telescop"],
        "Probability": [r"probability", r"expected value", r"random",
                        r"independent", r"conditional"],
        "Game Theory": [r"game", r"strategy", r"alice.*bob", r"winning",
                        r"optimal", r"first player", r"second player"],
    }

    problem_topics = {}
    for p in problems:
        # Collect all reasoning from all attempts
        all_reasoning = " ".join(
            t.reasoning_text.lower()
            for a in p.attempts for t in a.turns if t.reasoning_text
        )

        detected = []
        for topic, patterns in topic_patterns.items():
            match_count = sum(len(re.findall(pat, all_reasoning)) for pat in patterns)
            if match_count >= 2:
                detected.append((topic, match_count))

        detected.sort(key=lambda x: x[1], reverse=True)
        problem_topics[p.problem_id] = [t[0] for t in detected[:3]] if detected else ["Unknown"]

    # Aggregate topic stats
    topic_stats = defaultdict(lambda: {"total": 0, "correct": 0, "none_rate": 0.0, "avg_time": 0.0})
    for p in problems:
        for topic in problem_topics.get(p.problem_id, ["Unknown"]):
            ts = topic_stats[topic]
            ts["total"] += 1
            if p.correct:
                ts["correct"] += 1
            nones = sum(1 for a in p.attempts if a.is_none)
            ts["none_rate"] += nones / len(p.attempts) if p.attempts else 0
            ts["avg_time"] += p.wall_time

    print(f"\n  {'Topic':<20} {'Problems':>8} {'Correct':>8} {'Corr%':>8} {'AvgNone%':>10} {'AvgTime':>8}")
    print("  " + "-" * 65)

    for topic in sorted(topic_stats, key=lambda t: topic_stats[t]["total"], reverse=True):
        ts = topic_stats[topic]
        n = ts["total"]
        corr_pct = ts["correct"] / n * 100
        avg_none = ts["none_rate"] / n * 100
        avg_time = ts["avg_time"] / n
        print(f"  {topic:<20} {n:>8} {ts['correct']:>8} {corr_pct:>7.1f}% {avg_none:>9.1f}% {avg_time:>7.0f}s")

    # Show topic assignment for each problem
    print(f"\n  PROBLEM TOPIC ASSIGNMENTS:")
    for p in sorted(problems, key=lambda p: p.problem_id):
        topics = problem_topics.get(p.problem_id, ["Unknown"])
        correct_mark = "OK" if p.correct else "FAIL"
        print(f"    {p.problem_id}: [{correct_mark}] {', '.join(topics)}")

    return problem_topics


def none_vs_answered_comparison(problems):
    """Statistical comparison of problems with high none rate vs low."""
    print("\n" + "=" * 80)
    print("HIGH-NONE vs LOW-NONE PROBLEM COMPARISON")
    print("=" * 80)

    high_none = []
    low_none = []
    for p in problems:
        if not p.attempts:
            continue
        none_rate = sum(1 for a in p.attempts if a.is_none) / len(p.attempts)
        if none_rate >= 0.5:
            high_none.append(p)
        else:
            low_none.append(p)

    for label, group in [("HIGH None (>=50%)", high_none), ("LOW None (<50%)", low_none)]:
        if not group:
            continue
        correct = sum(1 for p in group if p.correct)
        avg_time = sum(p.wall_time for p in group) / len(group)
        avg_errors = sum(p.total_errors for p in group) / len(group)
        avg_turns = sum(len(a.turns) for p in group for a in p.attempts) / sum(len(p.attempts) for p in group)
        avg_code = sum(
            sum(len(t.code) for t in a.turns)
            for p in group for a in p.attempts
        ) / sum(len(p.attempts) for p in group)

        print(f"\n  {label} ({len(group)} problems):")
        print(f"    Correct: {correct}/{len(group)} ({correct/len(group)*100:.0f}%)")
        print(f"    Avg wall time: {avg_time:.0f}s")
        print(f"    Avg errors/problem: {avg_errors:.1f}")
        print(f"    Avg turns/attempt: {avg_turns:.1f}")
        print(f"    Avg code chars/attempt: {avg_code:.0f}")


def problem_correlation_matrix(problems, scores):
    """Show correlations between difficulty factors."""
    print("\n" + "=" * 80)
    print("DIFFICULTY FACTOR CORRELATIONS")
    print("=" * 80)

    # Simple correlation: for each pair of factors, show how they move together
    factors = ["error_rate", "none_rate", "vote_margin", "avg_turns"]
    factor_vals = defaultdict(list)
    for pid, s in scores.items():
        for f in factors:
            factor_vals[f].append(s[f])

    def simple_corr(xs, ys):
        n = len(xs)
        if n < 3:
            return 0
        mx, my = sum(xs)/n, sum(ys)/n
        sx = sum((x - mx)**2 for x in xs)**0.5
        sy = sum((y - my)**2 for y in ys)**0.5
        if sx == 0 or sy == 0:
            return 0
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (n * sx * sy) * n

    print(f"\n  Pearson correlations between difficulty factors:")
    print(f"  {'':>15}", end="")
    for f in factors:
        print(f" {f[:10]:>12}", end="")
    print()
    print("  " + "-" * 65)
    for f1 in factors:
        print(f"  {f1[:14]:<15}", end="")
        for f2 in factors:
            r = simple_corr(factor_vals[f1], factor_vals[f2])
            print(f" {r:>12.3f}", end="")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/problem_difficulty.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    print(f"Loaded {len(problems)} problems")
    print()

    scores = compute_difficulty_scores(problems)
    classifications = difficulty_classification(problems, scores)
    hard_problem_comparison(problems, scores, classifications)
    topic_detection(problems)
    none_vs_answered_comparison(problems)
    problem_correlation_matrix(problems, scores)


if __name__ == "__main__":
    main()
