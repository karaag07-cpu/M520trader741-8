class RiskManager:
    def __init__(self, risk_reward_ratio=3.0):
        self.rr_ratio = risk_reward_ratio

    def calculate_trade_levels(self, signal_type, current_price, atr=None, atr_multiplier=2.0):
        """
        Calculates Entry Zone, Stop-Loss, and Multiple Take-Profit levels.
        """
        entry_price = current_price
        
        if atr is not None:
            stop_distance = atr * atr_multiplier
        else:
            # Fallback to flat 1%
            stop_loss_pct = 0.01
            stop_distance = entry_price * stop_loss_pct
            
        tp_distance = stop_distance * self.rr_ratio
        
        # Entry zone is current_price +/- 0.1%
        entry_offset = entry_price * 0.001
        
        if signal_type == "BUY" or signal_type == "SignalType.BUY":
            entry_zone = (entry_price - entry_offset, entry_price + entry_offset)
            stop_loss = entry_price - stop_distance
            tp_levels = [
                entry_price + tp_distance,
                entry_price + tp_distance * 1.5,
                entry_price + tp_distance * 2.0
            ]
        elif signal_type == "SELL" or signal_type == "SignalType.SELL":
            entry_zone = (entry_price + entry_offset, entry_price - entry_offset)
            stop_loss = entry_price + stop_distance
            tp_levels = [
                entry_price - tp_distance,
                entry_price - tp_distance * 1.5,
                entry_price - tp_distance * 2.0
            ]
        else:
            return None

        return {
            'entry_zone': entry_zone,
            'stop_loss': stop_loss,
            'tp_levels': tp_levels
        }

    def validate_risk(self, account_balance, entry_price, stop_loss,
                      risk_per_trade=0.01, max_position_fraction=0.25,
                      size_modifier=1.0):
        """
        Determines position size using fixed-fractional risk.

        The dollar amount risked on the trade is
        ``account_balance * risk_per_trade * size_modifier``. Dividing this by
        the per-unit risk (the distance between entry and stop-loss) yields the
        quantity such that being stopped out loses at most the risk budget.
        The resulting notional is then capped at ``max_position_fraction`` of
        the account so a single tight-stop trade can't dominate the book.

        ``size_modifier`` is designed to accept the ``position_size_modifier``
        emitted by the macro-regime strategy (e.g. 0.0 to stand aside, 0.5 to
        halve exposure in a risk-off regime).

        Args:
            account_balance: Total account equity.
            entry_price: Intended entry price (must be > 0).
            stop_loss: Stop-loss price; its distance from entry sets the risk.
            risk_per_trade: Fraction of equity to risk (0 < x < 1).
            max_position_fraction: Cap on notional as a fraction of equity.
            size_modifier: Multiplier applied to the risk budget (>= 0).

        Returns:
            A dict with ``quantity``, ``notional``, ``risk_amount`` and
            ``stop_distance``, or ``None`` when the inputs can't produce a
            valid position.
        """
        if account_balance <= 0 or entry_price <= 0:
            return None
        if not 0 < risk_per_trade < 1:
            return None
        if not 0 < max_position_fraction <= 1:
            return None
        if size_modifier <= 0:
            return None

        stop_distance = abs(entry_price - stop_loss)
        if stop_distance <= 0:
            return None

        risk_amount = account_balance * risk_per_trade * size_modifier
        quantity = risk_amount / stop_distance

        # Never let a tight stop size us past the notional cap.
        max_notional = account_balance * max_position_fraction
        if quantity * entry_price > max_notional:
            quantity = max_notional / entry_price

        if quantity <= 0:
            return None

        return {
            'quantity': quantity,
            'notional': quantity * entry_price,
            'risk_amount': min(risk_amount, quantity * stop_distance),
            'stop_distance': stop_distance
        }
