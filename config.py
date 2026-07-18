"""
Configuration centrale du projet.
Modifier ce fichier pour ajouter des clubs, changer les fenêtres de mercato,
ou ajuster l'URL de la source BeSoccer.
"""

# --- Clubs suivis --------------------------------------------------------
# Chaque club a sa page "transferts" BeSoccer (source unique : détection
# officielle + montant en une seule requête, y compris la distinction
# entre "transfert gratuit" (pas d'indemnité) et "libéré" (agent libre)).
#
# NOTE : le Real Madrid a été retiré pour l'instant. Sa page BeSoccer est
# protégée par un anti-bot (Cloudflare probable) qui bloque aussi bien
# les requêtes HTTP classiques que Playwright (navigateur automatisé
# détecté). Voir README, section "Real Madrid mis en pause" pour les
# pistes envisageables si on veut reprendre ce chantier plus tard.
CLUBS = {
    "psg": {
        "display_name": "Paris Saint-Germain",
        "besoccer_url": "https://fr.besoccer.com/equipe/transferts/paris-saint-germain-fc",
        "embed_color": 0x1D9BF0,
    },
    # "real_madrid": {
    #     "display_name": "Real Madrid",
    #     "besoccer_url": "https://fr.besoccer.com/equipe/transferts/real-madrid",
    #     "embed_color": 0xFEBE10,
    # },
}

# --- Fenêtres de mercato ---------------------------------------------------
# Format : (mois_debut, jour_debut, mois_fin, jour_fin)
# Marge de sécurité incluse (les dates officielles varient légèrement chaque année).
MERCATO_WINDOWS = [
    {"name": "été", "start": (6, 1), "end": (9, 5)},
    {"name": "hiver", "start": (1, 1), "end": (2, 3)},
]

# --- Fichier d'état (anti-doublon) -----------------------------------------
STATE_FILE = "seen_transfers.json"

# --- Discord -----------------------------------------------------------
# L'URL du webhook n'est JAMAIS écrite ici en clair.
# Elle est lue depuis la variable d'environnement DISCORD_WEBHOOK_URL
# (injectée via GitHub Secrets en production, ou un export local en test).
DISCORD_WEBHOOK_ENV_VAR = "DISCORD_WEBHOOK_URL"

# --- Réseau ---------------------------------------------------------------
REQUEST_TIMEOUT_SECONDS = 15
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
