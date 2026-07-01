import pandas as pd
import numpy as np
from backtest.engine import BacktestEngine
from signals.momentum_strategy import MomentumStrategy
from signals.macro_regime import MacroRegimeStrategy
from utils.mock_data import generate_mock_ohlcv
from utils.logger import setup_logger

def run_ensemble_backtest():
    logger = setup_logger('Backtest', '/home/team/shared/trading_bot/logs/backtest.log')
    logger.info("Starting Ensemble Backtest...")

    # 1. Generate Mock Data for multiple assets
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'AAPL', 'TSLA']
    all_dfs = []
    for sym in symbols:
        df = generate_mock_ohlcv(sym, length=500)
        df.set_index('timestamp', inplace=True)
        df.columns = pd.MultiIndex.from_product([[sym], df.columns])
        all_dfs.append(df)
    
    # Combine into one multi-asset dataframe
    data_df = pd.concat(all_dfs, axis=1).ffill().dropna()

    # 2. Mock Macro Data (alternating regimes)
    macro_data = []
    for i in range(len(data_df)):
        if i < 100:
            regime = {'yc_spread': 1.2, 'inflation_yoy': 2.1, 'fed_rate_trend': "Stable"} # Goldilocks
        elif i < 200:
            regime = {'yc_spread': -0.1, 'inflation_yoy': 3.5, 'fed_rate_trend': "Rising"} # Deflationary Bust
        else:
            regime = {'yc_spread': 0.4, 'inflation_yoy': 4.5, 'fed_rate_trend': "Rising"} # Overheating
        macro_data.append(regime)

    # 3. Setup strategies
    strategies = [
        MomentumStrategy("Momentum", "15m"),
        MacroRegimeStrategy("Macro", "1d")
    ]

    # 4. Initialize and Run Engine
    engine = BacktestEngine(strategies, initial_capital=100000)
    logger.info(f"Running backtest over {len(data_df)} bars...")
    
    results = engine.run(data_df, macro_data=macro_data)

    # 5. Output results
    print("\n" + "="*30)
    print("BACKTEST RESULTS")
    print("="*30)
    for k, v in results.items():
        if isinstance(v, float):
            print(f"{k:15}: {v:.4f}")
        else:
            print(f"{k:15}: {v}")
    print("="*30)

    if results.get('total_trades', 0) > 0:
        logger.info(f"Backtest complete. Total Profit/Loss: {results['total_return']*100:.2f}%")
    else:
        logger.warning("No trades were executed during the backtest.")

if __name__ == "__main__":
    run_ensemble_backtest()
