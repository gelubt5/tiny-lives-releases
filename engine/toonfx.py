"""
ToonFX — screen effects, punchy camera moves and thumbnails for ToonEngine (2D + 3D).

Effects are plain picklable objects with draw(ctx, W, H, now); put them in
scene.fx (both toonengine.Scene and toon3d.Scene3D draw them after the world,
before subtitles and captions, so text stays readable through a transition).

    Fade(t, d, color="black")      dip to a colour and back (cut happens at t + d/2)
    Iris(t, d, center=(.5,.45))    circle closes to black then reopens
    Wipe(t, d, direction="left")   coloured panel sweeps across and away
    WhipPan(t, d, direction=1)     motion-blur smear of the frame + speed streaks
    Flash(t, d=0.25)               white impact flash

    make_style("paper"|"crayon"|"watercolour"|"chalk", fps)   texture styles (#72): one
                                   screen fx per scene, {"name", "intensity", "boil", "seed"}

    FastCamera                     2D camera whose keys can move fast (punch-ins)
    thumbnail(src, out, title)     YouTube/TikTok thumbnail from an episode or an MP4

CLI:  python3 toonfx.py thumb episode.json out.png "TITLE" [--time 4.2]
"""
import math, os, random, subprocess, sys

import cairo

import toonengine as te

INK = te.INK


def _env(now, t, d):
    """0..1..0 triangle around the midpoint of [t, t+d] (1 at the cut)."""
    if d <= 0 or now < t or now > t + d:
        return 0.0
    u = (now - t) / d
    return 1 - abs(2 * u - 1)


class Effect:
    t, d = 0.0, 0.5

    def active(self, now):
        return self.t <= now <= self.t + self.d

    @property
    def mid(self):
        return self.t + self.d / 2

    def draw(self, ctx, W, H, now):  # pragma: no cover - interface
        raise NotImplementedError


class Fade(Effect):
    """Dip to a colour: fully covered at the midpoint (put the camera cut there)."""

    def __init__(self, t, d=0.6, color="black"):
        self.t, self.d = t, d
        self.rgb = (0, 0, 0) if color == "black" else (1, 1, 1) if color == "white" else te.hex2rgb(color)

    def draw(self, ctx, W, H, now):
        a = te.ease(_env(now, self.t, self.d))
        if a > 0:
            ctx.save()
            ctx.set_source_rgba(*self.rgb, a)
            ctx.paint()
            ctx.restore()


class Iris(Effect):
    """Cartoon iris: a circle closes on `center` (0..1 screen coords) then reopens."""

    def __init__(self, t, d=0.8, center=(0.5, 0.45), color="black"):
        self.t, self.d, self.center = t, d, tuple(center)
        self.rgb = (0, 0, 0) if color == "black" else te.hex2rgb(color)

    def draw(self, ctx, W, H, now):
        e = _env(now, self.t, self.d)
        if e <= 0:
            return
        cx, cy = self.center[0] * W, self.center[1] * H
        rmax = math.hypot(max(cx, W - cx), max(cy, H - cy)) * 1.02
        r = rmax * (1 - te.ease(e))
        ctx.save()
        ctx.rectangle(0, 0, W, H)
        if r > 0.5:
            ctx.new_sub_path()
            ctx.arc_negative(cx, cy, r, 2 * math.pi, 0)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgb(*self.rgb)
        ctx.fill()
        if r > 0.5:
            ctx.arc(cx, cy, r, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.9)
            ctx.set_line_width(max(3, W * 0.006))
            ctx.stroke()
        ctx.restore()


class Wipe(Effect):
    """A panel sweeps in (covers the frame at the midpoint) and out the other side."""

    def __init__(self, t, d=0.7, direction="left", color="#ffd166"):
        self.t, self.d, self.direction = t, d, direction
        self.rgb = te.hex2rgb(color) if color.startswith("#") else (0, 0, 0)

    def draw(self, ctx, W, H, now):
        if not self.active(now):
            return
        u = te.ease((now - self.t) / self.d)  # 0..1 over the whole effect
        horiz = self.direction in ("left", "right")
        L = W if horiz else H
        # panel spans [lead - L, lead], lead travels 0 -> 2L
        lead = u * 2 * L
        a, b = max(0, lead - L), min(L, lead)
        if b <= a:
            return
        if self.direction in ("right", "down"):
            a, b = L - b, L - a
        ctx.save()
        if horiz:
            ctx.rectangle(a, 0, b - a, H)
        else:
            ctx.rectangle(0, a, W, b - a)
        ctx.set_source_rgb(*self.rgb)
        ctx.fill()
        # ink edge on the leading side
        edge = b if self.direction in ("left", "up") else a
        if 0 < edge < L:
            if horiz:
                ctx.rectangle(edge - 5, 0, 10, H)
            else:
                ctx.rectangle(0, edge - 5, W, 10)
            ctx.set_source_rgb(*INK)
            ctx.fill()
        ctx.restore()


class WhipPan(Effect):
    """Motion-blur smear of the frame already drawn (real copies of the pixels,
    shifted and faded) plus white speed streaks; strongest at the midpoint."""

    def __init__(self, t, d=0.4, direction=1, streaks=14):
        self.t, self.d, self.direction, self.streaks = t, d, 1 if direction >= 0 else -1, streaks

    def draw(self, ctx, W, H, now):
        e = _env(now, self.t, self.d)
        if e <= 0:
            return
        target = ctx.get_target()
        target.flush()
        snap = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c2 = cairo.Context(snap)
        c2.set_source_surface(target, 0, 0)
        c2.paint()
        spread = W * 0.2 * e
        n = 14
        ctx.save()
        # running average of shifted copies -> smooth directional blur
        for i in range(1, n + 1):
            ctx.set_source_surface(snap, self.direction * spread * i / n, 0)
            ctx.paint_with_alpha(1.0 / (i + 1))
        ctx.restore()
        # speed streaks
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(self.streaks):
            y = (i + 0.5) / self.streaks * H + 9 * math.sin(i * 7.3)
            ln = W * (0.25 + 0.35 * ((i * 37) % 10) / 10) * e
            x0 = ((i * 211) % W)
            ctx.move_to(x0, y)
            ctx.line_to(x0 + self.direction * ln, y)
            ctx.set_source_rgba(1, 1, 1, 0.55 * e)
            ctx.set_line_width(max(2, H * 0.004))
            ctx.stroke()
        ctx.restore()


class Flash(Effect):
    """Impact flash: instant white that decays."""

    def __init__(self, t, d=0.25, color="white", strength=0.85):
        self.t, self.d, self.strength = t, d, strength
        self.rgb = (1, 1, 1) if color == "white" else te.hex2rgb(color)

    def draw(self, ctx, W, H, now):
        if not self.active(now):
            return
        a = self.strength * (1 - (now - self.t) / self.d) ** 2
        ctx.save()
        ctx.set_source_rgba(*self.rgb, a)
        ctx.paint()
        ctx.restore()


TRANSITIONS = {"fade": Fade, "iris": Iris, "wipe": Wipe, "whip": WhipPan, "flash": Flash}
DEFAULT_D = {"fade": 0.6, "iris": 0.9, "wipe": 0.7, "whip": 0.4, "flash": 0.25}


