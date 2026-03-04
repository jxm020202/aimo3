#!/usr/bin/env python3
"""
Simulate Rerun Mechanism on v32 Diagnostic Log
================================================
Analyzes which problems would trigger a rerun (top_votes < 5) and simulates
what context the retry agents would receive.

For each triggered problem:
  - Per-attempt detail: answer, time, turns, code calls, errors, libraries, vboxed checkpoints, computed values
  - Vote summary and methods-to-answers mapping
  - Cross-reference with problem DB (technique_summary, known answer)
  - Assessment: would rerun + DB context have helped?

Usage:
    python3 log_exploration/simulate_rerun_v32.py [diagnostic.log] [--threshold N]

    Default log: output/v32/diagnostic.log
    Default threshold: 5 (rerun triggers when top_votes < threshold)
"""

import sys
import os
import re
import sqlite3
import argparse
from collections import defaultdict, Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

def parse_vboxed_checkpoints_from_raw(logpath: str) -> dict:
    """Parse vboxed_checkpoints lines from raw log, keyed by (problem_id, attempt_num).

    Returns: { (problem_id, attempt_num): [(turn_num, value), ...] }
    """
    checkpoints = defaultdict(list)
    current_problem_id = None
    current_attempt_num = None

    with open(logpath, 'r', errors='replace') as f:
        for line in f:
            stripped = line.strip()

            # Track current problem
            prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
            if prob_match:
                current_problem_id = prob_match.group(3)
                current_attempt_num = None
                continue

            # Track current attempt
            att_match = re.match(r'\s*---\s*Attempt\s+(\d+)\s*\[', stripped)
            if att_match:
                current_attempt_num = int(att_match.group(1))
                continue

            # Parse vboxed checkpoints
            vboxed_match = re.match(r'\s*vboxed_checkpoints:\s*(.+)', stripped)
            if vboxed_match and current_problem_id and current_attempt_num is not None:
                raw = vboxed_match.group(1)
                for m in re.finditer(r'turn(\d+)=(\d+)', raw):
                    turn_num = int(m.group(1))
                    value = int(m.group(2))
                    checkpoints[(current_problem_id, current_attempt_num)].append((turn_num, value))

    return checkpoints


def parse_source_confidence_from_raw(logpath: str) -> dict:
    """Parse source=X confidence=Y stop=Z lines from raw log.

    Returns: { (problem_id, attempt_num): {'source': str, 'confidence': float, 'stop': str} }
    """
    metadata = {}
    current_problem_id = None
    current_attempt_num = None

    with open(logpath, 'r', errors='replace') as f:
        for line in f:
            stripped = line.strip()

            prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
            if prob_match:
                current_problem_id = prob_match.group(3)
                current_attempt_num = None
                continue

            att_match = re.match(r'\s*---\s*Attempt\s+(\d+)\s*\[', stripped)
            if att_match:
                current_attempt_num = int(att_match.group(1))
                continue

            src_match = re.match(r'\s*source=(\S+)\s+confidence=([\d.]+)\s+stop=(\S+)', stripped)
            if src_match and current_problem_id and current_attempt_num is not None:
                metadata[(current_problem_id, current_attempt_num)] = {
                    'source': src_match.group(1),
                    'confidence': float(src_match.group(2)),
                    'stop': src_match.group(3),
                }

    return metadata


def extract_computed_values(attempt) -> tuple:
    """Extract notable computed values from code output across all turns.

    Returns: (display_values: list[int], all_values: set[int])
      - display_values: up to 30 unique values for display (deduplicated, insertion order)
      - all_values: complete set of ALL unique values found (for presence checks)
    """
    values = []
    all_vals = set()
    for t in attempt.turns:
        if t.output and not t.is_error:
            # Find integer outputs that look like computed answers
            for line in t.output.split('\n'):
                line = line.strip()
                # Skip empty, warnings, very long lines
                if not line or '[WARN]' in line or len(line) > 200:
                    continue
                # Look for standalone numbers or key=value patterns
                nums = re.findall(r'\b(\d{1,6})\b', line)
                for n in nums:
                    val = int(n)
                    if 1 <= val <= 99999:
                        values.append(val)
                        all_vals.add(val)
    # Deduplicate while preserving order for display
    seen = set()
    result = []
    for v in values:
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result[:30], all_vals  # Display cap at 30, all_vals is complete


