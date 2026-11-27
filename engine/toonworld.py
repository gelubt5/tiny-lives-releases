"""toonworld — vehicles (#63), crowds (#24) and curve paths (#8) for ToonEngine 2D.

Everything here is a scene "extra": an object with update(dt, scene) + draw(ctx, now) (drawn
behind the characters) and, for vehicles, draw_front(ctx, now) (drawn over the characters, e.g. a
car door hiding the driver's legs). Objects are plain data (no lambdas / closures), so they pickle
into the multiprocessing render snapshots.

Python API
----------
    import toonworld as tw
    car  = tw.add(scene, tw.Car(x=-900, color="#e63946"), "car1")
    car.drive_to(0, t=1.0, d=3.0)              # keyframed drive (ease in/out -> squat / nose dive)
    car.path([(6, 0), (9, 700)])               # or path keys (t, x); speed=... instead of d also ok
    car.mount(bobo, t=0.0, d=None)             # seat a character (driver); d=None = until the end
    car.honk(4.2)                              # horn sound + body hop
    bike = tw.add(scene, tw.Bicycle(x=-700, color="#2a9d8f"))
    bike.mount(mia, t=0.0); bike.ring(5.0)     # pedal_phase drives the rider's feet
    cart = tw.add(scene, tw.Cart(x=-400))
    cart.hitch(greta, t=0.0)                   # pulled by a quadruped (harness) or a person (hands)
    crowd = tw.Crowd(scene, n=24, x_range=(-600, 600), depth_rows=2, seed=3, behaviour="mixed")
    crowd.react(4.0, "cheer", d=2.0)           # cheer | gasp | laugh | clap | wave | look_at | flee | idle
    crowd.react(6.0, "look_at", target=car)    # target: x, or any object with .x (followed live)
    crowd.react(9.0, "flee", dir=1)            # run off screen (permanent)
    tw.add(scene, tw.Sidewalk())               # raised back sidewalk strip the crowd stands on

Vehicles expose x, y (world, y up), face, tilt (rad), speed, wheel_angle, pedal_phase and, as
anchors for toonengine's Ride action, seat=(dx, dy) / grip=(dx, dy): world offsets from (x, y) that
already include facing, terrain tilt and body bounce. Vehicles follow Scene.ground_at(x) when the
scene has it (terrain, positive up) and tilt to the slope. Vehicle.mount() snaps the rider in
Vehicle.update (after the characters update) so there is no one-frame lag; it works with or without
a Ride action in toonengine.ACTIONS.

Sound events (scene.event): engine, horn, brake, bell, creak, crowd_cheer, gasp, laugh, applause.
toonworld adds synthesized versions of these to toonengine.Audio (only for kinds the engine does
not know; files in sfx/ still win).

JSON spec (toonworld.build(spec, scene) — a dict or a list of dicts; returns {id: object})
---------------------------------------------------------------------------------------------
    {"vehicle": "car" | "bicycle" | "bike" | "cart" | "scooter",
     "id": "car1", "x": -900, "y": 0, "face": 1, "scale": 1.0,
     "color": "#e63946", "accent": "#ffffff",           # body colour / trim (any vehicle)
     "drive": [{"x": 0, "t": 1.0, "d": 3.0, "ease": "in_out"}, {"x": 800, "t": 7, "speed": 300}],
     "path": [[6.0, 0], [9.0, 700]],                    # (t, x) keys, eased segments
     "rider": "bobo" | {"id": "bobo", "t": 0, "d": null, "role": "driver"} | [..],
     "honk": [3.5, 4.0],  "ring": [5.0],                # car horn / bicycle bell times
     "hitch": "greta" | {"id": "greta", "t": 0, "d": null, "gap": null},   # cart only
     "engine": true}                                     # car: exhaust puffs + engine sounds
    {"crowd": {"id": "crowd", "n": 24, "x_range": [-600, 600], "depth_rows": 2, "seed": 3,
               "style_mix": {"adult": 0.6, "kid": 0.25, "elder": 0.15},
               "behaviour": "idle" | "wander" | "mixed", "y": 14, "scale": 0.8, "fog": 0.22,
               "fog_color": "#dfeaf5", "spread": 0.45,
               "reactions": [{"t": 2, "kind": "cheer", "d": 2},
                             {"t": 5, "kind": "look_at", "target": "car1", "d": 3},
                             {"t": 9, "kind": "flee", "dir": 1}]}}
    {"sidewalk": {"id": "walk", "depth": 64, "color": "#cfcac2", "x_range": [-3000, 3000]}}
Ids in rider / hitch / target are looked up in scene.objects (or earlier specs of the same build).

Curve paths (#8)
----------------
    trail = tw.add(scene, tw.Path([[-400, 0], [-100, 40, 120], [200, 0, 300]], style="footprints"), "trail")
    bobo.at(0.5, tw.FollowPath(trail, speed=120))            # walk (gait from speed), faces travel
    mia.at(2.0, tw.FollowPath(trail, speed=280, end=500)).then(tw.FollowPath(trail, speed=120, start=500))
    bike.follow(ring, t=0, speed=220, loop=True)              # vehicles: tilt, wheels, depth scale
    pip.at(1.0, tw.FollowPath(swoop, speed=360, mode="fly", bank=0.45))   # bird characters fly
    tw.add(scene, tw.Flyer("bird")).fly(swoop, t=0, speed=320, pingpong=True)  # bird|butterfly|plane
Path(points, closed=False, smooth=True, style="none", color, width, spacing, reveal, persp=0.0016,
relative=True, supports=True): points are [x], [x, h] or [x, h, depth] — h = height above the
terrain (scene.ground_at; relative=False: absolute world y), depth = pseudo-3D depth on the ground
strip (+ = nearer: lower on screen, scaled 1 + depth * persp, nearer characters drawn in front).
Centripetal Catmull-Rom through the points, arc-length parameterised (local_at / point_at /
world_at / tangent_at / sample / nearest_s / length). Styles: none | dotted | dashed | road
(asphalt band, dashed centre line, posts under raised parts) | footprints | trail | debug;
reveal=True (default for footprints / trail) draws only what followers have covered.
Followers: loop (lap a closed path / restart an open one), pingpong, laps, d, start / end (arc
length px), reverse. Without laps / d a loop runs until the scene ends (give "d" in JSON timelines).
Limitations: side view only (depth is a fake: no occlusion between vehicles, which are extras drawn
behind all characters); fly mode pitches with the climb (no roll); a closed loop on a vertical
circle (loop-the-loop) is not supported for vehicles (tilt is clamped to +-0.6 rad).

    {"path": {"id": "trail", "points": [[-400, 0], [0, 40, 120]], "closed": false, "smooth": true,
              "style": "footprints", "color": "#5a3d26", "width": 10, "spacing": 32, "reveal": true,
              "persp": 0.0016, "relative": true}}          # or the same keys flat (toonscript "paths")
    {"vehicle": "bicycle", "id": "bike", "follow": {"path": "ring", "t": 0, "speed": 220, "loop": true,
              "pingpong": false, "laps": 3, "d": null, "start": 0, "end": null, "reverse": false,
              "ease": true}}                               # follow may also be a list or a path id
    {"flyer": "bird" | "butterfly" | "plane", "id": "pip", "x": 0, "y": 300, "color", "accent",
              "scale": 1, "path": "swoop", "fly": [{"path": "swoop", "t": 2, "speed": 320, "bank": 0.7}]}
    beat: {"do": "follow_path", "who": "bobo", "path": "trail", "speed": 120, "gait": "walk",
           "loop": false, "pingpong": false, "laps": null, "d": null, "start": 0, "end": null,
           "reverse": false, "mode": "ground" | "fly", "bank": 0.5, "snap": true}
"""
import inspect
import math
import random

import cairo
import numpy as np

import toonengine as te

INK = te.INK

# ---------------------------------------------------------------- small helpers


def _rgb(c, default="#888888"):
    if c is None:
        c = default
    if isinstance(c, str):
        return te.hex2rgb(c)
    return tuple(float(v) for v in c[:3])


