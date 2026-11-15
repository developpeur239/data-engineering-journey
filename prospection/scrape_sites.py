"""Étape 4c-5 : lit page d'accueil + pages contact/à propos/carrières, extrait téléphone, mots-clés, offres internes."""
import json, re, html, urllib.parse, concurrent.futures as cf
from guess_domains import fetch, norm
KW = {"btp":r"\bbtp\b", "construction":r"construction", "travaux":r"\btravaux\b", "batiment":r"batiment", "genie civil":r"genie civil",
      "industrie":r"industri", "ingenierie":r"ingenier", "maintenance":r"maintenance", "aeronautique":r"aeronauti|aerospatial|aerospace",
      "energie":r"energie|enr\b|renouvelable", "immobilier":r"immobilier", "tech/IT":r"\bdigital|informatique|\btech\b|developpeur|data\b",
      "sante":r"\bsante\b|medical|pharma", "finance/compta":r"comptab|finance|expertise comptable", "vin/spiritueux":r"\bvin\b|vins\b|spiritueux|viticol",
      "commerce/vente":r"commercia|\bvente\b|\bsales\b", "logistique":r"logistique|transport"}
CORE = ["btp","construction","travaux","batiment","genie civil","industrie","ingenierie","maintenance","aeronautique"]
PHONE = re.compile(r"(?:\+33\s?\(?0?\)?\s?|\b0)[1-9](?:[\s.\-]?\d{2}){4}\b")
SUBP = re.compile(r"contact|propos|qui-sommes|cabinet|expertise|secteur|metier|rejoindre|recrut|carriere|join|equipe|about", re.I)
def text(h):
    h = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
def run(item):
    siren, url = item
    u, h = fetch(url)
    if not h: return siren, {"site_ok": False}
    pages = {u: h}
    host = urllib.parse.urlparse(u).netloc
    links = []
    for l in re.findall(r'href="([^"#]+)"', h):
        a = urllib.parse.urljoin(u, l)
        if urllib.parse.urlparse(a).netloc == host and SUBP.search(a) and a not in links and not re.search(r"\.(pdf|jpg|png)$", a): links.append(a)
    for a in links[:6]:
        uu, hh = fetch(a)
        if hh: pages[uu] = hh
    home = norm(text(h)); full = norm(" ".join(text(x) for x in pages.values()))
    tel = []
    for hh in pages.values():
        tel += [re.sub(r"\D", "", t) for t in re.findall(r'href="tel:([^"]+)"', hh)]
        tel += [re.sub(r"\D", "", t) for t in PHONE.findall(text(hh))]
    tel = [("0" + t[2:] if t.startswith("33") else t) for t in tel]; tel = [t for t in dict.fromkeys(tel) if len(t) == 10]
    kw_home = {k: len(re.findall(p, home)) for k, p in KW.items()}; kw_full = {k: len(re.findall(p, full)) for k, p in KW.items()}
    m = re.search(r'<title[^>]*>(.*?)</title>', h, re.S | re.I); desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', h, re.I)
    hire = re.findall(r".{0,80}(?:charge[e]?s? d.affaires|business manager|consultant[e]? en recrutement|consultant[e]? recrutement|nous recrutons|rejoignez[- ]nous).{0,80}", full)
    return siren, {"site_ok": True, "url": u, "title": html.unescape(m.group(1).strip()) if m else "", "meta": html.unescape(desc.group(1)) if desc else "",
                   "tel": tel[:3], "kw_home": {k:v for k,v in kw_home.items() if v}, "kw_full": {k:v for k,v in kw_full.items() if v},
                   "hiring_snips": hire[:4], "pages": list(pages)}
if __name__ != "__main__": raise ImportError
sites = json.load(open("sites.json"))
with cf.ThreadPoolExecutor(12) as ex: out = dict(ex.map(run, sites.items()))
json.dump(out, open("sites_scraped.json", "w"), ensure_ascii=False, indent=1)
for s, d in out.items():
    print("\n==", s, d.get("url"), "|", d.get("title","")[:80]); print("   meta:", d.get("meta","")[:160]); print("   tel:", d.get("tel"), "| home:", d.get("kw_home"), "\n   full:", d.get("kw_full"))
    for x in d.get("hiring_snips", [])[:2]: print("   HIRE:", x[:160])
