#!/usr/bin/env python3
"""
Deep Extraction Failure Analysis for v31
==========================================
For each None attempt, searches reasoning text and code output for patterns
that look like answers. Determines:
  - How many Nones had a recoverable answer vs truly no answer
  - What the answer text looked like (context around it)
  - Groups by failure mode: regex miss, model never stated answer, timeout, code error cascade
  - Simulates vote impact: would recovered answers have changed problem outcomes?

Usage: python3 log_exploration/extraction_deep_v31.py output/v31/diagnostic.log
"""

import sys
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, '/Users/intern/Desktop/sideprojects/aimo3')
from log_exploration.log_query import parse_log


# ── Extraction patterns ordered by reliability ──────────────────────────────

EXTRACTION_PATTERNS = [
    # High confidence: explicit answer markers
    ("boxed_standard",      r'\\boxed\s*\{\s*([0-9,]+)\s*\}',                          "high"),
    ("Vboxed",              r'\\Vboxed\s*\{\s*([0-9,]+)\s*\}',                          "high"),
    ("boxed_latex",         r'\\boxed\s*\{[^}]*?(\d{1,5})[^}]*\}',                     "high"),
    ("final_answer_is",     r'final\s+answer\s+is\s*:?\s*\*?\*?\s*(\d{1,5})',           "high"),
    ("answer_is",           r'(?:the\s+)?answer\s+is\s*:?\s*\*?\*?\s*(\d{1,5})',        "high"),
    ("answer_eq",           r'answer\s*[:=]\s*\*?\*?\s*(\d{1,5})',                      "high"),

    # Medium confidence: result/solution statements
    ("result_is",           r'(?:the\s+)?result\s+(?:is|equals?)\s*:?\s*(\d{1,5})',     "medium"),
    ("solution_is",         r'(?:the\s+)?solution\s+is\s*:?\s*(\d{1,5})',               "medium"),
    ("value_is",            r'(?:the\s+)?value\s+(?:is|equals?)\s*:?\s*(\d{1,5})',      "medium"),
    ("output_is",           r'(?:the\s+)?output\s+is\s*:?\s*(\d{1,5})',                 "medium"),
    ("k_min_eq",            r'k_{\s*\\?min\s*}\s*=\s*(\d{1,5})',                        "medium"),

    # Medium confidence: conclusion keywords
    ("therefore_N",         r'(?:therefore|thus|hence|so),?\s+(?:the\s+)?(?:answer|result|value|solution|total|sum|number|count|minimum|maximum)\s+(?:is|=|equals?)\s*(\d{1,5})', "medium"),

    # Low confidence: weaker signals
    ("we_get_N",            r'(?:we\s+(?:get|find|obtain|have|compute|calculate))\s+(?:that\s+)?(?:the\s+)?(?:answer|result|value)?\s*(?:is\s+|=\s*)?(\d{1,5})', "low"),
    ("equals_N",            r'(?:equals?|=)\s+(\d{1,5})\s*[.\n$]',                     "low"),
    ("print_N",             r'print\s*\(\s*(\d{1,5})\s*\)',                             "low"),
    ("bare_number_line",    r'(?:^|\n)\s*(\d{1,5})\s*(?:\n|$)',                         "low"),
]


@dataclass
class NoneAnalysis:
    problem_id: str
    attempt_num: int
    expected: Optional[int]
    failure_mode: str           # regex_miss, no_answer, timeout, code_error_cascade, code_no_output
    recoverable: bool
    recovered_answer: Optional[int]
    recovered_correct: bool
    recovery_pattern: Optional[str]
    recovery_confidence: Optional[str]
    context_snippet: str        # first 200 chars around the matched answer
    turns: int
    errors: int
    has_reasoning: bool
    has_code: bool
    has_output: bool


def get_full_text(attempt):
    """Get all reasoning + code + output concatenated."""
    parts = []
    for t in attempt.turns:
        if t.reasoning_text:
            parts.append(t.reasoning_text)
        if t.code:
            parts.append(t.code)
        if t.output:
            parts.append(t.output)
    return "\n".join(parts)


