"""
Point d'entrée du script. Orchestre :
1. Vérification de la fenêtre de mercato active (garde-fou en plus du cron).
2. Scraping des transferts officiels des clubs suivis (source : BeSoccer).
3. Pour chaque transfert détecté, déjà notifié -> ignoré, sinon -> notifié.
4. Sauvegarde de l'état.
"""

import sys

from mercato_window import is_mercato_open, active_window_name
from scraper_club import scrape_all_clubs
from discord_notify import send_transfer_alert
from state import load_state, save_state, make_key, is_notified, mark_notified


def process_club(club_key: str, raw_transfers: list[dict], state: dict) -> None:
    for transfer in raw_transfers:
        key = make_key(transfer["player_name"], club_key, transfer["direction"])

        if is_notified(state, key):
            continue  # déjà envoyé, on ignore définitivement

        sent = send_transfer_alert(transfer, club_key)
        if sent:
            mark_notified(state, key, transfer)
            print(f"[main] Notifié: {transfer['player_name']} ({club_key})")
        else:
            print(f"[main] Échec d'envoi Discord pour {transfer['player_name']} ({club_key}), retenté au prochain run.")


def main() -> int:
    if not is_mercato_open():
        print("[main] Hors période de mercato, le script ne fait rien.")
        return 0

    window = active_window_name()
    print(f"[main] Mercato {window} actif, lancement du scan.")

    state = load_state()

    scraped = scrape_all_clubs()
    for club_key, raw_transfers in scraped.items():
        process_club(club_key, raw_transfers, state)

    save_state(state)
    print("[main] Terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
