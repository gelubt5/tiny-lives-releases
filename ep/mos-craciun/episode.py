"""ToonEngine episode — Povestea Lucrurilor: "De unde vine Moș Crăciun?" (silueta style, 16:9).
python3 episode.py [scene ...] [--preview]  -> out/sc_XX.mp4
"""
import os, sys, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
import ep2_sarmale as E
from ep2_sarmale import *  # noqa  (helpers: grad, glow, rect, disc, text, ridge, haze, plaster, ...)
from silueta import Figure

HERE3 = os.path.dirname(os.path.abspath(__file__))
E.NAR = os.path.join(HERE3, "nar")
OUT = os.path.join(HERE3, "out")


class Painted3(E.Painted):
    def draw(self, ctx, W_, H_, cam, gy, now):
        globals()[self.back](ctx, cam, now)
        if self.props:
            ctx.save()
            world(ctx, cam)
            globals()[self.props](ctx, cam, now)
            ctx.restore()


def make3(back, D, zoom=1.3, props=None, vig=0.5, push=0.06, **kw):
    w = Painted3(back, props, vig, **kw)
    sc = Scene(W, H, fps=30, duration=D, world=w, ground_ratio=GR, bubbles=False)
    sc.music = False
    n = int(D / 0.4) + 1
    for i in range(n):
        sc.camera.at(i * 0.4, [Anchor(0.0)], zoom * (1 + push * i * 0.4 / D))
    return sc, w


# ------------------------------------------------------------------ props
GREENS = ("#2f4a3a", "#3a5a44", "#46684e")


