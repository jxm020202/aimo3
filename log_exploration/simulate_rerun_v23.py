#!/usr/bin/env python3
"""
Rerun Mechanism Simulation for v23
====================================
Simulates where a rerun mechanism would have triggered on v23 results
and what context the retry agents would have received.

A rerun triggers when top_votes < 5 (low confidence in the voted answer).
For each triggered problem, the script extracts the full rerun context:
  - Per-attempt detail: answer, time, turns, code calls, errors, libraries
  - Vote summary and distribution
  - Methods -> answers mapping (which libraries/approaches led to which answers)
  - Cross-reference with problem DB for technique hints
  - Assessment: would rerun + DB knowledge have helped?

Usage:
    python3 log_exploration/simulate_rerun_v23.py output/v23/diagnostic.log
    python3 log_exploration/simulate_rerun_v23.py output/v23/diagnostic.log --threshold 4
    python3 log_exploration/simulate_rerun_v23.py output/v23/diagnostic.log --problem 86e8e5
"""

import sys
import re
import os
import sqlite3
import argparse
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


# ── Configuration ────────────────────────────────────────────────────────────

RERUN_THRESHOLD = 5  # top_votes < this triggers rerun
DB_PATH = 'data/problem_db/problems.db'


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class AttemptContext:
    attempt_num: int
    answer: Optional[int]
    time_s: float
    turns: int
    code_calls: int
    errors: int
    tokens: int
    temperature: Optional[float]
    libraries: List[str]
    computed_values: List[int]  # numbers extracted from code outputs
    has_boxed: bool  # whether \boxed{} appeared in attempt text
    has_vboxed: bool  # whether \Vboxed{} appeared in attempt text
    error_types: List[str]
    is_none: bool


@dataclass
class RerunContext:
    problem_id: str
    batch_name: str
    problem_text: str
    expected: Optional[int]
    predicted: Optional[int]
    correct: bool
    wall_time: float
    top_votes: int
    votes: Dict[int, int]
    total_attempts: int
    total_answered: int
    attempt_contexts: List[AttemptContext]
    # Derived analysis
    answer_to_methods: Dict[int, List[str]]
    answer_to_attempts: Dict[int, List[int]]
    unique_answers: List[int]
    none_count: int
    correct_in_attempts: bool  # expected answer appears in any attempt
    correct_as_minority: bool  # expected answer appears but was outvoted
    correct_in_computed: bool  # expected answer in code outputs
    # DB cross-reference
    db_match: bool = False
    db_category: str = ""
    db_topics: str = ""
    db_technique: str = ""
    db_answer_hint: str = ""


# ── Helpers ──────────────────────────────────────────────────────────────────

def extract_computed_values(attempt) -> List[int]:
    """Extract integer values from code outputs across all turns."""
    values = set()
    for turn in attempt.turns:
        if turn.output and not turn.is_error:
            # Find standalone integers in output (2+ digits to avoid noise)
            for m in re.finditer(r'\b(\d{2,5})\b', turn.output):
                val = int(m.group(1))
                if 10 <= val <= 99999:  # 5-digit answer range
                    values.add(val)
    return sorted(values)


def extract_error_types(attempt) -> List[str]:
    """Extract error types from attempt turns."""
    errors = []
    for turn in attempt.turns:
        if turn.is_error and turn.output:
            for line in turn.output.split('\n'):
                line = line.strip()
                m = re.match(r'^([A-Z]\w*Error|[A-Z]\w*Exception):', line)
                if m:
                    errors.append(m.group(1))
                    break
    return errors


def has_pattern_in_attempt(attempt, pattern: str) -> bool:
    """Check if a regex pattern appears in any turn text of an attempt."""
    for turn in attempt.turns:
        for text in [turn.reasoning_text, turn.code, turn.output]:
            if text and re.search(pattern, text):
                return True
    return False


