#!/usr/bin/env python3
"""
Vboxed Deep Analysis
====================
Analyzes \Vboxed{} intermediate checkpoint usage:
- How many attempts use Vboxed?
- Accuracy comparison: Vboxed vs non-Vboxed attempts
- Per-problem breakdown
- Per-tier breakdown
- Vboxed intermediate values vs final answers
- Did Vboxed checkpoints contribute to correct voting?

Usage:
    python log_exploration/vboxed_deep_analysis.py output/v31/diagnostic.log
"""

import re
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log
from collections import defaultdict


# Tier definitions (same as test framework)
TIER_MAP = {
    'dbbfe8': 'T0', '3b88b3': 'T0',
    '86e8e5': 'T0.5',
}
# T1 and T2 assigned dynamically


def get_tier(pid_short, problem_correct):
    """Assign tier based on known mapping or correctness heuristic."""
    if pid_short in TIER_MAP:
        return TIER_MAP[pid_short]
    # Heuristic: T2 problems are always correct, T1 are not
    return 'T2' if problem_correct else 'T1'


def analyze_vboxed(logfile):
    problems = parse_log(logfile)

    # Collect per-attempt Vboxed data
    all_stats = []
    total_attempts = 0
    total_with_vboxed = 0
    total_with_boxed_only = 0
    total_no_answer_marker = 0

    for p in problems:
        pid = p.problem_id[:8]
        for a in p.attempts:
            total_attempts += 1
            vboxed_values = []
            boxed_values = []

            for t in a.turns:
                text = t.reasoning_text or ''
                # Find all Vboxed values
                vb = re.findall(r'\\Vboxed\s*\{([^}]*)\}', text)
                bx = re.findall(r'\\boxed\s*\{([^}]*)\}', text)
                vboxed_values.extend(vb)
                boxed_values.extend(bx)

            has_vboxed = len(vboxed_values) > 0
            has_boxed = len(boxed_values) > 0

            if has_vboxed:
                total_with_vboxed += 1
            elif has_boxed:
                total_with_boxed_only += 1
            else:
                total_no_answer_marker += 1

            is_correct = (a.answer is not None and p.expected is not None
                          and str(a.answer) == str(p.expected))

            all_stats.append({
                'problem_id': pid,
                'attempt': a.attempt_num,
                'has_vboxed': has_vboxed,
                'vboxed_count': len(vboxed_values),
                'vboxed_values': vboxed_values,
                'boxed_count': len(boxed_values),
                'boxed_values': boxed_values,
                'final_answer': a.answer,
                'expected': p.expected,
                'correct': is_correct,
                'problem_correct': p.correct,
                'entropy': a.entropy,
                'tokens': a.tokens,
                'time_s': a.time_s,
                'tier': get_tier(pid, p.correct),
            })

    # ── Section 1: Overview ──
    print("=" * 70)
    print("VBOXED CHECKPOINT ANALYSIS")
    print("=" * 70)
    print(f"\nTotal attempts: {total_attempts}")
    print(f"  With Vboxed:    {total_with_vboxed} ({100*total_with_vboxed/total_attempts:.1f}%)")
    print(f"  Boxed only:     {total_with_boxed_only} ({100*total_with_boxed_only/total_attempts:.1f}%)")
    print(f"  No marker:      {total_no_answer_marker} ({100*total_no_answer_marker/total_attempts:.1f}%)")

    # ── Section 2: Accuracy comparison ──
    print("\n" + "=" * 70)
    print("ACCURACY: VBOXED vs NON-VBOXED ATTEMPTS")
    print("=" * 70)

    for label, has_vb in [("Vboxed", True), ("Non-Vboxed", False)]:
        subset = [s for s in all_stats if s['has_vboxed'] == has_vb]
        answered = [s for s in subset if s['final_answer'] is not None]
        correct = [s for s in answered if s['correct']]
        print(f"\n  {label}:")
        print(f"    Attempts: {len(subset)}")
        print(f"    Answered: {len(answered)}")
        if answered:
            print(f"    Correct:  {len(correct)} ({100*len(correct)/len(answered):.1f}%)")
            avg_entropy = sum(s['entropy'] for s in answered) / len(answered)
            avg_tokens = sum(s['tokens'] for s in answered) / len(answered)
            print(f"    Avg entropy: {avg_entropy:.3f}")
            print(f"    Avg tokens:  {avg_tokens:.0f}")

    # ── Section 3: Per-tier breakdown ──
    print("\n" + "=" * 70)
    print("VBOXED USAGE BY TIER")
    print("=" * 70)

    tiers = sorted(set(s['tier'] for s in all_stats))
    for tier in tiers:
        tier_stats = [s for s in all_stats if s['tier'] == tier]
        tier_vb = [s for s in tier_stats if s['has_vboxed']]
        tier_vb_correct = [s for s in tier_vb if s['correct']]
        tier_novb = [s for s in tier_stats if not s['has_vboxed'] and s['final_answer'] is not None]
        tier_novb_correct = [s for s in tier_novb if s['correct']]

        print(f"\n  {tier}: {len(tier_stats)} total attempts")
        print(f"    Vboxed: {len(tier_vb)} attempts", end="")
        if tier_vb:
            vb_ans = [s for s in tier_vb if s['final_answer'] is not None]
            print(f" → {len(tier_vb_correct)}/{len(vb_ans)} correct ({100*len(tier_vb_correct)/len(vb_ans):.0f}%)" if vb_ans else "")
        else:
            print()
        print(f"    No-Vboxed: {len(tier_novb)} answered", end="")
        if tier_novb:
            print(f" → {len(tier_novb_correct)}/{len(tier_novb)} correct ({100*len(tier_novb_correct)/len(tier_novb):.0f}%)")
        else:
            print()

    # ── Section 4: Per-problem detail ──
    print("\n" + "=" * 70)
    print("PER-PROBLEM VBOXED DETAIL")
    print("=" * 70)

    prob_groups = defaultdict(list)
    for s in all_stats:
        if s['has_vboxed']:
            prob_groups[s['problem_id']].append(s)

    for pid in sorted(prob_groups.keys()):
        stats = prob_groups[pid]
        tier = stats[0]['tier']
        prob_correct = stats[0]['problem_correct']
        n_correct = sum(1 for s in stats if s['correct'])
        n_total = len(stats)

        print(f"\n  {pid} [{tier}] problem={'CORRECT' if prob_correct else 'WRONG'}:")
        print(f"    {n_total} attempts used Vboxed, {n_correct} correct")

        for s in stats:
            vb_str = ', '.join(s['vboxed_values'][:3])
            if len(s['vboxed_values']) > 3:
                vb_str += f' ... (+{len(s["vboxed_values"])-3} more)'
            ans_str = f"→ final={s['final_answer']}"
            corr_str = "✓" if s['correct'] else "✗"
            print(f"      A{s['attempt']:2d}: Vboxed=[{vb_str}] {ans_str} {corr_str}")

    # ── Section 5: Interesting case — Vboxed correct but problem wrong ──
    print("\n" + "=" * 70)
    print("INTERESTING: VBOXED CORRECT ON WRONG PROBLEMS (outvoted)")
    print("=" * 70)

    for pid in sorted(prob_groups.keys()):
        stats = prob_groups[pid]
        if not stats[0]['problem_correct']:
            correct_vb = [s for s in stats if s['correct']]
            if correct_vb:
                print(f"\n  {pid}: Problem voted WRONG, but {len(correct_vb)} Vboxed attempts had correct answer!")
                for s in correct_vb:
                    print(f"    A{s['attempt']:2d}: answer={s['final_answer']} (expected={s['expected']}) entropy={s['entropy']:.3f}")

    # ── Section 6: Vboxed checkpoint count distribution ──
    print("\n" + "=" * 70)
    print("VBOXED CHECKPOINT COUNT DISTRIBUTION")
    print("=" * 70)

    vb_counts = [s['vboxed_count'] for s in all_stats if s['has_vboxed']]
    from collections import Counter
    count_dist = Counter(vb_counts)
    for count in sorted(count_dist.keys()):
        subset = [s for s in all_stats if s['has_vboxed'] and s['vboxed_count'] == count]
        correct = sum(1 for s in subset if s['correct'])
        answered = sum(1 for s in subset if s['final_answer'] is not None)
        print(f"  {count} checkpoints: {len(subset)} attempts, {correct}/{answered} correct ({100*correct/answered:.0f}%)" if answered else f"  {count} checkpoints: {len(subset)} attempts")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log>")
        sys.exit(1)
    analyze_vboxed(sys.argv[1])
