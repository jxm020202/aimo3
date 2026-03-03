#!/usr/bin/env python3
"""
AIMO3 Logging Gap Analysis
===========================
Analyzes current diagnostic.log to identify what data is MISSING or incomplete,
what correlations we can't compute, and what would help us improve.

Usage:
    python log_exploration/logging_gaps.py [logfile]
    (default: output/v22/diagnostic.log)
"""

import sys
import os
import re
from collections import Counter, defaultdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log, Attempt, Turn, Problem


def analyze_field_completeness(problems):
    """Check which fields in parsed data are always empty/missing."""
    print("=" * 70)
    print("  1. FIELD COMPLETENESS ANALYSIS")
    print("=" * 70)

    # Problem-level fields
    p_fields = {
        'problem_id': 0, 'batch_name': 0, 'problem_text': 0,
        'budget': 0, 'deadline': 0, 'predicted': 0, 'expected': 0,
        'wall_time': 0, 'total_answered': 0, 'total_attempts': 0,
        'total_code_calls': 0, 'total_errors': 0, 'total_tokens': 0,
        'avg_entropy': 0, 'early_stop_threshold': 0, 'votes': 0,
    }
    total_problems = len(problems)
    for p in problems:
        if p.problem_id: p_fields['problem_id'] += 1
        if p.batch_name: p_fields['batch_name'] += 1
        if p.problem_text: p_fields['problem_text'] += 1
        if p.budget > 0: p_fields['budget'] += 1
        if p.deadline > 0: p_fields['deadline'] += 1
        if p.predicted is not None: p_fields['predicted'] += 1
        if p.expected is not None: p_fields['expected'] += 1
        if p.wall_time > 0: p_fields['wall_time'] += 1
        if p.total_answered > 0: p_fields['total_answered'] += 1
        if p.total_attempts > 0: p_fields['total_attempts'] += 1
        if p.total_code_calls > 0: p_fields['total_code_calls'] += 1
        if p.total_errors > 0: p_fields['total_errors'] += 1
        if p.total_tokens > 0: p_fields['total_tokens'] += 1
        if p.avg_entropy > 0: p_fields['avg_entropy'] += 1
        if p.early_stop_threshold > 0: p_fields['early_stop_threshold'] += 1
        if p.votes: p_fields['votes'] += 1

    print(f"\n  Problem-level fields ({total_problems} problems):")
    print(f"  {'Field':<25} {'Present':>8} {'Missing':>8} {'%':>6}")
    print(f"  {'─'*25} {'─'*8} {'─'*8} {'─'*6}")
    for field, count in sorted(p_fields.items(), key=lambda x: x[1]):
        missing = total_problems - count
        pct = count / max(total_problems, 1) * 100
        status = "  <<<" if pct < 50 else ("  <" if pct < 90 else "")
        print(f"  {field:<25} {count:>8} {missing:>8} {pct:>5.1f}%{status}")

    # Attempt-level fields
    a_fields = {
        'answer': 0, 'entropy': 0, 'code_calls': 0, 'errors': 0,
        'tokens': 0, 'time_s': 0, 'temperature': 0, 'libraries': 0,
        'turns': 0,
    }
    total_attempts = sum(len(p.attempts) for p in problems)
    for p in problems:
        for a in p.attempts:
            if a.answer is not None: a_fields['answer'] += 1
            if a.entropy > 0 and a.entropy != float('inf'): a_fields['entropy'] += 1
            if a.code_calls > 0: a_fields['code_calls'] += 1
            if a.errors > 0: a_fields['errors'] += 1
            if a.tokens > 0: a_fields['tokens'] += 1
            if a.time_s > 0: a_fields['time_s'] += 1
            if a.temperature is not None: a_fields['temperature'] += 1
            if a.libraries: a_fields['libraries'] += 1
            if a.turns: a_fields['turns'] += 1

    print(f"\n  Attempt-level fields ({total_attempts} attempts):")
    print(f"  {'Field':<25} {'Present':>8} {'Missing':>8} {'%':>6}")
    print(f"  {'─'*25} {'─'*8} {'─'*8} {'─'*6}")
    for field, count in sorted(a_fields.items(), key=lambda x: x[1]):
        missing = total_attempts - count
        pct = count / max(total_attempts, 1) * 100
        status = "  <<<" if pct < 50 else ("  <" if pct < 90 else "")
        print(f"  {field:<25} {count:>8} {missing:>8} {pct:>5.1f}%{status}")

    # Turn-level fields
    t_fields = {'reasoning_chars': 0, 'reasoning_text': 0, 'code': 0, 'output': 0}
    total_turns = sum(len(a.turns) for p in problems for a in p.attempts)
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.reasoning_chars > 0: t_fields['reasoning_chars'] += 1
                if t.reasoning_text: t_fields['reasoning_text'] += 1
                if t.code: t_fields['code'] += 1
                if t.output: t_fields['output'] += 1

    print(f"\n  Turn-level fields ({total_turns} turns):")
    print(f"  {'Field':<25} {'Present':>8} {'Missing':>8} {'%':>6}")
    print(f"  {'─'*25} {'─'*8} {'─'*8} {'─'*6}")
    for field, count in sorted(t_fields.items(), key=lambda x: x[1]):
        missing = total_turns - count
        pct = count / max(total_turns, 1) * 100
        status = "  <<<" if pct < 50 else ("  <" if pct < 90 else "")
        print(f"  {field:<25} {count:>8} {missing:>8} {pct:>5.1f}%{status}")


