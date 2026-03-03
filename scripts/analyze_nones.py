#!/usr/bin/env python3
"""Analyze NO ANSWER attempts — why do they fail to extract an answer?

Key finding: ALL 8 attempts run in parallel. There are NO "stopped" attempts.
Every NO ANSWER is a real failure where the model ran but couldn't produce \boxed{}.
"""

import re
import json
from collections import defaultdict, Counter

LOG_PATH = "output/v21/diagnostic.log"


def analyze_nones(path):
    with open(path, 'r') as f:
        text = f.read()

    # Split into problem blocks (merge pairs)
    raw_blocks = re.split(r'~{40,}', text)
    merged_blocks = []
    current_tier = "Unknown"
    i = 0
    while i < len(raw_blocks):
        block = raw_blocks[i]
        tier_match = re.search(
            r'(REFERENCE PROBLEMS|FIXED \d+ DIAGNOSTIC|RANDOM \d+|COMPREHENSIVE BENCHMARK)', block)
        if tier_match:
            current_tier = tier_match.group(1).strip()
        id_match = re.search(r'Problem id=(\w+)', block)
        if id_match and i + 1 < len(raw_blocks):
            merged_blocks.append((current_tier, id_match.group(1), block + raw_blocks[i + 1]))
            i += 2
        else:
            i += 1

    all_attempts = []
    none_attempts = []

    for tier, problem_id, block in merged_blocks:
        # Find early stop status
        early_stop = 'Early stop: Yes' in block

        # Get expected answer
        exp_match = re.search(r'Expected:\s*(\S+)', block)
        expected = exp_match.group(1) if exp_match else None

        # Parse all attempts
        attempt_sections = re.split(r'ATTEMPT\s+(\d+)\s+\|', block)
        # attempt_sections: [pre, num1, body1, num2, body2, ...]

        for j in range(1, len(attempt_sections) - 1, 2):
            att_num = int(attempt_sections[j])
            att_body = attempt_sections[j + 1]

            # Parse header line
            header_match = re.search(
                r'answer=(\S+)\s+entropy=([\d.]+)\s+code_calls=(\d+)\s+errors=(\d+)\s+'
                r'tokens=(\d+)\s+time=([\d.]+)s\s+<<\s+(CORRECT|WRONG|NO ANSWER)',
                att_body
            )
            if not header_match:
                continue

            answer = header_match.group(1)
            entropy = float(header_match.group(2))
            code_calls = int(header_match.group(3))
            errors = int(header_match.group(4))
            tokens = int(header_match.group(5))
            time_s = float(header_match.group(6))
            status = header_match.group(7)

            attempt = {
                'problem_id': problem_id,
                'tier': tier,
                'attempt': att_num,
                'answer': answer,
                'entropy': entropy,
                'code_calls': code_calls,
                'errors': errors,
                'tokens': tokens,
                'time': time_s,
                'status': status,
                'early_stop': early_stop,
                'expected': expected,
            }

            all_attempts.append(attempt)

            if status == 'NO ANSWER':
                # Analyze WHY it's None — look at the body for clues
                reasons = []

                # Check for timeout
                if 'timed out' in att_body.lower() or time_s >= 500:
                    reasons.append('timeout')

                # Check for many errors
                if errors >= 3:
                    reasons.append(f'many_errors({errors})')

                # Check if there's a boxed in the body but extraction failed
                boxed_in_body = len(re.findall(r'\\boxed', att_body))
                if boxed_in_body > 0:
                    reasons.append(f'boxed_present({boxed_in_body}x)')

                # Check for final answer text pattern
                final_ans_in_body = len(re.findall(r'final\s+answer', att_body, re.IGNORECASE))
                if final_ans_in_body > 0:
                    reasons.append(f'final_answer_text({final_ans_in_body}x)')

                # Check token count — did model ramble?
                if tokens >= 20000:
                    reasons.append('token_heavy')
                elif tokens < 2000:
                    reasons.append('token_light')

                # Check if model was cut off by stop_event (low tokens, mid-reasoning)
                if tokens < 500 and time_s < 5:
                    reasons.append('likely_stopped_early')

                # Check for code with no output (execution issues)
                code_blocks = re.findall(r'\[Code\]', att_body)
                output_blocks = re.findall(r'\[Output\]', att_body)
                if len(code_blocks) > len(output_blocks) + 1:
                    reasons.append('code_without_output')

                # Check if stopped by early_stop mid-reasoning
                if 'stop_event' in att_body.lower() or 'deadline' in att_body.lower():
                    reasons.append('stopped_mid_reasoning')

                # Count turns
                turns = len(re.findall(r'\[Turn \d+\]', att_body))
                attempt['turns'] = turns

                if not reasons:
                    if code_calls == 0 and tokens > 1000:
                        reasons.append('pure_reasoning_no_boxed')
                    elif code_calls > 0 and errors == 0:
                        reasons.append('ran_code_ok_but_no_extraction')
                    else:
                        reasons.append('unknown')

                attempt['none_reasons'] = reasons
                none_attempts.append(attempt)

    return all_attempts, none_attempts


