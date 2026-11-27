import math, random
import skia
from eng import *
import common
from common import keys, Cam, layer, talk_at, captions, FPS, CHUNKS

ALBERT = Look(shirt='#9cc3e0', coat='#6b3fa0', pants='#3d4f66', shoes='#2a2420', hair='grey', glasses=True,
              brows='#8f8a86', stache=False)
ALBERT_OLD = Look(**{**ALBERT.__dict__})
DOCTOR = Look(shirt='#7fb3c9', coat='#f6f6f4', tie='#3a6ea5', pants='#3d4f66', shoes='#2a2a2e', hair='side', hair_col='#3a2a22', glasses=False)
DOCTOR2 = Look(shirt='#d98a9a', coat='#f6f6f4', pants='#3d4f66', shoes='#2a2a2e', hair='bun', hair_col='#6b3f24')
NURSE = Look(shirt='#6fb3a8', pants='#6fb3a8', shoes='#f1f1f1', hair='pony', hair_col='#2a1d16')
KIDS = [Look(shirt='#9ad0f0', pants='#9ad0f0', hair='short', hair_col='#3b2a20', kid=True),
        Look(shirt='#f3b6c8', pants='#f3b6c8', hair='pony', hair_col='#c79a5a', kid=True, bow='#e05a7a'),
        Look(shirt='#b8e0a8', pants='#b8e0a8', hair='curly', hair_col='#1f1712', kid=True),
        Look(shirt='#ffd98a', pants='#ffd98a', hair='long', hair_col='#6b3f24', kid=True),
        Look(shirt='#c9b6f0', pants='#c9b6f0', hair='short', hair_col='#8a5a32', kid=True)]

PURPLE = '#7a4bb0'

def cart(c, x, y, s=1.0, jar=0.0):
    """purple shoeshine cart; jar = fill level 0..1"""
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 230, 36, 110)
    pc = hexc(PURPLE)
    box3d(c, -190, -330, 380, 260, pc, r=18)
    for i in range(2):
        rr(c, -165, -300 + i * 120, 330, 95, 10, color=shade(pc, -.12))
        rr(c, -30, -265 + i * 120, 60, 14, 7, color=hexc('e8c86a'))
    rr(c, -200, -350, 400, 30, 10, shader=lin(0, -350, 0, -320, [shade(pc, .3), shade(pc, -.1)]))
    # foot rest
    c.drawLine(110, -350, 110, -440, paint(hexc('3a3a40'), stroke=14))
    ellipse(c, 110, -448, 70, 20, color=hexc('2e2e34'))
    # handle
    c.drawLine(-190, -300, -270, -470, paint(hexc('3a3a40'), stroke=14))
    c.drawLine(-290, -470, -250, -470, paint(hexc('3a3a40'), stroke=18))
    for wx in (-130, 130):
        c.drawCircle(wx, -60, 58, paint(hexc('242226')))
        c.drawCircle(wx, -60, 24, paint(hexc('b9bcbf')))
    # tip jar
    if jar >= 0:
        jx, jy = -70, -350
        c.save(); c.translate(jx, jy)
        glass = skia.Path(); glass.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-55, -150, 110, 150), 18, 18))
        c.save(); c.clipPath(glass, doAntiAlias=True)
        fh = 150 * clamp(jar)
        c.drawRect(skia.Rect.MakeXYWH(-55, -fh, 110, fh), paint(shader=lin(0, -fh, 0, 0, [hexc('8fd18a'), hexc('4f9a4a')])))
        for k in range(int(10 * jar)):
            rr(c, -45 + (k * 37) % 80, -fh + 6 + (k * 23) % max(1, int(fh - 10) if fh > 12 else 1), 34, 14, 3, color=alpha(hexc('2f6e2c'), 160))
        c.restore()
        c.drawPath(glass, paint(alpha(hexc('dff2ff'), 70)))
        c.drawPath(glass, paint(alpha(skia.ColorWHITE, 180), stroke=5))
        c.drawLine(-38, -130, -38, -30, paint(alpha(skia.ColorWHITE, 150), stroke=8))
        rr(c, -60, -165, 120, 22, 6, color=hexc('c9ccd0'))
        rr(c, -64, -105, 128, 46, 6, color=hexc('fff6e0'))
        text(c, 'FREE CARE', 0, -88, 22, hexc('7a4bb0'))
        text(c, 'FUND', 0, -66, 22, hexc('7a4bb0'))
        c.restore()
    c.restore()

