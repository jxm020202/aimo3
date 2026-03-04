#!/usr/bin/env python3
"""
Intermediate Answer Analysis
=============================
Finds cases where the correct answer was computed during an attempt but lost
before final extraction. Three main loss channels:

  1. Over-verification: Model wrote \\boxed{correct} at some point but then
     wrote a different \\boxed{wrong} later (last-boxed-wins extraction).
  2. Computed-but-not-boxed: Correct answer appeared as a clear standalone
     result in code output, but the attempt ended as None or a different answer.
  3. Vote dilution on correct problems: Even for problems we got right, some
     attempts that *could* have voted correct ended up voting wrong or None.

Also tracks:
  4. Timing of first correct computation (how early did the model "know"?).

Usage:
    python3 log_exploration/intermediate_answer_analysis.py output/v31/diagnostic.log
"""

import sys
import re
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

BOXED_RE = re.compile(r'\\boxed\s*\{\s*(\d[\d,]*)\s*\}')
VBOXED_RE = re.compile(r'\\Vboxed\s*\{\s*(\d[\d,]*)\s*\}')
NO_OUTPUT = '[WARN] No output. Use print() to see results.'


def parse_int_safe(s: str) -> Optional[int]:
    """Parse integer from string, stripping commas. Returns None on failure."""
    try:
        v = int(s.replace(',', ''))
        if 0 <= v <= 99999:
            return v
        v_mod = v % 100000
        if 0 <= v_mod <= 99999:
            return v_mod
    except (ValueError, OverflowError):
        pass
    return None


def extract_all_boxed(text: str) -> List[Tuple[str, int]]:
    """Extract all \\boxed{N} and \\Vboxed{N} from text.
    Returns list of (type, value) where type is 'boxed' or 'vboxed'.
    """
    results = []
    for m in BOXED_RE.finditer(text):
        v = parse_int_safe(m.group(1))
        if v is not None:
            results.append(('boxed', v))
    for m in VBOXED_RE.finditer(text):
        v = parse_int_safe(m.group(1))
        if v is not None:
            results.append(('vboxed', v))
    return results


def is_standalone_answer(output: str, expected: int) -> bool:
    """Check if the expected answer appears as a clear standalone result
    in code output. Must be rigorous to avoid false positives.

    Positive patterns (the number IS the answer):
      - Output is just the number (possibly with whitespace)
      - "answer: 123" / "answer = 123" / "Answer is 123"
      - "result: 123" / "Result = 123"
      - "minimum: 123" / "maximum: 123"
      - "print(result) => 123" (number on its own line)

    Negative patterns (the number is NOT the answer):
      - Number appears inside a larger number (e.g. "8687" in "13080...8687...")
      - Number appears in a list/array: "[1, 22, 3]"
      - Number appears in solver output: "HiGHS 1.8.0 (git hash: 222cce7)"
      - Number appears in a fraction/large integer context
    """
    output = output.strip()
    if not output or output == NO_OUTPUT:
        return False

    exp_str = str(expected)

    # Pattern 1: Output IS the number (most reliable)
    # Allow surrounding whitespace and optional trailing punctuation
    if re.match(r'^\s*' + re.escape(exp_str) + r'\s*[.!]?\s*$', output):
        return True

    # Pattern 2: Number on its own line (very common for print(result))
    for line in output.split('\n'):
        line = line.strip()
        if re.match(r'^' + re.escape(exp_str) + r'$', line):
            return True

    # Pattern 3: Labeled answer patterns
    labeled_patterns = [
        r'(?:the\s+)?answer\s*(?:is|=|:)\s*' + re.escape(exp_str) + r'\b',
        r'(?:the\s+)?result\s*(?:is|=|:)\s*' + re.escape(exp_str) + r'\b',
        r'(?:minimum|maximum|min|max)\s*(?:is|=|:)\s*' + re.escape(exp_str) + r'\b',
        r'(?:total|count|sum|value|output)\s*(?:is|=|:)\s*' + re.escape(exp_str) + r'\b',
        r'(?:final answer|final result)\s*(?:is|=|:)\s*' + re.escape(exp_str) + r'\b',
    ]
    for pat in labeled_patterns:
        if re.search(pat, output, re.IGNORECASE):
            return True

    # Pattern 4: Number as the last line of multi-line output (common print pattern)
    lines = [l.strip() for l in output.strip().split('\n') if l.strip()]
    if len(lines) >= 1:
        last = lines[-1]
        if re.match(r'^' + re.escape(exp_str) + r'$', last):
            return True

    # Pattern 5: "= 123" at end of line (common computation output)
    for line in output.split('\n'):
        if re.search(r'=\s*' + re.escape(exp_str) + r'\s*$', line.strip()):
            return True

    return False


