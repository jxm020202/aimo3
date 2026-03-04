#!/usr/bin/env python3
"""
Convert NuminaMath matched solutions into DB entries.

Reads /tmp/numinamath_matches.json, processes 35 new matches,
appends to data/problem_db/unified.json, then run build_sqlite_db.py.

Rules:
- NEVER include numeric answer in technique_summary or approach
- technique_summary = concise METHOD description (150-400 chars)
- approach = longer HOW to solve (no answers)
- Cross-category tags in topics where appropriate
"""

import json
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)

with open('/tmp/numinamath_matches.json') as f:
    data = json.load(f)
matches = data['matches']

with open('data/problem_db/unified.json') as f:
    unified = json.load(f)

existing_ids = {p['problem_id'] for p in unified}


def redact_answer(text, answer_str):
    """Replace exact answer number (3+ digits) with N in text."""
    if len(answer_str) >= 3:
        text = re.sub(r'\b' + re.escape(answer_str) + r'\b', 'N', text)
    return text


def clean_approach(solution, answer_str):
    """Remove final answer mentions and boxed answers from solution text."""
    text = re.sub(r'The final answer is\s*\\?\\?boxed\{[^}]*\}\.?', '', solution)
    text = re.sub(r'\\boxed\{[^}]*\}', '[answer]', text)
    text = re.sub(
        r'\n*(?:The )?(?:answer|Answer)(?:\s+is)?\s*[:=]?\s*' + re.escape(answer_str) + r'\.?\s*$',
        '', text
    )
    text = redact_answer(text, answer_str)
    return text.strip()


def make_technique_summary(solution, problem, category, answer_str):
    """Extract a concise method description (150-400 chars)."""
    sol_lower = solution.lower()
    techniques = []
    kw_map = {
        'law of cosines': 'Law of Cosines',
        'pythagorean theorem': 'Pythagorean theorem',
        'ptolemy': "Ptolemy's theorem",
        'power of a point': 'Power of a Point',
        'am-gm': 'AM-GM inequality',
        'cauchy-schwarz': 'Cauchy-Schwarz inequality',
        "fermat's little": "Fermat's Little Theorem",
        'induction': 'induction',
        'pigeonhole': 'pigeonhole principle',
        'modular arithmetic': 'modular arithmetic',
        'casework': 'casework',
        'similarity': 'triangle similarity',
        'cyclic quadrilateral': 'cyclic quadrilateral properties',
        "brahmagupta": "Brahmagupta's formula",
        'law of sines': 'sine rule',
        'triangle inequality': 'triangle inequality',
        'coordinate': 'coordinate geometry',
        'graph': 'graph theory',
        'contradiction': 'proof by contradiction',
        'quadratic': 'quadratic equations',
        'discriminant': 'discriminant analysis',
        'isogonal conjugate': 'isogonal conjugation',
        'tangent': 'tangent line properties',
        'angle bisector': 'angle bisector properties',
        'modulo': 'modular arithmetic',
        'congruence': 'modular congruence',
    }
    for keyword, name in kw_map.items():
        if keyword in sol_lower and name not in techniques:
            techniques.append(name)
    if not techniques:
        techniques = [category]

    if 'prove' in sol_lower[:200] or 'show that' in sol_lower[:200]:
        prefix = "Prove via"
    elif 'construct' in sol_lower[:200]:
        prefix = "Construct solution using"
    elif 'bound' in sol_lower[:200]:
        prefix = "Bound the answer using"
    else:
        prefix = "Solve using"

    summary = f"{prefix} {', '.join(techniques[:4])}"
    strat = []
    for phrase in ['pairing', 'game theory', 'optimal strategy', 'greedy', 'reflection',
                   'symmetry', 'substitution', 'transformation', 'reduction', 'recursion',
                   'telescoping', 'bounding', 'estimation', 'extremal principle']:
        if phrase in sol_lower:
            strat.append(phrase)
    if strat:
        summary += f". Key ideas: {', '.join(strat[:3])}"
    if len(summary) < 150:
        first_para = solution.split('\n\n')[0][:300] if solution else ''
        clean_first = redact_answer(first_para, answer_str)
        extra = clean_first[:400 - len(summary) - 3]
        if '.' in extra[50:]:
            extra = extra[:extra.rindex('.', 50) + 1]
        summary = summary + ". " + extra
    return redact_answer(summary[:400], answer_str)


