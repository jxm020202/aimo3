#!/usr/bin/env python3
"""
Validate GenSelect summary builders: OLD (2000-char truncation) vs NEW (4000-char smart truncation).

Simulates what _build_genselect_solutions produces for real problems from diagnostic logs.
Shows full summary text side-by-side so you can read what the GenSelect judge would see.

Usage:
    python3 log_exploration/validate_genselect_summaries.py output/120b-v38/diagnostic.log
    python3 log_exploration/validate_genselect_summaries.py output/120b-v38/diagnostic.log output/shiv-latest-6/diagnostic.log
"""

import sys
import os
import re
import math
import random
from collections import Counter
from typing import List, Tuple, Optional, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log, Problem, Attempt, Turn


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _count_code_turns(attempt: Attempt) -> int:
    """Count turns that have code (code_call turns)."""
    return sum(1 for t in attempt.turns if t.code)


def _count_error_turns(attempt: Attempt) -> int:
    """Count turns with errors."""
    return sum(1 for t in attempt.turns if t.is_error)


def _has_verification(attempt: Attempt) -> bool:
    """Check if any turn looks like a verification step (re-checking answer)."""
    for t in attempt.turns:
        if t.code:
            code_lower = t.code.lower()
            if any(kw in code_lower for kw in ['verify', 'check', 'assert', 'confirm', 'validate', 'test']):
                return True
    return False


def _has_approach_pivot(turn: Turn) -> bool:
    """Check if a turn has a genuine approach pivot (not just common boilerplate imports).

    Only flags imports of optimization/solver libraries or strategy-changing keywords.
    Common imports like itertools/sympy/numpy are NOT pivots (they appear in nearly every attempt).
    """
    if not turn.code:
        return False
    code_lower = turn.code.lower()
    # Only flag genuinely rare/strategic imports and approach changes
    pivot_markers = [
        'from scipy.optimize', 'linear_sum_assignment', 'linprog', 'milp',
        'import pulp', 'from pulp',
        'import z3', 'from z3',
        'import networkx', 'from networkx',
        'import cvxpy', 'from cvxpy',
        # Strategy keywords (not just library names)
        'backtrack', 'dynamic program', 'dp[', 'dp =',
        'bfs(', 'dfs(', 'dijkstra',
    ]
    return any(marker in code_lower for marker in pivot_markers)


def _is_error_recovery(turn: Turn, prev_turn: Optional[Turn]) -> bool:
    """Check if this turn recovers from a previous error."""
    if prev_turn and prev_turn.is_error and turn.code and not turn.is_error:
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# OLD Builder: lowest entropy, raw format, 2000 char truncation
# ─────────────────────────────────────────────────────────────────────────────

def old_pick_representative(attempts: List[Attempt]) -> Attempt:
    """OLD: pick by lowest entropy (most confident)."""
    def _score(a: Attempt):
        e = a.entropy if a.entropy is not None and math.isfinite(a.entropy) else 999.0
        return -e  # higher = better (lower entropy)
    return max(attempts, key=_score)


def old_build_summary(rep: Attempt, answer) -> str:
    """OLD builder: raw Code:/Output: format, 2000 char truncation (first 500 + last 1500)."""
    sol_parts = []
    for turn in rep.turns:
        # Reasoning
        if turn.reasoning_text and len(turn.reasoning_text.strip()) > 30:
            sol_parts.append(turn.reasoning_text.strip())
        # Code + output
        if turn.code:
            sol_parts.append(f'Code: {turn.code.strip()}')
        if turn.output:
            prefix = 'Error: ' if turn.is_error else 'Output: '
            sol_parts.append(f'{prefix}{turn.output.strip()}')

    sol_text = '\n'.join(sol_parts)

    truncated = False
    trunc_boundary = -1
    if len(sol_text) > 2000:
        trunc_boundary = 500
        sol_text = sol_text[:500] + '\n... (middle truncated) ...\n' + sol_text[-1500:]
        truncated = True

    sol_text += f'\n\\boxed{{{answer}}}'
    return sol_text, truncated, trunc_boundary


# ─────────────────────────────────────────────────────────────────────────────
# NEW Builder: most code turns, structured format, 4000 char smart truncation
# ─────────────────────────────────────────────────────────────────────────────

