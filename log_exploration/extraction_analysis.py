#!/usr/bin/env python3
"""
Extraction Failure Deep Dive for AIMO3 Logs
=============================================
Analyzes why the answer extraction pipeline fails to extract answers from
model reasoning, and proposes improved extraction patterns.

Usage: python3 log_exploration/extraction_analysis.py output/v22/diagnostic.log
"""

import sys
import re
from collections import Counter, defaultdict

sys.path.insert(0, '/Users/intern/Desktop/sideprojects/aimo3')
from log_exploration.log_query import parse_log


def classify_attempt(attempt, problem):
    if attempt.is_none:
        return "none"
    if problem.expected is not None and attempt.answer == problem.expected:
        return "correct"
    return "wrong"


def get_full_reasoning(attempt):
    return "\n".join(t.reasoning_text for t in attempt.turns if t.reasoning_text)


def get_full_output(attempt):
    return "\n".join(t.output for t in attempt.turns if t.output)


def get_last_turn_text(attempt):
    """Get the last turn's reasoning and output, which is most likely to contain the answer."""
    if not attempt.turns:
        return "", "", ""
    last = attempt.turns[-1]
    return last.reasoning_text or "", last.code or "", last.output or ""


def none_classification(problems):
    """Classify WHY each None attempt failed to extract an answer."""
    print("=" * 80)
    print("NONE ATTEMPT CLASSIFICATION")
    print("=" * 80)

    categories = Counter()
    category_examples = defaultdict(list)

    for p in problems:
        for a in p.attempts:
            if not a.is_none:
                continue

            full_reasoning = get_full_reasoning(a)
            full_output = get_full_output(a)
            last_reasoning, last_code, last_output = get_last_turn_text(a)

            # Classify
            if not a.turns:
                cat = "no_turns"
            elif all(not t.code for t in a.turns):
                cat = "no_code_generated"
            elif all(t.is_error for t in a.turns if t.code):
                cat = "all_code_errors"
            elif a.turns[-1].is_error:
                cat = "last_turn_error"
            elif "timed out" in full_output.lower() or "timeout" in full_output.lower():
                cat = "timeout"
            elif re.search(r'\b\d{1,5}\b', last_output) and not re.search(r'\d{6,}', last_output):
                cat = "answer_in_output_not_extracted"
            elif re.search(r'(?:answer|result|value|solution)\s*(?:is|=|:)\s*(\d+)', full_reasoning, re.IGNORECASE):
                cat = "answer_in_reasoning_not_extracted"
            elif re.search(r'print\s*\(', last_code) and last_output.strip():
                cat = "print_output_not_parsed"
            elif not last_output.strip() and last_code:
                cat = "code_produced_no_output"
            elif any(t.is_error for t in a.turns):
                cat = "partial_errors"
            else:
                cat = "other_extraction_failure"

            categories[cat] += 1
            if len(category_examples[cat]) < 5:
                category_examples[cat].append({
                    "problem_id": p.problem_id,
                    "attempt": a.attempt_num,
                    "turns": len(a.turns),
                    "last_reasoning_snippet": last_reasoning[-300:] if last_reasoning else "(empty)",
                    "last_code_snippet": last_code[-200:] if last_code else "(empty)",
                    "last_output_snippet": last_output[-200:] if last_output else "(empty)",
                })

    total_nones = sum(categories.values())
    print(f"\n  Total None attempts: {total_nones}")
    print(f"\n  {'Category':<35} {'Count':>6} {'%':>7}")
    print("  " + "-" * 50)

    for cat, count in categories.most_common():
        print(f"  {cat:<35} {count:>6} {count/total_nones*100:>6.1f}%")

    return categories, category_examples


