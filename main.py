import argparse
import time
import os
from datetime import datetime, time as dtime
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None
from config.config_loader import load_config
from utils.logger import setup_logger, default_log_path
from utils.mock_data import generate_mock_ohlcv
from signals.momentum_strategy import MomentumStrategy
from signals.relative_strength import RelativeStrengthStrategy
from signals.cross_asset import CrossAssetStrategy
from signals.onchain_sentiment import OnChainSentimentStrategy
from signals.macro_regime import MacroRegimeStrategy
from signals.combiner import SignalCombiner
from signals.base_strategy import SignalType
from risk.risk_manager import RiskManager
from execution.paper_trader import PaperTrader
from execution.status_reporter import build_status, build_alpaca_status, write_status
from execution.reconciliation import reconcile_paper_trader
from execution.alpaca_broker import AlpacaBroker
from execution.crypto_exits import CryptoExitTracker
from execution.instance_lock import acquire as acquire_lock, release as release_lock
from data.fetchers import DataPipeline
from data.processors import calculate_atr
from data.macro_features import derive_macro_params

KILLSWITCH_PATH = 'killswitch.lock'

# US equity market session (Eastern). Stocks are flattened just before the
# close so nothing carries overnight unprotected; crypto trades 24/7.
MARKET_OPEN = dtime(9, 30)
MARKET_CLOSE = dtime(16, 0)
FLATTEN_START = dtime(15, 55)


def now_eastern():
    """Current time in US/Eastern, or None if zoneinfo/tzdata is unavailable."""
    if ZoneInfo is None:
        return None
    try:
        return datetime.now(ZoneInfo('America/New_York'))
    except Exception:
        return None


def equity_market_open(now_et):
    """True during regular US equity trading hours (Mon-Fri, 9:30-16:00 ET)."""
    return (now_et is not None and now_et.weekday() < 5
            and MARKET_OPEN <= now_et.time() < MARKET_CLOSE)


def in_flatten_window(now_et):
    """True in the last few minutes before the equity close (15:55-16:00 ET)."""
    return (now_et is not None and now_et.weekday() < 5
            and FLATTEN_START <= now_et.time() < MARKET_CLOSE)


def _is_crypto(symbol):
    return '/' in symbol


def _norm_symbol(symbol):
    """Normalise a symbol for matching (Alpaca reports 'BTCUSD', bot uses 'BTC/USD')."""
    return str(symbol).replace('/', '').upper()


def _env_bool(name, default=True):
    """Read a truthy/falsey environment variable; unset -> default."""
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ('1', 'true', 'yes', 'on')

DEFAULT_SYMBOLS = {
    'crypto': ['BTC/USD', 'ETH/USD', 'SOL/USD'],  # Alpaca crypto symbol format
    'stocks': ['AAPL', 'TSLA', 'QQQ'],
    'forex': [],  # Alpaca does not offer forex; leave empty (or wire OANDA to enable)
    'macro': ['T10Y2Y', 'CPIAUCSL', 'FEDFUNDS', 'UNRATE'],
}


