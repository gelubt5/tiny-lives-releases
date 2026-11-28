"""python3 tts_en.py <episode_dir>  -> <episode_dir>/nar/nXX.wav (ElevenLabs, voice Paul D, needs env ELEVENLABS_API_KEY)"""
import json, os, sys, urllib.request, subprocess
d = os.path.abspath(sys.argv[1]); sys.path.insert(0, d)
from script import S
K = os.environ["ELEVENLABS_API_KEY"]
V = os.environ.get("EL_VOICE", "JBFqnCBsd6RMkjVDRZzb")  # George (British storyteller) for English shorts
os.makedirs(f"{d}/nar", exist_ok=True)
for i, t in enumerate(S):
    body = {"text": t, "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True},
            "previous_text": S[i - 1] if i else None, "next_text": S[i + 1] if i + 1 < len(S) else None}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{V}?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": K, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        open(f"{d}/nar/n{i:02d}.mp3", "wb").write(r.read())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/nar/n{i:02d}.mp3", "-ar", "44100", f"{d}/nar/n{i:02d}.wav"], check=True)
    print(i, "ok")