def make_topics(category, solution, problem):
    """Generate topic tags including cross-category where appropriate."""
    sol_lower = solution.lower()
    topics = [category]
    if category != 'number_theory' and any(w in sol_lower for w in ['modular', 'modulo', 'divisib', 'prime', 'fermat']):
        topics.append('number_theory')
    if category != 'combinatorics' and any(w in sol_lower for w in ['counting', 'combinatorial', 'pigeonhole', 'permutation']):
        topics.append('combinatorics')
    if category != 'algebra' and any(w in sol_lower for w in ['inequality', 'am-gm', 'cauchy', 'polynomial', 'quadratic']):
        topics.append('algebra')
    if category != 'geometry' and any(w in sol_lower for w in ['circle', 'triangle', 'polygon', 'angle', 'perpendicular']):
        topics.append('geometry')
    topic_map = {
        'game_theory': ['game', 'strategy', 'player'],
        'graph_theory': ['graph', 'vertex', 'edge', 'bipartite'],
        'cyclic_quadrilateral': ['cyclic quadrilateral', 'ptolemy'],
        'trigonometry': ['cosine', 'sine', 'trigonometric'],
        'optimization': ['maximize', 'minimize', 'maximum', 'minimum'],
        'divisibility': ['divisib', 'modular', 'congruence'],
        'inequalities': ['inequality', 'am-gm', 'cauchy-schwarz'],
    }
    for tag, keywords in topic_map.items():
        if any(k in sol_lower for k in keywords):
            topics.append(tag)
    seen = set()
    return ', '.join(t for t in topics if not (t in seen or seen.add(t)))


# Process matches
new_entries = []
for m in matches:
    vid = m['val_bench_id']
    if vid in existing_ids:
        continue
    answer_str, nm_answer = m['val_bench_answer'], m['numinamath_answer']
    category, solution, problem = m['val_bench_category'], m['numinamath_solution'], m['numinamath_problem']
    ts = make_technique_summary(solution, problem, category, answer_str)
    ap = clean_approach(solution, answer_str)
    tp = make_topics(category, solution, problem)
    if nm_answer != answer_str and len(nm_answer) >= 3:
        ap = redact_answer(ap, nm_answer)
        ts = redact_answer(ts, nm_answer)
    new_entries.append({
        "problem_id": vid, "question": problem,
        "expected_answer": int(answer_str) if answer_str.isdigit() else answer_str,
        "topics": tp.split(', '), "skills": tp, "category": category,
        "technique_summary": ts, "approach": ap,
        "correct_approach": "", "wave2_hint": "", "failure_mode": "",
        "common_wrong_answers": [], "correct_rate": "", "why_wrong": "",
        "versions_wrong": [], "risk_level": "",
        "source": f"numinamath_{m['numinamath_source']}"
    })

print(f"New entries: {len(new_entries)}")
from collections import Counter
cats = Counter(e['category'] for e in new_entries)
print(f"By category: {dict(cats)}")

# Check for answer leaks
issues = []
for e in new_entries:
    ans = str(e['expected_answer'])
    if len(ans) >= 3:
        if ans in e['technique_summary']:
            issues.append(f"{e['problem_id']}: {ans} in technique_summary")
        if re.search(r'\b' + re.escape(ans) + r'\b', e['approach']):
            issues.append(f"{e['problem_id']}: {ans} in approach")
print(f"Answer leaks: {len(issues)}")
for i in issues:
    print(f"  {i}")

# Show samples
for e in new_entries[:3]:
    print(f"\n--- {e['problem_id']} ({e['category']}) ---")
    print(f"topics: {e['skills']}")
    print(f"technique_summary ({len(e['technique_summary'])} chars): {e['technique_summary'][:200]}...")
    print(f"approach length: {len(e['approach'])} chars")

# Write
unified.extend(new_entries)
with open('data/problem_db/unified.json', 'w') as f:
    json.dump(unified, f, indent=2, ensure_ascii=False)
print(f"\nunified.json: {len(unified)} total (was {len(unified) - len(new_entries)})")
