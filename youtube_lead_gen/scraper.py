"""Trouve les chaînes YouTube (EN + FR) qui parlent de génération de leads.

Usage :
    export YOUTUBE_API_KEY="..."
    python youtube_lead_gen/scraper.py

Sortie : chaines.csv (à côté de ce script), trié par langue puis par abonnés.
Filtres : >= 1 000 abonnés et au moins une vidéo publiée dans les 6 derniers mois.
"""

import csv
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")

KEYWORDS = {
    "EN": ["lead generation agency", "cold email agency",
           "appointment setting agency", "B2B lead gen"],
    "FR": ["génération de leads", "prospection B2B",
           "agence prospection", "cold email"],
}
SEARCH_PARAMS = {
    "EN": {"relevanceLanguage": "en"},
    "FR": {"relevanceLanguage": "fr"},
}
MIN_SUBS = 1000
ACTIVE_SINCE = datetime.now(timezone.utc) - timedelta(days=183)
CHANNEL_PAGES = 2   # pages de 50 résultats "type=channel" par mot-clé
VIDEO_PAGES = 1     # pages de 50 résultats "type=video" récents par mot-clé

FR_WORDS = {"le", "la", "les", "des", "une", "et", "pour", "vous", "votre", "vos",
            "avec", "dans", "sur", "est", "du", "au", "aux", "nous", "qui", "je",
            "entreprise", "clients", "prospection", "chaîne", "à", "être"}
EN_WORDS = {"the", "and", "for", "you", "your", "with", "in", "on", "is", "of",
            "to", "we", "our", "how", "my", "this", "business", "clients", "channel"}
FR_COUNTRIES = {"FR", "BE", "CH", "LU", "MC", "SN", "CI", "CM", "MA", "TN", "DZ", "CD", "BJ", "TG", "ML", "BF", "GA", "MG", "RE", "HT"}
# La chaîne doit parler du sujet dans son nom ou sa description.
TOPIC = re.compile(
    r"lead|prospect|cold ?e?mail|cold ?call|appointment|setter|setting|outbound|b2b|"
    r"sales|selling|closing|closer|pipeline|acquisition|agency|agence|linkedin|"
    r"growth|clients?|vente|commercia|business ?develop|smma|outreach|crm",
    re.I)
EN_COUNTRIES = {"US", "GB", "AU", "NZ", "IE", "IN", "PH", "PK", "NG", "ZA", "SG", "AE", "KE"}


def get(endpoint, **params):
    params["key"] = KEY
    r = requests.get(f"{API}/{endpoint}", params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"{endpoint} -> {r.status_code}: {r.text[:300]}")
    return r.json()


def search(query, lang, kind, pages, **extra):
    ids, token = set(), None
    for _ in range(pages):
        params = dict(part="snippet", q=query, type=kind, maxResults=50,
                      **SEARCH_PARAMS[lang], **extra)
        if token:
            params["pageToken"] = token
        data = get("search", **params)
        for it in data.get("items", []):
            ids.add(it["snippet"]["channelId"])
        token = data.get("nextPageToken")
        if not token:
            break
    return ids


def chunks(seq, n=50):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def detect_language(snippet, country, found_by):
    default = (snippet.get("defaultLanguage") or "").lower()
    if default.startswith("fr"):
        return "FR"
    if default.startswith("en"):
        return "EN"
    text = f"{snippet.get('title', '')} {snippet.get('description', '')}".lower()
    tokens = re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+", text)
    fr = sum(t in FR_WORDS for t in tokens) + 3 * bool(re.search(r"[éèêàçù]", text))
    en = sum(t in EN_WORDS for t in tokens)
    if fr > en and fr >= 2:
        return "FR"
    if en > fr and en >= 2:
        return "EN"
    if country in FR_COUNTRIES:
        return "FR"
    if country in EN_COUNTRIES:
        return "EN"
    return "FR" if found_by == {"FR"} else "EN"


def last_upload(uploads_playlist):
    try:
        data = get("playlistItems", part="contentDetails",
                   playlistId=uploads_playlist, maxResults=5)
    except RuntimeError:
        return None
    dates = [it["contentDetails"].get("videoPublishedAt") for it in data.get("items", [])]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def main():
    if not KEY:
        sys.exit("Définis la variable d'environnement YOUTUBE_API_KEY.")

    found_by = {}  # channelId -> {"EN", "FR"}
    after = ACTIVE_SINCE.strftime("%Y-%m-%dT%H:%M:%SZ")
    for lang, words in KEYWORDS.items():
        for kw in words:
            ids = search(kw, lang, "channel", CHANNEL_PAGES)
            ids |= search(kw, lang, "video", VIDEO_PAGES, publishedAfter=after, order="relevance")
            print(f"[{lang}] {kw!r}: {len(ids)} chaînes")
            for cid in ids:
                found_by.setdefault(cid, set()).add(lang)
    print(f"Total chaînes uniques : {len(found_by)}")

    rows = []
    for batch in chunks(found_by):
        data = get("channels", part="snippet,statistics,contentDetails",
                   id=",".join(batch), maxResults=50)
        for ch in data.get("items", []):
            stats = ch.get("statistics", {})
            if stats.get("hiddenSubscriberCount"):
                continue
            subs = int(stats.get("subscriberCount", 0))
            if subs < MIN_SUBS:
                continue
            uploads = ch["contentDetails"]["relatedPlaylists"].get("uploads")
            last = last_upload(uploads) if uploads else None
            if not last:
                continue
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if last_dt < ACTIVE_SINCE:
                continue
            sn = ch["snippet"]
            if not TOPIC.search(f"{sn.get('title', '')} {sn.get('description', '')}"):
                continue
            country = sn.get("country", "")
            custom = sn.get("customUrl")
            rows.append({
                "nom": sn["title"],
                "langue": detect_language(sn, country, found_by[ch["id"]]),
                "pays": country,
                "abonnes": subs,
                "nb_videos": int(stats.get("videoCount", 0)),
                "vues_totales": int(stats.get("viewCount", 0)),
                "derniere_video": last_dt.date().isoformat(),
                "lien": f"https://www.youtube.com/{custom}" if custom
                        else f"https://www.youtube.com/channel/{ch['id']}",
                "trouve_via": "+".join(sorted(found_by[ch["id"]])),
            })

    rows.sort(key=lambda r: (r["langue"], -r["abonnes"]))
    out = Path(__file__).with_name("chaines.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["nom"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} chaînes retenues -> {out}")


if __name__ == "__main__":
    main()
