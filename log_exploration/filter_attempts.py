#!/usr/bin/env python3
"""
AIMO3 Attempt Filter
=====================
Filter attempts by any combination of criteria. Powerful for narrowing down
specific patterns in the data.

Usage:
    python log_exploration/filter_attempts.py <logfile> [filters...]

Filters:
    --temp <val>          Temperature equals val (within 0.05)
    --errors-gt <n>       Errors greater than n
    --errors-eq <n>       Exactly n errors
    --time-gt <secs>      Time greater than secs
    --time-lt <secs>      Time less than secs
    --turns-gt <n>        More than n turns
    --tokens-gt <n>       More than n tokens
    --answer <val>        Answer equals val
    --none-only           Only None answers
    --correct-only        Only correct answers
    --wrong-only          Only wrong answers (not None, not correct)
    --problem <id>        Only specific problem (prefix match)
    --batch <name>        Only specific batch (substring match)
    --has-code            Only attempts with code calls
    --no-code             Only attempts without code calls
    --entropy-lt <val>    Entropy less than val
    --entropy-gt <val>    Entropy greater than val

    --count               Just show count, no details
    --stats               Show aggregate statistics
    --verbose             Show turn-level detail

Examples:
    filter_attempts.py log.txt --none-only --errors-gt 0 --stats
    filter_attempts.py log.txt --correct-only --temp 0.3 --stats
    filter_attempts.py log.txt --wrong-only --time-gt 100
    filter_attempts.py log.txt --problem 86e8e5 --verbose

"""

import sys
import os
import re
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def parse_args(argv):
    filters = {}
    flags = set()
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == '--temp':
            filters['temp'] = float(argv[i+1]); i += 2
        elif arg == '--errors-gt':
            filters['errors_gt'] = int(argv[i+1]); i += 2
        elif arg == '--errors-eq':
            filters['errors_eq'] = int(argv[i+1]); i += 2
        elif arg == '--time-gt':
            filters['time_gt'] = float(argv[i+1]); i += 2
        elif arg == '--time-lt':
            filters['time_lt'] = float(argv[i+1]); i += 2
        elif arg == '--turns-gt':
            filters['turns_gt'] = int(argv[i+1]); i += 2
        elif arg == '--tokens-gt':
            filters['tokens_gt'] = int(argv[i+1]); i += 2
        elif arg == '--answer':
            val = argv[i+1]
            filters['answer'] = None if val.lower() == 'none' else int(val); i += 2
        elif arg == '--problem':
            filters['problem'] = argv[i+1]; i += 2
        elif arg == '--batch':
            filters['batch'] = argv[i+1]; i += 2
        elif arg == '--entropy-lt':
            filters['entropy_lt'] = float(argv[i+1]); i += 2
        elif arg == '--entropy-gt':
            filters['entropy_gt'] = float(argv[i+1]); i += 2
        elif arg == '--none-only':
            flags.add('none_only'); i += 1
        elif arg == '--correct-only':
            flags.add('correct_only'); i += 1
        elif arg == '--wrong-only':
            flags.add('wrong_only'); i += 1
        elif arg == '--has-code':
            flags.add('has_code'); i += 1
        elif arg == '--no-code':
            flags.add('no_code'); i += 1
        elif arg == '--count':
            flags.add('count'); i += 1
        elif arg == '--stats':
            flags.add('stats'); i += 1
        elif arg == '--verbose':
            flags.add('verbose'); i += 1
        else:
            i += 1
    return filters, flags


