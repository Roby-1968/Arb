from config import MIN_TRADER_ROI, MIN_TRADER_TRADES

def score_trader(trader):
    """
    Assegna uno score ponderato. La leaderboard grezza (solo PnL)
    è ingannevole: un trader può avere PnL alto ma winrate pessimo
    e sopravvivere per fortuna. Serve un punteggio composito.
    """
    pnl = trader.get("pnl", 0)
    volume = trader.get("volume", 1) or 1
    trades = trader.get("tradeCount", 0)

    roi = pnl / volume
    if trades < MIN_TRADER_TRADES or roi < MIN_TRADER_ROI:
        return None

    # Sharpe-like: premia consistenza, penalizza pochi trade
    import math
    consistency_factor = math.log10(trades)
    score = roi * consistency_factor

    return {
        "wallet": trader.get("proxyWallet"),
        "roi": round(roi, 4),
        "pnl": pnl,
        "trades": trades,
        "score": round(score, 4),
    }

def rank_traders(leaderboard):
    scored = [s for t in leaderboard if (s := score_trader(t))]
    return sorted(scored, key=lambda x: x["score"], reverse=True)