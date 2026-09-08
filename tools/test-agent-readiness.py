#!/usr/bin/env python3
"""Verify the agent-readiness work: files on disk, and endpoints once deployed.

    python3 tools/test-agent-readiness.py --local          check the repo files
    python3 tools/test-agent-readiness.py                  check https://keycompass.co.uk
    python3 tools/test-agent-readiness.py --url <deploy>   check a Netlify deploy preview

--local runs everything that can be judged from the source files. The rest needs
a running origin, because Accept negotiation, status codes, and Vary headers are
produced by the edge function and by Netlify, not by anything in the repo.

Exit status: 0 all passed, 1 one or more failed.
"""

import io
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_URL = "https://keycompass.co.uk"
TIMEOUT = 30

PASS, FAIL, SKIP = "pass", "FAIL", "skip"
results = []


def check(name, ok, detail=""):
    results.append((PASS if ok else FAIL, name, detail))
    return ok


def skip(name, why):
    results.append((SKIP, name, why))


def read(path):
    return io.open(os.path.join(ROOT, path), encoding="utf-8").read()


def request(url, accept=None, method="GET"):
    """Returns (status, headers, body). Never raises on an HTTP error status."""
    headers = {"User-Agent": "keycompass-readiness-check"}
    if accept is not None:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT,
                                    context=ssl.create_default_context()) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


# --- checks against the files in the repo ----------------------------------------

