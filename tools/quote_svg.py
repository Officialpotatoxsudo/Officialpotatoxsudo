#!/usr/bin/env python3
"""Bake the quote plate: one line, rolling like water.

Every glyph gets its own sine offset — phase-shifted left to right — so the
line swells instead of bobbing as a block. Brightness rides the same wave and
a blurred copy lifts only where a glyph is cresting.

Usage:
    python3 tools/quote_svg.py --out quote.svg
"""
from __future__ import annotations

import argparse
import math
import os

BG = "#000000"
INK = "#FFFFFF"
ATTR = "#6B6B6B"

QUOTE = "simplicity is prerequisite for reliability."
CREDIT = "— EDSGER W. DIJKSTRA"

W = 781
H = 144
FS = 20.0
ADV = FS * 0.6
Y_Q = 68.0
Y_A = 98.0

PERIOD = 8.0     # seconds per swell
AMP = 2.8        # px of lift
PHASE = 0.34     # radians of delay per glyph
N = 24           # samples per cycle
FLOOR = 0.60     # dimmest a glyph gets
BLUR = 3.2


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def keytimes() -> str:
    return ";".join(f"{k / N:.5f}" for k in range(N + 1))


def glyphs(halo: bool) -> str:
    x0 = (W - len(QUOTE) * ADV) / 2
    times = keytimes()
    out = []
    for j, ch in enumerate(QUOTE):
        if ch == " ":
            continue
        phase = -j * PHASE
        ys, ops, gs = [], [], []
        for k in range(N + 1):
            s = math.sin(2 * math.pi * k / N + phase)
            ys.append(f"0 {-AMP * s:.2f}")
            ops.append(f"{FLOOR + (1 - FLOOR) * (s + 1) / 2:.3f}")
            gs.append(f"{max(0.0, s):.3f}")
        if halo:
            anim = (f'<animate attributeName="opacity" '
                    f'values="{";".join(gs)}" keyTimes="{times}" '
                    f'dur="{PERIOD:.3f}s" repeatCount="indefinite"/>')
            op = "0"
        else:
            anim = (f'<animate attributeName="opacity" '
                    f'values="{";".join(ops)}" keyTimes="{times}" '
                    f'dur="{PERIOD:.3f}s" repeatCount="indefinite"/>'
                    f'<animateTransform attributeName="transform" type="translate" '
                    f'values="{";".join(ys)}" keyTimes="{times}" '
                    f'dur="{PERIOD:.3f}s" repeatCount="indefinite"/>')
            op = "1"
        out.append(f'    <text class="q" x="{x0 + j * ADV:.1f}" y="{Y_Q:.0f}" '
                   f'opacity="{op}">{esc(ch)}{anim}</text>')
    return "\n".join(out)


def build(out_path: str) -> tuple[int, int]:
    x0 = (W - len(QUOTE) * ADV) / 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Quote: simplicity is prerequisite for reliability — Edsger W. Dijkstra">
<title>{esc(QUOTE)}</title>
<defs>
<filter id="soft" x="-4%" y="-120%" width="108%" height="340%">
  <feGaussianBlur stdDeviation="{BLUR}"/>
</filter>
</defs>
<rect width="{W}" height="{H}" fill="{BG}"/>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.0f}px;fill:{INK}}}
.q{{fill:{INK}}}
.attr{{font-size:9px;fill:{ATTR};letter-spacing:.18em}}
</style>
<g filter="url(#soft)" opacity=".34">
{glyphs(halo=True)}
</g>
{glyphs(halo=False)}
<text class="attr" x="{x0 + len(QUOTE) * ADV:.0f}" y="{Y_A:.0f}" text-anchor="end">{esc(CREDIT)}</text>
</svg>
"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return W, H


def main(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default="quote.svg")
    a = p.parse_args(argv)
    w, h = build(a.out)
    print(f"{a.out}: {len(QUOTE)} glyphs · {w}x{h}px · "
          f"{os.path.getsize(a.out) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
