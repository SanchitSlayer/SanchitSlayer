"""Build the GitHub stats card shown on the profile README.

Reads public data for one user from the GitHub GraphQL API and writes a dark and
a light SVG card (stats, top languages and contribution streaks) to assets/.
Runs daily from .github/workflows/profile.yml with the workflow's own token.
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from html import escape

USER = os.environ.get("PROFILE_USER", "SanchitSlayer")
TOKEN = os.environ.get("GITHUB_TOKEN")
OUT_DIR = os.environ.get("OUT_DIR", os.path.join(os.path.dirname(__file__), "..", "assets"))

THEMES = {
    "dark": {
        "bg1": "#0d1117", "bg2": "#161b2e", "border": "#30363d",
        "title": "#e6edf3", "text": "#c9d1d9", "muted": "#8b949e",
        "accent": "#58a6ff", "accent2": "#a371f7", "track": "#21262d",
    },
    "light": {
        "bg1": "#ffffff", "bg2": "#f3f6fb", "border": "#d0d7de",
        "title": "#1f2328", "text": "#24292f", "muted": "#57606a",
        "accent": "#0a66c2", "accent2": "#8250df", "track": "#eaeef2",
    },
}

# Notebook sizes are mostly stored outputs, which would swamp the code languages.
HIDDEN_LANGUAGES = {"Jupyter Notebook"}

LANG_COLORS = {
    "TypeScript": "#3178c6", "Python": "#3572A5", "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B", "TSQL": "#e38c00", "C": "#555555",
    "C++": "#f34b7d", "CSS": "#663399", "HTML": "#e34c26",
    "PLpgSQL": "#336790", "Shell": "#89e051", "Dockerfile": "#384d54",
}


def graphql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch():
    data = graphql(
        """
        query($login: String!) {
          user(login: $login) {
            createdAt
            followers { totalCount }
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
              totalCount
              nodes {
                stargazerCount
                languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                  edges { size node { name color } }
                }
              }
            }
            contributionsCollection {
              totalCommitContributions
              totalPullRequestContributions
            }
          }
        }
        """,
        {"login": USER},
    )["user"]

    # The calendar is limited to one year per query, so walk back to account creation.
    days = {}
    created = dt.datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
    end = dt.datetime.now(dt.timezone.utc)
    while end > created:
        start = max(created, end - dt.timedelta(days=364))
        cal = graphql(
            """
            query($login: String!, $from: DateTime!, $to: DateTime!) {
              user(login: $login) {
                contributionsCollection(from: $from, to: $to) {
                  contributionCalendar { weeks { contributionDays { date contributionCount } } }
                }
              }
            }
            """,
            {"login": USER, "from": start.isoformat(), "to": end.isoformat()},
        )["user"]["contributionsCollection"]["contributionCalendar"]
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                days[day["date"]] = day["contributionCount"]
        end = start - dt.timedelta(seconds=1)
    return data, days


def streaks(days):
    ordered = sorted(days.items())
    longest = run = 0
    for _, count in ordered:
        run = run + 1 if count else 0
        longest = max(longest, run)
    # Today may not have a contribution yet; the streak still counts until tomorrow.
    current = 0
    for i, (_, count) in enumerate(reversed(ordered)):
        if count:
            current += 1
        elif i > 0:
            break
    return current, longest, sum(days.values())


def languages(repos):
    totals, colors = {}, {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            if name in HIDDEN_LANGUAGES:
                continue
            totals[name] = totals.get(name, 0) + edge["size"]
            colors[name] = edge["node"]["color"] or LANG_COLORS.get(name, "#8b949e")
    grand = sum(totals.values()) or 1
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    return [(name, size / grand * 100, colors[name]) for name, size in top]


def render(theme, stats, langs):
    c = THEMES[theme]
    w, h = 900, 300
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="GitHub stats for {USER}">',
        "<defs>",
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["bg1"]}"/><stop offset="1" stop-color="{c["bg2"]}"/></linearGradient>',
        f'<linearGradient id="ac" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c["accent"]}"/><stop offset="1" stop-color="{c["accent2"]}"/></linearGradient>',
        "</defs>",
        "<style>",
        "text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif}",
        f".h{{font-size:15px;font-weight:600;fill:{c['muted']};letter-spacing:1.5px}}",
        f".big{{font-size:30px;font-weight:700;fill:{c['title']}}}",
        f".lbl{{font-size:13px;fill:{c['muted']}}}",
        f".ln{{font-size:13px;fill:{c['text']}}}",
        ".fade{animation:in .6s ease-out backwards}",
        "@keyframes in{from{opacity:0}}",
        "</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#bg)" stroke="{c["border"]}"/>',
        f'<rect x="0" y="0" width="{w}" height="4" rx="2" fill="url(#ac)"/>',
        '<text x="32" y="44" class="h">GITHUB AT A GLANCE</text>',
    ]

    tiles = [
        (stats["contributions"], "Total contributions"),
        (stats["current"], "Current streak (days)"),
        (stats["longest"], "Longest streak (days)"),
        (stats["commits"], "Commits (past year)"),
        (stats["repos"], "Public repositories"),
        (stats["stars"], "Stars earned"),
    ]
    for i, (value, label) in enumerate(tiles):
        x = 32 + (i % 3) * 150
        y = 96 + (i // 3) * 92
        parts.append(
            f'<g class="fade" style="animation-delay:{i * 0.08:.2f}s">'
            f'<text x="{x}" y="{y}" class="big">{value:,}</text>'
            f'<text x="{x}" y="{y + 24}" class="lbl">{escape(label)}</text></g>'
        )

    parts.append(f'<line x1="500" y1="40" x2="500" y2="{h - 40}" stroke="{c["border"]}"/>')
    parts.append('<text x="532" y="44" class="h">TOP LANGUAGES</text>')
    bar_x, bar_w, offset = 532, 336, 0.0
    parts.append(f'<rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5" fill="{c["track"]}"/>')
    parts.append(f'<clipPath id="bar"><rect x="{bar_x}" y="66" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)">')
    for name, pct, color in langs:
        seg = bar_w * pct / 100
        parts.append(f'<rect x="{bar_x + offset:.1f}" y="66" width="{seg:.1f}" height="10" fill="{color}"/>')
        offset += seg
    parts.append("</g>")
    for i, (name, pct, color) in enumerate(langs):
        x = bar_x + (i % 2) * 176
        y = 112 + (i // 2) * 34
        parts.append(
            f'<g class="fade" style="animation-delay:{0.4 + i * 0.08:.2f}s">'
            f'<circle cx="{x + 6}" cy="{y - 4}" r="6" fill="{color}"/>'
            f'<text x="{x + 20}" y="{y}" class="ln">{escape(name)} <tspan fill="{c["muted"]}">{pct:.1f}%</tspan></text></g>'
        )
    updated = dt.date.today().strftime("%d %b %Y")
    parts.append(f'<text x="{w - 32}" y="{h - 18}" class="lbl" text-anchor="end" style="font-size:11px">Updated {updated}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is not set")
    user, days = fetch()
    current, longest, total = streaks(days)
    repos = user["repositories"]["nodes"]
    cc = user["contributionsCollection"]
    stats = {
        "contributions": total,
        "current": current,
        "longest": longest,
        "commits": cc["totalCommitContributions"],
        "repos": user["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
    }
    langs = languages(repos)
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(OUT_DIR, f"stats-{theme}.svg"), "w") as f:
            f.write(render(theme, stats, langs))
    print(json.dumps({**stats, "languages": [(n, round(p, 1)) for n, p, _ in langs]}))


if __name__ == "__main__":
    main()
