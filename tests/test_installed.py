"""Stage 8 independent numerical checks for installed-fit models."""
import math
import unittest
from dataclasses import replace
from src.calculations.installed import (
    calculate_installed, observed_compression_section,
    volume_equivalent_section, installed_result_traces,
)
from src.calculations.rectangular import (
    Dimension as D, MaleRectangularInputs, FemaleRectangularInputs,
    calculate_male_rectangular, calculate_female_rectangular,
)
from src.calculations.criteria import screen_rectangular
from src.calculations.dovetail import MaleDovetailInputs


def male_case(id_val=.487,cs=.103):
    return MaleRectangularInputs(cylinder_id=D(.669,.001),gland_width=D(.1425,.0025),
        o_ring_id=D(id_val,.005),o_ring_section=D(cs,.003), mode='rod_and_depth',
        rod_od=D(.667,.001),groove_depth=D(.082,.0005))


def female_case():
    return FemaleRectangularInputs(rod_od=D(.684,.001),gland_width=D(.1425,.0025),
        o_ring_id=D(.674,.009),o_ring_section=D(.103,.003),
        mode='gland_id',gland_id=D(.851,.001),cylinder_id=D(.687,.0005))


class InstalledTests(unittest.TestCase):
    def test_observed_compression_section_3_percent(self):
        # Parker figure 3-3: polynomial returns approximately 2.476% reduction at 3%.
        x=3.0
        reduction=-.005+1.19*x-.19*x*x-.001*x**3+.008*x**4
        self.assertAlmostEqual(observed_compression_section(.103,x),.103*(1-reduction/100),12)
        self.assertAlmostEqual(observed_compression_section(.103,0),.103)

    def test_volume_conservation_middle_diameter(self):
        free_id=.487;cs=.103;installed=.503
        reduced=volume_equivalent_section(free_id,cs,installed)
        self.assertLess(reduced,cs)
        self.assertAlmostEqual(reduced**2*(installed+reduced),cs**2*(free_id+cs),13)
        self.assertEqual(volume_equivalent_section(free_id,cs,free_id),cs)

    def test_male_adjustment_preserves_cad_geometry(self):
        raw=calculate_male_rectangular(male_case())
        calc=calculate_installed(male_case()).results
        self.assertEqual(raw.cavity_area_sq_in,calc.cavity_area_sq_in)
        self.assertEqual(raw.gland_od,calc.gland_od)
        self.assertAlmostEqual(raw.stretch_percent.nominal,calc.stretch_percent.nominal)
        self.assertLess(calc.squeeze_percent.nominal,raw.squeeze_percent.nominal)
        self.assertLess(calc.gland_fill_percent.nominal,raw.gland_fill_percent.nominal)

    def test_single_nominal_case_witness_formula(self):
        inp=replace(male_case(),cylinder_id=D(.669),rod_od=D(.667),
                    groove_depth=D(.082),gland_width=D(.1425),
                    o_ring_id=D(.487),o_ring_section=D(.103))
        calc=calculate_installed(inp)
        r=calc.results
        gland=.667-2*.082
        h=(.669-gland)/2
        st=100*(gland/.487-1)
        expected_section=observed_compression_section(.103,st)
        equivalent=volume_equivalent_section(.487,.103,gland)
        self.assertAlmostEqual(r.squeeze_percent.nominal,100*(expected_section-h)/expected_section)
        self.assertAlmostEqual(r.gland_fill_percent.nominal,100*math.pi*equivalent**2/(4*(.1425*h)))
        witness=calc.cases[('Squeeze','Nominal')]
        self.assertAlmostEqual(witness.compression_section,expected_section)

    def test_endpoint_witness_is_reproducible(self):
        evaluation=calculate_installed(male_case())
        for label,attribute in [('Minimum','minimum'),('Nominal','nominal'),('Maximum','maximum')]:
            for metric,field in [('Squeeze','squeeze_percent'),('Fit','stretch_percent'),('Gland fill','gland_fill_percent')]:
                witness=evaluation.cases[(metric,label)]
                internal=('squeeze_pct' if metric=='Squeeze' else 'install_fit_pct' if metric=='Fit' else 'gland_fill_pct')
                self.assertAlmostEqual(getattr(witness,internal),getattr(getattr(evaluation.results,field),attribute))

    def test_female_interference_is_based_on_ring_od_and_gland_id(self):
        e=calculate_installed(female_case())
        self.assertAlmostEqual(e.results.stretch_percent.nominal,100*(.674+2*.103-.851)/(.674+2*.103))
        self.assertLess(e.results.stretch_percent.minimum,e.results.stretch_percent.nominal)
        self.assertGreater(e.results.stretch_percent.maximum,e.results.stretch_percent.nominal)
        self.assertAlmostEqual(e.results.squeeze_percent.nominal,calculate_female_rectangular(female_case()).squeeze_percent.nominal,places=12)
        self.assertFalse(screen_rectangular(e.results,'static',female=True).checks[1].within_limits)

    def test_female_2_percent_screening_limit_is_inclusive(self):
        data=calculate_installed(female_case()).results
        modified=replace(data,stretch_percent=replace(data.stretch_percent,minimum=0,nominal=1,maximum=2))
        self.assertTrue(screen_rectangular(modified,'static',female=True).checks[1].within_limits)
        modified=replace(data,stretch_percent=replace(data.stretch_percent,minimum=0,nominal=1,maximum=2.01))
        self.assertFalse(screen_rectangular(modified,'static',female=True).checks[1].within_limits)

    def test_installed_traces_show_exact_updated_results(self):
        for data,metric in [(male_case(),'ID stretch'),(female_case(),'OD interference')]:
            evaluation=calculate_installed(data)
            traces=installed_result_traces(evaluation)
            self.assertEqual(len(traces),9)
            self.assertAlmostEqual(traces[(metric,'Maximum')].value,evaluation.results.stretch_percent.maximum)
            self.assertIn('Installed compression section',dict(traces[('Squeeze','Nominal')].inputs))

    def test_transition_crossed_by_ring_id_tolerance(self):
        """Regression: nominal must not exceed the maximum squeeze."""
        inp = MaleRectangularInputs(
            cylinder_id=D(.681), rod_od=D(.667), gland_od=D(.515),
            gland_width=D(.146), o_ring_id=D(.500,.0005),
            o_ring_section=D(.103), mode='gland_od')
        evaluation = calculate_installed(inp)
        r = evaluation.results.squeeze_percent
        self.assertLessEqual(r.minimum, r.nominal)
        self.assertLessEqual(r.nominal, r.maximum)
        self.assertAlmostEqual(r.minimum,17.37159645641618, places=7)
        self.assertAlmostEqual(r.nominal,17.37159645641618, places=7)
        self.assertAlmostEqual(r.maximum,17.530068837181982, places=7)
        high = evaluation.cases[('Squeeze','Maximum')]
        self.assertGreater(high.install_fit_pct,3.0)
        self.assertLess(high.install_fit_pct,3.000001)
        self.assertGreater(dict(high.values)['ring_id'], inp.o_ring_id.minimum)
        self.assertLess(dict(high.values)['ring_id'], inp.o_ring_id.maximum)
        # Fit and gland fill still use their original endpoints, unchanged.
        self.assertAlmostEqual(evaluation.results.stretch_percent.minimum,2.897102897102921)
        self.assertAlmostEqual(evaluation.results.stretch_percent.maximum,3.103103103103111)
        self.assertAlmostEqual(evaluation.results.gland_fill_percent.nominal,67.217058670,places=6)

    def test_transition_crossed_by_groove_depth_tolerance(self):
        inp = MaleRectangularInputs(
            cylinder_id=D(.681), rod_od=D(.667),groove_depth=D(.076,.0006),
            gland_width=D(.146),o_ring_id=D(.5),o_ring_section=D(.103),
            mode='rod_and_depth')
        r = calculate_installed(inp).results.squeeze_percent
        self.assertAlmostEqual(r.minimum,16.945244764054213,places=7)
        self.assertAlmostEqual(r.nominal,17.37159645641618,places=7)
        self.assertAlmostEqual(r.maximum,18.013204944067382,places=7)

    def test_transition_crossed_by_gland_od_tolerance(self):
        inp = MaleRectangularInputs(
            cylinder_id=D(.681),rod_od=D(.667),gland_od=D(.515,.001),
            gland_width=D(.146),o_ring_id=D(.5),o_ring_section=D(.103),
            mode='gland_od')
        e=calculate_installed(inp)
        r=e.results.squeeze_percent
        self.assertLessEqual(r.minimum,r.nominal)
        self.assertLessEqual(r.nominal,r.maximum)
        for label in ('Minimum','Maximum'):
            witness = e.cases[('Squeeze',label)]
            self.assertGreaterEqual(dict(witness.values)['gland'],.514)
            self.assertLessEqual(dict(witness.values)['gland'],.516)

    def test_transition_exact_three_stable_and_both_sides(self):
        section=.103
        first=observed_compression_section(section,3.0)
        # 1.03 / 1.0 is mathematically exactly 3%; floating-point
        # representation must not choose the upper branch accidentally.
        self.assertEqual(observed_compression_section(section,100*(1.03/1.0-1)),first)
        below=observed_compression_section(section,3.0-1e-7)
        above=observed_compression_section(section,3.0+1e-7)
        self.assertLess(first,above)
        self.assertAlmostEqual(first,below,places=9)
        self.assertGreater(above,first)

    def test_transition_no_change_outside_three_percent(self):
        for ring_id in (.502,.497):
            inp=MaleRectangularInputs(
                cylinder_id=D(.681),rod_od=D(.667),gland_od=D(.515),
                gland_width=D(.146),o_ring_id=D(ring_id),o_ring_section=D(.103),
                mode='gland_od')
            e=calculate_installed(inp)
            self.assertAlmostEqual(e.results.squeeze_percent.minimum,e.results.squeeze_percent.nominal)
            self.assertAlmostEqual(e.results.squeeze_percent.maximum,e.results.squeeze_percent.nominal)
            stretch=100*(.515/ring_id-1)
            section=observed_compression_section(.103,stretch)
            expected=100*(section-.083)/section
            self.assertAlmostEqual(e.results.squeeze_percent.nominal,expected,places=10)

    def test_boundary_squeeze_inspector_explains_correct_branch(self):
        from src.ui.inspection_data import explain_case
        inp=MaleRectangularInputs(
            cylinder_id=D(.681),rod_od=D(.667),gland_od=D(.515),
            gland_width=D(.146),o_ring_id=D(.500,.0005),
            o_ring_section=D(.103),mode='gland_od')
        e=calculate_installed(inp)
        _, _, steps=explain_case(e,'Squeeze','Maximum',entered=inp)
        self.assertIn('0.56 + 0.59s',next(x.symbolic for x in steps if x.title=='Installed-section reduction'))
        self.assertIn('branch transition',next(x.note for x in steps if x.title=='Installed-section reduction'))

    def test_male_dovetail_area_unchanged(self):
        inp=MaleDovetailInputs(cylinder_id=D(11.5),rod_od=D(11.475),
            groove_depth=D(.1715),gland_width=D(.1735),
            o_ring_id=D(11.475),o_ring_section=D(.210),angle_deg=D(24),
            bottom_radius=D(.03125),entrance_radius=D(.015), mode='rod_and_depth')
        e=calculate_installed(inp)
        self.assertAlmostEqual(e.results.cavity_area_sq_in.nominal,.044777,places=5)
        self.assertAlmostEqual(e.results.stretch_percent.nominal,100*(11.132/11.475-1))

if __name__=='__main__':unittest.main()