def analyze_missing_correlations(problems):
    """Identify correlations we CAN'T compute with current data."""
    print(f"\n{'=' * 70}")
    print("  2. IMPOSSIBLE CORRELATIONS (data we don't have)")
    print("=" * 70)

    gaps = []

    # Gap 1: Temperature per attempt (v22 doesn't log it)
    temps_present = sum(1 for p in problems for a in p.attempts if a.temperature is not None)
    total_att = sum(len(p.attempts) for p in problems)
    if temps_present < total_att * 0.5:
        gaps.append({
            'name': 'TEMPERATURE x CORRECTNESS',
            'severity': 'CRITICAL',
            'detail': (
                f'Temperature is missing for {total_att - temps_present}/{total_att} attempts.\n'
                '    Cannot answer: "Which temperature produces best accuracy?"\n'
                '    Cannot answer: "Should we use temp=0.3 more and temp=0.7 less?"\n'
                '    Impact: Blind tuning of temp_schedule — our #1 hyperparameter.'
            ),
        })

    # Gap 2: No per-turn timing
    gaps.append({
        'name': 'REASONING TIME vs CODE EXECUTION TIME',
        'severity': 'CRITICAL',
        'detail': (
            'We log total attempt time but NOT per-turn breakdown.\n'
            '    Cannot answer: "How much time is reasoning vs code execution?"\n'
            '    Cannot answer: "Are slow problems slow because of code or thinking?"\n'
            '    Impact: Can\'t optimize the right bottleneck.'
        ),
    })

    # Gap 3: No extraction regex tracking
    gaps.append({
        'name': 'ANSWER EXTRACTION METHOD',
        'severity': 'HIGH',
        'detail': (
            '40% of Nones are "extraction-failure". We don\'t log WHICH regex matched.\n'
            '    Cannot answer: "Is \\\\boxed{} working? Or are we relying on fallbacks?"\n'
            '    Cannot answer: "What text did the model produce when extraction failed?"\n'
            '    Impact: 40% of all Nones — the #1 failure mode.'
        ),
    })

    # Gap 4: No raw model output before extraction
    gaps.append({
        'name': 'RAW MODEL OUTPUT (pre-extraction)',
        'severity': 'HIGH',
        'detail': (
            'When extraction fails, we can\'t see what the model actually said.\n'
            '    The reasoning text is logged, but the FINAL token sequence that\n'
            '    _scan_for_answer() searched is not preserved.\n'
            '    Cannot answer: "Did the model say the right answer in a weird format?"\n'
            '    Impact: Could recover answers by improving regex patterns.'
        ),
    })

    # Gap 5: No confidence/logprob per answer
    gaps.append({
        'name': 'PER-ANSWER CONFIDENCE (logprob at answer token)',
        'severity': 'HIGH',
        'detail': (
            'We compute mean entropy over ALL tokens but not specifically around \\\\boxed{}.\n'
            '    Cannot answer: "Was the model confident about THIS answer specifically?"\n'
            '    Cannot answer: "Which of two competing answers had higher local confidence?"\n'
            '    Impact: Entropy-weighted voting uses global entropy — answer-local entropy\n'
            '    would be a strictly better signal for vote weighting.'
        ),
    })

    # Gap 6: No code execution timing
    gaps.append({
        'name': 'CODE EXECUTION TIME (sandbox)',
        'severity': 'MEDIUM',
        'detail': (
            'We know how many code calls happened, but not how long each took.\n'
            '    Cannot answer: "Are timeouts from slow sympy or slow numpy?"\n'
            '    Cannot answer: "Which code cells took >10s?"\n'
            '    Impact: Timeouts are 6.4% of Nones. Can\'t diagnose without timing.'
        ),
    })

    # Gap 7: No code length tracking
    gaps.append({
        'name': 'CODE CELL LENGTH',
        'severity': 'LOW',
        'detail': (
            'We log the code text but not its character/line count as a structured field.\n'
            '    Cannot answer: "Do longer code cells correlate with errors?"\n'
            '    Impact: Minor, but could inform code complexity limits.'
        ),
    })

    # Gap 8: No problem topic/type classification
    gaps.append({
        'name': 'PROBLEM TOPIC CLASSIFICATION',
        'severity': 'HIGH',
        'detail': (
            'We don\'t tag problems by mathematical topic (algebra, geometry, NT, etc.).\n'
            '    Cannot answer: "Are we weak at geometry? Strong at number theory?"\n'
            '    Cannot answer: "Which topic has highest error rate?"\n'
            '    Impact: Can\'t focus improvement efforts on weakest areas.'
        ),
    })

    # Gap 9: No retry tracking
    gaps.append({
        'name': 'RETRY vs FIRST-TRY DISTINCTION',
        'severity': 'MEDIUM',
        'detail': (
            'When a code cell errors and the model retries, we can\'t distinguish:\n'
            '    - "Completely new approach" vs "Retry same code with fix"\n'
            '    Cannot answer: "How often does error recovery succeed?"\n'
            '    Cannot answer: "Should we cap retries for failing approaches?"\n'
            '    Impact: Error cascade analysis is approximate without this.'
        ),
    })

    # Gap 10: No KV cache / GPU utilization per problem
    gaps.append({
        'name': 'KV CACHE UTILIZATION PER PROBLEM',
        'severity': 'MEDIUM',
        'detail': (
            'gpu_metrics.log has aggregate stats but not per-problem cache usage.\n'
            '    Cannot answer: "Which problems exhausted KV cache?"\n'
            '    Cannot answer: "Did cache pressure cause quality degradation?"\n'
            '    Impact: KV cache is the binding constraint on attempts * context.'
        ),
    })

    # Gap 11: No answer-change tracking across turns
    gaps.append({
        'name': 'ANSWER EVOLUTION WITHIN ATTEMPT',
        'severity': 'MEDIUM',
        'detail': (
            'We extract the FINAL answer but not intermediate \\\\boxed{} values.\n'
            '    Cannot answer: "Did the model change its answer mid-attempt?"\n'
            '    Cannot answer: "Was the first answer correct but the model overthought?"\n'
            '    Impact: Could detect "overthinking" pattern — model finds answer then\n'
            '    changes it to wrong one.'
        ),
    })

    # Gap 12: No prompt token count
    gaps.append({
        'name': 'PROMPT TOKEN COUNT',
        'severity': 'LOW',
        'detail': (
            'We log completion tokens (response length) but not prompt tokens.\n'
            '    Cannot answer: "How much context window is the prompt consuming?"\n'
            '    Impact: Context window management.'
        ),
    })

    for gap in gaps:
        severity_marker = {'CRITICAL': '!!!', 'HIGH': '!! ', 'MEDIUM': '!  ', 'LOW': '   '}
        marker = severity_marker.get(gap['severity'], '   ')
        print(f"\n  {marker} [{gap['severity']}] {gap['name']}")
        for line in gap['detail'].split('\n'):
            print(f"    {line}")

    # Summary
    by_sev = Counter(g['severity'] for g in gaps)
    print(f"\n  {'─'*60}")
    print(f"  SUMMARY: {len(gaps)} logging gaps identified")
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if by_sev[sev]:
            print(f"    {sev}: {by_sev[sev]}")


