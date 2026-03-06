#!/usr/bin/env python3
"""
Wave 1 Notes Extractor
======================
Extracts the actual expert notes text injected into Wave 2 for each problem.

For each problem shows:
  - Selected taxonomy
  - DB matches found
  - Full notes text (between [Our IMO expert...] and [END EXPERT NOTES])
  - Classification: HELPFUL, MISLEADING, GENERIC, or NONE

For WRONG problems, shows the full notes text for analysis.

Usage:
    python3 log_exploration/wave1_notes_extract.py <diagnostic.log> [--wrong-only] [--problem PID]
"""

import sys
import re
import argparse
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ProblemNotes:
    problem_id: str
    index: int  # 1-based
    expected: Optional[int] = None
    predicted: Optional[int] = None
    correct: bool = False
    problem_text: str = ""
    # Wave 1
    wave1_taxonomies: List[str] = field(default_factory=list)
    wave1_votes: dict = field(default_factory=dict)
    wave1_type: str = ""  # "db_retrieval", "no_consensus", "basic"
    db_matches: List[str] = field(default_factory=list)  # matched problem IDs
    notes_chars: int = 0
    # The actual notes text
    notes_text: str = ""
    # The expert header line
    expert_header: str = ""
    # Classification
    note_class: str = "NONE"


def parse_wave1_notes(filepath: str) -> List[ProblemNotes]:
    """Parse diagnostic log and extract Wave 1 notes for each problem."""
    with open(filepath, 'r', errors='replace') as f:
        lines = f.readlines()

    problems = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].rstrip('\n')
        stripped = line.strip()

        # ── Problem header ──
        prob_match = re.match(r'\s*\[(\d+)/(\d+)\]\s*Problem\s+(?:id=)?(\w+)', stripped)
        if prob_match:
            p = ProblemNotes(
                problem_id=prob_match.group(3),
                index=int(prob_match.group(1)),
            )
            exp_match = re.search(r'Expected:\s*(\d+)', stripped)
            if exp_match:
                p.expected = int(exp_match.group(1))
            problems.append(p)
            i += 1

            # Read problem text (next non-empty line starting with "Problem:")
            while i < n:
                s = lines[i].strip()
                if s.startswith('Problem:'):
                    p.problem_text = s[8:].strip()[:200]
                    break
                if s.startswith('===') or s.startswith('──'):
                    break
                i += 1
            continue

        # ── Wave 1 taxonomy votes ──
        if stripped == '=== WAVE 1 TAXONOMY VOTES ===' and problems:
            p = problems[-1]
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.startswith('=== END VOTES ==='):
                    i += 1
                    break
                vote_match = re.match(r'(\S+):\s+([\d.]+)\s+votes', s)
                if vote_match:
                    tax = vote_match.group(1)
                    votes = float(vote_match.group(2))
                    selected = '<-- SELECTED' in s
                    p.wave1_votes[tax] = (votes, selected)
                i += 1
            continue

        # ── Wave 1 result ──
        w1_res = re.match(r"\s*Wave 1 result:\s*\[([^\]]*)\]", stripped)
        if w1_res and problems:
            p = problems[-1]
            content = w1_res.group(1).strip()
            if content:
                p.wave1_taxonomies = [t.strip().strip("'\"") for t in content.split(',')]
            i += 1
            continue

        # ── Wave 1 DB retrieval ──
        if stripped.startswith('=== WAVE 1') and 'DB RETRIEVAL' in stripped and problems:
            p = problems[-1]
            p.wave1_type = "db_retrieval"
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.startswith('=== END WAVE 1'):
                    i += 1
                    break
                # Match DB entry lines: "  - HEXID [taxonomy]"
                db_match = re.match(r'-\s+(\w+)\s+\[', s)
                if db_match:
                    p.db_matches.append(db_match.group(1))
                notes_match = re.match(r'Notes:\s*(\d+)\s*chars', s)
                if notes_match:
                    p.notes_chars = int(notes_match.group(1))
                i += 1
            continue

        # ── Wave 1 no consensus ──
        if stripped.startswith('=== WAVE 1') and 'NO CONSENSUS' in stripped and problems:
            p = problems[-1]
            p.wave1_type = "no_consensus"
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.startswith('=== END WAVE 1'):
                    i += 1
                    break
                i += 1
            continue

        # ── Wave 1 basic ──
        if stripped.startswith('=== WAVE 1') and 'BASIC' in stripped and problems:
            p = problems[-1]
            p.wave1_type = "basic"
            i += 1
            while i < n:
                s = lines[i].strip()
                if s.startswith('=== END WAVE 1'):
                    i += 1
                    break
                i += 1
            continue

        # ── USER PROMPT — extract notes text ──
        if stripped.startswith('=== USER PROMPT') and problems:
            p = problems[-1]
            i += 1
            # Collect lines until === END USER PROMPT ===
            in_notes = False
            notes_lines = []
            while i < n:
                s = lines[i].rstrip('\n')
                stripped_s = s.strip()

                if stripped_s == '=== END USER PROMPT ===':
                    i += 1
                    break

                # Expert header
                if stripped_s.startswith('[Our IMO expert'):
                    p.expert_header = stripped_s
                    # If it's the "tips and tricks" version, notes follow
                    if 'tips and tricks' in stripped_s:
                        in_notes = True
                        i += 1
                        continue
                    elif 'could not confidently' in stripped_s:
                        p.note_class = "NONE"
                        i += 1
                        continue
                    elif 'quick solve' in stripped_s:
                        p.note_class = "NONE"  # basic
                        i += 1
                        continue

                # End of expert notes section
                if stripped_s == '[END EXPERT NOTES]':
                    in_notes = False
                    i += 1
                    continue

                if in_notes:
                    notes_lines.append(s)

                i += 1

            p.notes_text = '\n'.join(notes_lines).strip()
            continue

        # ── STATUS line ──
        status_match = re.match(r'\s*STATUS:\s*(CORRECT|WRONG)\s*\|\s*Predicted:\s*(\d+)\s*\|\s*Expected:\s*(\d+)', stripped)
        if status_match and problems:
            p = problems[-1]
            p.correct = status_match.group(1) == 'CORRECT'
            p.predicted = int(status_match.group(2))
            p.expected = int(status_match.group(3))
            i += 1
            continue

        i += 1

    return problems


