import requests
from config import DATA_API

def fetch_leaderboard(period="all", limit=100):
    """
    Recupera la leaderboard trader.
    period: '1d', '7d', '30d', 'all'
    """
    url = f"{DATA_API}/leaderboard"
    params = {"window": period, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[leaderboard] errore: {e}")
        return []

def fetch_trader_positions(proxy_wallet):
    """Posizioni aperte di un trader specifico."""
    url = f"{DATA_API}/positions"
    params = {"user": proxy_wallet, "sizeThreshold": 1}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[positions] errore: {e}")
        return []

def fetch_trader_activity(proxy_wallet, limit=100):
    """Storico trade recenti (per copiare le entry)."""
    url = f"{DATA_API}/activity"
    params = {"user": proxy_wallet, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[activity] errore: {e}")
        return []