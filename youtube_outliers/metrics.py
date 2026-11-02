"""Transform : calcul des critères par chaîne et classement S/A/B/C.

Fonctions pures, sans réseau, donc testables.

Critères (repris de la vidéo « 13 faceless niches ») :
    - explosion    : vues du DERNIER succès / abonnés (seuil par défaut 100)
    - régularité   : médiane des vues récentes, part des vidéos >= 50K, drapeau « un seul carton »
    - tendance     : médiane des 5 dernières vidéos / médiane des précédentes
    - format       : Shorts (<= 3 min) ou vidéos longues
    - argent       : vues des 30 derniers jours x RPM (table par thème et par format).
                     Le score utilise le revenu « récurrent » : sans les cartons isolés,
                     et à 0 si la chaîne n'a pas les 1 000 abonnés pour être monétisée.
    - catégorie    : catégorie YouTube dominante des vidéos. Si elle contredit le thème
                     demandé (ex. « Film & Animation » pour une niche tech), la chaîne est
                     marquée « hors niche » et son RPM vient de la catégorie détectée.
    - concurrence  : nombre de chaînes outliers DANS la niche (hors-niche exclues)
    - Claude       : faisable en code ? -> laissé vide, à remplir à la main
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from statistics import median

SHORT_MAX_SECONDS = 180  # YouTube accepte des Shorts jusqu'à 3 minutes
MONETIZATION_MIN_SUBS = 1_000  # minimum du Programme Partenaire YouTube

# Catégories YouTube (snippet.categoryId) -> (nom, thème RPM).
# 22 « People & Blogs » est la catégorie par défaut à l'upload : elle ne dit rien, thème None.
CATEGORIES: dict[str, tuple[str, str | None]] = {
    "1": ("Film & Animation", "entertainment"),
    "2": ("Autos", None),
    "10": ("Musique", "entertainment"),
    "15": ("Animaux", "entertainment"),
    "17": ("Sport", "entertainment"),
    "19": ("Voyages", None),
    "20": ("Jeux vidéo", "entertainment"),
    "22": ("People & Blogs", None),
    "23": ("Humour", "entertainment"),
    "24": ("Divertissement", "entertainment"),
    "25": ("Actualités", "news"),
    "26": ("Tutoriels", "education"),
    "27": ("Éducation", "education"),
    "28": ("Science & Tech", "science"),
    "29": ("Associatif", None),
}

# Deux familles suffisent : c'est l'écart de RPM divertissement / informatif qui compte.
THEME_FAMILY = {
    "entertainment": "divertissement",
    "horror": "divertissement",
    "news": "informatif",
    "education": "informatif",
    "finance": "informatif",
    "science": "informatif",
    "tech": "informatif",
}

_DURATION_RE = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$")


# --------------------------------------------------------------------------- #
# Modèles
# --------------------------------------------------------------------------- #
@dataclass
class Video:
    video_id: str
    channel_id: str
    title: str
    published: datetime
    views: int
    duration_s: int
    category_id: str = ""

    @property
    def is_short(self) -> bool:
        return 0 < self.duration_s <= SHORT_MAX_SECONDS


@dataclass
class Channel:
    channel_id: str
    title: str
    subscribers: int
    video_count: int
    created: datetime
    uploads_playlist: str


@dataclass
class Thresholds:
    ratio: float = 100.0        # explosion minimale du dernier succès
    hit_views: int = 50_000     # seuil « vidéo qui marche » pour la régularité
    one_hit_factor: float = 50  # vidéo >= 50 x médiane -> carton isolé
    heating: float = 1.2        # tendance : au-dessus -> chauffe
    cooling: float = 0.8        # tendance : en dessous -> refroidit


@dataclass
class RpmTable:
    """RPM en $ pour 1 000 vues : un pour les Shorts, un par thème pour les vidéos longues."""

    short: float
    long: dict[str, float] = field(default_factory=lambda: {"default": 5.0})

    def long_for(self, theme: str) -> float:
        return self.long.get(theme, self.long["default"])


@dataclass
class ChannelReport:
    niche: str
    channel_id: str
    channel_title: str
    subscribers: int
    channel_created: str
    videos_analyzed: int
    latest_hit_title: str
    latest_hit_views: int
    latest_hit_days_ago: int
    blowup: float
    median_views: int
    share_above_hit_views: float
    one_hit: bool
    trend: str
    format: str
    views_30d: int
    revenue_30d: float
    revenue_recurring_30d: float
    monetizable: bool
    theme_requested: str = "default"
    category: str = ""
    theme_used: str = "default"
    off_niche: bool = False
    competition: int = 0
    score: int = 0
    tier: str = ""
    buildable_by_claude: str = ""  # à remplir à la main : oui / non / partiel

    @property
    def channel_url(self) -> str:
        return f"https://www.youtube.com/channel/{self.channel_id}"


# --------------------------------------------------------------------------- #
# Parsing des réponses de l'API
# --------------------------------------------------------------------------- #
def parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_duration(value: str) -> int:
    """Durée ISO 8601 (ex. PT1M30S) -> secondes. 0 si inconnue (live, etc.)."""
    match = _DURATION_RE.match(value or "")
    if not match:
        return 0
    days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def video_from_api(item: dict) -> Video:
    return Video(
        video_id=item["id"],
        channel_id=item["snippet"]["channelId"],
        title=item["snippet"]["title"],
        published=parse_date(item["snippet"]["publishedAt"]),
        views=int(item.get("statistics", {}).get("viewCount", 0)),
        duration_s=parse_duration(item.get("contentDetails", {}).get("duration", "")),
        category_id=item["snippet"].get("categoryId", ""),
    )


def channel_from_api(item: dict) -> Channel | None:
    """None si la chaîne masque ses abonnés (ratio incalculable)."""
    stats = item.get("statistics", {})
    if stats.get("hiddenSubscriberCount"):
        return None
    uploads = item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    return Channel(
        channel_id=item["id"],
        title=item["snippet"]["title"],
        subscribers=int(stats.get("subscriberCount", 0)),
        video_count=int(stats.get("videoCount", 0)),
        created=parse_date(item["snippet"]["publishedAt"]),
        uploads_playlist=uploads or "UU" + item["id"][2:],
    )


# --------------------------------------------------------------------------- #
# Critères
# --------------------------------------------------------------------------- #
def trend_label(videos_newest_first: list[Video], t: Thresholds) -> str:
    if len(videos_newest_first) < 6:
        return "n/a"
    recent = median(v.views for v in videos_newest_first[:5])
    previous = median(v.views for v in videos_newest_first[5:])
    change = recent / max(previous, 1)
    if change >= t.heating:
        return "chauffe"
    if change <= t.cooling:
        return "refroidit"
    return "stable"


def channel_format(videos: list[Video]) -> str:
    share_shorts = sum(v.is_short for v in videos) / len(videos)
    if share_shorts >= 0.7:
        return "short"
    if share_shorts <= 0.3:
        return "long"
    return "mixte"


def dominant_category(videos: list[Video]) -> str:
    counts = Counter(v.category_id for v in videos if v.category_id)
    return counts.most_common(1)[0][0] if counts else ""


def resolve_theme(requested: str, category_id: str) -> tuple[str, bool]:
    """(thème utilisé pour le RPM, hors niche ?)."""
    detected = CATEGORIES.get(category_id, ("", None))[1]
    wanted_family = THEME_FAMILY.get(requested)
    if detected is None or wanted_family is None:
        return requested, False  # rien à comparer
    if THEME_FAMILY[detected] == wanted_family:
        return requested, False  # ex. finance en « Éducation » : on garde le RPM finance
    return detected, True


def estimate_revenue(
    videos: list[Video], now: datetime, rpm_long: float, rpm_short: float
) -> tuple[int, float]:
    """(vues, revenu en $) des vidéos publiées dans les 30 derniers jours.

    L'API ne donne pas l'historique des vues : on additionne les vues totales des
    vidéos récentes, ce qui sous-estime les vues réelles du mois.
    """
    cutoff = now - timedelta(days=30)
    recent = [v for v in videos if v.published >= cutoff]
    views = sum(v.views for v in recent)
    revenue = sum(v.views * (rpm_short if v.is_short else rpm_long) / 1000 for v in recent)
    return views, round(revenue, 2)


def analyze_channel(
    channel: Channel,
    videos: list[Video],
    *,
    niche: str,
    theme: str,
    rpm: RpmTable,
    thresholds: Thresholds = Thresholds(),
    now: datetime | None = None,
) -> ChannelReport | None:
    """Rapport de la chaîne, ou None si aucune vidéo récente n'atteint le seuil d'explosion."""
    if not videos or channel.subscribers <= 0:
        return None
    now = now or datetime.now(timezone.utc)
    videos = sorted(videos, key=lambda v: v.published, reverse=True)

    hits = [v for v in videos if v.views >= thresholds.ratio * channel.subscribers]
    if not hits:
        return None
    latest_hit = hits[0]  # le plus récent, pas le plus gros

    med = median(v.views for v in videos)
    best = max(v.views for v in videos)
    carton_floor = thresholds.one_hit_factor * max(med, 1)
    category_id = dominant_category(videos)
    theme_used, off_niche = resolve_theme(theme, category_id)
    rpm_long, rpm_short = rpm.long_for(theme_used), rpm.short
    monetizable = channel.subscribers >= MONETIZATION_MIN_SUBS
    views_30d, revenue_30d = estimate_revenue(videos, now, rpm_long, rpm_short)
    _, revenue_recurring = estimate_revenue(
        [v for v in videos if v.views < carton_floor], now, rpm_long, rpm_short
    )
    if not monetizable:
        revenue_30d = revenue_recurring = 0.0

    return ChannelReport(
        niche=niche,
        channel_id=channel.channel_id,
        channel_title=channel.title,
        subscribers=channel.subscribers,
        channel_created=channel.created.date().isoformat(),
        videos_analyzed=len(videos),
        latest_hit_title=latest_hit.title,
        latest_hit_views=latest_hit.views,
        latest_hit_days_ago=(now - latest_hit.published).days,
        blowup=round(latest_hit.views / channel.subscribers, 1),
        median_views=int(med),
        share_above_hit_views=round(sum(v.views >= thresholds.hit_views for v in videos) / len(videos), 2),
        one_hit=len(videos) >= 5 and best >= carton_floor,
        trend=trend_label(videos, thresholds),
        format=channel_format(videos),
        views_30d=views_30d,
        revenue_30d=revenue_30d,
        revenue_recurring_30d=revenue_recurring,
        monetizable=monetizable,
        theme_requested=theme,
        category=CATEGORIES.get(category_id, (category_id or "?", None))[0],
        theme_used=theme_used,
        off_niche=off_niche,
    )


# --------------------------------------------------------------------------- #
# Classement
# --------------------------------------------------------------------------- #
def score(r: ChannelReport) -> int:
    """Barème indicatif, à ajuster. Le critère « faisable par Claude » n'y entre pas."""
    pts = 0
    # 1. Explosion du dernier succès
    pts += 3 if r.blowup >= 500 else 2 if r.blowup >= 100 else 1 if r.blowup >= 10 else 0
    # 2. Argent : revenu récurrent estimé sur 30 jours (sans les cartons isolés)
    rev = r.revenue_recurring_30d
    pts += 3 if rev >= 10_000 else 2 if rev >= 3_000 else 1 if rev >= 1_000 else 0
    # 3. Régularité
    if r.videos_analyzed >= 5:
        pts += 2 if r.share_above_hit_views >= 0.7 else 1 if r.share_above_hit_views >= 0.4 else 0
    if r.one_hit:
        pts -= 1
    # 4. Tendance
    pts += {"chauffe": 1, "refroidit": -1}.get(r.trend, 0)
    # 5. Concurrence : moins de chaînes dans la niche = mieux
    pts += 2 if r.competition <= 1 else 1 if r.competition <= 4 else -1 if r.competition >= 8 else 0
    # 6. Hors niche : la chaîne ne fait pas ce que la niche demandait
    if r.off_niche:
        pts -= 2
    return pts


def tier(points: int) -> str:
    return "S" if points >= 9 else "A" if points >= 7 else "B" if points >= 5 else "C"


def rank_board(reports: list[ChannelReport]) -> list[ChannelReport]:
    """Calcule concurrence, score et tier, puis trie.

    La concurrence ne compte que les chaînes dans la niche (les hors-niche ne sont pas des concurrents).
    Égalité de score : la niche la moins encombrée passe devant, puis la plus grosse explosion.
    """
    per_niche = Counter(r.niche for r in reports if not r.off_niche)
    for r in reports:
        r.competition = per_niche[r.niche] + (1 if r.off_niche else 0)
        r.score = score(r)
        r.tier = tier(r.score)
    return sorted(reports, key=lambda r: (-r.score, r.competition, -r.blowup))
