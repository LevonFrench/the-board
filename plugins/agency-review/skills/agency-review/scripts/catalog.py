"""List agency-agents personas (division, name, description, path) for agent selection.

Usage:
  python catalog.py                    # every persona, compact table
  python catalog.py unity shader ux    # only personas whose path/name/description match any keyword
  python catalog.py --divisions game-development,design,testing

Repo location: $AGENCY_AGENTS_DIR, else agency-agents.
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get('AGENCY_AGENTS_DIR', 'agency-agents'))


def frontmatter(path):
    text = path.read_text(encoding='utf-8', errors='replace')
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.S)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        if v and k.strip() in ('name', 'description'):
            fields[k.strip()] = v.strip().strip('"\'')
    return fields if 'name' in fields else None


def main(argv):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__)
        return
    if not ROOT.is_dir():
        sys.exit(f'agency-agents repo not found at {ROOT} (set AGENCY_AGENTS_DIR)')
    divisions = list(json.loads((ROOT / 'divisions.json').read_text(encoding='utf-8'))['divisions'])
    keywords, only = [], None
    it = iter(argv)
    for a in it:
        if a == '--divisions':
            only = set(next(it).split(','))
        else:
            keywords.append(a.lower())
    rows = []
    for div in divisions:
        if only and div not in only:
            continue
        for p in sorted((ROOT / div).rglob('*.md')):
            fm = frontmatter(p)
            if not fm:
                continue
            hay = f"{p.relative_to(ROOT).as_posix()} {fm['name']} {fm.get('description', '')}".lower()
            if keywords and not any(k in hay for k in keywords):
                continue
            rows.append((div, fm['name'], fm.get('description', '')[:160], p.as_posix()))
    for div, name, desc, path in rows:
        print(f'{div} | {name} | {desc} | {path}')
    print(f'\n{len(rows)} personas from {ROOT.as_posix()}', file=sys.stderr)


if __name__ == '__main__':
    main(sys.argv[1:])
