# Sources : « La panne mondiale d'Internet : les 72 premières heures »

Recherche faite le 3 novembre 2026. Ce fichier s'utilise avec [`format_bible.md`](format_bible.md) :
copie le bloc **ENTRÉES** ci-dessous à la place de celui du prompt.

**Légende de fiabilité**
- ✅ **Solide** : source officielle ou plusieurs médias concordants.
- 🟡 **À citer avec prudence** : estimation d'une entreprise ou chiffre d'une seule source. Dis-le dans le script (« selon… »).
- ⚠️ **À vérifier** : non confirmé par la recherche. À utiliser seulement après vérification.

---

## Le choix de scénario (important pour la crédibilité)

Une panne **totale et mondiale** d'Internet pendant 72 heures n'a jamais eu lieu. Pour respecter le contrat d'honnêteté, on fait comme Hindcast :
- **Ce qui est inventé :** le **déclencheur** et la **chronologie**. Par exemple, une mise à jour défectueuse diffusée en même temps par un fournisseur utilisé partout, qui casse la résolution des adresses (DNS). C'est un mélange de CrowdStrike 2024 et d'AWS 2025.
- **Ce qui est réel :** **chaque conséquence est calquée sur une panne qui a vraiment eu lieu**, ailleurs, en plus petit (Rogers, Orange, CrowdStrike, Corbeil-Essonnes, Tonga).
- **Le « presque » réel**, l'équivalent des « 9 jours » de Hindcast : le 19 juillet 2024, **une seule mise à jour** a suffi à planter 8,5 millions d'ordinateurs dans le monde.

---

