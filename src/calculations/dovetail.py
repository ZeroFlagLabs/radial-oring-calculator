"""Preliminary symmetric double-dovetail radial gland calculations.

The squeeze and installed ID mismatch are shared with the established
rectangular model. Gland fill is derived from the common Stage 6 geometry
engine with tangent circular arcs and a true surface opening. With radii
zero the former trapezoid/clearance formula still holds:
  - a trapezoid WITHIN the machined groove depth d, where the mouth width
    is w and both flanks flare at theta from the radial depth axis, and
  - a rectangular strip of width w above the mouth through the radial
    rod-to-bore clearance c = assembled cavity height h - groove depth d.

    A = d * (w + d*tan(theta)) + c*w = h*w + d*d*tan(theta).

This deliberately differs from the isolated Mathcad expression
h*(w+d*tan(theta)); the slope does not extend beyond the machined groove.
The general profile models TWO bottom and TWO entrance radii. It does not
predict annular volume or pressure deformation or stretched cross-section.
All linear dimensions in inches; the flank angle is in degrees.
"""

from dataclasses import dataclass, replace
from typing import Literal

from .profile_geometry import evaluate_male_gland, evaluate_female_gland, with_profile_results
from .rectangular import (
    Dimension, Range, MaleRectangularInputs, FemaleRectangularInputs,
    MaleRectangularResults, FemaleRectangularResults,
    _gland_od_range, _gland_id_range, calculate_male_rectangular,
    calculate_female_rectangular,
)


@dataclass(frozen=True)
class MaleDovetailInputs:
    cylinder_id: Dimension
    gland_width: Dimension
    o_ring_id: Dimension
    o_ring_section: Dimension
    angle_deg: Dimension
    bottom_radius: Dimension = Dimension(0.0)
    entrance_radius: Dimension = Dimension(0.0)
    mode: Literal['gland_od', 'rod_and_depth'] = 'rod_and_depth'
    gland_od: Dimension | None = None
    rod_od: Dimension | None = None
    groove_depth: Dimension | None = None


@dataclass(frozen=True)
class FemaleDovetailInputs:
    rod_od: Dimension
    gland_width: Dimension
    o_ring_id: Dimension
    o_ring_section: Dimension
    angle_deg: Dimension
    bottom_radius: Dimension = Dimension(0.0)
    entrance_radius: Dimension = Dimension(0.0)
    mode: Literal['gland_id', 'cylinder_and_depth'] = 'cylinder_and_depth'
    gland_id: Dimension | None = None
    cylinder_id: Dimension | None = None
    groove_depth: Dimension | None = None


def calculate_male_dovetail(inputs: MaleDovetailInputs) -> MaleRectangularResults:
    base = MaleRectangularInputs(
        cylinder_id=inputs.cylinder_id, gland_width=inputs.gland_width,
        o_ring_id=inputs.o_ring_id, o_ring_section=inputs.o_ring_section,
        mode=inputs.mode, gland_od=inputs.gland_od,
        rod_od=inputs.rod_od, groove_depth=inputs.groove_depth,
    )
    results = calculate_male_rectangular(base)
    envelopes = evaluate_male_gland(
        inputs, inputs.angle_deg, inputs.bottom_radius, inputs.entrance_radius)
    return with_profile_results(results, envelopes, inputs.o_ring_section)



def calculate_female_dovetail(inputs: FemaleDovetailInputs) -> FemaleRectangularResults:
    base = FemaleRectangularInputs(
        rod_od=inputs.rod_od, gland_width=inputs.gland_width,
        o_ring_id=inputs.o_ring_id, o_ring_section=inputs.o_ring_section,
        mode=inputs.mode, gland_id=inputs.gland_id,
        cylinder_id=inputs.cylinder_id, groove_depth=inputs.groove_depth,
    )
    results = calculate_female_rectangular(base)
    envelopes = evaluate_female_gland(
        inputs, inputs.angle_deg, inputs.bottom_radius, inputs.entrance_radius)
    return with_profile_results(results, envelopes, inputs.o_ring_section)