def make_transition(kind, t, d=None, **kw):
    """Build a transition effect starting at t; its cut point is t + d/2 (flash: t)."""
    if kind not in TRANSITIONS:
        raise ValueError(f"unknown transition {kind!r}; valid: {list(TRANSITIONS)}")
    return TRANSITIONS[kind](t, DEFAULT_D[kind] if d is None else d, **kw)


def cut_point(fx):
    return fx.t if isinstance(fx, Flash) else fx.t + fx.d / 2


def add_cut(scene, kind, t, follow, d=None, fx_kw=None, **cam):
    """Transition + camera cut at the transition's covered midpoint."""
    fx = make_transition(kind, t, d, **(fx_kw or {}))
    if not hasattr(scene, "fx"):
        scene.fx = []
    scene.fx.append(fx)
    ct = cut_point(fx)
    if hasattr(scene.camera, "dist"):  # 3D camera
        scene.camera.cut(ct, follow, **cam)
    else:
        scene.camera.cut(ct, follow, cam.get("zoom", 1.0), cam.get("y", 0.0))
    return fx


# ---------------------------------------------------------------- 2D camera with speeds
class FastCamera(te.Camera):
    """te.Camera whose keys may carry a speed (punch-ins, snap pans).
    Keys: (t, follow, zoom, y, cut, speed) — speed None = the engine default.
    lead: lead room in screen pixels — a single followed character is framed off-centre,
    with this much extra space on the side it faces (0 = centred)."""
    lead = 0.0

    def at(self, t, follow, zoom=1.0, y=0.0, speed=None):
        self.keys.append((t, follow, zoom, y, False, speed))
        self.keys.sort(key=lambda k: k[0])
        return self

    def cut(self, t, follow, zoom=1.0, y=0.0):
        self.keys.append((t, follow, zoom, y, True, None))
        self.keys.sort(key=lambda k: k[0])
        return self

    def update(self, dt, now, snap=False):
        key = None
        for k in self.keys:
            if k[0] <= now:
                key = k
        if not key:
            return
        _, follow, zoom, oy = key[:4]
        if not follow:
            return
        if len(key) > 4 and key[4] and getattr(self, "_active", None) is not key:
            snap = True
        self._active = key
        speed = key[5] if len(key) > 5 else None
        tx = sum(o.x for o in follow) / len(follow)
        lead = getattr(self, "lead", 0.0)
        if lead and len(follow) == 1 and hasattr(follow[0], "face"):
            # lead room (#50): single shots leave space in front of the subject
            tx += lead * (1 if follow[0].face >= 0 else -1) / max(0.2, zoom)
        kp = 1 if snap else min(1, dt * (speed or 3.0))
        kz = 1 if snap else min(1, dt * (speed or 2.2))
        self.x += (tx - self.x) * kp
        self.y += (oy - self.y) * kp
        self.zoom += (zoom - self.zoom) * kz
        self.sh *= max(0, 1 - dt * 8)


# ---------------------------------------------------------------- dynamic lights (#73)
# Lights are plain picklable objects. Positions are world units: x along the floor,
# y = height above the floor (up is positive). `par` is the parallax layer the light
# belongs to (1.0 = the floor / characters, 0.7 = a set's back wall, 0.88 = furniture);
# `period` repeats the light with a set's tiled decor (one lantern per wall tile).
# A Set renders its lights after the characters (Set.draw_foreground); with a plain
# toonengine.World put a LightRig in scene.world_fx instead.

def _wobble(now, seed):
    """Deterministic flicker noise in [-1, 1] (pure function of time: identical in every worker)."""
    return (0.5 * math.sin(now * 13.1 + seed * 1.7) + 0.3 * math.sin(now * 7.3 + seed * 3.1)
            + 0.2 * math.sin(now * 23.9 + seed * 0.7))


_SPRITES = {}   # per-process cache of pre-rendered radial glows (never pickled)


def _radial(ctx, sx, sy, r, color, stops, alpha, op):
    """Paint a radial falloff (stops: ((offset, alpha_mul), ...)) centred on (sx, sy).
    Large pixman radial gradients cost ~15 ns/px, so the glow is pre-rendered once per
    (radius bucket, colour, stops) into a sprite and blitted 1:1 (a fast SIMD path);
    radii are bucketed in 4% steps, which is invisible on a soft glow."""
    if r < 2 or alpha <= 0:
        return
    b = int(round(math.log(r) / math.log(1.04)))
    key = (b, tuple(round(v, 3) for v in color), stops)
    sp = _SPRITES.get(key)
    if sp is None:
        rq = 1.04 ** b
        n = int(math.ceil(rq))
        f = 4 if n > 64 else 1                      # draw the gradient small, upscale once
        lo = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2 * n // f + 2, 2 * n // f + 2)
        lc = cairo.Context(lo)
        g = cairo.RadialGradient(n / f + 1, n / f + 1, 0, n / f + 1, n / f + 1, rq / f)
        for o, m in stops:
            g.add_color_stop_rgba(o, *color, m)
        lc.set_source(g)
        lc.paint()
        sp = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2 * n, 2 * n)
        sc = cairo.Context(sp)
        sc.scale(f, f)
        sc.set_source_surface(lo, -1, -1)
        sc.get_source().set_filter(cairo.FILTER_BILINEAR)
        sc.paint()
        sp.flush()
        if len(_SPRITES) > 24:
            _SPRITES.pop(next(iter(_SPRITES)))
        _SPRITES[key] = sp
    n = sp.get_width() // 2
    ctx.save()
    ctx.set_operator(op)
    ctx.set_source_surface(sp, round(sx) - n, round(sy) - n)
    ctx.paint_with_alpha(min(1.0, alpha))
    ctx.restore()


class PointLight:
    """Round glow. intensity 0..1, radius in world units, flicker 0..1 (0 = steady).
    when: 'always' or 'night' (only lit when the scene is at night)."""
    kind = "point"

    def __init__(self, x=0.0, y=300.0, color="#ffd27a", radius=320.0, intensity=0.55, flicker=0.0,
                 par=1.0, period=None, when="always", seed=0):
        self.x, self.y, self.radius, self.intensity = float(x), float(y), float(radius), float(intensity)
        self.color = te.hex2rgb(color) if isinstance(color, str) else tuple(color)
        self.flicker, self.par, self.period, self.when, self.seed = float(flicker), float(par), period, when, seed

    def level(self, now):
        if not self.flicker:
            return self.intensity
        return max(0.0, self.intensity * (1.0 - self.flicker * (0.55 + 0.45 * _wobble(now, self.seed))))

    def lit(self, night):
        return self.when != "night" or night

    # screen-space drawing: (sx, sy) = light position on screen, s = pixels per world unit,
    # fy = screen y of the floor line
    def glow(self, ctx, sx, sy, s, fy, now, night):
        a = self.level(now) * (0.55 if night else 0.32)
        H = ctx.get_target().get_height()
        r = min(self.radius * s, 0.6 * H)
        _radial(ctx, sx, sy, r, self.color, ((0, 1.0), (0.35, 0.45), (1, 0.0)), a, cairo.OPERATOR_ADD)

    def cut(self, ctx, sx, sy, s, fy, now):
        """Punch this light's footprint out of the night darkness (DEST_OUT on the mask)."""
        a = min(1.0, self.level(now) * 1.6)
        H = ctx.get_target().get_height()
        r = min(self.radius * s * 1.25, 0.75 * H)
        _radial(ctx, sx, sy, r, (0.0, 0.0, 0.0), ((0, 1.0), (0.5, 0.6), (1, 0.0)), a, cairo.OPERATOR_DEST_OUT)

    def fixture(self, ctx, sx, sy, s, now):
        pass


