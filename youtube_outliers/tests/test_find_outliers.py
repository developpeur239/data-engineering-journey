import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from find_outliers import human, main, parse_niche  # noqa: E402
from metrics import (  # noqa: E402
    Channel,
    ChannelReport,
    Thresholds,
    Video,
    analyze_channel,
    channel_format,
    parse_duration,
    rank_board,
    tier,
    trend_label,
)
from youtube_client import YouTubeClient  # noqa: E402

NOW = datetime(2026, 11, 1, tzinfo=timezone.utc)


def vid(views, days_ago, duration=600, cid="c1", title="v"):
    return Video(f"v{views}_{days_ago}", cid, title, NOW - timedelta(days=days_ago), views, duration)


def chan(subs=5_000, cid="c1"):
    return Channel(cid, "Chaîne", subs, 20, NOW - timedelta(days=60), "UU" + cid)


def analyze(channel, videos, **kw):
    return analyze_channel(channel, videos, niche="n", rpm_long=10, rpm_short=0.4, now=NOW, **kw)


class ParsingTest(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(parse_duration("PT1M30S"), 90)
        self.assertEqual(parse_duration("PT1H2M"), 3720)
        self.assertEqual(parse_duration("P1DT1S"), 86401)
        self.assertEqual(parse_duration("P0D"), 0)
        self.assertEqual(parse_duration(""), 0)

    def test_parse_niche(self):
        self.assertEqual(parse_niche("3d news=news"), ("3d news", "news"))
        self.assertEqual(parse_niche("stickman"), ("stickman", "default"))

    def test_human(self):
        self.assertEqual(human(3_200_000), "3.2M")
        self.assertEqual(human(999), "999")


class CriteriaTest(unittest.TestCase):
    def test_blowup_uses_latest_hit_not_biggest(self):
        videos = [vid(5_000_000, 60, title="vieux gros"), vid(600_000, 3, title="récent"), vid(1_000, 1)]
        r = analyze(chan(5_000), videos)
        self.assertEqual(r.latest_hit_title, "récent")
        self.assertEqual(r.blowup, 120.0)
        self.assertEqual(r.latest_hit_days_ago, 3)

    def test_no_hit_above_ratio_is_rejected(self):
        self.assertIsNone(analyze(chan(5_000), [vid(400_000, 2)]))  # 80x < 100x
        self.assertIsNotNone(analyze(chan(5_000), [vid(400_000, 2)], thresholds=Thresholds(ratio=10)))

    def test_trend(self):
        t = Thresholds()
        heating = [vid(100_000, d) for d in range(5)] + [vid(10_000, d) for d in range(5, 15)]
        cooling = [vid(10_000, d) for d in range(5)] + [vid(100_000, d) for d in range(5, 15)]
        self.assertEqual(trend_label(heating, t), "chauffe")
        self.assertEqual(trend_label(cooling, t), "refroidit")
        self.assertEqual(trend_label(heating[:4], t), "n/a")

    def test_one_hit_and_regularity(self):
        one_hit = [vid(6_200_000, 20)] + [vid(30_000, d) for d in range(1, 10)]
        r = analyze(chan(20_000), one_hit)
        self.assertTrue(r.one_hit)
        self.assertEqual(r.share_above_hit_views, 0.1)

        regular = [vid(80_000 + d, d) for d in range(10)]
        r = analyze(chan(500), regular)
        self.assertFalse(r.one_hit)
        self.assertEqual(r.share_above_hit_views, 1.0)

    def test_format(self):
        self.assertEqual(channel_format([vid(1, 1, 45)] * 8 + [vid(1, 1, 900)] * 2), "short")
        self.assertEqual(channel_format([vid(1, 1, 900)] * 9 + [vid(1, 1, 45)]), "long")
        self.assertEqual(channel_format([vid(1, 1, 45), vid(1, 1, 900)]), "mixte")

    def test_revenue_last_30_days_with_rpm_per_format(self):
        videos = [vid(1_000_000, 5, 900), vid(1_000_000, 10, 40), vid(9_000_000, 45, 900)]
        r = analyze(chan(5_000), videos)
        self.assertEqual(r.views_30d, 2_000_000)  # la vidéo de 45 jours est exclue
        self.assertEqual(r.revenue_30d, 10_000 + 400)  # 1M x 10$ + 1M x 0,40$


class BoardTest(unittest.TestCase):
    def report(self, niche, blowup, revenue, **kw):
        defaults = dict(
            channel_id=f"{niche}{blowup}", channel_title="c", subscribers=5_000, channel_created="2026-09-01",
            videos_analyzed=15, latest_hit_title="t", latest_hit_views=1, latest_hit_days_ago=1,
            median_views=1, share_above_hit_views=0.8, one_hit=False, trend="chauffe", format="long",
            views_30d=1,
        )
        defaults.update(kw)
        return ChannelReport(niche=niche, blowup=blowup, revenue_30d=revenue, **defaults)

    def test_competition_and_tiers(self):
        crowded = [self.report("crowd", 500, 9_000) for _ in range(5)]
        for i, r in enumerate(crowded):
            r.channel_id += str(i)
        alone = self.report("alone", 240, 10_000)
        board = rank_board(crowded + [alone])
        self.assertIs(board[0], alone)
        self.assertEqual(alone.competition, 1)
        self.assertEqual(crowded[0].competition, 5)
        # alone : 2 (explosion) + 3 ($) + 2 (régularité) + 1 (chauffe) + 2 (seule) = 10 -> S
        self.assertEqual((alone.score, alone.tier), (10, "S"))
        # crowd : 3 + 2 + 2 + 1 + 0 = 8 -> A
        self.assertEqual((crowded[0].score, crowded[0].tier), (8, "A"))

    def test_tier_thresholds(self):
        self.assertEqual([tier(p) for p in (9, 7, 5, 4)], ["S", "A", "B", "C"])


class FakeClient(YouTubeClient):
    """Simule l'API : une niche, une petite chaîne qui explose, une grosse chaîne ignorée."""

    def __init__(self):
        super().__init__("fake")
        recent = (NOW - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.data = {
            "search": {"items": [{"id": {"videoId": "hit"}}, {"id": {"videoId": "big"}}]},
            "channels": {"items": [
                self._channel("small", 3_000), self._channel("giant", 2_000_000),
            ]},
            "playlistItems": {"items": [{"contentDetails": {"videoId": "hit"}}]},
            "videos": {"items": [
                self._video("hit", "small", 630_000, recent), self._video("big", "giant", 9_000_000, recent),
            ]},
        }

    @staticmethod
    def _channel(cid, subs):
        created = (datetime.now(timezone.utc) - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {"id": cid, "snippet": {"title": cid, "publishedAt": created},
                "statistics": {"subscriberCount": str(subs), "videoCount": "3"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU" + cid}}}

    @staticmethod
    def _video(vid_id, cid, views, published):
        return {"id": vid_id, "snippet": {"channelId": cid, "title": vid_id, "publishedAt": published},
                "statistics": {"viewCount": str(views)}, "contentDetails": {"duration": "PT8M"}}

    def _get(self, endpoint, cost=1, **params):
        self.quota_used += cost
        return self.data[endpoint]


class EndToEndTest(unittest.TestCase):
    def test_cli_with_fake_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_csv = Path(tmp) / "board.csv"
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = main(["3d news=news", "--csv", str(out_csv)], client=FakeClient())
            self.assertEqual(code, 0)
            with out_csv.open(encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        self.assertEqual([r["channel_id"] for r in rows], ["small"])  # la grosse chaîne est filtrée
        self.assertEqual(rows[0]["blowup"], "210.0")
        self.assertEqual(rows[0]["revenue_30d"], "6300.0")  # 630K x 10 $ (RPM news)
        self.assertEqual(rows[0]["buildable_by_claude"], "")
        self.assertIn("small", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