def money(c, x, y, val, s=1.0, rot=0, glow_=0.0):
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    if glow_ > 0: glow(c, 0, 0, 220, hexc('fff2a0'), int(200 * glow_))
    rr(c, -110, -50, 220, 100, 8, shader=lin(0, -50, 0, 50, [hexc('cfe8c0'), hexc('8fbf7a')]))
    rr(c, -98, -38, 196, 76, 6, color=None, stroke=0)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-98, -38, 196, 76), 6, 6), paint(hexc('3f7a38'), stroke=4))
    c.drawCircle(0, 0, 26, paint(hexc('a8d098')))
    text(c, str(val), -70, 14, 34, hexc('2f5e2a')); text(c, str(val), 70, 14, 34, hexc('2f5e2a'))
    c.restore()

def corridor(c, t, xmas=False, banner=None):
    wall(c, -400, 1260, hexc('d6ebe2'), None, None)
    c.drawRect(skia.Rect.MakeLTRB(-400, 880, W + 400, 1260), paint(hexc('b9d8cc')))
    c.drawRect(skia.Rect.MakeLTRB(-400, 870, W + 400, 890), paint(hexc('8fbfae')))
    for i, dx in enumerate((-120, 560)):
        rr(c, dx, 520, 260, 740, 8, shader=lin(dx, 0, dx + 260, 0, [hexc('f1e6d2'), hexc('d9c9ae')]))
        rr(c, dx + 70, 590, 120, 160, 6, color=hexc('bfe0f0'))
        c.drawCircle(dx + 225, 920, 14, paint(hexc('c9a13b')))
    # kids' drawings
    rnd = random.Random(5)
    for i in range(6):
        x = 170 + i * 75 + (i // 3) * 260; y = 420 + (i % 2) * 120
        if 300 < x < 560 or x > 900: continue
        rr(c, x, y, 110, 90, 3, color=hexc('fffdf6'))
        col = hexc(rnd.choice(['f0a050', '5a9ae0', 'e05a7a', '6ab85a']))
        c.drawCircle(x + 30, y + 30, 16, paint(hexc('ffd34a')))
        c.drawLine(x + 20, y + 70, x + 90, y + 60, paint(col, stroke=6))
        c.drawCircle(x + 70, y + 45, 12, paint(col))
    if xmas:
        for k in range(14):
            xx = -60 + k * 90
            c.drawCircle(xx, 180 + 30 * math.sin(k * 0.8), 12, paint(hexc(['ff5a5a', 'ffd34a', '5ad07a', '5aa0ff'][k % 4])))
            glow(c, xx, 180 + 30 * math.sin(k * 0.8), 40, hexc(['ff5a5a', 'ffd34a', '5ad07a', '5aa0ff'][k % 4]), 110 if (k + int(t * 3)) % 2 else 50)
        c.drawPath(path([(900, 1250), (1010, 860), (1120, 1250)]), paint(shader=lin(0, 860, 0, 1250, [hexc('5aa05a'), hexc('2f6e3a')])))
        c.drawPath(path([(930, 1050), (1010, 760), (1090, 1050)]), paint(hexc('4f9a4f')))
        c.drawCircle(1010, 750, 22, paint(hexc('ffd34a')))
    if banner:
        rr(c, 120, 230, 840, 150, 20, shader=lin(0, 230, 0, 380, [hexc('ffd98a'), hexc('f0a850')]))
        text(c, banner, 540, 330, 76, hexc('6b3fa0'))
    baseboard(c, 1260, '#8fbfae')
    floor(c, 1260, 2600, hexc('e6e2d6'), boards=False)
    for i in range(-10, 30):
        c.drawLine(-400, 1260 + i * 70, W + 400, 1260 + i * 70, paint(alpha(hexc('c9c3b3'), 90), stroke=3))
    c.drawRect(skia.Rect.MakeLTRB(-400, 1260, W + 400, 2600), paint(shader=lin(0, 1260, 0, 1800, [alpha(skia.ColorWHITE, 0), alpha(skia.ColorWHITE, 50)])))

def bed(c, x, y, s=1.0, kid=None, t=0, expr='happy', seed=0):
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 230, 30, 90)
    c.drawLine(-200, 0, -200, -380, paint(hexc('b9bcbf'), stroke=16))
    c.drawLine(200, 0, 200, -260, paint(hexc('b9bcbf'), stroke=16))
    rr(c, -210, -230, 420, 90, 20, color=hexc('f4f4f8'))
    if kid:
        c.save(); c.translate(-60, -60); draw_char(c, 0, 0, Look(**{**kid.__dict__, 'scale': 0.9}), t=t, expr=expr, look=(0.3, -0.2), shadow=False, blink_seed=seed, pose={'r': 150, 'rb': -30} if expr == 'happy' else None); c.restore()
    rr(c, -210, -200, 420, 120, 26, shader=lin(0, -200, 0, -80, [hexc('9ad0f0'), hexc('6aa8d0')]))
    ellipse(c, -150, -260, 60, 30, color=hexc('ffffff'))
    c.restore()

