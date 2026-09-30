#!/usr/bin/env python3
"""Generate the profile SVGs (header, cards, stack) in light and dark.

All text is converted to outlines (Instrument Serif, Geist, Geist Mono; SIL OFL),
so the SVGs need no font loading and make no external requests. The Vedetta tile
and the Blaze Labs lockup are the approved brand files, embedded unmodified.

Setup:  python3 -m venv .venv && .venv/bin/pip install fonttools uharfbuzz
Run:    BRAND_ROOT=<monorepo>/docs/brand FONT_DIR=<monorepo>/crates/documents/fonts \
        .venv/bin/python tools/build_assets.py
"""
import os
import re
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
MONO = "/Users/allangarbagnati/Blaze-PROD/blaze/.claude/worktrees/lead-p3"
BRAND = Path(os.environ.get("BRAND_ROOT", f"{MONO}/docs/brand"))
FONTS = Path(os.environ.get("FONT_DIR", f"{MONO}/crates/documents/fonts"))

# ---------------------------------------------------------------- palettes
LIGHT = dict(
    bg="#F7F5F0", raised="#FBFAF7", border="#D6D1C6", ink="#111214", sub="#5A5650",
    mute="#77726A", accent="#0E3B5E", faint="#D6D1C6", soft="#BDB7AB", mid="#9A9489",
    chip="#0E3B5E", chip_text="#F7F5F0", chip_line="#BDB7AB", chip_ink="#2A2926",
    sheen="#FFFFFF", sheen_op="0.7", tile_ring="#D6D1C6", lockup="ink",
)
DARK = dict(
    bg="#0B2336", raised="#0F2B42", border="#1D3D5A", ink="#F2EFE8", sub="#B0ABA1",
    mute="#A3AAAB", accent="#1E7EC8", faint="#1D3D5A", soft="#2C5273", mid="#3B6A90",
    chip="#154A73", chip_text="#F2EFE8", chip_line="#2C5273", chip_ink="#F2EFE8",
    sheen="#F2EFE8", sheen_op="0.09", tile_ring="#2C5273", lockup="paper",
)

# ---------------------------------------------------------------- text -> paths
_cache = {}


def _font(name):
    if name not in _cache:
        path = str(FONTS / name)
        tt = TTFont(path)
        face = hb.Face(hb.Blob.from_file_path(path))
        _cache[name] = (tt, tt.getGlyphSet(), tt.getGlyphOrder(), hb.Font(face), face.upem)
    return _cache[name]


def _num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def shape(fontfile, text, size, track=0.0):
    """Return (list of (glyphname, x, y-offset), advance width) in px."""
    tt, gs, order, hfont, upem = _font(fontfile)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(hfont, buf, {"kern": True, "liga": True})
    k = size / upem
    x = 0.0
    out = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        out.append((order[info.codepoint], x + pos.x_offset * k, pos.y_offset * k))
        x += pos.x_advance * k + track
    return out, x - track


def width(fontfile, text, size, track=0.0):
    return shape(fontfile, text, size, track)[1]


def text_path(fontfile, text, size, x, y, fill, track=0.0, anchor="start", extra=""):
    glyphs, w = shape(fontfile, text, size, track)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    _, gs, _, _, upem = _font(fontfile)
    k = size / upem
    pen = SVGPathPen(gs, ntos=_num)
    for name, gx, gy in glyphs:
        tp = TransformPen(pen, (k, 0, 0, -k, x + gx, y - gy))
        gs[name].draw(tp)
    return f'<path {extra} fill="{fill}" d="{pen.getCommands()}"/>'


def wrap(fontfile, text, size, maxw):
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if width(fontfile, trial, size) <= maxw:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


SERIF = "InstrumentSerif-Regular.ttf"
SANS = "Geist-Regular.ttf"
SANS_M = "Geist-Medium.ttf"
MONOF = "GeistMono-Regular.ttf"

# ---------------------------------------------------------------- brand assets
def tile_inner():
    svg = (BRAND / "vedetta/icon/icon-large.svg").read_text()
    return "".join(re.findall(r"<path[^>]*/>", svg))  # bg square + V. outlines, verbatim


def lockup(kind):
    svg = (BRAND / f"blaze-labs/final/readme/lockup-{kind}.svg").read_text()
    vb = re.search(r'viewBox="([^"]+)"', svg).group(1)
    fill = re.search(r'fill="([^"]+)"', svg).group(1)
    d = re.findall(r'<path d="([^"]+)"', svg)  # mark + wordmark, verbatim
    return vb, fill, d


def place_lockup(kind, x, y, h):
    vb, fill, d = lockup(kind)
    _, _, w, hh = map(float, vb.split())
    ww = h * w / hh
    return (f'<svg x="{_num(x)}" y="{_num(y)}" width="{_num(ww)}" height="{_num(h)}" viewBox="{vb}">'
            + "".join(f'<path fill="{fill}" d="{p}"/>' for p in d) + '</svg>'), ww


