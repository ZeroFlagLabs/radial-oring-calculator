"""Tests that worksheet acceptance checks are independent of gland geometry."""

from dataclasses import replace
import unittest

from src.calculations.criteria import screen_rectangular
from src.calculations.rectangular import (
    Dimension as D,
    MaleRectangularInputs,
    Range,
    calculate_male_rectangular,
)


def case():
    """Synthetic test case: deliberately not derived from confidential drawings."""
    return calculate_male_rectangular(MaleRectangularInputs(
        cylinder_id=D(.750, .001),
        gland_od=D(.584, .001),
        mode="gland_od",
        gland_width=D(.145, .003),
        o_ring_id=D(.565, .005),
        o_ring_section=D(.103, .003),
    ))


class ScreeningTests(unittest.TestCase):
    def test_same_geometry_with_different_application(self):
        r = case()
        static = screen_rectangular(r, "static")
        dynamic = screen_rectangular(r, "dynamic")
        self.assertEqual(static.max_squeeze_percent, 30)
        self.assertEqual(dynamic.max_squeeze_percent, 16)
        self.assertTrue(static.checks[0].within_limits)
        self.assertFalse(dynamic.checks[0].within_limits)

    def test_all_static_checks_can_pass(self):
        report = screen_rectangular(case(), "static")
        self.assertTrue(report.all_within_limits)
        self.assertEqual(report.within_count, 3)

    def test_dynamic_only_changes_squeeze_limit(self):
        r = case()
        s = screen_rectangular(r, "static")
        d = screen_rectangular(r, "dynamic")
        self.assertEqual(s.checks[1:], d.checks[1:])
        self.assertFalse(d.all_within_limits)
        self.assertEqual(d.within_count, 2)

    def test_squeeze_minimum_inclusive(self):
        r = replace(case(), squeeze_in=Range(.007, .020, .025))
        self.assertTrue(screen_rectangular(r, "static").checks[0].within_limits)

    def test_squeeze_maximum_inclusive(self):
        r = replace(case(), squeeze_percent=Range(10, 20, 30))
        self.assertTrue(screen_rectangular(r, "static").checks[0].within_limits)
        r = replace(case(), squeeze_percent=Range(10, 12, 16))
        self.assertTrue(screen_rectangular(r, "dynamic").checks[0].within_limits)

    def test_stretch_limits_inclusive(self):
        r = replace(case(), stretch_percent=Range(0, 3, 4))
        self.assertTrue(screen_rectangular(r, "static").checks[1].within_limits)
        r = replace(case(), stretch_percent=Range(1, 3, 5))
        self.assertTrue(screen_rectangular(r, "static").checks[1].within_limits)

    def test_fill_limits_inclusive(self):
        r = replace(case(), gland_fill_percent=Range(60, 70, 80))
        self.assertTrue(screen_rectangular(r, "static").checks[2].within_limits)
        r = replace(case(), gland_fill_percent=Range(61, 70, 85))
        self.assertTrue(screen_rectangular(r, "static").checks[2].within_limits)

    def test_invalid_application_rejected(self):
        with self.assertRaisesRegex(ValueError, "Application"):
            screen_rectangular(case(), "rotary")


if __name__ == "__main__":
    unittest.main()
