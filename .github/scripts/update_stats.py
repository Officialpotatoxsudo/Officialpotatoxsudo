"""Regenerate self-hosted stats.svg from the GitHub REST API.

Usage (CI):
    python .github/scripts/update_stats.py

Env:
    GITHUB_TOKEN      - provided by Actions (falls back to unauthenticated, low rate limit)
    GITHUB_REPOSITORY - e.g. Officialpotatoxsudo/Officialpotatoxsudo (owner = stats target)

What it updates in stats.svg:
    Stars (sum stargazers_count, excl. forks optionally), Repositories
    (public_repos), Followers, Following, Forks (sum forks_count),
    Open Issues (sum open_issues_count), and the "updated ..." footer.

langs.svg is intentionally curated (most-used showcase) and left untouched —
GitHub linguist on this account is fork-skewed / mostly null, so an
auto-overwrite would wipe a useful personal-brand signal.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys
import urllib.request
import json

API = "https://api.github.com"
TARGET = "stats.svg"


def _headers() -> dict:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-stats-updater",
    }
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def _get_json(url: str):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_owner() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "Officialpotatoxsudo/Officialpotatoxsudo")
    return repo.split("/")[0]


def fetch_stats(owner: str) -> dict:
    user = _get_json(f"{API}/users/{owner}")
    repos = _get_json(f"{API}/users/{owner}/repos?per_page=100&type=owner")
    # Exclude forks from star/fork totals so a big fork (e.g. openclaw)
    # doesn't misrepresent original work. Change to `repos` if you
    # prefer totals including forks.
    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) or 0 for r in owned)
    forks = sum(r.get("forks_count", 0) or 0 for r in owned)
    issues = sum(r.get("open_issues_count", 0) or 0 for r in owned)
    return {
        "stars": stars,
        "repos": user.get("public_repos", len(repos)),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "forks": forks,
        "issues": issues,
        "owner": owner,
        "date": dt.date.today().isoformat(),
    }


def patch_svg(path: str, s: dict) -> bool:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    orig = src

    def set_val(ident: str, value) -> None:
        nonlocal src
        # <text ... id="stars">4</text> -> replace inner number only
        src = re.sub(
            rf'(id="{ident}"[^>]*>)\d+',
            rf"\g<1>{value}",
            src,
            count=1,
        )

    set_val("stars", s["stars"])
    set_val("repos", s["repos"])
    set_val("followers", s["followers"])
    set_val("following", s["following"])
    set_val("forks", s["forks"])
    set_val("issues", s["issues"])
    src = re.sub(
        r'(id="updated"[^>]*>)[^<]*',
        rf"\g<1>updated {s['date']} · {s['owner']}",
        src,
        count=1,
    )
    # data comment for humans debugging the card
    src = re.sub(
        r"<!-- data: .*? -->",
        f"<!-- data: stars={s['stars']} repos={s['repos']} followers={s['followers']} "
        f"following={s['following']} forks={s['forks']} open_issues={s['issues']} · updated {s['date']} -->",
        src,
        count=1,
    )
    if src != orig:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        return True
    return False


def main() -> int:
    owner = fetch_owner()
    try:
        stats = fetch_stats(owner)
    except Exception as e:  # noqa: BLE001 — CI should fail loudly but readably
        print(f"stats update failed: {e}", file=sys.stderr)
        return 1
    changed = patch_svg(TARGET, stats)
    print(f"{TARGET} {'updated' if changed else 'already fresh'}: {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