def analyze_timing_gaps(problems):
    """Analyze what timing breakdowns we're missing."""
    print(f"\n{'=' * 70}")
    print("  3. TIMING BREAKDOWN GAPS")
    print("=" * 70)

    # What we have: total wall time per problem, time per attempt
    # What we DON'T have: reasoning time vs code time within each attempt

    # Estimate reasoning vs code time from what we CAN measure
    for p in problems[:3]:  # Sample first 3
        if not p.attempts:
            continue
        for a in p.attempts[:2]:
            total = a.time_s
            code_turns = sum(1 for t in a.turns if t.code)
            reasoning_turns = sum(1 for t in a.turns if t.reasoning_text)
            print(f"\n  Problem {p.problem_id}, Attempt {a.attempt_num}:")
            print(f"    Total time: {total:.1f}s")
            print(f"    Turns: {len(a.turns)} ({reasoning_turns} reasoning, {code_turns} code)")
            print(f"    Per-turn timing: NOT AVAILABLE")
            print(f"    Reasoning chars: {sum(t.reasoning_chars for t in a.turns)}")
            print(f"    Code chars: {sum(len(t.code) for t in a.turns if t.code)}")
            print(f"    Output chars: {sum(len(t.output) for t in a.turns if t.output)}")

    # Estimate what fraction of time is code execution
    # We can proxy this: code_calls * avg_jupyter_timeout_fraction
    total_time = sum(a.time_s for p in problems for a in p.attempts if a.time_s > 0)
    total_code_calls = sum(a.code_calls for p in problems for a in p.attempts)
    print(f"\n  Aggregate timing (what we know):")
    print(f"    Total attempt time: {total_time:.0f}s")
    print(f"    Total code calls: {total_code_calls}")
    print(f"    If avg code cell = 2s: ~{total_code_calls * 2:.0f}s code ({total_code_calls * 2 / max(total_time, 1) * 100:.0f}% of total)")
    print(f"    If avg code cell = 5s: ~{total_code_calls * 5:.0f}s code ({total_code_calls * 5 / max(total_time, 1) * 100:.0f}% of total)")
    print(f"    ACTUAL code time: UNKNOWN (not logged)")


