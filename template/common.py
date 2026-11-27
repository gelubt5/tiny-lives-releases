import json, math, random
import skia
from eng import *
import os
BASE = os.path.dirname(os.path.abspath(__file__)) + '/'
ENV = json.load(open(BASE + 'voice/env.json'))
WORDS = json.load(open(BASE + 'voice/words.json'))
FPS = 30
SC = 1.0
def talk_at(T, spans):
    if not any(a <= T <= b for a, b in spans): return 0.0
    i = int(T * FPS); e = ENV[i] if i < len(ENV) else 0
    return clamp((e - 0.08) * 1.6) * (0.6 + 0.4 * abs(math.sin(T * 23)))
# ---------------------------------------------------------------- camera helpers
def keys(t, ks):
    if t <= ks[0][0]: return ks[0][1:]
    for a, b in zip(ks, ks[1:]):
        if a[0] <= t <= b[0]:
            u = sms((t - a[0]) / (b[0] - a[0]))
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(1, 5))
    return ks[-1][1:]

class Cam:
    def __init__(self, z=1.0, x=0, y=0, rot=0, creep=0.0, t=0, kicks=()):
        self.z = z * (1 + creep * t); self.x = x; self.y = y; self.rot = rot
        sx = sy = 0
        for kt in kicks:
            d = (t - kt) * FPS
            if 0 <= d < 8:
                amp = 22 * (1 - d / 8)
                sx += amp * (1 if int(d) % 2 == 0 else -1); sy += amp * 0.6 * (1 if int(d) % 2 else -1)
        self.sx, self.sy = sx, sy

def layer(c, cam, p, blur, fn, fy=None):
    c.save()
    if blur > 0.3:
        bp = skia.Paint(); bp.setImageFilter(skia.ImageFilters.Blur(blur * SC, blur * SC)); c.saveLayer(None, bp)
    fy = H * 0.55 if fy is None else fy
    z = 1 + (cam.z - 1) * p
    c.translate(W / 2 + cam.sx * p, fy + cam.sy * p); c.rotate(cam.rot * p); c.scale(z, z)
    c.translate(-W / 2 - cam.x * p, -fy - cam.y * p)
    fn(c)
    if blur > 0.3: c.restore()
    c.restore()

def build_chunks():
    chunks = []; cur = []
    for w in WORDS:
        cur.append(w); word = w['w']
        if word[-1] in '.,?!"' or word.endswith('...') or len(cur) >= 2:
            chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    out = []
    for i, ch in enumerate(chunks):
        s = ch[0]['s'] - 0.03
        e = chunks[i + 1][0]['s'] - 0.03 if i + 1 < len(chunks) else ch[-1]['e'] + 0.8
        e = min(e, ch[-1]['e'] + 0.5)
        out.append((s, e, ' '.join(x['w'] for x in ch).replace('"', '').replace('...', '…')))
    return out
CHUNKS = build_chunks()

def captions(c, T):
    for s, e, txt in CHUNKS:
        if s <= T < e:
            a = ramp(T, s, s + 0.08); sc = 0.82 + 0.18 * back_out(ramp(T, s, s + 0.16))
            c.save(); c.translate(W / 2, H * 0.735); c.scale(sc, sc)
            f = skia.Font(FONT_BOLD, 82); w = f.measureText(txt); size = 82 if w < 900 else 82 * 900 / w
            text(c, txt, 4, 10, size, alpha(skia.ColorBLACK, int(90 * a)), stroke=16, scolor=alpha(skia.ColorBLACK, int(90 * a)))
            text(c, txt, 0, 0, size, alpha(skia.ColorWHITE, int(255 * a)), stroke=14, scolor=alpha(hexc('141018'), int(255 * a)))
            c.restore(); return