def get_full_reasoning(attempt):
    return "\n".join(t.reasoning_text for t in attempt.turns if t.reasoning_text)


def get_full_output(attempt):
    return "\n".join(t.output for t in attempt.turns if t.output)


def try_extract_number(val_str):
    """Try to parse a number from a string, same logic as the notebook."""
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


def extract_with_context(text, pattern_name, pattern_regex, confidence):
    """Search text for pattern, return (number, context_snippet, pattern_name, confidence) or None."""
    matches = list(re.finditer(pattern_regex, text, re.IGNORECASE | re.MULTILINE))
    if not matches:
        return None

    # Take last match (most likely to be final answer)
    match = matches[-1]
    val_str = match.group(1)
    num = try_extract_number(val_str)
    if num is None:
        return None

    # Extract context: 100 chars before and after
    start = max(0, match.start() - 100)
    end = min(len(text), match.end() + 100)
    snippet = text[start:end].replace('\n', ' ').strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return num, snippet[:200], pattern_name, confidence


def classify_failure_mode(attempt, found_answer):
    """Determine WHY extraction failed."""
    full_output = get_full_output(attempt)
    full_reasoning = get_full_reasoning(attempt)

    if not attempt.turns:
        return "no_turns"

    # Check timeout
    if "timed out" in full_output.lower() or "timeout" in full_output.lower():
        if not found_answer:
            return "timeout_no_answer"
        else:
            return "timeout_had_answer"

    # Check code error cascade (all code turns errored)
    code_turns = [t for t in attempt.turns if t.code]
    if code_turns and all(t.is_error for t in code_turns):
        if not found_answer:
            return "code_error_cascade_no_answer"
        else:
            return "code_error_cascade_had_answer"

    # Check last turn error
    if attempt.turns[-1].is_error:
        if not found_answer:
            return "last_turn_error_no_answer"
        else:
            return "last_turn_error_had_answer"

    # No code at all
    if all(not t.code for t in attempt.turns):
        if not found_answer:
            return "pure_reasoning_no_answer"
        else:
            return "pure_reasoning_had_answer"

    # Code produced no output
    if code_turns and not any(t.output.strip() for t in code_turns if t.output):
        if not found_answer:
            return "code_no_output_no_answer"
        else:
            return "code_no_output_had_answer"

    # If we found an answer, the extraction regex missed it
    if found_answer:
        return "regex_miss"

    # Model ran code but never stated a clear answer
    return "model_never_stated_answer"


def analyze_nones(problems):
    """Analyze all None attempts."""
    results = []

    for p in problems:
        for a in p.attempts:
            if not a.is_none:
                continue

            full_text = get_full_text(a)
            has_reasoning = any(t.reasoning_text for t in a.turns)
            has_code = any(t.code for t in a.turns)
            has_output = any(t.output for t in a.turns if t.output and t.output.strip())

            # Try all extraction patterns
            best_recovery = None
            for pname, pregex, pconf in EXTRACTION_PATTERNS:
                result = extract_with_context(full_text, pname, pregex, pconf)
                if result:
                    num, snippet, matched_pattern, conf = result
                    # Keep the highest confidence match
                    if best_recovery is None or \
                       (conf == "high" and best_recovery[3] != "high") or \
                       (conf == "medium" and best_recovery[3] == "low"):
                        best_recovery = (num, snippet, matched_pattern, conf)

            recovered_answer = best_recovery[0] if best_recovery else None
            recovered_correct = (recovered_answer == p.expected) if (recovered_answer is not None and p.expected is not None) else False
            failure_mode = classify_failure_mode(a, recovered_answer is not None)

            results.append(NoneAnalysis(
                problem_id=p.problem_id,
                attempt_num=a.attempt_num,
                expected=p.expected,
                failure_mode=failure_mode,
                recoverable=recovered_answer is not None,
                recovered_answer=recovered_answer,
                recovered_correct=recovered_correct,
                recovery_pattern=best_recovery[2] if best_recovery else None,
                recovery_confidence=best_recovery[3] if best_recovery else None,
                context_snippet=best_recovery[1] if best_recovery else "",
                turns=len(a.turns),
                errors=a.errors,
                has_reasoning=has_reasoning,
                has_code=has_code,
                has_output=has_output,
            ))

    return results


