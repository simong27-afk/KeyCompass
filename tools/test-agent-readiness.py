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

    for name in ("AGENTS.md", "llms-full.txt", "developers.md", "developers.html",
                 ".well-known/mcp"):
        check("%s exists" % name, os.path.exists(os.path.join(ROOT, name)))

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
    for slug in ("about", "contact", "privacy", "developers"):
        md = read(slug + ".md")
        prose = re.sub(r'^[#>\-\|\s].*$', '', md, flags=re.M)
        check("%s.md has 500+ characters of content" % slug, len(md) >= 500,
              "%d chars (%d excluding headings/lists)" % (len(md), len(prose.strip())))
        check("%s.html was generated from it" % slug,
              os.path.exists(os.path.join(ROOT, slug + ".html")))

    # 5. 404 recovery content
    notfound = read("404.html")
    check("404.html links to the sitemap and llms.txt",
          "/sitemap.xml" in notfound and "/llms.txt" in notfound)
    check("404.md exists with recovery links",
          os.path.exists(os.path.join(ROOT, "404.md")) and "llms.txt" in read("404.md"))

    # 6. sitemap covers the new pages
    sm = read("sitemap.xml")
    for slug in ("about", "contact", "privacy", "developers"):
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

    # 2. acceptmarkdown.com conformance on each negotiated page
    for path in ("/", "/about", "/contact", "/privacy", "/developers"):
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
                         ("/developers.md", "text/markdown"),
                         ("/index.md", "text/markdown"),
                         ("/.well-known/mcp", "application/json"),
                         ("/sitemap.xml", "xml"),
                         ("/robots.txt", "text/plain")):
        status, headers, _ = request(base + path)
        check("%s is served" % path, status == 200, "got %s" % status)
        check("%s has %s content type" % (path, expect),
              expect in headers.get("Content-Type", ""), headers.get("Content-Type"))

    # 7. trust anchor pages
    for path in ("/about", "/contact", "/privacy", "/developers"):
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