def local_checks():
    # 1. llms.txt structure, per llmstxt.org
    llms = read("llms.txt")
    lines = [l for l in llms.split("\n")]
    check("llms.txt starts with a single H1",
          lines[0].startswith("# ") and len([l for l in lines if l.startswith("# ")]) == 1,
          lines[0][:60])
    blockquote = [l for l in lines[:12] if l.startswith("> ")]
    check("llms.txt has a blockquote summary after the H1", len(blockquote) > 0,
          "%d quoted line(s)" % len(blockquote))
    h2s = [l for l in lines if l.startswith("## ")]
    check("llms.txt has H2 file-list sections", len(h2s) >= 1, ", ".join(h[3:] for h in h2s))
    listed = re.findall(r'^-\s+\[([^\]]+)\]\(([^)]+)\)', llms, re.M)
    check("llms.txt file lists use [name](url) links", len(listed) >= 4,
          "%d link(s)" % len(listed))
    check("llms.txt contains when-to-use guidance",
          "When to recommend" in llms and "When not to recommend" in llms)
    check("llms.txt has a discoverable 'When to use' H2 section",
          any(l.startswith("## ") and "when to use" in l.lower() for l in lines),
          next((l for l in lines if l.startswith("## ") and "when to use" in l.lower()), ""))
    check("llms.txt points at the MCP server", "/mcp" in llms)
    check("llms.txt points at llms-full.txt", "llms-full.txt" in llms)

    # 2. agent instruction file
    agent = read("agent-instructions.md")
    check("agent-instructions.md has when-to-use and when-not-to-use",
          "## When to use" in agent and "## When not to use" in agent)
    check("agent-instructions.md states the no-recovery-phrase rule",
          "recovery phrase" in agent.lower())

    for name in ("AGENTS.md", "llms-full.txt", "connect.md", "agents.html",
                 ".well-known/mcp"):
        check("%s exists" % name, os.path.exists(os.path.join(ROOT, name)))

    # site.css resets ul,ol{list-style:none} globally, so prose lists must draw
    # their own markers. They did not, and the pages shipped with silently
    # invisible bullets — a ::marker colour cannot colour a marker that is off.
    page_css = read("assets/css/page.css")
    site_css = read("assets/css/site.css")
    check("site.css still strips list markers globally (the reason page.css must draw its own)",
          "list-style:none" in site_css.replace(" ", ""))
    check("page.css draws its own list markers",
          ".prose__list li::before" in page_css and "border:var(--rule) solid var(--accent)" in page_css)
    check("numbered prose lists keep their numbers",
          "counter-increment:prose-step" in page_css.replace(" ", "") and
          "counter(prose-step" in page_css)

    # No two published files may differ only by case. macOS and Windows treat
    # those as one file, so a generator writing AGENTS.md silently destroyed
    # agents.md — the page and its own markdown alternate then disagreed, and
    # nothing noticed until the rendered HTML was compared against its source.
    published = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if any(part in dirpath for part in (".git", "node_modules", "export", "brand")):
            continue
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), ROOT)
            published.append(rel)
    lowered = {}
    collisions = []
    for rel in published:
        key = rel.lower()
        if key in lowered and lowered[key] != rel:
            collisions.append("%s vs %s" % (lowered[key], rel))
        lowered[key] = rel
    check("no two files differ only by case", not collisions, "; ".join(collisions))

    # The generated page must actually come from the source it claims.
    page = read("agents.html")
    check("agents.html was generated from connect.md",
          "Connecting an agent to KeyCompass" in page and
          "Agent instructions for KeyCompass" not in page)

    # 3. JSON-LD on the homepage
    index = read("index.html")
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', index, re.S)
    if not check("homepage has a JSON-LD block", bool(m)):
        return
    try:
        data = json.loads(m.group(1))
    except ValueError as e:
        check("homepage JSON-LD parses", False, str(e))
        return
    check("homepage JSON-LD parses", True)

    nodes = {n.get("@type"): n for n in data.get("@graph", [])}
    check("JSON-LD includes Organization", "Organization" in nodes)
    check("JSON-LD includes Person", "Person" in nodes)
    check("JSON-LD includes WebSite", "WebSite" in nodes)
    check("JSON-LD includes FAQPage", "FAQPage" in nodes)

    org = nodes.get("Organization", {})
    check("Organization has name, url, description",
          all(org.get(k) for k in ("name", "url", "description")))
    cp = org.get("contactPoint")
    cp = cp[0] if isinstance(cp, list) and cp else cp
    check("Organization has contactPoint with contactType and email",
          bool(cp) and bool(cp.get("contactType")) and bool(cp.get("email")),
          (cp or {}).get("email", ""))
    addr = org.get("address") or {}
    check("Organization has a PostalAddress",
          addr.get("@type") == "PostalAddress" and bool(addr.get("addressCountry")),
          "addressCountry=%s" % addr.get("addressCountry"))
    check("Organization has sameAs links", bool(org.get("sameAs")))
    check("Organization has an offer catalogue", bool(org.get("hasOfferCatalog")))

    faq = nodes.get("FAQPage", {})
    check("FAQPage has questions", len(faq.get("mainEntity", [])) >= 5,
          "%d question(s)" % len(faq.get("mainEntity", [])))

    # 4. trust anchor pages, 500+ characters of real content
    # connect.md renders to agents.html — the source name cannot match the URL,
    # because agents.md collides with AGENTS.md on a case-insensitive filesystem.
    for slug, page in (("about", "about.html"), ("contact", "contact.html"),
                       ("privacy", "privacy.html"), ("connect", "agents.html")):
        md = read(slug + ".md")
        prose = re.sub(r'^[#>\-\|\s].*$', '', md, flags=re.M)
        check("%s.md has 500+ characters of content" % slug, len(md) >= 500,
              "%d chars (%d excluding headings/lists)" % (len(md), len(prose.strip())))
        check("%s was generated from it" % page,
              os.path.exists(os.path.join(ROOT, page)))

    # Fenced code blocks must survive the renderer. They did not, the first time:
    # the developer page's curl command collapsed into a paragraph.
    # Derive the expected count from the source rather than hard-coding it, so
    # editing the page cannot make this pass or fail for the wrong reason.
    src_fences = read("connect.md").count("\n```") // 2
    devs = read("agents.html")
    check("every fenced block in connect.md renders as <pre>",
          src_fences > 0 and devs.count("<pre") == src_fences,
          "%d in source, %d rendered" % (src_fences, devs.count("<pre")))
    check("no raw backticks leak into rendered HTML", "``" not in devs)

    # 5. 404 recovery content
    notfound = read("404.html")
    check("404.html links to the sitemap and llms.txt",
          "/sitemap.xml" in notfound and "/llms.txt" in notfound)
    check("404.md exists with recovery links",
          os.path.exists(os.path.join(ROOT, "404.md")) and "llms.txt" in read("404.md"))

    # 6. sitemap covers the new pages
    sm = read("sitemap.xml")
    for slug in ("about", "contact", "privacy", "agents"):
        check("sitemap.xml lists /%s" % slug, "/%s<" % slug in sm)

    # 7. the edge function is wired up
    ef = "netlify/edge-functions/content-negotiation.ts"
    if check("edge function exists", os.path.exists(os.path.join(ROOT, ef))):
        src = read(ef)
        check("edge function sets text/markdown", "text/markdown; charset=utf-8" in src)
        check("edge function sets Vary: Accept", '"Vary"' in src and "Accept" in src)
        check("edge function returns 406", "status: 406" in src)
        check("edge function fails open on error", "catch" in src and "context.next()" in src)

    toml = read("netlify.toml")
    for path in ("/faq", "/services", "/pricing", "/how-it-works", "/book"):
        check("netlify.toml redirects %s" % path, 'from = "%s"' % path in toml)
    check("edge function returns structured JSON errors",
          "prefersJson" in read("netlify/edge-functions/content-negotiation.ts"))
    check("netlify.toml sets Vary: Accept on negotiated paths",
          toml.count('Vary = "Accept, Accept-Encoding"') >= 4)
    check("netlify.toml serves .md as text/markdown",
          'Content-Type = "text/markdown; charset=utf-8"' in toml)