def classify_method(attempt) -> str:
    """Classify the computational approach used by an attempt."""
    libs = set(l.strip().lower() for l in attempt.libraries)
    lib_str = ' '.join(attempt.libraries).lower()

    methods = []

    if 'sympy' in lib_str:
        methods.append('sympy')
    if 'numpy' in lib_str or 'np' in lib_str:
        methods.append('numpy')
    if 'scipy' in lib_str:
        methods.append('scipy')
    if 'itertools' in lib_str:
        methods.append('itertools')
    if 'z3' in lib_str:
        methods.append('z3')
    if 'pulp' in lib_str:
        methods.append('pulp')
    if 'networkx' in lib_str:
        methods.append('networkx')
    if 'sage' in lib_str:
        methods.append('sage')
    if 'fractions' in lib_str:
        methods.append('fractions')

    # Check code content for strategy
    for turn in attempt.turns:
        code = turn.code.lower() if turn.code else ''
        if 'brute' in code or 'for ' in code and 'range' in code:
            if 'brute_force' not in methods:
                methods.append('brute_force')
        if 'backtrack' in code:
            methods.append('backtracking')
        if 'dynamic' in code or 'dp[' in code or 'dp =' in code:
            methods.append('dynamic_programming')

    if not methods:
        methods.append('analytical')

    return '+'.join(sorted(set(methods)))


def build_attempt_context(attempt) -> AttemptContext:
    """Build rich context for a single attempt."""
    return AttemptContext(
        attempt_num=attempt.attempt_num,
        answer=attempt.answer,
        time_s=attempt.time_s,
        turns=len(attempt.turns),
        code_calls=attempt.code_calls,
        errors=attempt.errors,
        tokens=attempt.tokens,
        temperature=attempt.temperature,
        libraries=attempt.libraries,
        computed_values=extract_computed_values(attempt),
        has_boxed=has_pattern_in_attempt(attempt, r'\\boxed\s*\{'),
        has_vboxed=has_pattern_in_attempt(attempt, r'\\Vboxed\s*\{'),
        error_types=extract_error_types(attempt),
        is_none=attempt.is_none,
    )


def load_problem_db() -> Dict[str, dict]:
    """Load problem DB entries indexed by problem_id."""
    if not os.path.exists(DB_PATH):
        return {}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT problem_id, category, topics, technique_summary, answer FROM problems')
    db = {}
    for row in cursor.fetchall():
        db[row[0]] = {
            'category': row[1] or '',
            'topics': row[2] or '',
            'technique': row[3] or '',
            'answer': row[4] or '',
        }
    conn.close()
    return db


def build_rerun_context(problem, db: Dict[str, dict]) -> RerunContext:
    """Build the full rerun context for a triggered problem."""
    attempt_contexts = [build_attempt_context(a) for a in problem.attempts]

    # Answer -> methods mapping
    answer_to_methods = defaultdict(list)
    answer_to_attempts = defaultdict(list)
    for ac in attempt_contexts:
        if ac.answer is not None:
            method = classify_method(problem.attempts[ac.attempt_num - 1])
            answer_to_methods[ac.answer].append(method)
            answer_to_attempts[ac.answer].append(ac.attempt_num)

    # Unique answers sorted by vote count
    unique_answers = sorted(problem.votes.keys(), key=lambda a: -problem.votes.get(a, 0))

    none_count = sum(1 for ac in attempt_contexts if ac.is_none)

    # Check if correct answer appears anywhere
    expected = problem.expected
    correct_in_attempts = expected in answer_to_attempts if expected else False
    correct_as_minority = (correct_in_attempts and
                           problem.predicted != expected) if expected else False

    # Check if correct answer appears in computed values
    correct_in_computed = False
    if expected:
        for ac in attempt_contexts:
            if expected in ac.computed_values:
                correct_in_computed = True
                break

    top_votes = max(problem.votes.values()) if problem.votes else 0

    ctx = RerunContext(
        problem_id=problem.problem_id,
        batch_name=problem.batch_name,
        problem_text=problem.problem_text,
        expected=expected,
        predicted=problem.predicted,
        correct=problem.correct,
        wall_time=problem.wall_time,
        top_votes=top_votes,
        votes=dict(sorted(problem.votes.items(), key=lambda x: -x[1])),
        total_attempts=len(problem.attempts),
        total_answered=sum(1 for ac in attempt_contexts if not ac.is_none),
        attempt_contexts=attempt_contexts,
        answer_to_methods=dict(answer_to_methods),
        answer_to_attempts=dict(answer_to_attempts),
        unique_answers=unique_answers,
        none_count=none_count,
        correct_in_attempts=correct_in_attempts,
        correct_as_minority=correct_as_minority,
        correct_in_computed=correct_in_computed,
    )

    # DB cross-reference
    if problem.problem_id in db:
        entry = db[problem.problem_id]
        ctx.db_match = True
        ctx.db_category = entry['category']
        ctx.db_topics = entry['topics']
        ctx.db_technique = entry['technique']
        ctx.db_answer_hint = entry['answer']

    return ctx


