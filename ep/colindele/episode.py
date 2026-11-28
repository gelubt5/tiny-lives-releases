"""ToonEngine episode — Povestea Lucrurilor: "De unde vin colindele?" (silueta style, 16:9).
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
def boot(ctx, x, y, s=1.0, col="#4a2e24", shine=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-14, 0)
    ctx.line_to(-14, -46)
    ctx.line_to(10, -46)
    ctx.line_to(10, -18)
    ctx.curve_to(26, -16, 34, -10, 34, 0)
    ctx.close_path()
    ctx.set_source_rgb(*rgb(col))
    ctx.fill()
    rect(ctx, -16, -50, 28, 7, "#2a1a16")
    rect(ctx, -14, -2, 48, 3, "#1a1210")
    if shine:
        disc(ctx, -4, -30, 4, "#ffffff", 0.5 * shine)
        glow(ctx, 0, -30, 30, "#ffffff", 0.25 * shine)
    ctx.restore()


def candy(ctx, x, y, col, a=1.0):
    disc(ctx, x, y, 7, col, a)
    ctx.move_to(x - 7, y)
    ctx.line_to(x - 14, y - 5)
    ctx.line_to(x - 14, y + 5)
    ctx.close_path()
    ctx.move_to(x + 7, y)
    ctx.line_to(x + 14, y - 5)
    ctx.line_to(x + 14, y + 5)
    ctx.close_path()
    ctx.set_source_rgba(*rgb(col), a)
    ctx.fill()


def rod(ctx, x, y, a=1.0):
    ctx.set_source_rgba(*rgb("#5a3a22"), a)
    ctx.set_line_width(3)
    ctx.move_to(x, y)
    ctx.curve_to(x + 4, y - 40, x - 6, y - 70, x + 2, y - 96)
    ctx.stroke()
    ctx.move_to(x + 1, y - 50)
    ctx.line_to(x + 16, y - 66)
    ctx.stroke()
    disc(ctx, x + 16, y - 67, 3, "#9a6a7a", a)


def door(ctx, x):
    rect(ctx, x - 70, -260, 140, 260, "#3a2620")
    rect(ctx, x - 60, -250, 120, 250, "#4e3428")
    rect(ctx, x - 60, -130, 120, 6, "#3a2620")
    disc(ctx, x + 44, -120, 6, "#c9a24a")


def goldbag(ctx, x, y, a=1.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-14, 0)
    ctx.curve_to(-20, -20, -8, -26, -4, -26)
    ctx.line_to(4, -26)
    ctx.curve_to(8, -26, 20, -20, 14, 0)
    ctx.close_path()
    ctx.set_source_rgba(*rgb("#b08a4a"), a)
    ctx.fill()
    rect(ctx, -6, -30, 12, 5, "#6a4a2a", a)
    glow(ctx, 0, -12, 30, "#ffd27a", 0.35 * a)
    ctx.restore()


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


def three_balls(ctx, x, y, a):
    for k, (dx, dy) in enumerate(((-26, 0), (26, 0), (0, -40))):
        glow(ctx, x + dx, y + dy, 40, "#ffd27a", 0.4 * a)
        disc(ctx, x + dx, y + dy, 18, "#d4a63a", a)
        disc(ctx, x + dx - 6, y + dy - 6, 5, "#fff3c0", 0.6 * a)


def ship(ctx, x, y, now, s=1.0):
    ctx.save()
    ctx.translate(x, y + 4 * math.sin(now * 1.6))
    ctx.rotate(0.03 * math.sin(now * 1.3))
    ctx.scale(s, s)
    ctx.move_to(-170, -40)
    ctx.line_to(170, -40)
    ctx.line_to(130, 10)
    ctx.line_to(-140, 10)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#4a3226"))
    ctx.fill()
    rect(ctx, -170, -48, 340, 10, "#3a261e")
    rect(ctx, -4, -300, 8, 262, "#3a261e")
    ctx.move_to(-6, -290)
    ctx.curve_to(-120, -240, -120, -110, -6, -70)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#d9cfb6"))
    ctx.fill()
    ctx.move_to(6, -280)
    ctx.curve_to(110, -230, 110, -120, 6, -80)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#c9bfa6"))
    ctx.fill()
    ctx.restore()


def basilica(ctx, x, a=1.0):
    ctx.save()
    ctx.translate(x, 0)
    rect(ctx, -170, -230, 340, 230, "#cdbf9e", a)
    ctx.move_to(-180, -230)
    ctx.line_to(0, -320)
    ctx.line_to(180, -230)
    ctx.close_path()
    ctx.set_source_rgba(*rgb("#b8a986"), a)
    ctx.fill()
    for tx in (-210, 170):
        rect(ctx, tx, -360, 40, 360, "#c2b390", a)
    rect(ctx, -40, -140, 80, 140, "#4a3a30", a)
    ctx.arc(0, -140, 40, math.pi, 2 * math.pi)
    ctx.set_source_rgba(*rgb("#4a3a30"), a)
    ctx.fill()
    ctx.arc(0, -250, 22, 0, 2 * math.pi)
    ctx.set_source_rgba(*rgb("#6a5a48"), a)
    ctx.fill()
    ctx.restore()


def windmill(ctx, x, y, now, col="#4a4440"):
    ctx.move_to(x - 30, y)
    ctx.line_to(x - 18, y - 150)
    ctx.line_to(x + 18, y - 150)
    ctx.line_to(x + 30, y)
    ctx.close_path()
    ctx.set_source_rgb(*rgb(col))
    ctx.fill()
    ctx.save()
    ctx.translate(x, y - 150)
    ctx.rotate(now * 0.4)
    for k in range(4):
        ctx.rotate(math.pi / 2)
        rect(ctx, -6, -110, 12, 110, col)
        rect(ctx, 6, -104, 22, 80, "#8a8278", 0.8)
    ctx.restore()


def carrot(ctx, x, y, a=1.0):
    ctx.move_to(x - 5, y)
    ctx.line_to(x + 5, y)
    ctx.line_to(x, y - 34)
    ctx.close_path()
    ctx.set_source_rgba(*rgb("#d0702a"), a)
    ctx.fill()
    ctx.move_to(x - 5, y - 30)
    ctx.line_to(x, y - 46)
    ctx.line_to(x + 5, y - 30)
    ctx.set_source_rgba(*rgb("#4a6a3a"), a)
    ctx.fill()


def hay(ctx, x, y, a=1.0):
    ctx.set_source_rgba(*rgb("#d8b860"), a)
    ctx.set_line_width(2)
    for k in range(9):
        ctx.move_to(x - 8 + k * 2, y)
        ctx.line_to(x - 20 + k * 5, y - 22 - (k % 3) * 4)
    ctx.stroke()


def book(ctx, x, y, a=1.0):
    rect(ctx, x - 40, y - 52, 80, 52, "#6a2a22", a)
    rect(ctx, x - 34, y - 46, 68, 40, "#7a3a2e", a)
    rect(ctx, x - 2, y - 52, 4, 52, "#3a1a16", a)



def colac(ctx, x, y, a=1.0, s=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s * 0.55)
    ctx.set_line_width(14)
    ctx.set_source_rgba(*rgb("#b07a3a"), a)
    ctx.arc(0, 0, 26, 0, 2 * math.pi)
    ctx.stroke()
    ctx.set_line_width(4)
    ctx.set_source_rgba(*rgb("#d8a860"), a)
    for k in range(8):
        an = k * math.pi / 4
        ctx.move_to(26 * math.cos(an) - 5, 26 * math.sin(an) - 5)
        ctx.line_to(26 * math.cos(an) + 5, 26 * math.sin(an) + 5)
    ctx.stroke()
    ctx.restore()


def nuts(ctx, x, y, a=1.0):
    for k in range(6):
        disc(ctx, x - 20 + k * 8, y - (k % 2) * 6, 6, "#8a6a3a", a)


def drum(ctx, x, y):
    rect(ctx, x - 22, y - 30, 44, 30, "#8e2a22")
    ctx.save()
    ctx.translate(x, y - 30)
    ctx.scale(1, 0.3)
    disc(ctx, 0, 0, 22, "#e5dccb")
    ctx.restore()


def piano(ctx, x, now, play=0.0):
    rect(ctx, x - 120, -200, 240, 120, "#1e1a1c")
    rect(ctx, x - 130, -84, 260, 18, "#2a2426")
    rect(ctx, x - 118, -96, 236, 14, "#e9e2d0")
    for k in range(20):
        rect(ctx, x - 112 + k * 12, -96, 2, 14, "#3a3434")
    for k in (-100, 100):
        rect(ctx, x + k - 6, -66, 12, 66, "#1e1a1c")
    rect(ctx, x - 60, -190, 120, 70, "#e2d8c0")  # sheet music
    for k in range(5):
        rect(ctx, x - 52, -180 + k * 12, 104, 1.5, "#4a4040")
    if play:
        for k in range(3):
            t = (now * 0.7 + k / 3) % 1
            text(ctx, "♪", W / 2 + (k - 1) * 40, GY - 340 - t * 90, 40, "#efd9a0", outline=None, a=play * (1 - t))


def column(ctx, x, h=330):
    rect(ctx, x - 22, -h, 44, h, "#cdbf9e")
    rect(ctx, x - 32, -h - 16, 64, 18, "#b8a986")
    rect(ctx, x - 32, -14, 64, 14, "#b8a986")


def peasant_house(ctx, x, base, w, h, snow=True, lit=0.7):
    plaster(ctx, x, base - h, w, h, "#cfc5b0", int(x) % 7 + 1, 0.12)
    ctx.move_to(x - 20, base - h)
    ctx.line_to(x + w / 2, base - h - w * 0.45)
    ctx.line_to(x + w + 20, base - h)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#4a3a32"))
    ctx.fill()
    if snow:
        ctx.move_to(x - 20, base - h)
        ctx.line_to(x + w / 2, base - h - w * 0.45)
        ctx.line_to(x + w + 20, base - h)
        ctx.line_to(x + w + 10, base - h + 8)
        ctx.line_to(x + w / 2, base - h - w * 0.45 + 12)
        ctx.line_to(x - 10, base - h + 8)
        ctx.close_path()
        ctx.set_source_rgb(*rgb("#e8eaf0"))
        ctx.fill()
    for k in range(2):
        rect(ctx, x + w * 0.18 + k * w * 0.42, base - h * 0.7, w * 0.22, h * 0.32, "#e8b86a", lit)


def winter_night(ctx, now, houses=True):
    grad(ctx, [(0, "#101830"), (0.7, "#2a3a5a"), (1, "#3a4a66")])
    r = random.Random(3)
    for _ in range(80):
        x, y = r.uniform(0, W), r.uniform(0, GY - 300)
        disc(ctx, x, y, r.uniform(0.8, 2.0), "#f4ecd8", 0.3 + 0.4 * (0.5 + 0.5 * math.sin(now * 2 + x)))
    disc(ctx, W * 0.86, 100, 30, "#f2ead0", 0.9)
    glow(ctx, W * 0.86, 100, 130, "#f2ead0", 0.22)
    ridge(ctx, GY - 190, 40, "#22304a", 14, 0.9)
    trees(ctx, GY - 170, "#1a2638", 6, 60, 26, 60)
    if houses:
        for k, (x, w, h) in enumerate(((40, 200, 140), (330, 170, 120), (820, 210, 150), (1110, 190, 130))):
            peasant_house(ctx, x, GY - 70, w, h)
    haze(ctx, GY - 120, 60, "#4a5a7a", 0.25)
    rect(ctx, 0, GY - 70, W, H - GY + 70, "#c9ccd6")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#aeb2be")
    snowfall(ctx, now, 50, 0.5)


def fence(ctx, x0, x1):
    for x in range(int(x0), int(x1), 24):
        rect(ctx, x, -90, 14, 90, "#4a3a2e")
        ctx.move_to(x, -90)
        ctx.line_to(x + 7, -100)
        ctx.line_to(x + 14, -90)
        ctx.set_source_rgb(*rgb("#4a3a2e"))
        ctx.fill()
    rect(ctx, x0, -70, x1 - x0, 8, "#3a2a22")
    rect(ctx, x0, -30, x1 - x0, 8, "#3a2a22")


# --- foregrounds
def fg_table_colaci(ctx, cam, now):
    E.table(ctx, 250, 240)
    a = smooth((now - 1.0) / 0.6)
    colac(ctx, 200, -100, a)
    colac(ctx, 290, -102, smooth((now - 1.6) / 0.6))
    nuts(ctx, 330, -94, smooth((now - 2.2) / 0.6))
    E.candle(ctx, 150, -94, now)


def fg_rome(ctx, cam, now):
    column(ctx, -420)
    column(ctx, 420)
    a = smooth((now - 3.0) / 0.6)
    colac(ctx, 0, -40, 0)
    for k in range(3):
        disc(ctx, -30 + k * 30, -10, 9, "#d4a63a", a)  # coins as gifts


def fg_none(ctx, cam, now):
    pass


def fg_rehearsal(ctx, cam, now):
    E.candle(ctx, 0, -10, now)


def fg_street(ctx, cam, now):
    pass


def fg_gate(ctx, cam, now):
    fence(ctx, 160, 470)
    rect(ctx, 150, -150, 16, 150, "#3a2a22")
    drum(ctx, -200, -60) if False else None


def fg_gifts(ctx, cam, now):
    fence(ctx, 180, 470)
    a = smooth((now - 1.6) / 0.5)
    t = (now - 1.6) / 1.0
    colac(ctx, 60 - 40 * min(1, max(0, t)), -150, a, 0.9)


def fg_piano(ctx, cam, now):
    piano(ctx, 60, now, smooth((now - 2.0) / 0.6))


def fg_stage(ctx, cam, now):
    rect(ctx, -470, -20, 940, 20, "#4a3a30")


def fg_home_end(ctx, cam, now):
    E.table(ctx, 250, 240)
    colac(ctx, 200, -100)
    colac(ctx, 290, -102)
    nuts(ctx, 330, -94)
    E.candle(ctx, 150, -94, now)


# ------------------------------------------------------------------ backgrounds
def bg_home_ajun(ctx, cam, now):
    E.bg_home(ctx, cam, now)
    label(now, 0.8, "AJUNUL CRĂCIUNULUI", "24 DECEMBRIE", x=W * 0.5, y=56, ctx=ctx)


def bg_rome(ctx, cam, now):
    grad(ctx, [(0, "#8aa0b0"), (0.65, "#e6d6b4"), (1, "#e6d6b4")])
    glow(ctx, W * 0.5, 120, 260, "#fff1cf", 0.5)
    ridge(ctx, GY - 170, 50, "#a09a88", 4, 0.7)
    # temple silhouette
    tx = W * 0.5
    rect(ctx, tx - 260, GY - 330, 520, 24, "#bfb090")
    ctx.move_to(tx - 280, GY - 330)
    ctx.line_to(tx, GY - 420)
    ctx.line_to(tx + 280, GY - 330)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#b8a986"))
    ctx.fill()
    for k in range(8):
        rect(ctx, tx - 240 + k * 66, GY - 306, 22, 236, "#cdbf9e")
    haze(ctx, GY - 120, 70, "#efe2c4", 0.4)
    rect(ctx, 0, GY - 70, W, H - GY + 70, "#c9b48a")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#a8936a")
    label(now, 0.8, "CALENDAE", "ROMA ANTICĂ · PRIMA ZI A LUNII", x=W / 2, y=60, col="#5a2a1a", sub="#3a2a22", ctx=ctx)


def bg_slav(ctx, cam, now):
    winter_night(ctx, now)
    label(now, 0.8, "KOLEDA", "LA VECINII SLAVI", x=W / 2, y=80, ctx=ctx)


def bg_rehearsal(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#4a3a32", 9, 0.12)
    rect(ctx, 0, 0, W, 36, "#2b201d")
    for bx in (60, W - 94):
        rect(ctx, bx, 0, 34, GY, "#2b201d")
    window(ctx, W / 2 - 70, 100, 140, 150, "#18213a", "#3a4a72", snow=1, now=now)
    stergar(ctx, 930, 120, 110, 28)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e221e")
    glow(ctx, W / 2, GY - 100, 520, "#ffb15e", 0.2 + 0.03 * math.sin(now * 9))
    label(now, 0.8, "CEATA", "REPETIȚII ÎN FIECARE SEARĂ", x=W * 0.24, y=70, ctx=ctx)


def bg_street(ctx, cam, now):
    winter_night(ctx, now)
    c = smooth((now - 2.2) / 0.5)
    if c:
        text(ctx, "PRIMĂRIA", 925, GY - 280, 22, "#2a2020", outline=None, font=SERIF, a=c, shadow=False)
        text(ctx, "ȘCOALA", 1175, GY - 248, 22, "#2a2020", outline=None, font=SERIF, a=c, shadow=False)


def bg_gate(ctx, cam, now):
    winter_night(ctx, now, houses=False)
    peasant_house(ctx, W * 0.66, GY - 70, 360, 220)


def bg_bartok(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#3e3a40", 5, 0.12)
    rect(ctx, 0, GY - 160, W, 10, "#2a2426")
    for x in (120, W - 260):
        rect(ctx, x, 110, 140, 200, "#2a2a30")
        rect(ctx, x + 10, 120, 120, 180, "#6a7488", 0.6)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a2224")
    glow(ctx, W / 2, GY - 160, 440, "#ffcf8a", 0.16)
    label(now, 0.8, "1915", "BÉLA BARTÓK", x=W * 0.5, y=70, ctx=ctx)


def bg_unesco(ctx, cam, now):
    grad(ctx, [(0, "#2a3a44"), (1, "#1e2a30")], 0, GY)
    for k in range(9):
        glow(ctx, 80 + k * 140, 80, 60, "#ffe7a0", 0.12)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a201c")
    glow(ctx, W / 2, GY - 160, 460, "#ffcf8a", 0.2)
    label(now, 0.8, "2013 · UNESCO", "ROMÂNIA · REPUBLICA MOLDOVA", x=W / 2, y=70, ctx=ctx)


# ------------------------------------------------------------------ cast
def flacau(x, face=1, vest="#3a2a22", leader=False, name="Flacau"):
    return Figure(x=x, face=face, shirt=IE, band="#8e2a22", belt="#8e2a22", vest=vest, hat="cusma",
                  hat_color="#1e1a18" if not leader else "#5a4a3a", mustache=leader, name=name)


def roman(x, face=1, col="#d9cfb6"):
    return Figure(x=x, face=face, shirt=col, skirt=col, belt="#8e2a22", name="Roman")


def mos(x, face=1):
    return Figure(x=x, face=face, shirt=IE, vest="#2a2228", belt="#8e2a22", hat="cusma", beard=True, mustache=True,
                  name="Batran")


def bartok(x, face=1):
    return Figure(x=x, face=face, shirt="#2a2a33", vest="#3a3a44", belt="#2a2224", name="Bartok")


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make3("bg_home_ajun", D, 1.3, "fg_table_colaci", 0.6)
    b, c = add(sc, bunica(400, -1)), add(sc, copil(-150, 1))
    a = add(sc, ion(-330))
    b.do("offer", 0.8, 2.2)
    c.feel("surprised", 3.4, 2.4).do("raise", 3.4, 1.6).look(3.4, 2.4, -0.6, -0.4)
    w.pop(3.4, 2.4, "SE AUDE CÂNTEC!", W * 0.3, 210, 50, -0.05)
    a.do("think", 6.0, 3.0).look(6.0, 3.0, 0.3, -0.8)
    w.pop(D - 4.0, 3.6, "DE UNDE VIN COLINDELE?", W / 2, 200, 60, -0.02, "#efd9a0")
    return sc


def s1(D):
    sc, w = make3("bg_rome", D, 1.3, "fg_rome", 0.5)
    r1, r2 = add(sc, roman(-260, 1)), add(sc, roman(260, -1, "#b0663e"))
    r1.do("wave", 1.0, 1.6)
    r2.do("wave", 1.4, 1.6).feel("happy", 1.4, 2.4)
    r1.do("offer", 3.2, 2.0)
    w.pop(3.6, 2.4, "URĂRI ȘI DARURI!", W / 2, 250, 50, -0.04)
    r2.do("clap", 6.0, 1.4)
    return sc


def s2(D):
    sc, w = make3("bg_slav", D, 1.3, "fg_none", 0.55)
    s1_ = add(sc, Figure(x=-200, face=1, shirt="#cfc5b0", vest="#6a3a2a", belt="#2a2020", hat="cusma", hat_color="#5a4a3a", beard=True, name="Slav"))
    f = add(sc, flacau(200, -1))
    s1_.talk(1.0, 1.2).do("wave", 1.0, 1.4)
    w.pop(1.2, 2.2, "KOLEDA!", E.sx(-200), E.head_y() - 40, 54, -0.05)
    f.talk(3.6, 1.0).do("raise", 3.6, 1.4)
    w.pop(3.8, 2.2, "COLINDA!", E.sx(200), E.head_y() - 40, 54, 0.05)
    s1_.do("laugh", 6.2, 1.8)
    f.feel("happy", 6.2, 2.4).do("clap", 6.4, 1.2)
    return sc


def s3(D):
    sc, w = make3("bg_rehearsal", D, 1.3, "fg_rehearsal", 0.55)
    m = add(sc, mos(-380, 1))
    fs = [add(sc, flacau(x, -1, v)) for x, v in ((120, "#3a2a22"), (240, "#2f4a66"), (360, "#3a2a22"))]
    l = add(sc, flacau(-40, -1, "#6a2a2a", True, "Vataf"))
    m.do("point", 1.0, 2.4).talk(1.2, 1.2)
    for k, f in enumerate(fs):
        f.talk(3.6 + k * 0.2, 2.0).do("raise", 3.6 + k * 0.2, 1.2)
    l.do("wave", 3.4, 1.6)
    w.pop(5.6, 2.4, "ÎNCĂ O DATĂ!", E.sx(-380) + 20, E.head_y() - 40, 50, -0.05)
    m.do("nod", D - 3.0, 1.4).feel("happy", D - 3.0, 2.0)
    return sc


def s4(D):
    sc, w = make3("bg_street", D, 1.3, "fg_street", 0.55)
    g = [add(sc, flacau(x, 1, v)) for x, v in ((-640, "#2f4a66"), (-560, "#3a2a22"), (-480, "#6a2a2a"))]
    for k, f in enumerate(g):
        f.walk(0.4, 2.8, -300 + k * 90)
    g[0].do("point", 3.4, 1.8)
    w.pop(3.6, 2.6, "ÎNTÂI LA PRIMAR!", W * 0.62, 190, 50, -0.04)
    g[1].do("shrug", 6.0, 1.6)
    return sc


def s5(D):
    sc, w = make3("bg_gate", D, 1.3, "fg_gate", 0.55)
    g = [add(sc, flacau(x, 1, v)) for x, v in ((-420, "#3a2a22"), (-310, "#6a2a2a"), (-200, "#2f4a66"))]
    h = add(sc, ion(330, -1))
    for k, f in enumerate(g):
        f.talk(0.8 + k * 0.1, 3.0)
    g[1].do("raise", 1.0, 2.0)
    h.feel("happy", 2.0, 3.0).do("clap", 2.4, 1.4)
    for k, f in enumerate(g):
        f.do("jump", D * 0.55 + k * 0.3, 0.6).do("hop", D * 0.55 + 0.9 + k * 0.3, 0.6)
    w.pop(D * 0.55, 2.4, "ȘI LA JOC!", W * 0.3, 210, 54, -0.05)
    return sc


def s6(D):
    sc, w = make3("bg_gate", D, 1.3, "fg_gifts", 0.55)
    g = [add(sc, flacau(x, 1, v)) for x, v in ((-380, "#3a2a22"), (-270, "#6a2a2a"), (-160, "#2f4a66"))]
    h = add(sc, bunica(330, -1))
    h.do("offer", 1.2, 2.4).feel("happy", 1.2, 3.0)
    g[2].do("offer", 2.0, 1.6).feel("happy", 2.4, 3.0)
    w.pop(2.6, 2.2, "NUCI!", W * 0.32, 220, 54, -0.05)
    w.pop(4.4, 2.2, "COLACI!", W * 0.5, 180, 54, 0.04, "#ffe7a0")
    g[0].do("jump", 6.0, 0.6).feel("happy", 6.0, 3.0)
    g[1].do("laugh", 6.4, 1.8)
    return sc


def s7(D):
    sc, w = make3("bg_bartok", D, 1.3, "fg_piano", 0.55)
    b = add(sc, bartok(-160, 1))
    b.do("think", 0.6, 1.4).do("stir", 2.0, D - 5.0)
    w.pop(D - 4.4, 3.2, "20 DE PIESE PENTRU PIAN!", W / 2, 165, 46, -0.03, "#efd9a0")
    b.feel("happy", D - 4.4, 3.0)
    return sc


def s8(D):
    sc, w = make3("bg_unesco", D, 1.3, "fg_stage", 0.55)
    g = [add(sc, flacau(x, 1 if x < 0 else -1, v)) for x, v in ((-300, "#3a2a22"), (-150, "#6a2a2a"), (150, "#2f4a66"), (300, "#3a2a22"))]
    for k, f in enumerate(g):
        f.do("bow", 1.0 + k * 0.15, 1.4)
        f.feel("happy", 3.0, 4.0).do("raise", 3.2 + k * 0.1, 1.6)
    w.pop(3.2, 3.0, "PATRIMONIU UNESCO!", W / 2, 175, 52, -0.03, "#ffe7a0")
    return sc


def s9(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home_end", 0.6)
    a, b, c = add(sc, ion(-380)), add(sc, bunica(-250, 1)), add(sc, copil(80, 1))
    c.do("jump", 0.8, 0.6).feel("happy", 0.8, 4.0).talk(1.0, 2.0)
    a.feel("happy", 1.0, 4.0).do("clap", 1.2, 1.4)
    b.do("wave", 1.6, 1.8)
    w.pop(D - 5.0, 4.6, "CARE E COLINDA TA?", W / 2, 140, 58, -0.03, "#efd9a0")
    return sc


SCENES = [s0, s1, s2, s3, s4, s5, s6, s7, s8, s9]
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
