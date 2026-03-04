#!/usr/bin/env python3
"""
Vboxed Checkpoint Analysis
==========================
Analyzes the effectiveness of the \\Vboxed{N} checkpoint feature.

The solver instructs the model to write \\Vboxed{N} as a checkpoint answer
before writing the final \\boxed{N}. Extraction priority:
  - \\boxed{N}  -> confidence 1.0
  - \\Vboxed{N} -> confidence 0.7
  - fallback patterns -> confidence 0.7

Voting uses confidence as vote weight: answer_votes[ans] += confidence.
Primary sort: votes (desc), then entropy-weighted score, then answer value.

This script answers:
  1. How many attempts used Vboxed (0.7) vs boxed (1.0)?
  2. Of Vboxed-only attempts, how many were correct?
  3. Were there cases where Vboxed saved us (no boxed, but Vboxed caught answer)?
  4. Were there cases where Vboxed hurt us (wrong Vboxed diluted correct vote)?
  5. Did Vboxed change the outcome of any problem's final voted answer?
  6. Overall assessment: helping, hurting, or neutral?

Usage:
    python3 log_exploration/vboxed_analysis.py <diagnostic.log>
"""

import sys
import re
import math
import argparse
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, '.')
from log_exploration.log_query import parse_log


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_attempt_full_text(attempt) -> str:
    """Collect all text from an attempt's turns."""
    parts = []
    for t in attempt.turns:
        parts.append(t.reasoning_text)
        parts.append(t.code)
        parts.append(t.output)
    return ' '.join(parts)


def classify_answer_source(full_text: str) -> str:
    """Classify where the answer came from using the same priority as the solver.

    Returns one of: 'boxed', 'vboxed', 'fallback_final_answer',
                    'fallback_answer_is', 'fallback_answer_eq', 'fallback_boxed_latex', 'unknown'
    """
    # Priority 1: \boxed{N}
    if re.findall(r'[\\]boxed\s*\{\s*[0-9,]+\s*\}', full_text):
        return 'boxed'

    # Priority 2: \Vboxed{N}
    if re.findall(r'[\\]Vboxed\s*\{\s*[0-9,]+\s*\}', full_text):
        return 'vboxed'

    # Priority 3-5: fallback text patterns
    if re.findall(r'final\s+answer\s+is\s*[0-9,]+', full_text, re.IGNORECASE):
        return 'fallback_final_answer'
    if re.findall(r'(?:the\s+)?answer\s+is\s*:?\s*\*?\*?\s*[0-9,]+', full_text, re.IGNORECASE):
        return 'fallback_answer_is'
    if re.findall(r'answer\s*[:=]\s*\*?\*?\s*[0-9,]+', full_text, re.IGNORECASE):
        return 'fallback_answer_eq'

    # Priority 6: boxed with LaTeX content
    if re.findall(r'[\\]boxed\s*\{[^}]+\}', full_text):
        return 'fallback_boxed_latex'

    return 'unknown'


def extract_answer_like_solver(full_text: str):
    """Replicate the solver's extraction logic. Returns (answer, confidence, source)."""
    def _try_extract(val_str):
        try:
            v = int(val_str.replace(',', ''))
            if 0 <= v <= 99999:
                return v
            v_mod = v % 100000
            if 0 <= v_mod <= 99999:
                return v_mod
        except (ValueError, OverflowError):
            pass
        return None

    # Priority 1: \boxed{N}
    matches = re.findall(r'[\\]boxed\s*\{\s*([0-9,]+)\s*\}', full_text)
    if matches:
        val = _try_extract(matches[-1])
        if val is not None:
            return val, 1.0, 'boxed'

    # Priority 2: \Vboxed{N}
    matches = re.findall(r'[\\]Vboxed\s*\{\s*([0-9,]+)\s*\}', full_text)
    if matches:
        val = _try_extract(matches[-1])
        if val is not None:
            return val, 0.7, 'vboxed'

    # Priority 3: 'final answer is X'
    matches = re.findall(r'final\s+answer\s+is\s*([0-9,]+)', full_text, re.IGNORECASE)
    if matches:
        val = _try_extract(matches[-1])
        if val is not None:
            return val, 0.7, 'fallback_final_answer'

    # Priority 4: 'the answer is X'
    matches = re.findall(r'(?:the\s+)?answer\s+is\s*:?\s*\*?\*?\s*([0-9,]+)', full_text, re.IGNORECASE)
    if matches:
        val = _try_extract(matches[-1])
        if val is not None:
            return val, 0.7, 'fallback_answer_is'

    # Priority 5: 'answer: X' / 'answer = X'
    matches = re.findall(r'answer\s*[:=]\s*\*?\*?\s*([0-9,]+)', full_text, re.IGNORECASE)
    if matches:
        val = _try_extract(matches[-1])
        if val is not None:
            return val, 0.7, 'fallback_answer_eq'

    # Priority 6: boxed with LaTeX
    matches = re.findall(r'[\\]boxed\s*\{([^}]+)\}', full_text)
    if matches:
        nums = re.findall(r'(\d+)', matches[-1])
        if nums:
            val = _try_extract(nums[-1])
            if val is not None:
                return val, 0.5, 'fallback_boxed_latex'

    return None, 0.0, 'none'


