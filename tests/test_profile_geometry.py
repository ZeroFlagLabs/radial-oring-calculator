"""Independent CAD-style checks for Stage 6 profile geometry.

Numerical arc integration checks the *geometric boundary*, not merely the
closed-form circular-segment area formula in production code. All test cases
are generic planar sections, not copied proprietary drawing geometry.
"""
import math
import unittest
from dataclasses import replace

from src.calculations.profile_geometry import (
    SignedDimension as Angle, calculate_profile_area, evaluate_profile_extremes,
)
from src.calculations.rectangular import (
    Dimension as D, MaleRectangularInputs, FemaleRectangularInputs,
    calculate_male_rectangular, calculate_female_rectangular,
)
from src.calculations.dovetail import (
    MaleDovetailInputs, FemaleDovetailInputs,
    calculate_male_dovetail, calculate_female_dovetail,
)


def independently_integrated_area(w, d, c, angle, bottom, entrance):
    """Area under circular-arc/straight-line boundary using Simpson slices.

    Circle centres are found by offsetting the straight walls and horizontal
    planes. Boundary is evaluated at each radial depth and integrated. This
    is independent of production's corner-area correction formula.
    """
    t = math.radians(angle)
    slope = math.tan(t)
    k = 1 / math.cos(t) + math.tan(t)
    yt = entrance * (1 + math.sin(t))
    yb = d - bottom * (1 + math.sin(t))
    topcx, topcy = w/2 + entrance*k, entrance
    botcx, botcy = w/2 + slope*d - bottom*k, d-bottom

    def x(y, part):
        if part == 0:
            return topcx - math.sqrt(max(0.0, entrance**2 - (y-topcy)**2))
        if part == 2:
            return botcx + math.sqrt(max(0.0, bottom**2 - (y-botcy)**2))
        return w/2+slope*y

    def simpson(lo, hi, part, n=12000):
        if hi <= lo: return 0.0
        h=(hi-lo)/n
        total=x(lo,part)+x(hi,part)
        for i in range(1,n):
            total+=(4 if i%2 else 2)*x(lo+h*i,part)
        return total*h/3

    area = 2 * (simpson(0,yt,0) + simpson(yt,yb,1) + simpson(yb,d,2))
    return area + c * (w + 2*entrance*k)


