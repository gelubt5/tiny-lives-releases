"""
ToonSets — interior / tall background sets and per-channel style themes
for the 2D ToonEngine (Cairo, CPU only).  Roadmap #60 + #74.

A Set has the same interface as toonengine.World:
    draw(ctx, W, H, cam, gy, now)
and pickles, so it can replace scene.world (it goes into Scene.static() and the
multiprocessing render).  Sets are drawn in parallax layers around the floor
line (gy): back wall (slow), mid furniture, floor (moves with the characters).
Everything is filled from the floor up past the top of the frame, so tall 9:16
shots never show empty sky.

Sets:   barn, farmyard, kitchen, living_room, classroom, bedroom, street, stage
Themes: farm_files, kitchen_chaos, max_and_grandma, fruit_stories,
        stickman_lesson, did_you_know

    import toonsets
    scene.world = toonsets.make_set("kitchen", wall="#f6efe4")
    scene.fx = toonsets.theme_fx("kitchen_chaos") + scene.fx

ToonScript episodes:  "set": "barn"  or  {"name": "barn", "wall": "#..."},
                      "theme": "farm_files"   (2D only for now)
"""
import math
import random

import cairo

import toonfx

INK = (0.169, 0.133, 0.2)


def hex2rgb(h):
    if isinstance(h, (tuple, list)):
        return tuple(h)
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


# ---------------------------------------------------------------- drawing helpers
def _rrect(ctx, x, y, w, h, r=0.0):
    r = min(r, w / 2, h / 2)
    if r <= 0:
        ctx.rectangle(x, y, w, h)
        return
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def box(ctx, x, y, w, h, col, r=0.0, lw=3.0, shade_side=True, outline=True):
    """Filled, ink-outlined rounded rectangle with a soft cel shade on the right."""
    _rrect(ctx, x, y, w, h, r)
    ctx.set_source_rgb(*col)
    ctx.fill_preserve()
    if shade_side:
        ctx.save()
        ctx.clip_preserve()
        ctx.new_path()
        ctx.rectangle(x + w * 0.72, y, w * 0.28 + 1, h)
        ctx.set_source_rgba(*shade(col, 0.82), 0.55)
        ctx.fill()
        ctx.rectangle(x, y, w, max(2.0, h * 0.06))
        ctx.set_source_rgba(1, 1, 1, 0.18)
        ctx.fill()
        ctx.restore()
        _rrect(ctx, x, y, w, h, r)
    if outline:
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    else:
        ctx.new_path()


def line(ctx, pts, col=INK, lw=3.0, alpha=1.0):
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(*col, alpha)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def circle(ctx, x, y, r, col, lw=3.0, outline=True, alpha=1.0):
    ctx.new_path()
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*col, alpha)
    if outline:
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(lw)
        ctx.stroke()
    else:
        ctx.fill()


def poly(ctx, pts, col, lw=3.0, outline=True, alpha=1.0):
    ctx.new_path()
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_source_rgba(*col, alpha)
    if outline:
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(lw)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()
    else:
        ctx.fill()


