"""Chaînes et vidéos YouTube sur la relance automatique des devis /
réactivation de base clients vendue aux artisans et entreprises de services
(EN + FR).

Usage :
    export YOUTUBE_API_KEY="..."
    python youtube_lead_gen/relance_devis/relance_devis.py

Sorties (à côté du script) :
    videos_relance_devis.csv   une ligne par vidéo pertinente
    chaines_relance_devis.csv  une ligne par chaîne (≥ 1 vidéo sur le sujet
                               dans les 12 derniers mois), avec son type :
                               VEND / ENSEIGNE / EDITEUR / à vérifier
"""

import csv
import hashlib
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

HERE = Path(__file__).parent
API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
CACHE = HERE / ".cache"
SINCE = "2024-01-01T00:00:00Z"
RECENT = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")

QUERIES = {
    "EN": ["estimate follow up automation contractors", "database reactivation agency",
           "quote follow up automation", "AI automation agency home services",
           "speed to lead contractors", "missed call text back contractors",
           "dead lead reactivation SMS"],
    "FR": ["relance devis automatique", "automatisation artisans",
           "agence automatisation IA artisans", "relance devis n8n",
           "relance devis Make", "IA pour artisans BTP"],
}
ORDERS = ["relevance", "date"]  # 2 pages de 50 par requête : pertinence + récentes

# Une vidéo est retenue si titre + début de description contiennent un terme
# de relance précis, ET soit un métier visé, soit (terme de relance dans le
# titre + automatisation). Immobilier / assurance / voyage exclus.
STRONG = re.compile(
    r"follow.?up|relanc|devis|quote|estimate|reactivat|réactiv|speed.to.lead|"
    r"missed.call|text.?back|dead lead|old leads?|base (de )?clients?|fichier client", re.I)
TRADE = re.compile(
    r"contractor|home.?service|roof|hvac|plumb|pool|kitchen|cabinet|remodel|renovat|"
    r"window|solar|landscap|trades?\b|artisan|btp|cuisin|piscin|menuis|couvreur|toiture|"
    r"chauffag|plombi|rénovation|bâtiment|batiment|électricien|electrician|painting|"
    r"peintre|garage door|pressure wash|cleaning|nettoyage|pest", re.I)
AUTOM = re.compile(r"automat|n8n|make\.com|zapier|highlevel|\bghl\b|\bai\b|\bia\b|"
                   r"\bsms\b|crm|agent", re.I)
EXCLUDE = re.compile(r"real estate|realtor|immobili|mortgage|insurance|assurance|"
                     r"voyage|travel", re.I)


def on_topic(title, text):
    if EXCLUDE.search(title) or not STRONG.search(text):
        return False
    return bool(TRADE.search(text) or (STRONG.search(title) and AUTOM.search(text)))


# Type de chaîne : on compte des formulations typiques dans la description
# (et les titres pour VEND / ENSEIGNE). Les liens d'affiliation (GoHighLevel,
# "free trial") ne suffisent pas à faire un éditeur.
EDITEUR = re.compile(
    r"(is an?|is the|est une?|c'est une?) (\w+ ){0,3}(platform|plateforme|software|logiciel|"
    r"app|application|solution|saas|assistant|tool|outil)|notre (logiciel|plateforme|"
    r"application|solution|outil)|our (software|platform|app|product|tool)|"
    r"cha[iî]ne officielle|official channel|\bsaas\b|start your free trial|"
    r"essai gratuit de notre", re.I)
ENSEIGNE = re.compile(
    r"\b(course|formation|organisme de formation|community|communauté|skool|learn|"
    r"apprend|academy|académie|coaching|mentor|tutorials?|tutos?|i teach|j'enseigne|"
    r"helping (everyday )?people|non-coders|selling ai|sell ai|make money|"
    r"gagner de l'argent|start (your|an) (ai )?(automation )?agency|"
    r"lancer (ton|votre|son) agence|\baaa\b|students?|élèves?|masterclass|bootcamp|"
    r"you can copy|step.by.step|full guide|je t'aide à|je vous aide à)", re.I)
VEND = re.compile(
    r"\b(agency|agence|we help|nous aidons|j'aide les (artisans|entreprises|pme)|"
    r"i help (contractors|business|agency owners)|done.for.you|clé en main|"
    r"book a (call|demo)|réserve[rz]? un appel|prendre rendez-vous|freelance|consulting|"
    r"consultant|our clients|nos clients|we build|nous créons|on installe|we install|"
    r"conçoit|développe et intègre|intégrateur|fondateur de)", re.I)

