"""Numerical-only v2.0 simplified squeeze and gland-fill method regression tests.

Detailed remains the default and must remain bit-for-bit equivalent to the
existing installed-condition engine.  No UI or reporting change in this stage.
"""
import math
import unittest
from dataclasses import replace
from src.calculations.rectangular import Dimension as D
from src.calculations.rectangular import MaleRectangularInputs, FemaleRectangularInputs
from src.calculations.dovetail import MaleDovetailInputs, FemaleDovetailInputs
from src.calculations.installed import calculate_installed, installed_result_traces
from src.calculations.criteria import screen_rectangular


def male_rect():
    return MaleRectangularInputs(
        cylinder_id=D(.669,.001), rod_od=D(.667,.001),
        groove_depth=D(.0835,.0005), gland_width=D(.146,.005),
        o_ring_id=D(.487,.005), o_ring_section=D(.103,.003),
        mode='rod_and_depth')


def female_rect():
    return FemaleRectangularInputs(
        rod_od=D(.684,.001), cylinder_id=D(.687,.001),
        groove_depth=D(.0835,.0005), gland_width=D(.146,.005),
        o_ring_id=D(.674,.009), o_ring_section=D(.103,.003),
        mode='cylinder_and_depth')


def male_dovetail():
    return MaleDovetailInputs(
        cylinder_id=D(11.500,.010), rod_od=D(11.475,.002),
        groove_depth=D(.1715,.0015), gland_width=D(.1735,.0015),
        angle_deg=D(24,.5), o_ring_id=D(11.475,.065),
        o_ring_section=D(.210,.005), mode='rod_and_depth',
        bottom_radius=D(.03125), entrance_radius=D(.015))


def female_dovetail():
    return FemaleDovetailInputs(
        rod_od=D(11.475,.002), cylinder_id=D(11.500,.010),
        groove_depth=D(.1715,.0015), gland_width=D(.1735,.0015),
        angle_deg=D(24,.5), o_ring_id=D(11.475,.065),
        o_ring_section=D(.210,.005), mode='cylinder_and_depth')