def new_pick_representative(attempts: List[Attempt]) -> Attempt:
    """NEW: pick by most code turns (then lowest entropy as tiebreak)."""
    def _score(a: Attempt):
        code_turns = _count_code_turns(a)
        e = a.entropy if a.entropy is not None and math.isfinite(a.entropy) else 999.0
        return (code_turns, -e)  # more code turns first, then lower entropy
    return max(attempts, key=_score)


def new_build_summary(rep: Attempt, answer, all_attempts_for_answer: List[Attempt]) -> str:
    """NEW builder: structured format with metadata, smart truncation at 4000 chars."""
    n_votes = len(all_attempts_for_answer)
    n_code_steps = _count_code_turns(rep)
    n_errors_recovered = 0
    has_verif = _has_verification(rep)

    # Count error recoveries
    for i, turn in enumerate(rep.turns):
        prev = rep.turns[i - 1] if i > 0 else None
        if _is_error_recovery(turn, prev):
            n_errors_recovered += 1

    # Metadata header
    verif_str = 'includes verification' if has_verif else 'no verification'
    header = f'[{n_votes} votes | {n_code_steps} computation steps | {n_errors_recovered} errors recovered | {verif_str}]'

    # Build structured turns
    turn_entries = []  # (turn_index, label, text, is_key)
    step_num = 0
    for i, turn in enumerate(rep.turns):
        prev = rep.turns[i - 1] if i > 0 else None
        parts = []

        # Reasoning
        if turn.reasoning_text and len(turn.reasoning_text.strip()) > 30:
            parts.append(turn.reasoning_text.strip())

        # Code
        if turn.code:
            step_num += 1
            parts.append(f'```python\n{turn.code.strip()}\n```')

        # Output
        if turn.output:
            prefix = 'Error' if turn.is_error else 'Result'
            parts.append(f'{prefix}: {turn.output.strip()}')

        if not parts:
            continue

        # Determine if this turn is KEY (should be preserved during truncation)
        is_key = False
        key_reason = ''
        if i == 0:
            is_key = True
            key_reason = 'first'
        elif i >= len(rep.turns) - 2:
            is_key = True
            key_reason = 'final'
        elif turn.is_error:
            is_key = True
            key_reason = 'error'
        elif _is_error_recovery(turn, prev):
            is_key = True
            key_reason = 'recovery'
        elif _has_approach_pivot(turn):
            is_key = True
            key_reason = 'pivot'
        elif has_verif and turn.code and any(
            kw in turn.code.lower() for kw in ['verify', 'check', 'assert', 'confirm']
        ):
            is_key = True
            key_reason = 'verification'

        label = f'Step {step_num} (code)' if turn.code else f'Step {step_num} (reasoning)'
        text = '\n'.join(parts)
        turn_entries.append((i, label, text, is_key, key_reason))

    if not turn_entries:
        return f'{header}\n(no content)\n\\boxed{{{answer}}}', False, -1

    # Smart truncation at 4000 chars
    full_text = header + '\n'
    for idx, (i, label, text, is_key, key_reason) in enumerate(turn_entries):
        full_text += f'\n{label}:\n{text}\n'

    truncated = False
    if len(full_text) <= 4000:
        sol_text = full_text
    else:
        truncated = True
        # Keep: first turn, last 2 turns, and all KEY turns
        # Omit: non-key middle turns
        n = len(turn_entries)
        keep_indices = set()

        # Always keep first
        keep_indices.add(0)
        # Always keep last 2
        if n >= 2:
            keep_indices.add(n - 1)
            keep_indices.add(n - 2)
        elif n == 1:
            keep_indices.add(0)

        # Keep KEY middle turns
        for idx, (i, label, text, is_key, key_reason) in enumerate(turn_entries):
            if is_key:
                keep_indices.add(idx)

        # Build with omission markers
        sol_text = header + '\n'
        omitted_start = None
        omitted_count = 0
        for idx in range(n):
            if idx in keep_indices:
                if omitted_count > 0:
                    sol_text += f'\n[... {omitted_count} intermediate step{"s" if omitted_count > 1 else ""} omitted ...]\n'
                    omitted_count = 0
                i, label, text, is_key, key_reason = turn_entries[idx]
                marker = f' <-- {key_reason}' if key_reason and key_reason not in ('first', 'final') else ''
                sol_text += f'\n{label}{marker}:\n{text}\n'
            else:
                omitted_count += 1

        if omitted_count > 0:
            sol_text += f'\n[... {omitted_count} intermediate step{"s" if omitted_count > 1 else ""} omitted ...]\n'

        # If still over 4000 after smart truncation, do hard truncation on individual turn texts
        if len(sol_text) > 4000:
            # Truncate the longest non-first, non-last turn texts
            sol_text = sol_text[:1500] + '\n[... hard truncated middle ...]\n' + sol_text[-2500:]

    sol_text += f'\n\\boxed{{{answer}}}'
    return sol_text, truncated, len(full_text)


