"""Tiny 2.5D cartoon engine on skia: soft-shaded props, bean-head characters, DOF layers."""
import math, random
import skia

W, H = 1080, 1920
FONT_BOLD = skia.Typeface.MakeFromFile('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf')
FONT_CHALK = skia.Typeface.MakeFromFile('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf')

def hexc(h, a=255):
    h = h.lstrip('#')
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def mix(c1, c2, t):
    a = [skia.ColorGetR(c1), skia.ColorGetG(c1), skia.ColorGetB(c1), skia.ColorGetA(c1)]
    b = [skia.ColorGetR(c2), skia.ColorGetG(c2), skia.ColorGetB(c2), skia.ColorGetA(c2)]
    return skia.Color(*[int(a[i] + (b[i] - a[i]) * t) for i in range(4)])

def shade(c, k):  # k<0 darker, k>0 lighter
    return mix(c, skia.ColorBLACK if k < 0 else skia.ColorWHITE, abs(k))

def alpha(c, a):
    return skia.ColorSetA(c, int(a))

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))

def ss(x):  # smoothstep
    x = clamp(x); return x * x * (3 - 2 * x)

def sms(x):  # smootherstep
    x = clamp(x); return x * x * x * (x * (x * 6 - 15) + 10)

def ramp(t, a, b):
    return clamp((t - a) / (b - a)) if b != a else float(t >= a)

def back_out(x, s=1.7):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

def paint(color=None, shader=None, stroke=0, aa=True, blur=0, cap=None):
    p = skia.Paint(AntiAlias=aa)
    if color is not None: p.setColor(color)
    if shader is not None: p.setShader(shader)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(cap or skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p

def lin(x0, y0, x1, y1, cols, pos=None):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], cols, pos)

def rad(x, y, r, cols, pos=None):
    return skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 1), cols, pos)

def rr(c, x, y, w, h, r, color=None, shader=None, stroke=0, blur=0):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint(color, shader, stroke, blur=blur))

def box3d(c, x, y, w, h, base, r=14, light=0.18, dark=0.22):
    """Soft 'rendered' box: vertical gradient + top highlight + bottom AO."""
    rr(c, x, y, w, h, r, shader=lin(x, y, x, y + h, [shade(base, light), base, shade(base, -dark)], [0, 0.45, 1]))
    rr(c, x + w * 0.06, y + 3, w * 0.88, min(10, h * 0.2), r * 0.5, color=alpha(skia.ColorWHITE, 50))

def ellipse(c, cx, cy, rx, ry, color=None, shader=None, stroke=0, blur=0):
    c.drawOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry), paint(color, shader, stroke, blur=blur))

def cshadow(c, cx, cy, rx, ry=None, a=90):
    ry = ry or rx * 0.22
    ellipse(c, cx, cy, rx, ry, color=skia.Color(30, 20, 30, a), blur=rx * 0.18)

