import json,urllib.request,base64
K=open('/tmp/.el').read().strip()
text=("Every Tuesday and Thursday, before the sun came up, a man pushed a purple cart into a children's hospital in Pittsburgh. "
"His name was Albert Lexie. He wasn't a doctor. He shined shoes. "
"Five dollars a shine. He made about ten thousand dollars a year. "
"But if you gave him six dollars... that extra dollar wasn't his. "
"Every single tip went to the hospital's Free Care Fund, for sick kids whose families couldn't pay. "
"One dollar. Then a hundred. Then a thousand. "
"One Christmas, a doctor handed him a fifty-dollar bill. Straight to the kids. "
"He kept doing it for more than thirty years. "
"By the time he retired, in twenty thirteen, Albert had given over two hundred and two thousand dollars. "
"More than a third of everything he ever earned. "
"When people asked him why, his answer was simple. "
"\"I love my kids.\" "
"The hospital called them patients. "
"Albert called them... Albert's kids.")
print(len(text))
body=json.dumps({"text":text,"model_id":"eleven_multilingual_v2","voice_settings":{"stability":0.55,"similarity_boost":0.8,"style":0.15}}).encode()
req=urllib.request.Request("https://api.elevenlabs.io/v1/text-to-speech/q6K6eJHlET6X3ASlVWD9/with-timestamps?output_format=mp3_44100_128",data=body,headers={"xi-api-key":K,"Content-Type":"application/json"})
j=json.load(urllib.request.urlopen(req,timeout=180))
open('voice.mp3','wb').write(base64.b64decode(j['audio_base64']))
a=j['alignment'];words=[];cur='';s=e=None
for c,t0,t1 in zip(a['characters'],a['character_start_times_seconds'],a['character_end_times_seconds']):
    if c.isspace():
        if cur: words.append({'w':cur,'s':s,'e':e}); cur=''
    else:
        if not cur: s=t0
        cur+=c; e=t1
if cur: words.append({'w':cur,'s':s,'e':e})
json.dump(words,open('words.json','w'),indent=0)