def get(endpoint, **params):
    CACHE.mkdir(exist_ok=True)
    ident = json.dumps([endpoint, sorted(params.items())], ensure_ascii=False)
    path = CACHE / (hashlib.sha1(ident.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    r = requests.get(f"{API}/{endpoint}", params={**params, "key": KEY}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"{endpoint} -> {r.status_code}: {r.text[:300]}")
    data = r.json()
    path.write_text(json.dumps(data))
    return data


def iso_seconds(d):
    m = re.match(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d or "")
    days, h, mi, s = (int(x or 0) for x in m.groups()) if m else (0, 0, 0, 0)
    return days * 86400 + h * 3600 + mi * 60 + s


def chunks(seq, n=50):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def search():
    found = {}  # videoId -> {"lang", "queries"}
    for lang, qs in QUERIES.items():
        for q in qs:
            for order in ORDERS:
                data = get("search", part="snippet", q=q, type="video", maxResults=50,
                           publishedAfter=SINCE, order=order,
                           relevanceLanguage=lang.lower(),
                           **({"regionCode": "FR"} if lang == "FR" else {}))
                for it in data.get("items", []):
                    f = found.setdefault(it["id"]["videoId"], {"lang": lang, "queries": set()})
                    f["queries"].add(q)
            print(f"[{lang}] {q!r}")
    return found


def video_rows(found):
    rows = []
    for batch in chunks(found):
        data = get("videos", part="snippet,contentDetails,statistics", id=",".join(batch))
        for v in data.get("items", []):
            sn, st = v["snippet"], v.get("statistics", {})
            if sn["publishedAt"] < SINCE:
                continue
            title = html.unescape(sn["title"])
            text = f"{title} {sn.get('description', '')[:1000]} {' '.join(sn.get('tags', []))}"
            if not on_topic(title, text):
                continue
            audio = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").lower()
            lang = ("FR" if audio.startswith("fr") else "EN" if audio.startswith("en")
                    else found[v["id"]]["lang"])
            secs = iso_seconds(v["contentDetails"].get("duration"))
            rows.append({
                "titre": title, "chaine": sn["channelTitle"], "langue": lang,
                "date": sn["publishedAt"][:10], "vues": int(st.get("viewCount", 0)),
                "duree": f"{secs // 60}:{secs % 60:02d}", "duree_s": secs,
                "lien": f"https://www.youtube.com/watch?v={v['id']}",
                "requetes": " | ".join(sorted(found[v["id"]]["queries"])),
                "_cid": sn["channelId"],
            })
    return rows


def classify(desc, titles):
    text = f"{desc} {' '.join(titles)}"
    scores = {"EDITEUR": len(EDITEUR.findall(desc)) * 3,
              "ENSEIGNE": len(ENSEIGNE.findall(text))
                          + 3 * bool(re.search(r"tutorial|tuto", desc, re.I)),
              "VEND": len(VEND.findall(text))}
    best = max(scores, key=scores.get)
    ordered = sorted(scores.values(), reverse=True)
    if ordered[0] == 0 or ordered[0] == ordered[1]:
        return "à vérifier", scores
    return best, scores


def channel_rows(videos):
    by_ch = defaultdict(list)
    for v in videos:
        by_ch[v["_cid"]].append(v)
    rows = []
    for batch in chunks(by_ch):
        data = get("channels", part="snippet,statistics", id=",".join(batch))
        for ch in data.get("items", []):
            vids = by_ch[ch["id"]]
            last = max(v["date"] for v in vids)
            if last < RECENT:
                continue
            sn, st = ch["snippet"], ch.get("statistics", {})
            kind, scores = classify(sn.get("description", ""), [v["titre"] for v in vids])
            langs = Counter(v["langue"] for v in vids)
            custom = sn.get("customUrl")
            rows.append({
                "nom": sn["title"],
                "langue": langs.most_common(1)[0][0],
                "type": kind,
                "abonnes": "" if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0)),
                "nb_videos_sujet": len(vids),
                "vues_videos_sujet": sum(v["vues"] for v in vids),
                "derniere_video_sujet": last,
                "pays": sn.get("country", ""),
                "lien": f"https://www.youtube.com/{custom}" if custom
                        else f"https://www.youtube.com/channel/{ch['id']}",
                "signaux_type": f"vend={scores['VEND']} enseigne={scores['ENSEIGNE']} editeur={scores['EDITEUR']}",
                "description": re.sub(r"\s+", " ", sn.get("description", ""))[:300],
            })
    return rows


def write(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main():
    if not KEY:
        sys.exit("Définis la variable d'environnement YOUTUBE_API_KEY.")
    found = search()
    print(f"{len(found)} vidéos trouvées")
    videos = video_rows(found)
    print(f"{len(videos)} vidéos sur le sujet depuis 2024")
    channels = channel_rows(videos)
    keep = {c["lien"] for c in channels}
    names = {c["nom"] for c in channels}
    videos = [v for v in videos if v["chaine"] in names]
    videos.sort(key=lambda v: (v["langue"], -v["vues"]))
    channels.sort(key=lambda c: (c["langue"], -c["vues_videos_sujet"]))
    write(HERE / "videos_relance_devis.csv", videos,
          ["titre", "chaine", "langue", "date", "vues", "duree", "lien", "requetes"])
    write(HERE / "chaines_relance_devis.csv", channels,
          ["nom", "langue", "type", "abonnes", "nb_videos_sujet", "vues_videos_sujet",
           "derniere_video_sujet", "pays", "lien", "signaux_type", "description"])
    print(f"{len(channels)} chaînes actives sur le sujet (12 derniers mois), {len(videos)} vidéos")


if __name__ == "__main__":
    main()
