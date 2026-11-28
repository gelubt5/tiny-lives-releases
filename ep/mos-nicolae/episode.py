"""ToonEngine episode — Povestea Lucrurilor: "De unde vine Moș Nicolae?" (silueta style, 16:9).
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


# --- foregrounds
def fg_home_boots(ctx, cam, now):
    door(ctx, 330)
    sh = smooth((now - 2.0) / 1.0)
    boot(ctx, 220, 0, 1.0, shine=sh)
    boot(ctx, 262, 0, 1.0, shine=sh)


def fg_patara(ctx, cam, now):
    pass


def fg_window(ctx, cam, now):
    t = (now - 3.0) / 1.2
    if 0 < t < 1:
        x = -200 + t * 300
        y = -200 - 120 * math.sin(t * math.pi)
        goldbag(ctx, x, y, 1.0, 0.9)


def fg_hearth(ctx, cam, now):
    hearth(ctx, 0)
    fire(ctx, 0, now)
    for k, (x, col) in enumerate(((-110, "#8e2a22"), (-40, "#2f4a66"), (40, "#3f5f4a"))):
        stocking(ctx, x + 10, -222, col)
    boot(ctx, 130, 0, 0.9)
    boot(ctx, 170, 0, 0.9)
    for k, t0 in enumerate((1.2, 2.2, 3.2)):
        t = (now - t0) / 0.6
        if t > 0:
            y = -330 + min(1, t) * 110
            goldbag(ctx, -100 + k * 70, y if t < 1 else -195, min(1, t * 3), 0.7)
    a = smooth((now - (D3[0])) / 0.6)
    if a:
        three_balls(ctx, 0, -330, a)


D3 = [6.0]


def fg_church(ctx, cam, now):
    for i, x in enumerate((-120, -60, 60, 120)):
        E.candle(ctx, x, -160 + 0 * i, now)


def fg_sea(ctx, cam, now):
    if now < D5[0] * 0.5:
        p = smooth(now / max(1, D5[0] * 0.5))
        ship(ctx, -300 + 380 * p, -20, now, 0.9)


D5 = [10.0]


def fg_bari(ctx, cam, now):
    pass


def fg_dutch(ctx, cam, now):
    a = smooth((now - 3.0) / 0.6)
    for k, x in enumerate((-60, 10)):
        boot(ctx, x, 0, 0.9, col="#6a4a2a")
    carrot(ctx, -52, -44, a)
    hay(ctx, 22, -42, smooth((now - 3.6) / 0.6))


def fg_ny(ctx, cam, now):
    E.table(ctx, 260, 200, cloth="#3a3a44", motif="#c9a24a")
    book(ctx, 260, -94, smooth((now - 1.0) / 0.6))


def fg_night_boots(ctx, cam, now):
    door(ctx, 330)
    boot(ctx, 200, 0, 1.0, shine=1)
    boot(ctx, 262, 0, 1.0, shine=1)
    a = smooth((now - 2.4) / 0.5)
    candy(ctx, 196, -54, "#a8362c", a)
    candy(ctx, 208, -66, "#c9a24a", a)
    disc(ctx, 266, -52, 8, "#d0702a", a)  # orange
    rod(ctx, 268, -40, smooth((now - D8[0]) / 0.5))


D8 = [7.0]


def fg_home_end(ctx, cam, now):
    door(ctx, 330)
    boot(ctx, 200, 0, 1.0, shine=1)
    boot(ctx, 262, 0, 1.0, shine=1)
    candy(ctx, 196, -54, "#a8362c")
    candy(ctx, 208, -66, "#c9a24a")
    disc(ctx, 266, -52, 8, "#d0702a")


# ------------------------------------------------------------------ backgrounds
def bg_home_n(ctx, cam, now):
    E.bg_home(ctx, cam, now)
    label(now, 0.8, "5 DECEMBRIE", "SEARA", x=W * 0.3, y=60, ctx=ctx)


def coast(ctx, sky=("#7fa0b4", "#e6d6b4"), houses=True, seed=3):
    grad(ctx, [(0, sky[0]), (0.7, sky[1]), (1, sky[1])])
    glow(ctx, W * 0.78, 120, 220, "#fff1cf", 0.55)
    ridge(ctx, GY - 200, 60, "#9a9a8a", seed, 0.7)
    haze(ctx, GY - 170, 60, "#e8dcc0", 0.5)
    rect(ctx, 0, GY - 150, W, 60, "#5e8a96")  # sea
    for i in range(12):
        rect(ctx, (i * 117 + 30) % W, GY - 130 + (i % 3) * 14, 60, 2, "#e8f0f0", 0.4)
    if houses:
        r = random.Random(seed)
        x = 40
        while x < W:
            w = r.uniform(60, 110)
            h = r.uniform(50, 100)
            rect(ctx, x, GY - 90 - h, w, h + 10, "#d8ccb0")
            rect(ctx, x - 4, GY - 96 - h, w + 8, 8, "#b0663e")
            rect(ctx, x + w * 0.35, GY - 90 - h * 0.6, w * 0.25, h * 0.3, "#5a4a40", 0.7)
            x += w + r.uniform(20, 120)
    rect(ctx, 0, GY - 90, W, H - GY + 90, "#c9b48a")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#a8936a")
    for i in range(3):
        cx = 120 + i * 520
        rect(ctx, cx, GY - 220, 14, 130, "#5a4a3a")
        disc(ctx, cx + 7, GY - 230, 40, "#56664a")


def bg_patara(ctx, cam, now):
    coast(ctx)
    label(now, 0.8, "SECOLUL III", "PATARA · ASIA MICĂ · AZI TURCIA", x=W / 2, y=70, col="#5a2a1a", sub="#3a2a22", ctx=ctx)
    label(now, D1[0], "MIRA", "EPISCOP", x=W * 0.16, y=170, col="#5a2a1a", sub="#3a2a22", ctx=ctx)


D1 = [7.0]


def bg_window_night(ctx, cam, now):
    grad(ctx, [(0, "#101830"), (0.7, "#2a3a5a"), (1, "#3a4a66")])
    r = random.Random(3)
    for _ in range(80):
        x, y = r.uniform(0, W), r.uniform(0, GY - 300)
        tw = 0.5 + 0.5 * math.sin(now * r.uniform(1, 3) + x)
        disc(ctx, x, y, r.uniform(0.8, 2.0), "#f4ecd8", 0.3 + 0.5 * tw)
    disc(ctx, W * 0.15, 110, 34, "#f2ead0", 0.9)
    glow(ctx, W * 0.15, 110, 140, "#f2ead0", 0.25)
    # the poor man's house, right
    hx = W * 0.62
    plaster(ctx, hx, GY - 330, 420, 330, "#4a4a52", 6, 0.12)
    ctx.move_to(hx - 20, GY - 330)
    ctx.line_to(hx + 210, GY - 430)
    ctx.line_to(hx + 440, GY - 330)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#2a2630"))
    ctx.fill()
    rect(ctx, hx + 60, GY - 250, 110, 100, "#e8b86a", 0.75)
    glow(ctx, hx + 115, GY - 200, 120, "#ffb15e", 0.25)
    ctx.set_source_rgb(*rgb("#2a1f1d"))
    ctx.set_line_width(6)
    ctx.rectangle(hx + 60, GY - 250, 110, 100)
    ctx.stroke()
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a2a34")
    label(now, 0.8, "SE SPUNE CĂ...", "O LEGENDĂ", x=W * 0.36, y=90, ctx=ctx)


def bg_hearth_room(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#4a3a32", 9, 0.12)
    rect(ctx, 0, 0, W, 36, "#2b201d")
    for bx in (60, W - 94):
        rect(ctx, bx, 0, 34, GY, "#2b201d")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e221e")
    glow(ctx, W / 2, GY - 100, 520, "#ffb15e", 0.18 + 0.03 * math.sin(now * 9))


def bg_church(ctx, cam, now):
    grad(ctx, [(0, "#3a3028"), (1, "#24201c")], 0, GY)
    for x in (140, W - 300):
        ctx.save()
        ctx.move_to(x, 420)
        ctx.line_to(x, 200)
        ctx.arc(x + 80, 200, 80, math.pi, 2 * math.pi)
        ctx.line_to(x + 160, 420)
        ctx.close_path()
        ctx.clip()
        grad(ctx, [(0, "#c9a870"), (1, "#8a6a4a")], 120, 420)
        ctx.restore()
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a201a")
    glow(ctx, W / 2, GY - 150, 420, "#ffcf8a", 0.2)
    label(now, 0.8, "6 DECEMBRIE", "MIRA", x=W / 2, y=80, ctx=ctx)


def bg_sea(ctx, cam, now):
    grad(ctx, [(0, "#7a94a8"), (0.6, "#d8c8a8"), (1, "#d8c8a8")])
    glow(ctx, W * 0.8, 140, 220, "#fff1cf", 0.5)
    haze(ctx, GY - 220, 60, "#e8dcc0", 0.4)
    rect(ctx, 0, GY - 200, W, H - GY + 200, "#4e7a88")
    for i in range(26):
        y = GY - 190 + (i % 7) * 34
        x = (i * 173 + now * 30 * (1 + i % 3)) % (W + 120) - 60
        rect(ctx, x, y, 70, 3, "#e8f0f0", 0.35)
    rect(ctx, W * 0.74, GY - 14, W * 0.3, 18, "#5a4232")
    for px in range(int(W * 0.76), W, 70):
        rect(ctx, px, GY, 12, H - GY, "#3a2a22")
    label(now, 0.8, "1087", "SPRE BARI · ITALIA", x=W * 0.5, y=80, col="#5a2a1a", sub="#3a2a22", ctx=ctx)


def bg_sea_bari(ctx, cam, now):
    if now < D5[0] * 0.5:
        bg_sea(ctx, cam, now)
    else:
        bg_bari(ctx, cam, now)
        k = 1 - smooth((now - D5[0] * 0.5) / 0.4)
        if k:
            ctx.set_source_rgba(0, 0, 0, k)
            ctx.paint()


def bg_bari(ctx, cam, now):
    coast(ctx, ("#86a2b2", "#e2d2b0"), houses=False, seed=8)
    ctx.save()
    world(ctx, cam)
    basilica(ctx, 0, 1.0)
    ctx.restore()
    label(now, 0.8, "BARI", "BAZILICA SFÂNTUL NICOLAE", x=W * 0.16, y=90, col="#5a2a1a", sub="#3a2a22", ctx=ctx)


def bg_dutch(ctx, cam, now):
    grad(ctx, [(0, "#6a7488"), (0.7, "#b9b2a8"), (1, "#b9b2a8")])
    gables(ctx, GY - 140, ["#6a4a3a", "#5a5248", "#7a5a48", "#4e5458"], 9)
    windmill(ctx, W * 0.86, GY - 140, now)
    haze(ctx, GY - 170, 60, "#c9c2ba", 0.3)
    # parlour wall + stove
    plaster(ctx, 0, GY - 150, W, 150, "#4a3e3a", 4, 0.1)
    rect(ctx, 0, GY - 156, W, 10, "#2a201c")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#3a2a22")
    label(now, 0.8, "OLANDA", "SINTERKLAAS", x=W * 0.24, y=90, ctx=ctx)


def bg_ny_n(ctx, cam, now):
    grad(ctx, [(0, "#3a4458"), (0.7, "#8a8f9c"), (1, "#a8a29a")])
    gables(ctx, GY - 170, ["#5a4a48", "#4e5056", "#5e4e40", "#4a5248"], 12)
    rect(ctx, 0, GY - 170, W, 30, "#4e6a78")
    plaster(ctx, 0, GY - 140, W, 140, "#3a3236", 5, 0.1)
    rect(ctx, 0, GY - 146, W, 10, "#2a2224")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a2224")
    label(now, 0.8, "NEW AMSTERDAM", "AZI NEW YORK", x=W * 0.26, y=90, ctx=ctx)
    label(now, D7[0], "1809", "WASHINGTON IRVING", x=W * 0.8, y=90, ctx=ctx)


D7 = [6.0]


def bg_home_night(ctx, cam, now):
    E.bg_home(ctx, cam, now)
    ctx.set_source_rgba(0.05, 0.07, 0.15, 0.45)
    ctx.paint()
    label(now, 0.8, "5 SPRE 6 DECEMBRIE", "ROMÂNIA", x=W * 0.3, y=60, ctx=ctx)


# ------------------------------------------------------------------ cast
def nicolae(x, face=1, old=False):
    return Figure(x=x, face=face, hat="mitra", shirt="#7a1f1a", skirt="#6a1a16", vest="#d9cfb6",
                  belt="#c9a24a", beard=True, mustache=True, name="Nicolae")


def nicolae_young(x, face=1):
    return Figure(x=x, face=face, shirt="#5a3a30", skirt="#4a2e26", belt="#c9a24a", beard=True, name="Nicolae")


def localnic(x, face=1, shirt="#cfc5b0", skirt=None, name="Localnic"):
    return Figure(x=x, face=face, shirt=shirt, skirt=skirt, belt="#6a4a2a", name=name)


def fata(x, face=1, col="#8e2a22"):
    return Figure(x=x, face=face, shirt="#d6cdb9", skirt=col, hair="bun", scale=0.88, name="Fata")


def olandez(x, face=1):
    return Figure(x=x, face=face, scale=0.7, shirt="#3e5f7a", belt="#2a2020", name="Kind")


def irving(x, face=1):
    return Figure(x=x, face=face, hat="tophat", shirt="#2a2a33", vest="#4a3a2a", belt="#5a3a22", name="Irving")


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make3("bg_home_n", D, 1.3, "fg_home_boots", 0.6)
    a, b, c = add(sc, ion(-330)), add(sc, bunica(-180, 1)), add(sc, copil(120, 1))
    c.do("stir", 0.8, 2.4)
    w.pop(3.4, 2.2, "LUCESC!", E.sx(120) + 10, E.head_y(1.3, 0.7) - 40, 52, 0.06)
    c.feel("happy", 3.4, 2.4).do("jump", 3.6, 0.55)
    a.do("think", 6.0, 3.0).look(6.0, 3.0, 0.3, -0.8)
    b.do("shrug", 7.2, 1.6)
    w.pop(D - 4.4, 4.0, "CINE E MOȘ NICOLAE?", W / 2, 200, 62, -0.02, "#efd9a0")
    return sc


def s1(D):
    D1[0] = D * 0.5
    sc, w = make3("bg_patara", D, 1.3, "fg_patara", 0.5)
    n = add(sc, nicolae_young(-440, 1))
    p1, p2 = add(sc, localnic(260, -1)), add(sc, localnic(370, -1, "#b0663e", "#5a4a3a", "Femeie"))
    n.walk(0.6, 2.6, -120)
    p1.do("wave", 1.6, 1.4)
    n.do("wave", 3.4, 1.4).feel("happy", 3.4, 2.0)
    p1.do("bow", D * 0.5 + 0.4, 1.4)
    p2.do("bow", D * 0.5 + 0.6, 1.4)
    w.pop(D * 0.5 + 0.6, 2.4, "EPISCOP!", E.sx(-120), E.head_y() - 40, 56, -0.05)
    n.feel("surprised", D * 0.5 + 0.6, 1.6)
    return sc


def s2(D):
    sc, w = make3("bg_window_night", D, 1.3, "fg_window", 0.6)
    n = add(sc, nicolae_young(-420, 1))
    n.walk(0.4, 2.2, -240).do("think", 2.4, 0.6).look(2.4, 0.6, 0.0, -0.5)
    n.do("offer", 3.0, 1.0)
    w.pop(4.2, 2.2, "PSST!", E.sx(-240) - 10, E.head_y() - 40, 48, -0.05)
    n.walk(6.0, 2.0, -470).turn(6.0, -1)
    return sc


def s3(D):
    D3[0] = D - 5.0
    sc, w = make3("bg_hearth_room", D, 1.3, "fg_hearth", 0.55)
    f1, f2, f3 = add(sc, fata(-400, 1, "#8e2a22")), add(sc, fata(-300, 1, "#2f4a66")), add(sc, fata(330, -1, "#3f5f4a"))
    for k, f in enumerate((f1, f2, f3)):
        f.feel("surprised", 1.6 + k * 0.3, 2.0).do("raise", 1.8 + k * 0.3, 1.4)
        f.feel("happy", 4.2, 3.0)
    f3.do("jump", 4.0, 0.6)
    w.pop(2.0, 2.2, "AUR!", W / 2, 120, 64, -0.04, "#ffe7a0")
    w.pop(D - 4.6, 3.0, "3 BILE DE AUR", W * 0.5, 62, 46, 0.03, "#efd9a0")
    return sc


def s4(D):
    sc, w = make3("bg_church", D, 1.3, "fg_church", 0.6)
    n = add(sc, nicolae(0, 1))
    p1, p2 = add(sc, localnic(-330, 1)), add(sc, localnic(330, -1, "#b0663e", "#5a4a3a", "Femeie"))
    n.do("wave", 0.8, 2.0).feel("happy", 0.8, 3.0)
    p1.do("bow", 1.4, 1.6)
    p2.do("bow", 1.6, 1.6)
    p1.do("clap", 4.2, 1.4)
    return sc


def s5(D):
    D5[0] = D
    sc, w = make3("bg_sea_bari", D, 1.3, "fg_sea", 0.5)
    m = add(sc, localnic(400, -1, "#3e5f7a", None, "Marinar"))
    m.do("point", 1.2, 2.2).look(1.2, 2.2, -0.6, 0)
    w.pop(2.6, 2.2, "SPRE BARI!", W * 0.7, 230, 52, -0.04)
    m.feel("happy", D * 0.5 + 0.6, 3.0).do("wave", D * 0.5 + 0.8, 1.6)
    w.pop(D * 0.5 + 1.2, 2.6, "O BAZILICĂ ÎNTREAGĂ!", W / 2, 140, 50, 0.03, "#efd9a0")
    return sc


def s6(D):
    sc, w = make3("bg_dutch", D, 1.3, "fg_dutch", 0.55)
    k1, k2 = add(sc, olandez(-330, 1)), add(sc, Figure(x=-220, face=1, scale=0.66, shirt="#8e2a22", skirt="#3a3a44", hair="bun", name="Meisje"))
    k1.do("offer", 2.6, 1.4)
    k2.do("offer", 3.2, 1.4)
    w.pop(4.0, 2.4, "MORCOVI PENTRU CAL!", W / 2, 200, 48, -0.04)
    k1.feel("happy", 6.4, 3.0).do("jump", 6.6, 0.6)
    k2.do("laugh", 7.0, 1.8)
    return sc


def s7(D):
    D7[0] = D * 0.45
    sc, w = make3("bg_ny_n", D, 1.3, "fg_ny", 0.55)
    i = add(sc, irving(80, 1))
    k = add(sc, copil(-330, 1))
    i.do("think", 0.8, 2.0).do("point", D * 0.45, 2.0)
    i.talk(D * 0.45, 1.0)
    w.pop(D - 5.0, 3.6, "SINTERKLAAS... SANTA CLAUS!", W / 2, 230, 46, -0.03, "#efd9a0")
    k.feel("surprised", D - 5.0, 2.0).do("raise", D - 4.8, 1.6)
    return sc


def s8(D):
    D8[0] = D * 0.55
    sc, w = make3("bg_home_night", D, 1.3, "fg_night_boots", 0.65)
    n = add(sc, nicolae(-80, 1))
    n.walk(0.2, 1.6, 60).do("offer", 2.0, 1.4)
    w.pop(2.6, 2.4, "DULCIURI!", E.sx(-160), E.head_y() - 30, 54, -0.05, "#ffe7a0")
    n.do("offer", D * 0.55 - 0.4, 1.0)
    w.pop(D * 0.55 + 0.2, 2.6, "NUIELUȘA!", E.sx(-160), E.head_y() - 30, 54, 0.05)
    n.do("shrug", D * 0.55 + 1.2, 1.6)
    n.walk(D - 2.6, 1.8, -460).turn(D - 2.6, -1)
    return sc


def s9(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home_end", 0.6)
    a, b, c = add(sc, ion(-380)), add(sc, bunica(-250, 1)), add(sc, copil(100, 1))
    c.do("jump", 0.8, 0.6).feel("happy", 0.8, 4.0).do("raise", 1.4, 1.6)
    a.feel("happy", 1.0, 4.0).do("clap", 1.2, 1.4)
    b.do("wave", 1.6, 1.8)
    w.pop(D - 5.0, 4.6, "TU CE AI GĂSIT ÎN GHETE?", W / 2, 140, 56, -0.03, "#efd9a0")
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
