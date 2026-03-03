#!/usr/bin/env python3
"""
Q2 Analysis: When the model overrides its code output, is the opposite ever true?

For ALL problems in v23, finds cases where:
- An attempt has code output containing a clean number
- The attempt's final answer is DIFFERENT from that code output number
- Checks whether the final answer or the code output was correct

Run from project root:
    python scripts/code_vs_answer_analysis.py
"""

import sys
import re

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


def main():
    problems = parse_log('output/v23/diagnostic.log')
    print(f'Parsed {len(problems)} problems, {sum(len(p.attempts) for p in problems)} attempts\n')

    code_vs_answer = []

    for p in problems:
        for att in p.attempts:
            if att.answer is None or not att.turns:
                continue

            # Find the last non-error turn that has code AND output
            last_code_turn = None
            for turn in reversed(att.turns):
                if turn.output.strip() and turn.code.strip() and not turn.is_error:
                    last_code_turn = turn
                    break

            if not last_code_turn:
                continue

            output_text = last_code_turn.output.strip()
            lines = [l.strip() for l in output_text.split('\n') if l.strip()]
            if not lines:
                continue

            last_line = lines[-1].strip()

            # Strategy: look for a clean integer on the last line
            clean_match = re.match(r'^(\d{1,5})$', last_line)
            if not clean_match:
                # Also try: 'answer = 12345' or 'result: 12345'
                clean_match = re.match(
                    r'^(?:answer|result|ans|output|total|final|count|sum|value)\s*[:=]\s*(\d{1,5})$',
                    last_line, re.IGNORECASE
                )

            if not clean_match:
                continue

            code_answer = int(clean_match.group(1))

            code_vs_answer.append({
                'pid': p.problem_id,
                'expected': p.expected,
                'att': att.attempt_num,
                'final': att.answer,
                'code': code_answer,
                'agrees': code_answer == att.answer,
                'out': output_text[-200:],
                'src': last_code_turn.code[-200:],
            })

    total = len(code_vs_answer)
    agrees = sum(1 for x in code_vs_answer if x['agrees'])
    differs = sum(1 for x in code_vs_answer if not x['agrees'])

    print(f'=== CODE OUTPUT vs FINAL ANSWER ===')
    print(f'Attempts with clean code output number: {total}')
    print(f'  Code agrees with final answer: {agrees} ({100*agrees/max(total,1):.1f}%)')
    print(f'  Code DIFFERS from final answer: {differs} ({100*differs/max(total,1):.1f}%)')
    print()

    print(f'=== DETAILED DISAGREEMENTS ===')
    code_right = 0
    answer_right = 0
    neither = 0

    for case in code_vs_answer:
        if case['agrees'] or case['expected'] is None:
            continue

        c_ok = case['code'] == case['expected']
        a_ok = case['final'] == case['expected']

        if c_ok and not a_ok:
            code_right += 1
            tag = 'CODE_CORRECT (model wrongly overrode)'
        elif a_ok and not c_ok:
            answer_right += 1
            tag = 'MODEL_CORRECT (model correctly overrode code)'
        elif c_ok and a_ok:
            tag = 'BOTH_CORRECT'
        else:
            neither += 1
            tag = 'NEITHER_CORRECT'

        print(f'\n  [{tag}] Problem {case["pid"]} attempt #{case["att"]}')
        print(f'    code_output={case["code"]}  final_answer={case["final"]}  expected={case["expected"]}')
        print(f'    Last output line: ...{case["out"][-100:]}')
        print(f'    Last code line:   ...{case["src"][-100:]}')

    print(f'\n=== SUMMARY ===')
    print(f'Total disagreements: {differs}')
    print(f'  Code correct, model wrongly overrode: {code_right}')
    print(f'  Model correctly overrode code:        {answer_right}')
    print(f'  Neither correct:                      {neither}')
    if code_right + answer_right > 0:
        pct = 100 * code_right / (code_right + answer_right)
        print(f'  Trust-code win rate: {code_right}/{code_right+answer_right} = {pct:.1f}%')
        print(f'  => {"Trust code is better" if pct > 50 else "Model override is sometimes justified"}')


if __name__ == '__main__':
    main()
