"""Trouve les PETITES chaînes YouTube tenues par des fondateurs d'agences de
lead generation (EN + FR), avec un score "patron d'agence" et les contacts.

Stratégies (par rapport à scraper.py) :
  1. Recherche de VIDÉOS triées par date (order=date) sur les 6 derniers mois :
     l'algorithme "relevance" met en avant les grosses chaînes, le tri par date
     fait remonter les petits créateurs actifs.
  2. Mots-clés "longue traîne" que seuls les patrons d'agence utilisent :
     niches clientes (lead gen for roofers / dentists...), coulisses d'agence
     ("agency update", "how I got clients"), résultats ("meetings booked"),
     et en FR "mon agence de prospection", "setter", "Waalaxy", "lemlist"...
  3. Filtre de taille : entre MIN_SUBS et MAX_SUBS abonnés.
  4. Score "patron d'agence" : mots d'agence dans la description, lien de prise
     de RDV (calendly, cal.com...), site web, email, titres des 10 dernières
     vidéos sur le sujet, nombre de requêtes qui ont trouvé la chaîne.
     Les outils SaaS (Instantly, lemlist, HubSpot...) sont pénalisés.
  5. Boule de neige : les "chaînes mises en avant" des meilleures chaînes
     sont ajoutées puis évaluées.
  6. Cache disque des réponses API (.cache/) : relancer ne recoûte pas de quota.
     Budget de quota plafonné (QUOTA_BUDGET).

Usage :
    export YOUTUBE_API_KEY="..."
    python youtube_lead_gen/petites_chaines.py
Variables optionnelles : MIN_SUBS (défaut 300), MAX_SUBS (défaut 30000),
QUOTA_BUDGET (défaut 6000 unités).
"""

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

HERE = Path(__file__).parent
API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
MIN_SUBS = int(os.environ.get("MIN_SUBS", 300))
MAX_SUBS = int(os.environ.get("MAX_SUBS", 30000))
QUOTA_BUDGET = int(os.environ.get("QUOTA_BUDGET", 6000))
MIN_SCORE = 5
ACTIVE_SINCE = datetime.now(timezone.utc) - timedelta(days=183)
CACHE = HERE / ".cache"
COST = {"search": 100}  # tout le reste coûte 1 unité

KEYWORDS = {
    "EN": [
        # coulisses / parcours de fondateur
        "my lead generation agency", "lead gen agency update",
        "how I started my lead generation agency", "cold email agency results",
        "appointment setting agency how I got clients", "lead gen agency owner day in the life",
        "outbound agency founder", "meetings booked cold email case study",
        "B2B appointment setting agency", "cold email agency 2026",
        # niches clientes (les agences se spécialisent)
        "lead generation for roofers", "lead generation for dentists",
        "lead generation for solar companies", "lead generation for HVAC",
        "lead generation for law firms", "lead generation for real estate agents",
        "lead generation for SaaS outbound", "lead generation for coaches",
        "LinkedIn lead generation agency", "pay per lead agency",
        "facebook ads lead generation agency", "Clay outbound agency",
    ],
    "FR": [
        "mon agence de prospection", "agence génération de leads",
        "lancer une agence de prospection", "agence prise de rendez-vous B2B",
        "prospection LinkedIn B2B", "cold emailing B2B français",
        "prospection automatisée Waalaxy", "lemlist prospection",
        "setter prise de rendez-vous", "trouver des clients B2B prospection",
        "génération de rendez-vous qualifiés", "agence growth B2B",
        "prospection téléphonique B2B", "lead generation français",
        "agence acquisition clients B2B", "prospection La Growth Machine",
        "Sales Navigator prospection", "prospection multicanale B2B",
        "comment trouver des clients agence", "business developer externalisé",
        "prospection cold email résultats", "SMMA français clients",
        # jargon de l'écosystème "agence high ticket" FR (setting, value asset...)
        "scaler son agence", "agence high ticket", "setter closer agence",
        "value asset", "setting Instagram agence", "offre high ticket agence",
        "Mathis Clouet",
    ],
}
LANG_PARAMS = {"EN": {"relevanceLanguage": "en"},
               "FR": {"relevanceLanguage": "fr", "regionCode": "FR"}}

TOPIC = re.compile(
    r"lead ?gen|leads?\b|prospect|cold ?e?-?mail|cold ?call|appointment|rendez-vous|rdv|"
    r"setter|setting|outbound|outreach|b2b|pipeline|booked|meetings|acquisition|"
    r"linkedin|lemlist|waalaxy|instantly|smartlead|clay|apollo|closing|closer|"
    r"vente|sales|agency|agence|client", re.I)
