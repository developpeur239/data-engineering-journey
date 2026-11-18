import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import discover  # noqa: E402
from discovery import (  # noqa: E402
    channel_signature,
    competition_by_terms,
    drop_generic_terms,
    niche_label,
    tokenize,
)
from test_find_outliers import FakeClient  # noqa: E402
from youtube_client import QuotaExceeded  # noqa: E402


class DiscoveryTest(unittest.TestCase):
    def test_tokenize_drops_stopwords_and_digits(self):
        self.assertEqual(tokenize("What if a Tungsten Rod hit Earth in 2030? #shorts"), ["tungsten", "rod", "hit", "earth"])

    def test_signature_prefers_bigrams_and_skips_covered_words(self):
        titles = ["Tungsten rod hits Paris", "Tungsten rod vs the Moon", "Tungsten rod from space", "Random title"]
        sig = channel_signature(titles)
        self.assertEqual(sig[0], "tungsten rod")
        self.assertNotIn("tungsten", sig)

    def test_signature_needs_recurring_terms(self):
        self.assertEqual(channel_signature(["Ocean secrets", "Desert facts", "City at night"]), [])

    def test_generic_terms_removed_when_enough_channels(self):
        sigs = {f"c{i}": ["mystery", f"term{i}"] for i in range(10)}
        cleaned = drop_generic_terms(sigs)
        self.assertEqual(cleaned["c0"], ["term0"])

    def test_competition_by_shared_terms(self):
        sigs = {"a": ["tungsten rod"], "b": ["tungsten rod", "space"], "c": ["bodycam"], "d": []}
        self.assertEqual(competition_by_terms(sigs), {"a": 2, "b": 2, "c": 1, "d": 2})
        self.assertEqual(niche_label(["tungsten rod", "space", "x"]), "tungsten rod · space")
        self.assertEqual(niche_label([]), "(titres variés)")


class QuotaClient(FakeClient):
    """Quota épuisé au deuxième mot-clé."""

    def _get(self, endpoint, cost=1, **params):
        if endpoint == "search" and self.quota_used >= 100:
            raise QuotaExceeded("Quota épuisé.")
        return super()._get(endpoint, cost, **params)


class DiscoverCliTest(unittest.TestCase):
    def run_cli(self, argv, client):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = discover.main(argv, client=client)
        return code, buf.getvalue()

    def test_budget_stops_the_sweep(self):
        code, out = self.run_cli(["k1", "k2", "k3", "--budget", "200"], FakeClient())
        self.assertEqual(code, 0)
        self.assertIn("arrêt après 1 mot(s)-clé(s)", out)

    def test_quota_exceeded_keeps_partial_results(self):
        code, out = self.run_cli(["k1", "k2"], QuotaClient())
        self.assertEqual(code, 0)
        self.assertIn("résultats partiels", out)
        self.assertIn("1 chaîne(s) outlier", out)


if __name__ == "__main__":
    unittest.main()
