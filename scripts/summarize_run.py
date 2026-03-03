#!/usr/bin/env python3
"""Generate a compact per-question summary from diagnostic.log.

Usage:
    python3 scripts/summarize_run.py output/v22/diagnostic.log
    python3 scripts/summarize_run.py output/v22/diagnostic.log --save  # saves to diagnostics/v22/summary.txt

Output: One line per question with ID, result, votes, time, errors — scan in seconds.
"""

import re
import sys
import os
from collections import defaultdict


def parse_run(path):
    with open(path, 'r') as f:
        text = f.read()

    # Split into problem blocks (merge pairs)
    raw_blocks = re.split(r'~{40,}', text)
    problems = []
    current_tier = "Unknown"
    tier_num = 0

    tier_re = (r'(REFERENCE PROBLEMS|FIXED \d+ DIAGNOSTIC|RANDOM \d+|COMPREHENSIVE BENCHMARK|'
               r'HARD \d* ?BENCHMARK|AIME \d* ?BENCHMARK)')

    def update_tier_from_block(blk, cur_tier):
        """Find last non-COMPLETE tier marker in a block."""
        for m in re.finditer(tier_re, blk):
            after = blk[m.end():m.end()+15]
            if 'COMPLETE' not in after:
                cur_tier = m.group(1).strip()
        return cur_tier

    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i]
        current_tier = update_tier_from_block(block, current_tier)

        id_match = re.search(r'Problem id=(\w+)', block)
        if id_match and i + 1 < len(raw_blocks):
            merged = block + raw_blocks[i + 1]
            prob = parse_problem(id_match.group(1), current_tier, merged)
            if prob:
                problems.append(prob)
            # Check content block for tier transitions (affects NEXT problem)
            current_tier = update_tier_from_block(raw_blocks[i + 1], current_tier)
            i += 2
        else:
            i += 1

    return problems


def parse_problem(problem_id, tier, block):
    # Result line
    pred_match = re.search(r'Predicted:\s*(\S+)\s*\|\s*Expected:\s*(\S+)\s*\|\s*Wall time:\s*([\d.]+)s', block)
    if not pred_match:
        return None

    predicted = pred_match.group(1)
    expected = pred_match.group(2)
    wall_time = float(pred_match.group(3))
    correct = predicted == expected

    # Stats line
    stats_match = re.search(
        r'Attempts answered:\s*(\d+)/(\d+)\s*\|\s*Code calls:\s*(\d+)\s*\|\s*Errors:\s*(\d+)\s*\|\s*Tokens:\s*(\d+)',
        block)
    if stats_match:
        answered = int(stats_match.group(1))
        total_attempts = int(stats_match.group(2))
        code_calls = int(stats_match.group(3))
        errors = int(stats_match.group(4))
        tokens = int(stats_match.group(5))
    else:
        answered = total_attempts = code_calls = errors = tokens = 0

    # Entropy and early stop
    entropy_match = re.search(r'Avg entropy:\s*([\d.]+)\s*\|\s*Early stop:\s*(Yes|No)', block)
    entropy = float(entropy_match.group(1)) if entropy_match else 0
    early_stop = entropy_match.group(2) == 'Yes' if entropy_match else False

    # Votes
    votes_match = re.search(r'Votes:\s*\[([^\]]+)\]', block)
    votes_str = votes_match.group(1) if votes_match else ""
    # Parse vote counts
    vote_parts = re.findall(r'(\S+):\s*(\d+)\s*votes?', votes_str)
    top_vote = int(vote_parts[0][1]) if vote_parts else 0
    unique_answers = len(vote_parts)

    # WRONG/CORRECT tag
    is_wrong = '*** WRONG ***' in block

    return {
        'id': problem_id,
        'tier': tier,
        'predicted': predicted,
        'expected': expected,
        'correct': correct,
        'wall_time': wall_time,
        'answered': answered,
        'total_attempts': total_attempts,
        'code_calls': code_calls,
        'errors': errors,
        'tokens': tokens,
        'entropy': entropy,
        'early_stop': early_stop,
        'top_vote': top_vote,
        'unique_answers': unique_answers,
        'votes_str': votes_str,
    }


