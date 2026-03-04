#!/usr/bin/env python3
"""
Intermediate Answer Loss Analysis
==================================
Finds problems where the correct answer was computed during an attempt
but was NOT captured as the attempt's final answer.

Three analysis modes:
  1. Over-verification: Model wrote \\boxed{correct} then later wrote \\boxed{different}
  2. Correct in code output: Expected answer appeared in code output but attempt
     returned None or a different answer
  3. Correct in reasoning: Expected answer appeared in reasoning text (not boxed)
     but attempt returned None or a different answer

Also computes:
  - Vote impact: For problems we got correct, how many attempts wasted their vote
  - Per-problem summary with actionability score
  - Cross-version comparison with v31 (if available)

Usage:
    python3 log_exploration/intermediate_answer_v23.py <diagnostic.log> [--v31 <v31_log>]
    python3 log_exploration/intermediate_answer_v23.py output/v23/diagnostic.log --v31 output/v31/diagnostic.log
"""

import sys
import os
import re
import argparse
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


# ── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class IntermediateFind:
    """A single occurrence of the correct answer found in an attempt."""
    turn_num: int
    source: str           # 'code_output', 'reasoning', 'boxed'
    context: str = ""     # snippet around the match
    is_standalone: bool = False  # number appears as standalone value (not substring of larger expression)


@dataclass
class AttemptAnalysis:
    """Analysis of one attempt for intermediate answer presence."""
    attempt_num: int
    final_answer: Optional[int]
    is_none: bool
    finds: list = field(default_factory=list)  # list of IntermediateFind
    boxed_sequence: list = field(default_factory=list)  # ordered list of (turn, value) boxed
    over_verified: bool = False  # correct was boxed then replaced


@dataclass
class ProblemAnalysis:
    """Per-problem intermediate answer analysis."""
    problem_id: str
    batch_name: str
    expected: Optional[int]
    predicted: Optional[int]
    correct: bool
    total_attempts: int
    attempts_with_correct_intermediate: int = 0
    attempts_correct_final: int = 0
    attempt_analyses: list = field(default_factory=list)
    over_verification_cases: int = 0
    code_output_losses: int = 0
    reasoning_losses: int = 0
    wasted_votes: int = 0  # attempts that found correct but voted differently


# ── Core Analysis Functions ──────────────────────────────────────────────────

def extract_boxed_values(text: str) -> list:
    """Extract all \\boxed{N} values from text, return list of ints."""
    matches = re.findall(r'boxed\s*\{\s*(\d[\d,]*)\s*\}', text)
    return [int(m.replace(',', '')) for m in matches]


def extract_vboxed_values(text: str) -> list:
    """Extract all \\Vboxed{N} values from text, return list of ints."""
    matches = re.findall(r'[Vv]boxed\s*\{\s*(\d[\d,]*)\s*\}', text)
    return [int(m.replace(',', '')) for m in matches]


def find_number_in_text(text: str, target: int, source_name: str) -> list:
    """Find all standalone occurrences of target number in text.

    Returns list of IntermediateFind with context snippets.
    Uses word-boundary matching to reduce false positives.
    """
    if not text:
        return []

    target_str = str(target)
    finds = []

    # Use word boundary for matching: not preceded/followed by digit
    pattern = r'(?<![0-9])' + re.escape(target_str) + r'(?![0-9])'

    for m in re.finditer(pattern, text):
        start = max(0, m.start() - 60)
        end = min(len(text), m.end() + 60)
        context = text[start:end].replace('\n', ' ').strip()

        # Determine if this is a "standalone" value vs embedded in expression
        # Standalone: appears as a print output, or "= 315", or "is 315"
        # Not standalone: appears in large list, dictionary, or as part of computation
        local_ctx = text[max(0, m.start()-20):min(len(text), m.end()+20)]
        is_standalone = bool(re.search(
            r'(?:^|\n)\s*' + re.escape(target_str) + r'\s*(?:$|\n)',
            local_ctx
        )) or bool(re.search(
            r'(?:=|is|:)\s*' + re.escape(target_str) + r'(?:\s|$|\n|,)',
            local_ctx
        )) or bool(re.search(
            r'print.*' + re.escape(target_str),
            local_ctx
        ))

        finds.append(IntermediateFind(
            turn_num=0,  # will be set by caller
            source=source_name,
            context=context[:120],
            is_standalone=is_standalone,
        ))

    return finds


