# Vidéos « Et si » qui ont percé sur de petites chaînes FR : YTK=<clé> python3 perces_fr.py sortie.json (clé jamais écrite dans le dépôt)
import os, sys, json, requests
K=os.environ["YTK"]; API="https://www.googleapis.com/youtube/v3/"
def get(ep,**p): r=requests.get(API+ep,params={**p,"key":K},timeout=60); r.raise_for_status(); return r.json()
Q=["et si","et si la terre","et si le soleil","et si la lune","que se passerait-il si","et si simulation","et si l'humanité disparaissait",
   "et si un astéroïde","et si la gravité","et si les océans","et si tu","et si on","et si la terre arrêtait de tourner","simulation 3D science",
   "scénario catastrophe planète","et si internet","et si l'électricité","et si les humains"]
vids={}
for q in Q:
    for order in ("viewCount","relevance"):
        d=get("search",part="snippet",q=q,type="video",relevanceLanguage="fr",regionCode="FR",maxResults=50,order=order,publishedAfter="2025-01-01T00:00:00Z")
        for it in d["items"]: vids[it["id"]["videoId"]]=it["snippet"]["channelId"]
ids=list(vids); V={}
for i in range(0,len(ids),50):
    for v in get("videos",part="snippet,statistics,contentDetails",id=",".join(ids[i:i+50]))["items"]: V[v["id"]]=v
ch=list({v["snippet"]["channelId"] for v in V.values()}); C={}
for i in range(0,len(ch),50):
    for c in get("channels",part="snippet,statistics",id=",".join(ch[i:i+50]))["items"]: C[c["id"]]=c
rows=[]
for vid,v in V.items():
    c=C.get(v["snippet"]["channelId"]); 
    if not c: continue
    subs=int(c["statistics"].get("subscriberCount",0)); views=int(v["statistics"].get("viewCount",0))
    t=v["snippet"]["title"]; tl=t.lower()
    if not any(k in tl for k in ["et si","que se passerait","qu'arriverait","qu’arriverait"]): continue
    import re
    dur=v["contentDetails"]["duration"]; m=re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",dur); sec=int(m[1] or 0)*3600+int(m[2] or 0)*60+int(m[3] or 0)
    rows.append(dict(titre=t,chaine=c["snippet"]["title"],abos=subs,vues=views,ratio=views/max(subs,1),date=v["snippet"]["publishedAt"][:10],duree=sec,url="https://youtu.be/"+vid,curl="https://www.youtube.com/channel/"+c["id"]))
json.dump(rows,open(sys.argv[1],"w"),ensure_ascii=False,indent=1)
ok=[r for r in rows if r["abos"]<=100_000 and r["vues"]>=30_000 and r["ratio"]>=3]
ok.sort(key=lambda r:-r["ratio"])
for r in ok[:45]:
    print(f'{r["ratio"]:7.1f}x | {r["vues"]:>9} vues | {r["abos"]:>6} abos | {"Short" if r["duree"]<=180 else str(r["duree"]//60)+" min":>6} | {r["date"]} | {r["chaine"][:22]:22} | {r["titre"][:70]} | {r["url"]}')
print(len(rows),"vidéos 'et si'",len(ok),"percées")
