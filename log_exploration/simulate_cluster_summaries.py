#!/usr/bin/env python3
"""Simulate what _build_cluster_summaries would produce for each problem in a run.

Usage:
    python3 log_exploration/simulate_cluster_summaries.py output/shiv-latest-4/diagnostic.log
    python3 log_exploration/simulate_cluster_summaries.py output/shiv-latest-4/diagnostic.log --problem f7d683
    python3 log_exploration/simulate_cluster_summaries.py output/shiv-latest-4/diagnostic.log --wrong-only
    python3 log_exploration/simulate_cluster_summaries.py output/shiv-latest-4/diagnostic.log --rerun-only
"""
import sys
import re
import argparse
from collections import Counter, defaultdict
from log_exploration.log_query import parse_log


def summarize_attempt(result: dict) -> dict:
    """Extract structured signal from one attempt's conversation (mirrors AIMO3Solver._summarize_attempt)."""
    conv = result.get('Conversation', [])
    libs = set()
    for entry in conv:
        if entry.get('type') == 'code_call':
            code = entry.get('code', '')
            for m in re.findall(r'(?:from|import)\s+([\w.]+)', code):
                root = m.split('.')[0]
                if root not in ('sys', 'os', 'time', 'typing', 'json'):
                    libs.add(root)
    computed_values = []
    for entry in conv:
        if entry.get('type') == 'code_call' and not entry.get('error'):
            out = entry.get('output', '').strip()
            nums = re.findall(r'\b(\d{1,5})\b', out[-200:] if len(out) > 200 else out)
            for n in nums[-3:]:
                val = int(n)
                if 0 < val < 100000 and val not in computed_values:
                    computed_values.append(val)
    return {'computed': computed_values[-5:]}


def build_cluster_summaries(detailed_results: list) -> str:
    """Mirrors AIMO3Solver._build_cluster_summaries exactly."""
    clusters = {}
    for r in detailed_results:
        key = r['Answer']
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(r)

    all_answers = set(a for a in clusters if a is not None)
    sorted_clusters = sorted(
        ((ans, atts) for ans, atts in clusters.items() if len(atts) >= 2),
        key=lambda x: -len(x[1])
    )

    parts = []
    total_chars = 0
    MAX_CHARS = 1500

    for ans, atts in sorted_clusters:
        if total_chars >= MAX_CHARS:
            break

        if ans is None:
            stops = Counter(r.get('Stop_Reason', '?') for r in atts)
            top_stop = stops.most_common(1)[0][0] if stops else '?'
            part = f'{len(atts)}x returned None (common: {top_stop})'
            parts.append(part)
            total_chars += len(part)
            continue

        def _rep_score(r):
            conv = r.get('Conversation', [])
            successful = sum(1 for e in conv if e.get('type') == 'code_call' and not e.get('error'))
            return (successful, len(conv))

        best = max(atts, key=_rep_score)
        conv = best.get('Conversation', [])
        n_turns = len(conv)
        time_s = best.get('Time', 0)

        approach = ''
        for entry in conv:
            if entry.get('type') == 'reasoning' and len(entry.get('text', '')) > 30:
                approach = entry['text'].strip().replace('\n', ' ')[:200]
                break

        key_code = ''
        key_output = ''
        for entry in reversed(conv):
            if entry.get('type') == 'code_call' and not entry.get('error') and entry.get('output', '').strip():
                key_code = entry['code'].strip().replace('\n', '; ')[:200]
                key_output = entry['output'].strip().replace('\n', ' ')[:150]
                break

        cross_signals = []
        other_answers = all_answers - {ans}
        for r in atts:
            s = summarize_attempt(r)
            for val in s.get('computed', []):
                if val in other_answers:
                    cross_signals.append((r['Attempt'], val))
        seen_vals = set()
        unique_cross = []
        for att_num, val in cross_signals:
            if val not in seen_vals:
                seen_vals.add(val)
                unique_cross.append((att_num, val))

        header = f'{len(atts)}x answered {ans} (best: Att {best["Attempt"]}, {n_turns} turns, {time_s:.0f}s)'
        lines = [header]
        if approach:
            lines.append(f'  Approach: {approach}')
        if key_code:
            lines.append(f'  Code: {key_code}')
        if key_output:
            lines.append(f'  Output: {key_output}')
        for att_num, val in unique_cross[:2]:
            lines.append(f'  NOTE: Att {att_num} also computed {val} (matches another cluster)')

        part = '\n'.join(lines)
        if total_chars + len(part) > MAX_CHARS and parts:
            break
        parts.append(part)
        total_chars += len(part)

    if not parts:
        return ''
    return '--- Answer clusters ---\n' + '\n\n'.join(parts) + '\n--- End clusters ---'