def _mix(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def _shade(c, k):
    return tuple(max(0.0, min(1.0, v * k)) for v in c)


def _light(c, k=0.25):
    return tuple(min(1.0, v + (1 - v) * k) for v in c)


def _ground(scene, x):
    """Terrain height at x (positive up); 0 when the scene has no ground_at (flat)."""
    fn = getattr(scene, "ground_at", None)
    if fn is None:
        return 0.0
    try:
        return float(fn(x))
    except Exception:
        return 0.0


EASES = {
    "linear": lambda u: u,
    "in_out": lambda u: u * u * (3 - 2 * u),
    "in": lambda u: u * u,
    "out": lambda u: 1 - (1 - u) * (1 - u),
}


def _ease(name, u):
    u = max(0.0, min(1.0, u))
    if name == "in_out":
        return u * u * (3 - 2 * u)
    if name == "in":
        return u * u
    if name == "out":
        return 1 - (1 - u) * (1 - u)
    return u


def _fill_ink(ctx, col, lw=3.0, ink=INK, alpha=1.0):
    ctx.set_source_rgba(*col, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink, alpha)
    ctx.set_line_width(lw)
    ctx.stroke()


def _rrect(ctx, x, y, w, h, r):
    r = max(0.0, min(r, abs(w) / 2, abs(h) / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def _smooth(ctx, pts, closed=True):
    """Rounded polygon through the midpoints of pts (quadratic corners) — cartoon body shapes."""
    n = len(pts)
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    ctx.new_path()
    ctx.move_to(*mids[-1])
    for i in range(n):
        cx, cy = pts[i]
        mx, my = mids[i]
        px, py = ctx.get_current_point()
        ctx.curve_to(px + (cx - px) * 2 / 3, py + (cy - py) * 2 / 3,
                     mx + (cx - mx) * 2 / 3, my + (cy - my) * 2 / 3, mx, my)
    if closed:
        ctx.close_path()


def _line(ctx, pts, col, lw, ink=True, alpha=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for w, c in (((lw + 5, INK),) if ink else ()) + ((lw, col),):
        ctx.new_path()
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.set_source_rgba(*c, alpha)
        ctx.set_line_width(w)
        ctx.stroke()


class Anchor:
    """A plain point object (x, y) — e.g. a look_at target. Picklable."""

    def __init__(self, x=0.0, y=0.0):
        self.x, self.y = float(x), float(y)


# ---------------------------------------------------------------- engine hooks (fallbacks)
_ORIG_DRAW_FRAME = None
_ORIG_SYNTH = None


class _FrontPass:
    """Stands in for snap['particles'] inside draw_frame: draws extras' draw_front first
    (right after characters / balls / carried props), then the real particles."""

    def __init__(self, parts, extras, now):
        self._parts, self._extras, self._now = parts, extras, now

    def draw(self, ctx):
        for e in self._extras:
            f = getattr(e, "draw_front", None)
            if f is not None:
                f(ctx, self._now)
        self._parts.draw(ctx)

    def __getattr__(self, k):
        return getattr(self.__dict__["_parts"], k)


def _draw_frame_with_front(surf, st, snap):
    ex = snap.get("extras", ())
    if any(hasattr(e, "draw_front") for e in ex):
        snap = dict(snap)
        snap["particles"] = _FrontPass(snap["particles"], ex, snap["time"])
    return _ORIG_DRAW_FRAME(surf, st, snap)


def engine_has_front_pass():
    """True when toonengine.draw_frame itself calls extras' draw_front (agent J's hook)."""
    f = te.draw_frame
    if getattr(f, "_toonworld", False):
        return False
    try:
        return "draw_front" in inspect.getsource(f)
    except (OSError, TypeError):
        return False


def ensure_hooks():
    """Idempotent. Adds (only when missing) a front pass for extras' draw_front to
    toonengine.draw_frame and synthesized vehicle / crowd sounds to toonengine.Audio."""
    global _ORIG_DRAW_FRAME, _ORIG_SYNTH
    if not engine_has_front_pass() and not getattr(te.draw_frame, "_toonworld", False):
        _ORIG_DRAW_FRAME = te.draw_frame
        _draw_frame_with_front._toonworld = True
        te.draw_frame = _draw_frame_with_front
    if not getattr(te.Audio.synth, "_toonworld", False):
        _ORIG_SYNTH = te.Audio.synth

        def synth(self, kind):  # noqa: E306 - method on the class, not stored on objects
            sig = _ORIG_SYNTH(self, kind)
            if len(sig) <= 10 and kind in SFX:
                return _synth(self, kind)
            return sig
        synth._toonworld = True
        te.Audio.synth = synth


SFX = ("engine", "horn", "brake", "bell", "creak", "crowd_cheer", "gasp", "laugh", "applause", "idle_engine",
       "flap")


def _synth(A, kind):
    t, SR = A.t, A.SR
    if kind == "horn":  # two-tone cartoon "meep"
        d = 0.32
        tt = t(d)
        env = np.minimum(1, tt / 0.015) * np.minimum(1, (d - tt) / 0.05)
        s = np.sign(np.sin(2 * np.pi * 415 * tt)) * 0.5 + np.sign(np.sin(2 * np.pi * 520 * tt)) * 0.5
        return 0.16 * _onepole(s, 0.25) * env
    if kind in ("engine", "idle_engine"):  # rising rumble (start) / short idle putt
        d = 0.9 if kind == "engine" else 0.4
        tt = t(d)
        f = 38 + (60 * tt / d if kind == "engine" else 0 * tt)
        ph = 2 * np.pi * np.cumsum(f) / SR
        putt = (np.sin(ph) > 0.3).astype(float)
        s = putt * A.noise(d, 0.12) + 0.6 * np.sin(ph * 2)
        env = np.minimum(1, tt / 0.05) * np.exp(-tt * (1.2 if kind == "engine" else 4))
        return 0.32 * s * env
    if kind == "brake":
        d = 0.35
        tt = t(d)
        return 0.07 * np.sin(2 * np.pi * (2300 - 600 * tt) * tt) * np.sin(np.pi * tt / d)
    if kind == "bell":  # bicycle "ring-ring"
        out = np.zeros(int(0.6 * SR))
        for k in range(2):
            tt = t(0.3)
            s = (np.sin(2 * np.pi * 2350 * tt) + 0.5 * np.sin(2 * np.pi * 3720 * tt)) * np.exp(-tt * 14) * 0.13
            i = int(k * 0.16 * SR)
            out[i:i + len(s)] += s[:len(out) - i]
        return out
    if kind == "creak":
        d = 0.28
        tt = t(d)
        f = 180 + 60 * np.sin(tt * 30)
        return 0.06 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.sin(np.pi * tt / d) * A.noise(d, 0.6)
    if kind == "crowd_cheer":
        d = 1.8
        tt = t(d)
        env = np.minimum(1, tt / 0.25) * np.exp(-np.maximum(0, tt - 0.6) * 2.2)
        s = A.noise(d, 0.35) * 0.5 + A.noise(d, 0.08) * 0.5
        for k in range(7):  # a few "yay!" voices
            at, f0 = 0.05 + 0.13 * k, 380 + 70 * (k % 4)
            bt = t(0.35)
            v = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.4 * bt)) / SR) * np.sin(np.pi * bt / 0.35) * 0.25
            i = int(at * SR)
            s[i:i + len(v)] += v[:len(s) - i]
        return 0.3 * s * env
    if kind == "gasp":
        d = 0.5
        tt = t(d)
        env = np.minimum(1, tt / 0.06) * np.exp(-tt * 6)
        return 0.35 * A.noise(d, 0.45) * env
    if kind == "laugh":
        d = 1.3
        tt = t(d)
        env = np.zeros_like(tt)
        for k in range(5):  # ha-ha-ha bursts
            c = 0.08 + k * 0.22
            env += np.exp(-((tt - c) / 0.05) ** 2)
        s = A.noise(d, 0.3) * 0.6 + np.sin(2 * np.pi * 260 * tt) * 0.4
        return 0.3 * s * env * np.exp(-tt * 0.8)
    if kind == "applause":
        d = 2.0
        out = np.zeros(int(d * SR))
        rng = np.random.default_rng(7)
        clap = A.noise(0.05, 0.6) * np.exp(-t(0.05) * 70)
        for at in rng.uniform(0, d - 0.06, 90):
            i = int(at * SR)
            out[i:i + len(clap)] += clap * rng.uniform(0.3, 1.0)
        return 0.18 * out * np.exp(-np.maximum(0, t(d) - 1.2) * 2.5)
    if kind == "flap":  # a few soft wing beats
        d = 0.45
        tt = t(d)
        env = np.zeros_like(tt)
        for k in range(3):
            env += np.exp(-((tt - 0.05 - 0.13 * k) / 0.025) ** 2) * (1 - 0.25 * k)
        return 0.22 * _onepole(A.noise(d, 0.5), 0.12) * env
    return np.zeros(10)


def _onepole(x, lp):
    return te._onepole(np.asarray(x, dtype=np.float64), lp)


def add(scene, obj, id=None):
    """Add a toonworld object to a scene (works with or without Scene.add duck-typing).
    Extras are kept ordered by their `layer` (crowd -10 behind vehicles 0)."""
    ensure_hooks()
    scene.add(obj, id) if id is not None else scene.add(obj)
    if id is None:  # Scene.add keys by name; give it a stable id
        pass
    ex = scene.extras
    if obj in ex:
        ex.remove(obj)
    lay = getattr(obj, "layer", 0)
    i = len(ex)
    while i > 0 and getattr(ex[i - 1], "layer", 0) > lay:
        i -= 1
    ex.insert(i, obj)
    if hasattr(obj, "id") and id is not None:
        obj.id = id
    return obj


# ---------------------------------------------------------------- vehicles (#63)
class Vehicle:
    """Base 2D vehicle. Subclasses set geometry (local units, x forward, y up, ground = 0 under
    the wheels) and draw _back(ctx, now) / _front(ctx, now) in that local frame."""

    kind = "vehicle"
    layer = 0
    WHEELS = ((-80.0, 27.0), (80.0, 27.0))   # (local x, radius); wheel centre height = radius
    SEAT = (0.0, 50.0)                        # rider hip (local)
    GRIP = (30.0, 95.0)                       # rider hands (local)
    PEDAL = None                              # (crank centre local, crank length) or None
    HALF_LEN = 125.0
    STIFF, DAMP = 120.0, 9.0                  # body suspension spring

    def __init__(self, x=0.0, y=None, face=1, color="#e63946", accent="#ffffff", scale=1.0, id=None,
                 auto_face=True):
        self.x0 = float(x)
        self.x = float(x)
        self.y = 0.0 if y is None else float(y)
        self._fixed_y = y
        self.face = 1 if face >= 0 else -1
        self.color, self.accent = _rgb(color), _rgb(accent)
        self.scale = float(scale)
        self.id = id
        self.auto_face = auto_face
        self.segs = []          # (t, d, x_target, ease)
        self.riders = []        # dicts: char, t, d, role, state
        self.honks = []         # times (car horn / bike bell)
        self.tilt = 0.0         # world rotation (rad, + = counter-clockwise)
        self.speed = 0.0        # world units / s (signed, + = to the right)
        self.accel = 0.0
        self.distance = 0.0     # forward distance travelled (for wheels / pedals)
        self.pitch = te.Spring(self.STIFF, self.DAMP)   # body pitch (nose up +)
        self.bounce = te.Spring(self.STIFF * 1.4, self.DAMP)  # body vertical offset
        self.time = 0.0
        self.moving = False
        self.puffs = []         # exhaust / dust puffs (t0, x, y, vx, vy, r)
        self.rng = random.Random(int(abs(x)) + 17)
        self._honk_done = set()
        self.follows = []       # (t, _Travel) curve-path drives (#8)
        self.base_scale = self.scale
        self._fs = None         # last follow arc length
        self._init_pose()

    def _init_pose(self):
        pass

    # ---------------------------------------------------------------- keyframes
    def drive_to(self, x, t, d=None, speed=None, ease="in_out"):
        """Drive to x starting at time t over d seconds (or at `speed` units/s)."""
        if ease not in EASES:
            raise ValueError(f"unknown ease {ease!r}; valid: {sorted(EASES)}")
        if d is None:
            start = self.pos_at(t)
            sp = float(speed or 260.0)
            d = max(0.2, abs(float(x) - start) / sp * (1.5 if ease == "in_out" else 1.0))
        self.segs.append((float(t), float(d), float(x), ease))
        self.segs.sort(key=lambda s: s[0])
        return self

    def path(self, keys, ease="in_out"):
        """Path keys [(t, x), ...]: drive from key to key (the first key is where it waits)."""
        keys = sorted((float(t), float(x)) for t, x in keys)
        for (t0, _), (t1, x1) in zip(keys, keys[1:]):
            self.drive_to(x1, t0, max(0.05, t1 - t0), ease=ease)
        return self

    def pos_at(self, t):
        """Keyframed x at time t (pure function of the drive segments)."""
        x = self.x0
        for t0, d, xt, e in self.segs:
            if t < t0:
                break
            u = (t - t0) / d if d > 0 else 1.0
            if u >= 1:
                x = xt
            else:
                x = x + (xt - x) * _ease(e, u)
                break
        return x

    def honk(self, t):
        self.honks.append(float(t))
        return self

    def follow(self, path, t=0.0, speed=260.0, d=None, loop=False, pingpong=False, laps=None, start=0.0,
               end=None, reverse=False, ease=True):
        """Drive along a curve Path (#8) from time t at `speed` (or over d seconds): x, height,
        depth (pseudo-perspective scale) and tilt come from the path (+ terrain). loop / pingpong /
        laps as FollowPath. ease: accelerate / brake at the ends (suspension squats and dives).
        From the first follow's start time the path wins over drive_to / path keys."""
        r = 0.6 if ease else 0.0
        tr = _Travel(path, speed, start, end, loop, pingpong, laps, d, reverse, ramp=r, ramp_out=r)
        self.follows.append((float(t), tr))
        self.follows.sort(key=lambda f: f[0])
        return self

    def _follow_at(self, T, scene):
        """(x, y, tilt, k, s, sgn) on the active follow path at time T, or None."""
        fl = None
        for f in self.follows:
            if f[0] <= T:
                fl = f
        if fl is None:
            return None
        t0, tr = fl
        s, sgn, _ = tr.s_at(T - t0)
        P = tr.path
        x, y, k = P.world_at(s, scene)
        half = abs(self.WHEELS[-1][0] - self.WHEELS[0][0]) * 0.5 * self.base_scale * k
        sa, sb = s - half, s + half
        if not P.closed:
            sa, sb = max(0.0, sa), min(P.length, sb)
        xa, xb = P.local_at(sa)[0], P.local_at(sb)[0]
        ya, yb = P.surface_y(sa, scene), P.surface_y(sb, scene)
        tilt = math.atan((yb - ya) / (xb - xa)) if abs(xb - xa) > 0.3 * half else 0.0
        return x, y, max(-0.6, min(0.6, tilt)), k, s, sgn, P

    def mount(self, char, t=0.0, d=None, role="driver", hop=0.35, exit_dx=None):
        """Seat `char` from time t for d seconds (None = until the end). The vehicle positions and
        poses the rider every frame (after the character's own update: no lag)."""
        self.riders.append(dict(char=char, t=float(t), d=None if d is None else float(d), role=role,
                                hop=float(hop), exit_dx=exit_dx, frm=None, out=None, done=False,
                                shadow=getattr(char, "draw_shadow", True)))
        return self

    # ---------------------------------------------------------------- geometry
    def _body_local(self, lx, ly):
        """Apply body pitch / bounce (around the axle line) to a local point."""
        pv = self.WHEELS[0][1]
        p = self.pitch.x
        c, s = math.cos(p), math.sin(p)
        dx, dy = lx, ly - pv
        return (dx * c - dy * s, pv + dx * s + dy * c + self.bounce.x)

    def world_point(self, lx, ly, body=True):
        if body:
            lx, ly = self._body_local(lx, ly)
        u, v = self.face * lx * self.scale, ly * self.scale
        c, s = math.cos(self.tilt), math.sin(self.tilt)
        return (self.x + u * c - v * s, self.y + u * s + v * c)

    @property
    def seat(self):
        sx, sy = self.world_point(*self.SEAT)
        return (sx - self.x, sy - self.y)

    @property
    def grip(self):
        gx, gy = self.world_point(*self.GRIP)
        return (gx - self.x, gy - self.y)

    @property
    def wheel_r(self):
        return self.WHEELS[0][1] * self.scale

    @property
    def wheel_angle(self):
        """Wheel rotation (rad) = forward distance / wheel radius (rolling without slip)."""
        return self.distance / self.wheel_r

    @property
    def pedal_phase(self):
        """Crank angle (rad) for toonengine.Ride: near foot at pedal + (face*r*cos, r*sin)."""
        return -self.wheel_angle / 1.8 if self.PEDAL_ON else None

    PEDAL_ON = False
    FOOTREST = None   # local point for Ride's feet when there are no pedals

    @property
    def footrest(self):
        if self.FOOTREST is None:
            return None
        fx, fy = self.world_point(*self.FOOTREST)
        return (fx - self.x, fy - self.y)

    def _target_x(self, T, scene):
        return self.pos_at(T)

    # ---------------------------------------------------------------- simulation
    def update(self, dt, scene):
        T = scene.time + dt       # the frame drawn after this step shows time T
        self.time = T
        fp = self._follow_at(T, scene) if self.follows else None
        nx = self._target_x(T, scene) if fp is None else fp[0]
        dx = nx - self.x
        v = dx / dt if dt > 0 else 0.0
        if fp is not None:        # along a curve: speed / accel measured along the path
            P_len = fp[6].length
            ds = 0.0 if (self._fs is None or getattr(self, "_fpath", None) is not fp[6]) else fp[4] - self._fs
            self._fpath = fp[6]
            if abs(ds) > P_len / 2:       # wrapped round a closed path
                ds -= math.copysign(P_len, ds)
            self._fs = fp[4]
            tx = 0.0
            if dt > 0 and abs(ds) > 1e-9:
                tx = dx / abs(ds)
            if self.auto_face and abs(tx) > 0.25:
                self.face = 1 if tx > 0 else -1
            va = abs(ds) / dt * self.face if dt > 0 else 0.0
            self.accel = (va - self.speed) / dt if dt > 0 else 0.0
            self.speed = va
            self.distance += abs(ds)
            self.scale = self.base_scale * fp[3]
            for r in self.riders:
                c = r["char"]
                bs = r.setdefault("base_scale", c.scale)
                c.scale = bs * fp[3]
                c._path_depth = (fp[3] - 1.0) / fp[6].persp if fp[6].persp else 0.0
        else:
            self.accel = (v - self.speed) / dt if dt > 0 else 0.0
            self.speed = v
            if self.auto_face and abs(v) > 4:
                self.face = 1 if v > 0 else -1
            self.distance += dx * self.face
        self.x = nx
        # terrain: wheel contacts -> height + tilt
        (rx, _), (fx, _) = self.WHEELS[0], self.WHEELS[-1]
        xr, xf = self.x + self.face * rx * self.scale, self.x + self.face * fx * self.scale
        hr, hf = _ground(scene, xr), _ground(scene, xf)
        if fp is not None:
            self.y, self.tilt = fp[1], fp[2]
        elif self._fixed_y is not None:
            self.y, self.tilt = float(self._fixed_y), 0.0
        elif abs(xf - xr) > 1e-6:
            self.tilt = math.atan((hf - hr) / (xf - xr))
            self.y = (hr + hf) / 2
        # suspension: squat on acceleration, nose dive on braking (forward accel along facing)
        fa = self.accel * self.face
        self.pitch.update(max(-0.09, min(0.09, fa * 0.00011)), dt)
        self.bounce.update(max(-6.0, min(6.0, -abs(fa) * 0.004)), dt)
        was = self.moving
        self.moving = abs(v) > 6 or (fp is not None and abs(self.speed) > 6)
        self._events(scene, was, T, dt)
        self._update_puffs(dt, T)
        self._place_riders(dt, scene, T)

    def _events(self, scene, was, T, dt):
        for h in self.honks:
            if h not in self._honk_done and T >= h:
                self._honk_done.add(h)
                self._honk_event(scene)

    def _honk_event(self, scene):
        scene.event("horn", self.x)
        self.bounce.v += 90.0

    def _update_puffs(self, dt, T):
        self.puffs = [p for p in self.puffs if T - p[0] < 0.9]

    # ---------------------------------------------------------------- riders
    def _rider_pose(self, char, P, role, T):
        """Override char's drawn pose for sitting on this vehicle. Returns hip height (local
        character units) so the hip lands on the seat."""
        return 40.0

    def _hip_h(self, c, role):
        """Hip height above the seat (character units); the character origin sits this far
        below the seat point. 0 = the origin is on the seat (animals, standing riders)."""
        return 30.0

    def _place_riders(self, dt, scene, T):
        for r in self.riders:
            c = r["char"]
            t0, d = r["t"], r["d"]
            if T < t0 or r["done"]:
                continue
            end = None if d is None else t0 + d
            if r["frm"] is None and not r.get("hop_skip"):
                if T - t0 > r["hop"] + 1e-9 or T <= dt + 1e-9:  # mounted from the start: no hop
                    r["hop_skip"] = True
                else:
                    r["frm"] = (c.x, c.y)
            if end is not None and T >= end + r["hop"]:
                if not r["done"]:
                    r["done"] = True
                    if r["out"] is not None:
                        c.x, c.y = r["out"]
                    c.draw_shadow = r["shadow"]
                continue
            animal = getattr(c, "style", "toon") in ("quadruped", "bird")
            hipH = 0.0 if animal else self._hip_h(c, r["role"])
            sx, sy = self.world_point(*self._seat_for(r["role"]))
            tx, ty = sx, sy - hipH * c.scale
            # pose for the seated position (character placed on the seat first)
            c.x, c.y, c.face = tx, ty, self.face
            if not animal:
                P = dict(getattr(c, "dpose", None) or c.pose)
                self._rider_pose(c, P, r["role"], T)
                P["ik"] = 1.0
            # mount / dismount hop
            w = 1.0
            if r["frm"] is not None and T < t0 + r["hop"]:
                u = (T - t0) / r["hop"]
                fx, fy = r["frm"]
                w = te.ease(u)
                tx, ty = te.lerp(fx, tx, w), te.lerp(fy, ty, w) + 60 * math.sin(math.pi * u)
            elif end is not None and T >= end:
                if r["out"] is None:
                    ex = r["exit_dx"] if r["exit_dx"] is not None else (self.HALF_LEN + 45) * self.scale
                    ox = self.x + self.face * ex
                    r["out"] = (ox, _ground(scene, ox))
                    scene.event("hop", c.x)
                u = (T - end) / r["hop"]
                ox, oy = r["out"]
                w = 1 - te.ease(u)
                tx, ty = te.lerp(ox, tx, w), te.lerp(oy, ty, w) + 60 * math.sin(math.pi * u)
            c.x, c.y, c.vy = tx, ty, 0.0
            c.draw_shadow = False if w > 0.3 else r["shadow"]
            if not animal:
                base = dict(getattr(c, "dpose", None) or c.pose)
                for k, v in P.items():
                    if k in base and isinstance(v, (int, float)) and k not in ("ik", "hipIK"):
                        base[k] = te.lerp(base[k], v, w)
                if w > 0.5:
                    base["ik"], base["hipIK"] = 1.0, P["hipIK"]
                c.dpose = base

    def _seat_for(self, role):
        return self.SEAT

    def _arms_to(self, c, P, grip_world, skip_front=False, spread=4.0):
        sk = c._skeleton(P)
        if sk is None:
            return
        g = c.to_local(grip_world)
        gw = getattr(c, "_gw", 0.0) if getattr(c, "_gkind", None) else 0.0
        if not skip_front and gw < 0.5:
            au, el = te.arm_ik(sk["shoulderF"], (g[0] + spread, g[1]), c.UARM, c.LARM)
            P["armUF"], P["elbowF"] = au, el
        au, el = te.arm_ik(sk["shoulderB"], (g[0] - spread, g[1] + 2), c.UARM, c.LARM)
        P["armUB"], P["elbowB"] = au, el

    def _legs_to(self, c, P, footF, footB, hipH):
        hip = (0.0, -hipH)
        P["thighF"], P["kneeF"] = te.ik2(hip, c.to_local(footF), c.THIGH, c.SHIN)
        P["thighB"], P["kneeB"] = te.ik2(hip, c.to_local(footB), c.THIGH, c.SHIN)

    # ---------------------------------------------------------------- drawing
    def _xform(self, ctx, body=False):
        ctx.translate(self.x, -self.y)
        ctx.rotate(-self.tilt)
        ctx.scale(self.face * self.scale, -self.scale)
        if body:
            pv = self.WHEELS[0][1]
            ctx.translate(0, pv + self.bounce.x)
            ctx.rotate(self.pitch.x)
            ctx.translate(0, -pv)

    def _shadow(self, ctx):
        ctx.save()
        ctx.translate(self.x, -self.y + 2)
        ctx.scale(self.HALF_LEN * 0.95 * self.scale, 9 * self.scale)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0, 0, 0, 0.2)
        ctx.fill()

    def _draw_puffs(self, ctx, now):
        T = self.time
        for t0, x, y, vx, vy, r in self.puffs:
            a = T - t0
            if a < 0:
                continue
            k = a / 0.9
            rr = r * (0.6 + 1.6 * k) * self.scale
            ctx.arc(x + vx * a, -(y + vy * a), rr, 0, 2 * math.pi)
            ctx.set_source_rgba(0.93, 0.93, 0.95, 0.75 * (1 - k))
            ctx.fill_preserve()
            ctx.set_source_rgba(*INK, 0.35 * (1 - k))
            ctx.set_line_width(2)
            ctx.stroke()

    def draw(self, ctx, now):
        self._shadow(ctx)
        self._draw_puffs(ctx, now)
        ctx.save()
        self._xform(ctx, body=False)
        self._back_chassis(ctx, now)
        ctx.restore()
        ctx.save()
        self._xform(ctx, body=True)
        self._back(ctx, now)
        ctx.restore()

    def draw_front(self, ctx, now):
        ctx.save()
        self._xform(ctx, body=True)
        self._front(ctx, now)
        ctx.restore()
        ctx.save()
        self._xform(ctx, body=False)
        self._front_chassis(ctx, now)
        ctx.restore()

    def _back_chassis(self, ctx, now):
        pass

    def _back(self, ctx, now):
        pass

    def _front(self, ctx, now):
        pass

    def _front_chassis(self, ctx, now):
        pass

    def _wheel(self, ctx, cx, r, rim=(0.85, 0.86, 0.9), tire=(0.17, 0.16, 0.2), spokes=0, hub=None,
               lw=3.0):
        ang = -self.wheel_angle  # see module notes: local frame is y-up (mirrored)
        ctx.arc(cx, r, r, 0, 2 * math.pi)
        _fill_ink(ctx, tire, lw)
        if spokes:
            ctx.arc(cx, r, r * 0.84, 0, 2 * math.pi)
            ctx.set_source_rgba(*rim, 0.35)
            ctx.set_line_width(2.0)
            ctx.stroke()
            for k in range(spokes):
                a = ang + k * math.pi / spokes
                ctx.move_to(cx - r * 0.84 * math.cos(a), r - r * 0.84 * math.sin(a))
                ctx.line_to(cx + r * 0.84 * math.cos(a), r + r * 0.84 * math.sin(a))
            ctx.set_source_rgb(*_shade(rim, 0.8))
            ctx.set_line_width(1.6)
            ctx.stroke()
            ctx.arc(cx, r, r * 0.13, 0, 2 * math.pi)
            _fill_ink(ctx, hub or rim, 2)
            return
        ctx.arc(cx, r, r * 0.58, 0, 2 * math.pi)
        _fill_ink(ctx, rim, 2.5)
        ctx.arc(cx, r, r * 0.25, 0, 2 * math.pi)
        _fill_ink(ctx, hub or _shade(rim, 0.8), 2)
        for k in range(4):  # bolts: show the rotation
            a = ang + k * math.pi / 2
            ctx.arc(cx + r * 0.42 * math.cos(a), r + r * 0.42 * math.sin(a), r * 0.07, 0, 2 * math.pi)
            ctx.set_source_rgb(*_shade(rim, 0.55))
            ctx.fill()
        # tread marks
        for k in range(8):
            a = ang + k * math.pi / 4
            ctx.move_to(cx + r * 0.8 * math.cos(a), r + r * 0.8 * math.sin(a))
            ctx.line_to(cx + r * 0.95 * math.cos(a), r + r * 0.95 * math.sin(a))
        ctx.set_source_rgba(1, 1, 1, 0.18)
        ctx.set_line_width(2)
        ctx.stroke()


