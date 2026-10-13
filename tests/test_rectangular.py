"""Pure-Python regression tests. No Qt dependency needed."""

import math
import unittest

from src.calculations.rectangular import (
    Dimension as D, MaleRectangularInputs, calculate_male_rectangular,
)


def example(**overrides):
    # Synthetic values, not copied from employer-specific groove drawings.
    values = dict(
        cylinder_id=D(.750, .001),
        gland_width=D(.145, .003),
        o_ring_id=D(.565, .005),
        o_ring_section=D(.103, .003),
        bottom_radius=D(0),
        mode="gland_od",
        gland_od=D(.584, .001),
    )
    values.update(overrides)
    return MaleRectangularInputs(**values)


class CalculationTests(unittest.TestCase):
    def test_nominal_squeeze(self):
        r = calculate_male_rectangular(example())
        self.assertAlmostEqual(r.radial_cavity_height.nominal, .083)
        self.assertAlmostEqual(r.squeeze_in.nominal, .020)
        self.assertAlmostEqual(r.squeeze_percent.nominal, 100 * (.020 / .103))

    def test_worst_case_squeeze(self):
        r = calculate_male_rectangular(example())
        self.assertAlmostEqual(r.radial_cavity_height.minimum, .082)
        self.assertAlmostEqual(r.radial_cavity_height.maximum, .084)
        self.assertAlmostEqual(r.squeeze_in.minimum, .016)
        self.assertAlmostEqual(r.squeeze_in.maximum, .024)
        self.assertAlmostEqual(r.squeeze_percent.minimum, 100 * (.016 / .100))
        self.assertAlmostEqual(r.squeeze_percent.maximum, 100 * (.024 / .106))

    def test_stretch_uses_id_tolerance(self):
        r = calculate_male_rectangular(example())
        self.assertAlmostEqual(r.stretch_percent.minimum, 100 * (.583 / .570 - 1))
        self.assertAlmostEqual(r.stretch_percent.nominal, 100 * (.584 / .565 - 1))
        self.assertAlmostEqual(r.stretch_percent.maximum, 100 * (.585 / .560 - 1))

    def test_fill_sharp_corners(self):
        r = calculate_male_rectangular(example())
        self.assertAlmostEqual(
            r.gland_fill_percent.nominal,
            100 * (math.pi * .103**2 / 4) / (.145 * .083),
        )

    def test_equal_direct_and_depth_mode(self):
        direct = calculate_male_rectangular(example())
        derived = calculate_male_rectangular(example(
            mode="rod_and_depth", gland_od=None,
            rod_od=D(.748, 0), groove_depth=D(.082, .0005),
        ))
        self.assertAlmostEqual(derived.gland_od.nominal, direct.gland_od.nominal)
        self.assertAlmostEqual(derived.gland_od.minimum, direct.gland_od.minimum)
        self.assertAlmostEqual(derived.gland_od.maximum, direct.gland_od.maximum)
        self.assertAlmostEqual(derived.squeeze_percent.nominal, direct.squeeze_percent.nominal)

    def test_depth_tolerance_stacks_doubled(self):
        r = calculate_male_rectangular(example(
            mode="rod_and_depth", gland_od=None,
            rod_od=D(.748, .001), groove_depth=D(.082, .001),
        ))
        self.assertAlmostEqual(r.gland_od.minimum, .581)
        self.assertAlmostEqual(r.gland_od.nominal, .584)
        self.assertAlmostEqual(r.gland_od.maximum, .587)

    def test_negative_stretch_is_reported(self):
        r = calculate_male_rectangular(example(o_ring_id=D(.600, 0)))
        self.assertLess(r.stretch_percent.maximum, 0)

    def test_bottom_radii_increase_fill(self):
        sharp = calculate_male_rectangular(example())
        rounded = calculate_male_rectangular(example(bottom_radius=D(.010, 0)))
        self.assertGreater(rounded.gland_fill_percent.nominal, sharp.gland_fill_percent.nominal)
        removed_area = (2 - math.pi / 2) * .010**2
        self.assertAlmostEqual(rounded.cavity_area_sq_in.nominal,
                               sharp.cavity_area_sq_in.nominal - removed_area)

    def test_max_radius_and_min_width_produce_max_fill(self):
        r = calculate_male_rectangular(example(bottom_radius=D(.010, .002)))
        self.assertGreater(r.gland_fill_percent.maximum, r.gland_fill_percent.nominal)
        self.assertLess(r.gland_fill_percent.minimum, r.gland_fill_percent.nominal)

    def test_invalid_tolerance_rejected(self):
        with self.assertRaisesRegex(ValueError, "negative"):
            D(.001, .002)

    def test_negative_radial_height_rejected(self):
        with self.assertRaisesRegex(ValueError, "cavity height"):
            calculate_male_rectangular(example(gland_od=D(.750, .003)))

    def test_fillet_too_large_rejected(self):
        with self.assertRaisesRegex(ValueError, "fillets"):
            calculate_male_rectangular(example(bottom_radius=D(.090)))

    def test_rod_cylinder_interference_rejected(self):
        with self.assertRaisesRegex(ValueError, "interference"):
            calculate_male_rectangular(example(mode="rod_and_depth", gland_od=None,
                                               rod_od=D(.750, .002), groove_depth=D(.083)))

    def test_zero_cs_rejected(self):
        with self.assertRaisesRegex(ValueError, "cross-section"):
            calculate_male_rectangular(example(o_ring_section=D(0)))


if __name__ == "__main__":
    unittest.main()
