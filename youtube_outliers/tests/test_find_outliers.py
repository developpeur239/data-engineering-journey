import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from find_outliers import find_outliers, human  # noqa: E402


def channel(cid, subs, created="2026-05-01T00:00:00Z", hidden=False, videos=10):
    return {
        "id": cid,
        "snippet": {"title": f"Chaîne {cid}", "publishedAt": created},
        "statistics": {
            "subscriberCount": str(subs),
            "videoCount": str(videos),
            "hiddenSubscriberCount": hidden,
        },
    }


def video(cid, views, title="v"):
    return {"snippet": {"channelId": cid, "title": title}, "statistics": {"viewCount": str(views)}}


class FindOutliersTest(unittest.TestCase):
    def test_keeps_channel_above_ratio(self):
        result = find_outliers([video("a", 300_000)], [channel("a", 20_000)])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].ratio, 15.0)

    def test_rejects_below_ratio(self):
        self.assertEqual(find_outliers([video("a", 150_000)], [channel("a", 20_000)]), [])

    def test_rejects_big_channels(self):
        self.assertEqual(find_outliers([video("a", 50_000_000)], [channel("a", 2_000_000)]), [])

    def test_rejects_hidden_subscribers_and_tiny_channels(self):
        chans = [channel("a", 20_000, hidden=True), channel("b", 10)]
        self.assertEqual(find_outliers([video("a", 10**7), video("b", 10**6)], chans), [])

    def test_rejects_old_channels(self):
        cutoff = datetime(2026, 1, 1, tzinfo=timezone.utc)
        chans = [channel("a", 20_000, created="2019-01-01T00:00:00Z")]
        self.assertEqual(find_outliers([video("a", 10**6)], chans, created_after=cutoff), [])

    def test_keeps_best_video_per_channel_and_sorts_by_ratio(self):
        vids = [video("a", 300_000, "petit"), video("a", 900_000, "gros"), video("b", 2_000_000)]
        result = find_outliers(vids, [channel("a", 20_000), channel("b", 50_000)])
        self.assertEqual([o.channel_id for o in result], ["a", "b"])  # 45x puis 40x
        self.assertEqual(result[0].top_video_title, "gros")

    def test_human(self):
        self.assertEqual(human(3_200_000), "3.2M")
        self.assertEqual(human(20_600), "20.6K")
        self.assertEqual(human(999), "999")


if __name__ == "__main__":
    unittest.main()