class Car(Vehicle):
    """Small cartoon car (side view): rotating wheels, suspension squat / nose dive, idle shake,
    exhaust puffs, engine / horn / brake sounds. The driver shows through the windows; the door
    panel (draw_front) hides the legs."""

    kind = "car"
    WHEELS = ((-80.0, 27.0), (80.0, 27.0))
    SEAT = (-6.0, 46.0)
    FOOTREST = (58.0, 24.0)
    BACK_SEAT = (-80.0, 50.0)
    GRIP = (40.0, 102.0)
    HALF_LEN = 126.0

    def __init__(self, x=0.0, y=None, face=1, color="#e63946", accent="#ffffff", scale=1.0, id=None,
                 engine=True, glass="#bfe3f5", auto_face=True):
        super().__init__(x, y, face, color, accent, scale, id, auto_face)
        self.engine = bool(engine)
        self.glass = _rgb(glass)
        self._started = False

    def _seat_for(self, role):
        return self.BACK_SEAT if role in ("passenger", "back") else self.SEAT

    def _rider_pose(self, c, P, role, T):
        hipH = self._hip_h(c, role)
        P.update(ik=1.0, hipIK=hipH, torso=-0.06, head=P.get("head", 0.0) * 0.5,
                 thighF=1.45, kneeF=0.3, thighB=1.4, kneeB=0.35)
        if role == "driver":
            self._arms_to(c, P, self.world_point(*self.GRIP))
        else:
            P.update(armUF=0.5, elbowF=1.2, armUB=0.4, elbowB=1.0)
        return hipH

    def _events(self, scene, was, T, dt):
        super()._events(scene, was, T, dt)
        if self.engine and not self.moving:  # idle shake (before the riders are seated)
            self.bounce.x += 0.45 * math.sin(T * 2 * math.pi * 23)
        if self.moving and not was:
            if self.engine and not self._started:
                scene.event("engine", self.x, gain=0.8)
            self._started = True
            self.bounce.v -= 30
        if was and not self.moving and self.engine:
            scene.event("brake", self.x, gain=0.6)
            self.pitch.v -= 0.5 * 1  # extra nose-dive kick on the stop

    def _update_puffs(self, dt, T):
        super()._update_puffs(dt, T)
        if not self.engine:
            return
        rate = 3.0 + min(14.0, abs(self.speed) * 0.05)
        if self.rng.random() < rate * dt:
            ex, ey = self.world_point(-self.HALF_LEN - 4, 22)
            self.puffs.append((T, ex, ey, -self.face * self.rng.uniform(30, 70) - self.speed * 0.15,
                               self.rng.uniform(10, 30), self.rng.uniform(6, 10)))

    # ---- drawing (local frame: x forward, y up)
    def _body_path(self, ctx):
        _smooth(ctx, [(-126, 22), (-128, 74), (-104, 88), (62, 88), (116, 80), (128, 58),
                      (126, 24), (100, 18), (-100, 18)])

    def _cabin_path(self, ctx, inset=0.0):
        i = inset
        _smooth(ctx, [(-104 + i, 84), (-96 + i, 150 - i * 0.4), (-70 + i * 0.6, 184 - i),
                      (14 - i * 0.6, 184 - i), (36 - i * 0.6, 160 - i * 0.4), (72 - i * 1.6, 86)])

    def _back(self, ctx, now):
        col = self.color
        self._cabin_path(ctx)
        _fill_ink(ctx, col, 3.5)
        self._cabin_path(ctx, 9)
        ctx.set_source_rgb(*self.glass)
        ctx.fill()
        # interior: seat back + headrest behind the driver
        _rrect(ctx, -44, 40, 22, 82, 9)
        _fill_ink(ctx, _shade(col, 0.45), 2.5)
        _rrect(ctx, -42, 122, 18, 22, 7)
        _fill_ink(ctx, _shade(col, 0.45), 2.5)

    def _front(self, ctx, now):
        col = self.color
        dark = _shade(col, 0.72)
        # steering wheel (thin ring seen from the side) + column
        _line(ctx, [(60, 86), (42, 100)], (0.25, 0.25, 0.3), 4, ink=False)
        ctx.save()
        ctx.translate(42, 102)
        ctx.rotate(-0.45)
        ctx.scale(5, 17)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(0.2, 0.2, 0.25)
        ctx.set_line_width(4)
        ctx.stroke()
        # glass glints over the driver
        ctx.save()
        self._cabin_path(ctx, 9)
        ctx.clip()
        for x0, w in ((-20, 16), (6, 7)):
            ctx.move_to(x0, 90)
            ctx.line_to(x0 + w, 90)
            ctx.line_to(x0 + w + 46, 186)
            ctx.line_to(x0 + 46, 186)
            ctx.close_path()
        ctx.set_source_rgba(1, 1, 1, 0.28)
        ctx.fill()
        ctx.restore()
        # window frame: B-pillar + cabin outline over whatever overlaps it (driver's hat...)
        ctx.move_to(-56, 86)
        ctx.line_to(-54, 174)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(13)
        ctx.stroke()
        ctx.move_to(-56, 86)
        ctx.line_to(-54, 174)
        ctx.set_source_rgb(*col)
        ctx.set_line_width(8)
        ctx.stroke()
        self._cabin_path(ctx, 9)
        ctx.set_source_rgba(*INK, 0.8)
        ctx.set_line_width(2.5)
        ctx.stroke()
        # body (door panel hides the driver's legs)
        self._body_path(ctx)
        _fill_ink(ctx, col, 3.5)
        ctx.save()  # cel shade: lower band darker, top highlight
        self._body_path(ctx)
        ctx.clip()
        ctx.rectangle(-140, 0, 280, 44)
        ctx.set_source_rgb(*dark)
        ctx.fill()
        ctx.move_to(-110, 80)
        ctx.line_to(56, 80)
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ctx.set_line_width(5)
        ctx.stroke()
        ctx.restore()
        self._body_path(ctx)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3.5)
        ctx.stroke()
        # door seams + handle
        for x0 in (-58, 44):
            ctx.move_to(x0, 84)
            ctx.line_to(x0 + 2, 28)
        ctx.set_source_rgba(*INK, 0.7)
        ctx.set_line_width(2.5)
        ctx.stroke()
        _rrect(ctx, -46, 66, 18, 6, 3)
        _fill_ink(ctx, _shade(col, 0.5), 2)
        # stripe (accent)
        ctx.move_to(-126, 56)
        ctx.line_to(127, 56)
        ctx.set_source_rgba(*self.accent, 0.85)
        ctx.set_line_width(5)
        ctx.stroke()
        # lights + bumpers
        ctx.save()
        ctx.translate(119, 66)
        ctx.scale(8, 11)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        _fill_ink(ctx, (1.0, 0.95, 0.6), 2.5)
        _rrect(ctx, -131, 60, 8, 18, 3)
        _fill_ink(ctx, (0.9, 0.15, 0.2), 2.2)
        _rrect(ctx, 104, 16, 30, 13, 6)
        _fill_ink(ctx, (0.75, 0.76, 0.8), 2.5)
        _rrect(ctx, -136, 16, 30, 13, 6)
        _fill_ink(ctx, (0.75, 0.76, 0.8), 2.5)
        # exhaust pipe
        _rrect(ctx, -140, 18, 16, 7, 3)
        _fill_ink(ctx, (0.45, 0.45, 0.5), 2)

    def _front_chassis(self, ctx, now):
        for wx, r in self.WHEELS:  # arches + wheels (do not bounce with the body)
            ctx.arc(wx, r + 1, r + 6, 0, math.pi)
            ctx.set_source_rgb(0.12, 0.1, 0.14)
            ctx.fill()
            self._wheel(ctx, wx, r)


