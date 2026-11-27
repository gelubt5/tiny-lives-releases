"""ToonEngine episode v2 — "De unde vine sarmaua?" in the documentary silhouette style
(silueta.Figure characters, muted painted backgrounds, haze, film grain, comic exclamations).

python3 ep2_sarmale.py [scene ...] [--preview]   -> out2/sc_XX.mp4
"""
import os, sys, math, random, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "engine"))
sys.path.insert(0, HERE)
import numpy as np
from toonengine import Scene, Camera, cairo  # noqa
from silueta import Figure

OUT = os.path.join(HERE, "out2")
NAR = os.path.join(HERE, os.environ.get("NAR_DIR", "nar"))
W, H = 1280, 720
GR = 0.84
GY = H * GR
PAD = 0.9
COMIC, SERIF, ROUND = "Bangers", "Cinzel", "Baloo 2"


def nar_len(i):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        os.path.join(NAR, f"n{i:02d}.wav")], capture_output=True, text=True)
    return float(r.stdout.strip())


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ painting helpers (no ink outlines)
def grad(ctx, stops, y0=0, y1=H, x=None):
    g = cairo.LinearGradient(0, y0, 0, y1)
    for p, c in stops:
        g.add_color_stop_rgb(p, *rgb(c))
    ctx.set_source(g)
    if x is None:
        ctx.paint()
    else:
        ctx.rectangle(*x)
        ctx.fill()


def glow(ctx, x, y, r, col, a=1.0):
    c = rgb(col)
    g = cairo.RadialGradient(x, y, 0, x, y, r)
    g.add_color_stop_rgba(0, *c, a)
    g.add_color_stop_rgba(0.25, *c, a * 0.55)
    g.add_color_stop_rgba(1, *c, 0)
    ctx.set_source(g)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def disc(ctx, x, y, r, col, a=1.0):
    ctx.set_source_rgba(*rgb(col), a)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()


def rect(ctx, x, y, w, h, col, a=1.0):
    ctx.rectangle(x, y, w, h)
    ctx.set_source_rgba(*rgb(col), a)
    ctx.fill()


def ridge(ctx, base, amp, col, seed=1, a=1.0, step=24):
    r = random.Random(seed)
    ph = [r.uniform(0, 6) for _ in range(3)]
    ctx.move_to(0, H)
    for x in range(0, W + step, step):
        y = base - amp * (0.6 * math.sin(x / 230 + ph[0]) + 0.3 * math.sin(x / 90 + ph[1]) + 0.15 * math.sin(x / 31 + ph[2]))
        ctx.line_to(x, y)
    ctx.line_to(W, H)
    ctx.close_path()
    ctx.set_source_rgba(*rgb(col), a)
    ctx.fill()


def haze(ctx, y, h, col, a):
    c = rgb(col)
    g = cairo.LinearGradient(0, y - h, 0, y + h)
    g.add_color_stop_rgba(0, *c, 0)
    g.add_color_stop_rgba(0.5, *c, a)
    g.add_color_stop_rgba(1, *c, 0)
    ctx.set_source(g)
    ctx.rectangle(0, y - h, W, 2 * h)
    ctx.fill()


def trees(ctx, base, col, seed=3, n=60, hmin=20, hmax=46, a=1.0):
    r = random.Random(seed)
    ctx.set_source_rgba(*rgb(col), a)
    for _ in range(n):
        x = r.uniform(-20, W + 20)
        h = r.uniform(hmin, hmax)
        w = h * 0.38
        ctx.move_to(x, base - h)
        ctx.line_to(x + w, base + 2)
        ctx.line_to(x - w, base + 2)
        ctx.close_path()
        ctx.fill()


def plaster(ctx, x, y, w, h, col, seed=4, a=0.07):
    rect(ctx, x, y, w, h, col)
    r = random.Random(seed)
    for _ in range(int(w * h / 900)):
        px, py = r.uniform(x, x + w), r.uniform(y, y + h)
        ctx.set_source_rgba(0, 0, 0, r.uniform(0, a))
        ctx.arc(px, py, r.uniform(4, 22), 0, 2 * math.pi)
        ctx.fill()


def text(ctx, s, x, y, size, col="#f4ecd8", outline="#1d1a21", font=COMIC, a=1.0, rot=0.0, lw=0.13,
         anchor="c", shadow=True):
    ctx.save()
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    e = ctx.text_extents(s)
    ctx.translate(x, y)
    ctx.rotate(rot)
    tx = {"c": -e.width / 2, "l": 0, "r": -e.width}[anchor] - e.x_bearing
    ty = -e.y_bearing - e.height / 2
    if shadow:
        ctx.move_to(tx + size * 0.05, ty + size * 0.07)
        ctx.text_path(s)
        ctx.set_source_rgba(0, 0, 0, 0.35 * a)
        ctx.fill()
    ctx.move_to(tx, ty)
    ctx.text_path(s)
    if outline:
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_source_rgba(*rgb(outline), a)
        ctx.set_line_width(size * lw)
        ctx.stroke_preserve()
    ctx.set_source_rgba(*rgb(col), a)
    ctx.fill()
    ctx.restore()


_GRAIN = {}


def grain(ctx, now, a=0.09):
    if "p" not in _GRAIN:
        rng = np.random.default_rng(7)
        n = 256
        v = rng.integers(0, 255, (n, n), dtype=np.uint8)
        al = np.full((n, n), int(255 * a), dtype=np.uint8)
        arr = np.zeros((n, n, 4), dtype=np.uint8)
        pm = (v.astype(np.uint16) * al // 255).astype(np.uint8)
        arr[..., 0] = arr[..., 1] = arr[..., 2] = pm
        arr[..., 3] = al
        surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, n, n, n * 4)
        _GRAIN["arr"], _GRAIN["s"] = arr, surf
        p = cairo.SurfacePattern(surf)
        p.set_extend(cairo.EXTEND_REPEAT)
        _GRAIN["p"] = p
    k = int(now * 24)
    r = random.Random(k)
    m = cairo.Matrix()
    m.translate(r.uniform(0, 256), r.uniform(0, 256))
    _GRAIN["p"].set_matrix(m)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_OVERLAY)
    ctx.set_source(_GRAIN["p"])
    ctx.paint()
    ctx.restore()


