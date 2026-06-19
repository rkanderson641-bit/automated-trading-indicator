import unittest

from sma import calculate_sma


class TestCalculateSMA(unittest.TestCase):
    def test_basic_window(self):
        prices = [10, 11, 12, 13, 14, 15]
        self.assertEqual(calculate_sma(prices, 3), [11.0, 12.0, 13.0, 14.0])

    def test_window_equal_to_length(self):
        prices = [1, 2, 3]
        self.assertEqual(calculate_sma(prices, 3), [2.0])

    def test_window_larger_than_prices_returns_empty(self):
        self.assertEqual(calculate_sma([1, 2], 5), [])

    def test_invalid_window_raises(self):
        with self.assertRaises(ValueError):
            calculate_sma([1, 2, 3], 0)


if __name__ == "__main__":
    unittest.main()
