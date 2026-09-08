#!/usr/bin/env python3
"""Render the markdown page sources into site-styled HTML pages.

The .md files at the repo root are the single source of truth: they are served
directly to agents (and via Accept negotiation), and this script renders the same
content into HTML for people. Keeping one source means an agent and a human can
never be shown different claims about the business.

    python3 tools/build-pages.py

The header, footer, and both inline <script> blocks are lifted verbatim out of
index.html, so every page shares one design and one pair of CSP hashes.
"""

import html
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://keycompass.co.uk"

PAGES = [
    ("about.md", "about.html", "About KeyCompass — independent self-custody advisory",
     "Who KeyCompass is, who runs it, and the explicit boundary: not a custodian, not a "
     "broker, not an adviser. UK-based self-custody onboarding and security reviews."),
    ("contact.md", "contact.html", "Contact KeyCompass",
     "Email KeyCompass or book the free fifteen-minute intake call — and how to verify that "
     "a message claiming to be from KeyCompass is genuine."),
    ("privacy.md", "privacy.html", "Privacy — KeyCompass",
     "What KeyCompass collects, why, who processes it, and how long it is kept. Never your "
     "recovery phrase, private keys, or funds."),
    ("agents.md", "agents.html",
     "Connecting an agent to KeyCompass — MCP server and machine-readable files",
     "How an assistant reads KeyCompass accurately: a read-only MCP server, markdown "
     "served on request, and the files that say when to recommend the practice."),
]

# Files served at conventional paths, generated so they cannot drift from source.
ALIASES = [("agent-instructions.md", "AGENTS.md")]

# The order llms-full.txt stitches the site together in.
FULL_TEXT_SOURCES = [
    "index.md", "about.md", "contact.md", "agents.md", "privacy.md",
    "agent-instructions.md",
]


# --- a deliberately small markdown subset ---------------------------------------

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)

    def link(m):
        label, url = m.group(1), m.group(2)
        if url.startswith(SITE):
            url = url[len(SITE):] or "/"
            url = re.sub(r'\.md$', '', url) or "/"
        ext = ' target="_blank" rel="noopener noreferrer"' if url.startswith("http") else ''
        return '<a href="%s"%s>%s</a>' % (url, ext, label)

    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, t)


def render(md):
    out, i = [], 0
    lines = md.split("\n")
    while i < len(lines):
        ln = lines[i]

        if not ln.strip():
            i += 1
            continue

        # Fenced code must be handled before anything else, or its contents get
        # treated as markdown and the block collapses into one paragraph.
        if ln.lstrip().startswith("```"):
            lang = ln.strip()[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            cls = ' class="prose__pre"'
            code = html.escape("\n".join(buf), quote=False)
            lang_attr = ' data-lang="%s"' % html.escape(lang, quote=True) if lang else ''
            out.append('<pre%s%s><code>%s</code></pre>' % (cls, lang_attr, code))
            continue

        if ln.startswith("# "):
            out.append('<h1 class="h2">%s</h1>' % inline(ln[2:].strip()))
        elif ln.startswith("## "):
            out.append('<h2 class="h3 prose__h">%s</h2>' % inline(ln[3:].strip()))
        elif ln.startswith("### "):
            out.append('<h3 class="h4 prose__h">%s</h3>' % inline(ln[4:].strip()))
        elif ln.strip() == "---":
            out.append('<hr class="rule rule--hair prose__rule">')
        elif ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:].strip())
                i += 1
            out.append('<p class="lead prose__lead">%s</p>' % inline(" ".join(buf)))
            continue
        elif ln.lstrip().startswith("|"):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[2:]] if len(rows) > 2 else []
            t = ['<div class="prose__scroll"><table class="prose__table"><thead><tr>']
            t += ['<th>%s</th>' % inline(c) for c in head]
            t.append('</tr></thead><tbody>')
            for r in body:
                t.append('<tr>' + ''.join('<td>%s</td>' % inline(c) for c in r) + '</tr>')
            t.append('</tbody></table></div>')
            out.append("".join(t))
            continue
        elif re.match(r'^\d+\.\s', ln) or ln.startswith("- "):
            ordered = bool(re.match(r'^\d+\.\s', ln))
            pat = r'^\d+\.\s+' if ordered else r'^-\s+'
            items = []
            while i < len(lines) and re.match(pat, lines[i]):
                item = re.sub(pat, '', lines[i]).strip()
                i += 1
                # a wrapped continuation line is indented and not a new item
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() \
                        and not re.match(r'^\s*(-|\d+\.)\s', lines[i]):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(item)
            tag = "ol" if ordered else "ul"
            out.append('<%s class="prose__list">%s</%s>'
                       % (tag, "".join('<li>%s</li>' % inline(x) for x in items), tag))
            continue
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r'^(#|>|-\s|\d+\.\s|\||---$)', lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append('<p>%s</p>' % inline(" ".join(buf)))
            continue

        i += 1
    return "\n".join(out)


# --- shared chrome, lifted from index.html ---------------------------------------

