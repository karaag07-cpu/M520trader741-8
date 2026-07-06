# MinuteTrader

MinuteTrader is a multi-asset automated trading bot designed to exploit micro-inefficiencies across crypto, stocks, and forex markets. By combining multi-signal analysis with precise risk-managed entry/exit plans, the bot aims to generate small, consistent profits that compound rapidly with minimal human intervention.

## Status
The project is currently in the **Paper Trading / Backtesting** phase. No real capital is deployed.

## Core Features
- **Multi-Asset Support**: Primary data via **Alpaca** (stocks **and** crypto on one provider), with optional Binance (crypto) and OANDA (forex) fallbacks, and **FRED** for macro series.
- **High-Frequency Signals**: 5 distinct strategy modules providing timeframe-tagged signals (15m scalp to daily swing).
- **Unified Risk Manager**: Fixed-fractional position sizing with volatility-adaptive (ATR) stop-loss / take-profit levels (minimum 1:3 Risk-to-Reward) and buying-power limits across concurrent positions.
- **Signal Combiner**: Aggregates signals from multiple strategies and scales conviction based on alignment.
- **Paper Trading Engine**: Real-time simulation of trade execution and P&L tracking.
- **Live Dashboard**: Website page showing balance, open positions, PnL, and macro regime, auto-refreshing every 15s.
- **Broker Reconciliation**: Diffs the bot's positions against a broker snapshot and flags drift.
- **Schedulable**: Run continuously or as single cron-driven cycles (`--once`).

## Strategy Summary
1. **Momentum + Volume Confirmation**: EMA crossovers (9/21) confirmed by volume spikes and VWAP trend.
2. **Relative Strength / Flow Detection**: Tracks assets outperforming their benchmark (SPY/BTC) during volume surges.
3. **Cross-Asset Leading Signals**: Monitors leading indicators like DXY and Bond Yields to predict moves in risk assets.
4. **On-Chain & Sentiment (Crypto)**: Uses MVRV ratios and exchange flows for contrarian positioning.
5. **Macro Regime Detection**: Rules-based filter of yield curve and inflation to set overall market bias.

## Symbol Coverage
For a full list of monitored symbols, spreads, and liquidity analysis, see [symbol_validation.md](../symbol_validation.md).

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

Secrets live in a `.env` file at the project root — **never** commit it (it's
gitignored). `config/settings.yaml` references them as `${VAR}` placeholders
which are expanded from the environment at load time.

1. Create `.env` from the template:
   ```bash
   cp .env.example .env
   ```
2. Fill in your keys. **Alpaca** (paper trading) is the primary provider and
   covers both stocks and crypto; **FRED** is optional (real macro data):
   ```bash
   ALPACA_API_KEY=your_paper_key
   ALPACA_API_SECRET=your_paper_secret
   FRED_API_KEY=your_fred_key          # optional
   ```
   Get free Alpaca **paper** keys at https://app.alpaca.markets and a free FRED
   key at https://fredaccount.stlouisfed.org/apikeys.

   With no keys set, every data source falls back to deterministic **mock
   data**, so the bot still runs end-to-end for development.

3. Verify connectivity before running (checks account auth + market data):
   ```bash
   python scripts/check_alpaca.py      # expect ✅ ✅
   ```

### Running the Bot

```bash
python main.py                 # run continuously (default 60s cycles)
python main.py --interval 30   # custom cycle interval (seconds)
python main.py --once          # run a single cycle and exit (for cron/schedulers)
python main.py --cycles 10     # run N cycles then stop
```

Each cycle fetches data, runs the strategy ensemble, paper-trades with
risk-managed sizing, and publishes a snapshot to `website/status.json`.

To halt trading immediately, create a `killswitch.lock` file in the project
root; delete it to resume.

### Order execution: local vs Alpaca

By default (`trading.broker: paper` in `settings.yaml`) the bot trades a **local
simulator** — orders never reach Alpaca, so nothing appears on the Alpaca
dashboard. To also submit orders to your **Alpaca account** (so positions show
up there and reconcile automatically), set:

```yaml
trading:
  broker: alpaca      # mirror orders to Alpaca (paper account while
                      # exchanges.alpaca.paper is true)
```

With `exchanges.alpaca.paper: true` this uses your **paper** account — real
order flow, **no real money**. (Pointing at live keys would place real trades;
only do that once you've thoroughly paper-tested and understand the risk.)

When `broker: alpaca` is set, the bot:
- **sizes positions off your real Alpaca equity** (not the $10k simulator),
- **skips symbols you already hold** on Alpaca (no pile-up), and
- makes the **dashboard mirror your live Alpaca account** (balance + positions),
  so the website and the Alpaca dashboard match.

**Exit handling:** equity orders are submitted as **bracket orders**, so Alpaca
auto-manages the stop-loss / take-profit. Alpaca can't bracket crypto, so the
bot manages **crypto exits in software**: it records each crypto position's
stop/target (persisted in `crypto_exits.json`) and closes the position when a
level is touched on a later cycle. (Because exits are checked once per cycle,
crypto stops are approximate — they act on the next cycle after a level is hit,
not tick-by-tick.)

### Live Dashboard

The website surfaces the bot's live state (balance, open positions, PnL, macro
regime, broker reconciliation) and auto-refreshes every 15s.

```bash
cd website
bun install        # first time only
bun run publish    # build + serve on http://localhost:3000
```

Open `http://localhost:3000/dashboard`. Until the bot has run, it shows an
"awaiting first snapshot" state.

### Broker Reconciliation (optional)

The bot can diff its positions against your real broker holdings and flag any
drift on the dashboard. Provide a snapshot file (any broker):

```bash
cp broker_snapshot.example.json broker_snapshot.json   # then edit with real positions
```

`broker_snapshot.json` is gitignored. Override its location with
`MINUTETRADER_BROKER_SNAPSHOT`.

### Performance report

Print how the bot is doing:

```bash
python scripts/report.py
```

- **Alpaca mode** — current equity, open positions with unrealized P&L, and
  (best-effort) total return + max drawdown from Alpaca's portfolio history.
- **Simulator mode** — realized win rate, profit factor, expectancy and max
  drawdown from the local paper-trading history.

### Testing

```bash
python -m pytest -q          # Python test suite
cd website && bun run build  # type-check / build the site
```

## Contributing
Please follow the defined branch strategy and PR process outlined in [WORKFLOW.md](WORKFLOW.md).

## Architecture
For a deep dive into the bot's internal structure and data flow, see [ARCHITECTURE.md](ARCHITECTURE.md).
