#!/usr/bin/env python3
"""Bake the nameplate: KRIMAN, resolving out of liquid glass.

The word arrives as a displaced, blurred smear and settles into a frosted
mark. Once it has cleared it keeps moving: a broad caustic rolls across the
letters, a finer glint crosses the other way, and the refraction field drifts
so the edges never freeze.

With --window invert one eight-row band of the film is clipped into the word
and inverted: the letters become dark apertures with the film running white
inside them, while a flat white rim holds the letterforms together so the
word still reads at phone width.

Usage:
    python3 tools/name_svg.py --out name.svg
    python3 tools/name_svg.py --window invert --out name.svg
"""
from __future__ import annotations

import argparse
import math
import os
import re

BG = "#000000"
INK = "#FFFFFF"

NAME = "KRIMAN"
W = 781
H = 162
FS = 140.0
TRACK = 0.16      # em
WEIGHT = 500
CAP = 0.729       # measured cap height of the mono stack, em

REVEAL = 4.2      # seconds to resolve
BLUR0 = 30.0      # starting blur, px
WARP0 = 70.0      # starting displacement, px
WARP = 6.5        # resting displacement, px

GLINT_TILE = 700.0
GLINT_PERIOD = 11.0
GLINT_DARK = 0.17
GLINT_WHITE = 1.0

SPEC_TILE = 760.0
SPEC_PERIOD = 12.0
SPEC_WHITE = 0.65

DRIFT_PERIOD = 16.0
DRIFT_X = 55.0
DRIFT_Y = 38.0

# The window: an eight-row band of the film, clipped to the word.
WIN_FS = 12.0
WIN_LH = 13.5
WIN_CAP = WIN_FS * CAP
WIN_W = 749.0
WIN_H = 108.0
WIN_X = 16.0
WIN_ROWS = (8, 16)    # rows 8..15 of the 26-row film
WIN_RATE = 10.0

# The rim is what keeps the word readable once the film replaces the fill.
RIM_W = 1.8
RIM_OPACITY = 0.95
# How much of the glass letter body survives under the film. At 1.0 the
# letters are pure black apertures and the word collapses to an outline at
# phone width; a little body keeps the 140px weight.
WIN_DIM = 0.72


def load_band(path: str, rows: tuple[int, int]):
    """Cut one band out of every film frame and bake a 10 fps loop.

    Returns the 300 frame groups, a still of frame 0 for reduced motion, and
    the y offset that centres the band on the cap height.
    """
    with open(path, encoding="utf-8") as f:
        film = f.read()

    groups = re.findall(r'<g class="f(\d+)"[^>]*>(.*?)</g>', film, re.S)
    if len(groups) != 300:
        raise SystemExit(f"{path}: expected 300 frames, found {len(groups)}")

    bands = []
    for _, inner in groups:
        grid = [["\xa0"] * 104 for _ in range(26)]
        for y_text, content in re.findall(
                r'<text x="0" y="([0-9.]+)">(.*?)</text>', inner, re.S):
            row = int(round(float(y_text) / WIN_LH)) - 1
            if 0 <= row < 26:
                content = content.rstrip("\n")
                for i, ch in enumerate(content[:104]):
                    grid[row][i] = ch
        bands.append(["".join(grid[r][:104]) for r in range(rows[0], rows[1])])

    ys = [f"{WIN_CAP + r * WIN_LH:.1f}" for r in range(rows[1] - rows[0])]

    def body(idx: int) -> list[str]:
        out = [f'          <rect width="{WIN_W:.0f}" height="{WIN_H:.0f}" '
               f'fill="{BG}" fill-opacity="{WIN_DIM:.2f}"/>']
        out += [f'          <text x="0" y="{y}">{line}</text>'
                for y, line in zip(ys, bands[idx])]
        return out

    film_out, still_rows = [], []
    for idx in range(300):
        if idx == 0:
            still_rows = body(idx)
            film_out.append('      <g class="w0" visibility="visible">')
            film_out.extend(still_rows)
            film_out.append("      </g>")
        else:
            begin = idx / WIN_RATE
            film_out.append(f'      <g class="w{idx}" visibility="hidden">')
            film_out.append(
                '        <animate attributeName="visibility" calcMode="discrete" '
                'values="visible;hidden" keyTimes="0;0.003333" dur="30.000s" '
                f'begin="{begin:.3f}s" repeatCount="indefinite"/>')
            film_out.extend(body(idx))
            film_out.append("      </g>")

    # The band is a hair taller than the cap; centre the overflow so both the
    # top and bottom rows lose the same half-pixel to the clip.
    ink_h = WIN_CAP + (rows[1] - rows[0] - 1) * WIN_LH
    strip_y = (H / 2 - FS * CAP / 2) - (ink_h - FS * CAP) / 2
    return "\n".join(film_out), "\n".join(still_rows), strip_y


