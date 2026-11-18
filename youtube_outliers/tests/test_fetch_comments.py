import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import fetch_comments  # noqa: E402
from youtube_client import YouTubeClient  # noqa: E402


def comment(cid, text, likes):
    return {"id": cid, "snippet": {"authorDisplayName": "a", "publishedAt": "2026-11-01T00:00:00Z",
                                   "likeCount": likes, "textOriginal": text}}


class FakeComments(YouTubeClient):
    def __init__(self):
        super().__init__("fake")
        self.pages = [
            {"items": [{"snippet": {"topLevelComment": comment("c1", "New Zealand forever", 50), "totalReplyCount": 1},
                        "replies": {"comments": [comment("r1", "Same here", 3)]}}],
             "nextPageToken": "p2"},
            {"items": [{"snippet": {"topLevelComment": comment("c2", "Terrifying simulation", 900), "totalReplyCount": 0}}]},
        ]

    def _get(self, endpoint, cost=1, **params):
        self.quota_used += cost
        return self.pages[1 if params.get("pageToken") else 0]


class FetchCommentsTest(unittest.TestCase):
    def test_paginates_keeps_replies_and_writes_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = fetch_comments.main(["vid", "--out", tmp], client=FakeComments())
            self.assertEqual(code, 0)
            with open(Path(tmp) / "vid.csv", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual([r["comment_id"] for r in rows], ["c1", "r1", "c2"])
        self.assertEqual(rows[1]["parent_id"], "c1")
        out = buf.getvalue()
        self.assertIn("2 commentaires, 1 réponses", out)
        self.assertLess(out.index("Terrifying"), out.index("New Zealand"))  # trié par likes


if __name__ == "__main__":
    unittest.main()
