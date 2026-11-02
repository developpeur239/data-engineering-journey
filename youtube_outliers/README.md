# YouTube outliers : le tableau des niches

Pipeline ETL en Python sur l'API YouTube Data v3. Pour chaque niche (mot-clé), il repère les **petites chaînes récentes
qui explosent**, calcule leurs critères et les classe **S / A / B / C**.

## Installation

```bash
cd youtube_outliers
pip install -r requirements.txt
export YOUTUBE_API_KEY="ta_clé"
```

Pour la clé : Google Cloud Console → crée un projet → *APIs & Services* → active **YouTube Data API v3** → *Credentials* → **API key**.

## Utilisation

Une niche s'écrit `"mot-clé=thème"`. Le thème choisit le RPM des vidéos longues dans [`rpm.json`](rpm.json).

```bash
python find_outliers.py \
  "3d news reconstruction=news" \
  "ai takeover documentary=tech" \
  "stickman battle=entertainment" \
  "horror story stick figures=horror" \
  --csv board.csv
```

Thèmes fournis : `tech`, `finance`, `news`, `education`, `science`, `entertainment`, `horror`, `default`.

## Les critères

| Critère | Calcul | Option |
|---|---|---|
| **Explosion** | vues du **dernier succès** ÷ abonnés. Le dernier succès est la vidéo la plus récente, parmi les N dernières, qui dépasse le seuil | `--ratio` (défaut **100**) |
| **Régularité** | médiane des vues et part des N dernières vidéos au-dessus de 50K | `--hit-views`, `--recent` |
| **Un seul carton** ⚠️ | meilleure vidéo ≥ 50 × la médiane | — |
| **Tendance** | médiane des 5 dernières ÷ médiane des précédentes : 🔥 chauffe (≥ 1,2), ❄️ refroidit (≤ 0,8), ➖ stable | — |
| **Format** | Short si ≤ 3 min. Chaîne `short` (≥ 70 % de Shorts), `long` (≤ 30 %) ou `mixte` | — |
| **Argent** | vues des vidéos des 30 derniers jours × RPM (Short ou longue) ÷ 1000. Le **revenu récurrent** exclut les cartons isolés (≥ 50 × la médiane). Revenu à 0 et 🚫 sous 1 000 abonnés (non monétisable) | `rpm.json`, `--rpm-long`, `--rpm-short` |
| **Concurrence** | nombre de chaînes outliers trouvées dans la même niche | — |
| **Faisable par Claude** | jugement humain : colonne `buildable_by_claude` vide dans le CSV, à remplir | — |

Filtres de départ : entre `--min-subs` (1K) et `--max-subs` (100K) abonnés, chaîne créée il y a moins de `--months` (12) mois, abonnés non masqués.

### Barème (indicatif, dans `metrics.score`)

| Critère | Points |
|---|---|
| Explosion | ≥ 500× : 3 · ≥ 100× : 2 · ≥ 10× : 1 |
| Revenu **récurrent** estimé sur 30 jours | ≥ 10 000 $ : 3 · ≥ 3 000 $ : 2 · ≥ 1 000 $ : 1 |
| Régularité (au moins 5 vidéos) | ≥ 70 % des vidéos > 50K : 2 · ≥ 40 % : 1 · un seul carton : −1 |
| Tendance | chauffe : +1 · refroidit : −1 |
| Concurrence | 1 chaîne : +2 · ≤ 4 : +1 · ≥ 8 : −1 |

**S ≥ 9 · A ≥ 7 · B ≥ 5 · C sinon.** En cas d'égalité, la niche la moins encombrée passe devant, puis la plus grosse explosion.

## Structure

```
youtube_client.py   Extract   : appels API + compteur de quota
metrics.py          Transform : critères, score, tiers (fonctions pures)
find_outliers.py    Load/CLI  : tableau terminal + CSV
rpm.json            table des RPM, modifiable
tests/              tests unitaires + test bout-en-bout avec une fausse API
```

## Quota

Quota gratuit : 10 000 unités par jour. Par niche, il faut compter environ 100 unités par page de recherche, plus ~1 unité par chaîne candidate pour ses dernières vidéos, soit **~100 à 160 unités par niche**.
Le script affiche le quota utilisé à la fin.

## Limites

- **Les RPM sont des ordres de grandeur** repris de la vidéo, pas des mesures. Le vrai RPM n'est visible que dans le YouTube Studio de la chaîne, donc le revenu est une estimation grossière.
- **Les vues du mois sont sous-estimées.** L'API ne donne pas l'historique des vues : on additionne les vues totales des vidéos publiées dans les 30 derniers jours.
- **La concurrence dépend du mot-clé** et de l'échantillon que renvoie `search.list`. Varie les formulations et les langues.
- **La date de création** est celle de la chaîne, pas celle de sa première vidéo. Le nombre d'abonnés est arrondi par l'API.

## Tests

```bash
python -m unittest discover -s tests -v
```
