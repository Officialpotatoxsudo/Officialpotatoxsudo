#!/usr/bin/env python3
"""Bake the contribution plate: a year of work as a breathing bead field.

The public contribution calendar is read from GitHub, its real levels are
kept, and the 53 x 7 grid is drawn in monochrome. Beads pour in from the left,
then keep moving: a slow swell travels through the field and a glass glint
crosses it. The total is the only number on the plate.

Usage:
    python3 tools/contrib_svg.py --out contrib.svg
    python3 tools/contrib_svg.py --html saved.html --out contrib.svg
"""
from __future__ import annotations

import argparse
import os
import re
import urllib.request

USER = "Officialpotatoxsudo"
URL = "https://github.com/users/{}/contributions"

BG = "#000000"
W = 781
H = 164
PITCH = 14
GAP = 3
CELL = PITCH - GAP
COLS_MAX = 54
Y0 = 52

LEVEL = {0: "#0E0E0E", 1: "#464646", 2: "#7E7E7E", 3: "#B4B4B4", 4: "#FFFFFF"}

TOTAL_FS = 26
LABEL_FS = 11
BASE = 33

POUR_START = 0.4     # first column starts
POUR_STEP = 0.04     # seconds between columns
POUR_DUR = 0.55
POUR_RISE = 7

BREATH = 9.0
DIM = 0.78
SCALE = 1.12

GLINT = 12.0
GLINT_TILE = 700.0
GLINT_PEAK = 0.22

TAG = re.compile(r"<td\b[^>]*>")
ATTR = re.compile(r'([\w:-]+)="([^"]*)"')
TIP = re.compile(
    r'<tool-tip\b[^>]*\bfor="(contribution-day-component-\d+-\d+)"[^>]*>(.*?)</tool-tip>',
    re.S,
)
TOTAL_H2 = re.compile(r"([\d,]+)\s+contributions\s+in the last year")