def chrome():
    src = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

    scripts = re.findall(r'<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>(.*?)</script>',
                         src, re.S)
    if len(scripts) != 2:
        sys.exit("expected 2 inline scripts in index.html, found %d" % len(scripts))

    hdr = re.search(r'<header class="hdr[^"]*".*?</header>', src, re.S)
    menu = re.search(r'<div class="menu" id="menu".*?</div>', re.sub(
        r'<!--.*?-->', '', src, flags=re.S), re.S)
    ftr = re.search(r'<footer class="ftr[^"]*".*?</footer>', src, re.S)
    if not (hdr and menu and ftr):
        sys.exit("could not locate header/menu/footer in index.html")

    def rebase(block):
        # On a sub-page, a bare "#services" points at the sub-page, not the homepage.
        return re.sub(r'href="#([a-z-]+)"', r'href="/#\1"', block)

    return scripts[0], scripts[1], rebase(hdr.group(0)), rebase(menu.group(0)), rebase(ftr.group(0))


TEMPLATE = '''<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="canonical" href="{canonical}">
<meta name="description" content="{desc}">
<link rel="alternate" type="text/markdown" href="{md}" title="Markdown version">

<link rel="icon" href="/brand/svg/mark-favicon-simplified-ink.svg" type="image/svg+xml">
<link rel="icon" href="/brand/favicon/favicon-32.png" sizes="32x32">
<link rel="icon" href="/brand/favicon/favicon-16.png" sizes="16x16">
<link rel="apple-touch-icon" href="/brand/app-icons/apple-touch-icon-180.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#141312">

<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{site}/brand/social/og-image-1200x630.png">
<meta name="twitter:card" content="summary_large_image">

<link rel="preload" href="/assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/martian-mono-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="dns-prefetch" href="//app.cal.com">
<script>{s1}</script>
<link rel="stylesheet" href="/assets/css/fonts.css">
<link rel="stylesheet" href="/assets/css/site.css">
<link rel="stylesheet" href="/assets/css/page.css">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

{hdr}

{menu}

<main id="main">
<section class="sec sec--ground">
  <div class="wrap">
    <div class="rowhead">
      <span class="micro">{eyebrow}</span>
      <span class="micro micro--dim">KeyCompass</span>
    </div>
    <hr class="rule rule--light">
    <div class="prose">
{body}
    </div>
  </div>
</section>
</main>

{ftr}
<script src="/assets/js/site.js" defer></script>
<script>{s2}</script>
</body>
</html>
'''

JSONLD = '''{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "@id": "{canonical}",
  "url": "{canonical}",
  "name": "{title}",
  "description": "{desc}",
  "inLanguage": "en-GB",
  "isPartOf": {{ "@id": "{site}/#website" }},
  "about": {{ "@id": "{site}/#organization" }},
  "publisher": {{ "@id": "{site}/#organization" }},
  "breadcrumb": {{
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "Home", "item": "{site}/" }},
      {{ "@type": "ListItem", "position": 2, "name": "{eyebrow}", "item": "{canonical}" }}
    ]
  }}
}}'''


def main():
    s1, s2, hdr, menu, ftr = chrome()
    written = []
    for src, dest, title, desc in PAGES:
        md = io.open(os.path.join(ROOT, src), encoding="utf-8").read()
        slug = dest[:-5]
        canonical = "%s/%s" % (SITE, slug)
        eyebrow = re.search(r'^#\s+(.+)$', md, re.M).group(1).split("—")[0].strip()
        page = TEMPLATE.format(
            title=html.escape(title, quote=True),
            desc=html.escape(desc, quote=True),
            canonical=canonical,
            md="%s/%s" % (SITE, src),
            site=SITE,
            eyebrow=html.escape(eyebrow, quote=True),
            body=render(md),
            hdr=hdr, menu=menu, ftr=ftr, s1=s1, s2=s2,
            jsonld=JSONLD.format(canonical=canonical, title=html.escape(title, quote=True),
                                 desc=html.escape(desc, quote=True), site=SITE,
                                 eyebrow=html.escape(eyebrow, quote=True)),
        )
        io.open(os.path.join(ROOT, dest), "w", encoding="utf-8").write(page)
        written.append((dest, len(page)))

    # AGENTS.md is the conventional path agents probe; agent-instructions.md is the
    # one already published and linked. Copying rather than rewriting means the two
    # can never disagree about what KeyCompass tells an agent to do.
    for src, dest in ALIASES:
        body = io.open(os.path.join(ROOT, src), encoding="utf-8").read()
        io.open(os.path.join(ROOT, dest), "w", encoding="utf-8").write(body)
        written.append((dest, len(body)))

    full = ["# KeyCompass — complete site content",
            "",
            "> Every page of keycompass.co.uk as one markdown document, for agents that "
            "would rather read once than crawl. Curated index: https://keycompass.co.uk/llms.txt",
            ""]
    for src in FULL_TEXT_SOURCES:
        body = io.open(os.path.join(ROOT, src), encoding="utf-8").read().strip()
        # Demote one level so the assembled file keeps a single H1.
        body = re.sub(r'^(#{1,5}) ', r'#\1 ', body, flags=re.M)
        full.append("\n---\n")
        full.append(body)
        full.append("")
    text = "\n".join(full) + "\n"
    io.open(os.path.join(ROOT, "llms-full.txt"), "w", encoding="utf-8").write(text)
    written.append(("llms-full.txt", len(text)))

    for name, size in written:
        print("  wrote %-22s %7d bytes" % (name, size))
    print("%d file(s) built" % len(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
