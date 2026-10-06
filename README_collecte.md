# Collecte en direct dans Azure : mode d'emploi

Collecte Bronze du projet datalake Vélib' × météo × pannes (M2 Data, compte Azure for Students).
Le code est dans `function_app/` (Python 3.12, modèle v2) et ne contient **aucun secret**.

## Ressources

Tout se trouve dans **un seul groupe de ressources**, à supprimer en fin de projet.

| Ressource | Nom | Détail |
|---|---|---|
| Groupe de ressources | `rg-datalake-velib` | créé en francecentral (métadonnées uniquement) |
| Stockage ADLS Gen2 | `stdlvelibv8gywf` | **switzerlandnorth**, Standard_LRS, Hot, espace de noms hiérarchique ; conteneurs `bronze`, `silver`, `gold` |
| Function App | `func-datalake-velib-v8gywf` | **Flex Consumption**, Python 3.12, 512 Mo par instance, identité managée système |
| Supervision | `appi-datalake-velib` + `log-datalake-velib` | Application Insights sur Log Analytics, rétention 30 jours, plafond de 0,1 Go/jour |

**Pourquoi switzerlandnorth ?** La politique de l'abonnement étudiant (« Allowed resource deployment regions ») **refuse** francecentral, westeurope, swedencentral et northeurope (erreur `RequestDisallowedByAzure`, mesurée). Elle n'autorise que norwayeast, denmarkeast, switzerlandnorth, austriaeast et belgiumcentral. Parmi elles, switzerlandnorth est la plus proche de Paris à proposer à la fois Flex Consumption et Application Insights.

**Sécurité :**
- la Function App accède au stockage **par identité managée**, avec le rôle *Storage Blob Data Contributor* ;
- `AzureWebJobsStorage` est remplacé par `AzureWebJobsStorage__accountName`, il n'y a donc aucune clé de compte ;
- la clé PRIM est un *app setting* (`PRIM_API_KEY`), jamais présent dans le code, les logs ou les manifestes.

## Ce qui est collecté

| Fonction | Déclenchement (UTC) | Écrit dans `bronze/` |
|---|---|---|
| `collecte_5min` | `0 */5 * * * *` | `velib/status/date=AAAA-MM-JJ/heure=HH/status_<UTC>.json.gz` et `prim/disruptions/date=…/heure=…/disruptions_<UTC>.json.gz` |
| `collecte_quotidienne` | `0 30 3 * * *` | `velib/info/date=…/station_information_<UTC>.json.gz` ; `meteo/date=<jour>/meteo_<jour>_j-1.json.gz` et `…_j-6_consolidee.json.gz` ; `compteurs/date=<jour>/comptages_<jour>.parquet` ; **le lundi** : `idfm/arrets_lignes/date=<lundi>/arrets_lignes.csv` (référentiel arrêts-lignes, CSV `;` UTF-8 avec BOM, ≈ 14 Mo). Ce fichier n'est **jamais écrasé** : si la partition existe, le statut est `deja_present` et rien n'est écrit. |
| *(chargement unique)* | – | `compteurs/historique/mois=AAAA-MM/`, `ratpstatus/date=AAAA-MM-JJ/`, `kaggle/velib-data/v13/` (avec leurs `.meta.json`) |

**Manifestes.** Chaque fichier a un `<nom>.manifest.json` qui contient : source, URL (sans clé), heure UTC, code HTTP, nombre d'essais, tailles brute et stockée, sha256, nombre d'enregistrements et `statut`.

**Échecs.** Si un appel échoue définitivement, après 3 nouvelles tentatives à 2, 4 puis 8 s (aucune sur une erreur 4xx autre que 429), un manifeste `"statut": "echec"` est écrit **sans** fichier de données. Les trous sont ainsi traçables. Les appels Vélib' et PRIM sont indépendants : si l'un échoue, l'autre est quand même écrit.

**Test manuel du référentiel.** Pour déclencher uniquement le référentiel sans retoucher la météo ni les compteurs, ajoutez temporairement l'app setting `REFERENTIEL_SEUL=1`, déclenchez `collecte_quotidienne`, puis **supprimez** le paramètre (`az functionapp config appsettings delete … --setting-names REFERENTIEL_SEUL`). Sans ce paramètre, la fonction se comporte comme avant, avec le référentiel en plus le lundi.

**Décalages mesurés :**
- **Compteurs vélo :** le portail publie la journée J-1 vers 11:00 UTC. À 03:30 UTC, la fonction récupère donc la **journée de Paris J-2**.
- **Météo :** l'archive est rechargée à **J-6** pour disposer de la version consolidée.