def classify_notes(p: ProblemNotes) -> str:
    """
    Classify note quality based on content and outcome.

    Categories:
      HELPFUL       - Notes contain relevant technique, problem got correct
      WRONG_ANSWER  - Notes contain an explicit wrong answer that model adopted
      WRONG_TOPIC   - Taxonomy mismatch: notes are for a different problem type
      IRRELEVANT    - Notes have a technique but it doesn't apply to this problem
      GENERIC       - Notes exist but are too vague (empty Question/Answer fields)
      NONE          - No notes injected (no consensus / basic)
    """
    if not p.notes_text:
        return "NONE"
    if p.wave1_type == "no_consensus":
        return "NONE"
    if p.wave1_type == "basic":
        return "NONE"

    text = p.notes_text

    # Check for specific content indicators
    has_technique = bool(re.search(r'Technique:', text))
    has_question = bool(re.search(r'Question:\s*\S', text))  # non-empty question
    has_answer_content = bool(re.search(r'Answer:\s*\S', text))  # non-empty answer

    # Check if the notes are for the SAME problem (self-match in DB)
    is_self_match = p.problem_id in ' '.join(p.db_matches) if p.db_matches else False

    if not p.correct:
        # ── Wrong problem analysis ──

        # Check if the notes explicitly contain the wrong predicted answer
        if p.predicted is not None:
            pred_str = str(p.predicted)
            # Look for the predicted answer appearing in the Answer field or at end of notes
            answer_section = re.search(r'Answer:(.+?)(?:\n---|$)', text, re.DOTALL)
            if answer_section and pred_str in answer_section.group(1):
                return "WRONG_ANSWER"
            # Also check if the notes say "gives X" with the wrong answer
            if re.search(rf'gives\s+{pred_str}\b', text):
                return "WRONG_ANSWER"

        # Check if Question field is empty (generic DB entry, not problem-specific)
        if not has_question:
            return "GENERIC"

        # If notes have a full question+answer but for a DIFFERENT problem
        if has_question and not is_self_match:
            return "IRRELEVANT"

        # Self-match with full content but still wrong
        if is_self_match and has_technique:
            return "WRONG_ANSWER"

        # Has technique content but didn't help
        return "IRRELEVANT"

    # ── Correct problem analysis ──
    if has_technique and (has_question or has_answer_content):
        return "HELPFUL"
    elif has_technique:
        return "HELPFUL"
    else:
        return "GENERIC"


