"""ToonEngine episode — Povestea Lucrurilor #2: "De unde vine cozonacul?" (silueta style, 16:9).
python3 ep3_cozonac.py [scene ...] [--preview]  -> out/sc_XX.mp4
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
def cozonac(ctx, x, y, s=1.0, sliced=True):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(-60, 0)
    ctx.curve_to(-64, -46, -40, -58, 0, -58)
    ctx.curve_to(40, -58, 64, -46, 60, 0)
    ctx.close_path()
    g = cairo.LinearGradient(0, -58, 0, 0)
    g.add_color_stop_rgb(0, *rgb("#8a4a1e"))
    g.add_color_stop_rgb(0.5, *rgb("#a8632a"))
    g.add_color_stop_rgb(1, *rgb("#6e3a18"))
    ctx.set_source(g)
    ctx.fill()
    ctx.set_source_rgba(1, 0.9, 0.7, 0.25)
    for i in range(14):
        disc(ctx, -40 + (i * 37) % 80, -40 + (i * 13) % 24, 1.6, "#f3e3b8", 0.8)
    if sliced:  # a slice in front showing the swirl
        ctx.save()
        ctx.translate(70, -2)
        rect(ctx, -2, -46, 30, 46, "#e9c98a")
        ctx.set_source_rgb(*rgb("#5a3420"))
        ctx.set_line_width(3)
        for k in range(4):
            ctx.arc(13, -23, 4 + k * 4.5, k, k + 4.6)
            ctx.stroke()
        ctx.restore()
    ctx.restore()


def towel_bread(ctx, x, y):
    cozonac(ctx, x, y, 1.0, sliced=False)
    ctx.move_to(x - 70, y - 30)
    ctx.curve_to(x - 30, y - 70, x + 30, y - 70, x + 70, y - 30)
    ctx.line_to(x + 74, y + 2)
    ctx.line_to(x - 74, y + 2)
    ctx.close_path()
    ctx.set_source_rgba(*rgb("#ddd3bf"), 0.92)
    ctx.fill()
    rect(ctx, x - 74, y - 12, 148, 7, "#8e3a2c")


def fg_home2(ctx, cam, now):
    E.table(ctx, 0, 400)
    k = smooth((now - 3.0) / 1.2)  # the towel is lifted
    if k < 1:
        ctx.save()
        ctx.translate(0, -94 - 40 * k)
        towel_bread(ctx, 0, 0)
        ctx.restore()
    cozonac(ctx, 0, -94)
    if k < 1:
        ctx.save()
        ctx.push_group()
        towel_bread(ctx, 0, -94 - 120 * k)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(1 - k)
        ctx.restore()
    E.candle(ctx, -170, -94, now)
    E.candle(ctx, 170, -94, now)
    for i in range(3):  # walnuts bowl
        disc(ctx, -110 + i * 12, -100, 7, "#7a5a32")


def fg_dough(ctx, cam, now):
    E.table(ctx, -150, 220, cloth="#c9b893", motif="#3f5f4a")
    # bowl with rising dough
    rise = 1 + 0.35 * smooth((now - 2) / 9)
    ctx.save()
    ctx.translate(-150, -94)
    ctx.save()
    ctx.scale(1, rise)
    ctx.arc(0, -10, 50, math.pi, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*rgb("#efe2c2"))
    ctx.fill()
    ctx.move_to(-62, -10)
    ctx.curve_to(-60, 30, 60, 30, 62, -10)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#6e4a2c"))
    ctx.fill()
    ctx.restore()


def fg_ingredients(ctx, cam, now):
    E.table(ctx, -60, 380, cloth="#d9cfba", motif="#8e3a2c")
    items = [(-210, "#7a5a32", "NUCĂ"), (-130, "#3a2418", "CACAO"), (-50, "#6a3a1a", "ROM"),
             (30, "#4a2a3a", "STAFIDE"), (110, "#d98aa0", "RAHAT")]
    for i, (x, col, lab) in enumerate(items):
        a = smooth((now - (1.0 + i * 0.9)) / 0.4)
        if a <= 0:
            continue
        ctx.save()
        ctx.translate(x, -94 - 30 * (1 - a))
        if lab == "ROM":
            rect(ctx, -10, -60, 20, 60, col, a)
            rect(ctx, -4, -76, 8, 18, col, a)
        elif lab == "RAHAT":
            for k in range(5):
                rect(ctx, -22 + (k % 3) * 15, -14 - (k // 3) * 13, 13, 12, col, a)
        else:
            for k in range(6):
                disc(ctx, -16 + (k % 3) * 16, -8 - (k // 3) * 12, 8, col, a)
        text(ctx, lab, 0, -100, 22, "#efd9a0", outline="#1d1a21", a=a, lw=0.16)
        ctx.restore()


def fg_court(ctx, cam, now):
    E.table(ctx, 120, 300, cloth="#d9cfba", motif="#8e3a2c")
    cozonac(ctx, 60, -94, 0.8, sliced=False)
    cozonac(ctx, 190, -94, 0.8)
    E.candle(ctx, 250, -94, now)


def fg_stage(ctx, cam, now):
    rect(ctx, -90, -90, 180, 90, "#3a2a26")
    rect(ctx, -90, -90, 180, 8, "#5a4642")
    cozonac(ctx, -10, -90, 1.1)


def fg_greece(ctx, cam, now):
    E.table(ctx, 40, 240, cloth="#d6cdb9", motif="#2f5a66")
    ctx.save()  # plakous (flat honey cake)
    ctx.translate(10, -98)
    ctx.scale(1, 0.32)
    disc(ctx, 0, 0, 52, "#c98a3a")
    ctx.restore()
    for i in range(7):
        disc(ctx, -30 + i * 10, -100 + (i % 2) * 4, 4, "#6e4a2a")
    ctx.save()  # honey jar
    ctx.translate(120, -94)
    rect(ctx, -20, -46, 40, 46, "#c88a1e")
    rect(ctx, -22, -52, 44, 8, "#8a5a2a")
    ctx.restore()


def fg_eggs(ctx, cam, now):
    E.table(ctx, -120, 300, cloth="#c9b893", motif="#8e3a2c")
    n = int(min(21, max(0, (now - 1.0) * 4.5)))
    for i in range(n):
        x = -250 + (i % 7) * 40
        y = -104 - (i // 7) * 26
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(0.8, 1)
        disc(ctx, 0, 0, 13, "#efe6d4")
        ctx.restore()


# ------------------------------------------------------------------ backgrounds
def bg_greece(ctx, cam, now):
    grad(ctx, [(0, "#9fbfd0"), (0.7, "#ecdcbc"), (1, "#ecdcbc")])
    glow(ctx, W * 0.8, 120, 220, "#fff4d0", 0.6)
    ridge(ctx, GY - 140, 40, "#a8b0a0", 31, 0.6)
    haze(ctx, GY - 110, 60, "#efe4cc", 0.5)
    # temple with columns
    tx = 160
    rect(ctx, tx, GY - 300, 420, 26, "#cfc5b0")
    ctx.move_to(tx - 10, GY - 300)
    ctx.line_to(tx + 210, GY - 360)
    ctx.line_to(tx + 430, GY - 300)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#d8cfbb"))
    ctx.fill()
    for i in range(7):
        x = tx + 18 + i * 62
        rect(ctx, x, GY - 274, 26, 240, "#e2d9c6")
        rect(ctx, x + 18, GY - 274, 8, 240, "#c9bfab")
    rect(ctx, tx - 10, GY - 36, 440, 34, "#cfc5b0")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#a99a7a")
    c = smooth((now - 1.0) / 0.6)
    if c:
        text(ctx, "PLAKOUS", W * 0.8, 90, 58, "#3a2a20", outline=None, font=SERIF, a=c, shadow=False)
        text(ctx, "miere + nuci", W * 0.8, 142, 28, "#5a4030", outline=None, font=SERIF, a=c, shadow=False)


def bg_word2(ctx, cam, now):
    grad(ctx, [(0, "#3b3647"), (0.55, "#b9785a"), (0.85, "#d79a68")])
    glow(ctx, W * 0.5, GY - 60, 430, "#ffdca0", 0.55)
    ridge(ctx, GY - 120, 40, "#7c5a5c", 4, 0.8)
    haze(ctx, GY - 90, 60, "#d9a27a", 0.45)
    ridge(ctx, GY - 50, 30, "#5d4446", 9)
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#4a3630")
    a = smooth((now - 0.8) / 0.6)
    if a:
        text(ctx, "κοσωνάκι", W / 2, 115, 84, "#efd9a0", outline=None, font="DejaVu Serif", a=a)
        b = smooth((now - 2.6) / 0.5)
        if b:
            text(ctx, "= păpușică", W / 2, 190, 42, "#f4ecd8", outline=None, font=SERIF, a=b)


def fg_word2(ctx, cam, now):
    E.table(ctx, -160, 200, cloth="#c9b893", motif="#3f5f4a")
    # doll-shaped bread
    ctx.save()
    ctx.translate(-160, -94)
    ctx.move_to(-26, 0)
    ctx.curve_to(-34, -50, -20, -66, 0, -66)
    ctx.curve_to(20, -66, 34, -50, 26, 0)
    ctx.close_path()
    ctx.set_source_rgb(*rgb("#a8632a"))
    ctx.fill()
    disc(ctx, 0, -78, 16, "#a8632a")
    rect(ctx, -30, -36, 60, 10, "#ddd3bf")
    ctx.restore()


def bg_court(ctx, cam, now):
    grad(ctx, [(0, "#3a2a2a"), (1, "#2a1e1e")], 0, GY)
    for x in (120, 520, 920):  # arches with brâncovenesc decor
        ctx.save()
        ctx.move_to(x, GY - 40)
        ctx.line_to(x, 210)
        ctx.arc(x + 110, 210, 110, math.pi, 2 * math.pi)
        ctx.line_to(x + 220, GY - 40)
        ctx.close_path()
        ctx.clip()
        grad(ctx, [(0, "#5a4038"), (1, "#3a2a26")], 100, GY)
        ctx.set_source_rgba(*rgb("#c9a24a"), 0.16)
        for j in range(8):
            for i in range(5):
                ctx.arc(x + 22 + i * 44, 130 + j * 48, 12, 0, 2 * math.pi)
                ctx.fill()
        ctx.restore()
    for x in (110, 510, 910, 1130):
        rect(ctx, x, 90, 20, GY - 90, "#4a3630")
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#2e221e")
    glow(ctx, W * 0.6, GY - 120, 420, "#ffb15e", 0.22)
    c = smooth((now - 0.8) / 0.5)
    if c:
        text(ctx, "1703", W * 0.86, 90, 62, "#efd9a0", outline=None, font=SERIF, a=c)
        text(ctx, "CURTEA LUI BRÂNCOVEANU", W * 0.86, 138, 20, "#f4ecd8", outline=None, font=SERIF, a=c)


def bg_stage(ctx, cam, now):
    rect(ctx, 0, 0, W, H, "#1a1418")
    for side in (0, 1):  # curtains
        x0 = 0 if side == 0 else W - 190
        g = cairo.LinearGradient(x0, 0, x0 + 190, 0)
        g.add_color_stop_rgb(0, *rgb("#5a1a1e"))
        g.add_color_stop_rgb(0.5, *rgb("#8a2a2a"))
        g.add_color_stop_rgb(1, *rgb("#4a1418"))
        ctx.set_source(g)
        ctx.rectangle(x0, 0, 190, H)
        ctx.fill()
    rect(ctx, 0, 0, W, 50, "#6a1e22")
    # spotlight
    ctx.move_to(W / 2 - 60, 0)
    ctx.line_to(W / 2 + 60, 0)
    ctx.line_to(W / 2 + 260, GY)
    ctx.line_to(W / 2 - 260, GY)
    ctx.close_path()
    g = cairo.LinearGradient(0, 0, 0, GY)
    g.add_color_stop_rgba(0, 1, 0.95, 0.8, 0.25)
    g.add_color_stop_rgba(1, 1, 0.95, 0.8, 0.08)
    ctx.set_source(g)
    ctx.fill()
    rect(ctx, 0, GY - 4, W, H - GY + 4, "#4a3426")
    glow(ctx, W / 2, GY, 280, "#fff0c8", 0.25)
    c = smooth((now - 0.8) / 0.5)
    if c:
        text(ctx, "CAFÉ EUROPE · 2006", W / 2, 110, 46, "#efd9a0", outline=None, font=SERIF, a=c)
    d = smooth((now - 6.4) / 0.4)
    if d:
        text(ctx, "ROMÂNIA:", W / 2, 175, 34, "#f4ecd8", outline=None, font=SERIF, a=d)


# ------------------------------------------------------------------ cast
def grec(x, face=1, name="Grec"):
    return Figure(x=x, face=face, shirt="#d9d0bc", belt="#2f5a66", hair="tuft", beard=True, name=name)


def chiaro(x, face=1):
    return Figure(x=x, face=face, hat="beret", beard=True, shirt="#2c2a34", belt="#5a3a22", vest="#3a2a44",
                  name="DelChiaro")


def voda(x, face=-1):
    return Figure(x=x, face=face, hat="crown", beard=True, shirt="#6a2a2a", belt="#c9a24a", vest="#2a2a44",
                  name="Voda")


# ------------------------------------------------------------------ scenes
def s0(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home2", 0.6)
    a, b, c = add(sc, ion(-300)), add(sc, bunica(290, -1)), add(sc, copil(-410))
    b.do("offer", 2.6, 2.2)
    c.do("jump", 3.4, 0.55).do("raise", 3.4, 1.8).feel("happy", 3.4, 2.2).talk(3.5, 0.9)
    w.pop(3.5, 1.8, "COZONAC!", E.sx(-410), E.head_y(1.3, 0.7) - 30, 54, -0.08)
    a.feel("happy", 3.6, 2.0).do("clap", 3.8, 1.4)
    a.do("think", 7.6, 3.0).look(7.6, 3.0, 0.3, -0.8)
    c.do("shrug", 9.0, 1.6)
    w.pop(D - 3.6, 3.4, "DE UNDE VINE COZONACUL?", W / 2, 118, 66, -0.02, "#efd9a0")
    return sc


def s1(D):
    sc, w = make3("bg_word2", D, 1.3, "fg_word2", 0.5)
    g = add(sc, grec(60, -1))
    g.do("wave", 0.4, 1.2).do("point", 2.0, 2.2).talk(2.1, 0.9)
    g.do("offer", 5.6, 2.6)
    k = add(sc, copil(330, -1))
    k.feel("surprised", 9.6, 2.4).do("shock", 9.6, 1.8).talk(9.7, 0.9)
    w.pop(9.8, 2.2, "PĂPUȘI DULCI?!", E.sx(330) - 20, E.head_y(1.3, 0.7) - 30, 52, 0.05)
    g.do("laugh", 10.4, 1.8).feel("happy", 10.4, 2.0)
    return sc


def s2(D):
    sc, w = make3("bg_greece", D, 1.3, "fg_greece", 0.4)
    a = add(sc, grec(-280, 1, "G1"))
    b = add(sc, Figure(x=330, face=-1, shirt="#d9d0bc", belt="#8e3a2c", hair="bun", skirt="#b8ae98", name="G2"))
    a.walk(0.4, 1.8, -140).do("point", 2.4, 1.6)
    b.do("stir", 1.0, 3.0)
    a.do("eat", 6.0, 2.6).feel("happy", 6.0, 3.0)
    w.pop(6.6, 1.8, "MMM, MIERE!", E.sx(-140), E.head_y() - 20, 48, -0.06)
    b.do("nod", 9.6, 1.4)
    a.do("shrug", 11.0, 1.8)
    return sc


def s3(D):
    sc, w = make3("bg_court", D, 1.3, "fg_court", 0.55)
    d = add(sc, chiaro(-420, 1))
    v = add(sc, voda(430, -1))
    d.walk(0.3, 2.4, -170).do("bow", 2.9, 1.2)
    v.do("offer", 3.6, 2.2).feel("happy", 3.6, 2.4)
    d.do("eat", 5.6, 2.0).feel("happy", 5.6, 2.4)
    d.do("think", 8.0, 2.0)
    d.do("raise", 10.2, 1.8).talk(10.3, 1.0).feel("happy", 10.2, 2.0)
    w.pop(10.3, 2.4, "PANETTONE!", E.sx(-170), E.head_y() - 25, 58, -0.05)
    v.do("nod", 11.0, 1.4)
    return sc


def s4(D):
    sc, w = make3("bg_oven", D, 1.3, "fg_eggs", 0.55)
    b = add(sc, bunica(120, -1))
    k = add(sc, copil(300, -1))
    b.do("point", 1.0, 2.4)
    k.feel("surprised", 5.6, 2.4).do("shock", 5.6, 2.0).talk(5.7, 0.8)
    w.pop(5.8, 2.2, "21 DE OUĂ?!", E.sx(300) - 20, E.head_y(1.3, 0.7) - 30, 54, 0.05)
    b.do("hips", 9.0, 3.0).feel("happy", 9.0, 3.0)
    c = smooth(1)
    return sc


def s5(D):
    sc, w = make3("bg_oven", D, 1.3, "fg_ingredients", 0.55)
    b = add(sc, bunica(300, -1))
    b.do("offer", 0.8, 4.0).feel("happy", 0.8, 5.0)
    b.do("stir", 6.0, 3.0)
    b.do("hips", 10.0, 3.0)
    w.pop(10.4, 2.4, "AL NOSTRU!", E.sx(300) + 10, E.head_y(1.3, 0.94) - 30, 56, 0.04)
    return sc


def s6(D):
    sc, w = make3("bg_oven", D, 1.3, "fg_dough", 0.6)
    b = add(sc, bunica(60, -1))
    a = add(sc, ion(520, -1))
    k = add(sc, copil(680, -1))
    b.do("stir", 0.6, 4.0)
    a.walk(4.6, 5.0, 330, "walk")
    k.walk(5.0, 5.0, 440, "walk")
    b.turn(6.0, 1).do("fist", 6.4, 1.6).talk(6.5, 0.8).feel("angry", 6.4, 2.0)
    w.pop(6.5, 2.0, "ȘȘȘT!", E.sx(60) + 30, E.head_y(1.3, 0.94) - 30, 64, -0.06)
    a.feel("surprised", 6.6, 2.0)
    k.feel("surprised", 6.6, 2.0)
    return sc


def s7(D):
    sc, w = make3("bg_stage", D, 1.3, "fg_stage", 0.45)
    p = add(sc, Figure(x=-330, face=1, hat="tophat", shirt="#2a2a33", belt="#5a3a22", name="Prezentator"))
    p.do("point", 2.0, 2.0).talk(2.1, 1.2)
    p.do("raise", 6.4, 2.4).feel("happy", 6.4, 2.6)
    w.pop(6.6, 2.6, "COZONACUL!", W / 2, 232, 60, -0.03, "#efd9a0")
    return sc


def s8(D):
    sc, w = make3("bg_home", D, 1.3, "fg_home2", 0.6)
    a, b, c = add(sc, ion(-300)), add(sc, bunica(290, -1)), add(sc, copil(-410))
    b.do("offer", 0.6, 3.0).feel("happy", 0.6, 3.0)
    a.do("eat", 3.6, 2.6).feel("happy", 3.6, 5.0)
    c.do("eat", 4.0, 2.6)
    c.do("jump", 8.6, 0.6).feel("happy", 8.6, 3.0)
    a.talk(8.6, 1.0)
    w.pop(8.6, 3.0, "POFTĂ BUNĂ!", W / 2, 130, 84, -0.03, "#efd9a0")
    b.do("wave", 12.0, 2.0)
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
