#!/usr/bin/env python3
"""View and query the AIMO3 problem database.

Usage:
    python3 scripts/db_view.py                       # summary dashboard
    python3 scripts/db_view.py list                   # all entries, compact
    python3 scripts/db_view.py show <problem_id>      # full entry
    python3 scripts/db_view.py topic <topic>          # filter by topic
    python3 scripts/db_view.py cat <category>         # filter by category
    python3 scripts/db_view.py search <keyword>       # search all text fields
    python3 scripts/db_view.py tree                   # full taxonomy tree
"""
import sqlite3
import sys
import os

DB_PATHS = [
    'data/problem_db/problems.db',
    '/kaggle/input/aimo3-problem-db/problems.db',
]

def get_db():
    for p in DB_PATHS:
        if os.path.isfile(p):
            return sqlite3.connect(p)
    print(f"DB not found at any of: {DB_PATHS}")
    sys.exit(1)

def dashboard(db):
    total = db.execute('SELECT COUNT(*) FROM problems').fetchone()[0]
    print(f"\n  AIMO3 Problem DB — {total} problems\n")
    print(f"  {'Category':<16} {'Count':>5}")
    print(f"  {'─'*16} {'─'*5}")
    for cat, n in db.execute('SELECT category, COUNT(*) FROM problems GROUP BY category ORDER BY category'):
        print(f"  {cat:<16} {n:>5}")
    print()
    print(f"  {'Topic':<30} {'#':>3}  {'Category':<14}")
    print(f"  {'─'*30} {'─'*3}  {'─'*14}")
    for cat, topic, n in db.execute('SELECT category, topic, COUNT(*) FROM problems GROUP BY category, topic ORDER BY category, topic'):
        print(f"  {topic:<30} {n:>3}  {cat:<14}")

def list_all(db, where='1=1', params=()):
    rows = db.execute(f'SELECT problem_id, category, topic, subtopic, triggers FROM problems WHERE {where} ORDER BY category, topic, subtopic', params).fetchall()
    print(f"\n  {len(rows)} problems\n")
    print(f"  {'ID':<16} {'Category':<14} {'Topic':<22} {'Subtopic':<22} {'Triggers (first 50)':<50}")
    print(f"  {'─'*16} {'─'*14} {'─'*22} {'─'*22} {'─'*50}")
    for r in rows:
        trig = (r[4] or '')[:50]
        print(f"  {r[0]:<16} {r[1]:<14} {r[2]:<22} {r[3]:<22} {trig:<50}")

def show(db, pid):
    row = db.execute('SELECT * FROM problems WHERE problem_id = ?', (pid,)).fetchone()
    if not row:
        print(f"  Not found: {pid}")
        return
    cols = [d[0] for d in db.execute('SELECT * FROM problems LIMIT 1').description]
    print()
    for i, c in enumerate(cols):
        val = str(row[i] or '')
        if len(val) > 300:
            val = val[:300] + f'... ({len(str(row[i]))} chars total)'
        print(f"  {c:<12}: {val}")

def tree(db):
    rows = db.execute('SELECT category, topic, subtopic, COUNT(*) FROM problems GROUP BY category, topic, subtopic ORDER BY category, topic, subtopic').fetchall()
    print(f"\n  Taxonomy Tree\n")
    curr_cat = curr_topic = None
    for cat, topic, sub, n in rows:
        if cat != curr_cat:
            print(f"  {cat}/")
            curr_cat = cat
            curr_topic = None
        if topic != curr_topic:
            print(f"  ├── {topic}/")
            curr_topic = topic
        print(f"  │   ├── {sub} ({n})")

def search(db, keyword):
    kw = f'%{keyword}%'
    list_all(db, 
        "problem_id LIKE ? OR category LIKE ? OR topic LIKE ? OR subtopic LIKE ? OR triggers LIKE ? OR technique LIKE ? OR question LIKE ? OR answer LIKE ?",
        (kw, kw, kw, kw, kw, kw, kw, kw))

def main():
    db = get_db()
    args = sys.argv[1:]
    
    if not args:
        dashboard(db)
    elif args[0] == 'list':
        list_all(db)
    elif args[0] == 'show' and len(args) > 1:
        show(db, args[1])
    elif args[0] == 'topic' and len(args) > 1:
        list_all(db, "topic LIKE ?", (f'%{args[1]}%',))
    elif args[0] == 'cat' and len(args) > 1:
        list_all(db, "category = ?", (args[1],))
    elif args[0] == 'search' and len(args) > 1:
        search(db, args[1])
    elif args[0] == 'tree':
        tree(db)
    else:
        print(__doc__)
    
    db.close()

if __name__ == '__main__':
    main()