def analyze_close_miss_vs_wrong(problems):
    """What data would help distinguish 'close miss' from 'completely wrong'?"""
    print(f"\n{'=' * 70}")
    print("  4. CLOSE-MISS vs COMPLETELY-WRONG ANALYSIS")
    print("=" * 70)

    wrong_problems = [p for p in problems if not p.correct and p.expected is not None]

    print(f"\n  {len(wrong_problems)} wrong problems. What CAN we tell vs what CAN'T we tell:")
    print()

    for p in wrong_problems:
        print(f"  Problem {p.problem_id}:")
        print(f"    Expected: {p.expected}, Predicted: {p.predicted}")

        # What we CAN tell
        correct_votes = p.votes.get(p.expected, 0)
        total_votes = sum(p.votes.values())
        print(f"    Votes for correct: {correct_votes}/{total_votes}")

        # Attempt-level analysis
        correct_attempts = [a for a in p.attempts if a.answer == p.expected]
        wrong_attempts = [a for a in p.attempts if a.answer is not None and a.answer != p.expected]
        none_attempts = [a for a in p.attempts if a.is_none]

        print(f"    Correct attempts: {len(correct_attempts)}")
        print(f"    Wrong attempts: {len(wrong_attempts)} -> answers: {[a.answer for a in wrong_attempts]}")
        print(f"    None attempts: {len(none_attempts)}")

        # What we CAN'T tell
        print(f"    MISSING DATA:")
        print(f"      - Temperature of each attempt (v22): can't correlate temp with accuracy")
        print(f"      - Did any attempt ALMOST get it? (intermediate answers not tracked)")
        print(f"      - What math topic is this? (not classified)")
        if wrong_attempts:
            unique_wrong = set(a.answer for a in wrong_attempts)
            if len(unique_wrong) == 1:
                single_wrong = list(unique_wrong)[0]
                # Check if it's numerically close
                if p.expected and single_wrong:
                    diff = abs(single_wrong - p.expected)
                    ratio = single_wrong / max(p.expected, 1)
                    print(f"      - All wrong attempts gave {single_wrong} (diff={diff}, ratio={ratio:.3f})")
                    if diff <= 10 or 0.9 <= ratio <= 1.1:
                        print(f"        CLOSE MISS: systematic error, not random")
                    else:
                        print(f"        FAR MISS: fundamentally wrong approach")
        print()