class TradingBot:
    """Owns the trading context and executes market cycles.

    Splitting the per-cycle work into ``run_cycle()`` makes the bot schedulable
    (run one cycle from cron via ``--once``) and unit-testable (drive a cycle
    with mock data), while ``run()`` keeps the long-running loop for local use.
    """

    def __init__(self, config=None, logger=None, symbols=None):
        self.config = config if config is not None else load_config()
        self.logger = logger or setup_logger('MinuteTrader', default_log_path('bot.log'))
        # Copy so env toggles don't mutate the module default.
        self.symbols = symbols or {k: list(v) for k, v in DEFAULT_SYMBOLS.items()}
        # Enable/disable asset classes from .env (gitignored) without editing
        # code: MINUTETRADER_TRADE_CRYPTO / MINUTETRADER_TRADE_STOCKS = false.
        if not _env_bool('MINUTETRADER_TRADE_CRYPTO', True):
            self.symbols['crypto'] = []
        if not _env_bool('MINUTETRADER_TRADE_STOCKS', True):
            self.symbols['stocks'] = []

        trading_cfg = self.config.get('trading', {})
        self.risk_manager = RiskManager(risk_reward_ratio=trading_cfg.get('default_risk_reward', 3.0))
        self.paper_trader = PaperTrader(initial_balance=trading_cfg.get('initial_balance', 10000))
        # Resume prior balance/positions across restarts, if a state file exists.
        if self.paper_trader.load_state():
            self.logger.info(f"Resumed paper state: balance {self.paper_trader.balance:.2f}, "
                             f"{len(self.paper_trader.positions)} open position(s)")
        # Optional: mirror orders to a real Alpaca account (paper by default) so
        # positions appear on the Alpaca dashboard. Opt in with trading.broker:
        # alpaca. Stays None (local simulation only) unless configured + keyed.
        self.broker = self._init_broker(trading_cfg)
        # Software stop/target tracker for crypto (Alpaca can't bracket crypto).
        self.crypto_exits = CryptoExitTracker() if self.broker else None
        # Flatten stock positions just before the close so nothing sits
        # overnight unprotected (crypto is managed continuously and unaffected).
        self.flatten_at_close = trading_cfg.get('flatten_at_close', True)
        self._crypto_symbols = {s.replace('/', '').upper() for s in self.symbols.get('crypto', [])}

        self.pipeline = DataPipeline(self.config)
        self.combiner = SignalCombiner()
        self.strategies = [
            MomentumStrategy("EMA+VWAP Scalp", "15m"),
            RelativeStrengthStrategy("RS Flow", "15m"),
            CrossAssetStrategy("Cross-Asset Leader", "15m"),
            OnChainSentimentStrategy("On-Chain Sentiment", "1h"),
            MacroRegimeStrategy("Macro Filter", "1d"),
        ]
        self.logger.info(f"Initialized {len(self.strategies)} strategies")
        if self.broker:
            self.logger.info("Alpaca broker enabled: orders will be mirrored to your Alpaca account")

    def _init_broker(self, trading_cfg):
        # MINUTETRADER_BROKER in .env overrides settings.yaml, so your live/paper
        # choice can live in the gitignored .env instead of a tracked file.
        broker_mode = os.environ.get('MINUTETRADER_BROKER') or trading_cfg.get('broker', 'paper')
        if broker_mode != 'alpaca':
            return None
        alpaca_cfg = self.config.get('exchanges', {}).get('alpaca', {})
        if not (alpaca_cfg.get('api_key') and alpaca_cfg.get('api_secret')):
            self.logger.warning("trading.broker=alpaca but no Alpaca keys configured; staying in local simulation")
            return None
        try:
            return AlpacaBroker(
                api_key=alpaca_cfg.get('api_key'),
                secret_key=alpaca_cfg.get('api_secret'),
                paper=alpaca_cfg.get('paper', True),
            )
        except Exception as e:
            self.logger.error(f"Failed to init Alpaca broker (staying in simulation): {e}")
            return None

    def run_cycle(self):
        """Run one full market cycle; returns the published status snapshot."""
        logger = self.logger
        config = self.config
        symbols_to_fetch = self.symbols
        logger.info("--- New Market Cycle ---")

        # 2. Data Fetching
        data_results = self.pipeline.fetch_all(symbols_to_fetch)

        # Derive macro-regime features from recent FRED history (YoY inflation,
        # rate/unemployment trends) rather than raw index levels.
        macro_history = self.pipeline.fetch_macro_history(symbols_to_fetch.get('macro', []))
        macro_params = derive_macro_params(macro_history)

        # 3. Global Macro Filter
        macro_signal = None
        pos_size_modifier = 1.0
        for strategy in self.strategies:
            if isinstance(strategy, MacroRegimeStrategy):
                macro_signal = strategy.generate_signal(None, **macro_params)
                if macro_signal:
                    pos_size_modifier = macro_signal.metadata.get('position_size_modifier', 1.0)
                    logger.info(f"Macro Regime: {macro_signal.metadata['regime']} (Bias: {macro_signal.metadata['global_bias']}, Modifier: {pos_size_modifier})")

        # When mirroring to Alpaca, size off the real account and skip symbols
        # already held there. Fetch the account/positions once per cycle.
        now_et = now_eastern()
        flattening = self.flatten_at_close and in_flatten_window(now_et)
        alpaca_account = None
        alpaca_held = set()
        if self.broker:
            try:
                alpaca_account = self.broker.get_account()
                alpaca_positions = self.broker.get_positions()
                # Normalised so 'BTC/USD' (bot) matches 'BTCUSD' (Alpaca).
                alpaca_held = {_norm_symbol(p['symbol']) for p in alpaca_positions}

                # End-of-day flatten: near the close, close stock positions so
                # nothing carries overnight unprotected. Crypto is skipped (it
                # trades 24/7 and is managed by its own software stops).
                if flattening:
                    for p in alpaca_positions:
                        if _norm_symbol(p['symbol']) in self._crypto_symbols:
                            continue
                        try:
                            self.broker.close_position(p['symbol'])
                            alpaca_held.discard(_norm_symbol(p['symbol']))
                            logger.info(f"Flattened {p['symbol']} at market close")
                        except Exception as e:
                            logger.error(f"Failed to flatten {p['symbol']}: {e}")

                # Software stop/target for crypto: close any position whose
                # tracked level has been touched (Alpaca can't bracket crypto).
                for sym, reason in self.crypto_exits.positions_to_close(alpaca_positions):
                    try:
                        self.broker.close_position(sym)
                        self.crypto_exits.discard(sym)
                        alpaca_held.discard(_norm_symbol(sym))
                        logger.info(f"Closed {sym} on Alpaca ({reason})")
                    except Exception as e:
                        logger.error(f"Failed to close {sym}: {e}")
            except Exception as e:
                logger.error(f"Could not read Alpaca account: {e}")
        account_balance = alpaca_account['equity'] if alpaca_account else self.paper_trader.balance

        # 4. Process each Asset Class
        all_symbols = symbols_to_fetch['crypto'] + symbols_to_fetch['stocks'] + symbols_to_fetch['forex']

        # Track the latest observed price per symbol so open positions are
        # marked-to-market against real data this cycle, not a fresh random draw.
        current_market_prices = {}

        for symbol in all_symbols:
            # Find data in results
            df = None
            if symbol in data_results['crypto']: df = data_results['crypto'][symbol]
            elif symbol in data_results['stocks']: df = data_results['stocks'][symbol]
            elif symbol in data_results['forex']: df = data_results['forex'][symbol]

            # GRACEFUL FALLBACK
            if df is None or df.empty:
                df = generate_mock_ohlcv(symbol, length=300)

            df.attrs['symbol'] = symbol
            current_market_prices[symbol] = df['close'].iloc[-1]

            # 5. Signal Generation
            signals = []
            for strategy in self.strategies:
                if isinstance(strategy, MacroRegimeStrategy): continue

                # Some strategies might need extra context
                kwargs = {}
                if isinstance(strategy, CrossAssetStrategy):
                    kwargs['leaders'] = {
                        'BTC': data_results['crypto'].get('BTC/USD'),
                        'DXY': data_results['forex'].get('UUP'), # Proxy
                        'US10Y': data_results['macro'].get('T10Y2Y')
                    }
                elif isinstance(strategy, RelativeStrengthStrategy):
                    # Use appropriate benchmark
                    if symbol in symbols_to_fetch['crypto']:
                        kwargs['benchmark_data'] = data_results['crypto'].get('BTC/USD')
                    elif symbol in symbols_to_fetch['stocks']:
                        kwargs['benchmark_data'] = data_results['stocks'].get('SPY')

                sig = strategy.generate_signal(df, **kwargs)
                if sig:
                    sig.metadata['strategy_name'] = strategy.name
                    signals.append(sig)

            # 6. Signal Combination
            combined_signal = self.combiner.combine(signals, symbol)

            if combined_signal and combined_signal.type != SignalType.NEUTRAL:
                # Apply Macro Position Size Modifier
                if pos_size_modifier <= 0:
                    logger.info(f"Skipping {symbol} {combined_signal.type} due to Bearish Macro Bias")
                    continue

                logger.info(f"Consensus Signal for {symbol}: {combined_signal.type} ({combined_signal.conviction.name})")

                # Don't open new stock positions when the equity market is
                # closed or in the end-of-day flatten window (they'd be rejected
                # or flattened immediately). Crypto trades 24/7 and is exempt.
                if self.broker and not _is_crypto(symbol) and (not equity_market_open(now_et) or flattening):
                    logger.info(f"Skipping {symbol}: outside equity trading hours")
                    continue

                current_price = df['close'].iloc[-1]

                # 7. Risk Management — volatility-aware stops via ATR.
                atr_value = calculate_atr(df)
                levels = self.risk_manager.calculate_trade_levels(
                    combined_signal.type.value,
                    current_price,
                    atr=atr_value
                )

                if levels:
                    # 8. Position sizing — fixed-fractional risk, scaled by
                    # the macro regime's position-size modifier.
                    entry_price = (levels['entry_zone'][0] + levels['entry_zone'][1]) / 2

                    risk_per_trade = config.get('trading', {}).get('risk_per_trade', 0.01)
                    max_position_fraction = config.get('trading', {}).get('max_position_fraction', 0.25)

                    sizing = self.risk_manager.validate_risk(
                        account_balance=account_balance,
                        entry_price=entry_price,
                        stop_loss=levels['stop_loss'],
                        risk_per_trade=risk_per_trade,
                        max_position_fraction=max_position_fraction,
                        size_modifier=pos_size_modifier
                    )

                    if not sizing:
                        logger.info(f"Skipping {symbol}: no valid position size for current risk inputs")
                        continue

                    final_amount = sizing['quantity']

                    # 9. Execution
                    if self.broker:
                        # Mirror to Alpaca; skip symbols already held there so
                        # positions don't pile up. Equities get a bracket order
                        # (Alpaca manages the stop/target); crypto is a plain
                        # market order (see README on exit handling).
                        if _norm_symbol(symbol) in alpaca_held:
                            continue
                        logger.info(
                            f"Submitting {symbol} to Alpaca: {combined_signal.type.value} "
                            f"qty {final_amount:.6f} (~${sizing['notional']:.2f})"
                        )
                        try:
                            self.broker.submit_order(
                                symbol, combined_signal.type.value, final_amount,
                                take_profit=levels['tp_levels'][0],
                                stop_loss=levels['stop_loss'],
                            )
                            alpaca_held.add(_norm_symbol(symbol))
                            # Crypto has no Alpaca bracket — track its exit in software.
                            if '/' in symbol:
                                self.crypto_exits.record(
                                    symbol, combined_signal.type.value,
                                    levels['stop_loss'], levels['tp_levels'][0],
                                )
                        except Exception as e:
                            logger.error(f"Alpaca order failed for {symbol}: {e}")
                    else:
                        logger.info(
                            f"Executing paper trade: {symbol} at {entry_price:.2f} "
                            f"(Qty: {final_amount:.6f}, Notional: {sizing['notional']:.2f}, "
                            f"Risk: {sizing['risk_amount']:.2f})"
                        )
                        self.paper_trader.place_order(
                            symbol,
                            combined_signal.type.value,
                            final_amount,
                            entry_price,
                            stop_loss=levels['stop_loss'],
                            take_profit=levels['tp_levels'][0]
                        )

        regime_meta = macro_signal.metadata if macro_signal else {}
        status = None

        if self.broker:
            # Dashboard mirrors the live Alpaca account (balance + positions);
            # Alpaca manages equity exits via the bracket orders submitted above.
            try:
                account = alpaca_account or self.broker.get_account()
                positions = self.broker.get_positions()
                status = build_alpaca_status(account, positions, regime=regime_meta)
                write_status(status)
                logger.info(f"Alpaca equity: {account.get('equity', 0):.2f} "
                            f"({len(positions)} position(s))")
            except Exception as e:
                logger.error(f"Failed to publish Alpaca status: {e}")
        else:
            # Local simulator: manage exits, persist, publish, and reconcile
            # against a broker snapshot file if one is present.
            self.paper_trader.update_positions(current_market_prices)
            try:
                self.paper_trader.save_state()
            except Exception as e:
                logger.error(f"Failed to save paper state: {e}")
            try:
                status = build_status(self.paper_trader, current_market_prices, regime=regime_meta)
                reconciliation = reconcile_paper_trader(self.paper_trader)
                if reconciliation is not None:
                    status['reconciliation'] = reconciliation
                    if not reconciliation['in_sync']:
                        logger.warning("Positions out of sync with broker snapshot")
                write_status(status)
            except Exception as e:
                logger.error(f"Failed to write status snapshot: {e}")
            logger.info(f"Current Balance: {self.paper_trader.balance:.2f}")

        return status

    def killswitch_active(self):
        return os.path.exists(KILLSWITCH_PATH)

    def run(self, once=False, interval=60, max_cycles=None):
        """Run cycles until stopped.

        once: run a single cycle and return (cron-friendly).
        interval: seconds to sleep between cycles.
        max_cycles: stop after this many cycles (None = unlimited).
        """
        count = 0
        try:
            while True:
                # 0. Kill Switch Check
                if self.killswitch_active():
                    self.logger.warning("Kill Switch activated! Skipping cycle.")
                    if once:
                        break
                    time.sleep(min(interval, 10))
                    continue

                self.run_cycle()
                count += 1

                if once or (max_cycles is not None and count >= max_cycles):
                    break
                time.sleep(interval)
        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"An error occurred: {e}", exc_info=True)
        return count


def build_parser():
    p = argparse.ArgumentParser(prog="minutetrader", description="Run the MinuteTrader bot.")
    p.add_argument("--once", action="store_true",
                   help="Run a single cycle and exit (for cron / schedulers).")
    p.add_argument("--interval", type=int, default=60,
                   help="Seconds between cycles when looping (default: 60).")
    p.add_argument("--cycles", type=int, default=None,
                   help="Stop after this many cycles (default: run forever).")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    logger = setup_logger('MinuteTrader', default_log_path('bot.log'))

    # Refuse to start if another bot is already running (prevents duplicate
    # orders from multiple stray windows).
    ok, holder = acquire_lock()
    if not ok:
        logger.error(f"Another MinuteTrader instance is already running (PID {holder}). "
                     f"Exiting. Stop it first (taskkill /F /IM python.exe), or delete "
                     f"bot.lock if you're sure it's stale.")
        return 1

    logger.info("Starting MinuteTrader Bot with full Strategy Ensemble...")
    try:
        bot = TradingBot(logger=logger)
        bot.run(once=args.once, interval=args.interval, max_cycles=args.cycles)
    finally:
        release_lock()
    return 0


if __name__ == "__main__":
    main()
