#!/usr/bin/env python3
"""Parse v21 diagnostic.log and identify struggling problems.

Key insight: With 8 parallel attempts and early_stop=4, the NORMAL case is:
  - 4 attempts answer correctly, 4 return None
  - Early stop triggers, wall time is low
  - This is NOT struggling — this is the happy path

Real struggles are:
  1. Wrong final answer
  2. Wrong attempts (model produces wrong numbers)
  3. Answer scatter (many different answers = model confused)
  4. Very few usable answers (< 4 answered)
  5. High code error rate
  6. Very slow (compute-bound)
  7. No early stop (couldn't get 4 to agree)
"""

import re
import json

LOG_PATH = "output/v21/diagnostic.log"


def parse_log(path):
    with open(path, 'r') as f:
        text = f.read()

    raw_blocks = re.split(r'~{40,}', text)

    # Merge pairs: block with "Problem id=" + next block with content
    merged_blocks = []
    current_tier = "Unknown"
    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i]

        tier_match = re.search(
            r'(REFERENCE PROBLEMS|FIXED \d+ DIAGNOSTIC|RANDOM \d+.*?from remaining pool|COMPREHENSIVE BENCHMARK)',
            block
        )
        if tier_match:
            current_tier = tier_match.group(1).strip()

        id_match = re.search(r'Problem id=(\w+)', block)
        if id_match and i + 1 < len(raw_blocks):
            merged = block + raw_blocks[i + 1]
            merged_blocks.append((current_tier, merged))
            i += 2
        else:
            i += 1

    problems = []

    for tier, block in merged_blocks:
        id_match = re.search(r'Problem id=(\w+)', block)
        if not id_match:
            continue
        problem_id = id_match.group(1)

        prob_text_match = re.search(r'Problem:\s*(.*?)(?:\n\s*\n|\nBudget:)', block, re.DOTALL)
        prob_text = prob_text_match.group(1).strip()[:500] if prob_text_match else "Unknown"

        correct_match = re.search(r'>>\s*(CORRECT|\*{3}\s*WRONG\s*\*{3})', block)
        if not correct_match:
            continue
        is_correct = 'WRONG' not in correct_match.group(1)

        pred_match = re.search(r'Predicted:\s*(\S+)\s*\|\s*Expected:\s*(\S+)\s*\|\s*Wall time:\s*([\d.]+)s', block)
        if not pred_match:
            continue
        predicted = pred_match.group(1)
        expected = pred_match.group(2)
        wall_time = float(pred_match.group(3))

        att_match = re.search(
            r'Attempts answered:\s*(\d+)/(\d+)\s*\|\s*Code calls:\s*(\d+)\s*\|\s*Errors:\s*(\d+)\s*\|\s*Tokens:\s*(\d+)',
            block
        )
        if not att_match:
            continue
        attempts_answered = int(att_match.group(1))
        total_attempts = int(att_match.group(2))
        code_calls = int(att_match.group(3))
        errors = int(att_match.group(4))
        tokens = int(att_match.group(5))

        ent_match = re.search(r'Avg entropy:\s*([\d.]+)\s*\|\s*Early stop:\s*(Yes|No)', block)
        avg_entropy = float(ent_match.group(1)) if ent_match else 0
        early_stop = ent_match.group(2) == 'Yes' if ent_match else False

        time_match = re.search(r'Attempt times:\s*min=([\d.]+)s\s+max=([\d.]+)s\s+avg=([\d.]+)s', block)
        min_time = float(time_match.group(1)) if time_match else 0
        max_time = float(time_match.group(2)) if time_match else 0
        avg_time = float(time_match.group(3)) if time_match else 0

        votes_match = re.search(r'Votes:\s*\[(.*?)\]', block)
        votes = {}
        if votes_match:
            for vm in re.finditer(r'(\S+):\s*(\d+)\s*votes?', votes_match.group(1)):
                votes[vm.group(1)] = int(vm.group(2))

        attempts = []
        for am in re.finditer(
            r'ATTEMPT\s+(\d+)\s+\|\s+answer=(\S+)\s+entropy=([\d.]+)\s+'
            r'code_calls=(\d+)\s+errors=(\d+)\s+tokens=(\d+)\s+time=([\d.]+)s\s+<<\s+(CORRECT|WRONG|NO ANSWER)',
            block
        ):
            attempts.append({
                'num': int(am.group(1)),
                'answer': am.group(2),
                'entropy': float(am.group(3)),
                'code_calls': int(am.group(4)),
                'errors': int(am.group(5)),
                'tokens': int(am.group(6)),
                'time': float(am.group(7)),
                'status': am.group(8),
            })

        # Derived metrics
        none_count = sum(1 for a in attempts if a['answer'] == 'None')
        wrong_count = sum(1 for a in attempts if a['status'] == 'WRONG')
        correct_count = sum(1 for a in attempts if a['status'] == 'CORRECT')
        unique_answers = len(set(a['answer'] for a in attempts if a['answer'] != 'None'))
        max_votes = max(votes.values()) if votes else 0
        sorted_votes = sorted(votes.values(), reverse=True)
        vote_margin = sorted_votes[0] - sorted_votes[1] if len(sorted_votes) > 1 else sorted_votes[0] if sorted_votes else 0
        total_errors = sum(a['errors'] for a in attempts)
        total_code_calls = sum(a['code_calls'] for a in attempts)
        error_rate = total_errors / max(total_code_calls, 1)

        # None rate relative to what ran
        # "Expected" none: if early_stop and 4 answered, remaining 4 are expected None
        # "Excess" none: attempts that ran but failed extraction
        if early_stop and attempts_answered >= 4:
            # Normal early stop pattern: 4 answered, 4 None is expected
            excess_none = max(0, none_count - (total_attempts - 4))
        else:
            excess_none = none_count  # all None are excess if no early stop

        ###############################
        # STRUGGLE SCORE (calibrated)
        ###############################
        struggle_score = 0

        # 1. Wrong final answer (catastrophic)
        if not is_correct:
            struggle_score += 100

        # 2. Wrong attempts (model produced wrong numbers)
        if wrong_count >= 4:
            struggle_score += 30
        elif wrong_count >= 2:
            struggle_score += 15
        elif wrong_count >= 1:
            struggle_score += 8

        # 3. Answer scatter (many different answers = confused model)
        if unique_answers >= 5:
            struggle_score += 25
        elif unique_answers >= 4:
            struggle_score += 15
        elif unique_answers >= 3:
            struggle_score += 8

        # 4. No early stop (couldn't get 4 to agree — ran all 8)
        if not early_stop:
            struggle_score += 12

        # 5. Weak consensus (even with early stop, thin margin matters)
        if max_votes <= 2:
            struggle_score += 15
        elif max_votes <= 3:
            struggle_score += 5

        # 6. Thin vote margin (winning answer barely ahead)
        if len(votes) > 1 and vote_margin <= 1:
            struggle_score += 8

        # 7. High code error rate (> 15% of code calls fail)
        if total_code_calls > 0:
            if error_rate >= 0.3:
                struggle_score += 10
            elif error_rate >= 0.15:
                struggle_score += 5

        # 8. Slow (compute-bound — wastes budget on real test)
        if wall_time >= 500:
            struggle_score += 15
        elif wall_time >= 300:
            struggle_score += 8
        elif wall_time >= 200:
            struggle_score += 3

        # 9. Token-heavy (model rambling, complex reasoning)
        if tokens >= 150000:
            struggle_score += 10
        elif tokens >= 80000:
            struggle_score += 5

        # 10. Excess None (extraction failures beyond early-stop)
        if excess_none >= 3:
            struggle_score += 5
        elif excess_none >= 1:
            struggle_score += 2

        # Classify
        if not is_correct:
            category = "FAILED"
        elif struggle_score >= 30:
            category = "HARD"
        elif struggle_score >= 10:
            category = "MODERATE"
        else:
            category = "CLEAN"

        problem = {
            'id': problem_id,
            'tier': tier,
            'problem_text': prob_text,
            'predicted': predicted,
            'expected': expected,
            'correct': is_correct,
            'wall_time': wall_time,
            'attempts_answered': attempts_answered,
            'total_attempts': total_attempts,
            'code_calls': code_calls,
            'errors': errors,
            'tokens': tokens,
            'avg_entropy': avg_entropy,
            'early_stop': early_stop,
            'min_time': min_time,
            'max_time': max_time,
            'avg_time': avg_time,
            'votes': votes,
            'max_votes': max_votes,
            'vote_margin': vote_margin,
            'none_count': none_count,
            'wrong_count': wrong_count,
            'correct_count': correct_count,
            'excess_none': excess_none,
            'unique_answers': unique_answers,
            'total_errors': total_errors,
            'total_code_calls': total_code_calls,
            'error_rate': error_rate,
            'struggle_score': struggle_score,
            'category': category,
            'attempts': attempts,
        }

        problems.append(problem)

    return problems