def vignette(ctx, a=0.55):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, H * 0.95)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.04, 0.02, 0.05, a)
    ctx.set_source(g)
    ctx.paint()


def world(ctx, cam):
    """Switch a screen-space context to ToonEngine world space (same transform as the engine)."""
    ctx.translate(W / 2, GY)
    ctx.scale(cam.zoom, cam.zoom)
    ctx.translate(-cam.x, cam.y)


# ------------------------------------------------------------------ props (world space, y up = negative)
def table(ctx, x, w, h=86, cloth="#d9cfba", motif="#8e3a2c", wood="#2e211d"):
    for lx in (x - w / 2 + 14, x + w / 2 - 22):
        rect(ctx, lx, -h, 9, h, wood)
    rect(ctx, x - w / 2 - 8, -h - 8, w + 16, 40, cloth)
    rect(ctx, x - w / 2 - 8, -h - 8, w + 16, 5, "#efe7d6", 0.6)
    ctx.set_source_rgb(*rgb(motif))
    for i in range(int((w + 16) / 22)):
        xx = x - w / 2 - 4 + i * 22
        ctx.move_to(xx, -h + 20)
        ctx.line_to(xx + 7, -h + 13)
        ctx.line_to(xx + 14, -h + 20)
        ctx.line_to(xx + 7, -h + 27)
        ctx.close_path()
    ctx.fill()


