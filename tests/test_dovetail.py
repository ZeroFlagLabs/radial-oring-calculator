"""Independent geometric regression tests for symmetric dovetail glands.

The isolated worksheets remain local calculation references, not ground-truth
for the dovetail area: its original tapered area extends above the groove.
"""
import unittest
from math import pi, tan, radians
from src.calculations.rectangular import Dimension as D
from src.calculations.dovetail import (
    MaleDovetailInputs, FemaleDovetailInputs,
    calculate_male_dovetail, calculate_female_dovetail,
)
from src.calculations.criteria import screen_rectangular


def male(**changes):
    args = dict(
        cylinder_id=D(11.500, .010), rod_od=D(11.475, .002),
        groove_depth=D(.1715, .0015), gland_width=D(.1735, .0015),
        angle_deg=D(24, .5), o_ring_id=D(11.475, .065),
        o_ring_section=D(.210, .005), mode='rod_and_depth',
    )
    args.update(changes)
    return MaleDovetailInputs(**args)


def female(**changes):
    args = dict(
        rod_od=D(11.475, .002), cylinder_id=D(11.500, .010),
        groove_depth=D(.1715, .0015), gland_width=D(.1735, .0015),
        angle_deg=D(24, .5), o_ring_id=D(11.475, .065),
        o_ring_section=D(.210, .005), mode='cylinder_and_depth',
    )
    args.update(changes)
    return FemaleDovetailInputs(**args)