def main():
    all_attempts, none_attempts = analyze_nones(LOG_PATH)

    total = len(all_attempts)
    none_count = len(none_attempts)
    correct_count = sum(1 for a in all_attempts if a['status'] == 'CORRECT')
    wrong_count = sum(1 for a in all_attempts if a['status'] == 'WRONG')

    print("=" * 100)
    print("  NONE ANALYSIS — Why Do Attempts Fail to Extract Answers?")
    print("=" * 100)

    print(f"\n  Total attempts: {total}")
    print(f"  CORRECT: {correct_count} ({100*correct_count/total:.1f}%)")
    print(f"  WRONG:   {wrong_count} ({100*wrong_count/total:.1f}%)")
    print(f"  NONE:    {none_count} ({100*none_count/total:.1f}%)")

    print(f"\n  KEY FINDING: All 8 attempts run in parallel. There are NO 'stopped' attempts.")
    print(f"  Every NO ANSWER is a REAL failure — model ran but couldn't produce \\boxed{{}}.")

    # Classify the Nones
    print("\n" + "=" * 100)
    print("  NONE REASONS BREAKDOWN")
    print("=" * 100)

    reason_counts = Counter()
    for a in none_attempts:
        for r in a.get('none_reasons', ['unknown']):
            reason_counts[r] += 1

    for reason, count in reason_counts.most_common():
        pct = 100 * count / none_count
        print(f"  {reason:<35} {count:>4} ({pct:>5.1f}%)")

    # Per-problem breakdown
    print("\n" + "=" * 100)
    print("  NONE RATE BY PROBLEM")
    print("=" * 100)

    by_problem = defaultdict(list)
    all_by_problem = defaultdict(list)
    for a in all_attempts:
        all_by_problem[a['problem_id']].append(a)
    for a in none_attempts:
        by_problem[a['problem_id']].append(a)

    # Sort by none count
    for pid, nones in sorted(by_problem.items(), key=lambda x: len(x[1]), reverse=True):
        total_for_prob = len(all_by_problem[pid])
        none_for_prob = len(nones)
        pct = 100 * none_for_prob / total_for_prob
        reasons = Counter()
        for a in nones:
            for r in a.get('none_reasons', []):
                reasons[r] += 1
        reason_str = ', '.join(f'{r}:{c}' for r, c in reasons.most_common(3))
        tier = nones[0]['tier']
        print(f"  {pid} ({tier}): {none_for_prob}/{total_for_prob} ({pct:.0f}%) — {reason_str}")

    # Token distribution for None vs non-None
    print("\n" + "=" * 100)
    print("  TOKEN/TIME COMPARISON: NONE vs CORRECT attempts")
    print("=" * 100)

    none_tokens = [a['tokens'] for a in none_attempts]
    correct_tokens = [a['tokens'] for a in all_attempts if a['status'] == 'CORRECT']
    none_times = [a['time'] for a in none_attempts]
    correct_times = [a['time'] for a in all_attempts if a['status'] == 'CORRECT']
    none_code = [a['code_calls'] for a in none_attempts]
    correct_code = [a['code_calls'] for a in all_attempts if a['status'] == 'CORRECT']

    def stats(vals):
        if not vals: return "N/A"
        s = sorted(vals)
        return f"min={s[0]:.0f} median={s[len(s)//2]:.0f} avg={sum(s)/len(s):.0f} max={s[-1]:.0f}"

    print(f"\n  Tokens:     NONE: {stats(none_tokens)}")
    print(f"              CORR: {stats(correct_tokens)}")
    print(f"  Time (s):   NONE: {stats(none_times)}")
    print(f"              CORR: {stats(correct_times)}")
    print(f"  Code calls: NONE: {stats(none_code)}")
    print(f"              CORR: {stats(correct_code)}")

    # Boxed analysis — how many Nones had \boxed in their text?
    print("\n" + "=" * 100)
    print("  BOXED EXTRACTION FAILURES")
    print("=" * 100)
    print("  (Attempts where model wrote \\boxed{} but extraction didn't find it)")

    boxed_failures = [a for a in none_attempts
                      if any('boxed_present' in r for r in a.get('none_reasons', []))]
    print(f"\n  {len(boxed_failures)} of {none_count} None attempts ({100*len(boxed_failures)/none_count:.1f}%) had \\boxed in text")

    for a in boxed_failures[:10]:
        boxed_count = [r for r in a['none_reasons'] if 'boxed_present' in r]
        print(f"    {a['problem_id']} attempt {a['attempt']}: {boxed_count} | "
              f"tok={a['tokens']} time={a['time']:.1f}s code={a['code_calls']}")

    # "Final answer" text failures
    fa_failures = [a for a in none_attempts
                   if any('final_answer_text' in r for r in a.get('none_reasons', []))]
    print(f"\n  {len(fa_failures)} of {none_count} None attempts had 'final answer' text but no extraction")

    # Pure reasoning (no code, no boxed)
    pure_reasoning = [a for a in none_attempts
                      if any('pure_reasoning' in r for r in a.get('none_reasons', []))]
    print(f"  {len(pure_reasoning)} of {none_count} were pure reasoning (no code) with no \\boxed")

    # Ran code OK but no extraction
    code_ok = [a for a in none_attempts
               if any('ran_code_ok' in r for r in a.get('none_reasons', []))]
    print(f"  {len(code_ok)} of {none_count} ran code successfully but couldn't extract answer")

    # Save
    output = {
        'total_attempts': total,
        'correct': correct_count,
        'wrong': wrong_count,
        'none': none_count,
        'reason_counts': dict(reason_counts),
        'none_attempts': none_attempts,
    }
    with open("diagnostics/v21/none_analysis.json", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n\n  Saved to diagnostics/v21/none_analysis.json")


if __name__ == '__main__':
    main()
