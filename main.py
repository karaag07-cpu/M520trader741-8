import time
from config.config_loader import load_config
from utils.logger import setup_logger
from utils.mock_data import generate_mock_ohlcv
from signals.momentum_strategy import MomentumStrategy
from signals.combiner import SignalCombiner
from signals.base_strategy import SignalType
from risk.risk_manager import RiskManager
from execution.paper_trader import PaperTrader
from data.fetchers import DataPipeline

def main():
    # 1. Setup
    logger = setup_logger('MinuteTrader', '/home/team/shared/trading_bot/logs/bot.log')
    logger.info("Starting MinuteTrader Bot...")
    
    config = load_config()
    risk_manager = RiskManager(risk_reward_ratio=config.get('trading', {}).get('default_risk_reward', 3.0))
    paper_trader = PaperTrader(initial_balance=10000)
    
    # Initialize Data Pipeline
    pipeline = DataPipeline(config)
    
    # Initialize Combiner
    combiner = SignalCombiner()
    
    # Initialize strategies
    strategies = [
        MomentumStrategy("EMA+VWAP Scalp", "15m")
    ]
    
    logger.info("Bot initialized and entering main loop")
    
    # Symbols to track (from config or hardcoded for test)
    symbols_to_fetch = {
        'crypto': ['BTC/USDT', 'ETH/USDT'],
        'macro': ['T10Y2Y']
    }
    
    try:
        for i in range(10):  # Run 10 iterations for demo
            logger.info(f"--- Iteration {i+1} ---")
            
            # 2. Data Fetching
            data_results = pipeline.fetch_all(symbols_to_fetch)
            
            # Fallback to mock data if real data is missing (e.g. no API keys)
            all_symbols = symbols_to_fetch.get('crypto', []) + symbols_to_fetch.get('stocks', []) + symbols_to_fetch.get('forex', [])
            
            for symbol in all_symbols:
                # Find data in results
                df = None
                if symbol in data_results['crypto']:
                    df = data_results['crypto'][symbol]
                elif symbol in data_results['stocks']:
                    df = data_results['stocks'][symbol]
                elif symbol in data_results['forex']:
                    df = data_results['forex'][symbol]
                
                # GRACEFUL FALLBACK
                if df is None or df.empty:
                    # logger.warning(f"No real data for {symbol}, falling back to mock.")
                    df = generate_mock_ohlcv(symbol, length=300)
                
                # Ensure symbol attribute is set for strategies that need it
                df.attrs['symbol'] = symbol
                
                # 3. Signal Generation
                signals = []
                for strategy in strategies:
                    sig = strategy.generate_signal(df)
                    if sig:
                        sig.metadata['strategy_name'] = strategy.name
                        signals.append(sig)
                
                # 4. Signal Combination
                combined_signal = combiner.combine(signals, symbol)
                
                if combined_signal and combined_signal.type != SignalType.NEUTRAL:
                    logger.info(f"Consensus Signal for {symbol}: {combined_signal.type} ({combined_signal.conviction.name})")
                    logger.info(f"Details: {combined_signal.metadata['contributions']}")
                    
                    current_price = df['close'].iloc[-1]
                    
                    # 5. Risk Management
                    levels = risk_manager.calculate_trade_levels(
                        combined_signal.type.value, 
                        current_price
                    )
                    
                    if levels:
                        combined_signal.entry_zone = levels['entry_zone']
                        combined_signal.tp_levels = levels['tp_levels']
                        combined_signal.stop_loss = levels['stop_loss']
                        
                        # 6. Execution
                        entry_price = (combined_signal.entry_zone[0] + combined_signal.entry_zone[1]) / 2
                        logger.info(f"Executing paper trade: {symbol} at {entry_price:.2f}")
                        
                        paper_trader.place_order(
                            symbol, 
                            combined_signal.type.value, 
                            0.1, 
                            entry_price,
                            stop_loss=combined_signal.stop_loss,
                            take_profit=combined_signal.tp_levels[0]
                        )
            
            # Update positions with current prices
            current_market_prices = {}
            for s in all_symbols:
                # Again, try real data first for price update
                # (Simplified: just using the last close from 'df' above or fresh mock)
                latest = generate_mock_ohlcv(s, length=1)
                current_market_prices[s] = latest['close'].iloc[0]
                
            paper_trader.update_positions(current_market_prices)
            
            logger.info(f"Current Balance: {paper_trader.balance:.2f}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    main()