def path(pts, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    return p

def text(c, s, x, y, size, color, font=None, align='center', stroke=0, scolor=None, skew=0):
    f = skia.Font(font or FONT_BOLD, size)
    if skew: f.setSkewX(skew)
    wdt = f.measureText(s)
    if align == 'center': x -= wdt / 2
    elif align == 'right': x -= wdt
    blob = skia.TextBlob.MakeFromString(s, f)
    if stroke:
        p = paint(scolor or skia.ColorBLACK, stroke=stroke); c.drawTextBlob(blob, x, y, p)
    c.drawTextBlob(blob, x, y, paint(color))
    return wdt

def glow(c, x, y, r, col, a=120):
    c.drawCircle(x, y, r, paint(shader=rad(x, y, r, [alpha(col, a), alpha(col, 0)])))

def sparkle(c, x, y, s, a=1.0, rot=0):
    if a <= 0: return
    c.save(); c.translate(x, y); c.rotate(rot)
    glow(c, 0, 0, s * 1.6, skia.ColorWHITE, int(150 * a))
    p = skia.Path()
    for i in range(4):
        ang = i * math.pi / 2
        p.moveTo(0, 0); p.lineTo(math.cos(ang - 0.18) * s * 0.18, math.sin(ang - 0.18) * s * 0.18)
        p.lineTo(math.cos(ang) * s, math.sin(ang) * s)
        p.lineTo(math.cos(ang + 0.18) * s * 0.18, math.sin(ang + 0.18) * s * 0.18); p.close()
    c.drawPath(p, paint(alpha(skia.ColorWHITE, int(255 * a))))
    c.restore()

# ---------------------------------------------------------------- characters
INK = hexc('1d1a1f')

class Look:
    def __init__(self, shirt='#c0392b', pants='#3d5a80', shoes='#3b2a20', hat=None, hair=None, hair_col='#4a3326',
                 stache=False, glasses=False, tie=None, plaid=None, coat=None, gradcap=False, skin='#f4f2ee',
                 brows='#2a2224', bag=None, scale=1.0, kid=False, bow=None, stache_col='#d9d6d2', scarf=None, beard=None):
        self.__dict__.update(locals()); del self.__dict__['self']

def draw_head(c, cx, cy, R, L, expr='neutral', talk=0.0, blink=False, look=(0, 0), tilt=0):
    c.save(); c.translate(cx, cy); c.rotate(tilt)
    # soft shadow behind head onto neck
    ellipse(c, 6, R * 0.92, R * 0.7, R * 0.22, color=skia.Color(0, 0, 0, 60), blur=R * 0.12)
    skin = hexc(L.skin)
    # hair behind (long hair / ponytail)
    if L.hair in ('long', 'pony', 'bun'):
        hc = hexc(L.hair_col)
        if L.hair == 'long':
            rr(c, -R * 1.02, -R * 0.55, R * 2.04, R * 1.55, R * 0.6, shader=lin(0, -R, 0, R, [shade(hc, .15), shade(hc, -.25)]))
        if L.hair == 'pony':
            ellipse(c, R * 0.95, -R * 0.1, R * 0.32, R * 0.62, shader=lin(0, -R, 0, R, [shade(hc, .1), shade(hc, -.3)]))
        if L.hair == 'bun':
            c.drawCircle(0, -R * 1.02, R * 0.36, paint(shader=rad(-R * .1, -R * 1.1, R * .4, [shade(hc, .15), shade(hc, -.2)])))
    # bean head
    hp = skia.Path(); hp.addOval(skia.Rect.MakeLTRB(-R, -R * 1.05, R, R * 0.95))
    c.drawPath(hp, paint(shader=rad(-R * 0.35, -R * 0.45, R * 1.75,
                                     [shade(skin, .25), skin, shade(skin, -.10), mix(skin, hexc('b9b6c6'), .55)], [0, .35, .75, 1])))
    # rim light
    c.drawPath(hp, paint(alpha(skia.ColorWHITE, 60), stroke=R * 0.04))
    # eyes
    ex, ey = look[0] * R * 0.1, look[1] * R * 0.08
    eye_y = -R * 0.12 + ey
    for sx in (-1, 1):
        x = sx * R * 0.3 + ex
        if blink or expr == 'closed':
            c.drawPath(path([(x - R * .1, eye_y), (x, eye_y + R * .05), (x + R * .1, eye_y)], False), paint(INK, stroke=R * .045))
        elif expr == 'shock':
            ellipse(c, x, eye_y, R * .12, R * .15, color=skia.ColorWHITE); ellipse(c, x, eye_y, R * .12, R * .15, color=INK, stroke=R * .03)
            c.drawCircle(x, eye_y, R * .05, paint(INK))
        elif expr == 'happy':
            c.drawPath(path([(x - R * .1, eye_y + R * .03), (x, eye_y - R * .06), (x + R * .1, eye_y + R * .03)], False), paint(INK, stroke=R * .05))
        else:
            ellipse(c, x, eye_y, R * .075, R * .11, color=INK)
            c.drawCircle(x - R * .025, eye_y - R * .04, R * .025, paint(alpha(skia.ColorWHITE, 200)))
    # brows
    bc = hexc(L.brows)
    bro = {'neutral': (0, 0), 'sad': (-.10, .03), 'shock': (0, -.08), 'happy': (0, -.03), 'worried': (-.12, 0),
           'smug': (.06, 0), 'closed': (-.05, 0), 'think': (.08, -.02)}.get(expr, (0, 0))
    for sx in (-1, 1):
        x = sx * R * .3 + ex; y = eye_y - R * .25 + bro[1] * R
        tl = bro[0] * R * sx
        c.drawPath(path([(x - R * .12, y + tl), (x + R * .12, y - tl)], False), paint(bc, stroke=R * .055))
    # glasses
    if L.glasses:
        for sx in (-1, 1):
            c.drawCircle(sx * R * .3 + ex, eye_y, R * .2, paint(hexc('2d2a30'), stroke=R * .04))
            c.drawCircle(sx * R * .3 + ex, eye_y, R * .2, paint(alpha(skia.ColorWHITE, 35)))
        c.drawLine(-R * .1 + ex, eye_y, R * .1 + ex, eye_y, paint(hexc('2d2a30'), stroke=R * .04))
    # moustache
    my = R * 0.28 + ey * 0.5
    if L.stache:
        sc = hexc(L.stache_col)
        for sx in (-1, 1):
            ellipse(c, sx * R * .16 + ex * .6, my, R * .2, R * .09, shader=lin(0, my - R * .1, 0, my + R * .1, [shade(sc, .2), shade(sc, -.25)]))
    # mouth
    mx, mY = ex * 0.6, R * 0.42 + ey * 0.5
    if expr == 'shock' or talk > 0.05:
        o = max(talk, 0.55 if expr == 'shock' else 0)
        rx, ry = R * (0.13 + 0.05 * o), R * (0.05 + 0.17 * o)
        ellipse(c, mx, mY, rx, ry, color=hexc('3a1418'))
        ellipse(c, mx, mY + ry * 0.45, rx * 0.65, ry * 0.4, color=hexc('d65a63'))
    elif expr in ('happy', 'smug'):
        p = skia.Path(); p.moveTo(mx - R * .2, mY - R * .03); p.quadTo(mx, mY + R * .2, mx + R * .2, mY - R * .03)
        if expr == 'happy':
            p.quadTo(mx, mY + R * .05, mx - R * .2, mY - R * .03); c.drawPath(p, paint(hexc('3a1418')))
        else:
            c.drawPath(p, paint(INK, stroke=R * .045))
    elif expr in ('sad', 'worried'):
        p = skia.Path(); p.moveTo(mx - R * .14, mY + R * .05); p.quadTo(mx, mY - R * .07, mx + R * .14, mY + R * .05)
        c.drawPath(p, paint(INK, stroke=R * .045))
    else:
        c.drawLine(mx - R * .1, mY, mx + R * .1, mY, paint(INK, stroke=R * .045))
    # hair on top
    if L.hair:
        hc = hexc(L.hair_col)
        hs = lin(0, -R * 1.1, 0, -R * 0.3, [shade(hc, .18), shade(hc, -.15)])
        if L.hair in ('short', 'pony', 'long', 'bun'):
            p = skia.Path(); p.moveTo(-R * .98, -R * .25)
            p.cubicTo(-R * 1.0, -R * 1.25, R * 1.0, -R * 1.3, R * .98, -R * .25)
            p.cubicTo(R * .6, -R * .62, R * .1, -R * .5, -R * .1, -R * .72)
            p.cubicTo(-R * .4, -R * .5, -R * .7, -R * .55, -R * .98, -R * .25); p.close()
            c.drawPath(p, paint(shader=hs))
        elif L.hair == 'curly':
            for i in range(9):
                a = math.pi * (1.05 + i * 0.112)
                c.drawCircle(math.cos(a) * R * .88, math.sin(a) * R * .9 - R * .1, R * .3, paint(shader=hs))
        elif L.hair == 'side':
            p = skia.Path(); p.moveTo(-R * .97, -R * .2)
            p.cubicTo(-R * 1.05, -R * 1.3, R * 1.05, -R * 1.3, R * .97, -R * .2)
            p.cubicTo(R * .8, -R * .65, -R * .2, -R * .78, -R * .45, -R * .6)
            p.cubicTo(-R * .7, -R * .45, -R * .85, -R * .35, -R * .97, -R * .2); p.close()
            c.drawPath(p, paint(shader=hs))
        elif L.hair == 'grey':
            for sx in (-1, 1):
                ellipse(c, sx * R * .9, -R * .05, R * .17, R * .3, shader=lin(0, -R * .3, 0, R * .3, [hexc('e4e2e0'), hexc('a9a6a4')]))
    if L.bow:
        bc2 = hexc(L.bow)
        for sx in (-1, 1):
            c.drawPath(path([(R * .55, -R * .85), (R * .55 + sx * R * .28, -R * .85 - R * .18), (R * .55 + sx * R * .28, -R * .85 + R * .18)]), paint(bc2))
        c.drawCircle(R * .55, -R * .85, R * .09, paint(shade(bc2, -.2)))
    # hats
    if L.hat == 'cap':
        hc = hexc('7a5a3a')
        p = skia.Path(); p.moveTo(-R * 1.0, -R * .42)
        p.cubicTo(-R * 1.05, -R * 1.35, R * 1.0, -R * 1.4, R * 1.02, -R * .45); p.close()
        c.drawPath(p, paint(shader=lin(0, -R * 1.3, 0, -R * .4, [shade(hc, .2), shade(hc, -.25)])))
        p2 = skia.Path(); p2.moveTo(-R * .9, -R * .45); p2.quadTo(-R * .2, -R * .12, R * .55, -R * .42); p2.quadTo(0, -R * .5, -R * .9, -R * .45)
        c.drawPath(p2, paint(shade(hc, -.35)))
        c.drawLine(-R * .2, -R * 1.15, R * .4, -R * .55, paint(alpha(shade(hc, -.3), 140), stroke=R * .03))
    if L.hat == 'church':
        c.translate(0, -R * 0.28)
        hc = hexc('3b3a44')
        ellipse(c, 0, -R * .72, R * 1.35, R * .2, shader=lin(0, -R * .9, 0, -R * .55, [shade(hc, .15), shade(hc, -.3)]))
        rr(c, -R * .72, -R * 1.45, R * 1.44, R * .78, R * .22, shader=lin(0, -R * 1.45, 0, -R * .7, [shade(hc, .2), shade(hc, -.2)]))
        rr(c, -R * .72, -R * .92, R * 1.44, R * .16, 3, color=hexc('8a2b2b'))
    if L.gradcap:
        gc = hexc('1f2533')
        c.drawPath(path([(-R * 1.15, -R * .95), (0, -R * 1.3), (R * 1.15, -R * .95), (0, -R * .62)]), paint(shader=lin(0, -R * 1.3, 0, -R * .6, [shade(gc, .25), gc])))
        rr(c, -R * .55, -R * .9, R * 1.1, R * .3, R * .1, color=shade(gc, -.2))
        c.drawLine(0, -R * .96, R * .85, -R * .75, paint(hexc('f1c40f'), stroke=R * .05))
        c.drawLine(R * .85, -R * .75, R * .88, -R * .35, paint(hexc('f1c40f'), stroke=R * .06))
    c.restore()

def limb(c, x0, y0, x1, y1, w, col):
    c.drawLine(x0, y0, x1, y1, paint(shade(col, -.25), stroke=w + 3))
    c.drawLine(x0 - w * .12, y0 - w * .1, x1 - w * .12, y1 - w * .1, paint(col, stroke=w * .8))

def draw_char(c, x, y, L, t=0.0, expr='neutral', talk=0.0, pose=None, walk=0.0, face=0, look=(0, 0), tilt=0,
              seated=False, blink_seed=0.0, held=None, shadow=True):
    """x,y = feet center on ground. pose: dict of arm angles in degrees (l, r): 0 = down, 90 = forward/out."""
    s = L.scale * (0.82 if L.kid else 1.0)
    c.save(); c.translate(x, y); c.scale(s, s)
    if shadow: cshadow(c, 0, 0, 120, 26, 85)
    pose = pose or {}
    bob = -abs(math.sin(walk * math.pi)) * 10 if walk else 0
    c.translate(0, bob)
    R = 118 if not L.kid else 124
    leg_len = 150 if not L.kid else 110
    hip_y = -leg_len
    torso_h = 170 if not L.kid else 130
    sh_y = hip_y - torso_h + 30
    # legs
    pcol = hexc(L.pants)
    sw = math.sin(walk * math.pi * 2) * 28 if walk else 0
    for sx, ph in ((-1, sw), (1, -sw)):
        if seated:
            limb(c, sx * 34, hip_y, sx * 34 + 95 * (1 if face >= 0 else -1), hip_y + 6, 58, pcol)
            limb(c, sx * 34 + 95 * (1 if face >= 0 else -1), hip_y + 6, sx * 34 + 95 * (1 if face >= 0 else -1), -14, 54, pcol)
            fx = sx * 34 + 95 * (1 if face >= 0 else -1)
            ellipse(c, fx + 18, -12, 42, 20, shader=lin(0, -30, 0, 0, [shade(hexc(L.shoes), .2), hexc(L.shoes)]))
        else:
            limb(c, sx * 34, hip_y, sx * 34 + ph, -22, 58, pcol)
            ellipse(c, sx * 36 + ph + sx * 10, -16, 46, 21, shader=lin(0, -36, 0, 0, [shade(hexc(L.shoes), .25), hexc(L.shoes)]))
    # torso
    sc = hexc(L.coat or L.shirt)
    rr(c, -82, sh_y, 164, torso_h + 12, 58, shader=lin(-82, sh_y, 82, sh_y + torso_h, [shade(sc, .2), sc, shade(sc, -.3)], [0, .4, 1]))
    if L.plaid:
        c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-82, sh_y, 164, torso_h + 12), 58, 58), doAntiAlias=True)
        pc = hexc(L.plaid)
        for i in range(-4, 5):
            c.drawLine(i * 38, sh_y, i * 38, sh_y + torso_h + 20, paint(alpha(pc, 120), stroke=9))
        for j in range(0, 8):
            c.drawLine(-90, sh_y + j * 38, 90, sh_y + j * 38, paint(alpha(pc, 110), stroke=9))
        c.restore()
    if L.coat:  # open coat over shirt + tie
        wc = hexc(L.shirt)
        c.drawPath(path([(-30, sh_y + 2), (30, sh_y + 2), (0, sh_y + 120)]), paint(shade(wc, .05)))
        if L.tie:
            tc = hexc(L.tie)
            c.drawPath(path([(-11, sh_y + 10), (11, sh_y + 10), (16, sh_y + 95), (0, sh_y + 118), (-16, sh_y + 95)]), paint(shader=lin(0, sh_y, 0, sh_y + 110, [shade(tc, .2), shade(tc, -.2)])))
        c.drawPath(path([(-30, sh_y + 2), (-6, sh_y + 70), (-44, sh_y + 40)]), paint(shade(sc, -.12)))
        c.drawPath(path([(30, sh_y + 2), (6, sh_y + 70), (44, sh_y + 40)]), paint(shade(sc, -.12)))
    elif L.tie:
        tc = hexc(L.tie)
        c.drawPath(path([(-10, sh_y + 8), (10, sh_y + 8), (14, sh_y + 80), (0, sh_y + 98), (-14, sh_y + 80)]), paint(tc))
    # belt
    if not L.kid and not L.coat:
        rr(c, -80, hip_y - 14, 160, 18, 6, color=hexc('3a2a20'))
        rr(c, -12, hip_y - 15, 24, 20, 4, color=hexc('c9a13b'))
    # arms
    aw = 46 if not L.kid else 40
    la = math.radians(pose.get('l', 8 + (math.sin(walk * math.pi * 2) * 18 if walk else 0)))
    ra = math.radians(pose.get('r', 8 - (math.sin(walk * math.pi * 2) * 18 if walk else 0)))
    alen = 150 if not L.kid else 115
    hands = []
    for sx, ang, key in ((-1, la, 'l'), (1, ra, 'r')):
        bx, by = sx * 78, sh_y + 36
        ex_ = bx + sx * math.sin(ang) * alen * 0.55; ey_ = by + math.cos(ang) * alen * 0.55
        bend = math.radians(pose.get(key + 'b', 0))
        hx = ex_ + sx * math.sin(ang + bend) * alen * 0.5; hy = ey_ + math.cos(ang + bend) * alen * 0.5
        limb(c, bx, by, ex_, ey_, aw, sc)
        limb(c, ex_, ey_, hx, hy, aw * 0.92, sc)
        hands.append((hx, hy))
        c.drawCircle(hx, hy, aw * 0.5, paint(shader=rad(hx - 6, hy - 6, aw * .7, [shade(hexc(L.skin), .2), mix(hexc(L.skin), hexc('b9b6c6'), .5)])))
    if L.scarf:
        gc = hexc('f4efe4'); rc = hexc(L.scarf)
        p = skia.Path(); p.moveTo(-70, sh_y + 6); p.quadTo(0, sh_y + 60, 70, sh_y + 6); p.lineTo(64, sh_y + 30); p.quadTo(0, sh_y + 84, -64, sh_y + 30); p.close()
        c.drawPath(p, paint(shader=lin(0, sh_y, 0, sh_y + 80, [gc, shade(gc, -.15)])))
        c.drawPath(p, paint(rc, stroke=6))
        for sx in (-1,):
            rr(c, sx * 40 - 22, sh_y + 30, 44, 130, 10, shader=lin(0, sh_y + 30, 0, sh_y + 160, [gc, shade(gc, -.18)]))
            rr(c, sx * 40 - 22, sh_y + 138, 44, 14, 4, color=rc)
    if held: held(c, hands)
    # head
    blink = ((t + blink_seed) % 3.1) < 0.12
    draw_head(c, face * 6, sh_y - R * 0.72, R, L, expr=expr, talk=talk, blink=blink, look=look, tilt=tilt)
    c.restore()
    return hands

