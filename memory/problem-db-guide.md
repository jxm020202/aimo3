# Problem DB Guide — Adding Entries

## DB Location

- **Working copy**: `data/problem_db/problems.db` (SQLite)
- **Upload copy**: `data/problem_db_upload/problems.db` (what gets pushed to Kaggle)
- **Both must be identical.** After modifying one, copy to the other.

## Schema

```sql
CREATE TABLE "problems" (
    id TEXT PRIMARY KEY,
    category TEXT,
    topic TEXT,
    subtopic TEXT,
    triggers TEXT,
    technique TEXT,
    question TEXT,
    answer TEXT,
    taxonomy TEXT
);
```

- `id` — short hex string (e.g. `0c55f3`). Use `uuid.uuid4().hex[:6]` for new entries.
- `category` — one of: `algebra`, `combinatorics`, `geometry`, `number_theory`, `basic`
- `topic` — subcategory (e.g. `polynomial`, `counting`, `solid`, `modular`)
- `subtopic` — specific technique (e.g. `vieta`, `pigeonhole`, `crt`)
- `triggers` — comma-separated keywords that signal this technique applies
- `technique` — 1-3 sentence summary of the solving approach/strategy
- `question` — optional: a representative problem statement
- `answer` — optional: worked solution hints or the numeric answer
- `taxonomy` — MUST equal `{category}.{topic}.{subtopic}` exactly

## How to Add Rows

```python
import sqlite3
import uuid

db_path = 'data/problem_db/problems.db'
upload_path = 'data/problem_db_upload/problems.db'

entries = [
    {
        'id': uuid.uuid4().hex[:6],
        'category': 'number_theory',
        'topic': 'modular',
        'subtopic': 'crt_advanced',
        'triggers': 'chinese remainder theorem, simultaneous congruences, coprime moduli',
        'technique': 'Apply CRT to solve simultaneous congruences. Watch for non-coprime moduli — use LCM-based extension.',
        'question': '',  # optional
        'answer': '',    # optional
    },
]

# Build taxonomy automatically
for e in entries:
    e['taxonomy'] = f"{e['category']}.{e['topic']}.{e['subtopic']}"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for e in entries:
    cursor.execute('''
        INSERT OR REPLACE INTO problems (id, category, topic, subtopic, triggers, technique, question, answer, taxonomy)
        VALUES (:id, :category, :topic, :subtopic, :triggers, :technique, :question, :answer, :taxonomy)
    ''', e)

conn.commit()

# Rebuild FTS index
cursor.execute("DELETE FROM problems_fts")
cursor.execute("""
    INSERT INTO problems_fts(rowid, problem_id, category, topics, technique_summary, answer)
    SELECT rowid, id, category, topic || ' ' || subtopic || ' ' || triggers, technique, answer
    FROM problems
""")
conn.commit()
conn.close()

# Copy to upload directory
import shutil
shutil.copy2(db_path, upload_path)

print(f"Added {len(entries)} entries. Run count check:")
conn = sqlite3.connect(db_path)
print(f"  Total rows: {conn.execute('SELECT COUNT(*) FROM problems').fetchone()[0]}")
conn.close()
```

## Pushing to Kaggle

DB dataset is owned by `jxm222`, not `shivzzzzzz02`. Must swap credentials:

```bash
# Swap to jxm222
cp ~/.kaggle/kaggle.json ~/.kaggle/kaggle.json.shiv
cp ~/.kaggle/kaggle.json.bak ~/.kaggle/kaggle.json

# Push
kaggle datasets version -p data/problem_db_upload -m "vN: description"

# Swap back to shivzzzzzz02
cp ~/.kaggle/kaggle.json.shiv ~/.kaggle/kaggle.json
```

**NEVER push without user approval.**

## Rules

1. `taxonomy` MUST equal `{category}.{topic}.{subtopic}` — build it programmatically, never type manually
2. Primary key is `id` (NOT `problem_id` — was renamed)
3. Use `INSERT OR REPLACE` to handle duplicates safely
4. Always rebuild FTS after inserts
5. Always copy `problems.db` to both `data/problem_db/` and `data/problem_db_upload/`
6. Current count: **340 entries** (as of 2026-03-06)

## Viewing DB Contents

```bash
python3 scripts/db_view.py                    # overview
python3 -c "
import sqlite3
conn = sqlite3.connect('data/problem_db/problems.db')
for r in conn.execute('SELECT id, taxonomy, triggers FROM problems WHERE category=\"algebra\" LIMIT 5'):
    print(r)
"
```

## What Makes a Good Entry

- **triggers**: words that appear in problem statements (not solution words). Think "what would a classifier see?"
- **technique**: actionable advice. Not "use algebra" but "substitute y=x+1, reduce to single variable, apply AM-GM"
- **question/answer**: optional but valuable for trap warnings (e.g. "95 is the trap answer, correct is 42")