## Vérifier que la collecte tourne

```bash
RG=rg-datalake-velib; ST=stdlvelibv8gywf; FN=func-datalake-velib-v8gywf

# 1. Les fonctions sont-elles actives ?
az functionapp function list -g $RG -n $FN --query "[].{nom:name, desactivee:isDisabled}" -o table

# 2. Derniers fichiers écrits (Vélib' et PRIM) pour l'heure en cours
az storage fs file list --account-name $ST --auth-mode login -f bronze \
  --path "velib/status/date=$(date -u +%F)/heure=$(date -u +%H)" --query "[].name" -o tsv
az storage fs file list --account-name $ST --auth-mode login -f bronze \
  --path "prim/disruptions/date=$(date -u +%F)/heure=$(date -u +%H)" --query "[].name" -o tsv

# 3. Lire un manifeste (statut, http_status, nb_enregistrements)
az storage fs file download --account-name $ST --auth-mode login -f bronze \
  -p "<chemin>.manifest.json" -d manifeste.json --overwrite && cat manifeste.json
```

Valeurs attendues :
- Vélib' : `"statut": "ok"`, `"http_status": 200`, environ **1 500** enregistrements ;
- PRIM : quelques **centaines** de perturbations ;
- une paire de fichiers toutes les 5 minutes, soit **12 par heure** et par source.

**Dans le portail Azure :** Function App `func-datalake-velib-v8gywf` → **Monitoring → Invocations**, ou Application Insights `appi-datalake-velib` → **Logs**, avec par exemple :

```kusto
traces | where timestamp > ago(1h) | where message has "statut=" | project timestamp, message | order by timestamp desc
```

## Mettre en pause (sans rien supprimer)

```bash
az functionapp config appsettings set -g rg-datalake-velib -n func-datalake-velib-v8gywf \
  --settings "AzureWebJobs.collecte_5min.Disabled=true" "AzureWebJobs.collecte_quotidienne.Disabled=true" --output none
# reprendre :
az functionapp config appsettings set -g rg-datalake-velib -n func-datalake-velib-v8gywf \
  --settings "AzureWebJobs.collecte_5min.Disabled=false" "AzureWebJobs.collecte_quotidienne.Disabled=false" --output none
```

Pour tout arrêter d'un coup : `az functionapp stop -g rg-datalake-velib -n func-datalake-velib-v8gywf` (relance avec `start`).

## Mettre à jour la clé PRIM (à taper soi-même, jamais dans le dépôt)

```bash
read -rs PRIM_KEY   # collez la clé puis Entrée : rien ne s'affiche, rien n'entre dans l'historique
az functionapp config appsettings set -g rg-datalake-velib -n func-datalake-velib-v8gywf \
  --settings "PRIM_API_KEY=$PRIM_KEY" --output none
unset PRIM_KEY
```

Le paramètre `--output none` est indispensable : sans lui, la commande réaffiche tous les paramètres, **valeurs comprises**.

## Redéployer le code

```bash
cd function_app && zip -qr ../function_app.zip . -x ".venv/*" "__pycache__/*" && cd ..
az functionapp deployment source config-zip -g rg-datalake-velib -n func-datalake-velib-v8gywf \
  --src function_app.zip --build-remote true
```

## Coûts et surveillance

- **Volume mesuré (gzip) :** Vélib' ≈ 34 Ko et PRIM ≈ 233 Ko par déclenchement, soit environ **77 Mo par jour**, **0,5 Go par semaine** et 2,3 Go par mois.
- **Coût estimé** (calculé à partir des tarifs publics, **non mesuré** : à confirmer dans Cost analysis dans 24 à 48 h) : environ **0,01 à 0,05 $ par jour**.
  - L'exécution (≈ 8 700 appels par mois, environ 1,5 s à 0,5 Go) reste dans l'offre gratuite de Flex Consumption.
  - Le principal poste est le nombre d'écritures sur le stockage ADLS Gen2 (≈ 1 150 par jour).
- **Où regarder :**
  - portail Azure → **Cost Management + Billing → Cost analysis**, avec un filtre sur le groupe de ressources `rg-datalake-velib` ;
  - **Budgets** : budget de 100 $ avec alertes à 20 %, 50 % et 80 % ;
  - crédit restant : https://www.microsoftazuresponsorships.com/Balance

## Tout supprimer à la fin du projet

```bash
az group delete -n rg-datalake-velib --yes --no-wait
```

**Attention, c'est irréversible :** cette commande supprime le stockage, donc **toutes les données collectées**. Copiez d'abord ce que vous voulez garder, par exemple avec `az storage blob download-batch --auth-mode login`.