# ── Report Printing ──────────────────────────────────────────────────────────

def print_separator(char='=', width=100):
    print(char * width)


def print_attempt_table(ctx: RerunContext):
    """Print compact table of all attempts."""
    print(f"  {'Att':>3} | {'Answer':>7} | {'Temp':>4} | {'Time':>6} | {'Turns':>5} | {'Code':>4} | {'Err':>3} | {'Tokens':>6} | Libraries/Method")
    print(f"  {'-'*3}-+-{'-'*7}-+-{'-'*4}-+-{'-'*6}-+-{'-'*5}-+-{'-'*4}-+-{'-'*3}-+-{'-'*6}-+-{'-'*40}")
    for ac in ctx.attempt_contexts:
        ans_str = str(ac.answer) if ac.answer is not None else 'None'
        temp_str = f'{ac.temperature:.1f}' if ac.temperature is not None else '?'
        libs_short = ', '.join(l.replace('import ', '') for l in ac.libraries[:4])
        if len(ac.libraries) > 4:
            libs_short += f' (+{len(ac.libraries)-4})'
        marker = ''
        if ac.answer == ctx.expected:
            marker = ' << CORRECT'
        elif ac.is_none:
            marker = ' << NONE'
        print(f"  {ac.attempt_num:>3} | {ans_str:>7} | {temp_str:>4} | {ac.time_s:>5.0f}s | {ac.turns:>5} | {ac.code_calls:>4} | {ac.errors:>3} | {ac.tokens:>6} | {libs_short}{marker}")


def print_vote_summary(ctx: RerunContext):
    """Print vote distribution."""
    print(f"\n  Vote Distribution (threshold={RERUN_THRESHOLD}, top_votes={ctx.top_votes} -> RERUN TRIGGERED):")
    for answer, count in ctx.votes.items():
        marker = ''
        if answer == ctx.expected:
            marker = ' << EXPECTED'
        if answer == ctx.predicted:
            marker += ' << PREDICTED'
        bar = '#' * count
        print(f"    {answer:>7}: {count:>2} votes  {bar}{marker}")
    print(f"    Nones:  {ctx.none_count:>2}")
    print(f"    Unique answers: {len(ctx.unique_answers)}")


def print_methods_mapping(ctx: RerunContext):
    """Print which methods/libraries led to which answers."""
    print(f"\n  Methods -> Answers Mapping:")
    for answer in ctx.unique_answers:
        methods = ctx.answer_to_methods.get(answer, [])
        attempts = ctx.answer_to_attempts.get(answer, [])
        method_counts = Counter(methods)
        method_str = ', '.join(f'{m}({c})' if c > 1 else m for m, c in method_counts.most_common())
        marker = ' << CORRECT' if answer == ctx.expected else ''
        print(f"    {answer:>7} (att {','.join(map(str, attempts))}): {method_str}{marker}")


def print_computed_values(ctx: RerunContext):
    """Print interesting computed values from code outputs."""
    all_computed = Counter()
    for ac in ctx.attempt_contexts:
        for v in ac.computed_values:
            all_computed[v] += 1

    if not all_computed:
        print(f"\n  Computed Values from Code: (none extracted)")
        return

    # Show top computed values and whether expected is among them
    print(f"\n  Computed Values from Code (top 15 most frequent):")
    for val, count in all_computed.most_common(15):
        marker = ' << EXPECTED ANSWER' if val == ctx.expected else ''
        in_votes = ' [in votes]' if val in ctx.votes else ''
        print(f"    {val:>7}: seen in {count} attempt(s){in_votes}{marker}")

    if ctx.expected and ctx.correct_in_computed:
        print(f"  ** Expected answer {ctx.expected} WAS computed in code but may have been lost **")


