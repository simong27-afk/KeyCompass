#!/usr/bin/env python3
"""Render the markdown page sources into site-styled HTML pages.

The .md files at the repo root are the single source of truth: they are served
directly to agents (and via Accept negotiation), and this script renders the same
content into HTML for people. Keeping one source means an agent and a human can
never be shown different claims about the business.

    python3 tools/build-pages.py

The header, footer, and both inline <script> blocks are lifted verbatim out of
index.html, so every page shares one design and one pair of CSP hashes.

Guides
------
A guide is a markdown file that starts with a small front-matter block:

    ---
    title: Metal backups: are they worth it? — KeyCompass
    description: One or two sentences for search results (aim for ~155 characters).
    category: Backups
    published: 2026-10-06
    checked: 2026-10-06
    featured: no
    ---
    # Metal backups: are they worth it?
    ...

New guides go in guides/<slug>.md and are served at /guides/<slug>. Dropping a
file in and re-running this script is the whole job: it renders the page (with
byline, dates and Article structured data), rebuilds the /guides/ index, and
regenerates sitemap.xml, the Guides section of llms.txt, and llms-full.txt. The
one guide that predates the section, lost-recovery-phrase.md, stays at the repo
root so its existing URL keeps the ranking it has already earned.

"checked" is the date Simon last verified every claim in the guide against the
wallet makers' own documentation. It is printed on the page, so only move it
forward after actually doing that check.
"""

import datetime
import glob
import html
import io
import json
import math
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
     "Email KeyCompass or book the free thirty-minute intake call — and how to verify that "
     "a message claiming to be from KeyCompass is genuine."),
    ("privacy.md", "privacy.html", "Privacy — KeyCompass",
     "What KeyCompass collects, why, who processes it, and how long it is kept. Never your "
     "recovery phrase, private keys, or funds."),
    ("terms.md", "terms.html", "Terms and conditions — KeyCompass",
     "The terms on which KeyCompass provides onboarding sessions and security reviews: the "
     "custody boundary, cancellation rights, fees, and liability."),
    ("pricing.md", "pricing.html", "Pricing — KeyCompass",
     "KeyCompass prices: a free 30-minute intake call, a £95 drop-in hour, private "
     "onboarding sessions from £195 and security reviews from £295. No VAT, no percentage "
     "of holdings."),
    # Source is connect.md, not agents.md: on a case-insensitive filesystem
    # agents.md IS AGENTS.md, and the alias step below would silently overwrite it.
    ("connect.md", "agents.html",
     "Connecting an agent to KeyCompass — MCP server and machine-readable files",
     "How an assistant reads KeyCompass accurately: a read-only MCP server, markdown "
     "served on request, and the files that say when to recommend the practice."),
]

# Files served at conventional paths, generated so they cannot drift from source.
ALIASES = [("agent-instructions.md", "AGENTS.md")]

# The order llms-full.txt stitches the site together in. Guides are inserted
# after the core pages, newest first, by main().
FULL_TEXT_SOURCES = [
    "index.md", "pricing.md", "about.md", "contact.md", "connect.md", "privacy.md",
    "terms.md",
]
FULL_TEXT_TAIL = ["agent-instructions.md"]

# Guides that live at the repo root for historical reasons; everything else is
# discovered from guides/*.md.
ROOT_GUIDES = ["lost-recovery-phrase.md"]
GUIDES_DIR = "guides"

AUTHOR = "Simon Geils"
WORDS_PER_MINUTE = 220

# Pages that are not guides but belong in the sitemap. /terms is deliberately
# absent: it was added as an unpublished draft and is not linked from the site.
SITEMAP_PAGES = [
    ("/", "monthly", "1.0"),
    ("/about", "yearly", "0.8"),
    ("/contact", "yearly", "0.8"),
    ("/pricing", "monthly", "0.9"),
    ("/guides/", "weekly", "0.9"),
    ("/agents", "monthly", "0.6"),
    ("/privacy", "yearly", "0.3"),
]


# --- a deliberately small markdown subset ---------------------------------------

