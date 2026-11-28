"""python3 short.py shorts/<slug>  -> renders the episode's scenes with English on-screen text to shorts/<slug>/out/sc_XX.mp4
shorts/<slug>/script.py: TITLE, SCENES=(module path or "ep2", [scene indexes]), S=[English narration], T={ro: en}"""
import os, sys, importlib.util
TK = os.path.dirname(os.path.abspath(__file__))
D_ = os.path.abspath(sys.argv[1]); sys.path.insert(0, TK); sys.path.insert(0, os.path.join(TK, "engine"))
spec = importlib.util.spec_from_file_location("short_script", os.path.join(D_, "script.py"))
cfg = importlib.util.module_from_spec(spec); spec.loader.exec_module(cfg)
import ep2_sarmale as E
src, idx = cfg.SCENES
if src == "ep2":
    M = E
else:
    spec = importlib.util.spec_from_file_location("epmod", os.path.join(TK, src))
    M = importlib.util.module_from_spec(spec); sys.modules["epmod"] = M; spec.loader.exec_module(M)
_orig = E.text
def text_en(ctx, s, *a, **k):
    return _orig(ctx, cfg.T.get(s, s), *a, **k)
for mod in {E, M}:
    mod.text = text_en
E.NAR = os.path.join(D_, "nar")
OUT = os.path.join(D_, "out"); os.makedirs(OUT, exist_ok=True)
only = [int(a) for a in sys.argv[2:]] or range(len(idx))
for i in only:
    D = E.nar_len(i) + 0.75
    sc = M.SCENES[idx[i]](D)
    n = int(D * 30)
    sc.render(os.path.join(OUT, f"sc_{i:02d}.mp4"), workers=2,
              preview_png={f: os.path.join(OUT, f"p{i:02d}_{k}.png") for k, f in enumerate((30, n // 2, int(n * 0.8)))})
    print("scene", i, "ok", round(D, 2))
