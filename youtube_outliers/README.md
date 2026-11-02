# YouTube outliers

Petit pipeline ETL en Python qui repère les chaînes YouTube **« outliers »** d'un format :
petites, récentes, avec au moins une vidéo qui a fait **≥ 10 × plus de vues que la chaîne n'a d'abonnés**.

## Installation

```bash
cd youtube_outliers
pip install -r requirements.txt
export YOUTUBE_API_KEY="ta_clé"
```

Pour la clé : Google Cloud Console → crée un projet → *APIs & Services* → active **YouTube Data API v3** → *Credentials* → **API key**.

## Utilisation

```bash
python find_outliers.py "3d reconstruction"
python find_outliers.py "plane crash explained" --pages 3 --csv outliers.csv
python find_outliers.py "géographie" --region FR --months 6 --max-subs 50000
```

| Option | Défaut | Rôle |
|---|---|---|
| `--ratio` | 10 | vues / abonnés minimum |
| `--max-subs` / `--min-subs` | 100 000 / 1 000 | fourchette d'abonnés |
| `--months` | 12 | vidéos **et** chaînes de moins de N mois |
| `--pages` | 1 | pages de 50 résultats de recherche |
| `--region` | — | code pays (`FR`, `US`…) |
| `--csv` | — | export CSV |

## Pipeline

1. **Extract** : `search.list` (vidéos les plus vues sur le mot-clé), puis `videos.list` et `channels.list` par lots de 50.
2. **Transform** : jointure vidéo ↔ chaîne, filtres (abonnés, âge, abonnés masqués, ratio), meilleure vidéo par chaîne, tri par ratio.
3. **Load** : tableau dans le terminal + CSV.

## Quota

Quota gratuit : 10 000 unités par jour. Une page de recherche coûte 100 unités, `videos`/`channels` 1 unité par lot de 50.
Une exécution avec `--pages 1` coûte ~102 unités, donc environ 90 recherches par jour.

## Limites

- La date de « création » est celle de la chaîne (`publishedAt`), pas celle de la première vidéo.
- `search.list` ne renvoie qu'un échantillon ; varie les mots-clés (et la langue) pour couvrir un format.
- Le nombre d'abonnés renvoyé par l'API est arrondi à 3 chiffres significatifs.

## Tests

```bash
python -m unittest discover -s tests -v
```