def answer_format_discovery(problems):
    """Find all the formats the model uses to express answers."""
    print("\n" + "=" * 80)
    print("ANSWER FORMAT DISCOVERY")
    print("=" * 80)

    # Regex patterns the model might use to state answers
    answer_patterns = [
        (r'(?:the\s+)?(?:final\s+)?answer\s+is\s+(\d+)', "answer is N"),
        (r'(?:the\s+)?answer\s*[:=]\s*(\d+)', "answer: N / answer = N"),
        (r'(?:the\s+)?result\s+is\s+(\d+)', "result is N"),
        (r'(?:the\s+)?result\s*[:=]\s*(\d+)', "result: N / result = N"),
        (r'(?:the\s+)?solution\s+is\s+(\d+)', "solution is N"),
        (r'(?:the\s+)?value\s+(?:is|equals?)\s+(\d+)', "value is N"),
        (r'(?:the\s+)?output\s+is\s+(\d+)', "output is N"),
        (r'\\boxed\{(\d+)\}', "\\boxed{N}"),
        (r'boxed\s*\{?\s*(\d+)\s*\}?', "boxed N"),
        (r'print\s*\(\s*(\d+)\s*\)', "print(N)"),
        (r'(?:^|\n)\s*(\d{1,5})\s*(?:\n|$)', "bare number on line"),
        (r'(?:equals?|=)\s*(\d+)', "= N or equals N"),
        (r'(?:therefore|thus|hence|so)\s+.*?(\d+)', "therefore ... N"),
        (r'(?:we\s+get|we\s+find|we\s+obtain)\s+(\d+)', "we get N"),
        (r'final\s+(?:result|answer|value)\s*[:=]?\s*(\d+)', "final result N"),
    ]

    # Check which patterns appear in None attempts
    print(f"\n  FORMAT FREQUENCY IN NONE ATTEMPTS (reasoning text):")
    print(f"  {'Pattern':<40} {'Found':>6} {'Matched Expected':>16}")
    print("  " + "-" * 65)

    for pattern, label in answer_patterns:
        found_count = 0
        matched_expected = 0
        for p in problems:
            for a in p.attempts:
                if not a.is_none:
                    continue
                reasoning = get_full_reasoning(a)
                matches = re.findall(pattern, reasoning, re.IGNORECASE)
                if matches:
                    found_count += 1
                    if p.expected is not None:
                        for m in matches:
                            try:
                                if int(m) == p.expected:
                                    matched_expected += 1
                                    break
                            except ValueError:
                                pass
        if found_count > 0:
            print(f"  {label:<40} {found_count:>6} {matched_expected:>16}")

    # Same for code output
    print(f"\n  FORMAT FREQUENCY IN NONE ATTEMPTS (code output):")
    print(f"  {'Pattern':<40} {'Found':>6} {'Matched Expected':>16}")
    print("  " + "-" * 65)

    for pattern, label in answer_patterns:
        found_count = 0
        matched_expected = 0
        for p in problems:
            for a in p.attempts:
                if not a.is_none:
                    continue
                output = get_full_output(a)
                matches = re.findall(pattern, output, re.IGNORECASE)
                if matches:
                    found_count += 1
                    if p.expected is not None:
                        for m in matches:
                            try:
                                if int(m) == p.expected:
                                    matched_expected += 1
                                    break
                            except ValueError:
                                pass
        if found_count > 0:
            print(f"  {label:<40} {found_count:>6} {matched_expected:>16}")


def extraction_failure_samples(problems):
    """Show detailed examples of extraction failures."""
    print("\n" + "=" * 80)
    print("EXTRACTION FAILURE SAMPLES (20 examples)")
    print("=" * 80)

    samples = []
    for p in problems:
        for a in p.attempts:
            if not a.is_none:
                continue

            full_reasoning = get_full_reasoning(a)
            full_output = get_full_output(a)
            last_reasoning, last_code, last_output = get_last_turn_text(a)

            # Find any numbers that look like answers in the text
            reasoning_numbers = re.findall(r'\b(\d{1,5})\b', last_reasoning[-500:]) if last_reasoning else []
            output_numbers = re.findall(r'\b(\d{1,5})\b', last_output[-300:]) if last_output else []

            # Look for explicit answer statements
            answer_statement = None
            for pat in [r'(?:answer|result|solution|value)\s*(?:is|=|:)\s*(\d+)',
                        r'\\boxed\{(\d+)\}',
                        r'print\s*\(\s*(\d+)\s*\)',
                        r'(?:therefore|thus|hence).*?(\d{1,5})']:
                m = re.search(pat, full_reasoning + "\n" + full_output, re.IGNORECASE)
                if m:
                    answer_statement = m.group(0)[:100]
                    break

            samples.append({
                "problem_id": p.problem_id,
                "attempt": a.attempt_num,
                "expected": p.expected,
                "turns": len(a.turns),
                "errors": a.errors,
                "last_reasoning_tail": last_reasoning[-300:].strip() if last_reasoning else "(empty)",
                "last_code": last_code[-200:].strip() if last_code else "(empty)",
                "last_output": last_output[-200:].strip() if last_output else "(empty)",
                "reasoning_numbers": reasoning_numbers[-10:],
                "output_numbers": output_numbers[-10:],
                "answer_statement": answer_statement,
                "has_answer_in_text": answer_statement is not None,
            })

    # Prioritize interesting cases (those with answer statements)
    samples.sort(key=lambda s: (s["has_answer_in_text"], s["errors"] == 0), reverse=True)

    for i, s in enumerate(samples[:20]):
        print(f"\n  --- Sample {i+1}: Problem {s['problem_id']} Attempt {s['attempt']} ---")
        print(f"  Expected: {s['expected']} | Turns: {s['turns']} | Errors: {s['errors']}")
        if s["answer_statement"]:
            print(f"  FOUND ANSWER STATEMENT: {s['answer_statement']}")
        if s["reasoning_numbers"]:
            print(f"  Numbers in last reasoning: {s['reasoning_numbers']}")
        if s["output_numbers"]:
            print(f"  Numbers in last output: {s['output_numbers']}")
        print(f"  Last reasoning (tail):")
        for line in s["last_reasoning_tail"].split("\n")[-5:]:
            print(f"    | {line[:120]}")
        if s["last_code"]:
            print(f"  Last code (tail):")
            for line in s["last_code"].split("\n")[-3:]:
                print(f"    > {line[:120]}")
        print(f"  Last output:")
        for line in s["last_output"].split("\n")[-3:]:
            print(f"    >> {line[:120]}")