class ProfileGeometryTests(unittest.TestCase):
    def test_zero_fillets_rectangular_is_area_of_rectangle(self):
        r = calculate_profile_area(.146,.0835,.001,0)
        self.assertAlmostEqual(r.area_sq_in,.146*.0845)
        self.assertAlmostEqual(r.opening_width_in,.146)

    def test_zero_fillets_dovetail_is_trapezoid_plus_rectangle(self):
        r=calculate_profile_area(.1735,.1715,.0125,24)
        expected=.1735*.184+.1715**2*math.tan(math.radians(24))
        self.assertAlmostEqual(r.area_sq_in,expected)
        self.assertAlmostEqual(r.area_sq_in,.045019177399466,places=12)

    def test_zero_angle_bottom_radius_matches_square_minus_quarter_circle(self):
        r=calculate_profile_area(.146,.0835,.001,0,.01)
        self.assertAlmostEqual(r.area_sq_in, .146*.0845-2*(1-math.pi/4)*.01**2)

    def test_zero_angle_top_radius_adds_cavity_and_opens_surface(self):
        sharp=calculate_profile_area(.146,.0835,.001,0)
        fillet=calculate_profile_area(.146,.0835,.001,0,0,.005)
        self.assertAlmostEqual(fillet.opening_width_in,.156)
        self.assertAlmostEqual(fillet.area_sq_in-sharp.area_sq_in,
                               2*(1-math.pi/4)*.005**2+.001*.01)

    def test_numerical_arc_boundary_integral_dovetail(self):
        args=(.1735,.1715,.0125,24,.03125,.015)
        result=calculate_profile_area(*args)
        independent=independently_integrated_area(*args)
        self.assertAlmostEqual(result.area_sq_in, independent, places=9)
        self.assertAlmostEqual(result.area_sq_in,.04477738261534794,places=12)
        self.assertAlmostEqual(result.opening_width_in,.2196959489144375,places=12)

    def test_numerical_arc_boundary_integral_taper_both_directions(self):
        for angle in (-5, 0, 1, 12, 24):
            with self.subTest(angle=angle):
                args=(.146,.0835,.001,angle,.010,.005)
                self.assertAlmostEqual(calculate_profile_area(*args).area_sq_in,
                                       independently_integrated_area(*args),places=8)

    def test_signed_angle_changes_area_direction(self):
        a=calculate_profile_area(.146,.0835,.001,-1)
        b=calculate_profile_area(.146,.0835,.001,0)
        c=calculate_profile_area(.146,.0835,.001,1)
        self.assertLess(a.area_sq_in,b.area_sq_in)
        self.assertLess(b.area_sq_in,c.area_sq_in)

    def test_angle_tolerance_can_cross_zero(self):
        v=Angle(0,1)
        self.assertEqual((v.minimum,v.nominal,v.maximum),(-1,0,1))

    def test_reject_overlapping_arcs(self):
        with self.assertRaisesRegex(ValueError,'overlap'):
            calculate_profile_area(.15,.06,.001,20,.035,.025)

    def test_reject_bottom_floor_fillet_collision(self):
        with self.assertRaisesRegex(ValueError,'floor'):
            calculate_profile_area(.05,.1,0,0,.03,0)

    def test_reject_undercut_closing_floor(self):
        with self.assertRaisesRegex(ValueError,'closes'):
            calculate_profile_area(.02,.1,0,-10)

    def test_any_invalid_tolerance_corner_is_rejected(self):
        dims={'w':D(.065,.01),'d':D(.05,.01),'b':D(.02,.015)}
        with self.assertRaisesRegex(ValueError,'tolerance extreme'):
            evaluate_profile_extremes(dims, lambda v: calculate_profile_area(v['w'],v['d'],0,0,v['b']))

    def test_male_female_shared_geometry_and_squeeze(self):
        male=MaleRectangularInputs(
            cylinder_id=D(.669,.001),rod_od=D(.667,.001),groove_depth=D(.0835,.0005),
            gland_width=D(.146,.005),o_ring_id=D(.487,.005),o_ring_section=D(.103,.003),
            bottom_radius=D(.010,.002),entrance_radius=D(.005,.001),
            wall_angle_deg=Angle(1,.5),mode='rod_and_depth')
        female=FemaleRectangularInputs(
            rod_od=D(.667,.001),cylinder_id=D(.669,.001),groove_depth=D(.0835,.0005),
            gland_width=D(.146,.005),o_ring_id=D(.487,.005),o_ring_section=D(.103,.003),
            bottom_radius=D(.010,.002),entrance_radius=D(.005,.001),
            wall_angle_deg=Angle(1,.5),mode='cylinder_and_depth')
        r1=calculate_male_rectangular(male)
        r2=calculate_female_rectangular(female)
        self.assertAlmostEqual(r1.cavity_area_sq_in.nominal,r2.cavity_area_sq_in.nominal)
        self.assertAlmostEqual(r1.cavity_area_sq_in.minimum,r2.cavity_area_sq_in.minimum)
        self.assertAlmostEqual(r1.gland_fill_percent.maximum,r2.gland_fill_percent.maximum)

    def test_direct_and_depth_modes_same_nominal_when_equivalent(self):
        initial=MaleRectangularInputs(
            cylinder_id=D(.669),rod_od=D(.667),groove_depth=D(.0835),
            gland_width=D(.146),o_ring_id=D(.487),o_ring_section=D(.103),
            entrance_radius=D(.005),bottom_radius=D(.010),
            wall_angle_deg=Angle(-1),mode='rod_and_depth')
        r1=calculate_male_rectangular(initial)
        direct=replace(initial,mode='gland_od',groove_depth=None,gland_od=D(.500))
        r2=calculate_male_rectangular(direct)
        self.assertAlmostEqual(r1.cavity_area_sq_in.nominal,r2.cavity_area_sq_in.nominal)

    def test_original_dimension_correlation_in_direct_mode(self):
        # If rod diameter goes up with gland held fixed, its clearance
        # decreases while its depth increases: do NOT independently stack
        # min/max depth with min/max clearance.
        m=MaleDovetailInputs(
            cylinder_id=D(1), gland_od=D(.8),rod_od=D(.9,.01),
            groove_depth=None, mode='gland_od', angle_deg=D(24),
            gland_width=D(.2),o_ring_id=D(.8),o_ring_section=D(.10))
        res=calculate_male_dovetail(m)
        exact=[]
        for rod in (.89,.91):
            depth=(rod-.8)/2
            clearance=(1-rod)/2
            exact.append(calculate_profile_area(.2,depth,clearance,24).area_sq_in)
        self.assertAlmostEqual(res.cavity_area_sq_in.minimum,min(exact))
        self.assertAlmostEqual(res.cavity_area_sq_in.maximum,max(exact))

    def test_dovetail_variation_radius_envelope_gives_expected_order(self):
        m=MaleDovetailInputs(
            cylinder_id=D(11.5,.010),rod_od=D(11.475,.002),
            groove_depth=D(.1715,.0015),gland_width=D(.1735,.0015),
            angle_deg=D(24,.5),bottom_radius=D(.03125,.005),
            entrance_radius=D(.015,.005),o_ring_id=D(11.475,.065),
            o_ring_section=D(.210,.005),mode='rod_and_depth')
        r=calculate_male_dovetail(m)
        self.assertLess(r.cavity_area_sq_in.minimum,r.cavity_area_sq_in.nominal)
        self.assertLess(r.cavity_area_sq_in.nominal,r.cavity_area_sq_in.maximum)
        self.assertGreater(r.gland_fill_percent.maximum,r.gland_fill_percent.nominal)
        self.assertLess(r.gland_fill_percent.minimum,r.gland_fill_percent.nominal)
        self.assertAlmostEqual(r.cavity_area_sq_in.nominal,.04477738261534794)


