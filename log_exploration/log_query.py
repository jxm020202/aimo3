#!/usr/bin/env python3
"""
AIMO3 Log Query System
======================
Parses diagnostic.log into structured data and supports rich queries.
Works with v21, v22, v23, and v34+ (Wave 1) log formats.
Parses Wave 1 classification data (taxonomies, votes, time, failures, notes)
when present — older logs without Wave 1 sections are handled gracefully.

Usage:
    python log_exploration/log_query.py <logfile> <query> [args...]

Queries — Overview:
    summary                  Overall score, timing, batch breakdown
    problems                 Table of all problems with stats
    timeline                 Chronological problem order with cumulative stats

Queries — Failures & Debugging:
    failures                 All wrong/failed problems with vote analysis
    nones                    All None (no answer) attempts with reasons
    none-reasons             Classify why Nones happened (no code, error, extraction)
    close-votes              Problems with tight vote margins (nearly wrong)
    outvoted                 Correct answer existed but was outvoted

Queries — Performance:
    attempts <pid>           All attempts for a specific problem
    temp <val>               All attempts at a specific temperature
    temps                    Breakdown by temperature (correct/wrong/none rates)
    slow [threshold_s]       Problems exceeding time threshold (default 600)
    budget                   Budget allocation vs actual time per problem
    efficiency               Tokens/time per correct answer vs wrong/none
    early-stops              Early stop analysis

Queries — Wave 1 Classification:
    wave1                    Wave 1 stats: taxonomy, votes, time, failures per problem

Queries — Errors:
    errors                   All code execution errors with context
    errors-by-type           Error taxonomy (NameError, TypeError, etc.)
    errors-by-problem        Error count per problem
    hallucinations           Likely hallucinated API calls
    cascades                 Error cascade analysis (does error→more errors?)

Queries — Code & Reasoning:
    libraries                Library usage frequency
    turns                    Turn count distribution (reasoning depth)
    code-patterns            Most common code patterns/functions
    reasoning-length         Reasoning length vs correctness
    search <pattern>         Search all reasoning/code for a regex pattern

Queries — Export:
    json                     Full parsed data as JSON (pipe to file)
    csv                      Problem-level CSV (pipe to file)
    attempts-csv             Attempt-level CSV (pipe to file)
"""

import sys
import re
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Turn:
    turn_num: int
    reasoning_chars: int = 0
    reasoning_text: str = ""
    code: str = ""
    output: str = ""
    is_error: bool = False

@dataclass
class Attempt:
    attempt_num: int
    answer: Optional[int] = None
    entropy: float = 0.0
    code_calls: int = 0
    errors: int = 0
    tokens: int = 0
    time_s: float = 0.0
    temperature: Optional[float] = None
    libraries: list = field(default_factory=list)
    turns: list = field(default_factory=list)
    is_none: bool = False

