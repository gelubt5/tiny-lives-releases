import os, sys, subprocess, importlib.util
D = os.path.abspath(sys.argv[1])
spec = importlib.util.spec_from_file_location("s", os.path.join(D, "script.py")); c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
dur = lambda f: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
ts = lambda t: f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"
total = sum(dur(os.path.join(D, "out", f"sc_{i:02d}.mp4")) for i in range(len(c.S)))
ev = [f"Dialogue: 0,{ts(0)},{ts(total)},Title,,0,0,0,,{c.TITLE}"]
off = 0.0
for i, s in enumerate(c.S):
    n = dur(os.path.join(D, "nar", f"n{i:02d}.wav")); start = off + 0.4
    words = s.split(); chunks = [" ".join(words[k:k + 4]) for k in range(0, len(words), 4)]
    L = sum(len(x) + 1 for x in chunks); t = start
    for ch in chunks:
        d = n * (len(ch) + 1) / L
        ev.append(f"Dialogue: 1,{ts(t)},{ts(t + d)},Cap,,0,0,0,,{ch.upper()}"); t += d
    off += dur(os.path.join(D, "out", f"sc_{i:02d}.mp4"))
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Bangers,104,&H00A0D9EF,&H00FFFFFF,&H00211A1D,&H80000000,0,0,0,0,100,100,2,0,1,7,4,8,60,60,250,1
Style: Tag,Cinzel,40,&H00D8ECF4,&H00FFFFFF,&H00211A1D,&H80000000,1,0,0,0,100,100,4,0,1,2,2,8,60,60,520,1
Style: Cap,Bangers,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,2,0,1,7,4,2,60,60,470,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(os.path.join(D, "subs.ass"), "w").write(hdr + "\n".join(ev) + "\n")
