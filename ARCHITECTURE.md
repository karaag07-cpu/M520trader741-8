# MinuteTrader Architecture

## Module Tree
```text
trading_bot/
├── main.py                # Bot entry point & main loop
├── config/                # YAML configuration & loader
├── data/
│   ├── fetchers.py        # REST/WebSocket clients (CCXT, Alpaca, OANDA, FRED)
│   └── processors.py      # Technical indicator calculations (Pandas)
├── signals/
│   ├── base_strategy.py   # Abstract strategy interface
│   ├── momentum.py        # Strategy 1
│   ├── relative_strength.py # Strategy 2
│   └── ...                # Other strategy modules
├── combiner/
│   └── signal_combiner.py # Aggregates signals and scales conviction
├── risk/
│   └── risk_manager.py    # Calculates TP/SL and position sizing
├── execution/
│   ├── paper_trader.py    # Simulated execution engine
│   └── live_executor.py   # REAL order execution (future)
└── utils/
    └── logger.py          # Structured logging
```

## Data Flow
1. **Data Fetchers**: Continuously pull price data (OHLCV) and macro indicators (Yields, DXY) via REST and WebSockets.
2. **Strategies**: Individual strategy modules process data and emit `Signal` objects containing a side (Buy/Sell), timeframe, and base conviction.
3. **Signal Combiner**: Receives signals from all active strategies. If multiple strategies align, it increases the total conviction score and passes the consolidated signal forward.
4. **Risk Manager**: For every consolidated signal, the Risk Manager calculates the optimal entry zone, identifies support/resistance for stop-loss, and sets tiered take-profit targets ensuring a 1:3 R:R ratio.
5. **Executor**: The Paper Trader (or Live Executor) receives the finalized signal and simulates/executes the order, updating the local position database and logging the trade.

## Key Classes
- `BaseDataFetcher`: Standardizes data retrieval across different brokers and APIs.
- `BaseStrategy`: Abstract class that every strategy must implement. Enforces consistent output format.
- `Signal`: Dataclass containing all metadata for a trade trigger.
- `RiskManager`: Central logic for capital preservation and trade planning.
- `PaperTrader`: Manages a local portfolio and simulates fills based on market liquidity.
