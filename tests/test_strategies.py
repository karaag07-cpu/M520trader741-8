import unittest
import pandas as pd

from signals.base_strategy import SignalType, Conviction
from signals.cross_asset import CrossAssetStrategy
from signals.onchain_sentiment import OnChainSentimentStrategy
from signals.relative_strength import RelativeStrengthStrategy


def _ohlcv(n=25, close=100.0, low=95.0, high=105.0, volume=100.0, symbol='ETH/USDT'):
    df = pd.DataFrame({
        'open': [close] * n,
        'high': [high] * n,
        'low': [low] * n,
        'close': [close] * n,
        'volume': [volume] * n,
    })
    df.attrs['symbol'] = symbol
    return df


def _leader(prev, last):
    """Two-row frame so a strategy can read a last-vs-previous change."""
    return pd.DataFrame({'close': [prev, last]})


class TestCrossAssetStrategy(unittest.TestCase):
    def setUp(self):
        self.strat = CrossAssetStrategy("Cross-Asset", "15m")
        self.data = _ohlcv(symbol='ETH/USDT')

    def test_no_leaders_returns_none(self):
        self.assertIsNone(self.strat.generate_signal(self.data))
        self.assertIsNone(self.strat.generate_signal(self.data, leaders={}))

    def test_dxy_spike_sets_bearish_crypto_bias(self):
        sig = self.strat.generate_signal(
            self.data, leaders={'DXY': _leader(100.0, 100.2)}  # +0.2% > 0.1%
        )
        self.assertIsNotNone(sig)
        self.assertEqual(sig.type, SignalType.NEUTRAL)  # cross-asset is a filter
        self.assertEqual(sig.metadata['bias']['crypto_bias'], 'BEARISH')
        self.assertTrue(sig.metadata['bias']['dxy_spike'])

    def test_dxy_drop_sets_bullish_crypto_bias(self):
        sig = self.strat.generate_signal(
            self.data, leaders={'DXY': _leader(100.0, 99.8)}  # -0.2%
        )
        self.assertEqual(sig.metadata['bias']['crypto_bias'], 'BULLISH')

    def test_yield_spike_sets_bearish_tech_bias(self):
        sig = self.strat.generate_signal(
            self.data, leaders={'US10Y': _leader(4.00, 4.06)}  # +0.06 > 0.05
        )
        self.assertEqual(sig.metadata['bias']['tech_bias'], 'BEARISH')

    def test_btc_breakout_makes_altcoin_bullish(self):
        sig = self.strat.generate_signal(
            self.data, leaders={'BTC': _leader(100.0, 100.6)}  # +0.6% > 0.5%
        )
        self.assertEqual(sig.metadata['bias']['altcoin_bias'], 'BULLISH')

    def test_btc_move_ignored_for_btc_symbol(self):
        # A BTC move shouldn't set an altcoin bias when the target *is* BTC.
        btc_data = _ohlcv(symbol='BTC/USDT')
        sig = self.strat.generate_signal(
            btc_data, leaders={'BTC': _leader(100.0, 101.0)}
        )
        self.assertIsNone(sig)  # no other leaders -> empty bias -> None

    def test_quiet_leaders_return_none(self):
        sig = self.strat.generate_signal(
            self.data, leaders={'DXY': _leader(100.0, 100.01)}  # +0.01% below threshold
        )
        self.assertIsNone(sig)


class TestOnChainSentimentStrategy(unittest.TestCase):
    def setUp(self):
        self.strat = OnChainSentimentStrategy("On-Chain", "1h")
        self.data = _ohlcv(symbol='BTC/USDT')

    def test_no_onchain_data_returns_none(self):
        # Defaults (mvrv 1.5, funding 0.01, flow 0) are neutral.
        self.assertIsNone(self.strat.generate_signal(self.data))

    def test_high_conviction_bullish(self):
        sig = self.strat.generate_signal(
            self.data, onchain={'net_flow_z': -1.0, 'mvrv_ratio': 1.0, 'funding_rate': -0.01}
        )
        self.assertEqual(sig.type, SignalType.BUY)
        self.assertEqual(sig.conviction, Conviction.HIGH)

    def test_medium_bullish_on_flow_extreme(self):
        # Strong outflow but MVRV too high for high-conviction -> MEDIUM buy.
        sig = self.strat.generate_signal(
            self.data, onchain={'net_flow_z': -2.5, 'mvrv_ratio': 1.5, 'funding_rate': 0.01}
        )
        self.assertEqual(sig.type, SignalType.BUY)
        self.assertEqual(sig.conviction, Conviction.MEDIUM)

    def test_bearish_on_high_mvrv(self):
        sig = self.strat.generate_signal(
            self.data, onchain={'net_flow_z': 0.5, 'mvrv_ratio': 3.5, 'funding_rate': 0.01}
        )
        self.assertEqual(sig.type, SignalType.SELL)
        self.assertEqual(sig.conviction, Conviction.MEDIUM)

    def test_bearish_on_high_funding(self):
        sig = self.strat.generate_signal(
            self.data, onchain={'funding_rate': 0.05}
        )
        self.assertEqual(sig.type, SignalType.SELL)


class TestRelativeStrengthStrategy(unittest.TestCase):
    def setUp(self):
        self.strat = RelativeStrengthStrategy("RS Flow", "15m")

    def test_insufficient_history_returns_none(self):
        self.assertIsNone(self.strat.generate_signal(_ohlcv(n=10)))

    def test_volume_spike_above_support_is_high_conviction_buy(self):
        df = _ohlcv(n=25, volume=100.0)
        df.loc[df.index[-1], 'volume'] = 1000.0  # spike vs SMA(20) ~= 145
        sig = self.strat.generate_signal(df)
        self.assertIsNotNone(sig)
        self.assertEqual(sig.type, SignalType.BUY)
        # No benchmark -> rs_ok defaults True -> HIGH.
        self.assertEqual(sig.conviction, Conviction.HIGH)
        self.assertTrue(sig.metadata['volume_spike'])

    def test_underperforming_benchmark_downgrades_to_medium(self):
        df = _ohlcv(n=25, close=100.0, volume=100.0)
        df.loc[df.index[-1], 'volume'] = 1000.0
        benchmark = pd.DataFrame({'close': list(range(100, 125))})  # rising: asset lags
        sig = self.strat.generate_signal(df, benchmark_data=benchmark)
        self.assertEqual(sig.type, SignalType.BUY)
        self.assertEqual(sig.conviction, Conviction.MEDIUM)
        self.assertLess(sig.metadata['rs_value'], 1.0)

    def test_no_volume_spike_returns_none(self):
        # Flat volume -> no spike -> no actionable signal.
        self.assertIsNone(self.strat.generate_signal(_ohlcv(n=25, volume=100.0)))


if __name__ == '__main__':
    unittest.main()
