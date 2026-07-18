"""
Scrape la page "transferts" BeSoccer d'un club (onglet "Officiels" par
défaut) pour détecter les arrivées et départs, avec le montant déjà inclus.

Structure HTML confirmée (via inspection manuelle) : chaque transfert est
un <li class="sign-list"> contenant :
- <p class="pl-name">        -> nom du joueur
- <p class="date">           -> date du transfert
- div.shield > img[alt]      -> nom du club adverse (dans l'attribut alt)
- div.data-transfer > p, p   -> type de transfert ("Transfert.", "Prêt.",
                                 "Libéré.", "Transfert gratuit.") et montant

Seuls les transferts dont la date tombe dans la fenêtre de mercato active
sont conservés (voir active_window_bounds dans mercato_window.py) : on ne
veut pas re-signaler tout l'historique à chaque nouvelle ouverture du
mercato.

NOTE : seul le PSG est scrapé ici pour l'instant (voir config.py et le
README pour le Real Madrid, mis en pause à cause d'un anti-bot).
"""

import re
import time
import requests
from bs4 import BeautifulSoup

from config import CLUBS, REQUEST_TIMEOUT_SECONDS, USER_AGENT
from mercato_window import active_window_bounds

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

MONTH_MAP = {
    "JAN": 1, "FEV": 2, "FÉV": 2, "MAR": 3, "AVR": 4, "MAI": 5,
    "JUIN": 6, "JUIL": 7, "AOU": 8, "AOÛ": 8, "SEP": 9,
    "OCT": 10, "NOV": 11, "DEC": 12, "DÉC": 12,
}
DATE_PATTERN = re.compile(r"(\d{1,2})\s+([A-ZÉÛÔ]+)\s+(\d{4})")


def _get_with_retry(url: str, max_attempts: int = 3) -> requests.Response:
    """GET avec une nouvelle tentative en cas de 406 transitoire (léger anti-bot BeSoccer)."""
    last_exc = None
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as exc:
            last_exc = exc
            if attempt < max_attempts - 1:
                time.sleep(2 * (attempt + 1))
    raise last_exc


def _parse_date(text: str):
    """Parse '01 JUIL 2026' -> datetime.date(2026, 7, 1), ou None si échec."""
    from datetime import date as date_cls
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    day, month_abbr, year = match.groups()
    month = MONTH_MAP.get(month_abbr[:4]) or MONTH_MAP.get(month_abbr[:3])
    if not month:
        return None
    try:
        return date_cls(int(year), month, int(day))
    except ValueError:
        return None


def _format_amount(text: str) -> str:
    """Normalise '74,0M.€' -> '74,0 M€' pour l'affichage."""
    return text.replace("M.€", " M€").replace("M€", " M€").strip()


def _parse_sign_list_item(li_tag, direction: str) -> dict | None:
    a = li_tag.find("a", class_="item-box")
    if not a:
        return None

    href = a.get("href", "")
    source_url = href if href.startswith("http") else "https://fr.besoccer.com" + href

    name_tag = li_tag.find("p", class_="pl-name")
    player_name = name_tag.get_text(strip=True) if name_tag else None
    if not player_name:
        return None

    date_tag = li_tag.find("p", class_="date")
    transfer_date = _parse_date(date_tag.get_text(strip=True)) if date_tag else None

    other_club = None
    shield_div = li_tag.find("div", class_="shield")
    if shield_div:
        img = shield_div.find("img")
        if img and img.get("alt"):
            other_club = img["alt"].strip()

    transfer_type = None
    amount = None
    data_div = li_tag.find("div", class_="data-transfer")
    if data_div:
        ps = data_div.find_all("p")
        if len(ps) >= 1:
            transfer_type = ps[0].get_text(strip=True).rstrip(".") or None
        if len(ps) >= 2:
            raw_amount = ps[1].get_text(strip=True)
            amount = _format_amount(raw_amount) if raw_amount else None

    return {
        "player_name": player_name,
        "other_club": other_club,
        "transfer_type": transfer_type,
        "amount": amount,
        "contract_duration": None,  # non disponible sur cette page BeSoccer
        "source_url": source_url,
        "direction": direction,
        "transfer_date": transfer_date,
    }


def scrape_club(club_key: str) -> list[dict]:
    """
    Scrape la page transferts BeSoccer d'un club et retourne uniquement les
    transferts (arrivées + départs) dont la date tombe dans la fenêtre de
    mercato actuellement active.
    """
    club = CLUBS[club_key]
    url = club["besoccer_url"]

    window_bounds = active_window_bounds()
    if not window_bounds:
        return []  # garde-fou : ne devrait pas arriver (main.py vérifie déjà)
    window_start, window_end = window_bounds

    resp = _get_with_retry(url)
    soup = BeautifulSoup(resp.text, "html.parser")

    transfers = []
    current_direction = None

    for tag in soup.find_all(True):
        text = tag.get_text(strip=True)

        if text == "Arrivée":
            current_direction = "arrival"
            continue
        if text == "Départ":
            current_direction = "departure"
            continue

        if tag.name == "li" and "sign-list" in (tag.get("class") or []) and current_direction:
            parsed = _parse_sign_list_item(tag, current_direction)
            if not parsed:
                continue

            transfer_date = parsed.pop("transfer_date")
            if transfer_date is None:
                continue  # date illisible, on ignore plutôt que de risquer un faux positif
            if not (window_start <= transfer_date <= window_end):
                continue  # hors de la fenêtre de mercato en cours -> ignoré

            transfers.append(parsed)

    return transfers


def scrape_all_clubs() -> dict[str, list[dict]]:
    """Scrape tous les clubs définis dans config.CLUBS."""
    results = {}
    for club_key in CLUBS:
        try:
            results[club_key] = scrape_club(club_key)
        except requests.RequestException as exc:
            print(f"[scraper_club] Erreur en scrapant {club_key}: {exc}")
            results[club_key] = []
    return results
