#!/usr/bin/env python3
"""
Deep dive into high-None-rate problems.
Extracts problem text, categorizes None causes, reads reasoning for specific attempts.

Usage:
    python3 log_exploration/none_deep_dive.py output/v31/diagnostic.log aff75c 1ec970
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def analyze_problem(prob):
    print(f"\n{'='*100}")
    print(f"PROBLEM: {prob.problem_id}")
    print(f"Expected: {prob.expected}  |  Predicted: {prob.predicted}  |  Correct: {prob.correct}")
    print(f"Wall time: {prob.wall_time:.0f}s  |  Budget: {prob.budget:.0f}s")
    print(f"Attempts: {prob.total_attempts}  |  Answered: {prob.total_answered}")
    print(f"Votes: {prob.votes}")
    print(f"{'='*100}")

    # Problem text
    print(f"\n--- PROBLEM TEXT ---")
    print(prob.problem_text if prob.problem_text else "(not captured)")

    # Attempt overview
    print(f"\n--- ATTEMPT OVERVIEW ---")
    none_attempts = []
    answered_attempts = []
    for att in prob.attempts:
        status = f"answer={att.answer}" if att.answer is not None else "NONE"
        print(f"  Att {att.attempt_num:2d}: {status:>14s} | temp={att.temperature} | turns={len(att.turns):2d} | "
              f"errors={att.errors} | time={att.time_s:.0f}s | code_calls={att.code_calls}")
        if att.is_none or att.answer is None:
            none_attempts.append(att)
        else:
            answered_attempts.append(att)

    # None analysis
    print(f"\n--- NONE ANALYSIS ({len(none_attempts)}/{len(prob.attempts)} attempts) ---")
    for att in none_attempts:
        turns = att.turns
        total_turns = len(turns)
        error_turns = sum(1 for t in turns if t.is_error)
        code_turns = sum(1 for t in turns if t.code.strip())
        reasoning_len = sum(len(t.reasoning_text) for t in turns)

        # Check last turn for clues
        last_turn = turns[-1] if turns else None
        last_reasoning = last_turn.reasoning_text[-500:] if last_turn else ""
        last_output = last_turn.output[-500:] if last_turn else ""

        # Check for timeout indicators
        has_timeout = any("timeout" in t.output.lower() or "timed out" in t.output.lower()
                         or "execution timed out" in t.output.lower() for t in turns)
        has_context_limit = any("context" in t.output.lower() and ("limit" in t.output.lower() or "length" in t.output.lower())
                               for t in turns)

        # Check if any turn had a candidate answer
        candidate_answers = []
        for t in turns:
            import re
            # Look for "answer is XXXXX" or "= XXXXX" patterns in reasoning
            for m in re.finditer(r'(?:answer\s+is|answer:\s*|result\s+is|equals?\s+|=\s*)(\d{4,5})', t.reasoning_text, re.I):
                candidate_answers.append(int(m.group(1)))
            # Look for boxed answers
            for m in re.finditer(r'\\boxed\{(\d+)\}', t.reasoning_text):
                candidate_answers.append(int(m.group(1)))
            # Check code output for numeric results
            for m in re.finditer(r'^(\d{4,5})\s*$', t.output, re.M):
                candidate_answers.append(int(m.group(1)))

        cause = "unknown"
        if has_timeout:
            cause = "TIMEOUT"
        elif has_context_limit:
            cause = "CONTEXT_LIMIT"
        elif error_turns > total_turns * 0.5:
            cause = "ERROR_CASCADE"
        elif code_turns == 0:
            cause = "NO_CODE"
        elif total_turns >= 40:
            cause = "TURN_EXHAUSTION"
        elif candidate_answers:
            cause = "EXTRACTION_FAILURE"
        else:
            cause = "NO_SOLUTION_FOUND"

        print(f"\n  Attempt {att.attempt_num}: cause={cause}")
        print(f"    turns={total_turns}, errors={error_turns}, code_turns={code_turns}, reasoning_chars={reasoning_len}")
        if candidate_answers:
            print(f"    Candidate answers seen in reasoning: {candidate_answers[:10]}")
        if has_timeout:
            print(f"    [TIMEOUT detected in output]")
        print(f"    Last turn reasoning (last 300 chars): ...{last_reasoning[-300:]}")
        if last_output.strip():
            print(f"    Last turn output (last 300 chars): ...{last_output[-300:]}")

    # Answered attempts analysis
    print(f"\n--- ANSWERED ATTEMPTS ({len(answered_attempts)}/{len(prob.attempts)}) ---")
    for att in answered_attempts:
        turns = att.turns
        print(f"\n  Attempt {att.attempt_num}: answer={att.answer} | temp={att.temperature} | turns={len(turns)}")

    return none_attempts, answered_attempts


def print_full_attempt(att, label=""):
    """Print full reasoning trace for an attempt."""
    print(f"\n{'~'*80}")
    print(f"FULL TRACE: Attempt {att.attempt_num} {label}")
    print(f"Temperature: {att.temperature} | Turns: {len(att.turns)} | Answer: {att.answer}")
    print(f"{'~'*80}")

    for t in att.turns:
        print(f"\n  --- Turn {t.turn_num} ---")
        if t.reasoning_text.strip():
            # Print reasoning, truncated if very long
            text = t.reasoning_text.strip()
            if len(text) > 3000:
                print(f"  [REASONING] ({len(text)} chars, showing first 1500 + last 1500):")
                print(f"    {text[:1500]}")
                print(f"    [...{len(text)-3000} chars omitted...]")
                print(f"    {text[-1500:]}")
            else:
                print(f"  [REASONING] ({len(text)} chars):")
                print(f"    {text}")
        if t.code.strip():
            code = t.code.strip()
            if len(code) > 2000:
                print(f"  [CODE] ({len(code)} chars, showing first 1000 + last 1000):")
                print(f"    {code[:1000]}")
                print(f"    [...{len(code)-2000} chars omitted...]")
                print(f"    {code[-1000:]}")
            else:
                print(f"  [CODE] ({len(code)} chars):")
                print(f"    {code}")
        if t.output.strip():
            out = t.output.strip()
            if len(out) > 1500:
                print(f"  [OUTPUT] ({len(out)} chars, showing first 750 + last 750):")
                print(f"    {out[:750]}")
                print(f"    [...{len(out)-1500} chars omitted...]")
                print(f"    {out[-750:]}")
            else:
                print(f"  [OUTPUT] ({len(out)} chars):")
                print(f"    {out}")
        if t.is_error:
            print(f"  [ERROR FLAG SET]")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 log_exploration/none_deep_dive.py <logfile> <pid1> [pid2] ...")
        sys.exit(1)

    logfile = sys.argv[1]
    pids = sys.argv[2:]

    problems = parse_log(logfile)
    pid_map = {p.problem_id: p for p in problems}

    for pid in pids:
        # Support partial matching
        matches = [p for p in problems if p.problem_id.startswith(pid)]
        if not matches:
            print(f"Problem {pid} not found!")
            continue
        prob = matches[0]
        none_attempts, answered_attempts = analyze_problem(prob)

        # Print full traces for first 2 None attempts
        print(f"\n\n{'#'*100}")
        print(f"DETAILED TRACES FOR {prob.problem_id}")
        print(f"{'#'*100}")

        for att in none_attempts[:2]:
            print_full_attempt(att, label="[NONE attempt]")

        # Print full traces for all answered attempts
        for att in answered_attempts[:2]:
            print_full_attempt(att, label="[ANSWERED attempt]")


if __name__ == "__main__":
    main()
