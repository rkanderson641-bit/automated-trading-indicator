import argparse
import sys

import yfinance as yf

from sma import calculate_sma


def fetch_prices(ticker, period="6mo"):
    """Fetch daily closing prices for a ticker as a list of floats, oldest first."""
    history = yf.Ticker(ticker).history(period=period)
    if history.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'")
    return history["Close"].tolist()


def generate_signals(prices, fast_window, slow_window):
    """Return a list of (index, signal) tuples where signal is 'BUY' or 'SELL',
    based on fast SMA crossing above/below slow SMA."""
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


def main():
    parser = argparse.ArgumentParser(description="SMA crossover trading indicator")
    parser.add_argument("ticker", help="Stock ticker symbol, e.g. AAPL")
    parser.add_argument("--period", default="6mo", help="History period to fetch (default: 6mo)")
    parser.add_argument("--fast", type=int, default=10, help="Fast SMA window (default: 10)")
    parser.add_argument("--slow", type=int, default=30, help="Slow SMA window (default: 30)")
    args = parser.parse_args()

    try:
        prices = fetch_prices(args.ticker, args.period)
        signals = generate_signals(prices, args.fast, args.slow)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not signals:
        print(f"No crossover signals for {args.ticker} over {args.period}.")
        return

    print(f"Crossover signals for {args.ticker} (fast={args.fast}, slow={args.slow}, period={args.period}):")
    for index, signal in signals:
        print(f"  Day {index}: {signal}")


if __name__ == "__main__":
    main()