def recoverable_nones(problems):
    """Count how many Nones could be recovered with better extraction."""
    print("\n" + "=" * 80)
    print("RECOVERABLE NONES ANALYSIS")
    print("=" * 80)

    # For each None attempt, try all extraction patterns
    extraction_patterns = [
        (r'(?:the\s+)?(?:final\s+)?answer\s+is\s+(\d+)', "answer is N"),
        (r'(?:the\s+)?answer\s*[:=]\s*(\d+)', "answer :/= N"),
        (r'\\boxed\{(\d+)\}', "\\boxed{N}"),
        (r'(?:the\s+)?(?:result|value|solution)\s*(?:is|=|:)\s*(\d+)', "result/value/solution"),
        (r'(?:^|\n)\s*(\d{1,5})\s*(?:\n|$)', "bare number on line"),
        (r'print\s*\(\s*(\d+)\s*\)', "print(N)"),
        (r'(?:therefore|thus|hence|so),?\s+.*?(\d{1,5})', "therefore N"),
        (r'(?:we\s+get|we\s+find|we\s+obtain|we\s+have)\s+.*?(\d{1,5})', "we get N"),
    ]

    recoverable = 0
    recoverable_correct = 0
    total_nones = 0
    pattern_recovery = Counter()

    for p in problems:
        for a in p.attempts:
            if not a.is_none:
                continue
            total_nones += 1

            full_text = get_full_reasoning(a) + "\n" + get_full_output(a)

            for pattern, label in extraction_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    # Take the last match (most likely to be the final answer)
                    last_match = matches[-1]
                    try:
                        num = int(last_match)
                        if 0 <= num <= 99999:  # Valid 5-digit answer range
                            recoverable += 1
                            pattern_recovery[label] += 1
                            if p.expected is not None and num == p.expected:
                                recoverable_correct += 1
                            break
                    except ValueError:
                        pass

    print(f"\n  Total None attempts: {total_nones}")
    print(f"  Potentially recoverable: {recoverable} ({recoverable/total_nones*100:.1f}%)")
    print(f"  Would be correct: {recoverable_correct} ({recoverable_correct/total_nones*100:.1f}%)")
    print(f"  Would be wrong: {recoverable - recoverable_correct} ({(recoverable-recoverable_correct)/total_nones*100:.1f}%)")

    print(f"\n  Recovery by pattern:")
    for label, count in pattern_recovery.most_common():
        print(f"    {label:<35}: {count}")