def build(out_path: str, window: str = "none", film_path: str = "badapple.svg",
          rows: tuple[int, int] = WIN_ROWS) -> tuple[int, int]:
    cap = FS * CAP
    baseline = H / 2 + cap / 2
    x = W / 2

    clip_def, window_css, window_markup = "", "", ""
    rim_css = ".rim{fill:none;stroke:url(#edge);stroke-width:.8}"
    glass_tail = ""
    after_glass = ""
    if window != "none":
        if window != "invert":
            raise SystemExit(f"unknown window variant: {window}")
        strip, still, strip_y = load_band(film_path, rows)
        clip_def = (
            f'\n<clipPath id="wordClip"><text class="word" x="{x:.1f}" '
            f'y="{baseline:.2f}">{NAME}</text></clipPath>')
        window_css = (
            '\n.win-film text,.win-still text{font-family:ui-monospace,'
            'SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",'
            f'monospace;font-size:{WIN_FS:g}px}}\n'
            ".win-still{display:none}\n"
            "@media (prefers-reduced-motion:reduce){"
            ".win-film{display:none}.win-still{display:block}}")
        # Inside the window the rim is the only thing holding the letter
        # shapes, so it goes flat white: the glass edge gradient fades to
        # transparent and then to black, which erases the right half.
        rim_css = (f".rim{{fill:none;stroke:#FFFFFF;stroke-width:{RIM_W:.1f};"
                   f"stroke-opacity:{RIM_OPACITY:.2f}}}")
        window_markup = f"""
  <g opacity="1">
    <animate attributeName="opacity" values="0;0;1" keyTimes="0;.78;1" dur="{REVEAL:.3f}s" fill="freeze"/>
    <g clip-path="url(#wordClip)">
      <g class="win-film" transform="translate({WIN_X:.1f},{strip_y:.2f})" fill="{INK}">
{strip}
      </g>
      <g class="win-still" transform="translate({WIN_X:.1f},{strip_y:.2f})" fill="{INK}">
{still}
      </g>
    </g>
    <text class="word rim" x="{x:.1f}" y="{baseline:.2f}">{NAME}</text>
  </g>"""

    # The window and its rim are the projection, not the glass: they sit
    # outside the refraction filter so the film stays crisp and the stroke
    # does not get chewed by the displacement.
    rim_text = (f'\n    <text class="word rim" x="{x:.1f}" '
                f'y="{baseline:.2f}">{NAME}</text>')
    if window == "none":
        glass_tail, after_glass = rim_text, ""
    else:
        glass_tail, after_glass = "", window_markup

    # Twelve points around an ellipse: the refraction field drifts in a slow
    # loop instead of bouncing back and forth.
    orbit = []
    for i in range(12):
        a = i * math.tau / 12
        orbit.append((DRIFT_X * math.cos(a), DRIFT_Y * math.sin(a)))
    orbit.append(orbit[0])
    dx_values = ";".join(f"{0.0 if abs(v) < .05 else v:.1f}" for v, _ in orbit)
    dy_values = ";".join(f"{0.0 if abs(v) < .05 else v:.1f}" for _, v in orbit)
    key_times = ";".join(f"{i / 12:.4f}".rstrip("0").rstrip(".") or "0"
                         for i in range(13))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Kriman">
<title>Kriman</title>
<defs>
<linearGradient id="frost" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#FFFFFF"/>
  <stop offset=".07" stop-color="#FFFFFF"/>
  <stop offset=".34" stop-color="#FCFCFC"/>
  <stop offset="1" stop-color="#EAEAEA"/>
</linearGradient>
<linearGradient id="edge" x1="0" y1="0" x2=".55" y2="1">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".32"/>
  <stop offset=".45" stop-color="#FFFFFF" stop-opacity=".06"/>
  <stop offset="1" stop-color="#000000" stop-opacity=".18"/>