class Lamp(PointLight):
    """Warm steady lamp; hanging=True also draws a small pendant lamp at the light."""
    kind = "lamp"

    def __init__(self, x=0.0, y=420.0, color="#ffd889", radius=380.0, intensity=0.6, flicker=0.03,
                 hanging=False, cord=220.0, **kw):
        super().__init__(x, y, color, radius, intensity, flicker, **kw)
        self.hanging, self.cord = bool(hanging), float(cord)

    def fixture(self, ctx, sx, sy, s, now):
        if not self.hanging:
            return
        ctx.move_to(sx, sy - self.cord * s)
        ctx.line_to(sx, sy - 18 * s)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, 3 * s))
        ctx.stroke()
        ctx.move_to(sx - 46 * s, sy + 6 * s)
        ctx.curve_to(sx - 40 * s, sy - 30 * s, sx + 40 * s, sy - 30 * s, sx + 46 * s, sy + 6 * s)
        ctx.close_path()
        ctx.set_source_rgb(0.25, 0.42, 0.4)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(max(1.5, 3 * s))
        ctx.stroke()
        ctx.arc(sx, sy + 8 * s, 12 * s, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 0.95, 0.75)
        ctx.fill()


class Fire(PointLight):
    """Campfire / brazier / candle: strong flicker, a drawn flame and rising sparks.
    size scales the flame (world units); sparks = number of embers."""
    kind = "fire"

    def __init__(self, x=0.0, y=0.0, color="#ff9a3c", radius=420.0, intensity=0.75, flicker=0.35,
                 size=60.0, sparks=10, flame=True, **kw):
        super().__init__(x, y, color, radius, intensity, flicker, **kw)
        self.size, self.sparks, self.flame = float(size), int(sparks), bool(flame)

    def fixture(self, ctx, sx, sy, s, now):
        if not self.flame:
            return
        h = self.size * s
        for k, (col, f) in enumerate((((1.0, 0.45, 0.12), 1.0), ((1.0, 0.75, 0.2), 0.68), ((1.0, 0.95, 0.65), 0.38))):
            w = h * 0.42 * f
            hh = h * f * (1 + 0.12 * _wobble(now * 1.3, self.seed + k))
            tip = sx + 0.18 * h * _wobble(now * 0.9, self.seed + 5 + k)
            ctx.move_to(sx - w, sy)
            ctx.curve_to(sx - w, sy - hh * 0.5, tip - w * 0.2, sy - hh * 0.7, tip, sy - hh)
            ctx.curve_to(tip + w * 0.2, sy - hh * 0.7, sx + w, sy - hh * 0.5, sx + w, sy)
            ctx.curve_to(sx + w, sy + w * 0.6, sx - w, sy + w * 0.6, sx - w, sy)
            ctx.close_path()
            ctx.set_source_rgb(*col)
            ctx.fill()
        for i in range(self.sparks):
            per = 1.1 + 0.37 * ((i * 7) % 5)
            u = (now / per + i * 0.618 + self.seed * 0.13) % 1.0
            px = sx + (math.sin(i * 12.9898) * 0.6 * h) + math.sin(now * 3 + i) * 0.15 * h * u
            py = sy - h * (0.6 + 2.4 * u)
            ctx.arc(px, py, max(1.0, 3.2 * s * (1 - u)), 0, 2 * math.pi)
            ctx.set_source_rgba(1, 0.8 - 0.4 * u, 0.3, 1 - u)
            ctx.fill()


class Spotlight(PointLight):
    """Theatre spot: a cone from (x, y) down to a pool on the floor at aim_x.
    spread = half-angle in degrees."""
    kind = "spot"

    def __init__(self, x=0.0, y=900.0, aim_x=None, color="#fff3c4", spread=16.0, intensity=0.6,
                 flicker=0.0, sway=0.0, **kw):
        super().__init__(x, y, color, 300.0, intensity, flicker, **kw)
        self.aim_x = float(x if aim_x is None else aim_x)
        self.spread, self.sway = float(spread), float(sway)

    def _shape(self, sx, sy, s, fy, now):
        ax = sx + (self.aim_x - self.x) * s + self.sway * s * math.sin(now * 0.6 + self.seed)
        half = max(20 * s, math.tan(math.radians(self.spread)) * self.y * s)
        return ax, half

    def _cone(self, ctx, sx, sy, s, fy, ax, half):
        ctx.move_to(sx - 14 * s, sy)
        ctx.line_to(sx + 14 * s, sy)
        ctx.line_to(ax + half, fy)
        ctx.line_to(ax - half, fy)
        ctx.close_path()

    def glow(self, ctx, sx, sy, s, fy, now, night):
        ax, half = self._shape(sx, sy, s, fy, now)
        a = self.level(now) * (0.4 if night else 0.22)
        c = self.color
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        g = cairo.LinearGradient(sx, sy, ax, fy)
        g.add_color_stop_rgba(0, *c, a * 0.3)
        g.add_color_stop_rgba(1, *c, a)
        self._cone(ctx, sx, sy, s, fy, ax, half)
        ctx.set_source(g)
        ctx.fill()
        ctx.translate(ax, fy)
        ctx.scale(1.0, 0.22)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, half * 1.25)
        g.add_color_stop_rgba(0, *c, a * 1.4)
        g.add_color_stop_rgba(1, *c, 0.0)
        ctx.arc(0, 0, half * 1.25, 0, 2 * math.pi)
        ctx.set_source(g)
        ctx.fill()
        ctx.restore()

    def cut(self, ctx, sx, sy, s, fy, now):
        ax, half = self._shape(sx, sy, s, fy, now)
        a = min(1.0, self.level(now) * 1.5)
        g = cairo.LinearGradient(sx, sy, ax, fy)
        g.add_color_stop_rgba(0, 0, 0, 0, a * 0.5)
        g.add_color_stop_rgba(1, 0, 0, 0, a)
        self._cone(ctx, sx, sy, s, fy, ax, half)
        ctx.set_source(g)
        ctx.fill()
        ctx.save()
        ctx.translate(ax, fy)
        ctx.scale(1.0, 0.3)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, half * 1.5)
        g.add_color_stop_rgba(0, 0, 0, 0, a)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.0)
        ctx.arc(0, 0, half * 1.5, 0, 2 * math.pi)
        ctx.set_source(g)
        ctx.fill()
        ctx.restore()


LIGHTS = {"point": PointLight, "lamp": Lamp, "fire": Fire, "spot": Spotlight, "spotlight": Spotlight}
NIGHT_TINT = (0.03, 0.05, 0.22)  # darkness colour, laid OVER the frame (MULTIPLY is ~10x slower)
NIGHT_ALPHA = 0.72


