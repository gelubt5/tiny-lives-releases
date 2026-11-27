"""Original score + synthesized SFX + mix (48 kHz)."""
import numpy as np, scipy.io.wavfile as wf, scipy.signal as sg
SR = 48000; TOTAL = 58.6
N = int(SR * TOTAL)
rng = np.random.default_rng(7)

def env_adsr(n, a=0.005, d=0.1, s=0.6, r=0.2):
    t = np.arange(n) / SR; L = n / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((L - t) / r, 0, 1)
    return e * rel

def note_f(m): return 440 * 2 ** ((m - 69) / 12)

def pluck(f, dur, bright=0.5):
    n = int(SR * dur); t = np.arange(n) / SR
    y = sum((1 / k) * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (3 + k * (6 - 4 * bright))) for k in range(1, 7))
    return y * np.minimum(1, t / 0.003)

def pad(f, dur):
    n = int(SR * dur); t = np.arange(n) / SR
    y = sum(np.sin(2 * np.pi * f * k * t * (1 + 0.002 * np.sin(2 * np.pi * 0.3 * t + k))) / k ** 1.5 for k in range(1, 5))
    return y * env_adsr(n, 0.6, 0.5, 0.8, 0.9)

def bell(f, dur):
    n = int(SR * dur); t = np.arange(n) / SR
    ratios = [1, 2.76, 5.4, 8.93]
    return sum(np.sin(2 * np.pi * f * r * t) * np.exp(-t * (1.2 + r * 0.9)) / (1 + i) for i, r in enumerate(ratios))

def add(buf, x, at, g=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i: i + len(x)] += x * g

def noise(dur): return rng.standard_normal(int(SR * dur))

def bp(x, lo, hi, order=2):
    b, a = sg.butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band'); return sg.lfilter(b, a, x)

def lp(x, f):
    b, a = sg.butter(2, f / (SR / 2)); return sg.lfilter(b, a, x)

# ---------------------------------------------------------------- music
BPM = 104; beat = 60 / BPM
music = np.zeros(N)
# chord progression (bars of 4 beats): playful sneaky in D minor -> warm F major at the "gift" -> D major ending
prog_a = [(50, [62, 65, 69]), (46, [62, 65, 70]), (48, [64, 67, 72]), (45, [61, 64, 69])]   # Dm Bb C A
prog_b = [(53, [65, 69, 72]), (48, [64, 67, 72]), (50, [62, 65, 69]), (46, [62, 65, 70])]   # F C Dm Bb
prog_c = [(50, [62, 66, 69]), (55, [62, 67, 71]), (57, [61, 64, 69]), (50, [62, 66, 69])]   # D G A D
mel_a = [74, None, 72, 74, 77, None, 76, 74, 72, None, 70, 69, 70, 72, 69, None]
mel_b = [77, 76, 77, 79, 81, None, 79, 77, 76, None, 74, 72, 74, 76, 77, None]
mel_c = [78, 76, 74, 76, 78, None, 81, 79, 78, 76, 74, None, 74, None, None, None]

t = 0.0; bar = 0
sections = [(0, 25.1, prog_b, mel_b, 'pizz'), (25.1, 45.3, prog_b, mel_b, 'pizz'), (45.3, 58.6, prog_c, mel_c, 'warm')]
for s0, s1, prog, mel, style in sections:
    t = s0
    while t < s1 - 0.01:
        root, chord = prog[bar % 4]
        # bass on beats 1 and 3, walking pizz
        for k, off in enumerate([0, 2]):
            add(music, pluck(note_f(root - 12 + (7 if k else 0)), beat * 1.6, 0.3), t + off * beat, 0.55)
        if style == 'pizz':
            for b8 in range(8):  # offbeat chord stabs
                if b8 % 2 == 1:
                    for m in chord: add(music, pluck(note_f(m), 0.25, 0.7), t + b8 * beat / 2, 0.10)
            for i in range(4):
                m = mel[(bar % 4) * 4 + i] if mel else None
                if m: add(music, pluck(note_f(m), 0.5, 0.9), t + i * beat, 0.16)
            # soft brush hat
            for b8 in range(8):
                h = bp(noise(0.06), 5000, 12000) * np.exp(-np.arange(int(SR * 0.06)) / SR * 70)
                add(music, h, t + b8 * beat / 2, 0.05 if b8 % 2 else 0.03)
        else:
            for m in chord: add(music, pad(note_f(m), beat * 4.2), t, 0.06)
            for i in range(4):
                m = mel[(bar % 4) * 4 + i]
                if m: add(music, bell(note_f(m), 1.6), t + i * beat, 0.065); add(music, pluck(note_f(m), 0.8, 0.6), t + i * beat, 0.065)
        t += beat * 4; bar += 1
music = lp(music, 9000)

