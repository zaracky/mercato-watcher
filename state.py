"""
Gère le fichier d'état persistant (seen_transfers.json).

Un seul registre : "notified" -- les transferts déjà envoyés sur Discord,
pour ne jamais les renvoyer une deuxième fois.

Règle métier (mise à jour) : on notifie dès qu'un transfert officiel est
détecté, montant trouvé ou non ("non communiqué" sinon). On ne bloque plus
l'alerte en attendant le montant, car il est impossible de distinguer de
façon fiable "montant pas encore communiqué" (transfert entre 2 clubs) de
"il n'y aura jamais de montant" (agent libre, entraîneur, etc.).
"""

import json
import os
from config import STATE_FILE


def _empty_state() -> dict:
    return {"notified": {}}


def load_state(path: str = STATE_FILE) -> dict:
    if not os.path.exists(path):
        return _empty_state()
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return _empty_state()
    data.setdefault("notified", {})
    return data


def save_state(state: dict, path: str = STATE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


def make_key(player_name: str, club: str, direction: str) -> str:
    """
    Clé unique pour un transfert.
    direction: "arrival" ou "departure" (par rapport au club suivi).
    """
    normalized = player_name.strip().lower().replace(" ", "_")
    return f"{club}:{direction}:{normalized}"


def is_notified(state: dict, key: str) -> bool:
    return key in state["notified"]


def mark_notified(state: dict, key: str, transfer: dict) -> None:
    state["notified"][key] = transfer
