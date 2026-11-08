import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analyze_comments import (  # noqa: E402
    DEFAULT_THEMES,
    build_threads,
    classify,
    distribution,
    load_themes,
    provoked_summary,
)


def row(cid, text, likes, parent="", replies=0):
    return {"comment_id": cid, "parent_id": parent, "text": text, "likes": likes,
            "replies": replies, "published": "2026-10-22T00:00:00Z"}


class AnalyzeCommentsTest(unittest.TestCase):
    def setUp(self):
        self.themes = load_themes(DEFAULT_THEMES)

    def test_classify(self):
        self.assertIn("Erreur de la voix IA", classify("hotter than the center of the Sunday lol", self.themes))
        self.assertIn("Fin : Nouvelle-Zélande", classify("New Zealander here, spare bedroom", self.themes))
        self.assertEqual(classify("ok", self.themes), ["Autre"])

    def test_distribution_and_provoked_share(self):
        rows = [
            row("a", "the Sunday 😂", 90, replies=2), row("r1", "haha", 10, parent="a"), row("r2", "lol", 0, parent="a"),
            row("b", "nice", 0), row("c", "ok", 0),
        ]
        threads = build_threads(rows, self.themes)
        self.assertEqual(len(threads), 3)
        dist = {d["theme"]: d for d in distribution(threads, self.themes)}
        self.assertAlmostEqual(dist["Erreur de la voix IA"]["share_likes"], 1.0)
        self.assertAlmostEqual(dist["Erreur de la voix IA"]["share_replies"], 1.0)
        s = provoked_summary(threads, self.themes)
        # engagement = 1 + réponses + likes : a = 1+2+100 = 103, b = c = 1 -> 103/105
        self.assertAlmostEqual(s["share_engagement"], 103 / 105)
        self.assertAlmostEqual(s["share_threads"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
