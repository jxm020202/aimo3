#!/usr/bin/env python3
"""
Voting Analysis for AIMO3 Solver
=================================
Analyzes vote distributions, first-correct-attempt, early stop impact,
alternative voting strategies, and entropy distributions.

Usage: python3 log_exploration/voting_analysis.py output/v22/diagnostic.log
"""

import sys
import os
import math
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def mean(vals):
    return sum(vals) / len(vals) if vals else 0


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    n = len(s)
    if n % 2 == 0:
        return (s[n // 2 - 1] + s[n // 2]) / 2
    return s[n // 2]


def stdev(vals):
    if len(vals) < 2:
        return 0
    m = mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))


def entropy(counts):
    """Shannon entropy of a distribution given counts."""
    total = sum(counts)
    if total == 0:
        return 0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def analyze_vote_distribution(problems):
    """Vote distribution for correct vs wrong problems."""
    print_section("VOTE DISTRIBUTION")

    correct_problems = [p for p in problems if p.correct and p.votes]
    wrong_problems = [p for p in problems if not p.correct and p.votes]

    print(f"\n  Correct problems: {len(correct_problems)}, Wrong problems: {len(wrong_problems)}")

    # Winning vote count
    correct_winner_votes = []
    wrong_winner_votes = []

    for p in correct_problems:
        if p.votes:
            winner_votes = max(p.votes.values())
            correct_winner_votes.append(winner_votes)

    for p in wrong_problems:
        if p.votes:
            winner_votes = max(p.votes.values())
            wrong_winner_votes.append(winner_votes)

    print(f"\n  Winning Vote Count:")
    print(f"  {'Category':<20} {'Count':>6} {'Mean':>8} {'Median':>8} {'Min':>6} {'Max':>6}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 6} {'─' * 6}")
    if correct_winner_votes:
        print(f"  {'Correct':<20} {len(correct_winner_votes):>6} {mean(correct_winner_votes):>8.1f} {median(correct_winner_votes):>8.1f} {min(correct_winner_votes):>6} {max(correct_winner_votes):>6}")
    if wrong_winner_votes:
        print(f"  {'Wrong':<20} {len(wrong_winner_votes):>6} {mean(wrong_winner_votes):>8.1f} {median(wrong_winner_votes):>8.1f} {min(wrong_winner_votes):>6} {max(wrong_winner_votes):>6}")

    # Number of distinct answers voted on
    correct_distinct = [len(p.votes) for p in correct_problems]
    wrong_distinct = [len(p.votes) for p in wrong_problems]

    print(f"\n  Distinct Answers in Voting:")
    print(f"  {'Category':<20} {'Mean':>8} {'Median':>8} {'Min':>6} {'Max':>6}")
    print(f"  {'─' * 20} {'─' * 8} {'─' * 8} {'─' * 6} {'─' * 6}")
    if correct_distinct:
        print(f"  {'Correct':<20} {mean(correct_distinct):>8.1f} {median(correct_distinct):>8.1f} {min(correct_distinct):>6} {max(correct_distinct):>6}")
    if wrong_distinct:
        print(f"  {'Wrong':<20} {mean(wrong_distinct):>8.1f} {median(wrong_distinct):>8.1f} {min(wrong_distinct):>6} {max(wrong_distinct):>6}")

    # Vote margin (winner - runner up)
    print(f"\n  Vote Margin (winner - runner-up):")
    print(f"  {'Problem':<10} {'OK':>4} {'Winner':>10} {'Votes':>6} {'Runner-up':>10} {'RU Votes':>8} {'Margin':>7}")
    print(f"  {'─' * 10} {'─' * 4} {'─' * 10} {'─' * 6} {'─' * 10} {'─' * 8} {'─' * 7}")

    all_problems_sorted = sorted(problems, key=lambda p: _vote_margin(p))
    for p in all_problems_sorted:
        if not p.votes:
            continue
        sorted_votes = sorted(p.votes.items(), key=lambda x: -x[1])
        winner_ans, winner_count = sorted_votes[0]
        ru_ans = sorted_votes[1][0] if len(sorted_votes) > 1 else "-"
        ru_count = sorted_votes[1][1] if len(sorted_votes) > 1 else 0
        margin = winner_count - ru_count
        ok = "Y" if p.correct else "N"
        print(f"  {p.problem_id:<10} {ok:>4} {winner_ans:>10} {winner_count:>6} {str(ru_ans):>10} {ru_count:>8} {margin:>7}")


def _vote_margin(p):
    if not p.votes:
        return 999
    sorted_votes = sorted(p.votes.values(), reverse=True)
    return sorted_votes[0] - (sorted_votes[1] if len(sorted_votes) > 1 else 0)


def analyze_first_correct(problems):
    """First-correct-attempt analysis: which attempt number first finds the right answer?"""
    print_section("FIRST CORRECT ATTEMPT ANALYSIS")

    first_correct = Counter()
    never_correct = 0
    total = 0

    for p in problems:
        if p.expected is None:
            continue
        total += 1
        found = False
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            if a.answer == p.expected:
                first_correct[a.attempt_num] += 1
                found = True
                break
        if not found:
            never_correct += 1

    print(f"\n  When does the correct answer first appear? ({total} problems)")
    print(f"  {'Attempt #':<12} {'Count':>8} {'Cumulative':>12} {'% Solved':>10}")
    print(f"  {'─' * 12} {'─' * 8} {'─' * 12} {'─' * 10}")
    cumulative = 0
    max_att = max((a.attempt_num for p in problems for a in p.attempts), default=8)
    for n in range(1, max_att + 1):
        count = first_correct.get(n, 0)
        cumulative += count
        pct = 100 * cumulative / total if total > 0 else 0
        bar = '#' * count
        print(f"  {n:<12} {count:>8} {cumulative:>12} {pct:>9.1f}%  {bar}")
    print(f"  {'Never':<12} {never_correct:>8} {cumulative:>12} {100*cumulative/total if total else 0:>9.1f}%")

    # Time to first correct
    print(f"\n  Time to First Correct Answer:")
    times_to_first = []
    for p in problems:
        if p.expected is None:
            continue
        cum_time = 0
        for a in sorted(p.attempts, key=lambda x: x.attempt_num):
            cum_time += a.time_s
            if a.answer == p.expected:
                times_to_first.append(cum_time)
                break
    if times_to_first:
        print(f"  Mean: {mean(times_to_first):.1f}s | Median: {median(times_to_first):.1f}s | Max: {max(times_to_first):.1f}s")


def analyze_early_stop_impact(problems):
    """If we changed early stop threshold, what would happen?"""
    print_section("EARLY STOP THRESHOLD ANALYSIS")

    print(f"\n  Simulating different early stop thresholds...")
    print(f"  (Early stop = stop after N matching answers)")
    print(f"\n  {'Threshold':<12} {'Score':>8} {'Avg Attempts':>14} {'Avg Time':>10} {'Notes':<30}")
    print(f"  {'─' * 12} {'─' * 8} {'─' * 14} {'─' * 10} {'─' * 30}")

    total_with_expected = sum(1 for p in problems if p.expected is not None)

    # Auto-detect base attempts and rerun threshold
    attempt_counts = Counter(len(p.attempts) for p in problems)
    base_attempts = attempt_counts.most_common(1)[0][0] if attempt_counts else 8
    actual_threshold = max(1, (base_attempts + 2) // 3)  # ceil(attempts/3)

    # Simulate thresholds up to base_attempts
    thresholds = sorted(set(range(1, min(base_attempts + 1, 20))) | {actual_threshold})

    for threshold in thresholds:
        score = 0
        total_attempts_used = 0
        total_time_used = 0

        for p in problems:
            if p.expected is None:
                continue

            # Simulate: run attempts in order, stop when threshold matching
            votes = defaultdict(int)
            best_answer = None
            best_count = 0
            attempts_used = 0
            time_used = 0

            for a in sorted(p.attempts, key=lambda x: x.attempt_num):
                attempts_used += 1
                time_used += a.time_s
                if a.answer is not None:
                    votes[a.answer] += 1
                    if votes[a.answer] > best_count:
                        best_count = votes[a.answer]
                        best_answer = a.answer

                # Check early stop condition
                if best_count >= threshold:
                    break

            total_attempts_used += attempts_used
            total_time_used += time_used

            if best_answer == p.expected:
                score += 1

        avg_att = total_attempts_used / total_with_expected if total_with_expected else 0
        avg_time = total_time_used / total_with_expected if total_with_expected else 0
        actual = f" (actual rerun threshold ceil({base_attempts}/3))" if threshold == actual_threshold else ""
        no_stop = " (no early stop)" if threshold == base_attempts else ""
        print(f"  {threshold:<12} {score:>5}/{total_with_expected} {avg_att:>14.1f} {avg_time:>9.1f}s{actual}{no_stop}")

    print(f"\n  NOTE: Threshold={base_attempts} means 'no early stop' (run all {base_attempts}).")
    print(f"  Lower thresholds save time but risk incorrect majority votes.")


def analyze_alternative_voting(problems):
    """Simulate alternative voting strategies."""
    print_section("ALTERNATIVE VOTING STRATEGIES")

    strategies = {
        "Majority (simple)": _vote_majority,
        "Majority (drop Nones)": _vote_majority_drop_nones,
        "First non-None": _vote_first,
        "Last non-None": _vote_last,
        "Most common (top-1)": _vote_most_common,
        "Entropy-weighted": _vote_entropy_weighted,
        "Low-entropy only": _vote_low_entropy,
    }

    total = sum(1 for p in problems if p.expected is not None)
    print(f"\n  {'Strategy':<25} {'Score':>8} {'Accuracy':>10} {'Diff vs Majority':>16}")
    print(f"  {'─' * 25} {'─' * 8} {'─' * 10} {'─' * 16}")

    baseline_score = None
    for name, fn in strategies.items():
        score = 0
        for p in problems:
            if p.expected is None:
                continue
            predicted = fn(p)
            if predicted == p.expected:
                score += 1

        if baseline_score is None:
            baseline_score = score
        diff = score - baseline_score
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        print(f"  {name:<25} {score:>5}/{total} {100*score/total if total else 0:>9.1f}% {diff_str:>16}")

    # Show where strategies disagree
    print(f"\n  Problems Where Strategies Disagree:")
    print(f"  {'Problem':<10} {'Expected':>10} {'Majority':>10} {'Entropy-wt':>10} {'First':>10} {'Low-ent':>10}")
    print(f"  {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10} {'─' * 10}")

    for p in problems:
        if p.expected is None:
            continue
        maj = _vote_majority(p)
        ew = _vote_entropy_weighted(p)
        first = _vote_first(p)
        low = _vote_low_entropy(p)
        if len(set(filter(None, [maj, ew, first, low]))) > 1:
            print(f"  {p.problem_id:<10} {p.expected:>10} {str(maj):>10} {str(ew):>10} {str(first):>10} {str(low):>10}")


def _vote_majority(p):
    """Simple majority vote."""
    if not p.votes:
        return None
    return max(p.votes, key=p.votes.get)


def _vote_majority_drop_nones(p):
    """Majority vote excluding None answers."""
    votes = {k: v for k, v in p.votes.items() if k is not None}
    return max(votes, key=votes.get) if votes else None


def _vote_first(p):
    """First non-None answer."""
    for a in sorted(p.attempts, key=lambda x: x.attempt_num):
        if a.answer is not None:
            return a.answer
    return None


def _vote_last(p):
    """Last non-None answer."""
    for a in sorted(p.attempts, key=lambda x: -x.attempt_num):
        if a.answer is not None:
            return a.answer
    return None


def _vote_most_common(p):
    """Most common answer (same as majority)."""
    return _vote_majority(p)


def _vote_entropy_weighted(p):
    """Vote weighted by inverse entropy (low entropy = more confident)."""
    weighted_votes = defaultdict(float)
    for a in p.attempts:
        if a.answer is not None:
            weight = 1.0 / (1.0 + a.entropy)  # lower entropy = higher weight
            weighted_votes[a.answer] += weight
    return max(weighted_votes, key=weighted_votes.get) if weighted_votes else None


def _vote_low_entropy(p):
    """Only count votes from attempts with entropy < median entropy."""
    entropies = [a.entropy for a in p.attempts if a.answer is not None]
    if not entropies:
        return None
    threshold = sorted(entropies)[len(entropies) // 2]
    votes = defaultdict(int)
    for a in p.attempts:
        if a.answer is not None and a.entropy <= threshold:
            votes[a.answer] += 1
    return max(votes, key=votes.get) if votes else _vote_majority(p)


def analyze_entropy_distribution(problems):
    """Entropy distribution: correct answers vs wrong answers vs Nones."""
    print_section("ENTROPY DISTRIBUTION")

    correct_entropies = []
    wrong_entropies = []
    none_entropies = []

    for p in problems:
        for a in p.attempts:
            if a.is_none:
                none_entropies.append(a.entropy)
            elif a.answer is not None and p.expected is not None and a.answer == p.expected:
                correct_entropies.append(a.entropy)
            elif a.answer is not None:
                wrong_entropies.append(a.entropy)

    print(f"\n  {'Category':<20} {'Count':>6} {'Mean':>8} {'Median':>8} {'Stdev':>8} {'Min':>6} {'Max':>6}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 8} {'─' * 6} {'─' * 6}")
    for label, vals in [("Correct", correct_entropies), ("Wrong", wrong_entropies), ("None", none_entropies)]:
        if vals:
            print(f"  {label:<20} {len(vals):>6} {mean(vals):>8.3f} {median(vals):>8.3f} {stdev(vals):>8.3f} {min(vals):>6.3f} {max(vals):>6.3f}")

    # Problem-level avg entropy
    print(f"\n  Problem-Level Average Entropy:")
    correct_prob_ent = [p.avg_entropy for p in problems if p.correct]
    wrong_prob_ent = [p.avg_entropy for p in problems if not p.correct]

    print(f"  {'Category':<20} {'Count':>6} {'Mean':>8} {'Median':>8}")
    print(f"  {'─' * 20} {'─' * 6} {'─' * 8} {'─' * 8}")
    if correct_prob_ent:
        print(f"  {'Correct problems':<20} {len(correct_prob_ent):>6} {mean(correct_prob_ent):>8.3f} {median(correct_prob_ent):>8.3f}")
    if wrong_prob_ent:
        print(f"  {'Wrong problems':<20} {len(wrong_prob_ent):>6} {mean(wrong_prob_ent):>8.3f} {median(wrong_prob_ent):>8.3f}")

    # Entropy histogram
    print(f"\n  Entropy Histogram (all attempts):")
    all_ent = correct_entropies + wrong_entropies + none_entropies
    if all_ent:
        bins = [(0, 0.1), (0.1, 0.3), (0.3, 0.5), (0.5, 0.8), (0.8, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, float('inf'))]
        labels = ["0-0.1", "0.1-0.3", "0.3-0.5", "0.5-0.8", "0.8-1.0", "1.0-1.5", "1.5-2.0", "2.0+"]
        for (lo, hi), label in zip(bins, labels):
            c = sum(1 for e in correct_entropies if lo <= e < hi)
            w = sum(1 for e in wrong_entropies if lo <= e < hi)
            n = sum(1 for e in none_entropies if lo <= e < hi)
            total_bin = c + w + n
            bar_c = 'C' * c
            bar_w = 'W' * w
            bar_n = '.' * min(n, 20)  # cap None display
            print(f"  {label:>7} | {bar_c}{bar_w}{bar_n} (C:{c} W:{w} N:{n})")


def print_actionable_insights(problems):
    """Summarize key findings."""
    print_section("ACTIONABLE INSIGHTS")

    total = sum(1 for p in problems if p.expected is not None)

    # 1. Voting confidence
    tight_margin = sum(1 for p in problems if _vote_margin(p) <= 1 and p.expected is not None)
    print(f"\n  1. VOTE CONFIDENCE: {tight_margin} problems have margin <= 1 (winner beats runner-up by 0-1 votes).")
    print(f"     These are fragile — one different attempt could flip the answer.")
    print(f"     RECOMMENDATION: For tight votes, consider running more attempts or using entropy weighting.")

    # 2. Early stop
    es_correct = sum(1 for p in problems if p.early_stop and p.correct)
    es_wrong = sum(1 for p in problems if p.early_stop and not p.correct)
    print(f"\n  2. EARLY STOP: {es_correct} correct + {es_wrong} wrong among early-stopped problems.")
    if es_wrong > 0:
        wrong_es = [p for p in problems if p.early_stop and not p.correct]
        for p in wrong_es:
            print(f"     Problem {p.problem_id}: Predicted {p.predicted}, Expected {p.expected}, Votes: {p.votes}")
        print(f"     RECOMMENDATION: Early stop can lock in wrong answers. Consider requiring higher threshold for hard problems.")

    # 3. None impact
    total_nones = sum(1 for p in problems for a in p.attempts if a.is_none)
    total_atts = sum(len(p.attempts) for p in problems)
    print(f"\n  3. NONE IMPACT: {total_nones}/{total_atts} attempts returned None ({100*total_nones/total_atts:.0f}%).")
    print(f"     Each None is a wasted vote that could have contributed to consensus.")
    print(f"     RECOMMENDATION: Reducing None rate is the single highest-impact improvement.")

    # 4. Entropy as signal
    correct_ent = [a.entropy for p in problems for a in p.attempts if not a.is_none and a.answer == p.expected]
    wrong_ent = [a.entropy for p in problems for a in p.attempts if not a.is_none and a.answer is not None and a.answer != p.expected]
    if correct_ent and wrong_ent:
        print(f"\n  4. ENTROPY SIGNAL: Correct answers have mean entropy {mean(correct_ent):.3f}, wrong have {mean(wrong_ent):.3f}.")
        if mean(correct_ent) < mean(wrong_ent):
            print(f"     Lower entropy correlates with correctness — entropy weighting is justified.")
        else:
            print(f"     Entropy does NOT strongly discriminate correct from wrong here.")
    print()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: File not found: {logfile}")
        sys.exit(1)

    print(f"Parsing {logfile}...")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems.")

    analyze_vote_distribution(problems)
    analyze_first_correct(problems)
    analyze_early_stop_impact(problems)
    analyze_alternative_voting(problems)
    analyze_entropy_distribution(problems)
    print_actionable_insights(problems)


if __name__ == "__main__":
    main()
