# KeyCompass brand assets

Mark: **Vault Dial** — two concentric square rings with four key channels cut through them.
Black only. Zero radius. No gradients, no outline-only version, no rotation.

## Palette
| Role | Hex |
| --- | --- |
| Ink (mark, type) | `#201e1d` |
| Ground | `#f3f2f2` |
| White (reversed) | `#ffffff` |
| Accent (UI + poster only) | `#ec3013` |

Accent never appears inside the mark. For paragraph-size red text use `#b3210e` or darker for contrast.

## Type
Archivo. Wordmark = Archivo ExtraBold (800), tracking `-0.035em`, one word, no space at the join.

## Lockup ratio (the thing to preserve)
- Mark height = **cap height** of the wordmark → `0.78em` of the type size.
- Gap between mark and word = **0.22em**.
- Clear space around the mark = one outer-ring width (10% of the mark).
- Minimum mark size: **20px**. Below that use the simplified cut (`mark-favicon-simplified-*.svg`) — outer ring plus channels, inner ring dropped.

## Folders
- `svg/` — vector masters. `mark-ink`, `mark-white`, simplified favicon cuts, and pre-composed square icon tiles.
- `app-icons/` — 1024 / 512 / 192 / 180 PNG tiles (ink, light, accent variants at 1024).
- `favicon/` — 16 / 32 / 48 PNG, transparent, simplified cut.
- `lockups/` — rasterised horizontal + stacked lockups with real Archivo outlines (email signatures, decks, anywhere you can't load the font).
- `social/` — `og-image-1200x630`, `story-1080x1920` (ink + accent), `banner-1500x500`, `avatar-1000` (ink + light).
- `mark-png/` — 2048px transparent mark, ink and white.
- `code/` — `Logo.jsx` (React component, ratio baked in), `logo-inline.html`, `head-tags.html`, `site.webmanifest`, `tokens.css`.

## Building the site
Start from `code/tokens.css` + `code/head-tags.html`, then use `<KeyCompassLockup fontSize={21} />` in the header. Both numbers that control the lockup live in one place in `Logo.jsx` — change `0.78em` / `0.22em` there and every instance follows.

Story graphics are templates: the ink and accent 1080x1920 files show the layout (mark top-left, rule, display headline, 2px footer rule with URL). Reset the headline per post; keep the footer rule and the URL in accent.