def print_summary(results, problems):
    """High-level summary."""
    print("=" * 90)
    print("EXTRACTION DEEP DIVE — v31")
    print("=" * 90)

    total_nones = len(results)
    total_attempts = sum(len(p.attempts) for p in problems)
    recoverable = [r for r in results if r.recoverable]
    recoverable_correct = [r for r in results if r.recovered_correct]

    print(f"\n  Total attempts: {total_attempts}")
    print(f"  Total Nones: {total_nones} ({total_nones/total_attempts*100:.1f}%)")
    print(f"  Recoverable (answer found in text): {len(recoverable)} ({len(recoverable)/total_nones*100:.1f}% of Nones)")
    print(f"    Would be CORRECT: {len(recoverable_correct)} ({len(recoverable_correct)/total_nones*100:.1f}% of Nones)")
    print(f"    Would be WRONG: {len(recoverable) - len(recoverable_correct)} ({(len(recoverable)-len(recoverable_correct))/total_nones*100:.1f}% of Nones)")
    print(f"  Truly unrecoverable: {total_nones - len(recoverable)} ({(total_nones-len(recoverable))/total_nones*100:.1f}% of Nones)")


def print_failure_modes(results):
    """Group by failure mode."""
    print("\n" + "=" * 90)
    print("FAILURE MODE BREAKDOWN")
    print("=" * 90)

    mode_counts = Counter(r.failure_mode for r in results)
    mode_correct = Counter(r.failure_mode for r in results if r.recovered_correct)

    print(f"\n  {'Failure Mode':<40} {'Count':>6} {'%':>7} {'Correct if recovered':>20}")
    print("  " + "-" * 75)

    for mode, count in mode_counts.most_common():
        correct = mode_correct.get(mode, 0)
        pct = count / len(results) * 100
        corr_str = f"{correct}" if correct > 0 else "-"
        print(f"  {mode:<40} {count:>6} {pct:>6.1f}% {corr_str:>20}")


def print_recovery_patterns(results):
    """Which patterns would have recovered answers?"""
    print("\n" + "=" * 90)
    print("RECOVERY PATTERN ANALYSIS")
    print("=" * 90)

    pattern_counts = Counter()
    pattern_correct = Counter()
    conf_counts = Counter()

    for r in results:
        if r.recoverable:
            pattern_counts[r.recovery_pattern] += 1
            conf_counts[r.recovery_confidence] += 1
            if r.recovered_correct:
                pattern_correct[r.recovery_pattern] += 1

    print(f"\n  By pattern (which regex would have caught it):")
    print(f"  {'Pattern':<30} {'Found':>6} {'Correct':>8} {'Wrong':>6}")
    print("  " + "-" * 55)

    for pat, count in pattern_counts.most_common():
        correct = pattern_correct.get(pat, 0)
        wrong = count - correct
        print(f"  {pat:<30} {count:>6} {correct:>8} {wrong:>6}")

    print(f"\n  By confidence level:")
    for conf in ["high", "medium", "low"]:
        count = conf_counts.get(conf, 0)
        if count > 0:
            correct = sum(1 for r in results if r.recovery_confidence == conf and r.recovered_correct)
            print(f"    {conf:<10}: {count} recoverable, {correct} correct")

    # Which high-confidence patterns are NOT in the current extraction?
    print(f"\n  PATTERNS NOT IN CURRENT NOTEBOOK EXTRACTION:")
    current_patterns = {"boxed_standard", "Vboxed", "boxed_latex", "final_answer_is", "answer_is", "answer_eq"}
    missing = {pat for pat in pattern_counts if pat not in current_patterns}
    for pat in sorted(missing):
        count = pattern_counts[pat]
        correct = pattern_correct.get(pat, 0)
        print(f"    {pat}: {count} recoverable ({correct} correct) -- NOT IN NOTEBOOK")