AGENCY = re.compile(
    r"\bagency\b|\bagence\b|we help|nous aidons|j'aide|i help|founder|fondateur|"
    r"\bceo\b|co-?founder|cofondateur|my clients|mes clients|done.for.you|clé en main|"
    r"book (a|your) call|réserve[rz]? (un|ton|votre) appel|work with (me|us)|"
    r"travailler avec (moi|nous)|accompagne|high.?ticket|scal(er|ing) (ton|votre|son) |"
    r"appel (de consulting |découverte )?offert|session .{0,20}offerte|setter|closer", re.I)
BOOKING = re.compile(r"calendly\.com|cal\.com|tidycal|hubspot\.com/meetings|"
                     r"zcal|savvycal|oncehub|iclosed|leadconnector", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL = re.compile(r"https?://[^\s)>\]]+")
SOCIAL = re.compile(r"youtube|youtu\.be|instagram|tiktok|twitter|x\.com|facebook|"
                    r"linkedin|linktr|beacons|bit\.ly|amzn|discord|skool|t\.me", re.I)
TOOLS = re.compile(r"\b(instantly|lemlist|hubspot|woodpecker|apollo|smartlead|"
                   r"waalaxy|la growth machine|clay|salesforce|zoominfo|lusha|"
                   r"dropcontact|kaspr|phantombuster|odoo|pipedrive|semrush)\b", re.I)

FR_WORDS = {"le", "la", "les", "des", "une", "et", "pour", "vous", "votre", "vos",
            "avec", "dans", "sur", "est", "du", "au", "aux", "nous", "qui", "je",
            "comment", "mon", "ma", "mes", "clients", "à", "pas", "plus"}
EN_WORDS = {"the", "and", "for", "you", "your", "with", "in", "on", "is", "of",
            "to", "we", "our", "how", "my", "this", "i", "get", "clients", "without"}

used = 0


class QuotaReached(Exception):
    pass


def get(endpoint, **params):
    """GET avec cache disque et suivi du quota."""
    global used
    CACHE.mkdir(exist_ok=True)
    ident = json.dumps([endpoint, sorted(params.items())], ensure_ascii=False)
    path = CACHE / (hashlib.sha1(ident.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    cost = COST.get(endpoint, 1)
    if used + cost > QUOTA_BUDGET:
        raise QuotaReached
    r = requests.get(f"{API}/{endpoint}", params={**params, "key": KEY}, timeout=30)
    if r.status_code == 403 and "quota" in r.text.lower():
        raise QuotaReached
    if r.status_code != 200:
        raise RuntimeError(f"{endpoint} -> {r.status_code}: {r.text[:300]}")
    used += cost
    data = r.json()
    path.write_text(json.dumps(data))
    return data


def chunks(seq, n=50):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def collect(found):
    """Stratégies 1+2 : recherche de vidéos récentes triées par date."""
    after = ACTIVE_SINCE.strftime("%Y-%m-%dT00:00:00Z")
    queue = []
    en, fr = KEYWORDS["EN"], KEYWORDS["FR"]
    for i in range(max(len(en), len(fr))):  # alterne EN/FR : budget équilibré
        if i < len(en):
            queue.append(("EN", en[i]))
        if i < len(fr):
            queue.append(("FR", fr[i]))
    for lang, kw in queue:
        try:
            data = get("search", part="snippet", q=kw, type="video", order="date",
                       publishedAfter=after, maxResults=50, **LANG_PARAMS[lang])
        except QuotaReached:
            print(f"Budget de quota atteint ({used} unités) : on s'arrête là pour la recherche.")
            break
        n = 0
        for it in data.get("items", []):
            cid = it["snippet"]["channelId"]
            f = found.setdefault(cid, {"langs": set(), "queries": set()})
            f["langs"].add(lang)
            f["queries"].add(kw)
            n += 1
        print(f"[{lang}] {kw!r}: {n} vidéos")


def detect_language(sn, titles, langs):
    default = (sn.get("defaultLanguage") or "").lower()
    if default[:2] in ("fr", "en"):
        return default[:2].upper()
    text = " ".join([sn.get("title", ""), sn.get("description", "")] + titles).lower()
    toks = re.findall(r"[a-zàâçéèêëîïôûùüÿœ']+", text)
    fr = sum(t in FR_WORDS for t in toks) + 2 * len(re.findall(r"[éèêàçù]", text))
    en = sum(t in EN_WORDS for t in toks)
    if fr > en * 1.2:
        return "FR"
    if en > fr * 1.2:
        return "EN"
    return "FR" if langs == {"FR"} else "EN"


def evaluate(ids, found):
    """Récupère stats + 10 dernières vidéos, applique filtres et score."""
    rows = []
    for batch in chunks(ids):
        data = get("channels", part="snippet,statistics,contentDetails,brandingSettings",
                   id=",".join(batch), maxResults=50)
        for ch in data.get("items", []):
            st = ch.get("statistics", {})
            if st.get("hiddenSubscriberCount"):
                continue
            subs = int(st.get("subscriberCount", 0))
            if not MIN_SUBS <= subs <= MAX_SUBS:
                continue
            sn = ch["snippet"]
            uploads = ch["contentDetails"]["relatedPlaylists"].get("uploads")
            if not uploads:
                continue
            try:
                items = get("playlistItems", part="snippet,contentDetails",
                            playlistId=uploads, maxResults=10).get("items", [])
            except (RuntimeError, QuotaReached):
                continue
            dates = [it["contentDetails"].get("videoPublishedAt") for it in items]
            dates = [d for d in dates if d]
            if not dates:
                continue
            last = datetime.fromisoformat(max(dates).replace("Z", "+00:00"))
            if last < ACTIVE_SINCE:
                continue
            titles = [it["snippet"]["title"] for it in items]
            vdescs = " ".join(it["snippet"].get("description", "") for it in items)
            desc = sn.get("description", "")
            keywords = ch.get("brandingSettings", {}).get("channel", {}).get("keywords", "")
            profile = f"{sn['title']} {desc} {keywords}"
            all_text = f"{profile} {vdescs}"

            score, sig = 0, []
            topical = sum(bool(TOPIC.search(t)) for t in titles)
            if topical:
                score += min(topical, 8); sig.append(f"{topical}/{len(titles)} vidéos sur le sujet")
            if TOPIC.search(profile):
                score += 3; sig.append("profil sur le sujet")
            if AGENCY.search(profile):
                score += 4; sig.append("profil d'agence")
            elif AGENCY.search(vdescs):
                score += 2; sig.append("agence dans les descriptions")
            if BOOKING.search(all_text):
                score += 4; sig.append("lien de prise de RDV")
            emails = sorted({e.rstrip(".") for e in EMAIL.findall(desc + " " + vdescs)
                             if not e.lower().endswith((".png", ".jpg"))})
            if emails:
                score += 2; sig.append("email")
            urls = [u.rstrip(".,") for u in URL.findall(desc + " " + vdescs)]
            sites = sorted({re.sub(r"^https?://(www\.)?", "", u).split("/")[0]
                            for u in urls if not SOCIAL.search(u) and not BOOKING.search(u)})
            booking = sorted({u for u in urls if BOOKING.search(u)})
            if sites:
                score += 1; sig.append("site web")
            if re.search(r"skool\.com", all_text, re.I):
                score += 1; sig.append("communauté Skool")
            nq = len(found.get(ch["id"], {}).get("queries", ()))
            if nq > 1:
                score += min(nq, 4); sig.append(f"trouvée par {nq} requêtes")
            if TOOLS.search(sn["title"]):
                score -= 8; sig.append("outil SaaS")
            if score < MIN_SCORE:
                continue
            custom = sn.get("customUrl")
            f = found.get(ch["id"], {"langs": set(), "queries": set()})
            rows.append({
                "nom": sn["title"],
                "langue": detect_language(sn, titles, f["langs"]),
                "pays": sn.get("country", ""),
                "score": score,
                "abonnes": subs,
                "nb_videos": int(st.get("videoCount", 0)),
                "vues_totales": int(st.get("viewCount", 0)),
                "derniere_video": last.date().isoformat(),
                "lien": f"https://www.youtube.com/{custom}" if custom
                        else f"https://www.youtube.com/channel/{ch['id']}",
                "emails": " ".join(emails[:3]),
                "liens_rdv": " ".join(booking[:2]),
                "sites": " ".join(sites[:4]),
                "signaux": "; ".join(sig),
                "titres_recents": " | ".join(titles[:3]),
                "trouve_via": " | ".join(sorted(f["queries"])) or "boule de neige",
                "_id": ch["id"],
            })
    return rows


def snowball(rows, found, top=40):
    """Stratégie 5 : chaînes mises en avant par les meilleures chaînes."""
    new = set()
    for r in sorted(rows, key=lambda r: -r["score"])[:top]:
        try:
            data = get("channelSections", part="contentDetails", channelId=r["_id"])
        except (RuntimeError, QuotaReached):
            continue
        for sec in data.get("items", []):
            for cid in sec.get("contentDetails", {}).get("channels", []) or []:
                if cid not in found:
                    new.add(cid)
    print(f"Boule de neige : {len(new)} nouvelles chaînes mises en avant")
    return new


def main():
    if not KEY:
        sys.exit("Définis la variable d'environnement YOUTUBE_API_KEY.")
    found = {}
    collect(found)
    print(f"Chaînes uniques trouvées : {len(found)}")
    rows = evaluate(list(found), found)
    extra = snowball(rows, found)
    if extra:
        rows += evaluate(list(extra), found)

    rows.sort(key=lambda r: (r["langue"], -r["score"], -r["abonnes"]))
    out = HERE / "petites_chaines.csv"
    fields = [k for k in rows[0] if not k.startswith("_")] if rows else ["nom"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} petites chaînes retenues ({MIN_SUBS}-{MAX_SUBS} abonnés, score >= {MIN_SCORE})"
          f" -> {out}  | quota utilisé : {used} unités")


if __name__ == "__main__":
    main()