# ---------------------------------------------------------------- rooms & props
def wall(c, top, bot, col, pattern=None, pcol=None):
    c.drawRect(skia.Rect.MakeLTRB(-400, top, W + 400, bot), paint(shader=lin(0, top, 0, bot, [shade(col, -.08), shade(col, .08), shade(col, -.12)], [0, .55, 1])))
    if pattern == 'stripes':
        for i in range(-10, 40):
            c.drawRect(skia.Rect.MakeXYWH(i * 70, top, 30, bot - top), paint(alpha(pcol, 40)))
    if pattern == 'planks':
        for i in range(-10, 40):
            c.drawLine(i * 110, top, i * 110, bot, paint(alpha(pcol, 90), stroke=5))
    if pattern == 'brick':
        rows = int((bot - top) / 60) + 1
        for r in range(rows):
            yy = top + r * 60
            c.drawLine(-400, yy, W + 400, yy, paint(alpha(pcol, 70), stroke=4))
            off = 0 if r % 2 else 70
            for i in range(-6, 22):
                c.drawLine(i * 140 + off, yy, i * 140 + off, yy + 60, paint(alpha(pcol, 70), stroke=4))

def floor(c, top, bot, col, boards=True, bcol=None):
    c.drawRect(skia.Rect.MakeLTRB(-400, top, W + 400, bot), paint(shader=lin(0, top, 0, bot, [shade(col, -.15), shade(col, .08)])))
    if boards:
        bc = bcol or shade(col, -.25)
        n = 14
        for i in range(-n, n + 1):
            x0 = W / 2 + i * 60; x1 = W / 2 + i * 260
            c.drawLine(x0, top, x1, bot, paint(alpha(bc, 90), stroke=3))
    # AO at wall join
    c.drawRect(skia.Rect.MakeLTRB(-400, top, W + 400, top + 60), paint(shader=lin(0, top, 0, top + 60, [skia.Color(0, 0, 0, 70), skia.Color(0, 0, 0, 0)])))

