#!/usr/bin/env python3
"""
Close Vote & Dodgy Win Analysis for AIMO3
==========================================
Finds problems we got CORRECT but barely — at risk of flipping wrong on the real submission.

Also detects regressions (correct in v23 but wrong in v31) and improvements (vice versa).

Usage:
    python3 log_exploration/close_vote_analysis.py output/v23/diagnostic.log output/v31/diagnostic.log

Outputs:
    data/problem_db/close_votes.json
    Terminal summary of close votes, regressions, and improvements
"""

import sys
import os
import re
import json
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


# ── Full problem text extraction (bypasses 300-char truncation) ──────────────

def extract_full_problem_texts(filepath):
    """Parse diagnostic.log to get full problem texts, keyed by problem_id."""
    texts = {}
    with open(filepath, 'r', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    current_pid = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Match problem header to get ID
        prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
        if prob_match:
            current_pid = prob_match.group(3)
            continue

        # Match problem text line
        if stripped.startswith('Problem:') and current_pid and current_pid not in texts:
            texts[current_pid] = stripped[8:].strip()
            current_pid = None  # Only capture first occurrence

    return texts


# ── Topic classification (reused from wave2_analysis) ────────────────────────

def classify_topic(problem_text):
    """Classify problem into topic based on text content."""
    text = problem_text.lower() if problem_text else ""

    geo_kw = ['triangle', 'circle', 'angle', 'perpendicular', 'tangent', 'inscribed',
              'circumscribed', 'polygon', 'quadrilateral', 'area', 'perimeter',
              'circumcircle', 'incircle', 'midpoint', 'bisector', 'parallel',
              'equilateral', 'hexagon', 'pentagon', 'rectangle', 'square grid',
              'convex', 'diameter', 'chord', 'collinear', 'concyclic', 'observer',
              'lattice point']

    nt_kw = ['divisor', 'prime', 'gcd', 'lcm', 'modulo', 'remainder', 'congruent',
             'coprime', 'factorial', 'divides', 'divisible',
             'digit', 'sum of digits', 'number of positive', 'perfect square',
             'perfect cube', 'norwegian', 'euler', 'fermat', 'complex numbers',
             'root of unity']

    comb_kw = ['permutation', 'ways', 'arrange', 'select', 'choose',
               'subset', 'count', 'board', 'tile', 'domino',
               'coloring', 'colour', 'color', 'path', 'walk', 'game', 'player',
               'coin', 'flip', 'probability', 'expected', 'blackboard',
               'chessboard', 'placement', 'configuration', 'dice', 'maze',
               'marked', 'graph', 'simple graph', 'vertex']

    alg_kw = ['polynomial', 'equation', 'root', 'function', 'inequality',
              'maximum', 'minimum', 'recurrence',
              'real number', 'coefficient', 'degree', 'evaluate',
              'expression', 'formula', 'grid of cells']

    scores = {
        'geometry': sum(1 for kw in geo_kw if kw in text),
        'number_theory': sum(1 for kw in nt_kw if kw in text),
        'combinatorics': sum(1 for kw in comb_kw if kw in text),
        'algebra': sum(1 for kw in alg_kw if kw in text),
    }

    if max(scores.values()) == 0:
        return ['unknown']

    # Return all topics with scores > 0, sorted by score descending
    topics = [t for t, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0]
    return topics if topics else ['unknown']


def detect_skills(problem_text, attempts):
    """Detect mathematical skills required based on problem text and attempt strategies."""
    text = problem_text.lower() if problem_text else ""
    skills = []

    # From problem text
    if any(kw in text for kw in ['modulo', 'remainder', 'mod ', 'congruent']):
        skills.append('modular_arithmetic')
    if any(kw in text for kw in ['probability', 'expected value', 'random']):
        skills.append('probability')
    if any(kw in text for kw in ['sequence', 'recurrence', 'recursive']):
        skills.append('sequences')
    if any(kw in text for kw in ['maximum', 'minimum', 'optimize', 'largest', 'smallest']):
        skills.append('optimization')
    if any(kw in text for kw in ['prove', 'show that', 'find all']):
        skills.append('proof_construction')
    if any(kw in text for kw in ['grid', 'board', 'tile', 'chess']):
        skills.append('grid_reasoning')
    if any(kw in text for kw in ['how many', 'number of', 'count']):
        skills.append('counting')
    if any(kw in text for kw in ['polynomial', 'equation', 'solve']):
        skills.append('equation_solving')
    if any(kw in text for kw in ['triangle', 'circle', 'angle']):
        skills.append('geometric_reasoning')
    if any(kw in text for kw in ['digit', 'integer', 'divisor']):
        skills.append('number_properties')

    # From attempt code
    for att in attempts:
        for turn in att.turns:
            code = (turn.code or '').lower()
            if 'sympy' in code:
                skills.append('symbolic_computation')
            if 'itertools' in code or 'brute' in code:
                skills.append('brute_force_search')
            if 'numpy' in code or 'scipy' in code:
                skills.append('numerical_methods')

    return list(set(skills))


# ── Core analysis ────────────────────────────────────────────────────────────

def analyze_close_votes(problems, full_texts, version, margin_threshold=4):
    """Find problems that are correct but with dangerously close vote margins."""
    close_votes = []

    for p in problems:
        if not p.correct:
            continue
        if not p.votes:
            continue

        total_attempts = len(p.attempts)
        if total_attempts == 0:
            continue

        # Sort votes by count, descending
        sorted_votes = sorted(p.votes.items(), key=lambda x: -x[1])

        # The winning answer (should be the correct one)
        winning_answer = sorted_votes[0][0]
        winning_count = sorted_votes[0][1]

        # Runner up
        runner_up_count = sorted_votes[1][1] if len(sorted_votes) > 1 else 0
        runner_up_answer = sorted_votes[1][0] if len(sorted_votes) > 1 else None

        # Vote margin
        margin = winning_count - runner_up_count

        # Count None attempts
        none_count = sum(1 for a in p.attempts if a.answer is None or a.is_none)

        # Count attempts that voted for the correct answer
        correct_attempts = sum(1 for a in p.attempts if a.answer == p.expected)

        # Count non-None attempts that voted for a WRONG answer
        wrong_vote_count = sum(1 for a in p.attempts if a.answer is not None and a.answer != p.expected)

        # A "close vote" means there are actual competing wrong answers
        # Not just "lots of Nones but unanimous among those who answered"
        has_competing_wrong = wrong_vote_count >= 1 and margin <= margin_threshold
        # Also flag if correct answers are < 50% of non-None answers AND there are wrong answers
        non_none_total = correct_attempts + wrong_vote_count
        is_low_rate_with_competition = (non_none_total > 0 and
                                         correct_attempts / non_none_total < 0.6 and
                                         wrong_vote_count >= 2)

        if not has_competing_wrong and not is_low_rate_with_competition:
            continue

        # Build vote distribution dict
        vote_dist = {}
        for ans, count in sorted_votes:
            key = str(ans) if ans is not None else "None"
            vote_dist[key] = count

        # Get full problem text
        full_text = full_texts.get(p.problem_id, p.problem_text)

        # Determine risk level
        # Key insight: a problem with 5 correct, 0 wrong, 11 None is NOT really at risk
        # A problem with 5 correct, 4 wrong is very much at risk
        if margin <= 2 and wrong_vote_count >= 2:
            risk = "critical"
        elif margin <= 2:
            risk = "high"
        elif margin <= 4 and wrong_vote_count >= 2:
            risk = "high"
        elif margin <= 4:
            risk = "medium"
        elif is_low_rate_with_competition:
            risk = "high"
        else:
            risk = "medium"

        # Analyze what wrong attempts did differently
        wrong_analysis = analyze_wrong_attempts(p)

        topics = classify_topic(full_text)
        skills = detect_skills(full_text, p.attempts)

        entry = {
            "problem_id": p.problem_id,
            "question": full_text,
            "expected_answer": p.expected,
            "topics": topics,
            "skills": ", ".join(skills) if skills else "unknown",
            "vote_margin": margin,
            "vote_distribution": vote_dist,
            "correct_rate": f"{correct_attempts}/{total_attempts}",
            "none_count": none_count,
            "risk_level": risk,
            "why_close": wrong_analysis,
            "version": version,
            "batch": p.batch_name,
            "wall_time_s": round(p.wall_time, 1),
        }

        close_votes.append(entry)

    return sorted(close_votes, key=lambda x: x["vote_margin"])


def analyze_wrong_attempts(problem):
    """Analyze what wrong attempts did differently to explain why the vote is close."""
    p = problem
    reasons = []

    correct_answers = []
    wrong_answers = defaultdict(list)
    none_attempts = []

    for a in p.attempts:
        if a.answer is not None and a.answer == p.expected:
            correct_answers.append(a)
        elif a.answer is not None:
            wrong_answers[a.answer].append(a)
        else:
            none_attempts.append(a)

    total = len(p.attempts)

    # Check for off-by-one
    if p.expected is not None:
        for wrong_ans in wrong_answers:
            if abs(wrong_ans - p.expected) == 1:
                reasons.append(f"Off-by-one risk: {wrong_answers[wrong_ans].__len__()} attempts got {wrong_ans} instead of {p.expected}")
            elif abs(wrong_ans - p.expected) <= 10:
                reasons.append(f"Close numeric: {len(wrong_answers[wrong_ans])} attempts got {wrong_ans} (diff={wrong_ans - p.expected})")

    # Check if many Nones (extraction failures)
    if len(none_attempts) > total * 0.3:
        reasons.append(f"High None rate: {len(none_attempts)}/{total} attempts produced no answer")

    # Check if many different wrong answers (model is confused)
    if len(wrong_answers) >= 3:
        reasons.append(f"High disagreement: {len(wrong_answers)} different wrong answers produced")

    # Check if wrong attempts had more errors
    correct_errors = [a.errors for a in correct_answers]
    wrong_errors = []
    for attempts_list in wrong_answers.values():
        wrong_errors.extend(a.errors for a in attempts_list)

    if correct_errors and wrong_errors:
        avg_correct_err = sum(correct_errors) / len(correct_errors)
        avg_wrong_err = sum(wrong_errors) / len(wrong_errors)
        if avg_wrong_err > avg_correct_err * 2:
            reasons.append(f"Wrong attempts had {avg_wrong_err:.1f}x more errors on average")

    # Check temperature correlation
    correct_temps = [a.temperature for a in correct_answers if a.temperature is not None]
    wrong_temps = []
    for attempts_list in wrong_answers.values():
        wrong_temps.extend(a.temperature for a in attempts_list if a.temperature is not None)

    if correct_temps and wrong_temps:
        avg_correct_temp = sum(correct_temps) / len(correct_temps)
        avg_wrong_temp = sum(wrong_temps) / len(wrong_temps)
        if abs(avg_correct_temp - avg_wrong_temp) > 0.15:
            reasons.append(f"Temperature sensitive: correct avg temp={avg_correct_temp:.2f}, wrong avg={avg_wrong_temp:.2f}")

    # Summarize the top wrong answer
    if wrong_answers:
        top_wrong = max(wrong_answers.items(), key=lambda x: len(x[1]))
        reasons.append(f"Top wrong answer: {top_wrong[0]} ({len(top_wrong[1])} attempts)")

    if not reasons:
        reasons.append("Marginal majority — model barely favors correct answer")

    return "; ".join(reasons)


# ── Cross-version comparison ─────────────────────────────────────────────────

def find_regressions_and_improvements(problems_v23, problems_v31):
    """Find problems that flipped between correct/wrong across versions."""
    v23_results = {p.problem_id: p for p in problems_v23}
    v31_results = {p.problem_id: p for p in problems_v31}

    common_ids = set(v23_results.keys()) & set(v31_results.keys())

    regressions = []    # Correct in v23, wrong in v31
    improvements = []   # Wrong in v23, correct in v31

    for pid in sorted(common_ids):
        p23 = v23_results[pid]
        p31 = v31_results[pid]

        if p23.correct and not p31.correct:
            regressions.append({
                "problem_id": pid,
                "expected": p23.expected,
                "v23_predicted": p23.predicted,
                "v31_predicted": p31.predicted,
                "v23_votes": dict(sorted(p23.votes.items(), key=lambda x: -x[1])),
                "v31_votes": dict(sorted(p31.votes.items(), key=lambda x: -x[1])),
                "v23_correct_count": sum(1 for a in p23.attempts if a.answer == p23.expected),
                "v31_correct_count": sum(1 for a in p31.attempts if a.answer == p31.expected),
                "batch_v23": p23.batch_name,
                "batch_v31": p31.batch_name,
                "question_snippet": p23.problem_text[:200],
            })
        elif not p23.correct and p31.correct:
            improvements.append({
                "problem_id": pid,
                "expected": p23.expected,
                "v23_predicted": p23.predicted,
                "v31_predicted": p31.predicted,
                "v23_votes": dict(sorted(p23.votes.items(), key=lambda x: -x[1])),
                "v31_votes": dict(sorted(p31.votes.items(), key=lambda x: -x[1])),
                "v23_correct_count": sum(1 for a in p23.attempts if a.answer == p23.expected),
                "v31_correct_count": sum(1 for a in p31.attempts if a.answer == p31.expected),
                "batch_v23": p23.batch_name,
                "batch_v31": p31.batch_name,
                "question_snippet": p23.problem_text[:200],
            })

    return regressions, improvements


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 log_exploration/close_vote_analysis.py <v23_log> <v31_log>")
        sys.exit(1)

    v23_log = sys.argv[1]
    v31_log = sys.argv[2]

    print("Parsing v23 log...")
    problems_v23 = parse_log(v23_log)
    print(f"  Parsed {len(problems_v23)} problems from v23")

    print("Parsing v31 log...")
    problems_v31 = parse_log(v31_log)
    print(f"  Parsed {len(problems_v31)} problems from v31")

    # Extract full problem texts
    print("Extracting full problem texts...")
    full_texts_v23 = extract_full_problem_texts(v23_log)
    full_texts_v31 = extract_full_problem_texts(v31_log)
    # Merge (v31 texts override v23 if different)
    all_full_texts = {**full_texts_v23, **full_texts_v31}

    # ── Close vote analysis ──
    print("\n" + "="*80)
    print("CLOSE VOTE ANALYSIS")
    print("="*80)

    close_v23 = analyze_close_votes(problems_v23, all_full_texts, "v23", margin_threshold=4)
    close_v31 = analyze_close_votes(problems_v31, all_full_texts, "v31", margin_threshold=4)

    print(f"\nv23: {len(close_v23)} close-vote correct problems (out of {sum(1 for p in problems_v23 if p.correct)} correct)")
    print(f"v31: {len(close_v31)} close-vote correct problems (out of {sum(1 for p in problems_v31 if p.correct)} correct)")

    # Print details
    for label, close_list in [("v23", close_v23), ("v31", close_v31)]:
        if close_list:
            print(f"\n--- {label} Close Votes ---")
            for entry in close_list:
                print(f"\n  [{entry['risk_level'].upper()}] Problem {entry['problem_id']} ({entry['batch']})")
                print(f"    Expected: {entry['expected_answer']}")
                print(f"    Votes: {entry['vote_distribution']}")
                print(f"    Margin: {entry['vote_margin']} | Correct rate: {entry['correct_rate']}")
                print(f"    Topics: {', '.join(entry['topics'])}")
                print(f"    Why close: {entry['why_close']}")
                print(f"    Question: {entry['question'][:150]}...")

    # ── Regressions & improvements ──
    print("\n" + "="*80)
    print("REGRESSIONS & IMPROVEMENTS (v23 -> v31)")
    print("="*80)

    regressions, improvements = find_regressions_and_improvements(problems_v23, problems_v31)

    print(f"\nRegressions (correct in v23, WRONG in v31): {len(regressions)}")
    for r in regressions:
        print(f"  Problem {r['problem_id']}: expected={r['expected']}")
        print(f"    v23: predicted={r['v23_predicted']} votes={r['v23_votes']} correct_count={r['v23_correct_count']}")
        print(f"    v31: predicted={r['v31_predicted']} votes={r['v31_votes']} correct_count={r['v31_correct_count']}")
        print(f"    Question: {r['question_snippet'][:120]}...")

    print(f"\nImprovements (wrong in v23, CORRECT in v31): {len(improvements)}")
    for imp in improvements:
        print(f"  Problem {imp['problem_id']}: expected={imp['expected']}")
        print(f"    v23: predicted={imp['v23_predicted']} votes={imp['v23_votes']} correct_count={imp['v23_correct_count']}")
        print(f"    v31: predicted={imp['v31_predicted']} votes={imp['v31_votes']} correct_count={imp['v31_correct_count']}")
        print(f"    Question: {imp['question_snippet'][:120]}...")

    # ── Also check: problems that were close in BOTH versions ──
    print("\n" + "="*80)
    print("PROBLEMS CLOSE IN BOTH VERSIONS")
    print("="*80)

    close_v23_ids = {e['problem_id'] for e in close_v23}
    close_v31_ids = {e['problem_id'] for e in close_v31}
    both_close = close_v23_ids & close_v31_ids

    if both_close:
        print(f"\n{len(both_close)} problems are close votes in BOTH v23 and v31:")
        for pid in sorted(both_close):
            e23 = next(e for e in close_v23 if e['problem_id'] == pid)
            e31 = next(e for e in close_v31 if e['problem_id'] == pid)
            print(f"  {pid}: v23 margin={e23['vote_margin']} rate={e23['correct_rate']} | v31 margin={e31['vote_margin']} rate={e31['correct_rate']}")
    else:
        print("\n  No problems are close in both versions.")

    # ── Build combined output ──
    all_close = close_v23 + close_v31

    # Deduplicate: if a problem appears in both, keep both entries (different version data)
    # but also add a flag
    seen_pids = Counter(e['problem_id'] for e in all_close)
    for entry in all_close:
        entry['appears_in_both_versions'] = seen_pids[entry['problem_id']] > 1

    # Add regression info
    regression_pids = {r['problem_id'] for r in regressions}
    improvement_pids = {i['problem_id'] for i in improvements}

    for entry in all_close:
        if entry['problem_id'] in regression_pids:
            entry['cross_version_status'] = 'REGRESSION (correct in v23, wrong in v31)'
        elif entry['problem_id'] in improvement_pids:
            entry['cross_version_status'] = 'IMPROVEMENT (wrong in v23, correct in v31)'
        else:
            entry['cross_version_status'] = 'stable'

    # Add regressions to output even if they weren't close votes
    output_data = {
        "close_votes": all_close,
        "regressions": regressions,
        "improvements": improvements,
        "summary": {
            "v23_total": len(problems_v23),
            "v23_correct": sum(1 for p in problems_v23 if p.correct),
            "v23_close_vote_count": len(close_v23),
            "v31_total": len(problems_v31),
            "v31_correct": sum(1 for p in problems_v31 if p.correct),
            "v31_close_vote_count": len(close_v31),
            "regressions_count": len(regressions),
            "improvements_count": len(improvements),
            "both_close_count": len(both_close),
        }
    }

    # Write output
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'data', 'problem_db', 'close_votes.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"Written to {out_path}")
    print(f"  {len(all_close)} close-vote entries")
    print(f"  {len(regressions)} regressions")
    print(f"  {len(improvements)} improvements")

    # ── Final summary table ──
    print(f"\n{'='*80}")
    print("RISK SUMMARY")
    print("="*80)
    risk_counts = Counter(e['risk_level'] for e in all_close)
    for risk in ['critical', 'high', 'medium']:
        print(f"  {risk.upper():10s}: {risk_counts.get(risk, 0)} problems")

    print(f"\n  Total at-risk correct problems: {len(all_close)}")
    print(f"  Already-regressed (v23->v31):   {len(regressions)}")


if __name__ == '__main__':
    main()