def make_light(spec):
    """{"type": "lamp", "x": .., "y": .., ...} -> light object (clear errors for bad keys)."""
    import inspect
    if not isinstance(spec, dict):
        raise ValueError("a light must be an object like {\"type\": \"lamp\", \"x\": 0, \"y\": 400}")
    spec = dict(spec)
    kind = spec.pop("type", "point")
    if kind not in LIGHTS:
        raise ValueError(f"unknown light type {kind!r}; valid: {sorted(LIGHTS)}")
    cls = LIGHTS[kind]
    ok = set()
    for c in cls.__mro__:
        if "__init__" in c.__dict__:
            ok |= set(inspect.signature(c.__init__).parameters) - {"self", "kw"}
    bad = set(spec) - ok
    if bad:
        raise ValueError(f"light {kind!r}: unknown option(s) {sorted(bad)}; valid: {sorted(ok)}")
    if spec.get("when", "always") not in ("always", "night"):
        raise ValueError("light 'when' must be 'always' or 'night'")
    return cls(**spec)


def render_lights(ctx, W, H, placed, night, tint=NIGHT_TINT, strength=1.0, now=0.0):
    """Screen-space lighting pass. placed: [(light, sx, sy, s, floor_y)].
    night: darken the frame (multiply by tint) except where lights reach, then add glows."""
    placed = [p for p in placed if p[0].lit(night)]
    if night:
        ctx.save()
        ctx.identity_matrix()
        ctx.push_group()
        k = max(0.0, min(1.0, strength))
        ctx.set_source_rgba(*tint, NIGHT_ALPHA * k)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_DEST_OUT)
        for (lt, sx, sy, s, fy) in placed:
            lt.cut(ctx, sx, sy, s, fy, now)
        mask = ctx.pop_group()
        ctx.set_source(mask)
        ctx.paint()
        ctx.restore()
    for (lt, sx, sy, s, fy) in placed:
        lt.fixture(ctx, sx, sy, s, now)
    for (lt, sx, sy, s, fy) in placed:
        if -lt.radius * s * 2 < sx < W + lt.radius * s * 2:
            lt.glow(ctx, sx, sy, s, fy, now, night)


class LightRig:
    """world_fx for scenes without a Set: lights in world space (+ optional night).
    scene.world_fx.append(LightRig([Lamp(0, 400)], night=True)). Drawn after the characters."""

    def __init__(self, lights=(), night=False, tint=NIGHT_TINT, strength=1.0):
        self.lights, self.night, self.tint, self.strength = list(lights), bool(night), tint, strength

    def draw_world(self, ctx, now):
        surf = ctx.get_target()
        W, H = surf.get_width(), surf.get_height()
        m = ctx.get_matrix()
        fy = ctx.user_to_device(0, 0)[1]
        placed = []
        for lt in self.lights:
            sx, sy = ctx.user_to_device(lt.x, -lt.y)
            placed.append((lt, sx, sy, m.xx, fy))
        ctx.save()
        ctx.identity_matrix()
        render_lights(ctx, W, H, placed, self.night, self.tint, self.strength, now)
        ctx.restore()


class NightGrade(Effect):
    """Screen fx: blue night grade over the whole frame (no light holes; use a Set's
    night mode or a LightRig for lit areas). strength 0..1."""

    def __init__(self, strength=0.75, tint=NIGHT_TINT, t=0.0, d=1e9):
        self.t, self.d = t, d
        self.strength, self.tint = strength, tint

    def draw(self, ctx, W, H, now):
        if not self.active(now):
            return
        ctx.save()
        ctx.set_source_rgba(*self.tint, NIGHT_ALPHA * self.strength)
        ctx.paint()
        ctx.restore()

# ---------------------------------------------------------------- texture styles (#72)
# Per-theme / per-episode hand-made looks, drawn as ONE screen effect after the world
# (before subtitles/captions, so burned-in text stays crisp). Everything heavy is built once
# per worker process: tiling noise textures (numpy -> cairo ImageSurface, a few variants)
# that are composited per frame with plain OVER paints (pixman's SIMD fast path; MULTIPLY /
# SOFT_LIGHT cost 10-35 ms a frame at 720x1280, OVER with an alpha tile < 1 ms). A "multiply
# by grey" is an OVER of black with alpha; a "lighten" is an OVER of the paper colour.
# Per-frame numpy work is limited to a quarter-resolution wash (watercolour) and one
# uint32 gather for wobbly edges (crayon/chalk): see STYLE_COST_MS / demo_l.py for timings.
#
#     make_style("crayon")                                    -> CrayonStyle
#     make_style({"name": "paper", "intensity": 0.5, "boil": 0, "seed": 4})
#     scene.fx.insert(0, make_style("watercolour", fps=scene.fps))
#
# intensity 0..1 scales every layer; boil = k re-randomises the texture every k frames
# (deterministic per seed; 0 = static paper); fps is the scene's frame rate (boil timing).

def _np():
    import numpy as np
    return np


def _periodic_noise(shape, sigma, rng, aniso=None):
    """Tileable smooth noise (zero mean, unit std) by low-passing white noise with an FFT.
    sigma = feature size in pixels; aniso = (angle_rad, stretch) for streaky noise."""
    np = _np()
    h, w = shape
    white = rng.standard_normal((h, w)).astype(np.float32)
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    if aniso:
        ang, k = aniso
        ca, sa = math.cos(ang), math.sin(ang)
        u, v = fx * ca + fy * sa, -fx * sa + fy * ca
        r2 = (u / k) ** 2 + (v * k) ** 2
    else:
        r2 = fx ** 2 + fy ** 2
    filt = np.exp(-2 * (math.pi * sigma) ** 2 * r2)
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * filt)).astype(np.float32)
    out -= out.mean()
    sd = out.std()
    return out / sd if sd > 0 else out


def _over(acc, rgb, a):
    """acc = (premultiplied rgb HxWx3, alpha HxW); composite a layer (rgb, alpha array) OVER it."""
    np = _np()
    a = np.clip(a, 0, 1).astype(np.float32)
    prgb, pa = acc
    col = np.asarray(rgb, np.float32)
    prgb = prgb * (1 - a)[..., None] + (a[..., None] * col if col.ndim == 1 else a[..., None] * col)
    return prgb, pa * (1 - a) + a


def _layers_surface(h, w, layers):
    """Bake OVER-composited layers [(rgb, alpha_array)] into one premultiplied ARGB32 surface."""
    np = _np()
    acc = (np.zeros((h, w, 3), np.float32), np.zeros((h, w), np.float32))
    for rgb, a in layers:
        acc = _over(acc, rgb, a)
    return _surface_from_premul(*acc)


def _surface_from_premul(prgb, pa):
    np = _np()
    h, w = pa.shape
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    s = surf.get_stride() // 4
    buf = np.ndarray((h, s, 4), np.uint8, surf.get_data())
    buf[:, :w, 0] = np.clip(prgb[..., 2] * 255 + 0.5, 0, 255)   # BGRA (little-endian ARGB32)
    buf[:, :w, 1] = np.clip(prgb[..., 1] * 255 + 0.5, 0, 255)
    buf[:, :w, 2] = np.clip(prgb[..., 0] * 255 + 0.5, 0, 255)
    buf[:, :w, 3] = np.clip(pa * 255 + 0.5, 0, 255)
    surf.mark_dirty()
    return surf