def baseboard(c, y, col='#efe6d8'):
    bc = hexc(col)
    c.drawRect(skia.Rect.MakeLTRB(-400, y - 34, W + 400, y), paint(shader=lin(0, y - 34, 0, y, [shade(bc, .1), shade(bc, -.2)])))

def window(c, x, y, w, h, sky_top='#9fc6ea', sky_bot='#f6e3c2', frame='#f3ede2', t=0, night=False):
    fc = hexc(frame)
    rr(c, x - 22, y - 22, w + 44, h + 44, 10, shader=lin(x, y, x, y + h, [shade(fc, .1), shade(fc, -.15)]))
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), paint(shader=lin(x, y, x, y + h, [hexc(sky_top), hexc(sky_bot)])))
    # distant trees / houses silhouettes
    for i in range(6):
        cx = x + (i + 0.5) * w / 6
        c.drawCircle(cx, y + h * 0.85, w * 0.13, paint(alpha(hexc('7fa37a' if not night else '2e3d4f'), 160)))
    c.drawLine(x + w / 2, y, x + w / 2, y + h, paint(fc, stroke=16))
    c.drawLine(x, y + h / 2, x + w, y + h / 2, paint(fc, stroke=16))
    rr(c, x - 40, y + h + 14, w + 80, 26, 6, shader=lin(0, y + h + 14, 0, y + h + 40, [shade(fc, .1), shade(fc, -.25)]))

