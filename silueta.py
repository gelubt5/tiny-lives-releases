"""silueta.py — silhouette-style characters for ToonEngine (documentary cartoon look).

Tall, slim, flat-shaded figures in profile: charcoal body, one big white eye, nose + chin bump,
coloured clothes/belts/hats, a thin light rim instead of a thick ink outline. No blush, no outline.
Every pose is a pure function of time (deterministic, safe for ToonEngine's parallel workers).

    from silueta import Figure
    ion = Figure(x=-200, face=1, shirt="#d8d0bf", band="#9e2b25", belt="#9e2b25", hat="cusma")
    ion.walk(0.5, 2.5, to=-60)        # walk between t=0.5 and t=2.5 to x=-60
    ion.do("point", 3.0, 1.5)         # gesture: point / raise / shock / wave / stir / clap /
                                      #   shrug / eat / fist / hips / nod / shake / laugh / jump / bow
    ion.talk(3.0, 1.2)                # mouth moves (no audio)
    ion.feel("surprised", 3.0, 1.5)   # surprised / angry / happy / sad
    ion.turn(5.0, -1)                 # face the other way
    scene.extras.append(ion)          # ToonEngine Scene (drawn in world space)
"""
import math
import cairo

SKIN = "#1d1a21"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _shade(c, k):
    return tuple(max(0, min(1, v * k)) for v in c)


def _smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _env(now, t0, d, fade=0.25):
    """0..1 weight of an action window [t0, t0+d] with soft in/out."""
    if now < t0 - fade or now > t0 + d + fade:
        return 0.0
    a = _smooth((now - (t0 - fade)) / fade) if now < t0 else 1.0
    b = _smooth((t0 + d + fade - now) / fade) if now > t0 + d else 1.0
    return min(a, b)


# arm poses: (front shoulder, front elbow, back shoulder, back elbow), radians from hanging down,
# + = rotate toward the facing direction (forward/up)
POSES = {
    "idle":  (0.12, 0.25, -0.10, 0.20),
    "point": (1.55, 0.05, -0.15, 0.25),
    "raise": (2.85, 0.25, 2.65, 0.30),
    "shock": (2.55, 2.35, 2.25, 2.25),
    "wave":  (2.70, 0.60, -0.10, 0.20),
    "stir":  (0.95, 0.80, 0.20, 0.40),
    "clap":  (1.20, 0.90, 1.05, 1.10),
    "shrug": (0.35, -1.90, -0.35, 1.90),
    "eat":   (0.60, 2.40, -0.05, 0.25),
    "fist":  (2.40, 1.20, -0.25, 0.30),
    "hips":  (-0.55, -2.10, 0.55, 2.10),
    "offer": (1.25, 0.55, 0.90, 0.70),
    "think": (0.50, 2.55, -0.05, 0.20),
}


