"""Submit the bot's orders to a real Alpaca account (paper by default).

By default MinuteTrader trades a local simulator (`PaperTrader`) that never
touches Alpaca. Enabling this broker mirrors each entry to your Alpaca account
so positions show up on the Alpaca dashboard and can be reconciled. With
``paper=True`` (the default) this uses the **paper** account — real order flow,
no real money.

The alpaca-py SDK is imported lazily so importing this module doesn't require
it, and the request-building logic is factored out (``_order_params``) so it's
testable without the SDK or network.
"""

from __future__ import annotations


def _order_params(symbol, side, qty):
    """Decide the Alpaca order parameters (pure, no SDK needed).

    Crypto symbols (containing '/') use good-til-cancelled; equities use a
    day order. Side is normalised to 'BUY'/'SELL'.
    """
    is_crypto = '/' in symbol
    return {
        'symbol': symbol,
        'qty': float(qty),
        'side': 'BUY' if str(side).upper() == 'BUY' else 'SELL',
        'time_in_force': 'gtc' if is_crypto else 'day',
    }


class AlpacaBroker:
    def __init__(self, api_key=None, secret_key=None, paper=True, client=None):
        # ``client`` can be injected for testing; otherwise build a real one.
        if client is not None:
            self.client = client
        else:
            from alpaca.trading.client import TradingClient
            self.client = TradingClient(api_key, secret_key, paper=paper)

    def _build_order_request(self, symbol, side, qty):
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce
        p = _order_params(symbol, side, qty)
        return MarketOrderRequest(
            symbol=p['symbol'],
            qty=p['qty'],
            side=OrderSide.BUY if p['side'] == 'BUY' else OrderSide.SELL,
            time_in_force=TimeInForce.GTC if p['time_in_force'] == 'gtc' else TimeInForce.DAY,
        )

    def submit_order(self, symbol, side, qty):
        """Submit a market order; returns the Alpaca order object."""
        request = self._build_order_request(symbol, side, qty)
        return self.client.submit_order(request)

    def get_positions(self):
        """Return open Alpaca positions as [{symbol, qty(signed), side}]."""
        out = []
        for p in self.client.get_all_positions():
            qty = float(p.qty)
            out.append({
                'symbol': p.symbol,
                'qty': qty,
                'side': 'BUY' if qty >= 0 else 'SELL',
            })
        return out

    def get_account(self):
        """Return a small dict of account fields (cash, buying power, status)."""
        acct = self.client.get_account()
        return {
            'status': getattr(acct, 'status', None),
            'cash': float(getattr(acct, 'cash', 0) or 0),
            'buying_power': float(getattr(acct, 'buying_power', 0) or 0),
        }