def matches(p, a, filters, flags):
    """Check if an attempt matches all filters."""
    if 'temp' in filters:
        if a.temperature is None or abs(a.temperature - filters['temp']) > 0.05:
            return False
    if 'errors_gt' in filters and a.errors <= filters['errors_gt']:
        return False
    if 'errors_eq' in filters and a.errors != filters['errors_eq']:
        return False
    if 'time_gt' in filters and a.time_s <= filters['time_gt']:
        return False
    if 'time_lt' in filters and a.time_s >= filters['time_lt']:
        return False
    if 'turns_gt' in filters and len(a.turns) <= filters['turns_gt']:
        return False
    if 'tokens_gt' in filters and a.tokens <= filters['tokens_gt']:
        return False
    if 'answer' in filters and a.answer != filters['answer']:
        return False
    if 'problem' in filters and not p.problem_id.startswith(filters['problem']):
        return False
    if 'batch' in filters and filters['batch'].lower() not in (p.batch_name or '').lower():
        return False
    if 'entropy_lt' in filters and a.entropy >= filters['entropy_lt']:
        return False
    if 'entropy_gt' in filters and a.entropy <= filters['entropy_gt']:
        return False
    if 'none_only' in flags and not a.is_none:
        return False
    if 'correct_only' in flags and (a.answer is None or a.answer != p.expected):
        return False
    if 'wrong_only' in flags and (a.is_none or a.answer == p.expected):
        return False
    if 'has_code' in flags and a.code_calls == 0:
        return False
    if 'no_code' in flags and a.code_calls > 0:
        return False
    return True


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    filters, flags = parse_args(sys.argv[2:])
    problems = parse_log(logfile)

    matched = []
    for p in problems:
        for a in p.attempts:
            if matches(p, a, filters, flags):
                matched.append((p, a))

    total_attempts = sum(len(p.attempts) for p in problems)

    if 'count' in flags:
        print(f"{len(matched)}/{total_attempts} attempts match")
        return

    if 'stats' in flags:
        print(f"\n  FILTER RESULTS: {len(matched)}/{total_attempts} attempts match\n")

        if not matched:
            print("  No matching attempts.")
            return

        # Aggregate stats
        answers = [a.answer for _, a in matched if a.answer is not None]
        nones = sum(1 for _, a in matched if a.is_none)
        errors = sum(a.errors for _, a in matched)
        tokens = [a.tokens for _, a in matched]
        times = [a.time_s for _, a in matched if a.time_s > 0]
        entropies = [a.entropy for _, a in matched if a.entropy < float('inf')]
        correct = sum(1 for p, a in matched if a.answer == p.expected)

        print(f"  Answers: {len(answers)} | Nones: {nones} | Correct: {correct}")
        print(f"  Errors: {errors}")
        if tokens:
            print(f"  Tokens: avg={sum(tokens)/len(tokens):.0f} min={min(tokens)} max={max(tokens)}")
        if times:
            print(f"  Time: avg={sum(times)/len(times):.1f}s min={min(times):.1f}s max={max(times):.1f}s")
        if entropies:
            print(f"  Entropy: avg={sum(entropies)/len(entropies):.3f}")
        if answers:
            print(f"  Answer distribution: {dict(Counter(answers).most_common(10))}")

        # Per-problem breakdown
        by_problem = {}
        for p, a in matched:
            if p.problem_id not in by_problem:
                by_problem[p.problem_id] = []
            by_problem[p.problem_id].append(a)

        print(f"\n  Per-problem: {len(by_problem)} problems have matching attempts")
        print(f"  {'ID':<8} {'Match':>6} {'Ans':>4} {'None':>5} {'Corr':>5} {'AvgTok':>7}")
        print(f"  {'─'*8} {'─'*6} {'─'*4} {'─'*5} {'─'*5} {'─'*7}")
        for pid in sorted(by_problem.keys()):
            atts = by_problem[pid]
            n_ans = sum(1 for a in atts if a.answer is not None)
            n_none = sum(1 for a in atts if a.is_none)
            n_corr = sum(1 for a in atts if a.answer is not None and any(
                a.answer == p.expected for p in problems if p.problem_id == pid))
            avg_tok = sum(a.tokens for a in atts) / max(len(atts), 1)
            print(f"  {pid:<8} {len(atts):>6} {n_ans:>4} {n_none:>5} {n_corr:>5} {avg_tok:>6.0f}")
        return

    # Default: list matching attempts
    print(f"\n  {len(matched)}/{total_attempts} attempts match\n")
    print(f"  {'ID':<8} {'Att':>4} {'Ans':>7} {'Status':>7} {'Temp':>5} {'Ent':>6} {'Err':>4} {'Tok':>6} {'Time':>6} {'Turns':>6}")
    print(f"  {'─'*8} {'─'*4} {'─'*7} {'─'*7} {'─'*5} {'─'*6} {'─'*4} {'─'*6} {'─'*6} {'─'*6}")

    for p, a in matched[:100]:
        ans = str(a.answer) if a.answer is not None else 'None'
        if a.answer == p.expected:
            status = 'CORR'
        elif a.is_none:
            status = 'NONE'
        else:
            status = 'WRONG'
        temp = f"{a.temperature:.1f}" if a.temperature is not None else '?'
        ent = f"{a.entropy:.3f}" if a.entropy < float('inf') else 'inf'
        print(f"  {p.problem_id:<8} {a.attempt_num:>4} {ans:>7} {status:>7} {temp:>5} {ent:>6} {a.errors:>4} {a.tokens:>6} {a.time_s:>5.1f}s {len(a.turns):>6}")

        if 'verbose' in flags:
            for t in a.turns:
                err = ' [ERR]' if t.is_error else ''
                code = f' code={len(t.code)}ch' if t.code else ''
                out = f' out={len(t.output)}ch' if t.output else ''
                print(f"        T{t.turn_num}: reasoning={t.reasoning_chars}ch{code}{out}{err}")

    if len(matched) > 100:
        print(f"\n  ... showing first 100 of {len(matched)} matches. Use --count or --stats for full data.")


if __name__ == '__main__':
    main()