def generate_report(problems):
    lines = []
    problems.sort(key=lambda p: p['struggle_score'], reverse=True)

    # Category counts
    cats = {'FAILED': 0, 'HARD': 0, 'MODERATE': 0, 'CLEAN': 0}
    for p in problems:
        cats[p['category']] += 1

    lines.append("=" * 110)
    lines.append(f"  V21 DIAGNOSTIC ANALYSIS — {len(problems)} problems")
    lines.append(f"  Score: {sum(1 for p in problems if p['correct'])}/{len(problems)}")
    lines.append(f"  Categories: FAILED={cats['FAILED']} | HARD={cats['HARD']} | MODERATE={cats['MODERATE']} | CLEAN={cats['CLEAN']}")
    lines.append("=" * 110)

    # ===== DETAILED VIEW: HARD + FAILED =====
    lines.append("\n" + "=" * 110)
    lines.append("  DETAILED: FAILED + HARD PROBLEMS (struggle >= 30)")
    lines.append("=" * 110)

    for i, p in enumerate(problems):
        if p['struggle_score'] < 30:
            continue

        flag = p['category']
        lines.append(f"\n{'─' * 110}")
        lines.append(f"  [{flag}] #{i+1} | id={p['id']} | tier={p['tier']} | struggle={p['struggle_score']}")
        lines.append(f"  Answer: predicted={p['predicted']} expected={p['expected']} | {'CORRECT' if p['correct'] else 'WRONG'}")
        lines.append(f"  Time: {p['wall_time']:.1f}s wall (min={p['min_time']:.1f}s max={p['max_time']:.1f}s avg={p['avg_time']:.1f}s)")
        lines.append(f"  Attempts: {p['attempts_answered']}/{p['total_attempts']} answered | "
                     f"{p['correct_count']} correct | {p['wrong_count']} wrong | {p['none_count']} none (excess: {p['excess_none']})")
        lines.append(f"  Code: {p['total_code_calls']} calls | {p['total_errors']} errors ({p['error_rate']:.1%} error rate) | {p['tokens']:,} tokens")
        lines.append(f"  Voting: {p['votes']}")
        lines.append(f"    max_votes={p['max_votes']} | margin={p['vote_margin']} | unique_answers={p['unique_answers']}")
        lines.append(f"  Entropy: {p['avg_entropy']:.3f} | Early stop: {p['early_stop']}")
        lines.append(f"  Problem: {p['problem_text'][:300]}...")

        # Struggle factors
        factors = []
        if not p['correct']: factors.append("WRONG FINAL ANSWER")
        if p['wrong_count'] >= 2: factors.append(f"{p['wrong_count']} wrong attempts")
        elif p['wrong_count'] >= 1: factors.append(f"{p['wrong_count']} wrong attempt")
        if p['unique_answers'] >= 3: factors.append(f"{p['unique_answers']} unique answers (scattered)")
        if not p['early_stop']: factors.append("no early stop (all 8 ran)")
        if p['max_votes'] <= 3: factors.append(f"weak consensus ({p['max_votes']} votes)")
        if len(p['votes']) > 1 and p['vote_margin'] <= 1: factors.append(f"razor margin ({p['vote_margin']})")
        if p['error_rate'] >= 0.15: factors.append(f"high error rate ({p['error_rate']:.0%})")
        if p['wall_time'] >= 200: factors.append(f"slow ({p['wall_time']:.0f}s)")
        if p['tokens'] >= 80000: factors.append(f"token-heavy ({p['tokens']:,})")
        if p['excess_none'] >= 1: factors.append(f"{p['excess_none']} excess None")
        lines.append(f"  STRUGGLE FACTORS: {' | '.join(factors)}")

        lines.append(f"\n  Attempt breakdown:")
        for a in p['attempts']:
            icon = "OK" if a['status'] == 'CORRECT' else ("XX" if a['status'] == 'WRONG' else "--")
            lines.append(f"    [{icon}] #{a['num']}: ans={a['answer']:>10s} ent={a['entropy']:.3f} "
                        f"code={a['code_calls']:>3d} err={a['errors']} tok={a['tokens']:>6d} time={a['time']:>6.1f}s")

    # ===== MODERATE PROBLEMS (brief) =====
    moderate = [p for p in problems if p['category'] == 'MODERATE']
    if moderate:
        lines.append("\n\n" + "=" * 110)
        lines.append(f"  MODERATE PROBLEMS (10 <= struggle < 30) — {len(moderate)} problems")
        lines.append("=" * 110)
        for p in moderate:
            factors = []
            if p['wrong_count']: factors.append(f"wrng={p['wrong_count']}")
            if p['error_rate'] >= 0.1: factors.append(f"err={p['error_rate']:.0%}")
            if p['wall_time'] >= 100: factors.append(f"slow={p['wall_time']:.0f}s")
            if p['tokens'] >= 50000: factors.append(f"tok={p['tokens']:,}")
            if p['excess_none']: factors.append(f"xNone={p['excess_none']}")
            lines.append(f"  {p['id']} scr={p['struggle_score']:>3} | {p['wall_time']:>6.1f}s | "
                        f"{p['attempts_answered']}/{p['total_attempts']} ans | votes={p['votes']} | "
                        f"{', '.join(factors) if factors else 'minor issues'}")

    # ===== FULL TABLE =====
    lines.append("\n\n" + "=" * 110)
    lines.append("  FULL RANKING (sorted by struggle score)")
    lines.append("=" * 110)
    header = (f"{'#':>3} {'ID':<10} {'Cat':<8} {'Scr':>4} {'Time':>7} {'A/T':>5} "
              f"{'Wrng':>4} {'Uniq':>4} {'MaxV':>4} {'Mrgn':>4} "
              f"{'Errs':>4} {'ErrR':>5} {'Tokens':>8} {'ES':>3}")
    lines.append(header)
    lines.append("─" * 110)
    for i, p in enumerate(problems):
        line = (f"{i+1:>3} {p['id']:<10} {p['category']:<8} {p['struggle_score']:>4} {p['wall_time']:>6.1f}s "
                f"{p['attempts_answered']:>2}/{p['total_attempts']:<2} {p['wrong_count']:>4} "
                f"{p['unique_answers']:>4} {p['max_votes']:>4} {p['vote_margin']:>4} "
                f"{p['total_errors']:>4} {p['error_rate']:>4.0%} {p['tokens']:>8} "
                f"{'Y' if p['early_stop'] else 'N':>3}")
        lines.append(line)

    # ===== AGGREGATE STATS =====
    lines.append("\n\n" + "=" * 110)
    lines.append("  AGGREGATE STATISTICS")
    lines.append("=" * 110)

    tiers = {}
    for p in problems:
        if p['tier'] not in tiers:
            tiers[p['tier']] = []
        tiers[p['tier']].append(p)

    for tier_name, ps in tiers.items():
        correct = sum(1 for p in ps if p['correct'])
        avg_time = sum(p['wall_time'] for p in ps) / len(ps)
        avg_struggle = sum(p['struggle_score'] for p in ps) / len(ps)
        total_tokens = sum(p['tokens'] for p in ps)
        total_errors = sum(p['total_errors'] for p in ps)
        lines.append(f"\n  {tier_name}:")
        lines.append(f"    Score: {correct}/{len(ps)} | Avg time: {avg_time:.1f}s | Avg struggle: {avg_struggle:.1f}")
        lines.append(f"    Total tokens: {total_tokens:,} | Total errors: {total_errors}")

    all_attempts = []
    for p in problems:
        all_attempts.extend(p['attempts'])
    total_att = len(all_attempts)
    if total_att > 0:
        none_att = sum(1 for a in all_attempts if a['answer'] == 'None')
        wrong_att = sum(1 for a in all_attempts if a['status'] == 'WRONG')
        correct_att = total_att - none_att - wrong_att
        lines.append(f"\n  GLOBAL ATTEMPT STATS (across all {total_att} attempts):")
        lines.append(f"    Extraction success: {total_att - none_att}/{total_att} ({100*(total_att-none_att)/total_att:.1f}%)")
        lines.append(f"    None (extraction fail): {none_att}/{total_att} ({100*none_att/total_att:.1f}%)")
        lines.append(f"    Correct answers: {correct_att}/{total_att} ({100*correct_att/total_att:.1f}%)")
        lines.append(f"    Wrong answers: {wrong_att}/{total_att} ({100*wrong_att/total_att:.1f}%)")
        avg_tok = sum(a['tokens'] for a in all_attempts) / total_att
        avg_code = sum(a['code_calls'] for a in all_attempts) / total_att
        avg_err = sum(a['errors'] for a in all_attempts) / total_att
        lines.append(f"    Avg tokens/attempt: {avg_tok:,.0f} | Avg code/attempt: {avg_code:.1f} | Avg errors/attempt: {avg_err:.2f}")

    # ===== RISK ANALYSIS =====
    lines.append("\n\n" + "=" * 110)
    lines.append("  RISK ANALYSIS — Problems That Could Flip on Real Test")
    lines.append("=" * 110)
    lines.append("  (Correct but fragile — could go wrong on a different run)")

    at_risk = [p for p in problems if p['correct'] and (
        p['wrong_count'] >= 2 or
        (p['max_votes'] <= 3 and not p['early_stop']) or
        p['vote_margin'] <= 1 or
        p['unique_answers'] >= 4
    )]

    if at_risk:
        for p in at_risk:
            lines.append(f"\n  {p['id']}: votes={p['votes']}")
            lines.append(f"    wrong={p['wrong_count']} | unique_ans={p['unique_answers']} | "
                        f"time={p['wall_time']:.0f}s | struggle={p['struggle_score']}")
    else:
        lines.append("  None — all correct answers have solid consensus.")

    # ===== KEY INSIGHTS =====
    lines.append("\n\n" + "=" * 110)
    lines.append("  KEY INSIGHTS")
    lines.append("=" * 110)

    # None rate
    lines.append(f"\n  1. EXTRACTION FAILURE RATE: {100*none_att/total_att:.1f}% of attempts return None")
    lines.append(f"     This is the #1 bottleneck — nearly half of compute is wasted.")
    lines.append(f"     If we could reduce None rate from 44% to 20%, effective attempts per problem doubles.")

    # Error patterns
    high_err = [p for p in problems if p['error_rate'] >= 0.15]
    lines.append(f"\n  2. CODE ERRORS: {len(high_err)} problems have >15% error rate")
    for p in sorted(high_err, key=lambda x: x['error_rate'], reverse=True)[:5]:
        lines.append(f"     {p['id']}: {p['total_errors']} errors / {p['total_code_calls']} calls ({p['error_rate']:.0%})")

    # Slow problems
    slow = [p for p in problems if p['wall_time'] >= 200]
    total_slow_time = sum(p['wall_time'] for p in slow)
    total_time = sum(p['wall_time'] for p in problems)
    lines.append(f"\n  3. SLOW PROBLEMS: {len(slow)} problems >= 200s, consuming {total_slow_time:.0f}s / {total_time:.0f}s total ({100*total_slow_time/total_time:.0f}%)")
    for p in sorted(slow, key=lambda x: x['wall_time'], reverse=True):
        lines.append(f"     {p['id']}: {p['wall_time']:.0f}s | {p['tokens']:,} tok | {p['total_code_calls']} code calls")

    # Token hogs
    token_hogs = sorted(problems, key=lambda x: x['tokens'], reverse=True)[:5]
    lines.append(f"\n  4. TOKEN HOGS (top 5):")
    for p in token_hogs:
        lines.append(f"     {p['id']}: {p['tokens']:,} tokens | {p['wall_time']:.0f}s | category={p['category']}")

    return '\n'.join(lines)


def save_json(problems, path):
    slim = []
    for p in problems:
        pp = dict(p)
        pp['attempt_summary'] = [
            {'num': a['num'], 'answer': a['answer'], 'status': a['status'],
             'entropy': a['entropy'], 'code_calls': a['code_calls'],
             'errors': a['errors'], 'tokens': a['tokens'], 'time': a['time']}
            for a in p['attempts']
        ]
        del pp['attempts']
        slim.append(pp)

    with open(path, 'w') as f:
        json.dump(slim, f, indent=2)


if __name__ == '__main__':
    problems = parse_log(LOG_PATH)
    report = generate_report(problems)
    print(report)

    with open("output/v21/diagnostics/analysis_report.txt", 'w') as f:
        f.write(report)

    save_json(problems, "output/v21/diagnostics/all_problems.json")

    hard = [p for p in problems if p['struggle_score'] >= 30]
    save_json(hard, "output/v21/diagnostics/hard_problems.json")

    print(f"\n\nFiles saved:")
    print(f"  output/v21/diagnostics/analysis_report.txt")
    print(f"  output/v21/diagnostics/all_problems.json ({len(problems)} problems)")
    print(f"  output/v21/diagnostics/hard_problems.json ({len(hard)} problems)")