```text
# ENTRÉES
- SUJET : La panne mondiale d'Internet : que se passe-t-il pendant les 72 premières heures ?
- LANGUE DU SCRIPT : français
- DURÉE CIBLE : 12 minutes
- DATE DE PUBLICATION : {mois de publication, ex. décembre 2026}
- PERSONNAGE FIL ROUGE : à inventer (une personne ordinaire en France, dont la journée dépend d'Internet
  sans qu'elle s'en rende compte ; à retrouver aux temps 1, 5 et 8)
- FIN SOUHAITÉE : un geste concret (ex. garder un peu d'espèces et noter sur papier quelques numéros essentiels)
- PUBLIC : grand public curieux, sans connaissances techniques
- SCÉNARIO : le déclencheur et la chronologie sont inventés (une mise à jour défectueuse diffusée par un
  fournisseur utilisé partout casse la résolution des adresses Internet, le DNS). Chaque conséquence est calquée
  sur une panne réelle listée dans les sources. Le dire à voix haute dans le contrat d'honnêteté.
- SOURCES AUTORISÉES :

## Le « presque » réel : CrowdStrike, 19 juillet 2024
- ✅ Une mise à jour de configuration du logiciel de sécurité CrowdStrike, poussée le 19 juillet 2024 à 4 h 09 UTC,
  a fait planter les ordinateurs Windows qui l'ont reçue. Elle a été retirée à 5 h 27 UTC, soit 78 minutes plus tard.
  (TechTarget, Computer Weekly)
- ✅ Microsoft estime à environ 8,5 millions le nombre d'appareils Windows touchés, moins de 1 % des machines
  Windows dans le monde, mais des machines qui faisaient tourner des services essentiels. (Microsoft via TechCrunch, Bloomberg)
- ✅ Le 25 juillet, plus de 97 % des capteurs Windows de CrowdStrike étaient de nouveau en ligne, six jours après. (TechTarget, CBS)
- ✅ La compagnie Delta a annulé environ 5 000 à 7 000 vols sur plusieurs jours (les sources varient),
  a reçu plus de 176 000 demandes de remboursement et estime la perte à environ 500 millions de dollars. (Fortune, Silicon Republic)
- 🟡 L'assureur Parametrix estime la perte à 5,4 milliards de dollars pour les 500 plus grandes entreprises
  américaines, hors Microsoft. (Parametrix via Yahoo Finance)
- 🟡 Des hôpitaux ont été touchés, dont au moins 12 grands établissements américains selon ABC News (source secondaire).

## Quand un seul fournisseur tombe : le cloud
- ✅ AWS, Microsoft Azure et Google Cloud représentent ensemble 63 % des dépenses mondiales d'infrastructure
  cloud au 3e trimestre 2025 : AWS 29 %, Microsoft 20 %, Google 13 %. (Synergy Research via The Register, Computing)
- ✅ Le 20 octobre 2025, un problème de DNS dans la région « us-east-1 » d'AWS (Virginie) a rendu inaccessible
  la base de données DynamoDB. Par effet domino, des dizaines de services sont tombés : jeux, banques, maison connectée.
  (The Register, Built In)
- 🟡 Le nombre de services touchés lors de la panne AWS varie selon les sources, de plus de 80 à 142.
  Durée totale rapportée : environ 15 heures. (W.Media, DEV)
- ✅ Le 18 novembre 2025, une erreur interne chez Cloudflare (un fichier de configuration devenu trop gros après
  un changement de permissions sur une base de données) a rendu indisponibles pendant plusieurs heures
  X, ChatGPT, Spotify et Canva. Ce n'était pas une attaque. (Engadget, Global News)
- ✅ Le 4 octobre 2021, une erreur de configuration lors d'une maintenance a coupé Facebook, Instagram et WhatsApp
  pendant environ six heures. Les routes BGP de Facebook ont disparu d'Internet. (The Register, TechSpot)

## Les paiements
- ✅ Le 8 juillet 2022 au Canada, la panne de l'opérateur Rogers a rendu indisponibles dans tout le pays
  les paiements par carte de débit Interac en caisse et les virements Interac. Des villes ont annoncé ne plus
  pouvoir accepter ni carte de débit ni carte de crédit. (Global News, CBC, BNN Bloomberg)
- 🟡 Cette panne Rogers a touché plus de 12 millions d'utilisateurs (Wikipédia, source unique).
- ✅ En France, en 2024, la carte représente 48 % des paiements en magasin, contre 43 % pour les espèces.
  C'est la première fois que la carte dépasse le liquide. En 2016, les espèces faisaient 68 % des paiements
  et la carte 27 %. (Banque de France, enquête SPACE de la BCE)
- ✅ La France comptait 42 578 distributeurs de billets fin 2024, contre 44 123 un an plus tôt.
  Plus de 11 000 ont disparu depuis 2018. (Banque de France)
- 🟡 La France métropolitaine comptait 40 804 distributeurs fin 2025 (rapport du CNMP, via la Banque des Territoires).
- ⚠️ Les distributeurs de billets et la plupart des terminaux de paiement ont besoin d'une connexion réseau
  pour autoriser une opération (à vérifier : certains terminaux acceptent des paiements hors ligne sous un plafond).

## Les numéros d'urgence
- ✅ Le 2 juin 2021 en France, une panne chez Orange a empêché environ 11 800 appels vers le 15, le 17, le 18
  et le 112 d'aboutir, soit 11 % des appels, entre 16 h 45 et minuit environ. Cause : un bug logiciel lors
  d'une opération de maintenance, confirmé par l'ANSSI. (Rapport d'État du 19 juillet 2021 sur Vie-publique, Le Quotidien du Médecin)
- 🟡 Selon les rapports, cinq à six décès sont potentiellement liés à cette panne. Le lien de causalité n'est pas établi.
- ✅ Pendant la panne Rogers de 2022, les appels au 911 depuis les mobiles Rogers ne passaient plus.
  Les polices de Winnipeg et d'Ottawa ont demandé d'utiliser une ligne fixe ou un autre opérateur. (CBC, Global News)

## Les hôpitaux
- ✅ Lors de la cyberattaque de l'hôpital Sud Francilien de Corbeil-Essonnes (août 2022), l'hôpital est passé
  en « mode dégradé » : retour au dossier papier et au stylo, enregistrement des patients à la main,
  plan blanc, patients réorientés depuis les urgences et la chirurgie. (Le Monde Informatique, Europe 1, Infirmiers.com)
- ✅ Deux semaines après l'attaque, l'hôpital ne pouvait encore prendre en charge que la moitié des urgences.
  Retour à une activité « proche de la normale » annoncé pour fin octobre 2022, environ deux mois après. (Banque des Territoires)
- ✅ En décembre 2022, après une cyberattaque à l'hôpital de Versailles, six patients parmi « les plus lourds »
  ont été transférés : trois de réanimation et trois de néonatologie. (FrenchWeb)
- ⚠️ Ces cas sont des cyberattaques ciblées sur un seul hôpital, pas une panne d'Internet. Il faut le dire
  dans le script (« on a déjà vu ce que fait un hôpital privé de son informatique »).

## Les câbles sous-marins (pour l'échelle mondiale et le temps de réparation)
- ✅ Les câbles sous-marins transportent plus de 99 % du trafic de données intercontinental (TeleGeography,
  vérification de 2023 : vrai, même si un calcul précis est impossible).
- ✅ En février 2025, on comptait 570 systèmes de câbles en service et 81 en projet. (SubOptic, d'après TeleGeography)
- ✅ Début 2024, plusieurs câbles ont été coupés en mer Rouge. Réparer un câble sous-marin prend généralement
  deux à trois mois, parce qu'il faut des navires spécialisés. (Fortune, AP, Subtel Forum)
- 🟡 L'opérateur HGC estime que 25 % du trafic entre l'Asie, l'Europe et le Moyen-Orient a été touché.
  RETN parle de jusqu'à 70 %. Ce sont des estimations d'entreprises.
- 🟡 Selon un expert cité par la presse, plus de 90 % des communications entre l'Europe et l'Asie passent par la mer Rouge.
- ✅ En janvier 2022, l'éruption du volcan Hunga Tonga a coupé l'unique câble (872 km) qui reliait Tonga au monde.
  Le pays est resté 38 jours sans Internet, environ 5 semaines. Une section du câble avait été déplacée de près
  de 5 km par l'éruption. (SBS, Euronews, CBS)

## Les transports
- ✅ CrowdStrike, 19 juillet 2024 : des milliers de vols annulés dans le monde (pas de total précis fiable),
  et Delta seule entre 5 000 et 7 000 sur plusieurs jours.
- ⚠️ Le 11 janvier 2023, la panne du système de notification aux pilotes (NOTAM) de l'autorité américaine
  de l'aviation (FAA) a provoqué l'arrêt des décollages dans tout le pays, une première depuis le 11 septembre 2001
  (à vérifier et sourcer).

## L'alimentation
- 🟡 Ordre de grandeur cité par un dirigeant de la distribution (Europe 1, date ancienne) : un hypermarché a
  environ 20 jours de stock en produits de grande consommation, et environ 7 jours en produits frais.
- ⚠️ Le délai réel avant les ruptures dépend des commandes et de la logistique, qui sont informatisées.
  Pas de chiffre officiel récent trouvé (pistes : Fédération du commerce et de la distribution, Insee).
  Ne pas affirmer « 3 jours de stock » sans source.

## Ce qui continue de marcher (pour l'honnêteté et le retournement)
- ⚠️ Le réseau électrique, la radio FM, le GPS et les espèces ne dépendent pas d'Internet pour fonctionner
  (à vérifier avant d'écrire. Le retournement possible : ce n'est pas la technologie qui manque, c'est l'organisation
  qui ne sait plus fonctionner sans elle).
```

