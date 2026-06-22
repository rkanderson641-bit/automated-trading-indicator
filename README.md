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

### [pine/trend_line_strategy.pine](pine/trend_line_strategy.pine)

A standalone trend-line indicator rebuilt directly from a trend-line
tutorial (gold futures on ThinkOrSwim) rather than from a hand-typed spec —
audio transcript and on-screen chart frames were both reviewed to confirm
the rules below before writing any code. There is **no RSI gate of any
kind** — that was a mistaken assumption baked into an earlier, since-deleted
version of this script:
- An uptrend line connects 2+ ascending swing lows; a downtrend line
  connects 2+ descending swing highs — same pivot type only, never a high
  to a low. A line is drawn the instant it has two real touch points and
  stays visible the whole time it's structurally valid, exactly like a
  hand-drawn trend line.
- Two pivot lookbacks: `Swing Lookback/Lookahead Bars` (wider, default 8)
  picks the origin pivot and overall trend direction; `Touch Point
  Lookback/Lookahead Bars` (narrower, default 3) finds the touch points
  that roll a line's far point forward, since a single wide lookback is
  too strict to catch every real touch during a fast or choppy move.
- **Wick-only, checked continuously, not just at branch points**: every
  touch point that continues the structure is only accepted if the
  resulting line stays clear of every candle body the ENTIRE way from
  origin to that point — not just its newest segment. If extending the
  existing line that far would cut into some earlier candle's body, a
  fresh, shorter line anchored from just the last touch point onward is
  used instead, provided that shorter line is itself clean; if neither
  is clean, the touch point is ignored. On top of that, every single bar
  — even quiet ones with no new touch point — the line's projection to
  "today" is checked against today's candle too, since a fixed slope can
  drift into a body over many bars just as easily as a bad update can. If
  it would, rendering is simply skipped for that one bar (a `CLIP` debug
  marker) — the line and its anchors are left exactly as they are rather
  than torn down, since intrusion on a single bar is almost always a
  one-bar coincidence rather than proof the anchor has gone bad; tearing
  it down on every such bar left visible gaps in otherwise-clean trends
  and erased the very line a genuine divergence needed to compare against.
- **Branching**: when a new touch point continues the structure but lands
  meaningfully beyond where the existing line already projects (steeper
  than expected — `Divergence sensitivity margin`), the existing line
  freezes in place and a new, steeper line begins from that same point, in
  a separate lighter color. The same wick-only check applies, plus its two
  points must be far enough apart (at least the swing lookback) to not
  just be reacting to one noisy candle. A line can also branch this way
  purely because continuing the original line stopped being clean — not
  just because of steepness.
- **Reactions vs. real breaks**: a wick can cross a line while the candle's
  close stays on the correct side — that's a reaction (`REACT` marker, the
  line held), not a break. A real break only happens when CLOSE moves
  through the line by more than the break margin (`Minimum break size`).
  On a break the line freezes (with a small visual overshoot, never
  deleted) — but unlike a flagged signal, nothing fires yet.
- **Confirmation via backtest**: a break alone can fake out, so instead of
  signaling immediately, the broken level is watched for up to `Backtest
  window after a break` bars. If price comes back to test that level
  (within `Backtest proximity` x ATR) and then closes back away in the new
  direction, that's a `CONFIRMED LONG`/`CONFIRMED SHORT` entry signal. If
  price instead closes back through to the original side first, it's
  tagged `FAKEOUT` and the watch is cancelled.

RSI isn't used anywhere in this script.

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
