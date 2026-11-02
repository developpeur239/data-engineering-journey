"""Tableau des niches YouTube : repère les petites chaînes qui explosent et les classe S/A/B/C.

Pipeline (style ETL) :
    1. Extract   : pour chaque niche, recherche des vidéos les plus vues (search.list),
                   puis les chaînes (channels.list) et leurs N dernières vidéos
                   (playlistItems.list + videos.list).
    2. Transform : critères par chaîne (metrics.py) : explosion du dernier succès,
                   régularité, tendance, Short ou vidéo longue, revenu estimé, concurrence.
    3. Load      : tableau classé dans le terminal + export CSV optionnel.

Usage :
    export YOUTUBE_API_KEY="..."
    python find_outliers.py "3d news reconstruction=news" "ai takeover documentary=tech" \
        "stickman battle=entertainment" --csv board.csv

Une niche s'écrit "mot-clé=thème". Le thème choisit le RPM des vidéos longues dans rpm.json,
sauf si la catégorie YouTube de la chaîne le contredit (la chaîne est alors marquée « hors niche »).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from metrics import (
    ChannelReport,
    RpmTable,
    Thresholds,
    analyze_channel,
    channel_from_api,
    rank_board,
    video_from_api,
)
from youtube_client import YouTubeClient

DEFAULT_RPM_FILE = Path(__file__).with_name("rpm.json")
TREND_ICONS = {"chauffe": "🔥", "refroidit": "❄️", "stable": "➖", "n/a": "?"}


def parse_niche(arg: str) -> tuple[str, str]:
    query, _, theme = arg.partition("=")
    return query.strip(), (theme.strip() or "default")


def load_rpm(path: Path, rpm_long: float | None = None, rpm_short: float | None = None) -> RpmTable:
    """Table des RPM ; --rpm-long / --rpm-short écrasent toutes les valeurs correspondantes."""
    table = json.loads(path.read_text(encoding="utf-8"))
    long_table = {k: float(rpm_long if rpm_long is not None else v) for k, v in table["long"].items()}
    return RpmTable(short=float(table["short"] if rpm_short is None else rpm_short), long=long_table)


# --------------------------------------------------------------------------- #
# Extract + Transform
# --------------------------------------------------------------------------- #
def analyze_niche(
    client: YouTubeClient,
    query: str,
    *,
    theme: str,
    rpm: RpmTable,
    cutoff: datetime,
    pages: int,
    region: str | None,
    min_subs: int,
    max_subs: int,
    recent: int,
    thresholds: Thresholds,
    now: datetime,
) -> list[ChannelReport]:
    # 1. Vidéos les plus vues de la niche -> chaînes candidates
    found = client.videos(client.search_videos(query, cutoff, pages, region))
    channel_ids = list(dict.fromkeys(v["snippet"]["channelId"] for v in found))
    channels = [c for c in map(channel_from_api, client.channels(channel_ids)) if c]
    channels = [c for c in channels if min_subs <= c.subscribers <= max_subs and c.created >= cutoff]

    # 2. Dernières vidéos de chaque chaîne candidate
    upload_ids = [vid for c in channels for vid in client.recent_upload_ids(c.uploads_playlist, recent)]
    by_channel: dict[str, list] = {}
    for item in client.videos(upload_ids):
        video = video_from_api(item)
        by_channel.setdefault(video.channel_id, []).append(video)

    # 3. Critères
    reports = []
    for c in channels:
        report = analyze_channel(
            c,
            by_channel.get(c.channel_id, []),
            niche=query,
            theme=theme,
            rpm=rpm,
            thresholds=thresholds,
            now=now,
        )
        if report:
            reports.append(report)
    return reports


# --------------------------------------------------------------------------- #
# Load
# --------------------------------------------------------------------------- #
def human(n: float) -> str:
    for unit, div in (("M", 1_000_000), ("K", 1_000)):
        if n >= div:
            return f"{n / div:.1f}{unit}"
    return f"{n:.0f}"


def print_board(board: list[ChannelReport]) -> None:
    if not board:
        print("Aucune chaîne outlier. Essaie --ratio 10, plus de --pages, --months ou d'autres mots-clés.")
        return
    header = (
        f"{'Tier':<4} {'Pts':>3}  {'Explos.':>7} {'Abonnés':>7} {'Dern. succès':>14} {'Médiane':>7} "
        f"{'≥50K':>4} {'Tend.':>5} {'Format':>6} {'$/30j':>7} {'$récur.':>7} {'Conc.':>5}  Chaîne · Niche"
    )
    print(header)
    print("-" * len(header))
    for r in board:
        hit = f"{human(r.latest_hit_views)} {r.latest_hit_days_ago}j"
        flag = (" ⚠️1 carton" if r.one_hit else "") + ("" if r.monetizable else " 🚫non monétisable")
        if r.off_niche:
            flag += f" ⚠️hors niche ({r.category} → RPM {r.theme_used})"
        print(
            f"{r.tier:<4} {r.score:>3}  {r.blowup:>6.0f}x {human(r.subscribers):>7} {hit:>14} "
            f"{human(r.median_views):>7} {r.share_above_hit_views:>4.0%} {TREND_ICONS[r.trend]:>5} "
            f"{r.format:>6} {human(r.revenue_30d):>7} {human(r.revenue_recurring_30d):>7} {r.competition:>5}  "
            f"{r.channel_title} · {r.niche}{flag}\n{'':>6}{r.channel_url}"
        )
    print("\nColonne « faisable par Claude » : à remplir à la main dans le CSV.")


def write_csv(board: list[ChannelReport], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        fields = list(ChannelReport.__dataclass_fields__) + ["channel_url"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in board:
            writer.writerow({**asdict(r), "channel_url": r.channel_url})


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Classe les petites chaînes YouTube qui explosent, niche par niche.")
    p.add_argument("niches", nargs="+", help='une ou plusieurs niches "mot-clé=thème", ex. "3d news=news"')
    p.add_argument("--ratio", type=float, default=100, help="explosion min. du dernier succès, vues/abonnés (défaut 100)")
    p.add_argument("--hit-views", type=int, default=50_000, help="seuil de régularité en vues (défaut 50K)")
    p.add_argument("--max-subs", type=int, default=100_000, help="abonnés max (défaut 100K)")
    p.add_argument("--min-subs", type=int, default=1_000, help="abonnés min (défaut 1K)")
    p.add_argument("--months", type=int, default=12, help="chaînes créées il y a moins de N mois (défaut 12)")
    p.add_argument("--recent", type=int, default=15, help="nombre de dernières vidéos analysées, max 50 (défaut 15)")
    p.add_argument("--pages", type=int, default=1, help="pages de recherche par niche, 100 unités chacune (défaut 1)")
    p.add_argument("--region", help="code pays, ex. FR ou US")
    p.add_argument("--rpm-file", type=Path, default=DEFAULT_RPM_FILE, help="table des RPM (défaut rpm.json)")
    p.add_argument("--rpm-long", type=float, help="force le RPM des vidéos longues ($)")
    p.add_argument("--rpm-short", type=float, help="force le RPM des Shorts ($)")
    p.add_argument("--csv", help="chemin d'export CSV")
    return p


def main(argv: list[str] | None = None, client: YouTubeClient | None = None) -> int:
    args = build_parser().parse_args(argv)

    if client is None:
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            print("Erreur : définis la variable d'environnement YOUTUBE_API_KEY.", file=sys.stderr)
            return 1
        client = YouTubeClient(api_key)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30 * args.months)
    thresholds = Thresholds(ratio=args.ratio, hit_views=args.hit_views)

    rpm = load_rpm(args.rpm_file, args.rpm_long, args.rpm_short)
    reports: list[ChannelReport] = []
    for arg in args.niches:
        query, theme = parse_niche(arg)
        if theme not in rpm.long:
            print(f"Thème inconnu « {theme} » : RPM par défaut utilisé.", file=sys.stderr)
        found = analyze_niche(
            client,
            query,
            theme=theme,
            rpm=rpm,
            cutoff=cutoff,
            pages=args.pages,
            region=args.region,
            min_subs=args.min_subs,
            max_subs=args.max_subs,
            recent=args.recent,
            thresholds=thresholds,
            now=now,
        )
        off = sum(r.off_niche for r in found)
        print(
            f"« {query} » ({theme}, RPM long {rpm.long_for(theme)} $ / short {rpm.short} $) : "
            f"{len(found) - off} chaîne(s) outlier dans la niche, {off} hors niche"
        )
        reports += found

    board = rank_board(reports)
    print(f"\nQuota utilisé : ~{client.quota_used} unités sur 10 000 / jour.\n")
    print_board(board)
    if args.csv:
        write_csv(board, args.csv)
        print(f"\nCSV écrit : {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
