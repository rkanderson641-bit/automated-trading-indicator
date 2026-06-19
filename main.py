import argparse
import sys

import yfinance as yf

from sma import calculate_sma
from confluence import (
    find_swing_points,
    detect_structure_breaks,
    fib_pullback_zone,
    compute_opening_range,
    score_confluence,
)


def fetch_intraday_bars(ticker, period="5d", interval="5m"):
    """Fetch intraday OHLC bars for a ticker. Returns (timestamps, highs, lows, closes)."""
    history = yf.Ticker(ticker).history(period=period, interval=interval)
    if history.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'")
    timestamps = list(history.index)
    highs = history["High"].tolist()
    lows = history["Low"].tolist()
    closes = history["Close"].tolist()
    return timestamps, highs, lows, closes


def generate_crossover_signals(prices, fast_window, slow_window):
    """Return [(index, 'BUY'|'SELL'), ...] where the fast SMA crosses the slow SMA."""
    fast_sma = calculate_sma(prices, fast_window)
    slow_sma = calculate_sma(prices, slow_window)

    offset = slow_window - fast_window
    if offset < 0:
        raise ValueError("fast_window must not be larger than slow_window")
    fast_sma = fast_sma[offset:]

    signals = []
    prev_diff = None
    for i, (fast, slow) in enumerate(zip(fast_sma, slow_sma)):
        diff = fast - slow
        if prev_diff is not None:
            if prev_diff <= 0 and diff > 0:
                signals.append((i, "BUY"))
            elif prev_diff >= 0 and diff < 0:
                signals.append((i, "SELL"))
        prev_diff = diff
    return signals


def most_recent_swing_pair(swings, before_index):
    """Return the most recent (low, high) swing pair occurring before
    before_index, in chronological order, for fib zone calculation."""
    prior = [s for s in swings if s[0] < before_index]
    if len(prior) < 2:
        return None
    a, b = prior[-2], prior[-1]
    if a[1] == b[1]:
        return None
    low = a if a[1] == "low" else b
    high = a if a[1] == "high" else b
    return low[2], high[2]


def build_signals_with_confluence(timestamps, highs, lows, closes, fast_window, slow_window, swing_window):
    """Combine SMA crossover signals with reversal confluences (fib pullback
    zone, opening-range breakout, prior swing structure) and return a list
    of dicts describing each signal and its confluence score."""
    crossovers = generate_crossover_signals(closes, fast_window, slow_window)
    if not crossovers:
        return []

    # Crossover index i corresponds to closes[slow_window - 1 + i]
    base_offset = slow_window - 1

    swings = find_swing_points(closes, window=swing_window)
    structure_breaks = detect_structure_breaks(closes, swings)
    break_indices_by_type = {"bullish": [b[0] for b in structure_breaks if b[1] == "bullish"],
                              "bearish": [b[0] for b in structure_breaks if b[1] == "bearish"]}
    support_resistance = [level for _, _, level in swings]
    orb_range = compute_opening_range(timestamps, highs, lows)

    results = []
    for cross_idx, signal in crossovers:
        price_idx = base_offset + cross_idx
        price = closes[price_idx]
        timestamp = timestamps[price_idx]

        swing_pair = most_recent_swing_pair(swings, price_idx)
        fib_zone = fib_pullback_zone(*swing_pair) if swing_pair else None

        score, reasons = score_confluence(price, timestamp, fib_zone, orb_range, support_resistance)

        wanted_break = "bullish" if signal == "BUY" else "bearish"
        if any(b_idx <= price_idx for b_idx in break_indices_by_type[wanted_break]):
            score += 1
            reasons.append(f"{wanted_break}_structure_break")

        results.append({
            "index": price_idx,
            "timestamp": timestamp,
            "signal": signal,
            "price": price,
            "confluence_score": score,
            "reasons": reasons,
        })
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Reversal-confluence SMA crossover indicator (fib pullback zone, "
                     "8:30-9:00am CDT opening range, and swing structure breaks)"
    )
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--period", default="5d", help="History period to fetch (default: 5d)")
    parser.add_argument("--interval", default="5m", help="Bar interval (default: 5m)")
    parser.add_argument("--fast", type=int, default=10, help="Fast SMA window (default: 10)")
    parser.add_argument("--slow", type=int, default=30, help="Slow SMA window (default: 30)")
    parser.add_argument("--swing-window", type=int, default=3, help="Swing point lookback/lookahead bars (default: 3)")
    parser.add_argument("--min-confluence", type=int, default=1,
                         help="Minimum confluence score to display a signal (default: 1)")
    args = parser.parse_args()

    try:
        timestamps, highs, lows, closes = fetch_intraday_bars(args.ticker, args.period, args.interval)
        signals = build_signals_with_confluence(
            timestamps, highs, lows, closes, args.fast, args.slow, args.swing_window
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    signals = [s for s in signals if s["confluence_score"] >= args.min_confluence]

    if not signals:
        print(f"No qualifying signals for {args.ticker} over {args.period} ({args.interval} bars).")
        return

    print(f"Signals for {args.ticker} (fast={args.fast}, slow={args.slow}, "
          f"period={args.period}, interval={args.interval}):")
    for s in signals:
        reasons = ", ".join(s["reasons"]) if s["reasons"] else "crossover only"
        print(f"  {s['timestamp']} | {s['signal']} @ {s['price']:.2f} "
              f"| confluence={s['confluence_score']} ({reasons})")


if __name__ == "__main__":
    main()