def attempts_to_dicts(attempts) -> list[dict]:
    """Convert log_query Attempt objects to the dict format expected by build_cluster_summaries."""
    results = []
    for a in attempts:
        conv = []
        for t in (a.turns if hasattr(a, 'turns') else []):
            if hasattr(t, 'reasoning_text') and t.reasoning_text:
                conv.append({
                    'turn': t.turn_num, 'type': 'reasoning',
                    'text': t.reasoning_text, 'code': '', 'output': '', 'error': False
                })
            if hasattr(t, 'code') and t.code:
                conv.append({
                    'turn': t.turn_num, 'type': 'code_call',
                    'code': t.code, 'output': getattr(t, 'output', ''),
                    'error': getattr(t, 'is_error', False)
                })
        results.append({
            'Attempt': a.attempt_num,
            'Answer': a.answer,
            'Time': a.time_s,
            'Stop_Reason': getattr(a, 'stop_reason', '?'),
            'Python Calls': getattr(a, 'code_calls', 0),
            'Python Errors': getattr(a, 'errors', 0),
            'Conversation': conv,
            'Vboxed_Checkpoints': [],
            'Temperature': getattr(a, 'temperature', '?'),
            'Entropy': a.entropy,
        })
    return results


def analyze_problem(p, verbose=False):
    """Analyze one problem and print cluster summary + assessment."""
    n_attempts = len(p.attempts)
    is_rerun = n_attempts > 24
    r1 = p.attempts[:24]
    r2 = p.attempts[24:] if is_rerun else []

    r1_answers = Counter(a.answer for a in r1)
    r1_top = r1_answers.most_common(1)[0] if r1_answers else (None, 0)

    # Convert R1 to dicts and build cluster summary
    r1_dicts = attempts_to_dicts(r1)
    cluster_summary = build_cluster_summaries(r1_dicts)

    # Check: did correct answer appear in R1?
    correct_in_r1 = sum(1 for a in r1 if a.answer == p.expected)
    correct_in_r2 = sum(1 for a in r2 if a.answer == p.expected) if r2 else 0

    # Cross-cluster check: did any cluster's computed values include the correct answer?
    cross_cluster_has_correct = False
    for a in r1:
        conv_entries = []
        for t in (a.turns if hasattr(a, 'turns') else []):
            if hasattr(t, 'code') and t.code:
                conv_entries.append({
                    'type': 'code_call', 'code': t.code,
                    'output': getattr(t, 'output', ''),
                    'error': getattr(t, 'is_error', False)
                })
        s = summarize_attempt({'Conversation': conv_entries})
        if p.expected in s.get('computed', []) and a.answer != p.expected:
            cross_cluster_has_correct = True
            break

    print(f'\n{"="*70}')
    status = 'CORRECT' if p.correct else 'WRONG'
    print(f'  {p.problem_id} | {status} | pred={p.predicted} exp={p.expected} | {p.wall_time:.0f}s | {n_attempts} attempts')
    print(f'  R1 votes: {dict(r1_answers.most_common())}')
    if is_rerun:
        r2_answers = Counter(a.answer for a in r2)
        print(f'  R2 votes: {dict(r2_answers.most_common())}')
    print(f'  Correct in R1: {correct_in_r1}/24 | Correct in R2: {correct_in_r2}/{len(r2)}')
    print(f'  Cross-cluster has correct (wrong att computed {p.expected}): {cross_cluster_has_correct}')
    print(f'{"="*70}')

    if cluster_summary:
        print(f'\n{cluster_summary}')
        print(f'\n  [{len(cluster_summary)} chars, ~{len(cluster_summary)//4} tokens]')
    else:
        print('\n  [No cluster summary — all singletons or empty]')

    # Assessment
    print(f'\n  ASSESSMENT:')
    if p.correct and not is_rerun:
        print(f'  - Correct without rerun. Cluster summary not needed.')
    elif p.correct and is_rerun:
        if correct_in_r2 > correct_in_r1:
            print(f'  - Rerun helped ({correct_in_r1}→{correct_in_r2} correct). Cluster summary could have helped MORE.')
        else:
            print(f'  - Rerun helped (final answer correct). Summary adds signal for faster convergence.')
    elif not p.correct and cross_cluster_has_correct:
        print(f'  - WRONG but correct value was computed by a wrong-answer attempt!')
        print(f'    Cluster summary would surface this as a cross-cluster NOTE.')
        print(f'    This is the HIGH VALUE case — R2 agents see the conflicting computation.')
    elif not p.correct and correct_in_r1 > 0:
        print(f'  - WRONG but {correct_in_r1} R1 attempts got correct. Outvoted.')
        print(f'    Cluster summary would show correct approach + code for R2 to verify.')
    else:
        print(f'  - WRONG and no R1 attempt found correct. Model capability gap.')
        print(f'    Cluster summary helps avoid dead ends but may not fix this.')

    return {
        'pid': p.problem_id,
        'correct': p.correct,
        'is_rerun': is_rerun,
        'cross_cluster': cross_cluster_has_correct,
        'correct_in_r1': correct_in_r1,
        'summary_chars': len(cluster_summary),
    }