def print_db_context(ctx: RerunContext):
    """Print problem DB cross-reference."""
    print(f"\n  Problem DB Cross-Reference:")
    if not ctx.db_match:
        print(f"    No DB entry for {ctx.problem_id}")
        return

    print(f"    Category: {ctx.db_category}")
    print(f"    Topics: {ctx.db_topics[:200]}")
    print(f"    Technique hint: {ctx.db_technique[:300]}")
    if ctx.db_answer_hint:
        print(f"    Answer context: {ctx.db_answer_hint[:200]}")


def print_assessment(ctx: RerunContext):
    """Print assessment of whether rerun + DB would have helped."""
    print(f"\n  Assessment: Would Rerun + DB Have Helped?")
    print(f"  {'-'*60}")

    factors = []

    # Factor 1: Was the correct answer already found?
    if ctx.correct_in_attempts:
        votes_for_correct = ctx.votes.get(ctx.expected, 0)
        if ctx.correct_as_minority:
            factors.append(f"YES: Correct answer {ctx.expected} was found ({votes_for_correct} votes) but outvoted by {ctx.predicted} ({ctx.top_votes} votes)")
            factors.append("  -> Rerun with hint 'answer {expected} was found by {votes_for_correct} attempts, explore further' could flip it")
        else:
            factors.append(f"ALREADY CORRECT: Answer {ctx.expected} was the winner with {votes_for_correct} votes")
    else:
        if ctx.correct_in_computed:
            factors.append(f"MAYBE: Correct answer {ctx.expected} appeared in code computations but was not submitted")
            factors.append("  -> Rerun with hint about computed value could help")
        else:
            factors.append(f"NO SIGNAL: Correct answer {ctx.expected} never appeared in any attempt or computation")

    # Factor 2: High none rate
    if ctx.none_count > 8:
        factors.append(f"HIGH NONES: {ctx.none_count}/{ctx.total_attempts} attempts returned None - problem may be too hard")
    elif ctx.none_count > 4:
        factors.append(f"MODERATE NONES: {ctx.none_count}/{ctx.total_attempts} attempts returned None")

    # Factor 3: DB has useful info
    if ctx.db_match:
        if ctx.db_technique:
            factors.append(f"DB HAS TECHNIQUE: '{ctx.db_technique[:100]}...'")
            factors.append("  -> Feeding technique hint to rerun agent could dramatically help")
        else:
            factors.append("DB ENTRY EXISTS but technique_summary is empty")
    else:
        factors.append("NO DB ENTRY: No prior knowledge to guide rerun")

    # Factor 4: Vote dispersion
    if len(ctx.unique_answers) > 8:
        factors.append(f"HIGH DISPERSION: {len(ctx.unique_answers)} unique answers - model is confused, rerun with guidance needed")
    elif len(ctx.unique_answers) > 4:
        factors.append(f"MODERATE DISPERSION: {len(ctx.unique_answers)} unique answers")

    # Factor 5: Error rate
    total_errors = sum(ac.errors for ac in ctx.attempt_contexts)
    if total_errors > 20:
        factors.append(f"HIGH ERROR RATE: {total_errors} total errors across attempts")

    # Overall verdict
    if ctx.correct and ctx.correct_in_attempts:
        verdict = "UNNECESSARY - already correct (but fragile with only {top} votes)".format(top=ctx.top_votes)
    elif ctx.correct_as_minority and ctx.db_match:
        verdict = "HIGH POTENTIAL - correct answer exists as minority + DB technique available"
    elif ctx.correct_as_minority:
        verdict = "MODERATE POTENTIAL - correct answer exists as minority, no DB guidance"
    elif ctx.correct_in_computed and ctx.db_match:
        verdict = "MODERATE POTENTIAL - correct value computed + DB available"
    elif ctx.db_match and ctx.db_technique:
        verdict = "POSSIBLE - DB technique could guide fresh approach"
    elif ctx.none_count > 10:
        verdict = "LOW POTENTIAL - mostly Nones, problem likely too hard for model"
    else:
        verdict = "LOW POTENTIAL - no correct signal found, would need fundamentally different approach"

    for f in factors:
        print(f"    {f}")
    print(f"\n    VERDICT: {verdict}")


