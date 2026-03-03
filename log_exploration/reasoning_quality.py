#!/usr/bin/env python3
"""
Reasoning Quality Analyzer for AIMO3 Logs
==========================================
Analyzes reasoning text patterns to find what distinguishes successful from failed attempts.

Usage: python3 log_exploration/reasoning_quality.py output/v22/diagnostic.log
"""

import sys
import re
from collections import Counter, defaultdict

sys.path.insert(0, '/Users/intern/Desktop/sideprojects/aimo3')
from log_exploration.log_query import parse_log


def get_full_reasoning(attempt):
    """Concatenate all reasoning text across turns."""
    return "\n".join(t.reasoning_text for t in attempt.turns if t.reasoning_text)


def classify_attempt(attempt, problem):
    """Classify attempt as correct, wrong, or none."""
    if attempt.is_none:
        return "none"
    if problem.expected is not None and attempt.answer == problem.expected:
        return "correct"
    return "wrong"


def reasoning_length_analysis(problems):
    """Compare reasoning length distributions across outcome categories."""
    print("=" * 80)
    print("REASONING LENGTH ANALYSIS")
    print("=" * 80)

    lengths = {"correct": [], "wrong": [], "none": []}
    char_counts = {"correct": [], "wrong": [], "none": []}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            full = get_full_reasoning(a)
            lengths[cat].append(len(full))
            char_counts[cat].append(sum(t.reasoning_chars for t in a.turns))

    for cat in ["correct", "wrong", "none"]:
        vals = lengths[cat]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        med = sorted(vals)[len(vals) // 2]
        mn, mx = min(vals), max(vals)
        print(f"\n  {cat.upper()} attempts ({len(vals)} total):")
        print(f"    Mean reasoning length: {avg:,.0f} chars")
        print(f"    Median:               {med:,.0f} chars")
        print(f"    Range:                {mn:,.0f} - {mx:,.0f} chars")
        print(f"    Total chars:          {sum(vals):,.0f}")

    # Per-turn reasoning length
    print(f"\n  Per-Turn Reasoning Length:")
    for cat in ["correct", "wrong", "none"]:
        turn_lens = []
        for p in problems:
            for a in p.attempts:
                if classify_attempt(a, p) == cat:
                    for t in a.turns:
                        if t.reasoning_text:
                            turn_lens.append(len(t.reasoning_text))
        if turn_lens:
            avg = sum(turn_lens) / len(turn_lens)
            print(f"    {cat.upper()}: {avg:,.0f} avg chars/turn ({len(turn_lens)} turns)")


def keyword_correlation_analysis(problems):
    """Find keywords/phrases that correlate with success or failure."""
    print("\n" + "=" * 80)
    print("KEYWORD CORRELATION ANALYSIS")
    print("=" * 80)

    # Keywords to check — organized by hypothesis
    success_indicators = [
        "let's verify", "let me verify", "verification", "double check", "double-check",
        "brute force", "brute-force", "enumerate", "exhaustive",
        "modular arithmetic", "modulo", "mod ",
        "by induction", "base case", "inductive",
        "substitut", "let x =", "let n =",
        "simplif", "factor", "factoring",
        "therefore", "hence", "thus we have",
        "the answer is", "final answer",
        "systematic", "case analysis", "cases:",
        "recurrence", "recursive", "recursion",
        "generating function", "polynomial",
        "pigeonhole", "counting argument",
    ]

    failure_indicators = [
        "i think", "i believe", "probably", "maybe", "perhaps",
        "let me try", "let's try", "try another", "try a different",
        "not sure", "uncertain", "unclear",
        "approximate", "estimation", "roughly",
        "hmm", "wait", "actually",
        "this is tricky", "this is hard", "this is difficult", "this is complex",
        "wrong approach", "doesn't work", "that failed",
        "too slow", "timeout", "timed out", "takes too long",
        "let me reconsider", "reconsider",
        "i made an error", "i made a mistake", "mistake",
        "start over", "from scratch", "restart",
        "confused", "confusing",
    ]

    # Count keyword occurrences by category
    print("\n  SUCCESS-CORRELATED KEYWORDS:")
    print(f"  {'Keyword':<30} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Corr%':>8}")
    print("  " + "-" * 70)

    keyword_stats = []
    for kw in success_indicators:
        counts = {"correct": 0, "wrong": 0, "none": 0}
        totals = {"correct": 0, "wrong": 0, "none": 0}
        for p in problems:
            for a in p.attempts:
                cat = classify_attempt(a, p)
                totals[cat] += 1
                reasoning = get_full_reasoning(a).lower()
                if kw.lower() in reasoning:
                    counts[cat] += 1
        total = sum(counts.values())
        if total > 0:
            corr_rate = counts["correct"] / total * 100 if total else 0
            keyword_stats.append((kw, counts, totals, corr_rate))

    keyword_stats.sort(key=lambda x: x[3], reverse=True)
    for kw, counts, totals, corr_rate in keyword_stats:
        if sum(counts.values()) >= 3:  # At least 3 occurrences
            print(f"  {kw:<30} {counts['correct']:>8} {counts['wrong']:>8} {counts['none']:>8} {corr_rate:>7.1f}%")

    print(f"\n  FAILURE-CORRELATED KEYWORDS:")
    print(f"  {'Keyword':<30} {'Correct':>8} {'Wrong':>8} {'None':>8} {'None%':>8}")
    print("  " + "-" * 70)

    keyword_stats = []
    for kw in failure_indicators:
        counts = {"correct": 0, "wrong": 0, "none": 0}
        for p in problems:
            for a in p.attempts:
                cat = classify_attempt(a, p)
                reasoning = get_full_reasoning(a).lower()
                if kw.lower() in reasoning:
                    counts[cat] += 1
        total = sum(counts.values())
        if total > 0:
            none_rate = counts["none"] / total * 100 if total else 0
            keyword_stats.append((kw, counts, none_rate))

    keyword_stats.sort(key=lambda x: x[2], reverse=True)
    for kw, counts, none_rate in keyword_stats:
        if sum(counts.values()) >= 3:
            print(f"  {kw:<30} {counts['correct']:>8} {counts['wrong']:>8} {counts['none']:>8} {none_rate:>7.1f}%")


def approach_restart_analysis(problems):
    """Count how many times the model restarts its approach mid-reasoning."""
    print("\n" + "=" * 80)
    print("APPROACH RESTART ANALYSIS")
    print("=" * 80)

    restart_phrases = [
        r"wait[\s,]",
        r"actually[\s,]",
        r"let me (?:re)?try",
        r"let's (?:re)?try",
        r"(?:start|try) (?:over|again|differently|another)",
        r"that(?:'s| is) (?:wrong|incorrect|not right)",
        r"(?:doesn't|does not|didn't|did not) work",
        r"reconsider",
        r"different approach",
        r"alternative",
        r"back to",
        r"instead(?:,| let)",
        r"scratch that",
        r"no[\s,]+ (?:that|this)",
    ]

    restart_counts = {"correct": [], "wrong": [], "none": []}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            reasoning = get_full_reasoning(a).lower()
            count = 0
            for pattern in restart_phrases:
                count += len(re.findall(pattern, reasoning))
            restart_counts[cat].append(count)

    for cat in ["correct", "wrong", "none"]:
        vals = restart_counts[cat]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        total_with_restarts = sum(1 for v in vals if v > 0)
        max_restarts = max(vals) if vals else 0
        print(f"\n  {cat.upper()} ({len(vals)} attempts):")
        print(f"    Avg restarts/attempt: {avg:.2f}")
        print(f"    Attempts with any:    {total_with_restarts}/{len(vals)} ({total_with_restarts/len(vals)*100:.0f}%)")
        print(f"    Max restarts:         {max_restarts}")

    # High-restart attempts vs low
    print(f"\n  RESTART COUNT vs SUCCESS:")
    all_data = []
    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            reasoning = get_full_reasoning(a).lower()
            count = sum(len(re.findall(pat, reasoning)) for pat in restart_phrases)
            all_data.append((count, cat))

    for threshold in [0, 1, 3, 5, 10]:
        subset = [d for d in all_data if d[0] >= threshold]
        if not subset:
            continue
        correct = sum(1 for _, c in subset if c == "correct")
        none = sum(1 for _, c in subset if c == "none")
        print(f"    Restarts >= {threshold:>2}: {len(subset):>4} attempts | "
              f"correct: {correct/len(subset)*100:5.1f}% | none: {none/len(subset)*100:5.1f}%")


def planning_vs_diving_analysis(problems):
    """Check if model plans before coding vs diving straight into code."""
    print("\n" + "=" * 80)
    print("PLANNING vs DIVING ANALYSIS")
    print("=" * 80)

    planning_signals = [
        r"(?:my |the )?(?:plan|strategy|approach) (?:is|will be|:)",
        r"(?:step|first|second|third) [\d]*[:.]",
        r"(?:i'll|let me|let's|we) (?:first|start by|begin by)",
        r"outline",
        r"(?:key|main) (?:idea|insight|observation)",
        r"breaking (?:this|it) down",
        r"(?:algorithm|method|technique):",
    ]

    results = {"planned_correct": 0, "planned_wrong": 0, "planned_none": 0,
               "dived_correct": 0, "dived_wrong": 0, "dived_none": 0}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            if not a.turns:
                continue

            # Check first turn reasoning
            first_reasoning = a.turns[0].reasoning_text.lower() if a.turns[0].reasoning_text else ""

            has_plan = any(re.search(pat, first_reasoning) for pat in planning_signals)
            has_early_code = len(first_reasoning) < 500 and a.turns[0].code

            if has_plan:
                results[f"planned_{cat}"] += 1
            elif has_early_code or not first_reasoning:
                results[f"dived_{cat}"] += 1

    planned_total = results["planned_correct"] + results["planned_wrong"] + results["planned_none"]
    dived_total = results["dived_correct"] + results["dived_wrong"] + results["dived_none"]

    print(f"\n  {'Category':<20} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Corr%':>8}")
    print("  " + "-" * 60)
    if planned_total:
        print(f"  {'Planned first':<20} {results['planned_correct']:>8} {results['planned_wrong']:>8} "
              f"{results['planned_none']:>8} {planned_total:>8} "
              f"{results['planned_correct']/planned_total*100:>7.1f}%")
    if dived_total:
        print(f"  {'Dove into code':<20} {results['dived_correct']:>8} {results['dived_wrong']:>8} "
              f"{results['dived_none']:>8} {dived_total:>8} "
              f"{results['dived_correct']/dived_total*100:>7.1f}%")


def turn_depth_analysis(problems):
    """Analyze how number of turns relates to outcomes."""
    print("\n" + "=" * 80)
    print("TURN DEPTH ANALYSIS")
    print("=" * 80)

    turns_by_cat = {"correct": [], "wrong": [], "none": []}
    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            turns_by_cat[cat].append(len(a.turns))

    for cat in ["correct", "wrong", "none"]:
        vals = turns_by_cat[cat]
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        med = sorted(vals)[len(vals) // 2]
        print(f"\n  {cat.upper()} ({len(vals)} attempts):")
        print(f"    Mean turns: {avg:.1f}")
        print(f"    Median:     {med}")
        print(f"    Range:      {min(vals)} - {max(vals)}")

    # Turn count distribution
    print(f"\n  TURN COUNT vs OUTCOME:")
    print(f"  {'Turns':>6} {'Correct':>8} {'Wrong':>8} {'None':>8} {'Total':>8} {'Corr%':>8}")
    print("  " + "-" * 50)
    max_turns = max(len(a.turns) for p in problems for a in p.attempts) if problems else 0
    for t in range(1, min(max_turns + 1, 12)):
        correct = sum(1 for p in problems for a in p.attempts
                      if len(a.turns) == t and classify_attempt(a, p) == "correct")
        wrong = sum(1 for p in problems for a in p.attempts
                    if len(a.turns) == t and classify_attempt(a, p) == "wrong")
        none = sum(1 for p in problems for a in p.attempts
                   if len(a.turns) == t and classify_attempt(a, p) == "none")
        total = correct + wrong + none
        if total:
            print(f"  {t:>6} {correct:>8} {wrong:>8} {none:>8} {total:>8} "
                  f"{correct/total*100:>7.1f}%")


def reasoning_sophistication(problems):
    """Score reasoning sophistication and see if it correlates with success."""
    print("\n" + "=" * 80)
    print("REASONING SOPHISTICATION SCORING")
    print("=" * 80)

    math_concepts = {
        "number_theory": [r"modular", r"congruence", r"gcd", r"lcm", r"prime", r"euler.*totient",
                          r"fermat", r"diophantine", r"residue"],
        "algebra": [r"polynomial", r"coefficient", r"root", r"equation", r"variable",
                    r"substitut", r"quadratic", r"linear"],
        "combinatorics": [r"combin", r"permut", r"binomial", r"choose", r"counting",
                          r"pigeonhole", r"inclusion.exclusion"],
        "analysis": [r"bound", r"inequalit", r"maxim", r"minim", r"optim", r"limit"],
        "geometry": [r"triangle", r"circle", r"angle", r"polygon", r"area", r"perimeter",
                     r"coordinate"],
        "proof_techniques": [r"induction", r"contradiction", r"contraposi", r"by cases",
                             r"wlog", r"without loss"],
    }

    category_scores = {"correct": defaultdict(int), "wrong": defaultdict(int), "none": defaultdict(int)}
    category_counts = {"correct": 0, "wrong": 0, "none": 0}

    for p in problems:
        for a in p.attempts:
            cat = classify_attempt(a, p)
            category_counts[cat] += 1
            reasoning = get_full_reasoning(a).lower()
            for concept, patterns in math_concepts.items():
                if any(re.search(pat, reasoning) for pat in patterns):
                    category_scores[cat][concept] += 1

    print(f"\n  {'Concept':<25} {'Correct':>10} {'Wrong':>10} {'None':>10}")
    print("  " + "-" * 55)
    for concept in math_concepts:
        c = category_scores["correct"].get(concept, 0)
        w = category_scores["wrong"].get(concept, 0)
        n = category_scores["none"].get(concept, 0)
        ct = category_counts
        print(f"  {concept:<25} "
              f"{c:>4} ({c/ct['correct']*100:>4.0f}%) "
              f"{w:>4} ({w/ct['wrong']*100 if ct['wrong'] else 0:>4.0f}%) "
              f"{n:>4} ({n/ct['none']*100:>4.0f}%)")


def first_turn_quality(problems):
    """Analyze whether the quality of the first turn predicts the outcome."""
    print("\n" + "=" * 80)
    print("FIRST TURN QUALITY ANALYSIS")
    print("=" * 80)

    for cat_name, cat_filter in [("correct", lambda a, p: classify_attempt(a, p) == "correct"),
                                  ("wrong", lambda a, p: classify_attempt(a, p) == "wrong"),
                                  ("none", lambda a, p: classify_attempt(a, p) == "none")]:
        first_lens = []
        first_has_code = 0
        first_code_has_error = 0
        total = 0
        for p in problems:
            for a in p.attempts:
                if not cat_filter(a, p) or not a.turns:
                    continue
                total += 1
                t = a.turns[0]
                first_lens.append(len(t.reasoning_text))
                if t.code:
                    first_has_code += 1
                if t.is_error:
                    first_code_has_error += 1

        if not total:
            continue
        avg_len = sum(first_lens) / len(first_lens) if first_lens else 0
        print(f"\n  {cat_name.upper()} ({total} attempts):")
        print(f"    Avg first-turn reasoning: {avg_len:,.0f} chars")
        print(f"    First turn has code:      {first_has_code}/{total} ({first_has_code/total*100:.0f}%)")
        print(f"    First turn has error:     {first_code_has_error}/{total} ({first_code_has_error/total*100:.0f}%)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/reasoning_quality.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    print(f"Loaded {len(problems)} problems with {sum(len(p.attempts) for p in problems)} total attempts")
    print(f"Correct problems: {sum(1 for p in problems if p.correct)}/{len(problems)}")
    print()

    reasoning_length_analysis(problems)
    keyword_correlation_analysis(problems)
    approach_restart_analysis(problems)
    planning_vs_diving_analysis(problems)
    turn_depth_analysis(problems)
    reasoning_sophistication(problems)
    first_turn_quality(problems)


if __name__ == "__main__":
    main()
