import sys
import os
import pandas as pd
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from signals.momentum_strategy import MomentumStrategy
from signals.base_strategy import SignalType, Conviction
from utils.mock_data import generate_mock_ohlcv

def test_strategy_signal_generation():
    print("Testing MomentumStrategy signal generation...")
    strategy = MomentumStrategy("Test Scalp", "15m")
    
    # Test with mock data
    symbols = ['BTC/USDT', 'ETH/USDT']
    
    for symbol in symbols:
        df = generate_mock_ohlcv(symbol, length=300)
        signal = strategy.generate_signal(df)
        
        if signal:
            print(f"Signal generated for {symbol}: {signal.type} ({signal.conviction})")
            print(f"Metadata: {signal.metadata}")
            
            # Verify Signal properties
            assert signal.symbol == symbol
            assert isinstance(signal.type, SignalType)
            assert isinstance(signal.conviction, Conviction)
            assert 'vwap' in signal.metadata
            assert 'ema9' in signal.metadata
        else:
            print(f"No signal generated for {symbol} (this is normal for random-walk data)")

def test_indicators_calculation():
    print("\nTesting indicators calculation...")
    strategy = MomentumStrategy("Test Indicators", "15m")
    df = generate_mock_ohlcv("BTC/USDT", length=300)
    
    df_with_indicators = strategy.calculate_indicators(df.copy())
    
    required_cols = ['ema9', 'ema21', 'ema50', 'ema200', 'vwap', 'vol_sma']
    for col in required_cols:
        assert col in df_with_indicators.columns
        assert not df_with_indicators[col].isnull().all()
        print(f"Indicator {col} calculated successfully.")

if __name__ == "__main__":
    try:
        test_strategy_signal_generation()
        test_indicators_calculation()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        sys.exit(1)