def pot(ctx, x, y, now, s=1.0, col="#7a4630", steam=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if steam:
        for i in range(3):
            ph = (now * 0.5 + i / 3) % 1
            ctx.set_source_rgba(1, 1, 1, 0.32 * (1 - ph) * min(1, ph * 4))
            ctx.set_line_width(6)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            bx = -16 + i * 16
            ctx.move_to(bx, -62 - ph * 70)
            ctx.curve_to(bx + 10, -72 - ph * 70, bx - 10, -92 - ph * 70, bx, -104 - ph * 70)
            ctx.stroke()
    for i, (sx, sy) in enumerate([(-24, -56), (0, -60), (24, -56), (-12, -66), (12, -66)]):
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1, 0.6)
        ctx.arc(0, 0, 14, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*rgb("#6f7a3a" if i % 2 else "#808c45"))
        ctx.fill()
    ctx.move_to(-48, -52)
    ctx.curve_to(-52, -4, -40, 0, 0, 0)
    ctx.curve_to(40, 0, 52, -4, 48, -52)
    ctx.close_path()
    g = cairo.LinearGradient(-48, 0, 48, 0)
    c = rgb(col)
    g.add_color_stop_rgb(0, *[v * 0.7 for v in c])
    g.add_color_stop_rgb(0.4, *c)
    g.add_color_stop_rgb(1, *[v * 0.55 for v in c])
    ctx.set_source(g)
    ctx.fill()
    rect(ctx, -52, -58, 104, 9, "#5e3324")
    ctx.set_source_rgba(*rgb("#e7c87a"), 0.8)
    for i in range(7):
        ctx.arc(-30 + i * 10, -30, 2.6, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()


def mamaliga(ctx, x, y):
    ctx.save()
    ctx.translate(x, y)
    ctx.save()
    ctx.scale(1, 0.24)
    ctx.arc(0, 0, 44, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*rgb("#bdb3a2"))
    ctx.fill()
    ctx.move_to(-30, -3)
    ctx.curve_to(-32, -42, 32, -42, 30, -3)
    ctx.close_path()
    g = cairo.LinearGradient(-30, 0, 30, 0)
    g.add_color_stop_rgb(0, *rgb("#c98f22"))
    g.add_color_stop_rgb(0.45, *rgb("#e8b13c"))
    g.add_color_stop_rgb(1, *rgb("#b07a1c"))
    ctx.set_source(g)
    ctx.fill()
    ctx.restore()


def candle(ctx, x, y, now):
    rect(ctx, x - 4, y - 30, 8, 30, "#e5dccb")
    f = 1 + 0.15 * math.sin(now * 17 + x)
    glow(ctx, x, y - 40, 70, "#ffc46b", 0.35)
    ctx.save()
    ctx.translate(x, y - 38)
    ctx.scale(1, 1.6 * f)
    disc(ctx, 0, 0, 5, "#ffd88a")
    ctx.restore()


def skyline(ctx, base, col, seed=3, a=1.0):
    r = random.Random(seed)
    ctx.set_source_rgba(*rgb(col), a)
    x = -40
    while x < W + 40:
        w = r.uniform(60, 150)
        h = r.uniform(30, 80)
        ctx.rectangle(x, base - h, w, h + 400)
        ctx.fill()
        if r.random() < 0.7:
            cx, rr = x + w / 2, w * 0.33
            ctx.arc(cx, base - h, rr, math.pi, 2 * math.pi)
            ctx.fill()
            ctx.rectangle(cx - 1.5, base - h - rr - 14, 3, 14)
            ctx.fill()
        if r.random() < 0.35:
            mx, mh = x + w + 8, r.uniform(140, 220)
            ctx.rectangle(mx, base - mh, 10, mh)
            ctx.fill()
            ctx.move_to(mx - 2, base - mh)
            ctx.line_to(mx + 5, base - mh - 30)
            ctx.line_to(mx + 12, base - mh)
            ctx.fill()
            ctx.rectangle(mx - 4, base - mh * 0.72, 18, 5)
            ctx.fill()
            x += 30
        x += w + r.uniform(-10, 20)


def window(ctx, x, y, w, h, top, bot, frame="#2a1f1d", moon=True, snow=0.0, now=0.0):
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    grad(ctx, [(0, top), (1, bot)], y, y + h)
    if moon:
        glow(ctx, x + w * 0.65, y + h * 0.3, w * 0.7, "#f2ead0", 0.3)
        disc(ctx, x + w * 0.65, y + h * 0.3, w * 0.12, "#f2ead0")
    if snow:
        r = random.Random(5)
        for _ in range(40):
            sx = x + (r.uniform(0, w) + now * 8) % w
            sy = y + (r.uniform(0, h) + now * r.uniform(20, 40)) % h
            disc(ctx, sx, sy, r.uniform(1, 2.4), "#ffffff", 0.7)
    ctx.restore()
    ctx.set_source_rgb(*rgb(frame))
    ctx.set_line_width(10)
    ctx.rectangle(x, y, w, h)
    ctx.stroke()
    ctx.set_line_width(6)
    ctx.move_to(x + w / 2, y)
    ctx.line_to(x + w / 2, y + h)
    ctx.move_to(x, y + h / 2)
    ctx.line_to(x + w, y + h / 2)
    ctx.stroke()


def stergar(ctx, x, y, w, h):
    rect(ctx, x, y, w, h, "#ddd3bf")
    for k in (0.12, 0.82):
        rect(ctx, x, y + h * k, w, h * 0.08, "#8e3a2c")
    ctx.set_source_rgb(*rgb("#8e3a2c"))
    for i in range(int(w / 12)):
        ctx.rectangle(x + i * 12 + 3, y + h - 6, 4, 12)
    ctx.fill()


# ------------------------------------------------------------------ backgrounds (screen space)
def bg_home(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#4a3a36", 4, 0.12)
    for bx in (0, 300, 980):  # beams
        rect(ctx, bx, 0, 34, GY, "#2b201d")
    rect(ctx, 0, 0, W, 40, "#2b201d")
    window(ctx, W / 2 - 80, 110, 160, 170, "#18213a", "#3a4a72", snow=1, now=now)
    rect(ctx, 130, 130, 70, 90, "#7a5a2a")
    rect(ctx, 140, 140, 50, 70, "#3a2420")
    disc(ctx, 165, 162, 12, "#c9a24a")
    stergar(ctx, 110, 118, 110, 28)
    stergar(ctx, 1060, 200, 34, 160)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e221e")
    for i in range(0, W, 80):
        rect(ctx, i, GY, 2, H - GY, "#000000", 0.25)
    glow(ctx, W / 2, GY - 120, 560, "#ffb15e", 0.20 + 0.02 * math.sin(now * 9))


def bg_word(ctx, cam, now):
    grad(ctx, [(0, "#3b3647"), (0.55, "#b9785a"), (0.85, "#d79a68")])
    glow(ctx, W * 0.5, GY - 60, 430, "#ffdca0", 0.55)
    ridge(ctx, GY - 120, 40, "#7c5a5c", 4, 0.8)
    haze(ctx, GY - 90, 60, "#d9a27a", 0.45)
    ridge(ctx, GY - 50, 30, "#5d4446", 9)
    trees(ctx, GY - 48, "#4b3738", 9, 50, 14, 30)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#4a3630")
    a = smooth((now - 1.0) / 0.6)
    if a > 0:
        text(ctx, "SARMAK", W / 2, 120, 96, "#efd9a0", outline=None, font=SERIF, a=a)
        b = smooth((now - 2.6) / 0.5)
        if b > 0:
            text(ctx, "= a înfășura", W / 2, 195, 40, "#f4ecd8", outline=None, font=SERIF, a=b)
    c = smooth((now - 11.4) / 0.5)
    if c > 0:
        text(ctx, "DOLMA", W * 0.8, 300, 58, "#e9b9a0", outline=None, font=SERIF, a=c)
        text(ctx, "= umplut", W * 0.8, 352, 30, "#f4ecd8", outline=None, font=SERIF, a=c)


def bg_palace(ctx, cam, now):
    grad(ctx, [(0, "#2f4a52"), (1, "#22363c")], 0, GY)
    ctx.set_source_rgba(*rgb("#e3d6b8"), 0.10)
    for j in range(0, int(GY), 48):
        for i in range(0, W, 48):
            ctx.save()
            ctx.translate(i + 24 + (24 if (j // 48) % 2 else 0), j + 24)
            ctx.rotate(math.pi / 4)
            ctx.rectangle(-9, -9, 18, 18)
            ctx.restore()
    ctx.fill()
    for x in (150, W - 310):  # arched openings to the city
        ctx.save()
        ctx.move_to(x, 380)
        ctx.line_to(x, 170)
        ctx.arc(x + 80, 170, 80, math.pi, 2 * math.pi)
        ctx.line_to(x + 160, 380)
        ctx.close_path()
        ctx.clip()
        grad(ctx, [(0, "#9fbfc4"), (1, "#e9d2a8")], 90, 380)
        skyline(ctx, 360, "#8f7f86", 7 + x, 0.8)
        skyline(ctx, 390, "#6d5f68", 3 + x)
        ctx.restore()
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#3a2a24")
    glow(ctx, W / 2, GY - 40, 330, "#ff8a3a", 0.33 + 0.05 * math.sin(now * 9))


def bg_market(ctx, cam, now):
    grad(ctx, [(0, "#2a2840"), (0.45, "#7d4e66"), (0.75, "#d08a62"), (1, "#d08a62")])
    glow(ctx, W * 0.7, GY - 200, 320, "#ffd9a0", 0.6)
    skyline(ctx, GY - 90, "#6a4a62", 11, 0.7)
    haze(ctx, GY - 90, 70, "#c98a70", 0.4)
    skyline(ctx, GY - 30, "#3f2c40", 4)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#3f2e2c")
    c = smooth((now - 0.8) / 0.6)
    if c:
        text(ctx, "1555", W * 0.83, 95, 64, "#efd9a0", outline=None, font=SERIF, a=c)
        text(ctx, "ISTANBUL", W * 0.83, 145, 24, "#f4ecd8", outline=None, font=SERIF, a=c)


def bg_map(ctx, cam, now):
    z = 1.0 + 0.06 * min(1, now / 17)  # slow push-in
    ctx.save()
    ctx.translate(W / 2, H / 2)
    ctx.scale(z, z)
    ctx.translate(-W / 2, -H / 2)
    # sea with hatched waves
    rect(ctx, 0, 0, W, H, "#8d948f")
    ctx.set_source_rgba(*rgb("#5e6763"), 0.6)
    ctx.set_line_width(1.6)
    for j in range(0, H, 14):
        for i in range(-30, W, 60):
            ox = (j * 7) % 60
            ctx.move_to(i + ox, j)
            ctx.curve_to(i + ox + 10, j - 4, i + ox + 20, j + 4, i + ox + 30, j)
    ctx.stroke()
    land = "#d9c49a"

    def blob(pts):
        ctx.move_to(*pts[0])
        for k in range(1, len(pts)):
            x0, y0 = pts[k - 1]
            x1, y1 = pts[k]
            ctx.curve_to(x0 + (x1 - x0) * 0.4, y0 - 6, x1 - (x1 - x0) * 0.4, y1 + 6, x1, y1)
        ctx.close_path()
    # Balkans + Carpathian land (stylised)
    blob([(0, 0), (W, 0), (W, 250), (1050, 260), (980, 220), (900, 240), (880, 330), (820, 380),
          (760, 360), (720, 430), (650, 470), (600, 560), (540, 600), (500, 560), (430, 520),
          (360, 470), (300, 420), (220, 380), (120, 360), (0, 380)])
    ctx.set_source_rgb(*rgb(land))
    ctx.fill()
    blob([(760, 500), (900, 470), (1050, 480), (W, 470), (W, H), (720, H), (700, 600)])  # Anatolia
    ctx.set_source_rgb(*rgb(land))
    ctx.fill()
    # coast shading
    ctx.set_source_rgba(0.35, 0.28, 0.2, 0.25)
    ctx.set_line_width(3)
    # Danube
    ctx.set_source_rgb(*rgb("#6f8790"))
    ctx.set_line_width(5)
    ctx.move_to(60, 210)
    ctx.curve_to(260, 170, 420, 300, 560, 290)
    ctx.curve_to(700, 280, 800, 300, 880, 300)
    ctx.stroke()
    # mountains (Carpathians, Balkans)
    def mount(x, y, s=1.0):
        ctx.move_to(x - 14 * s, y)
        ctx.line_to(x, y - 20 * s)
        ctx.line_to(x + 14 * s, y)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#8a7556"))
        ctx.fill()
        ctx.move_to(x, y - 20 * s)
        ctx.line_to(x + 14 * s, y)
        ctx.line_to(x + 3 * s, y)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#6e5c42"))
        ctx.fill()
    for (mx, my) in [(520, 150), (548, 160), (600, 120), (640, 95), (660, 70), (450, 175), (480, 170),
                     (480, 380), (520, 390), (560, 385), (600, 392)]:
        mount(mx, my)
    for (tx, ty) in [(300, 120), (330, 140), (760, 120), (800, 150), (380, 300), (250, 300)]:
        disc(ctx, tx, ty, 6, "#7a8a5a")
    # Ottoman spread from Istanbul
    ix, iy = 830, 470
    p = smooth((now - 1.5) / 7.5)
    ctx.save()
    blob([(0, 0), (W, 0), (W, 250), (1050, 260), (980, 220), (900, 240), (880, 330), (820, 380),
          (760, 360), (720, 430), (650, 470), (600, 560), (540, 600), (500, 560), (430, 520),
          (360, 470), (300, 420), (220, 380), (120, 360), (0, 380)])
    blob([(760, 500), (900, 470), (1050, 480), (W, 470), (W, H), (720, H), (700, 600)])
    ctx.clip()
    g = cairo.RadialGradient(ix, iy, 0, ix, iy, 60 + 560 * p)
    g.add_color_stop_rgba(0, *rgb("#8e2a22"), 0.45)
    g.add_color_stop_rgba(0.85, *rgb("#8e2a22"), 0.35)
    g.add_color_stop_rgba(1, *rgb("#8e2a22"), 0.0)
    ctx.set_source(g)
    ctx.paint()
    ctx.restore()
    # dashed arrow Istanbul -> Danube
    q = smooth((now - 3.5) / 3.0)
    if q:
        ctx.set_source_rgba(*rgb("#7a1f1a"), 0.9)
        ctx.set_line_width(4)
        ctx.set_dash([12, 8])
        ctx.move_to(ix, iy)
        ex, ey = ix + (560 - ix) * q, iy + (300 - iy) * q
        ctx.curve_to(ix - 80 * q, iy - 60 * q, ex + 60 * q, ey + 80 * q, ex, ey)
        ctx.stroke()
        ctx.set_dash([])
    # Istanbul pin (crescent)
    disc(ctx, ix, iy, 13, "#7a1f1a")
    disc(ctx, ix + 3, iy - 2, 9, "#d9c49a")
    disc(ctx, ix + 7, iy - 3, 8, "#7a1f1a")
    text(ctx, "Istanbul", ix + 10, iy + 34, 26, "#3a2a20", outline=None, font=SERIF, shadow=False)
    text(ctx, "Dunărea", 300, 262, 20, "#3f5560", outline=None, font=SERIF, shadow=False, rot=0.08)
    text(ctx, "MAREA NEAGRĂ", 1010, 340, 22, "#4a524e", outline=None, font=SERIF, shadow=False)
    r2 = smooth((now - 7.5) / 0.8)
    if r2:
        text(ctx, "ȚARA ROMÂNEASCĂ", 360, 165, 26, "#3a2a20", outline=None, font=SERIF, a=r2, shadow=False)
        text(ctx, "MOLDOVA", 760, 140, 26, "#3a2a20", outline=None, font=SERIF, a=r2, shadow=False)
    ctx.restore()
    # parchment edge darkening
    vignette(ctx, 0.5)
    t = smooth((now - 11.0) / 0.4) * smooth((17.5 - now) / 0.4)
    if t:
        text(ctx, "TRIBUT LA POARTĂ", W / 2, H - 70, 54, "#f4ecd8", a=t, rot=-0.03)


def bg_village(ctx, cam, now):
    grad(ctx, [(0, "#8fa9b4"), (0.65, "#e0d2b4"), (1, "#e0d2b4")])
    glow(ctx, W * 0.18, 120, 220, "#fff1cf", 0.6)
    ridge(ctx, GY - 150, 50, "#8f9a88", 5, 0.7)
    haze(ctx, GY - 120, 60, "#e8dcc0", 0.5)
    ridge(ctx, GY - 80, 30, "#6e7f62", 9)
    trees(ctx, GY - 78, "#55664a", 2, 70, 16, 34)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#56603e")


def bg_oven(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#c8b897", 6, 0.08)
    rect(ctx, 0, GY - 70, W, 70, "#3c4f66")  # blue painted plinth
    rect(ctx, 0, 0, W, 34, "#2b201d")
    stergar(ctx, 520, 70, 120, 26)
    rect(ctx, 545, 96, 70, 84, "#6a4a22")
    rect(ctx, 553, 104, 54, 68, "#3a2420")
    disc(ctx, 580, 128, 11, "#c9a24a")
    rect(ctx, 120, 70, 220, 130, "#6e2622")  # wall rug
    for i in range(6):
        rect(ctx, 132 + i * 35, 80, 16, 110, "#c9a24a" if i % 2 else "#2f4a5e")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#4a362a")


def bg_balkans(ctx, cam, now):
    grad(ctx, [(0, "#2c2c44"), (0.6, "#7a5a72"), (0.9, "#c98f70")])
    glow(ctx, W / 2, GY - 70, 400, "#ffcf9a", 0.45)
    ridge(ctx, GY - 120, 60, "#5a4660", 12, 0.85)
    haze(ctx, GY - 90, 60, "#b98a80", 0.4)
    ridge(ctx, GY - 50, 25, "#3e3044", 13)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e2430")
    c = smooth((now - 9.0) / 0.6)
    if c:
        ctx.save()
        ctx.translate(W - 200, 130)
        ctx.rotate(0.03)
        rect(ctx, -130, -60, 260, 120, "#d9c49a", c)
        text(ctx, "UNESCO", 0, -15, 44, "#3a2a20", outline=None, font=SERIF, a=c, shadow=False)
        text(ctx, "2017 · DOLMA", 0, 32, 24, "#7a1f1a", outline=None, font=SERIF, a=c, shadow=False)
        ctx.restore()


def bg_fest(ctx, cam, now):
    grad(ctx, [(0, "#8fb0c0"), (0.7, "#e6dcc4"), (1, "#e6dcc4")])
    ridge(ctx, GY - 150, 70, "#88998c", 21, 0.8)
    haze(ctx, GY - 110, 60, "#ece2c8", 0.5)
    ridge(ctx, GY - 70, 35, "#62775a", 22)
    trees(ctx, GY - 66, "#4d5f45", 4, 50, 16, 32)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#58653e")
    cols = ["#9e3a2e", "#d0a548", "#3e5f7a"]
    for row, y in enumerate((36, 84)):
        ctx.set_source_rgb(*rgb("#2a2224"))
        ctx.set_line_width(1.5)
        ctx.move_to(0, y)
        ctx.curve_to(W / 3, y + 36, 2 * W / 3, y + 36, W, y)
        ctx.stroke()
        for i in range(24):
            t = i / 23
            x = t * W
            yy = y + 36 * 3 * t * (1 - t) + math.sin(now * 3 + i) * 1.5
            ctx.move_to(x - 12, yy)
            ctx.line_to(x + 12, yy)
            ctx.line_to(x, yy + 22)
            ctx.close_path()
            ctx.set_source_rgb(*rgb(cols[(i + row) % 3]))
            ctx.fill()
    c = smooth((now - 0.6) / 0.5)
    if c:
        text(ctx, "FESTIVALUL SARMALELOR", W / 2, 165, 56, "#f4ecd8", a=c)
        text(ctx, "PRAID", W / 2, 225, 30, "#efd9a0", outline=None, font=SERIF, a=c)


# ------------------------------------------------------------------ world props per scene
def fg_home(ctx, cam, now):
    table(ctx, 0, 400)
    pot(ctx, 0, -94, now, 1.1)
    mamaliga(ctx, -125, -94)
    mamaliga(ctx, 125, -94)
    candle(ctx, -180, -94, now)
    candle(ctx, 180, -94, now)


def fg_word(ctx, cam, now):
    table(ctx, -150, 200, cloth="#c9b893", motif="#3f5f4a")
    for i in range(3):
        ctx.save()
        ctx.translate(-215 + i * 44, -98)
        ctx.scale(1, 0.42)
        disc(ctx, 0, 0, 20, "#56763a")
        ctx.restore()
    pot(ctx, -100, -94, now, 0.6, steam=False, col="#6a5a7a")


def fg_palace(ctx, cam, now):
    rect(ctx, -95, -78, 190, 78, "#3a2d2b")
    rect(ctx, -95, -78, 190, 6, "#5a4642")
    for i in range(6):
        fl = 26 + 14 * math.sin(now * 12 + i * 1.7)
        ctx.move_to(-62 + i * 25, -78)
        ctx.line_to(-52 + i * 25, -78 - fl)
        ctx.line_to(-42 + i * 25, -78)
        ctx.set_source_rgba(*rgb("#ffb04a" if i % 2 else "#ff6a2b"), 0.9)
        ctx.fill()
    pot(ctx, 0, -78, now, 1.05, col="#8a6a3a")
    table(ctx, 330, 200, cloth="#d9cfba", motif="#2f5a66")
    for i in range(6):
        ctx.save()
        ctx.translate(262 + i * 26, -96)
        ctx.scale(1, 0.55)
        disc(ctx, 0, 0, 12, "#6c7f3e")
        ctx.restore()


def stall(ctx, x, w, awning="#8e3a2c"):
    for lx in (x - w / 2, x + w / 2 - 8):
        rect(ctx, lx, -165, 8, 165, "#2e221e")
    rect(ctx, x - w / 2, -68, w, 68, "#5a3e2c")
    for i in range(int(w / 40)):
        ctx.move_to(x - w / 2 + i * 40, -165)
        ctx.line_to(x - w / 2 + i * 40 + 40, -165)
        ctx.line_to(x - w / 2 + i * 40 + 20, -138)
        ctx.close_path()
        ctx.set_source_rgb(*rgb(awning if i % 2 else "#d6c9ad"))
        ctx.fill()


def fg_market(ctx, cam, now):
    stall(ctx, 250, 240)
    for i in range(9):
        ctx.save()
        ctx.translate(160 + (i % 5) * 42, -76 - (i // 5) * 15)
        ctx.scale(1, 0.55)
        disc(ctx, 0, 0, 19, "#4a6a30" if i % 2 else "#5f7f3c")
        ctx.restore()
    stall(ctx, -340, 200, "#2f5a66")
    for i in range(6):
        disc(ctx, -410 + i * 26, -82, 10, "#8aa040")


def fg_village(ctx, cam, now):
    x = -280
    rect(ctx, x - 150, -165, 300, 165, "#d8cfbd")
    rect(ctx, x - 150, -36, 300, 36, "#3c4f66")
    ctx.move_to(x - 185, -160)
    ctx.line_to(x, -295)
    ctx.line_to(x + 185, -160)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#6a5434"))
    ctx.fill()
    ctx.set_source_rgba(0, 0, 0, 0.12)
    for i in range(12):
        ctx.move_to(x - 170 + i * 30, -160)
        ctx.line_to(x - 20 + i * 3, -280)
    ctx.set_line_width(2)
    ctx.stroke()
    rect(ctx, x - 110, -128, 56, 56, "#2f3a4a")
    rect(ctx, x + 40, -136, 58, 136, "#4a3426")
    for i in range(14):
        rect(ctx, 60 + i * 30, -68, 13, 68, "#5e4632")
    rect(ctx, 50, -54, 430, 7, "#4e3826")
    ctx.save()  # barrel of sauerkraut
    ctx.translate(250, 0)
    rect(ctx, -44, -98, 88, 98, "#6e4a2c")
    for yy in (-84, -22):
        rect(ctx, -46, yy, 92, 7, "#2e221e")
    for i in range(4):
        ctx.save()
        ctx.translate(-26 + i * 17, -101)
        ctx.scale(1, 0.5)
        disc(ctx, 0, 0, 15, "#c8cf96")
        ctx.restore()
    ctx.restore()
    bob = math.sin(now * 5)
    ctx.save()  # pig (muted)
    ctx.translate(420, -38 + bob * 0.6)
    ctx.save()
    ctx.scale(1.4, 1)
    disc(ctx, 0, 0, 29, "#d9a0a4")
    ctx.restore()
    disc(ctx, 40, -10, 19, "#d9a0a4")
    disc(ctx, 55, -6, 7.5, "#c4848a")
    disc(ctx, 42, -18, 3.5, "#1d1a21")
    for lx in (-25, -8, 12, 26):
        rect(ctx, lx, 22, 7, 17, "#c98e94")
    ctx.restore()


def fg_oven(ctx, cam, now):
    ctx.move_to(130, 0)
    ctx.line_to(130, -150)
    ctx.curve_to(130, -260, 420, -260, 420, -150)
    ctx.line_to(420, 0)
    ctx.close_path()
    g = cairo.LinearGradient(130, 0, 420, 0)
    g.add_color_stop_rgb(0, *rgb("#b39c78"))
    g.add_color_stop_rgb(0.5, *rgb("#d0bb94"))
    g.add_color_stop_rgb(1, *rgb("#a28a66"))
    ctx.set_source(g)
    ctx.fill()
    ctx.move_to(215, -40)
    ctx.line_to(215, -110)
    ctx.arc(275, -110, 60, math.pi, 2 * math.pi)
    ctx.line_to(335, -40)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#24120e"))
    ctx.fill()
    glow(ctx, 275, -80, 130, "#ff8a2b", 0.5 + 0.1 * math.sin(now * 8))
    pot(ctx, 275, -40, now, 0.72)
    for sx, lab, col in [(-380, "GRÂU", "#c9b68c"), (-270, "ORZ", "#bba87c")]:
        ctx.move_to(sx - 40, 0)
        ctx.curve_to(sx - 50, -80, sx - 20, -110, sx, -110)
        ctx.curve_to(sx + 20, -110, sx + 50, -80, sx + 40, 0)
        ctx.close_path()
        ctx.set_source_rgb(*rgb(col))
        ctx.fill()
        text(ctx, lab, sx, -48, 20, "#4a3422", outline=None, font=SERIF, shadow=False)


def fg_balkans(ctx, cam, now):
    table(ctx, 0, 250)
    pot(ctx, 0, -94, now)


def fg_fest(ctx, cam, now):
    ctx.set_source_rgb(*rgb("#2a2224"))
    ctx.set_line_width(8)
    for dx in (-110, 110):
        ctx.move_to(0, -270)
        ctx.line_to(dx, 0)
    ctx.stroke()
    for i in range(6):
        fl = 28 + 16 * math.sin(now * 11 + i)
        ctx.move_to(-60 + i * 24, 0)
        ctx.line_to(-50 + i * 24, -fl)
        ctx.line_to(-40 + i * 24, 0)
        ctx.set_source_rgba(*rgb("#ffb04a" if i % 2 else "#ff6a2b"), 0.9)
        ctx.fill()
    glow(ctx, 0, -30, 120, "#ff9a4a", 0.35)
    pot(ctx, 0, -60, now, 2.0, col="#3a3a40")


# ------------------------------------------------------------------ engine glue
class Painted:
    """ToonEngine World: painted background + world props behind the figures; grain, vignette and
    comic exclamations over everything."""
    preset = "custom"

    def __init__(self, back, props=None, vig=0.5, light="#000000", light_a=0.0):
        self.back, self.props, self.vig = back, props, vig
        self.light, self.light_a = light, light_a
        self.pops = []  # (t, d, text, x, y, size, rot, col)

    def pop(self, t, d, s, x, y, size=58, rot=-0.05, col="#f4ecd8"):
        self.pops.append((t, d, s, x, y, size, rot, col))
        return self

    def draw(self, ctx, W_, H_, cam, gy, now):
        globals()[self.back](ctx, cam, now)
        if self.props:
            ctx.save()
            world(ctx, cam)
            globals()[self.props](ctx, cam, now)
            ctx.restore()

    def draw_foreground(self, ctx, W_, H_, cam, gy, now):
        if self.light_a:
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
            ctx.set_source_rgba(*rgb(self.light), self.light_a)
            ctx.paint()
            ctx.restore()
        if self.vig:
            vignette(ctx, self.vig)
        grain(ctx, now)
        for t, d, s, x, y, size, rot, col in self.pops:
            if t <= now <= t + d:
                k = (now - t) / 0.22
                sc = 1.0 + 0.25 * math.sin(min(1, k) * math.pi) if k < 1 else 1.0
                a = min(1, k * 2, (t + d - now) / 0.2)
                ctx.save()
                ctx.translate(x, y)
                ctx.scale(sc * min(1, 0.6 + k), sc * min(1, 0.6 + k))
                text(ctx, s, 0, 0, size, col, a=a, rot=rot)
                ctx.restore()


class Anchor:
    def __init__(self, x):
        self.x, self.ground_y = x, 0.0


def make(back, D, zoom=1.3, props=None, vig=0.5, push=0.06, **kw):
    world_ = Painted(back, props, vig, **kw)
    sc = Scene(W, H, fps=30, duration=D, world=world_, ground_ratio=GR, bubbles=False)
    sc.music = False
    # slow documentary push-in (camera keys every 0.4 s)
    n = int(D / 0.4) + 1
    for i in range(n):
        t = i * 0.4
        sc.camera.at(t, [Anchor(0.0)], zoom * (1 + push * t / D))
    return sc, world_


def add(sc, fig):
    sc.extras.append(fig)
    return fig


def sx(x, zoom=1.3):
    return W / 2 + x * zoom


def head_y(zoom=1.3, s=1.0):
    return GY - 270 * zoom * s


K = "#1d1a21"
IE = "#d6cdb9"   # ie (white shirt)


def ion(x, face=1):
    return Figure(x=x, face=face, shirt=IE, band="#8e2a22", belt="#8e2a22", hat="cusma", mustache=True,
                  name="Ion")


def bunica(x, face=1):
    return Figure(x=x, face=face, shirt=IE, band="#2f4a66", skirt="#2a2228", apron="#8e2a22",
                  hat="basma", hat_color="#6e2420", hair="bun", scale=0.94, name="Bunica")


def copil(x, face=1):
    return Figure(x=x, face=face, shirt=IE, band="#8e2a22", belt="#2f4a66", scale=0.7, name="Ionut")


def turc(x, face=1, sash="#8e2a22", vest="#2f4a66", name="Bucatar"):
    return Figure(x=x, face=face, hat="turban", belt=sash, vest=vest, shirt="#cfc5b0", mustache=True,
                  apron="#d6cdb9", name=name)


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make("bg_home", D, 1.3, "fg_home", 0.6)
    a, b, c = add(sc, ion(-290)), add(sc, bunica(290, -1)), add(sc, copil(-400))
    c.do("jump", 0.6, 0.55).do("raise", 0.6, 1.6).feel("happy", 0.6, 1.8).talk(0.7, 0.8)
    w.pop(0.7, 1.6, "SARMALE!", sx(-400), head_y(1.3, 0.7) - 30, 54, -0.08)
    a.do("offer", 1.0, 1.8).feel("happy", 1.0, 1.8)
    b.do("nod", 1.2, 1.0)
    a.do("think", 6.3, 2.6)
    a.look(6.3, 2.6, 0.3, -0.8)
    b.do("shrug", 9.5, 1.8).talk(9.6, 1.0)
    w.pop(9.6, 1.9, "NU CHIAR...", sx(290), head_y(1.3) - 20, 46, 0.05)
    c.feel("surprised", 10.0, 1.8)
    a.feel("surprised", 10.2, 1.6).do("shock", 10.2, 1.4)
    w.pop(D - 3.6, 3.4, "DE UNDE VINE SARMAUA?", W / 2, 120, 70, -0.02, "#efd9a0")
    return sc


def s1(D):
    sc, w = make("bg_word", D, 1.3, "fg_word", 0.5)
    t = add(sc, turc(60, -1))
    t.do("wave", 0.3, 1.2).do("point", 1.8, 2.0).talk(1.9, 0.9)
    t.do("stir", 4.5, 5.0)
    t.do("point", 11.3, 2.0).talk(11.4, 0.8)
    t.do("laugh", 15.0, 1.6).feel("happy", 15.0, 1.6)
    return sc


def s2(D):
    sc, w = make("bg_palace", D, 1.3, "fg_palace", 0.55)
    a = add(sc, turc(-230, 1, name="B1"))
    b = add(sc, turc(395, -1, "#2f4a66", "#8e2a22", name="B2"))
    sult = add(sc, Figure(x=-700, face=1, hat="crown", shirt="#5a2a3a", belt="#c9a24a", vest="#2a2a44",
                          beard=True, name="Sultan"))
    a.do("stir", 0.5, 3.0)
    b.do("clap", 0.8, 1.8)
    sult.walk(3.0, 3.0, -420).do("point", 6.4, 1.6).feel("happy", 6.4, 2.0)
    a.turn(6.0, -1).do("bow", 6.6, 1.4)
    b.do("bow", 6.8, 1.4)
    sult.do("eat", 8.5, 3.0).feel("happy", 8.5, 3.5)
    w.pop(9.0, 1.6, "MMM!", sx(-420) - 40, head_y() - 20, 50, -0.1)
    return sc


def s3(D):
    sc, w = make("bg_market", D, 1.3, "fg_market", 0.55)
    d = add(sc, Figure(x=-680, face=1, hat="beret", beard=True, shirt="#2c2a34", belt="#5a3a22",
                       vest="#3a2a22", name="Dernschwam"))
    v = add(sc, turc(110, -1, "#3f6a4a", "#5a3a22", name="Negustor"))
    d.walk(0.2, 4.0, -150)
    v.do("wave", 1.0, 1.2)
    d.do("think", 5.0, 2.4)
    v.do("offer", 7.5, 3.0).talk(7.6, 1.4)
    d.do("eat", 9.0, 2.0)
    d.feel("surprised", 13.0, 2.4).do("shock", 13.0, 1.6).talk(13.1, 0.9)
    w.pop(13.1, 2.2, "CU PRUNE?!", sx(-150), head_y() - 25, 58, -0.06)
    v.do("nod", 13.8, 1.4).feel("happy", 13.8, 2.0)
    return sc


def s4(D):
    sc, w = make("bg_map", D, 1.3, None, 0.0, push=0.0)
    return sc


def s5(D):
    sc, w = make("bg_village", D, 1.3, "fg_village", 0.4)
    t = add(sc, turc(-560, 1))
    b = add(sc, bunica(80, -1))
    t.walk(0.2, 2.2, -130).do("point", 2.5, 1.2)
    b.do("hips", 1.6, 2.4).talk(1.7, 1.0).feel("angry", 1.6, 1.6)
    w.pop(1.7, 1.8, "STAI PUȚIN!", sx(80) + 30, head_y(1.3, 0.94) - 30, 56, 0.05)
    t.feel("surprised", 1.9, 1.4)
    b.walk(5.6, 1.6, 330).do("point", 7.4, 1.6)
    t.feel("surprised", 8.0, 2.0).do("shock", 8.0, 1.8).talk(8.1, 0.8)
    w.pop(8.2, 1.8, "PORC?!", sx(-130), head_y() - 20, 58, -0.07)
    b.turn(11.6, -1).do("laugh", 11.7, 1.6).feel("happy", 11.7, 1.8)
    b.walk(13.6, 1.4, 180).do("point", 15.1, 1.4)
    w.pop(15.2, 1.8, "VARZĂ MURATĂ!", sx(250), head_y() + 10, 44, 0.04)
    return sc


def s6(D):
    sc, w = make("bg_oven", D, 1.3, "fg_oven", 0.55)
    b = add(sc, bunica(-60, -1))
    k = add(sc, copil(-210, 1))
    b.do("point", 0.8, 2.4).talk(0.9, 1.0)
    k.look(1.0, 2.0, -1, 0)
    b.turn(5.6, 1).walk(6.0, 1.2, 60).do("stir", 7.4, 3.6)
    k.do("jump", 7.0, 0.55).feel("happy", 7.0, 2.2)
    b.do("nod", 11.4, 1.4)
    k.do("raise", 13.2, 1.8).feel("happy", 13.2, 2.0)
    w.pop(13.3, 1.8, "ABIA AȘTEPT!", sx(-210), head_y(1.3, 0.7) - 30, 46, -0.06)
    return sc


def s7(D):
    sc, w = make("bg_balkans", D, 1.06, "fg_balkans", 0.55)
    cast = [
        Figure(x=-470, face=1, hat="turban", belt="#8e2a22", vest="#2f4a66", mustache=True, name="T"),
        Figure(x=-320, face=1, hat="cusma", hat_color="#3a3028", shirt=IE, band="#2a6a4a", belt="#2a6a4a", name="B"),
        Figure(x=250, face=-1, hat="sajkaca", shirt=IE, band="#2f4a66", belt="#8e2a22", mustache=True, name="S"),
        Figure(x=370, face=-1, hat="clop", shirt=IE, band="#8e2a22", belt="#3a5a8a", name="C"),
        Figure(x=490, face=-1, hat="fez", hat_color="#2a2a3a", shirt="#d9d2c2", vest="#2f4a66", beard=True, name="G"),
    ]
    lines = ["A NOASTRĂ!", "BA A NOASTRĂ!", "BA NU!", "A MEA!", "BA A MEA!"]
    zoom = 1.06
    for i, c in enumerate(cast):
        add(sc, c)
        t = 1.0 + i * 1.0
        c.do("fist", t, 1.1).talk(t, 0.7).feel("angry", t, 2.2)
        w.pop(t, 1.0, lines[i], sx(c.x0, zoom), head_y(zoom) - 25 - (i % 2) * 30, 44, (-0.06, 0.06)[i % 2])
    for c in cast:
        c.do("point", 6.8, 1.6)
    cast[0].do("raise", 9.6, 1.6).feel("happy", 9.6, 1.6)
    for c in cast[1:]:
        c.feel("surprised", 9.8, 1.8).do("shock", 11.8, 1.8)
    return sc


def s8(D):
    sc, w = make("bg_fest", D, 1.2, "fg_fest", 0.35)
    figs = [add(sc, ion(-330)), add(sc, bunica(330, -1)), add(sc, copil(-450)),
            add(sc, Figure(x=460, face=-1, hat="clop", shirt=IE, band="#3a5a8a", belt="#3a5a8a", name="V"))]
    for i, f in enumerate(figs):
        f.do("raise", 0.4 + i * 0.2, 2.2).feel("happy", 0.4, 7.5).do("hop", 3.0, 3.2)
    return sc


def s9(D):
    sc, w = make("bg_home", D, 1.3, "fg_home", 0.6)
    a, b, c = add(sc, ion(-290)), add(sc, bunica(290, -1)), add(sc, copil(-400))
    b.do("offer", 0.6, 3.0).feel("happy", 0.6, 3.0)
    a.do("clap", 4.0, 1.8).feel("happy", 4.0, 4.0)
    c.do("raise", 4.2, 1.8)
    a.do("eat", 6.4, 2.4)
    c.do("jump", 9.0, 0.6).feel("happy", 9.0, 3.0)
    a.talk(9.0, 1.0)
    w.pop(9.0, 3.0, "POFTĂ BUNĂ!", W / 2, 130, 84, -0.03, "#efd9a0")
    b.do("wave", 12.0, 2.0)
    return sc


SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    idx = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(len(SCENES))
    preview = "--preview" in sys.argv
    for i in idx:
        D = nar_len(i) + PAD + 0.4
        sc = SCENES[i](D)
        n = int(D * 30)
        if preview:
            frames = {int(f * 30): os.path.join(OUT, f"p{i:02d}_{k}.png") for k, f in enumerate((1.0, 2.0, 8.5, 10.4, 13.5, D - 1.5)) if f < D}
            # render only stills: simulate up to the last frame we need
            sc.duration = max(frames) / 30 + 0.05
            sc.render(os.path.join(OUT, f"prev_{i:02d}.mp4"), workers=2, preview_png=frames)
        else:
            sc.render(os.path.join(OUT, f"sc_{i:02d}.mp4"), workers=2,
                      preview_png={f: os.path.join(OUT, f"p{i:02d}_{k}.png") for k, f in enumerate((45, n // 2, n - 10))})
        print("scene", i, "ok", round(D, 2))
