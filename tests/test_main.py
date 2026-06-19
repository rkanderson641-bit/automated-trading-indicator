import unittest

from main import generate_signals


class TestGenerateSignals(unittest.TestCase):
    def test_detects_bullish_and_bearish_crossovers(self):
        # Prices dip then rise then fall, forcing the fast SMA to cross
        # below and then above the slow SMA.
        prices = [10] * 5 + [5] * 5 + [20] * 10 + [2] * 10
        signals = generate_signals(prices, fast_window=3, slow_window=6)
        kinds = [signal for _, signal in signals]
        self.assertIn("BUY", kinds)
        self.assertIn("SELL", kinds)

    def test_no_crossover_returns_empty(self):
        prices = list(range(1, 21))  # steadily increasing, no crossover
        signals = generate_signals(prices, fast_window=3, slow_window=6)
        self.assertEqual(signals, [])

    def test_fast_window_larger_than_slow_raises(self):
        with self.assertRaises(ValueError):
            generate_signals([1, 2, 3, 4, 5], fast_window=6, slow_window=3)


if __name__ == "__main__":
    unittest.main()
