import os

# Polymarket usa Polygon + CLOB API
CLOB_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"

# Chiave privata wallet (usa .env, MAI hardcoded)
PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY")
WALLET_ADDR = os.getenv("POLY_WALLET")

# Parametri risk management (fondamentali)
MAX_POSITION_PCT = 0.02      # max 2% capitale per trade
MIN_TRADER_ROI = 0.15        # segui solo trader con ROI storico >15%
MIN_TRADER_TRADES = 50       # almeno 50 trade per validità statistica
POLL_INTERVAL = 30           # secondi