def analyze_attempt(attempt, expected: int) -> AttemptAnalysis:
    """Analyze a single attempt for intermediate correct answers."""
    analysis = AttemptAnalysis(
        attempt_num=attempt.attempt_num,
        final_answer=attempt.answer,
        is_none=attempt.is_none,
    )

    for turn in attempt.turns:
        # 1. Check boxed values in reasoning
        boxed_vals = extract_boxed_values(turn.reasoning_text)
        vboxed_vals = extract_vboxed_values(turn.reasoning_text)

        for v in boxed_vals:
            analysis.boxed_sequence.append((turn.turn_num, v))

        for v in vboxed_vals:
            analysis.boxed_sequence.append((turn.turn_num, v))

        # If expected appears in boxed but is not the final answer
        if expected in boxed_vals or expected in vboxed_vals:
            analysis.finds.append(IntermediateFind(
                turn_num=turn.turn_num,
                source='boxed',
                context=f'boxed={boxed_vals} vboxed={vboxed_vals}',
                is_standalone=True,
            ))

        # 2. Check code output for expected answer
        output_finds = find_number_in_text(turn.output, expected, 'code_output')
        for f in output_finds:
            f.turn_num = turn.turn_num
            analysis.finds.append(f)

        # 3. Check reasoning text for expected answer (non-boxed)
        reasoning_finds = find_number_in_text(turn.reasoning_text, expected, 'reasoning')
        for f in reasoning_finds:
            f.turn_num = turn.turn_num
            # Skip if already captured as boxed
            if not (expected in boxed_vals or expected in vboxed_vals):
                analysis.finds.append(f)

    # Check for over-verification: correct boxed then replaced
    unique_boxed = []
    seen = set()
    for _, v in analysis.boxed_sequence:
        if v not in seen:
            unique_boxed.append(v)
            seen.add(v)

    if len(unique_boxed) > 1 and expected in unique_boxed:
        # Check if correct appeared before a different final value
        first_correct_idx = unique_boxed.index(expected)
        if first_correct_idx < len(unique_boxed) - 1:
            analysis.over_verified = True

    return analysis


def analyze_problem(problem) -> Optional[ProblemAnalysis]:
    """Analyze one problem for intermediate answer loss."""
    if problem.expected is None:
        return None

    pa = ProblemAnalysis(
        problem_id=problem.problem_id,
        batch_name=problem.batch_name,
        expected=problem.expected,
        predicted=problem.predicted,
        correct=problem.correct,
        total_attempts=len(problem.attempts),
    )

    for attempt in problem.attempts:
        aa = analyze_attempt(attempt, problem.expected)
        pa.attempt_analyses.append(aa)

        has_correct_intermediate = len(aa.finds) > 0
        has_correct_final = (attempt.answer == problem.expected)

        if has_correct_final:
            pa.attempts_correct_final += 1

        if has_correct_intermediate and not has_correct_final:
            pa.attempts_with_correct_intermediate += 1

            # Classify the loss
            sources = set(f.source for f in aa.finds)
            if aa.over_verified:
                pa.over_verification_cases += 1
            if 'code_output' in sources:
                pa.code_output_losses += 1
            if 'reasoning' in sources:
                pa.reasoning_losses += 1

            # This attempt wasted its vote
            if attempt.answer is not None:
                pa.wasted_votes += 1

    return pa


