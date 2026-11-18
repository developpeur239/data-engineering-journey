"""Répartition des commentaires d'une vidéo par thème : volume, likes, réponses, timing.

    python analyze_comments.py commentaires/y99SjQLmxmI.csv --published 2026-10-21T13:13:18Z

Question posée : les commentaires « provoqués » par un choix ou une erreur du créateur
(voix IA qui se trompe, faute dans le titre, fin mémorable) pèsent-ils dans l'engagement ?
Les thèmes sont dans comment_themes.json (expressions régulières, modifiables).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_THEMES = Path(__file__).with_name("comment_themes.json")


def load_themes(path: Path) -> dict[str, dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        name: {"provoque": t["provoque"], "regex": re.compile(t["regex"])}
        for name, t in raw.items() if not name.startswith("_")
    }


def classify(text: str, themes: dict[str, dict]) -> list[str]:
    low = text.lower()
    return [name for name, t in themes.items() if t["regex"].search(low)] or ["Autre"]


def build_threads(rows: list[dict], themes: dict[str, dict]) -> list[dict]:
    """Un fil = commentaire principal + ses réponses. Le thème est celui du commentaire principal."""
    replies = defaultdict(list)
    for r in rows:
        if r["parent_id"]:
            replies[r["parent_id"]].append(r)
    threads = []
    for r in rows:
        if r["parent_id"]:
            continue
        rep = replies.get(r["comment_id"], [])
        threads.append({
            "text": r["text"],
            "published": datetime.fromisoformat(r["published"].replace("Z", "+00:00")),
            "likes": int(r["likes"]),
            "replies": max(int(r["replies"]), len(rep)),
            "reply_likes": sum(int(x["likes"]) for x in rep),
            "themes": classify(r["text"], themes),
        })
    return threads


def distribution(threads: list[dict], themes: dict[str, dict]) -> list[dict]:
    """Par thème : part des fils, des likes et des réponses. Un fil multi-thèmes compte dans chacun."""
    total = {
        "threads": len(threads),
        "likes": sum(t["likes"] + t["reply_likes"] for t in threads) or 1,
        "replies": sum(t["replies"] for t in threads) or 1,
    }
    out = []
    for name in [*themes, "Autre"]:
        sel = [t for t in threads if name in t["themes"]]
        if not sel:
            continue
        likes = sum(t["likes"] + t["reply_likes"] for t in sel)
        replies = sum(t["replies"] for t in sel)
        out.append({
            "theme": name,
            "provoque": themes.get(name, {}).get("provoque", False),
            "threads": len(sel),
            "share_threads": len(sel) / total["threads"],
            "share_likes": likes / total["likes"],
            "share_replies": replies / total["replies"],
            "avg_likes": likes / len(sel),
            "avg_replies": replies / len(sel),
        })
    return sorted(out, key=lambda d: -d["share_likes"])


def provoked_summary(threads: list[dict], themes: dict[str, dict]) -> dict:
    """Part de l'engagement total qui vient des fils « provoqués » (au moins un thème provoqué)."""
    prov = {n for n, t in themes.items() if t["provoque"]}
    sel = [t for t in threads if prov & set(t["themes"])]
    eng = lambda ts: sum(1 + t["replies"] + t["likes"] + t["reply_likes"] for t in ts)  # noqa: E731
    total = eng(threads) or 1
    return {"threads": len(sel), "share_threads": len(sel) / max(len(threads), 1), "share_engagement": eng(sel) / total}


def by_day(threads: list[dict], published: datetime, themes: dict[str, dict]) -> list[tuple[int, int, float]]:
    """(jour depuis la publication, nb de fils, part de fils provoqués)."""
    prov = {n for n, t in themes.items() if t["provoque"]}
    days = defaultdict(list)
    for t in threads:
        days[(t["published"] - published).days].append(t)
    return [(d, len(ts), sum(bool(prov & set(t["themes"])) for t in ts) / len(ts)) for d, ts in sorted(days.items())]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Répartition des commentaires par thème.")
    p.add_argument("csv", type=Path, help="CSV produit par fetch_comments.py")
    p.add_argument("--themes", type=Path, default=DEFAULT_THEMES)
    p.add_argument("--published", help="date de publication ISO, pour la répartition par jour")
    args = p.parse_args(argv)

    themes = load_themes(args.themes)
    with open(args.csv, encoding="utf-8") as f:
        threads = build_threads(list(csv.DictReader(f)), themes)
    if not threads:
        print("Aucun commentaire.")
        return 0

    print(f"{args.csv.stem} : {len(threads)} fils, {sum(t['replies'] for t in threads)} réponses\n")
    print(f"{'Thème':26} {'Prov.':>5} {'Fils':>5} {'%fils':>6} {'%likes':>7} {'%rép.':>6} {'♥/fil':>6} {'rép/fil':>7}")
    for d in distribution(threads, themes):
        print(f"{d['theme']:26} {'oui' if d['provoque'] else '':>5} {d['threads']:>5} {d['share_threads']:>6.1%} "
              f"{d['share_likes']:>7.1%} {d['share_replies']:>6.1%} {d['avg_likes']:>6.1f} {d['avg_replies']:>7.1f}")
    s = provoked_summary(threads, themes)
    print(f"\nFils provoqués : {s['threads']} ({s['share_threads']:.1%} des fils) "
          f"-> {s['share_engagement']:.1%} de l'engagement (commentaires + réponses + likes)")
    if args.published:
        pub = datetime.fromisoformat(args.published.replace("Z", "+00:00"))
        print("\nJour  Fils  %provoqués")
        for d, n, share in by_day(threads, pub, themes):
            print(f"J{d:<4} {n:>4}  {share:>6.0%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
