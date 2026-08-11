#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard against the kind of damage a bulk edit does silently.

    python3 tools/check.py snapshot     # before you edit
    python3 tools/check.py verify       # after you edit

verify reports, per page:
  - CSS rules that disappeared        (a regex ate them)
  - CSS rules whose position moved    (the cascade changed)
  - internal links that no longer resolve
  - unbalanced <section> or <div>
  - <script> blocks that stopped parsing
  - filter values on Our Work cards with no matching chip

Every one of these has been a real bug on this site at least once.
"""
import io, re, os, sys, json, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAP = os.path.join(ROOT, 'tools', '.snapshot.json')


def rules(css):
    """Ordered list of (selector, normalised body)."""
    out = []; i = 0; n = len(css)
    while i < n:
        while i < n and css[i] in ' \n\t;': i += 1
        if i >= n: break
        if css[i:i+2] == '/*':
            j = css.find('*/', i); i = (j + 2 if j > 0 else n); continue
        if css.startswith('@', i):
            j = css.find('{', i)
            if j < 0: break
            d = 1; k = j + 1
            while d and k < n:
                if css[k] == '{': d += 1
                elif css[k] == '}': d -= 1
                k += 1
            out.append((css[i:j].strip(), re.sub(r'\s+', '', css[i:k]))); i = k; continue
        j = css.find('{', i)
        if j < 0: break
        k = css.find('}', j)
        out.append((css[i:j].strip(), re.sub(r'\s+', '', css[i:k+1]))); i = k + 1
    return out


def page_css(s):
    return ''.join(m.group(1) for m in re.finditer(r'<style>(.*?)</style>', s, re.S))


def inventory():
    inv = {}
    for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
        s = io.open(f, encoding='utf-8').read()
        rs = rules(page_css(s))
        inv[os.path.basename(f)] = {
            'rules': [b for _, b in rs],
            'selectors': [sel for sel, _ in rs],
        }
    return inv


def structural():
    """Faults that do not need a before/after to spot."""
    faults = []
    for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
        name = os.path.basename(f)
        s = io.open(f, encoding='utf-8').read()
        if s.count('<section') != s.count('</section>'):
            faults.append((name, 'unbalanced <section>'))
        body = re.sub(r'<script\b.*?</script>', '', s, flags=re.S)
        body = re.sub(r'<style\b.*?</style>', '', body, flags=re.S)
        if len(re.findall(r'<div\b', body)) != len(re.findall(r'</div>', body)):
            faults.append((name, 'unbalanced <div>'))
        for u in re.findall(r'href="([^"#?:]+\.html)"', s):
            if not os.path.exists(os.path.join(ROOT, u)):
                faults.append((name, 'link goes nowhere: %s' % u))
        if re.search(r"url\(\\'", s):
            faults.append((name, 'escaped quote in a background-image url'))
        if re.search(r'&mdash;|—', re.sub(r'<script\b.*?</script>', '', s, flags=re.S)):
            faults.append((name, 'em dash in copy'))
    # Our Work: a card value with no chip can never be reached
    ow = os.path.join(ROOT, 'our-work.html')
    if os.path.exists(ow):
        s = io.open(ow, encoding='utf-8').read()
        chips = {d: set(re.findall(r'data-dim="%s" data-val="([^"]*)"' % d, s))
                 for d in ('sector', 'offering', 'audience', 'function')}
        for attr in re.findall(r'<button type="button" class="wcard"([^>]*)>', s):
            cid = re.search(r'data-case="([^"]+)"', attr)
            for d, valid in chips.items():
                m = re.search(r'data-%s="([^"]*)"' % d, attr)
                for v in (m.group(1).split() if m else []):
                    if v and v not in valid:
                        faults.append(('our-work.html',
                                       '%s: %s="%s" has no filter chip' % (cid.group(1), d, v)))

    # a component used without its stylesheet renders raw in the page flow
    COMPONENTS = {
        'ccph': '.ccph{', 'ccbd': '.ccbd{', 'ccstat': '.ccstat{', 'cckeys': '.cckeys{',
        'ccmore': '.ccmore{', 'ccards': '.ccards{', 'cmodal': '.cmodal{', 'handover': '.handover{',
        'steps': '.steps{', 'sitelink': '.sitelink{', 'deckbar': '.deckbar{', 'prodsite': '.prodsite{',
        'crumbbar': '.crumbbar{', 'fnav': '.fnav{', 'tchip': '.tchip{', 'tnote': '.tnote{',
        'getlist': '.getlist{', 'figrow': '.figrow{', 'creds': '.creds{', 'callout': '.callout{',
        'sect-chip': '.sect-chip{', 'jfit': '.jfit{', 'minicase': '.minicase{',
    }
    for f in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
        name = os.path.basename(f)
        s = io.open(f, encoding='utf-8').read()
        for cls, rule in COMPONENTS.items():
            if 'class="%s' % cls in s and rule not in s:
                faults.append((name, 'uses .%s but has no styles for it' % cls))
    return faults


def cmd_snapshot():
    json.dump(inventory(), io.open(SNAP, 'w', encoding='utf-8'))
    inv = inventory()
    print('snapshot written: %d pages, %d rules' %
          (len(inv), sum(len(v['rules']) for v in inv.values())))


def cmd_verify():
    if not os.path.exists(SNAP):
        print('no snapshot; run "snapshot" first'); return 1
    before = json.load(io.open(SNAP, encoding='utf-8'))
    after = inventory()
    problems = 0

    for name, old in before.items():
        new = after.get(name)
        if new is None:
            print('REMOVED PAGE  %s' % name); problems += 1; continue
        lost = [r for r in old['rules'] if r not in new['rules']]
        if lost:
            print('LOST %d CSS rules on %s' % (len(lost), name)); problems += 1
            for r in lost[:6]:
                print('       %s' % r[:96])
        moved = 0
        common = [s for s in old['selectors'] if s in new['selectors']]
        for s in set(common):
            if old['selectors'].index(s) != new['selectors'].index(s): moved += 1
        if moved:
            print('MOVED %d selectors on %s (the cascade changed)' % (moved, name)); problems += 1
    for name in set(after) - set(before):
        print('new page: %s' % name)

    for name, fault in structural():
        print('FAULT  %-26s %s' % (name, fault)); problems += 1

    print('\n%s' % ('no problems found' if not problems else '%d problem(s) above' % problems))
    return 1 if problems else 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    sys.exit(cmd_snapshot() if cmd == 'snapshot' else cmd_verify())