# =========================================================== shots
def b1(c, t, T):  # pre-dawn arrival
    cam = Cam(*keys(t, [(0, 1.0, 0, 300, 0), (6.9, 1.12, 60, 380, 0)]), t=t)
    def far(c):
        c.drawRect(skia.Rect.MakeLTRB(-500, -800, W + 500, 1500), paint(shader=lin(0, -600, 0, 1300, [hexc('1c2550'), hexc('f0a070')])))
        rnd = random.Random(3)
        for i in range(40): c.drawCircle(rnd.uniform(-200, 1300), rnd.uniform(-300, 600), rnd.uniform(1.5, 3.5), paint(alpha(skia.ColorWHITE, int(120 + 100 * math.sin(t * 2 + i)))))
        c.drawCircle(860, 200, 50, paint(hexc('fff4d6')))
        # hospital building
        hc = hexc('d9d2c6')
        box3d(c, 80, 560, 920, 800, hc, r=6)
        for r_ in range(5):
            for k in range(6):
                lit = (r_ * 7 + k * 3) % 5 != 0
                rr(c, 130 + k * 145, 620 + r_ * 130, 90, 80, 6, color=hexc('ffe2a0') if lit else hexc('5a6a8a'))
                if lit: glow(c, 175 + k * 145, 660 + r_ * 130, 80, hexc('ffd27a'), 60)
        rr(c, 380, 470, 320, 100, 10, color=hexc('c0392b'))
        text(c, "CHILDREN'S", 540, 512, 40, skia.ColorWHITE); text(c, 'HOSPITAL', 540, 556, 40, skia.ColorWHITE)
        rr(c, 440, 1160, 200, 200, 10, color=hexc('9fc6e0'))
        glow(c, 540, 1260, 200, hexc('ffe8b0'), 120)
    def mid(c):
        c.drawRect(skia.Rect.MakeLTRB(-500, 1350, W + 500, 2600), paint(shader=lin(0, 1350, 0, 2000, [hexc('6a6a78'), hexc('4a4a58')])))
        # street lamp
        c.drawLine(940, 1700, 940, 1000, paint(hexc('2a2a30'), stroke=16))
        glow(c, 940, 1000, 260, hexc('ffd98a'), 150); c.drawCircle(940, 1000, 30, paint(hexc('fff2c8')))
        wx = -30 + t * 80
        cart(c, wx + 330, 1820, 0.85, jar=0.15)
        draw_char(c, wx, 1830, ALBERT, t=t, walk=t * 1.6, look=(1, 0), pose={'r': 75, 'rb': -10}, blink_seed=0.4)
    layer(c, cam, 0.8, 5, far)
    layer(c, cam, 1.0, 0, mid)

def b2(c, t, T):  # corridor, doctor passes
    cam = Cam(*keys(t, [(0, 1.05, 0, 330, 0), (3.0, 1.12, 0, 350, 0)]), t=t)
    def bg(c): corridor(c, t)
    def mid(c):
        cart(c, 640, 1800, 1.0, jar=0.2)
        draw_char(c, 330, 1810, ALBERT, t=t, expr='happy', look=(0.6, 0), pose={'r': 60, 'rb': 20}, blink_seed=1.0)
        d = ramp(T, 8.5, 9.9)
        if 0 < d < 1:
            draw_char(c, 1250 - d * 1700, 1950, Look(**{**DOCTOR.__dict__, 'scale': 1.15}), t=t, walk=t * 2, look=(-1, 0), face=-1)
    layer(c, cam, 0.85, 6, bg)
    layer(c, cam, 1.0, 0, mid)

