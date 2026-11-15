"""Collecte des vidéos "étude de cas / interview d'élève" sur les agences de
lead gen (EN + FR), puis récupération des transcriptions.

Usage :
    export YOUTUBE_API_KEY="..."
    python youtube_lead_gen/etudes_de_cas/collecte.py

Sorties (à côté du script) :
    videos.csv            titre, chaîne, langue, date, vues, durée, lien, transcription_ok
    transcriptions/*.txt  une transcription par vidéo
    .cache/               réponses API (relancer ne recoûte pas de quota)

Transcriptions : youtube-transcript-api. YouTube bloque les IP de serveurs
cloud (erreur IpBlocked) : lancer le script depuis un ordinateur personnel.
"""

import csv
import hashlib
import html
import json
import os
import re
import sys
from pathlib import Path

import requests

HERE = Path(__file__).parent
API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
CACHE = HERE / ".cache"
TRANSCRIPTS = HERE / "transcriptions"
SINCE = "2024-01-01T00:00:00Z"
MIN_SECONDS = 4 * 60          # durée moyenne ou longue (> 4 min)
TARGET = 30

QUERIES = {
    "EN": ["lead gen agency case study", "cold email agency 0 to 10k",
           "student interview cold email agency", "how I got my first lead gen client",
           "appointment setting agency case study", "outbound agency $10k month"],
    "FR": ["étude de cas agence prospection", "agence cold email premier client",
           "interview élève agence", "lancer agence génération de leads",
           "de 0 à 10k agence"],
}
# Chaînes prioritaires : handle YouTube (résolu via channels.list forHandle,
# repli sur une recherche par nom si le handle ne répond pas).
PRIORITY = {
    "Daniel Fazio": ("@danielfazio", "EN"),
    "Alex Berman": ("@alexberman", "EN"),
    "Lead Gen Jay": ("@leadgenjay", "EN"),
    "Matt Lucero": ("@matthewlucero", "EN"),
    "Alex Zartarian": ("@alexzartarian", "EN"),
    "Scalezia": ("@scalezia", "FR"),
    "Katana - Quentin Despas": ("@katana-vente", "FR"),
}
STORY = re.compile(
    r"case stud|interview|first client|\b0 to\b|\$0 to|zero to|from 0\b|student|"
    r"premier client|premiers clients|étude de cas|etude de cas|de 0 à|de 0 a|"
    r"témoignage|temoignage|élève|eleve", re.I)

TOPIC = re.compile(
    r"lead ?gen|cold ?e-?mail|outbound|appointment|setting|setter|prospect|linkedin|"
    r"outreach|meetings? booked|rendez-vous|\brdv\b|agence|agency|\bb2b\b|smma|"
    r"g[ée]n[ée]ration de leads|closing", re.I)
COURSE = re.compile(
    r"skool\.com|accelerator|accélérateur|accelerateur|mentorship|coaching|formation|"
    r"programme|program\b|bootcamp|masterclass|cohort|communauté|community|"
    r"work with me|travailler avec moi|apply|candidat|client ascension|whop\.com|"
    r"stan\.store|académie|academy|incubat", re.I)


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
    if not m:
        return 0
    days, h, mi, s = (int(x or 0) for x in m.groups())
    return days * 86400 + h * 3600 + mi * 60 + s


def resolve_channel(name, handle):
    data = get("channels", part="contentDetails,snippet", forHandle=handle)
    if data.get("items"):
        return data["items"][0]
    found = get("search", part="snippet", q=name, type="channel", maxResults=1)
    if not found.get("items"):
        return None
    cid = found["items"][0]["snippet"]["channelId"]
    return get("channels", part="contentDetails,snippet", id=cid)["items"][0]


def collect():
    cands = {}  # videoId -> {"lang", "source", "priority"}
    # 1) chaînes prioritaires : on parcourt leurs uploads (1 unité / 50 vidéos)
    for name, (handle, lang) in PRIORITY.items():
        ch = resolve_channel(name, handle)
        if not ch:
            print(f"! chaîne introuvable : {name}")
            continue
        uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        token, n = None, 0
        for _ in range(6):  # jusqu'à 300 dernières vidéos
            params = dict(part="snippet,contentDetails", playlistId=uploads, maxResults=50)
            if token:
                params["pageToken"] = token
            data = get("playlistItems", **params)
            stop = False
            for it in data.get("items", []):
                pub = it["contentDetails"].get("videoPublishedAt", "")
                if pub and pub < SINCE:
                    stop = True
                    continue
                sn = it["snippet"]
                if STORY.search(sn["title"]) or STORY.search(sn.get("description", "")[:600]):
                    cands.setdefault(it["contentDetails"]["videoId"],
                                     {"lang": lang, "source": f"chaîne {name}", "priority": 1})
                    n += 1
            token = data.get("nextPageToken")
            if stop or not token:
                break
        print(f"[chaîne] {name} ({ch['snippet']['title']}): {n} candidates")
    # 2) recherches par mots-clés
    for lang, qs in QUERIES.items():
        for q in qs:
            data = get("search", part="snippet", q=q, type="video", maxResults=50,
                       publishedAfter=SINCE, relevanceLanguage=lang.lower(),
                       order="relevance")
            n = 0
            for it in data.get("items", []):
                vid = it["id"]["videoId"]
                cands.setdefault(vid, {"lang": lang, "source": f"recherche « {q} »", "priority": 0})
                n += 1
            print(f"[{lang}] {q!r}: {n} vidéos")
    return cands