# ── False Positive Filtering ────────────────────────────────────────────────

def is_likely_false_positive(expected: int, finds: list) -> bool:
    """Filter out likely false positives for small numbers.

    Small numbers (1-2 digits) appearing in code output are very often
    coincidental (loop counters, array indices, etc.) unless they appear
    in standalone contexts.
    """
    if expected >= 100:
        return False  # Large numbers are rarely false positives

    # For small numbers, require at least one standalone find
    return not any(f.is_standalone for f in finds)


# ── Reporting ────────────────────────────────────────────────────────────────

def print_section(title: str, char: str = "="):
    print(f"\n{title}")
    print(char * len(title))


def report_over_verification(analyses: list):
    """Report 1: Over-verification cases."""
    print_section("1. OVER-VERIFICATION ANALYSIS")
    print("Cases where model wrote \\boxed{correct} then replaced with \\boxed{different}.\n")

    total_cases = 0
    for pa in analyses:
        for aa in pa.attempt_analyses:
            if aa.over_verified:
                total_cases += 1
                print(f"  Problem {pa.problem_id} Attempt {aa.attempt_num}: "
                      f"expected={pa.expected}, final={aa.final_answer}")
                for turn_num, val in aa.boxed_sequence:
                    marker = " <-- CORRECT" if val == pa.expected else ""
                    print(f"    Turn {turn_num}: \\boxed{{{val}}}{marker}")

    if total_cases == 0:
        print("  No over-verification cases found.")
        print("  The model never wrote \\boxed{correct} and then changed to \\boxed{different}.")
        print("  When the model commits to a boxed answer, it sticks with it.")
    else:
        print(f"\n  Total over-verification cases: {total_cases}")


def report_code_output_losses(analyses: list):
    """Report 2: Correct answer in code output but lost."""
    print_section("2. CORRECT ANSWER IN CODE OUTPUT BUT LOST")
    print("Attempts where expected answer appeared in code execution output")
    print("but the attempt returned None or a different answer.\n")

    # Group by problem
    problems_with_losses = []
    for pa in analyses:
        if pa.code_output_losses == 0:
            continue

        # Filter false positives for this problem
        real_losses = 0
        attempt_details = []
        for aa in pa.attempt_analyses:
            code_finds = [f for f in aa.finds if f.source == 'code_output']
            if not code_finds or aa.final_answer == pa.expected:
                continue
            if is_likely_false_positive(pa.expected, code_finds):
                continue

            real_losses += 1
            standalone = sum(1 for f in code_finds if f.is_standalone)
            attempt_details.append((aa, code_finds, standalone))

        if real_losses > 0:
            problems_with_losses.append((pa, attempt_details, real_losses))

    # Sort by number of losses (most wasteful first)
    problems_with_losses.sort(key=lambda x: x[2], reverse=True)

    total_losses = sum(n for _, _, n in problems_with_losses)
    print(f"  Problems affected: {len(problems_with_losses)}")
    print(f"  Total attempts with lost code output answers: {total_losses}")
    print()

    for pa, details, n_losses in problems_with_losses:
        status = "CORRECT" if pa.correct else "WRONG"
        print(f"  Problem {pa.problem_id} [{status}] expected={pa.expected} predicted={pa.predicted}")
        print(f"    Attempts finding correct in output: {n_losses}/{pa.total_attempts}")
        print(f"    Attempts with correct final answer: {pa.attempts_correct_final}/{pa.total_attempts}")

        for aa, code_finds, standalone in details[:5]:  # show up to 5
            ans_str = "None" if aa.is_none else str(aa.final_answer)
            print(f"      Att {aa.attempt_num}: submitted={ans_str}, "
                  f"found in turns: {[f.turn_num for f in code_finds]}, "
                  f"standalone={standalone}")
            # Show best context snippet
            best = next((f for f in code_finds if f.is_standalone), code_finds[0])
            print(f"        Context: \"{best.context}\"")

        if len(details) > 5:
            print(f"      ... and {len(details) - 5} more attempts")
        print()

    return problems_with_losses