def light_shaft(c, x, y, w, h, ang=18, a=40, col='#fff3d6'):
    p = path([(x, y), (x + w, y), (x + w + h * math.tan(math.radians(ang)), y + h), (x + h * math.tan(math.radians(ang)), y + h)])
    c.drawPath(p, paint(shader=lin(0, y, 0, y + h, [alpha(hexc(col), a), alpha(hexc(col), 0)]), blur=20))

def frame_pic(c, x, y, w, h, inner='#a9c4d8', fcol='#6b4a33', draw=None):
    rr(c, x + 8, y + 10, w, h, 6, color=skia.Color(0, 0, 0, 60), blur=10)
    rr(c, x, y, w, h, 6, shader=lin(x, y, x + w, y + h, [shade(hexc(fcol), .2), shade(hexc(fcol), -.2)]))
    c.drawRect(skia.Rect.MakeXYWH(x + 14, y + 14, w - 28, h - 28), paint(hexc(inner)))
    if draw:
        c.save(); c.clipRect(skia.Rect.MakeXYWH(x + 14, y + 14, w - 28, h - 28)); draw(c, x + 14, y + 14, w - 28, h - 28); c.restore()

def plant(c, x, y, s=1.0, pot='#c96f4a'):
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 70, 16, 80)
    rr(c, -55, -110, 110, 110, 18, shader=lin(-55, 0, 55, 0, [shade(hexc(pot), .15), shade(hexc(pot), -.25)]))
    rr(c, -62, -122, 124, 26, 10, color=shade(hexc(pot), .08))
    g = hexc('5e9c5a')
    for i, (lx, ly, rx_, ry_, rot) in enumerate([(-50, -200, 30, 80, -30), (40, -210, 30, 85, 28), (0, -250, 32, 95, 0), (-70, -150, 26, 60, -55), (70, -155, 26, 60, 55)]):
        c.save(); c.translate(lx, ly); c.rotate(rot)
        ellipse(c, 0, 0, rx_, ry_, shader=lin(-rx_, 0, rx_, 0, [shade(g, .2), shade(g, -.25)]))
        c.drawLine(0, -ry_ * .8, 0, ry_ * .8, paint(alpha(shade(g, -.35), 150), stroke=3))
        c.restore()
    c.restore()

