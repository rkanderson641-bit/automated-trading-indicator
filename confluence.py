"""Reversal-confluence helpers: swing structure, fib pullback zones, and
opening-range breakout (ORB) levels, used to add confidence to raw SMA
crossover signals.
"""

import datetime
from zoneinfo import ZoneInfo

CHICAGO_TZ = ZoneInfo("America/Chicago")
ORB_START = datetime.time(8, 30)
ORB_END = datetime.time(9, 0)


def find_swing_points(prices, window=3):
    """Return [(index, 'high'|'low', price), ...] for local extrema using a
    symmetric lookback/lookahead window on each side of the candidate bar."""
    swings = []
    n = len(prices)
    for i in range(window, n - window):
        segment = prices[i - window:i + window + 1]
        if prices[i] == max(segment):
            swings.append((i, "high", prices[i]))
        elif prices[i] == min(segment):
            swings.append((i, "low", prices[i]))
    return swings


def detect_structure_breaks(prices, swings):
    """Return [(index, 'bullish'|'bearish', broken_level), ...] marking bars
    where price closes beyond the most recent prior swing high (bullish
    break of a downtrend) or swing low (bearish break of an uptrend)."""
    breaks = []
    last_high = None
    last_low = None
    swing_idx = 0

    for i, price in enumerate(prices):
        while swing_idx < len(swings) and swings[swing_idx][0] < i:
            _, kind, level = swings[swing_idx]
            if kind == "high":
                last_high = level
            else:
                last_low = level
            swing_idx += 1

        if last_high is not None and price > last_high:
            breaks.append((i, "bullish", last_high))
            last_high = price
        if last_low is not None and price < last_low:
            breaks.append((i, "bearish", last_low))
            last_low = price

    return breaks


def fib_pullback_zone(swing_start, swing_end):
    """Return (lower, upper) bounds of the 0.5-0.618 retracement zone for a
    move from swing_start to swing_end, where institutional pullback orders
    are typically expected to fill before trend continuation."""
    move = swing_end - swing_start
    level_50 = swing_end - 0.5 * move
    level_618 = swing_end - 0.618 * move
    return (min(level_50, level_618), max(level_50, level_618))


def in_zone(price, zone, tolerance_pct=0.0015):
    """True if price falls within (or just outside, by tolerance_pct) a
    (lower, upper) price zone."""
    lower, upper = zone
    pad = price * tolerance_pct
    return (lower - pad) <= price <= (upper + pad)


def compute_opening_range(timestamps, highs, lows):
    """Compute the 8:30-9:00 America/Chicago opening-range high/low for each
    trading day present in the bars. Returns {date: (range_low, range_high)}."""
    ranges = {}
    for ts, high, low in zip(timestamps, highs, lows):
        local = ts.astimezone(CHICAGO_TZ)
        if ORB_START <= local.time() < ORB_END:
            day = local.date()
            prev_low, prev_high = ranges.get(day, (low, high))
            ranges[day] = (min(prev_low, low), max(prev_high, high))
    return ranges


def score_confluence(price, timestamp, fib_zone, orb_range, support_resistance, tolerance_pct=0.0015):
    """Return (score, reasons) counting how many reversal confluences the
    given price/time lines up with: fib pullback zone, opening-range
    breakout level, and prior swing support/resistance."""
    reasons = []

    if fib_zone is not None and in_zone(price, fib_zone, tolerance_pct):
        reasons.append("fib_0.5_0.618_zone")

    if orb_range is not None:
        local_day = timestamp.astimezone(CHICAGO_TZ).date()
        day_range = orb_range.get(local_day)
        if day_range is not None:
            range_low, range_high = day_range
            if price >= range_high:
                reasons.append("orb_breakout_above")
            elif price <= range_low:
                reasons.append("orb_breakout_below")

    for level in support_resistance:
        if in_zone(price, (level, level), tolerance_pct):
            reasons.append(f"structure_level_{level:.2f}")
            break

    return len(reasons), reasons
