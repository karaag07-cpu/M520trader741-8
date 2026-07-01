"""Derive macro-regime parameters from raw FRED series history.

The macro regime strategy expects derived features (year-over-year inflation,
a rate *trend*), not raw index levels. This module turns each FRED series'
recent observations into those features. It is pure and dependency-free so it
can be unit-tested without network access.

Input shape: a mapping of ``series_id -> observations`` where observations is
a chronological (oldest -> newest) list of floats. A bare float is accepted
and treated as a single observation.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

Observations = Union[float, int, List[float], None]

# FRED series identifiers used by the macro regime.
YIELD_CURVE = "T10Y2Y"   # 10Y-2Y Treasury spread (percentage points)
CPI = "CPIAUCSL"         # CPI index level (monthly)
FED_FUNDS = "FEDFUNDS"   # Effective federal funds rate (monthly, %)
UNRATE = "UNRATE"        # Unemployment rate (monthly, %)

# A move smaller than this (in the series' own units) counts as "Stable".
_TREND_DEADBAND = 0.05


def _as_list(value: Observations) -> List[float]:
    if value is None:
        return []
    if isinstance(value, (int, float)):
        return [float(value)]
    return [float(v) for v in value if v is not None]


def _latest(value: Observations, default: Optional[float] = None) -> Optional[float]:
    series = _as_list(value)
    return series[-1] if series else default


def _yoy_percent(value: Observations, periods: int = 12) -> Optional[float]:
    """Year-over-year % change of a monthly index (needs periods+1 points)."""
    series = _as_list(value)
    if len(series) < periods + 1:
        return None
    past = series[-(periods + 1)]
    if past == 0:
        return None
    return (series[-1] / past - 1.0) * 100.0


def _trend(value: Observations, lookback: int = 3, deadband: float = _TREND_DEADBAND) -> str:
    """Classify a series' recent direction as Rising / Falling / Stable."""
    series = _as_list(value)
    if len(series) < 2:
        return "Stable"
    past = series[-(lookback + 1)] if len(series) > lookback else series[0]
    delta = series[-1] - past
    if delta > deadband:
        return "Rising"
    if delta < -deadband:
        return "Falling"
    return "Stable"


def derive_macro_params(macro: Dict[str, Observations]) -> Dict[str, object]:
    """Build the kwargs MacroRegimeStrategy.generate_signal expects.

    Missing or too-short series fall back to neutral defaults, so the caller
    always gets a usable, well-formed params dict.
    """
    macro = macro or {}

    yc_spread = _latest(macro.get(YIELD_CURVE), default=1.0)
    inflation_yoy = _yoy_percent(macro.get(CPI))
    if inflation_yoy is None:
        inflation_yoy = 2.0  # neutral default when history is unavailable

    return {
        "yc_spread": yc_spread,
        "inflation_yoy": inflation_yoy,
        "fed_rate_trend": _trend(macro.get(FED_FUNDS)),
        "unrate_trend": _trend(macro.get(UNRATE)),
    }