def lamp(c, x, y, s=1.0, on=True):
    c.save(); c.translate(x, y); c.scale(s, s)
    if on: glow(c, 0, -230, 260, hexc('ffd99a'), 90)
    c.drawLine(0, 0, 0, -200, paint(hexc('3b3530'), stroke=10))
    ellipse(c, 0, 0, 60, 14, color=hexc('3b3530'))
    c.drawPath(path([(-70, -170), (70, -170), (45, -280), (-45, -280)]), paint(shader=lin(0, -280, 0, -170, [hexc('fff1cf'), hexc('f2c879')])))
    c.restore()

def bookshelf(c, x, y, w, h, seed=3):
    rnd = random.Random(seed)
    wood = hexc('7b5236')
    box3d(c, x, y, w, h, wood, r=8)
    shelves = 4
    for i in range(shelves):
        sy = y + 20 + i * (h - 40) / shelves
        sh_ = (h - 40) / shelves
        c.drawRect(skia.Rect.MakeXYWH(x + 16, sy, w - 32, sh_ - 14), paint(shade(wood, -.45)))
        bx = x + 22
        while bx < x + w - 50:
            bw = rnd.randint(18, 34); bh = sh_ * rnd.uniform(.55, .85)
            col = hexc(rnd.choice(['b5523b', '3e6b8a', 'd9a441', '5d8a5a', '8a4f7d', 'e8dcc6', '2f4858']))
            rr(c, bx, sy + sh_ - 14 - bh, bw, bh, 3, shader=lin(bx, 0, bx + bw, 0, [shade(col, .15), shade(col, -.25)]))
            bx += bw + 3

def desk(c, x, y, w, h, wood='#8a5a3a'):
    wc = hexc(wood)
    cshadow(c, x + w / 2, y + h, w * 0.55, 30, 90)
    box3d(c, x + 20, y + 30, w - 40, h - 30, shade(wc, -.15), r=10)
    rr(c, x, y, w, 46, 10, shader=lin(0, y, 0, y + 46, [shade(wc, .25), shade(wc, -.1)]))
    for i in range(2):
        rr(c, x + 60 + i * (w - 240), y + 80, 120, 60, 8, color=shade(wc, -.05))
        rr(c, x + 100 + i * (w - 240), y + 104, 40, 10, 5, color=hexc('c9a13b'))