# ─────────────────────────────────────────────────────────────────────────────
# Analysis: what key content is in the OLD truncated middle that NEW keeps?
# ─────────────────────────────────────────────────────────────────────────────

def analyze_old_truncated_middle(rep: Attempt) -> Dict[str, Any]:
    """Analyze what the OLD builder cuts out in the middle section."""
    sol_parts = []
    for turn in rep.turns:
        if turn.reasoning_text and len(turn.reasoning_text.strip()) > 30:
            sol_parts.append(('reasoning', turn.reasoning_text.strip()))
        if turn.code:
            sol_parts.append(('code', f'Code: {turn.code.strip()}'))
        if turn.output:
            prefix = 'Error: ' if turn.is_error else 'Output: '
            sol_parts.append(('output', f'{prefix}{turn.output.strip()}'))

    full = '\n'.join(text for _, text in sol_parts)
    if len(full) <= 2000:
        return {'truncated': False, 'lost_chars': 0, 'lost_items': []}

    # Characters 500 to len-1500 are lost
    lost_start = 500
    lost_end = len(full) - 1500
    lost_text = full[lost_start:lost_end]

    # What's in the lost section?
    lost_items = []
    if 'Error:' in lost_text or 'error' in lost_text.lower():
        lost_items.append('error messages')
    if 'import ' in lost_text:
        lost_items.append('imports/approach pivots')
    if re.search(r'Output:\s*\d', lost_text):
        lost_items.append('computed outputs')
    if 'verify' in lost_text.lower() or 'check' in lost_text.lower():
        lost_items.append('verification steps')
    if re.search(r'Code:', lost_text):
        code_blocks = lost_text.count('Code:')
        lost_items.append(f'{code_blocks} code block(s)')

    return {
        'truncated': True,
        'lost_chars': lost_end - lost_start,
        'lost_text_preview': lost_text[:300] + '...' if len(lost_text) > 300 else lost_text,
        'lost_items': lost_items,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main simulation
# ─────────────────────────────────────────────────────────────────────────────

def simulate_problem(p: Problem) -> Dict[str, Any]:
    """Run both OLD and NEW builders on a problem. Returns analysis dict."""
    # Group attempts by answer
    clusters = {}
    for a in p.attempts:
        if a.answer is not None:
            if a.answer not in clusters:
                clusters[a.answer] = []
            clusters[a.answer].append(a)

    if len(clusters) < 2:
        return None  # GenSelect needs >= 2 clusters

    # Sort by vote count, take top 3 for detailed analysis
    sorted_clusters = sorted(clusters.items(), key=lambda x: -len(x[1]))[:3]

    result = {
        'problem_id': p.problem_id,
        'predicted': p.predicted,
        'expected': p.expected,
        'correct': p.correct,
        'total_attempts': len(p.attempts),
        'vote_dist': Counter(a.answer for a in p.attempts).most_common(),
        'clusters': [],
    }

    old_total_chars = 0
    new_total_chars = 0
    old_truncated_count = 0
    new_truncated_count = 0
    key_turns_saved = 0

    for ans, atts in sorted_clusters:
        # OLD representative
        old_rep = old_pick_representative(atts)
        old_summary, old_trunc, old_trunc_boundary = old_build_summary(old_rep, ans)

        # NEW representative
        new_rep = new_pick_representative(atts)
        new_summary, new_trunc, new_full_len = new_build_summary(new_rep, ans, atts)

        # Analyze what OLD loses
        old_loss = analyze_old_truncated_middle(old_rep)

        # Count key turns in the NEW rep that fall in OLD builder's truncated middle.
        # We check the NEW rep's turns, but measure against what OLD would see
        # if it had this same attempt (i.e., middle turns between char 500 and len-1500).
        key_in_middle = 0
        if new_trunc:
            # Count only actually-key middle turns (not first, not last 2)
            n_turns = len(new_rep.turns)
            for i, turn in enumerate(new_rep.turns):
                if i == 0 or i >= n_turns - 2:
                    continue  # first/last are always kept
                prev = new_rep.turns[i - 1] if i > 0 else None
                is_key = (
                    turn.is_error
                    or _is_error_recovery(turn, prev)
                    or _has_approach_pivot(turn)
                    or (turn.code and any(kw in turn.code.lower()
                        for kw in ['verify', 'check', 'assert', 'confirm']))
                )
                if is_key:
                    key_in_middle += 1

        same_rep = (old_rep.attempt_num == new_rep.attempt_num)

        cluster_info = {
            'answer': ans,
            'votes': len(atts),
            'is_correct_answer': (ans == p.expected),
            'old_rep_attempt': old_rep.attempt_num,
            'old_rep_entropy': old_rep.entropy,
            'old_rep_turns': len(old_rep.turns),
            'old_rep_code_turns': _count_code_turns(old_rep),
            'new_rep_attempt': new_rep.attempt_num,
            'new_rep_entropy': new_rep.entropy,
            'new_rep_turns': len(new_rep.turns),
            'new_rep_code_turns': _count_code_turns(new_rep),
            'same_rep': same_rep,
            'old_summary': old_summary,
            'old_chars': len(old_summary),
            'old_truncated': old_trunc,
            'new_summary': new_summary,
            'new_chars': len(new_summary),
            'new_truncated': new_trunc,
            'old_loss': old_loss,
            'key_turns_saved': key_in_middle,
        }
        result['clusters'].append(cluster_info)

        old_total_chars += len(old_summary)
        new_total_chars += len(new_summary)
        if old_trunc:
            old_truncated_count += 1
        if new_trunc:
            new_truncated_count += 1
        key_turns_saved += key_in_middle

    result['old_total_chars'] = old_total_chars
    result['new_total_chars'] = new_total_chars
    result['old_truncated_count'] = old_truncated_count
    result['new_truncated_count'] = new_truncated_count
    result['key_turns_saved'] = key_turns_saved

    return result


def print_divider(char='=', width=100):
    print(char * width)


def print_summary_text(title: str, text: str, max_display: int = 0):
    """Print a summary text with clear boundaries."""
    print(f'  --- {title} ({len(text)} chars) ---')
    if max_display > 0 and len(text) > max_display:
        print(text[:max_display])
        print(f'  [...{len(text) - max_display} more chars not shown...]')
    else:
        # Indent each line for readability
        for line in text.split('\n'):
            print(f'  | {line}')
    print(f'  --- end {title} ---')


def main():
    if len(sys.argv) < 2:
        print(f'Usage: {sys.argv[0]} <diagnostic.log> [<diagnostic2.log> ...]')
        sys.exit(1)

    # Parse all provided log files
    all_problems = []
    for logpath in sys.argv[1:]:
        print(f'Parsing {logpath}...')
        probs = parse_log(logpath)
        print(f'  Found {len(probs)} problems ({sum(1 for p in probs if p.correct)} correct)')
        all_problems.extend(probs)

    # Deduplicate by problem_id (keep first occurrence)
    seen = set()
    unique_problems = []
    for p in all_problems:
        if p.problem_id not in seen:
            seen.add(p.problem_id)
            unique_problems.append(p)

    print(f'\nTotal unique problems: {len(unique_problems)}')

    # Filter to problems with >= 2 answer clusters (GenSelect requires this)
    eligible = []
    for p in unique_problems:
        clusters = set(a.answer for a in p.attempts if a.answer is not None)
        if len(clusters) >= 2:
            eligible.append(p)

    print(f'Eligible for GenSelect (>= 2 clusters): {len(eligible)}')

    # Sample: prioritize a mix of correct and wrong, preferring interesting cases
    wrong = [p for p in eligible if not p.correct]
    correct = [p for p in eligible if p.correct]

    # Pick up to 3 wrong, up to 3 correct
    random.seed(42)
    sampled = []
    if wrong:
        sampled.extend(wrong[:3])
    if correct:
        # Prefer correct problems with more diverse clusters (more interesting summaries)
        correct_sorted = sorted(correct, key=lambda p: -len(set(a.answer for a in p.attempts if a.answer is not None)))
        sampled.extend(correct_sorted[:max(0, 6 - len(sampled))])

    sampled = sampled[:6]

    print(f'Sampled {len(sampled)} problems for analysis')
    print()

    # Run simulation on each
    results = []
    full_display_count = 0  # Show full text for first 2 problems

    for p in sampled:
        r = simulate_problem(p)
        if r is None:
            print(f'Problem {p.problem_id}: skipped (< 2 clusters)')
            continue
        results.append(r)

        print_divider('=')
        status = 'OK' if r['correct'] else 'FAIL'
        print(f"PROBLEM {r['problem_id']} | Status: {status} | Predicted: {r['predicted']} | Expected: {r['expected']}")
        print(f"Total attempts: {r['total_attempts']}")
        print(f"Vote distribution: {r['vote_dist']}")
        print()

        for ci, c in enumerate(r['clusters']):
            correct_marker = ' <<<< CORRECT ANSWER' if c['is_correct_answer'] else ''
            print(f'  CLUSTER {ci}: answer={c["answer"]} ({c["votes"]} votes){correct_marker}')
            print()

            # Representative comparison
            if c['same_rep']:
                print(f'    Representative: Attempt {c["old_rep_attempt"]} (SAME for both OLD and NEW)')
                print(f'      Entropy: {c["old_rep_entropy"]:.3f}, Turns: {c["old_rep_turns"]}, Code turns: {c["old_rep_code_turns"]}')
            else:
                print(f'    OLD representative: Attempt {c["old_rep_attempt"]} (entropy={c["old_rep_entropy"]:.3f}, turns={c["old_rep_turns"]}, code_turns={c["old_rep_code_turns"]})')
                print(f'    NEW representative: Attempt {c["new_rep_attempt"]} (entropy={c["new_rep_entropy"]:.3f}, turns={c["new_rep_turns"]}, code_turns={c["new_rep_code_turns"]})')
            print()

            # Character counts
            print(f'    Char counts: OLD={c["old_chars"]} | NEW={c["new_chars"]} | Delta={c["new_chars"] - c["old_chars"]:+d}')
            print(f'    Truncated:   OLD={"YES" if c["old_truncated"] else "no"} | NEW={"YES" if c["new_truncated"] else "no"}')

            # Old loss analysis
            if c['old_loss']['truncated']:
                loss = c['old_loss']
                print(f'    OLD truncation lost {loss["lost_chars"]} chars containing: {", ".join(loss["lost_items"]) if loss["lost_items"] else "unknown content"}')
                print(f'    Key turns NEW saves from truncation: {c["key_turns_saved"]}')

            print()

            # Show full summary text for first 2 problems
            show_full = (full_display_count < 2)
            max_disp = 0 if show_full else 600

            print_summary_text(f'OLD summary (Attempt {c["old_rep_attempt"]})', c['old_summary'], max_disp)
            print()
            print_summary_text(f'NEW summary (Attempt {c["new_rep_attempt"]})', c['new_summary'], max_disp)
            print()

            # Information lost analysis
            if c['old_loss']['truncated'] and c['key_turns_saved'] > 0:
                print(f'    >> KEY CONTENT ANALYSIS: OLD truncated {c["old_loss"]["lost_chars"]} chars from middle.')
                print(f'       NEW smart truncation preserves {c["key_turns_saved"]} key turn(s) that OLD discards.')
                if c['old_loss'].get('lost_items'):
                    print(f'       Lost content types: {", ".join(c["old_loss"]["lost_items"])}')
                print()

        if full_display_count < 2:
            full_display_count += 1

        print()

    # ─────────────────────────────────────────────────────────────────────────
    # Final comparison table
    # ─────────────────────────────────────────────────────────────────────────
    print_divider('=')
    print('COMPARISON TABLE')
    print_divider('-')
    header = f'{"Problem":<10} {"Status":<6} {"Clusters":<8} {"Old Chars":>10} {"New Chars":>10} {"Old Trunc":>10} {"New Trunc":>10} {"Key Saved":>10}'
    print(header)
    print_divider('-')

    total_old = 0
    total_new = 0
    total_old_trunc = 0
    total_new_trunc = 0
    total_key_saved = 0

    for r in results:
        status = 'OK' if r['correct'] else 'FAIL'
        row = f'{r["problem_id"]:<10} {status:<6} {len(r["clusters"]):<8} {r["old_total_chars"]:>10} {r["new_total_chars"]:>10} {r["old_truncated_count"]:>10} {r["new_truncated_count"]:>10} {r["key_turns_saved"]:>10}'
        print(row)
        total_old += r['old_total_chars']
        total_new += r['new_total_chars']
        total_old_trunc += r['old_truncated_count']
        total_new_trunc += r['new_truncated_count']
        total_key_saved += r['key_turns_saved']

    print_divider('-')
    print(f'{"TOTAL":<10} {"":6} {"":8} {total_old:>10} {total_new:>10} {total_old_trunc:>10} {total_new_trunc:>10} {total_key_saved:>10}')
    print()

    # ─────────────────────────────────────────────────────────────────────────
    # Verdict
    # ─────────────────────────────────────────────────────────────────────────
    print_divider('=')
    print('VERDICT')
    print_divider('-')

    if total_new > total_old:
        pct_more = ((total_new - total_old) / total_old * 100) if total_old > 0 else 0
        print(f'NEW builder uses {pct_more:.1f}% more characters ({total_new} vs {total_old}).')
    else:
        pct_less = ((total_old - total_new) / total_old * 100) if total_old > 0 else 0
        print(f'NEW builder uses {pct_less:.1f}% fewer characters ({total_new} vs {total_old}).')

    if total_key_saved > 0:
        print(f'NEW builder preserves {total_key_saved} key turn(s) that OLD discards via blind truncation.')
    else:
        print(f'No key turns were saved (content was short enough to fit without smart truncation).')

    if total_old_trunc > total_new_trunc:
        print(f'OLD truncated {total_old_trunc} clusters vs NEW truncated {total_new_trunc} (NEW fits more within budget).')
    elif total_old_trunc == total_new_trunc:
        print(f'Both builders truncated the same number of clusters ({total_old_trunc}).')
    else:
        print(f'NEW truncated more clusters ({total_new_trunc} vs {total_old_trunc}) despite larger budget.')

    # Check for cases where NEW is worse
    worse_cases = []
    better_from_rep = []
    for r in results:
        for c in r['clusters']:
            # NEW is "worse" if it's truncated when OLD isn't (and OLD had real content)
            if c['new_truncated'] and not c['old_truncated'] and c['old_chars'] > 100:
                worse_cases.append((r['problem_id'], c['answer'], 'NEW truncated but OLD was not'))
            # Flag if same rep but much larger with no benefit (only if OLD had real content)
            if c['same_rep'] and c['new_chars'] > c['old_chars'] * 2.5 and not c['old_truncated'] and c['old_chars'] > 100:
                worse_cases.append((r['problem_id'], c['answer'], f'NEW is {c["new_chars"]/c["old_chars"]:.1f}x larger with same rep'))
            # Track cases where NEW rep is BETTER (OLD had near-empty content)
            if not c['same_rep'] and c['old_chars'] < 50 and c['new_chars'] > 100:
                better_from_rep.append((r['problem_id'], c['answer'],
                    f'OLD had {c["old_chars"]} chars (attempt {c["old_rep_attempt"]}, {c["old_rep_code_turns"]} code turns) '
                    f'vs NEW has {c["new_chars"]} chars (attempt {c["new_rep_attempt"]}, {c["new_rep_code_turns"]} code turns)'))

    if worse_cases:
        print()
        print('Cases where NEW is WORSE:')
        for pid, ans, reason in worse_cases:
            print(f'  Problem {pid}, answer {ans}: {reason}')
    else:
        print()
        print('No cases where NEW builder is worse.')

    if better_from_rep:
        print()
        print('Cases where NEW rep selection RESCUED near-empty summaries:')
        for pid, ans, reason in better_from_rep:
            print(f'  Problem {pid}, answer {ans}: {reason}')

    # Representative selection comparison
    diff_rep_count = 0
    for r in results:
        for c in r['clusters']:
            if not c['same_rep']:
                diff_rep_count += 1
                print(f'\nDifferent representative for {r["problem_id"]} answer={c["answer"]}:')
                print(f'  OLD chose Attempt {c["old_rep_attempt"]} (entropy={c["old_rep_entropy"]:.3f}, {c["old_rep_code_turns"]} code turns)')
                print(f'  NEW chose Attempt {c["new_rep_attempt"]} (entropy={c["new_rep_entropy"]:.3f}, {c["new_rep_code_turns"]} code turns)')

    if diff_rep_count == 0:
        print('\nAll representatives were the same between OLD and NEW (code turn count did not change selection).')
    else:
        total_clusters = sum(len(r['clusters']) for r in results)
        print(f'\n{diff_rep_count}/{total_clusters} clusters chose a different representative.')

    print()
    print_divider('=')


if __name__ == '__main__':
    main()
