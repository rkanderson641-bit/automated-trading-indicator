import datetime
import unittest
from zoneinfo import ZoneInfo

from confluence import (
    find_swing_points,
    detect_structure_breaks,
    fib_pullback_zone,
    in_zone,
    compute_opening_range,
    score_confluence,
)

CHICAGO = ZoneInfo("America/Chicago")


def ts(hour, minute, day=1):
    return datetime.datetime(2026, 6, day, hour, minute, tzinfo=CHICAGO)


class TestSwingPoints(unittest.TestCase):
    def test_finds_high_and_low(self):
        prices = [1, 2, 5, 2, 1, 0, 1, 2]
        swings = find_swing_points(prices, window=2)
        kinds = {(i, k) for i, k, _ in swings}
        self.assertIn((2, "high"), kinds)
        self.assertIn((5, "low"), kinds)


class TestStructureBreaks(unittest.TestCase):
    def test_detects_bullish_break_above_prior_swing_high(self):
        prices = [1, 2, 5, 2, 1, 0, 1, 4, 6]
        swings = find_swing_points(prices, window=2)
        breaks = detect_structure_breaks(prices, swings)
        kinds = [b[1] for b in breaks]
        self.assertIn("bullish", kinds)

    def test_no_breaks_when_no_swings(self):
        prices = [1, 1, 1, 1, 1]
        self.assertEqual(detect_structure_breaks(prices, []), [])


class TestFibPullbackZone(unittest.TestCase):
    def test_zone_bounds_for_upmove(self):
        lower, upper = fib_pullback_zone(swing_start=100, swing_end=200)
        self.assertAlmostEqual(lower, 138.2)
        self.assertAlmostEqual(upper, 150.0)

    def test_in_zone_respects_tolerance(self):
        zone = (100.0, 110.0)
        self.assertTrue(in_zone(105.0, zone))
        self.assertTrue(in_zone(99.95, zone))
        self.assertFalse(in_zone(50.0, zone))


class TestOpeningRange(unittest.TestCase):
    def test_computes_range_within_window_only(self):
        timestamps = [ts(8, 0), ts(8, 30), ts(8, 45), ts(9, 0), ts(9, 15), ts(10, 0)]
        highs = [999, 10, 12, 999, 999, 999]
        lows = [1, 9, 11, -999, -999, -999]
        ranges = compute_opening_range(timestamps, highs, lows)
        day = ts(8, 0).date()
        self.assertEqual(ranges[day], (9, 12))


class TestScoreConfluence(unittest.TestCase):
    def test_scores_fib_and_orb_and_structure(self):
        timestamp = ts(9, 0)
        orb_range = {timestamp.date(): (10, 20)}
        score, reasons = score_confluence(
            price=21,
            timestamp=timestamp,
            fib_zone=(20.5, 21.5),
            orb_range=orb_range,
            support_resistance=[21.0],
        )
        self.assertEqual(score, 3)
        self.assertIn("fib_0.5_0.618_zone", reasons)
        self.assertIn("orb_breakout_above", reasons)

    def test_zero_score_when_no_confluence(self):
        timestamp = ts(9, 0)
        score, reasons = score_confluence(
            price=5,
            timestamp=timestamp,
            fib_zone=(100, 110),
            orb_range={},
            support_resistance=[200],
        )
        self.assertEqual(score, 0)
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