def classify_library_approach(libraries: list) -> str:
    """Classify the approach based on imported libraries."""
    libs_str = ' '.join(libraries).lower()

    if 'sympy' in libs_str:
        if 'milp' in libs_str or 'scipy.optimize' in libs_str:
            return 'sympy+ILP'
        return 'symbolic (sympy)'
    if 'scipy.optimize' in libs_str or 'milp' in libs_str:
        return 'ILP (scipy)'
    if 'numpy' in libs_str and 'itertools' in libs_str:
        return 'brute_force+numpy'
    if 'itertools' in libs_str:
        return 'brute_force'
    if 'numpy' in libs_str:
        return 'numerical (numpy)'
    if 'fractions' in libs_str or 'Fraction' in libs_str:
        return 'exact_arithmetic'
    if 'math' in libs_str:
        return 'math_stdlib'
    if not libraries:
        return 'pure_reasoning'
    return 'other'


def get_db_info(db_path: str) -> dict:
    """Load problem DB and return { problem_id: row_dict }."""
    if not os.path.exists(db_path):
        return {}

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT problem_id, category, topics, technique_summary, question, answer FROM problems')
    rows = cur.fetchall()
    conn.close()

    result = {}
    for row in rows:
        result[row[0]] = {
            'problem_id': row[0],
            'category': row[1],
            'topics': row[2],
            'technique_summary': row[3],
            'question': row[4],
            'answer': row[5],
        }
    return result


# ── Main Analysis ────────────────────────────────────────────────────────────

