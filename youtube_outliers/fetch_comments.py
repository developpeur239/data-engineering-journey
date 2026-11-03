"""Extrait les commentaires publics de vidéos YouTube (API YouTube Data v3).

    export YOUTUBE_API_KEY="..."
    python fetch_comments.py y99SjQLmxmI iX7s3G8jjFU --out commentaires --max 2000

Pour chaque vidéo : un CSV (commentaires principaux + réponses) et un résumé dans le terminal
(commentaires les plus aimés, mots qui reviennent). Coût : 1 unité de quota par page de 100.

Les commentaires contiennent des noms d'auteurs : garde les CSV pour toi, ne les commite pas.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

from discovery import STOPWORDS
from youtube_client import QuotaExceeded, YouTubeClient

FIELDS = ["comment_id", "parent_id", "author", "published", "likes", "replies", "text"]


def fetch_comments(client: YouTubeClient, video_id: str, max_comments: int) -> list[dict]:
    rows: list[dict] = []
    page_token = None
    while len(rows) < max_comments:
        params = dict(part="snippet,replies", videoId=video_id, maxResults=100, order="relevance", textFormat="plainText")
        if page_token:
            params["pageToken"] = page_token
        data = client._get("commentThreads", **params)
        for thread in data.get("items", []):
            top = thread["snippet"]["topLevelComment"]
            rows.append(_row(top, parent_id="", replies=thread["snippet"].get("totalReplyCount", 0)))
            # l'API joint au plus 5 réponses par fil : suffisant pour voir les débats
            for reply in thread.get("replies", {}).get("comments", []):
                rows.append(_row(reply, parent_id=top["id"], replies=0))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return rows[:max_comments]


def _row(comment: dict, parent_id: str, replies: int) -> dict:
    s = comment["snippet"]
    return {
        "comment_id": comment["id"],
        "parent_id": parent_id,
        "author": s.get("authorDisplayName", ""),
        "published": s.get("publishedAt", ""),
        "likes": int(s.get("likeCount", 0)),
        "replies": replies,
        "text": s.get("textOriginal") or s.get("textDisplay", ""),
    }


def top_words(rows: list[dict], n: int = 25) -> list[tuple[str, int]]:
    words = Counter()
    for r in rows:
        tokens = re.findall(r"[a-zà-ÿ']{4,}", r["text"].lower())
        words.update(t for t in set(tokens) if t not in STOPWORDS)
    return words.most_common(n)


def main(argv: list[str] | None = None, client: YouTubeClient | None = None) -> int:
    p = argparse.ArgumentParser(description="Extrait les commentaires de vidéos YouTube.")
    p.add_argument("video_ids", nargs="+", help="IDs de vidéos, ex. y99SjQLmxmI")
    p.add_argument("--out", type=Path, default=Path("commentaires"), help="dossier des CSV")
    p.add_argument("--max", type=int, default=2000, help="commentaires max par vidéo (défaut 2000)")
    args = p.parse_args(argv)

    if client is None:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            print("Erreur : définis la variable d'environnement YOUTUBE_API_KEY.", file=sys.stderr)
            return 1
        client = YouTubeClient(api_key)

    args.out.mkdir(parents=True, exist_ok=True)
    for video_id in args.video_ids:
        try:
            rows = fetch_comments(client, video_id, args.max)
        except QuotaExceeded as exc:
            print(exc, file=sys.stderr)
            return 1
        except RuntimeError as exc:  # commentaires désactivés, vidéo privée…
            print(f"{video_id} : {exc}", file=sys.stderr)
            continue
        path = args.out / f"{video_id}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        top = [r for r in rows if not r["parent_id"]]
        print(f"\n=== {video_id} : {len(top)} commentaires, {len(rows) - len(top)} réponses -> {path}")
        print("Les plus aimés :")
        for r in sorted(top, key=lambda r: -r["likes"])[:10]:
            text = " ".join(r["text"].split())[:160]
            print(f"  {r['likes']:>6} ♥  {r['replies']:>3} rép.  {text}")
        print("Mots fréquents :", ", ".join(f"{w} ({c})" for w, c in top_words(rows)))

    print(f"\nQuota utilisé : ~{client.quota_used} unités.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
