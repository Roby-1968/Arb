from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType
from py_clob_client.order_builder.constants import BUY
from config import PRIVATE_KEY, CLOB_API, MAX_POSITION_PCT

class Executor:
    def __init__(self, bankroll):
        self.bankroll = bankroll
        self.client = ClobClient(
            CLOB_API, key=PRIVATE_KEY, chain_id=137
        )
        self.client.set_api_creds(self.client.create_or_derive_api_creds())

    def place_order(self, token_id, price, signal_weight):
        # Kelly frazionario semplificato sul peso del segnale
        size_usd = self.bankroll * MAX_POSITION_PCT * min(signal_weight, 1.0)
        shares = round(size_usd / price, 2)

        order = OrderArgs(
            token_id=token_id,
            price=price,
            size=shares,
            side=BUY,
        )
        signed = self.client.create_order(order)
        resp = self.client.post_order(signed, OrderType.GTC)
        print(f"[executor] ordine: {shares} @ {price} → {resp}")
        return resp