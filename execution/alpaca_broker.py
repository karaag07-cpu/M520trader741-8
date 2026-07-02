"""Submit the bot's orders to a real Alpaca account (paper by default).

By default MinuteTrader trades a local simulator (`PaperTrader`) that never
touches Alpaca. Enabling this broker mirrors each entry to your Alpaca account
so positions show up on the Alpaca dashboard, sizing runs off the real balance,
and the website dashboard can read the live account. With ``paper=True`` (the
default) this uses the **paper** account — real order flow, no real money.

The alpaca-py SDK is imported lazily so importing this module doesn't require
it, and the request-building logic is factored out (``_order_params``) so it's
testable without the SDK or network.
"""

from __future__ import annotations


def _order_params(symbol, side, qty):
    """Decide the Alpaca order parameters (pure, no SDK needed).

    Crypto symbols (containing '/') use good-til-cancelled; equities use a day
    order. Side is normalised to 'BUY'/'SELL'.
    """
    is_crypto = '/' in symbol
    return {
        'symbol': symbol,
        'qty': float(qty),
        'side': 'BUY' if str(side).upper() == 'BUY' else 'SELL',
        'time_in_force': 'gtc' if is_crypto else 'day',
        'is_crypto': is_crypto,
    }


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class AlpacaBroker:
    def __init__(self, api_key=None, secret_key=None, paper=True, client=None):
        # ``client`` can be injected for testing; otherwise build a real one.
        if client is not None:
            self.client = client
        else:
            from alpaca.trading.client import TradingClient
            self.client = TradingClient(api_key, secret_key, paper=paper)

    def _build_order_request(self, symbol, side, qty, take_profit=None, stop_loss=None):
        from alpaca.trading.requests import (
            MarketOrderRequest, TakeProfitRequest, StopLossRequest,
        )
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
        p = _order_params(symbol, side, qty)
        order_side = OrderSide.BUY if p['side'] == 'BUY' else OrderSide.SELL
        tif = TimeInForce.GTC if p['time_in_force'] == 'gtc' else TimeInForce.DAY

        # Bracket orders (Alpaca auto-manages the stop/target) are supported for
        # equities only; crypto falls back to a plain market order.
        if not p['is_crypto'] and take_profit is not None and stop_loss is not None:
            return MarketOrderRequest(
                symbol=p['symbol'], qty=p['qty'], side=order_side, time_in_force=tif,
                order_class=OrderClass.BRACKET,
                take_profit=TakeProfitRequest(limit_price=round(float(take_profit), 2)),
                stop_loss=StopLossRequest(stop_price=round(float(stop_loss), 2)),
            )
        return MarketOrderRequest(
            symbol=p['symbol'], qty=p['qty'], side=order_side, time_in_force=tif,
        )

    def submit_order(self, symbol, side, qty, take_profit=None, stop_loss=None):
        """Submit a market order (bracketed for equities); returns the order."""
        request = self._build_order_request(symbol, side, qty, take_profit, stop_loss)
        return self.client.submit_order(request)

    def get_positions(self):
        """Return open Alpaca positions with entry/current price and PnL."""
        out = []
        for p in self.client.get_all_positions():
            qty = _to_float(p.qty)
            out.append({
                'symbol': p.symbol,
                'qty': qty,
                'side': 'BUY' if qty >= 0 else 'SELL',
                'entry_price': _to_float(getattr(p, 'avg_entry_price', 0)),
                'current_price': _to_float(getattr(p, 'current_price', 0)),
                'unrealized_pnl': _to_float(getattr(p, 'unrealized_pl', 0)),
            })
        return out

    def get_account(self):
        """Return key account figures (status, cash, buying power, equity)."""
        acct = self.client.get_account()
        return {
            'status': str(getattr(acct, 'status', '')),
            'cash': _to_float(getattr(acct, 'cash', 0)),
            'buying_power': _to_float(getattr(acct, 'buying_power', 0)),
            'equity': _to_float(getattr(acct, 'equity', 0)),
            'portfolio_value': _to_float(getattr(acct, 'portfolio_value', 0)),
        }
