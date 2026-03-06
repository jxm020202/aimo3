#!/usr/bin/env python3
"""
Per-attempt detailed summary for a single problem.
Shows: temp, time, tokens, turns, errors, answer, source, libraries, approach summary.

Usage:
    python3 log_exploration/per_attempt_summary.py <diagnostic.log> [problem_id]
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from log_exploration.log_query import parse_log
from collections import Counter


def analyze(logfile, target_pid=None):
    problems = parse_log(logfile)

    # Deduplicate
    seen = set()
    unique = []
    for p in problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique.append(p)
    problems = unique

    if target_pid:
        problems = [p for p in problems if p.problem_id == target_pid]

    for p in problems:
        print(f"{'='*100}")
        print(f"  PROBLEM: {p.problem_id} | Expected: {p.expected} | Predicted: {p.predicted}")
        correct = p.predicted == p.expected
        print(f"  Status: {'CORRECT' if correct else 'WRONG'}")
        print(f"{'='*100}")

        # Vote distribution
        votes = Counter()
        for a in p.attempts:
            if a.answer is not None:
                votes[a.answer] += 1
        print(f"\n  Vote distribution: {dict(votes.most_common())}")
        print(f"  Total attempts: {len(p.attempts)} | Answered: {sum(votes.values())} | Nones: {sum(1 for a in p.attempts if a.answer is None)}")

        # DB notes
        batch = getattr(p, 'batch_name', '') or ''
        print(f"  Batch: {batch}")

        # Per-attempt table
        print(f"\n  {'#':>3} {'Ans':>7} {'OK':>3} {'Temp':>5} {'Time':>6} {'Tokens':>7} {'Turns':>6} {'Code':>5} {'Errs':>5} {'Source':>12} {'Conf':>5} {'Entropy':>8} {'Stop':>15}")
        print(f"  {'─'*3} {'─'*7} {'─'*3} {'─'*5} {'─'*6} {'─'*7} {'─'*6} {'─'*5} {'─'*5} {'─'*12} {'─'*5} {'─'*8} {'─'*15}")

        for i, a in enumerate(p.attempts):
            idx = getattr(a, 'attempt_index', i+1)
            ans = a.answer if a.answer is not None else 'None'
            ok = 'Y' if a.answer == p.expected else ('N' if a.answer is not None else '-')
            temp = getattr(a, 'temperature', '?')
            time_s = getattr(a, 'time_s', 0)
            tokens = getattr(a, 'response_length', 0) or getattr(a, 'tokens', 0) or 0
            turns = len(a.turns) if hasattr(a, 'turns') else 0
            code_calls = getattr(a, 'code_calls', 0)
            errors = getattr(a, 'errors', 0)
            source = getattr(a, 'source', '?')
            conf = getattr(a, 'confidence', '?')
            entropy = getattr(a, 'entropy', 0)
            stop = getattr(a, 'stop_reason', '?')

            print(f"  {idx:>3} {str(ans):>7} {ok:>3} {temp:>5} {time_s:>5.0f}s {tokens:>7} {turns:>6} {code_calls:>5} {errors:>5} {str(source):>12} {str(conf):>5} {entropy:>8.3f} {str(stop):>15}")

        # Per-attempt detail: first code cell + approach
        print(f"\n  {'='*96}")
        print(f"  PER-ATTEMPT DETAIL")
        print(f"  {'='*96}")

        for i, a in enumerate(p.attempts):
            idx = getattr(a, 'attempt_index', i+1)
            ans = a.answer if a.answer is not None else 'None'
            ok = 'CORRECT' if a.answer == p.expected else ('WRONG' if a.answer is not None else 'NONE')
            temp = getattr(a, 'temperature', '?')
            time_s = getattr(a, 'time_s', 0)
            errors = getattr(a, 'errors', 0)
            code_calls = getattr(a, 'code_calls', 0)
            source = getattr(a, 'source', '?')
            libs = getattr(a, 'libraries', []) or []
            vboxed = getattr(a, 'vboxed_checkpoints', []) or []

            print(f"\n  {'─'*96}")
            print(f"  ATTEMPT {idx} [{ok}] answer={ans} temp={temp} time={time_s:.0f}s errors={errors} code_calls={code_calls}")
            print(f"  source={source} libs={', '.join(libs) if libs else 'none'}")
            if vboxed:
                cp_str = ', '.join(f"turn{cp.get('turn','?')}={cp.get('answer','?')}" for cp in vboxed)
                print(f"  vboxed_checkpoints: {cp_str}")

            # Show reasoning summary from turns
            if hasattr(a, 'turns') and a.turns:
                # Show first reasoning snippet (approach identification)
                first_reasoning = None
                first_code = None
                last_code = None
                error_turns = []

                for t in a.turns:
                    text = getattr(t, 'reasoning_text', '') or ''
                    code = getattr(t, 'code', '') or ''
                    output = getattr(t, 'output', '') or ''
                    is_err = getattr(t, 'is_error', False)

                    if text and first_reasoning is None:
                        # Get first 200 chars of reasoning
                        first_reasoning = text[:300].replace('\n', ' ').strip()
                    if code and first_code is None:
                        first_code = code[:200].replace('\n', ' ').strip()
                    if code:
                        last_code = code[:200].replace('\n', ' ').strip()
                    if is_err:
                        err_msg = output[:150].replace('\n', ' ').strip() if output else 'unknown error'
                        error_turns.append((getattr(t, 'turn_number', '?'), err_msg))

                if first_reasoning:
                    print(f"  Approach: {first_reasoning[:250]}{'...' if len(first_reasoning) > 250 else ''}")
                if first_code:
                    print(f"  First code: {first_code[:200]}{'...' if len(str(first_code)) > 200 else ''}")
                if error_turns:
                    print(f"  Errors ({len(error_turns)}):")
                    for tn, msg in error_turns[:3]:
                        print(f"    Turn {tn}: {msg[:120]}")
                    if len(error_turns) > 3:
                        print(f"    ... and {len(error_turns)-3} more")

        # Summary stats
        print(f"\n\n  {'='*96}")
        print(f"  SUMMARY STATS")
        print(f"  {'='*96}")

        times = [getattr(a, 'time_s', 0) for a in p.attempts]
        tokens_list = [getattr(a, 'response_length', 0) or getattr(a, 'tokens', 0) or 0 for a in p.attempts]
        correct_times = [getattr(a, 'time_s', 0) for a in p.attempts if a.answer == p.expected]
        wrong_times = [getattr(a, 'time_s', 0) for a in p.attempts if a.answer is not None and a.answer != p.expected]

        import numpy as np
        if times:
            print(f"  Time: min={min(times):.0f}s  median={np.median(times):.0f}s  max={max(times):.0f}s  mean={np.mean(times):.0f}s")
        if correct_times:
            print(f"  Correct time: min={min(correct_times):.0f}s  median={np.median(correct_times):.0f}s  max={max(correct_times):.0f}s")
        if wrong_times:
            print(f"  Wrong time: min={min(wrong_times):.0f}s  median={np.median(wrong_times):.0f}s  max={max(wrong_times):.0f}s")
        if tokens_list:
            print(f"  Tokens: min={min(tokens_list)}  median={int(np.median(tokens_list))}  max={max(tokens_list)}  total={sum(tokens_list)}")

        # Temp accuracy
        temp_stats = {}
        for a in p.attempts:
            temp = getattr(a, 'temperature', None)
            if temp not in temp_stats:
                temp_stats[temp] = {'correct': 0, 'wrong': 0, 'none': 0, 'total': 0, 'times': [], 'tokens': []}
            temp_stats[temp]['total'] += 1
            temp_stats[temp]['times'].append(getattr(a, 'time_s', 0))
            temp_stats[temp]['tokens'].append(getattr(a, 'response_length', 0) or 0)
            if a.answer == p.expected:
                temp_stats[temp]['correct'] += 1
            elif a.answer is not None:
                temp_stats[temp]['wrong'] += 1
            else:
                temp_stats[temp]['none'] += 1

        print(f"\n  Per-temperature breakdown:")
        print(f"  {'Temp':>5} {'N':>3} {'Correct':>8} {'Wrong':>6} {'None':>5} {'Acc%':>6} {'AvgTime':>8} {'AvgTok':>8}")
        for temp in sorted(temp_stats.keys(), key=lambda x: x if x is not None else -1):
            s = temp_stats[temp]
            acc = s['correct'] / s['total'] * 100 if s['total'] > 0 else 0
            avg_t = np.mean(s['times']) if s['times'] else 0
            avg_tok = int(np.mean(s['tokens'])) if s['tokens'] else 0
            print(f"  {temp if temp is not None else '?':>5} {s['total']:>3} {s['correct']:>8} {s['wrong']:>6} {s['none']:>5} {acc:>5.0f}% {avg_t:>7.0f}s {avg_tok:>8}")

        # Answer source breakdown
        source_stats = Counter()
        source_correct = Counter()
        for a in p.attempts:
            src = getattr(a, 'source', 'unknown')
            source_stats[src] += 1
            if a.answer == p.expected:
                source_correct[src] += 1

        print(f"\n  Answer source breakdown:")
        for src, count in source_stats.most_common():
            c = source_correct.get(src, 0)
            print(f"    {src}: {count} attempts, {c} correct ({c/count*100:.0f}%)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <diagnostic.log> [problem_id]")
        sys.exit(1)

    pid = sys.argv[2] if len(sys.argv) > 2 else None
    analyze(sys.argv[1], pid)