class SimplifiedMethodTests(unittest.TestCase):
    def test_current_default_is_explicit_detailed(self):
        for inp in (male_rect(), female_rect(), male_dovetail(), female_dovetail()):
            implicit = calculate_installed(inp)
            explicit = calculate_installed(inp, method='detailed')
            self.assertEqual(implicit, explicit)
            self.assertEqual(implicit.method, 'detailed')

    def test_independent_nominal_male_squeeze_formula(self):
        inp = male_rect()
        detailed = calculate_installed(inp)
        simple = calculate_installed(inp, method='simplified')
        g = .667 - 2*.0835
        h = (.669-g)/2
        expected_in = .103-h
        expected_pct = 100*expected_in/.103
        self.assertAlmostEqual(expected_in,.0185,places=12)
        self.assertAlmostEqual(simple.results.squeeze_in.nominal,expected_in,places=12)
        self.assertAlmostEqual(simple.results.squeeze_percent.nominal,expected_pct,places=12)
        self.assertAlmostEqual(expected_pct,17.96116504854369,places=10)
        self.assertLess(detailed.results.squeeze_percent.nominal,expected_pct)
        self.assertEqual(simple.method,'simplified')
        witness = simple.cases[('Squeeze','Nominal')]
        self.assertEqual(witness.compression_section,.103)
        self.assertAlmostEqual(witness.squeeze_pct,expected_pct,places=12)

    def test_unchanged_fit_and_geometry_for_all_types(self):
        for inp in (male_rect(), female_rect(), male_dovetail(), female_dovetail()):
            with self.subTest(config=type(inp).__name__):
                detailed=calculate_installed(inp)
                simplified=calculate_installed(inp,method='simplified')
                for attr in ('stretch_percent',
                             'cavity_area_sq_in','surface_opening_width_in',
                             'groove_area_sq_in','radial_cavity_height'):
                    self.assertEqual(getattr(detailed.results,attr),
                                     getattr(simplified.results,attr),attr)
                for condition in ('Minimum','Nominal','Maximum'):
                    original=detailed.cases[('Fit',condition)]
                    alternative=simplified.cases[('Fit',condition)]
                    self.assertEqual(original.values,alternative.values)
                    self.assertEqual(original.install_fit_pct,alternative.install_fit_pct)
                    self.assertEqual(original.cavity_area,alternative.cavity_area)
                female=isinstance(inp,(FemaleRectangularInputs,FemaleDovetailInputs))
                if female:
                    self.assertEqual(detailed.results.gland_fill_percent,
                                     simplified.results.gland_fill_percent)
                for app in ('static','dynamic'):
                    screening_d=screen_rectangular(detailed.results,app,female=female)
                    screening_s=screen_rectangular(simplified.results,app,female=female)
                    self.assertEqual(screening_d.checks[1],screening_s.checks[1])
                    if female:
                        self.assertEqual(screening_d.checks[2],screening_s.checks[2])

    def test_mathcad_reference_male_gland_fill_full_tolerance_range(self):
        # Independent free-state area / current validated sharp-gland area.
        # The original worksheet gives 60.5 / 67.5 / 75.4% rounded.
        inp=male_rect()
        evaluation=calculate_installed(inp,method='simplified')
        values=evaluation.results.gland_fill_percent
        min_area=(.146+.005)*((.669+.001)-((.667-.001)-2*(.0835+.0005)))/2
        nom_area=.146*(.669-(.667-2*.0835))/2
        max_area=(.146-.005)*((.669-.001)-((.667+.001)-2*(.0835-.0005)))/2
        expected_min=100*math.pi*(.103-.003)**2/(4*min_area)
        expected_nom=100*math.pi*.103**2/(4*nom_area)
        expected_max=100*math.pi*(.103+.003)**2/(4*max_area)
        self.assertAlmostEqual(values.minimum,expected_min,places=10)
        self.assertAlmostEqual(values.nominal,expected_nom,places=10)
        self.assertAlmostEqual(values.maximum,expected_max,places=10)
        self.assertAlmostEqual(values.minimum,60.5,delta=.06)
        self.assertAlmostEqual(values.nominal,67.5,delta=.06)
        self.assertAlmostEqual(values.maximum,75.4,delta=.06)
        detailed=calculate_installed(inp)
        self.assertNotEqual(detailed.results.gland_fill_percent,values)
        self.assertFalse(screen_rectangular(detailed.results,'static').checks[2].within_limits)
        self.assertTrue(screen_rectangular(evaluation.results,'static').checks[2].within_limits)

    def test_free_material_area_preserves_angled_and_radiused_groove(self):
        for inp in (male_rect(),male_dovetail(),
                    replace(male_rect(),mode='gland_od',groove_depth=None,
                            gland_od=D(.500,.002))):
            with self.subTest(config=type(inp).__name__,mode=inp.mode):
                detailed=calculate_installed(inp)
                simplified=calculate_installed(inp,method='simplified')
                self.assertEqual(detailed.results.cavity_area_sq_in,
                                 simplified.results.cavity_area_sq_in)
                for condition,attr in (('Minimum','minimum'),('Nominal','nominal'),
                                       ('Maximum','maximum')):
                    witness=simplified.cases[('Gland fill',condition)]
                    free_section=dict(witness.values)['section']
                    free_area=math.pi*free_section**2/4
                    expected=100*free_area/witness.cavity_area
                    self.assertAlmostEqual(witness.equivalent_area_section,free_section)
                    self.assertAlmostEqual(witness.gland_fill_pct,expected,places=11)
                    self.assertAlmostEqual(getattr(simplified.results.gland_fill_percent,attr),
                                           expected,places=11)

    def test_female_gland_fill_unchanged_with_correct_od_interference(self):
        for inp in (female_rect(),female_dovetail()):
            detailed=calculate_installed(inp)
            simplified=calculate_installed(inp,method='simplified')
            self.assertEqual(detailed.results,simplified.results)
            self.assertEqual(detailed.cases,simplified.cases)
            self.assertEqual(detailed.results.stretch_percent,
                             simplified.results.stretch_percent)

    def test_simplified_trace_identifies_free_state_fill_method(self):
        evaluation=calculate_installed(male_rect(),method='simplified')
        trace=installed_result_traces(evaluation)[('Gland fill','Nominal')]
        self.assertIn('free-state O-ring material area',trace.explanation)
        self.assertIn('Material section used for fill',dict(trace.inputs))
        self.assertNotIn('Area-equivalent section',dict(trace.inputs))

    def test_female_squeeze_identical_for_both_methods(self):
        for inp in (female_rect(),female_dovetail()):
            detailed=calculate_installed(inp)
            simple=calculate_installed(inp,method='simplified')
            self.assertEqual(detailed.results.squeeze_in,simple.results.squeeze_in)
            self.assertEqual(detailed.results.squeeze_percent,simple.results.squeeze_percent)
            for condition in ('Minimum','Nominal','Maximum'):
                self.assertEqual(detailed.cases[('Squeeze',condition)],
                                 simple.cases[('Squeeze',condition)])

    def test_male_direct_od_and_dovetail_preserve_formula(self):
        rect=replace(male_rect(), mode='gland_od', groove_depth=None,
                     gland_od=D(.500,.002))
        dovetail=male_dovetail()
        for inp in (rect,dovetail):
            simple=calculate_installed(inp,method='simplified')
            nominal=simple.cases[('Squeeze','Nominal')]
            values=dict(nominal.values)
            gland=values.get('gland',values.get('rod',0)-2*values.get('depth',0))
            h=(values['cylinder']-gland)/2
            free=values['section']
            self.assertAlmostEqual(simple.results.squeeze_in.nominal,free-h)
            self.assertAlmostEqual(simple.results.squeeze_percent.nominal,
                                   100*(free-h)/free)

    def test_no_positive_stretch_yields_same_male_squeeze(self):
        inp=MaleRectangularInputs(
            cylinder_id=D(.669),rod_od=D(.667),gland_od=D(.500),
            gland_width=D(.146),o_ring_id=D(.510),
            o_ring_section=D(.103),mode='gland_od')
        detailed=calculate_installed(inp)
        simple=calculate_installed(inp,method='simplified')
        self.assertEqual(detailed.results.squeeze_in,simple.results.squeeze_in)
        self.assertEqual(detailed.results.squeeze_percent,simple.results.squeeze_percent)

    def test_no_three_percent_transition_for_simplified(self):
        # Vary ONLY ID through the Parker 3% transition: simplified squeeze
        # has no ring-ID dependence, but fit and fill still do.
        inp=MaleRectangularInputs(
            cylinder_id=D(.681),rod_od=D(.667),gland_od=D(.515),
            gland_width=D(.146),o_ring_id=D(.500,.0005),
            o_ring_section=D(.103),mode='gland_od')
        detailed=calculate_installed(inp)
        simple=calculate_installed(inp,method='simplified')
        expected=100*(.103-(.681-.515)/2)/.103
        self.assertAlmostEqual(simple.results.squeeze_percent.minimum,expected)
        self.assertAlmostEqual(simple.results.squeeze_percent.nominal,expected)
        self.assertAlmostEqual(simple.results.squeeze_percent.maximum,expected)
        self.assertGreater(detailed.results.squeeze_percent.maximum,
                           detailed.results.squeeze_percent.nominal)
        self.assertEqual(detailed.results.stretch_percent,simple.results.stretch_percent)
        self.assertGreater(simple.results.gland_fill_percent.nominal,
                           detailed.results.gland_fill_percent.nominal)
        for condition in ('Minimum','Maximum'):
            ring=dict(simple.cases[('Squeeze',condition)].values)['ring_id']
            self.assertIn(ring,(inp.o_ring_id.minimum,inp.o_ring_id.maximum))
        trace=installed_result_traces(simple)[('Squeeze','Nominal')]
        self.assertIn('Simplified:',trace.explanation)
        self.assertIn('Compression section used for squeeze',dict(trace.inputs))
        self.assertNotIn('Installed compression section',dict(trace.inputs))
        self.assertNotIn('3% Parker stretch transition',trace.explanation)

    def test_simplified_stretch_outside_empirical_curve_is_still_screened(self):
        # This is not a recommendation to use a 25%+ stretched seal.
        # The simplified squeeze formula has no Parker 25% domain limit;
        # the unchanged 0-5% stretch screening must still flag REVIEW.
        inp=MaleRectangularInputs(
            cylinder_id=D(.681),rod_od=D(.667),gland_od=D(.620),
            gland_width=D(.146),o_ring_id=D(.480),
            o_ring_section=D(.103),mode='gland_od')
        with self.assertRaisesRegex(ValueError,'25%'):
            calculate_installed(inp,method='detailed')
        evaluation=calculate_installed(inp,method='simplified')
        self.assertFalse(screen_rectangular(evaluation.results,'static').checks[1].within_limits)

    def test_bad_method_rejected(self):
        with self.assertRaisesRegex(ValueError,'Calculation method'):
            calculate_installed(male_rect(),method='mathcad')


if __name__=='__main__':
    unittest.main()