def simulate_voting(attempt_results, use_confidence=True):
    """Simulate the solver's voting logic. Returns (predicted_answer, vote_details).

    attempt_results: list of (answer, confidence, entropy, successful_code)
    """
    answer_weights = defaultdict(float)
    answer_votes = defaultdict(float)

    for answer, confidence, entropy, successful_code in attempt_results:
        if answer is not None:
            if not math.isfinite(entropy) or entropy <= 0:
                entropy = float('inf')
            weight = 1.0 / max(entropy, 1e-9)

            if successful_code == 0:
                weight *= 0.5

            answer_weights[answer] += weight
            if use_confidence:
                answer_votes[answer] += confidence
            else:
                answer_votes[answer] += 1.0  # flat vote

    scored = []
    for answer, total_weight in answer_weights.items():
        scored.append({
            'answer': answer,
            'votes': answer_votes[answer],
            'score': total_weight
        })

    scored.sort(key=lambda x: (x['votes'], x['score'], x['answer']), reverse=True)

    if scored:
        return scored[0]['answer'], scored
    return None, []


# ── Main Analysis ────────────────────────────────────────────────────────────

def analyze_vboxed(logfile: str):
    problems = parse_log(logfile)

    print(f'{"=" * 80}')
    print(f'  VBOXED CHECKPOINT ANALYSIS — {logfile}')
    print(f'{"=" * 80}')
    print()

    # ── Phase 1: Classify every attempt ──────────────────────────────────
    @dataclass
    class AttemptInfo:
        problem_id: str
        attempt_num: int
        answer: Optional[int]
        confidence: float
        source: str
        entropy: float
        temperature: Optional[float]
        expected: Optional[int]
        is_correct: bool
        successful_code: int
        has_both_boxed_and_vboxed: bool
        boxed_answer: Optional[int]
        vboxed_answer: Optional[int]

    all_attempts = []
    total_none = 0

    for p in problems:
        for a in p.attempts:
            full_text = get_attempt_full_text(a)
            answer, confidence, source = extract_answer_like_solver(full_text)

            # Also check if both patterns exist
            boxed_matches = re.findall(r'[\\]boxed\s*\{\s*([0-9,]+)\s*\}', full_text)
            vboxed_matches = re.findall(r'[\\]Vboxed\s*\{\s*([0-9,]+)\s*\}', full_text)

            boxed_answer = None
            if boxed_matches:
                try:
                    v = int(boxed_matches[-1].replace(',', ''))
                    if 0 <= v <= 99999:
                        boxed_answer = v
                except (ValueError, OverflowError):
                    pass

            vboxed_answer = None
            if vboxed_matches:
                try:
                    v = int(vboxed_matches[-1].replace(',', ''))
                    if 0 <= v <= 99999:
                        vboxed_answer = v
                except (ValueError, OverflowError):
                    pass

            # Count successful code calls
            successful_code = sum(1 for t in a.turns if t.code and not t.is_error)

            if answer is None:
                total_none += 1

            info = AttemptInfo(
                problem_id=p.problem_id,
                attempt_num=a.attempt_num,
                answer=answer,
                confidence=confidence,
                source=source,
                entropy=a.entropy,
                temperature=a.temperature,
                expected=p.expected,
                is_correct=(answer is not None and answer == p.expected),
                successful_code=successful_code,
                has_both_boxed_and_vboxed=(boxed_answer is not None and vboxed_answer is not None),
                boxed_answer=boxed_answer,
                vboxed_answer=vboxed_answer,
            )
            all_attempts.append(info)

    # ── Section 1: Overall source breakdown ──────────────────────────────
    print('1. ANSWER SOURCE BREAKDOWN')
    print('-' * 60)

    source_counts = defaultdict(int)
    source_correct = defaultdict(int)
    for ai in all_attempts:
        source_counts[ai.source] += 1
        if ai.is_correct:
            source_correct[ai.source] += 1

    total_attempts = len(all_attempts)
    total_with_answer = sum(1 for a in all_attempts if a.answer is not None)

    print(f'Total attempts: {total_attempts}')
    print(f'  With answer: {total_with_answer}')
    print(f'  None (no answer): {total_none}')
    print()
    print(f'  {"Source":<25} {"Count":>6} {"% of ans":>8} {"Correct":>8} {"Acc%":>8} {"Conf":>6}')
    print(f'  {"─" * 25} {"─" * 6} {"─" * 8} {"─" * 8} {"─" * 8} {"─" * 6}')

    conf_map = {'boxed': 1.0, 'vboxed': 0.7, 'fallback_final_answer': 0.7,
                'fallback_answer_is': 0.7, 'fallback_answer_eq': 0.7,
                'fallback_boxed_latex': 0.5, 'none': 0.0}

    for source in ['boxed', 'vboxed', 'fallback_final_answer', 'fallback_answer_is',
                    'fallback_answer_eq', 'fallback_boxed_latex', 'none']:
        c = source_counts.get(source, 0)
        corr = source_correct.get(source, 0)
        pct = (c / total_with_answer * 100) if total_with_answer and source != 'none' else 0
        acc = (corr / c * 100) if c else 0
        conf = conf_map.get(source, 0)
        if source == 'none':
            pct_str = ''
        else:
            pct_str = f'{pct:>7.1f}%'
        print(f'  {source:<25} {c:>6} {pct_str:>8} {corr:>8} {acc:>7.1f}% {conf:>5.1f}')
    print()

    # ── Section 2: Vboxed-only attempts analysis ─────────────────────────
    print('2. VBOXED-ONLY ATTEMPTS (answer came from Vboxed, not boxed)')
    print('-' * 60)

    vboxed_only = [a for a in all_attempts if a.source == 'vboxed']
    vboxed_correct = [a for a in vboxed_only if a.is_correct]

    print(f'Total Vboxed-only attempts: {len(vboxed_only)}')
    print(f'  Correct: {len(vboxed_correct)}')
    print(f'  Wrong: {len(vboxed_only) - len(vboxed_correct)}')
    if vboxed_only:
        print(f'  Accuracy: {len(vboxed_correct)/len(vboxed_only)*100:.1f}%')
    print()

    if vboxed_only:
        print(f'  {"Problem":<10} {"Att#":>4} {"Answer":>8} {"Expected":>8} {"Correct":>8} {"Temp":>5} {"Entropy":>8}')
        print(f'  {"─" * 10} {"─" * 4} {"─" * 8} {"─" * 8} {"─" * 8} {"─" * 5} {"─" * 8}')
        for a in sorted(vboxed_only, key=lambda x: (x.problem_id, x.attempt_num)):
            corr = 'YES' if a.is_correct else 'NO'
            print(f'  {a.problem_id:<10} {a.attempt_num:>4} {a.answer:>8} {a.expected:>8} {corr:>8} {a.temperature:>5.1f} {a.entropy:>8.3f}')
    print()

    # ── Section 3: "Vboxed saved us" — no boxed but Vboxed caught answer ─
    print('3. VBOXED SAVES: Attempts with no \\boxed but \\Vboxed caught an answer')
    print('-' * 60)

    # These are vboxed-only attempts (source == 'vboxed') — they have Vboxed but no boxed
    saves = [a for a in vboxed_only if a.answer is not None]
    saves_correct = [a for a in saves if a.is_correct]

    print(f'Vboxed rescued {len(saves)} attempts that would have been None without it')
    print(f'  Of those, {len(saves_correct)} were correct answers')
    print(f'  And {len(saves) - len(saves_correct)} were wrong answers')
    print()

    # Also: attempts that have BOTH patterns but different answers
    print('  Attempts with BOTH \\boxed and \\Vboxed:')
    both_attempts = [a for a in all_attempts if a.has_both_boxed_and_vboxed]
    both_agree = [a for a in both_attempts if a.boxed_answer == a.vboxed_answer]
    both_disagree = [a for a in both_attempts if a.boxed_answer != a.vboxed_answer]
    print(f'    Total: {len(both_attempts)}')
    print(f'    Agree (same answer): {len(both_agree)}')
    print(f'    Disagree (different answers): {len(both_disagree)}')
    if both_disagree:
        print()
        print(f'    Disagreements (boxed wins per extraction priority):')
        print(f'    {"Problem":<10} {"Att#":>4} {"boxed":>8} {"Vboxed":>8} {"Expected":>8} {"boxed=?":>8} {"Vboxed=?":>8}')
        print(f'    {"─" * 10} {"─" * 4} {"─" * 8} {"─" * 8} {"─" * 8} {"─" * 8} {"─" * 8}')
        for a in sorted(both_disagree, key=lambda x: (x.problem_id, x.attempt_num)):
            bc = 'CORR' if a.boxed_answer == a.expected else 'WRONG'
            vc = 'CORR' if a.vboxed_answer == a.expected else 'WRONG'
            print(f'    {a.problem_id:<10} {a.attempt_num:>4} {a.boxed_answer:>8} {a.vboxed_answer:>8} {a.expected:>8} {bc:>8} {vc:>8}')
    print()

    # ── Section 4: "Vboxed hurt us" — wrong Vboxed diluting correct votes ─
    print('4. VBOXED HARM: Did wrong Vboxed answers dilute correct votes?')
    print('-' * 60)

    # Group attempts by problem
    problem_attempts = defaultdict(list)
    problem_expected = {}
    for a in all_attempts:
        problem_attempts[a.problem_id].append(a)
        problem_expected[a.problem_id] = a.expected

    harm_cases = []
    for pid, attempts in problem_attempts.items():
        expected = problem_expected[pid]
        if expected is None:
            continue

        # Find Vboxed-sourced attempts that are WRONG
        wrong_vboxed = [a for a in attempts if a.source == 'vboxed' and not a.is_correct and a.answer is not None]
        # Find any correct attempts from any source
        correct_any = [a for a in attempts if a.is_correct]

        if wrong_vboxed and correct_any:
            # Check if the wrong Vboxed answers compete with the correct answer in voting
            harm_cases.append({
                'problem_id': pid,
                'expected': expected,
                'wrong_vboxed': wrong_vboxed,
                'correct_count': len(correct_any),
                'total_attempts': len(attempts),
            })

    if harm_cases:
        print(f'Found {len(harm_cases)} problems with wrong Vboxed + correct answer present:')
        for case in harm_cases:
            print(f'  Problem {case["problem_id"]} (expected={case["expected"]}):')
            print(f'    Correct attempts: {case["correct_count"]}/{case["total_attempts"]}')
            for wv in case['wrong_vboxed']:
                print(f'    Wrong Vboxed: att#{wv.attempt_num} answered {wv.answer} (conf=0.7)')
    else:
        print('No cases found where wrong Vboxed answers competed with correct answers.')
    print()

    # ── Section 5: Did Vboxed change any problem's final voted answer? ───
    print('5. VOTE OUTCOME IMPACT: Does Vboxed change any problem\'s predicted answer?')
    print('-' * 60)

    outcome_changes = []
    for pid, attempts in problem_attempts.items():
        expected = problem_expected[pid]

        # Build attempt data for voting
        attempt_data = []
        for a in attempts:
            attempt_data.append((a.answer, a.confidence, a.entropy, a.successful_code))

        # Vote WITH confidence (as-is)
        pred_with, details_with = simulate_voting(attempt_data, use_confidence=True)

        # Vote WITHOUT confidence (all votes = 1.0)
        pred_without, details_without = simulate_voting(attempt_data, use_confidence=False)

        if pred_with != pred_without:
            outcome_changes.append({
                'problem_id': pid,
                'expected': expected,
                'pred_with_conf': pred_with,
                'pred_without_conf': pred_without,
                'correct_with': pred_with == expected,
                'correct_without': pred_without == expected,
                'votes_with': details_with[:5],
                'votes_without': details_without[:5],
            })

    if outcome_changes:
        print(f'Vboxed confidence weighting CHANGED the outcome of {len(outcome_changes)} problem(s):')
        print()
        for oc in outcome_changes:
            impact = ''
            if oc['correct_with'] and not oc['correct_without']:
                impact = 'VBOXED HELPED (changed wrong -> correct)'
            elif not oc['correct_with'] and oc['correct_without']:
                impact = 'VBOXED HURT (changed correct -> wrong)'
            elif oc['correct_with'] and oc['correct_without']:
                impact = 'NEUTRAL (both correct, different answer)'
            else:
                impact = 'NEUTRAL (both wrong, different answer)'

            print(f'  Problem {oc["problem_id"]} (expected={oc["expected"]}): {impact}')
            print(f'    With confidence:    predicted={oc["pred_with_conf"]} {"CORRECT" if oc["correct_with"] else "WRONG"}')
            print(f'    Without confidence: predicted={oc["pred_without_conf"]} {"CORRECT" if oc["correct_without"] else "WRONG"}')
            print(f'    Votes WITH confidence (top 5):')
            for v in oc['votes_with'][:5]:
                marker = ' <-- expected' if v['answer'] == oc['expected'] else ''
                print(f'      answer={v["answer"]:>6}  votes={v["votes"]:>5.1f}  score={v["score"]:>10.2f}{marker}')
            print(f'    Votes WITHOUT confidence (top 5):')
            for v in oc['votes_without'][:5]:
                marker = ' <-- expected' if v['answer'] == oc['expected'] else ''
                print(f'      answer={v["answer"]:>6}  votes={v["votes"]:>5.1f}  score={v["score"]:>10.2f}{marker}')
            print()
    else:
        print('Vboxed confidence weighting did NOT change any problem\'s final answer.')
        print('(All problems would have the same predicted answer with flat 1.0 votes.)')
    print()

    # ── Section 6: Deeper analysis — Vboxed agreement with final ─────────
    print('6. VBOXED vs BOXED AGREEMENT IN DUAL-SOURCE ATTEMPTS')
    print('-' * 60)

    # For attempts with both boxed AND vboxed, analyze whether vboxed was
    # an early correct checkpoint that boxed then confirmed/overrode
    both_correct_both = 0
    both_correct_boxed_only = 0
    both_correct_vboxed_only = 0
    both_correct_neither = 0

    for a in both_attempts:
        bc = (a.boxed_answer == a.expected)
        vc = (a.vboxed_answer == a.expected)
        if bc and vc:
            both_correct_both += 1
        elif bc:
            both_correct_boxed_only += 1
        elif vc:
            both_correct_vboxed_only += 1
        else:
            both_correct_neither += 1

    print(f'Attempts with BOTH \\boxed and \\Vboxed present: {len(both_attempts)}')
    print(f'  Both correct:           {both_correct_both}')
    print(f'  Only boxed correct:     {both_correct_boxed_only}')
    print(f'  Only Vboxed correct:    {both_correct_vboxed_only}  (model over-verified and lost it)')
    print(f'  Neither correct:        {both_correct_neither}')
    print()

    if both_correct_vboxed_only > 0:
        print('  Cases where Vboxed was RIGHT but boxed was WRONG (model over-verified):')
        print(f'  {"Problem":<10} {"Att#":>4} {"boxed":>8} {"Vboxed":>8} {"Expected":>8}')
        print(f'  {"─" * 10} {"─" * 4} {"─" * 8} {"─" * 8} {"─" * 8}')
        for a in both_attempts:
            if a.vboxed_answer == a.expected and a.boxed_answer != a.expected:
                print(f'  {a.problem_id:<10} {a.attempt_num:>4} {a.boxed_answer:>8} {a.vboxed_answer:>8} {a.expected:>8}')
        print()

    # ── Section 7: Per-problem Vboxed presence summary ───────────────────
    print('7. PER-PROBLEM VBOXED PRESENCE')
    print('-' * 60)

    problems_with_any_vboxed = set()
    for a in all_attempts:
        if a.source == 'vboxed' or a.has_both_boxed_and_vboxed:
            problems_with_any_vboxed.add(a.problem_id)

    # Get problem correctness from the parsed problems
    problem_correct = {p.problem_id: p.correct for p in problems}
    problem_predicted = {p.problem_id: p.predicted for p in problems}

    print(f'Problems with any Vboxed usage: {len(problems_with_any_vboxed)}/{len(problems)}')
    print()
    print(f'  {"Problem":<10} {"Predicted":>9} {"Expected":>9} {"Correct":>8} {"Vboxed-src":>10} {"Both-src":>8} {"Total att":>9}')
    print(f'  {"─" * 10} {"─" * 9} {"─" * 9} {"─" * 8} {"─" * 10} {"─" * 8} {"─" * 9}')

    for pid in sorted(problems_with_any_vboxed):
        atts = problem_attempts[pid]
        vb_src = sum(1 for a in atts if a.source == 'vboxed')
        both_src = sum(1 for a in atts if a.has_both_boxed_and_vboxed)
        corr = 'YES' if problem_correct.get(pid) else 'NO'
        pred = problem_predicted.get(pid, '?')
        exp = problem_expected.get(pid, '?')
        print(f'  {pid:<10} {str(pred):>9} {str(exp):>9} {corr:>8} {vb_src:>10} {both_src:>8} {len(atts):>9}')
    print()

    # ── Section 8: Counterfactual — score without Vboxed feature ─────────
    print('8. COUNTERFACTUAL: What if we removed Vboxed entirely?')
    print('-' * 60)

    # Scenario A: Current (with Vboxed extraction)
    # Scenario B: If Vboxed attempts had None instead (no checkpoint rescue)
    # Scenario C: If Vboxed confidence was 1.0 instead of 0.7

    score_current = sum(1 for p in problems if p.correct)

    # Scenario B: Remove Vboxed extraction (vboxed-only attempts become None)
    score_no_vboxed = 0
    for pid, attempts in problem_attempts.items():
        expected = problem_expected[pid]
        if expected is None:
            continue
        data = []
        for a in attempts:
            if a.source == 'vboxed':
                # This attempt would be None without Vboxed
                data.append((None, 0.0, a.entropy, a.successful_code))
            else:
                data.append((a.answer, a.confidence, a.entropy, a.successful_code))
        pred, _ = simulate_voting(data, use_confidence=True)
        if pred == expected:
            score_no_vboxed += 1

    # Scenario C: Vboxed with confidence 1.0 (same as boxed)
    score_vboxed_full_conf = 0
    for pid, attempts in problem_attempts.items():
        expected = problem_expected[pid]
        if expected is None:
            continue
        data = []
        for a in attempts:
            conf = 1.0 if a.source == 'vboxed' else a.confidence
            data.append((a.answer, conf, a.entropy, a.successful_code))
        pred, _ = simulate_voting(data, use_confidence=True)
        if pred == expected:
            score_vboxed_full_conf += 1

    # Scenario D: All confidence = 1.0 (no confidence weighting at all)
    score_flat = 0
    for pid, attempts in problem_attempts.items():
        expected = problem_expected[pid]
        if expected is None:
            continue
        data = []
        for a in attempts:
            data.append((a.answer, a.confidence, a.entropy, a.successful_code))
        pred, _ = simulate_voting(data, use_confidence=False)
        if pred == expected:
            score_flat += 1

    total_problems = len(problems)
    print(f'  {"Scenario":<50} {"Score":>6} {"Pct":>7}')
    print(f'  {"─" * 50} {"─" * 6} {"─" * 7}')
    print(f'  {"A. Current (Vboxed=0.7, boxed=1.0)":<50} {score_current:>5}/{total_problems} {score_current/total_problems*100:>6.1f}%')
    print(f'  {"B. No Vboxed (vboxed attempts -> None)":<50} {score_no_vboxed:>5}/{total_problems} {score_no_vboxed/total_problems*100:>6.1f}%')
    print(f'  {"C. Vboxed with conf=1.0 (same weight as boxed)":<50} {score_vboxed_full_conf:>5}/{total_problems} {score_vboxed_full_conf/total_problems*100:>6.1f}%')
    print(f'  {"D. All flat votes (all conf=1.0)":<50} {score_flat:>5}/{total_problems} {score_flat/total_problems*100:>6.1f}%')
    print()

    # Show which problems changed
    for scenario_name, scenario_score_fn in [
        ('B (no Vboxed)', lambda pid, atts, exp: simulate_voting(
            [(None if a.source == 'vboxed' else a.answer, 0.0 if a.source == 'vboxed' else a.confidence, a.entropy, a.successful_code) for a in atts],
            use_confidence=True)[0]),
        ('D (flat votes)', lambda pid, atts, exp: simulate_voting(
            [(a.answer, a.confidence, a.entropy, a.successful_code) for a in atts],
            use_confidence=False)[0]),
    ]:
        changes = []
        for pid, atts in problem_attempts.items():
            exp = problem_expected[pid]
            if exp is None:
                continue
            # Current
            data_current = [(a.answer, a.confidence, a.entropy, a.successful_code) for a in atts]
            pred_current, _ = simulate_voting(data_current, use_confidence=True)
            # Scenario
            pred_scenario = scenario_score_fn(pid, atts, exp)
            if pred_current != pred_scenario:
                changes.append({
                    'pid': pid, 'expected': exp,
                    'current': pred_current, 'scenario': pred_scenario,
                    'curr_correct': pred_current == exp,
                    'scen_correct': pred_scenario == exp,
                })
        if changes:
            print(f'  Problems that change in scenario {scenario_name}:')
            for ch in changes:
                arrow = ''
                if ch['curr_correct'] and not ch['scen_correct']:
                    arrow = 'CURRENT BETTER'
                elif not ch['curr_correct'] and ch['scen_correct']:
                    arrow = 'SCENARIO BETTER'
                else:
                    arrow = 'BOTH WRONG' if not ch['curr_correct'] else 'BOTH RIGHT'
                print(f'    {ch["pid"]}: current={ch["current"]} scenario={ch["scenario"]} expected={ch["expected"]} -> {arrow}')
            print()

    # ── Summary ──────────────────────────────────────────────────────────
    print('=' * 80)
    print('  SUMMARY')
    print('=' * 80)
    print()
    print(f'Vboxed checkpoint feature in this run:')
    print(f'  - {len(vboxed_only)} attempts rescued (would have been None without Vboxed)')
    print(f'    - {len(vboxed_correct)} correct, {len(vboxed_only) - len(vboxed_correct)} wrong')
    print(f'  - {len(both_attempts)} attempts had both \\boxed and \\Vboxed')
    print(f'    - {len(both_agree)} agreed, {len(both_disagree)} disagreed')
    print(f'    - {both_correct_vboxed_only} cases where Vboxed was right but boxed was wrong')
    print(f'  - Score impact: current={score_current}/{total_problems}, without Vboxed={score_no_vboxed}/{total_problems}, flat votes={score_flat}/{total_problems}')

    delta_no_vboxed = score_current - score_no_vboxed
    delta_flat = score_current - score_flat

    if delta_no_vboxed > 0:
        print(f'  - Removing Vboxed would LOSE {delta_no_vboxed} problem(s) -> Vboxed is HELPING')
    elif delta_no_vboxed < 0:
        print(f'  - Removing Vboxed would GAIN {-delta_no_vboxed} problem(s) -> Vboxed is HURTING')
    else:
        print(f'  - Removing Vboxed has ZERO score impact -> Vboxed is NEUTRAL on score')

    if delta_flat != 0:
        print(f'  - Confidence weighting (0.7 vs 1.0) changes {abs(delta_flat)} problem(s)')
    else:
        print(f'  - Confidence weighting (0.7 vs 1.0) has NO impact on any problem outcome')

    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Vboxed checkpoint analysis')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    args = parser.parse_args()
    analyze_vboxed(args.logfile)