def fir(ctx, x, y, s, now, apples=0, nuts=0, candles=0, ribbons=0, flowers=0, lights=0, globes=0, star=0):
    """Muted fir tree standing at world (x, y); every decoration has its own 0..1 alpha."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rect(ctx, -12, -40, 24, 40, "#4a3226")
    tiers = [(-40, 120, 110), (-120, 98, 100), (-196, 76, 92), (-266, 54, 84)]
    for k, (by, hw, th) in enumerate(tiers):
        ctx.move_to(-hw, by)
        ctx.curve_to(-hw * 0.5, by + 10, hw * 0.5, by + 10, hw, by)
        ctx.line_to(0, by - th)
        ctx.close_path()
        ctx.set_source_rgb(*rgb(GREENS[k % 3]))
        ctx.fill()
        ctx.move_to(-hw * 0.9, by - 2)
        ctx.line_to(0, by - th)
        ctx.line_to(-hw * 0.2, by - 2)
        ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, 0.06)
        ctx.fill()
    spots = [(-70, -56), (60, -60), (-20, -92), (30, -140), (-55, -136), (48, -110), (-10, -184),
             (36, -210), (-34, -214), (8, -250), (-80, -70), (84, -52), (-40, -168), (20, -280)]
    r = random.Random(7)
    if ribbons:
        ctx.set_line_width(5)
        ctx.set_source_rgba(*rgb("#9e3a2e"), ribbons)
        for by, hw in ((-70, 96), (-150, 72), (-226, 52)):
            ctx.move_to(-hw, by)
            ctx.curve_to(-hw * 0.3, by + 22, hw * 0.3, by + 2, hw, by - 18)
            ctx.stroke()
    for i, (px, py) in enumerate(spots):
        if apples and i % 4 == 0:
            disc(ctx, px, py, 9, "#a8362c", apples)
            disc(ctx, px - 3, py - 3, 3, "#e88a6a", apples * 0.6)
        if nuts and i % 4 == 1:
            disc(ctx, px, py, 6, "#8a6a3a", nuts)
        if flowers and i % 4 == 2:
            for k in range(5):
                a = k * 2 * math.pi / 5
                disc(ctx, px + 6 * math.cos(a), py + 6 * math.sin(a), 4, "#e9d9c2", flowers)
            disc(ctx, px, py, 3, "#c9a24a", flowers)
        if globes and i % 3 == 0:
            disc(ctx, px, py, 10, ("#9e3a2e", "#c9a24a", "#3e5f7a")[i % 3], globes)
            disc(ctx, px - 3, py - 4, 3, "#ffffff", globes * 0.5)
        if candles and i % 4 == 3:
            rect(ctx, px - 3, py - 16, 6, 16, "#e5dccb", candles)
            f = 1 + 0.15 * math.sin(now * 17 + i)
            glow(ctx, px, py - 22, 34, "#ffc46b", 0.4 * candles)
            ctx.save()
            ctx.translate(px, py - 21)
            ctx.scale(1, 1.6 * f)
            disc(ctx, 0, 0, 3.4, "#ffd88a", candles)
            ctx.restore()
    if lights:
        cols = ("#ffcf6a", "#ff7a5a", "#8ad0ff", "#a8f08a")
        for i in range(30):
            t = i / 29
            by = -50 - t * 230
            hw = 100 * (1 - t) + 14
            px = hw * math.sin(i * 1.9)
            on = 0.55 + 0.45 * math.sin(now * 5 + i * 1.3)
            glow(ctx, px, by, 16, cols[i % 4], 0.5 * lights * on)
            disc(ctx, px, by, 3.2, cols[i % 4], lights)
    if star:
        ctx.save()
        ctx.translate(0, -312)
        ctx.rotate(0.15 * math.sin(now * 2))
        glow(ctx, 0, 0, 60, "#ffe7a0", 0.5 * star)
        ctx.move_to(0, -22)
        for k in range(1, 10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = 22 if k % 2 == 0 else 9
            ctx.line_to(rr * math.cos(a), rr * math.sin(a))
        ctx.close_path()
        ctx.set_source_rgba(*rgb("#e8c35a"), star)
        ctx.fill()
        ctx.restore()
    ctx.restore()


def label(now, t, big, small, x=W * 0.84, y=90, col="#efd9a0", sub="#f4ecd8", ctx=None):
    c = smooth((now - t) / 0.5)
    if c:
        text(ctx, big, x, y, 56, col, outline=None, font=SERIF, a=c)
        if small:
            text(ctx, small, x, y + 46, 22, sub, outline=None, font=SERIF, a=c)


def gables(ctx, base, cols, seed=3):
    r = random.Random(seed)
    x = -20
    i = 0
    while x < W + 20:
        w = r.uniform(90, 140)
        h = r.uniform(120, 200)
        col = cols[i % len(cols)]
        rect(ctx, x, base - h, w, h + 10, col)
        ctx.move_to(x - 4, base - h)
        ctx.line_to(x + w / 2, base - h - w * 0.7)
        ctx.line_to(x + w + 4, base - h)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#3a2a2a"))
        ctx.fill()
        for k in range(2):
            rect(ctx, x + w * 0.22 + k * w * 0.36, base - h + 30, w * 0.2, 34, "#e8c88a", 0.55)
        x += w + 6
        i += 1


def snowfall(ctx, now, n=60, a=0.6):
    r = random.Random(11)
    for _ in range(n):
        sx_ = (r.uniform(0, W) + now * 10) % W
        sy_ = (r.uniform(0, H) + now * r.uniform(25, 45)) % H
        disc(ctx, sx_, sy_, r.uniform(1.2, 2.8), "#ffffff", a)



# ------------------------------------------------------------------ props (world coords, y=0 ground)
def hearth(ctx, x):
    rect(ctx, x - 150, -230, 300, 230, "#5a4a42")
    rect(ctx, x - 165, -245, 330, 22, "#3a2e2a")
    rect(ctx, x - 95, -150, 190, 150, "#1e1614")


def fire(ctx, x, now, s=1.0):
    glow(ctx, x, -50, 160 * s, "#ff9a3a", 0.5)
    for k in range(5):
        f = 1 + 0.2 * math.sin(now * 11 + k * 1.7)
        ctx.save()
        ctx.translate(x - 50 + k * 25, -10)
        ctx.scale(1, f)
        ctx.move_to(-14, 0)
        ctx.curve_to(-14, -30, 0, -40, 0, -64 + 6 * (k % 2))
        ctx.curve_to(4, -40, 14, -30, 14, 0)
        ctx.close_path()
        ctx.set_source_rgba(*rgb("#ffb24a" if k % 2 else "#ff7a2a"), 0.9)
        ctx.fill()
        ctx.restore()


def stocking(ctx, x, y, col):
    ctx.move_to(x - 12, y)
    ctx.line_to(x - 12, y + 50)
    ctx.curve_to(x - 12, y + 66, x + 20, y + 70, x + 24, y + 56)
    ctx.line_to(x + 12, y + 44)
    ctx.line_to(x + 12, y)
    ctx.close_path()
    ctx.set_source_rgb(*rgb(col))
    ctx.fill()
    rect(ctx, x - 14, y - 6, 28, 10, "#e5dccb")


def book(ctx, x, y, a=1.0):
    rect(ctx, x - 40, y - 52, 80, 52, "#6a2a22", a)
    rect(ctx, x - 34, y - 46, 68, 40, "#7a3a2e", a)
    rect(ctx, x - 2, y - 52, 4, 52, "#3a1a16", a)


# --- foregrounds
def door(ctx, x):
    rect(ctx, x - 70, -260, 140, 260, "#3a2620")
    rect(ctx, x - 60, -250, 120, 250, "#4e3428")
    rect(ctx, x - 60, -130, 120, 6, "#3a2620")
    disc(ctx, x + 44, -120, 6, "#c9a24a")


# ------------------------------------------------------------------ cast extras
class Santa(Figure):
    """Silhouette Figure with a white beard and a red floppy cap (drawn over the standard head)."""
    def _draw_head(self, ctx, now, feel, fw, talk):
        super()._draw_head(ctx, now, feel, fw, talk)
        ctx.save()
        ctx.translate(4, -34)
        ctx.move_to(-10, 8)
        ctx.curve_to(-10, 46, 26, 50, 28, 10)
        ctx.line_to(22, 14)
        ctx.curve_to(14, 20, 2, 18, -10, 8)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#ece6da"))
        ctx.fill()
        ctx.move_to(14, 9)
        ctx.curve_to(20, 5, 27, 7, 31, 13)
        ctx.curve_to(24, 12, 18, 13, 12, 12)
        ctx.close_path()
        ctx.fill()
        ctx.move_to(-22, -24)
        ctx.curve_to(-20, -54, 6, -64, 18, -48)
        ctx.curve_to(10, -52, -16, -52, -34, -40)
        ctx.curve_to(-26, -34, -24, -30, -22, -24)
        ctx.close_path()
        ctx.move_to(-22, -24)
        ctx.curve_to(-18, -50, 20, -52, 24, -24)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#a8302a"))
        ctx.fill()
        ctx.rectangle(-24, -30, 50, 9)
        ctx.set_source_rgb(*rgb("#ece6da"))
        ctx.fill()
        disc(ctx, -36, -38, 7, "#ece6da")
        ctx.restore()


def mos(x, face=1, scale=1.0):
    return Santa(x=x, face=face, scale=scale, shirt="#a8302a", skirt="#9a2a24", belt="#1d1a21",
                 hair=None, name="Mos")


def cioban(x, face=1):
    return Figure(x=x, face=face, hat="cusma", shirt="#d6cdb9", vest="#6a4a2e", belt="#8e2a22",
                  beard=True, mustache=True, name="Craciun")


def irving(x, face=1):
    return Figure(x=x, face=face, hat="tophat", shirt="#2a2a33", vest="#4a3a2a", belt="#5a3a22", name="Irving")


def nast(x, face=1):
    return Figure(x=x, face=face, shirt="#3a3a44", vest="#5a4a3a", belt="#2a2020", mustache=True, beard=True,
                  name="Nast")


def pictor(x, face=1):
    return Figure(x=x, face=face, shirt="#d6cdb9", vest="#3e5f7a", belt="#2a2020", hat="beret",
                  hat_color="#3a3036", mustache=True, name="Sundblom")


def may(x, face=1):
    return Figure(x=x, face=face, shirt="#4a4e58", vest="#2f3a4a", belt="#2a2020", name="May")


def copila(x, face=1):
    return Figure(x=x, face=face, shirt="#d6cdb9", skirt="#8e2a22", hair="bun", scale=0.68, name="Ana")


# ------------------------------------------------------------------ props
DEER = "#6a4a34"


def reindeer(ctx, x, y, s=1.0, now=0.0, fly=0.0, nose=0.0, col=DEER, face=1):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * face, s)
    g = math.sin(now * 9 + x * 0.05) * fly
    for k, lx in enumerate((-40, -28, 30, 42)):
        sw = (g if k % 2 else -g) * 0.5
        ctx.save()
        ctx.translate(lx, -72)
        ctx.rotate(sw + (0.5 * fly if k < 2 else -0.5 * fly))
        rect(ctx, -3.5, 0, 7, 72, col)
        ctx.restore()
    ctx.save()
    ctx.translate(0, -84)
    ctx.scale(1, 0.44)
    ctx.arc(0, 0, 56, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*rgb(col))
    ctx.fill()
    ctx.move_to(36, -96)
    ctx.line_to(60, -136)
    ctx.line_to(74, -128)
    ctx.line_to(54, -78)
    ctx.close_path()
    ctx.fill()
    ctx.save()
    ctx.translate(74, -134)
    ctx.scale(1, 0.6)
    ctx.arc(0, 0, 17, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    ctx.move_to(78, -140)
    ctx.line_to(96, -132)
    ctx.line_to(92, -124)
    ctx.line_to(76, -126)
    ctx.close_path()
    ctx.fill()
    disc(ctx, -54, -92, 7, "#e5dccb")
    ctx.set_source_rgb(*rgb("#4a3424"))
    ctx.set_line_width(4)
    for dx in (0, -10):
        ctx.move_to(66 + dx, -142)
        ctx.line_to(56 + dx, -178)
        ctx.move_to(60 + dx, -160)
        ctx.line_to(44 + dx, -168)
        ctx.move_to(57 + dx, -174)
        ctx.line_to(68 + dx, -186)
    ctx.stroke()
    disc(ctx, 80, -138, 3, "#f4ecd8")
    if nose:
        glow(ctx, 96, -128, 46, "#ff4a3a", 0.6 * nose * (0.8 + 0.2 * math.sin(now * 6)))
        disc(ctx, 96, -128, 7, "#e0362a", nose)
    ctx.restore()


def sleigh(ctx, x, y, s=1.0, rider=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_source_rgb(*rgb("#3a2a22"))
    ctx.set_line_width(6)
    ctx.move_to(-80, 0)
    ctx.line_to(70, 0)
    ctx.curve_to(96, 0, 100, -24, 84, -30)
    ctx.stroke()
    for px in (-50, 40):
        rect(ctx, px, -22, 6, 22, "#3a2a22")
    if rider:
        disc(ctx, -10, -70, 34, "#a8302a")
        disc(ctx, 4, -112, 15, "#c99a78")
        ctx.move_to(-6, -104)
        ctx.curve_to(-4, -80, 22, -82, 22, -104)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#ece6da"))
        ctx.fill()
        ctx.move_to(-12, -120)
        ctx.line_to(-32, -142)
        ctx.line_to(20, -122)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#a8302a"))
        ctx.fill()
        disc(ctx, -32, -142, 6, "#ece6da")
        rect(ctx, 40, -70, 30, 34, "#6a4a2e")
        disc(ctx, 56, -76, 18, "#8a6a3a")
    ctx.move_to(-84, -20)
    ctx.line_to(76, -20)
    ctx.line_to(84, -64)
    ctx.line_to(-70, -60)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#7a2a22"))
    ctx.fill()
    rect(ctx, -84, -26, 160, 6, "#c9a24a")
    ctx.restore()


def wagon(ctx, x, y, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    rect(ctx, -70, -50, 140, 34, "#5a3a26")
    for px in (-44, 44):
        disc(ctx, px, -12, 16, "#3a2a20")
        disc(ctx, px, -12, 5, "#8a6a3a")
    for k, (bx, col) in enumerate(((-46, "#8e2a22"), (-6, "#3e5f7a"), (32, "#c9a24a"))):
        rect(ctx, bx, -82, 30, 32, col)
        rect(ctx, bx + 12, -82, 6, 32, "#e5dccb", 0.7)
    disc(ctx, -20, -98, 16, "#a8302a")
    disc(ctx, -14, -122, 10, "#c99a78")
    ctx.move_to(-20, -128)
    ctx.line_to(-34, -142)
    ctx.line_to(-4, -128)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#a8302a"))
    ctx.fill()
    ctx.restore()


def box(ctx, x, y, col="#6e2622", rib="#c9a24a", s=1.0):
    rect(ctx, x - 34 * s, y - 40 * s, 68 * s, 40 * s, col)
    rect(ctx, x - 6 * s, y - 40 * s, 12 * s, 40 * s, rib)
    rect(ctx, x - 34 * s, y - 24 * s, 68 * s, 8 * s, rib)


def gifts(ctx, x, a=1.0):
    if a <= 0:
        return
    ctx.push_group()
    box(ctx, x, 0)
    box(ctx, x + 74, 0, "#2f4a66", "#e5dccb", 0.8)
    box(ctx, x - 70, 0, "#3f5f4a", "#c9a24a", 0.7)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def sheep(ctx, x, y, s=1.0, now=0.0):
    ctx.save()
    ctx.translate(x, y + 1.5 * math.sin(now * 3 + x))
    ctx.scale(s, s)
    for lx in (-18, -8, 12, 22):
        rect(ctx, lx, -22, 5, 22, "#3a3230")
    for k in range(6):
        disc(ctx, -22 + k * 9, -36 + (k % 2) * -6, 15, "#e2dacb")
    ctx.save()
    ctx.translate(34, -42)
    ctx.scale(1.2, 0.8)
    ctx.arc(0, 0, 9, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*rgb("#3a3230"))
    ctx.fill()
    ctx.restore()


def crook(ctx, x, y):
    ctx.set_source_rgb(*rgb("#5a3a22"))
    ctx.set_line_width(5)
    ctx.move_to(x, y)
    ctx.line_to(x, y - 250)
    ctx.arc(x + 12, y - 250, 12, math.pi, 2 * math.pi)
    ctx.stroke()


def easel(ctx, x, w=170, h=200, art=None, a=1.0, now=0.0):
    ctx.set_source_rgb(*rgb("#4a3226"))
    ctx.set_line_width(7)
    ctx.move_to(x - 60, 0)
    ctx.line_to(x - 10, -h - 120)
    ctx.move_to(x + 60, 0)
    ctx.line_to(x + 10, -h - 120)
    ctx.move_to(x, -h - 60)
    ctx.line_to(x + 10, 0)
    ctx.stroke()
    rect(ctx, x - w / 2, -h - 110, w, h, "#e5dccb")
    rect(ctx, x - w / 2 - 6, -110, w + 12, 8, "#4a3226")
    if art and a:
        art(ctx, x, -110 - h / 2, a)


def santa_face(ctx, cx, cy, a, red=True, line=False):
    """Simple painted Santa portrait on a canvas (centre cx, cy)."""
    ctx.push_group()
    if red:
        rect(ctx, cx - 70, cy + 20, 140, 60, "#a8302a")
    disc(ctx, cx, cy - 6, 30, "#d9b494")
    ctx.move_to(cx - 32, cy)
    ctx.curve_to(cx - 30, cy + 62, cx + 30, cy + 62, cx + 32, cy)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#f4f0e6") if not line else rgb("#bdb4a4"))
    ctx.fill()
    if red:
        ctx.move_to(cx - 34, cy - 24)
        ctx.curve_to(cx - 20, cy - 74, cx + 30, cy - 70, cx + 52, cy - 40)
        ctx.line_to(cx + 34, cy - 24)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#a8302a"))
        ctx.fill()
        rect(ctx, cx - 38, cy - 30, 76, 12, "#f4f0e6")
        disc(ctx, cx + 54, cy - 38, 8, "#f4f0e6")
    else:
        ctx.set_source_rgb(*rgb("#4a4440"))
        ctx.set_line_width(2.5)
        ctx.arc(cx, cy - 6, 30, 0, 2 * math.pi)
        ctx.stroke()
        rect(ctx, cx - 36, cy - 44, 72, 14, "#6a6460")
    disc(ctx, cx - 10, cy - 10, 3.5, "#2a2020")
    disc(ctx, cx + 10, cy - 10, 3.5, "#2a2020")
    disc(ctx, cx, cy, 5, "#c97a6a")
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def letter(ctx, x, y, a=1.0):
    rect(ctx, x - 40, y - 4, 80, 4, "#000000", 0.0)
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.08)
    rect(ctx, -44, -6, 88, 6, "#e9e1cf", a)
    ctx.restore()


def chimney_roofs(ctx, now, base, col="#2a2630", snow=True, seed=5):
    r = random.Random(seed)
    x = -30
    while x < W + 30:
        w = r.uniform(140, 220)
        h = r.uniform(60, 130)
        ctx.move_to(x, base)
        ctx.line_to(x, base - h)
        ctx.line_to(x + w / 2, base - h - w * 0.35)
        ctx.line_to(x + w, base - h)
        ctx.line_to(x + w, base)
        ctx.close_path()
        ctx.set_source_rgb(*rgb(col))
        ctx.fill()
        if snow:
            ctx.move_to(x - 4, base - h + 2)
            ctx.line_to(x + w / 2, base - h - w * 0.35 - 6)
            ctx.line_to(x + w + 4, base - h + 2)
            ctx.line_to(x + w / 2, base - h - w * 0.35 + 6)
            ctx.close_path()
            ctx.set_source_rgba(0.92, 0.93, 0.95, 0.8)
            ctx.fill()
        cx = x + w * 0.7
        rect(ctx, cx, base - h - w * 0.3 - 30, 24, 60, "#3a2a2a")
        for k in range(2):
            rect(ctx, x + w * 0.2 + k * w * 0.4, base - h + 24, w * 0.18, 30, "#e8c88a", 0.6)
        x += w + r.uniform(0, 30)


def night_sky(ctx, now, top="#0e1428", bot="#2a3656", moon=(0.82, 110)):
    grad(ctx, [(0, top), (0.75, bot), (1, bot)])
    r = random.Random(3)
    for _ in range(90):
        x, y = r.uniform(0, W), r.uniform(0, GY - 260)
        tw = 0.5 + 0.5 * math.sin(now * r.uniform(1, 3) + x)
        disc(ctx, x, y, r.uniform(0.8, 2.0), "#f4ecd8", 0.25 + 0.5 * tw)
    disc(ctx, W * moon[0], moon[1], 40, "#f2ead0", 0.92)
    glow(ctx, W * moon[0], moon[1], 170, "#f2ead0", 0.22)


# ------------------------------------------------------------------ backgrounds
def bg_home_eve(ctx, cam, now):
    E.bg_home(ctx, cam, now)
    label(now, 0.8, "24 DECEMBRIE", "AJUNUL CRĂCIUNULUI", x=W * 0.3, y=60, ctx=ctx)


def bg_legend(ctx, cam, now):
    grad(ctx, [(0, "#4a5674"), (0.6, "#b8a8a0"), (1, "#d8d0c8")])
    glow(ctx, W * 0.2, 130, 200, "#ffe1b8", 0.45)
    ridge(ctx, GY - 190, 60, "#7a8090", 5, 0.8)
    haze(ctx, GY - 160, 70, "#d8d0c8", 0.55)
    ridge(ctx, GY - 100, 30, "#8a8e98", 9)
    trees(ctx, GY - 98, "#3e4a4a", 2, 60, 18, 40)
    rect(ctx, 0, GY - 70, W, H - GY + 70, "#dcd8d2")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#c8c4c0")
    snowfall(ctx, now, 50, 0.55)
    label(now, 0.8, "SE SPUNE CĂ...", "O LEGENDĂ POPULARĂ", x=W * 0.5, y=70, col="#3a2a3a", sub="#2a2430", ctx=ctx)


def bg_ny_old(ctx, cam, now):
    grad(ctx, [(0, "#3a4458"), (0.7, "#8a8f9c"), (1, "#a8a29a")])
    gables(ctx, GY - 170, ["#5a4a48", "#4e5056", "#5e4e40", "#4a5248"], 12)
    haze(ctx, GY - 200, 60, "#a8a29a", 0.3)
    # the flying wagon over the treetops
    p = (now - D2[0]) / 4.5
    if 0 < p < 1.2:
        x = -150 + p * (W + 300)
        y = 345 - 45 * math.sin(p * math.pi)
        wagon(ctx, x, y, 1.1)
    trees(ctx, GY - 160, "#3e4a40", 4, 40, 30, 70)
    rect(ctx, 0, GY - 160, W, 20, "#4e5a50")
    plaster(ctx, 0, GY - 140, W, 140, "#3a3236", 5, 0.1)
    rect(ctx, 0, GY - 146, W, 10, "#2a2224")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a2224")
    label(now, 0.8, "NEW AMSTERDAM", "AZI NEW YORK", x=W * 0.24, y=80, ctx=ctx)
    label(now, D2[0] - 1.0, "1809", "WASHINGTON IRVING", x=W * 0.8, y=80, ctx=ctx)


D2 = [6.0]


def bg_troy(ctx, cam, now):
    night_sky(ctx, now, moon=(0.12, 110))
    p = (now - D3[0]) / 5.0
    if 0 < p < 1.3:
        x = -260 + p * (W + 400)
        y = 255 - 55 * math.sin(p * math.pi)
        for k in range(8):
            reindeer(ctx, x + 60 - (k // 2) * 62 + (k % 2) * 16, y - (k % 2) * 14 + 6 * math.sin(now * 4 + k),
                     0.4, now, fly=1.0)
        sleigh(ctx, x - 260, y + 6, 0.7)
        ctx.set_source_rgba(0.85, 0.75, 0.55, 0.6)
        ctx.set_line_width(1.5)
        ctx.move_to(x - 210, y - 20)
        ctx.line_to(x + 60, y - 30)
        ctx.stroke()
    chimney_roofs(ctx, now, GY - 60)
    haze(ctx, GY - 120, 60, "#3a4666", 0.35)
    rect(ctx, 0, GY - 60, W, H - GY + 60, "#2a2a34")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#24242c")
    snowfall(ctx, now, 40, 0.4)
    label(now, 0.8, "1823", "TROY · NEW YORK", x=W * 0.84, y=70, ctx=ctx)


D3 = [6.0]


def bg_studio(ctx, cam, now, tag=("1863", "HARPER'S WEEKLY")):
    plaster(ctx, 0, 0, W, GY, "#4e4440", 7, 0.12)
    rect(ctx, 0, 0, W, 36, "#2b201d")
    E.window(ctx, W - 300, 120, 170, 200, "#4a5a72", "#8a98a8", snow=1, now=now)
    for i, fx in enumerate((140, 300)):
        rect(ctx, fx, 150, 110, 140, "#2b201d")
        rect(ctx, fx + 8, 158, 94, 124, "#cfc5b0")
        ctx.set_source_rgba(0.2, 0.18, 0.18, 0.5)
        ctx.set_line_width(2)
        for k in range(5):
            ctx.move_to(fx + 16, 176 + k * 22)
            ctx.line_to(fx + 92, 176 + k * 22)
        ctx.stroke()
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e221e")
    glow(ctx, W * 0.6, GY - 200, 520, "#ffcf8a", 0.14)
    label(now, 0.8, tag[0], tag[1], x=W * 0.5, y=70, ctx=ctx)


def bg_pole(ctx, cam, now):
    grad(ctx, [(0, "#2a3a5a"), (0.6, "#8aa0b8"), (1, "#dce4ea")])
    r = random.Random(9)
    for k in range(4):  # aurora
        ctx.set_source_rgba(0.45, 0.85, 0.7, 0.10 + 0.04 * math.sin(now + k))
        ctx.set_line_width(26)
        ctx.move_to(0, 120 + k * 26)
        ctx.curve_to(W * 0.3, 60 + k * 30 + 20 * math.sin(now * 0.7 + k), W * 0.6, 170 + k * 20, W, 90 + k * 24)
        ctx.stroke()
    ridge(ctx, GY - 170, 70, "#c8d4de", 6, 0.9)
    haze(ctx, GY - 140, 70, "#e8eef2", 0.5)
    # workshop hut
    hx = W * 0.66
    rect(ctx, hx, GY - 250, 300, 250, "#6a4a34")
    ctx.move_to(hx - 30, GY - 250)
    ctx.line_to(hx + 150, GY - 360)
    ctx.line_to(hx + 330, GY - 250)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#ecf0f2"))
    ctx.fill()
    rect(ctx, hx + 40, GY - 190, 80, 70, "#ffcf7a", 0.8)
    glow(ctx, hx + 80, GY - 155, 110, "#ffb15e", 0.3)
    rect(ctx, hx + 170, GY - 150, 80, 150, "#3a2620")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#e2e8ec")
    snowfall(ctx, now, 50, 0.6)
    label(now, 0.6, "POLUL NORD", "ATELIERUL DE JUCĂRII", x=W * 0.26, y=80, col="#f4ecd8", sub="#e8eef2", ctx=ctx)


def bg_studio_pole(ctx, cam, now):
    if now < D4[0]:
        bg_studio(ctx, cam, now)
    else:
        bg_pole(ctx, cam, now - D4[0])
        k = 1 - smooth((now - D4[0]) / 0.4)
        if k:
            ctx.set_source_rgba(0, 0, 0, k)
            ctx.paint()


D4 = [7.0]


def bg_studio31(ctx, cam, now):
    bg_studio(ctx, cam, now, ("1931", "HADDON SUNDBLOM"))


def bg_store(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#4a3e3a", 8, 0.1)
    rect(ctx, 0, 0, W, 40, "#2b201d")
    for sy in (170, 290):  # shelves with goods
        rect(ctx, 60, sy, W - 120, 10, "#2b201d")
        r = random.Random(sy)
        x = 80
        while x < W - 120:
            w = r.uniform(30, 60)
            h = r.uniform(30, 70)
            rect(ctx, x, sy - h, w, h, r.choice(["#8e2a22", "#3e5f7a", "#c9a24a", "#3f5f4a", "#6a4a3a"]), 0.8)
            x += w + r.uniform(6, 20)
    for lx in (300, 640, 980):
        glow(ctx, lx, 60, 160, "#ffcf8a", 0.18)
        disc(ctx, lx, 60, 10, "#ffe7b0")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#3a2a22")
    label(now, 0.8, "1939", "CHICAGO · MONTGOMERY WARD", x=W * 0.5, y=110, ctx=ctx)


def bg_home_night(ctx, cam, now):
    E.bg_home(ctx, cam, now)
    ctx.set_source_rgba(0.05, 0.07, 0.15, 0.45)
    ctx.paint()
    label(now, 0.8, "NOAPTEA DE AJUN", "ROMÂNIA", x=W * 0.3, y=60, ctx=ctx)


# ------------------------------------------------------------------ foregrounds (world coords)
def fg_home_eve(ctx, cam, now):
    hearth(ctx, 300)
    fire(ctx, 300, now, 0.8)
    fir(ctx, -60, 0, 1.0, now, globes=1, ribbons=1, star=1, candles=1)
    gifts(ctx, -40, 1.0)


def fg_legend(ctx, cam, now):
    for k, (x, s) in enumerate(((60, 1.0), (150, 0.9), (240, 1.05), (330, 0.85), (110, 0.8))):
        sheep(ctx, x, 0 if k < 4 else -6, s, now)
    crook(ctx, -150, 0)


def fg_irving(ctx, cam, now):
    E.table(ctx, 260, 200, cloth="#3a3a44", motif="#c9a24a")
    book(ctx, 260, -94, smooth((now - 1.0) / 0.6))


def fg_troy(ctx, cam, now):
    a = smooth((now - 1.0) / 0.6)
    ctx.save()
    ctx.translate(300, -150)
    ctx.rotate(-0.06)
    rect(ctx, -70, -90, 140, 90, "#d8cfba", a)
    rect(ctx, -60, -80, 120, 12, "#3a3030", a)
    for k in range(5):
        rect(ctx, -60, -58 + k * 12, 120 if k % 2 else 90, 4, "#6a6058", a)
    ctx.restore()


def fg_studio(ctx, cam, now):
    if now < D4[0]:
        easel(ctx, 160, art=lambda c, x, y, a: santa_face(c, x, y, a, red=False, line=True),
              a=smooth((now - 2.0) / 2.0), now=now)
    else:
        for k, (x, col) in enumerate(((-120, "#8e2a22"), (-40, "#3e5f7a"), (40, "#c9a24a"))):
            box(ctx, x, 0, col, "#e5dccb", 0.9)


def fg_sundblom(ctx, cam, now):
    easel(ctx, 0, art=lambda c, x, y, a: santa_face(c, x, y, a, red=True), a=1.0, now=now)


def fg_store(ctx, cam, now):
    rect(ctx, -380, -110, 260, 110, "#4a3226")
    rect(ctx, -390, -120, 280, 12, "#2b201d")
    a = smooth((now - 1.5) / 0.6)
    ctx.save()
    ctx.translate(-250, -132)
    rect(ctx, -40, -10, 80, 10, "#a8302a", a)
    rect(ctx, -36, -14, 72, 4, "#e5dccb", a)
    ctx.restore()
    reindeer(ctx, 250, 0, 1.2, now, nose=smooth((now - D6[0]) / 0.5))


D6 = [5.0]


def fg_home_night(ctx, cam, now):
    fir(ctx, -60, 0, 1.0, now, globes=1, ribbons=1, star=1, lights=1)
    E.table(ctx, 280, 200, cloth="#d9cfba", motif="#8e3a2c")
    letter(ctx, 280, -94, 1.0)
    gifts(ctx, -40, smooth((now - D7[0]) / 0.6))


D7 = [6.0]


def fg_home_end(ctx, cam, now):
    hearth(ctx, 300)
    fire(ctx, 300, now, 0.8)
    fir(ctx, -60, 0, 1.0, now, globes=1, ribbons=1, star=1, lights=1)
    gifts(ctx, -40, 1.0)


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make3("bg_home_eve", D, 1.3, "fg_home_eve", 0.6)
    a, b, c = add(sc, ion(-420)), add(sc, bunica(-290, 1)), add(sc, copil(140, 1))
    c.look(0.6, 4.0, 0.4, -0.9)
    if D > 9:
        w.pop(2.2, 2.4, "PÂNDESC HORNUL!", E.sx(140) - 30, E.head_y(1.3, 0.7) - 60, 48, 0.05)
    a.do("think", 4.4, 2.6).look(4.4, 2.6, 0.3, -0.8)
    b.do("shrug", 5.6, 1.6)
    w.pop(max(0.6, D - 5.0), 4.4, "DE UNDE VINE MOȘ CRĂCIUN?", W / 2, 200, 58, -0.02, "#efd9a0")
    c.feel("surprised", D - 5.0, 2.0)
    return sc


def s1(D):
    sc, w = make3("bg_legend", D, 1.3, "fg_legend", 0.5)
    m = add(sc, cioban(-260, 1))
    m.walk(0.6, 2.4, -190).do("wave", 3.2, 1.6).feel("happy", 3.2, 3.0)
    m.do("point", 5.4, 2.0).look(5.4, 2.0, 0.6, 0)
    w.pop(D - 4.2, 3.6, "CRĂCIUN!", E.sx(-190), E.head_y() - 50, 56, -0.05, "#efd9a0")
    return sc


def s2(D):
    D2[0] = D * 0.5
    sc, w = make3("bg_ny_old", D, 1.3, "fg_irving", 0.55)
    i = add(sc, irving(80, 1))
    k = add(sc, copil(-330, 1))
    i.do("think", 0.8, 2.0).talk(D * 0.5 - 1.0, 1.0)
    i.do("point", D * 0.5, 2.2).look(D * 0.5, 3.0, 0.2, -0.9)
    k.feel("surprised", D * 0.5 + 0.6, 2.4).do("raise", D * 0.5 + 0.8, 1.6).look(D * 0.5, 3.0, 0.4, -0.9)
    w.pop(D * 0.5 + 1.0, 2.6, "ZBOARĂ!", E.sx(-330), E.head_y(1.3, 0.7) - 50, 54, -0.05)
    return sc


def s3(D):
    D3[0] = D * 0.35
    sc, w = make3("bg_troy", D, 1.3, "fg_troy", 0.6)
    a = add(sc, localnic(-260, 1))
    a.do("offer", 1.2, 1.6).look(1.2, 1.6, 0.4, 0.2)
    a.look(D * 0.35, 4.0, 0.2, -0.9).feel("surprised", D * 0.4, 2.0)
    w.pop(D * 0.35 + 1.4, 2.6, "OPT RENI!", W * 0.5, 440, 60, -0.04, "#efd9a0")
    a.do("raise", D - 4.2, 1.6).feel("happy", D - 4.2, 3.0)
    w.pop(D - 3.6, 3.0, "PE HORN!", E.sx(-260), E.head_y() - 40, 50, 0.05)
    return sc


def localnic(x, face=1, shirt="#3e4a5a", name="Cititor"):
    return Figure(x=x, face=face, shirt=shirt, vest="#5a4a3a", belt="#2a2020", name=name)


def s4(D):
    D4[0] = D * 0.55
    sc, w = make3("bg_studio_pole", D, 1.3, "fg_studio", 0.55)
    n = add(sc, nast(-60, 1))
    n.do("stir", 1.4, 3.0).feel("happy", 4.2, 2.0)
    w.pop(3.4, 2.2, "BĂTRÂN ȘI VESEL!", E.sx(160), 150, 46, -0.04)
    n.walk(D * 0.55 - 1.8, 1.4, -760)
    m = add(sc, mos(600, -1))
    m.walk(D * 0.55 + 0.3, 1.8, 220).do("wave", D * 0.55 + 2.4, 1.6).feel("happy", D * 0.55 + 2.4, 3.0)
    w.pop(D * 0.55 + 2.4, 2.6, "POLUL NORD!", W * 0.5, 210, 54, 0.04, "#efd9a0")
    return sc


def s5(D):
    sc, w = make3("bg_studio31", D, 1.3, "fg_sundblom", 0.55)
    p = add(sc, pictor(-200, 1))
    m = add(sc, mos(300, -1))
    w.pop(0.8, 2.6, "MIT!", W * 0.5, 180, 90, -0.06, "#ff8a6a")
    p.do("shake", 1.0, 1.6)
    m.do("shrug", 1.2, 1.4)
    w.pop(4.2, 3.0, "ROȘU DE DINAINTE!", E.sx(300), E.head_y() - 60, 44, 0.04)
    m.talk(4.2, 1.6)
    p.do("stir", 7.4, 3.0)
    m.feel("happy", D * 0.6, 3.0).do("wave", D * 0.62, 1.6)
    if D > 12:
        w.pop(D - 4.6, 3.6, "CELEBRU ÎN TOATĂ LUMEA!", W / 2, 190, 48, -0.03, "#efd9a0")
    return sc


def s6(D):
    D6[0] = D * 0.4
    sc, w = make3("bg_store", D, 1.3, "fg_store", 0.55)
    r = add(sc, may(-100, 1))
    r.do("think", 0.6, 1.8).do("offer", 2.4, 1.6)
    r.look(D * 0.4, 3.0, 0.4, -0.2).feel("happy", D * 0.4 + 0.4, 3.0).do("clap", D * 0.4 + 0.6, 1.4)
    w.pop(D * 0.4 + 0.5, 3.0, "RUDOLF!", E.sx(300), 230, 62, -0.05, "#ff8a6a")
    return sc


def s7(D):
    D7[0] = D * 0.6
    sc, w = make3("bg_home_night", D, 1.3, "fg_home_night", 0.65)
    c = add(sc, copila(380, -1))
    c.do("stir", 0.6, 2.4)
    w.pop(1.0, 2.6, "DRAGĂ MOȘULE...", E.sx(330), E.head_y(1.3, 0.68) - 60, 42, 0.04)
    c.walk(3.4, 1.8, 780)
    m = add(sc, mos(-560, 1))
    m.walk(D * 0.4, 2.0, -200).do("offer", D * 0.6, 1.4).feel("happy", D * 0.6, 2.4)
    w.pop(D * 0.6 + 0.6, 2.4, "DARURI!", E.sx(-40), E.head_y() - 10, 54, -0.05, "#ffe7a0")
    m.walk(D - 1.8, 1.4, -560).turn(D - 1.8, -1)
    return sc


def s8(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home_end", 0.6)
    a, b, c = add(sc, ion(-430)), add(sc, bunica(130, -1)), add(sc, copil(-300, 1))
    c.do("jump", 0.8, 0.6).feel("happy", 0.8, 4.0).do("raise", 1.4, 1.6)
    a.feel("happy", 1.0, 4.0).do("clap", 1.2, 1.4)
    b.do("wave", 1.6, 1.8)
    if D > 9:
        w.pop(3.4, 2.8, "CRĂCIUN FERICIT!", W / 2, 70, 72, -0.03, "#efd9a0")
    w.pop(max(0.6, D - 4.8), 4.4, "TU CE I-AI CERUT MOȘULUI?", W / 2, 70, 52, -0.03, "#efd9a0")
    return sc


SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8]
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    idx = [int(a) for a in sys.argv[1:] if a.isdigit()] or range(len(SCENES))
    for i in idx:
        D = E.nar_len(i) + E.PAD + 0.4
        sc = SCENES[i](D)
        n = int(D * 30)
        sc.render(os.path.join(OUT, f"sc_{i:02d}.mp4"), workers=2,
                  preview_png={f: os.path.join(OUT, f"p{i:02d}_{k}.png") for k, f in enumerate((45, n // 2, int(n * 0.75)))})
        print("scene", i, "ok", round(D, 2))