def report_reasoning_losses(analyses: list):
    """Report 3: Correct answer mentioned in reasoning but lost."""
    print_section("3. CORRECT ANSWER IN REASONING TEXT BUT LOST")
    print("Attempts where expected answer appeared in reasoning (not \\boxed)")
    print("but the attempt returned None or a different answer.\n")
    print("NOTE: High false-positive rate for small numbers. Filtered aggressively.\n")

    problems_with_losses = []
    for pa in analyses:
        if pa.reasoning_losses == 0:
            continue

        real_losses = 0
        attempt_details = []
        for aa in pa.attempt_analyses:
            reasoning_finds = [f for f in aa.finds if f.source == 'reasoning']
            if not reasoning_finds or aa.final_answer == pa.expected:
                continue
            if is_likely_false_positive(pa.expected, reasoning_finds):
                continue
            real_losses += 1
            attempt_details.append((aa, reasoning_finds))

        if real_losses > 0:
            problems_with_losses.append((pa, attempt_details, real_losses))

    problems_with_losses.sort(key=lambda x: x[2], reverse=True)

    total_losses = sum(n for _, _, n in problems_with_losses)
    print(f"  Problems affected: {len(problems_with_losses)}")
    print(f"  Total attempts with lost reasoning answers: {total_losses}")
    print()

    for pa, details, n_losses in problems_with_losses[:20]:
        status = "CORRECT" if pa.correct else "WRONG"
        print(f"  Problem {pa.problem_id} [{status}] expected={pa.expected} predicted={pa.predicted}")
        print(f"    Lost reasoning mentions: {n_losses}/{pa.total_attempts}")

        for aa, finds in details[:3]:
            ans_str = "None" if aa.is_none else str(aa.final_answer)
            print(f"      Att {aa.attempt_num}: submitted={ans_str}, "
                  f"found in turns: {sorted(set(f.turn_num for f in finds))}")
            best = next((f for f in finds if f.is_standalone), finds[0])
            print(f"        Context: \"{best.context}\"")
        if len(details) > 3:
            print(f"      ... and {len(details) - 3} more attempts")
        print()

    return problems_with_losses


def report_vote_impact(analyses: list):
    """Report 4: Vote waste analysis."""
    print_section("4. VOTE IMPACT ANALYSIS")
    print("For ALL problems: how many attempts computed the correct answer")
    print("but voted for something else (wasted signal).\n")

    # Categorize problems
    correct_probs = [pa for pa in analyses if pa.correct]
    wrong_probs = [pa for pa in analyses if not pa.correct]

    print(f"  Total problems analyzed: {len(analyses)}")
    print(f"  Correct: {len(correct_probs)}, Wrong: {len(wrong_probs)}")
    print()

    # For correct problems: wasted votes show room for improvement
    print_section("4a. CORRECT PROBLEMS — Wasted Signal", "-")
    print("  These problems got the right final answer, but some attempts")
    print("  computed it and then submitted something else.\n")

    correct_with_waste = []
    for pa in correct_probs:
        waste = 0
        for aa in pa.attempt_analyses:
            code_finds = [f for f in aa.finds if f.source == 'code_output']
            any_finds = aa.finds
            if any_finds and aa.final_answer != pa.expected:
                if not is_likely_false_positive(pa.expected, any_finds):
                    waste += 1
        if waste > 0:
            correct_with_waste.append((pa, waste))

    correct_with_waste.sort(key=lambda x: x[1], reverse=True)
    total_wasted = sum(w for _, w in correct_with_waste)
    print(f"  Correct problems with wasted votes: {len(correct_with_waste)}/{len(correct_probs)}")
    print(f"  Total wasted attempts: {total_wasted}")
    print()

    for pa, waste in correct_with_waste[:15]:
        print(f"    {pa.problem_id}: expected={pa.expected}, "
              f"wasted={waste}/{pa.total_attempts}, "
              f"correct_final={pa.attempts_correct_final}/{pa.total_attempts}")

    # For wrong problems: lost answers that could have swung the vote
    print()
    print_section("4b. WRONG PROBLEMS — Recoverable Signal", "-")
    print("  These problems got the WRONG answer, but some attempts found the correct one.\n")

    wrong_with_signal = []
    for pa in wrong_probs:
        signal = 0
        for aa in pa.attempt_analyses:
            if aa.finds and aa.final_answer != pa.expected:
                if not is_likely_false_positive(pa.expected, aa.finds):
                    signal += 1
        # Also count attempts that DID get correct final answer
        correct_final = pa.attempts_correct_final
        total_potential = signal + correct_final
        if total_potential > 0:
            wrong_with_signal.append((pa, signal, correct_final, total_potential))

    wrong_with_signal.sort(key=lambda x: x[3], reverse=True)
    print(f"  Wrong problems with any correct signal: {len(wrong_with_signal)}/{len(wrong_probs)}")
    print()

    for pa, lost, found, total in wrong_with_signal:
        print(f"    {pa.problem_id}: expected={pa.expected} predicted={pa.predicted}, "
              f"correct_final={found}, computed_but_lost={lost}, "
              f"total_correct_signal={total}/{pa.total_attempts}")
        if total > pa.total_attempts // 2:
            print(f"      *** COULD HAVE WON VOTE with better extraction ***")

    return correct_with_waste, wrong_with_signal


