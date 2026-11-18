"""Extrait tous les commentaires (et leurs réponses) d'une vidéo YouTube.

Usage :
    export YOUTUBE_API_KEY="..."
    python youtube_lead_gen/commentaires/commentaires.py <url_ou_id_video>

Sortie : commentaires_<id>.csv à côté du script.
Coût : 1 unité de quota par page de 100 commentaires.
"""

import csv
import html
import os
import re
import sys
from pathlib import Path

import requests

API = "https://www.googleapis.com/youtube/v3"
KEY = os.environ.get("YOUTUBE_API_KEY")
HERE = Path(__file__).parent


def get(endpoint, **params):
    r = requests.get(f"{API}/{endpoint}", params={**params, "key": KEY}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"{endpoint} -> {r.status_code}: {r.text[:300]}")
    return r.json()


def video_id(arg):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", arg)
    return m.group(1) if m else arg


def clean(text):
    text = html.unescape(re.sub(r"<br\s*/?>", "\n", text))
    return re.sub(r"<[^>]+>", "", text).strip()


def row(c, kind, parent=""):
    s = c["snippet"]
    return {
        "type": kind, "auteur": s.get("authorDisplayName", ""),
        "chaine_auteur": s.get("authorChannelUrl", ""),
        "texte": clean(s.get("textDisplay", "")), "likes": s.get("likeCount", 0),
        "date": s.get("publishedAt", "")[:10], "id": c["id"], "parent_id": parent,
    }


def main():
    if not KEY or len(sys.argv) < 2:
        sys.exit("Usage : YOUTUBE_API_KEY=... python commentaires.py <url_ou_id_video>")
    vid = video_id(sys.argv[1])
    info = get("videos", part="snippet,statistics", id=vid)["items"][0]
    print(f"{info['snippet']['title']} — {info['snippet']['channelTitle']} "
          f"({info['statistics'].get('commentCount', '?')} commentaires annoncés)")
    rows, token = [], None
    while True:
        params = dict(part="snippet,replies", videoId=vid, maxResults=100,
                      order="relevance", textFormat="html")
        if token:
            params["pageToken"] = token
        data = get("commentThreads", **params)
        for th in data.get("items", []):
            top = th["snippet"]["topLevelComment"]
            r = row(top, "commentaire")
            r["nb_reponses"] = th["snippet"].get("totalReplyCount", 0)
            rows.append(r)
            inline = th.get("replies", {}).get("comments", [])
            if r["nb_reponses"] > len(inline):  # l'API n'en renvoie que 5 : on va chercher le reste
                inline, rtoken = [], None
                while True:
                    p = dict(part="snippet", parentId=top["id"], maxResults=100, textFormat="html")
                    if rtoken:
                        p["pageToken"] = rtoken
                    rd = get("comments", **p)
                    inline += rd.get("items", [])
                    rtoken = rd.get("nextPageToken")
                    if not rtoken:
                        break
            for rep in sorted(inline, key=lambda c: c["snippet"]["publishedAt"]):
                rows.append(row(rep, "réponse", top["id"]))
        token = data.get("nextPageToken")
        if not token:
            break
    out = HERE / f"commentaires_{vid}.csv"
    fields = ["type", "auteur", "texte", "likes", "nb_reponses", "date",
              "chaine_auteur", "id", "parent_id"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    tops = sum(r["type"] == "commentaire" for r in rows)
    print(f"{tops} commentaires + {len(rows) - tops} réponses -> {out}")


if __name__ == "__main__":
    main()