</linearGradient>
<linearGradient id="glint" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{GLINT_TILE:.0f}" y2="{GLINT_TILE * .2:.0f}" spreadMethod="repeat">
  <stop offset="0" stop-color="#000000" stop-opacity="0"/>
  <stop offset=".21" stop-color="#000000" stop-opacity="0"/>
  <stop offset=".31" stop-color="#000000" stop-opacity="{GLINT_DARK * .55:.3f}"/>
  <stop offset=".39" stop-color="#000000" stop-opacity="{GLINT_DARK:.3f}"/>
  <stop offset=".45" stop-color="#FFFFFF" stop-opacity="{GLINT_WHITE * .4:.3f}"/>
  <stop offset=".48" stop-color="#FFFFFF" stop-opacity="{GLINT_WHITE:.3f}"/>
  <stop offset=".52" stop-color="#FFFFFF" stop-opacity="{GLINT_WHITE:.3f}"/>
  <stop offset=".55" stop-color="#FFFFFF" stop-opacity="{GLINT_WHITE * .4:.3f}"/>
  <stop offset=".61" stop-color="#000000" stop-opacity="{GLINT_DARK:.3f}"/>
  <stop offset=".69" stop-color="#000000" stop-opacity="{GLINT_DARK * .55:.3f}"/>
  <stop offset=".79" stop-color="#000000" stop-opacity="0"/>
  <stop offset="1" stop-color="#000000" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="0 0;{GLINT_TILE:.0f} {GLINT_TILE * .2:.0f}" dur="{GLINT_PERIOD:.3f}s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="spec" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{SPEC_TILE:.0f}" y2="{SPEC_TILE * .2:.0f}" spreadMethod="repeat">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".492" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset=".497" stop-color="#FFFFFF" stop-opacity="{SPEC_WHITE:.3f}"/>
  <stop offset=".503" stop-color="#FFFFFF" stop-opacity="{SPEC_WHITE:.3f}"/>
  <stop offset=".508" stop-color="#FFFFFF" stop-opacity="0"/>
  <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
  <animateTransform attributeName="gradientTransform" type="translate" values="{SPEC_TILE:.0f} {SPEC_TILE * .2:.0f};0 0" dur="{SPEC_PERIOD:.3f}s" repeatCount="indefinite"/>
</linearGradient>
<filter id="bloom" filterUnits="userSpaceOnUse" x="-160" y="-140" width="{W + 320}" height="{H + 280}">
  <feGaussianBlur stdDeviation="9"/>
</filter>
<filter id="glass" filterUnits="userSpaceOnUse" x="-320" y="-260" width="{W + 640}" height="{H + 520}">
  <feTurbulence type="fractalNoise" baseFrequency="0.008 0.012" numOctaves="2" seed="11" result="noise"/>
  <feOffset in="noise" result="shift">
    <animate attributeName="dx" values="{dx_values}" keyTimes="{key_times}" dur="{DRIFT_PERIOD:.3f}s" repeatCount="indefinite"/>
    <animate attributeName="dy" values="{dy_values}" keyTimes="{key_times}" dur="{DRIFT_PERIOD:.3f}s" repeatCount="indefinite"/>
  </feOffset>
  <feDisplacementMap in="SourceGraphic" in2="shift" scale="{WARP}" xChannelSelector="R" yChannelSelector="G" result="warp">
    <animate attributeName="scale" values="{WARP0};{WARP}" dur="{REVEAL:.3f}s" fill="freeze" calcMode="spline" keySplines=".37 0 .2 1"/>
  </feDisplacementMap>
  <feGaussianBlur in="warp" stdDeviation="0">
    <animate attributeName="stdDeviation" values="{BLUR0};0" dur="{REVEAL:.3f}s" fill="freeze" calcMode="spline" keySplines=".37 0 .2 1"/>
  </feGaussianBlur>
</filter>{clip_def}
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<style>
.word{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.1f}px;font-weight:{WEIGHT};letter-spacing:{TRACK:.3f}em;text-anchor:middle}}
{rim_css}{window_css}
</style>
<g opacity="1">
  <animate attributeName="opacity" values="0;1" dur="3.4s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1"/>
  <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="{INK}" opacity="0" filter="url(#bloom)">{NAME}<animate attributeName="opacity" values="0;0;.12" keyTimes="0;.55;1" dur="{REVEAL:.3f}s" fill="freeze"/></text>
  <g filter="url(#glass)">
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#frost)">{NAME}</text>
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#glint)">{NAME}</text>
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#spec)">{NAME}</text>{glass_tail}
  </g>{after_glass}
</g>
</svg>
"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return W, H


def main(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="name.svg")
    p.add_argument("--window", choices=("none", "invert"), default="none",
                   help="clip a band of the film into the word, inverted")
    p.add_argument("--film", default="badapple.svg",
                   help="baked film to slice the window from")
    p.add_argument("--rows", default="8:16",
                   help="row band of the 26-row film, start:end")
    a = p.parse_args(argv)
    rows = tuple(int(n) for n in a.rows.split(":"))
    if len(rows) != 2 or not 0 <= rows[0] < rows[1] <= 26:
        p.error("--rows must be a start:end inside 0..26")
    w, h = build(a.out, window=a.window, film_path=a.film, rows=rows)
    note = "" if a.window == "none" else f" · window {a.window} {rows[0]}:{rows[1]}"
    print(f"{a.out}: {w}x{h}px · {os.path.getsize(a.out) / 1024:.1f} KB{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