def format_notes_block(p: ProblemNotes, show_full: bool = False) -> str:
    """Format a problem's notes for display."""
    lines = []

    status = "CORRECT" if p.correct else "WRONG"
    lines.append(f"{'='*80}")
    lines.append(f"[{p.index}/50] Problem {p.problem_id} | {status} | "
                 f"Predicted: {p.predicted} | Expected: {p.expected}")
    lines.append(f"{'='*80}")

    if p.problem_text:
        lines.append(f"  Problem: {p.problem_text}...")

    # Taxonomy
    if p.wave1_taxonomies:
        tax_str = ', '.join(p.wave1_taxonomies)
        lines.append(f"  Taxonomy: {tax_str}")
    else:
        lines.append(f"  Taxonomy: (no consensus)")

    # Votes summary
    if p.wave1_votes:
        sorted_votes = sorted(p.wave1_votes.items(), key=lambda x: -x[1][0])
        top3 = sorted_votes[:3]
        vote_parts = []
        for tax, (votes, selected) in top3:
            sel = " *" if selected else ""
            vote_parts.append(f"{tax}={votes:.0f}{sel}")
        lines.append(f"  Top votes: {', '.join(vote_parts)}")

    # Wave 1 type
    lines.append(f"  Wave 1 type: {p.wave1_type or 'unknown'}")

    # DB matches
    if p.db_matches:
        lines.append(f"  DB matches: {len(p.db_matches)} ({', '.join(p.db_matches)})")

    # Notes classification
    lines.append(f"  Notes class: {p.note_class} ({p.notes_chars} chars)")

    # Notes text
    if p.notes_text:
        if show_full or not p.correct:
            lines.append(f"  {'─'*70}")
            lines.append(f"  NOTES TEXT:")
            for nl in p.notes_text.split('\n'):
                lines.append(f"  | {nl}")
            lines.append(f"  {'─'*70}")
        else:
            # Show truncated version for correct problems
            preview = p.notes_text.replace('\n', ' ')[:150]
            lines.append(f"  Notes preview: {preview}...")
    elif p.wave1_type == "no_consensus":
        lines.append(f"  Notes: [No notes — no taxonomy consensus]")
    elif p.wave1_type == "basic":
        lines.append(f"  Notes: [No notes — classified as basic]")
    else:
        lines.append(f"  Notes: [No notes text found]")

    # Expert header
    if p.expert_header:
        lines.append(f"  Expert header: {p.expert_header}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Extract Wave 1 notes from diagnostic log')
    parser.add_argument('logfile', help='Path to diagnostic.log')
    parser.add_argument('--wrong-only', action='store_true', help='Show only wrong problems')
    parser.add_argument('--problem', '-p', help='Show specific problem ID')
    parser.add_argument('--full', action='store_true', help='Show full notes for all problems')
    parser.add_argument('--summary', action='store_true', help='Show summary table only')
    args = parser.parse_args()

    problems = parse_wave1_notes(args.logfile)

    # Classify notes
    for p in problems:
        p.note_class = classify_notes(p)

    # Filter
    if args.problem:
        problems = [p for p in problems if p.problem_id.startswith(args.problem)]
    if args.wrong_only:
        problems = [p for p in problems if not p.correct]

    # Summary statistics
    all_problems = parse_wave1_notes(args.logfile) if (args.wrong_only or args.problem) else problems
    for p in all_problems:
        p.note_class = classify_notes(p)

    total = len(all_problems)
    correct = sum(1 for p in all_problems if p.correct)
    wrong = total - correct
    with_notes = sum(1 for p in all_problems if p.notes_text)
    no_consensus = sum(1 for p in all_problems if p.wave1_type == "no_consensus")
    basic = sum(1 for p in all_problems if p.wave1_type == "basic")

    # Notes class counts
    class_counts = {}
    for p in all_problems:
        class_counts[p.note_class] = class_counts.get(p.note_class, 0) + 1

    # Wrong problems with/without notes
    wrong_with_notes = sum(1 for p in all_problems if not p.correct and p.notes_text)
    wrong_no_notes = sum(1 for p in all_problems if not p.correct and not p.notes_text)

    # Correct problems with/without notes
    correct_with_notes = sum(1 for p in all_problems if p.correct and p.notes_text)
    correct_no_notes = sum(1 for p in all_problems if p.correct and not p.notes_text)

    print(f"\n{'='*80}")
    print(f"  WAVE 1 NOTES EXTRACTION REPORT")
    print(f"{'='*80}")
    print(f"  Score: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"  With notes: {with_notes}/{total} | No consensus: {no_consensus} | Basic: {basic}")
    print(f"  Notes classification: {class_counts}")
    print(f"")
    print(f"  Correct + notes: {correct_with_notes}/{correct} | Correct no-notes: {correct_no_notes}/{correct}")
    print(f"  Wrong + notes:   {wrong_with_notes}/{wrong}  | Wrong no-notes:   {wrong_no_notes}/{wrong}")
    print()

    # Notes effectiveness table
    print(f"  {'TYPE':<15} {'CORRECT':>8} {'WRONG':>8} {'TOTAL':>8} {'RATE':>8}")
    print(f"  {'─'*50}")
    for ntype in ['db_retrieval', 'no_consensus', 'basic', '']:
        if ntype:
            c = sum(1 for p in all_problems if p.correct and p.wave1_type == ntype)
            w = sum(1 for p in all_problems if not p.correct and p.wave1_type == ntype)
        else:
            ntype = 'unknown'
            c = sum(1 for p in all_problems if p.correct and not p.wave1_type)
            w = sum(1 for p in all_problems if not p.correct and not p.wave1_type)
        t = c + w
        if t > 0:
            print(f"  {ntype:<15} {c:>8} {w:>8} {t:>8} {c/t*100:>7.0f}%")
    print()

    if args.summary:
        # Summary table
        print(f"\n  {'#':>3} {'ID':<8} {'OK':>4} {'Pred':>6} {'Exp':>6} {'Type':<14} {'Taxonomy':<40} {'Class':<10} {'Chars':>5}")
        print(f"  {'─'*100}")
        for p in (problems if not args.wrong_only and not args.problem else all_problems):
            ok = "OK" if p.correct else "MISS"
            tax = ', '.join(p.wave1_taxonomies)[:40] if p.wave1_taxonomies else '(none)'
            print(f"  {p.index:>3} {p.problem_id:<8} {ok:>4} {p.predicted or 0:>6} {p.expected or 0:>6} "
                  f"{p.wave1_type:<14} {tax:<40} {p.note_class:<10} {p.notes_chars:>5}")
        return

    # ── Detailed output ──
    if not args.wrong_only and not args.problem:
        # Show summary table first
        print(f"  {'#':>3} {'ID':<8} {'OK':>4} {'Pred':>6} {'Exp':>6} {'Type':<14} {'Taxonomy':<40} {'Class':<10} {'Chars':>5}")
        print(f"  {'─'*100}")
        for p in all_problems:
            ok = "OK" if p.correct else "MISS"
            tax = ', '.join(p.wave1_taxonomies)[:40] if p.wave1_taxonomies else '(none)'
            print(f"  {p.index:>3} {p.problem_id:<8} {ok:>4} {p.predicted or 0:>6} {p.expected or 0:>6} "
                  f"{p.wave1_type:<14} {tax:<40} {p.note_class:<10} {p.notes_chars:>5}")

        print(f"\n{'='*80}")
        print(f"  WRONG PROBLEMS — FULL NOTES DETAIL ({wrong} problems)")
        print(f"{'='*80}\n")

    # Show detailed blocks
    for p in problems:
        show_full = args.full or not p.correct
        print(format_notes_block(p, show_full=show_full))
        print()


if __name__ == '__main__':
    main()
