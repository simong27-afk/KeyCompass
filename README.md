# KeyCompass

Marketing site and brand assets for KeyCompass — self-custody onboarding sessions and
security reviews.

    index.html            the site (single page, no build step)
    assets/css/site.css
    assets/js/site.js
    site.webmanifest
    brand/                logo marks, lockups, favicons, social, tokens
    docs/design-notes.md  design direction, tokens, and the rules the site follows

## Preview

    python3 .claude/serve.py

Then open http://localhost:4321.

## Deploy

Static — push the repo root to Netlify, Cloudflare Pages, GitHub Pages, or any static host.
Nothing to compile.

## Before publishing

- Replace the `mailto:` links in `index.html` (search for `TODO`) with the real booking link.
- Have a solicitor review the boundary section, the financial-advice answer, and the footer
  risk warning against the FCA financial promotion rules.
