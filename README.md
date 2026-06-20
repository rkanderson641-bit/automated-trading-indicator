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
directly from `main.py`. There are five independent indicators so each
piece can be added or removed on its own to declutter the chart without
touching the others:

### [pine/reversal_confluence.pine](pine/reversal_confluence.pine)

SMA crossover signals scored against a swing structure break confluence,
plus an auxiliary overlay:
- SMA crossover BUY/SELL signals, scored against confluences and plotted
  with a confluence score label
- ATR-based take-profit/stop-loss lines for the most recently printed
  signal (default 1.5x ATR stop, 3x ATR target)
- An `alertcondition()` for setting up TradingView alerts on qualifying
  signals

All toggles and lengths (TP/SL multiples, etc.) are exposed as inputs,
grouped by feature.

### [pine/orb_session_range.pine](pine/orb_session_range.pine)

A standalone indicator with three independent opening-range windows, each
with its own visibility toggle, session/timezone inputs, and styling — all
default to CDT (America/Chicago):
- **8:30-9:00 main ORB**: drawn as a translucent box so candles remain
  visible through it. Exposes `alertcondition()`s for closes above/below
  the range ("disrespected").
- **7:30-7:45 overnight ORB**: drawn the same way as the main ORB box
  (single translucent box), just white by default instead of purple.
- **8:30-8:45 NY AM 15-minute ORB**: drawn as opaque high/low lines that
  extend the same length as the main ORB box (stopping at the current
  bar, not stretching into the empty future), instead of a box.

All three also draw an opaque dotted midpoint line in the same color as
their range, toggleable independently per range.

All three automatically apply each trading day, extending through the
rest of the session once their window closes (configurable per range).
Note: these intraday windows (15-30 minutes) need a chart timeframe at or
below the window size to register a bar inside them — e.g. a 1-hour chart
will never show any of these, since no 1H bar's start time falls within a
15-30 minute window. Use 5m or 15m.

### [pine/auto_support_resistance.pine](pine/auto_support_resistance.pine)

A standalone automatic support/resistance indicator. Tracks swing
highs/lows as levels, which flip color/role (support -> resistance, or
back) once price closes through them, with optional flip labels. Kept
separate from the confluence indicator so it can be hidden independently
to declutter the chart.

### [pine/micro_fib_pullback.pine](pine/micro_fib_pullback.pine)

A standalone 0.5/0.618 fib retracement indicator built on a standard
ZigZag swing detector, drawn in the familiar manual-tool style: plain
dashed lines labeled `50.00% (price)` and `61.80% (price)`, extending
right.

- A new swing point only confirms once price reverses from the current
  candidate extreme by at least `thresholdMult` x ATR (default 4x
  ATR(20)) — a confirmed pivot can never be "un-confirmed," which avoids
  the whipsaw that simpler structure-break heuristics ran into.
- The fib for each confirmed leg is colored green (bullish/support) or
  red (bearish/resistance), measured between the last two confirmed swing
  points.
- Only the most recent `maxActiveLegs` (default 2 — the current trend's
  leg plus the immediately preceding opposing leg) stay on the chart, so
  you see both a "true trend" entry zone and the opposing support/
  resistance confluence behind it, not the whole session's history.
- A leg is dropped immediately once it's no longer "unvisited or
  respected" — i.e. once price closes through its 61.8% level against it
  without holding.

### [pine/key_price_levels.pine](pine/key_price_levels.pine)

A standalone "key price levels" overlay, replicating the kind of
multi-timeframe confluence levels traders mark up by hand:
- **Multi-timeframe SMAs**: Daily, 4H, and 1H 50/200 SMAs, each drawn as a
  flat reference line + right-edge label at the SMA's current value
  (not the historical curve), so a higher-timeframe SMA is visible on a
  low-timeframe chart without needing to switch timeframes. These move
  live as the higher-timeframe candle prints, reflecting the most
  current value of that timeframe. These span the whole chart since
  there's no single "origin candle" for a continuously evolving average.
