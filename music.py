import numpy as np, wave, sys
sr=44100; dur=float(sys.argv[1]); bpm=108; beat=60/bpm
n=int(sr*dur); out=np.zeros(n)
def tone(f,d,a,kind='acc'):
    t=np.arange(int(sr*d))/sr
    if kind=='acc':  # accordion-ish: detuned saw-like harmonics with tremolo
        w=sum(np.sin(2*np.pi*f*k*t)/k for k in range(1,7))+sum(np.sin(2*np.pi*f*1.004*k*t)/k for k in range(1,7))
        w*=0.5*(1+0.15*np.sin(2*np.pi*5.5*t))
    elif kind=='bass':
        w=np.sin(2*np.pi*f*t)+0.3*np.sin(4*np.pi*f*t)
    else:
        w=np.sin(2*np.pi*f*t)
    env=np.minimum(1,t/0.02)*np.exp(-t*(2.5 if kind!='acc' else 1.2))
    return a*w*env
def put(x,at):
    i=int(at*sr); j=min(n,i+len(x))
    if i<n: out[i:j]+=x[:j-i]
N=lambda m:440*2**((m-69)/12)
# D minor folk progression: Dm Dm A A Gm Dm A Dm
prog=[(50,[62,65,69]),(50,[62,65,69]),(45,[61,64,69]),(45,[61,64,69]),(43,[62,67,70]),(50,[62,65,69]),(45,[61,64,69]),(50,[62,65,69])]
mel=[74,73,74,76,77,76,74,73, 76,74,73,71,69,70,69,0, 70,72,74,72,70,69,67,69, 73,74,76,73,74,0,74,0]
t=0;bar=0
while t<dur:
    root,ch=prog[bar%8]
    for b in range(2):  # oom-pah in 2/4
        put(tone(N(root-12+(7 if b else 0)),beat*0.9,0.5,'bass'),t+b*beat)
        for m in ch: put(tone(N(m),beat*0.35,0.10,'acc'),t+b*beat+beat/2)
    for k in range(4):
        m=mel[(bar*4+k)%len(mel)]
        if m and bar%16>=4: put(tone(N(m),beat*0.45,0.09,'acc'),t+k*beat/2)
    t+=2*beat; bar+=1
fade=int(sr*2.5); out[-fade:]*=np.linspace(1,0,fade); out[:int(sr*1)]*=np.linspace(0,1,int(sr*1))
out/=np.max(np.abs(out))*1.1
w=wave.open(sys.argv[2],'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((out*32767).astype(np.int16).tobytes())