def report_summary(analyses: list, code_losses: list, reasoning_losses: list):
    """Report 5: Summary statistics."""
    print_section("5. SUMMARY STATISTICS")

    total_problems = len(analyses)
    total_attempts = sum(pa.total_attempts for pa in analyses)

    # Count problems with any intermediate correct answer loss
    probs_with_any_loss = set()
    total_lost_attempts = 0

    for pa in analyses:
        for aa in pa.attempt_analyses:
            if aa.finds and aa.final_answer != pa.expected:
                if not is_likely_false_positive(pa.expected, aa.finds):
                    probs_with_any_loss.add(pa.problem_id)
                    total_lost_attempts += 1

    print(f"\n  Problems analyzed:             {total_problems}")
    print(f"  Total attempts analyzed:       {total_attempts}")
    print(f"  Problems with lost answers:    {len(probs_with_any_loss)}/{total_problems} "
          f"({100*len(probs_with_any_loss)/total_problems:.1f}%)")
    print(f"  Attempts with lost answers:    {total_lost_attempts}/{total_attempts} "
          f"({100*total_lost_attempts/total_attempts:.1f}%)")
    print()

    # Breakdown by loss type
    over_ver = sum(pa.over_verification_cases for pa in analyses)
    code_loss_atts = sum(n for _, _, n in code_losses)
    reason_loss_atts = sum(n for _, _, n in reasoning_losses)

    print(f"  Over-verification (boxed then changed):  {over_ver} attempts")
    print(f"  Code output (computed but not extracted): {code_loss_atts} attempts across {len(code_losses)} problems")
    print(f"  Reasoning (mentioned but not captured):  {reason_loss_atts} attempts across {len(reasoning_losses)} problems")


