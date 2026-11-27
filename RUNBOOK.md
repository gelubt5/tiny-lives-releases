# Unsung Stories — make and publish ONE episode (scheduled run)

Channel: YouTube @UnsungStoriesTV + Facebook page Unsung Stories, published by Leo (Lansio business slug `unsung-stories`).
Style: Celyxi-like 2.5D cartoon — white bean-head characters (eng.draw_char), soft-shaded rooms/props, depth-of-field layers,
slow camera push-ins, word-by-word captions (Poppins Bold, white with dark outline, at 73.5% height), ~55-62 s, 1440x2560.
The template/ folder is a complete working episode ("Albert's Kids") — copy it and change the story-specific parts.

## 1. Story (English, true, clean)
- ONE true, heart-warming story of an ordinary person who did something extraordinary (kindness, generosity, persistence).
  No violence, no war, no crime, no sexual content, no swearing, no politics, no minors' names. Must be visual.
- Never repeat a person listed in `stories.md` (this branch). Verify every fact with WebSearch (2+ reputable sources). Write SCRIPT.md with sources.
- Script ~140-160 words: hook → who → 3-4 escalating beats incl. a NUMBER COUNTER beat (e.g. 1 → 100 → 1,000) →
  big number reveal → why/quote → callback twist ending. Short sentences, "..." for pauses.

## 2. Voice — ElevenLabs API (NOT the ElevenLabs MCP connector: that free account is out of credits)
- Two Starter account keys (never commit or print them). Find them with conversation_search:
  key A: "ElevenLabs API key sk_a5d3" ; key B (backup, use after A is used up): "sk_99e8".
- For each key in order A, B: GET https://api.elevenlabs.io/v1/user/subscription (character_limit - character_count).
  Use the first key with >= 950 characters left; save it to /tmp/.el (chmod 600). If neither has 950, STOP and report it.
- Voice "Clark" q6K6eJHlET6X3ASlVWD9, model eleven_multilingual_v2, /with-timestamps — template/voice/tts.py does it (edit the text) and writes words.json.
- Then: `ffmpeg -y -i voice/voice.mp3 -ac 1 -ar 48000 voice/voice.wav` and make env.json (section 5).

## 3. Animation — copy template/ to /home/claude/ep/ and rewrite shots.py
- `pip install --break-system-packages skia-python numpy scipy` (ffmpeg is installed).
- shots.py: 12-15 shot functions timed to the sentence times in words.json, SHOTS list, XFADE at place changes, FLASH after hook, TOTAL = voice end + ~3.5 s.
- eng.py helpers: draw_char/Look, wall/floor/window/baseboard/desk/bookshelf/plant/lamp/tree/house_front/church/truck/chalkboard/lunchbox/frame_pic/sparkle/glow/text.
  Keep characters big and centred (use camera y offsets so they are not at the bottom edge; captions sit at 73.5% height).
- Stills: `python3 render.py stills 0.5 2,5,9,...` → contact sheet with ffmpeg tile → LOOK at it (Read) and fix cropping, hidden faces, empty frames.

## 4. Sound
- audio.py = original score + synthesized SFX. Set TOTAL, section times, and replace the SFX event block with events timed to this episode. Then:
  `python3 audio.py && ffmpeg -y -i out/mix.wav -af "volume=12dB,alimiter=limit=0.78:attack=2:release=80:level=disabled" -ar 48000 out/mix14.wav`

## 5. Render (2 processes, ~10 min)
```
python3 -c "import numpy as np,scipy.io.wavfile as w,json;sr,a=w.read('voice/voice.wav');a=a.astype(float)/32768;n=int(len(a)/sr*30)+1;e=[float(np.sqrt(np.mean(a[int(i*sr/30):int((i+1)*sr/30)]**2)+1e-9)) for i in range(n)];m=np.percentile(e,95);json.dump([min(1,x/m) for x in e],open('voice/env.json','w'))"
mkdir -p out; N=$(python3 -c "import shots;print(int(shots.TOTAL*30))"); H=$((N/2))
python3 render.py video 1.33334 0 $H out/partA.mp4 & python3 render.py video 1.33334 $H $N out/partB.mp4 & wait
printf "file partA.mp4\nfile partB.mp4\n" > out/list.txt; ffmpeg -y -f concat -i out/list.txt -c copy out/video.mp4
ffmpeg -y -i out/video.mp4 -i out/mix14.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest out/final.mp4
```
QA: tile 1 frame every 3 s and look at it. No black/frozen frames, captions readable.

## 6. Publish through Leo (GitHub)
- In a NEW empty dir: `git init`, add remote https://github.com/gelubt5/tiny-lives-releases, commit `<slug>.mp4` + `lansio.json` on branch
  `unsung-stories--<slug>` and push it (`git -c push.negotiate=true push -u origin <branch>`).
  lansio.json: {"title","yt_title" (ends " #shorts", ≤100 chars),"yt_description" (story + "A true story. Sources: …" + #unsungstories #truestory #shorts),
  "yt_tags":[...],"caption" (Facebook text with "🎬 {youtube}"),"script"}
- Leo picks it up within ~15 min and posts to YouTube + Facebook. Check with the leo MCP tool recent_videos business "unsung-stories".
- Append the new person to stories.md on branch `tools--unsung-engine` and push it.
