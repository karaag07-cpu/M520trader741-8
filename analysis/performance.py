"""Pure performance analytics — no SDK or network required.

Two entry points:
- ``summarize_trades`` turns a list of closed trades (each with a ``pnl``) into
  win rate, profit factor, average win/loss, expectancy and max drawdown of the
  cumulative P&L curve.
- ``equity_metrics`` turns an equity curve (list of account values over time)
  into total return and max drawdown.
"""

from __future__ import annotations


def _max_drawdown_pct(series):
    """Largest peak-to-trough drop of a value series, as a percentage."""
    peak = None
    max_dd = 0.0
    for v in series:
        peak = v if peak is None else max(peak, v)
        if peak and peak > 0:
            dd = (peak - v) / peak * 100.0
            max_dd = max(max_dd, dd)
    return max_dd


def summarize_trades(trades):
    """Summarize a list of closed trades (dicts containing ``pnl``)."""
    pnls = [float(t['pnl']) for t in trades if t.get('pnl') is not None]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    net = sum(pnls)

    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = float('inf') if gross_profit > 0 else 0.0

    # Max drawdown of the cumulative P&L curve (starting from 0).
    cumulative = []
    running = 0.0
    for p in pnls:
        running += p
        cumulative.append(running)

    return {
        'num_trades': n,
        'wins': len(wins),
        'losses': len(losses),
        'win_rate_pct': (len(wins) / n * 100.0) if n else 0.0,
        'net_pnl': net,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'profit_factor': profit_factor,
        'avg_win': (gross_profit / len(wins)) if wins else 0.0,
        'avg_loss': (gross_loss / len(losses)) if losses else 0.0,
        'expectancy': (net / n) if n else 0.0,
        'max_drawdown': _max_drawdown_pct([0.0] + cumulative),
    }


def equity_metrics(equity):
    """Total return and max drawdown from an equity curve (list of values)."""
    vals = [float(e) for e in equity if e is not None]
    if not vals:
        return {'start': 0.0, 'end': 0.0, 'net_pnl': 0.0, 'return_pct': 0.0,
                'max_drawdown_pct': 0.0, 'points': 0}
    start, end = vals[0], vals[-1]
    net = end - start
    return {
        'start': start,
        'end': end,
        'net_pnl': net,
        'return_pct': (net / start * 100.0) if start else 0.0,
        'max_drawdown_pct': _max_drawdown_pct(vals),
        'points': len(vals),
    }


def format_report(summary=None, equity=None):
    """Render a plain-text report from either/both summaries."""
    lines = ["=" * 40, "  MinuteTrader — Performance Report", "=" * 40]
    if equity is not None:
        pf = equity
        lines += [
            "Account equity:",
            f"  Start:         ${pf['start']:,.2f}",
            f"  Current:       ${pf['end']:,.2f}",
            f"  Net P&L:       ${pf['net_pnl']:+,.2f} ({pf['return_pct']:+.2f}%)",
            f"  Max drawdown:  {pf['max_drawdown_pct']:.2f}%",
            "-" * 40,
        ]
    if summary is not None:
        pf_str = "inf" if summary['profit_factor'] == float('inf') else f"{summary['profit_factor']:.2f}"
        lines += [
            "Closed trades:",
            f"  Trades:        {summary['num_trades']} "
            f"({summary['wins']}W / {summary['losses']}L)",
            f"  Win rate:      {summary['win_rate_pct']:.1f}%",
            f"  Net P&L:       ${summary['net_pnl']:+,.2f}",
            f"  Profit factor: {pf_str}",
            f"  Avg win/loss:  ${summary['avg_win']:,.2f} / ${summary['avg_loss']:,.2f}",
            f"  Expectancy:    ${summary['expectancy']:+,.2f} per trade",
            f"  Max drawdown:  {summary['max_drawdown']:.2f}%",
            "-" * 40,
        ]
    if equity is None and summary is None:
        lines.append("No data yet — let the bot run and trade first.")
    return "\n".join(lines)