def _smooth(x, rounds=1):
    """Cheap separable [1 2 1]/4 blur with edge padding (works on HxW or HxWxC)."""
    np = _np()
    for _ in range(rounds):
        p = np.pad(x, [(1, 1), (1, 1)] + [(0, 0)] * (x.ndim - 2), mode="edge")
        x = (p[:-2] + 2 * p[1:-1] + p[2:]) * 0.25
        x = (x[:, :-2] + 2 * x[:, 1:-1] + x[:, 2:]) * 0.25
    return x


def _wobble_index(W, H, S, amp, wavelength, rng):
    """Flat int32 gather index (row stride S pixels) that displaces the frame by a smooth
    field of +-amp pixels with the given wavelength: wobbly, hand-drawn edges."""
    np = _np()
    h, w = max(2, H // 8), max(2, W // 8)
    sig = max(1.0, wavelength / 8 / 2.5)
    fields = []
    for _ in range(2):
        n = _periodic_noise((h, w), sig, rng)
        # bilinear upsample to H x W
        yy = np.linspace(0, h - 1, H, dtype=np.float32)
        xx = np.linspace(0, w - 1, W, dtype=np.float32)
        y0, x0 = np.floor(yy).astype(int), np.floor(xx).astype(int)
        y1, x1 = np.minimum(y0 + 1, h - 1), np.minimum(x0 + 1, w - 1)
        fy, fx = (yy - y0)[:, None], (xx - x0)[None, :]
        top = n[y0][:, x0] * (1 - fx) + n[y0][:, x1] * fx
        bot = n[y1][:, x0] * (1 - fx) + n[y1][:, x1] * fx
        fields.append((top * (1 - fy) + bot * fy) * amp)
    gy, gx = np.mgrid[0:H, 0:W]
    sx = np.clip(np.rint(gx + fields[0]), 0, W - 1).astype(np.int32)
    sy = np.clip(np.rint(gy + fields[1]), 0, H - 1).astype(np.int32)
    return (sy * S + sx).ravel()


class TextureStyle:
    """Base texture style: a screen fx with draw(ctx, W, H, now). Picklable: caches
    (attributes starting with '_c') are dropped when pickled and rebuilt lazily in each
    worker. Subclasses build tiles in _build(W, H) and paint them in _paint(...)."""
    name = "clean"
    t, d = 0.0, 1e9
    default_intensity, default_boil = 0.6, 0
    TILE = 512
    VARIANTS = 3

    def __init__(self, intensity=None, boil=None, seed=7, fps=30, **opts):
        self.intensity = float(self.default_intensity if intensity is None else intensity)
        self.intensity = max(0.0, min(1.0, self.intensity))
        self.boil = int(self.default_boil if boil is None else boil)
        self.seed, self.fps = int(seed), float(fps or 30)
        bad = set(opts) - set(self.OPTIONS)
        if bad:
            raise ValueError(f"style {self.name!r}: unknown option(s) {sorted(bad)}; "
                             f"valid: {sorted({'name', 'intensity', 'boil', 'seed'} | set(self.OPTIONS))}")
        for k, v in self.OPTIONS.items():
            setattr(self, k, opts.get(k, v))
        self._c = None

    OPTIONS = {}

    def __getstate__(self):
        d = self.__dict__.copy()
        for k in list(d):
            if k.startswith("_c"):
                d[k] = None
        return d

    def __repr__(self):
        return f"{type(self).__name__}(intensity={self.intensity}, boil={self.boil}, seed={self.seed})"

    def active(self, now):
        return True

    # ---- boil: which texture variant / offset is shown at time `now`
    def boil_step(self, now):
        """Integer that changes only every `boil` frames (0 when boil is off)."""
        if self.boil <= 0:
            return 0
        return int(math.floor(now * self.fps + 1e-6)) // self.boil

    def _offset(self, step, n):
        rng = random.Random(self.seed * 1000003 + step * 7919 + 17)
        return rng.randrange(n), rng.randrange(n), step % self.VARIANTS

    # ---- helpers for subclasses
    def _scale(self, W, H):
        return max(0.25, min(W, H) / 720.0)

    def _paint_tile(self, ctx, tile, step, k, alpha=1.0, extra_scale=1.0):
        """Paint a repeating tile OVER the frame, shifted by the boil offset (k = px scale)."""
        if alpha <= 0:
            return
        ox, oy, _ = self._offset(step, tile.get_width())
        pat = cairo.SurfacePattern(tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        pat.set_filter(cairo.FILTER_BILINEAR if k * extra_scale != 1 else cairo.FILTER_FAST)
        m = cairo.Matrix()
        m.scale(1 / (k * extra_scale), 1 / (k * extra_scale))
        m.translate(ox, oy)
        pat.set_matrix(m)
        ctx.set_source(pat)
        if alpha >= 0.999:
            ctx.paint()
        else:
            ctx.paint_with_alpha(alpha)

    def _target_array(self, ctx, W, H):
        """uint8 (H, stride/4, 4) view of the target surface, or None if it is not an image."""
        target = ctx.get_target()
        if not isinstance(target, cairo.ImageSurface) or target.get_format() != cairo.FORMAT_ARGB32:
            return None, None
        if target.get_width() != W or target.get_height() != H:
            return None, None
        target.flush()
        np = _np()
        S = target.get_stride() // 4
        return target, np.ndarray((H, S, 4), np.uint8, target.get_data())

    def _wobble(self, ctx, W, H, step, key="wobble"):
        """Displace the frame with one of the precomputed wobble fields (uint32 gather)."""
        if not self._c.get(key):
            return
        target, arr = self._target_array(ctx, W, H)
        if arr is None:
            return
        np = _np()
        idx = self._c[key][step % len(self._c[key])]
        flat = arr.view(np.uint32).reshape(-1)
        flat[:] = flat[idx]
        target.mark_dirty()

    def _build_wobble(self, W, H, amp, wavelength, variants):
        target = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        S = target.get_stride() // 4
        np = _np()
        rng = np.random.default_rng(self.seed + 101)
        out = []
        for _ in range(variants):
            idx = _wobble_index(W, H, S, amp, wavelength, rng)
            if S != W:   # keep padding columns mapped to themselves
                full = np.arange(H * S, dtype=np.int32).reshape(H, S)
                full[:, :W] = idx.reshape(H, W)
                idx = full.ravel()
            out.append(idx)
        return out

    def _vignette_surface(self, W, H, strength, color=(0.25, 0.16, 0.08)):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(surf)
        r = math.hypot(W, H) / 2
        g = cairo.RadialGradient(W / 2, H * 0.45, r * 0.42, W / 2, H * 0.45, r * 1.08)
        g.add_color_stop_rgba(0, *color, 0.0)
        g.add_color_stop_rgba(0.6, *color, strength * 0.45)
        g.add_color_stop_rgba(1, *color, strength)
        c.set_source(g)
        c.paint()
        return surf

    # ---- main entry
    def draw(self, ctx, W, H, now):
        if self.intensity <= 0:
            return
        if self._c is None or self._c.get("size") != (W, H):
            self._c = {"size": (W, H)}
            self._build(W, H)
        ctx.save()
        ctx.identity_matrix()
        ctx.reset_clip()
        ctx.set_operator(cairo.OPERATOR_OVER)
        self._paint(ctx, W, H, now, self.boil_step(now))
        ctx.restore()

    def _build(self, W, H):
        pass

    def _paint(self, ctx, W, H, now, step):
        pass


class CleanStyle(TextureStyle):
    """No texture (the plain vector look)."""
    name = "clean"
    default_intensity = 0.0


class PaperStyle(TextureStyle):
    """Printed-on-paper look: warm paper tint, fine grain + fibres, soft mottling, vignette."""
    name = "paper"
    default_intensity, default_boil = 0.6, 0
    OPTIONS = {"tint": "#f6ead2", "vignette": 0.32}

    def _build(self, W, H):
        np = _np()
        i, n = self.intensity, self.TILE
        rng = np.random.default_rng(self.seed)
        tint = te.hex2rgb(self.tint) if isinstance(self.tint, str) else tuple(self.tint)
        tiles = []
        for v in range(1 if self.boil <= 0 else 2):
            grain = _periodic_noise((n, n), 0.7, rng)
            mid = _periodic_noise((n, n), 3.0, rng)
            mottle = _periodic_noise((n, n), 40.0, rng)
            base = (0.15 + 0.05 * mottle) * i
            blotch = np.clip(mottle - 0.6, 0, None) * 0.10 * i
            dark = np.clip(grain * 0.8 + mid * 0.25 - 0.75, 0, None) * 0.26 * i
            light = np.clip(-grain * 0.8 - mid * 0.25 - 0.8, 0, None) * 0.32 * i
            surf = _layers_surface(n, n, [(tint, base), ((0.55, 0.42, 0.28), blotch),
                                          ((0.30, 0.22, 0.14), dark), ((1, 1, 1), light)])
            self._fibres(surf, n, random.Random(self.seed * 31 + v), i)
            tiles.append(surf)
        self._c["tiles"] = tiles
        self._c["vig"] = self._vignette_surface(W, H, self.vignette * i)

    def _fibres(self, surf, n, rng, i):
        c = cairo.Context(surf)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        for _ in range(110):
            x, y = rng.uniform(0, n), rng.uniform(0, n)
            ang, ln = rng.uniform(0, math.pi * 2), rng.uniform(10, 38)
            bend = rng.uniform(-8, 8)
            dark = rng.random() < 0.55
            col = (0.38, 0.29, 0.19, 0.22 * i) if dark else (1, 1, 1, 0.30 * i)
            for dx in (-n, 0, n):            # wrap around: the tile stays seamless
                for dy in (-n, 0, n):
                    x0, y0 = x + dx, y + dy
                    x1, y1 = x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln
                    c.move_to(x0, y0)
                    c.curve_to((x0 + x1) / 2 + bend, (y0 + y1) / 2 - bend, x1, y1, x1, y1)
            c.set_source_rgba(*col)
            c.set_line_width(rng.uniform(0.6, 1.4))
            c.stroke()
        surf.flush()

    def _paint(self, ctx, W, H, now, step):
        k = self._scale(W, H)
        tiles = self._c["tiles"]
        self._paint_tile(ctx, tiles[step % len(tiles)], step, k)
        ctx.set_source_surface(self._c["vig"], 0, 0)
        ctx.paint()


class CrayonStyle(TextureStyle):
    """Wax crayon on paper: wobbly boiling edges, paper tooth breaking up fills and ink
    (light specks along a stroke direction), waxy pressure streaks."""
    name = "crayon"
    default_intensity, default_boil = 0.6, 3
    OPTIONS = {"paper": "#fbf5e8", "wobble": 1.0, "angle": 62}

    def _build(self, W, H):
        np = _np()
        i, n = self.intensity, self.TILE
        rng = np.random.default_rng(self.seed)
        paper = te.hex2rgb(self.paper) if isinstance(self.paper, str) else tuple(self.paper)
        ang = math.radians(self.angle)
        tiles = []
        for v in range(min(2, self.VARIANTS) if self.boil > 0 else 1):
            streak = _periodic_noise((n, n), 1.1, rng, aniso=(ang, 5.0))
            fine = _periodic_noise((n, n), 0.6, rng)
            press = _periodic_noise((n, n), 26.0, rng, aniso=(ang, 2.5))
            tooth = streak * 0.7 + fine * 0.45 + press * 0.35
            light = np.clip((tooth - 0.35) * 0.6, 0, 1) * 1.25 * i         # paper shows through
            dark = np.clip((-tooth - 0.8) * 0.5, 0, 1) * 0.40 * i          # wax build-up
            base = np.full((n, n), 0.035 * i, np.float32)
            tiles.append(_layers_surface(n, n, [(paper, base), ((0.1, 0.07, 0.05), dark), (paper, light)]))
        self._c["tiles"] = tiles
        k = self._scale(W, H)
        amp = 1.7 * k * self.wobble * (0.4 + 0.6 * i)
        nvar = self.VARIANTS if self.boil > 0 else 1
        self._c["wobble"] = self._build_wobble(W, H, amp, 34 * k, nvar) if amp >= 0.5 else []
        self._c["vig"] = self._vignette_surface(W, H, 0.18 * i)

    def _paint(self, ctx, W, H, now, step):
        self._wobble(ctx, W, H, step)
        tiles = self._c["tiles"]
        self._paint_tile(ctx, tiles[step % len(tiles)], step, self._scale(W, H))
        ctx.set_source_surface(self._c["vig"], 0, 0)
        ctx.paint()


class WatercolourStyle(TextureStyle):
    """Watercolour wash: quarter-resolution soft, desaturated colour wash with pigment
    pooling at shape edges and blotchy density, laid over the frame; cold-press paper grain."""
    name = "watercolour"
    default_intensity, default_boil = 0.6, 0
    OPTIONS = {"paper": "#fbf6ea", "desaturate": 0.45, "edges": 1.0, "bleed": 1.0}
    F = 4      # wash resolution divisor

    def _build(self, W, H):
        np = _np()
        i, n = self.intensity, self.TILE
        rng = np.random.default_rng(self.seed)
        paper = te.hex2rgb(self.paper) if isinstance(self.paper, str) else tuple(self.paper)
        tiles = []
        for v in range(1 if self.boil <= 0 else 2):
            bump = _periodic_noise((n, n), 1.6, rng)
            fine = _periodic_noise((n, n), 0.7, rng)
            g = bump * 0.6 + fine * 0.5
            light = np.clip(g - 0.9, 0, None) * 0.12 * i
            dark = np.clip(-g - 0.8, 0, None) * 0.20 * i                   # granulation
            base = np.full((n, n), 0.06 * i, np.float32)
            tiles.append(_layers_surface(n, n, [(paper, base), ((0.30, 0.26, 0.22), dark), ((1, 1, 1), light)]))
        self._c["tiles"] = tiles
        f = self.F
        h, w = (H + f - 1) // f, (W + f - 1) // f
        k = self._scale(W, H)
        blot = [_periodic_noise((h, w), 22.0 * k, rng) * 0.55 + _periodic_noise((h, w), 7.0 * k, rng) * 0.35
                + _periodic_noise((h, w), 2.0 * k, rng) * 0.2 for _ in range(1 if self.boil <= 0 else 2)]
        self._c["blot"] = [(1.0 - 0.26 * i * np.clip(b, -1.5, 2.0)).astype(np.float32) for b in blot]
        self._c["wash"] = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        self._c["vig"] = self._vignette_surface(W, H, 0.16 * i, color=(0.22, 0.18, 0.12))
        self._c["wob"] = self._build_wobble(W, H, 1.0 * k, 46 * k, 1) if i >= 0.3 else []

    def _wash(self, ctx, W, H, step):
        np = _np()
        target, arr = self._target_array(ctx, W, H)
        if arr is None:
            return None
        f, i = self.F, self.intensity
        small = arr[::f, :W:f, :3].astype(np.float32) * (1 / 255.0)       # BGR
        sh, sw = small.shape[:2]
        soft = _smooth(small, 2)
        lum = soft[..., 0] * 0.114 + soft[..., 1] * 0.587 + soft[..., 2] * 0.299
        # pigment pooling: darken along colour edges (gradient of the softened image)
        sharp = _smooth(small, 1)
        gx = np.abs(np.diff(sharp, axis=1, append=sharp[:, -1:])).sum(-1)
        gy = np.abs(np.diff(sharp, axis=0, append=sharp[-1:])).sum(-1)
        edge = _smooth(np.clip((gx + gy) * 2.5, 0, 1), 1)
        de = self.desaturate
        wash = soft * (1 - de) + lum[..., None] * de
        wash = wash * 0.88 + 0.12                                             # paper glows through
        blot = self._c["blot"][step % len(self._c["blot"])][:sh, :sw]
        wash *= (blot * (1 - 0.65 * self.edges * i * edge))[..., None]
        # bleed: a wider blur so colour drifts past the lines
        wash = _smooth(wash, int(1 + self.bleed))
        alpha = 0.40 + 0.18 * edge * self.edges
        a = np.clip(alpha, 0, 1)
        surf = self._c["wash"]
        S = surf.get_stride() // 4
        buf = np.ndarray((surf.get_height(), S, 4), np.uint8, surf.get_data())
        buf[:sh, :sw, :3] = np.clip(wash * a[..., None] * 255, 0, 255)
        buf[:sh, :sw, 3] = np.clip(a * 255, 0, 255)
        surf.mark_dirty()
        return surf

    def _paint(self, ctx, W, H, now, step):
        self._wobble(ctx, W, H, 0, key="wob")
        wash = self._wash(ctx, W, H, step)
        if wash is not None:
            ctx.save()
            ctx.scale(self.F, self.F)
            ctx.set_source_surface(wash, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
            ctx.paint_with_alpha(min(1.0, 0.95 * self.intensity))
            ctx.restore()
        tiles = self._c["tiles"]
        self._paint_tile(ctx, tiles[step % len(tiles)], step, self._scale(W, H))
        ctx.set_source_surface(self._c["vig"], 0, 0)
        ctx.paint()


class ChalkStyle(CrayonStyle):
    """Chalk on a blackboard: dark board tint, chalk dust smudges, grainy light strokes."""
    name = "chalk"
    default_intensity, default_boil = 0.7, 3
    OPTIONS = {"board": "#24332b", "wobble": 0.8, "angle": 20, "chalk_lines": True}

    def _build(self, W, H):
        np = _np()
        i, n = self.intensity, self.TILE
        rng = np.random.default_rng(self.seed)
        board = te.hex2rgb(self.board) if isinstance(self.board, str) else tuple(self.board)
        ang = math.radians(self.angle)
        tiles = []
        for v in range(2 if self.boil > 0 else 1):
            streak = _periodic_noise((n, n), 1.0, rng, aniso=(ang, 4.0))
            fine = _periodic_noise((n, n), 0.6, rng)
            smudge = _periodic_noise((n, n), 45.0, rng, aniso=(ang, 1.8))
            tooth = streak * 0.6 + fine * 0.55
            base = (0.74 + 0.06 * smudge) * i
            gaps = np.clip((tooth - 0.45) * 0.6, 0, 1) * 0.9 * i             # board shows through
            dust = (np.clip((-tooth - 1.2) * 0.5, 0, 1) * 0.35 + np.clip(smudge - 0.8, 0, None) * 0.06) * i
            tiles.append(_layers_surface(n, n, [(board, base), (board, gaps), ((0.93, 0.95, 0.9), dust)]))
        self._c["tiles"] = tiles
        k = self._scale(W, H)
        amp = 1.4 * k * self.wobble * (0.4 + 0.6 * i)
        nvar = self.VARIANTS if self.boil > 0 else 1
        self._c["wobble"] = self._build_wobble(W, H, amp, 30 * k, nvar) if amp >= 0.5 else []
        self._c["vig"] = self._vignette_surface(W, H, 0.35 * i, color=(0.05, 0.08, 0.06))

    def _board_rgb(self):
        return te.hex2rgb(self.board) if isinstance(self.board, str) else tuple(self.board)

    def _chalk_lines(self, ctx, W, H):
        """Ink outlines become chalk: near-black pixels are redrawn in chalk white."""
        target, arr = self._target_array(ctx, W, H)
        if arr is None:
            return
        np = _np()
        g = arr[..., 1]
        m = g < 72
        m &= arr[..., 2] < 90
        m &= arr[..., 0] < 100
        v = int(200 + 40 * self.intensity)
        col = np.uint32(0xFF000000 | (v << 16) | ((v + 4) << 8) | (v - 8))
        # paper-white areas (eye whites, bubbles) become board so the drawing reads inverted
        w = arr[..., 1] > 232
        w &= arr[..., 2] > 232
        w &= arr[..., 0] > 225
        br, bg, bb = (int(c * 255 * 0.8 + 40) for c in self._board_rgb())
        arr.view(np.uint32)[..., 0][w] = np.uint32(0xFF000000 | (br << 16) | (bg << 8) | bb)
        arr.view(np.uint32)[..., 0][m] = col
        target.mark_dirty()

    def _paint(self, ctx, W, H, now, step):
        if self.chalk_lines:
            self._chalk_lines(ctx, W, H)
        super()._paint(ctx, W, H, now, step)


STYLES = {"clean": CleanStyle, "paper": PaperStyle, "crayon": CrayonStyle,
          "watercolour": WatercolourStyle, "watercolor": WatercolourStyle, "chalk": ChalkStyle}


def _style_parts(spec):
    """Normalise a style spec (name string or {"name", "intensity", "boil", ...}) to (name, kwargs)."""
    if spec is None or spec is False:
        return "clean", {}
    if isinstance(spec, str):
        name, kw = spec, {}
    elif isinstance(spec, dict):
        kw = dict(spec)
        name = kw.pop("name", None)
        if not isinstance(name, str):
            raise ValueError(f"style object needs a 'name'; valid: {sorted(STYLES)}")
    else:
        raise ValueError(f"style must be a name or an object like {{\"name\": \"crayon\", \"intensity\": 0.5}}; "
                         f"valid names: {sorted(STYLES)}")
    name = name.lower().strip()
    if name not in STYLES:
        raise ValueError(f"unknown style {name!r}; valid: {sorted(STYLES)}")
    if "intensity" in kw and not (isinstance(kw["intensity"], (int, float)) and not isinstance(kw["intensity"], bool)
                                  and 0 <= kw["intensity"] <= 1):
        raise ValueError("style 'intensity' must be a number from 0 to 1")
    if "boil" in kw and not (isinstance(kw["boil"], int) and not isinstance(kw["boil"], bool) and 0 <= kw["boil"] <= 60):
        raise ValueError("style 'boil' must be a whole number of frames (0 = static, 3 = every 3rd frame)")
    if "seed" in kw and not isinstance(kw["seed"], int):
        raise ValueError("style 'seed' must be an integer")
    return name, kw


def make_style(spec, fps=30):
    """Texture-style screen fx from a name or {"name", "intensity", "boil", "seed", ...}.
    Returns None for "clean" (nothing to draw). Raises ValueError with the valid options."""
    name, kw = _style_parts(spec)
    if name == "clean":
        return None
    return STYLES[name](fps=fps, **kw)


def validate_style(spec):
    """Error message (str) for a bad style spec, or None."""
    try:
        name, kw = _style_parts(spec)
        if name != "clean":
            STYLES[name](**kw)
    except (ValueError, TypeError) as e:
        return str(e)
    return None


# ---------------------------------------------------------------- framing helpers
def char_height(ch):
    """World height of a character's head top above its feet (dry draw, no side effects
    beyond head_world)."""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
    ctx = cairo.Context(surf)
    ox, oy = ch.x, ch.y
    hw = getattr(ch, "head_world", None)
    try:
        ch.x, ch.y = 0.0, 0.0
        ch.draw(ctx, 0.0)
        h = ch.head_world[1]
    except Exception:
        h = 180.0 * getattr(ch, "scale", 1.0)
    finally:
        ch.x, ch.y = ox, oy
        if hw is not None:
            ch.head_world = hw
    return max(40.0, float(h))


def vertical_lift(H, gy, zoom, height, centre=0.5, lo=0.58, hi=0.72):
    """Camera y (2D) for vertical frames: centre the characters (feet-to-head) around
    `centre` of the height, keeping the ground line between `lo` and `hi` of the frame,
    so neither a big empty sky nor a big empty ground remains. Only lifts (<= 0)."""
    g_target = H * centre + 0.5 * height * zoom      # where the ground line should be
    g_target = max(H * lo, min(H * hi, g_target))
    # ground line on screen = gy + zoom * y
    return min(0.0, (g_target - gy) / zoom)


# ---------------------------------------------------------------- thumbnails
def _expressive_time(scene):
    """Most 'thumbnail-worthy' moment: a line spoken with a strong emotion, else the
    first line, else the first caption, else 30% in."""
    best, score = None, -1
    strong = {"surprised": 5, "scared": 5, "angry": 4, "excited": 4, "confused": 3, "dizzy": 3, "sad": 2}
    for c in scene.characters:
        for ln in c.lines:
            t = ln["t"] + ln["d"] * 0.45
            sc = strong.get(c.expression(t), 1)
            if sc > score:
                best, score = t, sc
    if best is None and scene.captions:
        best = scene.captions[0][0] + 0.4
    return best if best is not None else scene.duration * 0.3


def _punch_pixels(surf, sat=1.25, contrast=1.08):
    import numpy as np
    surf.flush()
    W, H = surf.get_width(), surf.get_height()
    stride = surf.get_stride()
    buf = np.ndarray((H, stride // 4, 4), dtype=np.uint8, buffer=surf.get_data())
    px = buf[:, :W, :3].astype(np.float32)
    grey = px.mean(axis=2, keepdims=True)
    px = grey + (px - grey) * sat
    px = (px - 128) * contrast + 128
    buf[:, :W, :3] = np.clip(px, 0, 255).astype(np.uint8)
    surf.mark_dirty()


def _title(ctx, W, H, text, vertical):
    ctx.select_font_face(te.FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    fs = W * (0.13 if vertical else 0.095)
    words = text.upper().split()
    maxw = W * 0.9

    def wrap(size):
        ctx.set_font_size(size)
        lines, cur = [], []
        for w in words:
            t = " ".join(cur + [w])
            if cur and ctx.text_extents(t).x_advance > maxw:
                lines.append(" ".join(cur))
                cur = [w]
            else:
                cur.append(w)
        lines.append(" ".join(cur))
        return lines

    lines = wrap(fs)
    while (len(lines) > 3 or any(ctx.text_extents(l).x_advance > maxw for l in lines)) and fs > 20:
        fs *= 0.9
        lines = wrap(fs)
    y = H * (0.16 if vertical else 0.2)
    for i, ln in enumerate(lines):
        ext = ctx.text_extents(ln)
        x = (W - ext.x_advance) / 2
        ctx.move_to(x + fs * 0.06, y + fs * 0.08)  # drop shadow
        ctx.text_path(ln)
        ctx.set_source_rgba(0, 0, 0, 0.45)
        ctx.fill()
        ctx.move_to(x, y)
        ctx.text_path(ln)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(fs * 0.2)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
        ctx.set_source_rgb(1, 0.85, 0.2) if i % 2 == 0 else ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        y += fs * 1.08


def _vignette(ctx, W, H):
    g = cairo.RadialGradient(W / 2, H / 2, min(W, H) * 0.35, W / 2, H / 2, math.hypot(W, H) * 0.6)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.45)
    ctx.set_source(g)
    ctx.paint()


def thumbnail(src, out_png, title, time=None, size=None):
    """Thumbnail from an episode (JSON path/dict) or an MP4. Picks an expressive moment
    unless `time` is given; adds saturation punch, vignette and a big outlined title.
    Size: the episode/video's own size (vertical stays vertical) unless `size` given."""
    if isinstance(src, str) and src.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                    "csv=p=0", src], capture_output=True, text=True).stdout.strip() or 0)
        t = time if time is not None else dur * 0.35
        tmp = out_png + ".frame.png"
        vf = [] if size is None else ["-vf", f"scale={size[0]}:{size[1]}"]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", *vf, tmp],
                       check=True)
        surf = cairo.ImageSurface.create_from_png(tmp)
        os.remove(tmp)
    else:
        import toonscript
        scene = toonscript.build_episode(src)
        scene.subtitles, scene.bubbles = False, False
        scene.captions = []
        scene.fx = []
        t = time if time is not None else _expressive_time(scene)
        dt = 1.0 / scene.fps
        while scene.time < t:
            scene.step(dt)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, scene.W, scene.H)
        if hasattr(scene, "stairs"):  # 3D
            import toon3d
            toon3d.draw_frame3d(surf, scene.static(), scene.snapshot())
        else:
            te.draw_frame(surf, scene.static(), scene.snapshot())
    W, H = surf.get_width(), surf.get_height()
    _punch_pixels(surf)
    ctx = cairo.Context(surf)
    _vignette(ctx, W, H)
    if title:
        _title(ctx, W, H, title, H > W)
    surf.write_to_png(out_png)
    return out_png


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "thumb":
        tm = None
        if "--time" in a:
            i = a.index("--time")
            tm = float(a[i + 1])
            a = a[:i] + a[i + 2:]
        print("wrote", thumbnail(a[1], a[2], a[3] if len(a) > 3 else "", time=tm))
    else:
        print(__doc__)