def print_simulated_rerun_prompt(ctx: RerunContext):
    """Print what the rerun agent's context prompt would look like."""
    print(f"\n  Simulated Rerun Agent Context:")
    print(f"  {'-'*60}")

    # Build the context that would be passed to Wave 2
    lines = []
    lines.append(f"Previous 16 attempts produced {ctx.total_answered} answers and {ctx.none_count} Nones.")
    lines.append(f"Vote distribution: {dict(list(ctx.votes.items())[:5])}")
    lines.append(f"Top voted answer: {ctx.predicted} with {ctx.top_votes} votes (LOW CONFIDENCE)")

    if len(ctx.unique_answers) > 1:
        lines.append(f"Alternative answers found: {ctx.unique_answers[:8]}")

    # Methods that produced each top answer
    for answer in list(ctx.votes.keys())[:3]:
        methods = ctx.answer_to_methods.get(answer, [])
        if methods:
            lines.append(f"  Answer {answer}: produced by {Counter(methods).most_common(3)}")

    if ctx.db_match and ctx.db_technique:
        lines.append(f"\nDB Technique Hint: {ctx.db_technique[:200]}")

    # Error summary
    all_error_types = Counter()
    for ac in ctx.attempt_contexts:
        for et in ac.error_types:
            all_error_types[et] += 1
    if all_error_types:
        lines.append(f"\nCommon errors: {dict(all_error_types.most_common(5))}")

    for line in lines:
        print(f"    {line}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    global RERUN_THRESHOLD

    parser = argparse.ArgumentParser(description='Simulate rerun mechanism on v23 diagnostic log')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--threshold', type=int, default=RERUN_THRESHOLD,
                        help=f'Rerun trigger threshold (top_votes < N, default={RERUN_THRESHOLD})')
    parser.add_argument('--problem', '-p', help='Filter to specific problem ID')
    args = parser.parse_args()

    RERUN_THRESHOLD = args.threshold

    # Parse log
    print(f"Parsing {args.logfile}...")
    problems = parse_log(args.logfile)
    print(f"Found {len(problems)} problem instances ({len(set(p.problem_id for p in problems))} unique IDs)")

    # Load DB
    db = load_problem_db()
    print(f"Loaded {len(db)} entries from problem DB")

    # Identify rerun candidates
    triggered = []
    not_triggered = []
    for p in problems:
        if args.problem and p.problem_id != args.problem:
            continue
        top_votes = max(p.votes.values()) if p.votes else 0
        if top_votes < RERUN_THRESHOLD:
            ctx = build_rerun_context(p, db)
            triggered.append(ctx)
        else:
            not_triggered.append(p)

    print_separator()
    print(f"  RERUN SIMULATION REPORT")
    print(f"  Threshold: top_votes < {RERUN_THRESHOLD}")
    print(f"  Problems analyzed: {len(problems)}")
    print(f"  Would trigger rerun: {len(triggered)}")
    print(f"  Would NOT trigger: {len(not_triggered)}")
    print_separator()

    # Summary table
    print(f"\n{'='*100}")
    print(f"  SUMMARY: All Triggered Problems")
    print(f"{'='*100}")
    print(f"  {'PID':>8} | {'Batch':>25} | {'Top':>3} | {'Pred':>7} | {'Exp':>7} | {'OK':>3} | {'Ans':>3} | {'None':>4} | {'CorrectInAtt':>12} | {'DB':>3}")
    print(f"  {'-'*8}-+-{'-'*25}-+-{'-'*3}-+-{'-'*7}-+-{'-'*7}-+-{'-'*3}-+-{'-'*3}-+-{'-'*4}-+-{'-'*12}-+-{'-'*3}")
    for ctx in triggered:
        ok = 'YES' if ctx.correct else 'NO'
        cia = 'MINORITY' if ctx.correct_as_minority else ('YES' if ctx.correct_in_attempts else 'NO')
        db_flag = 'YES' if ctx.db_match else 'NO'
        batch_short = ctx.batch_name[:25] if ctx.batch_name else '?'
        print(f"  {ctx.problem_id:>8} | {batch_short:>25} | {ctx.top_votes:>3} | {ctx.predicted or 0:>7} | {ctx.expected or 0:>7} | {ok:>3} | {len(ctx.unique_answers):>3} | {ctx.none_count:>4} | {cia:>12} | {db_flag:>3}")

    # Category breakdown
    correct_triggered = sum(1 for ctx in triggered if ctx.correct)
    wrong_triggered = len(triggered) - correct_triggered
    minority_count = sum(1 for ctx in triggered if ctx.correct_as_minority)
    computed_count = sum(1 for ctx in triggered if ctx.correct_in_computed and not ctx.correct_in_attempts)
    db_count = sum(1 for ctx in triggered if ctx.db_match)

    print(f"\n  Category Breakdown:")
    print(f"    Already correct (fragile):    {correct_triggered}")
    print(f"    Wrong - correct as minority:  {minority_count}")
    print(f"    Wrong - correct in code only: {computed_count}")
    print(f"    Wrong - no correct signal:    {wrong_triggered - minority_count - computed_count}")
    print(f"    Have DB entry:                {db_count}/{len(triggered)}")

    # Detailed reports
    for i, ctx in enumerate(triggered):
        print(f"\n{'='*100}")
        print(f"  [{i+1}/{len(triggered)}] Problem {ctx.problem_id} — {ctx.batch_name}")
        print(f"  Status: {'CORRECT' if ctx.correct else 'WRONG'} | Predicted: {ctx.predicted} | Expected: {ctx.expected}")
        print(f"  Wall time: {ctx.wall_time:.0f}s ({ctx.wall_time/60:.1f} min)")
        print(f"{'='*100}")

        print(f"\n  Problem text (truncated): {ctx.problem_text[:200]}...")

        print(f"\n  Attempt Details:")
        print_attempt_table(ctx)
        print_vote_summary(ctx)
        print_methods_mapping(ctx)
        print_computed_values(ctx)
        print_db_context(ctx)
        print_assessment(ctx)
        print_simulated_rerun_prompt(ctx)

    # Final summary
    print(f"\n{'='*100}")
    print(f"  FINAL ANALYSIS")
    print(f"{'='*100}")

    high_potential = sum(1 for ctx in triggered if ctx.correct_as_minority and ctx.db_match)
    moderate_potential = sum(1 for ctx in triggered
                            if (ctx.correct_as_minority and not ctx.db_match) or
                            (ctx.correct_in_computed and ctx.db_match))
    already_ok = sum(1 for ctx in triggered if ctx.correct)
    low_potential = len(triggered) - high_potential - moderate_potential - already_ok

    print(f"\n  Rerun would trigger on: {len(triggered)}/{len(problems)} problem instances")
    print(f"\n  Potential Impact Breakdown:")
    print(f"    HIGH POTENTIAL (minority + DB):     {high_potential} problems")
    print(f"    MODERATE POTENTIAL (minority or DB): {moderate_potential} problems")
    print(f"    ALREADY CORRECT (fragile):          {already_ok} problems")
    print(f"    LOW POTENTIAL (no signal):           {low_potential} problems")

    if high_potential + moderate_potential > 0:
        print(f"\n  Best case scenario: rerun could flip {high_potential + moderate_potential} wrong -> correct")
        print(f"  This would improve score from {sum(1 for p in problems if p.correct)}/{len(problems)} to "
              f"{sum(1 for p in problems if p.correct) + high_potential + moderate_potential}/{len(problems)}")

    # List the most promising rerun targets
    promising = [ctx for ctx in triggered if ctx.correct_as_minority or
                 (ctx.correct_in_computed and ctx.db_match)]
    if promising:
        print(f"\n  Most Promising Rerun Targets:")
        for ctx in promising:
            reason = []
            if ctx.correct_as_minority:
                votes_correct = ctx.votes.get(ctx.expected, 0)
                reason.append(f"correct answer {ctx.expected} got {votes_correct} votes (minority)")
            if ctx.correct_in_computed:
                reason.append(f"correct answer computed in code")
            if ctx.db_match:
                reason.append(f"DB has technique hint")
            print(f"    {ctx.problem_id}: {'; '.join(reason)}")


if __name__ == '__main__':
    main()
