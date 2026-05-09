# Johnny74 — Athlete Profile Site + GC Stats Pipeline

Same architecture as `kass21`. Pink palette. Stats fed by a GameChanger
scraper because GC has no public API.

## Layout
```
johnny74/
├── index.html            # main page (pink, mirrors kass21 sections)
├── recruiting_v2.html    # TODO — clone from kass21 and restyle
├── story.html            # TODO — clone from kass21 and restyle
├── player-card.html      # TODO — clone from kass21 and restyle
└── scraper/
    ├── gc_scraper.py     # GameChanger API client
    ├── requirements.txt
    └── (out/<ts>/        # raw JSON + summary, written at runtime)
```

## Workflow

### 1. Capture a GC bearer token
GameChanger Team Manager has no public API. The internal one
(`api.team-manager.gc.com`) accepts the same bearer token your browser uses.

1. Log in to **https://web.gc.com** in Chrome.
2. Open DevTools → **Network** tab. Filter on `team-manager.gc.com`.
3. Click around the app (open a team, view stats) so requests fire.
4. Click any request → **Headers** → copy the value of
   `Authorization: Bearer <very long string>`.
5. Export it:
   ```bash
   export GC_TOKEN="eyJhbGc...the_long_thing"
   ```
   Tokens expire — recapture when you see `401 Unauthorized`.

### 2. Run the scraper

```bash
cd scraper
pip install -r requirements.txt

# Step A — list your teams
python gc_scraper.py discover

# Step B — pick a team index from the list, drill into the roster
python gc_scraper.py discover --team-index 0

# Step C — pull stats for a player (two ways)
python gc_scraper.py player <person_id>
python gc_scraper.py player --jersey 74 --team-name "Hotshots"

# Anything else — raw passthrough
python gc_scraper.py raw /me
python gc_scraper.py raw /teams/<id>/season-stats
```

Each run writes to `scraper/out/<UTC-timestamp>/`:
- `me.json`, `my_teams.json`, `team_<id>_*.json`
- `person_<id>_profile.json`, `person_<id>_season.json`,
  `person_<id>_career.json`
- `person_<id>_summary.json` ← the flat one to pull from for the site

### 3. Update the site
Open `index.html` and replace the placeholders. Search-and-replace on:
- `[LAST_NAME]` → her last name
- `[TEAM_NAME]`, `[ORG]`, `[CITY]`, `[STATE]` → team line
- `[TODO: ...]` → narrative copy
- `.XXX`, `X.XXX`, `XX` → actual stat values from `*_summary.json`
- `[Add photo N]` → real photo URLs (drop into the repo or hotlink)
- `#instagram` reel links and `@johnny_handle`

Then `git push` to the `johnny74` repo (mirror your `kass21` GH Pages setup).

## When endpoints break
The scraper has **candidate paths** for each resource — first 2xx wins.
If GC moves things and everything 404s on a key:
1. Open browser DevTools → Network on web.gc.com.
2. Find the request that hits the resource you want.
3. Copy the path (everything after `api.team-manager.gc.com`).
4. Add it to the matching list in `ENDPOINTS` at the top of `gc_scraper.py`.

## Legal note
GameChanger's ToS prohibits scraping. This is for **personal use** —
pulling Johnny's own stats from a team you're rostered on, for a personal
athlete profile site. Don't redistribute the data, don't run high-volume
scrapes against their API, and don't share the bearer token.
