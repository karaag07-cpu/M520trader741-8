import unittest
from unittest.mock import patch

import data.fetchers as fetchers
from data.fetchers import DataPipeline


class _FakeAlpacaStock:
    def __init__(self, api_key=None, secret_key=None, paper=True):
        self.kind = 'alpaca_stock'


class _FakeAlpacaCrypto:
    def __init__(self, api_key=None, secret_key=None):
        self.kind = 'alpaca_crypto'


class _FakeBinance:
    def __init__(self, exchange_id='binance', use_testnet=True):
        self.kind = 'binance'

        class _Ex:
            apiKey = None
            secret = None
        self.exchange = _Ex()


def _patched():
    return patch.multiple(
        fetchers,
        StockDataFetcher=_FakeAlpacaStock,
        AlpacaCryptoDataFetcher=_FakeAlpacaCrypto,
        CryptoDataFetcher=_FakeBinance,
    )


class TestPipelineRouting(unittest.TestCase):
    def test_alpaca_serves_both_stocks_and_crypto(self):
        cfg = {'exchanges': {'alpaca': {'api_key': 'k', 'api_secret': 's'}}}
        with _patched():
            p = DataPipeline(cfg)
        self.assertEqual(p.stock.kind, 'alpaca_stock')
        self.assertEqual(p.crypto.kind, 'alpaca_crypto')

    def test_alpaca_preferred_over_binance_for_crypto(self):
        cfg = {'exchanges': {
            'alpaca': {'api_key': 'k', 'api_secret': 's'},
            'binance': {'api_key': 'bk', 'api_secret': 'bs'},
        }}
        with _patched():
            p = DataPipeline(cfg)
        self.assertEqual(p.crypto.kind, 'alpaca_crypto')  # not binance

    def test_binance_fallback_when_no_alpaca(self):
        cfg = {'exchanges': {'binance': {'api_key': 'bk', 'api_secret': 'bs'}}}
        with _patched():
            p = DataPipeline(cfg)
        self.assertEqual(p.crypto.kind, 'binance')
        self.assertIsNone(p.stock)

    def test_no_credentials_means_no_fetchers(self):
        with _patched():
            p = DataPipeline({})
        self.assertIsNone(p.stock)
        self.assertIsNone(p.crypto)
        self.assertIsNone(p.forex)
        self.assertIsNone(p.macro)


if __name__ == '__main__':
    unittest.main()
