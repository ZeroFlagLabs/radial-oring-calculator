"""Trace witnesses reproduce the output values and use physically linked inputs."""
import math
import unittest
from src.calculations.profile_geometry import SignedDimension
from src.calculations.rectangular import (
    Dimension as D, MaleRectangularInputs, FemaleRectangularInputs,
    calculate_male_rectangular, calculate_female_rectangular,
)
from src.calculations.dovetail import MaleDovetailInputs, FemaleDovetailInputs, calculate_male_dovetail, calculate_female_dovetail
from src.calculations.tolerance_trace import result_traces
from src.calculations.profile_geometry import calculate_profile_area


class TraceTests(unittest.TestCase):
    def check_trace(self, inputs, result):
        cases = result_traces(inputs,result)
        self.assertEqual(len(cases),9)
        for measure, values in [('Squeeze',result.squeeze_percent),
                                ('Stretch',result.stretch_percent),
                                ('Gland fill',result.gland_fill_percent)]:
            for label,attr in [('Minimum','minimum'),('Nominal','nominal'),('Maximum','maximum')]:
                self.assertAlmostEqual(cases[(measure,label)].value,getattr(values,attr))
        return cases

    def test_male_depth_witness_recalculates_squeeze_and_stretch(self):
        x=MaleRectangularInputs(
            cylinder_id=D(.669,.001),rod_od=D(.667,.001),groove_depth=D(.0835,.0005),
            gland_width=D(.146,.005),o_ring_id=D(.487,.005),o_ring_section=D(.103,.003),
            mode='rod_and_depth',bottom_radius=D(.01,.001),entrance_radius=D(.005,.001),
            wall_angle_deg=SignedDimension(-1,.25))
        result=calculate_male_rectangular(x)
        traces=self.check_trace(x,result)
        for label in ('Minimum','Nominal','Maximum'):
            s=dict(traces[('Squeeze',label)].inputs)
            h=(s['Cylinder ID']-(s['Rod OD']-2*s['Groove depth']))/2
            pct=(s['O-ring section']-h)/s['O-ring section']*100
            self.assertAlmostEqual(pct,traces[('Squeeze',label)].value)
            st=dict(traces[('Stretch',label)].inputs)
            pct=((st['Rod OD']-2*st['Groove depth'])/st['O-ring ID']-1)*100
            self.assertAlmostEqual(pct,traces[('Stretch',label)].value)
        area_case={'Minimum':'maximum','Nominal':'nominal','Maximum':'minimum'}
        for label in ('Minimum','Nominal','Maximum'):
            fields=dict(traces[('Gland fill',label)].inputs)
            area=calculate_profile_area(fields['Groove width'],fields['Groove depth'],
                   (fields['Cylinder ID']-fields['Rod OD'])/2,fields['Wall angle (deg)'],
                   fields['Bottom radius'],fields['Entrance radius']).area_sq_in
            self.assertAlmostEqual(area,fields['Resulting cavity area (in²)'])
            pct=100*math.pi*fields['O-ring section']**2/(4*area)
            self.assertAlmostEqual(pct,traces[('Gland fill',label)].value)
            self.assertAlmostEqual(area,getattr(result.cavity_area_sq_in,area_case[label]))

    def test_female_depth_witness_recalculates_squeeze(self):
        x=FemaleRectangularInputs(
            rod_od=D(.684,.001),cylinder_id=D(.687,.001),groove_depth=D(.0835,.0005),
            gland_width=D(.146,.005),o_ring_id=D(.674,.009),o_ring_section=D(.103,.003),
            mode='cylinder_and_depth',bottom_radius=D(.005,.001),entrance_radius=D(.003,.001))
        result=calculate_female_rectangular(x)
        traces=self.check_trace(x,result)
        for label in ('Minimum','Nominal','Maximum'):
            s=dict(traces[('Squeeze',label)].inputs)
            h=((s['Cylinder ID']+2*s['Groove depth'])-s['Rod OD'])/2
            pct=(s['O-ring section']-h)/s['O-ring section']*100
            self.assertAlmostEqual(pct,traces[('Squeeze',label)].value)

    def test_male_dovetail_direct_coupled_diameter(self):
        x=MaleDovetailInputs(
            cylinder_id=D(11.5,.010),gland_od=D(11.132,.004),rod_od=D(11.475,.002),
            gland_width=D(.1735,.0015),angle_deg=D(24,.5),bottom_radius=D(.03125,.005),
            entrance_radius=D(.015,.005),o_ring_id=D(11.475,.065),o_ring_section=D(.210,.005),
            mode='gland_od')
        result=calculate_male_dovetail(x)
        self.check_trace(x,result)

    def test_female_dovetail_direct_coupled_diameter(self):
        x=FemaleDovetailInputs(
            rod_od=D(11.475,.002),gland_id=D(11.843,.004),cylinder_id=D(11.5,.010),
            gland_width=D(.1735,.0015),angle_deg=D(24,.5),bottom_radius=D(.03125,.005),
            entrance_radius=D(.015,.005),o_ring_id=D(11.475,.065),o_ring_section=D(.210,.005),
            mode='gland_id')
        result=calculate_female_dovetail(x)
        self.check_trace(x,result)


if __name__=='__main__':
    unittest.main()
