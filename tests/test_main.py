import datetime
import unittest
from zoneinfo import ZoneInfo

from main import generate_crossover_signals, build_signals_with_confluence

CHICAGO = ZoneInfo("America/Chicago")


def ts(hour, minute, day=1):
    return datetime.datetime(2026, 6, day, hour, minute, tzinfo=CHICAGO)


class TestGenerateCrossoverSignals(unittest.TestCase):
    def test_detects_bullish_and_bearish_crossovers(self):
        prices = [10] * 5 + [5] * 5 + [20] * 10 + [2] * 10
        signals = generate_crossover_signals(prices, fast_window=3, slow_window=6)
        kinds = [signal for _, signal in signals]
        self.assertIn("BUY", kinds)
        self.assertIn("SELL", kinds)

    def test_no_crossover_returns_empty(self):
        prices = list(range(1, 21))
        signals = generate_crossover_signals(prices, fast_window=3, slow_window=6)
        self.assertEqual(signals, [])

    def test_fast_window_larger_than_slow_raises(self):
        with self.assertRaises(ValueError):
            generate_crossover_signals([1, 2, 3, 4, 5], fast_window=6, slow_window=3)


class TestBuildSignalsWithConfluence(unittest.TestCase):
    def test_returns_signals_with_scores_for_a_crossover_series(self):
        closes = [10] * 5 + [5] * 5 + [20] * 10 + [2] * 10
        n = len(closes)
        timestamps = [ts(8, 0) + datetime.timedelta(minutes=5 * i) for i in range(n)]
        highs = [c + 0.5 for c in closes]
        lows = [c - 0.5 for c in closes]

        results = build_signals_with_confluence(
            timestamps, highs, lows, closes, fast_window=3, slow_window=6, swing_window=2
        )

        self.assertTrue(len(results) > 0)
        for r in results:
            self.assertIn(r["signal"], ("BUY", "SELL"))
            self.assertGreaterEqual(r["confluence_score"], 0)
            self.assertEqual(len(r["reasons"]), r["confluence_score"])

    def test_no_crossover_means_no_signals(self):
        closes = list(range(1, 21))
        n = len(closes)
        timestamps = [ts(8, 0) + datetime.timedelta(minutes=5 * i) for i in range(n)]
        highs = [c + 0.5 for c in closes]
        lows = [c - 0.5 for c in closes]

        results = build_signals_with_confluence(
            timestamps, highs, lows, closes, fast_window=3, slow_window=6, swing_window=2
        )
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