def print_summary(problems, out=sys.stdout):
    w = out.write

    # Header
    w("=" * 120 + "\n")
    w("  RUN SUMMARY — Per-Question Results\n")
    w("=" * 120 + "\n\n")

    correct_count = sum(1 for p in problems if p['correct'])
    wrong = [p for p in problems if not p['correct']]
    total = len(problems)
    total_time = sum(p['wall_time'] for p in problems)

    w(f"  Score: {correct_count}/{total} ({100*correct_count/total:.1f}%) | "
      f"Time: {total_time:.0f}s ({total_time/60:.1f} min) | "
      f"Wrong: {len(wrong)}\n\n")

    # Per-tier breakdown
    tiers = {}
    for p in problems:
        tiers.setdefault(p['tier'], []).append(p)

    for tier, probs in tiers.items():
        tier_correct = sum(1 for p in probs if p['correct'])
        tier_time = sum(p['wall_time'] for p in probs)
        w(f"  {tier}: {tier_correct}/{len(probs)} | {tier_time:.0f}s\n")

    # Column headers
    w("\n" + "-" * 120 + "\n")
    w(f"  {'ID':>6}  {'Result':>7}  {'Pred':>6} {'Exp':>6}  "
      f"{'Time':>6}  {'Ans':>3}/{'':<3}  {'Votes':>5}  {'Uniq':>4}  "
      f"{'Errs':>4}  {'Code':>4}  {'Tok':>6}  {'Ent':>5}  {'ES':>2}  {'Vote Detail'}\n")
    w("-" * 120 + "\n")

    current_tier = None
    for p in problems:
        if p['tier'] != current_tier:
            current_tier = p['tier']
            w(f"\n  --- {current_tier} ---\n")

        result = "OK" if p['correct'] else "WRONG"
        es = "Y" if p['early_stop'] else "N"

        # Highlight wrong answers
        prefix = "  " if p['correct'] else ">>"

        w(f"{prefix}{p['id']:>6}  {result:>7}  {p['predicted']:>6} {p['expected']:>6}  "
          f"{p['wall_time']:>5.0f}s  {p['answered']:>3}/{p['total_attempts']:<3}  "
          f"{p['top_vote']:>5}  {p['unique_answers']:>4}  "
          f"{p['errors']:>4}  {p['code_calls']:>4}  {p['tokens']:>6}  "
          f"{p['entropy']:>5.3f}  {es:>2}  [{p['votes_str']}]\n")

    # Wrong answers detail
    if wrong:
        w("\n" + "=" * 120 + "\n")
        w("  WRONG ANSWERS — Details\n")
        w("=" * 120 + "\n\n")
        for p in wrong:
            w(f"  {p['id']} ({p['tier']})\n")
            w(f"    Predicted: {p['predicted']} | Expected: {p['expected']}\n")
            w(f"    Time: {p['wall_time']:.1f}s | Answered: {p['answered']}/{p['total_attempts']} | "
              f"Errors: {p['errors']} | Code: {p['code_calls']}\n")
            w(f"    Votes: [{p['votes_str']}]\n")
            w(f"    Entropy: {p['entropy']:.3f} | Early stop: {'Yes' if p['early_stop'] else 'No'}\n\n")

    # Risk assessment: problems with weak consensus
    risky = [p for p in problems if p['correct'] and (p['top_vote'] <= 3 or p['unique_answers'] >= 3)]
    if risky:
        w("=" * 120 + "\n")
        w("  AT-RISK — Correct but weak consensus (top_vote<=3 or unique>=3)\n")
        w("=" * 120 + "\n\n")
        for p in risky:
            w(f"  {p['id']}: top_vote={p['top_vote']} unique={p['unique_answers']} "
              f"time={p['wall_time']:.0f}s errs={p['errors']} [{p['votes_str']}]\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/summarize_run.py <diagnostic.log> [--save]")
        sys.exit(1)

    log_path = sys.argv[1]
    save = '--save' in sys.argv

    problems = parse_run(log_path)
    if not problems:
        print(f"No problems found in {log_path}")
        sys.exit(1)

    # Print to stdout
    print_summary(problems)

    # Optionally save
    if save:
        # Infer version from path
        parts = log_path.split('/')
        version = next((p for p in parts if p.startswith('v')), 'unknown')
        out_dir = f'diagnostics/{version}'
        os.makedirs(out_dir, exist_ok=True)
        out_path = f'{out_dir}/summary.txt'
        with open(out_path, 'w') as f:
            print_summary(problems, out=f)
        print(f"\n  Saved to {out_path}")


if __name__ == '__main__':
    main()
