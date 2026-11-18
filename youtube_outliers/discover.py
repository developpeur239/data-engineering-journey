"""Mode découverte : balaie des mots-clés larges et fait émerger les niches qui explosent.

    export YOUTUBE_API_KEY="..."
    python discover.py --budget 5000 --csv decouverte.csv
    python discover.py "3d animation" "documentary" --lang fr --region FR

Différences avec find_outliers.py :
    - recherche sur les 30 derniers jours seulement (ce qui explose MAINTENANT)
    - pas de thème : le RPM vient de la catégorie YouTube de chaque chaîne
    - la niche et la concurrence viennent des titres des chaînes (discovery.py),
      pas du mot-clé de recherche
    - le balayage s'arrête avant de dépasser le budget de quota
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from discovery import channel_signature, competition_by_terms, drop_generic_terms, niche_label
from find_outliers import DEFAULT_RPM_FILE, analyze_niche, load_rpm, print_board, write_csv
from metrics import ChannelReport, Thresholds, rank_board
from youtube_client import QuotaExceeded, YouTubeClient

DEFAULT_KEYWORDS = Path(__file__).with_name("discovery_keywords.txt")
COST_PER_KEYWORD = 170  # estimation prudente : 100 (search) + ~70 (chaînes, dernières vidéos)


def read_keywords(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fait émerger les niches YouTube qui explosent en ce moment.")
    p.add_argument("keywords", nargs="*", help="mots-clés larges (défaut : discovery_keywords.txt)")
    p.add_argument("--keywords-file", type=Path, default=DEFAULT_KEYWORDS)
    p.add_argument("--days", type=int, default=30, help="vidéos publiées il y a moins de N jours (défaut 30)")
    p.add_argument("--months", type=int, default=12, help="chaînes créées il y a moins de N mois (défaut 12)")
    p.add_argument("--ratio", type=float, default=10, help="explosion minimale vues/abonnés (défaut 10)")
    p.add_argument("--max-subs", type=int, default=100_000)
    p.add_argument("--min-subs", type=int, default=1_000)
    p.add_argument("--recent", type=int, default=15, help="dernières vidéos analysées par chaîne (défaut 15)")
    p.add_argument("--lang", help="langue des résultats (relevanceLanguage), ex. fr, es, pt, de")
    p.add_argument("--region", help="code pays, ex. FR")
    p.add_argument("--budget", type=int, default=9_000, help="quota max à dépenser (défaut 9000 sur 10000/jour)")
    p.add_argument("--top", type=int, default=30, help="nombre de chaînes affichées (défaut 30)")
    p.add_argument("--rpm-file", type=Path, default=DEFAULT_RPM_FILE)
    p.add_argument("--csv", help="chemin d'export CSV (toutes les chaînes)")
    return p


def main(argv: list[str] | None = None, client: YouTubeClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    if client is None:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            print("Erreur : définis la variable d'environnement YOUTUBE_API_KEY.", file=sys.stderr)
            return 1
        client = YouTubeClient(api_key)

    keywords = args.keywords or read_keywords(args.keywords_file)
    now = datetime.now(timezone.utc)
    rpm = load_rpm(args.rpm_file)
    reports: dict[str, ChannelReport] = {}
    titles: dict[str, list[str]] = {}
    seen: set[str] = set()

    for i, keyword in enumerate(keywords, 1):
        if client.quota_used + COST_PER_KEYWORD > args.budget:
            print(f"Budget de {args.budget} unités atteint : arrêt après {i - 1} mot(s)-clé(s).")
            break
        before = len(reports)
        try:
            found = analyze_niche(
                client, keyword, theme="default", rpm=rpm,
                cutoff=now - timedelta(days=30 * args.months),
                search_after=now - timedelta(days=args.days),
                pages=1, region=args.region, language=args.lang,
                min_subs=args.min_subs, max_subs=args.max_subs, recent=args.recent,
                thresholds=Thresholds(ratio=args.ratio), now=now,
                exclude=seen, titles=titles,
            )
        except QuotaExceeded as exc:
            print(f"{exc} Arrêt : résultats partiels.")
            break
        for r in found:
            reports.setdefault(r.channel_id, r)
        seen |= {r.channel_id for r in found}
        print(f"[{i}/{len(keywords)}] « {keyword} » : +{len(reports) - before} chaîne(s), quota ~{client.quota_used}")

    # Les niches émergent des titres
    signatures = drop_generic_terms({cid: channel_signature(t) for cid, t in titles.items() if cid in reports})
    for cid, r in reports.items():
        r.niche = niche_label(signatures.get(cid, []))
    board = rank_board(list(reports.values()), competition=competition_by_terms(signatures))

    print(f"\n{len(board)} chaîne(s) outlier, quota utilisé ~{client.quota_used} unités.\n")
    print_board(board[: args.top])
    if args.csv:
        write_csv(board, args.csv)
        print(f"\nCSV écrit : {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
