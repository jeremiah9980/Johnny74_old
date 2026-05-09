# Johnny Rogers #74 — Athlete Profile Site

Static four-page site for Johnny Rogers' 2026 season profile. Built to deploy on GitHub Pages, Netlify, Vercel, Cloudflare Pages, or any static host. Zero build step.

## File map

```
johnny74/
├── index.html        Main profile — hero, slash line, full stat table, photos
├── story.html        Long-form season narrative with pullquotes
├── recruiting.html   Recruiting kit — verified stats, profile, references, contact
├── 404.html          On-brand error page
├── styles.css        Shared stylesheet — edit once, updates everywhere
└── README.md         This file
```

## Stats wired in (from GameChanger, 2026 season)

### Hotshots 2K15 — Primary, 10U

| Category | Value |
|---|---|
| Slash line | .623 / .655 / .679 |
| OPS | 1.334 |
| Hits / AB | 33 / 53 |
| Singles / 2B / 3B / HR | 32 / 0 / 0 / 1 |
| Runs / RBI | 30 / 11 |
| BB / SO / K-L | 5 / 7 / 1 |
| HBP / SAC / SF | 0 / 1 / 0 |
| Stolen Bases | 40 (95.24%) |
| Caught Stealing / PIK | 2 / 0 |
| PA / AB | 59 / 53 |

### Bananas — Secondary

| Category | Value |
|---|---|
| Slash line | .345 / .537 / .345 |
| OPS | .881 |
| GP / PA / AB | 33 / 43 / 29 |
| Hits | 10 (10 1B, 0 2B, 0 3B, 0 HR) |
| Runs / RBI | 16 / 7 |
| BB / SO / K-L | 11 / 13 / 2 |
| HBP / SAC / SF | 1 / 1 / 0 |
| Stolen Bases | 17 (89.47%) |
| Caught Stealing / PIK | 2 / 0 |

### Combined 2026

- 82 AB · 43 H · 46 R · 18 RBI · 16 BB · 1 HR
- **57 stolen bases at 93%+ success across both teams**

## What's still placeholder (search and replace)

Every placeholder is wrapped in `[TBD — ...]` or `[Add ...]`. Open each `.html` in your editor and search for `[` to find them all.

**Profile fields** (in `index.html` and `recruiting.html`):
- Position
- Bats / Throws
- Team name
- Height / Weight (recruiting only)

**Story narrative** (in `story.html`):
- Two narrative paragraph blocks marked `[OPTIONAL — Add ...]`

**Photos** (in `index.html` and `recruiting.html`):
- 5 photo slots on the home page
- 5 highlight clips on the recruiting page

**References & contact** (in `recruiting.html`):
- Head coach name + contact
- Hitting coach name + contact
- Travel org
- Family contact info
- Update the `mailto:` link at the bottom of recruiting.html

## How to add photos

Drop image files into the same folder, then replace the placeholder `<div>` blocks with:

```html
<div class="p1"><img src="hero.jpg" alt="Johnny Rogers at bat" /></div>
```

The grid handles sizing automatically (object-fit: cover).

## Deploy to GitHub Pages

1. Drop these files at the root of a new repo (e.g. `johnny74`).
2. Go to repo Settings → Pages → Source = `main` branch, `/` (root).
3. Site goes live at `https://<your-username>.github.io/johnny74/`.

Or rename the repo to `<your-username>.github.io` to serve at the root domain.

## Color & font tokens

All colors and fonts live as CSS variables at the top of `styles.css`:

```css
--navy: #0a1628;     /* base background */
--lime: #d4ff3c;     /* primary accent */
--cream: #f4ecd8;    /* warm contrast */
--red:  #c63d1f;     /* flame red accent */
```

Change one variable, the whole site updates.

## Fonts loaded

Google Fonts:
- **Big Shoulders Stencil Display** — jersey #74 stencil treatment
- **Big Shoulders Display** — solid hero/section headings
- **JetBrains Mono** — stat tables, eyebrows, micro-text
- **Fraunces** — body / editorial copy

## Credits

Stats sourced from GameChanger team-manager logs. Site design + build by Claude.