def b3(c, t, T):  # shoe shine close-up + $5
    cam = Cam(1.0, 0, 0, 0, creep=0.006, t=t)
    def bg(c):
        c.save(); c.translate(W / 2, 1100); c.scale(1.6, 1.6); c.translate(-W / 2, -1100); corridor(c, t); c.restore()
    def mid(c):
        # big shoe
        c.save(); c.translate(540, 1300); c.scale(2.2, 2.2)
        sc_ = hexc('3a2418')
        p = skia.Path(); p.moveTo(-220, 40); p.cubicTo(-230, -60, -150, -110, -60, -100); p.lineTo(40, -60); p.cubicTo(160, -50, 230, -10, 230, 40); p.close()
        c.drawPath(p, paint(shader=lin(0, -110, 0, 40, [shade(sc_, .35), sc_, shade(sc_, -.3)], [0, .45, 1])))
        rr(c, -230, 30, 470, 30, 10, color=hexc('1e1410'))
        shine = clamp((t - 0.6) / 2.0)
        ellipse(c, -40, -60, 90, 18, color=alpha(skia.ColorWHITE, int(60 + 150 * shine)), blur=4)
        c.drawLine(-120, -95, -60, -100, paint(alpha(skia.ColorWHITE, int(200 * shine)), stroke=6))
        c.drawPath(path([(-60, -100), (-30, -70), (0, -100)], False), paint(hexc('e8dcc6'), stroke=4))
        # trouser leg
        rr(c, -170, -420, 200, 330, 20, shader=lin(-170, 0, 30, 0, [hexc('5a6a8a'), hexc('3a4660')]))
        c.restore()
        # brush
        bx = 540 + math.sin(t * 16) * 160
        c.save(); c.translate(bx, 1120); c.rotate(-8)
        rr(c, -120, -40, 240, 70, 18, shader=lin(0, -40, 0, 30, [hexc('b9875a'), hexc('7a5236')]))
        for k in range(16): c.drawLine(-105 + k * 14, 30, -105 + k * 14, 70, paint(hexc('3a2a20'), stroke=6))
        c.restore()
        # hand holding brush
        c.drawCircle(bx + 10, 1080, 40, paint(hexc('f0eee8')))
        sparkle(c, 380, 1150, 70, ramp(t, 1.4, 1.8) * (1 - ramp(t, 2.6, 2.9)), rot=t * 60)
        a = ramp(T, 11.1, 11.4)
        if a > 0:
            c.save(); c.translate(820, 620); s_ = back_out(a); c.scale(s_, s_); c.rotate(6)
            rr(c, -170, -110, 340, 220, 24, color=hexc('7a4bb0'))
            rr(c, -150, -90, 300, 180, 18, color=hexc('fff6e0'))
            text(c, '$5', 0, 30, 110, hexc('7a4bb0')); text(c, 'SHINE', 0, 80, 34, hexc('7a4bb0'))
            c.restore()
    layer(c, cam, 0.8, 12, bg)
    layer(c, cam, 1.0, 0, mid)

def b4(c, t, T):  # $10,000 a year
    cam = Cam(1.0, 0, 0, 0, creep=0.006, t=t)
    def bg(c):
        c.save(); c.translate(W / 2, 1100); c.scale(1.5, 1.5); c.translate(-W / 2 + 120, -1100); corridor(c, t); c.restore()
    def mid(c):
        c.save(); c.translate(540, 1100); c.scale(2.1, 2.1); c.translate(-540, -1100)
        draw_char(c, 470, 1440, ALBERT, t=t, expr='happy', look=(0.4, 0), pose={'r': 40}, blink_seed=0.2, shadow=False)
        c.restore()
        a = ramp(T, 13.4, 13.75)
        if a > 0:
            c.save(); c.translate(780, 520); s_ = back_out(a); c.scale(s_, s_)
            rr(c, -230, -100, 460, 200, 20, color=hexc('fffdf6'))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-230, -100, 460, 200), 20, 20), paint(hexc('3f7a38'), stroke=6))
            text(c, '~$10,000', 0, 20, 84, hexc('2f5e2a')); text(c, 'a year', 0, 72, 40, hexc('5a5a5a'))
            c.restore()
    layer(c, cam, 0.8, 12, bg)
    layer(c, cam, 1.0, 0, mid)

