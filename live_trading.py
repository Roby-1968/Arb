from __future__ import annotations

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from typing import Optional

from config import (
    POLL_INTERVAL_SEC,
    LIVE_MAX_USD_PER_TRADE,
    LIVE_MAX_OPEN_POSITIONS,
    LIVE_MAX_TOTAL_USD,
)
from leaderboard import fetch_leaderboard
from trader_analysis import rank_traders
from signals import generate_signals, fetch_market_prices, fetch_markets_info
from executor import Executor
import telegram_alerts as tg

logger = logging.getLogger("live_trading")

LEDGER_PATH = Path("live_ledger.json")
KILL_SWITCH = Path("STOP")


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class LivePosition:
    market_id: str
    outcome: str
    token_id: str
    entry_price: float
    size_usd: float
    shares: float
    opened_at: str
    source_trader: str
    closed: bool = False
    exit_price: Optional[float] = None
    closed_at: Optional[str] = None
    pnl_usd: float = 0.0


@dataclass
class LiveLedger:
    positions: list[LivePosition] = field(default_factory=list)
    realized_pnl: float = 0.0
    history: list[dict] = field(default_factory=list)

    @property
    def open_positions(self) -> list[LivePosition]:
        return [p for p in self.positions if not p.closed]

    @property
    def committed(self) -> float:
        return sum(p.size_usd for p in self.open_positions)


# ============================================================
# LEDGER LOAD/SAVE
# ============================================================

def _load() -> LiveLedger:
    lg = LiveLedger()
    if LEDGER_PATH.exists():
        raw = json.loads(LEDGER_PATH.read_text())
        lg.realized_pnl = raw.get("realized_pnl", 0.0)
        lg.history = raw.get("history", [])
        lg.positions = [LivePosition(**p) for p in raw.get("positions", [])]
    return lg


def _save(lg: LiveLedger) -> None:
    LEDGER_PATH.write_text(json.dumps({
        "realized_pnl": lg.realized_pnl,
        "positions": [asdict(p) for p in lg.positions],
        "history": lg.history,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }, indent=2))


# ============================================================
# LIVE TRADING LOOP (MODIFICATO)
# ============================================================

