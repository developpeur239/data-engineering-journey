"""Étape 4a : devine les domaines web plausibles et vérifie qu'ils correspondent au cabinet."""
import json, re, unicodedata, concurrent.futures as cf, urllib.request, ssl
def norm(s): return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower()
def brands(r):
    n = r["nom"]; names = re.findall(r"\(([^)]+)\)", n) + [re.sub(r"\(.*?\)", "", n)]
    out = []
    for b in names:
        b = norm(b); b = re.sub(r"\b(sarl|sas|s\.a\.s|groupe)\b", "", b); b = re.sub(r"[^a-z0-9 &'-]", "", b).strip()
        if len(b) < 4: continue
        out.append(b)
    return list(dict.fromkeys(out))
def slugs(b):
    w = re.split(r"[ &'\-]+", b); w = [x for x in w if x]
    s = {"".join(w), "-".join(w)}
    if len(w) > 1 and w[-1] in ("recrutement","conseil","conseils","consulting","search","rh"): s.add("".join(w[:-1]) + "-" + w[-1])
    return s
def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.geturl(), r.read(400000).decode("utf-8", "ignore")
    except Exception: return None, None
def check(r):
    hits = []
    for b in brands(r):
        key = [x for x in re.split(r"[ &'\-]+", b) if len(x) > 3 and x not in ("recrutement","conseil","conseils","consulting","search")]
        for s in slugs(b):
            for tld in ("fr", "com"):
                u, h = fetch(f"https://www.{s}.{tld}/")
                if not h: continue
                low = norm(h[:200000])
                rec = any(k in low for k in ("recrut", "talent", "candidat", "chasse"))
                if rec and all(k in low for k in key[:2]): hits.append(u); break
            if hits: break
        if hits: break
    return r["siren"], hits[0] if hits else None
if __name__ == "__main__":
  cands = json.load(open("candidates.json"))
  with cf.ThreadPoolExecutor(16) as ex: res = dict(ex.map(check, cands))
  json.dump(res, open("sites_guess.json","w"), indent=1)
  for r in cands: print(r["siren"], r["nom"][:45], "->", res[r["siren"]])