def b5(c, t, T):  # $6 -> extra dollar to jar
    cam = Cam(*keys(t, [(0, 1.1, 0, 330, 0), (4.1, 1.18, 0, 350, 0)]), t=t)
    fly = ss(ramp(T, 17.9, 18.8))
    def bg(c): corridor(c, t)
    def mid(c):
        cart(c, 560, 1820, 1.0, jar=0.25 + 0.05 * fly)
        draw_char(c, 280, 1830, ALBERT, t=t, expr='happy', look=(1, -0.3), pose={'r': 95, 'rb': 0}, blink_seed=0.7)
        draw_char(c, 880, 1860, DOCTOR, t=t, expr='happy', look=(-1, -0.2), face=-1, pose={'l': 95, 'lb': 0}, blink_seed=1.3)
        give = ss(ramp(T, 15.6, 16.3))
        x5 = 720 - 200 * give; y5 = 1300
        money(c, x5, y5, 5, 0.9, rot=-6)
        g1 = ramp(T, 17.3, 17.7)
        x1 = (740 - 180 * give) * (1 - fly) + 490 * fly
        y1 = (1210) * (1 - fly) + 1380 * fly - 260 * math.sin(fly * math.pi)
        if fly < 1: money(c, x1, y1, 1, 0.9 * (1 - 0.6 * fly), rot=8 + 300 * fly, glow_=g1 * (1 - fly))
        if T > 18.8: sparkle(c, 490, 1370, 60, 1 - ramp(T, 18.8, 19.3), rot=t * 50)
    layer(c, cam, 0.85, 7, bg)
    layer(c, cam, 1.0, 0, mid)

def b6(c, t, T):  # jar close-up then kids ward
    if T < 22.3:
        cam = Cam(1.0, 0, 0, 0, creep=0.006, t=t)
        def bg(c):
            c.save(); c.translate(W / 2, 1100); c.scale(1.5, 1.5); c.translate(-W / 2, -1100); corridor(c, t); c.restore()
        def mid(c):
            c.save(); c.translate(540, 2050); c.scale(2.6, 2.6); c.translate(70, 0)
            cart(c, 0, 0, 1.0, jar=0.3 + 0.1 * ramp(T, 19.4, 22.3))
            c.restore()
            rnd = random.Random(int(T * 2))
            for k in range(3):
                ft = ((T - 19.4) * 1.2 + k / 3) % 1
                money(c, 540 + (k - 1) * 120, 300 + ft * 700, 1, 0.8, rot=ft * 200 + k * 40)
        layer(c, cam, 0.8, 12, bg); layer(c, cam, 1.0, 0, mid)
    else:
        cam = Cam(1.25, 0, 420, 0, creep=0.005, t=t)
        def bg(c):
            wall(c, -400, 1300, hexc('f4e6d8'), 'stripes', hexc('ead6c2'))
            window(c, 360, 260, 360, 400, '#bfe0ff', '#ffe8c8')
            baseboard(c, 1300); floor(c, 1300, 2600, hexc('e6e2d6'), boards=False)
        def mid(c):
            bed(c, 270, 1700, 1.0, KIDS[0], t, 'happy', 0.2)
            bed(c, 820, 1720, 1.0, KIDS[1], t, 'happy', 1.1)
            draw_char(c, 540, 1980, NURSE, t=t, expr='happy', look=(0, -0.3), pose={'l': 40, 'r': 40}, blink_seed=0.6)
        layer(c, cam, 0.85, 6, bg); layer(c, cam, 1.0, 0, mid)