---

## Liens

**CrowdStrike**
- [TechCrunch : Microsoft dit que 8,5 M d'appareils Windows ont été touchés](https://techcrunch.com/2024/07/20/microsoft-says-8.5m-windows-devices-were-affected-by-crowdstrike-outage)
- [Bloomberg](https://www.bloomberg.com/news/articles/2024-07-20/crowdstrike-crash-affected-8-5-million-microsoft-windows-devices)
- [TechTarget : explication de la panne](https://techtarget.com/whatis/video/An-explanation-of-the-CrowdStrike-outage)
- [TechTarget : 97 % des capteurs de nouveau en ligne](https://www.techtarget.com/cybersecurity/news/366599094/CrowdStrike-97-of-Windows-sensors-back-online-after-outage)
- [Computer Weekly](https://www.computerweekly.com/news/366596373/CrowdStrike-update-snafu-affected-85-million-Windows-devices)
- [Fortune : la perte de Delta](https://www.fortune.com/2024/08/09/delta-380-million-lost-revenue-crowdstrike-outage-cancel-thousands-flights)
- [Silicon Republic](https://siliconrepublic.com/enterprise/delta-air-lines-crowdstrike-outage-cost)
- [Yahoo Finance : l'estimation Parametrix](https://uk.finance.yahoo.com/news/crowdstrike-global-outage-cost-us-161917841.html)

**AWS, Cloudflare, Facebook, cloud**
- [The Register : la panne AWS](https://www.theregister.com/2025/10/20/amazon_aws_outage/?td=rt-3a)
- [Built In](https://builtin.com/articles/aws-outage-what-happened)
- [W.Media](https://w.media/developing-story-aws-outage-impacts-over-80-amazon-apps-and-services-recovery-underway/)
- [Engadget : la panne Cloudflare](https://www.engadget.com/cybersecurity/cloudflare-outage-was-not-caused-by-a-cyber-attack-053000551.html)
- [Global News](https://globalnews.ca/news/11530818/cloudflare-technical-outage-twitter)
- [The Register : le retour de Facebook](https://www.theregister.com/2021/10/04/facebook_back_online/)
- [TechSpot](https://www.techspot.com/news/91574-facebook-back-online-after-more-than-6-hours.html)
- [The Register : les parts de marché du cloud](https://www.theregister.com/2025/11/20/aws_loses_market_share_azure_google/)
- [Computing](https://www.computing.co.uk/news/2025/cloud/aws-feels-the-heat/)

**Rogers**
- [Global News : Interac et la panne Rogers](https://globalnews.ca/news/8975789/rogers-outage-today-phone-internet-interac)
- [CBC : le 911 et la ligne fixe](https://www.cbc.ca/lite/story/1.6514653)
- [CBC : les paiements bloqués en Colombie-Britannique](https://www.cbc.ca/1.6514932)
- [BNN Bloomberg](https://www.bnnbloomberg.ca/rogers-outage-affects-passport-services-interac-and-offices-1.1789398)
- [Wikipédia](https://en.wikipedia.org/wiki/2022_Rogers_Communications_outage)

**Orange, numéros d'urgence**
- [Vie-publique : synthèse](https://www.vie-publique.fr/en-bref/280875-panne-des-numeros-durgence-quelle-responsabilite-dorange)
- [Rapport d'État (PDF)](https://www.vie-publique.fr/sites/default/files/rapport/pdf/280855.pdf)
- [Le Quotidien du Médecin](https://www.lequotidiendumedecin.fr/hopital/urgences/panne-des-numeros-durgence-un-rapport-accuse-orange-et-pointe-un-retard-de-reactivite-de-plusieurs)

**Paiements et distributeurs**
- [Banque de France : l'usage des espèces](https://www.banque-france.fr/fr/publications-et-statistiques/publications/les-francais-continuent-dapprecier-les-especes-meme-si-leur-usage-se-reduit-au-profit-des-paiements)
- [MoneyVox](https://www.moneyvox.fr/banque/actualites/102245/un-chiffre-historique-pour-les-paiements-par-carte-bancaire)
- [Journal de l'économie : le nombre de distributeurs](https://www.journaldeleconomie.fr/?p=39712)
- [Banque des Territoires](https://www.banquedesterritoires.fr/la-baisse-du-nombre-de-distributeurs-de-billets-en-partie-compensee-par-les-points-retraits-chez)

**Hôpitaux**
- [Le Monde Informatique : Corbeil-Essonnes](https://www.lemondeinformatique.fr/actualites/lire-l-hopital-sud-francilien-de-corbeil-essonnes-en-proie-a-une-cyberattaque-87743.html)
- [Infirmiers.com](https://www.infirmiers.com/profession-ide/actualite-sociale/un-centre-hospitalier-ebranle-par-une-cyberattaque-corbeil-essonnes)
- [Banque des Territoires : le retour à la normale](https://www.banquedesterritoires.fr/apres-sa-cyberattaque-retour-une-activite-proche-de-la-normale-dans-le-centre-hospitalier-de)
- [FrenchWeb : les transferts à Versailles](https://www.frenchweb.fr/france-nouvelle-cyberattaque-contre-un-hopital-des-patients-transferes/437569)

**Câbles sous-marins**
- [TeleGeography : le chiffre de 99 %](https://blog.telegeography.com/2023-mythbusting-part-3)
- [SubOptic : le nombre de câbles](https://www.suboptic.org/news/how-many-submarine-cables-are-there-anyway)
- [Fortune : la mer Rouge](https://fortune.com/2024/03/04/internet-cables-cut-red-sea/amp)
- [Subtel Forum](https://subtelforum.com/red-sea-cable-damage-disrupt-me-networks/)
- [SBS : Tonga, 38 jours](https://www.sbs.com.au/news/article/tonga-back-online-after-38-days-of-no-internet-due-to-volcanic-eruption/abx9r4rre)
- [Euronews](https://www.euronews.com/2022/02/23/tonga-is-finally-back-online-here-s-why-it-took-5-weeks-to-fix-its-volcano-damaged-interne)

**Alimentation**
- [Europe 1 : les stocks des supermarchés](https://www.europe1.fr/economie/coronavirus-faut-il-craindre-des-penuries-les-entrepots-sont-pleins-les-magasins-sont-reapprovisionnes-3954153)