def print_context_samples(results):
    """Show actual text around where answers were found."""
    print("\n" + "=" * 90)
    print("RECOVERABLE ANSWER SAMPLES (context around detected answer)")
    print("=" * 90)

    # Separate correct vs wrong recoveries
    correct_recoveries = [r for r in results if r.recovered_correct]
    wrong_recoveries = [r for r in results if r.recoverable and not r.recovered_correct]

    print(f"\n  --- CORRECT answers we missed ({len(correct_recoveries)} total) ---")
    for r in correct_recoveries[:20]:
        print(f"\n  Problem {r.problem_id} Att {r.attempt_num} | Expected={r.expected} | Found={r.recovered_answer} | Pattern={r.recovery_pattern} [{r.recovery_confidence}]")
        print(f"  Mode: {r.failure_mode} | Turns={r.turns} Errors={r.errors}")
        print(f"  Context: {r.context_snippet[:200]}")

    print(f"\n  --- WRONG answers we would have recovered ({len(wrong_recoveries)} total, showing 15) ---")
    for r in wrong_recoveries[:15]:
        print(f"\n  Problem {r.problem_id} Att {r.attempt_num} | Expected={r.expected} | Found={r.recovered_answer} | Pattern={r.recovery_pattern} [{r.recovery_confidence}]")
        print(f"  Mode: {r.failure_mode} | Turns={r.turns} Errors={r.errors}")
        print(f"  Context: {r.context_snippet[:200]}")

    # Show truly unrecoverable
    unrecoverable = [r for r in results if not r.recoverable]
    print(f"\n  --- TRULY UNRECOVERABLE ({len(unrecoverable)} total, showing 10) ---")
    for r in unrecoverable[:10]:
        print(f"\n  Problem {r.problem_id} Att {r.attempt_num} | Expected={r.expected}")
        print(f"  Mode: {r.failure_mode} | Turns={r.turns} Errors={r.errors}")
        print(f"  Has reasoning={r.has_reasoning} code={r.has_code} output={r.has_output}")