def b7(c, t, T):  # counter $1 $100 $1,000
    cam = Cam(*keys(t, [(0, 1.0, 0, 0, 0), (3.9, 1.1, 0, -20, 0)]), t=t, kicks=(26.57 - 25.1, 27.7 - 25.1))
    vals = [(25.1, '$1'), (26.55, '$100'), (27.68, '$1,000')]
    v, at = vals[0][1], vals[0][0]
    for tt, s_ in vals:
        if T >= tt: v, at = s_, tt
    lvl = {'$1': 0.1, '$100': 0.45, '$1,000': 0.85}[v]
    def bg(c):
        c.drawRect(skia.Rect.MakeLTRB(-500, -800, W + 500, 2600), paint(shader=rad(540, 900, 1400, [hexc('efe2ff'), hexc('b89ad8')])))
        for i in range(12):
            ang = i / 12 * math.pi * 2 + t * 0.2
            c.drawPath(path([(540, 1000), (540 + math.cos(ang) * 1800, 1000 + math.sin(ang) * 1800), (540 + math.cos(ang + .2) * 1800, 1000 + math.sin(ang + .2) * 1800)]), paint(alpha(skia.ColorWHITE, 40)))
    def mid(c):
        c.save(); c.translate(540, 2150); c.scale(3.0, 3.0); c.translate(70, 0)
        cart(c, 0, 0, 1.0, jar=lvl)
        c.restore()
        pop = clamp((T - at) / 0.3); s_ = 1 + 0.3 * (1 - back_out(pop))
        c.save(); c.translate(540, 560); c.scale(s_, s_)
        text(c, v, 0, 60, 200, skia.ColorWHITE, stroke=16, scolor=hexc('4a2a7a')); c.restore()
    layer(c, cam, 0.8, 0, bg); layer(c, cam, 1.0, 0, mid)

def b8(c, t, T):  # Christmas $50
    cam = Cam(*keys(t, [(0, 1.1, 0, 330, 0), (4.8, 1.2, 0, 350, 0)]), t=t)
    fly = ss(ramp(T, 32.6, 33.4))
    def bg(c): corridor(c, t, xmas=True)
    def mid(c):
        cart(c, 560, 1820, 1.0, jar=0.85 + 0.1 * fly)
        surprised = T > 31.2
        draw_char(c, 280, 1830, ALBERT, t=t, expr='shock' if 31.2 < T < 32.4 else 'happy', look=(1, -0.3), pose={'r': 95}, blink_seed=0.3)
        draw_char(c, 880, 1860, DOCTOR2, t=t, expr='happy', look=(-1, -0.2), face=-1, pose={'l': 95}, blink_seed=1.7)
        give = ss(ramp(T, 30.6, 31.3))
        x = (740 - 260 * give) * (1 - fly) + 490 * fly
        y = 1260 * (1 - fly) + 1380 * fly - 280 * math.sin(fly * math.pi)
        if fly < 1: money(c, x, y, 50, 1.1 * (1 - 0.6 * fly), rot=-4 + 300 * fly, glow_=ramp(T, 31.2, 31.6) * (1 - fly))
        if T > 33.4: sparkle(c, 490, 1370, 80, 1 - ramp(T, 33.4, 33.9), rot=t * 50)
    layer(c, cam, 0.85, 7, bg); layer(c, cam, 1.0, 0, mid)

def b9(c, t, T):  # 30 years time-lapse
    cam = Cam(1.05, 0, 250, 0, creep=0.005, t=t)
    yr = int(1981 + 32 * ss(ramp(T, 34.0, 36.4)))
    def bg(c): corridor(c, t)
    def mid(c):
        from common import keys as _k
        rr(c, 690, 560, 300, 360, 10, color=hexc('f7f3ea'))
        rr(c, 690, 560, 300, 90, 10, color=hexc('7a4bb0'))
        text(c, str(yr), 840, 628, 64, skia.ColorWHITE)
        for i in range(5):
            for j in range(4): rr(c, 714 + i * 52, 680 + j * 56, 40, 40, 6, color=hexc('e3dccd'))
        k = ramp(T, 34.0, 36.4)
        L = Look(**{**ALBERT.__dict__, 'hair_col': '#8a8580'})
        cart(c, 640, 1800, 1.0, jar=0.6)
        draw_char(c, 330, 1810, L, t=t, expr='happy', look=(0.6, 0.3), pose={'r': 70 + 30 * math.sin(t * 14), 'rb': 30}, blink_seed=0.5)
    layer(c, cam, 0.9, 5, bg); layer(c, cam, 1.0, 0, mid)

