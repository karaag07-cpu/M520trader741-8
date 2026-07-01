import pandas as pd
import requests
from datetime import datetime, timedelta

# Broker SDKs (ccxt, alpaca-py, oandapyV20) are imported lazily inside the
# fetchers that use them, so importing this module — e.g. for the FRED macro
# fetcher or a single asset class — doesn't require every broker SDK installed.


class CryptoDataFetcher:
    def __init__(self, exchange_id='binance', use_testnet=True):
        import ccxt
        self.exchange = getattr(ccxt, exchange_id)({
            'enableRateLimit': True,
        })
        if use_testnet:
            self.exchange.set_sandbox_mode(True)

    def fetch_ohlcv(self, symbol, timeframe='15m', limit=100):
        """
        Fetches historical OHLCV data for a crypto asset.
        """
        bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

class StockDataFetcher:
    def __init__(self, api_key=None, secret_key=None, paper=True):
        from alpaca.data.historical import StockHistoricalDataClient
        self.client = StockHistoricalDataClient(api_key, secret_key)
        self.paper = paper

    def fetch_ohlcv(self, symbol, timeframe='15m', limit=100):
        """
        Fetches historical bars for a stock asset using Alpaca.
        """
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        # Map string timeframe to Alpaca TimeFrame
        if timeframe == '1m':
            alpaca_tf = TimeFrame.Minute
        elif timeframe == '5m':
            alpaca_tf = TimeFrame(5, TimeFrame.Minute.unit)
        elif timeframe == '15m':
            alpaca_tf = TimeFrame(15, TimeFrame.Minute.unit)
        elif timeframe == '1h':
            alpaca_tf = TimeFrame.Hour
        elif timeframe == '1d':
            alpaca_tf = TimeFrame.Day
        else:
            alpaca_tf = TimeFrame(15, TimeFrame.Minute.unit)
        
        # Calculate start time based on limit and timeframe
        # This is a simplification; for a precise 'limit' bars, we'd need more complex logic
        end = datetime.now()
        start = end - timedelta(days=7) # Default to last 7 days for small limits
        
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=alpaca_tf,
            start=start
        )
        bars = self.client.get_stock_bars(request_params)
        df = bars.df
        return df

class ForexDataFetcher:
    def __init__(self, access_token=None, account_id=None, environment='practice'):
        from oandapyV20 import API
        self.client = API(access_token=access_token, environment=environment)
        self.account_id = account_id

    def fetch_ohlcv(self, instrument, timeframe='M15', count=100):
        """
        Fetches historical candles for a forex instrument using OANDA.
        """
        import oandapyV20.endpoints.instruments as instruments
        params = {
            "count": count,
            "granularity": timeframe
        }
        r = instruments.InstrumentsCandles(instrument=instrument, params=params)
        self.client.request(r)
        
        candles = r.response.get('candles', [])
        data = []
        for c in candles:
            if c['complete']:
                data.append({
                    'timestamp': c['time'],
                    'open': float(c['mid']['o']),
                    'high': float(c['mid']['h']),
                    'low': float(c['mid']['l']),
                    'close': float(c['mid']['c']),
                    'volume': int(c['volume'])
                })
        return pd.DataFrame(data)

class MacroDataFetcher:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

    def fetch_series(self, series_id):
        """
        Fetches the latest value of an economic series from FRED.
        """
        history = self.fetch_series_history(series_id, limit=1)
        return history[-1] if history else None

    def fetch_series_history(self, series_id, limit=13):
        """
        Fetches the most recent ``limit`` observations of a FRED series as a
        chronological (oldest -> newest) list of floats.

        A history (rather than a single point) is needed to derive
        year-over-year inflation and rate trends. Non-numeric observations
        (FRED uses '.' for missing values) are skipped.
        """
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'sort_order': 'desc',   # newest first, so we can cap with limit
            'limit': limit
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()
        observations = data.get('observations', []) if isinstance(data, dict) else []
        values = []
        for obs in observations:
            try:
                values.append(float(obs['value']))
            except (KeyError, TypeError, ValueError):
                continue  # skip missing/non-numeric points
        values.reverse()  # oldest -> newest
        return values

