#!/usr/bin/env python3
"""Bake the stack plate: four layers, one signal, no badges.

Same field and type as the film so the two read as one instrument. A single
vertical pulse runs the rail once per loop and a white overlay brightens each
row as it passes. Everything after the scan sits still for most of the loop.

Usage:
    python3 tools/stack_svg.py --out stack.svg
"""
from __future__ import annotations

import argparse
import os

BG = "#000000"
RULE = "#141414"
RAIL = "#1A1A1A"
DIM = "#3D3D3D"      # index
MID = "#6B6B6B"      # layer name
INK = "#B8B8B8"      # tech list
HOT = "#FFFFFF"      # scan overlay
PULSE = "#FFFFFF"

FS = 12.0        # tech size
ADV = 7.2        # monospace advance
W = 620
ROWH = 38
TOP = 18
PAD_R = 14
RAIL_X = 14
IDX_X = 30
LAYER_X = 56
TECH_X = 150

PERIOD = 9.0      # loop, seconds
SCAN = 2.2        # rail travel
HOT_IN = 0.35     # overlay fade in
HOT_OUT = 0.85    # overlay fade out

ROWS = [
    ("01", "CLIENT", "flutter · kotlin · compose · react · next · expo"),
    ("02", "SERVER", "typescript · python · fastapi · fastify · node · go"),
    ("03", "DATA", "postgres · supabase · redis · minio · prisma · room"),
    ("04", "OPS", "docker · actions · linux · cloudflare · gradle · git"),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row(i: int) -> str:
    idx, layer, tech = ROWS[i]
    base = TOP + i * ROWH + 25
    hot = (0.05 + 0.075 * i) * PERIOD   # pulse reaches this row

    def kt(t: float) -> str:
        return f"{t / PERIOD:.4f}"

    in_at = hot + 0.10
    out_at = hot + 0.55
    op = "0;0;0.55;0.55;0;0"
    times = f"0;{kt(hot)};{kt(in_at)};{kt(out_at)};{kt(out_at + 0.45)};1"

    return f"""  <g>
    <line x1="0" y1="{TOP + (i + 1) * ROWH - 1}" x2="{W}" y2="{TOP + (i + 1) * ROWH - 1}" stroke="{RULE}"/>
    <text class="idx" x="{IDX_X}" y="{base}">{idx}</text>
    <text class="layer" x="{LAYER_X}" y="{base}">{layer}</text>
    <text class="tech" x="{TECH_X}" y="{base}">{esc(tech)}</text>
    <g opacity="0">
      <animate attributeName="opacity" values="{op}" keyTimes="{times}" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>
      <text class="tech hot" x="{TECH_X}" y="{base}">{esc(tech)}</text>
    </g>
  </g>"""


def build(out_path: str) -> tuple[int, int, int]:
    h = TOP + len(ROWS) * ROWH + 14
    rows = "\n".join(row(i) for i in range(len(ROWS)))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Stack: Flutter, Kotlin, Compose, React, Next, Expo for clients; TypeScript, Python, FastAPI, Fastify, Node, Go for services; Postgres, Supabase, Redis, MinIO, Prisma, Room for data; Docker, Actions, Linux, Cloudflare, Gradle, Git for ops">
<title>Stack</title>
<rect width="{W}" height="{h}" fill="{BG}"/>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.0f}px;fill:{INK}}}
.idx{{font-size:9px;fill:{DIM};letter-spacing:.06em}}
.layer{{font-size:9px;fill:{MID};letter-spacing:.18em}}
.hot{{fill:{HOT}}}
</style>
<rect x="{RAIL_X}" y="{TOP}" width="1" height="{len(ROWS) * ROWH}" fill="{RAIL}"/>
<g opacity="0">
  <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;0.02;0.30;0.34;1" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>
  <rect x="{RAIL_X - 1}" y="{TOP}" width="3" height="24" fill="{PULSE}" opacity="0.55">
    <animate attributeName="y" values="{TOP};{TOP};{TOP + len(ROWS) * ROWH - 24};{TOP + len(ROWS) * ROWH - 24}" keyTimes="0;0.02;0.30;1" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>
  </rect>
</g>
{rows}
</svg>
"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return W, h, len(ROWS)


def main(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="stack.svg")
    a = p.parse_args(argv)
    w, h, n = build(a.out)
    print(f"{a.out}: {n} rows · {w}x{h}px · "
          f"{os.path.getsize(a.out) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
