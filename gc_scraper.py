#!/usr/bin/env python3
"""
gc_scraper.py — Pull GameChanger Team Manager stats via the unofficial API.

GameChanger has no public API. This hits their internal REST endpoints
(api.team-manager.gc.com) using a bearer token captured from a logged-in
browser session at web.gc.com. See README.md for token-capture steps.

Modes
-----
  discover                   List your teams, then players on a chosen team.
  team   <team_id>           Dump team metadata + roster + season stats.
  player <person_id>         Pull season + career stats for one person.
  player --jersey N --team-name "..."
                             Find a player by jersey + team name match.
  raw    <path>              Hit any API path and print JSON
                             (e.g. raw /me, raw /teams/<id>/games).

Output goes to ./out/<UTC-timestamp>/ as raw JSON files plus a
flattened *_summary.json suitable for plugging into the johnny74 site.

Endpoint notes
--------------
The endpoint paths below are based on observed traffic from web.gc.com.
GC changes them occasionally — if any return 404/410, capture the actual
path from your browser's DevTools (Network tab, filter `team-manager.gc.com`)
and update the constants in the ENDPOINTS section.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://api.team-manager.gc.com"

# ─── Endpoint candidates ──────────────────────────────────────────────────
# Each entry is a list of probable paths tried in order. First 2xx wins.
ENDPOINTS = {
    "me":            ["/me", "/users/me"],
    "my_teams":      ["/me/teams", "/teams?mine=true", "/teams"],
    "team":          ["/teams/{team_id}"],
    "team_roster":   ["/teams/{team_id}/players",
                      "/teams/{team_id}/roster",
                      "/teams/{team_id}/persons"],
    "team_seasons":  ["/teams/{team_id}/seasons",
                      "/teams/{team_id}/season-stats"],
    "team_games":    ["/teams/{team_id}/games",
                      "/teams/{team_id}/schedule"],
    "person":        ["/persons/{person_id}", "/players/{person_id}"],
    "person_season": ["/persons/{person_id}/season-stats",
                      "/players/{person_id}/season-stats",
                      "/persons/{person_id}/stats?type=season"],
    "person_career": ["/persons/{person_id}/career-stats",
                      "/players/{person_id}/career-stats",
                      "/persons/{person_id}/stats?type=career"],
    "game":          ["/games/{game_id}"],
    "game_box":      ["/games/{game_id}/box-score",
                      "/games/{game_id}/stats"],
}

# ─── Output dir ───────────────────────────────────────────────────────────
RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT_DIR = Path("out") / RUN_TS


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)


def save_json(name: str, data: Any) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe = name.replace("/", "_").strip("_")
    p = OUT_DIR / f"{safe}.json"
    p.write_text(json.dumps(data, indent=2, default=str))
    return p


# ─── HTTP client ──────────────────────────────────────────────────────────
class GCClient:
    def __init__(self, token: str):
        if not token:
            raise SystemExit("Missing GC_TOKEN. See README.md for how to capture it.")
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/124.0 Safari/537.36",
            "Origin": "https://web.gc.com",
            "Referer": "https://web.gc.com/",
        })

    def get(self, path: str, **params) -> tuple[int, Any]:
        url = path if path.startswith("http") else API_BASE + path
        r = self.s.get(url, params=params or None, timeout=20)
        ct = r.headers.get("content-type", "")
        body: Any
        try:
            body = r.json() if "json" in ct else r.text
        except Exception:
            body = r.text
        return r.status_code, body

    def try_endpoints(self, key: str, **fmt) -> tuple[str | None, Any]:
        """Try each candidate path for an endpoint key, return (path, body) on first 2xx."""
        for tmpl in ENDPOINTS[key]:
            path = tmpl.format(**fmt)
            status, body = self.get(path)
            log(f"  GET {path} → {status}")
            if 200 <= status < 300:
                return path, body
            if status == 401:
                raise SystemExit("401 Unauthorized — token expired. Recapture from browser.")
        return None, None


# ─── helpers to walk JSON safely ──────────────────────────────────────────
def walk(obj: Any, *keys: str, default=None):
    """Safe nested get: walk(obj, 'a','b',0,'c')."""
    for k in keys:
        if obj is None:
            return default
        if isinstance(obj, list):
            try:
                obj = obj[int(k)]
            except (IndexError, ValueError):
                return default
        elif isinstance(obj, dict):
            obj = obj.get(k, default if k == keys[-1] else None)
        else:
            return default
    return obj if obj is not None else default


def find_collection(body: Any) -> list:
    """API responses sometimes wrap arrays in {data: [...]} or {teams: [...]}."""
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        for k in ("data", "items", "results", "teams", "players", "persons", "roster"):
            v = body.get(k)
            if isinstance(v, list):
                return v
    return []


# ─── modes ────────────────────────────────────────────────────────────────
def cmd_discover(c: GCClient, args) -> None:
    log("Fetching /me ...")
    _, me = c.try_endpoints("me")
    if me:
        save_json("me", me)
        log(f"  user: {walk(me,'first_name')} {walk(me,'last_name')} ({walk(me,'email')})")

    log("Fetching teams ...")
    path, teams_body = c.try_endpoints("my_teams")
    if not teams_body:
        log("  ✗ Could not fetch teams. Run with `raw /me` to inspect, then "
            "update ENDPOINTS['my_teams'] with the path your browser uses.")
        return
    save_json("my_teams", teams_body)

    teams = find_collection(teams_body)
    if not teams:
        log("  Response had no recognizable team list. Saved raw to "
            f"{OUT_DIR}/my_teams.json — inspect and adjust find_collection().")
        return

    print("\n── Your teams ──")
    for i, t in enumerate(teams):
        tid = t.get("id") or t.get("team_id") or t.get("_id") or "?"
        name = t.get("name") or t.get("team_name") or "?"
        sport = t.get("sport") or t.get("sport_id") or ""
        season = t.get("season_name") or walk(t, "season", "name") or ""
        print(f"  [{i}] {name}  ({sport} {season})  id={tid}")

    if args.team_index is None:
        print("\nRe-run with --team-index N to drill into a roster.")
        return

    team = teams[args.team_index]
    tid = team.get("id") or team.get("team_id")
    log(f"\nFetching roster for team {tid} ...")
    _, roster_body = c.try_endpoints("team_roster", team_id=tid)
    if roster_body:
        save_json(f"team_{tid}_roster", roster_body)
        roster = find_collection(roster_body)
        print(f"\n── Roster ({len(roster)} players) ──")
        for p in roster:
            pid = p.get("id") or p.get("person_id") or "?"
            jersey = p.get("number") or p.get("jersey_number") or p.get("uniform_number") or "?"
            first = p.get("first_name") or walk(p, "person", "first_name") or "?"
            last = p.get("last_name") or walk(p, "person", "last_name") or ""
            print(f"  #{jersey:<3} {first} {last}  id={pid}")


def cmd_team(c: GCClient, args) -> None:
    tid = args.team_id
    log(f"Team {tid} — fetching all the things ...")
    for key in ("team", "team_roster", "team_seasons", "team_games"):
        _, body = c.try_endpoints(key, team_id=tid)
        if body:
            save_json(f"team_{tid}_{key}", body)
    log(f"Done. Files in {OUT_DIR}/")


def cmd_player(c: GCClient, args) -> None:
    pid = args.person_id

    # Resolve by jersey + team name if no person_id
    if not pid:
        if not (args.jersey and args.team_name):
            raise SystemExit("Provide <person_id> OR --jersey and --team-name.")
        log(f"Resolving #{args.jersey} on team matching '{args.team_name}' ...")
        _, teams_body = c.try_endpoints("my_teams")
        teams = find_collection(teams_body)
        match_team = next((t for t in teams
                           if args.team_name.lower() in (t.get("name") or "").lower()), None)
        if not match_team:
            raise SystemExit(f"No team match for '{args.team_name}'.")
        tid = match_team.get("id") or match_team.get("team_id")
        _, roster_body = c.try_endpoints("team_roster", team_id=tid)
        roster = find_collection(roster_body)
        match = next((p for p in roster
                      if str(p.get("number") or p.get("jersey_number") or "")
                         == str(args.jersey)), None)
        if not match:
            raise SystemExit(f"No #{args.jersey} on {match_team.get('name')}.")
        pid = match.get("id") or match.get("person_id")
        log(f"  → resolved to person_id={pid}")

    log(f"Person {pid} — pulling profile, season, career ...")
    _, profile = c.try_endpoints("person", person_id=pid)
    _, season  = c.try_endpoints("person_season", person_id=pid)
    _, career  = c.try_endpoints("person_career", person_id=pid)

    if profile: save_json(f"person_{pid}_profile", profile)
    if season:  save_json(f"person_{pid}_season",  season)
    if career:  save_json(f"person_{pid}_career",  career)

    # Build a flat summary suitable for the johnny74 site
    summary = {
        "person_id": pid,
        "fetched_at": RUN_TS,
        "name": {
            "first": walk(profile, "first_name"),
            "last":  walk(profile, "last_name"),
            "jersey": walk(profile, "number") or walk(profile, "jersey_number"),
        },
        "career": career,        # keep raw for now — shape varies by sport
        "seasons": season,       # ditto
        "_endpoints_note": "raw payloads; reshape per kass21 site after first run",
    }
    p = save_json(f"person_{pid}_summary", summary)
    log(f"\nSummary written: {p}")
    print("\n── Quick view ──")
    print(json.dumps({
        "name": summary["name"],
        "career_keys": list(career.keys()) if isinstance(career, dict) else type(career).__name__,
        "season_keys": list(season.keys()) if isinstance(season, dict) else type(season).__name__,
    }, indent=2))


def cmd_raw(c: GCClient, args) -> None:
    path = args.path if args.path.startswith("/") else "/" + args.path
    log(f"GET {path}")
    status, body = c.get(path)
    log(f"  → {status}")
    out = save_json(f"raw_{path}", {"status": status, "body": body})
    log(f"  saved {out}")
    print(json.dumps(body, indent=2, default=str)[:4000])


# ─── main ─────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gc_scraper", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="List teams (and optionally a roster)")
    d.add_argument("--team-index", type=int, help="Index from team list to drill into")

    t = sub.add_parser("team", help="Dump everything for a team_id")
    t.add_argument("team_id")

    p = sub.add_parser("player", help="Pull stats for a person")
    p.add_argument("person_id", nargs="?")
    p.add_argument("--jersey")
    p.add_argument("--team-name")

    r = sub.add_parser("raw", help="Hit any API path")
    r.add_argument("path")

    return ap


def main():
    args = build_parser().parse_args()
    token = os.environ.get("GC_TOKEN", "").strip()
    c = GCClient(token)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log(f"Output dir: {OUT_DIR}/")

    {
        "discover": cmd_discover,
        "team":     cmd_team,
        "player":   cmd_player,
        "raw":      cmd_raw,
    }[args.cmd](c, args)


if __name__ == "__main__":
    main()
