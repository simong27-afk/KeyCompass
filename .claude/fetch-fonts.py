"""Re-download the self-hosted fonts and regenerate assets/css/fonts.css.
Both families are variable, so each subset is one file covering a weight range."""
import re, urllib.request, os, collections

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
URL = ("https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700;800"
       "&family=Martian+Mono:wght@400;500;600&display=swap")
KEEP = ['latin', 'latin-ext']
ROOT = os.path.join(os.path.dirname(__file__), '..')

def get(u, binary=False):
    r = urllib.request.Request(u, headers={'User-Agent': UA})
    with urllib.request.urlopen(r) as f:
        return f.read() if binary else f.read().decode('utf-8')

css = get(URL)
faces = collections.OrderedDict()
for subset, block in re.findall(r'/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})', css, re.S):
    if subset not in KEEP:
        continue
    fam = re.search(r"font-family:\s*'([^']+)'", block).group(1)
    w   = int(re.search(r'font-weight:\s*([^;]+);', block).group(1).strip())
    key = (fam, subset)
    e = faces.setdefault(key, {
        'url': re.search(r"url\((https://fonts\.gstatic\.com[^)]+)\)", block).group(1),
        'range': re.search(r'unicode-range:\s*([^;]+);', block).group(1).strip(),
        'min': w, 'max': w})
    e['min'] = min(e['min'], w); e['max'] = max(e['max'], w)

os.makedirs(os.path.join(ROOT, 'assets/fonts'), exist_ok=True)
out, total = [], 0
for (fam, subset), e in faces.items():
    name = f"{fam.lower().replace(' ', '-')}-{subset}.woff2"
    data = get(e['url'], binary=True)
    open(os.path.join(ROOT, 'assets/fonts', name), 'wb').write(data)
    total += len(data)
    print(f"  {name:32s} {len(data)/1024:6.1f} KB  weights {e['min']}-{e['max']}")
    out.append(f"""@font-face{{
  font-family:'{fam}';
  font-style:normal;
  font-weight:{e['min']} {e['max']};
  font-display:swap;
  src:url('../fonts/{name}') format('woff2');
  unicode-range:{e['range']};
}}""")

header = ("/* Self-hosted from Google Fonts. Removes two third-party round trips from\n"
          "   the critical path, and no visitor request goes to Google.\n"
          "   Both families are variable: one file per subset covers every weight.\n"
          "   Regenerate: python3 .claude/fetch-fonts.py */\n\n")
open(os.path.join(ROOT, 'assets/css/fonts.css'), 'w').write(header + '\n'.join(out) + '\n')
print(f"\n{len(out)} @font-face rules, {total/1024:.1f} KB on disk")