def proposed_regex_improvements(problems):
    """Analyze what regex patterns would improve extraction."""
    print("\n" + "=" * 80)
    print("PROPOSED EXTRACTION IMPROVEMENTS")
    print("=" * 80)

    # Analyze what the model actually prints
    print_patterns = Counter()
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.code:
                    prints = re.findall(r'print\s*\((.+?)\)', t.code)
                    for pr in prints:
                        # Classify print statement
                        pr = pr.strip()
                        if re.match(r'^f["\']', pr):
                            print_patterns["f-string"] += 1
                        elif re.match(r'^["\']', pr):
                            print_patterns["string literal"] += 1
                        elif re.match(r'^\w+$', pr):
                            print_patterns["bare variable"] += 1
                        elif re.match(r'^int\(', pr):
                            print_patterns["int() cast"] += 1
                        else:
                            print_patterns["expression"] += 1

    print(f"\n  Model's print() patterns:")
    for pat, count in print_patterns.most_common():
        print(f"    {pat:<25}: {count}")

    # Check output format of successful extractions
    successful_outputs = []
    for p in problems:
        for a in p.attempts:
            if a.is_none or not a.turns:
                continue
            last_output = a.turns[-1].output.strip() if a.turns[-1].output else ""
            if last_output and a.answer is not None:
                successful_outputs.append(last_output)

    output_formats = Counter()
    for out in successful_outputs:
        lines = out.strip().split('\n')
        last_line = lines[-1].strip()
        if re.match(r'^\d+$', last_line):
            output_formats["bare integer"] += 1
        elif re.match(r'^\d+\.\d+$', last_line):
            output_formats["decimal"] += 1
        elif re.search(r'answer.*?(\d+)', last_line, re.IGNORECASE):
            output_formats["answer: N"] += 1
        elif re.search(r'result.*?(\d+)', last_line, re.IGNORECASE):
            output_formats["result: N"] += 1
        elif last_line:
            output_formats["other"] += 1

    print(f"\n  Successful extraction output formats (last line):")
    for fmt, count in output_formats.most_common():
        print(f"    {fmt:<25}: {count}")

    # Recommendation
    print(f"\n  RECOMMENDED EXTRACTION REGEX (priority order):")
    recommendations = [
        (1, r'(?:^|\n)\s*(\d{1,5})\s*$', "Bare integer on last output line"),
        (2, r'(?:final\s+)?answer\s*(?:is|=|:)\s*(\d{1,5})', "answer is/=/: N"),
        (3, r'\\boxed\{(\d{1,5})\}', "LaTeX boxed"),
        (4, r'(?:result|value|solution)\s*(?:is|=|:)\s*(\d{1,5})', "result/value/solution"),
        (5, r'(?:therefore|thus|hence|so)\s+.*?(\d{1,5})', "Conclusion keywords + N"),
        (6, r'print\s*\(\s*(\d{1,5})\s*\)', "print(N) in code"),
    ]
    for priority, pattern, desc in recommendations:
        print(f"    {priority}. /{pattern}/")
        print(f"       {desc}")


def none_by_problem(problems):
    """Show None distribution by problem."""
    print("\n" + "=" * 80)
    print("NONE RATE BY PROBLEM")
    print("=" * 80)

    problem_data = []
    for p in problems:
        total = len(p.attempts)
        nones = sum(1 for a in p.attempts if a.is_none)
        if total > 0:
            problem_data.append((p.problem_id, nones, total, nones/total, p.correct, p.expected))

    problem_data.sort(key=lambda x: x[3], reverse=True)

    print(f"\n  {'PID':<10} {'Nones':>6} {'Total':>6} {'Rate':>7} {'Correct':>8} {'Expected':>9}")
    print("  " + "-" * 55)
    for pid, nones, total, rate, correct, expected in problem_data:
        mark = "YES" if correct else "NO"
        exp = str(expected) if expected is not None else "?"
        print(f"  {pid:<10} {nones:>6} {total:>6} {rate:>6.0%} {mark:>8} {exp:>9}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_exploration/extraction_analysis.py <logfile>")
        sys.exit(1)

    logfile = sys.argv[1]
    problems = parse_log(logfile)

    total_attempts = sum(len(p.attempts) for p in problems)
    total_nones = sum(1 for p in problems for a in p.attempts if a.is_none)
    print(f"Loaded {len(problems)} problems with {total_attempts} attempts ({total_nones} Nones = {total_nones/total_attempts*100:.0f}%)")
    print()

    none_classification(problems)
    answer_format_discovery(problems)
    extraction_failure_samples(problems)
    recoverable_nones(problems)
    proposed_regex_improvements(problems)
    none_by_problem(problems)


if __name__ == "__main__":
    main()
