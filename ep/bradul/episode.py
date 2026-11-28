"""ToonEngine episode — Povestea Lucrurilor: "De unde vine bradul de Crăciun?" (silueta style, 16:9).
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


def box(ctx, x, y):
    rect(ctx, x - 34, y - 40, 68, 40, "#6e2622")
    rect(ctx, x - 6, y - 40, 12, 40, "#c9a24a")
    rect(ctx, x - 34, y - 24, 68, 8, "#c9a24a")


def fg_home_tree(ctx, cam, now):
    E.table(ctx, 250, 240)
    E.candle(ctx, 200, -94, now)
    E.candle(ctx, 300, -94, now)
    a = smooth((now - 1.2) / 1.0)
    fir(ctx, -40, 0, 1.0, now, globes=a, ribbons=a, star=smooth((now - 4.0) / 0.4))
    box(ctx, 90, 0)


def fg_square(ctx, cam, now):
    up = smooth((now - 0.6) / 2.0)
    ctx.save()
    ctx.translate(0, 0)
    ctx.rotate(-0.9 * (1 - up))
    fir(ctx, 0, 0, 1.15, now, ribbons=smooth((now - 4) / 1))
    ctx.restore()


def fg_bremen(ctx, cam, now):
    E.table(ctx, 0, 260, cloth="#c9b893", motif="#3f5f4a")
    fir(ctx, 0, -94, 0.6, now, apples=smooth((now - 1.5) / 0.6), nuts=smooth((now - 3.0) / 0.6),
        flowers=smooth((now - 5.0) / 0.6))
    p = smooth((now - 4.0) / 0.6)  # pretzels + dates on the table
    for i, px in enumerate((-100, 90)):
        ctx.save()
        ctx.translate(px, -102)
        ctx.set_source_rgba(*rgb("#9a6a32"), p)
        ctx.set_line_width(5)
        ctx.arc(-6, 0, 8, 0, 2 * math.pi)
        ctx.stroke()
        ctx.arc(6, 0, 8, 0, 2 * math.pi)
        ctx.stroke()
        ctx.restore()
    for i in range(4):
        disc(ctx, -60 + i * 10, -100, 4, "#5a3020", p)


def fg_forest(ctx, cam, now):
    fir(ctx, 60, 0, 1.0, now, candles=smooth((now - 2.6) / 1.2))


def fg_windsor(ctx, cam, now):
    E.table(ctx, 0, 200, cloth="#2f4a3a", motif="#c9a24a")
    fir(ctx, 0, -94, 0.75, now, candles=1, globes=1, ribbons=1, star=1)


def fg_palace66(ctx, cam, now):
    fir(ctx, 0, 0, 0.9, now, candles=smooth((now - 3.0) / 1.0), star=0)


def fg_deco(ctx, cam, now):
    fir(ctx, -40, 0, 0.9, now, candles=smooth((now - 0.6) / 0.5), ribbons=smooth((now - 1.6) / 0.5),
        apples=smooth((now - 2.6) / 0.5), nuts=smooth((now - 3.6) / 0.5))


def fg_ny(ctx, cam, now):
    sw = now > 3.2
    fir(ctx, 20, 0, 1.1, now, lights=1 if sw else 0, star=1 if sw else 0)
    rect(ctx, 180, -150, 30, 50, "#3a3030")  # switch box
    rect(ctx, 191, -140 if sw else -125, 8, 16, "#c9a24a")


def fg_home_end(ctx, cam, now):
    E.table(ctx, 250, 240)
    E.candle(ctx, 200, -94, now)
    E.candle(ctx, 300, -94, now)
    fir(ctx, -40, 0, 1.0, now, globes=1, ribbons=1, lights=1, star=1)
    box(ctx, 90, 0)
    box(ctx, -160, 0)


# ------------------------------------------------------------------ backgrounds
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


def bg_baltic(ctx, cam, now):
    grad(ctx, [(0, "#3a4458"), (0.6, "#8a8f9c"), (1, "#b9b2a8")])
    glow(ctx, W * 0.2, 110, 200, "#f2ead0", 0.35)
    gables(ctx, GY - 60, ["#6a5a5a", "#5a6268", "#7a6a58", "#606a5a"], 5)
    haze(ctx, GY - 120, 80, "#c9c2ba", 0.35)
    rect(ctx, 0, GY - 70, W, H - GY + 70, "#d8d6d2")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#bdb8b2")
    snowfall(ctx, now)
    label(now, 0.8, "1441", "TALLINN · RIGA", ctx=ctx)


def bg_guild(ctx, cam, now):
    plaster(ctx, 0, 0, W, GY, "#5a4234", 8, 0.1)
    for i in range(0, W, 160):
        rect(ctx, i, 0, 20, GY, "#3a2a22")
    rect(ctx, 0, 0, W, 36, "#2b201d")
    rect(ctx, 0, GY - 160, W, 12, "#3a2a22")
    window(ctx, 80, 110, 140, 160, "#1e2a40", "#44557a", snow=1, now=now)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#3a2a22")
    glow(ctx, W / 2, GY - 120, 480, "#ffb15e", 0.22)
    label(now, 0.8, "1570", "BREMEN · GERMANIA", ctx=ctx)


def bg_night(ctx, cam, now):
    grad(ctx, [(0, "#101830"), (0.7, "#2a3a5a"), (1, "#3a4a66")])
    r = random.Random(3)
    for _ in range(90):
        x, y = r.uniform(0, W), r.uniform(0, GY - 220)
        tw = 0.5 + 0.5 * math.sin(now * r.uniform(1, 3) + x)
        disc(ctx, x, y, r.uniform(0.8, 2.2), "#f4ecd8", 0.4 + 0.5 * tw)
    ridge(ctx, GY - 120, 40, "#22304a", 14, 0.9)
    trees(ctx, GY - 90, "#1a2638", 6, 60, 30, 70)
    haze(ctx, GY - 90, 60, "#4a5a7a", 0.3)
    rect(ctx, 0, GY - 30, W, H - GY + 30, "#c9ccd6")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#aeb2be")
    label(now, 0.8, "SE SPUNE CĂ...", "MARTIN LUTHER", y=90, ctx=ctx)


def bg_windsor(ctx, cam, now):
    grad(ctx, [(0, "#2a3a34"), (1, "#1e2a26")], 0, GY)
    ctx.set_source_rgba(*rgb("#c9a24a"), 0.08)
    for j in range(0, int(GY), 60):
        for i in range(0, W, 60):
            ctx.arc(i + 30, j + 30, 8, 0, 2 * math.pi)
            ctx.fill()
    for x in (90, W - 230):
        rect(ctx, x, 120, 140, 280, "#6a2a2a")
        rect(ctx, x + 10, 120, 20, 280, "#8a3a34")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a201c")
    glow(ctx, W / 2, GY - 140, 420, "#ffcf8a", 0.22)
    c = smooth((now - 0.6) / 0.6)  # the newspaper page
    if c:
        ctx.save()
        ctx.translate(W * 0.2, 110 + 30 * (1 - c))
        ctx.rotate(-0.04)
        rect(ctx, -170, -50, 340, 108, "#ddd3bf", c)
        text(ctx, "THE ILLUSTRATED", 0, -22, 24, "#2a2020", outline=None, font=SERIF, a=c, shadow=False)
        text(ctx, "LONDON NEWS", 0, 8, 30, "#2a2020", outline=None, font=SERIF, a=c, shadow=False)
        text(ctx, "DECEMBRIE 1848", 0, 40, 18, "#7a1f1a", outline=None, font=SERIF, a=c, shadow=False)
        ctx.restore()


def bg_palace66(ctx, cam, now):
    E.bg_palace(ctx, cam, now)
    label(now, 0.8, "23 DECEMBRIE 1866", "PODUL MOGOȘOAIEI · AZI CALEA VICTORIEI", x=W / 2, y=70, ctx=ctx)


def bg_palace_deco(ctx, cam, now):
    E.bg_palace(ctx, cam, now)
    for i, (lab, t) in enumerate((("LUMÂNĂRI", 0.6), ("PANGLICI", 1.6), ("MERE", 2.6), ("NUCI", 3.6))):
        c = smooth((now - t) / 0.4)
        if c:
            text(ctx, lab, W * (0.38 + i * 0.16), 50, 30, "#efd9a0", outline="#1d1a21", a=c, lw=0.16)
    label(now, D_LATE[0], "DUPĂ 1900", "BUCUREȘTI", x=W * 0.16, y=110, ctx=ctx)


D_LATE = [10.0]


def bg_ny(ctx, cam, now):
    grad(ctx, [(0, "#141a2c"), (0.7, "#2c3046"), (1, "#3a3a50")])
    E.skyline(ctx, GY - 60, "#22263a", 17, 1.0)
    r = random.Random(4)
    for _ in range(70):
        disc(ctx, r.uniform(0, W), r.uniform(GY - 200, GY - 70), 2, "#e8c88a", 0.35)
    plaster(ctx, 0, GY - 260, W, 200, "#3a3236", 5, 0.1)  # parlour wall
    rect(ctx, 0, GY - 270, W, 14, "#2a2224")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2a2224")
    lit = smooth((now - 3.2) / 0.3)
    glow(ctx, W / 2, GY - 160, 460, "#ffcf8a", 0.08 + 0.2 * lit)
    label(now, 0.8, "1882", "NEW YORK", ctx=ctx)


# ------------------------------------------------------------------ cast
def negustor(x, face=1, vest="#2f4a66", name="Negustor"):
    return Figure(x=x, face=face, hat="beret", shirt="#5a4a3a", belt="#2a2020", vest=vest, beard=True, name=name)


def luther(x, face=1):
    return Figure(x=x, face=face, hat="beret", shirt="#24222a", belt="#3a2a22", vest="#1e1c24", name="Luther")


def victoria(x, face=1):
    return Figure(x=x, face=face, hat="crown", shirt="#3a2a44", skirt="#2a2238", hair="bun", scale=0.92,
                  name="Victoria")


def albert(x, face=-1):
    return Figure(x=x, face=face, shirt="#2a2a33", vest="#6a2a2a", belt="#c9a24a", mustache=True, name="Albert")


def carol(x, face=1):
    return Figure(x=x, face=face, hat="crown", beard=True, shirt="#2a2a44", vest="#3a4a3a", belt="#c9a24a",
                  name="Carol")


def boier(x, face=-1):
    return Figure(x=x, face=face, hat="cusma", shirt="#cfc5b0", vest="#6a2a2a", belt="#c9a24a",
                  mustache=True, name="Boier")


def johnson(x, face=1):
    return Figure(x=x, face=face, hat="tophat", shirt="#2a2a33", belt="#5a3a22", mustache=True, name="Johnson")


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home_tree", 0.6)
    a, b, c = add(sc, ion(-330)), add(sc, bunica(400, -1)), add(sc, copil(170, -1))
    a.do("offer", 1.0, 2.4)
    b.do("stir", 1.2, 2.0)
    c.do("jump", 3.6, 0.55).do("raise", 3.6, 1.8).feel("happy", 3.6, 2.2).talk(3.7, 0.9)
    w.pop(3.7, 2.2, "STEAUA E A MEA!", E.sx(170) + 30, E.head_y(1.3, 0.7) - 40, 50, 0.06)
    a.do("think", 7.0, 3.0).look(7.0, 3.0, 0.3, -0.8)
    b.do("shrug", 8.4, 1.6)
    w.pop(D - 3.6, 3.4, "DE UNDE VINE BRADUL?", W / 2, 128, 66, -0.02, "#efd9a0")
    return sc


def s1(D):
    sc, w = make3("bg_baltic", D, 1.3, "fg_square", 0.5)
    m1, m2 = add(sc, negustor(-330, 1, "#2f4a66", "N1")), add(sc, negustor(320, -1, "#6a2a2a", "N2"))
    m1.do("point", 0.8, 2.0)
    m2.do("clap", 3.0, 1.6).feel("happy", 3.0, 2.0)
    m1.do("jump", 5.6, 0.6).feel("happy", 5.6, 3.0)
    m2.do("hop", 6.0, 0.6)
    w.pop(6.0, 2.4, "UN BRAD ÎN PIAȚĂ!", W / 2, 230, 52, -0.04)
    m1.do("wave", 9.6, 1.6)
    m2.do("laugh", 10.0, 1.8)
    return sc


def s2(D):
    sc, w = make3("bg_guild", D, 1.3, "fg_bremen", 0.55)
    g = add(sc, negustor(-300, 1, "#3f5f4a", "Breasla"))
    k = add(sc, copil(290, -1))
    g.do("offer", 1.4, 2.4).talk(1.6, 1.0)
    g.do("point", 4.6, 2.0)
    k.walk(7.0, 1.4, 200).do("eat", 8.6, 2.0).feel("happy", 8.6, 2.6)
    w.pop(8.8, 2.4, "SE ȘI MĂNÂNCĂ!", E.sx(200) + 20, E.head_y(1.3, 0.7) - 40, 50, 0.05)
    g.do("laugh", 9.4, 1.8)
    return sc


def s3(D):
    sc, w = make3("bg_night", D, 1.3, "fg_forest", 0.6)
    l = add(sc, luther(-300, 1))
    k = add(sc, copil(-400, 1))
    l.do("point", 0.6, 2.0).look(0.6, 2.0, 0.4, -0.9)
    l.do("offer", 2.8, 2.0)
    k.feel("surprised", 4.6, 2.2).do("raise", 4.6, 1.8).talk(4.7, 0.8)
    w.pop(4.8, 2.2, "STELE ÎN BRAD!", E.sx(-400) + 40, E.head_y(1.3, 0.7) - 40, 48, -0.05)
    l.do("shrug", D - 3.2, 1.8)
    return sc


def s4(D):
    sc, w = make3("bg_windsor", D, 1.3, "fg_windsor", 0.5)
    v, a = add(sc, victoria(-200, 1)), add(sc, albert(200, -1))
    v.do("wave", 1.2, 1.6).feel("happy", 1.2, 2.4)
    a.do("offer", 1.6, 2.2)
    p = add(sc, Figure(x=-470, face=1, shirt="#d6cdb9", vest="#3e5f7a", belt="#2a2020", hat="tophat", name="Londonez"))
    p.walk(4.0, 1.6, -380).feel("surprised", 5.6, 2.0).do("raise", 5.8, 2.0).talk(5.9, 0.9)
    w.pop(6.0, 2.4, "VREAU ȘI EU UNUL!", W * 0.64, 250, 50, 0.04)
    a.do("nod", 7.0, 1.4)
    return sc


def s5(D):
    sc, w = make3("bg_palace66", D, 1.3, "fg_palace66", 0.5)
    c = add(sc, carol(-430, 1))
    k1, k2 = add(sc, copil(230, -1)), add(sc, copil(330, -1))
    c.walk(0.4, 2.2, -260).do("point", 2.8, 2.0)
    k1.do("raise", 3.2, 1.6).feel("happy", 3.2, 3.0)
    k2.do("jump", 3.6, 0.6).feel("happy", 3.6, 3.0)
    w.pop(D - 5.0, 2.6, "PRIMUL BRAD DIN ROMÂNIA!", W / 2, 200, 48, -0.03)
    c.feel("happy", D - 5.0, 3.0).do("clap", D - 4.6, 1.4)
    return sc


def s6(D):
    D_LATE[0] = D - 5.4
    sc, w = make3("bg_palace_deco", D, 1.3, "fg_deco", 0.5)
    c = add(sc, carol(-330, 1))
    c.do("offer", 0.6, 3.6).feel("happy", 0.6, 4.0)
    b1 = add(sc, boier(520, -1))
    b2 = add(sc, Figure(x=600, face=-1, shirt="#cfc5b0", skirt="#3a2a44", hat="basma", hat_color="#3e5f7a",
                        hair="bun", scale=0.92, name="Boieroaica"))
    b1.walk(5.4, 2.0, 300)
    b2.walk(5.8, 2.0, 410)
    b1.feel("surprised", 7.6, 2.0).do("raise", 7.8, 1.8).talk(7.9, 0.8)
    w.pop(8.0, 2.2, "VREM ȘI NOI!", E.sx(300) - 20, E.head_y() - 30, 52, 0.05)
    b2.do("clap", 8.2, 1.4)
    return sc


def s7(D):
    sc, w = make3("bg_ny", D, 1.3, "fg_ny", 0.55)
    j = add(sc, johnson(330, -1))
    k = add(sc, copil(-330, 1))
    j.do("point", 0.8, 2.0)
    j.do("raise", 3.0, 1.4).talk(3.2, 0.8)
    w.pop(3.4, 2.4, "LUMINIȚE!", W / 2, 150, 64, -0.04, "#ffe7a0")
    k.feel("surprised", 3.4, 2.2).do("shock", 3.4, 1.6)
    k.do("jump", 6.6, 0.6).feel("happy", 6.6, 3.0)
    j.feel("happy", 6.8, 3.0).do("laugh", 7.0, 1.8)
    return sc


def s8(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home_end", 0.6)
    a, b, c = add(sc, ion(-360)), add(sc, bunica(400, -1)), add(sc, copil(170, -1))
    a.feel("happy", 0.6, 5.0).do("clap", 0.8, 1.4)
    b.do("offer", 1.0, 2.6).feel("happy", 1.0, 3.0)
    c.do("jump", 6.6, 0.6).feel("happy", 6.6, 3.0)
    w.pop(6.8, 3.0, "CRĂCIUN FERICIT!", W / 2, 120, 76, -0.03, "#efd9a0")
    a.talk(D - 4.0, 1.0)
    b.do("wave", D - 3.0, 2.0)
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
