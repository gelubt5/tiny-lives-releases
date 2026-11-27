import sys, subprocess, numpy as np, skia
import shots
from eng import W, H, vignette, paint, alpha, ramp, clamp
from shots import SHOTS, XFADE, FLASH, TOTAL, captions, FPS

def draw_shot(c, T):
    for a, b, fn in SHOTS:
        if a <= T < b:
            fn(c, T - a, T); return a
    a, b, fn = SHOTS[-1]; fn(c, T - a, T); return a

def frame(T, scale):
    w, h = int(round(W * scale)), int(round(H * scale))
    surf = skia.Surface(w, h); c = surf.getCanvas()
    c.scale(scale, scale)
    c.clear(skia.ColorBLACK)
    start = draw_shot(c, T)
    # crossfade from previous shot
    xf = XFADE.get(round(start, 2), 0)
    if xf and T - start < xf:
        prev = [s for s in SHOTS if abs(s[1] - start) < 1e-6]
        if prev:
            a, b, fn = prev[0]
            p = skia.Paint(); p.setAlphaf(1 - (T - start) / xf)
            c.saveLayer(None, p); c.clear(skia.ColorBLACK); fn(c, T - a, T); c.restore()
    # grade: warm lift + vignette
    c.drawRect(skia.Rect.MakeWH(W, H), paint(skia.Color(255, 200, 150, 14)))
    vignette(c, 120)
    # flash after hook
    fa = 1 - abs(T - FLASH) / 0.18
    if fa > 0: c.drawRect(skia.Rect.MakeWH(W, H), paint(alpha(skia.ColorWHITE, int(235 * clamp(fa)))))
    # fade in / out
    fo = max(ramp(T, TOTAL - 0.8, TOTAL), 1 - ramp(T, 0, 0.25))
    if fo > 0: c.drawRect(skia.Rect.MakeWH(W, H), paint(alpha(skia.ColorBLACK, int(255 * fo))))
    captions(c, T)
    return surf.makeImageSnapshot()

if __name__ == '__main__':
    mode = sys.argv[1]
    scale = float(sys.argv[2])
    shots.SC = scale; import common; common.SC = scale
    if mode == 'stills':
        for tt in sys.argv[3].split(','):
            img = frame(float(tt), scale); img.save(f'out/still_{float(tt):05.2f}.png')
    else:
        f0, f1, out = int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
        w, h = int(round(W * scale)), int(round(H * scale))
        p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for f in range(f0, f1):
            img = frame(f / FPS, scale)
            arr = img.toarray(colorType=skia.kRGBA_8888_ColorType)
            p.stdin.write(arr.tobytes())
            if f % 150 == 0: print(out, f, flush=True)
        p.stdin.close(); p.wait()