def report_cross_version(analyses_v23: list, v31_path: str):
    """Report 6: Cross-version comparison."""
    print_section("6. CROSS-VERSION COMPARISON (v23 vs v31)")

    try:
        problems_v31 = parse_log(v31_path)
    except Exception as e:
        print(f"  Could not load v31 log: {e}")
        return

    print(f"  v31: {len(problems_v31)} problems, "
          f"{sum(1 for p in problems_v31 if p.correct)}/{len(problems_v31)} correct\n")

    # Build v31 lookup
    v31_by_id = defaultdict(list)
    for p in problems_v31:
        v31_by_id[p.problem_id].append(p)

    # Analyze v31
    v31_analyses = {}
    for p in problems_v31:
        pa = analyze_problem(p)
        if pa:
            v31_analyses[pa.problem_id] = pa

    # Compare problems present in both
    v23_by_id = {}
    for pa in analyses_v23:
        v23_by_id[pa.problem_id] = pa

    common_ids = set(v23_by_id.keys()) & set(v31_analyses.keys())
    print(f"  Common problems: {len(common_ids)}\n")

    if not common_ids:
        print("  No common problems to compare.")
        return

    print(f"  {'Problem':<12} {'v23 Status':<12} {'v31 Status':<12} {'v23 Lost':<10} {'v31 Lost':<10} {'Pattern Same?'}")
    print(f"  {'─'*12} {'─'*12} {'─'*12} {'─'*10} {'─'*10} {'─'*15}")

    both_have_loss = 0
    for pid in sorted(common_ids):
        pa23 = v23_by_id[pid]
        pa31 = v31_analyses[pid]

        # Count real losses (filtered)
        losses_23 = 0
        losses_31 = 0
        for aa in pa23.attempt_analyses:
            if aa.finds and aa.final_answer != pa23.expected:
                if not is_likely_false_positive(pa23.expected, aa.finds):
                    losses_23 += 1
        for aa in pa31.attempt_analyses:
            if aa.finds and aa.final_answer != pa31.expected:
                if not is_likely_false_positive(pa31.expected, aa.finds):
                    losses_31 += 1

        if losses_23 == 0 and losses_31 == 0:
            continue

        s23 = "CORRECT" if pa23.correct else "WRONG"
        s31 = "CORRECT" if pa31.correct else "WRONG"
        same = "YES" if (losses_23 > 0 and losses_31 > 0) else "no"
        if same == "YES":
            both_have_loss += 1

        print(f"  {pid:<12} {s23:<12} {s31:<12} {losses_23:<10} {losses_31:<10} {same}")

    print(f"\n  Problems with intermediate loss in BOTH versions: {both_have_loss}")
    if both_have_loss > 0:
        print("  These represent systematic model behavior — not random failures.")


def report_per_problem_table(analyses: list):
    """Print a compact per-problem table."""
    print_section("7. PER-PROBLEM DETAIL TABLE")
    print()

    header = (f"  {'PID':<12} {'Status':<8} {'Expected':<10} {'Predicted':<10} "
              f"{'Correct':<8} {'Lost':<6} {'OV':<4} {'Code':<6} {'Reas':<6} {'Waste':<6}")
    print(header)
    print("  " + "─" * (len(header) - 2))

    for pa in analyses:
        # Count filtered losses
        lost = 0
        for aa in pa.attempt_analyses:
            if aa.finds and aa.final_answer != pa.expected:
                if not is_likely_false_positive(pa.expected, aa.finds):
                    lost += 1

        if lost == 0 and pa.over_verification_cases == 0:
            continue

        status = "OK" if pa.correct else "WRONG"
        pred = str(pa.predicted) if pa.predicted else "None"

        # Count code output and reasoning losses (filtered)
        code_losses = 0
        reas_losses = 0
        waste = 0
        for aa in pa.attempt_analyses:
            if aa.final_answer == pa.expected:
                continue
            code_f = [f for f in aa.finds if f.source == 'code_output']
            reas_f = [f for f in aa.finds if f.source == 'reasoning']
            if code_f and not is_likely_false_positive(pa.expected, code_f):
                code_losses += 1
            if reas_f and not is_likely_false_positive(pa.expected, reas_f):
                reas_losses += 1
            if aa.finds and aa.final_answer is not None and aa.final_answer != pa.expected:
                if not is_likely_false_positive(pa.expected, aa.finds):
                    waste += 1

        print(f"  {pa.problem_id:<12} {status:<8} {pa.expected:<10} {pred:<10} "
              f"{pa.attempts_correct_final:<8} {lost:<6} {pa.over_verification_cases:<4} "
              f"{code_losses:<6} {reas_losses:<6} {waste:<6}")