@dataclass
class Problem:
    problem_id: str
    batch_name: str = ""
    batch_idx: int = 0
    batch_total: int = 0
    problem_text: str = ""
    budget: float = 0.0
    deadline: float = 0.0
    predicted: Optional[int] = None
    expected: Optional[int] = None
    correct: bool = False
    wall_time: float = 0.0
    total_answered: int = 0
    total_attempts: int = 0
    total_code_calls: int = 0
    total_errors: int = 0
    total_tokens: int = 0
    avg_entropy: float = 0.0
    early_stop: bool = False
    early_stop_threshold: int = 0
    votes: dict = field(default_factory=dict)
    attempts: list = field(default_factory=list)
    # Wave 1 classification data
    wave1_taxonomies: list = field(default_factory=list)  # selected taxonomies
    wave1_votes: dict = field(default_factory=dict)       # taxonomy -> vote count
    wave1_time: float = 0.0                               # total Wave 1 time
    wave1_attempts: int = 0                                # number of classification attempts
    wave1_failures: int = 0                                # failed classification attempts
    wave1_notes_chars: int = 0                             # length of injected notes
    has_wave1: bool = False                                # whether Wave 1 ran
    is_basic: bool = False                                 # basic.basic.basic detected
    is_rerun: bool = False                                 # whether problem got rerun (48 attempts)


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_log(filepath: str) -> list:
    """Parse diagnostic.log into list of Problem objects."""
    with open(filepath, 'r', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    problems = []
    current_problem = None
    current_attempt = None
    current_turn = None
    current_batch = ""
    in_reasoning = in_code = in_output = False
    reasoning_buf, code_buf, output_buf = [], [], []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Batch header ──
        batch_match = re.match(r'\s*(?:BATCH:\s*)?(.+?)\s*\((\d+)\s*problems?\)', stripped)
        if batch_match:
            candidate = batch_match.group(1).strip()
            # Only accept known batch name patterns
            known = ['REFERENCE', 'PRIORITY', 'AT-RISK', 'VAL BENCH', 'DOUBLE-RUN',
                     'HARD', 'COMPREHENSIVE', 'RANDOM', 'RETRY']
            if any(k in candidate.upper() for k in known):
                current_batch = candidate
                i += 1
                continue

        # ── Problem header: [idx/total] Problem id=XXX or [idx/total] Problem XXX ──
        prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
        if prob_match:
            _flush_all(current_attempt, current_turn, in_reasoning, reasoning_buf, in_code, code_buf, in_output, output_buf)
            in_reasoning = in_code = in_output = False
            reasoning_buf, code_buf, output_buf = [], [], []
            current_turn = None

            current_problem = Problem(
                problem_id=prob_match.group(3),
                batch_name=current_batch,
                batch_idx=int(prob_match.group(1)),
                batch_total=int(prob_match.group(2)),
            )
            current_attempt = None
            problems.append(current_problem)

            # Check if Expected is on same line (v23 format)
            exp_on_line = re.search(r'Expected:\s*(\d+)', stripped)
            if exp_on_line:
                current_problem.expected = int(exp_on_line.group(1))
            i += 1
            continue

        # ── Problem text ──
        if stripped.startswith('Problem:') and current_problem and not current_problem.problem_text:
            current_problem.problem_text = stripped[8:].strip()[:300]
            i += 1
            continue

        # ── Wave 1 classification header ──
        if stripped == 'WAVE 1: CLASSIFICATION' and current_problem:
            current_problem.has_wave1 = True
            # Look for Budget: Ns | Attempts: M on the line after the '===...' separator
            j = i + 1
            while j < len(lines) and j < i + 5:
                w1_budget_match = re.match(r'\s*Budget:\s*\d+s?\s*\|\s*Attempts:\s*(\d+)', lines[j].strip())
                if w1_budget_match:
                    current_problem.wave1_attempts = int(w1_budget_match.group(1))
                    break
                j += 1
            i += 1
            continue

        # ── Wave 1 classification failures ──
        if stripped.startswith('Classification failed:') and current_problem and current_problem.has_wave1:
            current_problem.wave1_failures += 1
            i += 1
            continue

        # ── Wave 1 classification results (extract times) ──
        w1_result_match = re.match(r'\s*Classification results\s*\((\d+)\s*attempts?\)', stripped)
        if w1_result_match and current_problem and current_problem.has_wave1:
            # Parse individual attempt lines that follow
            j = i + 1
            while j < len(lines):
                aline = lines[j].strip()
                attempt_match = re.match(r'\s*Attempt\s+\d+:\s*(.+?)\s*\(conf=([\d.]+),\s*turns=\d+,\s*time=([\d.]+)s\)', aline)
                if attempt_match:
                    time_val = float(attempt_match.group(3))
                    current_problem.wave1_time += time_val
                    taxonomy_val = attempt_match.group(1).strip()
                    # Strip leading \text{ artifacts from LaTeX
                    taxonomy_val = re.sub(r'^\\text\{', '', taxonomy_val)
                    if 'basic.basic.basic' in taxonomy_val:
                        current_problem.is_basic = True
                    j += 1
                elif aline == '' or aline.startswith('===') or aline.startswith('Wave') or aline.startswith('Classification'):
                    break
                else:
                    j += 1
            i += 1
            continue

        # ── Wave 1 taxonomy votes ──
        if stripped == '=== WAVE 1 TAXONOMY VOTES ===' and current_problem and current_problem.has_wave1:
            j = i + 1
            while j < len(lines):
                vline = lines[j].strip()
                if vline == '=== END VOTES ===':
                    break
                # Parse: taxonomy: N.N votes [<-- SELECTED]
                vote_match = re.match(r'\s*(.+?):\s*([\d.]+)\s*votes', vline)
                if vote_match:
                    tax_name = vote_match.group(1).strip()
                    # Strip leading \text{ artifacts from LaTeX
                    tax_name = re.sub(r'^\\text\{', '', tax_name)
                    vote_count = float(vote_match.group(2))
                    current_problem.wave1_votes[tax_name] = vote_count
                    if 'basic.basic.basic' in tax_name:
                        current_problem.is_basic = True
                j += 1
            i = j + 1 if j < len(lines) else j
            continue

        # ── Wave 1 result ──
        w1_res_match = re.match(r"\s*Wave 1 result:\s*\[([^\]]*)\]", stripped)
        if w1_res_match and current_problem and current_problem.has_wave1:
            result_str = w1_res_match.group(1).strip()
            if result_str:
                # Parse list of quoted taxonomy strings
                current_problem.wave1_taxonomies = [
                    t.strip().strip("'\"") for t in result_str.split(',') if t.strip()
                ]
                if any('basic.basic.basic' in t for t in current_problem.wave1_taxonomies):
                    current_problem.is_basic = True
            i += 1
            continue

        # ── Wave 1 DB retrieval (notes chars) ──
        w1_notes_match = re.match(r'\s*Notes:\s*(\d+)\s*chars', stripped)
        if w1_notes_match and current_problem and current_problem.has_wave1 and current_problem.wave1_notes_chars == 0:
            current_problem.wave1_notes_chars = int(w1_notes_match.group(1))
            i += 1
            continue

        # ── Budget ──
        budget_match = re.match(r'\s*Budget:\s*([\d.]+)\s*seconds\s*\|\s*Deadline:\s*([\d.]+)', stripped)
        if budget_match and current_problem:
            current_problem.budget = float(budget_match.group(1))
            current_problem.deadline = float(budget_match.group(2))
            i += 1
            continue

        # ── Final Answer ──
        fa_match = re.match(r'\s*Final Answer:\s*(\d+)', stripped)
        if fa_match and current_problem:
            current_problem.predicted = int(fa_match.group(1))
            i += 1
            continue

        # ── Result: >> CORRECT / >> WRONG ──
        if stripped.startswith('>> CORRECT') and current_problem:
            current_problem.correct = True
            i += 1
            continue
        if stripped.startswith('>> WRONG') and current_problem:
            current_problem.correct = False
            i += 1
            continue

        # ── Stats: Predicted/Expected/Wall time ──
        stats_match = re.match(r'\s*Predicted:\s*(\d+)\s*\|\s*Expected:\s*(\d+)\s*\|\s*Wall time:\s*([\d.]+)s', stripped)
        if stats_match and current_problem:
            current_problem.predicted = int(stats_match.group(1))
            current_problem.expected = int(stats_match.group(2))
            current_problem.wall_time = float(stats_match.group(3))
            i += 1
            continue

        # ── Stats: Attempts answered ──
        att_match = re.match(r'\s*Attempts answered:\s*(\d+)/(\d+)\s*\|\s*Code calls:\s*(\d+)\s*\|\s*Errors:\s*(\d+)\s*\|\s*Tokens:\s*(\d+)', stripped)
        if att_match and current_problem:
            current_problem.total_answered = int(att_match.group(1))
            current_problem.total_attempts = int(att_match.group(2))
            current_problem.total_code_calls = int(att_match.group(3))
            current_problem.total_errors = int(att_match.group(4))
            current_problem.total_tokens = int(att_match.group(5))
            i += 1
            continue

        # ── Early stop ──
        es_match = re.match(r'\s*Avg entropy:\s*([\d.]+)\s*\|\s*Early stop:\s*(Yes|No)(?:\s*\(threshold=(\d+)\))?', stripped)
        if es_match and current_problem:
            current_problem.avg_entropy = float(es_match.group(1))
            current_problem.early_stop = es_match.group(2) == 'Yes'
            if es_match.group(3):
                current_problem.early_stop_threshold = int(es_match.group(3))
            i += 1
            continue

        # ── Votes: [answer: N votes, ...] ──
        votes_match = re.match(r'\s*Votes:\s*\[(.+)\]', stripped)
        if votes_match and current_problem:
            vote_str = votes_match.group(1)
            for vm in re.finditer(r'(\d+):\s*(\d+)\s*vote', vote_str):
                current_problem.votes[int(vm.group(1))] = int(vm.group(2))
            i += 1
            continue

        # ── Votes: {answer: count, ...} (v23) ──
        votes_match2 = re.match(r'\s*Votes:\s*(\{.+\})', stripped)
        if votes_match2 and current_problem:
            try:
                vd = json.loads(votes_match2.group(1).replace("'", '"'))
                current_problem.votes = {int(k): int(v) for k, v in vd.items()}
            except (json.JSONDecodeError, ValueError):
                vote_str = votes_match2.group(1)
                for vm in re.finditer(r'(\d+):\s*(\d+)', vote_str):
                    current_problem.votes[int(vm.group(1))] = int(vm.group(2))
            i += 1
            continue

        # ── v23 STATUS line ──
        status_match = re.match(r'\s*STATUS:\s*(CORRECT|WRONG)\s*\|\s*Predicted:\s*(\d+)\s*\|\s*Expected:\s*(\d+)\s*\|\s*Time:\s*([\d.]+)s', stripped)
        if status_match and current_problem:
            current_problem.correct = status_match.group(1) == 'CORRECT'
            current_problem.predicted = int(status_match.group(2))
            current_problem.expected = int(status_match.group(3))
            current_problem.wall_time = float(status_match.group(4))
            i += 1
            continue

        # ── v23 combined stats: Votes: ... | Answers: N | Nones: N | Errors: N | ES: True/False ──
        van_match = re.match(r'\s*Votes:.*\|\s*Answers:\s*(\d+)\s*\|\s*Nones:\s*(\d+)\s*\|\s*Errors:\s*(\d+)\s*\|\s*ES:\s*(True|False)', stripped)
        if van_match and current_problem:
            current_problem.total_answered = int(van_match.group(1))
            nones = int(van_match.group(2))
            current_problem.total_errors = int(van_match.group(3))
            current_problem.early_stop = van_match.group(4) == 'True'
            current_problem.total_attempts = current_problem.total_answered + nones
            i += 1
            continue

        # ── Attempt header (v22/v23): ATTEMPT N | answer=X [temp=T] entropy=Y code_calls=Z errors=W tokens=T time=Xs ──
        att_hdr = re.match(
            r'\s*ATTEMPT\s+(\d+)\s*\|\s*answer=(\S+)\s+(?:temp=([\d.]+)\s+)?entropy=([\d.]+)\s+code_calls=(\d+)\s+errors=(\d+)\s+tokens=(\d+)\s+time=([\d.]+)s',
            stripped
        )
        if att_hdr:
            _flush_all(current_attempt, current_turn, in_reasoning, reasoning_buf, in_code, code_buf, in_output, output_buf)
            in_reasoning = in_code = in_output = False
            reasoning_buf, code_buf, output_buf = [], [], []
            current_turn = None

            ans_str = att_hdr.group(2)
            ans = None if ans_str == 'None' else int(ans_str)
            temp_str = att_hdr.group(3)
            temp = float(temp_str) if temp_str else None
            current_attempt = Attempt(
                attempt_num=int(att_hdr.group(1)),
                answer=ans,
                entropy=float(att_hdr.group(4)),
                code_calls=int(att_hdr.group(5)),
                errors=int(att_hdr.group(6)),
                tokens=int(att_hdr.group(7)),
                time_s=float(att_hdr.group(8)),
                temperature=temp,
                is_none=(ans is None),
            )
            if current_problem:
                current_problem.attempts.append(current_attempt)
            i += 1
            continue

        # ── Attempt header (v23): --- Attempt N [STATUS] answer=X expected=Y temp=T entropy=E --- ──
        att_hdr2 = re.match(
            r'\s*---\s*Attempt\s+(\d+)\s*\[(\w+)\]\s*answer=(\S+)\s+expected=(\S+)\s+temp=([\d.?]+)\s+entropy=([\d.]+)',
            stripped
        )
        if att_hdr2:
            _flush_all(current_attempt, current_turn, in_reasoning, reasoning_buf, in_code, code_buf, in_output, output_buf)
            in_reasoning = in_code = in_output = False
            reasoning_buf, code_buf, output_buf = [], [], []
            current_turn = None

            ans_str = att_hdr2.group(3)
            ans = None if ans_str == 'None' else int(ans_str)
            temp_str = att_hdr2.group(5)
            temp = None if temp_str == '?' else float(temp_str)
            current_attempt = Attempt(
                attempt_num=int(att_hdr2.group(1)),
                answer=ans,
                entropy=float(att_hdr2.group(6)),
                temperature=temp,
                is_none=(ans is None),
            )
            if current_problem:
                current_problem.attempts.append(current_attempt)
                if current_problem.expected is None:
                    exp_str = att_hdr2.group(4)
                    if exp_str not in ('None', '?'):
                        current_problem.expected = int(exp_str)
            i += 1
            continue

        # ── v23 attempt stats: python_calls=N errors=M tokens=T time=Xs ──
        att_stats = re.match(r'\s*python_calls=(\d+)\s+errors=(\d+)\s+tokens=(\d+)\s+time=([\d.]+)s', stripped)
        if att_stats and current_attempt:
            current_attempt.code_calls = int(att_stats.group(1))
            current_attempt.errors = int(att_stats.group(2))
            current_attempt.tokens = int(att_stats.group(3))
            current_attempt.time_s = float(att_stats.group(4))
            i += 1
            continue

        # ── Libraries ──
        lib_match = re.match(r'\s*Libraries:\s*(.+)', stripped)
        if lib_match and current_attempt:
            current_attempt.libraries = [l.strip() for l in lib_match.group(1).split(',')]
            i += 1
            continue

        # ── Turn header: [Turn N] or [Turn N REASONING] or [Turn N CODE] or [Turn N CODE [ERROR]] ──
        turn_match = re.match(r'\s*\[Turn\s+(\d+)(?:\s+(REASONING|CODE))?(?:\s*\[ERROR\])?\]', stripped)
        if turn_match:
            _flush_all(current_attempt, current_turn, in_reasoning, reasoning_buf, in_code, code_buf, in_output, output_buf)
            in_reasoning = in_code = in_output = False
            reasoning_buf, code_buf, output_buf = [], [], []

            current_turn = Turn(turn_num=int(turn_match.group(1)))
            if 'ERROR' in stripped:
                current_turn.is_error = True

            section = turn_match.group(2)
            if section == 'REASONING':
                in_reasoning = True
            elif section == 'CODE':
                in_code = True
            i += 1
            continue

        # ── Reasoning header ──
        r_match = re.match(r'\s*\[Reasoning\]\s*\((\d+)\s*chars?\)', stripped)
        if r_match:
            in_reasoning = True
            in_code = in_output = False
            if current_turn:
                current_turn.reasoning_chars = int(r_match.group(1))
            i += 1
            continue

        # ── Code header: [Code]: or [Code] [ERROR]: ──
        if (stripped.startswith('[Code]') and stripped.endswith(':')) or stripped.startswith('>>> Code:'):
            _flush_section(current_turn, 'reasoning', reasoning_buf)
            reasoning_buf = []
            in_reasoning = False
            in_code = True
            in_output = False
            if current_turn and '[ERROR]' in stripped:
                current_turn.is_error = True
            i += 1
            continue

        # ── Output header: [Output]: or [Output] [ERROR]: ──
        if (stripped.startswith('[Output]') and stripped.endswith(':')) or stripped.startswith('>>> Output:'):
            _flush_section(current_turn, 'code', code_buf)
            code_buf = []
            in_reasoning = False
            in_code = False
            in_output = True
            if current_turn and '[ERROR]' in stripped:
                current_turn.is_error = True
            i += 1
            continue

        # ── Content accumulation ──
        content_line = line
        for prefix in ['       | ', '       > ', '            ', '        ']:
            if content_line.startswith(prefix):
                content_line = content_line[len(prefix):]
                break

        if in_reasoning:
            reasoning_buf.append(content_line)
        elif in_code:
            code_buf.append(content_line)
        elif in_output:
            output_buf.append(content_line)
            # Detect errors in output content
            if current_turn and not current_turn.is_error:
                if re.search(r'(Traceback|Error:|Exception:|timed out)', stripped):
                    current_turn.is_error = True

        i += 1

    # Flush final state
    _flush_all(current_attempt, current_turn, in_reasoning, reasoning_buf, in_code, code_buf, in_output, output_buf)

    # Post-process
    for p in problems:
        if p.expected is None and p.correct and p.predicted is not None:
            p.expected = p.predicted
        if not p.wall_time and p.attempts:
            p.wall_time = max((a.time_s for a in p.attempts), default=0)
        if not p.total_attempts and p.attempts:
            p.total_attempts = len(p.attempts)
        if not p.total_answered and p.attempts:
            p.total_answered = sum(1 for a in p.attempts if not a.is_none)
        # Detect reruns: more than 24 attempts means the problem was rerun
        if len(p.attempts) > 24:
            p.is_rerun = True

    return problems


def _flush_section(turn, name, buf):
    if turn and buf:
        text = '\n'.join(buf).strip()
        if name == 'reasoning':
            turn.reasoning_text = text
        elif name == 'code':
            turn.code = text
        elif name == 'output':
            turn.output = text


def _flush_all(attempt, turn, in_r, r_buf, in_c, c_buf, in_o, o_buf):
    if turn:
        if in_r: _flush_section(turn, 'reasoning', r_buf)
        if in_c: _flush_section(turn, 'code', c_buf)
        if in_o: _flush_section(turn, 'output', o_buf)
        if attempt:
            attempt.turns.append(turn)


def _extract_error_type(output_text):
    """Extract clean error type from traceback output."""
    if not output_text:
        return None
    for line in output_text.split('\n'):
        line = line.strip()
        # Match "SomeError: message" pattern at start of line
        m = re.match(r'^([A-Z]\w*Error|[A-Z]\w*Exception|[A-Z]\w*Warning):\s*', line)
        if m:
            return m.group(1)
    return None


def _extract_error_message(output_text):
    """Extract full error line from traceback."""
    if not output_text:
        return ""
    for line in reversed(output_text.split('\n')):
        line = line.strip()
        if re.match(r'^[A-Z]\w*(Error|Exception):', line):
            return line[:100]
    return ""


def _vote_margin(p):
    if not p.votes or len(p.votes) < 2:
        return 99
    sv = sorted(p.votes.values(), reverse=True)
    return sv[0] - sv[1]


# ── Queries ──────────────────────────────────────────────────────────────────

def q_summary(problems):
    total = len(problems)
    correct = sum(1 for p in problems if p.correct)
    total_time = sum(p.wall_time for p in problems)
    total_att = sum(len(p.attempts) for p in problems)
    total_nones = sum(1 for p in problems for a in p.attempts if a.is_none)
    total_errors = sum(a.errors for p in problems for a in p.attempts)

    print(f"{'='*60}")
    print(f"  LOG SUMMARY")
    print(f"{'='*60}")
    print(f"  Score: {correct}/{total} ({correct/max(total,1)*100:.1f}%)")
    print(f"  Total wall time: {total_time:.0f}s ({total_time/60:.1f} min)")
    print(f"  Total attempts: {total_att}")
    print(f"  Total Nones: {total_nones}/{total_att} ({total_nones/max(total_att,1)*100:.1f}%)")
    print(f"  Total code errors: {total_errors}")
    times = [p.wall_time for p in problems if p.wall_time > 0]
    if times:
        print(f"  Problem time: min={min(times):.0f}s  max={max(times):.0f}s  avg={sum(times)/len(times):.0f}s  median={sorted(times)[len(times)//2]:.0f}s")

    # Batch breakdown
    batches = defaultdict(list)
    for p in problems:
        batches[p.batch_name or 'unknown'].append(p)
    print(f"\n  {'Batch':<35} {'Score':>8} {'Time':>8} {'Nones':>8}")
    print(f"  {'─'*35} {'─'*8} {'─'*8} {'─'*8}")
    for bname, bprobs in batches.items():
        bc = sum(1 for p in bprobs if p.correct)
        bt = sum(p.wall_time for p in bprobs)
        bn = sum(1 for p in bprobs for a in p.attempts if a.is_none)
        print(f"  {bname:<35} {bc}/{len(bprobs):>5} {bt:>6.0f}s {bn:>8}")


def q_problems(problems):
    print(f"  {'ID':<8} {'Batch':<20} {'OK':>3} {'Pred':>6} {'Exp':>6} {'Time':>6} {'Att':>4} {'Ans':>4} {'None':>5} {'Err':>4} {'ES':>3} {'Budget':>7}")
    print(f"  {'─'*8} {'─'*20} {'─'*3} {'─'*6} {'─'*6} {'─'*6} {'─'*4} {'─'*4} {'─'*5} {'─'*4} {'─'*3} {'─'*7}")
    for p in problems:
        ok = 'Y' if p.correct else 'N'
        es = 'Y' if p.early_stop else 'N'
        nones = sum(1 for a in p.attempts if a.is_none)
        errs = sum(a.errors for a in p.attempts)
        pred = str(p.predicted) if p.predicted is not None else '-'
        exp = str(p.expected) if p.expected is not None else '-'
        batch = (p.batch_name or '-')[:20]
        print(f"  {p.problem_id:<8} {batch:<20} {ok:>3} {pred:>6} {exp:>6} {p.wall_time:>5.0f}s {len(p.attempts):>4} {p.total_answered:>4} {nones:>5} {errs:>4} {es:>3} {p.budget:>6.0f}s")


def q_timeline(problems):
    """Chronological view with cumulative stats."""
    cum_correct = 0
    cum_time = 0.0
    print(f"  {'#':>3} {'ID':<8} {'OK':>3} {'Time':>6} {'CumTime':>8} {'CumScore':>10} {'Budget':>7} {'Batch':<20}")
    print(f"  {'─'*3} {'─'*8} {'─'*3} {'─'*6} {'─'*8} {'─'*10} {'─'*7} {'─'*20}")
    for i, p in enumerate(problems):
        cum_correct += int(p.correct)
        cum_time += p.wall_time
        ok = 'Y' if p.correct else 'N'
        batch = (p.batch_name or '-')[:20]
        print(f"  {i+1:>3} {p.problem_id:<8} {ok:>3} {p.wall_time:>5.0f}s {cum_time:>7.0f}s {cum_correct:>4}/{i+1:<4} {p.budget:>6.0f}s {batch:<20}")


def q_failures(problems):
    wrong = [p for p in problems if not p.correct]
    if not wrong:
        print("  No failures!")
        return
    print(f"  {len(wrong)} FAILURES:\n")
    for p in wrong:
        print(f"  {p.problem_id} ({p.batch_name})")
        print(f"    Predicted: {p.predicted} | Expected: {p.expected} | Time: {p.wall_time:.0f}s")
        if p.votes:
            print(f"    Votes: {dict(sorted(p.votes.items(), key=lambda x: -x[1]))}")
        ans_map = {a.attempt_num: a.answer for a in p.attempts}
        correct_att = [n for n, a in ans_map.items() if a == p.expected]
        wrong_att = [n for n, a in ans_map.items() if a is not None and a != p.expected]
        none_att = [n for n, a in ans_map.items() if a is None]
        if correct_att:
            print(f"    Correct attempts (outvoted): {correct_att}")
        if wrong_att:
            print(f"    Wrong attempts: {wrong_att} → {[ans_map[n] for n in wrong_att]}")
        if none_att:
            print(f"    None attempts: {none_att}")

        # Show error summary per attempt
        for a in p.attempts:
            if a.errors > 0:
                errs = []
                for t in a.turns:
                    et = _extract_error_type(t.output)
                    if et:
                        errs.append(et)
                if errs:
                    print(f"    Attempt {a.attempt_num} errors: {', '.join(errs)}")
        print()


def q_nones(problems):
    print(f"  {'ID':<8} {'Att':>4} {'Temp':>5} {'Errs':>5} {'Turns':>6} {'Tokens':>7} {'Time':>6} {'Reason':<30}")
    print(f"  {'─'*8} {'─'*4} {'─'*5} {'─'*5} {'─'*6} {'─'*7} {'─'*6} {'─'*30}")
    total = 0
    for p in problems:
        for a in p.attempts:
            if not a.is_none:
                continue
            total += 1
            temp_s = f"{a.temperature:.1f}" if a.temperature is not None else "?"
            reason = _classify_none(a)
            print(f"  {p.problem_id:<8} {a.attempt_num:>4} {temp_s:>5} {a.errors:>5} {len(a.turns):>6} {a.tokens:>7} {a.time_s:>5.1f}s {reason:<30}")
    print(f"\n  Total Nones: {total}")


def _classify_none(a):
    """Classify why an attempt returned None."""
    if not a.turns:
        return "no-turns"
    if a.errors > 0:
        last_err = None
        for t in reversed(a.turns):
            et = _extract_error_type(t.output)
            if et:
                last_err = et
                break
        if last_err:
            return f"error:{last_err}"
    # Check if model produced code
    has_code = any(t.code for t in a.turns)
    if not has_code:
        return "no-code-generated"
    # Check for timeout in any turn's output
    for t in a.turns:
        if t.output and 'timed out' in t.output.lower():
            return "timeout"
    # Check reasoning for "answer is" patterns (extraction failure)
    all_reasoning = ' '.join(t.reasoning_text or '' for t in a.turns)
    lower_reasoning = all_reasoning.lower()
    answer_patterns = ['the answer is', 'final answer', 'answer =', 'answer:', 'therefore',
                       'we get', 'the result is', 'thus the answer', 'our answer']
    if any(p in lower_reasoning for p in answer_patterns):
        return "extraction-failure"
    # Check if last turn had output with actual content but no answer extracted
    last_turn = a.turns[-1]
    last_output = (last_turn.output or '').strip()
    if last_output and last_output not in ('[WARN] No output. Use print() to see results.',):
        return "output-not-extracted"
    # Check if reasoning appears truncated (ran out of tokens)
    last_reasoning = (last_turn.reasoning_text or '').rstrip()
    if last_reasoning and not last_reasoning.endswith(('.', ':', ')', ']', '}', '"', "'", '?', '!')):
        return "reasoning-truncated"
    # Check for WARN no output (code ran but produced nothing)
    for t in a.turns:
        if t.output and 'WARN' in t.output and 'No output' in t.output:
            return "no-print-output"
    return "unknown-no-answer"


def q_none_reasons(problems):
    """Breakdown of why Nones happened."""
    reasons = Counter()
    for p in problems:
        for a in p.attempts:
            if a.is_none:
                reasons[_classify_none(a)] += 1

    total = sum(reasons.values())
    print(f"  None Reason Breakdown ({total} total):\n")
    for reason, count in reasons.most_common():
        pct = count / max(total, 1) * 100
        print(f"  {count:>5} ({pct:>5.1f}%)  {reason}")


def q_close_votes(problems, max_margin=2):
    close = [p for p in problems if 0 < _vote_margin(p) <= int(max_margin)]
    print(f"  Close votes (margin ≤ {max_margin}): {len(close)}\n")
    for p in sorted(close, key=lambda x: _vote_margin(x)):
        ok = 'Y' if p.correct else 'N'
        votes = dict(sorted(p.votes.items(), key=lambda x: -x[1]))
        print(f"  {p.problem_id} [{ok}] margin={_vote_margin(p)} votes={votes}")
        if p.expected is not None and not p.correct:
            cv = p.votes.get(p.expected, 0)
            print(f"    Expected {p.expected} had {cv} votes — outvoted!")


def q_outvoted(problems):
    """Problems where the correct answer existed but lost the vote."""
    outvoted = []
    for p in problems:
        if p.correct:
            continue
        if p.expected is None:
            continue
        correct_votes = p.votes.get(p.expected, 0)
        if correct_votes > 0:
            outvoted.append(p)

    print(f"  {len(outvoted)} problems had correct answer but lost vote:\n")
    for p in outvoted:
        votes = dict(sorted(p.votes.items(), key=lambda x: -x[1]))
        winning_ans = max(p.votes, key=p.votes.get)
        print(f"  {p.problem_id}: expected={p.expected} got {p.votes.get(p.expected, 0)} votes, winner={winning_ans} got {p.votes[winning_ans]} votes")
        print(f"    All votes: {votes}")
        # Show entropy of correct vs wrong attempts
        correct_entropies = [a.entropy for a in p.attempts if a.answer == p.expected]
        wrong_entropies = [a.entropy for a in p.attempts if a.answer is not None and a.answer != p.expected]
        if correct_entropies:
            print(f"    Correct entropy: {[f'{e:.3f}' for e in correct_entropies]}")
        if wrong_entropies:
            print(f"    Wrong entropy: {[f'{e:.3f}' for e in wrong_entropies]}")
        print()


def q_attempts(problems, pid):
    target = [p for p in problems if p.problem_id.startswith(pid)]
    if not target:
        print(f"  No problem matching '{pid}'")
        return
    for p in target:
        print(f"  Problem {p.problem_id} ({p.batch_name})")
        print(f"  Expected: {p.expected} | Predicted: {p.predicted} | {'CORRECT' if p.correct else 'WRONG'}")
        print(f"  Budget: {p.budget:.0f}s | Wall time: {p.wall_time:.0f}s")
        print(f"  Text: {p.problem_text[:200]}...")
        print()
        for a in p.attempts:
            status = "CORRECT" if a.answer == p.expected else ("NONE" if a.is_none else "WRONG")
            temp_s = f"temp={a.temperature:.1f}" if a.temperature is not None else ""
            print(f"  Attempt {a.attempt_num} [{status}] answer={a.answer} entropy={a.entropy:.3f} {temp_s}")
            print(f"    calls={a.code_calls} errors={a.errors} tokens={a.tokens} time={a.time_s:.1f}s")
            if a.libraries:
                print(f"    libs: {', '.join(a.libraries)}")
            for t in a.turns:
                err = " [ERR]" if t.is_error else ""
                code_s = f" code={len(t.code)}ch" if t.code else ""
                out_s = f" out={len(t.output)}ch" if t.output else ""
                print(f"      T{t.turn_num}: reasoning={t.reasoning_chars}ch{code_s}{out_s}{err}")
                if t.is_error:
                    msg = _extract_error_message(t.output)
                    if msg:
                        print(f"        >> {msg}")
            print()


def q_temp(problems, temp_val):
    temp_f = float(temp_val)
    eps = 0.05
    matching = [(p, a) for p in problems for a in p.attempts
                if a.temperature is not None and abs(a.temperature - temp_f) < eps]
    if not matching:
        print(f"  No attempts at temperature ~{temp_f}")
        temps = sorted({a.temperature for p in problems for a in p.attempts if a.temperature is not None})
        if temps:
            print(f"  Available: {temps}")
        return
    total = len(matching)
    correct = sum(1 for p, a in matching if a.answer == p.expected)
    nones = sum(1 for _, a in matching if a.is_none)
    wrong = total - correct - nones
    print(f"  Temperature ~{temp_f}: {total} attempts")
    print(f"    Correct: {correct} ({correct/total*100:.1f}%)")
    print(f"    Wrong:   {wrong} ({wrong/total*100:.1f}%)")
    print(f"    None:    {nones} ({nones/total*100:.1f}%)")
    print(f"    Avg entropy: {sum(a.entropy for _, a in matching)/total:.3f}")
    print(f"    Avg time: {sum(a.time_s for _, a in matching)/total:.1f}s")
    print(f"    Avg tokens: {sum(a.tokens for _, a in matching)/total:.0f}")


def q_temps(problems):
    by_temp = defaultdict(lambda: {'total': 0, 'correct': 0, 'none': 0, 'wrong': 0, 'entropy': [], 'time': [], 'tokens': []})
    for p in problems:
        for a in p.attempts:
            t = a.temperature if a.temperature is not None else -1
            key = f"{t:.2f}" if t >= 0 else "unknown"
            by_temp[key]['total'] += 1
            if a.answer == p.expected:
                by_temp[key]['correct'] += 1
            elif a.is_none:
                by_temp[key]['none'] += 1
            else:
                by_temp[key]['wrong'] += 1
            by_temp[key]['entropy'].append(a.entropy)
            by_temp[key]['time'].append(a.time_s)
            by_temp[key]['tokens'].append(a.tokens)

    print(f"  {'Temp':>7} {'Total':>6} {'Corr':>6} {'Wrong':>6} {'None':>6} {'%Corr':>6} {'%None':>6} {'AvgEnt':>7} {'AvgTok':>7} {'AvgTime':>8}")
    print(f"  {'─'*7} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*7} {'─'*7} {'─'*8}")
    for key in sorted(by_temp.keys()):
        d = by_temp[key]
        n = d['total']
        print(f"  {key:>7} {n:>6} {d['correct']:>6} {d['wrong']:>6} {d['none']:>6} "
              f"{d['correct']/n*100:>5.1f}% {d['none']/n*100:>5.1f}% "
              f"{sum(d['entropy'])/n:>7.3f} {sum(d['tokens'])/n:>6.0f} {sum(d['time'])/n:>7.1f}s")


def q_slow(problems, threshold=600):
    slow = [(p, p.wall_time) for p in problems if p.wall_time >= int(threshold)]
    slow.sort(key=lambda x: -x[1])
    print(f"  Problems ≥{threshold}s: {len(slow)}\n")
    for p, t in slow:
        es = "ES" if p.early_stop else "no-ES"
        print(f"  {p.problem_id} {t:>6.0f}s {'OK' if p.correct else 'FAIL'} budget={p.budget:.0f}s {es} {p.batch_name}")


def q_budget(problems):
    print(f"  {'ID':<8} {'Budget':>7} {'Actual':>7} {'Util%':>6} {'OK':>3} {'Batch':<25}")
    print(f"  {'─'*8} {'─'*7} {'─'*7} {'─'*6} {'─'*3} {'─'*25}")
    for p in problems:
        util = (p.wall_time / p.budget * 100) if p.budget > 0 else 0
        ok = 'Y' if p.correct else 'N'
        batch = (p.batch_name or '-')[:25]
        print(f"  {p.problem_id:<8} {p.budget:>6.0f}s {p.wall_time:>6.0f}s {util:>5.1f}% {ok:>3} {batch:<25}")
    budgets = sorted({int(p.budget) for p in problems if p.budget > 0})
    if budgets:
        print(f"\n  Unique budgets: {budgets}")


def q_efficiency(problems):
    """Tokens and time per correct vs wrong vs none answer."""
    correct_tok, wrong_tok, none_tok = [], [], []
    correct_time, wrong_time, none_time = [], [], []
    for p in problems:
        for a in p.attempts:
            if a.answer == p.expected:
                correct_tok.append(a.tokens)
                correct_time.append(a.time_s)
            elif a.is_none:
                none_tok.append(a.tokens)
                none_time.append(a.time_s)
            else:
                wrong_tok.append(a.tokens)
                wrong_time.append(a.time_s)

    def _stats(label, toks, times):
        n = len(toks)
        if n == 0:
            print(f"  {label}: (none)")
            return
        avg_t = sum(toks) / n
        avg_s = sum(times) / n
        print(f"  {label}: n={n}  avg_tokens={avg_t:.0f}  avg_time={avg_s:.1f}s  total_tokens={sum(toks)}")

    print(f"  Efficiency Analysis:\n")
    _stats("Correct", correct_tok, correct_time)
    _stats("Wrong  ", wrong_tok, wrong_time)
    _stats("None   ", none_tok, none_time)

    # Wasted compute: tokens spent on wrong + none answers
    wasted = sum(wrong_tok) + sum(none_tok)
    useful = sum(correct_tok)
    total = wasted + useful
    print(f"\n  Useful tokens: {useful:,} ({useful/max(total,1)*100:.1f}%)")
    print(f"  Wasted tokens: {wasted:,} ({wasted/max(total,1)*100:.1f}%)")


def q_early_stops(problems):
    es = [p for p in problems if p.early_stop]
    no_es = [p for p in problems if not p.early_stop and p.attempts]

    print(f"  Early stopped: {len(es)}/{len(problems)}")
    print(f"  Not early stopped: {len(no_es)}/{len(problems)}")

    if es:
        c = sum(1 for p in es if p.correct)
        t = [p.wall_time for p in es if p.wall_time > 0]
        print(f"\n  ES group: {c}/{len(es)} correct ({c/len(es)*100:.0f}%), avg={sum(t)/max(len(t),1):.0f}s")
    if no_es:
        c = sum(1 for p in no_es if p.correct)
        t = [p.wall_time for p in no_es if p.wall_time > 0]
        print(f"  No-ES group: {c}/{len(no_es)} correct ({c/len(no_es)*100:.0f}%), avg={sum(t)/max(len(t),1):.0f}s")


def q_wave1(problems):
    """Wave 1 classification stats per problem."""
    w1_problems = [p for p in problems if p.has_wave1]
    if not w1_problems:
        print("  No Wave 1 data found in this log.")
        return

    total = len(w1_problems)
    with_tax = sum(1 for p in w1_problems if p.wave1_taxonomies)
    no_consensus = total - with_tax
    basic_count = sum(1 for p in w1_problems if p.is_basic)
    total_failures = sum(p.wave1_failures for p in w1_problems)
    total_time = sum(p.wave1_time for p in w1_problems)
    with_notes = sum(1 for p in w1_problems if p.wave1_notes_chars > 0)

    print(f"{'='*70}")
    print(f"  WAVE 1 CLASSIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Problems with Wave 1: {total}/{len(problems)}")
    print(f"  Taxonomy selected: {with_tax} ({with_tax/total*100:.0f}%)")
    print(f"  No consensus: {no_consensus} ({no_consensus/total*100:.0f}%)")
    print(f"  Basic detected: {basic_count}")
    print(f"  Notes injected: {with_notes}")
    print(f"  Total classification failures: {total_failures}")
    print(f"  Total Wave 1 time: {total_time:.0f}s ({total_time/60:.1f} min)")
    print(f"  Avg Wave 1 time: {total_time/total:.1f}s per problem")

    # Accuracy: did Wave 1 help?
    w1_correct = sum(1 for p in w1_problems if p.correct and p.wave1_taxonomies)
    w1_total = sum(1 for p in w1_problems if p.wave1_taxonomies)
    nc_correct = sum(1 for p in w1_problems if p.correct and not p.wave1_taxonomies)
    nc_total = no_consensus
    if w1_total > 0:
        print(f"\n  Taxonomy selected → correct: {w1_correct}/{w1_total} ({w1_correct/w1_total*100:.0f}%)")
    if nc_total > 0:
        print(f"  No consensus → correct: {nc_correct}/{nc_total} ({nc_correct/nc_total*100:.0f}%)")

    # Per-problem details
    print(f"\n  {'ID':<8} {'OK':>3} {'Taxonomy':<45} {'Votes':>6} {'Fails':>6} {'Time':>6} {'Notes':>6}")
    print(f"  {'─'*8} {'─'*3} {'─'*45} {'─'*6} {'─'*6} {'─'*6} {'─'*6}")
    for p in w1_problems:
        ok = 'Y' if p.correct else 'N'
        tax = ', '.join(p.wave1_taxonomies)[:45] if p.wave1_taxonomies else '(no consensus)'
        if p.is_basic and not p.wave1_taxonomies:
            tax = '(no consensus, basic detected)'
        top_votes = max(p.wave1_votes.values()) if p.wave1_votes else 0
        print(f"  {p.problem_id:<8} {ok:>3} {tax:<45} {top_votes:>5.0f} {p.wave1_failures:>6} {p.wave1_time:>5.0f}s {p.wave1_notes_chars:>6}")

    # Top taxonomies across all problems
    tax_counter = Counter()
    for p in w1_problems:
        for t in p.wave1_taxonomies:
            tax_counter[t] += 1
    if tax_counter:
        print(f"\n  Top selected taxonomies:")
        for tax, count in tax_counter.most_common(15):
            print(f"    {count:>3}x  {tax}")


def q_errors(problems):
    print(f"  {'ID':<8} {'Att':>4} {'Turn':>5} {'Type':<20} {'Message':<50}")
    print(f"  {'─'*8} {'─'*4} {'─'*5} {'─'*20} {'─'*50}")
    total = 0
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if t.is_error or (t.output and re.search(r'[A-Z]\w*Error:', t.output)):
                    total += 1
                    etype = _extract_error_type(t.output) or "unknown"
                    msg = _extract_error_message(t.output)
                    msg = msg[len(etype)+2:].strip()[:50] if msg.startswith(etype) else msg[:50]
                    print(f"  {p.problem_id:<8} {a.attempt_num:>4} {t.turn_num:>5} {etype:<20} {msg:<50}")
    print(f"\n  Total error turns: {total}")


def q_errors_by_type(problems):
    types = Counter()
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                et = _extract_error_type(t.output)
                if et:
                    types[et] += 1
    total = sum(types.values())
    print(f"  Error Taxonomy ({total} total):\n")
    for et, count in types.most_common():
        print(f"  {count:>5} ({count/max(total,1)*100:>5.1f}%)  {et}")


def q_errors_by_problem(problems):
    """Error count per problem, sorted by most errors."""
    prob_errors = []
    for p in problems:
        err_count = sum(1 for a in p.attempts for t in a.turns if _extract_error_type(t.output))
        err_types = Counter()
        for a in p.attempts:
            for t in a.turns:
                et = _extract_error_type(t.output)
                if et:
                    err_types[et] += 1
        if err_count > 0:
            prob_errors.append((p, err_count, err_types))

    prob_errors.sort(key=lambda x: -x[1])
    print(f"  {'ID':<8} {'Errors':>7} {'OK':>3} {'Types':<50}")
    print(f"  {'─'*8} {'─'*7} {'─'*3} {'─'*50}")
    for p, count, types in prob_errors:
        ok = 'Y' if p.correct else 'N'
        types_s = ', '.join(f'{t}:{c}' for t, c in types.most_common(5))
        print(f"  {p.problem_id:<8} {count:>7} {ok:>3} {types_s:<50}")


def q_hallucinations(problems):
    """Detect likely hallucinated API calls from error messages."""
    halluc = Counter()
    examples = defaultdict(list)

    patterns = [
        (r"module '(\w+)' has no attribute '(\w+)'", "attr"),
        (r"name '(\w+)' is not defined", "name"),
        (r"unexpected keyword argument '(\w+)'", "kwarg"),
    ]

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if not t.output:
                    continue
                for pat, cat in patterns:
                    for m in re.finditer(pat, t.output):
                        if cat == "attr":
                            key = f"{m.group(1)}.{m.group(2)}"
                        elif cat == "name":
                            key = m.group(1)
                        elif cat == "kwarg":
                            key = f"kwarg:{m.group(1)}"
                        else:
                            key = m.group(0)
                        halluc[key] += 1
                        if len(examples[key]) < 2:
                            examples[key].append(p.problem_id)

    print(f"  Likely Hallucinated APIs ({sum(halluc.values())} total):\n")
    for api, count in halluc.most_common(30):
        ex = ', '.join(examples[api])
        print(f"  {count:>4}x  {api:<40} (e.g. {ex})")


def q_cascades(problems):
    """Analyze error cascades: does an error in turn N lead to more errors?"""
    cascade_yes = 0  # error followed by another error
    cascade_no = 0   # error NOT followed by another error
    first_error_turn = Counter()  # which turn has first error

    for p in problems:
        for a in p.attempts:
            error_turns = [t for t in a.turns if t.is_error or _extract_error_type(t.output)]
            if not error_turns:
                continue
            first_error_turn[error_turns[0].turn_num] += 1
            if len(error_turns) > 1:
                cascade_yes += 1
            else:
                cascade_no += 1

    total = cascade_yes + cascade_no
    print(f"  Error Cascade Analysis:\n")
    print(f"  Attempts with errors: {total}")
    if total:
        print(f"  Single error (recovered): {cascade_no} ({cascade_no/total*100:.0f}%)")
        print(f"  Cascaded (multiple errors): {cascade_yes} ({cascade_yes/total*100:.0f}%)")
    print(f"\n  First error appears at turn:")
    for tn, count in first_error_turn.most_common():
        print(f"    Turn {tn}: {count}")


def q_libraries(problems):
    lib_counter = Counter()
    for p in problems:
        for a in p.attempts:
            for lib in a.libraries:
                lib_counter[lib.strip()] += 1
    print(f"  Library usage:\n")
    for lib, count in lib_counter.most_common():
        print(f"  {count:>5}  {lib}")


def q_turns(problems):
    turn_counts = Counter()
    for p in problems:
        for a in p.attempts:
            turn_counts[len(a.turns)] += 1

    print(f"  Turn count distribution:\n")
    for tc in sorted(turn_counts.keys()):
        bar = '█' * min(turn_counts[tc], 60)
        print(f"  {tc:>3} turns: {turn_counts[tc]:>5}  {bar}")

    # Reasoning depth analysis
    by_turn = defaultdict(list)
    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                by_turn[t.turn_num].append(t.reasoning_chars)
    print(f"\n  Avg reasoning per turn:")
    for tn in sorted(by_turn.keys()):
        chars = by_turn[tn]
        print(f"    Turn {tn}: avg {sum(chars)/len(chars):.0f} chars ({len(chars)} samples)")


def q_code_patterns(problems):
    """Most common functions/patterns in generated code."""
    func_calls = Counter()
    imports = Counter()

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                if not t.code:
                    continue
                # Count function calls
                for m in re.finditer(r'(\w+(?:\.\w+)*)\s*\(', t.code):
                    func = m.group(1)
                    if func not in ('if', 'for', 'while', 'print', 'range', 'len', 'int', 'str', 'float', 'list', 'dict', 'set', 'tuple', 'type', 'isinstance', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'min', 'max', 'sum', 'abs', 'round', 'open', 'format'):
                        func_calls[func] += 1
                # Count imports
                for m in re.finditer(r'(?:from\s+(\S+)\s+)?import\s+(.+)', t.code):
                    pkg = m.group(1) or m.group(2).split(',')[0].strip().split(' ')[0]
                    imports[pkg] += 1

    print(f"  Top function calls:\n")
    for func, count in func_calls.most_common(30):
        print(f"  {count:>5}  {func}")

    print(f"\n  Import frequency:\n")
    for pkg, count in imports.most_common(20):
        print(f"  {count:>5}  {pkg}")


def q_reasoning_length(problems):
    """Reasoning length vs correctness."""
    correct_lens = []
    wrong_lens = []
    none_lens = []

    for p in problems:
        for a in p.attempts:
            total_chars = sum(t.reasoning_chars for t in a.turns)
            if a.answer == p.expected:
                correct_lens.append(total_chars)
            elif a.is_none:
                none_lens.append(total_chars)
            else:
                wrong_lens.append(total_chars)

    def _report(label, lens):
        if not lens:
            print(f"  {label}: (none)")
            return
        print(f"  {label}: n={len(lens)}  avg={sum(lens)/len(lens):.0f}  median={sorted(lens)[len(lens)//2]:.0f}  "
              f"min={min(lens)}  max={max(lens)}")

    print(f"  Reasoning Length Analysis:\n")
    _report("Correct", correct_lens)
    _report("Wrong  ", wrong_lens)
    _report("None   ", none_lens)

    # Histogram
    all_lens = correct_lens + wrong_lens + none_lens
    if all_lens:
        buckets = [0, 1000, 3000, 5000, 10000, 20000, 50000, 999999]
        print(f"\n  {'Range':<15} {'Correct':>8} {'Wrong':>8} {'None':>8} {'%Corr':>6}")
        print(f"  {'─'*15} {'─'*8} {'─'*8} {'─'*8} {'─'*6}")
        for lo, hi in zip(buckets[:-1], buckets[1:]):
            c = sum(1 for x in correct_lens if lo <= x < hi)
            w = sum(1 for x in wrong_lens if lo <= x < hi)
            n = sum(1 for x in none_lens if lo <= x < hi)
            t = c + w + n
            pct = c / max(t, 1) * 100
            label = f"{lo//1000}k-{hi//1000}k" if hi < 999999 else f">{lo//1000}k"
            print(f"  {label:<15} {c:>8} {w:>8} {n:>8} {pct:>5.0f}%")


def q_search(problems, pattern):
    """Search all reasoning and code for a regex pattern."""
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []

    for p in problems:
        for a in p.attempts:
            for t in a.turns:
                for section, text in [('reasoning', t.reasoning_text), ('code', t.code), ('output', t.output)]:
                    if not text:
                        continue
                    for m in regex.finditer(text):
                        start = max(0, m.start() - 40)
                        end = min(len(text), m.end() + 40)
                        context = text[start:end].replace('\n', ' ')
                        matches.append((p.problem_id, a.attempt_num, t.turn_num, section, context))

    print(f"  Search: /{pattern}/ — {len(matches)} matches\n")
    shown = 0
    for pid, att, turn, section, ctx in matches:
        if shown >= 50:
            print(f"  ... and {len(matches) - 50} more")
            break
        print(f"  {pid} att={att} t={turn} [{section}]: ...{ctx}...")
        shown += 1


def q_votes(problems):
    print(f"  {'ID':<8} {'OK':>3} {'Pred':>6} {'Exp':>6} {'Margin':>7} {'Uniq':>5} {'Votes':<30}")
    print(f"  {'─'*8} {'─'*3} {'─'*6} {'─'*6} {'─'*7} {'─'*5} {'─'*30}")
    for p in sorted(problems, key=lambda x: _vote_margin(x)):
        ok = 'Y' if p.correct else 'N'
        pred = str(p.predicted) if p.predicted is not None else '-'
        exp = str(p.expected) if p.expected is not None else '-'
        vs = str(dict(sorted(p.votes.items(), key=lambda x: -x[1])))[:30] if p.votes else '-'
        print(f"  {p.problem_id:<8} {ok:>3} {pred:>6} {exp:>6} {_vote_margin(p):>7} {len(p.votes):>5} {vs:<30}")


def q_json(problems):
    data = []
    for p in problems:
        pd = {
            'id': p.problem_id, 'batch': p.batch_name,
            'correct': p.correct, 'predicted': p.predicted, 'expected': p.expected,
            'wall_time': p.wall_time, 'budget': p.budget,
            'total_attempts': len(p.attempts), 'total_answered': p.total_answered,
            'early_stop': p.early_stop, 'votes': {str(k): v for k, v in p.votes.items()},
            'attempts': [{
                'num': a.attempt_num, 'answer': a.answer, 'entropy': a.entropy,
                'code_calls': a.code_calls, 'errors': a.errors, 'tokens': a.tokens,
                'time_s': a.time_s, 'temperature': a.temperature, 'is_none': a.is_none,
                'turns': len(a.turns), 'libraries': a.libraries,
            } for a in p.attempts]
        }
        data.append(pd)
    print(json.dumps(data, indent=2))


def q_csv(problems):
    print("id,batch,correct,predicted,expected,wall_time,budget,attempts,answered,nones,errors,early_stop,vote_margin,unique_answers")
    for p in problems:
        nones = sum(1 for a in p.attempts if a.is_none)
        errs = sum(a.errors for a in p.attempts)
        print(f"{p.problem_id},{p.batch_name},{p.correct},{p.predicted},{p.expected},{p.wall_time:.1f},{p.budget:.0f},{len(p.attempts)},{p.total_answered},{nones},{errs},{p.early_stop},{_vote_margin(p)},{len(p.votes)}")


def q_attempts_csv(problems):
    """Attempt-level CSV export."""
    print("problem_id,batch,attempt,answer,expected,correct,is_none,entropy,temperature,code_calls,errors,tokens,time_s,turns,libraries")
    for p in problems:
        for a in p.attempts:
            correct = 'True' if a.answer == p.expected else 'False'
            temp = a.temperature if a.temperature is not None else ''
            libs = ';'.join(a.libraries)
            print(f"{p.problem_id},{p.batch_name},{a.attempt_num},{a.answer},{p.expected},{correct},{a.is_none},{a.entropy:.3f},{temp},{a.code_calls},{a.errors},{a.tokens},{a.time_s:.1f},{len(a.turns)},{libs}")


# ── Main ─────────────────────────────────────────────────────────────────────

QUERIES = {
    'summary': (q_summary, 0),
    'problems': (q_problems, 0),
    'timeline': (q_timeline, 0),
    'failures': (q_failures, 0),
    'nones': (q_nones, 0),
    'none-reasons': (q_none_reasons, 0),
    'close-votes': (q_close_votes, 0),
    'outvoted': (q_outvoted, 0),
    'attempts': (q_attempts, 1),
    'temp': (q_temp, 1),
    'temps': (q_temps, 0),
    'slow': (q_slow, 0),
    'budget': (q_budget, 0),
    'efficiency': (q_efficiency, 0),
    'early-stops': (q_early_stops, 0),
    'wave1': (q_wave1, 0),
    'errors': (q_errors, 0),
    'errors-by-type': (q_errors_by_type, 0),
    'errors-by-problem': (q_errors_by_problem, 0),
    'hallucinations': (q_hallucinations, 0),
    'cascades': (q_cascades, 0),
    'libraries': (q_libraries, 0),
    'turns': (q_turns, 0),
    'code-patterns': (q_code_patterns, 0),
    'reasoning-length': (q_reasoning_length, 0),
    'search': (q_search, 1),
    'votes': (q_votes, 0),
    'json': (q_json, 0),
    'csv': (q_csv, 0),
    'attempts-csv': (q_attempts_csv, 0),
}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print(f"\nAvailable queries: {', '.join(sorted(QUERIES.keys()))}")
        print(f"\nExample: python log_exploration/log_query.py output/v22/diagnostic.log summary")
        return

    logfile = sys.argv[1]
    query = sys.argv[2]
    args = sys.argv[3:]

    if not os.path.isfile(logfile):
        print(f"Error: {logfile} not found")
        return

    if query not in QUERIES:
        print(f"Unknown query: {query}")
        print(f"Available: {', '.join(sorted(QUERIES.keys()))}")
        return

    problems = parse_log(logfile)

    func, nargs = QUERIES[query]
    if nargs == 0:
        if args and query in ('slow', 'close-votes'):
            func(problems, args[0])
        else:
            func(problems)
    elif nargs == 1:
        if not args:
            print(f"Query '{query}' requires an argument")
            return
        func(problems, args[0])


if __name__ == '__main__':
    main()
