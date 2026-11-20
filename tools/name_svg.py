#!/usr/bin/env python3
"""Bake the nameplate: KRIMAN, resolving out of liquid glass.

The word arrives as a displaced, blurred smear and settles into a frosted
mark. Once it has cleared it keeps moving: a broad caustic rolls across the
letters, a finer glint crosses the other way, and the refraction field drifts
so the edges never freeze.

Usage:
    python3 tools/name_svg.py --out name.svg
"""
from __future__ import annotations

import argparse
import math
import os

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


def build(out_path: str) -> tuple[int, int]:
    cap = FS * CAP
    baseline = H / 2 + cap / 2
    x = W / 2

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
</filter>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<style>
.word{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.1f}px;font-weight:{WEIGHT};letter-spacing:{TRACK:.3f}em;text-anchor:middle}}
.rim{{fill:none;stroke:url(#edge);stroke-width:.8}}
</style>
<g opacity="1">
  <animate attributeName="opacity" values="0;1" dur="3.4s" fill="freeze" calcMode="spline" keySplines=".4 0 .2 1"/>
  <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="{INK}" opacity="0" filter="url(#bloom)">{NAME}<animate attributeName="opacity" values="0;0;.12" keyTimes="0;.55;1" dur="{REVEAL:.3f}s" fill="freeze"/></text>
  <g filter="url(#glass)">
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#frost)">{NAME}</text>
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#glint)">{NAME}</text>
    <text class="word" x="{x:.1f}" y="{baseline:.2f}" fill="url(#spec)">{NAME}</text>
    <text class="word rim" x="{x:.1f}" y="{baseline:.2f}">{NAME}</text>
  </g>
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
    a = p.parse_args(argv)
    w, h = build(a.out)
    print(f"{a.out}: {w}x{h}px · {os.path.getsize(a.out) / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