BOOKING_LINK = re.compile(r'^\[([^\]]+)\]\((https://cal\.com/simongeils/([a-z0-9-]+))\)$')

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
            # A paragraph that is nothing but a booking link becomes a button that
            # opens the Cal.com pop-up, the same way every Book button on the site does.
            cta = BOOKING_LINK.match(" ".join(t for t, _ in buf).strip())
            if cta:
                out.append('<p class="prose__cta"><a class="btn btn--accent" href="%s" '
                           'data-cal-namespace="intake" data-cal-link="simongeils/%s">%s</a></p>'
                           % (cta.group(2), cta.group(3), html.escape(cta.group(1), quote=False)))
            else:
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

<meta property="og:type" content="{ogtype}">
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
      <span class="micro">{eyebrow_html}</span>
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

def anchor(heading):
    """'Drop-in hour' -> 'drop-in-hour', so a section can be linked to directly."""
    return re.sub(r'[^a-z0-9]+', '-', re.sub(r'<[^>]+>', '', heading).lower()).strip('-')


BLOCK = '''<section class="sec sec--ground page__block" id="{anchor}" data-reveal>
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


# --- guides ------------------------------------------------------------------------

FRONT_MATTER = re.compile(r'\A---\n(.*?)\n---\n', re.S)
REQUIRED_META = ("title", "description", "category", "published", "checked")


def front_matter(text, src):
    """(meta, body). Every guide must carry the fields in REQUIRED_META."""
    m = FRONT_MATTER.match(text)
    if not m:
        sys.exit("%s: a guide must start with a --- front-matter block" % src)
    meta = {}
    for line in m.group(1).split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            sys.exit("%s: front-matter line has no ':' — %r" % (src, line))
        key, value = line.split(":", 1)
        meta[key.strip().lower()] = value.strip()
    missing = [k for k in REQUIRED_META if not meta.get(k)]
    if missing:
        sys.exit("%s: front matter is missing %s" % (src, ", ".join(missing)))
    for key in ("published", "checked"):
        try:
            meta[key] = datetime.date.fromisoformat(meta[key])
        except ValueError:
            sys.exit("%s: %s must be a date like 2026-10-06, got %r" % (src, key, meta[key]))
    if meta["checked"] < meta["published"]:
        sys.exit("%s: checked (%s) is earlier than published (%s)"
                 % (src, meta["checked"], meta["published"]))
    meta["featured"] = meta.get("featured", "").lower() in ("yes", "true", "1")
    return meta, text[m.end():]


def strip_front_matter(text):
    return FRONT_MATTER.sub("", text, count=1)


def human_date(d):
    return "%d %s" % (d.day, d.strftime("%b %Y"))


def reading_minutes(body):
    words = len(re.findall(r"[A-Za-z0-9'’-]+", body))
    return max(1, int(math.ceil(words / float(WORDS_PER_MINUTE))))


def load_guides():
    sources = list(ROOT_GUIDES) + sorted(
        os.path.relpath(p, ROOT)
        for p in glob.glob(os.path.join(ROOT, GUIDES_DIR, "*.md"))
        if os.path.basename(p) != "index.md")
    guides = []
    for src in sources:
        text = io.open(os.path.join(ROOT, src), encoding="utf-8").read()
        meta, body = front_matter(text, src)
        stem = os.path.splitext(src)[0].replace(os.sep, "/")
        if not re.match(r'^([a-z0-9-]+/)?[a-z0-9-]+$', stem):
            sys.exit("%s: guide file names must be lower-case words joined by hyphens" % src)
        h1, lead, intro, blocks = split_sections(body)
        guides.append(dict(
            meta, src=src.replace(os.sep, "/"), dest=stem + ".html", path="/" + stem,
            url="%s/%s" % (SITE, stem), md_url="%s/%s" % (SITE, src.replace(os.sep, "/")),
            h1=h1, lead=lead, intro=intro, blocks=blocks,
            minutes=reading_minutes(body)))
    # Newest first; a tie keeps file order.
    guides.sort(key=lambda g: g["published"], reverse=True)
    return guides


def json_ld(obj):
    # "</" would close the <script> element early; JSON allows the escaped form.
    return json.dumps(obj, indent=2, ensure_ascii=False).replace("</", "<\\/")


def breadcrumb(*crumbs):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": n, "name": name, "item": url}
        for n, (name, url) in enumerate(crumbs, 1)]}


BYLINE = '''    <dl class="byline">
      <div><dt>Written by</dt><dd><a href="/about">{author}</a></dd></div>
      <div><dt>Published</dt><dd><time datetime="{pub_iso}">{pub}</time></dd></div>
      <div><dt>Last checked</dt><dd><time datetime="{chk_iso}">{chk}</time></dd></div>
      <div><dt>Reading time</dt><dd>{minutes} min</dd></div>
    </dl>
    <p class="checked"><strong>Checked by a person.</strong> {author} last went through every
      claim on this page on {chk}. Spotted something out of date?
      <a href="/contact">Tell us</a> and it will be corrected.</p>
