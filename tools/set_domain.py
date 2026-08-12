# -*- coding: utf-8 -*-
"""Re-point every canonical, og:url, og:image, twitter:image, sitemap and robots entry
at a new base URL.

    python3 tools/set_domain.py https://www.dhwaniris.com

This matters: a canonical pointing at a host that serves a DIFFERENT site tells Google
to credit that site instead. If launch lands anywhere other than the domain currently
baked in, run this before going live.
"""
import io, re, sys, glob, os

if len(sys.argv) != 2:
    print(__doc__); raise SystemExit(1)
NEW = sys.argv[1].rstrip('/')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OLD = None
s = io.open('index.html', encoding='utf-8').read()
m = re.search(r'<link rel="canonical" href="(https?://[^/"]+)', s)
if m: OLD = m.group(1)
if not OLD:
    print('could not read the current base URL from index.html'); raise SystemExit(1)
if OLD == NEW:
    print('already set to %s' % NEW); raise SystemExit(0)

n = 0
for f in sorted(glob.glob('*.html')) + sorted(glob.glob('insights/*.html')) + ['sitemap.xml', 'robots.txt']:
    if not os.path.exists(f): continue
    s = io.open(f, encoding='utf-8').read()
    if OLD not in s: continue
    io.open(f, 'w', encoding='utf-8').write(s.replace(OLD, NEW))
    n += 1
print('re-pointed %s -> %s across %d files' % (OLD, NEW, n))
