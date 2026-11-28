# Povestea Lucrurilor — episode toolkit (ToonEngine + silueta style)

Romanian animated history explainers, ~2–2.5 min, 16:9, in the style of the Gicu Caras video
"De unde vine mămăliga?" (tall silhouette figures in profile, one big white eye, thin light rim,
coloured folk clothes; muted painted backgrounds, haze, film grain, vignette; comic "STAI PUȚIN!"
exclamations in Bangers; serif labels/maps in Cinzel). Narrator: casual, warm, jokey ("Da, mă..."),
real documented facts only, no violence / politics / swearing / sexual content.

## Topic rule (Gelu, 28.11.2026)
No Orthodox/saint feast days (Moș Nicolae, Sf. Andrei, Sânziene, Bobotează...) and no other holidays
(Halloween, Valentine's, mărțișor, Dragobete...). The ONLY holidays allowed: Easter, Christmas, New Year.
Everything else = everyday food, objects and customs.

## Files
- `engine/` ToonEngine core (Scene, Camera, render) — `silueta.py` the silhouette Figure
- `ep2_sarmale.py` shared painting helpers + backgrounds (bg_home, bg_word, bg_palace, bg_market,
  bg_map, bg_village, bg_oven, bg_balkans, bg_fest), props (table, pot, mamaliga, candle, stall...),
  cast (ion, bunica, copil, turc), Painted world, make(), add(), sx(), head_y(), text(), grain()...
- `ep/cozonac/episode.py` + `script.py` — the TEMPLATE episode (9 scenes). Copy it for a new episode.
- `tts_el.py` ElevenLabs narration (voice Paul D, eleven_multilingual_v2), `build.sh` final mix,
  `music.py` code-made folk loop, `episodes.json` done list + topic backlog.

## Make one episode
1. `bash setup.sh`
2. Pick the first backlog topic not in `done` (or a better seasonal one). Research it with web search
   (3–6 searches), keep only facts confirmed by sources.
3. `mkdir ep/<slug>`; write `ep/<slug>/script.py` with `S = [...]` — 8–10 narration blocks,
   TOTAL ≤ 1,800 characters (credits!), numbers and years written out in Romanian words.
   Block 0 = hook at a Romanian home/table, last block = wrap-up + question for comments.
4. Copy `ep/cozonac/episode.py` to `ep/<slug>/episode.py` and rewrite the scenes (one `sN(D)` per block):
   new backgrounds/props drawn in the same muted style, Figures with walk/do/talk/feel, `w.pop(...)`
   exclamations, serif year/place labels. Reuse ep2 backgrounds where they fit. Keep figures inside
   the frame (|x| ≤ 470 at zoom 1.3).
5. `ELEVENLABS_API_KEY=... python3 tts_el.py ep/<slug>`  (ONE take only, never retry blindly)
6. `cd ep/<slug> && python3 episode.py` — then look at out/p*_1.png contact sheet; fix overlaps / text
   collisions / cut-off figures and re-render only those scenes.
7. `bash build.sh ep/<slug> ep/<slug>/final.mp4` (expect -14 LUFS)
8. Publish through Leo: in the tiny-lives-releases repo create an ORPHAN branch
   `povestea-lucrurilor--de-unde-vine-<slug>` containing only `<slug>.mp4` and `lansio.json`
   (keys: title, yt_title, yt_description, yt_tags, caption with {youtube}, script). Push it.
   Leo (Lansio business "Povestea Lucrurilor", id 25) picks it up within ~15 min and posts to YouTube.
9. Append the episode to `episodes.json` "done" (and remove it from backlog) on this toolkit branch,
   also commit the new `ep/<slug>/episode.py` + `script.py` (not nar/ or out/).

## English Short for every episode (since 28.11.2026)
Every new episode also gets a ~50–55 s vertical English Short, published on the SAME channel (Leo business "povestea-lucrurilor").
1. `shorts/<slug>/script.py`: `TITLE` (English, on screen), `SCENES = ("ep/<slug>/episode.py", [6–7 scene indexes])` (or `"ep2"` for ep2_sarmale.py),
   `S` = 6–7 English narration blocks, total ≈ 700–780 characters (≈ 48 s), numbers/years written in words, last block = question for comments;
   `T` = {Romanian on-screen string: English} for every pop/label shown in those scenes. See shorts/bradul as the example.
2. `ELEVENLABS_API_KEY=... python3 tts_en.py shorts/<slug>` (voice George, ONE take)
3. `python3 short.py shorts/<slug>` (re-renders the chosen scenes with English text) then `bash build_short.sh shorts/<slug>` -> shorts/<slug>/short.mp4
   (1080x1920: blurred background, the 16:9 scene in the middle, English title on top, big captions below). Look at a few frames.
4. Host: orphan branch `mcp-pl-short-<slug>` with only `pl-short-<slug>.mp4` (NO lansio.json, so Lansio's watcher ignores it), push,
   then `mcp__leo__publish_video` once: business "povestea-lucrurilor", networks ["youtube"],
   url https://raw.githubusercontent.com/gelubt5/tiny-lives-releases/mcp-pl-short-<slug>/pl-short-<slug>.mp4,
   English catchy title with emoji + "#shorts", English description (facts, question, #shorts + hashtags), 6–9 tags.
5. Add it to `episodes.json` "shorts_en".
