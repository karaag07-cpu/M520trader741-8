class RiskManager:
    def __init__(self, risk_reward_ratio=3.0):
        self.rr_ratio = risk_reward_ratio

    def calculate_trade_levels(self, signal_type, current_price, volatility_data=None):
        """
        Calculates Entry Zone, Stop-Loss, and Multiple Take-Profit levels.
        """
        entry_price = current_price
        
        # Simple implementation: 
        # Entry zone is current_price +/- 0.1%
        # 1% SL
        # 3 TP levels starting at 3%
        
        stop_loss_pct = 0.01
        tp_base_pct = stop_loss_pct * self.rr_ratio
        
        if signal_type == "BUY" or signal_type == "SignalType.BUY":
            entry_zone = (entry_price * 0.999, entry_price * 1.001)
            stop_loss = entry_price * (1 - stop_loss_pct)
            tp_levels = [
                entry_price * (1 + tp_base_pct),
                entry_price * (1 + tp_base_pct * 1.5),
                entry_price * (1 + tp_base_pct * 2.0)
            ]
        elif signal_type == "SELL" or signal_type == "SignalType.SELL":
            entry_zone = (entry_price * 1.001, entry_price * 0.999)
            stop_loss = entry_price * (1 + stop_loss_pct)
            tp_levels = [
                entry_price * (1 - tp_base_pct),
                entry_price * (1 - tp_base_pct * 1.5),
                entry_price * (1 - tp_base_pct * 2.0)
            ]
        else:
            return None

        return {
            'entry_zone': entry_zone,
            'stop_loss': stop_loss,
            'tp_levels': tp_levels
        }

    def calculate_position_size(self, account_balance, entry_price, stop_loss,
                                risk_per_trade=0.01):
        """
        Determine position size (in units) from account risk.

        Risks a fixed fraction of the account (``risk_per_trade``) on the
        distance between entry and stop-loss, so that a stop-out loses exactly
        that fraction:  size = (balance * risk_per_trade) / |entry - stop_loss|.

        Returns 0.0 when inputs are non-positive or the stop distance is zero,
        so callers never place a trade with undefined/infinite size.
        """
        if account_balance <= 0 or entry_price <= 0:
            return 0.0
        if not 0 < risk_per_trade < 1:
            raise ValueError("risk_per_trade must be between 0 and 1")

        risk_capital = account_balance * risk_per_trade
        per_unit_risk = abs(entry_price - stop_loss)
        if per_unit_risk <= 0:
            return 0.0

        size = risk_capital / per_unit_risk

        # Never let a single position exceed the account's buying power.
        max_size = account_balance / entry_price
        return min(size, max_size)

    def validate_risk(self, account_balance, entry_price, stop_loss,
                      risk_per_trade=0.01):
        """Backwards-compatible alias for :meth:`calculate_position_size`."""
        return self.calculate_position_size(account_balance, entry_price,
                                            stop_loss, risk_per_trade)
