# Chaînes francophones « Et si » : YTK=<clé> python3 etsi_fr.py sortie.json (clé jamais écrite dans le dépôt)
import os, sys, json, statistics, requests
K = os.environ["YTK"]; API = "https://www.googleapis.com/youtube/v3/"
def get(ep, **p): r = requests.get(API + ep, params={**p, "key": K}, timeout=60); r.raise_for_status(); return r.json()
Q = ["et si la terre", "et si le soleil disparaissait", "et si la lune", "que se passerait-il si", "et si simulation",
     "simulation 3D et si", "et si l'humanité", "et si la gravité", "et si les océans", "et si un astéroïde",
     "scénario et si planète", "et si tu", "et si on", "et si la terre arrêtait de tourner", "et si la terre tournait plus vite"]
chans = {}
for q in Q:
    tok = None
    for _ in range(2):
        d = get("search", part="snippet", q=q, type="video", relevanceLanguage="fr", regionCode="FR", maxResults=50, **({"pageToken": tok} if tok else {}))
        for it in d["items"]:
            s = it["snippet"]; t = s["title"].lower()
            if "et si" in t or "que se passerait" in t or "qu'arriverait" in t or "what if" in t:
                c = chans.setdefault(s["channelId"], {"nom": s["channelTitle"], "hits": []}); c["hits"].append(s["title"])
        tok = d.get("nextPageToken")
        if not tok: break
ids = list(chans)
rows = []
for i in range(0, len(ids), 50):
    for c in get("channels", part="snippet,statistics,contentDetails", id=",".join(ids[i:i+50]))["items"]:
        st = c["statistics"]; sn = c["snippet"]
        rows.append({"id": c["id"], "nom": sn["title"], "pays": sn.get("country", "?"), "lang": sn.get("defaultLanguage", "?"),
                     "cree": sn["publishedAt"][:10], "abos": int(st.get("subscriberCount", 0)), "vues": int(st.get("viewCount", 0)),
                     "nvid": int(st.get("videoCount", 0)), "up": c["contentDetails"]["relatedPlaylists"]["uploads"], "hits": chans[c["id"]]["hits"]})
petites = [r for r in rows if 500 <= r["abos"] <= 300_000]
for r in petites:
    try:
        pl = get("playlistItems", part="contentDetails", playlistId=r["up"], maxResults=15)["items"]
        vids = get("videos", part="snippet,statistics,contentDetails", id=",".join(x["contentDetails"]["videoId"] for x in pl))["items"]
    except Exception: vids = []
    v = [int(x["statistics"].get("viewCount", 0)) for x in vids]
    r["med15"] = int(statistics.median(v)) if v else 0
    r["dernier"] = vids[0]["snippet"]["publishedAt"][:10] if vids else "?"
    best = max(vids, key=lambda x: int(x["statistics"].get("viewCount", 0))) if vids else None
    r["top"] = (best["snippet"]["title"], int(best["statistics"]["viewCount"])) if best else ("", 0)
    r["etsi_part"] = sum(("et si" in x["snippet"]["title"].lower() or "que se passerait" in x["snippet"]["title"].lower()) for x in vids)
    r["nrec"] = len(vids)
json.dump(rows, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
petites.sort(key=lambda r: -r["etsi_part"] / max(r.get("nrec", 1), 1) * 1e7 - r["med15"])
for r in petites:
    print(f'{r["nom"][:34]:34} | {r["abos"]:>7} abos | {r["nvid"]:>4} vid | méd15 {r["med15"]:>7} | etsi {r["etsi_part"]}/{r["nrec"]} | créée {r["cree"]} | dern {r["dernier"]} | {r["pays"]} | top: {r["top"][0][:60]} ({r["top"][1]})')
print(len(rows), "chaînes,", len(petites), "petites")