def analyze_extraction_failures(problems):
    """Deep dive into extraction failures — our #1 failure mode."""
    print(f"\n{'=' * 70}")
    print("  5. EXTRACTION FAILURE DEEP DIVE")
    print("=" * 70)

    extraction_failures = []
    for p in problems:
        for a in p.attempts:
            if a.is_none and a.turns:
                # Check if any turn has reasoning with answer-like patterns
                all_text = ' '.join(t.reasoning_text or '' for t in a.turns)
                patterns = [
                    (r'\\boxed\s*\{[^}]*\}', 'boxed'),
                    (r'answer\s+is\s+\d+', 'answer-is'),
                    (r'final\s+answer.*\d+', 'final-answer'),
                    (r'therefore.*\d+', 'therefore'),
                ]
                found_patterns = []
                for pat, name in patterns:
                    matches = re.findall(pat, all_text, re.IGNORECASE)
                    if matches:
                        found_patterns.append((name, matches[-1][:60]))

                if found_patterns:
                    extraction_failures.append({
                        'problem': p.problem_id,
                        'attempt': a.attempt_num,
                        'patterns': found_patterns,
                        'reasoning_len': len(all_text),
                        'turns': len(a.turns),
                    })

    print(f"\n  {len(extraction_failures)} attempts had answer-like text but returned None:")
    print()

    pattern_counts = Counter()
    for ef in extraction_failures:
        for name, _ in ef['patterns']:
            pattern_counts[name] += 1

    print(f"  Pattern frequency in extraction failures:")
    for pat, count in pattern_counts.most_common():
        print(f"    {pat}: {count}")

    print(f"\n  MISSING: We don't log which _scan_for_answer() regex was tried and failed.")
    print(f"  MISSING: We don't log the search_text that was fed to _scan_for_answer().")
    print(f"  MISSING: We don't log the raw final tokens before parsing.")

    # Sample extraction failures
    print(f"\n  Sample extraction failures (first 5):")
    for ef in extraction_failures[:5]:
        print(f"    {ef['problem']} att#{ef['attempt']}: {ef['patterns']}")


def analyze_available_but_not_logged(problems):
    """Data available in the code but not currently logged."""
    print(f"\n{'=' * 70}")
    print("  6. DATA AVAILABLE IN CODE BUT NOT LOGGED")
    print("=" * 70)

    available = [
        {
            'name': 'attempt_seed',
            'where': 'AIMO3Solver._process_attempt (cell 13)',
            'line': 'attempt_seed = int(math.pow(self.cfg.seed + attempt_index, 2))',
            'status': 'COMPUTED but not logged',
            'value': 'Could help reproduce specific attempts',
        },
        {
            'name': 'max_tokens (remaining context)',
            'where': 'AIMO3Solver._process_attempt, inside turn loop',
            'line': 'max_tokens = self.cfg.context_tokens - len(prompt_ids)',
            'status': 'COMPUTED but not logged',
            'value': 'Shows how much context window was consumed per turn',
        },
        {
            'name': 'token_buffer length per chunk',
            'where': 'AIMO3Solver._process_attempt, streaming loop',
            'line': 'token_buffer.extend(new_tokens)',
            'status': 'ACCUMULATED but only total logged',
            'value': 'Per-turn token count would show reasoning depth evolution',
        },
        {
            'name': 'stop reason (why streaming stopped)',
            'where': 'AIMO3Solver._process_attempt',
            'line': 'Multiple break points: answer found, stop_event, deadline, no tokens',
            'status': 'NOT logged — we exit the loop silently',
            'value': 'Critical: did we stop because we found answer, or timed out?',
        },
        {
            'name': 'message.channel / message.recipient',
            'where': 'AIMO3Solver._process_attempt, after parse_messages',
            'line': 'last_message.channel == "final" / last_message.recipient == "python"',
            'status': 'CHECKED but not logged',
            'value': 'Would show if model tried to use unsupported tools',
        },
        {
            'name': 'sandbox reset timing',
            'where': 'AIMO3Solver._process_attempt, finally block',
            'line': 'sandbox.reset()',
            'status': 'NOT timed',
            'value': 'Sandbox reset cost could be significant',
        },
        {
            'name': 'logprobs per token',
            'where': 'AIMO3Solver._process_attempt',
            'line': 'logprobs_buffer.extend(chunk_logprobs.top_logprobs)',
            'status': 'COLLECTED but only mean entropy logged',
            'value': 'Per-token logprobs enable: answer confidence, uncertainty maps',
        },
        {
            'name': 'vote weights (entropy-weighted scores)',
            'where': 'AIMO3Solver._select_answer',
            'line': 'weight = 1.0 / max(entropy, 1e-9)',
            'status': 'COMPUTED, displayed in DataFrame, but not in diagnostic.log',
            'value': 'Shows HOW CLOSE the vote was. Margin matters.',
        },
        {
            'name': 'retry indicator',
            'where': 'AIMO3Solver.solve_problem (retry block)',
            'line': 'retry_idx + self.cfg.attempts',
            'status': 'Retry attempts use indices > cfg.attempts but log doesn\'t flag them',
            'value': 'Can\'t distinguish retry attempts from first-round attempts',
        },
        {
            'name': 'GPU metrics per problem',
            'where': 'AIMO3Solver._start_gpu_monitor (background thread)',
            'line': 'Logs to gpu_metrics.log globally, not correlated to problems',
            'status': 'LOGGED separately, not correlated',
            'value': 'Per-problem GPU pressure would show capacity-related failures',
        },
    ]

    for item in available:
        print(f"\n  {item['name']}")
        print(f"    Where: {item['where']}")
        print(f"    Code:  {item['line']}")
        print(f"    Status: {item['status']}")
        print(f"    Value: {item['value']}")