def is_false_positive_output(output: str, expected: int) -> bool:
    """Additional check: even if the number appears, is it clearly NOT the answer?"""
    exp_str = str(expected)

    # If the number only appears as part of larger numbers, it's false positive
    # Find all occurrences and check if any are word-bounded
    word_bounded = re.findall(r'(?<!\d)' + re.escape(exp_str) + r'(?!\d)', output)
    if not word_bounded:
        return True

    return False


@dataclass
class OverVerification:
    """Case where model wrote boxed{correct} then boxed{wrong}."""
    problem_id: str
    expected: int
    attempt_num: int
    attempt_final_answer: Optional[int]
    correct_boxed_turn: int
    correct_boxed_type: str  # 'boxed' or 'vboxed'
    final_boxed_turn: int
    final_boxed_value: int
    final_boxed_type: str
    total_turns: int


@dataclass
class ComputedNotBoxed:
    """Case where correct answer in code output but not captured."""
    problem_id: str
    expected: int
    attempt_num: int
    attempt_final_answer: Optional[int]
    output_turn: int
    output_text: str  # truncated
    total_turns: int
    turns_remaining: int


@dataclass
class VoteDilution:
    """Attempt on a correct problem that didn't vote correctly."""
    problem_id: str
    expected: int
    attempt_num: int
    attempt_answer: Optional[int]
    had_correct_intermediate: bool
    loss_type: str  # 'none', 'wrong_answer'


@dataclass
class ProblemSummary:
    """Summary for one problem."""
    problem_id: str
    expected: int
    predicted: int
    correct: bool
    total_attempts: int
    over_verifications: List[OverVerification] = field(default_factory=list)
    computed_not_boxed: List[ComputedNotBoxed] = field(default_factory=list)
    diluted_votes: List[VoteDilution] = field(default_factory=list)
    attempts_with_correct_answer: int = 0
    first_correct_turn: Optional[int] = None
    first_correct_attempt: Optional[int] = None


# ── Main Analysis ────────────────────────────────────────────────────────────

