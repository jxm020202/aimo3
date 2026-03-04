#!/usr/bin/env python3
"""
Confident Wrong Analysis
========================
Finds problems where the model is confidently wrong:
- All/most attempts agree on the SAME wrong answer
- High vote margin but wrong
- Distribution of unique answers per problem (1=unanimous, 16=chaos)

Also: Do vboxed checkpoints ever save answers that boxed misses?
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log
from collections import Counter


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 confident_wrong_analysis.py <logfile>")
        sys.exit(1)

    problems = parse_log(sys.argv[1])
    print(f"Loaded {len(problems)} problems\n")

    # ── 1. Answer Diversity Distribution ──
    print("=" * 80)
    print("  ANSWER DIVERSITY DISTRIBUTION")
    print("  (How many unique answers per problem?)")
    print("=" * 80)
    print()
    print(f"  {'PID':<12} {'OK':<5} {'Answers':<4} {'Nones':<5} {'Unique':<6} {'Top Vote':<10} {'Top Ans':<10} {'Expected':<10} {'Distribution'}")
    print("  " + "-" * 110)

    diversity_data = []
    for p in problems:
        answers = [a.answer for a in p.attempts if a.answer is not None]
        nones = sum(1 for a in p.attempts if a.answer is None)
        unique = len(set(answers))
        vote_counts = Counter(answers)
        if vote_counts:
            top_ans, top_count = vote_counts.most_common(1)[0]
        else:
            top_ans, top_count = None, 0

        ok = "Y" if p.correct else "N"
        dist_str = ", ".join(f"{ans}:{cnt}" for ans, cnt in vote_counts.most_common(5))
        print(f"  {p.problem_id:<12} {ok:<5} {len(answers):<4} {nones:<5} {unique:<6} {top_count:<10} {str(top_ans):<10} {str(p.expected):<10} {dist_str}")
        diversity_data.append((p, unique, nones, top_count, top_ans, answers))

    # ── 2. Confident Wrong Problems ──
    print()
    print("=" * 80)
    print("  CONFIDENT WRONG PROBLEMS")
    print("  (Wrong answer chosen with high agreement)")
    print("=" * 80)
    print()

    confident_wrong = []
    for p, unique, nones, top_count, top_ans, answers in diversity_data:
        if not p.correct and top_count >= 3:
            agreement_pct = top_count / len(answers) * 100 if answers else 0
            confident_wrong.append((p, unique, top_count, top_ans, agreement_pct, answers))

    confident_wrong.sort(key=lambda x: x[4], reverse=True)

    for p, unique, top_count, top_ans, agreement_pct, answers in confident_wrong:
        correct_in_attempts = sum(1 for a in answers if a == p.expected)
        print(f"  Problem: {p.problem_id}")
        print(f"    Expected: {p.expected} | Predicted: {p.predicted}")
        print(f"    Top wrong answer: {top_ans} ({top_count}/{len(answers)} = {agreement_pct:.0f}% agreement)")
        print(f"    Unique answers: {unique}")
        print(f"    Correct answer in attempts: {correct_in_attempts}/{len(answers)}")
        print(f"    Votes: {dict(Counter(answers).most_common())}")
        if correct_in_attempts > 0:
            print(f"    >>> RECOVERABLE: Correct answer exists but outvoted!")
        else:
            print(f"    >>> SYSTEMATIC: Model never finds correct answer")
        print()

    # ── 3. Unanimous Problems ──
    print("=" * 80)
    print("  UNANIMOUS PROBLEMS (all attempts agree)")
    print("=" * 80)
    print()

    unanimous_correct = 0
    unanimous_wrong = 0
    for p, unique, nones, top_count, top_ans, answers in diversity_data:
        if unique == 1 and len(answers) > 0:
            if p.correct:
                unanimous_correct += 1
            else:
                unanimous_wrong += 1
                print(f"  UNANIMOUS WRONG: {p.problem_id}")
                print(f"    All {len(answers)} attempts answered: {top_ans}")
                print(f"    Expected: {p.expected}")
                print(f"    Diff: {top_ans - p.expected if p.expected else 'N/A'}")
                print()

    print(f"  Summary: {unanimous_correct} unanimous correct, {unanimous_wrong} unanimous wrong")
    print()

    # ── 4. Chaotic Problems (many unique answers) ──
    print("=" * 80)
    print("  CHAOTIC PROBLEMS (high answer diversity)")
    print("=" * 80)
    print()

    chaotic = [(p, u, n, tc, ta, ans) for p, u, n, tc, ta, ans in diversity_data if u >= 5]
    chaotic.sort(key=lambda x: x[1], reverse=True)

    for p, unique, nones, top_count, top_ans, answers in chaotic:
        print(f"  {p.problem_id}: {unique} unique answers, {nones} nones, correct={p.correct}")
        print(f"    Expected: {p.expected} | Votes: {dict(Counter(answers).most_common())}")
        correct_in = sum(1 for a in answers if a == p.expected)
        print(f"    Correct in attempts: {correct_in}/{len(answers)}")
        print()

    # ── 5. Diversity vs Correctness ──
    print("=" * 80)
    print("  DIVERSITY vs CORRECTNESS")
    print("=" * 80)
    print()

    from collections import defaultdict
    buckets = defaultdict(lambda: [0, 0])  # [correct, total]
    for p, unique, nones, top_count, top_ans, answers in diversity_data:
        if len(answers) == 0:
            continue
        buckets[unique][1] += 1
        if p.correct:
            buckets[unique][0] += 1

    print(f"  {'Unique Ans':<12} {'Correct':<10} {'Total':<10} {'Acc%':<10}")
    print("  " + "-" * 42)
    for u in sorted(buckets.keys()):
        c, t = buckets[u]
        pct = c / t * 100 if t > 0 else 0
        bar = "#" * int(pct / 5)
        print(f"  {u:<12} {c:<10} {t:<10} {pct:>5.1f}%  {bar}")

    # ── 6. Speed vs Accuracy Correlation ──
    print()
    print("=" * 80)
    print("  SPEED vs ACCURACY (per-attempt)")
    print("=" * 80)
    print()

    time_buckets = {
        "0-60s": (0, 60),
        "60-120s": (60, 120),
        "120-180s": (120, 180),
        "180-300s": (180, 300),
        "300-600s": (300, 600),
        "600s+": (600, 99999),
    }

    for label, (lo, hi) in time_buckets.items():
        correct = 0
        wrong = 0
        none = 0
        for p in problems:
            for a in p.attempts:
                if lo <= a.time_s < hi:
                    if a.answer is not None and a.answer == p.expected:
                        correct += 1
                    elif a.answer is not None:
                        wrong += 1
                    else:
                        none += 1
        total = correct + wrong + none
        if total == 0:
            continue
        acc = correct / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        raw_acc = correct / total * 100
        print(f"  {label:<12} | {total:>4} attempts | {correct:>4} correct | {wrong:>4} wrong | {none:>4} none | acc={acc:.1f}% | raw={raw_acc:.1f}%")

    # ── 7. Code Calls vs Correctness ──
    print()
    print("=" * 80)
    print("  CODE CALLS vs CORRECTNESS")
    print("=" * 80)
    print()

    code_buckets = {
        "0 calls": (0, 1),
        "1-3 calls": (1, 4),
        "3-5 calls": (3, 6),
        "5-10 calls": (5, 11),
        "10-20 calls": (10, 21),
        "20-50 calls": (20, 51),
        "50+ calls": (50, 999),
    }

    for label, (lo, hi) in code_buckets.items():
        correct = 0
        wrong = 0
        none = 0
        for p in problems:
            for a in p.attempts:
                if lo <= a.code_calls < hi:
                    if a.answer is not None and a.answer == p.expected:
                        correct += 1
                    elif a.answer is not None:
                        wrong += 1
                    else:
                        none += 1
        total = correct + wrong + none
        if total == 0:
            continue
        acc = correct / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        raw_acc = correct / total * 100
        print(f"  {label:<12} | {total:>4} attempts | {correct:>4} correct | {wrong:>4} wrong | {none:>4} none | acc={acc:.1f}% | raw={raw_acc:.1f}%")

    # ── 8. Restart Count vs Correctness ──
    print()
    print("=" * 80)
    print("  APPROACH RESTARTS vs CORRECTNESS (per-attempt)")
    print("=" * 80)
    print()

    restart_data = []
    for p in problems:
        for a in p.attempts:
            # Count "let's try", "let me try", "alternatively", "instead" as restarts
            text = " ".join(t.reasoning_text for t in a.turns)
            restarts = len(re.findall(r"(?:let'?s try|let me try|alternatively|instead,|different approach|try another)", text, re.IGNORECASE))
            is_correct = a.answer is not None and a.answer == p.expected
            is_none = a.answer is None
            restart_data.append((restarts, is_correct, is_none))

    restart_buckets = {
        "0 restarts": (0, 1),
        "1-3": (1, 4),
        "3-5": (3, 6),
        "5-10": (5, 11),
        "10-20": (10, 21),
        "20+": (20, 9999),
    }

    for label, (lo, hi) in restart_buckets.items():
        correct = sum(1 for r, c, n in restart_data if lo <= r < hi and c)
        wrong = sum(1 for r, c, n in restart_data if lo <= r < hi and not c and not n)
        none = sum(1 for r, c, n in restart_data if lo <= r < hi and n)
        total = correct + wrong + none
        if total == 0:
            continue
        acc = correct / (correct + wrong) * 100 if (correct + wrong) > 0 else 0
        raw_acc = correct / total * 100
        print(f"  {label:<12} | {total:>4} attempts | {correct:>4} correct | {wrong:>4} wrong | {none:>4} none | acc={acc:.1f}% | raw={raw_acc:.1f}%")


import re

if __name__ == "__main__":
    main()
