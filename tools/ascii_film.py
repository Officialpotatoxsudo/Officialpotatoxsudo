#!/usr/bin/env python3
"""Bake a clip into a black-and-white ASCII filmstrip SVG.

ffmpeg -> centred crop -> grayscale cells -> character ramp -> one <g> per
frame, each with a single discrete visibility animation. No JS, no external
assets, no web fonts. Frame 0 stays visible when SMIL is unavailable, so
static renderers (email, RSS, link previews) get a real still.

Polarity is normalised per frame: Bad Apple flips between white and black
backgrounds, so every frame is forced onto black before it is ramped.

The clipped top row is trimmed and the grid is inset, so the film starts
on black instead of a permanent row of glyphs against the plate edge.

Usage:
    python3 tools/ascii_film.py --src badapple.mp4 --start 51 --dur 30
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

RAMP = " .:-=+*#%@"
FS = 12.0        # font-size, px
ADV = 7.2        # monospace advance, px (0.6em)
LH = 13.5        # line height, px
PAD = 16         # px padding around the grid
PAD_TOP = PAD + 4  # extra top inset: balances the top/bottom margins
TRIM_TOP = 1     # drop the clipped first character row
BG = "#000000"
INK = "#FFFFFF"
NBSP = "\u00a0"


def source_size(src: str) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", src],
        capture_output=True, text=True, check=True).stdout.strip()
    w, h = out.split("x")[:2]
    return int(w), int(h)


def crop_box(w: int, h: int, cols: int, rows: int, crop_y: float):
    """Crop to the aspect the character grid really has (cell is 0.6em wide)."""
    aspect = (cols * ADV) / (rows * LH)
    cw, ch = w, h
    if w / h > aspect:
        cw = int(round(h * aspect))
    else:
        ch = int(round(w / aspect))
    return cw, ch, (w - cw) // 2, int(round((h - ch) * crop_y))


def frames(src, start, dur, fps, cols, rows, crop_y):
    w, h = source_size(src)
    cw, ch, x, y = crop_box(w, h, cols, rows, crop_y)
    vf = (f"crop={cw}:{ch}:{x}:{y},fps={fps},"
          f"scale={cols}:{rows}:flags=area,format=gray")
    raw = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-ss", str(start), "-t", str(dur),
         "-i", src, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    size = cols * rows
    n = len(raw) // size
    if not n:
        sys.exit("ffmpeg produced no frames - check --start/--dur")
    for i in range(n):
        block = raw[i * size:(i + 1) * size]
        if sum(block) / size > 127.5:            # white-background frame
            block = bytes(255 - v for v in block)  # -> black background
        yield block


def rows_of(block, cols, rows) -> list[str]:
    return [
        "".join(RAMP[min(len(RAMP) - 1, v * len(RAMP) // 256)]
                for v in block[r * cols:(r + 1) * cols]).rstrip()
        for r in range(rows)
    ]


def frame_group(rows, cls, vis, animate, fps, total, gw, gh, indent="    "):
    # every frame repaints the black, so the always-visible frame 0 behind it
    # never ghosts through the gaps
    out = [f'{indent}<g class="{cls}" visibility="{vis}">',
           f'{indent}  <rect width="{gw:.0f}" height="{gh:.0f}" fill="{BG}"/>']
    if animate:
        out.append(
            f'{indent}  <animate attributeName="visibility" calcMode="discrete" '
            f'values="visible;hidden" keyTimes="0;{1.0 / (total * fps):.6f}" '
            f'dur="{total:.3f}s" begin="{animate / fps:.3f}s" '
            f'repeatCount="indefinite"/>')
    for r, row in enumerate(rows):
        if row:
            out.append(f'{indent}  <text x="0" y="{r * LH:.1f}">'
                       f'{row.replace(" ", NBSP)}</text>')
    out.append(f"{indent}</g>")
    return "\n".join(out)


def build(frames_rows, cols, rows, fps, out_path):
    n = len(frames_rows)
    total = n / fps
    gw, gh = cols * ADV, rows * LH
    cw, ch = gw + 2 * PAD, gh + 2 * PAD

    # The top row is the clipped edge of the source crop; blanking it keeps
    # the plate's top black instead of a permanent rule of glyphs.
    def trimmed(fr):
        return [""] * TRIM_TOP + fr[TRIM_TOP:]

    # frame 0 never animates: it is the fallback when SMIL is unavailable,
    # and every later frame repaints the black over it.
    film = "\n".join(
        frame_group(trimmed(fr), f"f{i}", "visible" if i == 0 else "hidden", i,
                    fps, total, gw, gh)
        for i, fr in enumerate(frames_rows))

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{cw:.0f}" height="{ch:.0f}" viewBox="0 0 {cw:.0f} {ch:.0f}" role="img" aria-label="Bad Apple!! rendered as ASCII art">
<title>Bad Apple!! in ASCII</title>
<rect width="100%" height="100%" fill="{BG}"/>
<style>
text{{font-family:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;font-size:{FS:.0f}px;fill:{INK}}}
.still{{display:none}}
@media (prefers-reduced-motion:reduce){{.film{{display:none}}.still{{display:block}}}}
</style>
<g class="film" transform="translate({PAD},{PAD_TOP})">
{film}
</g>
<g class="still" transform="translate({PAD},{PAD_TOP})">
{frame_group(trimmed(frames_rows[0]), "still", "visible", None, fps, total, gw, gh)}
</g>
</svg>
"""
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    return cw, ch, n, total


def main(argv):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", required=True)
    p.add_argument("--start", type=float, default=51.0, help="seconds into source")
    p.add_argument("--dur", type=float, default=30.0, help="seconds of film")
    p.add_argument("--fps", type=float, default=10.0, help="loop frame rate")
    p.add_argument("--cols", type=int, default=104)
    p.add_argument("--rows", type=int, default=26)
    p.add_argument("--crop-y", type=float, default=0.5, help="0=top 1=bottom")
    p.add_argument("--out", default="badapple.svg")
    a = p.parse_args(argv)

    all_rows = [rows_of(b, a.cols, a.rows) for b in
                frames(a.src, a.start, a.dur, a.fps, a.cols, a.rows, a.crop_y)]
    cw, ch, n, total = build(all_rows, a.cols, a.rows, a.fps, a.out)
    glyphs = sum(len(r) for fr in all_rows for r in fr[TRIM_TOP:])
    print(f"{a.out}: {n} frames · {total:.1f}s @ {a.fps:g}fps · "
          f"{cw:.0f}x{ch:.0f}px · {glyphs:,} glyphs · "
          f"{os.path.getsize(a.out) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
