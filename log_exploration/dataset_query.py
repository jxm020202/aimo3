#!/usr/bin/env python3
"""Query external math datasets (CHAMP, Omni-MATH) for problems matching specific patterns.

Usage:
    python3 log_exploration/dataset_query.py champ [--category CAT] [--concept CONCEPT] [--integer-only]
    python3 log_exploration/dataset_query.py omni [--domain DOMAIN] [--difficulty MIN] [--source SRC] [--integer-only]
    python3 log_exploration/dataset_query.py omni --search "keyword" [--integer-only]
    python3 log_exploration/dataset_query.py champ --list-concepts
    python3 log_exploration/dataset_query.py omni --list-domains
    python3 log_exploration/dataset_query.py omni --list-sources
"""

import json, sys, os

CHAMP_PATH = '/tmp/champ_integer_problems.json'
OMNI_PATH = '/tmp/omni_math_candidates.json'

def load_champ():
    if not os.path.exists(CHAMP_PATH):
        # Generate from package
        import importlib
        pkg_dir = os.path.dirname(importlib.import_module('champ_dataset').__file__)
        with open(os.path.join(pkg_dir, 'dataset_files', 'v0.json')) as f:
            data = json.load(f)

        all_problems = []
        for pid, prob in sorted(data['problems'].items()):
            concepts = [c for c in prob.get('ch_list', []) if c.startswith('C_')]
            hints = [h for h in prob.get('ch_list', []) if h.startswith('H_')]
            concept_names = []
            for c in concepts:
                cd = data['concepts'].get(c, {})
                concept_names.append(cd.get('name') or c)
            hint_texts = []
            for h in hints:
                hd = data['hints'].get(h, {})
                hint_texts.append(hd.get('_text', ''))

            try:
                int_ans = int(str(prob.get('_raw_answer', '')).strip())
                is_integer = True
            except:
                int_ans = None
                is_integer = False

            all_problems.append({
                'id': pid, 'category': prob['category'],
                'text': prob['_raw_text'].replace('@@', ''),
                'answer': prob.get('_raw_answer', ''),
                'int_answer': int_ans,
                'is_integer': is_integer,
                'concepts': concept_names,
                'concept_ids': concepts,
                'hints': hint_texts,
            })
        return all_problems

    with open(CHAMP_PATH) as f:
        return json.load(f)

def load_omni():
    with open(OMNI_PATH) as f:
        return json.load(f)

def cmd_champ(args):
    data = load_champ()

    if '--list-concepts' in args:
        from collections import Counter
        concepts = Counter()
        for p in data:
            for c in p.get('concepts', []):
                concepts[c] += 1
        print(f"{'Concept':<50} Count")
        print("-" * 60)
        for c, n in concepts.most_common():
            print(f"  {c:<48} {n}")
        return

    filtered = data

    cat = None
    if '--category' in args:
        cat = args[args.index('--category') + 1]
        filtered = [p for p in filtered if cat.lower() in p['category'].lower()]

    if '--concept' in args:
        concept = args[args.index('--concept') + 1].lower()
        filtered = [p for p in filtered if any(concept in c.lower() for c in p.get('concepts', []))]

    if '--integer-only' in args:
        filtered = [p for p in filtered if p.get('is_integer') or p.get('int_answer') is not None]

    if '--search' in args:
        kw = args[args.index('--search') + 1].lower()
        filtered = [p for p in filtered if kw in p['text'].lower()]

    print(f"CHAMP: {len(filtered)} problems" + (f" (category={cat})" if cat else ""))
    print()
    for p in filtered:
        ans = p.get('int_answer') or p.get('answer', '?')
        print(f"  [{p['category']}] {p['id']} → {ans}")
        print(f"    Q: {p['text'][:200]}")
        if p.get('concepts'):
            print(f"    Concepts: {', '.join(p['concepts'][:4])}")
        if p.get('hints'):
            print(f"    Hint: {p['hints'][0][:120]}")
        print()

def cmd_omni(args):
    data = load_omni()

    if '--list-domains' in args:
        from collections import Counter
        domains = Counter(p['domain'] for p in data)
        print(f"{'Domain':<55} Count")
        print("-" * 65)
        for d, n in domains.most_common():
            print(f"  {d:<53} {n}")
        return

    if '--list-sources' in args:
        from collections import Counter
        sources = Counter(p['source'] for p in data)
        print(f"{'Source':<35} Count")
        print("-" * 45)
        for s, n in sources.most_common():
            print(f"  {s:<33} {n}")
        return

    filtered = data

    if '--domain' in args:
        domain = args[args.index('--domain') + 1].lower()
        filtered = [p for p in filtered if domain in p['domain'].lower()]

    if '--difficulty' in args:
        min_diff = int(args[args.index('--difficulty') + 1])
        filtered = [p for p in filtered if p['difficulty'] >= min_diff]

    if '--source' in args:
        src = args[args.index('--source') + 1].lower()
        filtered = [p for p in filtered if src in p['source'].lower()]

    if '--integer-only' in args:
        filtered = [p for p in filtered if isinstance(p.get('answer'), int)]

    if '--search' in args:
        kw = args[args.index('--search') + 1].lower()
        filtered = [p for p in filtered if kw in p['problem'].lower()]

    if '--max' in args:
        max_n = int(args[args.index('--max') + 1])
    else:
        max_n = 30

    print(f"Omni-MATH: {len(filtered)} problems (showing first {min(max_n, len(filtered))})")
    print()
    for p in filtered[:max_n]:
        print(f"  [{p['domain']}] diff={p['difficulty']} src={p['source']} → {p['answer']}")
        print(f"    Q: {p['problem'][:250]}")
        print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'champ':
        cmd_champ(args)
    elif cmd == 'omni':
        cmd_omni(args)
    else:
        print(f"Unknown command: {cmd}. Use 'champ' or 'omni'.")