def analyze_rerun(logpath: str, db_path: str, threshold: int = 5):
    """Run the full rerun simulation analysis."""

    print(f"Parsing log: {logpath}")
    problems = parse_log(logpath)
    print(f"Total problems parsed: {len(problems)}")

    print(f"Parsing raw vboxed checkpoints...")
    vboxed_data = parse_vboxed_checkpoints_from_raw(logpath)
    print(f"Total attempt-checkpoint entries: {len(vboxed_data)}")

    print(f"Parsing source/confidence metadata...")
    source_data = parse_source_confidence_from_raw(logpath)

    print(f"Loading problem DB: {db_path}")
    db = get_db_info(db_path)
    print(f"DB entries: {len(db)}")

    # Identify rerun triggers
    rerun_problems = []
    for p in problems:
        if not p.votes:
            continue
        top_vote = max(p.votes.values())
        if top_vote < threshold:
            rerun_problems.append(p)

    total_correct = sum(1 for p in problems if p.correct)
    total_wrong = sum(1 for p in problems if not p.correct)

    print(f"\n{'='*80}")
    print(f"  RERUN SIMULATION REPORT — v32")
    print(f"{'='*80}")
    print(f"  Score: {total_correct}/{len(problems)} correct, {total_wrong} wrong")
    print(f"  Rerun threshold: top_votes < {threshold}")
    print(f"  Problems triggering rerun: {len(rerun_problems)}")
    print(f"{'='*80}\n")

    # Track summary stats
    would_help_count = 0
    correct_in_minority = 0
    correct_in_vboxed = 0
    db_has_entry = 0

    for p in rerun_problems:
        top_vote = max(p.votes.values())
        top_answer = max(p.votes.keys(), key=lambda k: p.votes[k])
        correct_in_votes = p.expected in p.votes if p.expected else False

        print(f"{'─'*80}")
        print(f"  PROBLEM {p.problem_id}")
        print(f"  Expected: {p.expected} | Predicted: {p.predicted} | {'CORRECT' if p.correct else 'WRONG'}")
        print(f"  Top vote: {top_vote} (answer={top_answer}) | Total answers: {sum(p.votes.values())} | Vote spread: {len(p.votes)} distinct")
        print(f"  Votes: {dict(sorted(p.votes.items(), key=lambda x: -x[1]))}")
        print(f"  Wall time: {p.wall_time:.1f}s | Budget: {p.budget:.1f}s")
        print(f"{'─'*80}")

        # ── Per-attempt detail ──
        print(f"\n  ATTEMPT DETAILS ({len(p.attempts)} attempts):")
        print(f"  {'#':>3} {'Answer':>8} {'Temp':>5} {'Time':>7} {'Turns':>6} {'Code':>5} {'Err':>4} {'Source':>10} {'Conf':>5} {'Approach'}")
        print(f"  {'─'*90}")

        # Methods -> answers mapping
        method_answers = defaultdict(list)
        all_computed_values = set()
        all_vboxed_values = set()

        for a in p.attempts:
            src_info = source_data.get((p.problem_id, a.attempt_num), {})
            source = src_info.get('source', '?')
            confidence = src_info.get('confidence', '?')
            approach = classify_library_approach(a.libraries)

            n_turns = len(a.turns)
            ans_str = str(a.answer) if a.answer is not None else 'None'
            marker = ''
            if a.answer == p.expected:
                marker = ' << CORRECT'

            print(f"  {a.attempt_num:>3} {ans_str:>8} {a.temperature or 0:>5.1f} {a.time_s:>6.1f}s {n_turns:>6} {a.code_calls:>5} {a.errors:>4} {source:>10} {confidence:>5} {approach}{marker}")

            method_answers[approach].append(a.answer)

            # Extract computed values
            display_vals, full_vals = extract_computed_values(a)
            all_computed_values.update(full_vals)

            # Get vboxed checkpoints for this attempt
            vboxed_key = (p.problem_id, a.attempt_num)
            if vboxed_key in vboxed_data:
                for turn_num, val in vboxed_data[vboxed_key]:
                    all_vboxed_values.add(val)

        # ── Vboxed checkpoints ──
        print(f"\n  VBOXED CHECKPOINTS:")
        has_any_vboxed = False
        for a in p.attempts:
            vboxed_key = (p.problem_id, a.attempt_num)
            if vboxed_key in vboxed_data:
                cps = vboxed_data[vboxed_key]
                unique_vals = sorted(set(v for _, v in cps))
                cp_summary = ', '.join(f"turn{t}={v}" for t, v in cps)
                print(f"    Attempt {a.attempt_num}: [{cp_summary}] -> unique values: {unique_vals}")
                has_any_vboxed = True
        if not has_any_vboxed:
            print(f"    (none)")

        # ── Methods -> Answers mapping ──
        print(f"\n  METHODS -> ANSWERS:")
        for method, answers in sorted(method_answers.items()):
            ans_counts = Counter(a for a in answers if a is not None)
            none_count = sum(1 for a in answers if a is None)
            parts = [f"{ans}x{cnt}" for ans, cnt in ans_counts.most_common()]
            if none_count:
                parts.append(f"Nonex{none_count}")
            print(f"    {method}: {', '.join(parts)}")

        # ── Notable computed values ──
        if all_computed_values:
            # Only show values that appear interesting (near expected, or that match votes)
            interesting = sorted(all_computed_values)
            correct_in_computed = p.expected in all_computed_values
            print(f"\n  COMPUTED VALUES ({len(interesting)} unique ints found in code output):")
            # Show all if few, or show a filtered set
            if len(interesting) <= 30:
                print(f"    {interesting}")
            else:
                # Show those matching votes + expected (only if present) + a sample
                extra = set(p.votes.keys())
                if p.expected and p.expected in all_computed_values:
                    extra.add(p.expected)
                highlighted = sorted(set(interesting[:10]) | extra)
                print(f"    (showing {len(highlighted)} of {len(interesting)} total)")
                print(f"    {highlighted}")
            if correct_in_computed:
                print(f"    >>> Expected answer {p.expected} WAS computed in code output!")

        # ── Correct answer presence analysis ──
        correct_in_minority_vote = p.expected in p.votes if p.expected else False
        correct_in_vboxed_check = p.expected in all_vboxed_values if p.expected else False
        correct_in_computed_check = p.expected in all_computed_values if p.expected else False

        print(f"\n  CORRECT ANSWER ({p.expected}) PRESENCE:")
        print(f"    In minority vote?     {'YES' if correct_in_minority_vote else 'NO'} ", end='')
        if correct_in_minority_vote:
            print(f"({p.votes.get(p.expected, 0)} votes)")
            correct_in_minority += 1
        else:
            print()
        print(f"    In vboxed checkpoint?  {'YES' if correct_in_vboxed_check else 'NO'} ", end='')
        if correct_in_vboxed_check:
            vboxed_count = sum(1 for vals in vboxed_data.values() if any(v == p.expected for _, v in vals))
            print(f"(in {vboxed_count} attempt checkpoints)")
            correct_in_vboxed += 1
        else:
            print()
        print(f"    In computed output?    {'YES' if correct_in_computed_check else 'NO'}")

        # ── DB cross-reference ──
        print(f"\n  PROBLEM DB CROSS-REFERENCE:")
        db_entry = db.get(p.problem_id)
        if db_entry:
            db_has_entry += 1
            print(f"    Category: {db_entry['category']}")
            print(f"    Topics: {db_entry['topics']}")
            technique = db_entry['technique_summary']
            # Word wrap at ~100 chars
            lines = []
            while technique:
                if len(technique) <= 100:
                    lines.append(technique)
                    break
                idx = technique.rfind(' ', 0, 100)
                if idx == -1:
                    idx = 100
                lines.append(technique[:idx])
                technique = technique[idx:].strip()
            print(f"    Technique summary:")
            for line in lines:
                print(f"      {line}")
        else:
            print(f"    NOT in problem DB")

        # ── Assessment ──
        print(f"\n  ASSESSMENT: Would rerun + DB help?")

        # Determine helpfulness
        help_signals = []
        no_help_signals = []

        if correct_in_minority_vote:
            help_signals.append(f"Correct answer {p.expected} already in minority ({p.votes[p.expected]} votes) -- rerun with hint could amplify it")
        if correct_in_vboxed_check:
            help_signals.append(f"Correct answer appeared in vboxed checkpoints -- model found it but didn't commit")
        if correct_in_computed_check:
            help_signals.append(f"Correct answer appeared in computed code output -- extraction or verification failed")
        if db_entry:
            help_signals.append(f"DB has technique summary that could guide the retry approach")

        if not correct_in_minority_vote and not correct_in_vboxed_check and not correct_in_computed_check:
            no_help_signals.append("Correct answer never appeared in ANY attempt (vote, vboxed, or computed output)")
        if top_vote <= 1 and len(p.votes) >= 3:
            no_help_signals.append(f"Complete chaos: {len(p.votes)} distinct answers, max 1 vote each -- model has no signal")
        if not db_entry:
            no_help_signals.append("No DB entry -- rerun would have no technique hints")

        # Compute off-by-one / near-miss
        if p.expected and p.predicted:
            diff = abs(p.expected - p.predicted)
            if diff <= 3:
                help_signals.append(f"Near miss: off by {diff} (predicted {p.predicted} vs expected {p.expected})")

        verdict = "LIKELY HELPFUL" if len(help_signals) > len(no_help_signals) else "UNLIKELY TO HELP"
        if correct_in_minority_vote and db_entry:
            verdict = "VERY LIKELY HELPFUL"
        if not correct_in_minority_vote and not correct_in_vboxed_check and not correct_in_computed_check and not db_entry:
            verdict = "VERY UNLIKELY TO HELP"

        would_help = verdict.startswith("VERY LIKELY") or verdict.startswith("LIKELY")
        if would_help:
            would_help_count += 1

        print(f"    Verdict: {verdict}")
        for s in help_signals:
            print(f"    [+] {s}")
        for s in no_help_signals:
            print(f"    [-] {s}")

        # ── Simulated rerun context ──
        print(f"\n  SIMULATED RERUN CONTEXT (what the retry agent would receive):")
        print(f"    ┌─────────────────────────────────────────────────────────┐")
        print(f"    │ Problem: {p.problem_id} | Budget remaining: ~{max(0, p.budget - p.wall_time):.0f}s         │")
        print(f"    │ Previous: {len(p.attempts)} attempts, {sum(p.votes.values())} answered, {sum(1 for a in p.attempts if a.is_none)} Nones    │")
        print(f"    │ Vote distribution: {dict(sorted(p.votes.items(), key=lambda x: -x[1]))}  │")

        # Compile hints
        all_answers = sorted(set(a.answer for a in p.attempts if a.answer is not None))
        if all_vboxed_values:
            all_answers_and_vboxed = sorted(set(all_answers) | all_vboxed_values)
        else:
            all_answers_and_vboxed = all_answers

        print(f"    │ All answers seen: {all_answers}  │")
        if all_vboxed_values - set(all_answers):
            print(f"    │ Vboxed-only values: {sorted(all_vboxed_values - set(all_answers))}  │")

        if db_entry:
            tech_short = db_entry['technique_summary'][:120]
            print(f"    │ DB technique hint: {tech_short}...  │")

        print(f"    └─────────────────────────────────────────────────────────┘")
        print()

    # ── Summary ──
    print(f"\n{'='*80}")
    print(f"  SUMMARY")
    print(f"{'='*80}")
    print(f"  Problems triggering rerun (top_votes < {threshold}): {len(rerun_problems)}")

    rerun_pids = [p.problem_id for p in rerun_problems]
    print(f"  Problem IDs: {rerun_pids}")

    rerun_wrong = [p for p in rerun_problems if not p.correct]
    rerun_correct = [p for p in rerun_problems if p.correct]
    print(f"  Of these: {len(rerun_wrong)} wrong, {len(rerun_correct)} already correct")

    print(f"\n  Correct answer in minority vote:  {correct_in_minority} / {len(rerun_problems)}")
    print(f"  Correct answer in vboxed:         {correct_in_vboxed} / {len(rerun_problems)}")
    print(f"  Has DB entry with technique:      {db_has_entry} / {len(rerun_problems)}")
    print(f"  Assessment: would help:            {would_help_count} / {len(rerun_problems)}")

    # Potential score improvement
    if rerun_wrong:
        rescuable = [p for p in rerun_wrong if p.expected in p.votes]
        print(f"\n  POTENTIAL SCORE IMPROVEMENT:")
        print(f"    Current score: {total_correct}/{len(problems)}")
        print(f"    Rescuable (correct in minority): {len(rescuable)} problems")
        if rescuable:
            print(f"    Best case (rerun rescues all minority-correct): {total_correct + len(rescuable)}/{len(problems)}")
            for p in rescuable:
                print(f"      {p.problem_id}: {p.votes[p.expected]} votes for correct answer {p.expected}")

    # Also show the borderline problems (top_votes == threshold)
    borderline = [p for p in problems if p.votes and max(p.votes.values()) == threshold and not p.correct]
    if borderline:
        print(f"\n  BORDERLINE (top_votes == {threshold}, would NOT trigger rerun but still wrong):")
        for p in borderline:
            correct_present = p.expected in p.votes
            print(f"    {p.problem_id}: votes={dict(sorted(p.votes.items(), key=lambda x: -x[1]))}"
                  f" | expected={p.expected} in votes: {correct_present}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Simulate rerun mechanism on v32 diagnostic log')
    parser.add_argument('logfile', nargs='?', default='output/v32/diagnostic.log',
                        help='Path to diagnostic.log (default: output/v32/diagnostic.log)')
    parser.add_argument('--threshold', '-t', type=int, default=5,
                        help='Rerun triggers when top_votes < threshold (default: 5)')
    parser.add_argument('--db', type=str, default='data/problem_db/problems.db',
                        help='Path to problems.db (default: data/problem_db/problems.db)')
    args = parser.parse_args()

    analyze_rerun(args.logfile, args.db, args.threshold)


if __name__ == '__main__':
    main()