class Bicycle(Vehicle):
    """Bicycle: spoked wheels, the crank turns with distance (pedal_phase) and drives the rider's
    feet by IK; hands on the handlebar; ring(t) for the bell."""

    kind = "bicycle"
    WHEELS = ((-54.0, 33.0), (54.0, 33.0))
    SEAT = (-16.0, 86.0)
    GRIP = (34.0, 104.0)
    CRANK = (2.0, 33.0)
    CRANK_L = 15.0
    HALF_LEN = 88.0
    STIFF, DAMP = 200.0, 14.0

    def ring(self, t):
        return self.honk(t)

    def _honk_event(self, scene):
        scene.event("bell", self.x)

    PEDAL_ON = True

    @property
    def pedal(self):
        """Crank centre (world offset from x, y) for toonengine.Ride."""
        px, py = self.world_point(*self.CRANK)
        return (px - self.x, py - self.y)

    @property
    def pedal_r(self):
        return self.CRANK_L * self.scale

    def _pedals(self):
        ph = self.pedal_phase
        cx, cy = self.CRANK
        L = self.CRANK_L
        near = (cx + L * math.cos(ph), cy + L * math.sin(ph))
        far = (cx - L * math.cos(ph), cy - L * math.sin(ph))
        return near, far

    def _hip_h(self, c, role):
        return 40.0

    def _rider_pose(self, c, P, role, T):
        hipH = 40.0
        near, far = self._pedals()
        P.update(ik=1.0, hipIK=hipH, torso=0.32, head=-0.22)
        hip = (0.0, -hipH)
        fn = c.to_local(self.world_point(near[0] + 3, near[1] + 4))  # ankle just above the pedal
        ff = c.to_local(self.world_point(far[0] + 3, far[1] + 4))
        P["thighF"], P["kneeF"] = te.ik2(hip, fn, c.THIGH, c.SHIN)
        P["thighB"], P["kneeB"] = te.ik2(hip, ff, c.THIGH, c.SHIN)
        self._arms_to(c, P, self.world_point(*self.GRIP), spread=3.0)
        return hipH

    def _back_chassis(self, ctx, now):
        col = self.color
        for wx, r in self.WHEELS:
            ctx.arc(wx, r, r, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(7)
            ctx.stroke()
            ctx.arc(wx, r, r, 0, 2 * math.pi)
            ctx.set_source_rgb(0.25, 0.24, 0.28)
            ctx.set_line_width(4)
            ctx.stroke()
            self._spokes(ctx, wx, r)
        near, far = self._pedals()
        cx, cy = self.CRANK
        _line(ctx, [(cx, cy), far], (0.35, 0.35, 0.4), 3.5)
        _rrect(ctx, far[0] - 7, far[1] - 2.5, 14, 5, 2)
        _fill_ink(ctx, (0.3, 0.3, 0.33), 1.5)
        rear, front = self.WHEELS[0], self.WHEELS[1]
        seat_top = (self.SEAT[0] - 2, self.SEAT[1] - 8)
        head = (front[0] - 18, 92)
        frame = [(rear[0], rear[1]), (cx, cy), seat_top, (rear[0], rear[1])]
        _line(ctx, frame, col, 5)
        _line(ctx, [(cx, cy), (head[0] + 2, head[1] - 10), seat_top], col, 5)
        _line(ctx, [(front[0], front[1]), head, (head[0] - 3, head[1] + 10)], _shade(col, 0.8), 5)
        ctx.arc(cx, cy, 8, 0, 2 * math.pi)  # chain ring
        _fill_ink(ctx, (0.6, 0.6, 0.65), 2)
        ctx.move_to(cx, cy + 8)
        ctx.line_to(rear[0], rear[1] + 4)
        ctx.move_to(cx, cy - 8)
        ctx.line_to(rear[0], rear[1] - 4)
        ctx.set_source_rgba(*INK, 0.6)
        ctx.set_line_width(1.5)
        ctx.stroke()
        # saddle
        _smooth(ctx, [(self.SEAT[0] - 16, self.SEAT[1] - 6), (self.SEAT[0] + 14, self.SEAT[1] - 4),
                      (self.SEAT[0] + 10, self.SEAT[1] + 1), (self.SEAT[0] - 16, self.SEAT[1] + 2)])
        _fill_ink(ctx, (0.2, 0.18, 0.22), 2)
        # handlebar
        g = self.GRIP
        _line(ctx, [(head[0] - 3, head[1] + 10), (g[0] - 6, g[1]), (g[0] + 4, g[1] - 2)], (0.3, 0.3, 0.35), 3.5)
        # basket / mudguard accent
        ctx.arc(rear[0], rear[1], rear[1] + 5, math.pi * 0.15, math.pi * 0.85)
        ctx.set_source_rgb(*self.accent)
        ctx.set_line_width(4)
        ctx.stroke()

    def _spokes(self, ctx, wx, r):
        ang = -self.wheel_angle
        for k in range(6):
            a = ang + k * math.pi / 6
            ctx.move_to(wx - r * 0.92 * math.cos(a), r - r * 0.92 * math.sin(a))
            ctx.line_to(wx + r * 0.92 * math.cos(a), r + r * 0.92 * math.sin(a))
        ctx.set_source_rgba(0.55, 0.56, 0.6, 0.9)
        ctx.set_line_width(1.4)
        ctx.stroke()
        ctx.arc(wx, r, 4, 0, 2 * math.pi)
        _fill_ink(ctx, (0.7, 0.7, 0.75), 1.5)
        # valve: a visible dot that spins with the wheel
        ctx.arc(wx + r * 0.88 * math.cos(ang), r + r * 0.88 * math.sin(ang), 2.5, 0, 2 * math.pi)
        ctx.set_source_rgb(*self.accent)
        ctx.fill()

    def _front_chassis(self, ctx, now):
        near, _ = self._pedals()
        cx, cy = self.CRANK
        _line(ctx, [(cx, cy), near], (0.4, 0.4, 0.45), 3.5)
        _rrect(ctx, near[0] - 8, near[1] - 3, 16, 6, 2)
        _fill_ink(ctx, (0.3, 0.3, 0.33), 1.5)
        ctx.arc(cx, cy, 4, 0, 2 * math.pi)
        _fill_ink(ctx, (0.75, 0.75, 0.8), 1.5)

    def _shadow(self, ctx):
        ctx.save()
        ctx.translate(self.x, -self.y + 2)
        ctx.scale(self.HALF_LEN * self.scale, 7 * self.scale)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0, 0, 0, 0.18)
        ctx.fill()


class Scooter(Vehicle):
    """Kick scooter: the rider stands on the deck and pushes off the ground with the back foot
    while it rolls (kick rhythm follows the distance)."""

    kind = "scooter"
    WHEELS = ((-42.0, 11.0), (42.0, 11.0))
    SEAT = (-6.0, 18.0)          # feet level (deck top) — the rider stands
    GRIP = (36.0, 104.0)
    HALF_LEN = 55.0
    STIFF, DAMP = 220.0, 16.0

    def ring(self, t):
        return self.honk(t)

    def _honk_event(self, scene):
        scene.event("bell", self.x)

    def _hip_h(self, c, role):
        return 0.0  # the rider stands: character origin = deck top

    def _rider_pose(self, c, P, role, T):
        hipH = c.THIGH + c.SHIN - 5
        P.update(ik=1.0, hipIK=hipH, torso=0.12, head=-0.1)
        hip = (0.0, -hipH)
        front = c.to_local(self.world_point(self.SEAT[0] + 12, self.SEAT[1] + 3))
        # back foot: kicks along the ground while rolling, rests on the deck when idle
        if abs(self.speed) > 20:
            u = (self.distance / 200.0) % 1.0
            if u < 0.5:   # foot on the ground, sliding back
                gx, gy = te.lerp(-6, -62, u / 0.5), 4.0
            else:         # lift and swing forward
                k = (u - 0.5) / 0.5
                gx, gy = te.lerp(-62, -6, k), 4.0 + 26 * math.sin(math.pi * k)
            bw = self.world_point(self.SEAT[0] + gx, 0, body=False)
            back = c.to_local((bw[0], self.y + gy))
        else:
            back = c.to_local(self.world_point(self.SEAT[0] - 14, self.SEAT[1] + 3))
        P["thighF"], P["kneeF"] = te.ik2(hip, front, c.THIGH, c.SHIN)
        P["thighB"], P["kneeB"] = te.ik2(hip, back, c.THIGH, c.SHIN)
        self._arms_to(c, P, self.world_point(*self.GRIP), spread=3.0)
        return 0.0

    def _back_chassis(self, ctx, now):
        col = self.color
        _rrect(ctx, -48, 12, 92, 8, 4)
        _fill_ink(ctx, col, 2.5)
        _line(ctx, [(42, 11), (40, 22), (36, 100)], (0.55, 0.56, 0.62), 4)
        _line(ctx, [(28, 102), (42, 104)], (0.2, 0.2, 0.25), 4)
        _line(ctx, [(-46, 18), (-44, 26)], _shade(col, 0.7), 3)
        for wx, r in self.WHEELS:
            self._wheel(ctx, wx, r, rim=self.accent, tire=(0.2, 0.2, 0.24), lw=2.5)

    def _shadow(self, ctx):
        ctx.save()
        ctx.translate(self.x, -self.y + 2)
        ctx.scale(self.HALF_LEN * self.scale, 6 * self.scale)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(0, 0, 0, 0.18)
        ctx.fill()


class Cart(Vehicle):
    """Wooden farm cart (one big spoked wheel, plank bed, shafts). hitch(puller): pulled by a
    quadruped (shafts + harness at the chest) or a person (both hands on the shaft ends).
    Unhitched, the shafts rest on the ground. Riders sit on the bed (role 'passenger')."""

    kind = "cart"
    WHEELS = ((0.0, 36.0),)
    SEAT = (-18.0, 76.0)
    FOOTREST = (40.0, 50.0)
    HALF_LEN = 100.0
    STIFF, DAMP = 160.0, 10.0

    def __init__(self, x=0.0, y=None, face=1, color="#b07a46", accent="#7a4b2a", scale=1.0, id=None,
                 auto_face=True, load=None):
        super().__init__(x, y, face, color, accent, scale, id, auto_face)
        self.hitches = []     # dicts: puller, t, d, gap
        self.load = load      # None | "hay" | "apples"
        self._hitch_pt = None
        self._creak_d = 0.0
        self._side = None

    def hitch(self, puller, t=0.0, d=None, gap=None):
        self.hitches.append(dict(puller=puller, t=float(t), d=None if d is None else float(d),
                                 gap=None if gap is None else float(gap)))
        return self

    def _active_hitch(self, T):
        for h in self.hitches:
            if h["t"] <= T and (h["d"] is None or T < h["t"] + h["d"]):
                return h
        return None

    def _gap(self, h):
        p = h["puller"]
        if h["gap"] is not None:
            return h["gap"]
        if getattr(p, "style", "toon") == "quadruped":
            sp = p.spec
            return (sp["blen"] * 0.5 + sp["br"] * 0.9) * p.scale + 84 * self.scale
        return 56 * p.scale + 76 * self.scale

    def _target_x(self, T, scene):
        h = self._active_hitch(T)
        if h is None:
            return self.pos_at(T) if self.segs else self.x
        p = h["puller"]
        side = self._side
        if side is None:
            side = 1 if p.x >= self.x else -1
        if abs(p.x - self.x) > 30 and (p.x - self.x) * side < 0 and p.face == -side:
            side = -side  # puller turned round and walked past: the cart swings round
        self._side = side
        return p.x - side * self._gap(h)

    def update(self, dt, scene):
        super().update(dt, scene)
        T = self.time
        h = self._active_hitch(T)
        if h is not None:
            self.face = self._side or self.face
        self._creak_d += abs(self.speed) * dt
        if self._creak_d > 2 * math.pi * self.wheel_r * 0.5:
            self._creak_d = 0.0
            scene.event("creak", self.x, gain=0.5)
        self._hitch_pt = None
        if h is not None:
            p = h["puller"]
            if getattr(p, "style", "toon") == "quadruped":
                sp = p.spec
                P = getattr(p, "dpose", None) or p.pose
                hipH = p._animal_hip(P)
                chest = (p.x + p.face * (sp["blen"] * 0.42) * p.scale, p.y + (hipH + sp["br"] * 0.15) * p.scale)
                self._hitch_pt = chest
            elif getattr(p, "style", "toon") != "bird":
                # a person pulls with both hands behind the back
                P = dict(getattr(p, "dpose", None) or p.pose)
                grip = (p.x - p.face * 34 * p.scale, p.y + 78 * p.scale)
                sk = p._skeleton(P)
                if sk is not None:
                    g = p.to_local(grip)
                    P["armUF"], P["elbowF"] = te.arm_ik(sk["shoulderF"], (g[0] + 3, g[1]), p.UARM, p.LARM)
                    P["armUB"], P["elbowB"] = te.arm_ik(sk["shoulderB"], (g[0] - 3, g[1]), p.UARM, p.LARM)
                    P["torso"] = P.get("torso", 0) + 0.12
                    p.dpose = P
                self._hitch_pt = grip

    def _hip_h(self, c, role):
        return 24.0

    def _rider_pose(self, c, P, role, T):
        hipH = 24.0
        P.update(ik=1.0, hipIK=hipH, torso=-0.08, thighF=1.45, kneeF=1.1, thighB=1.4, kneeB=1.2,
                 armUF=0.35, elbowF=0.4, armUB=-0.3, elbowB=0.3)
        return hipH

    def _shaft_local(self):
        """Shaft start (local, on the bed front) and end (local)."""
        start = (66.0, 62.0)
        if self._hitch_pt is None:
            return start, (150.0, 6.0)
        hx, hy = self._hitch_pt
        # world -> local (inverse of world_point without body motion)
        dx, dy = hx - self.x, hy - self.y
        c, s = math.cos(-self.tilt), math.sin(-self.tilt)
        u, v = dx * c - dy * s, dx * s + dy * c
        return start, (u * self.face / self.scale, v / self.scale)

    def _back(self, ctx, now):
        col, dk = self.color, _shade(self.color, 0.75)
        a, b = self._shaft_local()
        _line(ctx, [(a[0] - 4, a[1] + 6), (b[0] - 4, b[1] + 6)], dk, 6)  # far shaft
        # bed + side boards
        _rrect(ctx, -96, 44, 166, 16, 3)
        _fill_ink(ctx, dk, 3)
        if self.load == "hay":
            _smooth(ctx, [(-92, 70), (-80, 118), (-30, 132), (30, 128), (66, 108), (66, 70)])
            _fill_ink(ctx, (0.93, 0.8, 0.38), 3)
            for k in range(7):
                ctx.move_to(-80 + k * 20, 80 + (k % 3) * 9)
                ctx.line_to(-70 + k * 20, 98 + (k % 2) * 10)
            ctx.set_source_rgba(0.7, 0.55, 0.2, 0.8)
            ctx.set_line_width(2)
            ctx.stroke()
        elif self.load == "apples":
            for k in range(9):
                ctx.arc(-80 + k * 17, 98 + 8 * math.sin(k * 1.7), 10, 0, 2 * math.pi)
                _fill_ink(ctx, (0.9, 0.22, 0.25), 2)

    def _front(self, ctx, now):
        col, dk = self.color, _shade(self.color, 0.75)
        # near side board with planks
        _rrect(ctx, -100, 56, 172, 40, 5)
        _fill_ink(ctx, col, 3.5)
        for yy in (69, 82):
            ctx.move_to(-96, yy)
            ctx.line_to(68, yy)
        for xx in (-60, 0, 44):
            ctx.move_to(xx, 58)
            ctx.line_to(xx, 94)
        ctx.set_source_rgba(*_shade(col, 0.6), 0.9)
        ctx.set_line_width(2)
        ctx.stroke()
        ctx.rectangle(-100, 56, 172, 8)
        ctx.set_source_rgba(*_light(col, 0.3), 0.6)
        ctx.fill()
        _rrect(ctx, -100, 56, 172, 40, 5)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3.5)
        ctx.stroke()
        for xx in (-96, 64):  # iron corner straps
            _rrect(ctx, xx, 54, 8, 44, 2)
            _fill_ink(ctx, (0.4, 0.38, 0.4), 2)
        a, b = self._shaft_local()
        _line(ctx, [a, b], col, 6)  # near shaft over the puller's side
        if self._hitch_pt is not None:
            ctx.arc(b[0], b[1], 6, 0, 2 * math.pi)
            _fill_ink(ctx, self.accent, 2)

    def _front_chassis(self, ctx, now):
        wx, r = self.WHEELS[0]
        self._wheel(ctx, wx, r, rim=_shade(self.color, 0.85), tire=(0.36, 0.25, 0.16), spokes=4,
                    hub=self.accent, lw=3.5)
        ctx.arc(wx, r, r, 0, 2 * math.pi)  # iron tyre rim
        ctx.set_source_rgb(0.3, 0.3, 0.33)
        ctx.set_line_width(4)
        ctx.stroke()


VEHICLES = {"car": Car, "bicycle": Bicycle, "bike": Bicycle, "cart": Cart, "scooter": Scooter}


# ---------------------------------------------------------------- scenery
class Sidewalk:
    """Raised back sidewalk strip (world y 0..depth above the ground line, drawn behind everything
    else in the extras) with a kerb edge — where a Crowd stands, behind the street."""

    layer = -20

    def __init__(self, depth=64.0, color="#cfcac2", kerb="#a49d93", x_range=(-3000, 3000), tile=150.0,
                 id=None):
        self.depth, self.color, self.kerb = float(depth), _rgb(color), _rgb(kerb)
        self.x_range, self.tile, self.id = tuple(x_range), float(tile), id

    def update(self, dt, scene):
        pass

    def draw(self, ctx, now):
        a, b = self.x_range
        ctx.rectangle(a, -self.depth, b - a, self.depth)
        ctx.set_source_rgb(*self.color)
        ctx.fill()
        x = math.floor(a / self.tile) * self.tile
        ctx.set_source_rgba(*_shade(self.color, 0.82), 1)
        ctx.set_line_width(2)
        while x < b:
            ctx.move_to(x, -self.depth)
            ctx.line_to(x - 18, -8)
            x += self.tile
        ctx.stroke()
        ctx.rectangle(a, -10, b - a, 10)
        ctx.set_source_rgb(*self.kerb)
        ctx.fill()
        ctx.move_to(a, -self.depth)
        ctx.line_to(b, -self.depth)
        ctx.move_to(a, 0)
        ctx.line_to(b, 0)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()


