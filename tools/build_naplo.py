#!/usr/bin/env python3
"""content/naplo.md (a projekt claude/naplo.md másolata) -> content/naplo.hu.json

Frissítés: másold a legfrissebb naplo.md-t a content/ alá, majd: python3 tools/build_naplo.py
Szerkezet: '## <dátum> – <cím>' = nap; '**<cím>**' = bejegyzés; '- ' = sor; táblázat a '## Eszközök' alatt.
"""
import html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); SITE = os.path.dirname(HERE)
src = open(os.path.join(SITE, 'content/naplo.md'), encoding='utf-8').read()

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    return s

def kind(t):
    for k, ch in (('stuck', '⚠️'), ('fix', '✅'), ('lesson', '💡'), ('human', '🧑'), ('ai', '🤖')):
        if t.startswith(ch): return k
    return 'note'

tools, days, day, entry = [], [], None, None
section = None
for line in src.splitlines():
    if line.startswith('## '):
        section = line[3:].strip()
        if section.lower().startswith('eszköz'): day = None; continue
        m = re.match(r'(\d{4}-\d{2}-\d{2})\s*(\([^)]*\))?\s*[–-]\s*(.*)', section)
        day = {'date': m.group(1) if m else '', 'weekday': (m.group(2) or '').strip('()') if m else '',
               'title': inline(m.group(3) if m else section), 'entries': []}
        days.append(day); entry = None
    elif line.startswith('|') and day is None and section and section.lower().startswith('eszköz'):
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) >= 2 and not set(cells[0]) <= set('-: ') and cells[0] != 'Eszköz':
            tools.append({'tool': inline(cells[0]), 'use': inline(cells[1])})
    elif day is not None and re.match(r'^\*\*.+\*\*\s*$', line.strip()):
        t = line.strip()[2:-2]
        icons = re.match(r'^([🧑🤖\s]*)', t).group(1)
        entry = {'who': ('human+ai' if '🧑' in icons and '🤖' in icons else 'human' if '🧑' in icons else 'ai'),
                 'title': inline(t[len(icons):].strip()), 'items': []}
        day['entries'].append(entry)
    elif entry is not None and line.startswith('- '):
        t = line[2:].strip(); entry['items'].append({'kind': kind(t), 'html': inline(t)})
out = {'lang': 'hu', 'tools': tools, 'days': days,
       'en_summary': 'The full project log is kept in Hungarian. In short: an orchestrator chat plans and launches parallel '
                     'AI agents; the shared project documents act as their memory; the AI drives SOLIDWORKS through an MCP '
                     'server and checks every step with numbers (volume, position, interference). The human decides, approves, '
                     'installs – and catches the AI when it races ahead.'}
json.dump(out, open(os.path.join(SITE, 'content/naplo.hu.json'), 'w'), ensure_ascii=False, indent=1)
print('days', len(days), 'entries', sum(len(d['entries']) for d in days), 'tools', len(tools))
