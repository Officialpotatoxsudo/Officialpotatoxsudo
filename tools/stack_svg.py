#!/usr/bin/env python3
"""Bake the stack plate: four layers, one signal, no badges.

Same field and type as the film so the two read as one instrument. A pulse
runs the rail once per loop; as it reaches a row, a soft crest travels the
tech string, lifting and brightening each character in turn.

Usage:
    python3 tools/stack_svg.py --out stack.svg
"""
from __future__ import annotations

import argparse
import os

BG = "#000000"
RULE = "#141414"
RAIL = "#1A1A1A"
DIM = "#474747"      # index
MID = "#7C7C7C"      # layer name
HOT = "#FFFFFF"      # wave crest
PULSE = "#FFFFFF"

FS = 12.0        # tech size
ADV = 7.2        # monospace advance
W = 620
ROWH = 38
TOP = 18
RAIL_X = 14
IDX_X = 30
LAYER_X = 56
TECH_X = 150

PERIOD = 9.0      # loop, seconds
ROW_START = 0.38  # first crest
ROW_STEP = 0.50   # crest to crest
CHAR_STEP = 0.026 # per character
REST_OP = 0.66    # idle glyph brightness
LIFT = 2.2        # px each character rises at the crest
BLUR = 2.8        # crest halo blur

ROWS = [
    ("01", "CLIENT", "flutter · kotlin · compose · react · next · expo"),
    ("02", "SERVER", "typescript · python · fastapi · fastify · node · go"),
    ("03", "DATA", "postgres · supabase · redis · minio · prisma · room"),
    ("04", "OPS", "docker · actions · linux · cloudflare · gradle · git"),
]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wave(text: str, base: float, y: float, halo: bool = False) -> str:
    """One <text> per glyph, each with its own crest delay.

    halo=True draws the blur source: it has no lift and is invisible at rest,
    so only the passing crest glows.
    """
    out = []
    lo, hi = ("0", "1") if halo else (str(REST_OP), "1")
    for j, ch in enumerate(text):
        if ch == " ":
            continue
        t0 = (base + j * CHAR_STEP) / PERIOD
        t1 = (base + j * CHAR_STEP + 0.22) / PERIOD
        t2 = (base + j * CHAR_STEP + 0.40) / PERIOD
        t3 = (base + j * CHAR_STEP + 1.20) / PERIOD
        times = f"0;{t0:.5f};{t1:.5f};{t2:.5f};{t3:.5f};1"
        splines = "0 0 1 1;.2 .1 .3 1;0 0 1 1;.4 0 .6 1;0 0 1 1"
        anim = (f'<animate attributeName="opacity" calcMode="spline" keySplines="{splines}" '
                f'values="{lo};{lo};{hi};{hi};{lo};{lo}" '
                f'keyTimes="{times}" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>')
        if not halo:
            anim += (f'<animateTransform attributeName="transform" type="translate" calcMode="spline" '
                     f'keySplines="{splines}" values="0 0;0 0;0 {-LIFT};0 {-LIFT};0 0;0 0" '
                     f'keyTimes="{times}" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>')
        out.append(
            f'    <text class="tech" x="{TECH_X + j * ADV:.1f}" y="{y:.1f}" '
            f'opacity="{lo}">{esc(ch)}{anim}</text>')
    return "\n".join(out)


def row(i: int) -> str:
    idx, layer, tech = ROWS[i]
    top = TOP + i * ROWH
    base = top + 25
    start = ROW_START + i * ROW_STEP

    def kt(t: float) -> str:
        return f"{t / PERIOD:.5f}"

    return f"""  <g>
    <line x1="0" y1="{top + ROWH - 1}" x2="{W}" y2="{top + ROWH - 1}" stroke="{RULE}"/>
    <text class="idx" x="{IDX_X}" y="{base}">{idx}</text>
    <text class="layer" x="{LAYER_X}" y="{base}">{layer}</text>
    <g filter="url(#soft)" opacity=".65">
{wave(tech, start, base, halo=True)}
    </g>
{wave(tech, start, base)}
  </g>"""


def build(out_path: str) -> tuple[int, int, int]:
    h = TOP + len(ROWS) * ROWH + 14
    rows = "\n".join(row(i) for i in range(len(ROWS)))
    pulse_end = ROW_START + (len(ROWS) - 1) * ROW_STEP
    pulse_y0 = TOP + 7
    pulse_y1 = TOP + (len(ROWS) - 1) * ROWH + 7

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="Stack: Flutter, Kotlin, Compose, React, Next, Expo for clients; TypeScript, Python, FastAPI, Fastify, Node, Go for services; Postgres, Supabase, Redis, MinIO, Prisma, Room for data; Docker, Actions, Linux, Cloudflare, Gradle, Git for ops">
<title>Stack</title>
<defs>
<filter id="soft" x="-4%" y="-60%" width="108%" height="220%">
  <feGaussianBlur stdDeviation="{BLUR}"/>
</filter>
</defs>
<rect width="{W}" height="{h}" fill="{BG}"/>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.0f}px;fill="{HOT}"}}
.idx{{font-size:9px;fill:{DIM};letter-spacing:.06em}}
.layer{{font-size:9px;fill:{MID};letter-spacing:.18em}}
.tech{{fill:{HOT}}}
</style>
<rect x="{RAIL_X}" y="{TOP}" width="1" height="{len(ROWS) * ROWH}" fill="{RAIL}"/>
<g opacity="0">
  <animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;{ROW_START / PERIOD - 0.01:.5f};{(pulse_end + 0.1) / PERIOD:.5f};{(pulse_end + 0.2) / PERIOD:.5f};1" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>
  <rect x="{RAIL_X - 1}" y="{pulse_y0}" width="3" height="24" fill="{PULSE}" opacity="0.55">
    <animate attributeName="y" values="{pulse_y0};{pulse_y0};{pulse_y1};{pulse_y1}" keyTimes="0;{ROW_START / PERIOD:.5f};{pulse_end / PERIOD:.5f};1" dur="{PERIOD:.3f}s" repeatCount="indefinite"/>
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