# ---------------------------------------------------------------- crowds (#24)
REACTIONS = ("cheer", "gasp", "laugh", "clap", "wave", "look_at", "flee", "idle")
REACTION_D = dict(cheer=2.0, gasp=1.4, laugh=2.0, clap=2.2, wave=1.8, look_at=3.0, flee=None, idle=1.0)
REACTION_SFX = dict(cheer="crowd_cheer", gasp="gasp", laugh="laugh", clap="applause")
STYLES = ("adult", "kid", "elder")
SHIRTS = ("#e76f51", "#2a9d8f", "#e9c46a", "#457b9d", "#f4a261", "#8e7dbe", "#ef476f", "#06d6a0",
          "#118ab2", "#ffd166", "#9c6644", "#6d597a")
PANTS = ("#3d5a80", "#2b2d42", "#5c4d3c", "#4a4e69", "#335c67", "#6b705c")
SKINS = ("#ffd2a8", "#f1c27d", "#e0ac69", "#c68642", "#8d5524", "#ffdbac")
HAIRS = ("#2b1d14", "#5a3825", "#a0522d", "#e1b382", "#1b1b1b", "#7b3f00")
HATS = (None, None, None, "cap", "beanie")


class Crowd:
    """Cheap background extras (lightweight figure renderer, not full rigs): they idle, wander
    and react to cues with seeded per-member timing. Drawn behind the main characters (layer -10),
    far rows smaller, higher and fogged toward the background.

    n: members; x_range: (x0, x1); depth_rows: rows (0 = nearest); seed: layout / timing;
    style_mix: {"adult": w, "kid": w, "elder": w}; behaviour: idle | wander | mixed;
    y: feet height of the nearest row (world, above the ground line); scale: nearest-row scale;
    fog: fog amount per row; fog_color: hex; spread: max per-member reaction delay (s).
    Pass scene to add it right away."""

    layer = -10

    def __init__(self, scene=None, n=20, x_range=(-600, 600), depth_rows=2, seed=1, style_mix=None,
                 behaviour="idle", y=14.0, scale=0.8, fog=0.22, fog_color="#dfeaf5", spread=0.45,
                 row_gap=22.0, id=None, fast=False):
        if behaviour not in ("idle", "wander", "mixed"):
            raise ValueError(f"unknown crowd behaviour {behaviour!r}; valid: idle, wander, mixed")
        mix = dict(style_mix or {"adult": 0.65, "kid": 0.2, "elder": 0.15})
        bad = set(mix) - set(STYLES)
        if bad:
            raise ValueError(f"unknown crowd style(s) {sorted(bad)}; valid: {list(STYLES)}")
        self.n, self.x_range, self.rows = int(n), (float(x_range[0]), float(x_range[1])), max(1, int(depth_rows))
        self.seed, self.behaviour, self.spread = int(seed), behaviour, float(spread)
        self.base_y, self.base_scale, self.fog, self.row_gap = float(y), float(scale), float(fog), float(row_gap)
        self.fog_color = _rgb(fog_color)
        self.id = id
        self.fast = bool(fast)  # cheaper antialiasing for very big crowds
        self.reactions = []   # dicts: t, kind, d, target, dir, delays, amps
        self.time = 0.0
        self._fired = set()
        rng = random.Random(self.seed)
        names, weights = zip(*sorted(mix.items()))
        self.members = []
        per_row = [self.n // self.rows + (1 if r < self.n % self.rows else 0) for r in range(self.rows)]
        x0, x1 = self.x_range
        for row in range(self.rows):
            k = per_row[row]
            for j in range(k):
                style = rng.choices(names, weights)[0]
                span = (x1 - x0)
                cell = span / max(1, k)
                # far rows offset half a cell: their faces show in the gaps of the near row
                x = x0 + cell * (j + 0.5 + (0.5 if row % 2 else 0.0)) + rng.uniform(-0.18, 0.18) * cell
                if row % 2 and x > x1:
                    x -= span
                fogk = min(0.85, self.fog * (row + 0.6))
                fcol = lambda c: _mix(_rgb(c), self.fog_color, fogk)  # noqa: E731 (local only)
                h = {"adult": rng.uniform(0.94, 1.06), "kid": rng.uniform(0.66, 0.74),
                     "elder": rng.uniform(0.9, 0.98)}[style]
                hair = "#d9d9d9" if style == "elder" and rng.random() < 0.8 else rng.choice(HAIRS)
                wander = behaviour == "wander" or (behaviour == "mixed" and rng.random() < 0.35)
                m = dict(
                    i=len(self.members), row=row, style=style, x=x,
                    s=self.base_scale * (1 - 0.13 * row) * h, wide=rng.uniform(0.9, 1.15),
                    shirt=fcol(rng.choice(SHIRTS)), pants=fcol(rng.choice(PANTS)),
                    skin=fcol(rng.choice(SKINS)), hair=fcol(hair), ink=_mix(INK, self.fog_color, fogk * 0.8),
                    hat=rng.choice(HATS) if style != "kid" else rng.choice((None, "cap")),
                    hatc=fcol(rng.choice(SHIRTS)),
                    face=rng.choice((-1, 1)), ph=rng.uniform(0, 2 * math.pi),
                    hunch=0.14 if style == "elder" else 0.0,
                    wander=wander, wa=x - rng.uniform(35, 90), wb=x + rng.uniform(35, 90),
                    wv=rng.uniform(35, 60) * (0.8 if style == "elder" else 1.0),
                    glance=rng.uniform(0, 100),
                )
                self.members.append(m)
        # draw order: far rows first, then by x
        self.order = sorted(range(len(self.members)), key=lambda i: (-self.members[i]["row"], self.members[i]["x"]))
        self.state = [None] * len(self.members)
        if scene is not None:
            add(scene, self, id)

    # ---------------------------------------------------------------- cues
    def react(self, t, kind, d=None, target=None, dir=None, spread=None, members=None):
        """React from time t: cheer | gasp | laugh | clap | wave | look_at (target x or object) |
        flee (dir +1/-1, permanent) | idle (cancel). Each member starts after its own seeded delay
        (0..spread s). members: optional list of member indices (default all)."""
        if kind not in REACTIONS:
            raise ValueError(f"unknown crowd reaction {kind!r}; valid: {list(REACTIONS)}")
        if kind == "look_at" and target is None:
            raise ValueError("look_at needs a target (x or an object with .x)")
        sp = self.spread if spread is None else float(spread)
        idx = len(self.reactions)
        rng = random.Random(self.seed * 7919 + idx * 104729 + 13)
        delays = [rng.uniform(0, sp) for _ in self.members]
        amps = [rng.uniform(0.75, 1.1) for _ in self.members]
        dd = REACTION_D[kind] if d is None else d
        if isinstance(target, (int, float)):
            target = Anchor(float(target), 0.0)
        if kind == "flee" and dir is None:
            dir = 1
        self.reactions.append(dict(t=float(t), kind=kind, d=None if dd is None else float(dd), target=target,
                                   dir=None if dir is None else (1 if dir >= 0 else -1), delays=delays,
                                   amps=amps, members=None if members is None else set(members)))
        return self

    # ---------------------------------------------------------------- state (pure functions of t)
    def _frozen(self, i, t):
        """Seconds of wandering skipped because member i was reacting (not walking)."""
        tot = 0.0
        for r in self.reactions:
            if r["kind"] in ("look_at",) or (r["members"] is not None and i not in r["members"]):
                continue
            s = r["t"] + r["delays"][i]
            if s >= t:
                continue
            e = t if r["d"] is None else min(t, s + r["d"])
            tot += max(0.0, e - s)
        return tot

    def _wander_x(self, m, t):
        if not m["wander"]:
            return m["x"], m["face"], 0.0, False
        L = m["wb"] - m["wa"]
        v = m["wv"]
        per = 2 * L / v + 2.0  # walk there, pause 1 s, walk back, pause 1 s
        u = (t + m["ph"] * 3) % per
        tw = L / v
        if u < tw:
            return m["wa"] + v * u, 1, v * u, True
        if u < tw + 1:
            return m["wb"], 1, L, False
        if u < 2 * tw + 1:
            return m["wb"] - v * (u - tw - 1), -1, L + v * (u - tw - 1), True
        return m["wa"], -1, 2 * L, False

    def _target_x(self, tgt):
        return float(getattr(tgt, "x", 0.0))

    def member_state(self, i, t):
        """Current state of member i at time t: dict(x, y, face, kind, w, walking, ...)."""
        m = self.members[i]
        tw = t - self._frozen(i, t) if m["wander"] else t
        x, face, dist, walking = self._wander_x(m, tw)
        kind, w, rt, look, flee = None, 0.0, 0.0, None, None
        for r in self.reactions:
            if r["members"] is not None and i not in r["members"]:
                continue
            s = r["t"] + r["delays"][i]
            if t < s:
                continue
            if r["kind"] == "flee":
                flee = (s, r["dir"])
                continue
            e = None if r["d"] is None else s + r["d"]
            if e is not None and t >= e:
                continue
            if r["kind"] == "look_at":
                look = r
                continue
            if r["kind"] == "idle":
                kind = None
                continue
            kind, rt = r["kind"], t - s
            w = min(1.0, rt / 0.15, 1.0 if e is None else (e - t) / 0.3) * r["amps"][i]
        if look is not None:
            tx = self._target_x(look["target"])
            face = 1 if tx >= x else -1
        if flee is not None:
            s, dr = flee
            a = t - s
            run = 260 * max(0.0, a - 0.15) + 0.0
            x0f = x
            x = x0f + dr * run
            face, walking, dist, kind, w, rt = dr, a > 0.15, run, "flee", 1.0, a
        if kind in (None, "look_at"):
            w = 0.0
        return dict(x=x, y=self.base_y + self.row_gap * m["row"], face=face, kind=kind, w=max(0.0, w),
                    rt=rt, walking=walking, dist=dist, look=look is not None)

    def update(self, dt, scene):
        T = scene.time + dt
        self.time = T
        cx = sum(self.x_range) / 2
        for k, r in enumerate(self.reactions):
            if k not in self._fired and T >= r["t"]:
                self._fired.add(k)
                snd = REACTION_SFX.get(r["kind"])
                if snd:
                    scene.event(snd, cx, gain=min(1.0, 0.35 + self.n / 40))
                elif r["kind"] == "flee":
                    scene.event("gasp", cx, gain=0.6)
        has_ground = getattr(scene, "ground_at", None) is not None
        st = []
        for i in range(len(self.members)):
            s = self.member_state(i, T)
            if has_ground:
                s["y"] += _ground(scene, s["x"])
            st.append(s)
        self.state = st

    # ---------------------------------------------------------------- drawing
    def draw(self, ctx, now):
        if not self.state or self.state[0] is None:
            return
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_tolerance(0.6)  # small background figures: coarser curve flattening
        if self.fast:
            ctx.set_antialias(cairo.ANTIALIAS_FAST)
        for i in self.order:
            self._figure(ctx, self.members[i], self.state[i], now)
        ctx.restore()

    def _pose(self, m, s, now):
        """Arm/leg angles (0 = down, + = forward), bob, lean, mouth, eyes for a member."""
        t = now + m["ph"]
        kind, w, rt = s["kind"], s["w"], s["rt"]
        sway = math.sin(t * 1.3) * 0.05
        aF, eF, aB, eB = 0.12 + sway, 0.25, -0.1 - sway, 0.25
        legF = legB = 0.0
        bob, lean, mouth, eyes = 0.0, m["hunch"] + 0.02 * math.sin(t * 0.9), "smile", "dot"
        if s["walking"]:
            q = s["dist"] / 40.0 * math.pi
            run = kind == "flee"
            A = 0.75 if run else 0.42
            legF, legB = A * math.sin(q), -A * math.sin(q)
            aF, aB = -A * 1.1 * math.sin(q), A * 1.1 * math.sin(q)
            eF = eB = 1.4 if run else 0.3
            bob = (5 if run else 2.5) * abs(math.cos(q))
            lean = m["hunch"] + (0.3 if run else 0.06)
        if kind == "flee":
            mouth, eyes = "O", "wide"
            if not s["walking"]:  # first startle
                aF, eF, aB, eB = 2.6, 0.4, 2.4, 0.4
            return aF, eF, aB, eB, legF, legB, bob, lean, mouth, eyes
        if kind and w > 0:
            if kind == "cheer":
                wv = math.sin(rt * 14 + m["ph"])
                tgt = (2.8 + 0.15 * wv, 0.2, 2.6 - 0.15 * wv, 0.25)
                bob2, lean2, mouth, eyes = 12 * abs(math.sin(rt * 7 + m["ph"])), -0.08, "open", "happy"
            elif kind == "clap":
                ph = math.cos(rt * 4.5 * 2 * math.pi + m["ph"])
                o = 0.22 * (1 - ph) / 2
                tgt = (1.05 + o, 1.0 - o, 1.05 - o, 1.05 + o)
                bob2, lean2, mouth, eyes = 0.0, 0.02, "smile", "happy"
            elif kind == "wave":
                tgt = (2.7, 0.5 + 0.45 * math.sin(rt * 13), aB, eB)
                bob2, lean2, mouth, eyes = 0.0, 0.0, "smile", "dot"
            elif kind == "gasp":
                tgt = (0.75, 2.45, 0.7, 2.4)  # hands to the cheeks
                jump = 6 * math.sin(math.pi * min(1.0, rt / 0.25))
                bob2, lean2, mouth, eyes = max(0.0, jump), -0.16, "O", "wide"
            elif kind == "laugh":
                k = math.sin(rt * 16)
                tgt = (0.55, 1.9, 0.5, 1.8)  # hands on the belly
                bob2, lean2, mouth, eyes = 2.5 * abs(k), -0.14 + 0.06 * k, "laugh", "happy"
            else:
                tgt = (aF, eF, aB, eB)
                bob2, lean2 = 0.0, lean
            w = min(1.0, w)
            aF, eF, aB, eB = (te.lerp(a, b, w) for a, b in zip((aF, eF, aB, eB), tgt))
            bob, lean = te.lerp(bob, bob2, w), te.lerp(lean, lean2, w)
        elif s.get("look"):
            eyes = "dot"
        return aF, eF, aB, eB, legF, legB, bob, lean, mouth, eyes

    def _figure(self, ctx, m, s, now):
        aF, eF, aB, eB, legF, legB, bob, lean, mouth, eyes = self._pose(m, s, now)
        sc = m["s"]
        ink, shirt, pants, skin, hair = m["ink"], m["shirt"], m["pants"], m["skin"], m["hair"]
        ctx.save()
        ctx.translate(s["x"], -(s["y"] + bob * sc))
        ctx.scale(s["face"] * sc, sc)
        # local y down, feet at 0
        hip = (0.0, -62.0)
        nl, sl = math.sin(lean), math.cos(lean)
        sh = (hip[0] + 48 * nl, hip[1] - 48 * sl)
        neck = (hip[0] + 56 * nl, hip[1] - 56 * sl)
        hc = (neck[0] + 22 * nl + 2, neck[1] - 20)
        W = 13.0 * m["wide"]

        def limb(o, a, l1, e, l2):
            j = (o[0] + l1 * math.sin(a), o[1] + l1 * math.cos(a))
            return j, (j[0] + l2 * math.sin(a + e), j[1] + l2 * math.cos(a + e))

        def stroke(pts, w, col):
            ctx.move_to(*pts[0])
            for p in pts[1:]:
                ctx.line_to(*p)
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(w + 4.5)
            ctx.stroke_preserve()
            ctx.set_source_rgb(*col)
            ctx.set_line_width(w)
            ctx.stroke()

        # back arm + legs: one ink pass (shoes are chunky ink caps), then the colours
        ja, ha = limb(sh, aB, 24, eB, 23)
        legs = []
        for a in (legB, legF):
            k = max(0.0, -a) * 0.6 + 0.08
            legs.append(limb(hip, a, 32, -k * 1.6 if a > 0 else k, 31))
        ctx.move_to(*sh)
        ctx.line_to(*ja)
        ctx.line_to(*ha)
        for j, f in legs:
            ctx.move_to(*hip)
            ctx.line_to(*j)
            ctx.line_to(*f)
            ctx.line_to(f[0] + 7, f[1])
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(13.5)
        ctx.stroke()
        ctx.move_to(*sh)
        ctx.line_to(*ja)
        ctx.line_to(*ha)
        ctx.set_source_rgb(*_shade(shirt, 0.82))
        ctx.set_line_width(8)
        ctx.stroke()
        for (j, f), c in zip(legs, (_shade(pants, 0.82), pants)):
            ctx.move_to(*hip)
            ctx.line_to(*j)
            ctx.line_to(f[0], f[1] - 4)
            ctx.set_source_rgb(*c)
            ctx.set_line_width(9)
            ctx.stroke()
        # torso (rounded capsule)
        ctx.move_to(hip[0] - W * 0.9, hip[1] + 6)
        ctx.line_to(sh[0] - W, sh[1] + 4)
        ctx.curve_to(sh[0] - W, sh[1] - 10, sh[0] + W, sh[1] - 10, sh[0] + W, sh[1] + 4)
        ctx.line_to(hip[0] + W * 0.9, hip[1] + 6)
        ctx.close_path()
        ctx.set_source_rgb(*shirt)
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(3)
        ctx.stroke()
        # head
        r = 20.0
        ctx.arc(hc[0], hc[1], r, 0, 2 * math.pi)
        ctx.set_source_rgb(*skin)
        ctx.fill_preserve()
        ctx.set_source_rgb(*ink)
        ctx.set_line_width(3)
        ctx.stroke()
        hat = m["hat"]
        if hat == "cap":
            ctx.arc(hc[0], hc[1] - 2, r + 1, math.pi, 2 * math.pi)
            ctx.close_path()
            ctx.set_source_rgb(*m["hatc"])
            ctx.fill_preserve()
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(2.5)
            ctx.stroke()
            ctx.move_to(hc[0] + r * 0.6, hc[1] - 3)
            ctx.line_to(hc[0] + r * 1.45, hc[1] - 1)
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(5)
            ctx.stroke()
        elif hat == "beanie":
            ctx.arc(hc[0], hc[1] - 4, r + 1, math.pi * 1.02, math.pi * 1.98)
            ctx.close_path()
            ctx.set_source_rgb(*m["hatc"])
            ctx.fill_preserve()
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(2.5)
            ctx.stroke()
        else:  # hair cap at the back of the head
            ctx.arc(hc[0] - 3, hc[1] - 3, r * 0.98, math.pi * 0.72, math.pi * 1.82)
            ctx.close_path()
            ctx.set_source_rgb(*hair)
            ctx.fill()
        # face (profile-ish, toward +x)
        ex, ey = hc[0] + 8, hc[1] - 3
        if eyes == "wide":
            for dx in (0, 8):
                ctx.arc(ex + dx, ey, 4.2, 0, 2 * math.pi)
                ctx.set_source_rgb(1, 1, 1)
                ctx.fill_preserve()
                ctx.set_source_rgb(*ink)
                ctx.set_line_width(1.5)
                ctx.stroke()
                ctx.arc(ex + dx + 0.8, ey, 1.8, 0, 2 * math.pi)
                ctx.fill()
        elif eyes == "happy":
            ctx.set_source_rgb(*ink)
            ctx.set_line_width(2.2)
            for dx in (0, 8):
                ctx.arc(ex + dx, ey + 1.5, 3, math.pi * 1.1, math.pi * 1.9)
                ctx.stroke()
        else:
            look = 1.0 if s.get("look") else 0.0
            ctx.set_source_rgb(*ink)
            for dx in (0, 8):
                ctx.new_sub_path()
                ctx.arc(ex + dx + look, ey, 2.4, 0, 2 * math.pi)
            ctx.fill()
        mx, my = hc[0] + 11, hc[1] + 9
        ctx.set_source_rgb(*ink)
        if mouth == "smile":
            ctx.set_line_width(2.2)
            ctx.arc(mx, my - 3, 5, math.pi * 0.2, math.pi * 0.8)
            ctx.stroke()
        elif mouth == "O":
            ctx.arc(mx, my, 3.6, 0, 2 * math.pi)
            ctx.fill()
        else:  # open / laugh
            ctx.move_to(mx - 6, my - 2)
            ctx.line_to(mx + 6, my - 2)
            ctx.arc(mx, my - 2, 6 if mouth == "laugh" else 5, 0, math.pi)
            ctx.close_path()
            ctx.fill_preserve()
            ctx.set_source_rgb(0.95, 0.45, 0.5)
            ctx.arc(mx, my + 1.5, 2.6, 0, math.pi)
            ctx.fill()
        # front arm + hand
        j, hnd = limb(sh, aF, 24, eF, 23)
        stroke((sh, j, hnd), 8, shirt)
        ctx.arc(hnd[0], hnd[1], 4.5, 0, 2 * math.pi)
        ctx.set_source_rgb(*skin)
        ctx.fill()
        ctx.restore()


# ---------------------------------------------------------------- curve paths (#8)
PATH_STYLES = ("none", "dotted", "dashed", "road", "footprints", "trail", "debug")


def _catmull(p0, p1, p2, p3, n, alpha=0.5):
    """Centripetal Catmull-Rom samples between p1 and p2 (n points, p1 included, p2 excluded)."""
    def tj(ti, a, b):
        return ti + max(float(np.linalg.norm(b - a)), 1e-4) ** alpha
    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    ts = np.linspace(t1, t2, n, endpoint=False)[:, None]
    a1 = (t1 - ts) / (t1 - t0) * p0 + (ts - t0) / (t1 - t0) * p1
    a2 = (t2 - ts) / (t2 - t1) * p1 + (ts - t1) / (t2 - t1) * p2
    a3 = (t3 - ts) / (t3 - t2) * p2 + (ts - t2) / (t3 - t2) * p3
    b1 = (t2 - ts) / (t2 - t0) * a1 + (ts - t0) / (t2 - t0) * a2
    b2 = (t3 - ts) / (t3 - t1) * a2 + (ts - t1) / (t3 - t1) * a3
    return (t2 - ts) / (t2 - t1) * b1 + (ts - t1) / (t2 - t1) * b2


def _parse_point(p, k):
    """[x] | [x, h] | [x, h, depth] | {"x", "h"|"y", "depth"|"z"} -> (x, h, depth)."""
    if isinstance(p, dict):
        bad = set(p) - {"x", "h", "y", "depth", "z"}
        if bad or "x" not in p:
            raise ValueError(f"path point #{k}: expected keys x, h (or y), depth (or z); got {sorted(p)}")
        return (float(p["x"]), float(p.get("h", p.get("y", 0.0))), float(p.get("depth", p.get("z", 0.0))))
    if isinstance(p, (int, float)):
        return (float(p), 0.0, 0.0)
    try:
        v = [float(a) for a in p]
    except (TypeError, ValueError):
        raise ValueError(f"path point #{k} must be [x], [x, h], [x, h, depth] or a dict, got {p!r}") from None
    if not 1 <= len(v) <= 3:
        raise ValueError(f"path point #{k} must have 1-3 numbers ([x, h, depth]), got {len(v)}")
    return tuple(v + [0.0] * (3 - len(v)))


class Path:
    """A 2D curve through control points (#8) for characters, vehicles and flyers to follow.

    points: [x] | [x, h] | [x, h, depth] (or dicts). h = height above the terrain (relative=True,
    default: combined with Scene.ground_at) or absolute world y (relative=False). depth = pseudo-3D
    depth on the ground strip in px: + = nearer the camera (lower on screen, drawn larger by
    1 + depth * persp) — lets roads wind toward / away from the viewer or loop round a ring.
    closed: loop back to the first point; smooth: centripetal Catmull-Rom (False = polyline).
    The curve is arc-length parameterised: point_at(s) moves at uniform speed in s.
    style: none | dotted | dashed | road | footprints | trail | debug (visible look, drawn behind
    the characters); reveal=True draws only the part followers have already covered."""

    layer = -25
    SAMPLES = 28   # dense samples per control segment

    def __init__(self, points, closed=False, smooth=True, style="none", color=None, width=None,
                 spacing=None, reveal=None, persp=0.0016, relative=True, supports=True, id=None):
        pts = [_parse_point(p, k) for k, p in enumerate(points or [])]
        if len(pts) < 2:
            raise ValueError("a path needs at least 2 points")
        if style is None:
            style = "none"
        if style not in PATH_STYLES:
            raise ValueError(f"unknown path style {style!r}; valid: {list(PATH_STYLES)}")
        self.ctrl = np.array(pts, dtype=np.float64)
        self.closed, self.smooth, self.style = bool(closed), bool(smooth), style
        self.color = _rgb(color, {"road": "#5b5f6b", "footprints": "#6b4f3a", "trail": "#ffffff",
                                  "dotted": "#ffffff", "dashed": "#ffffff", "debug": "#e63946"}.get(style, "#ffffff"))
        self.width = float(width if width is not None else {"road": 64.0, "footprints": 7.0}.get(style, 6.0))
        self.spacing = float(spacing if spacing is not None else {"footprints": 34.0, "dashed": 30.0}.get(style, 24.0))
        self.reveal = bool(reveal if reveal is not None else style in ("footprints", "trail"))
        self.persp, self.relative, self.supports = float(persp), bool(relative), bool(supports)
        self.id = id
        self.progress = 0.0          # furthest arc length covered by a follower (for reveal)
        self._followers = []         # characters currently placed by this path (not pickled)
        self._terrain = None
        self._world = None           # cached (x, y, k) samples in world space for drawing
        self._build()

    # ---------------------------------------------------------------- geometry
    def _build(self):
        P = self.ctrl
        n = len(P)
        if self.closed and np.linalg.norm(P[0] - P[-1]) < 1e-6:
            P = P[:-1]
            n = len(P)
        if not self.smooth or n == 2 and not self.closed:
            seq = np.vstack([P, P[:1]]) if self.closed else P
            dense = []
            for a, b in zip(seq[:-1], seq[1:]):
                u = np.linspace(0, 1, self.SAMPLES, endpoint=False)[:, None]
                dense.append(a + (b - a) * u)
            dense.append(seq[-1:])
            D = np.vstack(dense)
        else:
            if self.closed:
                ext = np.vstack([P[-1:], P, P[:2]])
                segs = n
            else:
                ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
                segs = n - 1
            dense = [_catmull(ext[i], ext[i + 1], ext[i + 2], ext[i + 3], self.SAMPLES) for i in range(segs)]
            dense.append((P[0] if self.closed else P[-1])[None, :])
            D = np.vstack(dense)
        seg = np.linalg.norm(np.diff(D, axis=0), axis=1)
        self._dense = D
        self._cum = np.concatenate([[0.0], np.cumsum(seg)])
        self.length = float(self._cum[-1])
        if self.length <= 1e-6:
            raise ValueError("path has zero length (all points equal)")

    def __getstate__(self):
        d = self.__dict__.copy()
        d["_followers"] = []
        return d

    def _wrap_s(self, s):
        if self.closed:
            return s % self.length
        return min(max(s, 0.0), self.length)

    def local_at(self, s):
        """(x, h, depth) at arc length s (wraps on closed paths, clamps on open ones)."""
        s = self._wrap_s(float(s))
        c = self._cum
        return tuple(float(np.interp(s, c, self._dense[:, j])) for j in range(3))

    def point_at(self, s):
        """(x, h) at arc length s — h relative to the terrain (see world_at for world y)."""
        x, h, _ = self.local_at(s)
        return (x, h)

    def at(self, u):
        """Point at normalised position u in 0..1 (uniform in arc length)."""
        return self.point_at(u * self.length)

    def tangent_at(self, s, eps=2.0):
        """Unit (dx, dh, ddepth) direction of travel at s."""
        a = np.array(self.local_at(s - eps if (self.closed or s - eps >= 0) else 0.0))
        b = np.array(self.local_at(s + eps if (self.closed or s + eps <= self.length) else self.length))
        d = b - a
        n = float(np.linalg.norm(d)) or 1.0
        return tuple(float(v) for v in d / n)

    def sample(self, n):
        """n points uniformly spaced in arc length: list of (x, h, depth)."""
        top = self.length if not self.closed else self.length * (1 - 1.0 / n)
        return [self.local_at(s) for s in np.linspace(0, top, n)]

    def nearest_s(self, x, h=None):
        """Arc length of the dense sample nearest to (x, h) (x only when h is None)."""
        D = self._dense
        d = (D[:, 0] - x) ** 2 + (0 if h is None else (D[:, 1] - h) ** 2)
        return float(self._cum[int(np.argmin(d))])

    def ground(self, x, scene=None):
        if not self.relative:
            return 0.0
        if scene is not None:
            return _ground(scene, x)
        T = self._terrain
        return T.at(x) if T is not None else 0.0

    def world_at(self, s, scene=None):
        """World placement at s: (x, y, k) — y includes terrain, height and depth offset; k is the
        pseudo-perspective scale factor for depth."""
        x, h, dp = self.local_at(s)
        return (x, self.ground(x, scene) + h - dp, 1.0 + dp * self.persp)

    def surface_y(self, s, scene=None):
        """World y of the path surface ignoring depth (used for vehicle tilt on slopes)."""
        x, h, _ = self.local_at(s)
        return self.ground(x, scene) + h

    # ---------------------------------------------------------------- scene hooks
    def update(self, dt, scene):
        T = getattr(scene, "terrain", None)
        if T is not self._terrain:
            self._terrain = T
            self._world = None
        if self._world is None:
            self._cache_world(scene)
        live = []
        for c, off in self._followers:   # followers stand on the path: shadows under their feet
            if off is None:              # active follower (FollowPath sets c._path_off live)
                off = getattr(c, "_path_off", 0.0)
            c.ground_y = _ground(scene, c.x) + off if self.relative else off
            live.append((c, None if getattr(c, "_path_live", None) is self else off))
        self._followers = live
        chars = getattr(scene, "characters", None)
        if chars and any(getattr(c, "_path_depth", 0.0) for c in chars):
            chars.sort(key=lambda c: getattr(c, "_path_depth", 0.0))   # far first (stable)

    def _cache_world(self, scene=None):
        n = max(64, int(self.length / 4))
        ss = np.linspace(0, self.length, n)
        self._world = np.array([self.world_at(s, scene) for s in ss] if scene is not None else
                               [self.world_at(s) for s in ss])
        self._world_s = ss

    def _attach(self, c, scene):
        if scene is not None and self not in getattr(scene, "extras", ()):
            add(scene, self, self.id)
        for e in getattr(scene, "extras", ()) if scene is not None else ():
            if isinstance(e, Path) and e is not self:
                e._followers = [(cc, o) for cc, o in e._followers if cc is not c]
        self._followers = [(cc, o) for cc, o in self._followers if cc is not c] + [(c, None)]
        c._path_live = self

    def _detach(self, c, off):
        c._path_live = None
        if abs(off) < 1e-6:   # back on the plain ground: nothing to keep fixing
            self._followers = [(cc, o) for cc, o in self._followers if cc is not c]
        else:                 # parked on a raised / deep part: keep its shadow there
            self._followers = [(cc, (off if cc is c else o)) for cc, o in self._followers]

    # ---------------------------------------------------------------- drawing
    def _pts_until(self, smax):
        if self._world is None:
            self._cache_world()
        W, S = self._world, self._world_s
        if smax >= self.length - 1e-6:
            return W
        i = int(np.searchsorted(S, smax))
        return W[:max(1, i)]

    def draw(self, ctx, now):
        if self.style == "none":
            return
        smax = self.progress if self.reveal else self.length
        if smax <= 0:
            return
        W = self._pts_until(smax)
        if len(W) < 2:
            return
        ctx.save()
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        getattr(self, "_draw_" + self.style)(ctx, W, smax, now)
        ctx.restore()

    def _poly(self, ctx, W):
        ctx.new_path()
        ctx.move_to(W[0][0], -W[0][1])
        for x, y, _ in W[1:]:
            ctx.line_to(x, -y)

    def _along(self, smax, step):
        s = step * 0.5
        while s <= smax:
            yield s
            s += step

    def _draw_dotted(self, ctx, W, smax, now, dash=False):
        col = self.color
        for s in self._along(smax, self.spacing):
            x, y, k = self.world_at(s)
            r = self.width * 0.5 * k
            if dash:
                tx, th, td = self.tangent_at(s)
                ang = math.atan2(-(th - td), tx)
                ctx.save()
                ctx.translate(x, -y)
                ctx.rotate(ang)
                _rrect(ctx, -self.spacing * 0.3 * k, -r, self.spacing * 0.6 * k, 2 * r, r)
                ctx.restore()
            else:
                ctx.new_path()
                ctx.arc(x, -y, r, 0, 2 * math.pi)
            _fill_ink(ctx, col, 2.0, alpha=0.95)

    def _draw_dashed(self, ctx, W, smax, now):
        self._draw_dotted(ctx, W, smax, now, dash=True)

    def _draw_trail(self, ctx, W, smax, now):
        self._draw_dotted(ctx, W, smax, now)

    def _draw_debug(self, ctx, W, smax, now):
        self._poly(ctx, W)
        ctx.set_source_rgba(*self.color, 0.9)
        ctx.set_line_width(3)
        ctx.stroke()
        for x, h, dp in self.ctrl:
            y = self.ground(x) + h - dp
            ctx.new_path()
            ctx.arc(x, -y, 7, 0, 2 * math.pi)
            _fill_ink(ctx, (1, 1, 1), 2.5)
        for s in self._along(self.length, 120):
            x, y, _ = self.world_at(s)
            tx, th, td = self.tangent_at(s)
            a = math.atan2(-(th - td), tx)
            ctx.save()
            ctx.translate(x, -y)
            ctx.rotate(a)
            ctx.move_to(-8, -6)
            ctx.line_to(4, 0)
            ctx.line_to(-8, 6)
            ctx.set_source_rgba(*self.color, 0.9)
            ctx.set_line_width(3)
            ctx.stroke()
            ctx.restore()

    def _draw_road(self, ctx, W, smax, now):
        col = self.color
        # raised parts (bridges): posts down to the ground first
        if self.supports:
            for s in self._along(smax, 140):
                x, h, dp = self.local_at(s)
                if h > 24:
                    g = self.ground(x) - dp
                    y = g + h
                    k = 1 + dp * self.persp
                    w = 14 * k
                    ctx.rectangle(x - w / 2, -y + self.width * 0.25 * k, w, max(0.0, y - g - self.width * 0.25 * k))
                    _fill_ink(ctx, _shade(col, 1.25), 2.5)
        # band: ink edge, asphalt, lighter top lip, dashed centre line (per-segment widths for depth)
        for pass_, (extra, c) in enumerate(((7.0, INK), (0.0, col))):
            for i in range(len(W) - 1):
                (x0, y0, k0), (x1, y1, k1) = W[i], W[i + 1]
                ctx.new_path()
                ctx.move_to(x0, -y0)
                ctx.line_to(x1, -y1)
                ctx.set_source_rgb(*c)
                ctx.set_line_width(self.width * 0.5 * (k0 + k1) + extra)
                ctx.stroke()
        self._poly(ctx, W)
        ctx.set_source_rgba(1, 0.86, 0.35, 0.95)
        ctx.set_dash([18, 16])
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.set_dash([])

    def _draw_footprints(self, ctx, W, smax, now):
        col = self.color
        for i, s in enumerate(self._along(smax, self.spacing)):
            x, y, k = self.world_at(s)
            tx, th, td = self.tangent_at(s)
            side = 1 if i % 2 else -1
            ang = math.atan2(-(th - td), tx)
            age = (smax - s) / max(1.0, self.spacing * 30)
            a = max(0.25, 0.75 - age * 0.5)
            ctx.save()
            ctx.translate(x, -y + side * 4 * k)
            ctx.rotate(ang)
            ctx.scale(self.width * 1.3 * k, self.width * 0.6 * k)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*col, a)
            ctx.fill()


