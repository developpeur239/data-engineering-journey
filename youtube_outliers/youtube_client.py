"""Extract : client minimal de l'API YouTube Data v3."""

from __future__ import annotations

from datetime import datetime
from typing import Iterator

import requests

API_URL = "https://www.googleapis.com/youtube/v3"
BATCH_SIZE = 50  # maximum d'IDs par appel videos.list / channels.list


def chunked(seq: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


class YouTubeClient:
    """Coûts de quota : search = 100, videos / channels / playlistItems = 1 par appel."""

    def __init__(self, api_key: str, session: requests.Session | None = None):
        self.api_key = api_key
        self.session = session or requests.Session()
        self.quota_used = 0

    def _get(self, endpoint: str, cost: int = 1, **params) -> dict:
        params["key"] = self.api_key
        resp = self.session.get(f"{API_URL}/{endpoint}", params=params, timeout=30)
        self.quota_used += cost
        if resp.status_code != 200:
            raise RuntimeError(f"{endpoint} -> HTTP {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def search_videos(
        self, query: str, published_after: datetime, pages: int, region: str | None = None
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
            data = self._get("search", cost=100, **params)
            video_ids += [item["id"]["videoId"] for item in data.get("items", [])]
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return list(dict.fromkeys(video_ids))

    def recent_upload_ids(self, uploads_playlist: str, n: int) -> list[str]:
        """IDs des n dernières vidéos publiées par une chaîne (playlist « uploads »)."""
        try:
            data = self._get(
                "playlistItems", part="contentDetails", playlistId=uploads_playlist, maxResults=min(n, 50)
            )
        except RuntimeError:
            return []  # playlist privée ou supprimée
        return [item["contentDetails"]["videoId"] for item in data.get("items", [])]

    def videos(self, video_ids: list[str]) -> list[dict]:
        return self._batched("videos", video_ids, part="snippet,statistics,contentDetails")

    def channels(self, channel_ids: list[str]) -> list[dict]:
        return self._batched("channels", channel_ids, part="snippet,statistics,contentDetails")

    def _batched(self, endpoint: str, ids: list[str], part: str) -> list[dict]:
        items: list[dict] = []
        for chunk in chunked(ids, BATCH_SIZE):
            items += self._get(endpoint, part=part, id=",".join(chunk)).get("items", [])
        return items