'''

GUIDE_ROW = '''      <li class="guides__row">
        <span class="micro micro--dim guides__cat">{category}</span>
        <a class="guides__link" href="{path}">
          <h3 class="h4 guides__title">{h1}</h3>
          <p class="guides__lead">{lead}</p>
        </a>
        <span class="micro micro--dim guides__min">{minutes} min</span>
      </li>
'''

MORE_GUIDES = '''<section class="sec sec--ground page__block guides__more" data-reveal>
  <div class="wrap">
    <hr class="rule rule--hair">
    <h2 class="h3 page__h">More guides</h2>
    <ul class="guides">
{rows}    </ul>
    <p class="guides__all"><a href="/guides/">All guides</a></p>
  </div>
</section>
'''

FEATURE = '''    <div class="feature">
      <div class="feature__fig" aria-hidden="true">
        <span class="micro feature__tag">Fig. 01</span>
        <svg class="feature__mark" viewBox="0 0 100 100" fill="currentColor" fill-rule="evenodd">
          <path d="M4 4h92v92H4z M14 14v72h72V14z"/>
          <path d="M32 32h36v36H32z M42 42v16h16V42z"/>
          <rect x="44" y="12" width="12" height="22"/>
          <rect x="44" y="66" width="12" height="22"/>
          <rect x="66" y="44" width="22" height="12"/>
          <rect x="12" y="44" width="22" height="12"/>
        </svg>
      </div>
      <div class="feature__body">
        <span class="micro">Featured · {category} · {minutes} min</span>
        <h2 class="h3 feature__title"><a href="{path}">{h1}</a></h2>
        <p class="feature__lead">{lead}</p>
        <a class="btn btn--accent btn--sm" href="{path}">Read the guide</a>
      </div>
    </div>
