import unittest
from unittest.mock import patch, MagicMock

from data.fetchers import MacroDataFetcher, DataPipeline


def _fred_response(values):
    """Mimic a FRED observations payload (newest-first)."""
    resp = MagicMock()
    resp.json.return_value = {'observations': [{'value': v} for v in values]}
    return resp


class TestMacroFetcher(unittest.TestCase):
    def test_history_is_chronological_oldest_to_newest(self):
        fetcher = MacroDataFetcher(api_key='x')
        # FRED returns newest-first; the method should reverse to oldest-first.
        with patch('data.fetchers.requests.get', return_value=_fred_response(['315', '311', '300'])):
            hist = fetcher.fetch_series_history('CPIAUCSL', limit=3)
        self.assertEqual(hist, [300.0, 311.0, 315.0])

    def test_non_numeric_observations_skipped(self):
        fetcher = MacroDataFetcher(api_key='x')
        with patch('data.fetchers.requests.get', return_value=_fred_response(['4.5', '.', '4.75'])):
            hist = fetcher.fetch_series_history('FEDFUNDS')
        self.assertEqual(hist, [4.75, 4.5])  # '.' dropped, then reversed

    def test_fetch_series_returns_latest_value(self):
        fetcher = MacroDataFetcher(api_key='x')
        with patch('data.fetchers.requests.get', return_value=_fred_response(['5.0'])):
            self.assertEqual(fetcher.fetch_series('FEDFUNDS'), 5.0)

    def test_pipeline_history_empty_without_macro_fetcher(self):
        # No FRED key configured -> no macro fetcher -> empty history (mock mode).
        pipeline = DataPipeline(config={})
        self.assertIsNone(pipeline.macro)
        self.assertEqual(pipeline.fetch_macro_history(['T10Y2Y', 'CPIAUCSL']), {})


if __name__ == '__main__':
    unittest.main()
