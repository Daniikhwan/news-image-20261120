#!/usr/bin/env python3
"""Render the world news of Friday 20 November 2026 as one infographic.

Pure standard library, no network, fully deterministic: two runs write
byte-identical PNG files. Writes to $MAKEFUN_OUTPUT_DIR/entry.png
(default ./out/entry.png).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 bits, "#" = on, "." = off.
FONT = {
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "*": ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}

CHAR_W, CHAR_H = 6, 7  # advance width and glyph height in font units


def text_width(text, scale):
    return len(text) * CHAR_W * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines."""
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, t=1):
        self.rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.rect(x0 - t // 2, y0 - t // 2, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d2 <= r * r:
                        self.set(xx, yy, color)
                else:
                    if abs(d2 - r * r) <= r * 2:
                        self.set(xx, yy, color)

    def arc(self, cx, cy, r, a0, a1, color, t=2):
        import math
        steps = max(8, int(r * 3))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            x = int(cx + r * math.cos(a))
            y = int(cy + r * math.sin(a))
            self.rect(x - t // 2, y - t // 2, t, t, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += CHAR_W * scale
        return cx

    def text_center(self, y, s, scale, color):
        x = (self.w - text_width(s, scale)) // 2
        self.text(x, y, s, scale, color)


# ---------------------------------------------------------------- PNG encode
def png_bytes(canvas):
    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- palette
INK = bytes((11, 21, 38))          # page background
PANEL = bytes((22, 35, 58))        # panel background
PANEL2 = bytes((30, 46, 74))       # icon tile background
WHITE = bytes((245, 247, 250))
MUTE = bytes((176, 190, 208))
GOLD = bytes((240, 196, 80))
PINK = bytes((255, 93, 162))
RED = bytes((231, 76, 60))
CYAN = bytes((51, 198, 255))
ORANGE = bytes((255, 140, 66))
GREEN = bytes((46, 204, 113))
AMBER = bytes((212, 160, 23))

# ---------------------------------------------------------------- stories
# (tag, accent, headline <=8 words, summary <=12 words, icon key)
STORIES = [
    ("CULTURE", PINK, "GTA VI PASSES $2.36 BILLION",
     "24.6m copies in under 24 hours", "city"),
    ("WEATHER", ORANGE, "CYCLONE AKVAN HITS INDIA",
     "Landfall near Gopalpur, 50,000 moved", "storm"),
    ("CLIMATE", GREEN, "COP31 CLOSING DAY IN ANTALYA",
     "Fossil-free draft faces final test", "globe"),
    ("DIPLOMACY", RED, "TRUMP, PUTIN ISSUE PEACE STATEMENT",
     "Joint text after Shenzhen, omits Ukraine", "flags"),
    ("SPORT", CYAN, "NICHOLLS 113 PUTS NZ ON TOP",
     "NZ 243 for 5, day 2 in Wellington", "bat"),
    ("ENERGY", AMBER, "GULF REFINERY RESTARTS",
     "Bapco restarts after strikes", "flame"),
]


def icon_city(cv, x, y, s, accent):
    # Neon skyline with sun over Vice City.
    cv.circle(x + s - 14, y + 22, 13, GOLD)
    base = y + s - 8
    for bx, bw, bh in ((0, 18, 46), (22, 14, 66), (40, 20, 38),
                       (64, 14, 58), (82, 18, 30)):
        cv.rect(x + bx, base - bh, bw, bh, accent)
    cv.rect(x, base, s, 8, WHITE)
    for wx, wy in ((5, base - 34), (27, base - 54), (47, base - 26),
                   (69, base - 46), (87, base - 20)):
        cv.rect(x + wx, wy, 5, 5, GOLD)


def icon_flags(cv, x, y, s, accent):
    # Three leaders: three overlapping discs.
    cols = (bytes((70, 130, 230)), bytes((222, 41, 16)), bytes((0, 120, 215)))
    for i, c in enumerate(cols):
        cx = x + 24 + i * 28
        cv.circle(cx, y + 48, 20, c)
        cv.circle(cx, y + 48, 20, WHITE, fill=False)
    cv.line(x + 8, y + 86, x + s - 8, y + 86, WHITE, 4)


def icon_dish(cv, x, y, s, accent):
    # Deep-space dish beaming at a star field.
    for sx, sy in ((12, 12), (30, 6), (52, 16), (86, 8), (96, 26), (70, 4)):
        cv.rect(x + sx, y + sy, 3, 3, WHITE)
    cv.arc(x + 50, y + 58, 30, 3.5, 5.9, WHITE, 5)
    cv.line(x + 50, y + 58, x + 50, y + 88, WHITE, 4)
    cv.line(x + 34, y + 88, x + 66, y + 88, WHITE, 4)
    cv.circle(x + 88, y + 18, 5, GOLD)


def icon_storm(cv, x, y, s, accent):
    # Cyclone spiral with rain.
    import math
    for r, a0 in ((10, 0.0), (20, 1.2), (30, 2.4), (40, 3.6)):
        cv.arc(x + 50, y + 46, r, a0, a0 + 3.6, accent, 5)
    for dx in (8, 34, 60, 86):
        cv.line(x + dx, y + 88, x + dx - 6, y + 98, CYAN, 3)


def icon_moon(cv, x, y, s, accent):
    # Crescent moon and star.
    cv.circle(x + 48, y + 50, 34, GOLD)
    cv.circle(x + 62, y + 40, 30, PANEL2)
    cv.text(x + 76, y + 66, "*", 3, WHITE)


def icon_globe(cv, x, y, s, accent):
    # Earth with a wedge of missing time.
    cv.circle(x + 50, y + 50, 38, bytes((46, 134, 193)))
    cv.circle(x + 50, y + 50, 38, WHITE, fill=False)
    cv.rect(x + 50, y + 12, 38, 10, GREEN)
    cv.rect(x + 14, y + 62, 34, 10, GREEN)
    # Missing wedge: cut a gap in the lower right of the globe.
    for i in range(20):
        cv.line(x + 50 + i, y + 52 + i // 2, x + 50 + i, y + 52 + 20, PANEL2, 2)


def icon_bat(cv, x, y, s, accent):
    # Cricket bat and ball.
    cv.line(x + 30, y + 82, x + 72, y + 22, WHITE, 10)
    cv.rect(x + 66, y + 14, 16, 14, accent)
    cv.circle(x + 24, y + 78, 9, RED)
    cv.circle(x + 24, y + 78, 9, WHITE, fill=False)


def icon_flame(cv, x, y, s, accent):
    # Flame over an oil drop.
    cv.line(x + 50, y + 12, x + 78, y + 52, accent, 5)
    cv.line(x + 78, y + 52, x + 64, y + 52, accent, 5)
    cv.line(x + 64, y + 52, x + 74, y + 72, accent, 5)
    cv.line(x + 74, y + 72, x + 50, y + 88, accent, 5)
    cv.line(x + 50, y + 88, x + 28, y + 70, accent, 5)
    cv.line(x + 28, y + 70, x + 40, y + 56, accent, 5)
    cv.line(x + 40, y + 56, x + 50, y + 12, accent, 5)
    cv.circle(x + 50, y + 62, 10, GOLD)


ICONS = {"city": icon_city, "flags": icon_flags, "dish": icon_dish,
         "storm": icon_storm, "moon": icon_moon, "globe": icon_globe,
         "bat": icon_bat, "flame": icon_flame}


def draw_panel(cv, x, y, w, h, story):
    tag, accent, headline, summary, icon = story
    cv.rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, 8, accent)
    # Icon tile.
    cv.rect(x + 16, y + 26, 100, 100, PANEL2)
    ICONS[icon](cv, x + 16, y + 26, 100, accent)
    # Tag + headline + summary.
    tx = x + 132
    tw = w - 132 - 16
    cv.text(tx, y + 28, tag, 2, accent)
    lines = wrap_text(headline, 3, tw)
    yy = y + 52
    for ln in lines[:2]:
        cv.text(tx, yy, ln, 3, WHITE)
        yy += 26
    lines = wrap_text(summary, 2, tw)
    yy += 4
    for ln in lines[:3]:
        cv.text(tx, yy, ln, 2, MUTE)
        yy += 18


def render():
    cv = Canvas(W, H, INK)
    cv.rect(0, 0, W, 10, GOLD)
    cv.text_center(34, "FRIDAY 20 NOVEMBER 2026", 5, WHITE)
    cv.text_center(96, "THE WORLD IN ONE DAY", 3, GOLD)
    cv.hline(212, 140, 600, GOLD, 3)
    # Grid: 2 cols x 3 rows.
    pw, ph, gap = 480, 240, 16
    x0, y0 = 24, 168
    for i, story in enumerate(STORIES):
        px = x0 + (i % 2) * (pw + gap)
        py = y0 + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, story)
    cv.text_center(960, "SOURCES: REUTERS - AP - IMD - SENSOR TOWER - UNFCCC - DEADLINE",
                   2, MUTE)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "./out")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
