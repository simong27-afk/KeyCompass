#!/usr/bin/env python3
"""Unit tests for the Accept negotiation algorithm.

IMPORTANT: `choose_variant` below is a line-for-line port of `chooseVariant` in
netlify/edge-functions/content-negotiation.ts. There is no Deno or Node runtime
in this repo, so the TypeScript cannot be executed here — this mirror is what
proves the algorithm is right. If you change one, change both, and re-run this.

The deployed behaviour is checked separately, against the live site, by
tools/test-agent-readiness.py.

    python3 tools/test-negotiation.py
"""

import sys

MARKDOWN = "text/markdown"
HTML = "text/html"


def parse_accept(header):
    out = []
    for part in header.split(","):
        bits = part.strip().split(";")
        media = bits.pop(0).strip().lower()
        q = 1.0
        for p in bits:
            kv = p.split("=")
            if len(kv) == 2 and kv[0].strip().lower() == "q":
                try:
                    q = float(kv[1])
                except ValueError:
                    pass
        if media:
            out.append((media, q))
    return out


def quality_for(entries, media_type):
    group = media_type.split("/")[0]
    best_specificity, best_q = -1, 0.0
    for media, q in entries:
        if media == media_type:
            specificity = 2
        elif media == group + "/*":
            specificity = 1
        elif media == "*/*":
            specificity = 0
        else:
            continue
        if specificity > best_specificity or (specificity == best_specificity and q > best_q):
            best_specificity, best_q = specificity, q
    return 0.0 if best_specificity < 0 else best_q


def choose_variant(accept_header):
    if not accept_header or not accept_header.strip():
        return "html"
    entries = parse_accept(accept_header)
    if not entries:
        return "html"

    q_markdown = quality_for(entries, MARKDOWN)
    q_html = quality_for(entries, HTML)
    named_markdown = any(m == MARKDOWN and q > 0 for m, q in entries)

    if named_markdown and q_markdown > 0 and q_markdown >= q_html:
        return "markdown"
    if q_html > 0:
        return "html"
    if q_markdown > 0:
        return "markdown"
    return "none"


BROWSER = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"

CASES = [
    # (Accept header, expected, why it matters)
    (None, "html", "no Accept header at all"),
    ("", "html", "empty Accept header"),
    ("   ", "html", "whitespace-only Accept header"),
    (BROWSER, "html", "a real browser must still get HTML"),
    ("*/*", "html", "curl's default must not silently become markdown"),
    ("text/*", "html", "a text wildcard alone is not a markdown request"),

    ("text/markdown", "markdown", "the basic acceptmarkdown.com request"),
    ("TEXT/MARKDOWN", "markdown", "media types are case-insensitive"),
    ("  text/markdown  ", "markdown", "surrounding whitespace is ignored"),
    ("text/markdown, text/html", "markdown", "markdown listed first, equal q"),
    ("text/html, text/markdown", "markdown", "order must not matter, only q"),

    ("text/markdown;q=1.0, text/html;q=0.5", "markdown", "q-values: markdown preferred"),
    ("text/markdown;q=0.5, text/html;q=1.0", "html", "q-values: HTML preferred"),
    ("text/markdown;q=0.9, text/html;q=0.9", "markdown", "tie goes to the explicit ask"),
    ("text/markdown;q=0.5, text/*;q=0.1", "markdown", "exact type beats the wildcard"),
    ("*/*, text/markdown;q=0", "html", "q=0 is a refusal, even under a wildcard"),
    ("text/markdown;q=0.001, text/html;q=0.002", "html", "tiny q-values still compare"),

    ("application/pdf", "none", "nothing acceptable -> 406"),
    ("application/pdf, image/png", "none", "still nothing acceptable -> 406"),
    ("text/markdown;q=0", "none", "markdown refused and nothing else offered -> 406"),
    ("text/html;q=0", "none", "HTML refused and nothing else offered -> 406"),
    ("application/pdf, */*;q=0.1", "html", "a wildcard fallback rescues it from 406"),
    ("text/html;q=0, text/markdown", "markdown", "HTML refused, markdown named"),

    ("text/markdown;q=abc", "markdown", "an unparseable q falls back to 1"),
    ("text/markdown;charset=utf-8", "markdown", "non-q parameters are ignored"),
    (",,,", "html", "a degenerate header does not crash"),
]


def main():
    failures = []
    for header, expected, why in CASES:
        actual = choose_variant(header)
        if actual != expected:
            failures.append((header, expected, actual, why))

    for header, expected, actual, why in failures:
        print("FAIL  Accept: %r" % header)
        print("      expected %-9s got %-9s (%s)" % (expected, actual, why))

    print("%d/%d negotiation cases passed" % (len(CASES) - len(failures), len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