if __name__=='__main__':
    unittest.main()


class DirectDatumEndpointConventionTests(unittest.TestCase):
    """Stage 7 intentionally searches original +/- tolerance endpoints only."""

    def test_male_direct_uses_only_endpoint_original_diameters(self):
        m=MaleDovetailInputs(
            cylinder_id=D(.9), gland_od=D(.8), rod_od=D(.86,.01),
            mode='gland_od', angle_deg=D(30), gland_width=D(.1),
            entrance_radius=D(.01), o_ring_id=D(.8), o_ring_section=D(.10))
        r=calculate_male_dovetail(m)
        endpoints = [calculate_profile_area(.1,(rod-.8)/2,(.9-rod)/2,30,0,.01).area_sq_in
                     for rod in (.85,.87)]
        self.assertAlmostEqual(r.cavity_area_sq_in.minimum,min(endpoints))
        self.assertAlmostEqual(r.cavity_area_sq_in.maximum,max(endpoints))
        # The interior minimum exists, but is intentionally NOT the reported
        # tolerance endpoint result under the user's Stage 7 convention.
        interior=calculate_profile_area(.1,.03,.02,30,0,.01).area_sq_in
        self.assertLess(interior,r.cavity_area_sq_in.minimum)

    def test_female_direct_uses_only_endpoint_original_diameters(self):
        m=FemaleDovetailInputs(
            rod_od=D(.7), gland_id=D(.92), cylinder_id=D(.86,.01),
            mode='gland_id', angle_deg=D(30), gland_width=D(.1),
            entrance_radius=D(.01), o_ring_id=D(.7), o_ring_section=D(.10))
        r=calculate_female_dovetail(m)
        endpoints = [calculate_profile_area(.1,(.92-cyl)/2,(cyl-.7)/2,30,0,.01).area_sq_in
                     for cyl in (.85,.87)]
        self.assertAlmostEqual(r.cavity_area_sq_in.minimum,min(endpoints))
        self.assertAlmostEqual(r.cavity_area_sq_in.maximum,max(endpoints))
        interior=calculate_profile_area(.1,.03,.08,30,0,.01).area_sq_in
        self.assertLess(interior,r.cavity_area_sq_in.minimum)
