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

Pine Script is a different language from Python, so these are separate,
hand-written implementations — they can't be pasted into the Pine Editor
directly from `main.py`. There are four independent indicators so each
piece can be added or removed on its own to declutter the chart without
touching the others:

### [pine/reversal_confluence.pine](pine/reversal_confluence.pine)

SMA crossover signals scored against a swing structure break confluence,
plus auxiliary chart overlays:
- SMA crossover BUY/SELL signals, scored against confluences and plotted
  with a confluence score label
- ATR-based take-profit/stop-loss lines for the most recently printed
  signal (default 1.5x ATR stop, 3x ATR target)
- 1H, 4H, and Daily 50/200 SMA lines pulled via `request.security`,
  intended for use on a 5-minute chart
- Two `alertcondition()`s for setting up TradingView alerts on qualifying
  signals

All toggles and lengths (TP/SL multiples, which timeframe SMAs to show)
are exposed as inputs, grouped by feature.

### [pine/orb_session_range.pine](pine/orb_session_range.pine)

A standalone 8:30-9:00am America/Chicago opening-range indicator, drawn as
a translucent box so candles remain visible through it. Kept separate so
you can remove just this indicator from the chart if the range gets
"disrespected" (broken) and you no longer want it cluttering the chart.
Exposes its own `alertcondition()`s for closes above/below the range.

### [pine/auto_support_resistance.pine](pine/auto_support_resistance.pine)

A standalone automatic support/resistance indicator. Tracks swing
highs/lows as levels, which flip color/role (support -> resistance, or
back) once price closes through them, with optional flip labels. Kept
separate from the confluence indicator so it can be hidden independently
to declutter the chart.

### [pine/micro_fib_pullback.pine](pine/micro_fib_pullback.pine)

A standalone 0.5/0.618 fib retracement indicator, drawn in the familiar
manual-tool style: plain dashed lines labeled `50.00% (price)` and
`61.80% (price)`, extending right. The fib is only shown while a pullback
is actually happening — not during the impulsive trend leg itself and not
when there's no active setup — to keep the chart decluttered.

Sequence per setup:
1. **Structure break**: tracks the most recent *significant* swing
   high/low (`structureBars` lookback/lookahead, default 8 — intentionally
   wider than a noisy short pivot so this doesn't fire on every minor
   wiggle). The moment price closes beyond one of these levels, a trend
   leg begins, originating from the swing low that preceded a bullish
   break (or swing high that preceded a bearish break) — i.e. the launch
   point of the move. This single rule covers both a break of established
   trend structure and emerging from a consolidation/range, since a
   range's boundary is mechanically the same kind of level.
2. **Impulsive move**: the trend's running high (bullish) or low
   (bearish) is tracked internally, but nothing is drawn yet.
3. **Minimum move filter**: once a confirmed pivot against the trend
   direction appears, it only qualifies as a real pullback if the
   impulsive leg (origin to that pivot) traveled at least
   `minMoveAtrMult` x ATR (default 1.5x, ATR length 14) — filtering out
   small moves that aren't a meaningful trend. If the move is too small,
   the pivot is ignored and impulsive tracking continues.
4. **Confirmed pullback**: once a qualifying pivot locks in "the last
   high/low of the trend before it reversed," the fib lines appear —
   green for a bullish trend/pullback, red for a bearish one — measured
   from the origin swing low/high to that locked extreme.
5. **Resolution**: the fib disappears again once either (a) price fully
   invalidates the setup by closing back through the origin level, or (b)
   the trend resumes past the locked extreme (no longer a pullback), at
   which point tracking goes back to step 2 with the new extreme until the
   next qualifying pullback.

### Using any script

1. Open any chart on [TradingView](https://www.tradingview.com)
2. Open the Pine Editor (bottom panel) and paste in the contents of the
   desired `.pine` file
3. Click "Add to Chart"
4. Adjust settings from the indicator's settings panel

None of these scripts have been run inside TradingView by me directly —
`reversal_confluence.pine` and `auto_support_resistance.pine` use Pine's
user-defined types and object arrays, which is more advanced syntax, so
review them carefully in the Pine Editor and confirm they compile/behave
as expected before relying on them.
