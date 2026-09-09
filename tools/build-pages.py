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
    # Source is connect.md, not agents.md: on a case-insensitive filesystem
    # agents.md IS AGENTS.md, and the alias step below would silently overwrite it.
    ("connect.md", "agents.html",
     "Connecting an agent to KeyCompass — MCP server and machine-readable files",
     "How an assistant reads KeyCompass accurately: a read-only MCP server, markdown "
     "served on request, and the files that say when to recommend the practice."),
]

# Files served at conventional paths, generated so they cannot drift from source.
ALIASES = [("agent-instructions.md", "AGENTS.md")]

# The order llms-full.txt stitches the site together in.
FULL_TEXT_SOURCES = [
    "index.md", "about.md", "contact.md", "connect.md", "privacy.md",
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


def split_sections(md):
    """(title, lead, intro, [(h2, body), ...]) — H2 headings become sections.

    The homepage animates per section: [data-reveal] on the <section>, with the
    rowhead, rule and .wrap children staggered as they scroll in. One giant
    .prose div has nothing to stagger and nothing to observe, which is why these
    pages arrived flat. Splitting at H2 gives each part its own reveal.
    """
    lines = md.split("\n")
    title, lead, i = "", [], 0

    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i < len(lines):
        title = lines[i][2:].strip()
        i += 1

    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].startswith("> "):
        lead.append(lines[i][2:].strip())
        i += 1

    intro, blocks, current, heading = [], [], [], None
    for ln in lines[i:]:
        if ln.startswith("## "):
            (blocks.append((heading, current)) if heading is not None
             else intro.extend(current))
            heading, current = ln[3:].strip(), []
        else:
            current.append(ln)
    if heading is not None:
        blocks.append((heading, current))
    else:
        intro.extend(current)

    return (title, " ".join(lead),
            render("\n".join(intro)).strip(),
            [(h, render("\n".join(b)).strip()) for h, b in blocks])


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

        if ln.startswith("### "):
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
            # A line ending in two spaces is a hard break, the markdown
            # convention. Needed for postal addresses, which must keep their
            # line structure rather than collapsing into one run of text.
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(
                    r'^(#|>|-\s|\d+\.\s|\||---$)', lines[i]):
                buf.append((lines[i].rstrip(), lines[i].endswith("  ")))
                i += 1
            para = ""
            for n, (text, hard) in enumerate(buf):
                if n:
                    para += "<br>" if buf[n - 1][1] else " "
                para += inline(text.strip())
            out.append('<p>%s</p>' % para)
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
<section class="sec sec--ground page__head" data-reveal>
  <div class="wrap">
    <div class="rowhead">
      <span class="micro">{eyebrow}</span>
      <span class="micro micro--dim">KeyCompass</span>
    </div>
    <hr class="rule rule--light">
    <h1 class="h2 sec__head">{h1}</h1>
{head_extra}  </div>
</section>
{blocks}</main>

{ftr}
<script src="/assets/js/site.js" defer></script>
<script>{s2}</script>
</body>
</html>
'''

BLOCK = '''<section class="sec sec--ground page__block" data-reveal>
  <div class="wrap">
    <hr class="rule rule--hair">
    <h2 class="h3 page__h">{heading}</h2>
    <div class="prose">
{body}
    </div>
  </div>
</section>
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
        h1, lead, intro, blocks = split_sections(md)
        eyebrow = h1.split("—")[0].strip()

        head_extra = ""
        if lead:
            head_extra += '    <p class="lead page__lead">%s</p>\n' % inline(lead)
        if intro:
            head_extra += '    <div class="prose page__intro">\n%s\n    </div>\n' % intro

        rendered_blocks = "".join(
            BLOCK.format(heading=inline(h), body=b) for h, b in blocks)

        page = TEMPLATE.format(
            h1=html.escape(h1, quote=False),
            head_extra=head_extra,
            blocks=rendered_blocks,
            title=html.escape(title, quote=True),
            desc=html.escape(desc, quote=True),
            canonical=canonical,
            md="%s/%s" % (SITE, src),
            site=SITE,
            eyebrow=html.escape(eyebrow, quote=True),
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