def b10(c, t, T):  # retirement, $202,000
    cam = Cam(*keys(t, [(0, 1.0, 0, 200, 0), (6.0, 1.1, 0, 180, 0)]), t=t, kicks=(41.15 - 36.62,))
    a = ramp(T, 40.35, 40.8)
    def bg(c): corridor(c, t, banner='THANK YOU, ALBERT!')
    def mid(c):
        for i, (x, L) in enumerate([(130, DOCTOR), (930, NURSE), (790, DOCTOR2)]):
            draw_char(c, x, 1760 - (i == 2) * 40, Look(**{**L.__dict__, 'scale': 0.85}), t=t, expr='happy', look=(0, 0), pose={'r': 150 + 15 * math.sin(t * 6 + i), 'rb': -20} if T > 41 else None, blink_seed=i)
        draw_char(c, 470, 1880, ALBERT, t=t, expr='happy', look=(0, -0.3), blink_seed=0.4)
        if a > 0:
            c.save(); c.translate(540, 780); s_ = back_out(a); c.scale(s_, s_); c.rotate(-3)
            rr(c, -400, -150, 800, 300, 16, color=hexc('fffdf2'))
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-400, -150, 800, 300), 16, 16), paint(hexc('7a4bb0'), stroke=8))
            text(c, 'FREE CARE FUND', 0, -80, 40, hexc('7a4bb0'))
            text(c, '$202,000', 0, 50, 130, hexc('2f5e2a'))
            c.restore()
            rnd = random.Random(2)
            for i in range(30):
                ct = T - 40.4
                x = rnd.uniform(0, W) + 40 * math.sin(ct * 3 + i); y = -50 + (ct * rnd.uniform(250, 450) + rnd.uniform(0, 200))
                c.save(); c.translate(x, y); c.rotate(ct * 200 + i * 30)
                rr(c, -10, -5, 20, 10, 2, color=hexc(['ff5a5a', 'ffd34a', '5ad07a', '5aa0ff', 'c07aff'][i % 5])); c.restore()
    layer(c, cam, 0.85, 6, bg); layer(c, cam, 1.0, 0, mid)

def b11(c, t, T):  # one third of earnings
    cam = Cam(1.0, 0, 0, 0, creep=0.004, t=t)
    a = ramp(T, 42.9, 43.5)
    def bg(c):
        c.drawRect(skia.Rect.MakeLTRB(-500, -800, W + 500, 2600), paint(shader=rad(540, 900, 1400, [hexc('fbf4e6'), hexc('e2cfa8')])))
    def mid(c):
        cx, cy, r = 540, 800, 330
        c.drawCircle(cx, cy, r, paint(hexc('d9cdb3')))
        p = skia.Path(); p.moveTo(cx, cy); p.arcTo(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), -90, 120 * ss(a), False); p.close()
        c.drawPath(p, paint(shader=rad(cx, cy, r, [hexc('8fd18a'), hexc('4f9a4a')])))
        c.drawCircle(cx, cy, r, paint(hexc('7a6a50'), stroke=6))
        if a > 0.6:
            text(c, '1/3', cx + 150, cy - 40, 90, skia.ColorWHITE, stroke=10, scolor=hexc('2f5e2a'))
        text(c, 'EVERYTHING HE EARNED', 540, 1260, 52, hexc('5a4a30'))
    layer(c, cam, 0.9, 0, bg); layer(c, cam, 1.0, 0, mid)

def b12(c, t, T):  # "I love my kids" CU
    cam = Cam(1.0, 0, 0, 0, creep=0.006, t=t)
    if T > 48.3: cam.z *= 1 + 0.05 * ss(ramp(T, 48.3, 48.6))
    def bg(c):
        c.save(); c.translate(W / 2, 1100); c.scale(1.6, 1.6); c.translate(-W / 2, -1100); corridor(c, t); c.restore()
    def mid(c):
        c.save(); c.translate(540, 1100); c.scale(2.3, 2.3); c.translate(-540, -1100)
        draw_char(c, 520, 1440, ALBERT, t=t, expr='happy' if T < 48.3 or T > 49.8 else 'neutral', talk=talk_at(T, [(48.3, 49.8)]), look=(0.2, -0.1), blink_seed=0.9, shadow=False)
        c.restore()
        if T > 49.6:
            for i in range(3):
                ht = T - 49.6 - i * 0.2
                if ht > 0:
                    hx = 720 + i * 90; hy = 600 - ht * 160
                    c.save(); c.translate(hx, hy); c.scale(1 + 0.2 * math.sin(ht * 6), 1 + 0.2 * math.sin(ht * 6))
                    p = skia.Path(); p.moveTo(0, 30); p.cubicTo(-60, -10, -40, -60, 0, -30); p.cubicTo(40, -60, 60, -10, 0, 30)
                    c.drawPath(p, paint(alpha(hexc('ff5a7a'), int(255 * clamp(1 - ht / 1.5)))))
                    c.restore()
    layer(c, cam, 0.8, 12, bg); layer(c, cam, 1.0, 0, mid)

