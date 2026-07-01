import time
import os
from config.config_loader import load_config
from utils.logger import setup_logger
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
from data.fetchers import DataPipeline
from data.processors import latest_atr

def main():
    # 1. Setup
    log_file = os.environ.get(
        'MINUTETRADER_LOG_FILE',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'bot.log')
    )
    logger = setup_logger('MinuteTrader', log_file)
    logger.info("Starting MinuteTrader Bot with full Strategy Ensemble...")
    
    config = load_config()
    trading_cfg = config.get('trading', {})
    risk_manager = RiskManager(risk_reward_ratio=trading_cfg.get('default_risk_reward', 3.0))
    risk_per_trade = trading_cfg.get('risk_per_trade', 0.01)
    atr_period = trading_cfg.get('atr_period', 14)
    atr_stop_mult = trading_cfg.get('atr_stop_mult', 2.0)
    paper_trader = PaperTrader(initial_balance=10000)
    
    # Initialize Data Pipeline
    pipeline = DataPipeline(config)
    
    # Initialize Combiner
    combiner = SignalCombiner()
    
    # Initialize strategies
    strategies = [
        MomentumStrategy("EMA+VWAP Scalp", "15m"),
        RelativeStrengthStrategy("RS Flow", "15m"),
        CrossAssetStrategy("Cross-Asset Leader", "15m"),
        OnChainSentimentStrategy("On-Chain Sentiment", "1h"),
        MacroRegimeStrategy("Macro Filter", "1d")
    ]
    
    logger.info(f"Initialized {len(strategies)} strategies")
    
    # Symbols to track
    symbols_to_fetch = {
        'crypto': ['BTC/USDT', 'ETH/USDT', 'SOL/USDT'],
        'stocks': ['AAPL', 'TSLA', 'QQQ'],
        'forex': ['EUR/USD', 'GBP/USD'],
        'macro': ['T10Y2Y', 'CPIAUCSL', 'FEDFUNDS', 'UNRATE']
    }
    
    KILLSWITCH_PATH = 'killswitch.lock'
    killswitch_engaged = False

    try:
        while True: # Run continuously
            # 0. Kill Switch Check
            if os.path.exists(KILLSWITCH_PATH):
                if not killswitch_engaged:
                    logger.warning("Kill Switch activated! Flattening all open positions and halting trading.")
                    if paper_trader.positions:
                        # Mark-to-market close of every open position so nothing
                        # is left unmanaged while trading is halted.
                        flatten_prices = {
                            s: generate_mock_ohlcv(s, length=1)['close'].iloc[0]
                            for s in list(paper_trader.positions.keys())
                        }
                        closed = paper_trader.close_all_positions(flatten_prices)
                        logger.warning(f"Kill Switch: closed {closed} open position(s). Balance: {paper_trader.balance:.2f}")
                    killswitch_engaged = True
                time.sleep(10)
                continue
            else:
                # Kill switch cleared: resume normal trading.
                killswitch_engaged = False

            logger.info("--- New Market Cycle ---")
            
            # 2. Data Fetching
            data_results = pipeline.fetch_all(symbols_to_fetch)
            
            # Extract Macro Data for global filtering
            macro_context = data_results.get('macro', {})
            # Simplified: just using current values
            
            # 3. Global Macro Filter
            macro_signal = None
            pos_size_modifier = 1.0
            for strategy in strategies:
                if isinstance(strategy, MacroRegimeStrategy):
                    # Map FRED series to logic parameters
                    params = {
                        'yc_spread': macro_context.get('T10Y2Y', 1.0),
                        'inflation_yoy': macro_context.get('CPIAUCSL', 2.0),
                        'fed_rate_trend': "Stable" # For now, can be calculated from history
                    }
                    macro_signal = strategy.generate_signal(None, **params)
                    if macro_signal:
                        pos_size_modifier = macro_signal.metadata.get('position_size_modifier', 1.0)
                        logger.info(f"Macro Regime: {macro_signal.metadata['regime']} (Bias: {macro_signal.metadata['global_bias']}, Modifier: {pos_size_modifier})")
            
            # 4. Process each Asset Class
            all_symbols = symbols_to_fetch['crypto'] + symbols_to_fetch['stocks'] + symbols_to_fetch['forex']
            
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
                
                # 5. Signal Generation
                signals = []
                for strategy in strategies:
                    if isinstance(strategy, MacroRegimeStrategy): continue
                    
                    # Some strategies might need extra context
                    kwargs = {}
                    if isinstance(strategy, CrossAssetStrategy):
                        kwargs['leaders'] = {
                            'BTC': data_results['crypto'].get('BTC/USDT'),
                            'DXY': data_results['forex'].get('UUP'), # Proxy
                            'US10Y': data_results['macro'].get('T10Y2Y')
                        }
                    elif isinstance(strategy, RelativeStrengthStrategy):
                        # Use appropriate benchmark
                        if symbol in symbols_to_fetch['crypto']:
                            kwargs['benchmark_data'] = data_results['crypto'].get('BTC/USDT')
                        elif symbol in symbols_to_fetch['stocks']:
                            kwargs['benchmark_data'] = data_results['stocks'].get('SPY')
                    
                    sig = strategy.generate_signal(df, **kwargs)
                    if sig:
                        sig.metadata['strategy_name'] = strategy.name
                        signals.append(sig)
                
                # 6. Signal Combination
                combined_signal = combiner.combine(signals, symbol)
                
                if combined_signal and combined_signal.type != SignalType.NEUTRAL:
                    # Apply Macro Position Size Modifier
                    if pos_size_modifier <= 0:
                        logger.info(f"Skipping {symbol} {combined_signal.type} due to Bearish Macro Bias")
                        continue

                    logger.info(f"Consensus Signal for {symbol}: {combined_signal.type} ({combined_signal.conviction.name})")
                    
                    current_price = df['close'].iloc[-1]

                    # 7. Risk Management (volatility-scaled stops via ATR)
                    atr = latest_atr(df, period=atr_period)
                    levels = risk_manager.calculate_trade_levels(
                        combined_signal.type.value,
                        current_price,
                        atr=atr,
                        atr_stop_mult=atr_stop_mult
                    )
                    
                    if levels:
                        # 8. Execution
                        entry_price = (levels['entry_zone'][0] + levels['entry_zone'][1]) / 2
                        
                        # Risk-based position sizing, scaled by the macro modifier
                        base_amount = risk_manager.calculate_position_size(
                            paper_trader.balance,
                            entry_price,
                            levels['stop_loss'],
                            risk_per_trade=risk_per_trade
                        )
                        final_amount = base_amount * pos_size_modifier

                        if final_amount <= 0:
                            logger.info(f"Skipping {symbol}: computed position size is zero")
                            continue

                        logger.info(f"Executing paper trade: {symbol} at {entry_price:.2f} (Amount: {final_amount:.6f})")

                        paper_trader.place_order(
                            symbol, 
                            combined_signal.type.value, 
                            final_amount, 
                            entry_price,
                            stop_loss=levels['stop_loss'],
                            take_profit=levels['tp_levels'][0]
                        )
            
            # 9. Update positions
            current_market_prices = {}
            for s in all_symbols:
                # Mock current price for update (or use real if available)
                latest = generate_mock_ohlcv(s, length=1)
                current_market_prices[s] = latest['close'].iloc[0]
                
            paper_trader.update_positions(current_market_prices)
            
            logger.info(f"Current Balance: {paper_trader.balance:.2f}")
            time.sleep(60) # Wait 60s for next cycle
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
