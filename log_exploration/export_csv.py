#!/usr/bin/env python3
"""
AIMO3 CSV Exporter
===================
Export parsed diagnostic.log data to CSV files for spreadsheet/notebook analysis.

Outputs:
    problems.csv  — One row per problem (score, time, votes, errors)
    attempts.csv  — One row per attempt (answer, entropy, temp, time)
    turns.csv     — One row per turn (reasoning length, code length, errors)
    errors.csv    — One row per error occurrence (type, message, context)

Usage:
    python log_exploration/export_csv.py <logfile> [output_dir]
    python log_exploration/export_csv.py output/v22/diagnostic.log
    python log_exploration/export_csv.py output/v22/diagnostic.log /tmp/csv_export
    python log_exploration/export_csv.py --help
"""

import sys
import os
import csv
import re
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log_exploration.log_query import parse_log


def _extract_error_type(output_text):
    if not output_text:
        return None
    for line in output_text.split('\n'):
        line = line.strip()
        m = re.match(r'^([A-Z]\w*Error|[A-Z]\w*Exception):\s*', line)
        if m:
            return m.group(1)
    return None


def _extract_error_message(output_text):
    if not output_text:
        return ""
    for line in reversed(output_text.split('\n')):
        line = line.strip()
        if re.match(r'^[A-Z]\w*(Error|Exception):', line):
            return line[:200]
    return ""


def export_problems(problems, outdir):
    path = os.path.join(outdir, 'problems.csv')
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'problem_id', 'batch', 'correct', 'predicted', 'expected',
            'wall_time_s', 'budget_s', 'budget_util_pct',
            'total_attempts', 'total_answered', 'total_nones', 'none_rate',
            'total_errors', 'total_tokens', 'avg_entropy',
            'early_stop', 'vote_margin', 'votes_json',
            'problem_text_preview'
        ])
        for p in problems:
            nones = sum(1 for a in p.attempts if a.is_none)
            none_rate = nones / max(len(p.attempts), 1)
            budget_util = p.wall_time / max(p.budget, 1) * 100
            votes = sorted(p.votes.values(), reverse=True)
            margin = votes[0] - votes[1] if len(votes) >= 2 else (votes[0] if votes else 0)
            writer.writerow([
                p.problem_id, p.batch_name, int(p.correct),
                p.predicted, p.expected,
                round(p.wall_time, 1), round(p.budget, 1), round(budget_util, 1),
                len(p.attempts), p.total_answered, nones, round(none_rate, 3),
                sum(a.errors for a in p.attempts),
                sum(a.tokens for a in p.attempts),
                round(p.avg_entropy, 4),
                int(p.early_stop), margin, json.dumps(p.votes),
                (p.problem_text or '')[:100]
            ])
    print(f"  problems.csv: {len(problems)} rows")


def export_attempts(problems, outdir):
    path = os.path.join(outdir, 'attempts.csv')
    rows = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'problem_id', 'attempt_num', 'answer', 'is_none', 'is_correct',
            'entropy', 'temperature', 'code_calls', 'errors', 'tokens',
            'time_s', 'num_turns', 'reasoning_chars', 'code_chars', 'output_chars',
            'libraries'
        ])
        for p in problems:
            for a in p.attempts:
                is_correct = 1 if (a.answer is not None and a.answer == p.expected) else 0
                reasoning_chars = sum(t.reasoning_chars for t in a.turns)
                code_chars = sum(len(t.code) for t in a.turns if t.code)
                output_chars = sum(len(t.output) for t in a.turns if t.output)
                libs = ', '.join(a.libraries) if a.libraries else ''
                writer.writerow([
                    p.problem_id, a.attempt_num, a.answer, int(a.is_none), is_correct,
                    round(a.entropy, 4), a.temperature, a.code_calls, a.errors, a.tokens,
                    round(a.time_s, 1), len(a.turns), reasoning_chars, code_chars, output_chars,
                    libs
                ])
                rows += 1
    print(f"  attempts.csv: {rows} rows")


def export_turns(problems, outdir):
    path = os.path.join(outdir, 'turns.csv')
    rows = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'problem_id', 'attempt_num', 'turn_num', 'has_reasoning', 'reasoning_chars',
            'has_code', 'code_chars', 'code_lines',
            'has_output', 'output_chars', 'is_error', 'error_type'
        ])
        for p in problems:
            for a in p.attempts:
                for t in a.turns:
                    error_type = _extract_error_type(t.output) if t.is_error else ''
                    code_lines = len(t.code.split('\n')) if t.code else 0
                    writer.writerow([
                        p.problem_id, a.attempt_num, t.turn_num,
                        int(bool(t.reasoning_text)), t.reasoning_chars,
                        int(bool(t.code)), len(t.code) if t.code else 0, code_lines,
                        int(bool(t.output)), len(t.output) if t.output else 0,
                        int(t.is_error), error_type or ''
                    ])
                    rows += 1
    print(f"  turns.csv: {rows} rows")


def export_errors(problems, outdir):
    path = os.path.join(outdir, 'errors.csv')
    rows = 0
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'problem_id', 'problem_correct', 'attempt_num', 'turn_num',
            'error_type', 'error_message', 'code_preview', 'output_preview'
        ])
        for p in problems:
            for a in p.attempts:
                for t in a.turns:
                    etype = _extract_error_type(t.output)
                    if etype:
                        emsg = _extract_error_message(t.output)
                        code_preview = (t.code or '')[:200]
                        output_preview = (t.output or '')[:200]
                        writer.writerow([
                            p.problem_id, int(p.correct), a.attempt_num, t.turn_num,
                            etype, emsg, code_preview, output_preview
                        ])
                        rows += 1
    print(f"  errors.csv: {rows} rows")


def main():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0 if '--help' in sys.argv else 1)

    logfile = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(logfile) or '.'

    if not os.path.exists(logfile):
        print(f"Error: {logfile} not found")
        sys.exit(1)

    os.makedirs(outdir, exist_ok=True)

    print(f"Parsing: {logfile}")
    problems = parse_log(logfile)
    print(f"Parsed {len(problems)} problems\n")

    print(f"Exporting to: {outdir}/")
    export_problems(problems, outdir)
    export_attempts(problems, outdir)
    export_turns(problems, outdir)
    export_errors(problems, outdir)

    print(f"\nDone. Files in {outdir}/")


if __name__ == '__main__':
    main()
