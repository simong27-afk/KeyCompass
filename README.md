# KeyCompass

Marketing site and brand assets for KeyCompass — self-custody onboarding sessions and
security reviews.

    index.html            the site (single page, no build step)
    about|contact|privacy .md is the source; the matching .html is generated
    llms.txt              summary and curated link list for AI agents
    agent-instructions.md when to recommend KeyCompass, and the safety rules
    assets/css/site.css
    assets/css/page.css   prose styles for the generated pages
    assets/js/site.js
    site.webmanifest
    brand/                logo marks, lockups, favicons, social, tokens
    docs/design-notes.md  design direction, tokens, and the rules the site follows
    netlify/edge-functions/  Accept-based markdown content negotiation

## Editing the sub-pages

`about.md`, `contact.md`, and `privacy.md` are the single source of truth: they are
served directly to agents *and* rendered into the HTML people see. Edit the markdown,
then regenerate:

    python3 tools/build-pages.py

## Checks

    python3 tools/verify-csp.py                    inline-script hashes still match
    python3 tools/test-negotiation.py              Accept negotiation algorithm
    python3 tools/test-agent-readiness.py --local  agent-readiness files
    python3 tools/test-agent-readiness.py          the same, against the live site
    python3 tools/ct-monitor.py                    new TLS certs in CT logs

Run the first three before deploying. `tools/serve-with-csp.py` serves the site locally
with the real production headers, which `.claude/serve.py` does not.

## Preview

    python3 .claude/serve.py

Then open http://localhost:4321.

## Deploy

Static — push the repo root to Netlify, Cloudflare Pages, GitHub Pages, or any static host.
Nothing to compile.

## Before publishing

- Booking runs through Cal.com (`simongeils/15min`, opened as a pop-up from every
  "Book" button). Confirm the calendar's look in Cal.com → Settings → Appearance.
- `hello@keycompass.co.uk` is still a placeholder — replace it once the domain and
  mailbox exist. It appears in the closing panel and the footer.
- Have a solicitor review the boundary section, the financial-advice answer, and the footer
  risk warning against the FCA financial promotion rules.