def analyze_question_priorities(problems):
    """What questions would most help go from 44->47?"""
    print(f"\n{'=' * 70}")
    print("  7. KEY UNANSWERABLE QUESTIONS (what blocks 44->47)")
    print("=" * 70)

    questions = [
        {
            'question': 'Which temperature setting produces the highest per-attempt accuracy?',
            'blocked_by': 'No per-attempt temperature in v22 logs',
            'impact': 'CRITICAL — temp_schedule is our #1 tunable. v23 fixes this.',
            'priority': 1,
        },
        {
            'question': 'When the model writes \\boxed{} but extraction fails, what exact text did it produce?',
            'blocked_by': 'No logging of search_text passed to _scan_for_answer()',
            'impact': 'CRITICAL — 40% of Nones are extraction failures. Fixable if we see the text.',
            'priority': 2,
        },
        {
            'question': 'How much time is spent on LLM inference vs code execution per attempt?',
            'blocked_by': 'No per-turn timing',
            'impact': 'HIGH — can\'t optimize the right bottleneck',
            'priority': 3,
        },
        {
            'question': 'Did the model change its answer during the attempt (overthinking)?',
            'blocked_by': 'Only final \\boxed{} extracted, intermediates discarded',
            'impact': 'HIGH — overthinking wastes tokens and can change correct→wrong',
            'priority': 4,
        },
        {
            'question': 'Are we worse at geometry vs number theory vs combinatorics?',
            'blocked_by': 'No problem topic classification',
            'impact': 'MEDIUM — can\'t focus prompt engineering on weak areas',
            'priority': 5,
        },
        {
            'question': 'Why did the attempt stop? (found answer, timed out, context exhausted, stop_event)',
            'blocked_by': 'No stop_reason field logged',
            'impact': 'HIGH — 21% of Nones are "no-code-generated" which might be context exhaustion',
            'priority': 6,
        },
        {
            'question': 'How close was the vote for wrong problems? Could one more correct attempt flip it?',
            'blocked_by': 'Entropy-weighted scores not in diagnostic.log (only in notebook DataFrame output)',
            'impact': 'HIGH — vote margin tells us if more attempts would help',
            'priority': 7,
        },
        {
            'question': 'When early stop triggers, were the stopped attempts going to be correct?',
            'blocked_by': 'Stopped attempts return None immediately, no data captured',
            'impact': 'MEDIUM — are we discarding correct attempts too early?',
            'priority': 8,
        },
    ]

    for q in sorted(questions, key=lambda x: x['priority']):
        print(f"\n  #{q['priority']}. {q['question']}")
        print(f"     Blocked by: {q['blocked_by']}")
        print(f"     Impact: {q['impact']}")


def main():
    logfile = sys.argv[1] if len(sys.argv) > 1 else 'output/v22/diagnostic.log'
    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    print(f"Analyzing: {logfile}\n")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems, "
          f"{sum(len(p.attempts) for p in problems)} attempts, "
          f"{sum(len(a.turns) for p in problems for a in p.attempts)} turns\n")

    analyze_field_completeness(problems)
    analyze_missing_correlations(problems)
    analyze_timing_gaps(problems)
    analyze_close_miss_vs_wrong(problems)
    analyze_extraction_failures(problems)
    analyze_available_but_not_logged(problems)
    analyze_question_priorities(problems)


if __name__ == '__main__':
    main()
