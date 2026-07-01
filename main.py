import argparse
import time
import os
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
from execution.status_reporter import build_status, write_status
from execution.reconciliation import reconcile_paper_trader
from data.fetchers import DataPipeline
from data.processors import calculate_atr
from data.macro_features import derive_macro_params

KILLSWITCH_PATH = 'killswitch.lock'

DEFAULT_SYMBOLS = {
    'crypto': ['BTC/USD', 'ETH/USD', 'SOL/USD'],  # Alpaca crypto symbol format
    'stocks': ['AAPL', 'TSLA', 'QQQ'],
    'forex': ['EUR/USD', 'GBP/USD'],
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
        self.symbols = symbols or DEFAULT_SYMBOLS

        trading_cfg = self.config.get('trading', {})
        self.risk_manager = RiskManager(risk_reward_ratio=trading_cfg.get('default_risk_reward', 3.0))
        self.paper_trader = PaperTrader(initial_balance=trading_cfg.get('initial_balance', 10000))
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
                        account_balance=self.paper_trader.balance,
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
                    logger.info(
                        f"Executing paper trade: {symbol} at {entry_price:.2f} "
                        f"(Qty: {final_amount:.6f}, Notional: {sizing['notional']:.2f}, "
                        f"Risk: {sizing['risk_amount']:.2f})"
                    )

                    # 9. Execution
                    self.paper_trader.place_order(
                        symbol,
                        combined_signal.type.value,
                        final_amount,
                        entry_price,
                        stop_loss=levels['stop_loss'],
                        take_profit=levels['tp_levels'][0]
                    )

        # 10. Update positions against the prices actually observed this cycle
        # (collected above from the fetched data / fallback series), so
        # stop-loss and take-profit trigger on real market moves.
        self.paper_trader.update_positions(current_market_prices)

        # 11. Publish a status snapshot for the website dashboard to read.
        status = None
        try:
            regime_meta = macro_signal.metadata if macro_signal else {}
            status = build_status(self.paper_trader, current_market_prices, regime=regime_meta)
            # Reconcile against a broker snapshot if one is present.
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
    logger.info("Starting MinuteTrader Bot with full Strategy Ensemble...")
    bot = TradingBot(logger=logger)
    bot.run(once=args.once, interval=args.interval, max_cycles=args.cycles)


if __name__ == "__main__":
    main()
