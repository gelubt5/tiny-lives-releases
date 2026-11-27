"""
ToonVoice — voices + automatic dialogue timing for ToonEngine (2D and 3D).

  tts(text, voice)            -> path to an audio file (cached, never paid twice)
     engine "elevenlabs": needs env ELEVENLABS_API_KEY, voice = ElevenLabs voice_id
     engine "piper":      free/offline, voice = path to a Piper .onnx model
     engine "none":       no audio (lip sync from text)
  Timeline(scene)             -> writes the script for you: each line starts when
                                 the previous one ends (auto-timing from audio length)

Example
    tl = Timeline(scene, gap=0.35)
    tl.narrate("Some people wait for motivation.", voice=NARRATOR)
    tl.line(bob, "I'll start tomorrow.", voice=BOB, emote="sleepy")
    tl.line(ana, "I start today.", voice=ANA, gesture="fist")
    scene.duration = tl.t + 1.5
"""
import hashlib, json, os, subprocess, sys, urllib.request

CACHE = os.environ.get("TOON_VOICE_CACHE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "voices", "cache"))
ELEVEN_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")


def _key(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]


def tts(text, voice=None, engine=None, cache_dir=CACHE, stability=0.45, similarity=0.8, style=0.3,
        length_scale=1.0):
    """Synthesize `text` and return the audio path (or None for engine 'none').
    Results are cached by (engine, voice, text, settings): re-rendering an episode
    never spends ElevenLabs credits twice."""
    if engine is None:
        engine = "elevenlabs" if os.environ.get("ELEVENLABS_API_KEY") and voice and not str(voice).endswith(".onnx") \
            else ("piper" if voice and str(voice).endswith(".onnx") else "none")
    if engine == "none" or not text.strip():
        return None
    os.makedirs(cache_dir, exist_ok=True)
    if engine == "elevenlabs":
        out = os.path.join(cache_dir, f"el_{_key(voice, ELEVEN_MODEL, text, stability, similarity, style)}.mp3")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            raise RuntimeError("ELEVENLABS_API_KEY is not set")
        body = json.dumps({"text": text, "model_id": ELEVEN_MODEL,
                           "voice_settings": {"stability": stability, "similarity_boost": similarity,
                                              "style": style}}).encode()
        req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                                     data=body, headers={"xi-api-key": key, "Content-Type": "application/json",
                                                         "Accept": "audio/mpeg"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        tmp = out + ".part"
        with open(tmp, "wb") as f:
            f.write(data)
        os.replace(tmp, out)
        return out
    if engine == "piper":
        out = os.path.join(cache_dir, f"pi_{_key(os.path.basename(voice), text, length_scale)}.wav")
        if os.path.exists(out) and os.path.getsize(out) > 0:
            return out
        subprocess.run([sys.executable, "-m", "piper", "-m", voice, "--length-scale", str(length_scale), "-f", out],
                       input=text.encode(), check=True, capture_output=True)
        return out
    raise ValueError(f"unknown TTS engine {engine!r} (use elevenlabs, piper or none)")


class Timeline:
    """Auto-timed script: lines/narration/beats are placed one after another.
    Listeners automatically look at whoever is speaking."""

    def __init__(self, scene, t=0.0, gap=0.35):
        self.scene, self.t, self.gap = scene, t, gap

    def wait(self, s):
        self.t += s
        return self

    def at(self, t):
        self.t = t
        return self

    def narrate(self, text, voice=None, engine=None, pause=None, **kw):
        audio = tts(text, voice, engine, **kw)
        d = self.scene.narrate(text, self.t, audio=audio)
        start = self.t
        self.t += d + (self.gap if pause is None else pause)
        return start

    def line(self, who, text, voice=None, engine=None, emote=None, gesture=None, pause=None, look=True, **kw):
        audio = tts(text, voice, engine, **kw)
        who.say(text, self.t, audio=audio)
        d = who.lines[-1]["d"]
        if emote:
            who.emote(emote, self.t, d + 0.3)
        if gesture:
            who.gesture(gesture, self.t, d)
        if look:
            for other in self.scene.characters:
                if other is not who:
                    other.look_keys.append((self.t, who))
        start = self.t
        self.t += d + (self.gap if pause is None else pause)
        return start

    def beat(self, fn, d=1.0):
        """Run fn(t) to schedule actions at the current time, then advance by d."""
        fn(self.t)
        start = self.t
        self.t += d
        return start