def lunchbox(c, x, y, s=1.0, shine=0.0, open_=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 130, 24, 110)
    m = hexc('6f8b8f')
    # body (dome lunch pail)
    p = skia.Path(); p.moveTo(-120, 0); p.lineTo(-120, -110); p.cubicTo(-120, -190, 120, -190, 120, -110); p.lineTo(120, 0); p.close()
    c.drawPath(p, paint(shader=lin(-120, 0, 120, 0, [shade(m, .25), m, shade(m, -.3)], [0, .35, 1])))
    c.drawPath(p, paint(shade(m, -.45), stroke=4))
    c.drawLine(-120, -110, 120, -110, paint(shade(m, -.4), stroke=5))
    # scratches / dents
    for (a, b, cc, d) in [(-80, -50, -40, -60), (30, -30, 70, -25), (-20, -140, 20, -150)]:
        c.drawLine(a, b, cc, d, paint(alpha(skia.ColorWHITE, 70), stroke=3))
    ellipse(c, 60, -70, 18, 12, color=alpha(shade(m, -.4), 120))
    # rust spots
    for (a, b, r_) in [(-90, -20, 12), (95, -40, 9), (-30, -12, 8)]:
        c.drawCircle(a, b, r_, paint(alpha(hexc('9a5a32'), 170), blur=2))
    # latches + handle
    for sx in (-1, 1):
        rr(c, sx * 70 - 12, -122, 24, 30, 4, color=hexc('c7c9c8'))
    hp = skia.Path(); hp.moveTo(-60, -170); hp.cubicTo(-60, -235, 60, -235, 60, -170)
    c.drawPath(hp, paint(hexc('3d3a38'), stroke=12))
    # top highlight
    c.drawPath(path([(-100, -120), (-70, -165), (-50, -168), (-80, -118)]), paint(alpha(skia.ColorWHITE, 70)))
    c.restore()
    if shine > 0: sparkle(c, x - 70 * s, y - 150 * s, 70 * s, shine, rot=shine * 40)

def jeans_item(c, x, y, s=1.0, col='#3d5a80', worn=False):
    c.save(); c.translate(x, y); c.scale(s, s)
    jc = hexc(col)
    shd = lin(-80, 0, 80, 0, [shade(jc, .2), jc, shade(jc, -.3)], [0, .4, 1])
    rr(c, -80, 0, 160, 50, 10, shader=shd)
    c.drawPath(path([(-80, 30), (0, 30), (-6, 330), (-80, 330)]), paint(shader=shd))
    c.drawPath(path([(80, 30), (6, 30), (10, 330), (80, 330)]), paint(shader=shd))
    c.drawLine(-2, 50, -3, 320, paint(alpha(shade(jc, -.5), 160), stroke=4))
    for xx in (-55, 55):
        c.drawLine(xx, 50, xx, 320, paint(alpha(hexc('e0a84a'), 120), stroke=3))
    c.drawLine(-80, 8, 80, 8, paint(alpha(hexc('e0a84a'), 160), stroke=3))
    if worn:
        for (a, b) in [(-50, 230), (40, 180), (-40, 120)]:
            ellipse(c, a, b, 18, 10, color=alpha(hexc('c8d3dd'), 150))
        ellipse(c, 45, 280, 22, 14, color=alpha(hexc('8a6a4a'), 120))
    c.restore()

def hook(c, x, y):
    c.drawCircle(x, y, 12, paint(hexc('5a4a3a')))
    c.drawLine(x, y, x, y + 30, paint(hexc('3b3028'), stroke=8))

def truck(c, x, y, s=1.0, t=0):
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 420, 50, 120)
    body = hexc('6e8a6a')
    # bed
    box3d(c, -400, -250, 380, 180, body, r=16)
    # cab
    p = skia.Path(); p.moveTo(-30, -70); p.lineTo(-30, -380); p.quadTo(-28, -400, 0, -400); p.lineTo(170, -400); p.lineTo(260, -260); p.lineTo(380, -245)
    p.quadTo(420, -240, 420, -200); p.lineTo(420, -70); p.close()
    c.drawPath(p, paint(shader=lin(0, -400, 0, -70, [shade(body, .25), body, shade(body, -.3)], [0, .45, 1])))
    c.drawPath(path([(10, -370), (160, -370), (230, -265), (10, -265)]), paint(shader=lin(0, -370, 0, -265, [hexc('cfe3f0'), hexc('8fb3c9')])))
    c.drawLine(40, -360, 90, -280, paint(alpha(skia.ColorWHITE, 120), stroke=10))
    # rust
    rnd = random.Random(7)
    for i in range(16):
        rx_ = rnd.uniform(-380, 400); ry_ = rnd.uniform(-230, -90)
        ellipse(c, rx_, ry_, rnd.uniform(10, 30), rnd.uniform(6, 16), color=alpha(hexc('8a4b2a'), rnd.randint(110, 190)), blur=3)
    # bumper, light
    rr(c, 380, -130, 60, 40, 10, color=hexc('bfc3c4'))
    ellipse(c, 400, -190, 22, 20, color=hexc('fff2c4'))
    # wheels
    for wx in (-260, 260):
        c.drawCircle(wx, -70, 82, paint(hexc('242226')))
        c.drawCircle(wx, -70, 40, paint(shader=rad(wx - 10, -80, 45, [hexc('d6d8d8'), hexc('7a7d80')])))
        c.drawCircle(wx, -70, 10, paint(hexc('4a4c4e')))
    c.restore()

