#!/usr/bin/env python3
"""Friday 20 November 2026 - The World in One Day.

A make.fun news-image-20261120 entry. Pure Python 3 standard library:
draws a 1024x1024 newspaper-style infographic summing up the six biggest
world stories of Friday 20 November 2026 and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default ./out/entry.png).

The run is deterministic: two runs write byte-identical PNG files.
No network, no third-party packages, no system fonts - the glyphs below
are a hand-built 5x7 bitmap font and the PNG encoder is hand-rolled
with zlib.
"""

import math
import os
import struct
import zlib

# --------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 cells, '#' = ink, '.' = blank.
# --------------------------------------------------------------------------

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".###.", "#....", "#....", "#...#", ".###."),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "###..", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "\u2022": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}

CELL_W, CELL_H = 6, 7  # advance width and glyph height, in font units


def measure(text, scale):
    """Pixel width of text at the given scale."""
    return len(text) * CELL_W * scale


def wrap(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if measure(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --------------------------------------------------------------------------
# Raster: a plain RGB canvas with small drawing helpers.
# --------------------------------------------------------------------------

class Raster:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bg * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = color

    def fill(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            base = yy * self.w * 3 + x0 * 3
            for xx in range(x0, x1):
                self.buf[base:base + 3] = color
                base += 3

    def border(self, x, y, w, h, color, t=2):
        self.fill(x, y, w, t, color)
        self.fill(x, y + h - t, w, t, color)
        self.fill(x, y, t, h, color)
        self.fill(x + w - t, y, t, h, color)

    def rule_h(self, x, y, w, color, t=1):
        self.fill(x, y, w, t, color)

    def rule_v(self, x, y, h, color, t=1):
        self.fill(x, y, t, h, color)

    def segment(self, x0, y0, x1, y1, color, t=2):
        """Bresenham line with a square brush of width t."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        half = t // 2
        while True:
            self.fill(x - half, y - half, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def dot(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, color)

    def circ(self, cx, cy, r, color, t=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= (r + 1) ** 2:
                    self.put(xx, yy, color)

    def curve(self, cx, cy, r, start, end, color, t=2):
        steps = max(8, int(abs(end - start) * r))
        for i in range(steps + 1):
            a = start + (end - start) * i / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.fill(x - t // 2, y - t // 2, t, t, color)

    def glyphs(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            rows = GLYPHS.get(ch, GLYPHS[" "])
            for row in range(CELL_H):
                bits = rows[row]
                for col in range(5):
                    if bits[col] == "#" or bits[col] == "1":
                        self.fill(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += CELL_W * scale
        return cx

    def centred(self, y, s, scale, color):
        x = (self.w - measure(s, scale)) // 2
        return self.glyphs(x, y, s, scale, color)


# --------------------------------------------------------------------------
# PNG writer: 8-bit RGB, filter 0, zlib level 9. Deterministic output.
# --------------------------------------------------------------------------

def encode_png(raster):
    def block(kind, data):
        size = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return size + kind + data + crc

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", raster.w, raster.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = raster.w * 3
    for y in range(raster.h):
        raw.append(0)
        raw += raster.buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return sig + block(b"IHDR", ihdr) + block(b"IDAT", idat) + block(b"IEND", b"")


# --------------------------------------------------------------------------
# Palette: cream newsprint, ink navy, one accent per story.
# --------------------------------------------------------------------------

PAPER = bytes((250, 246, 236))
CARD = bytes((255, 255, 255))
INK = bytes((18, 24, 38))
NAVY = bytes((16, 32, 64))
SOFT = bytes((90, 100, 118))
GOLD = bytes((196, 148, 44))
WHITE = bytes((245, 247, 250))
RUST = bytes((178, 58, 44))
TEAL = bytes((15, 118, 110))
SKY = bytes((37, 99, 235))
VIOLET = bytes((109, 40, 217))
FOREST = bytes((21, 101, 52))
AMBER = bytes((180, 83, 9))

W, H = 1024, 1024


# --------------------------------------------------------------------------
# Pictograms, one per story. Each draws inside a square tile of side s
# whose top-left corner is (x, y); accent is the story's colour.
# --------------------------------------------------------------------------

def pic_scales(cv, x, y, s, accent):
    cx = x + s // 2
    cv.rule_v(cx - 2, y + 12, 62, INK, 4)               # post
    cv.segment(x + 8, y + 22, x + s - 8, y + 22, INK, 4)  # beam
    cv.fill(cx - 16, y + 74, 32, 6, INK)                # base
    for px in (x + 12, x + s - 34):                      # pans
        cv.segment(px + 2, y + 22, px + 11, y + 40, INK, 3)
        cv.segment(px + 20, y + 22, px + 11, y + 40, INK, 3)
        cv.segment(px, y + 40, px + 22, y + 40, accent, 4)
        cv.dot(px + 11, y + 44, 3, accent)


def pic_clock(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2 - 8
    cv.circ(cx, cy, 28, INK, 4)
    cv.dot(cx, cy, 4, accent)
    cv.segment(cx, cy, cx - 2, cy - 20, INK, 4)          # to 11
    cv.segment(cx, cy, cx + 15, cy + 7, INK, 4)          # to 4
    for k in range(12):                                  # ticks
        a = k * math.pi / 6
        x0 = int(cx + 23 * math.cos(a))
        y0 = int(cy + 23 * math.sin(a))
        cv.fill(x0 - 1, y0 - 1, 3, 3, INK)
    cv.glyphs(x + 14, y + s - 16, "2027", 2, accent)


def pic_spiral(cv, x, y, s, accent):
    cx, cy = x + s // 2, y + s // 2 - 8
    for r, a0 in ((9, 0.0), (17, 1.1), (25, 2.2), (33, 3.3)):
        cv.curve(cx, cy, r, a0, a0 + 3.8, accent, 5)
    cv.dot(cx, cy, 5, INK)
    for dx in (10, 32, 54, 76):                          # rain
        cv.segment(x + dx, y + s - 16, x + dx - 5, y + s - 6, SKY, 3)


def pic_probe(cv, x, y, s, accent):
    cx = x + s // 2
    for sx, sy in ((12, 10), (30, 5), (54, 12), (80, 7), (88, 26)):
        cv.fill(x + sx, y + sy, 3, 3, INK)
    cv.curve(cx, y + 52, 30, 3.6, 5.8, INK, 5)           # dish
    cv.segment(cx, y + 52, cx, y + 84, INK, 4)           # mast
    cv.segment(cx - 16, y + 84, cx + 16, y + 84, INK, 4)
    cv.curve(cx + 26, y + 26, 14, -0.9, 0.9, accent, 3)  # signal
    cv.curve(cx + 26, y + 26, 22, -0.9, 0.9, accent, 3)
    cv.dot(x + 84, y + 16, 5, GOLD)


def pic_talks(cv, x, y, s, accent):
    cv.fill(x + 8, y + 14, 52, 34, SKY)                  # left bubble
    cv.segment(x + 16, y + 48, x + 24, y + 62, SKY, 5)
    cv.fill(x + 34, y + 44, 52, 34, accent)              # right bubble
    cv.segment(x + 70, y + 78, x + 62, y + 92, accent, 5)
    for dx in (20, 32, 44):
        cv.dot(x + dx, y + 31, 4, WHITE)
    for dx in (46, 58, 70):
        cv.dot(x + dx, y + 61, 4, WHITE)


def pic_pad(cv, x, y, s, accent):
    cv.fill(x + 10, y + 30, 72, 36, INK)                 # body
    cv.dot(x + 10, y + 48, 18, INK)
    cv.dot(x + 82, y + 48, 18, INK)
    cv.fill(x + 24, y + 42, 6, 16, WHITE)                # d-pad
    cv.fill(x + 19, y + 47, 16, 6, WHITE)
    for dx, dy in ((62, 40), (72, 48), (62, 56), (52, 48)):
        cv.dot(x + dx, y + dy, 4, accent)
    cv.fill(x + 38, y + 22, 16, 5, GOLD)                 # start bar


ICONS = {"scales": pic_scales, "clock": pic_clock, "spiral": pic_spiral,
         "probe": pic_probe, "talks": pic_talks, "pad": pic_pad}


# --------------------------------------------------------------------------
# The six stories: (category, accent, headline, summary, source, icon).
# Facts as reported on 20 November 2026.
# --------------------------------------------------------------------------

STORIES = [
    ("JUSTICE", RUST, "MYANMAR GUILTY OF GENOCIDE",
     "The UN court rules Myanmar committed genocide against the Rohingya "
     "in 2017, the first state ever held responsible. About 10,000 killed; "
     "reparations ordered.",
     "UN News - Reuters", "scales"),
    ("UNITED STATES", SKY, "TRUMP DELAYS IRAN CALL TO 2027",
     "The president says there is 'no rush' on Iran and he will 'see what "
     "happens' after Jan 1, pushing any war decision into next year.",
     "Reuters", "clock"),
    ("INDIA", TEAL, "CYCLONE AKVAN: 300,000 FLEE",
     "Severe Cyclonic Storm Akvan bears down on Odisha. Schools shut and "
     "423 rescue teams deploy as landfall nears.",
     "The Hindu", "spiral"),
    ("SPACE", VIOLET, "VOYAGER 1, ONE LIGHT-DAY OUT",
     "NASA confirms the 1977 probe has reached one light-day from Earth, "
     "some 16 billion miles, the farthest human object ever.",
     "NASA", "probe"),
    ("EUROPE", FOREST, "EUROPE READY FOR RUSSIA TALKS",
     "European leaders say they are ready to talk with Moscow about ending "
     "the war in Ukraine, as diplomacy stirs again.",
     "BBC", "talks"),
    ("GAMES", AMBER, "GTA 6 SALES TOP $1.8 BILLION",
     "The Vice City return has already outgrossed The Odyssey's global run, "
     "days after launch ends a 13-year wait.",
     "Mezha", "pad"),
]

ALSO = ("Also: Hayabusa2 drops its asteroid landing after engine trouble - "
        "Houthis strike a Riyadh tower - Tanker ablaze after hitting a "
        "mine near Hormuz")


def draw_card(cv, x, y, w, h, num, story):
    tag, accent, headline, summary, source, icon = story
    cv.fill(x, y, w, h, CARD)
    cv.border(x, y, w, h, INK, 2)
    cv.fill(x, y, 8, h, accent)                          # accent spine
    tx = x + 24
    tw = w - 24 - 116
    cv.glyphs(tx, y + 20, "%d. %s" % (num, tag), 2, accent)
    lines = wrap(headline, 3, tw)
    yy = y + 48
    for ln in lines[:2]:
        cv.glyphs(tx, yy, ln, 3, INK)
        yy += 25
    yy += 2
    for ln in wrap(summary, 2, tw)[:6]:
        cv.glyphs(tx, yy, ln, 2, SOFT)
        yy += 17
    cv.glyphs(tx, y + h - 26, source, 2, accent)
    # Icon tile on the right.
    ix, iy = x + w - 104, y + 22
    cv.fill(ix, iy, 88, 88, PAPER)
    cv.border(ix, iy, 88, 88, INK, 2)
    ICONS[icon](cv, ix, iy, 88, accent)


def render():
    cv = Raster(W, H, PAPER)
    # Masthead.
    cv.fill(0, 0, W, 148, NAVY)
    cv.rule_h(0, 148, W, GOLD, 4)
    cv.centred(26, "THE WORLD IN ONE DAY", 5, WHITE)
    cv.centred(96, "FRIDAY - 20 NOVEMBER 2026", 3, GOLD)
    # Cards: 2 columns x 3 rows.
    cw, ch, gap = 480, 236, 16
    x0, y0 = 24, 172
    for i, story in enumerate(STORIES):
        px = x0 + (i % 2) * (cw + gap)
        py = y0 + (i // 2) * (ch + gap)
        draw_card(cv, px, py, cw, ch, i + 1, story)
    # Footer strip.
    fy = y0 + 3 * ch + 2 * gap + 16
    cv.fill(0, fy, W, H - fy, NAVY)
    cv.rule_h(0, fy, W, GOLD, 3)
    ly = fy + 16
    for ln in wrap(ALSO, 2, W - 64)[:2]:
        cv.glyphs(32, ly, ln, 2, WHITE)
        ly += 17
    cv.glyphs(32, fy + 64, "Sources: Reuters, BBC, UN News, The Hindu, NASA, "
             "Space.com, Mezha", 2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "./out")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