def analyze(logfile: str):
    problems = parse_log(logfile)

    print(f'{"=" * 90}')
    print(f'  INTERMEDIATE ANSWER ANALYSIS — {logfile}')
    print(f'  {len(problems)} problems, {sum(1 for p in problems if p.correct)}/{len(problems)} correct')
    print(f'{"=" * 90}')
    print()

    summaries = []

    for p in problems:
        expected = p.expected
        if expected is None:
            continue

        summary = ProblemSummary(
            problem_id=p.problem_id,
            expected=expected,
            predicted=p.predicted,
            correct=p.correct,
            total_attempts=len(p.attempts),
        )

        for a in p.attempts:
            # ── Collect all boxed values per turn ──
            turn_boxed = []  # list of (turn_num, type, value)
            for t in a.turns:
                for fld in [t.reasoning_text, t.code]:
                    for btype, bval in extract_all_boxed(fld):
                        turn_boxed.append((t.turn_num, btype, bval))

            # ── Analysis 1: Over-verification ──
            # Did the model write boxed{correct} and then boxed{wrong}?
            correct_boxed_entries = [(tn, bt, bv) for tn, bt, bv in turn_boxed if bv == expected]
            wrong_boxed_after = []
            if correct_boxed_entries:
                first_correct = correct_boxed_entries[0]
                # Find any boxed AFTER the first correct that has a different value
                for tn, bt, bv in turn_boxed:
                    if tn > first_correct[0] and bv != expected:
                        wrong_boxed_after.append((tn, bt, bv))
                    elif tn == first_correct[0] and bv != expected:
                        # Same turn but different value after correct
                        # Check position in text: we can't easily do this, skip same-turn
                        pass

                # Also: correct Vboxed followed by wrong boxed is over-verification
                # (since boxed wins over Vboxed)
                if correct_boxed_entries and not wrong_boxed_after:
                    # Check if first correct is vboxed but final answer uses boxed with wrong val
                    for ce in correct_boxed_entries:
                        if ce[1] == 'vboxed':
                            # Any boxed (not vboxed) with wrong value?
                            for tn, bt, bv in turn_boxed:
                                if bt == 'boxed' and bv != expected:
                                    wrong_boxed_after.append((tn, bt, bv))

                if wrong_boxed_after and a.answer != expected:
                    # The attempt ended wrong AND had correct intermediate
                    last_wrong = wrong_boxed_after[-1]
                    ov = OverVerification(
                        problem_id=p.problem_id,
                        expected=expected,
                        attempt_num=a.attempt_num,
                        attempt_final_answer=a.answer,
                        correct_boxed_turn=first_correct[0],
                        correct_boxed_type=first_correct[1],
                        final_boxed_turn=last_wrong[0],
                        final_boxed_value=last_wrong[2],
                        final_boxed_type=last_wrong[1],
                        total_turns=len(a.turns),
                    )
                    summary.over_verifications.append(ov)

            # ── Analysis 2: Computed-but-not-boxed ──
            # Correct answer in code output but attempt ended wrong or None
            if a.answer != expected:
                for t in a.turns:
                    out = t.output.strip()
                    if not out or out == NO_OUTPUT:
                        continue
                    if is_standalone_answer(out, expected) and not is_false_positive_output(out, expected):
                        cnb = ComputedNotBoxed(
                            problem_id=p.problem_id,
                            expected=expected,
                            attempt_num=a.attempt_num,
                            attempt_final_answer=a.answer,
                            output_turn=t.turn_num,
                            output_text=out[:120],
                            total_turns=len(a.turns),
                            turns_remaining=len(a.turns) - t.turn_num,
                        )
                        summary.computed_not_boxed.append(cnb)
                        break  # Only count first occurrence per attempt

            # ── Track correct attempts ──
            if a.answer == expected:
                summary.attempts_with_correct_answer += 1

            # ── Analysis 3: Vote dilution (for ALL problems) ──
            if a.answer != expected:
                had_correct_intermediate = (
                    any(bv == expected for _, _, bv in turn_boxed) or
                    any(
                        is_standalone_answer(t.output.strip(), expected) and
                        not is_false_positive_output(t.output.strip(), expected)
                        for t in a.turns if t.output.strip() and t.output.strip() != NO_OUTPUT
                    )
                )
                vd = VoteDilution(
                    problem_id=p.problem_id,
                    expected=expected,
                    attempt_num=a.attempt_num,
                    attempt_answer=a.answer,
                    had_correct_intermediate=had_correct_intermediate,
                    loss_type='none' if a.answer is None else 'wrong_answer',
                )
                summary.diluted_votes.append(vd)

            # ── Analysis 4: Timing of first correct computation ──
            for t in a.turns:
                # Check boxed in reasoning
                for _, bv in extract_all_boxed(t.reasoning_text):
                    if bv == expected:
                        if summary.first_correct_turn is None or t.turn_num < summary.first_correct_turn:
                            summary.first_correct_turn = t.turn_num
                            summary.first_correct_attempt = a.attempt_num
                        break
                # Check code output
                out = t.output.strip()
                if out and out != NO_OUTPUT and is_standalone_answer(out, expected) and not is_false_positive_output(out, expected):
                    if summary.first_correct_turn is None or t.turn_num < summary.first_correct_turn:
                        summary.first_correct_turn = t.turn_num
                        summary.first_correct_attempt = a.attempt_num

        summaries.append(summary)

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 1: OVER-VERIFICATION
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  1. OVER-VERIFICATION: Correct \\boxed then wrong \\boxed')
    print('=' * 90)
    print()

    all_ov = []
    for s in summaries:
        all_ov.extend(s.over_verifications)

    if all_ov:
        # Group by problem
        ov_by_prob = defaultdict(list)
        for ov in all_ov:
            ov_by_prob[ov.problem_id].append(ov)

        print(f'Total over-verification cases: {len(all_ov)} across {len(ov_by_prob)} problems')
        print()

        for pid in sorted(ov_by_prob.keys()):
            ovs = ov_by_prob[pid]
            s = next(s for s in summaries if s.problem_id == pid)
            status = 'CORRECT' if s.correct else 'WRONG'
            print(f'  Problem {pid} [{status}] (pred={s.predicted}, exp={s.expected})')
            for ov in sorted(ovs, key=lambda x: x.attempt_num):
                print(f'    Att {ov.attempt_num:2d}: {ov.correct_boxed_type}({ov.expected}) at turn {ov.correct_boxed_turn}'
                      f' -> {ov.final_boxed_type}({ov.final_boxed_value}) at turn {ov.final_boxed_turn}'
                      f' | final_answer={ov.attempt_final_answer} | turns={ov.total_turns}')
            print()
    else:
        print('  No over-verification cases found.')
        print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 2: COMPUTED-BUT-NOT-BOXED
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  2. COMPUTED-BUT-NOT-BOXED: Correct answer in code output, lost')
    print('=' * 90)
    print()

    all_cnb = []
    for s in summaries:
        all_cnb.extend(s.computed_not_boxed)

    if all_cnb:
        cnb_by_prob = defaultdict(list)
        for cnb in all_cnb:
            cnb_by_prob[cnb.problem_id].append(cnb)

        print(f'Total computed-but-not-boxed cases: {len(all_cnb)} across {len(cnb_by_prob)} problems')
        print()

        for pid in sorted(cnb_by_prob.keys()):
            cnbs = cnb_by_prob[pid]
            s = next(s for s in summaries if s.problem_id == pid)
            status = 'CORRECT' if s.correct else 'WRONG'
            print(f'  Problem {pid} [{status}] (pred={s.predicted}, exp={s.expected})')
            for cnb in sorted(cnbs, key=lambda x: x.attempt_num):
                final_str = str(cnb.attempt_final_answer) if cnb.attempt_final_answer is not None else 'None'
                print(f'    Att {cnb.attempt_num:2d}: correct output at turn {cnb.output_turn}/{cnb.total_turns}'
                      f' ({cnb.turns_remaining} turns remaining) | final={final_str}')
                # Show truncated output
                out_lines = cnb.output_text.split('\n')
                for ol in out_lines[:2]:
                    print(f'      output: {ol[:100]}')
            print()
    else:
        print('  No computed-but-not-boxed cases found.')
        print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 3: VOTE DILUTION ON CORRECT PROBLEMS
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  3. VOTE DILUTION: Wasted signal on ALL problems')
    print('=' * 90)
    print()

    # Separate correct vs wrong problems
    correct_probs = [s for s in summaries if s.correct]
    wrong_probs = [s for s in summaries if not s.correct]

    print('  A. CORRECT PROBLEMS — wasted votes')
    print('  ' + '-' * 70)
    total_wasted_correct = 0
    total_wasted_with_intermediate_correct = 0
    wasted_none_correct = 0
    wasted_wrong_correct = 0

    for s in correct_probs:
        if not s.diluted_votes:
            continue
        n_diluted = len(s.diluted_votes)
        n_with_intermediate = sum(1 for vd in s.diluted_votes if vd.had_correct_intermediate)
        n_none = sum(1 for vd in s.diluted_votes if vd.loss_type == 'none')
        n_wrong = sum(1 for vd in s.diluted_votes if vd.loss_type == 'wrong_answer')
        total_wasted_correct += n_diluted
        total_wasted_with_intermediate_correct += n_with_intermediate
        wasted_none_correct += n_none
        wasted_wrong_correct += n_wrong

        correct_votes = s.attempts_with_correct_answer
        print(f'    {s.problem_id}: {correct_votes}/{s.total_attempts} correct votes '
              f'| {n_diluted} wasted ({n_none} None, {n_wrong} wrong) '
              f'| {n_with_intermediate} had correct intermediate')

    print()
    print(f'  Total wasted votes on correct problems: {total_wasted_correct}')
    print(f'    Of which had correct intermediate: {total_wasted_with_intermediate_correct}')
    print(f'    None: {wasted_none_correct}, Wrong answer: {wasted_wrong_correct}')
    print()

    print('  B. WRONG PROBLEMS — could more correct votes have changed outcome?')
    print('  ' + '-' * 70)
    total_lost_votes_wrong = 0
    total_lost_with_intermediate_wrong = 0

    problems_with_any_correct = []
    for s in wrong_probs:
        n_correct = s.attempts_with_correct_answer
        n_diluted = len(s.diluted_votes)
        n_with_intermediate = sum(1 for vd in s.diluted_votes if vd.had_correct_intermediate)
        total_lost_votes_wrong += n_diluted
        total_lost_with_intermediate_wrong += n_with_intermediate

        if n_correct > 0 or n_with_intermediate > 0:
            problems_with_any_correct.append(s)
            none_votes = sum(1 for vd in s.diluted_votes if vd.loss_type == 'none')
            wrong_votes = sum(1 for vd in s.diluted_votes if vd.loss_type == 'wrong_answer')
            print(f'    {s.problem_id}: {n_correct}/{s.total_attempts} correct votes '
                  f'| {n_diluted} wrong/none ({none_votes} None, {wrong_votes} wrong) '
                  f'| {n_with_intermediate} had correct intermediate')
            # Show what the wrong votes were
            vote_dist = defaultdict(int)
            for vd in s.diluted_votes:
                vote_dist[vd.attempt_answer] += 1
            vote_dist[s.expected] = n_correct  # add correct
            sorted_votes = sorted(vote_dist.items(), key=lambda x: -x[1])
            vote_str = ', '.join(f'{v}:{c}' for v, c in sorted_votes[:5])
            print(f'      Vote distribution: {vote_str}')

    print()
    print(f'  Total non-correct votes on wrong problems: {total_lost_votes_wrong}')
    print(f'    Of which had correct intermediate: {total_lost_with_intermediate_wrong}')
    print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 4: TIMING OF CORRECT COMPUTATION
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  4. TIMING: When correct answer first appears')
    print('=' * 90)
    print()

    print(f'  {"Problem":<10} {"Status":>8} {"1st Turn":>8} {"1st Att":>7} {"Att w/correct":>13} {"OV cases":>8} {"CNB cases":>9}')
    print(f'  {"─" * 10} {"─" * 8} {"─" * 8} {"─" * 7} {"─" * 13} {"─" * 8} {"─" * 9}')

    for s in summaries:
        status = 'CORR' if s.correct else 'WRONG'
        ft = str(s.first_correct_turn) if s.first_correct_turn is not None else '-'
        fa = str(s.first_correct_attempt) if s.first_correct_attempt is not None else '-'
        print(f'  {s.problem_id:<10} {status:>8} {ft:>8} {fa:>7} '
              f'{s.attempts_with_correct_answer:>13} {len(s.over_verifications):>8} {len(s.computed_not_boxed):>9}')

    print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 5: WRONG PROBLEM CLASSIFICATION
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  5. WRONG PROBLEM CLASSIFICATION')
    print('=' * 90)
    print()

    recoverable = []
    for s in summaries:
        if s.correct:
            continue
        n_ov = len(s.over_verifications)
        n_cnb = len(s.computed_not_boxed)
        n_correct = s.attempts_with_correct_answer
        if n_ov > 0 or n_cnb > 0 or n_correct > 0:
            recoverable.append(s)

    # Classify each wrong problem
    categories = {
        'outvoted': [],      # Correct answer found by some attempts, but outvoted
        'computed_lost': [],  # Correct computed in output but not extracted
        'no_signal': [],      # No attempt even got close to the correct answer
    }

    for s in summaries:
        if s.correct:
            continue
        n_ov = len(s.over_verifications)
        n_cnb = len(s.computed_not_boxed)
        n_correct = s.attempts_with_correct_answer

        if n_correct > 0:
            categories['outvoted'].append(s)
        elif n_cnb > 0 or n_ov > 0:
            categories['computed_lost'].append(s)
        else:
            categories['no_signal'].append(s)

    total_wrong = sum(len(v) for v in categories.values())
    print(f'  Wrong problems breakdown ({total_wrong} total):')
    print(f'    Outvoted (correct found but lost vote):     {len(categories["outvoted"])}')
    print(f'    Computed-but-lost (in output, not boxed):   {len(categories["computed_lost"])}')
    print(f'    No signal (never computed correct):         {len(categories["no_signal"])}')
    print()

    # Detail each category
    if categories['outvoted']:
        print('  OUTVOTED problems (correct answer was boxed by some attempts):')
        for s in categories['outvoted']:
            # Get full vote distribution from the parsed problem
            prob_obj = next(p for p in problems if p.problem_id == s.problem_id and p.expected == s.expected)
            vote_dist = defaultdict(int)
            for a in prob_obj.attempts:
                vote_dist[a.answer] += 1
            sorted_v = sorted(vote_dist.items(), key=lambda x: -(x[1] if x[0] is not None else 0))
            vote_str = ', '.join(f'{k}:{v}' for k, v in sorted_v[:5])
            margin = vote_dist.get(s.predicted, 0) - s.attempts_with_correct_answer
            print(f'    {s.problem_id}: {s.attempts_with_correct_answer} correct vs {vote_dist.get(s.predicted, 0)} for {s.predicted} '
                  f'(margin={margin}) | Votes: {vote_str}')
        print()

    if categories['computed_lost']:
        print('  COMPUTED-BUT-LOST problems (correct in code output, never properly boxed):')
        for s in categories['computed_lost']:
            n_cnb = len(s.computed_not_boxed)
            # Show the turns where it appeared
            turn_details = []
            for cnb in s.computed_not_boxed:
                turn_details.append(f'att{cnb.attempt_num}:T{cnb.output_turn}/{cnb.total_turns}')
            print(f'    {s.problem_id}: {n_cnb} attempts had correct in output | {", ".join(turn_details)}')
        print()

    if categories['no_signal']:
        print('  NO-SIGNAL problems (model never computed the correct answer):')
        for s in categories['no_signal']:
            print(f'    {s.problem_id}: pred={s.predicted}, exp={s.expected} '
                  f'({"off by " + str(abs(s.predicted - s.expected)) if s.predicted and s.expected else "N/A"})')
        print()

    # Deep dive for recoverable problems
    if recoverable:
        print(f'  DEEP DIVE — {len(recoverable)} wrong problems with recoverable signal:')
        print()
        for s in recoverable:
            n_ov = len(s.over_verifications)
            n_cnb = len(s.computed_not_boxed)
            total_recoverable = n_ov + n_cnb + s.attempts_with_correct_answer
            print(f'  Problem {s.problem_id} (pred={s.predicted}, exp={s.expected})')
            print(f'    Correct-voting attempts: {s.attempts_with_correct_answer}/{s.total_attempts}')
            print(f'    Over-verifications: {n_ov} (model had correct, then changed)')
            print(f'    Computed-not-boxed: {n_cnb} (correct in output, not extracted)')
            potential = s.attempts_with_correct_answer + n_ov + n_cnb
            print(f'    POTENTIAL correct votes if captured: {potential}/{s.total_attempts}')

            # Would capturing these flip the vote?
            # Use ACTUAL vote counts from the parsed problem (not just diluted votes)
            prob_obj = next(p for p in problems if p.problem_id == s.problem_id and p.expected == s.expected)
            rescued_attempt_nums = set()
            for cnb in s.computed_not_boxed:
                rescued_attempt_nums.add(cnb.attempt_num)
            for ov in s.over_verifications:
                rescued_attempt_nums.add(ov.attempt_num)

            # Build new vote distribution: rescued attempts vote correct, others unchanged
            new_votes = defaultdict(int)
            new_votes[s.expected] = s.attempts_with_correct_answer + len(rescued_attempt_nums)
            for a in prob_obj.attempts:
                if a.attempt_num in rescued_attempt_nums:
                    continue  # already counted as correct
                if a.answer == s.expected:
                    continue  # already counted
                if a.answer is not None:
                    new_votes[a.answer] += 1

            top_answer = max(new_votes, key=new_votes.get)
            top_count = new_votes[top_answer]
            correct_count = new_votes[s.expected]

            if top_answer == s.expected:
                print(f'    >> WOULD FLIP: {correct_count} correct votes = new plurality (next: '
                      f'{sorted(new_votes.items(), key=lambda x: -x[1])[1] if len(new_votes) > 1 else ("N/A", 0)})')
            else:
                print(f'    >> Would NOT flip: {correct_count} correct vs {top_count} for {top_answer}')
            print()
    else:
        print('  No recoverable wrong problems found.')
        print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 6: NET SCORE IMPACT
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  6. NET SCORE IMPACT: If we could capture all intermediate correct answers')
    print('=' * 90)
    print()

    current_score = sum(1 for s in summaries if s.correct)

    # For each wrong problem, simulate: if over-verification and computed-not-boxed
    # attempts had voted for the correct answer instead, would the vote flip?
    flippable = 0
    flip_details = []
    for s in summaries:
        if s.correct:
            continue

        # Count actual correct votes
        actual_correct_votes = s.attempts_with_correct_answer

        # Count additional rescuable votes
        ov_attempts = set(ov.attempt_num for ov in s.over_verifications)
        cnb_attempts = set(cnb.attempt_num for cnb in s.computed_not_boxed)
        all_rescuable = ov_attempts | cnb_attempts
        additional = len(all_rescuable)

        if additional == 0:
            continue

        total_correct_if_rescued = actual_correct_votes + additional

        # Count votes for each answer (excluding rescued attempts)
        prob_obj = next(p for p in problems if p.problem_id == s.problem_id and p.expected == s.expected)
        all_votes = defaultdict(int)
        all_votes[s.expected] = total_correct_if_rescued
        for a_obj in prob_obj.attempts:
            if a_obj.attempt_num in all_rescuable:
                continue
            if a_obj.answer == s.expected:
                continue
            if a_obj.answer is not None:
                all_votes[a_obj.answer] += 1

        # Check if correct answer now wins
        top_answer = max(all_votes, key=all_votes.get)
        top_count = all_votes[top_answer]

        # Also check non-correct top
        wrong_votes = {k: v for k, v in all_votes.items() if k != s.expected}
        top_wrong_answer = max(wrong_votes.values()) if wrong_votes else 0
        top_wrong_val = max(wrong_votes, key=wrong_votes.get) if wrong_votes else None

        would_flip = total_correct_if_rescued > top_wrong_answer
        if would_flip:
            flippable += 1
            flip_details.append({
                'pid': s.problem_id,
                'expected': s.expected,
                'predicted': s.predicted,
                'actual_correct': actual_correct_votes,
                'rescued': additional,
                'total_correct': total_correct_if_rescued,
                'top_wrong_votes': top_wrong_answer,
                'top_wrong_val': top_wrong_val,
            })

    print(f'  Current score: {current_score}/{len(summaries)}')
    print(f'  Wrong problems with rescuable signal: {len(recoverable) if recoverable else 0}')
    print(f'  Wrong problems that WOULD FLIP with rescue: {flippable}')
    print(f'  Potential new score: {current_score + flippable}/{len(summaries)}')
    print(f'  Net gain: +{flippable} problems')
    print()

    if flip_details:
        print(f'  Flippable problems:')
        for fd in flip_details:
            print(f'    {fd["pid"]}: {fd["actual_correct"]} existing + {fd["rescued"]} rescued = '
                  f'{fd["total_correct"]} correct vs {fd["top_wrong_votes"]} for {fd["top_wrong_val"]}')
        print()

    # Non-flippable problems with signal
    non_flip = [s for s in (recoverable or []) if s.problem_id not in [fd['pid'] for fd in flip_details]]
    if non_flip:
        print(f'  Non-flippable (not enough signal even with rescue):')
        for s in non_flip:
            n_ov = len(s.over_verifications)
            n_cnb = len(s.computed_not_boxed)
            potential = s.attempts_with_correct_answer + n_ov + n_cnb
            print(f'    {s.problem_id}: {potential} potential correct votes vs strong wrong majority '
                  f'(pred={s.predicted}, exp={s.expected})')
        print()

    # ════════════════════════════════════════════════════════════════════════
    # SECTION 7: GRAND SUMMARY
    # ════════════════════════════════════════════════════════════════════════
    print('=' * 90)
    print('  GRAND SUMMARY')
    print('=' * 90)
    print()

    total_ov = sum(len(s.over_verifications) for s in summaries)
    total_cnb = sum(len(s.computed_not_boxed) for s in summaries)
    total_ov_wrong = sum(len(s.over_verifications) for s in summaries if not s.correct)
    total_cnb_wrong = sum(len(s.computed_not_boxed) for s in summaries if not s.correct)

    # Wasted signal on correct problems
    total_wasted = sum(
        len(s.diluted_votes) for s in summaries if s.correct
    )
    total_wasted_with_signal = sum(
        sum(1 for vd in s.diluted_votes if vd.had_correct_intermediate)
        for s in summaries if s.correct
    )

    print(f'  Over-verification (boxed correct then boxed wrong):')
    print(f'    Total cases: {total_ov} ({total_ov_wrong} on wrong problems)')
    ov_probs = set(ov.problem_id for s in summaries for ov in s.over_verifications)
    print(f'    Affected problems: {len(ov_probs)}')
    print()

    print(f'  Computed-but-not-boxed (correct in output, not extracted):')
    print(f'    Total cases: {total_cnb} ({total_cnb_wrong} on wrong problems)')
    cnb_probs = set(cnb.problem_id for s in summaries for cnb in s.computed_not_boxed)
    print(f'    Affected problems: {len(cnb_probs)}')
    print()

    print(f'  Vote dilution on correct problems:')
    print(f'    Total non-correct votes: {total_wasted_correct}')
    print(f'    Of which had correct intermediate: {total_wasted_with_intermediate_correct}')
    print(f'    None votes: {wasted_none_correct}, Wrong votes: {wasted_wrong_correct}')
    print()

    print(f'  Score impact:')
    print(f'    Current: {current_score}/{len(summaries)} ({current_score/len(summaries)*100:.1f}%)')
    print(f'    With intermediate capture: {current_score + flippable}/{len(summaries)} '
          f'({(current_score + flippable)/len(summaries)*100:.1f}%)')
    print(f'    Net gain: +{flippable} problems')
    print()

    # Highest-impact problems
    print(f'  Highest-impact problems for intermediate capture:')
    impact_list = []
    for s in summaries:
        if s.correct:
            continue
        n_ov = len(s.over_verifications)
        n_cnb = len(s.computed_not_boxed)
        if n_ov + n_cnb > 0:
            impact_list.append((s.problem_id, n_ov, n_cnb, s.attempts_with_correct_answer,
                               s.predicted, s.expected,
                               s.problem_id in [fd['pid'] for fd in flip_details]))

    impact_list.sort(key=lambda x: -(x[1] + x[2]))
    for pid, nov, ncnb, ncorr, pred, exp, flips in impact_list:
        flip_str = 'FLIPPABLE' if flips else 'not enough'
        print(f'    {pid}: {nov} over-verif + {ncnb} computed-not-boxed + {ncorr} correct '
              f'= {nov + ncnb + ncorr} signal | pred={pred} exp={exp} | {flip_str}')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Intermediate answer analysis')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    args = parser.parse_args()
    analyze(args.logfile)