# ---------------------------------------------------------------- set base
class Set:
    """Base class: parallax layers + periodic decor around the floor line."""

    name = "base"
    PALETTE = {}
    PERIOD = 1400.0       # decor repeats every PERIOD world units (camera can pan anywhere)
    WALL_PAR = 0.7        # parallax of the back wall layer
    MID_PAR = 0.88        # parallax of the furniture layer
    FLOOR_DEPTH = 2000.0

    def __init__(self, **over):
        pal = dict(self.PALETTE)
        opts = {}
        for k, v in over.items():
            if k in pal:
                pal[k] = v
            else:
                opts[k] = v
        self.pal = {k: hex2rgb(v) for k, v in pal.items()}
        self.opts = opts
        self.seed = opts.get("seed", 7)
        rng = random.Random(self.seed)
        self.motes = [(rng.uniform(-1, 1), rng.uniform(0, 1), rng.uniform(0.5, 1.4), rng.uniform(0, 6.28))
                      for _ in range(int(opts.get("motes", 40)))]
        self.night = bool(opts.get("night", False))
        self.dollies = []
        lights = opts.get("lights", True)
        self.lights = [toonfx.make_light(d) for d in self.DEFAULT_LIGHTS] if lights is not False else []
        if isinstance(lights, list):
            self.lights += [toonfx.make_light(d) for d in lights]

    # -- foreground (#60) + lights (#73): drawn over the characters by toonengine.draw_frame
    FG_PAR = 1.3            # foreground pans faster than the floor (it is nearer the lens)
    FG_PERIOD = 1.8         # layout repeats every FG_PERIOD frame widths
    FOREGROUND = ()         # ((x offset in frame widths from centre, kind), ...) -> self.fg_<kind>(ctx, sx, H, u, now)
    DEFAULT_LIGHTS = ()     # toonfx.make_light specs: x/y in the layer `par`, `period` = decor tile

    def add_light(self, light):
        self.lights.append(light if not isinstance(light, dict) else toonfx.make_light(light))
        return self.lights[-1]

    def draw_foreground(self, ctx, W, H, cam, gy, now):
        self._now = now
        if self.FOREGROUND and self.opts.get("foreground", True):
            self._draw_fg(ctx, W, H, cam, gy, now)
        if self.lights or self.night:
            toonfx.render_lights(ctx, W, H, self._place_lights(W, H, cam, gy), self.night, now=now)

    def _draw_fg(self, ctx, W, H, cam, gy, now):
        """Foreground pieces anchored to the bottom edge of the frame, laid out in screen
        space (offsets are fractions of the frame width, repeating every FG_PERIOD widths)
        so they read the same at any zoom; they slide FG_PAR x faster than the floor when the
        camera pans, and stay in the lowest ~13% of the frame (below subtitles), below every face."""
        u = 0.7 * H / 1920.0 * max(0.6, min(1.4, cam.zoom)) ** 0.15   # tallest piece ~0.13 H: under subtitles
        P = self.FG_PERIOD * W
        c = cam.x * cam.zoom * self.FG_PAR
        k0, k1 = int(math.floor((c - W) / P)) - 1, int(math.ceil((c + W) / P)) + 1
        for k in range(k0, k1 + 1):
            for off, kind in self.FOREGROUND:
                sx = W / 2 + off * W + k * P - c
                if -700 * u < sx < W + 700 * u:
                    ctx.save()
                    getattr(self, "fg_" + kind)(ctx, sx, H, u, now)
                    ctx.restore()

    def _place_lights(self, W, H, cam, gy):
        oy = gy + cam.y * cam.zoom
        out = []
        for lt in self.lights:
            s = self._scale(cam, lt.par)
            c = cam.x * lt.par
            xs = [lt.x]
            if lt.period:
                half = W / 2 / s + lt.radius * 2
                k0 = int(math.floor((c - half - lt.x) / lt.period))
                k1 = int(math.ceil((c + half - lt.x) / lt.period))
                xs = [lt.x + k * lt.period for k in range(k0, k1 + 1)]
            for X in xs:
                sx = W / 2 + s * (X - c)
                if -lt.radius * s * 2 < sx < W + lt.radius * s * 2:
                    out.append((lt, sx, oy - s * lt.y, s, oy))
        return out

    # -- layer helpers
    def _layer(self, ctx, W, gy, cam, par):
        """Parallax in x only; every layer shares the floor line on screen so
        furniture stays grounded when the camera lifts (vertical framing)."""
        ctx.save()
        ctx.translate(W / 2, gy + cam.y * cam.zoom)
        s = self._scale(cam, par)
        ctx.scale(s, s)
        ctx.translate(-cam.x * par, 0)
        return s

    def _span(self, W, cam, par, pad=600.0):
        s = self._scale(cam, par)
        c = cam.x * par
        return c - W / 2 / s - pad, c + W / 2 / s + pad

    def _tiles(self, W, cam, par, period=None):
        period = period or self.PERIOD
        a, b = self._span(W, cam, par)
        k0, k1 = int(math.floor(a / period)) - 1, int(math.ceil(b / period)) + 1
        return [k * period for k in range(k0, k1 + 1)]

    def _top(self, H, gy, cam, par):
        """World y (negative) of the top of the frame in this layer, with margin."""
        s = self._scale(cam, par)
        return -(gy + cam.y * cam.zoom) / s - 200

    # -- hooks
    def background(self, ctx, W, H, cam, gy, now):
        ctx.set_source_rgb(*self.pal.get("wall", (0.9, 0.9, 0.9)))
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        pass

    def mid(self, ctx, W, H, cam, gy, now, x0):
        pass

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*self.pal.get("floor", (0.6, 0.5, 0.4)))
        ctx.fill()
        line(ctx, [(a, 0), (b, 0)], shade(self.pal.get("floor", (0.6, 0.5, 0.4)), 0.7), lw=6)

    def light(self, ctx, W, H, cam, gy, now):
        pass

    # -- render passes: the static parts of wall()/mid() are cached per camera framing,
    # animated bits (steam, swinging pans, curtains...) are drawn live every frame.
    # Inside wall()/mid(): wrap static drawing in `if self._st():`, animated in `if self._an():`.
    _pass = None              # None = draw everything, "static" / "live" = one half only
    CACHE_LAYERS = ("wall", "mid")   # layers whose static half may be cached
    LIVE_LAYERS = ()          # layers that have animated content (live pass needed)

    def _st(self):
        return self._pass != "live"

    def _an(self):
        return self._pass != "static"

    def __getstate__(self):
        d = dict(self.__dict__)
        for k in list(d):
            if k.startswith("_c"):   # lazily built cairo surfaces don't pickle
                d[k] = None
        return d

    def _scale(self, cam, par):
        """Layer scale; a dolly-zoom (vertigo) beat counter-scales the back layers."""
        s = cam.zoom ** par
        m = self._dolly_mul(getattr(self, "_now", 0.0))
        if m != 1.0 and par < 1.0:
            s *= m ** ((1.0 - par) / 0.3)
        return s

    def _dolly_mul(self, now):
        m = 1.0
        for (t0, d, k) in getattr(self, "dollies", ()):
            if now <= t0:
                continue
            u = min(1.0, (now - t0) / max(1e-3, d))
            e = u * u * (3 - 2 * u)
            m *= 1.0 / (1.0 + (k - 1.0) * e)
        return m

    def _tiles_rng(self, a, b, period=None):
        period = period or self.PERIOD
        k0, k1 = int(math.floor(a / period)) - 1, int(math.ceil(b / period)) + 1
        return [k * period for k in range(k0, k1 + 1)]

    def _draw_layer(self, name, ctx, W, H, cam, gy, now):
        par = self.WALL_PAR if name == "wall" else self.MID_PAR
        fn = getattr(self, name)
        args = (lambda x0: (ctx, W, H, cam, gy, now, x0, self._top(H, gy, cam, par))) if name == "wall" \
            else (lambda x0: (ctx, W, H, cam, gy, now, x0))
        strip = None
        if name in self.CACHE_LAYERS and self.opts.get("cache", True):
            strip = self._strip(name, fn, args, ctx, W, H, cam, gy, par)
        if strip is None:
            self._layer(ctx, W, gy, cam, par)
            for x0 in self._tiles(W, cam, par):
                fn(*args(x0))
            ctx.restore()
            return
        surf, dx = strip
        ctx.save()
        ctx.set_source_surface(surf, dx, 0)
        if abs(dx - round(dx)) > 1e-6:
            ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
        ctx.paint()
        ctx.restore()
        if name in self.LIVE_LAYERS:
            self._pass = "live"
            try:
                self._layer(ctx, W, gy, cam, par)
                for x0 in self._tiles(W, cam, par):
                    fn(*args(x0))
                ctx.restore()
            finally:
                self._pass = None

    def _strip(self, name, fn, args, ctx, W, H, cam, gy, par):
        """Cached static half of a parallax layer: a strip one PERIOD + one screen wide,
        rendered once per (size, zoom, vertical framing, period tile) and blitted with the
        horizontal offset. Built only when the same framing repeats on consecutive frames
        (moving zooms are drawn directly), so a still shot costs one render."""
        s = self._scale(cam, par)
        c = cam.x * par
        oy = gy + cam.y * cam.zoom
        base = math.floor((c - W / 2 / s) / self.PERIOD) * self.PERIOD
        key = (W, H, round(s, 5), round(oy, 2), base)
        X0 = W / 2 + s * (base - c)          # screen x of world x = base in this layer
        cache = self.__dict__.get("_cache") or {}
        self._cache = cache
        hit = cache.get(name)
        M = 48
        if hit is not None and hit[0] == key:
            _, surf, phase = hit
            return surf, X0 - M - phase
        last = cache.get(name + "_last")
        cache[name + "_last"] = key
        if last != key:
            return None
        phase = X0 - math.floor(X0)
        SW = int(math.ceil((self.PERIOD + W / s) * s)) + 2 * M + 2
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, int(H))
        sc = cairo.Context(surf)
        sc.translate(M + phase, oy)
        sc.scale(s, s)
        sc.translate(-base, 0)
        wa, wb = base - (M + 8) / s - 600, base + (SW + 8) / s + 600
        self._pass = "static" if name in self.LIVE_LAYERS else None
        try:
            for x0 in self._tiles_rng(wa, wb):
                a = list(args(x0))
                a[0] = sc
                fn(*a)
        finally:
            self._pass = None
        surf.flush()
        cache[name] = (key, surf, phase)
        return surf, X0 - M - phase

    # -- main entry (same signature as toonengine.World.draw)
    def draw(self, ctx, W, H, cam, gy, now):
        self._now = now
        self.background(ctx, W, H, cam, gy, now)
        self._draw_layer("wall", ctx, W, H, cam, gy, now)
        self._draw_layer("mid", ctx, W, H, cam, gy, now)
        self._layer(ctx, W, gy, cam, 1.0)
        a, b = self._span(W, cam, 1.0, pad=400)
        self.floor(ctx, W, H, cam, gy, now, a, b)
        self._floor_depth(ctx, H, gy, cam, a, b)
        ctx.restore()
        if not getattr(self, "night", 0):
            self.light(ctx, W, H, cam, gy, now)
        else:
            self.night_light(ctx, W, H, cam, gy, now)

    def night_light(self, ctx, W, H, cam, gy, now):
        pass

    def _floor_depth(self, ctx, H, gy, cam, a, b):
        """Soft contact shadow at the wall line + floor darkening toward the viewer
        (gives the flat floor band depth in tall 9:16 frames)."""
        if not self.opts.get("depth", True):
            return
        bottom = (H - (gy + cam.y * cam.zoom)) / cam.zoom + 50
        g = cairo.LinearGradient(0, 0, 0, 70)
        g.add_color_stop_rgba(0, *INK, 0.22)
        g.add_color_stop_rgba(1, *INK, 0.0)
        ctx.rectangle(a, 0, b - a, 70)
        ctx.set_source(g)
        ctx.fill()
        if bottom > 80:
            g = cairo.LinearGradient(0, 60, 0, bottom)
            g.add_color_stop_rgba(0, *INK, 0.0)
            g.add_color_stop_rgba(1, *INK, 0.2)
            ctx.rectangle(a, 60, b - a, bottom)
            ctx.set_source(g)
            ctx.fill()

    # -- shared effects
    def god_rays(self, ctx, W, gy, cam, now, x, y, w, h, alpha=0.16, par=None):
        """Soft light shaft from a window (world coords in the wall layer) to the floor."""
        par = self.WALL_PAR if par is None else par
        self._layer(ctx, W, gy, cam, par)
        flick = 0.85 + 0.15 * math.sin(now * 0.7)
        g = cairo.LinearGradient(x, y, x + 260, 0)
        g.add_color_stop_rgba(0, 1, 0.96, 0.78, alpha * flick)
        g.add_color_stop_rgba(1, 1, 0.96, 0.78, 0.0)
        ctx.move_to(x, y)
        ctx.line_to(x + w, y)
        ctx.line_to(x + w + 330, 40)
        ctx.line_to(x + 230, 40)
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()
        ctx.restore()

    def dust(self, ctx, W, H, gy, cam, now, col=(1, 0.95, 0.8), alpha=0.5):
        """Floating dust motes in screen space (cheap, gentle)."""
        for (u, v, s, ph) in self.motes:
            x = (u * 0.5 + 0.5) * W + 18 * math.sin(now * 0.4 * s + ph) - (cam.x * 0.2 % W)
            x %= W
            y = (v - now * 0.012 * s) % 1.0 * gy
            r = 1.2 + 1.6 * s
            ctx.arc(x, y, r, 0, 2 * math.pi)
            ctx.set_source_rgba(*col, alpha * (0.5 + 0.5 * math.sin(now * 1.3 + ph)))
            ctx.fill()