def print_vote_impact(results, problems):
    """Simulate: if we recovered these answers, would vote outcomes change?"""
    print("\n" + "=" * 90)
    print("VOTE IMPACT SIMULATION")
    print("=" * 90)
    print("  Question: If we had recovered these answers, which problems would flip?")

    # Build per-problem recovery map
    problem_recoveries = defaultdict(list)
    for r in results:
        if r.recoverable:
            problem_recoveries[r.problem_id].append(r)

    problems_by_id = {}
    for p in problems:
        # Handle duplicate problem IDs (same problem in different batches)
        key = p.problem_id
        if key in problems_by_id:
            key = f"{p.problem_id}_{p.batch_idx}"
        problems_by_id[key] = p

    flipped_problems = []
    improved_margin = []
    worsened_margin = []

    for p in problems:
        pid = p.problem_id
        if pid not in problem_recoveries:
            continue

        # Current votes
        current_votes = dict(p.votes)  # copy
        current_winner = max(current_votes, key=current_votes.get) if current_votes else None

        # Add recovered answers
        new_votes = dict(current_votes)
        for r in problem_recoveries[pid]:
            if r.recovered_answer is not None:
                new_votes[r.recovered_answer] = new_votes.get(r.recovered_answer, 0) + 1

        new_winner = max(new_votes, key=new_votes.get) if new_votes else None

        # Check if outcome changes
        currently_correct = p.correct
        would_be_correct = (new_winner == p.expected) if (new_winner is not None and p.expected is not None) else False

        n_recovered = len(problem_recoveries[pid])
        n_correct_recovered = sum(1 for r in problem_recoveries[pid] if r.recovered_correct)
        n_wrong_recovered = n_recovered - n_correct_recovered

        if not currently_correct and would_be_correct:
            flipped_problems.append({
                "pid": pid,
                "expected": p.expected,
                "old_winner": current_winner,
                "new_winner": new_winner,
                "old_votes": current_votes,
                "new_votes": new_votes,
                "n_recovered": n_recovered,
                "n_correct": n_correct_recovered,
            })
        elif currently_correct and not would_be_correct:
            worsened_margin.append({
                "pid": pid,
                "expected": p.expected,
                "old_winner": current_winner,
                "new_winner": new_winner,
                "old_votes": current_votes,
                "new_votes": new_votes,
                "n_recovered": n_recovered,
                "n_correct": n_correct_recovered,
                "n_wrong": n_wrong_recovered,
            })
        elif currently_correct and would_be_correct:
            # Check if margin improved or stayed
            old_margin = current_votes.get(p.expected, 0) - max(
                (v for k, v in current_votes.items() if k != p.expected), default=0)
            new_margin = new_votes.get(p.expected, 0) - max(
                (v for k, v in new_votes.items() if k != p.expected), default=0)
            if new_margin > old_margin:
                improved_margin.append({
                    "pid": pid,
                    "old_margin": old_margin,
                    "new_margin": new_margin,
                    "n_correct": n_correct_recovered,
                })

    print(f"\n  Problems with recoverable Nones: {len(problem_recoveries)}")
    print(f"\n  WOULD FLIP TO CORRECT: {len(flipped_problems)}")
    for f in flipped_problems:
        old_v = ", ".join(f"{k}:{v}" for k, v in sorted(f['old_votes'].items(), key=lambda x: -x[1]))
        new_v = ", ".join(f"{k}:{v}" for k, v in sorted(f['new_votes'].items(), key=lambda x: -x[1]))
        print(f"    {f['pid']}: expected={f['expected']}, old winner={f['old_winner']}, new winner={f['new_winner']}")
        print(f"      Old votes: [{old_v}]")
        print(f"      New votes: [{new_v}]")
        print(f"      Recovered: {f['n_recovered']} attempts ({f['n_correct']} correct)")

    print(f"\n  WOULD FLIP TO WRONG (regression!): {len(worsened_margin)}")
    for w in worsened_margin:
        old_v = ", ".join(f"{k}:{v}" for k, v in sorted(w['old_votes'].items(), key=lambda x: -x[1]))
        new_v = ", ".join(f"{k}:{v}" for k, v in sorted(w['new_votes'].items(), key=lambda x: -x[1]))
        print(f"    {w['pid']}: expected={w['expected']}, was correct, now winner={w['new_winner']}")
        print(f"      Old votes: [{old_v}]")
        print(f"      New votes: [{new_v}]")
        print(f"      Recovered: {w['n_recovered']} ({w['n_correct']} correct, {w['n_wrong']} wrong)")

    print(f"\n  IMPROVED MARGIN (already correct, stronger): {len(improved_margin)}")
    for m in improved_margin[:10]:
        print(f"    {m['pid']}: margin {m['old_margin']} -> {m['new_margin']} (+{m['new_margin']-m['old_margin']}, {m['n_correct']} correct recovered)")

    # Net score impact
    net_change = len(flipped_problems) - len(worsened_margin)
    current_score = sum(1 for p in problems if p.correct)
    print(f"\n  NET SCORE IMPACT: {current_score}/53 -> {current_score + net_change}/53 ({'+' if net_change >= 0 else ''}{net_change})")
    if net_change > 0:
        print(f"  CONCLUSION: Better extraction would gain {net_change} problem(s)")
    elif net_change < 0:
        print(f"  CONCLUSION: Naive recovery would LOSE {-net_change} problem(s) — wrong answers outvote correct ones")
    else:
        print(f"  CONCLUSION: No net score change from extraction recovery")