# --- checks against a live origin -------------------------------------------------

def live_checks(base):
    base = base.rstrip("/")

    # 1. agent-friendly 404
    status, headers, body = request(base + "/a-path-that-does-not-exist-9f2b")
    check("nonexistent path returns 404", status == 404, "got %s" % status)
    check("404 body points somewhere useful",
          "sitemap" in body.lower() or "llms.txt" in body.lower())

    status, headers, body = request(base + "/a-path-that-does-not-exist-9f2b",
                                    accept="text/markdown")
    check("404 with Accept: text/markdown returns markdown",
          status == 404 and "markdown" in headers.get("Content-Type", ""),
          "%s / %s" % (status, headers.get("Content-Type")))

    # 1b. paths an agent guesses must land somewhere, not 404
    # /docs, /api and /mcp-server were deliberately NOT reinstated: a
    # developer-documentation path is what opened the API surface in the scan,
    # and this is the configuration that measured 100/100.
    for path, target in (("/services", "/#services"), ("/pricing", "/#services"),
                         ("/faq", "/#faq"), ("/how-it-works", "/#method"),
                         ("/book", "/#book")):
        status, headers, _ = request(base + path)
        location = headers.get("Location", "")
        # urllib follows redirects, so a 200 here means it resolved; check the
        # redirect itself with a non-following request where the header survives.
        check("%s does not 404" % path, status != 404, "got %s" % status)

    # 1c. structured JSON errors for agents that ask for JSON
    status, headers, body = request(base + "/a-path-that-does-not-exist-9f2b",
                                    accept="application/json")
    check("404 with Accept: application/json returns JSON",
          status == 404 and "application/json" in headers.get("Content-Type", ""),
          "%s / %s" % (status, headers.get("Content-Type")))
    try:
        err = json.loads(body).get("error", {})
    except ValueError:
        err = {}
    check("JSON 404 carries a code, message and hint",
          all(err.get(k) for k in ("code", "message", "hint")), err.get("code", ""))
    check("JSON 404 links onward to the sitemap and MCP endpoint",
          "sitemap" in json.dumps(err.get("links", {})) and
          "mcp" in json.dumps(err.get("links", {})).lower())
    check("JSON 404 sets Vary: Accept",
          "accept" in [t.strip().lower() for t in headers.get("Vary", "").split(",")],
          headers.get("Vary"))

    # A client offering only JSON accepts neither variant this URL has, so 406 is
    # correct — and the 406 itself should be JSON. Note the Accept must exclude
    # text/html entirely: "application/json, text/html;q=0.1" still accepts HTML,
    # so serving HTML there is right and a 406 would be the bug.
    status, headers, body = request(base + "/about", accept="application/json")
    check("406 answers in JSON when only JSON is acceptable",
          status == 406 and "application/json" in headers.get("Content-Type", ""),
          "%s / %s" % (status, headers.get("Content-Type")))
    status, headers, _ = request(base + "/about", accept="application/json, text/html;q=0.1")
    check("HTML is still served when the client accepts it at any q",
          status == 200 and headers.get("Content-Type", "").startswith("text/html"),
          "%s / %s" % (status, headers.get("Content-Type")))

    # A browser must still get the HTML 404 page, not an error object.
    status, headers, _ = request(base + "/a-path-that-does-not-exist-9f2b",
                                 accept="text/html,application/xhtml+xml,*/*;q=0.8")
    check("browser Accept still gets the HTML 404 page",
          status == 404 and headers.get("Content-Type", "").startswith("text/html"),
          headers.get("Content-Type"))

    # 2. acceptmarkdown.com conformance on each negotiated page
    for path in ("/", "/about", "/contact", "/privacy", "/agents"):
        status, headers, body = request(base + path, accept="text/markdown")
        ctype = headers.get("Content-Type", "")
        check("%s serves markdown for Accept: text/markdown" % path,
              status == 200 and ctype.startswith("text/markdown"),
              "%s / %s" % (status, ctype))
        vary = headers.get("Vary", "")
        # "Accept" must be its own token: a bare Vary: Accept-Encoding contains
        # the substring "Accept" but does not vary the response on Accept at all.
        tokens = [t.strip().lower() for t in vary.split(",")]
        check("%s sets Vary: Accept" % path, "accept" in tokens, vary or "(no Vary header)")
        check("%s markdown body looks like markdown" % path, body.lstrip().startswith("#"),
              body.lstrip()[:40])

    # 3. HTML is still the default
    status, headers, _ = request(base + "/", accept="text/html,application/xhtml+xml,*/*;q=0.8")
    check("browser Accept still returns HTML",
          status == 200 and headers.get("Content-Type", "").startswith("text/html"),
          headers.get("Content-Type"))

    status, headers, _ = request(base + "/", accept="*/*")
    check("Accept: */* returns HTML, not markdown",
          headers.get("Content-Type", "").startswith("text/html"),
          headers.get("Content-Type"))

    # 4. q-values
    status, headers, _ = request(base + "/", accept="text/markdown;q=0.5, text/html;q=1.0")
    check("q-values honoured: HTML preferred",
          headers.get("Content-Type", "").startswith("text/html"),
          headers.get("Content-Type"))

    status, headers, _ = request(base + "/", accept="text/markdown;q=1.0, text/html;q=0.5")
    check("q-values honoured: markdown preferred",
          headers.get("Content-Type", "").startswith("text/markdown"),
          headers.get("Content-Type"))

    # 5. 406
    status, _, _ = request(base + "/", accept="application/pdf")
    check("unsupported Accept returns 406", status == 406, "got %s" % status)

    # 6. machine-readable files
    for path, expect in (("/llms.txt", "text/plain"),
                         ("/llms-full.txt", "text/plain"),
                         ("/agent-instructions.md", "text/markdown"),
                         ("/AGENTS.md", "text/markdown"),
                         ("/connect.md", "text/markdown"),
                         ("/index.md", "text/markdown"),
                         ("/.well-known/mcp", "application/json"),
                         ("/sitemap.xml", "xml"),
                         ("/robots.txt", "text/plain")):
        status, headers, _ = request(base + path)
        check("%s is served" % path, status == 200, "got %s" % status)
        check("%s has %s content type" % (path, expect),
              expect in headers.get("Content-Type", ""), headers.get("Content-Type"))

    # 7. trust anchor pages
    for path in ("/about", "/contact", "/privacy", "/agents"):
        status, _, body = request(base + path)
        text = re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style).*?</\1>', '', body, flags=re.S))
        text = re.sub(r'\s+', ' ', text).strip()
        check("%s returns 200" % path, status == 200, "got %s" % status)
        check("%s has 500+ characters of text" % path, len(text) >= 500,
              "%d chars" % len(text))

    # 8. JSON-LD survived the deploy
    status, _, body = request(base + "/")
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', body, re.S)
    if check("homepage serves JSON-LD", bool(m)):
        try:
            types = [n.get("@type") for n in json.loads(m.group(1)).get("@graph", [])]
            check("JSON-LD includes Organization and FAQPage",
                  "Organization" in types and "FAQPage" in types, ", ".join(types))
        except ValueError as e:
            check("live JSON-LD parses", False, str(e))

    # 9. the security headers added earlier are still intact
    status, headers, _ = request(base + "/")
    for h in ("Content-Security-Policy", "Strict-Transport-Security",
              "X-Content-Type-Options", "X-Frame-Options"):
        check("%s still present" % h, h in headers)


def main():
    args = sys.argv[1:]
    if "--local" in args:
        print("Checking repo files\n")
        local_checks()
    else:
        base = DEFAULT_URL
        if "--url" in args:
            base = args[args.index("--url") + 1]
        print("Checking live origin: %s\n" % base)
        try:
            live_checks(base)
        except (urllib.error.URLError, OSError) as e:
            print("Could not reach %s: %s" % (base, e), file=sys.stderr)
            return 2

    width = max(len(n) for _, n, _ in results)
    failed = 0
    for state, name, detail in results:
        if state == FAIL:
            failed += 1
        mark = {PASS: "  ok  ", FAIL: " FAIL ", SKIP: " skip "}[state]
        print("%s %-*s %s" % (mark, width, name, detail))

    print("\n%d passed, %d failed, %d total"
          % (len(results) - failed, failed, len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
