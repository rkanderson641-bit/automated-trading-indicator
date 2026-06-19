# Automated Trading Indicator

Simple technical indicators for trading research.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the reversal-confluence indicator against live intraday price data:

```bash
python3 main.py AAPL --period 5d --interval 5m --fast 10 --slow 30 --min-confluence 2
```

This fetches intraday OHLC bars for the ticker and generates BUY/SELL
signals from a fast/slow SMA crossover, then scores each signal against
three reversal confluences:

- **Swing structure breaks** — price closing beyond the most recent prior
  swing high/low, indicating a potential trend reversal rather than
  mid-trend noise
- **0.5-0.618 fibonacci pullback zone** — the classic institutional
  order-fill retracement zone measured from the most recent swing move
- **8:30-9:00am America/Chicago opening range breakout (ORB)** — whether
  price is trading outside the high/low range set in the first 30 minutes
  after the US cash open

Signals are reported with a `confluence_score` (how many of the above line
up) and the matching reasons. Use `--min-confluence` to filter out
low-confluence (likely noisier) signals.

### Library usage

```python
from sma import calculate_sma

prices = [10, 11, 12, 13, 14, 15]
calculate_sma(prices, window=3)
# [11.0, 12.0, 13.0, 14.0]
```

## TradingView (Pine Script)

[pine/reversal_confluence.pine](pine/reversal_confluence.pine) is a Pine
Script v6 port of the same confluence logic (SMA crossover, swing structure
breaks, fib pullback zone, and 8:30-9:00am CDT opening range), for use
directly on a TradingView chart. Python and Pine Script are different
languages, so this is a separate implementation, not the same file — it
can't be pasted into the Pine Editor as-is from `main.py`.

To use it:
1. Open any chart on [TradingView](https://www.tradingview.com)
2. Open the Pine Editor (bottom panel) and paste in the contents of
   `pine/reversal_confluence.pine`
3. Click "Add to Chart"
4. Adjust the Fast/Slow SMA length, swing lookback, tolerance, and minimum
   confluence score from the indicator's settings panel

BUY/SELL triangles are plotted with a confluence score label, and two
`alertcondition()`s are exposed for setting up TradingView alerts on
qualifying signals.

This Pine version hasn't been run inside TradingView yet — review it in the
Pine Editor and confirm it compiles/behaves as expected before relying on it.