# ---------------------------------------------------------------- sfx
sfx = np.zeros(N)
def chime(at, g=0.25, base=88):
    for i, m in enumerate([base, base + 4, base + 7, base + 12]):
        add(sfx, bell(note_f(m), 1.2) * 0.4, at + i * 0.045, g)
def whoosh(at, dur=0.45, g=0.35, up=True):
    n = noise(dur); e = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    add(sfx, bp(n, 400, 3000) * e, at, g)
def thud(at, g=0.6, f=70):
    n = int(SR * 0.35); tt = np.arange(n) / SR
    y = np.sin(2 * np.pi * (f + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) + lp(noise(0.35), 900) * np.exp(-tt * 25) * 0.6
    add(sfx, y, at, g)
def tick(at, g=0.12, f=2500):
    y = bp(noise(0.03), f * 0.7, f * 1.3) * np.exp(-np.arange(int(SR * 0.03)) / SR * 150); add(sfx, y, at, g)
def coin(at, g=0.25):
    n = int(SR * 0.5); tt = np.arange(n) / SR
    y = (np.sin(2 * np.pi * 3100 * tt) + 0.6 * np.sin(2 * np.pi * 4700 * tt)) * np.exp(-tt * 9); add(sfx, y, at, g)
def step(at, g=0.12):
    y = lp(noise(0.08), 600) * np.exp(-np.arange(int(SR * 0.08)) / SR * 40); add(sfx, y, at, g)

for k in range(10): step(0.3 + k * 0.6, 0.06)
whoosh(6.75, 0.4, 0.3)
for k in range(8): step(8.6 + k * 0.3, 0.07)
for k in range(int(2.8 * 16 / np.pi)):
    n = noise(0.08); add(sfx, bp(n, 2500, 7000) * np.sin(np.linspace(0, np.pi, len(n))), 9.95 + k * np.pi / 16, 0.06)
chime(11.5, 0.15, 91)
thud(11.15, 0.25, 90); thud(13.45, 0.2, 90)
for k in range(2): add(sfx, bp(noise(0.15), 2000, 6000) * np.sin(np.linspace(0, np.pi, int(SR * 0.15))), 15.7 + k * 0.1, 0.06)
chime(17.4, 0.15, 93); whoosh(17.9, 0.5, 0.15); coin(18.8, 0.18)
for k in range(5): coin(19.6 + k * 0.55, 0.08)
for at in (25.12, 26.57, 27.70):
    thud(at - 0.02, 0.25, 90); coin(at, 0.12)
add(sfx, bell(note_f(88), 1.5), 29.1, 0.08); add(sfx, bell(note_f(91), 1.5), 29.35, 0.08)
chime(31.2, 0.18, 88); whoosh(32.6, 0.5, 0.15); coin(33.4, 0.2)
for k in range(24): tick(34.0 + k * 0.1, 0.06, 3200)
thud(40.4, 0.4, 70); chime(40.45, 0.2, 86)
for k in range(12): add(sfx, bp(noise(0.06), 1500, 6000) * np.exp(-np.arange(int(SR*0.06))/SR*60), 40.6 + k * 0.09, 0.08)
whoosh(42.9, 0.5, 0.15)
chime(49.7, 0.15, 91)
chime(52.6, 0.22, 86)
# ---------------------------------------------------------------- mix
sr, v = wf.read('voice/voice.wav'); v = v.astype(float) / 32768
voice = np.zeros(N); voice[: min(N, len(v))] = v[:N]
# ducking envelope
e = np.abs(voice); e = lp(e, 6)
e = np.clip(e / (np.percentile(e, 98) + 1e-9), 0, 1)
duck = 1 - 0.55 * np.clip(lp(np.maximum.accumulate(e[::-1])[::-1] * 0 + e, 3) * 1.6, 0, 1)
def rms_db(x): return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
vr = rms_db(voice[voice != 0])
music *= 10 ** ((vr - 15 - rms_db(music)) / 20)   # bed ~15 dB under voice (+3 dB house rule applied below)
music *= 10 ** (3 / 20)
sfx *= 10 ** ((vr - 12 - rms_db(sfx[np.abs(sfx) > 1e-4])) / 20) * 10 ** (-6 / 20) * 2.0
fade = np.ones(N); fo = int(SR * 1.2); fade[-fo:] = np.linspace(1, 0, fo); fade[: int(SR * 0.2)] = np.linspace(0, 1, int(SR * 0.2))
mix = voice + music * duck * fade + sfx
peak = np.max(np.abs(mix)); mix = mix / peak * 0.89
wf.write('out/mix.wav', SR, (mix * 32767).astype(np.int16))
wf.write('out/music.wav', SR, (music / np.max(np.abs(music)) * 0.8 * 32767).astype(np.int16))
print('ok', peak)