class _Travel:
    """Pure function of elapsed time -> arc length along a path (trapezoid speed profile), with
    once / loop / ping-pong modes. Shared by FollowPath, Vehicle.follow and Flyer.fly."""

    def __init__(self, path, speed, start=0.0, end=None, loop=False, pingpong=False, laps=None, d=None,
                 reverse=False, ramp=0.25, ramp_out=None):
        if speed is None or speed <= 0:
            raise ValueError("path speed must be > 0")
        self.path, self.speed = path, float(speed)
        L = path.length
        self.s0 = min(max(float(start), 0.0), L)
        self.s1 = L if end is None else min(max(float(end), 0.0), L)
        self.dir = -1.0 if reverse else 1.0
        if reverse and end is None:
            self.s1 = 0.0
        self.loop, self.pingpong = bool(loop), bool(pingpong)
        self.ramp = max(0.0, float(ramp))
        self.ramp_out = self.ramp if ramp_out is None else max(0.0, float(ramp_out))
        span = abs(self.s1 - self.s0) if not (self.loop and path.closed) else L
        if span <= 0 and not self.loop:
            span = 0.0
        self.span = span
        if self.loop or self.pingpong:
            lap = span if self.loop else 2 * span
            if laps is not None:
                self.total = float(laps) * lap / self.speed + self.ramp / 2
            elif d is not None:
                self.total = float(d)
            else:
                self.total = 1e9
            self.ramp_out = 0.0 if laps is None and d is None else self.ramp_out
        else:
            self.total = span / self.speed + self.ramp / 2 + self.ramp_out / 2 if d is None else float(d)
            if d is not None:   # fixed duration: speed chosen to cover the span in d
                eff = max(1e-3, self.total - self.ramp / 2 - self.ramp_out / 2)
                self.speed = max(1e-3, span / eff)

    def dist(self, t):
        """Distance travelled after t seconds (accelerate over ramp, decelerate over ramp_out)."""
        v, r, ro, T = self.speed, self.ramp, self.ramp_out, self.total
        t = min(max(t, 0.0), T)
        d = v * t * t / (2 * r) if (r > 0 and t < r) else v * (t - r / 2)
        if ro > 0 and T < 1e8 and t > T - ro:
            u = T - t
            d = v * (T - r / 2 - ro / 2) - v * u * u / (2 * ro) if ro > 0 else d
        return d

    def s_at(self, t):
        """(arc length, travel direction +1/-1, done) at elapsed time t."""
        d = self.dist(t)
        P = self.path
        done = t >= self.total
        if self.loop:
            if P.closed:
                return (self.s0 + self.dir * d) % P.length, self.dir, done
            span = self.span or 1.0
            sg = 1.0 if self.s1 >= self.s0 else -1.0
            return self.s0 + sg * (d % span), sg, done
        sgn = 1.0 if self.s1 >= self.s0 else -1.0
        if self.pingpong:
            span = self.span or 1.0
            q = d % (2 * span)
            if q <= span:
                return self.s0 + sgn * q, sgn, done
            return self.s0 + sgn * (2 * span - q), -sgn, done
        d = min(d, self.span)
        return self.s0 + sgn * d, sgn, done


