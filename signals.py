from leaderboard import fetch_trader_activity
from datetime import datetime, timezone

def extract_fresh_signals(top_traders, max_age_min=10):
    """
    Guarda i trade più recenti dei top trader.
    Se più trader entrano sullo stesso mercato/lato → segnale forte
    (consenso = alta convinzione).
    """
    now = datetime.now(timezone.utc).timestamp()
    market_votes = {}

    for trader in top_traders[:20]:
        activity = fetch_trader_activity(trader["wallet"], limit=20)
        for trade in activity:
            if trade.get("type") != "TRADE":
                continue
            ts = trade.get("timestamp", 0)
            if (now - ts) / 60 > max_age_min:
                continue

            key = (trade["market"], trade["outcome"])
            market_votes.setdefault(key, {"weight": 0, "traders": []})
            market_votes[key]["weight"] += trader["score"]
            market_votes[key]["traders"].append(trader["wallet"])

    # Ordina per peso di consenso
    signals = [
        {"market": k[0], "outcome": k[1], **v}
        for k, v in market_votes.items()
    ]
    return sorted(signals, key=lambda x: x["weight"], reverse=True)