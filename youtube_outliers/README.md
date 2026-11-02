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
| **Catégorie** | catégorie YouTube dominante des vidéos de la chaîne. Si elle contredit le thème demandé (famille *divertissement* contre *informatif*), la chaîne est marquée ⚠️ **hors niche** : son RPM vient de la catégorie détectée et elle perd 2 points | — |
| **Shorts seulement** 📱 | chaîne à ≥ 70 % de Shorts. Colonne `monetization_path` : voie Shorts du Programme Partenaire (**10M vues de Shorts en 90 jours**) et progression, voie vidéos longues (4 000 h, non vérifiable via l'API), ou non monétisable (< 1 000 abonnés) | — |
| **Concurrence** | nombre de chaînes outliers **dans** la niche (les hors-niche ne comptent pas) | — |
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
| Shorts seulement | −1 |
| Hors niche | −2 |

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

- **Les RPM sont des ordres de grandeur** : ceux de la vidéo, baissés d'environ 40 % après comparaison avec vidIQ. Ce ne sont pas des mesures. Le vrai RPM n'est visible que dans le YouTube Studio de la chaîne, donc le revenu est une estimation grossière.
- **Les vues du mois sont sous-estimées.** L'API ne donne pas l'historique des vues : on additionne les vues totales des vidéos publiées dans les 30 derniers jours.
- **Les vues de Shorts sur 90 jours ne comptent que les `--recent` dernières vidéos analysées** (15 par défaut). Pour une chaîne qui publie beaucoup, monte `--recent` à 50.
- **La catégorie YouTube est choisie par le créateur** : elle peut être fausse. « People & Blogs », la catégorie par défaut, est ignorée. Un « hors niche » peut aussi vouloir dire que le thème donné à la niche est mal choisi.
- **La concurrence dépend du mot-clé** et de l'échantillon que renvoie `search.list`. Varie les formulations et les langues.
- **La date de création** est celle de la chaîne, pas celle de sa première vidéo. Le nombre d'abonnés est arrondi par l'API.

## Tests

```bash
python -m unittest discover -s tests -v
```
