"""
Vérifie si la date du jour se trouve dans une fenêtre de mercato active.
Sert de garde-fou en plus du cron GitHub Actions.
"""

from datetime import date

from config import MERCATO_WINDOWS


def _in_range(today: date, start: tuple, end: tuple) -> bool:
    """Vérifie que `today` est compris entre (mois, jour) start et end, incl."""
    start_date = date(today.year, start[0], start[1])
    end_date = date(today.year, end[0], end[1])
    return start_date <= today <= end_date


def is_mercato_open(today: date = None) -> bool:
    """Retourne True si on est dans au moins une fenêtre de mercato définie."""
    today = today or date.today()
    return any(
        _in_range(today, window["start"], window["end"])
        for window in MERCATO_WINDOWS
    )


def active_window_name(today: date = None) -> str | None:
    """Retourne le nom de la fenêtre active ('été', 'hiver'), ou None."""
    today = today or date.today()
    for window in MERCATO_WINDOWS:
        if _in_range(today, window["start"], window["end"]):
            return window["name"]
    return None


def active_window_bounds(today: date = None) -> tuple[date, date] | None:
    """
    Retourne (date_debut, date_fin) de la fenêtre de mercato active pour
    l'année en cours, ou None si aucune fenêtre n'est active. Sert à filtrer
    les transferts scrapés pour ne garder que ceux de la période en cours
    (et éviter de re-signaler tout l'historique à chaque réouverture).
    """
    today = today or date.today()
    for window in MERCATO_WINDOWS:
        start = date(today.year, window["start"][0], window["start"][1])
        end = date(today.year, window["end"][0], window["end"][1])
        if start <= today <= end:
            return start, end
    return None