def fetch(user: str) -> str:
    req = urllib.request.Request(
        URL.format(user), headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse(html: str) -> tuple[list[dict], int, int]:
    counts = {}
    for cid, text in TIP.findall(html):
        m = re.search(r"(\d+)\s+contribution", text)
        counts[cid] = int(m.group(1)) if m else 0

    cells = []
    for tag in TAG.findall(html):
        a = dict(ATTR.findall(tag))
        if "data-date" not in a or "data-level" not in a:
            continue
        m = re.search(r"contribution-day-component-(\d+)-(\d+)", a.get("id", ""))
        if not m:
            continue
        cells.append(
            {
                "date": a["data-date"],
                "row": int(m.group(1)),
                "col": int(m.group(2)),
                "level": int(a["data-level"]),
                "count": counts.get(a.get("id", ""), 0),
            }
        )

    if not cells:
        raise SystemExit("no contribution cells found")

    total = sum(c["count"] for c in cells)
    active = sum(1 for c in cells if c["count"] > 0)
    cells.sort(key=lambda c: c["date"])

    h2 = TOTAL_H2.search(html)
    if h2 and int(h2.group(1).replace(",", "")) != total:
        print(f"note: page total {h2.group(1)} vs summed {total:,}")

    return cells, total, active


def build(cells: list[dict], total: int, active: int, out_path: str) -> tuple[int, int]:
    cols = max(c["col"] for c in cells) + 1
    if cols > COLS_MAX:
        raise SystemExit(f"calendar has {cols} columns, widen the plate")
    rows = max(c["row"] for c in cells) + 1

    grid_w = (cols - 1) * PITCH + CELL
    grid_h = (rows - 1) * PITCH + CELL
    x0 = (W - grid_w) / 2
    x1 = x0 + grid_w

    by_pos = {(c["row"], c["col"]): c for c in cells}

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Contributions: {total:,} in the last year, {active} active days">'
    )
    out.append("<title>Contributions</title>")
    out.append("<defs>")
    out.append(
        f"""<linearGradient id="glint" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{GLINT_TILE:.0f}" y2="{GLINT_TILE * .2:.0f}" spreadMethod="repeat">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".26" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".36" stop-color="#FFFFFF" stop-opacity=".05"/>
  <stop offset=".46" stop-color="#FFFFFF" stop-opacity=".16"/>
  <stop offset=".50" stop-color="#FFFFFF" stop-opacity="{GLINT_PEAK:.2f}"/>
  <stop offset=".54" stop-color="#FFFFFF" stop-opacity=".16"/>
  <stop offset=".64" stop-color="#FFFFFF" stop-opacity=".05"/>
  <stop offset=".74" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="0 0;{GLINT_TILE:.0f} {GLINT_TILE * .2:.0f}" dur="{GLINT:.3f}s" repeatCount="indefinite"/>
</linearGradient>"""
    )
    out.append(
        '<filter id="numblur" x="-50%" y="-120%" width="200%" height="340%">'
        '<feGaussianBlur stdDeviation="0">'
        '<animate attributeName="stdDeviation" values="12;0" dur="1.6s" begin=".6s" '
        'fill="freeze" calcMode="spline" keySplines=".37 0 .2 1"/>'
        "</feGaussianBlur></filter>"
    )
    out.append(
        '<filter id="bloom" x="-120%" y="-120%" width="340%" height="340%">'
        '<feGaussianBlur stdDeviation="5"/></filter>'
    )
    out.append("</defs>")
    out.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    out.append("<style>")
    out.append(
        'text{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,'
        'Consolas,"Liberation Mono",monospace}'
    )
    out.append(
        f".lbl{{font-size:{LABEL_FS}px;fill:#767676;letter-spacing:.14em}}"
    )
    out.append(
        f".tot{{font-size:{TOTAL_FS}px;font-weight:500;fill:#FFFFFF;"
        "letter-spacing:.02em;text-anchor:end}"
    )
    out.append("</style>")

    # label
    out.append(
        f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur=".9s" '
        f'begin=".15s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1"/>'
        f'<text class="lbl" x="{x0:.1f}" y="{BASE}">CONTRIBUTIONS · LAST 12 MONTHS</text></g>'
    )
    # total
    out.append(
        f'<g filter="url(#numblur)" opacity="0">'
        f'<animate attributeName="opacity" values="0;1" dur="1.2s" begin=".6s" fill="freeze"/>'
        f'<text class="tot" x="{x1:.1f}" y="{BASE + 5}">{total:,}</text></g>'
    )

    # bloom on the brightest days
    out.append('<g filter="url(#bloom)" opacity=".18">')
    for c in cells:
        if c["level"] < 3:
            continue
        x = x0 + c["col"] * PITCH
        y = Y0 + c["row"] * PITCH
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="3" fill="#FFFFFF"/>'
        )
    out.append("</g>")

    # beads
    out.append("<g>")
    for col in range(cols):
        begin = POUR_START + col * POUR_STEP
        out.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="0;1" dur="{POUR_DUR:.2f}s" '
            f'begin="{begin:.2f}s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'values="0 {POUR_RISE};0 0" dur=".7s" begin="{begin:.2f}s" '
            f'fill="freeze" calcMode="spline" keySplines=".37 0 .2 1"/>'
        )
        for row in range(rows):
            c = by_pos.get((row, col))
            if not c:
                continue
            cx = x0 + col * PITCH + CELL / 2
            cy = Y0 + row * PITCH + CELL / 2
            phase = (col * 0.13 + row * 0.19) % BREATH
            phase_s = "0" if abs(phase) < 0.0005 else f"-{phase:.3f}"
            out.append(f'<g transform="translate({cx:.1f} {cy:.1f})">')
            out.append(
                f'<rect x="{-CELL / 2:.1f}" y="{-CELL / 2:.1f}" width="{CELL}" height="{CELL}" '
                f'rx="3" fill="{LEVEL[c["level"]]}" opacity="1">'
            )
            out.append(
                f'<animateTransform attributeName="transform" type="scale" '
                f'values="1;{SCALE};1" keyTimes="0;.5;1" dur="{BREATH:.3f}s" '
                f'begin="{phase_s}s" repeatCount="indefinite" '
                f'calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1"/>'
            )
            out.append(
                f'<animate attributeName="opacity" values="{DIM};1;{DIM}" '
                f'keyTimes="0;.5;1" dur="{BREATH:.3f}s" begin="{phase_s}s" '
                f'repeatCount="indefinite" calcMode="spline" '
                f'keySplines=".4 0 .6 1;.4 0 .6 1"/>'
            )
            out.append("</rect></g>")
        out.append("</g>")
    out.append("</g>")

    # glint, only on the beads
    out.append(
        f'<mask id="cells" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
    )
    for c in cells:
        x = x0 + c["col"] * PITCH
        y = Y0 + c["row"] * PITCH
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="3" fill="#FFFFFF"/>'
        )
    out.append("</mask>")
    out.append(
        f'<rect x="{x0:.1f}" y="{Y0:.1f}" width="{grid_w:.1f}" height="{grid_h:.1f}" '
        f'fill="url(#glint)" mask="url(#cells)"/>'
    )
    out.append("</svg>")

    svg = "\n".join(out) + "\n"
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return W, H


def main(argv):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--out", default="contrib.svg")
    p.add_argument("--user", default=USER)
    p.add_argument("--html", help="read a saved contributions page instead of fetching")
    a = p.parse_args(argv)

    html = open(a.html, encoding="utf-8").read() if a.html else fetch(a.user)
    cells, total, active = parse(html)
    w, h = build(cells, total, active, a.out)
    print(
        f"{a.out}: {w}x{h}px · {os.path.getsize(a.out) / 1024:.1f} KB · "
        f"{total:,} contributions · {active} active days · "
        f"{cells[0]['date']} → {cells[-1]['date']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