def _speed_gait(speed, gait):
    if gait is not None:
        if gait not in te.MoveTo.GAITS:
            raise ValueError(f"unknown gait {gait!r}; valid: {sorted(te.MoveTo.GAITS)}")
        return gait
    if speed is None:
        return "walk"
    return "sneak" if speed < 95 else ("walk" if speed < 230 else "run")


class FollowPath(te.MoveTo):
    """Walk / run / sneak (or fly) along a Path (#8) at `speed` (px/s, default from the gait; the
    gait defaults from the speed: < 95 sneak, < 230 walk, else run). Faces the direction of travel,
    feet stride with the gait, heights / depth / terrain come from the path.
    start / end: arc lengths in px (default: the whole path);
    loop: lap a closed path (or restart an open one); pingpong: back and forth; laps / d limit
    looping (otherwise it runs until the scene ends — give d in JSON timelines);
    reverse: travel from the end to the start; snap: jump onto the path at the start (default
    True; False = blend in from where the character stands);
    mode: "ground" (walkers) or "fly" (birds / flying characters: no feet, pitch follows the
    climb, banked; bank = max pitch in rad). Registered as te.ACTIONS["follow_path"]."""
    abs_y = True
    blend = 40.0

    def __init__(self, path, speed=None, gait=None, start=0.0, end=None, loop=False, pingpong=False,
                 laps=None, d=None, reverse=False, mode="ground", bank=0.5, snap=True):
        if not isinstance(path, Path):
            raise ValueError(f"follow_path needs a toonworld.Path (got {type(path).__name__}); "
                             "in JSON give the id of an item from 'paths'")
        if mode not in ("ground", "fly"):
            raise ValueError(f"follow_path mode must be 'ground' or 'fly', got {mode!r}")
        g = _speed_gait(speed, gait)
        te.MoveTo.__init__(self, 0.0, g, speed)
        self.path, self.mode, self.bank, self.snap = path, mode, float(bank), bool(snap)
        self.travel = _Travel(path, self.speed, start, end, loop, pingpong, laps, d, reverse,
                              ramp=0.25 if mode == "ground" else 0.4)
        self.duration = self.travel.total

    def start(self, c, scene):
        te.Action.start(self, c, scene)
        self.last_half = math.floor(c.phase / math.pi)
        self.base_scale = getattr(c, "_path_base_scale", None) or c.scale
        c._path_base_scale = self.base_scale
        self.from_xy = None if self.snap else (c.x, c.y)
        self.prev = None
        self.path._attach(c, scene)
        self._place(c, scene, 0.0, first=True)

    def _place(self, c, scene, dt, first=False):
        P = self.path
        s, sgn, done = self.travel.s_at(self.t)
        x, h, dp = P.local_at(s)
        g = P.ground(x, scene)
        y = g + h - dp
        k = 1.0 + dp * P.persp
        if self.from_xy is not None and self.t < 0.35:   # blend in from where we stood
            w = te.ease(self.t / 0.35)
            x, y = te.lerp(self.from_xy[0], x, w), te.lerp(self.from_xy[1], y, w)
        tx, th, td = P.tangent_at(s)
        tx, th, td = tx * sgn, th * sgn, td * sgn
        if abs(tx) > 0.2:
            c.face = 1 if tx > 0 else -1
        moved = 0.0 if self.prev is None else abs(s - self.prev) if abs(s - self.prev) < P.length / 2 \
            else P.length - abs(s - self.prev)
        self.prev = s
        c.x, c.y, c.vy = x, y, 0.0
        c.scale = self.base_scale * k
        c._path_depth = dp
        c._path_off = (h - dp) if self.mode == "ground" else -dp   # ground_y offset from the terrain
        if self.mode == "fly":
            climb = math.atan2(th - td, abs(tx) + 1e-6)
            c.body_rot = max(-self.bank, min(self.bank, -climb))
        tr = self.travel
        if tr.loop and tr.dist(self.t) >= tr.span - 1e-6:
            P.progress = P.length
        elif sgn > 0:
            P.progress = max(P.progress, s)
        return moved, done

    def update(self, c, dt, scene):
        self.t += dt
        moved, done = self._place(c, scene, dt)
        if self.mode == "ground":
            c.phase += moved / (self.stride * c.leg_k() * (c.scale / self.base_scale)) * math.pi * 2
            half = math.floor(c.phase / math.pi)
            if half != self.last_half:
                self.last_half = half
                scene.event("step" if self.gait != "run" else "runstep", c.x, gain=min(1.0, c.scale / self.base_scale))
                if self.gait == "run" and hasattr(scene.particles, "dust"):
                    scene.particles.dust(c.x - c.face * 10, c.y, 3, c.face)
        else:
            c.phase += dt * 6
        if done:
            self._finish(c)
            return True
        return False

    def _finish(self, c):
        off = getattr(c, "_path_off", 0.0)
        if self.mode == "fly":
            c.body_rot = 0.0
        self.path._detach(c, off)

    def pose(self, c):
        if self.mode == "fly":
            p = te.Action.pose(self, c)
            if getattr(c, "style", "toon") == "bird":    # legs streamed back in flight
                p.update(thighF=-1.25, thighB=-1.15, kneeF=0.2, kneeB=0.25)
            elif getattr(c, "style", "toon") != "quadruped":
                p.update(armUF=-1.2, armUB=-1.1, elbowF=0.2, elbowB=0.2, thighF=0.35, kneeF=0.6,
                         thighB=-0.1, kneeB=0.5, torso=0.25)
            return p
        return te.MoveTo.pose(self, c)


def follow_path(char, path, t=None, **kw):
    """Queue FollowPath on a character: at time t (None = right after its previous action)."""
    a = FollowPath(path, **kw)
    return char.at(t, a) if t is not None else char.then(a)