class DataPipeline:
    def __init__(self, config):
        self.config = config
        self.crypto = None
        self.stock = None
        self.forex = None
        self.macro = None
        
        # Initialize fetchers based on config
        self._init_fetchers()

    def _init_fetchers(self):
        exchanges = self.config.get('exchanges', {})
        
        # Crypto
        binance_cfg = exchanges.get('binance', {})
        if binance_cfg.get('api_key') and binance_cfg.get('api_secret'):
            self.crypto = CryptoDataFetcher(
                exchange_id='binance',
                use_testnet=binance_cfg.get('testnet', True)
            )
            # CCXT usually handles keys via the exchange object, but the stub was simple.
            # I'll update the CryptoDataFetcher to accept keys if needed, 
            # but let's assume it picks them up from env as per common practice or passed here.
            self.crypto.exchange.apiKey = binance_cfg.get('api_key')
            self.crypto.exchange.secret = binance_cfg.get('api_secret')

        # Stocks
        alpaca_cfg = exchanges.get('alpaca', {})
        if alpaca_cfg.get('api_key') and alpaca_cfg.get('api_secret'):
            self.stock = StockDataFetcher(
                api_key=alpaca_cfg.get('api_key'),
                secret_key=alpaca_cfg.get('api_secret'),
                paper=alpaca_cfg.get('paper', True)
            )

        # Forex
        oanda_cfg = exchanges.get('oanda', {})
        if oanda_cfg.get('api_key'):
            self.forex = ForexDataFetcher(
                access_token=oanda_cfg.get('api_key'),
                account_id=oanda_cfg.get('account_id'),
                environment='practice' if oanda_cfg.get('testnet', True) else 'live'
            )

        # Macro
        macro_cfg = self.config.get('macro', {})
        if macro_cfg.get('fred_api_key'):
            self.macro = MacroDataFetcher(api_key=macro_cfg.get('fred_api_key'))

    def fetch_all(self, symbols_dict):
        """
        fetches data for all requested symbols.
        symbols_dict: {'crypto': [...], 'stocks': [...], 'forex': [...], 'macro': [...]}
        """
        results = {
            'crypto': {},
            'stocks': {},
            'forex': {},
            'macro': {}
        }

        if self.crypto and 'crypto' in symbols_dict:
            for symbol in symbols_dict['crypto']:
                try:
                    results['crypto'][symbol] = self.crypto.fetch_ohlcv(symbol)
                except Exception as e:
                    print(f"Error fetching crypto {symbol}: {e}")

        if self.stock and 'stocks' in symbols_dict:
            for symbol in symbols_dict['stocks']:
                try:
                    results['stocks'][symbol] = self.stock.fetch_ohlcv(symbol)
                except Exception as e:
                    print(f"Error fetching stock {symbol}: {e}")

        if self.forex and 'forex' in symbols_dict:
            for symbol in symbols_dict['forex']:
                try:
                    results['forex'][symbol] = self.forex.fetch_ohlcv(symbol)
                except Exception as e:
                    print(f"Error fetching forex {symbol}: {e}")

        if self.macro and 'macro' in symbols_dict:
            for series_id in symbols_dict['macro']:
                try:
                    results['macro'][series_id] = self.macro.fetch_series(series_id)
                except Exception as e:
                    print(f"Error fetching macro {series_id}: {e}")

        return results

    def fetch_macro_history(self, series_ids, limit=13):
        """Fetch recent history for macro series as {series_id: [floats]}.

        Used to derive regime features (YoY inflation, rate trends). Returns an
        empty dict when no macro fetcher is configured (e.g. running on mock
        data) so callers can fall back to neutral defaults.
        """
        history = {}
        if not self.macro:
            return history
        for series_id in series_ids:
            try:
                history[series_id] = self.macro.fetch_series_history(series_id, limit=limit)
            except Exception as e:
                print(f"Error fetching macro history {series_id}: {e}")
        return history
