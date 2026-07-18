"""
Envoie une alerte Discord (embed) pour un transfert officiel détecté.
"""

import os
import requests

from config import CLUBS, DISCORD_WEBHOOK_ENV_VAR, REQUEST_TIMEOUT_SECONDS


def _direction_label(direction: str, club_display_name: str) -> str:
    if direction == "arrival":
        return f"Arrivée officielle — {club_display_name}"
    return f"Départ officiel — {club_display_name}"


def build_embed(transfer: dict, club_key: str) -> dict:
    club = CLUBS[club_key]
    direction = transfer["direction"]

    fields = []
    club_field_name = "Provenance" if direction == "arrival" else "Destination"
    fields.append({
        "name": club_field_name,
        "value": transfer.get("other_club") or "non communiqué",
        "inline": True,
    })

    fields.append({
        "name": "Montant",
        "value": transfer.get("amount") or transfer.get("transfer_type") or "non communiqué",
        "inline": True,
    })
    fields.append({
        "name": "Contrat",
        "value": transfer.get("contract_duration") or "non communiqué",
        "inline": True,
    })
    fields.append({
        "name": "Source",
        "value": transfer["source_url"],
        "inline": False,
    })

    return {
        "title": _direction_label(direction, club["display_name"]),
        "description": transfer["player_name"],
        "color": club["embed_color"],
        "fields": fields,
    }


def send_transfer_alert(transfer: dict, club_key: str) -> bool:
    """
    Envoie une alerte Discord pour un transfert. Retourne True si succès.
    L'URL du webhook est lue depuis la variable d'environnement, jamais
    stockée en clair dans le code (voir README pour la config GitHub Secrets).
    """
    webhook_url = os.environ.get(DISCORD_WEBHOOK_ENV_VAR)
    if not webhook_url:
        print(f"[discord_notify] Variable d'environnement {DISCORD_WEBHOOK_ENV_VAR} absente, alerte annulée.")
        return False

    payload = {"embeds": [build_embed(transfer, club_key)]}

    try:
        resp = requests.post(webhook_url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        print(f"[discord_notify] Échec de l'envoi Discord: {exc}")
        return False
