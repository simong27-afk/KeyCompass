#!/usr/bin/env python3
"""Check that the CSP script hashes in netlify.toml still match index.html.

The CSP names each inline <script> by its sha256. Edit one of those scripts and
the hash no longer matches, so the browser silently refuses to run it — the page
looks fine locally (no CSP on file://) and breaks in production. Run this after
touching any inline script, and before deploying.

    python3 tools/verify-csp.py

Exit status: 0 in sync, 1 out of sync (prints the values to paste).
"""

import base64
import hashlib
import io
import os
import re
import sys

TOML = "netlify.toml"
HTML_PAGES = ("index.html", "about.html", "contact.html", "privacy.html",
              "developers.html", "404.html")
INLINE = re.compile(r"<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>", re.DOTALL | re.I)
TYPE_ATTR = re.compile(r'\btype\s*=\s*["\']([^"\']+)["\']', re.I)

# A <script> whose type is not a JavaScript MIME type is data, not code: the
# browser never executes it, so script-src does not apply and it needs no hash.
# JSON-LD is the case that matters here.
NON_EXECUTABLE = ("application/ld+json", "application/json", "importmap", "speculationrules")


def executable(attrs):
    m = TYPE_ATTR.search(attrs)
    return m.group(1).strip().lower() not in NON_EXECUTABLE if m else True


def hashes_in(path):
    """Every executable inline script in one page, as CSP hash values."""
    html = io.open(path, encoding="utf-8").read()
    out, skipped = [], 0
    for m in INLINE.finditer(html):
        if not executable(m.group(1)):
            skipped += 1
            continue
        digest = hashlib.sha256(m.group(2).encode("utf-8")).digest()
        out.append("sha256-" + base64.b64encode(digest).decode())
    return out, skipped


def main():
    toml = io.open(TOML, encoding="utf-8").read()

    actual, skipped, per_page = [], 0, {}
    for page in HTML_PAGES:
        if not os.path.exists(page):
            continue
        found, skip = hashes_in(page)
        per_page[page] = found
        skipped += skip
        for h in found:
            if h not in actual:
                actual.append(h)

    declared = re.findall(r"'(sha256-[A-Za-z0-9+/=]+)'", toml)

    missing = [h for h in actual if h not in declared]
    stale = [h for h in declared if h not in actual]

    if not missing and not stale:
        note = " (%d non-executable block(s) skipped)" % skipped if skipped else ""
        print("CSP in sync: %d distinct inline script(s) across %d page(s), all hashes "
              "present.%s" % (len(actual), len(per_page), note))
        for page, found in per_page.items():
            print("    %-14s %d script(s)" % (page, len(found)))
        return 0

    print("CSP OUT OF SYNC — the live site would break.\n")
    if missing:
        print("  Inline scripts with no matching hash in %s:" % TOML)
        for page, found in per_page.items():
            for h in found:
                if h in missing:
                    print("    %s  (%s)" % (h, page))
    if stale:
        print("  Hashes in %s that match no inline script (safe to remove):" % TOML)
        for h in stale:
            print("    '%s'" % h)
    print("\n  Correct script-src for the current pages:")
    print("    script-src 'self' %s" % " ".join("'%s'" % h for h in actual))
    return 1


if __name__ == "__main__":
    sys.exit(main())