class Figure:
    def __init__(self, x=0.0, face=1, scale=1.0, skin=SKIN, shirt=None, band=None, belt=None,
                 pants=None, skirt=None, apron=None, vest=None, hat=None, hat_color=None, hair="tuft",
                 mustache=False, beard=False, rim="#bfe6ee", rim_a=0.42, name=""):
        self.name = name
        self.x0, self.face0, self.s = float(x), face, scale
        self.skin = _rgb(skin)
        self.shirt = _rgb(shirt) if shirt else self.skin
        self.band = _rgb(band) if band else None
        self.belt = _rgb(belt) if belt else None
        self.pants = _rgb(pants) if pants else self.skin
        self.skirt = _rgb(skirt) if skirt else None
        self.apron = _rgb(apron) if apron else None
        self.vest = _rgb(vest) if vest else None
        self.hat, self.hat_color = hat, (_rgb(hat_color) if hat_color else None)
        self.hair, self.mustache, self.beard = hair, mustache, beard
        self.rim, self.rim_a = _rgb(rim), rim_a
        self.walks, self.acts, self.talks, self.feels, self.turns = [], [], [], [], []
        self.looks = []
        self.x, self.y = self.x0, 0.0  # for ToonEngine (camera / audio pan)

    # ------------------------------------------------------------ script API
    def walk(self, t, d, to, gait="walk"):
        self.walks.append((t, d, to, gait))
        self.walks.sort()
        return self

    def do(self, kind, t, d=1.2):
        self.acts.append((kind, t, d))
        return self

    def talk(self, t, d=1.0):
        self.talks.append((t, d))
        return self

    def feel(self, kind, t, d=1.5):
        self.feels.append((kind, t, d))
        return self

    def turn(self, t, face):
        self.turns.append((t, face))
        self.turns.sort()
        return self

    def look(self, t, d, dx, dy=0.0):
        self.looks.append((t, d, dx, dy))
        return self

    # ------------------------------------------------------------ engine duck-typing
    def update(self, dt, scene):
        self.x = self.pos(scene.time)[0]

    # ------------------------------------------------------------ state
    def pos(self, now):
        x, moving, phase, gait = self.x0, 0.0, 0.0, "walk"
        travelled = 0.0
        for t, d, to, g in self.walks:
            if now >= t + d:
                travelled += abs(to - x)
                x = to
            elif now > t:
                k = (now - t) / d
                k2 = k  # constant speed, eased at ends
                k2 = _smooth(k) * 0.25 + k * 0.75
                nx = x + (to - x) * k2
                travelled += abs(nx - x)
                moving, gait = 1.0, g
                x = nx
                break
        stride = 70.0 if gait == "walk" else 95.0
        phase = travelled / stride * math.pi
        return x, moving, phase, gait

    def facing(self, now):
        f = self.face0
        x0 = self.x0
        for t, d, to, g in self.walks:  # walking sets facing automatically
            if now > t:
                f = 1 if to > x0 else (-1 if to < x0 else f)
            x0 = to
        for t, ff in self.turns:
            if now >= t:
                tw = [w for w in self.walks if w[0] > t and w[0] <= now]
                if not tw:
                    f = ff
        return f

    def _act_weights(self, now):
        out = []
        for kind, t, d in self.acts:
            w = _env(now, t, d)
            if w > 0:
                out.append((kind, w, now - t, d))
        return out

    def _feel(self, now):
        best, bw = None, 0.0
        for kind, t, d in self.feels:
            w = _env(now, t, d, 0.15)
            if w > bw:
                best, bw = kind, w
        return best, bw

    def _talking(self, now):
        for t, d in self.talks:
            if t <= now <= t + d:
                return 0.5 + 0.5 * abs(math.sin((now - t) * 17)) * (0.6 + 0.4 * math.sin((now - t) * 5.3))
        return 0.0

    # ------------------------------------------------------------ drawing helpers
    def _limb(self, ctx, pts, w, col):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.set_source_rgb(*col)
        ctx.set_line_width(w)
        ctx.stroke()

    def _fill(self, ctx, col, rim=True):
        ctx.set_source_rgb(*col)
        ctx.fill()

    @staticmethod
    def _arm_pts(sx, sy, a1, a2, l1=44, l2=40):
        ex = sx + math.sin(a1) * l1
        ey = sy + math.cos(a1) * l1
        hx = ex + math.sin(a1 + a2) * l2
        hy = ey + math.cos(a1 + a2) * l2
        return (sx, sy), (ex, ey), (hx, hy)

    @staticmethod
    def _leg_pts(hx, hy, a, knee):
        kx = hx + math.sin(a) * 52
        ky = hy + math.cos(a) * 52
        fx = kx + math.sin(a - knee) * 50
        fy = ky + math.cos(a - knee) * 50
        return (hx, hy), (kx, ky), (fx, fy)

    # ------------------------------------------------------------ draw
    def draw(self, ctx, now):
        x, moving, phase, gait = self.pos(now)
        f = self.facing(now)
        acts = self._act_weights(now)
        feel, fw = self._feel(now)
        talk = self._talking(now)

        # ---- body motion
        breath = math.sin(now * 2.1 + self.x0 * 0.01) * 1.2
        bob = abs(math.sin(phase)) * (4 if gait == "walk" else 8) * moving
        lift, lean, head_tilt, head_dy = 0.0, 0.04 + (0.10 if gait == "run" else 0.03) * moving, 0.0, 0.0
        arms = list(POSES["idle"])
        for kind, w, el, d in acts:
            if kind in POSES:
                tgt = list(POSES[kind])
                if kind == "wave":
                    tgt[1] += 0.45 * math.sin(el * 10)
                elif kind == "stir":
                    tgt[0] += 0.25 * math.sin(el * 7)
                    tgt[1] += 0.25 * math.cos(el * 7)
                elif kind == "clap":
                    c = 0.22 * math.sin(el * 14)
                    tgt[1] += c
                    tgt[3] -= c
                elif kind == "eat":
                    tgt[1] -= 0.6 * max(0, math.sin(el * 5))
                elif kind == "fist":
                    tgt[0] += 0.18 * math.sin(el * 13)
                elif kind == "raise":
                    tgt[1] += 0.2 * math.sin(el * 8)
                    tgt[3] += 0.2 * math.sin(el * 8 + 1)
                arms = [a + (b - a) * w for a, b in zip(arms, tgt)]
            if kind == "jump":
                k = min(1, el / max(d, 0.01))
                lift += 70 * 4 * k * (1 - k) * w
            if kind == "hop":
                lift += 22 * abs(math.sin(el * 7)) * w
            if kind == "nod":
                head_tilt += 0.22 * math.sin(el * 9) * w
            if kind == "shake":
                head_tilt += 0.05 * math.sin(el * 14) * w
            if kind == "laugh":
                head_tilt -= (0.25 + 0.08 * math.sin(el * 18)) * w
                lift += 3 * abs(math.sin(el * 18)) * w
            if kind == "bow":
                lean += 0.55 * w
            if kind == "think":
                head_tilt -= 0.12 * w
        if moving:  # arm swing while walking
            sw = 0.55 if gait == "walk" else 0.95
            arms[0] += sw * math.sin(phase) * (1 - min(1, sum(w for k, w, *_ in acts if k in POSES)))
            arms[2] -= sw * math.sin(phase) * (1 - min(1, sum(w for k, w, *_ in acts if k in POSES)))
        if feel == "surprised":
            lift += 0
        # shadow
        ctx.save()
        ctx.translate(x, 0)
        ctx.scale(self.s, self.s * 0.18)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 46)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.35)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        ctx.set_source(g)
        ctx.arc(0, 0, 46, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()
        st = (x, f, lift, bob, moving, phase, gait, arms, lean, head_tilt, feel, fw, talk)
        if self.rim_a > 0:  # rim light: whole silhouette, outer edge only
            ctx.push_group()
            self._body(_RimCtx(ctx, self.rim), now, *st)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(self.rim_a)
        self._body(ctx, now, *st)

    def _body(self, ctx, now, x, f, lift, bob, moving, phase, gait, arms, lean, head_tilt, feel, fw, talk):
        ctx.save()
        ctx.translate(x, -lift)
        ctx.scale(f * self.s, self.s)

        hip_y = -110 + bob * 0.5
        # ---- legs
        if moving:
            a1 = 0.48 * math.sin(phase) * (1.2 if gait == "run" else 1)
            a2 = -a1
            k1 = 0.15 + 0.7 * max(0, -math.cos(phase))
            k2 = 0.15 + 0.7 * max(0, math.cos(phase))
        else:
            a1, a2, k1, k2 = 0.06, -0.06, 0.05, 0.05
        if lift > 5:
            a1, a2, k1, k2 = 0.35, 0.05, 0.9, 0.6
        back_col = _shade(self.pants, 0.82)
        for (a, k, col) in ((a2, k2, back_col), (a1, k1, self.pants)):
            pts = self._leg_pts(0, hip_y, a, k)
            self._limb(ctx, pts, 13, col)
            fx, fy = pts[2]
            ctx.save()
            ctx.translate(fx + 7, fy - 1)
            ctx.scale(1.0, 0.55)
            ctx.arc(0, 0, 11, 0, 2 * math.pi)
            ctx.restore()
            self._fill(ctx, _shade(self.skin, 0.9) if col is back_col else self.skin)

        # ---- body pivot (lean)
        ctx.save()
        ctx.translate(0, hip_y)
        ctx.rotate(lean)
        sh = (5, -68)  # shoulder (relative to hip)
        # back arm
        bpts = self._arm_pts(sh[0] - 3, sh[1] + 2, arms[2], arms[3])
        self._limb(ctx, bpts[:2], 10, _shade(self.shirt, 0.8))
        self._limb(ctx, bpts[1:], 9, _shade(self.shirt, 0.8))
        hx, hy = bpts[2]
        ctx.arc(hx, hy, 7, 0, 2 * math.pi)
        self._fill(ctx, _shade(self.skin, 0.9))

        # skirt / torso
        if self.skirt:
            ctx.move_to(-20, -10)
            ctx.line_to(22, -10)
            ctx.curve_to(30, 30, 34, 52, 30, 62)
            ctx.line_to(-30, 62)
            ctx.curve_to(-32, 50, -28, 30, -20, -10)
            ctx.close_path()
            self._fill(ctx, self.skirt)
        ctx.move_to(-17, 4)
        ctx.line_to(18, 4)
        ctx.curve_to(22, -30, 24, -55, 17, -74)
        ctx.curve_to(8, -80, -8, -80, -14, -72)
        ctx.curve_to(-22, -50, -21, -25, -17, 4)
        ctx.close_path()
        self._fill(ctx, self.shirt)
        if self.vest:
            ctx.move_to(-17, -2)
            ctx.line_to(2, -2)
            ctx.line_to(6, -74)
            ctx.curve_to(-4, -79, -10, -78, -14, -72)
            ctx.curve_to(-22, -50, -21, -25, -17, -2)
            ctx.close_path()
            self._fill(ctx, self.vest, rim=False)
        if self.band:  # folk embroidery: vertical stripe at the chest + hem
            for i in range(6):
                yy = -66 + i * 9
                ctx.move_to(10, yy)
                ctx.line_to(14, yy + 4)
                ctx.line_to(10, yy + 8)
                ctx.line_to(6, yy + 4)
                ctx.close_path()
            ctx.set_source_rgb(*self.band)
            ctx.fill()
            ctx.rectangle(-17, -4, 35, 4)
            ctx.fill()
        if self.apron:
            ctx.move_to(-2, -22)
            ctx.line_to(20, -22)
            ctx.line_to(26, 48 if self.skirt else 28)
            ctx.line_to(2, 48 if self.skirt else 28)
            ctx.close_path()
            self._fill(ctx, self.apron, rim=False)
        if self.belt:
            ctx.move_to(-19, -18)
            ctx.line_to(20, -18)
            ctx.line_to(20, -8)
            ctx.line_to(-19, -8)
            ctx.close_path()
            ctx.set_source_rgb(*self.belt)
            ctx.fill()
            ctx.move_to(-19, -10)  # hanging sash end
            ctx.line_to(-25, 10)
            ctx.line_to(-19, 9)
            ctx.close_path()
            ctx.fill()

        # ---- head
        ctx.save()
        ctx.translate(9, -82)
        ctx.rotate(head_tilt - lean * 0.6)
        self._draw_head(ctx, now, feel, fw, talk)
        ctx.restore()

        # front arm
        fpts = self._arm_pts(sh[0], sh[1], arms[0], arms[1])
        self._limb(ctx, fpts[:2], 11, self.shirt)
        self._limb(ctx, fpts[1:], 10, self.shirt if self.shirt is not self.skin else self.skin)
        hx, hy = fpts[2]
        ctx.arc(hx, hy, 7.5, 0, 2 * math.pi)
        self._fill(ctx, self.skin)
        ctx.restore()  # body pivot
        ctx.restore()

    def _draw_head(self, ctx, now, feel, fw, talk):
        # neck
        self._limb(ctx, [(0, 4), (3, -12)], 13, self.skin)
        # head: rounded profile with nose + chin
        ctx.save()
        ctx.translate(4, -34)
        ctx.move_to(-20, 8)
        ctx.curve_to(-26, -14, -14, -32, 4, -31)
        ctx.curve_to(18, -30, 23, -18, 23, -8)
        ctx.line_to(29, 0)          # nose
        ctx.line_to(23, 4)
        ctx.curve_to(23, 12, 20, 22, 10, 24)   # chin
        ctx.curve_to(-6, 26, -18, 20, -20, 8)
        ctx.close_path()
        self._fill(ctx, self.skin)
        # hair
        if self.hair == "tuft" and self.hat not in ("cusma", "turban", "tophat", "chef", "bork", "basma"):
            ctx.move_to(-20, -12)
            for i in range(6):
                a = math.pi * (1.05 + i * 0.13)
                r1 = 32 + (6 if i % 2 else 0)
                ctx.line_to(3 + math.cos(a) * r1, -6 + math.sin(a) * r1)
            ctx.line_to(14, -30)
            ctx.close_path()
            self._fill(ctx, self.skin)
        if self.hair == "bun" and self.hat != "basma":
            ctx.arc(-18, -22, 9, 0, 2 * math.pi)
            self._fill(ctx, self.skin)
        if self.mustache:
            ctx.move_to(14, 8)
            ctx.curve_to(20, 6, 26, 8, 30, 14)
            ctx.curve_to(24, 12, 18, 13, 12, 12)
            ctx.close_path()
            ctx.set_source_rgb(*_shade(self.skin, 0.55))
            ctx.fill()
        if self.beard:
            ctx.move_to(-6, 14)
            ctx.curve_to(0, 34, 20, 36, 24, 14)
            ctx.line_to(20, 20)
            ctx.curve_to(10, 24, 2, 22, -6, 14)
            ctx.close_path()
            self._fill(ctx, self.skin)
        # hats
        hc = self.hat_color
        h = self.hat
        if h == "cusma":  # tall sheepskin hat
            c = hc or _rgb("#2a2520")
            ctx.move_to(-19, -18)
            ctx.curve_to(-22, -48, -14, -60, 2, -60)
            ctx.curve_to(18, -60, 24, -46, 22, -20)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.set_source_rgba(1, 1, 1, 0.06)
            for i in range(10):
                ctx.arc(-14 + (i % 5) * 8, -50 + (i // 5) * 14, 3, 0, 2 * math.pi)
                ctx.fill()
        elif h == "basma":  # headscarf
            c = hc or _rgb("#8e2a26")
            ctx.move_to(-24, 18)
            ctx.curve_to(-30, -20, -16, -36, 4, -35)
            ctx.curve_to(20, -34, 26, -22, 25, -10)
            ctx.line_to(16, -8)
            ctx.curve_to(12, -22, -4, -22, -10, 0)
            ctx.line_to(-14, 24)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.move_to(-20, 16)
            ctx.line_to(-34, 34)
            ctx.line_to(-22, 32)
            ctx.close_path()
            ctx.set_source_rgb(*c)
            ctx.fill()
            ctx.set_source_rgba(1, 0.92, 0.7, 0.55)
            for i in range(6):
                ctx.arc(-14 + i * 6, -24 + (i % 2) * 6, 1.6, 0, 2 * math.pi)
                ctx.fill()
        elif h == "turban":
            c = hc or _rgb("#e8e2d4")
            for i in range(3):
                ctx.save()
                ctx.translate(2, -24 - i * 9)
                ctx.scale(1, 0.45)
                ctx.arc(0, 0, 26 - i * 4, 0, 2 * math.pi)
                ctx.restore()
                self._fill(ctx, _shade(c, 1 - i * 0.05))
            ctx.arc(14, -30, 4, 0, 2 * math.pi)
            ctx.set_source_rgb(0.72, 0.2, 0.17)
            ctx.fill()
        elif h == "fez":
            c = hc or _rgb("#8f2420")
            ctx.move_to(-14, -24)
            ctx.line_to(-10, -48)
            ctx.line_to(10, -48)
            ctx.line_to(16, -24)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.move_to(0, -48)
            ctx.curve_to(-8, -44, -14, -36, -16, -28)
            ctx.set_source_rgb(0.1, 0.08, 0.08)
            ctx.set_line_width(2)
            ctx.stroke()
        elif h == "bork":  # janissary felt hat folding back
            c = hc or _rgb("#ebe5d6")
            ctx.move_to(-16, -22)
            ctx.line_to(-8, -60)
            ctx.curve_to(-14, -70, -30, -62, -40, -40)
            ctx.curve_to(-30, -50, -20, -52, -18, -44)
            ctx.line_to(-22, -22)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.move_to(-18, -20)
            ctx.line_to(-8, -62)
            ctx.line_to(14, -58)
            ctx.line_to(20, -20)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.rectangle(-20, -26, 42, 7)
            ctx.set_source_rgb(0.75, 0.6, 0.25)
            ctx.fill()
        elif h == "tophat" or h == "beret":
            c = hc or _rgb("#141216")
            if h == "beret":
                ctx.save()
                ctx.translate(0, -28)
                ctx.scale(1.35, 0.5)
                ctx.arc(0, 0, 22, 0, 2 * math.pi)
                ctx.restore()
                self._fill(ctx, c)
                ctx.move_to(-10, -36)
                ctx.curve_to(-30, -60, -44, -62, -50, -58)
                ctx.set_source_rgb(0.85, 0.82, 0.74)
                ctx.set_line_width(4)
                ctx.stroke()
            else:
                ctx.rectangle(-26, -30, 54, 7)
                ctx.rectangle(-16, -70, 34, 42)
                self._fill(ctx, c)
        elif h == "chef":
            c = hc or _rgb("#ece7dc")
            ctx.move_to(-16, -24)
            ctx.line_to(-18, -54)
            ctx.curve_to(-30, -76, 30, -76, 20, -54)
            ctx.line_to(18, -24)
            ctx.close_path()
            self._fill(ctx, c)
        elif h == "clop":  # straw hat
            c = hc or _rgb("#b8955a")
            ctx.save()
            ctx.translate(2, -24)
            ctx.scale(1, 0.22)
            ctx.arc(0, 0, 40, 0, 2 * math.pi)
            ctx.restore()
            self._fill(ctx, c)
            ctx.move_to(-16, -24)
            ctx.curve_to(-16, -44, 18, -44, 18, -24)
            ctx.close_path()
            self._fill(ctx, c)
            ctx.rectangle(-16, -30, 34, 5)
            ctx.set_source_rgb(0.55, 0.15, 0.14)
            ctx.fill()
        elif h == "sajkaca":  # side cap
            c = hc or _rgb("#3d4a3a")
            ctx.move_to(-20, -20)
            ctx.line_to(-14, -42)
            ctx.line_to(20, -40)
            ctx.line_to(24, -18)
            ctx.close_path()
            self._fill(ctx, c)
        elif h == "crown":
            c = hc or _rgb("#d4a63a")
            ctx.move_to(-16, -24)
            for i in range(5):
                ctx.line_to(-16 + i * 8 + 4, -46)
                ctx.line_to(-16 + i * 8 + 8, -32)
            ctx.line_to(24, -24)
            ctx.close_path()
            self._fill(ctx, c)
        # eye
        blink = ((now + self.x0 * 0.013) % 3.7) < 0.12
        er = 10.5 * (1.25 if feel == "surprised" else 1.0) ** fw
        ex, ey = 12, -10
        if feel == "happy" and fw > 0.5:
            ctx.arc(ex, ey + 2, er * 0.8, math.pi * 1.1, math.pi * 1.9)
            ctx.set_source_rgb(0.96, 0.95, 0.9)
            ctx.set_line_width(3.5)
            ctx.stroke()
        else:
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(1, 0.12 if blink else 1.0)
            ctx.arc(0, 0, er, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(0.97, 0.96, 0.92)
            ctx.fill()
            if not blink:
                lx, ly = 3.0, 0.0
                for t, d, dx, dy in self.looks:
                    if t <= now <= t + d:
                        lx, ly = dx * 4, dy * 4
                pr = 4.2 * (0.7 if feel == "surprised" else 1.0) ** fw
                ctx.arc(ex + lx, ey + ly, pr, 0, 2 * math.pi)
                ctx.set_source_rgb(0.08, 0.07, 0.09)
                ctx.fill()
            if feel == "angry" and fw > 0.3:
                ctx.move_to(ex - 10, ey - 16)
                ctx.line_to(ex + 11, ey - 9)
                ctx.set_source_rgb(*_shade(self.skin, 0.4))
                ctx.set_line_width(4)
                ctx.stroke()
            if feel == "sad" and fw > 0.3:
                ctx.move_to(ex - 10, ey - 10)
                ctx.line_to(ex + 10, ey - 16)
                ctx.set_source_rgb(*_shade(self.skin, 0.4))
                ctx.set_line_width(4)
                ctx.stroke()
        # mouth
        if talk > 0 or (feel in ("surprised", "happy") and fw > 0.4):
            o = max(talk, 0.7 if feel == "surprised" else 0.45)
            ctx.save()
            ctx.translate(17, 14)
            ctx.scale(1, 0.4 + o)
            ctx.arc(0, 0, 5.5, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(0.55, 0.12, 0.14)
            ctx.fill()
        ctx.restore()


class _RimCtx:
    """Cairo proxy for the rim pass: every shape is filled + outlined in the rim colour."""
    PAD = 3.5

    def __init__(self, c, rim):
        self._c, self._rim, self._w = c, rim, 1.0

    def set_source_rgb(self, *a):
        self._c.set_source_rgb(*self._rim)

    def set_source_rgba(self, *a):
        self._c.set_source_rgb(*self._rim)

    def set_source(self, *a):
        self._c.set_source_rgb(*self._rim)

    def set_line_width(self, w):
        self._w = w

    def stroke(self):
        self._c.set_source_rgb(*self._rim)
        self._c.set_line_width(self._w + self.PAD)
        self._c.stroke()

    def stroke_preserve(self):
        self._c.set_source_rgb(*self._rim)
        self._c.set_line_width(self._w + self.PAD)
        self._c.stroke_preserve()

    def fill(self):
        self._c.set_source_rgb(*self._rim)
        self._c.set_line_width(self.PAD)
        self._c.set_line_join(cairo.LINE_JOIN_ROUND)
        self._c.stroke_preserve()
        self._c.fill()

    def fill_preserve(self):
        self._c.set_source_rgb(*self._rim)
        self._c.fill_preserve()

    def __getattr__(self, k):
        return getattr(self._c, k)