def main():
    parser = argparse.ArgumentParser(description='Simulate cluster summaries for diagnostic logs')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--problem', '-p', help='Analyze specific problem ID')
    parser.add_argument('--wrong-only', action='store_true', help='Only show wrong problems')
    parser.add_argument('--rerun-only', action='store_true', help='Only show problems with reruns')
    parser.add_argument('--summary', action='store_true', help='Summary table only, no cluster details')
    args = parser.parse_args()

    problems = parse_log(args.logfile)

    if args.problem:
        found = [p for p in problems if p.problem_id.startswith(args.problem)]
        if not found:
            print(f'Problem {args.problem} not found')
            sys.exit(1)
        for p in found:
            analyze_problem(p, verbose=True)
        return

    # Filter
    filtered = problems
    if args.wrong_only:
        filtered = [p for p in filtered if not p.correct]
    if args.rerun_only:
        filtered = [p for p in filtered if len(p.attempts) > 24]

    stats = []
    for p in filtered:
        if args.summary:
            # Quick stats only
            n = len(p.attempts)
            r1 = p.attempts[:24]
            r1_dicts = attempts_to_dicts(r1)
            cs = build_cluster_summaries(r1_dicts)
            correct_in_r1 = sum(1 for a in r1 if a.answer == p.expected)

            # Check cross-cluster
            cross = False
            for a in r1:
                conv_entries = []
                for t in (a.turns if hasattr(a, 'turns') else []):
                    if hasattr(t, 'code') and t.code:
                        conv_entries.append({
                            'type': 'code_call', 'code': t.code,
                            'output': getattr(t, 'output', ''),
                            'error': getattr(t, 'is_error', False)
                        })
                s = summarize_attempt({'Conversation': conv_entries})
                if p.expected in s.get('computed', []) and a.answer != p.expected:
                    cross = True
                    break

            status = 'OK' if p.correct else 'WRONG'
            rerun = 'Y' if n > 24 else 'N'
            cross_str = 'YES' if cross else 'no'
            print(f'{p.problem_id}  {status:>5}  rerun={rerun}  correct_in_r1={correct_in_r1:>2}/24  cross_cluster={cross_str:>3}  summary={len(cs):>4}ch')
            stats.append({'correct': p.correct, 'cross': cross, 'correct_in_r1': correct_in_r1})
        else:
            result = analyze_problem(p)
            stats.append(result)

    if stats and args.summary:
        wrong = [s for s in stats if not s['correct']]
        cross_count = sum(1 for s in wrong if s['cross'])
        has_correct = sum(1 for s in wrong if s['correct_in_r1'] > 0)
        print(f'\n--- Summary ---')
        print(f'Total: {len(stats)} | Wrong: {len(wrong)}')
        print(f'Wrong with cross-cluster signal: {cross_count}/{len(wrong)}')
        print(f'Wrong with correct in R1 votes: {has_correct}/{len(wrong)}')


if __name__ == '__main__':
    main()
