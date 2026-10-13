"""Human-readable witness values for the Stage 7 endpoint-only convention.

Extreme squeeze and installed-ID mismatch have direct monotonic expressions.
Gland fill depends on the geometric endpoint envelope, whose MINIMUM area
produces MAXIMUM fill and vice versa. Witnesses are from the same corner
search as the production geometric calculation, not separately stacked
or invented ranges.
"""

from dataclasses import dataclass
from typing import Literal

from .profile_geometry import evaluate_female_gland, evaluate_male_gland
from .rectangular import FemaleRectangularInputs, MaleRectangularInputs
from .dovetail import FemaleDovetailInputs, MaleDovetailInputs


@dataclass(frozen=True)
class ExtremumTrace:
    metric: str
    condition: str
    value: float
    units: str
    inputs: tuple[tuple[str, float], ...]
    explanation: str


def _gland_cases(dim, mode, sex):
    """Get geometric ring-seat diameter witness for squeeze/stretch."""
    if sex == 'male':
        if mode == 'gland_od':
            return {key: ({'Gland OD': getattr(dim.gland_od, direction)})
                    for key, direction in [('Minimum', 'minimum'), ('Nominal', 'nominal'), ('Maximum', 'maximum')]}
        rod, depth = dim.rod_od, dim.groove_depth
        return {
            'Minimum': {'Rod OD': rod.minimum, 'Groove depth': depth.maximum},
            'Nominal': {'Rod OD': rod.nominal, 'Groove depth': depth.nominal},
            'Maximum': {'Rod OD': rod.maximum, 'Groove depth': depth.minimum},
        }
    if mode == 'gland_id':
        return {key: {'Gland ID': getattr(dim.gland_id, direction)}
                for key, direction in [('Minimum', 'minimum'), ('Nominal', 'nominal'), ('Maximum', 'maximum')]}
    cylinder, depth = dim.cylinder_id, dim.groove_depth
    return {
        'Minimum': {'Cylinder ID': cylinder.minimum, 'Groove depth': depth.minimum},
        'Nominal': {'Cylinder ID': cylinder.nominal, 'Groove depth': depth.nominal},
        'Maximum': {'Cylinder ID': cylinder.maximum, 'Groove depth': depth.maximum},
    }


def result_traces(inputs, result):
    """Return {(measure, case): ExtremumTrace} for squeeze, stretch and fill.

    `Minimum/Maximum` refer to the RESULT, not a universal choice of min/max
    dimensional values. An invalid geometry raises ValueError as in the main
    engine. Uses only endpoint dimensions, never interior optimisations.
    """
    male = isinstance(inputs, (MaleRectangularInputs, MaleDovetailInputs))
    sex = 'male' if male else 'female'
    gland = _gland_cases(inputs, inputs.mode, sex)
    labels = ['Minimum', 'Nominal', 'Maximum']
    original = ['minimum', 'nominal', 'maximum']
    output = {}
    for case, attr in zip(labels, original):
        if male:
            # Male h = (cylinder - gland OD)/2.
            cylside = {'Minimum': 'maximum', 'Nominal': 'nominal', 'Maximum': 'minimum'}[case]
            gland_case = {'Minimum': 'Minimum', 'Nominal': 'Nominal', 'Maximum': 'Maximum'}[case]
            sq_state = {'Cylinder ID': getattr(inputs.cylinder_id, cylside), **gland[gland_case],
                        'O-ring section': getattr(inputs.o_ring_section, attr)}
        else:
            # Female h = (gland ID - rod OD)/2.
            rodside = {'Minimum': 'minimum', 'Nominal': 'nominal', 'Maximum': 'maximum'}[case]
            gland_case = {'Minimum': 'Maximum', 'Nominal': 'Nominal', 'Maximum': 'Minimum'}[case]
            sq_state = {'Rod OD': getattr(inputs.rod_od, rodside), **gland[gland_case],
                        'O-ring section': getattr(inputs.o_ring_section, attr)}
        if male:
            st_state = {**gland[case],
                        'O-ring ID': getattr(inputs.o_ring_id,
                                             {'Minimum': 'maximum', 'Nominal': 'nominal', 'Maximum': 'minimum'}[case])}
        else:
            st_state = {'Rod OD': getattr(inputs.rod_od, attr),
                        'O-ring ID': getattr(inputs.o_ring_id,
                                             {'Minimum': 'maximum', 'Nominal': 'nominal', 'Maximum': 'minimum'}[case])}
        output[('Squeeze', case)] = ExtremumTrace(
            'Squeeze', case, getattr(result.squeeze_percent, attr), '%', tuple(sq_state.items()),
            'Minimum/maximum squeeze use the opposite cavity-height and O-ring section limits. '
            'The displayed value is squeeze as a percentage of that section.')
        output[('Stretch', case)] = ExtremumTrace(
            'Stretch', case, getattr(result.stretch_percent, attr), '%', tuple(st_state.items()),
            'Uses the installed male gland OD or female rod OD, compared with the O-ring ID.')

    # Profile geometry enumerates the original independent toleranced input
    # dimensions, preserving cylinder/rod/depth correlations in direct mode.
    angle = (inputs.angle_deg if hasattr(inputs, 'angle_deg') else inputs.wall_angle_deg)
    evalfn = evaluate_male_gland if male else evaluate_female_gland
    _, witness = evalfn(inputs, angle, inputs.bottom_radius, inputs.entrance_radius,
                        return_witnesses=True)
    mapping = {
        'cylinder': 'Cylinder ID', 'rod': 'Rod OD', 'gland': ('Gland OD' if male else 'Gland ID'),
        'depth': 'Groove depth', 'width': 'Groove width', 'angle': 'Wall angle (deg)',
        'bottom': 'Bottom radius', 'top': 'Entrance radius',
    }
    area_case = {'Minimum': 'maximum', 'Nominal': 'nominal', 'Maximum': 'minimum'}
    cs_side = {'Minimum': 'minimum', 'Nominal': 'nominal', 'Maximum': 'maximum'}
    for case, attr in zip(labels, original):
        state = witness[area_case[case]]
        displayed = [(mapping[key], val) for key, val in state.items()]
        displayed.append(('O-ring section', getattr(inputs.o_ring_section, cs_side[case])))
        displayed.append(('Resulting cavity area (in²)', getattr(result.cavity_area_sq_in, area_case[case])))
        output[('Gland fill', case)] = ExtremumTrace(
            'Gland fill', case, getattr(result.gland_fill_percent, attr), '%', tuple(displayed),
            'Minimum fill uses the maximum cavity area and minimum O-ring section. '
            'Maximum fill uses the minimum cavity area and maximum O-ring section. '
            'The geometry is searched at all dimensional tolerance endpoints only.')
    return output