# ---------------------------------------------------------------- barn
class Barn(Set):
    name = "barn"
    CACHE_LAYERS = ()     # planks + one sparse mid layer draw faster than a full-frame blit (profiled)
    PALETTE = dict(wall="#a8683d", plank_dark="#7d4a2a", beam="#6b3e22", hay="#e8c15a", hay_dark="#c99a35",
                   floor="#c9a56b", straw="#e9cf7d", window="#ffe7a6", stall="#8f5631")
    PERIOD = 1300.0

    def background(self, ctx, W, H, cam, gy, now):
        ctx.set_source_rgb(*self.pal["wall"])
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        # vertical planks
        for i in range(0, int(self.PERIOD), 62):
            x = x0 + i
            ctx.rectangle(x, top, 62, -top)
            ctx.set_source_rgb(*shade(P["wall"], 0.94 + 0.08 * ((i // 62 * 37) % 5) / 5))
            ctx.fill()
            line(ctx, [(x, top), (x, 0)], P["plank_dark"], lw=3)
            for ky in (-130, -330, -560):  # nail heads
                circle(ctx, x + 10, ky, 2.6, shade(P["plank_dark"], 0.7), outline=False)
        # big beams
        for by in (-470, -760):
            box(ctx, x0 - 2, by, self.PERIOD + 4, 34, P["beam"], lw=3)
        for bx in (120, 760):
            box(ctx, x0 + bx, top, 40, -top, P["beam"], lw=3)
        # window with frame + cross
        wx, wy = x0 + 380, -640
        box(ctx, wx - 10, wy - 10, 220, 170, P["beam"], r=6)
        box(ctx, wx, wy, 200, 150, P["window"], r=4, shade_side=False)
        g = cairo.RadialGradient(wx + 100, wy + 75, 10, wx + 100, wy + 75, 180)
        g.add_color_stop_rgba(0, 1, 1, 0.92, 0.9)
        g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0.0)
        ctx.rectangle(wx, wy, 200, 150)
        ctx.set_source(g)
        ctx.fill()
        line(ctx, [(wx + 100, wy), (wx + 100, wy + 150)], P["beam"], lw=8)
        line(ctx, [(wx, wy + 75), (wx + 200, wy + 75)], P["beam"], lw=8)
        # hanging lantern + rope
        lx = x0 + 1000
        line(ctx, [(lx, -760), (lx, -560)], INK, lw=2.5)
        box(ctx, lx - 22, -560, 44, 56, (0.98, 0.82, 0.4), r=8)
        circle(ctx, lx, -532, 14, (1, 0.95, 0.7), outline=False, alpha=0.9)
        # pitchfork + rope coil on wall
        line(ctx, [(x0 + 260, -330), (x0 + 300, -60)], (0.55, 0.36, 0.2), lw=7)
        for d in (-12, 0, 12):
            line(ctx, [(x0 + 255 + d, -330), (x0 + 250 + d * 1.3, -390)], (0.6, 0.6, 0.65), lw=4)
        for r in (34, 26, 18):
            ctx.new_path()
            ctx.arc(x0 + 640, -300, r, 0, 2 * math.pi)
            ctx.set_source_rgb(0.78, 0.62, 0.38)
            ctx.set_line_width(7)
            ctx.stroke()

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        # stall gate with X brace
        sx = x0 + 40
        box(ctx, sx, -150, 260, 150, P["stall"], r=4)
        line(ctx, [(sx + 8, -142), (sx + 252, -8)], shade(P["stall"], 0.75), lw=10)
        line(ctx, [(sx + 252, -142), (sx + 8, -8)], shade(P["stall"], 0.75), lw=10)
        box(ctx, sx - 14, -170, 22, 170, shade(P["stall"], 0.85), r=3)
        box(ctx, sx + 252, -170, 22, 170, shade(P["stall"], 0.85), r=3)
        # hay bales stack
        for (hx, hy, w, h) in ((x0 + 720, -88, 170, 88), (x0 + 900, -88, 170, 88), (x0 + 805, -170, 170, 82)):
            box(ctx, hx, hy, w, h, P["hay"], r=12)
            for k in range(6):
                yy = hy + 12 + k * (h - 20) / 5
                line(ctx, [(hx + 14, yy), (hx + w - 14, yy + 3)], P["hay_dark"], lw=2.2, alpha=0.8)
            line(ctx, [(hx + w * 0.3, hy + 2), (hx + w * 0.3, hy + h - 2)], (0.55, 0.35, 0.2), lw=4)
            line(ctx, [(hx + w * 0.7, hy + 2), (hx + w * 0.7, hy + h - 2)], (0.55, 0.35, 0.2), lw=4)
        # bucket
        poly(ctx, [(x0 + 1150, -62), (x0 + 1210, -62), (x0 + 1200, 0), (x0 + 1160, 0)], (0.62, 0.66, 0.72))
        line(ctx, [(x0 + 1150, -62), (x0 + 1180, -95), (x0 + 1210, -62)], INK, lw=2.5)

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        rng = random.Random(3)
        x = math.floor(a / 40) * 40
        while x < b:
            r = random.Random(int(x))
            for _ in range(3):
                px, py = x + r.uniform(0, 40), r.uniform(6, 260)
                ang = r.uniform(-0.5, 0.5)
                line(ctx, [(px, py), (px + 22 * math.cos(ang), py + 22 * math.sin(ang))], P["straw"], lw=3,
                     alpha=0.9)
            x += 40
        line(ctx, [(a, 0), (b, 0)], shade(P["floor"], 0.7), lw=6)

    def light(self, ctx, W, H, cam, gy, now):
        for x0 in self._tiles(W, cam, self.WALL_PAR):
            self.god_rays(ctx, W, gy, cam, now, x0 + 380, -640, 200, 150, alpha=0.22)
        self.dust(ctx, W, H, gy, cam, now, alpha=0.45)


# ---------------------------------------------------------------- farmyard
class Farmyard(Set):
    LIVE_LAYERS = ("mid",)
    name = "farmyard"
    PALETTE = dict(sky_top="#78c5f5", sky_bottom="#dff3ff", barn="#c8433a", trim="#fff4e6", roof="#5b4a4a",
                   grass="#79c45a", grass_dark="#5ea64a", fence="#e9d3a5", hay="#e8c15a", hay_dark="#c99a35",
                   tree="#4fa356", trunk="#7a5132", floor="#8fd16b")
    PERIOD = 1600.0
    WALL_PAR = 0.55

    def background(self, ctx, W, H, cam, gy, now):
        g = cairo.LinearGradient(0, 0, 0, gy)
        g.add_color_stop_rgb(0, *self.pal["sky_top"])
        g.add_color_stop_rgb(1, *self.pal["sky_bottom"])
        ctx.set_source(g)
        ctx.paint()
        rng = random.Random(11)
        for i in range(6):  # clouds drifting
            cx = (rng.uniform(0, 1) * W + now * 8 * (1 + i % 3) - cam.x * 0.1) % (W + 400) - 200
            cy = rng.uniform(0.06, 0.3) * gy
            s = rng.uniform(0.7, 1.3) * W / 1080
            for dx, dy, r in ((0, 0, 40), (42, 8, 32), (-40, 10, 30), (16, -20, 32)):
                circle(ctx, cx + dx * s, cy + dy * s, r * s, (1, 1, 1), outline=False, alpha=0.92)

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        # distant hills
        poly(ctx, [(x0 - 50, -120), (x0 + 400, -320), (x0 + 900, -200), (x0 + 1300, -360), (x0 + 1650, -140),
                   (x0 + 1650, 0), (x0 - 50, 0)], P["grass_dark"], outline=False)
        # big barn facade
        bx, bw, bh = x0 + 260, 620, 520
        poly(ctx, [(bx - 30, -bh), (bx + bw / 2, -bh - 230), (bx + bw + 30, -bh)], P["roof"], lw=4)
        box(ctx, bx, -bh, bw, bh, P["barn"], r=4, lw=4)
        for i in range(1, 8):  # vertical boards
            line(ctx, [(bx + i * bw / 8, -bh + 6), (bx + i * bw / 8, -6)], shade(P["barn"], 0.8), lw=3)
        # hay loft door
        box(ctx, bx + bw / 2 - 70, -bh - 120, 140, 120, P["barn"], lw=4)
        line(ctx, [(bx + bw / 2 - 64, -bh - 114), (bx + bw / 2 + 64, -bh - 6)], P["trim"], lw=8)
        line(ctx, [(bx + bw / 2 + 64, -bh - 114), (bx + bw / 2 - 64, -bh - 6)], P["trim"], lw=8)
        # main doors with white X
        dx, dw, dh = bx + bw / 2 - 160, 320, 300
        box(ctx, dx, -dh, dw, dh, shade(P["barn"], 0.9), lw=4)
        for k in (0, 1):
            xx = dx + k * dw / 2
            box(ctx, xx + 6, -dh + 6, dw / 2 - 12, dh - 12, shade(P["barn"], 0.92), lw=0.1, outline=False)
            line(ctx, [(xx + 12, -dh + 12), (xx + dw / 2 - 12, -12)], P["trim"], lw=10)
            line(ctx, [(xx + dw / 2 - 12, -dh + 12), (xx + 12, -12)], P["trim"], lw=10)
        _rrect(ctx, dx, -dh, dw, dh, 0)
        ctx.set_source_rgb(*P["trim"])
        ctx.set_line_width(12)
        ctx.stroke()
        # silo
        sx = x0 + 1050
        box(ctx, sx, -640, 150, 640, (0.82, 0.84, 0.88), r=8, lw=4)
        ctx.new_path()
        ctx.arc(sx + 75, -640, 75, math.pi, 2 * math.pi)
        ctx.set_source_rgb(0.65, 0.68, 0.74)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        for yy in range(-600, 0, 80):
            line(ctx, [(sx + 4, yy), (sx + 146, yy)], (0.66, 0.68, 0.74), lw=3)

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        # tall trees with sway
        for tx, s in ((x0 + 80, 1.15), (x0 + 1350, 1.0)):
            sway = 6 * math.sin(now * 1.2 + tx * 0.01)
            if self._st():
                box(ctx, tx - 16 * s, -260 * s, 32 * s, 260 * s, P["trunk"], r=6)
            if self._an():
                for dx, dy, r in ((0, -330, 120), (-80, -270, 90), (85, -265, 95), (0, -420, 90)):
                    circle(ctx, tx + dx * s + sway, dy * s, r * s, P["tree"], lw=4)
                circle(ctx, tx - 30 * s + sway, -360 * s, 40 * s, shade(P["tree"], 1.15), outline=False, alpha=0.5)
        if not self._st():
            return
        # fence
        for i in range(0, int(self.PERIOD), 90):
            box(ctx, x0 + i, -120, 18, 120, P["fence"], r=4, lw=2.5)
        for yy in (-100, -55):
            box(ctx, x0, yy, self.PERIOD, 14, P["fence"], lw=2.5, shade_side=False)
        # hay bales
        for hx in (x0 + 560, x0 + 700):
            box(ctx, hx, -80, 130, 80, P["hay"], r=12)
            for k in range(4):
                yy = -70 + k * 18
                line(ctx, [(hx + 12, yy), (hx + 118, yy + 3)], P["hay_dark"], lw=2.2)

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        x = math.floor(a / 50) * 50
        while x < b:
            r = random.Random(int(x) * 7)
            for _ in range(2):
                px, py = x + r.uniform(0, 50), r.uniform(10, 300)
                line(ctx, [(px, py), (px - 4, py - 12)], P["grass_dark"], lw=3)
                line(ctx, [(px + 6, py), (px + 8, py - 10)], P["grass_dark"], lw=3)
            x += 50
        line(ctx, [(a, 0), (b, 0)], P["grass_dark"], lw=6)


# ---------------------------------------------------------------- kitchen
class Kitchen(Set):
    LIVE_LAYERS = ("wall", "mid")
    name = "kitchen"
    PALETTE = dict(wall="#f3e6cf", tile="#ffffff", grout="#d9d2c4", cabinet="#7fb7a4", counter="#e9e2d6",
                   wood="#c98b5a", fridge="#e8edf2", steel="#b9c2cc", floor="#e6d2b0", floor2="#d4bc95",
                   window="#bfe6ff", curtain="#ff8c6b", pan="#4a4f5a")
    PERIOD = 1500.0

    def background(self, ctx, W, H, cam, gy, now):
        ctx.set_source_rgb(*self.pal["wall"])
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        wx, wy = x0 + 560, -640
        if self._st():
            # subway tiles band behind the counter
            ctx.rectangle(x0, -330, self.PERIOD, 330)
            ctx.set_source_rgb(*P["tile"])
            ctx.fill()
            for r_ in range(0, 330, 30):
                y = -330 + r_
                line(ctx, [(x0, y), (x0 + self.PERIOD, y)], P["grout"], lw=2)
                off = 30 if (r_ // 30) % 2 else 0
                for xx in range(off, int(self.PERIOD), 60):
                    line(ctx, [(x0 + xx, y), (x0 + xx, y + 30)], P["grout"], lw=2)
            line(ctx, [(x0, -330), (x0 + self.PERIOD, -330)], INK, lw=3)
            # upper cabinets
            for cx in (x0 + 60, x0 + 260, x0 + 1060, x0 + 1260):
                box(ctx, cx, -620, 190, 220, P["cabinet"], r=6)
                box(ctx, cx + 14, -606, 162, 192, shade(P["cabinet"], 1.06), r=4, shade_side=False, lw=2)
                circle(ctx, cx + 160, -500, 6, (0.95, 0.85, 0.5), lw=2)
            # window with curtains and a plant
            box(ctx, wx - 14, wy - 14, 368, 288, (1, 1, 1), r=8)
            box(ctx, wx, wy, 340, 260, P["window"], r=4, shade_side=False)
            g = cairo.LinearGradient(wx, wy, wx, wy + 260)
            g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
            g.add_color_stop_rgba(1, 1, 1, 1, 0.55)
            ctx.rectangle(wx, wy, 340, 260)
            ctx.set_source(g)
            ctx.fill()
            line(ctx, [(wx + 170, wy), (wx + 170, wy + 260)], (1, 1, 1), lw=10)
            line(ctx, [(wx, wy + 130), (wx + 340, wy + 130)], (1, 1, 1), lw=10)
        if self._an():
            for side in (0, 1):
                cx = wx - 50 if side == 0 else wx + 340 - 40
                sw = 4 * math.sin(now * 0.8 + side)
                poly(ctx, [(cx, wy - 30), (cx + 90, wy - 30), (cx + 70 + sw, wy + 250), (cx + 10 + sw, wy + 250)],
                     P["curtain"])
            line(ctx, [(wx - 70, wy - 30), (wx + 410, wy - 30)], P["wood"], lw=10)
        # hanging rail with pans
        rx = x0 + 1050
        if self._st():
            line(ctx, [(rx, -380), (rx + 380, -380)], P["steel"], lw=8)
            circle(ctx, x0 + 470, -560, 42, (1, 1, 1), lw=3.5)  # clock face
        if not self._an():
            return
        for i, (r, ln) in enumerate(((44, 70), (36, 55), (30, 50))):
            px = rx + 60 + i * 120
            sw = 0.05 * math.sin(now * 1.5 + i)
            ctx.save()
            ctx.translate(px, -380)
            ctx.rotate(sw)
            line(ctx, [(0, 0), (0, ln)], P["pan"], lw=6)
            circle(ctx, 0, ln + r, r, P["pan"], lw=3)
            circle(ctx, -r * 0.25, ln + r * 0.8, r * 0.35, shade(P["pan"], 1.4), outline=False, alpha=0.5)
            ctx.restore()
        # clock hands
        ang = now * 0.3
        line(ctx, [(x0 + 470, -560), (x0 + 470 + 26 * math.sin(ang), -560 - 26 * math.cos(ang))], INK, lw=3)
        line(ctx, [(x0 + 470, -560), (x0 + 470 + 18, -560 + 4)], INK, lw=4)

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        sx = x0 + 560
        if self._st():
            self._kitchen_counter(ctx, x0, sx)
        if self._an():
            for k in range(3):
                t = (now * 0.6 + k / 3) % 1.0
                x = sx + 90 + k * 25 + 10 * math.sin(now * 2 + k)
                circle(ctx, x, -270 - t * 120, 12 + t * 14, (1, 1, 1), outline=False, alpha=0.5 * (1 - t))
        if self._st():
            self._kitchen_rest(ctx, x0)

    def _kitchen_counter(self, ctx, x0, sx):
        P = self.pal
        # counter run with lower cabinets
        box(ctx, x0, -150, 1500, 150, P["cabinet"], lw=3)
        for i in range(0, 1500, 150):
            box(ctx, x0 + i + 8, -138, 134, 128, shade(P["cabinet"], 1.05), r=4, shade_side=False, lw=2)
            line(ctx, [(x0 + i + 60, -110), (x0 + i + 90, -110)], (0.95, 0.85, 0.5), lw=5)
        box(ctx, x0 - 6, -172, 1512, 24, P["counter"], r=4)
        # stove with pot (+ live steam)
        box(ctx, sx, -160, 230, 160, P["steel"], r=6)
        box(ctx, sx + 30, -120, 170, 90, shade(P["steel"], 0.7), r=8)
        box(ctx, sx + 45, -108, 140, 66, (0.25, 0.22, 0.28), r=6, shade_side=False, lw=2)
        for k in range(3):
            circle(ctx, sx + 40 + k * 70, -145, 8, (0.95, 0.4, 0.3), lw=2)
        box(ctx, sx + 60, -250, 120, 78, (0.86, 0.32, 0.32), r=10)
        line(ctx, [(sx + 50, -248), (sx + 190, -248)], INK, lw=6)

    def _kitchen_rest(self, ctx, x0):
        P = self.pal
        # fridge (tall)
        fx = x0 + 1260
        box(ctx, fx, -470, 200, 470, P["fridge"], r=16, lw=3.5)
        line(ctx, [(fx + 4, -300), (fx + 196, -300)], INK, lw=3)
        box(ctx, fx + 168, -440, 12, 110, P["steel"], r=6, lw=2)
        box(ctx, fx + 168, -270, 12, 140, P["steel"], r=6, lw=2)
        for k, c in enumerate(((1, 0.6, 0.3), (0.5, 0.8, 0.5), (0.9, 0.4, 0.6))):
            circle(ctx, fx + 40 + k * 40, -420 + (k % 2) * 30, 10, c, lw=2)
        # cutting board + fruit bowl on counter
        box(ctx, x0 + 150, -190, 140, 18, P["wood"], r=6)
        ctx.new_path()
        ctx.arc(x0 + 400, -172, 60, 0, math.pi)
        ctx.set_source_rgb(0.98, 0.95, 0.9)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
        for k, c in enumerate(((1, 0.55, 0.15), (0.85, 0.2, 0.25), (0.98, 0.85, 0.3))):
            circle(ctx, x0 + 365 + k * 35, -192 - (k == 1) * 14, 22, c, lw=2.5)

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        size = 90
        x = math.floor(a / size) * size
        while x < b:
            for row in range(0, 6):
                if (int(x / size) + row) % 2 == 0:
                    y = row * size * 0.6
                    poly(ctx, [(x, y), (x + size, y), (x + size * 1.06, y + size * 0.6), (x + size * 0.06, y + size * 0.6)],
                         P["floor2"], outline=False)
            x += size
        line(ctx, [(a, 0), (b, 0)], shade(P["floor"], 0.7), lw=6)

    def light(self, ctx, W, H, cam, gy, now):
        for x0 in self._tiles(W, cam, self.WALL_PAR):
            self.god_rays(ctx, W, gy, cam, now, x0 + 560, -640, 340, 260, alpha=0.12)


# ---------------------------------------------------------------- living room
class LivingRoom(Set):
    LIVE_LAYERS = ("wall", "mid")
    name = "living_room"
    PALETTE = dict(wall="#f2d9c2", stripe="#ead0b6", wainscot="#c98f6a", sofa="#6e9ccf", wood="#9a6440",
                   rug="#d76a5d", rug2="#f1c27d", floor="#b9835c", floor2="#a67350", lamp="#ffd27a",
                   window="#a9dcff", curtain="#7c5aa6", frame="#8a5a3a", plant="#4f9a55")
    PERIOD = 1400.0

    def background(self, ctx, W, H, cam, gy, now):
        ctx.set_source_rgb(*self.pal["wall"])
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        wx, wy = x0 + 480, -640
        if self._st():
            for i in range(0, int(self.PERIOD), 70):  # wallpaper stripes + small flowers
                ctx.rectangle(x0 + i, top, 35, -top)
                ctx.set_source_rgb(*P["stripe"])
                ctx.fill()
                for yy in range(int(top) // 120 * 120, -200, 120):
                    circle(ctx, x0 + i + 52, yy + (i // 70 % 2) * 60, 5, shade(P["wall"], 0.88), outline=False)
            # wainscot
            box(ctx, x0, -200, self.PERIOD, 200, P["wainscot"], lw=3)
            for i in range(0, int(self.PERIOD), 175):
                box(ctx, x0 + i + 14, -184, 147, 168, shade(P["wainscot"], 1.06), r=4, shade_side=False, lw=2)
            box(ctx, x0, -212, self.PERIOD, 16, shade(P["wainscot"], 0.85), lw=2.5)
            # window with curtains
            box(ctx, wx - 12, wy - 12, 344, 304, (1, 0.98, 0.94), r=6)
            box(ctx, wx, wy, 320, 280, P["window"], r=4, shade_side=False)
            poly(ctx, [(wx, wy + 280), (wx + 60, wy + 200), (wx + 140, wy + 230), (wx + 220, wy + 170),
                       (wx + 320, wy + 220), (wx + 320, wy + 280)], (0.55, 0.78, 0.55), outline=False)
            line(ctx, [(wx + 160, wy), (wx + 160, wy + 280)], (1, 0.98, 0.94), lw=10)
            line(ctx, [(wx, wy + 140), (wx + 320, wy + 140)], (1, 0.98, 0.94), lw=10)
        if self._an():
            for side in (0, 1):
                cx = wx - 70 if side == 0 else wx + 320 - 40
                sw = 3 * math.sin(now * 0.7 + side)
                poly(ctx, [(cx, wy - 40), (cx + 110, wy - 40), (cx + 90 + sw, wy + 310), (cx + 10 + sw, wy + 310)],
                     P["curtain"])
            line(ctx, [(wx - 90, wy - 40), (wx + 410, wy - 40)], P["wood"], lw=10)
        if not self._st():
            return
        # picture frames
        for (fx, fy, fw, fh, c) in ((x0 + 120, -560, 180, 140, (0.98, 0.8, 0.5)),
                                    (x0 + 950, -600, 130, 170, (0.6, 0.8, 0.95)),
                                    (x0 + 1120, -520, 150, 110, (0.95, 0.7, 0.75))):
            box(ctx, fx, fy, fw, fh, P["frame"], r=4)
            box(ctx, fx + 12, fy + 12, fw - 24, fh - 24, c, shade_side=False, lw=2)
            poly(ctx, [(fx + 20, fy + fh - 20), (fx + fw * 0.45, fy + fh * 0.45), (fx + fw - 20, fy + fh - 20)],
                 shade(c, 0.75), outline=False)
            circle(ctx, fx + fw * 0.72, fy + fh * 0.32, min(fw, fh) * 0.1, (1, 1, 0.85), outline=False)

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        tx = x0 + 1050
        if self._st():
            # sofa
            sx = x0 + 120
            box(ctx, sx, -230, 420, 130, P["sofa"], r=30)
            box(ctx, sx - 30, -170, 480, 120, shade(P["sofa"], 0.95), r=30)
            for k in range(3):
                box(ctx, sx + 20 + k * 130, -215, 120, 70, shade(P["sofa"], 1.08), r=18, lw=2.5)
            box(ctx, sx - 50, -190, 70, 140, shade(P["sofa"], 0.9), r=24)
            box(ctx, sx + 400, -190, 70, 140, shade(P["sofa"], 0.9), r=24)
            for lx in (sx - 20, sx + 430):
                box(ctx, lx, -52, 16, 52, P["wood"], r=4, lw=2)
            circle(ctx, sx + 360, -235, 26, (0.98, 0.85, 0.4), lw=2.5)  # cushion
            # floor lamp
            lx = x0 + 760
            line(ctx, [(lx, 0), (lx, -380)], (0.3, 0.3, 0.32), lw=7)
            poly(ctx, [(lx - 70, -360), (lx + 70, -360), (lx + 45, -460), (lx - 45, -460)], P["lamp"])
            g = cairo.RadialGradient(lx, -330, 10, lx, -330, 260)
            g.add_color_stop_rgba(0, 1, 0.9, 0.6, 0.35)
            g.add_color_stop_rgba(1, 1, 0.9, 0.6, 0.0)
            ctx.arc(lx, -330, 260, 0, 2 * math.pi)
            ctx.set_source(g)
            ctx.fill()
            box(ctx, lx - 40, -10, 80, 10, (0.3, 0.3, 0.32), r=4, lw=2)
            # side table + plant
            tx = x0 + 1050
            box(ctx, tx, -120, 160, 18, P["wood"], r=4)
            for k in (12, 130):
                box(ctx, tx + k, -102, 14, 102, shade(P["wood"], 0.9), r=3, lw=2)
            poly(ctx, [(tx + 50, -120), (tx + 110, -120), (tx + 100, -175), (tx + 60, -175)], (0.85, 0.5, 0.35))
        self._plant(ctx, tx, now)

    def _plant(self, ctx, tx, now):
        if not self._an():
            return
        P = self.pal
        for k in range(5):
            a = -1.2 + k * 0.6
            ctx.save()
            ctx.translate(tx + 80, -175)
            ctx.rotate(a + 0.05 * math.sin(now + k))
            poly(ctx, [(0, 0), (-14, -50), (0, -95), (14, -50)], P["plant"], lw=2.5)
            ctx.restore()

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        for y in range(0, 400, 36):  # floorboards
            line(ctx, [(a, y), (b, y)], P["floor2"], lw=3)
        x = math.floor(a / 300) * 300
        while x < b:
            for row in range(0, 12):
                xx = x + (row % 2) * 150
                line(ctx, [(xx, row * 36), (xx, row * 36 + 36)], P["floor2"], lw=3)
            x += 300
        # rug (periodic)
        x = math.floor(a / self.PERIOD) * self.PERIOD
        while x < b:
            ctx.save()
            ctx.translate(x + 700, 50)
            ctx.scale(520, 70)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(*P["rug"])
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(3)
            ctx.stroke()
            ctx.save()
            ctx.translate(x + 700, 50)
            ctx.scale(400, 48)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(*P["rug2"])
            ctx.set_line_width(6 / 48)
            ctx.stroke()
            x += self.PERIOD
        line(ctx, [(a, 0), (b, 0)], shade(P["floor"], 0.7), lw=6)

    def light(self, ctx, W, H, cam, gy, now):
        for x0 in self._tiles(W, cam, self.WALL_PAR):
            self.god_rays(ctx, W, gy, cam, now, x0 + 480, -640, 320, 280, alpha=0.12)
        self.dust(ctx, W, H, gy, cam, now, alpha=0.3)


# ---------------------------------------------------------------- classroom
class Classroom(Set):
    name = "classroom"
    PALETTE = dict(wall="#f3edd9", lower="#8fc0a9", board="#2f5d4a", chalk="#f4f4ee", wood="#b98352",
                   floor="#cfa57a", floor2="#bb915f", desk="#d9a066", poster="#ffcf5c")
    PERIOD = 1500.0

    def __init__(self, text="2 + 2 = 4", **kw):
        super().__init__(**kw)
        self.text = text

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        ctx.rectangle(x0, -220, self.PERIOD, 220)
        ctx.set_source_rgb(*P["lower"])
        ctx.fill()
        line(ctx, [(x0, -220), (x0 + self.PERIOD, -220)], INK, lw=3)
        bx, by, bw, bh = x0 + 360, -640, 760, 340
        box(ctx, bx - 18, by - 18, bw + 36, bh + 36, P["wood"], r=6)
        box(ctx, bx, by, bw, bh, P["board"], r=4, shade_side=False)
        ctx.select_font_face("Fredoka", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(80)
        ext = ctx.text_extents(self.text)
        ctx.move_to(bx + (bw - ext.x_advance) / 2, by + bh / 2 + 28)
        ctx.set_source_rgba(*P["chalk"], 0.92)
        ctx.show_text(self.text)
        line(ctx, [(bx + 40, by + bh - 40), (bx + 260, by + bh - 52)], P["chalk"], lw=4, alpha=0.6)
        box(ctx, bx + 20, by + bh + 14, 120, 14, P["wood"], r=4, lw=2)
        circle(ctx, x0 + 200, -560, 50, (1, 1, 1), lw=3.5)
        line(ctx, [(x0 + 200, -560), (x0 + 200, -595)], INK, lw=3)
        line(ctx, [(x0 + 200, -560), (x0 + 225, -560)], INK, lw=4)
        box(ctx, x0 + 1240, -560, 150, 200, P["poster"], r=6)
        for k in range(4):
            line(ctx, [(x0 + 1265, -520 + k * 40), (x0 + 1365, -520 + k * 40)], shade(P["poster"], 0.6), lw=6)

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        for dx in (x0 + 80, x0 + 560, x0 + 1040):
            box(ctx, dx, -120, 260, 22, P["desk"], r=5)
            box(ctx, dx + 16, -98, 14, 98, shade(P["desk"], 0.8), r=3, lw=2)
            box(ctx, dx + 230, -98, 14, 98, shade(P["desk"], 0.8), r=3, lw=2)
            box(ctx, dx + 60, -140, 70, 20, (0.95, 0.95, 0.98), r=3, lw=2)

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        for y in range(0, 400, 40):
            line(ctx, [(a, y), (b, y)], P["floor2"], lw=3)
        line(ctx, [(a, 0), (b, 0)], shade(P["floor"], 0.7), lw=6)


# ---------------------------------------------------------------- bedroom
class Bedroom(Set):
    name = "bedroom"
    PALETTE = dict(wall="#c9d8f2", star="#ffffff", bed="#f28b82", sheet="#fff6e6", wood="#a8744e",
                   floor="#d9b48c", floor2="#c99f74", window="#24305e", moon="#fff3b0", poster="#ffd166")
    PERIOD = 1400.0

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        rng = random.Random(int(x0) + 5)
        for _ in range(14):
            sx, sy = x0 + rng.uniform(0, self.PERIOD), rng.uniform(max(top, -900), -260)
            s = rng.uniform(5, 9)
            poly(ctx, [(sx, sy - s), (sx + s * 0.3, sy - s * 0.3), (sx + s, sy), (sx + s * 0.3, sy + s * 0.3),
                       (sx, sy + s), (sx - s * 0.3, sy + s * 0.3), (sx - s, sy), (sx - s * 0.3, sy - s * 0.3)],
                 shade(P["wall"], 1.12), outline=False)
        wx, wy = x0 + 700, -620
        box(ctx, wx - 12, wy - 12, 284, 244, (1, 1, 1), r=8)
        box(ctx, wx, wy, 260, 220, P["window"], r=4, shade_side=False)
        circle(ctx, wx + 180, wy + 70, 34, P["moon"], outline=False)
        circle(ctx, wx + 196, wy + 60, 30, P["window"], outline=False)
        line(ctx, [(wx + 130, wy), (wx + 130, wy + 220)], (1, 1, 1), lw=10)
        box(ctx, x0 + 1110, -560, 170, 220, P["poster"], r=6)
        poly(ctx, [(x0 + 1150, -380), (x0 + 1195, -500), (x0 + 1240, -380)], (0.4, 0.6, 0.95))

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        bx = x0 + 120
        box(ctx, bx, -260, 40, 260, P["wood"], r=6)
        box(ctx, bx + 40, -130, 460, 70, P["bed"], r=14)
        box(ctx, bx + 40, -160, 460, 40, P["sheet"], r=14)
        box(ctx, bx + 60, -205, 120, 52, (1, 1, 1), r=20)
        box(ctx, bx + 500, -180, 30, 180, P["wood"], r=6)
        box(ctx, bx + 40, -60, 460, 60, shade(P["wood"], 0.9), r=4, lw=2.5)
        tx = x0 + 1000
        box(ctx, tx, -150, 140, 150, P["wood"], r=6)
        box(ctx, tx + 12, -138, 116, 56, shade(P["wood"], 1.08), r=4, shade_side=False, lw=2)
        line(ctx, [(tx + 70, -150), (tx + 70, -220)], INK, lw=4)
        poly(ctx, [(tx + 30, -215), (tx + 110, -215), (tx + 92, -270), (tx + 48, -270)], (1, 0.85, 0.5))

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        for y in range(0, 400, 36):
            line(ctx, [(a, y), (b, y)], P["floor2"], lw=3)
        line(ctx, [(a, 0), (b, 0)], shade(P["floor"], 0.7), lw=6)


# ---------------------------------------------------------------- street
class Street(Set):
    name = "street"
    PALETTE = dict(sky_top="#8ccdf7", sky_bottom="#f1f9ff", road="#6d7380", sidewalk="#cfcac2", curb="#a49d93",
                   lamp="#3e4450", glow="#fff0a8")
    HOUSES = ("#f4a261", "#e76f51", "#90be6d", "#f9c74f", "#86bbd8", "#c39bd3")
    PERIOD = 1500.0
    WALL_PAR = 0.75

    def background(self, ctx, W, H, cam, gy, now):
        g = cairo.LinearGradient(0, 0, 0, gy)
        g.add_color_stop_rgb(0, *self.pal["sky_top"])
        g.add_color_stop_rgb(1, *self.pal["sky_bottom"])
        ctx.set_source(g)
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        widths = (260, 220, 300, 240, 240, 240)
        x = x0
        for i, w in enumerate(widths):
            col = hex2rgb(self.HOUSES[(i + int(x0 / self.PERIOD)) % len(self.HOUSES)])
            h = 520 + (i * 97) % 260
            box(ctx, x, -h, w, h, col, lw=3.5)
            # roof/cornice
            box(ctx, x - 8, -h - 22, w + 16, 26, shade(col, 0.75), lw=3)
            # windows
            for r in range(2, max(3, int(h / 130))):
                for c in range(2):
                    wx, wy = x + 30 + c * (w - 100), -h + 40 + (r - 2) * 120
                    if wy > -200:
                        continue
                    box(ctx, wx, wy, 70, 80, (0.85, 0.93, 1.0), r=4, shade_side=False, lw=2.5)
                    line(ctx, [(wx + 35, wy), (wx + 35, wy + 80)], (1, 1, 1), lw=4)
            # shop front on alternate houses
            if i % 2 == 0:
                box(ctx, x + 20, -190, w - 40, 170, (0.75, 0.88, 0.97), r=4, shade_side=False)
                stripes = shade(col, 0.8)
                for k in range(0, int(w - 20), 30):
                    poly(ctx, [(x + 10 + k, -230), (x + 40 + k, -230), (x + 40 + k, -195), (x + 10 + k, -195)],
                         stripes if (k // 30) % 2 else (1, 1, 1), outline=False)
                line(ctx, [(x + 10, -195), (x + w - 10, -195)], INK, lw=3)
            else:
                box(ctx, x + w / 2 - 40, -170, 80, 170, shade(col, 0.6), r=30)
                circle(ctx, x + w / 2 + 22, -85, 5, (0.95, 0.85, 0.4), lw=1.5)
            x += w

    def mid(self, ctx, W, H, cam, gy, now, x0):
        P = self.pal
        for lx in (x0 + 200, x0 + 950):
            box(ctx, lx - 8, -420, 16, 420, P["lamp"], r=6, lw=2.5)
            box(ctx, lx - 34, -470, 68, 54, P["glow"], r=10)
            line(ctx, [(lx - 40, -470), (lx + 40, -470)], INK, lw=6)
            g = cairo.RadialGradient(lx, -440, 5, lx, -440, 120)
            g.add_color_stop_rgba(0, 1, 0.95, 0.7, 0.35)
            g.add_color_stop_rgba(1, 1, 0.95, 0.7, 0.0)
            ctx.arc(lx, -440, 120, 0, 2 * math.pi)
            ctx.set_source(g)
            ctx.fill()
        # bench + trash bin
        bx = x0 + 520
        box(ctx, bx, -80, 220, 18, (0.62, 0.42, 0.26), r=4)
        box(ctx, bx, -130, 220, 16, (0.62, 0.42, 0.26), r=4)
        for k in (10, 196):
            box(ctx, bx + k, -62, 14, 62, (0.3, 0.3, 0.32), r=3, lw=2)
        box(ctx, x0 + 1250, -100, 70, 100, (0.35, 0.55, 0.45), r=10)

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, 110)
        ctx.set_source_rgb(*P["sidewalk"])
        ctx.fill()
        x = math.floor(a / 120) * 120
        while x < b:
            line(ctx, [(x, 0), (x + 10, 110)], P["curb"], lw=2.5)
            x += 120
        ctx.rectangle(a, 110, b - a, 26)
        ctx.set_source_rgb(*P["curb"])
        ctx.fill()
        ctx.rectangle(a, 136, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["road"])
        ctx.fill()
        x = math.floor(a / 260) * 260
        while x < b:
            ctx.rectangle(x, 230, 140, 14)
            ctx.set_source_rgb(0.95, 0.92, 0.75)
            ctx.fill()
            x += 260
        line(ctx, [(a, 0), (b, 0)], INK, lw=4)


# ---------------------------------------------------------------- stage
class Stage(Set):
    CACHE_LAYERS = ()   # the whole curtain wall sways
    name = "stage"
    PALETTE = dict(back="#2a1b3d", curtain="#b3262f", curtain2="#8e1c25", gold="#e8b84a", floor="#a8693c",
                   floor2="#8f5732", spot="#fff3c4")
    PERIOD = 1600.0

    def background(self, ctx, W, H, cam, gy, now):
        ctx.set_source_rgb(*self.pal["back"])
        ctx.paint()

    def wall(self, ctx, W, H, cam, gy, now, x0, top):
        P = self.pal
        for i in range(0, int(self.PERIOD), 80):
            sw = 6 * math.sin(now * 0.6 + i * 0.05)
            ctx.rectangle(x0 + i + sw * 0.2, top, 80, -top)
            g = cairo.LinearGradient(x0 + i, 0, x0 + i + 80, 0)
            g.add_color_stop_rgb(0, *P["curtain2"])
            g.add_color_stop_rgb(0.5, *P["curtain"])
            g.add_color_stop_rgb(1, *P["curtain2"])
            ctx.set_source(g)
            ctx.fill()
        box(ctx, x0, top, self.PERIOD, -top - 760, P["curtain"], lw=3)
        for i in range(0, int(self.PERIOD), 160):
            ctx.new_path()
            ctx.arc(x0 + i + 80, -760, 80, 0, math.pi)
            ctx.set_source_rgb(*P["curtain"])
            ctx.fill_preserve()
            ctx.set_source_rgb(*P["gold"])
            ctx.set_line_width(6)
            ctx.stroke()

    def floor(self, ctx, W, H, cam, gy, now, a, b):
        P = self.pal
        ctx.rectangle(a, 0, b - a, self.FLOOR_DEPTH)
        ctx.set_source_rgb(*P["floor"])
        ctx.fill()
        for y in range(0, 400, 34):
            line(ctx, [(a, y), (b, y)], P["floor2"], lw=3)
        box(ctx, a, -14, b - a, 20, P["gold"], lw=3, shade_side=False)

    def light(self, ctx, W, H, cam, gy, now):
        cx = W / 2 + 40 * math.sin(now * 0.5)
        g = cairo.RadialGradient(cx, gy, 10, cx, gy, W * 0.6)
        g.add_color_stop_rgba(0, 1, 0.96, 0.8, 0.35)
        g.add_color_stop_rgba(1, 1, 0.96, 0.8, 0.0)
        ctx.move_to(cx - 60, 0)
        ctx.line_to(cx + 60, 0)
        ctx.line_to(cx + W * 0.4, gy + 60)
        ctx.line_to(cx - W * 0.4, gy + 60)
        ctx.close_path()
        ctx.set_source(g)
        ctx.fill()


# ---------------------------------------------------------------- foreground pieces (#60)
# fg_<kind>(ctx, sx, H, u, now): screen space, the piece's base sits on the bottom edge (y=H),
# sx = its centre, u = pixels per design unit (1920-tall frame = 1). Pieces stay below ~0.84 H.
def _fg_col(c, k=0.82):
    return shade(c, k)   # nearer the lens -> a touch darker


def _fg_counter(self, ctx, sx, H, u, now):
    P = self.pal
    w, h = 560 * u, 120 * u
    box(ctx, sx - w / 2, H - h, w, h + 20 * u, _fg_col(P["cabinet"]), r=10 * u, lw=4 * u)
    box(ctx, sx - w / 2 - 18 * u, H - h - 26 * u, w + 36 * u, 34 * u, _fg_col(P["counter"], 0.9), r=8 * u, lw=4 * u,
        shade_side=False)
    for i, (dx, jh, lid) in enumerate(((-170, 120, (0.85, 0.35, 0.3)), (-50, 150, (0.95, 0.75, 0.3)), (90, 105, (0.4, 0.6, 0.85)))):
        jx, jw = sx + dx * u, 86 * u
        base = H - h - 26 * u
        box(ctx, jx - jw / 2, base - jh * u, jw, jh * u, (0.82, 0.9, 0.92), r=16 * u, lw=3.5 * u, shade_side=False)
        box(ctx, jx - jw / 2 + 8 * u, base - jh * u * 0.62, jw - 16 * u, jh * u * 0.55,
            _fg_col((0.96, 0.8, 0.45) if i != 1 else (0.75, 0.45, 0.3), 0.95), r=10 * u, lw=0, outline=False)
        box(ctx, jx - jw / 2 - 4 * u, base - jh * u - 18 * u, jw + 8 * u, 22 * u, lid, r=6 * u, lw=3.5 * u)


def _fg_hay(self, ctx, sx, H, u, now):
    P = self.pal
    w, h = 400 * u, 150 * u
    box(ctx, sx - w / 2, H - h, w, h + 20 * u, _fg_col(P["hay"]), r=26 * u, lw=4 * u)
    for i in range(14):
        x = sx - w / 2 + (i + 0.5) * w / 14
        line(ctx, [(x, H - h + 12 * u), (x + 10 * u * math.sin(i * 1.7), H)], _fg_col(P["hay_dark"]), lw=3 * u)
    for k in range(6):   # stray straws on top
        x = sx - w / 3 + k * w / 8
        line(ctx, [(x, H - h + 4 * u), (x + 26 * u * math.sin(k * 2.3), H - h - 30 * u)], _fg_col(P["straw"]), lw=4 * u)
    line(ctx, [(sx - w / 2 + 40 * u, H - h * 0.55), (sx + w / 2 - 40 * u, H - h * 0.55)], _fg_col(P["beam"]), lw=6 * u)


def _fg_post(self, ctx, sx, H, u, now):
    P = self.pal
    box(ctx, sx - 34 * u, H - 300 * u, 68 * u, 320 * u, _fg_col(P["beam"]), r=6 * u, lw=4 * u)
    for y in (90, 210):
        circle(ctx, sx, H - y * u, 6 * u, shade(P["beam"], 0.5), outline=False)


def _fg_armchair(self, ctx, sx, H, u, now):
    P = self.pal
    col = _fg_col(P["sofa"], 0.78)
    box(ctx, sx - 240 * u, H - 150 * u, 480 * u, 170 * u, col, r=40 * u, lw=4 * u)
    box(ctx, sx - 270 * u, H - 230 * u, 150 * u, 250 * u, shade(col, 0.92), r=60 * u, lw=4 * u)
    line(ctx, [(sx - 100 * u, H - 120 * u), (sx + 200 * u, H - 120 * u)], shade(col, 0.8), lw=4 * u)


def _fg_plant(self, ctx, sx, H, u, now):
    P = self.pal
    leaf = _fg_col(P["plant"])
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.32 + 0.04 * math.sin(now * 1.1 + i)
        L = (210 + 40 * ((i * 3) % 4)) * u
        bx, by = sx, H - 120 * u
        tx, ty = bx + math.cos(a) * L, by + math.sin(a) * L
        nx, ny = -math.sin(a) * 34 * u, math.cos(a) * 34 * u
        ctx.move_to(bx, by)
        ctx.curve_to(bx + nx + (tx - bx) * 0.4, by + ny + (ty - by) * 0.4, tx + nx * 0.3, ty + ny * 0.3, tx, ty)
        ctx.curve_to(tx - nx * 0.3, ty - ny * 0.3, bx - nx + (tx - bx) * 0.4, by - ny + (ty - by) * 0.4, bx, by)
        ctx.set_source_rgb(*shade(leaf, 0.9 + 0.08 * (i % 2)))
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3 * u)
        ctx.stroke()
    poly(ctx, [(sx - 85 * u, H - 130 * u), (sx + 85 * u, H - 130 * u), (sx + 65 * u, H + 10 * u), (sx - 65 * u, H + 10 * u)],
         _fg_col((0.85, 0.45, 0.3)), lw=4 * u)


def _fg_desk(self, ctx, sx, H, u, now):
    P = self.pal
    wood = _fg_col(P["desk"])
    box(ctx, sx - 280 * u, H - 200 * u, 560 * u, 42 * u, wood, r=8 * u, lw=4 * u)
    for lx in (sx - 250 * u, sx + 220 * u):
        box(ctx, lx, H - 160 * u, 30 * u, 180 * u, shade(wood, 0.8), r=4 * u, lw=3.5 * u)
    for i, (c, bh) in enumerate((((0.85, 0.3, 0.3), 34), ((0.3, 0.55, 0.8), 28), ((0.95, 0.8, 0.3), 30))):
        box(ctx, sx - 200 * u + i * 6 * u, H - 200 * u - (sum((34, 28, 30)[:i + 1])) * u, 190 * u, bh * u,
            _fg_col(c), r=4 * u, lw=3 * u, shade_side=False)
    box(ctx, sx + 90 * u, H - 290 * u, 70 * u, 90 * u, _fg_col((0.55, 0.7, 0.85)), r=10 * u, lw=3.5 * u)
    for k, c in enumerate(((0.95, 0.8, 0.2), (0.9, 0.35, 0.3), (0.3, 0.6, 0.4))):
        line(ctx, [(sx + 105 * u + k * 18 * u, H - 280 * u), (sx + 98 * u + k * 22 * u, H - 350 * u)], c, lw=7 * u)


def _fg_mailbox(self, ctx, sx, H, u, now):
    box(ctx, sx - 16 * u, H - 230 * u, 32 * u, 250 * u, (0.35, 0.3, 0.28), r=4 * u, lw=3.5 * u)
    box(ctx, sx - 80 * u, H - 330 * u, 160 * u, 110 * u, (0.3, 0.45, 0.75), r=50 * u, lw=4 * u)
    box(ctx, sx + 62 * u, H - 340 * u, 12 * u, 70 * u, (0.85, 0.25, 0.25), r=3 * u, lw=3 * u)


def _fg_hydrant(self, ctx, sx, H, u, now):
    col = (0.86, 0.26, 0.24)
    box(ctx, sx - 50 * u, H - 190 * u, 100 * u, 210 * u, col, r=24 * u, lw=4 * u)
    box(ctx, sx - 78 * u, H - 140 * u, 156 * u, 44 * u, shade(col, 0.85), r=14 * u, lw=4 * u)
    circle(ctx, sx, H - 206 * u, 34 * u, shade(col, 0.9), lw=4 * u)


def _fg_footlights(self, ctx, sx, H, u, now):
    P = self.pal
    w = self.FG_PERIOD * ctx.get_target().get_width() + 2   # one tile = one layout period: seamless
    box(ctx, sx - w / 2, H - 60 * u, w, 80 * u, _fg_col(P["gold"], 0.7), r=0, lw=4 * u, shade_side=False)
    n = max(4, int(round(w / (190 * u))))
    for i in range(n):
        x = sx - w / 2 + (i + 0.5) * w / n
        g = cairo.RadialGradient(x, H - 70 * u, 4 * u, x, H - 70 * u, 160 * u)
        g.add_color_stop_rgba(0, 1, 0.95, 0.75, 0.45 + 0.05 * math.sin(now * 2 + i))
        g.add_color_stop_rgba(1, 1, 0.95, 0.75, 0.0)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ADD)
        ctx.arc(x, H - 70 * u, 160 * u, 0, 2 * math.pi)
        ctx.set_source(g)
        ctx.fill()
        ctx.restore()
        ctx.move_to(x - 44 * u, H - 50 * u)
        ctx.curve_to(x - 40 * u, H - 100 * u, x + 40 * u, H - 100 * u, x + 44 * u, H - 50 * u)
        ctx.close_path()
        ctx.set_source_rgb(0.18, 0.14, 0.2)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3 * u)
        ctx.stroke()


def _fg_grass(self, ctx, sx, H, u, now):
    P = self.pal
    w = 900 * u
    ctx.move_to(sx - w / 2, H + 10 * u)
    n = 22
    for i in range(n + 1):
        x = sx - w / 2 + i * w / n
        hgt = (60 + 50 * ((i * 7) % 3) + 20 * math.sin(i * 2.1)) * u
        lean = 10 * u * math.sin(now * 1.2 + i * 0.6)
        ctx.line_to(x - w / n / 2, H - 20 * u)
        ctx.line_to(x + lean, H - hgt)
    ctx.line_to(sx + w / 2, H + 10 * u)
    ctx.close_path()
    ctx.set_source_rgb(*_fg_col(P["grass_dark"], 0.85))
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(3 * u)
    ctx.stroke()


def _fg_fencepost(self, ctx, sx, H, u, now):
    P = self.pal
    col = _fg_col(P["fence"], 0.8)
    for dx in (-130, 130):
        poly(ctx, [(sx + (dx - 30) * u, H + 10 * u), (sx + (dx - 30) * u, H - 280 * u), (sx + dx * u, H - 310 * u),
                   (sx + (dx + 30) * u, H - 280 * u), (sx + (dx + 30) * u, H + 10 * u)], col, lw=4 * u)
    box(ctx, sx - 200 * u, H - 230 * u, 400 * u, 40 * u, shade(col, 0.95), r=6 * u, lw=4 * u, shade_side=False)
    box(ctx, sx - 200 * u, H - 120 * u, 400 * u, 40 * u, shade(col, 0.95), r=6 * u, lw=4 * u, shade_side=False)


def _setup_foreground():
    def attach(cls, items, **fns):
        cls.FOREGROUND = items
        for k, f in fns.items():
            setattr(cls, "fg_" + k, f)
    attach(Barn, ((-0.44, "hay"), (0.47, "post")), hay=_fg_hay, post=_fg_post)
    attach(Kitchen, ((-0.45, "counter"),), counter=_fg_counter)
    attach(LivingRoom, ((-0.46, "armchair"), (0.44, "plant")), armchair=_fg_armchair, plant=_fg_plant)
    attach(Classroom, ((-0.45, "desk"),), desk=_fg_desk)
    attach(Street, ((-0.44, "mailbox"), (0.45, "hydrant")), mailbox=_fg_mailbox, hydrant=_fg_hydrant)
    attach(Farmyard, ((-0.42, "grass"), (0.47, "fencepost"), (0.33, "grass")), grass=_fg_grass, fencepost=_fg_fencepost)
    Stage.FG_PERIOD = 1.4
    attach(Stage, ((0, "footlights"),), footlights=_fg_footlights)
    Stage.FG_PAR = 1.1


_setup_foreground()

# default lights (#73): positions match each set's drawn fixtures (layer coords, tiled per PERIOD)
Barn.DEFAULT_LIGHTS = (dict(type="fire", x=1000, y=532, par=Barn.WALL_PAR, period=Barn.PERIOD, flame=False,
                            sparks=0, radius=430, intensity=0.75, flicker=0.16, color="#ffc35a"),)
Kitchen.DEFAULT_LIGHTS = (dict(type="point", x=730, y=510, par=Kitchen.WALL_PAR, period=Kitchen.PERIOD,
                               radius=430, intensity=0.32, color="#d6efff"),
                          dict(type="lamp", x=0, y=760, hanging=True, cord=400, radius=520, when="night"))
LivingRoom.DEFAULT_LIGHTS = (dict(type="lamp", x=760, y=330, par=LivingRoom.MID_PAR, period=LivingRoom.PERIOD,
                                  radius=430, intensity=0.7, when="night"),)
Street.DEFAULT_LIGHTS = tuple(dict(type="lamp", x=lx, y=445, par=Street.MID_PAR, period=Street.PERIOD, radius=380,
                                   intensity=0.75, color="#fff0a8", when="night") for lx in (200, 950))
Stage.DEFAULT_LIGHTS = (dict(type="spot", x=0, y=1300, spread=14, sway=90, intensity=0.8, when="night"),)


SETS = {c.name: c for c in (Barn, Farmyard, Kitchen, LivingRoom, Classroom, Bedroom, Street, Stage)}


def set_options(name):
    """Palette keys and extra options a set accepts (for validation messages)."""
    cls = SETS[name]
    extra = {"seed", "motes", "depth", "cache", "foreground", "lights", "night"}
    if cls is Classroom:
        extra |= {"text"}
    return set(cls.PALETTE) | extra


def make_set(spec, **over):
    """'kitchen' or {"name": "kitchen", "wall": "#..."} -> Set instance."""
    if isinstance(spec, dict):
        spec = dict(spec)
        name = spec.pop("name", None)
        over = {**spec, **over}
    else:
        name = spec
    if name not in SETS:
        raise ValueError(f"unknown set {name!r}; valid: {sorted(SETS)}")
    bad = set(over) - set_options(name)
    if bad:
        raise ValueError(f"set {name!r}: unknown option(s) {sorted(bad)}; valid: {sorted(set_options(name))}")
    return SETS[name](**over)


# ---------------------------------------------------------------- theme fx (scene.fx objects)
class _Cached:
    """fx base: keeps a lazily built cairo surface that is dropped when pickled."""

    def __getstate__(self):
        d = self.__dict__.copy()
        for k in list(d):
            if k.startswith("_c"):
                d[k] = None
        return d


class Grade(_Cached):
    """Colour grade + vignette baked into ONE cached full-frame overlay (fast: a
    single OVER paint per frame). amount = tint strength, vignette = edge darkening."""

    def __init__(self, tint="#ffb86b", amount=0.08, vignette=0.0, vcolor="#1a1020", lift=0.0):
        self.tint, self.amount, self.vignette = hex2rgb(tint), amount, vignette
        self.vcolor, self.lift = hex2rgb(vcolor), lift
        self._c_surf, self._c_size = None, None

    def _build(self, W, H):
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(surf)
        if self.amount > 0:
            c.set_source_rgba(*self.tint, self.amount)
            c.paint()
        if self.lift > 0:
            c.set_source_rgba(1, 1, 1, self.lift)
            c.paint()
        if self.vignette > 0:
            r = math.hypot(W, H) / 2
            g = cairo.RadialGradient(W / 2, H / 2, r * 0.45, W / 2, H / 2, r * 1.05)
            g.add_color_stop_rgba(0, *self.vcolor, 0.0)
            g.add_color_stop_rgba(1, *self.vcolor, self.vignette)
            c.rectangle(0, 0, W, H)
            c.set_source(g)
            c.fill()
        self._c_surf, self._c_size = surf, (W, H)

    def draw(self, ctx, W, H, now):
        if self._c_surf is None or self._c_size != (W, H):
            self._build(W, H)
        ctx.set_source_surface(self._c_surf, 0, 0)
        ctx.paint()


class Vignette(Grade):
    def __init__(self, strength=0.35, color="#1a1020"):
        super().__init__(amount=0.0, vignette=strength, vcolor=color)


class Grain(_Cached):
    """Paper / film grain: a small alpha noise tile blended with OVER, shifted per frame."""

    def __init__(self, amount=0.06, seed=3, animated=True):
        self.amount, self.seed, self.animated = amount, seed, animated
        self._c_tile = None

    def _make(self):
        n = 160
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, n, n)
        c = cairo.Context(surf)
        rng = random.Random(self.seed)
        for _ in range(n * n // 7):
            x, y = rng.randrange(n), rng.randrange(n)
            v = 1.0 if rng.random() < 0.5 else 0.0
            c.rectangle(x, y, 1, 1)
            c.set_source_rgba(v, v, v, rng.uniform(0.4, 1.0))
            c.fill()
        self._c_tile = surf

    def draw(self, ctx, W, H, now):
        if self.amount <= 0:
            return
        if self._c_tile is None:
            self._make()
        off = int(now * 12) % 7 * 23 if self.animated else 0
        pat = cairo.SurfacePattern(self._c_tile)
        pat.set_extend(cairo.EXTEND_REPEAT)
        m = cairo.Matrix()
        m.translate(off, off * 2)
        pat.set_matrix(m)
        ctx.set_source(pat)
        ctx.paint_with_alpha(self.amount)


# "style" = default texture style (#72, toonfx.make_style); an episode "style" key overrides it.
# Chalk tested on the stickman stage but made faces too faint there, so the lesson uses paper.
THEMES = {
    "farm_files": dict(set="barn", style={"name": "paper", "intensity": 0.55},  accent="#ffcf3f", ground_ratio=0.74,
                       zoom={"single": 3.2, "two": 2.7, "group": 2.15},
                       fx=[("grade", dict(tint="#ffb35c", amount=0.07, vignette=0.3)), ("grain", dict(amount=0.05))]),
    "kitchen_chaos": dict(set="kitchen", style={"name": "crayon", "intensity": 0.35},  accent="#ff7a59", ground_ratio=0.74,
                          zoom={"single": 3.4, "two": 2.8, "group": 2.25},
                          fx=[("grade", dict(tint="#ffe2a8", amount=0.05, vignette=0.25))]),
    "max_and_grandma": dict(set="living_room", style={"name": "paper", "intensity": 0.5},  accent="#ffd166", ground_ratio=0.74,
                            zoom={"single": 3.0, "two": 2.5, "group": 2.1},
                            fx=[("grade", dict(tint="#ffc48a", amount=0.08, vignette=0.32)), ("grain", dict(amount=0.06))]),
    "fruit_stories": dict(set="kitchen", style={"name": "watercolour", "intensity": 0.5},  accent="#ffd23f", ground_ratio=0.74,
                          zoom={"single": 3.4, "two": 2.8, "group": 2.25},
                          fx=[("grade", dict(tint="#fff0b0", amount=0.05, vignette=0.2))]),
    "stickman_lesson": dict(set="stage", style={"name": "paper", "intensity": 0.45},  accent="#ffffff", ground_ratio=0.72,
                            zoom={"single": 3.0, "two": 2.5, "group": 2.0},
                            fx=[("vignette", dict(strength=0.4))]),
    "did_you_know": dict(set="classroom", style={"name": "paper", "intensity": 0.35},  accent="#4cc9f0", ground_ratio=0.74,
                         zoom={"single": 3.2, "two": 2.6, "group": 2.1},
                         fx=[("grade", dict(tint="#bde0ff", amount=0.04, vignette=0.22))]),
}
_FX = {"grade": Grade, "vignette": Vignette, "grain": Grain}


def theme_style(name):
    """The theme's default texture style spec (#72): a name, {"name", "intensity", ...} or None."""
    return THEMES[name].get("style")


def theme_fx(name, style=None, fps=30):
    """Screen fx objects for a theme: its texture style (theme default, or `style` = an
    episode override; "clean"/False = none) followed by grade/vignette/grain. A texture
    style brings its own grain, so the theme's plain Grain is dropped when one is active."""
    th = THEMES[name]
    spec = th.get("style") if style is None else style
    st = toonfx.make_style(spec, fps=fps) if spec else None
    out = [st] if st is not None else []
    out += [_FX[k](**opts) for k, opts in th.get("fx", []) if not (st is not None and k == "grain")]
    return out


def theme_zoom(name, n_follow):
    z = THEMES[name]["zoom"]
    return z["single"] if n_follow <= 1 else (z["two"] if n_follow == 2 else z["group"])


def validate_episode_keys(ep):
    """Return an error message (str) for bad set/theme keys, or None."""
    mode = ep.get("mode", "2d")
    if ("set" in ep or "theme" in ep) and mode != "2d":
        return "'set' and 'theme' are 2D-only for now (3D episodes use 'env')"
    if "theme" in ep and ep["theme"] not in THEMES:
        return f"theme {ep['theme']!r} is not valid; use one of {sorted(THEMES)}"
    if "set" in ep:
        try:
            make_set(ep["set"])
        except ValueError as e:
            return str(e)
        except TypeError:
            return f"set must be a name or an object with 'name'; valid names: {sorted(SETS)}"
    return None