def b13(c, t, T):  # patients -> Albert's kids
    cam = Cam(*keys(t, [(0, 1.15, 0, -100, 0), (2.0, 1.15, 0, -100, 0), (3.2, 1.0, 0, 40, 0), (8.5, 1.05, 0, 40, 0)]), t=t)
    def bg(c):
        wall(c, -400, 1300, hexc('f4e6d8'), 'stripes', hexc('ead6c2'))
        # big sign changes
        rr(c, 140, 300, 800, 230, 20, color=hexc('fffdf6'))
        if T < 52.5:
            text(c, 'PATIENTS', 540, 450, 110, hexc('5a6a7a'))
        else:
            k = ramp(T, 52.5, 52.9)
            text(c, "ALBERT'S KIDS", 540, 450, 104, alpha(hexc('7a4bb0'), int(255 * k)))
            for i in range(10):
                glow(c, 160 + i * 85, 300, 30, hexc(['ff5a5a', 'ffd34a', '5ad07a', '5aa0ff', 'c07aff'][i % 5]), int(160 * k))
        rnd = random.Random(8)
        for i in range(10):
            x = 60 + (i % 5) * 200; y = 620 + (i // 5) * 170
            rr(c, x, y, 150, 130, 4, color=hexc('fffdf6'))
            col = hexc(rnd.choice(['f0a050', '5a9ae0', 'e05a7a', '6ab85a', '7a4bb0']))
            c.drawCircle(x + 75, y + 50, 26, paint(col))
            c.drawLine(x + 75, y + 76, x + 75, y + 115, paint(col, stroke=6))
            p = skia.Path(); p.moveTo(x + 110, y + 40); p.cubicTo(x + 100, y + 25, x + 125, y + 20, x + 120, y + 40); p.lineTo(x + 115, y + 52); p.close()
            c.drawPath(p, paint(hexc('ff5a7a')))
        baseboard(c, 1300); floor(c, 1300, 2600, hexc('e6e2d6'), boards=False)
        glow(c, 540, 1300, 600, hexc('ffe2a8'), 60)
    def mid(c):
        draw_char(c, 540, 1800, ALBERT, t=t, expr='happy', look=(0, -0.2), pose={'l': 60, 'r': 60}, blink_seed=0.3)
        for i, (x, y) in enumerate([(170, 1840), (330, 1900), (750, 1900), (910, 1840), (440, 2010)]):
            a = ramp(T, 52.7 + i * 0.15, 53.1 + i * 0.15)
            if a <= 0: continue
            draw_char(c, x, y + 120 * (1 - back_out(a)), Look(**{**KIDS[i].__dict__, 'scale': 0.95}), t=t, expr='happy', look=((540 - x) / 400, -0.5),
                      pose={'r': 150 + 20 * math.sin(t * 7 + i), 'rb': -20} if i % 2 == 0 else {'l': 150 + 20 * math.sin(t * 7 + i), 'lb': -20}, blink_seed=i)
    layer(c, cam, 0.85, 4, bg); layer(c, cam, 1.0, 0, mid)

SHOTS = [(0.0, 6.92, b1), (6.92, 9.89, b2), (9.89, 12.77, b3), (12.77, 15.21, b4), (15.21, 19.35, b5), (19.35, 25.1, b6),
         (25.1, 29.05, b7), (29.05, 33.9, b8), (33.9, 36.62, b9), (36.62, 42.69, b10), (42.69, 45.3, b11), (45.3, 50.38, b12),
         (50.38, 58.6, b13)]
XFADE = {29.05: 0.3, 33.9: 0.3, 36.62: 0.3, 50.38: 0.35}
FLASH = 6.92
TOTAL = 58.6
