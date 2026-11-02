"""Repère les chaînes YouTube « outliers » : petites, récentes, avec au moins
une vidéo qui a fait beaucoup plus de vues que la chaîne n'a d'abonnés.

Critère par défaut : vues de la vidéo >= 10 x abonnés de la chaîne.

Pipeline (style ETL) :
    1. Extract   : search.list  -> vidéos récentes sur un mot-clé (100 unités de quota / page)
                   videos.list  -> vues de chaque vidéo        (1 unité / 50 vidéos)
                   channels.list -> abonnés, date de création   (1 unité / 50 chaînes)
    2. Transform : jointure vidéo <-> chaîne, filtres, meilleure vidéo par chaîne
    3. Load      : tableau dans le terminal + export CSV optionnel

Usage :
    export YOUTUBE_API_KEY="..."
    python find_outliers.py "3d reconstruction" --pages 2 --csv outliers.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Iterator

import requests

API_URL = "https://www.googleapis.com/youtube/v3"
BATCH_SIZE = 50  # maximum d'IDs par appel videos.list / channels.list


@dataclass
class Outlier:
    channel_id: str
    channel_title: str
    subscribers: int
    channel_videos: int
    channel_created: str
    top_video_title: str
    top_video_views: int
    ratio: float

    @property
    def channel_url(self) -> str:
        return f"https://www.youtube.com/channel/{self.channel_id}"


# --------------------------------------------------------------------------- #
# Extract
# --------------------------------------------------------------------------- #
class YouTubeClient:
    def __init__(self, api_key: str, session: requests.Session | None = None):
        self.api_key = api_key
        self.session = session or requests.Session()

    def _get(self, endpoint: str, **params) -> dict:
        params["key"] = self.api_key
        resp = self.session.get(f"{API_URL}/{endpoint}", params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"{endpoint} -> HTTP {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def search_videos(
        self, query: str, published_after: datetime, pages: int, region: str | None
    ) -> list[str]:
        """IDs des vidéos les plus vues publiées après `published_after`."""
        video_ids: list[str] = []
        page_token = None
        for _ in range(pages):
            params = dict(
                part="id",
                q=query,
                type="video",
                order="viewCount",
                maxResults=50,
                publishedAfter=published_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
            )
            if region:
                params["regionCode"] = region
            if page_token:
                params["pageToken"] = page_token
            data = self._get("search", **params)
            video_ids += [item["id"]["videoId"] for item in data.get("items", [])]
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return list(dict.fromkeys(video_ids))  # dédoublonne en gardant l'ordre

    def videos(self, video_ids: list[str]) -> list[dict]:
        return self._batched("videos", video_ids, part="snippet,statistics")

    def channels(self, channel_ids: list[str]) -> list[dict]:
        return self._batched("channels", channel_ids, part="snippet,statistics")

    def _batched(self, endpoint: str, ids: list[str], part: str) -> list[dict]:
        items: list[dict] = []
        for chunk in chunked(ids, BATCH_SIZE):
            items += self._get(endpoint, part=part, id=",".join(chunk)).get("items", [])
        return items


def chunked(seq: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


# --------------------------------------------------------------------------- #
# Transform (fonctions pures -> testables sans réseau)
# --------------------------------------------------------------------------- #
def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def find_outliers(
    videos: Iterable[dict],
    channels: Iterable[dict],
    *,
    min_ratio: float = 10.0,
    max_subs: int = 100_000,
    min_subs: int = 1_000,
    created_after: datetime | None = None,
) -> list[Outlier]:
    """Garde, pour chaque chaîne qui passe les filtres, sa meilleure vidéo."""
    channels_by_id = {c["id"]: c for c in channels}
    best: dict[str, Outlier] = {}

    for video in videos:
        channel = channels_by_id.get(video["snippet"]["channelId"])
        if channel is None:
            continue
        stats = channel.get("statistics", {})
        if stats.get("hiddenSubscriberCount"):
            continue  # impossible de calculer le ratio
        subs = int(stats.get("subscriberCount", 0))
        if not (min_subs <= subs <= max_subs):
            continue
        created = parse_date(channel["snippet"]["publishedAt"])
        if created_after and created < created_after:
            continue

        views = int(video.get("statistics", {}).get("viewCount", 0))
        ratio = views / subs
        if ratio < min_ratio:
            continue

        current = best.get(channel["id"])
        if current is None or views > current.top_video_views:
            best[channel["id"]] = Outlier(
                channel_id=channel["id"],
                channel_title=channel["snippet"]["title"],
                subscribers=subs,
                channel_videos=int(stats.get("videoCount", 0)),
                channel_created=created.date().isoformat(),
                top_video_title=video["snippet"]["title"],
                top_video_views=views,
                ratio=round(ratio, 1),
            )

    return sorted(best.values(), key=lambda o: o.ratio, reverse=True)


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def human(n: int) -> str:
    for unit, div in (("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return str(n)


def print_table(outliers: list[Outlier]) -> None:
    if not outliers:
        print("Aucune chaîne outlier trouvée. Essaie un autre mot-clé, plus de --pages ou --months.")
        return
    print(f"{'Ratio':>7}  {'Abonnés':>8}  {'Vues top':>8}  {'Vidéos':>6}  {'Créée':>10}  Chaîne")
    for o in outliers:
        print(
            f"{o.ratio:>6.1f}x  {human(o.subscribers):>8}  {human(o.top_video_views):>8}  "
            f"{o.channel_videos:>6}  {o.channel_created:>10}  {o.channel_title}  {o.channel_url}"
        )


def write_csv(outliers: list[Outlier], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        fields = list(Outlier.__dataclass_fields__) + ["channel_url"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for o in outliers:
            writer.writerow({**asdict(o), "channel_url": o.channel_url})


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Trouve les chaînes YouTube outliers d'un format.")
    p.add_argument("query", help='mot-clé du format, ex. "3d reconstruction"')
    p.add_argument("--ratio", type=float, default=10.0, help="vues / abonnés minimum (défaut 10)")
    p.add_argument("--max-subs", type=int, default=100_000, help="abonnés max (défaut 100K)")
    p.add_argument("--min-subs", type=int, default=1_000, help="abonnés min (défaut 1K)")
    p.add_argument("--months", type=int, default=12, help="vidéos et chaînes de moins de N mois (défaut 12)")
    p.add_argument("--pages", type=int, default=1, help="pages de recherche, 100 unités de quota chacune (défaut 1)")
    p.add_argument("--region", help="code pays, ex. FR ou US")
    p.add_argument("--csv", help="chemin d'export CSV")
    args = p.parse_args(argv)

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("Erreur : définis la variable d'environnement YOUTUBE_API_KEY.", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=30 * args.months)
    client = YouTubeClient(api_key)

    video_ids = client.search_videos(args.query, cutoff, args.pages, args.region)
    videos = client.videos(video_ids)
    channel_ids = list(dict.fromkeys(v["snippet"]["channelId"] for v in videos))
    channels = client.channels(channel_ids)

    outliers = find_outliers(
        videos,
        channels,
        min_ratio=args.ratio,
        max_subs=args.max_subs,
        min_subs=args.min_subs,
        created_after=cutoff,
    )
    print(f"{len(video_ids)} vidéos analysées, {len(channels)} chaînes, {len(outliers)} outliers.\n")
    print_table(outliers)
    if args.csv:
        write_csv(outliers, args.csv)
        print(f"\nCSV écrit : {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