def print_high_conf_only_impact(results, problems):
    """Same vote simulation but only with high-confidence recoveries."""
    print("\n" + "=" * 90)
    print("HIGH-CONFIDENCE-ONLY VOTE IMPACT")
    print("=" * 90)
    print("  Only recovering answers matched by high-confidence patterns")
    print("  (boxed, Vboxed, final_answer_is, answer_is, answer_eq)")

    problem_recoveries = defaultdict(list)
    for r in results:
        if r.recoverable and r.recovery_confidence == "high":
            problem_recoveries[r.problem_id].append(r)

    if not problem_recoveries:
        print("\n  No high-confidence recoveries found.")
        return

    flipped = 0
    regressed = 0

    for p in problems:
        if p.problem_id not in problem_recoveries:
            continue

        current_votes = dict(p.votes)
        current_winner = max(current_votes, key=current_votes.get) if current_votes else None

        new_votes = dict(current_votes)
        for r in problem_recoveries[p.problem_id]:
            if r.recovered_answer is not None:
                new_votes[r.recovered_answer] = new_votes.get(r.recovered_answer, 0) + 1

        new_winner = max(new_votes, key=new_votes.get) if new_votes else None
        currently_correct = p.correct
        would_be_correct = (new_winner == p.expected) if (new_winner is not None and p.expected is not None) else False

        if not currently_correct and would_be_correct:
            flipped += 1
            n_rec = len(problem_recoveries[p.problem_id])
            n_corr = sum(1 for r in problem_recoveries[p.problem_id] if r.recovered_correct)
            old_v = ", ".join(f"{k}:{v}" for k, v in sorted(current_votes.items(), key=lambda x: -x[1]))
            new_v = ", ".join(f"{k}:{v}" for k, v in sorted(new_votes.items(), key=lambda x: -x[1]))
            print(f"\n    FLIP: {p.problem_id} expected={p.expected}")
            print(f"      Old votes: [{old_v}] -> winner={current_winner}")
            print(f"      New votes: [{new_v}] -> winner={new_winner}")
            print(f"      Recovered {n_rec} attempts ({n_corr} correct)")
        elif currently_correct and not would_be_correct:
            regressed += 1

    current_score = sum(1 for p in problems if p.correct)
    net = flipped - regressed
    print(f"\n  High-conf recoveries: {sum(len(v) for v in problem_recoveries.values())} across {len(problem_recoveries)} problems")
    print(f"  Flipped to correct: {flipped}")
    print(f"  Regressed: {regressed}")
    print(f"  NET: {current_score}/53 -> {current_score + net}/53 ({'+' if net >= 0 else ''}{net})")


def print_per_problem_none_impact(results, problems):
    """For each problem, show how Nones affect the vote."""
    print("\n" + "=" * 90)
    print("PER-PROBLEM NONE IMPACT (problems with >= 6 Nones)")
    print("=" * 90)

    for p in problems:
        nones = [a for a in p.attempts if a.is_none]
        if len(nones) < 6:
            continue

        p_results = [r for r in results if r.problem_id == p.problem_id]
        n_recoverable = sum(1 for r in p_results if r.recoverable)
        n_correct = sum(1 for r in p_results if r.recovered_correct)
        mode_counts = Counter(r.failure_mode for r in p_results)

        mark = "CORRECT" if p.correct else "WRONG"
        votes_str = ", ".join(f"{k}:{v}" for k, v in sorted(p.votes.items(), key=lambda x: -x[1]))

        print(f"\n  {p.problem_id} [{mark}] expected={p.expected}")
        print(f"    Nones: {len(nones)}/16 | Recoverable: {n_recoverable} ({n_correct} correct)")
        print(f"    Current votes: [{votes_str}]")
        print(f"    Failure modes: {dict(mode_counts.most_common())}")

        # Show what answers would be recovered
        if n_recoverable > 0:
            recovered = Counter(r.recovered_answer for r in p_results if r.recoverable)
            print(f"    Recovered answers would be: {dict(recovered.most_common())}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/extraction_deep_v31.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    results = analyze_nones(problems)

    print_summary(results, problems)
    print_failure_modes(results)
    print_recovery_patterns(results)
    print_context_samples(results)
    print_vote_impact(results, problems)
    print_high_conf_only_impact(results, problems)
    print_per_problem_none_impact(results, problems)


if __name__ == "__main__":
    main()