def report_actionable_insights(analyses: list, code_losses: list, wrong_with_signal: list):
    """Report 8: Actionable insights."""
    print_section("8. ACTIONABLE INSIGHTS")
    print()

    # 1. Extraction failures are the main loss mode
    total_code_loss_atts = sum(n for _, _, n in code_losses)
    print(f"  a) CODE OUTPUT EXTRACTION FAILURES: {total_code_loss_atts} attempts across {len(code_losses)} problems")
    print(f"     The model computes the correct answer in Python but the extraction")
    print(f"     regex fails to capture it. This is the #1 source of intermediate loss.")
    print(f"     FIX: Improve answer extraction from code output. Look for the last")
    print(f"     standalone integer printed, not just boxed patterns.")
    print()

    # 2. Wrong problems that could be rescued
    rescuable = [(pa, lost, found, total) for pa, lost, found, total in wrong_with_signal
                 if total >= 3]
    if rescuable:
        print(f"  b) RESCUABLE WRONG PROBLEMS: {len(rescuable)} problems have 3+ attempts")
        print(f"     that computed the correct answer but failed to capture it.")
        for pa, lost, found, total in rescuable:
            print(f"       {pa.problem_id}: {total} attempts had correct signal "
                  f"(need {pa.total_attempts//2 + 1} to win vote)")
        print()

    # 3. Over-verification
    ov_total = sum(pa.over_verification_cases for pa in analyses)
    if ov_total == 0:
        print(f"  c) OVER-VERIFICATION: Not a problem. The model never changes its")
        print(f"     \\boxed{{}} answer once written. No signal lost this way.")
    else:
        print(f"  c) OVER-VERIFICATION: {ov_total} cases found. Consider checkpointing")
        print(f"     the first \\boxed{{}} value as a fallback.")
    print()

    # 4. Small vs large number problem
    small_fp_risk = sum(1 for pa in analyses if pa.expected and pa.expected < 100)
    print(f"  d) ANALYSIS NOTE: {small_fp_risk} problems have expected < 100.")
    print(f"     Small-number matches in code output have high false-positive rates.")
    print(f"     The filtered counts above exclude uncertain small-number matches.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Analyze intermediate answer loss in AIMO3 diagnostic logs."
    )
    parser.add_argument("logfile", help="Path to diagnostic.log")
    parser.add_argument("--v31", help="Path to v31 diagnostic.log for comparison",
                        default=None)
    parser.add_argument("--problem", "-p", help="Analyze a single problem ID",
                        default=None)
    args = parser.parse_args()

    print("=" * 70)
    print("INTERMEDIATE ANSWER LOSS ANALYSIS")
    print("=" * 70)
    print(f"Log: {args.logfile}")

    problems = parse_log(args.logfile)
    print(f"Parsed: {len(problems)} problems, "
          f"{sum(1 for p in problems if p.correct)}/{len(problems)} correct")

    # Analyze all problems
    analyses = []
    for p in problems:
        pa = analyze_problem(p)
        if pa:
            if args.problem and pa.problem_id != args.problem:
                continue
            analyses.append(pa)

    print(f"Analyzing: {len(analyses)} problems with known expected answers")

    # Run all reports
    report_over_verification(analyses)
    code_losses = report_code_output_losses(analyses)
    reasoning_losses = report_reasoning_losses(analyses)
    correct_waste, wrong_signal = report_vote_impact(analyses)
    report_summary(analyses, code_losses, reasoning_losses)

    if args.v31:
        report_cross_version(analyses, args.v31)

    report_per_problem_table(analyses)
    report_actionable_insights(analyses, code_losses, wrong_signal)


if __name__ == "__main__":
    main()