# ---------------------------------------------------------------- header
ANIM_CSS = """
.draw{stroke-dasharray:1 1;stroke-dashoffset:0;animation:draw 2.4s cubic-bezier(.45,0,.2,1) backwards}
@keyframes draw{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}
.fade{animation:fade 1.1s cubic-bezier(.2,.7,.2,1) backwards}
@keyframes fade{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}
.pop{animation:pop .6s ease-out backwards}
@keyframes pop{from{opacity:0}to{opacity:1}}
.ring{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1.8s ease-out 3.1s both}
@keyframes ring{0%{opacity:0;transform:scale(1)}1%{opacity:.7;transform:scale(1)}100%{opacity:0;transform:scale(4.2)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def header(t, name):
    W, H = 1200, 340
    ink, sub, mute = t["ink"], t["sub"], t["mute"]

    def line(d, colour, w, delay, op=1):
        return (f'<path pathLength="1" class="draw" style="animation-delay:{delay}s" d="{d}" '
                f'fill="none" stroke="{colour}" stroke-width="{w}" stroke-opacity="{op}" '
                f'stroke-linecap="butt" stroke-linejoin="round"/>')

    parts = []
    # relief: three ridges rising eastward (behind), faint to firm
    parts.append(line("M470 176 C560 168 650 138 730 116 C810 94 890 70 970 50 C1040 33 1110 28 1190 22",
                      t["faint"], 1.4, 0.15))
    parts.append(line("M470 206 C548 198 610 176 676 158 C740 141 810 126 880 102 C950 79 1010 66 1080 60 C1130 56 1165 52 1190 50",
                      t["soft"], 1.4, 0.35))
    parts.append(line("M470 232 C540 224 606 206 664 190 C700 180 730 170 760 160 C820 141 870 130 930 112 C990 94 1050 90 1110 84 C1145 81 1170 80 1190 79",
                      t["mid"], 1.5, 0.55))
    # the Rock: plateau silhouette
    parts.append(line("M698 250 C702 226 707 208 718 202 H746 C756 206 760 226 764 250", ink, 1.6, 1.1, 0.85))
    # coastline (the accent line): Fontvieille platform, the Rock, the harbour, Larvotto
    parts.append(line(
        "M470 250 H556 C574 250 576 264 594 264 H636 C652 264 652 250 668 250 H696 "
        "C702 250 706 270 730 270 C752 270 758 254 766 250 C782 244 794 226 816 226 "
        "C838 226 846 246 862 254 C872 259 880 256 886 250 H906 "
        "C936 250 952 238 984 238 H1012 C1044 238 1054 252 1086 252 H1190",
        t["accent"], 2.6, 0.8))
    # sea: three quiet lines
    for i, (yy, delay, col) in enumerate([(288, 1.7, t["soft"]), (306, 2.0, t["faint"]), (322, 2.3, t["faint"])]):
        d = f"M470 {yy} " + "".join("q30 -7 60 0 t60 0 " for _ in range(11)) + "t60 0"
        d = f"M470 {yy}" + " q30 -6 60 0" + " t60 0" * 11
        parts.append(line(d, col, 1.3, delay))
    # harbour marker
    parts.append(f'<circle class="pop" style="animation-delay:2.9s" cx="826" cy="240" r="5.5" fill="{t["accent"]}"/>')
    parts.append(f'<circle class="ring" cx="826" cy="240" r="5.5" fill="none" stroke="{t["accent"]}" stroke-width="1.6"/>')

    # text (outlines)
    lk, lw = place_lockup(t["lockup"], 64, 46, 19)
    name_svg = text_path(SERIF, "Allan Garbagnati", 88, 60, 172, ink, track=-1.2)
    role_svg = text_path(SANS, "Founder, Blaze Labs — Monaco", 25, 64, 222, sub, track=-0.2)
    coord_svg = text_path(MONOF, "43.7384° N   7.4246° E", 15, 64, 284, mute, track=1.2)

    css = ANIM_CSS
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Allan Garbagnati</title>
<desc id="d">Allan Garbagnati, founder of Blaze Labs, Monaco. A line drawing of the Monaco coast draws itself once.</desc>
<style>{css}</style>
<defs><linearGradient id="lg" gradientUnits="userSpaceOnUse" x1="566" x2="760" y1="0" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff"/></linearGradient><mask id="cut"><rect x="566" y="0" width="{W-566-1}" height="{H}" fill="url(#lg)"/></mask></defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="18" fill="{t["bg"]}" stroke="{t["border"]}"/>
<g class="fade" style="animation-delay:.1s">{lk}</g>
<g class="fade" style="animation-delay:.3s">{name_svg}</g>
<g class="fade" style="animation-delay:.6s">{role_svg}</g>
<g class="fade" style="animation-delay:.9s">{coord_svg}</g>
<g mask="url(#cut)">{"".join(parts)}</g>
</svg>
'''
    (OUT / f"header-{name}.svg").write_text(svg)


# ---------------------------------------------------------------- cards
CARDS = [
    dict(key="vedetta", kicker="WORKSPACE", title="Vedetta",
         body="AML/KYC workspace for Monaco firms: client files, screening, reports.",
         foot="Client data hosted in Monaco"),
    dict(key="lists", kicker="LISTS ENGINE", title="Vedetta Lists",
         body="Sanctions and PEP lists engine, built on 380+ official sources.",
         foot="Official sources first"),
    dict(key="pro", kicker="ON SITE", title="Vedetta Pro",
         body="Vedetta, installable at the bank.",
         foot="Runs inside the institution"),
]


def card(t, name, c, idx):
    W, H = 400, 236
    tile = tile_inner()
    body_lines = wrap(SANS, c["body"], 18, 340)
    assert len(body_lines) <= 2, body_lines
    body = "".join(text_path(SANS, ln, 18, 30, 152 + i * 25, t["sub"], track=-0.1) for i, ln in enumerate(body_lines))
    title = text_path(SERIF, c["title"], 40, 29, 118, t["ink"], track=-0.5)
    kicker = text_path(MONOF, c["kicker"], 13, W - 30, 52, t["mute"], track=1.5, anchor="end")
    foot = text_path(MONOF, c["foot"].upper(), 12.5, 30, 213, t["mute"], track=1.0)
    delay = idx * 2.6
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
<title id="t">{c["title"]}: {c["body"]}</title>
<style>
.sheen{{animation:sheen 10s linear infinite;animation-delay:{delay}s;transform:translateX(-260px)}}
@keyframes sheen{{0%{{transform:translateX(-260px)}}22%,100%{{transform:translateX(620px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<linearGradient id="g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="{t["sheen"]}" stop-opacity="0"/><stop offset=".5" stop-color="{t["sheen"]}" stop-opacity="{t["sheen_op"]}"/><stop offset="1" stop-color="{t["sheen"]}" stop-opacity="0"/></linearGradient>
<clipPath id="c"><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16"/></clipPath>
</defs>
<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="{t["raised"]}" stroke="{t["border"]}"/>
<svg x="30" y="28" width="46" height="46" viewBox="0 0 100 100">{tile}</svg>
<rect x="29.5" y="27.5" width="47" height="47" rx="10.5" fill="none" stroke="{t["tile_ring"]}" stroke-opacity=".9"/>
{kicker}{title}{body}
<path d="M30 190.5H{W-30}" stroke="{t["border"]}" stroke-width="1"/>
{foot}
<g clip-path="url(#c)"><g class="sheen"><rect x="0" y="-10" width="120" height="{H+20}" transform="skewX(-18)" fill="url(#g)"/></g></g>
</svg>
'''
    (OUT / f"card-{c['key']}-{name}.svg").write_text(svg)


# ---------------------------------------------------------------- stack
STACK = ["Rust", "PostgreSQL", "React", "TypeScript", "Linux", "Cloudflare", "Docker", "Swift"]
PRIMARY = 3  # Rust · PostgreSQL · React are the headline stack


def stack(t, name):
    W = 1200
    size, padx, gap, h = 21, 22, 14, 50
    widths = [width(SANS_M, s, size, -0.2) + padx * 2 for s in STACK]
    total = sum(widths) + gap * (len(STACK) - 1)
    x0 = (W - total) / 2
    H = h + 12
    els, x = [], x0
    for i, (s, w) in enumerate(zip(STACK, widths)):
        if i < PRIMARY:
            els.append(f'<rect x="{_num(x)}" y="6" width="{_num(w)}" height="{h}" rx="{h/2}" fill="{t["chip"]}"/>')
            col = t["chip_text"]
        else:
            els.append(f'<rect x="{_num(x+.5)}" y="6.5" width="{_num(w-1)}" height="{h-1}" rx="{(h-1)/2}" fill="none" stroke="{t["chip_line"]}"/>')
            col = t["chip_ink"]
        els.append(text_path(SANS_M, s, size, x + w / 2, 6 + h / 2 + 7.5, col, track=-0.2, anchor="middle"))
        x += w + gap
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
<title id="t">Stack: {", ".join(STACK)}</title>
{"".join(els)}
</svg>
'''
    (OUT / f"stack-{name}.svg").write_text(svg)
    return total


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, t in (("light", LIGHT), ("dark", DARK)):
        header(t, name)
        for i, c in enumerate(CARDS):
            card(t, name, c, i)
        print("stack row width", round(stack(t, name)))
    for p in sorted(OUT.glob("*.svg")):
        print(p.name, p.stat().st_size)