class Flyer:
    """A small flying prop (#8 fly mode): bird | butterfly | plane (paper plane). Drawn as a scene
    extra; fly(path, ...) moves it along a Path with banking (the body rolls into the climb /
    dive, wings flap faster climbing, glide diving). Sounds: 'flap' bursts for birds."""

    layer = 5
    KINDS = ("bird", "butterfly", "plane")

    def __init__(self, kind="bird", x=0.0, y=300.0, color=None, accent=None, scale=1.0, face=1, id=None,
                 sound=True):
        if kind not in self.KINDS:
            raise ValueError(f"unknown flyer kind {kind!r}; valid: {list(self.KINDS)}")
        self.kind, self.x, self.y, self.face, self.scale, self.id = kind, float(x), float(y), face, float(scale), id
        dflt = {"bird": ("#4f8fd6", "#f4a261"), "butterfly": ("#f28482", "#ffd166"), "plane": ("#f8f9fa", "#9fb3c8")}
        self.color, self.accent = _rgb(color, dflt[kind][0]), _rgb(accent, dflt[kind][1])
        self.flights = []     # (t0, _Travel, bank)
        self.angle = 0.0      # body rotation (rad, + = nose up in facing frame)
        self.flap = 0.0       # wing phase
        self.k = 1.0
        self.sound = sound
        self._last_flap = -9.0
        self.time = 0.0
        self._ang_s = te.Spring(40.0, 9.0)

    def fly(self, path, t=0.0, speed=320.0, loop=False, pingpong=False, laps=None, d=None, start=0.0,
            end=None, reverse=False, bank=0.7):
        self.flights.append((float(t), _Travel(path, speed, start, end, loop, pingpong, laps, d, reverse,
                                               ramp=0.0, ramp_out=0.0), float(bank)))
        self.flights.sort(key=lambda f: f[0])
        return self

    def update(self, dt, scene):
        T = scene.time + dt
        self.time = T
        fl = None
        for f in self.flights:
            if f[0] <= T:
                fl = f
        climb = 0.0
        if fl is not None:
            t0, tr, bank = fl
            s, sgn, _ = tr.s_at(T - t0)
            P = tr.path
            x, y, k = P.world_at(s, scene)
            tx, th, td = P.tangent_at(s)
            tx, th = tx * sgn, (th - td) * sgn
            if abs(tx) > 0.15:
                self.face = 1 if tx > 0 else -1
            climb = math.atan2(th, abs(tx) + 1e-6)
            self._ang_s.update(max(-bank, min(bank, climb)), dt)
            self.angle = self._ang_s.x
            self.x, self.y, self.k = x, y, k
        rate = {"bird": 15.0, "butterfly": 22.0, "plane": 0.0}[self.kind]
        glide = self.kind == "bird" and climb < -0.25
        self.flap += dt * rate * (0.25 if glide else (1.0 + max(0.0, climb)))
        if self.kind == "bird" and self.sound and fl is not None and not glide and T - self._last_flap > 0.9:
            self._last_flap = T
            scene.event("flap", self.x, gain=0.5)

    def draw(self, ctx, now):
        s = self.scale * self.k
        ctx.save()
        ctx.translate(self.x, -self.y)
        ctx.scale(self.face * s, s)
        ctx.rotate(-self.angle)
        getattr(self, "_draw_" + self.kind)(ctx)
        ctx.restore()

    def _wing(self, ctx, col, w, up, back=False):
        ctx.new_path()
        ctx.move_to(-6, 0)
        ctx.curve_to(-10, -w * 0.6 * up, -2 - w * 0.4, -w * up, -w * 0.15 - 4, -w * 1.05 * up)
        ctx.curve_to(4, -w * 0.7 * up, 12, -w * 0.3 * up, 10, 0)
        ctx.close_path()
        _fill_ink(ctx, _shade(col, 0.8) if back else col, 2.5)

    def _draw_bird(self, ctx):
        up = math.sin(self.flap)
        self._wing(ctx, self.color, 30, max(-0.6, up) * 1.0 + 0.15, back=True)
        # tail
        ctx.new_path()
        ctx.move_to(-20, -2)
        ctx.line_to(-38, -9)
        ctx.line_to(-36, 4)
        ctx.close_path()
        _fill_ink(ctx, _shade(self.color, 0.85), 2.5)
        # body + head
        ctx.save()
        ctx.scale(1.0, 0.62)
        ctx.new_path()
        ctx.arc(0, 0, 24, 0, 2 * math.pi)
        ctx.restore()
        _fill_ink(ctx, self.color, 2.5)
        ctx.new_path()
        ctx.arc(20, -10, 12, 0, 2 * math.pi)
        _fill_ink(ctx, self.color, 2.5)
        ctx.new_path()     # belly
        ctx.save()
        ctx.scale(1.0, 0.45)
        ctx.arc(3, 12, 15, 0.1, math.pi - 0.1)
        ctx.restore()
        ctx.set_source_rgba(1, 1, 1, 0.55)
        ctx.fill()
        ctx.new_path()     # beak
        ctx.move_to(30, -13)
        ctx.line_to(42, -9)
        ctx.line_to(30, -5)
        ctx.close_path()
        _fill_ink(ctx, self.accent, 2.0)
        ctx.new_path()
        ctx.arc(23, -13, 3.2, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.new_path()
        ctx.arc(24, -14, 1.1, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        self._wing(ctx, _light(self.color, 0.15), 30, up * 1.1 + 0.1)

    def _draw_butterfly(self, ctx):
        o = abs(math.cos(self.flap))
        for back in (True, False):
            col = _shade(self.color, 0.8) if back else self.color
            for big, (dx, dy, r) in enumerate(((-4, 8, 11), (-2, -12, 16))):
                ctx.save()
                ctx.translate(dx, 0)
                ctx.scale(0.25 + 0.75 * o if not back else 0.2 + 0.6 * o, 1.0)
                ctx.new_path()
                ctx.arc(0, dy, r, 0, 2 * math.pi)
                ctx.restore()
                _fill_ink(ctx, col, 2.0)
                if not back and big:
                    ctx.save()
                    ctx.translate(dx, 0)
                    ctx.scale(0.25 + 0.75 * o, 1.0)
                    ctx.arc(0, dy, r * 0.4, 0, 2 * math.pi)
                    ctx.restore()
                    ctx.set_source_rgb(*self.accent)
                    ctx.fill()
            if back:
                ctx.save()
                ctx.scale(1.0, 0.3)
                ctx.new_path()
                ctx.arc(0, 0, 14, 0, 2 * math.pi)
                ctx.restore()
                _fill_ink(ctx, INK, 1.0)
                ctx.move_to(10, -2)
                ctx.curve_to(16, -10, 18, -14, 22, -16)
                ctx.set_source_rgb(*INK)
                ctx.set_line_width(1.6)
                ctx.stroke()

    def _draw_plane(self, ctx):
        ctx.new_path()
        ctx.move_to(34, 0)
        ctx.line_to(-26, -14)
        ctx.line_to(-14, 0)
        ctx.line_to(-26, 8)
        ctx.close_path()
        _fill_ink(ctx, self.color, 2.5)
        ctx.new_path()
        ctx.move_to(34, 0)
        ctx.line_to(-14, 0)
        ctx.line_to(-20, 12)
        ctx.close_path()
        _fill_ink(ctx, self.accent, 2.5)


def _register_path_actions():
    te.ACTIONS.setdefault("follow_path", FollowPath)
    if te.ACTIONS.get("follow_path") is not FollowPath and \
            getattr(te.ACTIONS.get("follow_path"), "__name__", "") == "FollowPath":
        te.ACTIONS["follow_path"] = FollowPath   # module reloaded: point at the live class


_register_path_actions()

PATH_KEYS = {"id", "points", "closed", "smooth", "style", "color", "width", "spacing", "reveal", "persp",
             "relative", "supports"}
FLYER_KEYS = {"flyer", "id", "x", "y", "color", "accent", "scale", "face", "sound", "path", "fly"}
FOLLOW_KEYS = {"path", "t", "speed", "loop", "pingpong", "laps", "d", "start", "end", "reverse", "bank", "ease"}


def validate_path(item):
    """Error string for a bad path item ('' when fine) — used by toonscript.validate."""
    sp = item.get("path", item) if isinstance(item, dict) else item
    if not isinstance(sp, dict):
        return "a path item must be an object"
    bad = set(sp) - PATH_KEYS
    if bad:
        return f"path {sp.get('id')!r}: unknown key(s) {sorted(bad)}; valid: {sorted(PATH_KEYS)}"
    if not isinstance(sp.get("points"), list):
        return "path needs 'points': [[x, h?, depth?], ...]"
    try:
        Path(sp["points"], sp.get("closed", False), sp.get("smooth", True), sp.get("style", "none"))
    except ValueError as e:
        return str(e)
    return ""


def _path_from_spec(sp):
    sp = dict(sp)
    err = validate_path(sp)
    if err:
        raise ValueError(err)
    pid = sp.pop("id", None) or "path"
    return Path(id=pid, **sp), pid


def _follow_specs(v):
    fs = v if isinstance(v, list) else [v]
    out = []
    for f in fs:
        f = {"path": f} if isinstance(f, str) else dict(f)
        bad = set(f) - FOLLOW_KEYS
        if bad:
            raise ValueError(f"follow: unknown key(s) {sorted(bad)}; valid: {sorted(FOLLOW_KEYS)}")
        if "path" not in f:
            raise ValueError("follow needs a 'path' id")
        out.append(f)
    return out


# ---------------------------------------------------------------- JSON factories (toonscript)
def _resolve(ref, scene, made, objs=None):
    if ref is None or not isinstance(ref, str):
        return ref
    if ref in made:
        return made[ref]
    obj = (objs or {}).get(ref)
    if obj is None:
        obj = getattr(scene, "objects", {}).get(ref)
    if obj is None:
        known = sorted(set(made) | set(getattr(scene, "objects", {})) | set(objs or {}))
        raise ValueError(f"unknown id {ref!r}; known ids: {known}")
    return obj


def _riders(spec):
    r = spec.get("rider")
    if r is None:
        return []
    if not isinstance(r, list):
        r = [r]
    return [x if isinstance(x, dict) else {"id": x} for x in r]


VEHICLE_KEYS = {"vehicle", "id", "x", "y", "face", "scale", "color", "accent", "drive", "path", "rider",
                "honk", "ring", "hitch", "engine", "glass", "load", "auto_face", "follow"}
CROWD_KEYS = {"id", "n", "x_range", "depth_rows", "seed", "style_mix", "behaviour", "behavior", "y", "scale",
              "fog", "fog_color", "spread", "row_gap", "reactions"}


def build(spec, scene, group=None, objs=None):
    """Build vehicles / crowds / sidewalks / curve paths / flyers from JSON-able specs (see module
    docstring) and add them to the scene. spec: dict or list of dicts (paths first is not needed:
    path ids are resolved after everything is built). objs: extra {id: object} to resolve ids in.
    Returns {id: object}."""
    specs = spec if isinstance(spec, list) else [spec]
    made, pending, follows = {}, [], []
    # paths first, so vehicles / flyers in the same list can name them
    rest = []
    for k, sp in enumerate(specs):
        if not isinstance(sp, dict):
            raise ValueError(f"spec #{k} must be a dict, got {type(sp).__name__}")
        if "path" in sp and isinstance(sp["path"], dict) and "vehicle" not in sp and "flyer" not in sp:
            p, pid = _path_from_spec(sp["path"])
        elif "points" in sp and not ({"vehicle", "crowd", "sidewalk", "flyer"} & set(sp)):
            p, pid = _path_from_spec(sp)
        else:
            rest.append((k, sp))
            continue
        add(scene, p, pid)
        made[pid] = p
    for k, sp in rest:
        if "flyer" in sp:
            bad = set(sp) - FLYER_KEYS
            if bad:
                raise ValueError(f"flyer {sp.get('id')!r}: unknown key(s) {sorted(bad)}; valid: {sorted(FLYER_KEYS)}")
            fid = sp.get("id") or f"flyer{k}"
            fl = Flyer(sp["flyer"], sp.get("x", 0.0), sp.get("y", 300.0), sp.get("color"), sp.get("accent"),
                       sp.get("scale", 1.0), sp.get("face", 1), fid, sp.get("sound", True))
            fs = sp.get("fly", [])
            fs = _follow_specs(fs) if fs else []
            if "path" in sp:
                fs = [{"path": sp["path"]}] + fs
            for f in fs:
                follows.append((fl, f))
            add(scene, fl, fid)
            made[fid] = fl
            continue
        if "vehicle" in sp:
            kind = sp["vehicle"]
            if kind not in VEHICLES:
                raise ValueError(f"unknown vehicle {kind!r}; valid: {sorted(VEHICLES)}")
            bad = set(sp) - VEHICLE_KEYS
            if bad:
                raise ValueError(f"vehicle {sp.get('id', kind)!r}: unknown key(s) {sorted(bad)}; "
                                 f"valid: {sorted(VEHICLE_KEYS)}")
            vid = sp.get("id") or f"{kind}{k}"
            kw = dict(x=sp.get("x", 0.0), y=sp.get("y"), face=sp.get("face", 1), scale=sp.get("scale", 1.0),
                      id=vid, auto_face=sp.get("auto_face", True))
            if "color" in sp:
                kw["color"] = sp["color"]
            if "accent" in sp:
                kw["accent"] = sp["accent"]
            cls = VEHICLES[kind]
            if cls is Car:
                kw["engine"] = sp.get("engine", True)
                if "glass" in sp:
                    kw["glass"] = sp["glass"]
            if cls is Cart and "load" in sp:
                kw["load"] = sp["load"]
            v = cls(**kw)
            for dk in sp.get("drive", []):
                v.drive_to(dk["x"], dk.get("t", 0.0), dk.get("d"), dk.get("speed"), dk.get("ease", "in_out"))
            if sp.get("path"):
                v.path(sp["path"])
            for f in _follow_specs(sp["follow"]) if sp.get("follow") else []:
                follows.append((v, f))
            for t in sp.get("honk", []) + sp.get("ring", []):
                v.honk(t)
            for r in _riders(sp):
                v.mount(_resolve(r["id"], scene, made, objs), r.get("t", 0.0), r.get("d"), r.get("role", "driver"))
            if "hitch" in sp:
                if not isinstance(v, Cart):
                    raise ValueError(f"vehicle {vid!r}: only a cart can be hitched")
                hs = sp["hitch"] if isinstance(sp["hitch"], list) else [sp["hitch"]]
                for h in hs:
                    h = h if isinstance(h, dict) else {"id": h}
                    v.hitch(_resolve(h["id"], scene, made, objs), h.get("t", 0.0), h.get("d"), h.get("gap"))
            add(scene, v, vid)
            made[vid] = v
        elif "crowd" in sp:
            c = dict(sp["crowd"])
            bad = set(c) - CROWD_KEYS
            if bad:
                raise ValueError(f"crowd: unknown key(s) {sorted(bad)}; valid: {sorted(CROWD_KEYS)}")
            cid = c.get("id", "crowd")
            cr = Crowd(None, n=c.get("n", 20), x_range=tuple(c.get("x_range", (-600, 600))),
                       depth_rows=c.get("depth_rows", 2), seed=c.get("seed", 1), style_mix=c.get("style_mix"),
                       behaviour=c.get("behaviour", c.get("behavior", "idle")), y=c.get("y", 14.0),
                       scale=c.get("scale", 0.8), fog=c.get("fog", 0.22), fog_color=c.get("fog_color", "#dfeaf5"),
                       spread=c.get("spread", 0.45), row_gap=c.get("row_gap", 22.0), id=cid)
            add(scene, cr, cid)
            made[cid] = cr
            for r in c.get("reactions", []):
                if r.get("kind") not in REACTIONS:
                    raise ValueError(f"unknown crowd reaction {r.get('kind')!r}; valid: {list(REACTIONS)}")
                pending.append((cr, r))  # targets may be specs further down the list
        elif "sidewalk" in sp:
            s = dict(sp["sidewalk"] or {})
            sid = s.pop("id", "sidewalk")
            if "x_range" in s:
                s["x_range"] = tuple(s["x_range"])
            sw = Sidewalk(id=sid, **s)
            add(scene, sw, sid)
            made[sid] = sw
        else:
            raise ValueError(f"spec #{k}: expected a 'vehicle', 'crowd', 'sidewalk', 'path' or 'flyer' key, "
                             f"got {sorted(sp)}")
    for obj, f in follows:
        p = _resolve(f["path"], scene, made, objs)
        if not isinstance(p, Path):
            raise ValueError(f"{getattr(obj, 'id', '?')!r}: {f['path']!r} is not a path")
        kw = {k: f[k] for k in ("t", "loop", "pingpong", "laps", "d", "start", "end", "reverse") if k in f}
        if "speed" in f:
            kw["speed"] = f["speed"]
        if isinstance(obj, Flyer):
            if "bank" in f:
                kw["bank"] = f["bank"]
            obj.fly(p, **kw)
        else:
            if "ease" in f:
                kw["ease"] = f["ease"]
            obj.follow(p, **kw)
    for cr, r in pending:
        tgt = r.get("target")
        if isinstance(tgt, str):
            tgt = _resolve(tgt, scene, made, objs)
        cr.react(r.get("t", 0.0), r["kind"], r.get("d"), tgt, r.get("dir"), r.get("spread"), r.get("members"))
    return made


FACTORIES = {"vehicle": VEHICLES, "crowd": Crowd, "sidewalk": Sidewalk, "path": Path, "flyer": Flyer}

ensure_hooks()
