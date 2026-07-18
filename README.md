# Mercato Watcher — PSG
Script qui vérifie une fois par semaine, uniquement pendant les périodes de
mercato (été: juin-sept, hiver: janvier-début fév), les transferts
**officiels** (pas les rumeurs) du PSG, et envoie une alerte Discord par
transfert détecté.

## Source de données (PSG)

**BeSoccer** (`fr.besoccer.com/equipe/transferts/paris-saint-germain-fc`) :
- Page "transferts" avec onglet "Officiels" distinct de "Rumeurs"
- Montant déjà inclus, pas besoin d'une source séparée
- Distingue "Transfert" (montant connu), "Transfert gratuit" (pas
  d'indemnité), "Libéré" (agent libre), "Prêt" -- ce qui règle le cas des
  entraîneurs et agents libres qui n'auront jamais de montant à proprement
  parler

Limite connue : cette page ne donne pas la durée du contrat. Un transfert
est notifié quand même, avec "non communiqué" pour le contrat.

## Règles métier

- Un transfert officiel détecté est **toujours** notifié, montant connu
  ou non (affiché "non communiqué" le cas échéant, sinon le type de
  transfert -- ex. "Prêt" -- est affiché à la place).
- Un transfert déjà notifié n'est plus jamais renvoyé (anti-doublon via
  `seen_transfers.json`).
- Seuls les transferts dont la date tombe dans la fenêtre de mercato
  actuellement active sont pris en compte (pas de rappel de l'historique
  à chaque réouverture du mercato).

## Structure du projet

```
mercato_watcher/
├── config.py                  # clubs suivis (URL BeSoccer), fenêtres de mercato
├── mercato_window.py           # vérifie si on est dans une période active
├── scraper_club.py               # scrape BeSoccer (détection + montant en une fois)
├── discord_notify.py             # formate et envoie l'alerte Discord
├── state.py                       # anti-doublon (seen_transfers.json)
├── main.py                         # orchestre tout le flux
├── requirements.txt
├── seen_transfers.json             # état persistant (committé automatiquement)
└── .github/workflows/mercato.yml   # cron GitHub Actions
```

## Installation locale (test)

```bash
pip install -r requirements.txt
```

## Mise en place

1. Créer un repo GitHub et y pousser ces fichiers.
2. Créer un webhook Discord dans le salon souhaité (Paramètres du salon →
   Intégrations → Webhooks → Nouveau webhook → copier l'URL).
3. Dans le repo GitHub : Settings → Secrets and variables → Actions →
   "New repository secret" → nom `DISCORD_WEBHOOK_URL`, valeur = l'URL copiée.
4. Aller dans l'onglet **Actions** du repo, sélectionner le workflow
   "Mercato Watcher", cliquer sur "Run workflow" pour un premier test manuel.
5. Vérifier les logs d'exécution et l'alerte reçue sur Discord.

## Point d'attention

BeSoccer n'expose pas de classes CSS documentées pour son widget de
transferts. Le parsing dans `scraper_club.py` repère le texte des liens
plutôt que des sélecteurs CSS précis -- plus robuste à un changement de
design, mais sensible à un changement de mise en forme du texte. À tester
en local et ajuster si besoin.