- **Overnight session high/low** (`ONH`/`ONL`): tracked live during a
  configurable overnight session window (default 1700-0730
  America/Chicago, i.e. CDT), then frozen for the rest of the day. The
  line starts exactly at the bar where that high/low printed.
- **Previous day high/low** (`PDH`/`PDL`): the line starts exactly at the
  bar in yesterday's session where that high/low actually printed, not at
  today's open.
- **Today's opening price** (`OP`): today's daily bar's open, with the
  line starting at today's first bar.

Each group has its own visibility toggle and color inputs.

### [pine/trend_line_rsi_reversal.pine](pine/trend_line_rsi_reversal.pine)

A standalone trend-line indicator for spotting reversal points on an
already-overextended trend:
- Trend direction uses a structure-break definition (same as
  `reversal_confluence.pine`): a close beyond the most recent prior swing
  high/low confirms a bullish/bearish trend immediately, without waiting
  for a pullback to form a second confirming pivot.
- A trend line has a FIXED origin — the swing low (uptrend) or swing high
  (downtrend) that launched the move, captured once when the leg starts —
  and a far point that continuously tracks the running extreme (the
  highest high so far for an uptrend, the lowest low so far for a
  downtrend) using each bar's own real wick. Neither point is ever a
  synthetic value like the current bar's close, which can land inside a
  candle's body and make the line cut through printed candles instead of
  touching their corners/wicks. The far point updates every single bar a
  new extreme prints, with no pivot-confirmation lag, so the line never
  falls behind price the way an earlier pivot-gated design did.
- The line is drawn the moment RSI's moving average confirms the trend is
  stretched (above overbought during a confirmed uptrend = "overextended,"
  or below oversold during a confirmed downtrend = "underextended") —
  using the origin and running extreme already accumulated since the leg
  began, so it reflects the move's full progress even if RSI confirms a
  while after the breakout. The overextended/underextended check uses a
  level-based "armed" latch rather than a same-bar crossover, so it still
  fires even when the swing-confirmation lag means the trend structure
  confirms a few bars after RSI actually crossed the threshold.
- If price stops making new extremes, the line simply stays put at the
  last one — it does not need a separate "divergence" mechanism, since
  there's nothing to fall behind: the far point IS the actual running
  extreme. A "re-anchor on violation" mechanism (freezing the line and
  starting a fresh one from the same origin whenever price closed back
  through its own projection, to avoid a single straight line cutting
  through an intermediate bounce) was tried but removed — comparing
  against a slope built from a recent, narrow origin-to-extreme span
  triggered "violations" almost immediately after nearly every new
  extreme, producing a runaway fan of one-bar lines. Only a genuine
  opposite structure break ends a leg, at which point the current line
  freezes permanently exactly as drawn and stays on the chart as a record
  of that completed leg — lines are never deleted, so the full history of
  overextended/underextended trend lines for the day remains visible. The
  break is flagged with its own label and `alertcondition()`.
- The line's far point also gets a small overshoot
  (`Extend each line past its last point`, default 8 bars) projected
  along the line's own slope, so it doesn't stop dead exactly at the last
  touch — closer to how a hand-drawn trend line usually runs slightly
  past its last contact point.
- The break level always ratchets to the most recent confirmed pivot,
  regardless of current trend state. A close back above the most recent
  lower-high pivot (or below the most recent higher-low) is a legitimate
  micro-reversal/bounce — exactly what this indicator is meant to catch,
  even within a larger trend. An earlier attempt froze the
  opposite-direction level once a trend was confirmed, on the theory that
  a reversal-direction line appearing mid-trend was a bug, but that meant
  a reversal had to clear the price level from before the entire PRIOR
  trend even started — an almost unreachable bar after any real move —
  so breaks (and therefore lines) almost stopped firing at all.

RSI itself isn't plotted by this script (it's overlay-only, used purely
to gate when a line gets drawn) — pair it with a regular RSI indicator in
its own pane for visual confirmation.

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
