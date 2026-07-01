# MinuteTrader

MinuteTrader is a multi-asset automated trading bot designed to exploit micro-inefficiencies across crypto, stocks, and forex markets. By combining multi-signal analysis with precise risk-managed entry/exit plans, the bot aims to generate small, consistent profits that compound rapidly with minimal human intervention.

## Status
The project is currently in the **Paper Trading / Backtesting** phase. No real capital is deployed.

## Core Features
- **Multi-Asset Support**: Integrated with Alpaca (Stocks), Binance/Bybit (Crypto), and OANDA (Forex).
- **High-Frequency Signals**: 5 distinct strategy modules providing timeframe-tagged signals (15m scalp to daily swing).
- **Unified Risk Manager**: Calculates Entry Zones, dynamic Take-Profit targets, and strict Stop-Loss levels (minimum 1:3 Risk-to-Reward).
- **Signal Combiner**: Aggregates signals from multiple strategies and scales conviction based on alignment.
- **Paper Trading Engine**: Real-time simulation of trade execution and P&L tracking.

## Strategy Summary
1. **Momentum + Volume Confirmation**: EMA crossovers (9/21) confirmed by volume spikes and VWAP trend.
2. **Relative Strength / Flow Detection**: Tracks assets outperforming their benchmark (SPY/BTC) during volume surges.
3. **Cross-Asset Leading Signals**: Monitors leading indicators like DXY and Bond Yields to predict moves in risk assets.
4. **On-Chain & Sentiment (Crypto)**: Uses MVRV ratios and exchange flows for contrarian positioning.
5. **Macro Regime Detection**: Rules-based filter of yield curve and inflation to set overall market bias.

## Symbol Coverage
The set of monitored symbols is configured under `trading.assets` in [config/settings.yaml](config/settings.yaml).

## Getting Started

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) or `pip`

### Installation
```bash
# Clone the repository
git clone https://github.com/MinuteTrader/bot.git
cd bot

# Create virtual environment and install dependencies
pip install -r requirements.txt
```

### Configuration
1. Copy the example config: `cp config/settings.yaml.example config/settings.yaml`
2. Update `config/settings.yaml` with your API keys (Alpaca, Binance, OANDA, FRED).
3. Set environment variables if not using the config file for secrets.

### Running the Bot
```bash
python main.py
```

## Contributing
Please follow the defined branch strategy and PR process outlined in [WORKFLOW.md](WORKFLOW.md).

## Architecture
For a deep dive into the bot's internal structure and data flow, see [ARCHITECTURE.md](ARCHITECTURE.md).
