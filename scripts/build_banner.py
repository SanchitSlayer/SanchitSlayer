"""Build the animated header banner (dark and light) for the profile README.

The roles line types and erases each role in turn using SMIL animations, which
GitHub renders inside <img>. Only system fonts are used, since images on GitHub
cannot load web fonts.
"""

import os

NAME = "Sanchit Garg"
SUBTITLE = "IIT Jodhpur  ·  Ex-Product Management Intern, OneMetric"
ROLES = [
    "Building AI agents",
    "AI Engineering",
    "Automating workflows",
    "Product Management",
    "Product Analytics",
    "Consulting",
]
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

THEMES = {
    "dark": {
        "bg1": "#0b1020", "bg2": "#141a35", "grid": "#ffffff", "grid_op": "0.05",
        "name": "#f0f6fc", "sub": "#8b949e", "role": "#7ee0ff", "prompt": "#a371f7",
        "glow1": "#2f81f7", "glow2": "#8957e5", "border": "#30363d",
    },
    "light": {
        "bg1": "#f6f8ff", "bg2": "#eef1fb", "grid": "#0a2540", "grid_op": "0.06",
        "name": "#0f172a", "sub": "#57606a", "role": "#0a66c2", "prompt": "#8250df",
        "glow1": "#54aeff", "glow2": "#c297ff", "border": "#d0d7de",
    },
}

W, H = 1200, 300
CHAR_W = 0.6 * 30  # monospace advance at 30px
SLOT = 3.0  # seconds each role is on screen
TOTAL = SLOT * len(ROLES)


def role_layers(c):
    out = []
    for i, role in enumerate(ROLES):
        width = len(role) * CHAR_W + 4
        start, end = i * SLOT / TOTAL, (i + 1) * SLOT / TOTAL
        typed = start + 0.9 / TOTAL
        erase = end - 0.45 / TOTAL
        # Width of the reveal mask over the whole cycle: closed, typing, open, erasing, closed.
        key_times = sorted({0.0, start, typed, erase, end, 1.0})
        widths = {0.0: 0, start: 0, typed: width, erase: width, end: 0, 1.0: 0}
        kt = ";".join(f"{t:.4f}" for t in key_times)
        vals = ";".join(str(round(widths[t], 1)) for t in key_times)
        out.append(
            f'<clipPath id="r{i}"><rect x="128" y="186" height="44" width="0">'
            f'<animate attributeName="width" dur="{TOTAL}s" repeatCount="indefinite" '
            f'keyTimes="{kt}" values="{vals}" calcMode="linear"/></rect></clipPath>'
            f'<text x="130" y="219" class="role" clip-path="url(#r{i})">{role}</text>'
        )
        # The cursor is shown only during this role's slot and follows the typed text.
        vis = [(0.0, 0), (start, 1), (end, 0)]
        if start == 0.0:
            vis = [(0.0, 1), (end, 0)]
        if end >= 1.0:
            vis = [p for p in vis if p[0] < 1.0]
        vis_kt = ";".join(f"{t:.4f}" for t, _ in vis)
        vis_vals = ";".join(str(v) for _, v in vis)
        out.append(
            f'<rect y="192" width="3" height="32" fill="{c["role"]}" x="130" opacity="0">'
            f'<animate attributeName="x" dur="{TOTAL}s" repeatCount="indefinite" keyTimes="{kt}" '
            f'values="{";".join(str(round(130 + widths[t], 1)) for t in key_times)}"/>'
            f'<animate attributeName="opacity" dur="{TOTAL}s" repeatCount="indefinite" calcMode="discrete" '
            f'keyTimes="{vis_kt}" values="{vis_vals}"/></rect>'
        )
    return "".join(out)


def render(theme):
    c = THEMES[theme]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{NAME}: AI Engineering, Product, Consulting">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/>
  </linearGradient>
  <radialGradient id="g1" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{c['glow1']}" stop-opacity="0.55"/><stop offset="1" stop-color="{c['glow1']}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="g2" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{c['glow2']}" stop-opacity="0.5"/><stop offset="1" stop-color="{c['glow2']}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="nm" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{c['name']}"/><stop offset="1" stop-color="{c['role']}"/>
  </linearGradient>
  <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M40 0H0V40" fill="none" stroke="{c['grid']}" stroke-opacity="{c['grid_op']}"/>
  </pattern>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<style>
  .name {{ font: 800 64px -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; letter-spacing: -1px; }}
  .sub {{ font: 500 20px -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {c['sub']}; }}
  .role {{ font: 600 30px ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; fill: {c['role']}; }}
  .prompt {{ font: 600 30px ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; fill: {c['prompt']}; }}
  .in {{ animation: up .8s ease-out backwards; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <circle cx="1010" cy="70" r="230" fill="url(#g1)">
    <animate attributeName="cy" values="70;110;70" dur="9s" repeatCount="indefinite"/>
  </circle>
  <circle cx="860" cy="280" r="200" fill="url(#g2)">
    <animate attributeName="cx" values="860;920;860" dur="11s" repeatCount="indefinite"/>
  </circle>
  <g fill="none" stroke="{c['role']}" stroke-opacity="0.35" stroke-width="1.5">
    <path d="M900 150 L980 110 L1060 160 L1130 120"/>
    <path d="M980 110 L1010 200 L1060 160"/>
  </g>
  <g fill="{c['role']}">
    <circle cx="900" cy="150" r="5"><animate attributeName="opacity" values="1;.3;1" dur="2.4s" repeatCount="indefinite"/></circle>
    <circle cx="980" cy="110" r="6"><animate attributeName="opacity" values=".3;1;.3" dur="2.4s" repeatCount="indefinite"/></circle>
    <circle cx="1060" cy="160" r="5"><animate attributeName="opacity" values="1;.4;1" dur="3s" repeatCount="indefinite"/></circle>
    <circle cx="1130" cy="120" r="4"><animate attributeName="opacity" values=".4;1;.4" dur="2s" repeatCount="indefinite"/></circle>
    <circle cx="1010" cy="200" r="5"><animate attributeName="opacity" values="1;.3;1" dur="2.8s" repeatCount="indefinite"/></circle>
  </g>
  <text x="72" y="118" class="name in" fill="url(#nm)">{NAME}</text>
  <text x="76" y="160" class="sub in" style="animation-delay:.2s">{SUBTITLE}</text>
  <g class="in" style="animation-delay:.4s">
    <text x="76" y="219" class="prompt">&gt;_</text>
    {role_layers(c)}
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="18" fill="none" stroke="{c['border']}"/>
</g>
</svg>
"""


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for theme in THEMES:
        with open(os.path.join(OUT_DIR, f"banner-{theme}.svg"), "w") as f:
            f.write(render(theme))


if __name__ == "__main__":
    main()
