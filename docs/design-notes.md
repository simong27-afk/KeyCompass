# KeyCompass site — design notes

Static one-pager. No build step: `index.html`, `assets/css/site.css`, `assets/js/site.js`,
plus the existing `brand/` folder. Drop the repo on any static host.

## Direction

Set by the business plan (§11): dark ground, orange-red accent, blueprint/technical-drawing
aesthetic, oversized sans headlines — the `enerblock.net` reference. Enerblock's own system,
for reference: full-bleed alternating section grounds, near-zero radius, uppercase micro-labels
as eyebrows, drawing annotations (sheet numbers, scale, coordinates), grotesk display at ~0.9
line-height and tight negative tracking.

## Tokens

| Role | Value | Note |
| --- | --- | --- |
| `--pitch` | `#141312` | deepest ground: hero, founder, footer |
| `--ink` | `#201e1d` | brand ink |
| `--ground` | `#f3f2f2` | brand light ground |
| `--accent` | `#ec3013` | brand accent — rules, graphics, one flood |
| `--accent-deep` | `#b3210e` | accent at paragraph size on light (brand rule) |
| `--dim` | `#9a9391` | muted on dark — brand `--kc-muted` fails 4.5:1 on pitch |
| `--dim-2` | `#6b6664` | brand muted, on light only |

Zero radius and 2px rules throughout, per `brand/README.md`.

Type: **Archivo** for the wordmark (800 / -0.035em) and display (600–700 / -0.03em / 0.88–0.94
leading). **Martian Mono** as the utility face — annotations, sheet numbers, prices, buttons,
eyebrows, never above 13px. An engineering drawing uses a separate notation letter; this is that.

## The signature

The hero drawing, "Sheet 01 — Custody surfaces": a plan view with an outer `ACCESS` perimeter
and an inner `BACKUP` perimeter around a `KEYS` core, cut by four channels — Phishing, Device,
Backup loss, Succession. Geometry is derived from the Vault Dial mark (concentric squares, four
orthogonal channels, 2px strokes); it is *not* the mark and must not be swapped for it.
Hover, focus, or click a channel and the title block's readout swaps to what a review checks
there. The four channels are the actual scope of the security review, so the drawing is the
offer, not an ornament.

The mark itself appears at scale exactly once, as a stamp on the closing accent panel — the page
opens with the drawing and closes with the thing it was drawn from.

## Rules kept

- Accent floods **once**, at the close. Elsewhere it is rules, marks, hover, prices.
- Numbered markers appear **once** — "How a session runs" — because that is the only real sequence.
- Contrast: ink-on-accent is 3.9:1, so the closing panel's small label is a filled ink chip and
  its paragraph is set bold at ≥20px (large-text threshold). Never put 11px type on the accent.
- Motion: one orchestrated load sequence, then quiet scroll reveals. Initial hidden states are
  scoped to `.js` (set by an inline script in `<head>`) so the page is fully readable without JS.
  `prefers-reduced-motion` drops the fades but **keeps** the drawing's rotated label transforms.

## Copy constraints

Per business plan §4, the site must not name the former employer or invoke past association.
Credibility is framed as years, QA/CSAT figures, and certifications only. The FCA-facing lines
(the boundary section, the "is this financial advice" answer, and the footer risk warning) should
be reviewed by a solicitor before publishing.

## Local preview

    python3 .claude/serve.py     # serves the repo root on :4321

`.claude/snap.py` renders section screenshots with headless Chrome for design passes:

    python3 .claude/snap.py "[('hero',0,900),('services',1700,1300)]"

Args are `(name, scroll_offset_px, window_height, [window_width])`. Headless Chrome clamps the
window to ~500px wide, so check narrower layouts in a real browser.