def run_live():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # 🔥 AVVIO AUTOMATICO (senza input)
    print("\n" + "=" * 52)
    print("  ⚠️  SESSIONE LIVE — AVVIO AUTOMATICO (GitHub Actions) ⚠️")
    print(f"  Max per ordine .......... {LIVE_MAX_USD_PER_TRADE:.2f}$")
    print(f"  Max posizioni aperte .... {LIVE_MAX_OPEN_POSITIONS}")
    print(f"  Max capitale impegnato .. {LIVE_MAX_TOTAL_USD:.2f}$")
    print("  Kill switch: crea un file 'STOP' per fermare il bot")
    print("=" * 52)

    execu = Executor()  # fallisce subito se .env incompleto
    ledger = _load()

    logger.info(
        "Live avviato: %d posizioni aperte, PnL storico %+.2f$",
        len(ledger.open_positions), ledger.realized_pnl,
    )
    tg.send("🔴 <b>SESSIONE LIVE AVVIATA</b> — capitale reale")

    loop = 0

    while True:
        loop += 1

        # 🔥 Kill switch
        if KILL_SWITCH.exists():
            logger.warning("File STOP rilevato: esco dal loop")
            tg.send("🛑 Kill switch attivato, bot live fermato")
            break

        try:
            # ============================================================
            # FETCH DATI
            # ============================================================
            leaders = fetch_leaderboard(period="30d", limit=50)
            qualified = rank_traders(leaders)
            signals, market_prices = generate_signals(qualified)

            open_ids = {p.market_id for p in ledger.open_positions}
            missing = open_ids - set(market_prices)
            if missing:
                market_prices.update(fetch_market_prices(missing))

            # ============================================================
            # ANTI-CHURN
            # ============================================================
            sell_keys = {(s.market_id, s.outcome) for s in signals if s.action == "SELL"}
            now = datetime.now(timezone.utc)
            recently_closed = set()

            for p in ledger.positions:
                if p.closed and p.closed_at:
                    age = (now - datetime.fromisoformat(p.closed_at)).total_seconds() / 60
                    if age < 30:
                        recently_closed.add((p.market_id, p.outcome))

            # ============================================================
            # APERTURE POSIZIONI
            # ============================================================
            attempted: set[tuple[str, str]] = set()

            for sig in signals:
                if sig.action != "BUY" or not sig.token_id:
                    continue

                key = (sig.market_id, sig.outcome)
                if key in attempted:
                    continue
                attempted.add(key)

                if key in sell_keys or key in recently_closed:
                    continue

                if any(p.market_id == sig.market_id and p.outcome == sig.outcome
                       for p in ledger.open_positions):
                    continue

                # Guard-rail
                if len(ledger.open_positions) >= LIVE_MAX_OPEN_POSITIONS:
                    logger.info("Max posizioni raggiunto, niente nuove entry")
                    break

                size = min(LIVE_MAX_USD_PER_TRADE,
                           LIVE_MAX_TOTAL_USD - ledger.committed)

                if size < 1.0:
                    logger.info("Capitale massimo impegnato, niente nuove entry")
                    break

                resp, px, shares = execu.buy(sig.token_id, size)
                if resp is None:
                    continue

                try:
                    real_usd = float(resp.get("makingAmount", 0)) or px * shares
                    real_shares = float(resp.get("takingAmount", 0)) or shares
                except (TypeError, ValueError):
                    real_usd, real_shares = px * shares, shares

                real_entry = real_usd / real_shares if real_shares else px

                pos = LivePosition(
                    market_id=sig.market_id,
                    outcome=sig.outcome,
                    token_id=sig.token_id,
                    entry_price=real_entry,
                    size_usd=real_usd,
                    shares=real_shares,
                    opened_at=datetime.now(timezone.utc).isoformat(),
                    source_trader=sig.trader_addr,
                )

                ledger.positions.append(pos)
                ledger.history.append({"event": "OPEN", "ts": pos.opened_at, **asdict(pos)})
                tg.alert_open(pos)

            # ============================================================
            # CHIUSURE POSIZIONI
            # ============================================================
            open_market_ids = {p.market_id for p in ledger.open_positions}
            markets_info = fetch_markets_info(open_market_ids)

            for pos in list(ledger.open_positions):
                info = markets_info.get(pos.market_id, {})
                resolved = info.get("closed", False)

                px = info.get("prices", {}).get(
                    pos.outcome,
                    market_prices.get(pos.market_id, {}).get(pos.outcome),
                )

                reason = None

                if resolved and px is not None:
                    reason = ("market_resolved_win" if px >= 0.5 else "market_resolved_loss")
                elif px is not None and px >= 0.999:
                    reason = "market_resolved_win"
                elif px is not None and px <= 0.001:
                    reason = "market_resolved_loss"
                elif any(s.market_id == pos.market_id and s.outcome == pos.outcome
                         and s.action == "SELL" for s in signals):
                    reason = "source_sell"

                if reason is None:
                    continue

                if "resolved" in reason and markets_info.get(pos.market_id, {}).get("closed"):
                    resp, exit_px = None, None
                else:
                    resp, exit_px = execu.sell(pos.token_id, pos.shares)
                    if resp is None and "resolved" not in reason:
                        continue

                if resp is not None:
                    try:
                        usd_in = float(resp.get("takingAmount", 0))
                        sh_out = float(resp.get("makingAmount", 0))
                        final_px = usd_in / sh_out if sh_out else exit_px
                    except (TypeError, ValueError):
                        final_px = exit_px
                else:
                    final_px = 1.0 if "win" in reason else 0.0

                pos.closed = True
                pos.exit_price = final_px
                pos.closed_at = datetime.now(timezone.utc).isoformat()
                pos.pnl_usd = pos.shares * (final_px - pos.entry_price)
                ledger.realized_pnl += pos.pnl_usd

                ledger.history.append({
                    "event": "CLOSE",
                    "ts": pos.closed_at,
                    "reason": reason,
                    **asdict(pos)
                })

                tg.alert_close(pos, reason)

            logger.info(
                "--- Loop %d | aperte=%d | impegnato=%.2f$ | PnL realizzato=%+.2f$",
                loop, len(ledger.open_positions), ledger.committed, ledger.realized_pnl,
            )

            _save(ledger)

        except Exception as e:
            # 🔥 RESTART IMMEDIATO
            logger.exception("Errore nel loop %d: %s", loop, e)
            tg.send(f"❌ Errore nel loop {loop}: {e}")
            tg.send("♻️ Riavvio immediato del bot LIVE...")
            time.sleep(3)
            continue

        logger.info("In attesa %d secondi...", POLL_INTERVAL_SEC)
        time.sleep(POLL_INTERVAL_SEC)


# ============================================================
# MAIN — AVVIO AUTOMATICO
# ============================================================

if __name__ == "__main__":
    print("Avvio automatico della SESSIONE LIVE (GitHub Actions)")
    run_live()