'''

INDEX_TITLE = "Guides to self-custody — KeyCompass"
INDEX_H1 = "Guides to keeping your crypto yours."
INDEX_LEAD = ("Plain-English guides to self-custody: setting up, backing up, spotting scams, "
              "and planning for the people who come after you. Written and checked by "
              "Simon Geils.")
INDEX_DESC = ("Plain-English guides to crypto self-custody from KeyCompass: hardware wallet "
              "setup, recovery phrase backups, scams to watch for, and inheritance.")


def row(g):
    return GUIDE_ROW.format(category=html.escape(g["category"]), path=g["path"],
                            h1=html.escape(g["h1"], quote=False),
                            lead=inline(g["lead"]), minutes=g["minutes"])


def render_guide(g, others, chrome_parts):
    s1, s2, hdr, menu, ftr = chrome_parts
    head_extra = ""
    if g["lead"]:
        head_extra += '    <p class="lead page__lead">%s</p>\n' % inline(g["lead"])
    head_extra += BYLINE.format(author=AUTHOR, minutes=g["minutes"],
                                pub_iso=g["published"].isoformat(), pub=human_date(g["published"]),
                                chk_iso=g["checked"].isoformat(), chk=human_date(g["checked"]))
    if g["intro"]:
        head_extra += '    <div class="prose page__intro">\n%s\n    </div>\n' % g["intro"]

    blocks = "".join(BLOCK.format(heading=inline(h), anchor=anchor(h), body=b) for h, b in g["blocks"])
    # Up to three other guides, same category first. Internal links are how Google
    # finds and weighs new guides, so every guide links to its neighbours.
    if others:
        picks = sorted(others, key=lambda o: o["category"] != g["category"])[:3]
        blocks += MORE_GUIDES.format(rows="".join(row(o) for o in picks))

    ld = {
        "@context": "https://schema.org",
        "@type": "Article",
        "@id": g["url"] + "#article",
        "mainEntityOfPage": g["url"],
        "url": g["url"],
        "headline": g["h1"],
        "description": g["description"],
        "articleSection": g["category"],
        "inLanguage": "en-GB",
        "datePublished": g["published"].isoformat(),
        "dateModified": g["checked"].isoformat(),
        "image": SITE + "/brand/social/og-image-1200x630.png",
        "author": {"@type": "Person", "@id": SITE + "/#person", "name": AUTHOR,
                   "url": SITE + "/about"},
        "publisher": {"@id": SITE + "/#organization"},
        "isPartOf": {"@id": SITE + "/#website"},
        "breadcrumb": breadcrumb(("Home", SITE + "/"), ("Guides", SITE + "/guides/"),
                                 (g["h1"], g["url"])),
    }

    eyebrow_html = ('<a class="crumb" href="/guides/">Guides</a> / %s'
                    % html.escape(g["category"]))
    return TEMPLATE.format(
        h1=html.escape(g["h1"], quote=False), head_extra=head_extra, blocks=blocks,
        title=html.escape(g["title"], quote=True), desc=html.escape(g["description"], quote=True),
        canonical=g["url"], md=g["md_url"], site=SITE, ogtype="article",
        eyebrow_html=eyebrow_html, hdr=hdr, menu=menu, ftr=ftr, s1=s1, s2=s2,
        jsonld=json_ld(ld))


def render_index(guides, chrome_parts):
    s1, s2, hdr, menu, ftr = chrome_parts
    featured = next((g for g in guides if g["featured"]), guides[0])
    rest = [g for g in guides if g is not featured]

    head_extra = '    <p class="lead page__lead">%s</p>\n' % html.escape(INDEX_LEAD, quote=False)
    head_extra += FEATURE.format(category=html.escape(featured["category"]),
                                 minutes=featured["minutes"], path=featured["path"],
                                 h1=html.escape(featured["h1"], quote=False),
                                 lead=inline(featured["lead"]))
    if rest:
        head_extra += '    <ul class="guides">\n%s    </ul>\n' % "".join(row(g) for g in rest)

    url = SITE + "/guides/"
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": url,
        "url": url,
        "name": INDEX_TITLE,
        "description": INDEX_DESC,
        "inLanguage": "en-GB",
        "isPartOf": {"@id": SITE + "/#website"},
        "publisher": {"@id": SITE + "/#organization"},
        "breadcrumb": breadcrumb(("Home", SITE + "/"), ("Guides", url)),
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": n, "url": g["url"], "name": g["h1"]}
            for n, g in enumerate([featured] + rest, 1)]},
    }
    return TEMPLATE.format(
        h1=html.escape(INDEX_H1, quote=False), head_extra=head_extra, blocks="",
        title=html.escape(INDEX_TITLE, quote=True), desc=html.escape(INDEX_DESC, quote=True),
        canonical=url, md=SITE + "/guides/index.md", site=SITE, ogtype="website",
        eyebrow_html="Guides", hdr=hdr, menu=menu, ftr=ftr, s1=s1, s2=s2,
        jsonld=json_ld(ld))


def index_markdown(guides):
    out = ["# " + INDEX_H1, "", "> " + INDEX_LEAD, ""]
    for g in guides:
        out.append("- [%s](%s) — %s (%s, last checked %s)"
                   % (g["h1"], g["md_url"], g["description"], g["category"],
                      g["checked"].isoformat()))
    return "\n".join(out) + "\n"


def sitemap(guides):
    rows = []
    entries = [(p, f, pr, None) for p, f, pr in SITEMAP_PAGES]
    entries += [(g["path"], "monthly", "0.9" if g["featured"] else "0.8", g["checked"])
                for g in guides]
    for path, freq, prio, lastmod in entries:
        rows.append("  <url>\n    <loc>%s%s</loc>\n%s    <changefreq>%s</changefreq>\n"
                    "    <priority>%s</priority>\n  </url>"
                    % (SITE, path, ("    <lastmod>%s</lastmod>\n" % lastmod.isoformat())
                       if lastmod else "", freq, prio))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def llms_guides_section(guides):
    lines = ["## Guides", "",
             "- [All guides](%s/guides/index.md): Every guide, newest first, with the date "
             "each was last checked." % SITE]
    for g in guides:
        lines.append("- [%s](%s): %s" % (g["h1"], g["md_url"], g["description"]))
    return "\n".join(lines) + "\n"


def update_llms_txt(guides):
    path = os.path.join(ROOT, "llms.txt")
    text = io.open(path, encoding="utf-8").read()
    section = llms_guides_section(guides)
    pattern = re.compile(r'^## Guides\n.*?(?=^## |\Z)', re.S | re.M)
    if pattern.search(text):
        text = pattern.sub(section + "\n", text, count=1)
    else:
        # First run: place it just before "## Agent interfaces".
        anchor = "## Agent interfaces"
        if anchor not in text:
            sys.exit("llms.txt: cannot find '%s' to insert the Guides section" % anchor)
        text = text.replace(anchor, section + "\n" + anchor, 1)
    io.open(path, "w", encoding="utf-8").write(text)
    return text


# --- build -------------------------------------------------------------------------

def write(rel, text, written):
    path = os.path.join(ROOT, rel)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    io.open(path, "w", encoding="utf-8").write(text)
    written.append((rel, len(text)))


def main():
    chrome_parts = chrome()
    s1, s2, hdr, menu, ftr = chrome_parts
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
            BLOCK.format(heading=inline(h), anchor=anchor(h), body=b) for h, b in blocks)

        page = TEMPLATE.format(
            h1=html.escape(h1, quote=False),
            head_extra=head_extra,
            blocks=rendered_blocks,
            title=html.escape(title, quote=True),
            desc=html.escape(desc, quote=True),
            canonical=canonical,
            md="%s/%s" % (SITE, src),
            site=SITE,
            ogtype="website",
            eyebrow_html=html.escape(eyebrow, quote=True),
            hdr=hdr, menu=menu, ftr=ftr, s1=s1, s2=s2,
            jsonld=JSONLD.format(canonical=canonical, title=html.escape(title, quote=True),
                                 desc=html.escape(desc, quote=True), site=SITE,
                                 eyebrow=html.escape(eyebrow, quote=True)),
        )
        write(dest, page, written)

    guides = load_guides()
    for g in guides:
        others = [o for o in guides if o is not g]
        write(g["dest"], render_guide(g, others, chrome_parts), written)
    write(os.path.join(GUIDES_DIR, "index.html"), render_index(guides, chrome_parts), written)
    write(os.path.join(GUIDES_DIR, "index.md"), index_markdown(guides), written)
    write("sitemap.xml", sitemap(guides), written)
    written.append(("llms.txt", len(update_llms_txt(guides))))

    # AGENTS.md is the conventional path agents probe; agent-instructions.md is the
    # one already published and linked. Copying rather than rewriting means the two
    # can never disagree about what KeyCompass tells an agent to do.
    for src, dest in ALIASES:
        body = io.open(os.path.join(ROOT, src), encoding="utf-8").read()
        write(dest, body, written)

    full = ["# KeyCompass — complete site content",
            "",
            "> Every page of keycompass.co.uk as one markdown document, for agents that "
            "would rather read once than crawl. Curated index: https://keycompass.co.uk/llms.txt",
            ""]
    for src in FULL_TEXT_SOURCES + [g["src"] for g in guides] + FULL_TEXT_TAIL:
        body = strip_front_matter(
            io.open(os.path.join(ROOT, src), encoding="utf-8").read()).strip()
        # Demote one level so the assembled file keeps a single H1.
        body = re.sub(r'^(#{1,5}) ', r'#\1 ', body, flags=re.M)
        full.append("\n---\n")
        full.append(body)
        full.append("")
    write("llms-full.txt", "\n".join(full) + "\n", written)

    for name, size in written:
        print("  wrote %-34s %7d bytes" % (name, size))
    print("%d file(s) built, %d guide(s)" % (len(written), len(guides)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