def enrich(cands):
    rows = []
    ids = list(cands)
    for i in range(0, len(ids), 50):
        data = get("videos", part="snippet,contentDetails,statistics", id=",".join(ids[i:i + 50]))
        for v in data.get("items", []):
            sn, cd, st = v["snippet"], v["contentDetails"], v.get("statistics", {})
            secs = iso_seconds(cd.get("duration"))
            if secs < MIN_SECONDS or sn["publishedAt"] < SINCE:
                continue
            title, desc = sn["title"], sn.get("description", "")
            in_title = bool(STORY.search(title))
            if not (in_title or STORY.search(desc[:1500])):
                continue
            prio = cands[v["id"]]["priority"]
            if prio and not in_title:      # chaînes prioritaires : parcours dans le titre
                continue
            if re.search(r"immobili|real estate", title, re.I):
                continue
            if not (TOPIC.search(title) or (prio and TOPIC.search(desc[:800]))):
                continue
            course = sorted({m.lower() for m in COURSE.findall(desc)})
            audio = (sn.get("defaultAudioLanguage") or sn.get("defaultLanguage") or "").lower()
            lang = "FR" if audio.startswith("fr") else "EN" if audio.startswith("en") else cands[v["id"]]["lang"]
            rows.append({
                "id": v["id"], "titre": html.unescape(title), "chaine": sn["channelTitle"],
                "langue": lang, "date": sn["publishedAt"][:10],
                "vues": int(st.get("viewCount", 0)), "duree_min": round(secs / 60),
                "lien": f"https://www.youtube.com/watch?v={v['id']}",
                "source": cands[v["id"]]["source"],
                "vend_formation": ("probable (" + ", ".join(course[:4]) + ")") if course else "pas de signal",
                "_score": 3 * cands[v["id"]]["priority"] + 2 * in_title,
            })
    return rows


def pick(rows):
    """Priorité : chaînes demandées, mot-clé dans le titre, puis vues.
    On garde ~1/3 de FR si le stock le permet, et 4 vidéos max par chaîne."""
    rows.sort(key=lambda r: (-r["_score"], -r["vues"]))
    chosen, per_channel = [], {}
    fr_quota = TARGET // 3
    for want_fr in (True, False):
        for r in rows:
            if len(chosen) >= (fr_quota if want_fr else TARGET):
                break
            if (r["langue"] == "FR") != want_fr or r in chosen:
                continue
            if per_channel.get(r["chaine"], 0) >= 4:
                continue
            chosen.append(r)
            per_channel[r["chaine"]] = per_channel.get(r["chaine"], 0) + 1
    return chosen


def vtt_to_text(vtt):
    lines, prev = [], None
    for line in vtt.splitlines():
        if "-->" in line or not line.strip() or line.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        line = html.unescape(re.sub(r"<[^>]+>", "", line)).strip()
        if line and line != prev:
            lines.append(line)
            prev = line
    return " ".join(lines)


def transcript(vid, lang):
    langs = ["fr", "fr-FR", "en", "en-US"] if lang == "FR" else ["en", "en-US", "fr"]
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        t = YouTubeTranscriptApi().fetch(vid, languages=langs)
        return " ".join(s.text for s in t.snippets), "youtube-transcript-api"
    except Exception as e:  # IpBlocked sur les serveurs cloud, ou pas de sous-titres
        first_err = type(e).__name__
    return None, first_err


def slug(s):
    s = re.sub(r"[^\w\s-]", "", s, flags=re.U).strip().lower()
    return re.sub(r"[\s_-]+", "-", s)[:60]


def main():
    if not KEY:
        sys.exit("Définis la variable d'environnement YOUTUBE_API_KEY.")
    cands = collect()
    print(f"{len(cands)} vidéos candidates")
    rows = enrich(cands)
    print(f"{len(rows)} vidéos > 4 min, depuis 2024, avec un mot-clé de parcours")
    chosen = pick(rows)
    TRANSCRIPTS.mkdir(exist_ok=True)
    for r in chosen:
        name = f"{r['langue']}_{r['date']}_{slug(r['titre'])}_{r['id']}.txt"
        path = TRANSCRIPTS / name
        if path.exists():
            r["transcription_ok"], r["fichier"] = "oui", name
            continue
        text, how = transcript(r["id"], r["langue"])
        if text and len(text) > 500:
            header = (f"Titre : {r['titre']}\nChaîne : {r['chaine']}\nDate : {r['date']}\n"
                      f"Lien : {r['lien']}\nSource transcription : {how}\n\n")
            path.write_text(header + text, encoding="utf-8")
            r["transcription_ok"], r["fichier"] = "oui", name
        else:
            r["transcription_ok"], r["fichier"] = "non", ""
        print(f"  [{r['transcription_ok']}] {r['titre'][:70]} ({how})")
    chosen.sort(key=lambda r: (r["langue"], r["date"]), reverse=False)
    fields = ["titre", "chaine", "langue", "date", "vues", "duree_min", "lien",
              "transcription_ok", "vend_formation", "fichier", "source"]
    with (HERE / "videos.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(chosen)
    ok = sum(r["transcription_ok"] == "oui" for r in chosen)
    print(f"{len(chosen)} vidéos retenues, {ok} transcriptions -> {HERE / 'videos.csv'}")


if __name__ == "__main__":
    main()
