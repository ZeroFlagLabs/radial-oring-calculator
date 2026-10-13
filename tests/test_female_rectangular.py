"""Independent synthetic female radial rectangular gland test cases."""

import math
import unittest

from src.calculations.criteria import screen_rectangular
from src.calculations.rectangular import (
    Dimension as D, FemaleRectangularInputs, calculate_female_rectangular,
)


def female_example(**updates):
    values = dict(
        rod_od=D(.575, .001),
        gland_width=D(.145, .003),
        o_ring_id=D(.565, .005),
        o_ring_section=D(.103, .003),
        bottom_radius=D(0),
        mode="gland_id", gland_id=D(.741, .001),
    )
    values.update(updates)
    return FemaleRectangularInputs(**values)


class FemaleGlandTests(unittest.TestCase):
    def test_direct_nominal_values(self):
        results = calculate_female_rectangular(female_example())
        self.assertAlmostEqual(results.gland_id.nominal, .741)
        self.assertAlmostEqual(results.radial_cavity_height.nominal, .083)
        self.assertAlmostEqual(results.squeeze_in.nominal, .020)
        self.assertAlmostEqual(results.squeeze_percent.nominal, 100 * .020 / .103)
        self.assertAlmostEqual(results.stretch_percent.nominal, 100 * (.575 / .565 - 1))
        self.assertAlmostEqual(results.gland_fill_percent.nominal,
                               100 * (math.pi * .103**2 / 4) / (.083 * .145))

    def test_direct_tolerance_extremes(self):
        results = calculate_female_rectangular(female_example())
        self.assertAlmostEqual(results.radial_cavity_height.minimum, .082)
        self.assertAlmostEqual(results.radial_cavity_height.maximum, .084)
        self.assertAlmostEqual(results.squeeze_in.minimum, .016)
        self.assertAlmostEqual(results.squeeze_in.maximum, .024)

    def test_female_stretch_uses_ring_id_tolerance(self):
        results = calculate_female_rectangular(female_example())
        self.assertAlmostEqual(results.stretch_percent.minimum, 100 * (.574 / .570 - 1))
        self.assertAlmostEqual(results.stretch_percent.maximum, 100 * (.576 / .560 - 1))

    def test_direct_and_depth_must_agree(self):
        direct = calculate_female_rectangular(female_example())
        from_depth = calculate_female_rectangular(female_example(
            mode="cylinder_and_depth", gland_id=None,
            cylinder_id=D(.577, .0005), groove_depth=D(.082, .00025),
        ))
        for key in ("minimum", "nominal", "maximum"):
            self.assertAlmostEqual(getattr(direct.gland_id, key), getattr(from_depth.gland_id, key))
            self.assertAlmostEqual(getattr(direct.radial_cavity_height, key), getattr(from_depth.radial_cavity_height, key))
        self.assertAlmostEqual(direct.gland_fill_percent.nominal,
                               from_depth.gland_fill_percent.nominal)

    def test_depth_tolerance_doubles(self):
        result = calculate_female_rectangular(female_example(
            mode="cylinder_and_depth", gland_id=None,
            cylinder_id=D(.577, .001), groove_depth=D(.082, .001),
        ))
        self.assertAlmostEqual(result.gland_id.minimum, .738)
        self.assertAlmostEqual(result.gland_id.maximum, .744)

    def test_screening_static_vs_dynamic_uses_same_results(self):
        result = calculate_female_rectangular(female_example())
        static = screen_rectangular(result, "static")
        dynamic = screen_rectangular(result, "dynamic")
        self.assertEqual(static.checks[1:], dynamic.checks[1:])
        self.assertTrue(static.checks[0].within_limits)
        self.assertFalse(dynamic.checks[0].within_limits)

    def test_bottom_radius_increases_fill(self):
        zero = calculate_female_rectangular(female_example())
        rounded = calculate_female_rectangular(female_example(bottom_radius=D(.010, 0)))
        self.assertGreater(rounded.gland_fill_percent.nominal, zero.gland_fill_percent.nominal)
        self.assertAlmostEqual(
            zero.cavity_area_sq_in.nominal - rounded.cavity_area_sq_in.nominal,
            (2 - math.pi / 2) * .010**2,
        )

    def test_positive_groove_depth_required(self):
        with self.assertRaisesRegex(ValueError, "Groove depth"):
            calculate_female_rectangular(female_example(
                mode="cylinder_and_depth", gland_id=None,
                cylinder_id=D(.577), groove_depth=D(.001, .001),
            ))

    def test_negative_cavity_rejected(self):
        with self.assertRaisesRegex(ValueError, "cavity height"):
            calculate_female_rectangular(female_example(gland_id=D(.570)))

    def test_rod_cylinder_interference_rejected_in_depth_mode(self):
        with self.assertRaisesRegex(ValueError, "interference"):
            calculate_female_rectangular(female_example(
                mode="cylinder_and_depth", gland_id=None,
                cylinder_id=D(.575, .001), groove_depth=D(.082),
            ))

    def test_invalid_mode_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            calculate_female_rectangular(female_example(mode="oops"))

    def test_radius_above_groove_depth_rejected(self):
        with self.assertRaisesRegex(ValueError, "radius"):
            calculate_female_rectangular(female_example(
                mode="cylinder_and_depth", gland_id=None,
                cylinder_id=D(.577, .0005), groove_depth=D(.082),
                bottom_radius=D(.083),
            ))


if __name__ == "__main__":
    unittest.main()
