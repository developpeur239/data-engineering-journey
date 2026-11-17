import numpy as np, wave, sys
sr=44100; bpm=80; step=60/bpm/4; bars=16
N=int(sr*step*16*bars)+sr*2
L=np.zeros(N); R=np.zeros(N)
rng=np.random.default_rng(1)
def t(d): return np.arange(int(sr*d))/sr
def add(sig,pos,gain=1.0,pan=0.0):
    i=int(pos*sr); s=sig[:N-i]*gain
    L[i:i+len(s)]+=s*(1-pan)/1.0 if pan>0 else s
    R[i:i+len(s)]+=s*(1+pan) if pan<0 else s
def kick():
    x=t(0.45); f=45+120*np.exp(-x*30)
    return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-x*7)
def clap():
    x=t(0.25); n=rng.standard_normal(len(x))
    env=np.exp(-x*18)*(1+0.6*np.exp(-((x-0.012)%0.012)*400)*(x<0.03))
    n=np.convolve(n,[1,-0.6],'same'); return n*env*0.5
def rim():
    x=t(0.08); return (np.sin(2*np.pi*1700*x)+0.6*np.sin(2*np.pi*820*x))*np.exp(-x*70)*0.5
def shaker():
    x=t(0.07); n=np.diff(rng.standard_normal(len(x)+1)); return n*np.exp(-x*60)*np.minimum(1,x*400)*0.25
def hat_open():
    x=t(0.3); n=np.diff(rng.standard_normal(len(x)+1),2,append=[0,0]) if False else np.diff(np.diff(rng.standard_normal(len(x)+2)))
    return n*np.exp(-x*10)*0.12
def note(f,d,kind):
    x=t(d)
    if kind=='pad':
        s=sum(np.sin(2*np.pi*f*k*x+0.3*k)/k**1.5 for k in range(1,6))
        s+=0.5*np.sin(2*np.pi*f*1.003*x)
        env=np.minimum(1,x/0.25)*np.minimum(1,(d-x)/0.3); return s*env*0.07
    if kind=='bass':
        s=np.sin(2*np.pi*f*x)+0.25*np.sin(2*np.pi*2*f*x)
        return np.tanh(1.5*s)*np.exp(-x*2.5)*np.minimum(1,(d-x)/0.02)*0.5
    if kind=='gtr':
        s=sum(np.sin(2*np.pi*f*k*x)*np.exp(-x*(6+k*3))/k for k in range(1,7))
        return s*np.minimum(1,x/0.003)*0.22
mid=lambda m:440*2**((m-69)/12)
# Am F C G
chords=[[57,60,64],[53,57,60],[55,60,64],[55,59,62]]
roots=[45,41,48,43]
riff=[[76,72,69,72],[77,72,69,72],[76,72,67,72],[74,71,67,71]]
kickp=[0,7,9]; clapp=[4,12]; rimp=[3,6,10,14]; hatp=[2,6,10,14]
bassp=[(0,3),(3,2),(7,2),(10,3),(14,2)]  # step, length; offsets in octave pattern
K,C,Ri=kick(),clap(),rim()
for b in range(bars):
    bt=b*16*step; c=b%4
    full=b>=4      # intro: 4 bars pads+gtr then drums
    for m in chords[c]: add(note(mid(m),16*step+0.2,'pad'),bt,1,0)
    for i,m in enumerate(riff[c]*2):
        s=[0,2,3,5,8,10,11,13][i]
        add(note(mid(m),0.6,'gtr'),bt+s*step,0.9 if full else 0.7,0.3)
    if not full: 
        if b>=2:
            for s in range(0,16,2): add(shaker(),bt+s*step,0.6)
        continue
    for s in kickp: add(K,bt+s*step,0.95)
    for s in clapp: add(C,bt+s*step,0.8)
    for s in rimp: add(Ri,bt+s*step,0.6,-0.3)
    for s in range(16): add(shaker(),bt+s*step,0.55 if s%2 else 0.35,0.2)
    for s in hatp: add(hat_open(),bt+s*step,0.8,-0.2)
    for s,l in bassp:
        r=roots[c]+(12 if s==10 else 0)
        add(note(mid(r-12+12),l*step,'bass'),bt+s*step,0.9)
# fade out last bar
end=int(bars*16*step*sr)+sr
L=L[:end];R=R[:end]
fade=np.linspace(1,0,sr*2); L[-len(fade):]*=fade; R[-len(fade):]*=fade
st=np.stack([L,R],1); st=np.tanh(st/np.abs(st).max()*1.2)*0.9
w=wave.open(sys.argv[1],'w'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
w.writeframes((st*32767).astype(np.int16).tobytes())