class DovetailTests(unittest.TestCase):
    def test_male_matches_new_mathcad_page_two(self):
        r = calculate_male_dovetail(male())
        self.assertAlmostEqual(r.gland_od.nominal, 11.132)
        self.assertAlmostEqual(r.radial_cavity_height.nominal, .184)
        self.assertAlmostEqual(r.squeeze_in.minimum, .0135)
        self.assertAlmostEqual(r.squeeze_in.nominal, .026)
        self.assertAlmostEqual(r.squeeze_in.maximum, .0385)
        self.assertAlmostEqual(r.squeeze_percent.minimum, 6.58536585, places=5)
        self.assertAlmostEqual(r.squeeze_percent.nominal, 12.38095238, places=5)
        self.assertAlmostEqual(r.squeeze_percent.maximum, 17.90697674, places=5)
        self.assertAlmostEqual(r.gland_fill_percent.minimum, 70.0000128213)
        self.assertAlmostEqual(r.gland_fill_percent.nominal, 76.9362325271)
        self.assertAlmostEqual(r.gland_fill_percent.maximum, 84.5796394523)

    def test_female_matches_new_mathcad_page_four(self):
        r = calculate_female_dovetail(female())
        self.assertAlmostEqual(r.gland_id.nominal, 11.843)
        self.assertAlmostEqual(r.radial_cavity_height.nominal, .184)
        self.assertAlmostEqual(r.gland_fill_percent.minimum, 70.0000128213)
        self.assertAlmostEqual(r.gland_fill_percent.nominal, 76.9362325271)
        self.assertAlmostEqual(r.gland_fill_percent.maximum, 84.5796394523)
        self.assertAlmostEqual(r.stretch_percent.nominal, 0)

    def test_male_direct_gland_od_nominal_agrees_with_depth(self):
        depth = calculate_male_dovetail(male())
        direct = calculate_male_dovetail(male(
            mode='gland_od', groove_depth=None, gland_od=D(11.132, .005),
        ))
        self.assertAlmostEqual(direct.gland_fill_percent.nominal, depth.gland_fill_percent.nominal)
        self.assertAlmostEqual(direct.squeeze_percent.nominal, depth.squeeze_percent.nominal)
        # Independent tolerance stacks in diameter mode need not give same
        # worst-case fill as depth mode, where OD and depth are correlated.

    def test_female_direct_gland_id_nominal_agrees_with_depth(self):
        depth = calculate_female_dovetail(female())
        direct = calculate_female_dovetail(female(
            mode='gland_id', groove_depth=None, gland_id=D(11.843, .013),
        ))
        self.assertAlmostEqual(direct.gland_fill_percent.nominal, depth.gland_fill_percent.nominal)
        self.assertAlmostEqual(direct.squeeze_percent.nominal, depth.squeeze_percent.nominal)

    def test_sharp_trapezoid_area_independent_polygon_and_clearance(self):
        # The shoelace method uses actual corner coordinates, not the
        # analytical formula implemented by the production code.
        r = calculate_male_dovetail(male())
        w, d, theta = .1735, .1715, radians(24)
        spread = d * tan(theta)
        # At z=0 the width is w; at z=d it is w+2*spread.
        poly = [(0, 0), (w, 0), (w+spread, d), (-spread, d)]
        twice_area = sum(poly[i][0] * poly[(i+1)%4][1] -
                         poly[(i+1)%4][0] * poly[i][1]
                         for i in range(4))
        area_groove = abs(twice_area) / 2
        clear_above = (.500 - .475) / 2
        expected = area_groove + clear_above * w
        self.assertAlmostEqual(r.cavity_area_sq_in.nominal, expected)
        self.assertAlmostEqual(expected, .04501917739946599)

    def test_mathcad_overstates_cavity_when_rod_clearance_is_nonzero(self):
        r = calculate_male_dovetail(male())
        mathcad = .184 * (.1735 + .1715 * tan(radians(24)))
        extra_area = (.184 - .1715) * .1715 * tan(radians(24))
        self.assertAlmostEqual(mathcad - r.cavity_area_sq_in.nominal, extra_area)
        self.assertGreater(mathcad, r.cavity_area_sq_in.nominal)

    def test_dovetail_reduces_to_trapezoid_without_rod_clearance(self):
        # Here cylinder ID == rod OD at nominal, hence h == d.
        r = calculate_male_dovetail(male(cylinder_id=D(11.475,0),
                                          rod_od=D(11.475,0),
                                          groove_depth=D(.1715,0),
                                          gland_width=D(.1735,0),
                                          angle_deg=D(24,0)))
        trapezoid = .1715 * (.1735 + .1715 * tan(radians(24)))
        self.assertAlmostEqual(r.cavity_area_sq_in.nominal, trapezoid)

    def test_zero_angle_is_same_as_sharp_rectangular(self):
        r = calculate_male_dovetail(male(angle_deg=D(0,0)))
        h = r.radial_cavity_height.nominal
        expected = 100 * (pi * .210**2 / 4) / (h * .1735)
        self.assertAlmostEqual(r.gland_fill_percent.nominal, expected)

    def test_invalid_angle_rejected(self):
        with self.assertRaisesRegex(ValueError, 'angle'):
            calculate_male_dovetail(male(angle_deg=D(89,2)))

    def test_nonpositive_physical_depth_rejected(self):
        with self.assertRaisesRegex(ValueError, 'depth'):
            calculate_male_dovetail(male(
                mode='gland_od', groove_depth=None, gland_od=D(11.480),
            ))
        with self.assertRaisesRegex(ValueError, 'depth'):
            calculate_female_dovetail(female(
                mode='gland_id', groove_depth=None, gland_id=D(11.490),
            ))

    def test_missing_reference_diameter_rejected(self):
        with self.assertRaisesRegex(ValueError, 'rod OD'):
            calculate_male_dovetail(male(
                mode='gland_od', groove_depth=None, rod_od=None, gland_od=D(11.132),
            ))
        with self.assertRaisesRegex(ValueError, 'cylinder ID'):
            calculate_female_dovetail(female(
                mode='gland_id', groove_depth=None, cylinder_id=None,
                gland_id=D(11.843),
            ))

    def test_dynamic_and_static_same_geometry_different_screening(self):
        r = calculate_male_dovetail(male())
        s = screen_rectangular(r, 'static')
        d = screen_rectangular(r, 'dynamic')
        self.assertIs(r, r)
        self.assertEqual(s.checks[1:], d.checks[1:])
        self.assertTrue(s.checks[0].within_limits)
        self.assertFalse(d.checks[0].within_limits)

    def test_sensitivity_angle_increases_area_and_reduces_fill(self):
        a = calculate_male_dovetail(male(angle_deg=D(20)))
        b = calculate_male_dovetail(male(angle_deg=D(30)))
        self.assertGreater(b.cavity_area_sq_in.nominal, a.cavity_area_sq_in.nominal)
        self.assertLess(b.gland_fill_percent.nominal, a.gland_fill_percent.nominal)


if __name__ == '__main__':
    unittest.main()