def chalkboard(c, x, y, w, h, title, value, pop=0.0, sub=None):
    wood = hexc('8a5a3a')
    rr(c, x + 12, y + 16, w, h, 12, color=skia.Color(0, 0, 0, 80), blur=14)
    box3d(c, x, y, w, h, wood, r=12)
    board = skia.Rect.MakeXYWH(x + 30, y + 30, w - 60, h - 60)
    c.drawRect(board, paint(shader=rad(x + w * .4, y + h * .35, w, [hexc('3f5a4c'), hexc('2b3e35')])))
    # chalk smudges
    rnd = random.Random(11)
    for i in range(14):
        ellipse(c, rnd.uniform(x + 60, x + w - 60), rnd.uniform(y + 60, y + h - 60), rnd.uniform(40, 120), rnd.uniform(10, 30), color=alpha(skia.ColorWHITE, 14), blur=12)
    chalk = hexc('f2f0e6')
    for i, line in enumerate(title.split('\n')):
        text(c, line, x + w / 2, y + 120 + i * 70, 62, chalk)
    sc = 1 + 0.35 * (1 - back_out(pop)) if pop < 1 else 1
    c.save(); c.translate(x + w / 2, y + h * 0.7); c.scale(sc, sc)
    text(c, value, 0, 70, 240, chalk)
    c.restore()
    if sub: text(c, sub, x + w / 2, y + h - 70, 44, alpha(chalk, 200))
    # chalk tray
    rr(c, x + 40, y + h - 26, w - 80, 26, 6, color=shade(wood, -.1))
    rr(c, x + w * .65, y + h - 38, 70, 16, 6, color=chalk)

def church(c, x, y, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    wc = hexc('efe7da'); rf = hexc('8c3b34')
    box3d(c, -300, -520, 600, 520, wc, r=6)
    c.drawPath(path([(-340, -510), (0, -760), (340, -510)]), paint(shader=lin(0, -760, 0, -510, [shade(rf, .2), shade(rf, -.2)])))
    box3d(c, -90, -1050, 180, 560, wc, r=4)
    c.drawPath(path([(-110, -1040), (0, -1250), (110, -1040)]), paint(shader=lin(0, -1250, 0, -1040, [shade(rf, .2), shade(rf, -.2)])))
    c.drawLine(0, -1250, 0, -1330, paint(hexc('c9a13b'), stroke=10)); c.drawLine(-30, -1300, 30, -1300, paint(hexc('c9a13b'), stroke=10))
    rr(c, -40, -900, 80, 120, 40, color=hexc('3d2f2a'))
    # door + windows
    p = skia.Path(); p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-80, -260, 160, 260), 80, 80)); c.drawPath(p, paint(shader=lin(0, -260, 0, 0, [hexc('7b4a2e'), hexc('4f2e1c')])))
    for wx in (-200, 200):
        rr(c, wx - 40, -400, 80, 170, 40, shader=lin(0, -400, 0, -230, [hexc('9ec3e6'), hexc('e8c97a')]))
    c.restore()

def house_front(c, x, y, w, h, col, roof='#6b3e36', s=1.0):
    hc = hexc(col)
    box3d(c, x, y - h, w, h, hc, r=4)
    c.drawPath(path([(x - 30, y - h + 6), (x + w / 2, y - h - w * .42), (x + w + 30, y - h + 6)]), paint(shader=lin(0, y - h - w * .4, 0, y - h, [shade(hexc(roof), .2), shade(hexc(roof), -.2)])))
    for i in range(2):
        wx = x + w * (.2 + .45 * i)
        rr(c, wx, y - h * .7, w * .2, h * .28, 6, shader=lin(0, y - h * .7, 0, y - h * .42, [hexc('fbe7b0'), hexc('e8b864')]))
    rr(c, x + w * .42, y - h * .38, w * .16, h * .38, 6, color=shade(hexc(roof), -.1))

def tree(c, x, y, s=1.0, col='#6a9a5b'):
    c.save(); c.translate(x, y); c.scale(s, s)
    cshadow(c, 0, 0, 120, 26, 70)
    rr(c, -22, -260, 44, 260, 18, shader=lin(-22, 0, 22, 0, [hexc('8a6446'), hexc('5a3e2b')]))
    g = hexc(col)
    for (dx, dy, r_) in [(-80, -330, 120), (80, -340, 120), (0, -440, 140), (-20, -300, 110), (60, -260, 90)]:
        c.drawCircle(dx, dy, r_, paint(shader=rad(dx - r_ * .4, dy - r_ * .4, r_ * 1.6, [shade(g, .25), g, shade(g, -.3)], [0, .4, 1])))
    c.restore()

def vignette(c, strength=150):
    c.drawRect(skia.Rect.MakeWH(W, H), paint(shader=rad(W / 2, H * 0.48, H * 0.72, [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 0), skia.Color(10, 5, 15, strength)], [0, .55, 1])))
