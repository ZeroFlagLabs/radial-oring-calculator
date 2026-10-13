"""Independent dimensional model for rectangular radial O-ring glands.

All length values are in inches. Results are *geometric estimates*, not
seal design approval. Assumes straight walls, symmetric tolerances and a
constant unstretched circular O-ring cross-section.
"""

from dataclasses import dataclass
from math import pi, isfinite
from typing import Literal
from .profile_geometry import SignedDimension


@dataclass(frozen=True)
class Dimension:
    nominal: float
    tolerance: float = 0.0  # symmetric, +/- in

    def __post_init__(self) -> None:
        if not (isfinite(self.nominal) and isfinite(self.tolerance)):
            raise ValueError("All dimensions and tolerances must be finite numbers.")
        if self.nominal < 0 or self.tolerance < 0:
            raise ValueError("Dimensions and +/- tolerances cannot be negative.")
        if self.minimum < 0:
            raise ValueError("A tolerance cannot make a dimension negative.")

    @property
    def minimum(self) -> float:
        return self.nominal - self.tolerance

    @property
    def maximum(self) -> float:
        return self.nominal + self.tolerance


@dataclass(frozen=True)
class Range:
    minimum: float
    nominal: float
    maximum: float


@dataclass(frozen=True)
class MaleRectangularInputs:
    cylinder_id: Dimension
    gland_width: Dimension
    o_ring_id: Dimension
    o_ring_section: Dimension
    bottom_radius: Dimension = Dimension(0.0)
    entrance_radius: Dimension = Dimension(0.0)
    wall_angle_deg: SignedDimension = SignedDimension(0.0)
    mode: Literal["gland_od", "rod_and_depth"] = "gland_od"
    gland_od: Dimension | None = None
    rod_od: Dimension | None = None
    groove_depth: Dimension | None = None


@dataclass(frozen=True)
class MaleRectangularResults:
    gland_od: Range
    radial_cavity_height: Range
    squeeze_in: Range
    squeeze_percent: Range
    stretch_percent: Range
    gland_fill_percent: Range
    cavity_area_sq_in: Range
    surface_opening_width_in: Range | None = None
    groove_area_sq_in: Range | None = None


@dataclass(frozen=True)
class FemaleRectangularInputs:
    """Female radial gland (groove in bore), per supplied worksheet convention.

    When using cylinder ID and groove depth, gland ID = cylinder ID + 2*depth.
    The installed-size comparison (called stretch in the worksheets) uses the
    rod OD, not the gland ID. It is a dimensional screening convention and is
    not a model of installation deformation.
    """
    rod_od: Dimension
    gland_width: Dimension
    o_ring_id: Dimension
    o_ring_section: Dimension
    bottom_radius: Dimension = Dimension(0.0)
    entrance_radius: Dimension = Dimension(0.0)
    wall_angle_deg: SignedDimension = SignedDimension(0.0)
    mode: Literal["gland_id", "cylinder_and_depth"] = "gland_id"
    gland_id: Dimension | None = None
    cylinder_id: Dimension | None = None
    groove_depth: Dimension | None = None


@dataclass(frozen=True)
class FemaleRectangularResults:
    gland_id: Range
    radial_cavity_height: Range
    squeeze_in: Range
    squeeze_percent: Range
    stretch_percent: Range
    gland_fill_percent: Range
    cavity_area_sq_in: Range
    surface_opening_width_in: Range | None = None
    groove_area_sq_in: Range | None = None


def _gland_od_range(inputs: MaleRectangularInputs) -> Range:
    if inputs.mode == "gland_od":
        if inputs.gland_od is None:
            raise ValueError("Provide gland OD in direct-OD mode.")
        d = inputs.gland_od
        return Range(d.minimum, d.nominal, d.maximum)
    if inputs.mode == "rod_and_depth":
        if inputs.rod_od is None or inputs.groove_depth is None:
            raise ValueError("Provide both rod OD and groove depth.")
        rod, depth = inputs.rod_od, inputs.groove_depth
        if depth.minimum <= 0:
            raise ValueError("Groove depth must remain positive at minimum tolerance.")
        return Range(
            rod.minimum - 2 * depth.maximum,
            rod.nominal - 2 * depth.nominal,
            rod.maximum - 2 * depth.minimum,
        )
    raise ValueError("Unknown dimension entry mode.")


def calculate_male_rectangular(inputs: MaleRectangularInputs) -> MaleRectangularResults:
    """Calculate conservative, independently stacked dimensional extremes.

    Cross-sectional *area* gland fill follows a 2D approximation. The optional
    two bottom fillets reduce area by (2 - pi/2) * radius^2. No top fillets,
    extrusion gap, thermal effects, O-ring elongation correction or pressure
    capability are modelled. Actual 3D annular volume is not calculated.
    """
    g = _gland_od_range(inputs)
    c = inputs.cylinder_id
    w = inputs.gland_width
    ring_id = inputs.o_ring_id
    section = inputs.o_ring_section
    radius = inputs.bottom_radius

    if not (c.minimum > 0 and g.minimum > 0 and w.minimum > 0):
        raise ValueError("Minimum cylinder ID, gland OD and gland width must be positive.")
    if not (ring_id.minimum > 0 and section.minimum > 0):
        raise ValueError("Minimum O-ring ID and cross-section must be positive.")
    if inputs.mode == "rod_and_depth":
        assert inputs.rod_od is not None and inputs.groove_depth is not None
        if inputs.rod_od.maximum > c.minimum:
            raise ValueError("Rod OD maximum exceeds cylinder ID minimum: possible interference.")
        if radius.maximum > inputs.groove_depth.minimum:
            raise ValueError("Bottom radius exceeds minimum physical groove depth.")

    height = Range(
        (c.minimum - g.maximum) / 2,
        (c.nominal - g.nominal) / 2,
        (c.maximum - g.minimum) / 2,
    )
    if height.minimum <= 0:
        raise ValueError("Radial cavity height is zero or negative at a tolerance extreme.")
    has_depth_datum = inputs.mode == 'rod_and_depth' or inputs.rod_od is not None
    if not has_depth_datum and radius.maximum > min(height.minimum, w.minimum / 2):
        raise ValueError("Bottom fillets do not fit the minimum cavity height/width.")

    # When the actual depth is known, the profile engine validates fillet
    # tangencies against the tapered FLOOR width, not the sharp mouth width.
    legacy_radius = Dimension(0.0) if has_depth_datum else radius
    common = _calculate_common(height, w, ring_id, section, legacy_radius, g)
    result = MaleRectangularResults(g, *common)
    from .profile_geometry import evaluate_male_gland, with_profile_results
    if inputs.mode == 'gland_od' and inputs.rod_od is None:
        # Legacy direct gland OD needs no rod datum for a straight, sharp lip;
        # detailed wall taper / entrance radii require an actual groove depth.
        if inputs.wall_angle_deg.minimum != 0 or inputs.wall_angle_deg.maximum != 0 or inputs.entrance_radius.maximum:
            raise ValueError('Direct gland OD with wall angle or entrance radius also requires Rod OD.')
        return result
    envelopes = evaluate_male_gland(
        inputs, inputs.wall_angle_deg, radius, inputs.entrance_radius)
    return with_profile_results(result, envelopes, section)


def _calculate_common(
    height: Range, width: Dimension, ring_id: Dimension,
    section: Dimension, radius: Dimension, installed_diameter: Range,
) -> tuple[Range, Range, Range, Range, Range, Range]:
    """Shared geometry for male and female rectangular radial glands.

    Returns cavity height, squeeze-in, squeeze-%, installed ID mismatch %,
    fill %, and cavity area.
    Tolerance extrema use conservative independent worst-case stacking.
    """
    if width.minimum <= 0 or ring_id.minimum <= 0 or section.minimum <= 0:
        raise ValueError("Minimum gland width, O-ring ID and cross-section must be positive.")
    if height.minimum <= 0:
        raise ValueError("Radial cavity height is zero or negative at a tolerance extreme.")
    if radius.maximum > min(height.minimum, width.minimum / 2):
        raise ValueError("Bottom fillets do not fit the minimum cavity height/width.")

    sq = Range(
        section.minimum - height.maximum,
        section.nominal - height.nominal,
        section.maximum - height.minimum,
    )
    sq_pct = Range(
        100 * (1 - height.maximum / section.minimum),
        100 * (1 - height.nominal / section.nominal),
        100 * (1 - height.minimum / section.maximum),
    )
    stretch_pct = Range(
        100 * (installed_diameter.minimum / ring_id.maximum - 1),
        100 * (installed_diameter.nominal / ring_id.nominal - 1),
        100 * (installed_diameter.maximum / ring_id.minimum - 1),
    )

    fillet_factor = 2 * (1 - pi / 4)

    def cavity_area(w: float, h: float, r: float) -> float:
        return w * h - fillet_factor * r * r

    areas = Range(
        cavity_area(width.minimum, height.minimum, radius.maximum),
        cavity_area(width.nominal, height.nominal, radius.nominal),
        cavity_area(width.maximum, height.maximum, radius.minimum),
    )
    if areas.minimum <= 0:
        raise ValueError("Minimum gland cavity area must be positive.")
    ring_area_min = pi * section.minimum**2 / 4
    ring_area_nom = pi * section.nominal**2 / 4
    ring_area_max = pi * section.maximum**2 / 4
    fill_pct = Range(
        100 * ring_area_min / areas.maximum,
        100 * ring_area_nom / areas.nominal,
        100 * ring_area_max / areas.minimum,
    )
    return height, sq, sq_pct, stretch_pct, fill_pct, areas


def _gland_id_range(inputs: FemaleRectangularInputs) -> Range:
    if inputs.mode == "gland_id":
        if inputs.gland_id is None:
            raise ValueError("Provide gland ID in direct-ID mode.")
        g = inputs.gland_id
        return Range(g.minimum, g.nominal, g.maximum)
    if inputs.mode == "cylinder_and_depth":
        if inputs.cylinder_id is None or inputs.groove_depth is None:
            raise ValueError("Provide cylinder ID and groove depth.")
        c, d = inputs.cylinder_id, inputs.groove_depth
        if d.minimum <= 0:
            raise ValueError("Groove depth must remain positive at minimum tolerance.")
        if c.minimum <= 0:
            raise ValueError("Minimum cylinder ID must be positive.")
        return Range(
            c.minimum + 2 * d.minimum,
            c.nominal + 2 * d.nominal,
            c.maximum + 2 * d.maximum,
        )
    raise ValueError("Unknown female dimension entry mode.")


def calculate_female_rectangular(
    inputs: FemaleRectangularInputs,
) -> FemaleRectangularResults:
    """Female groove in a bore; same squeeze/fill calculation core as male.

    The installed ID mismatch is reported from rod OD / O-ring ID - 1,
    mirroring the supplied female worksheet's *intended* ID tolerance use.
    This is not a predictor of how the ring will deform during installation.
    """
    gland = _gland_id_range(inputs)
    rod = inputs.rod_od
    if rod.minimum <= 0 or gland.minimum <= 0:
        raise ValueError("Minimum rod OD and gland ID must be positive.")
    if inputs.mode == "cylinder_and_depth":
        assert inputs.cylinder_id is not None and inputs.groove_depth is not None
        if rod.maximum > inputs.cylinder_id.minimum:
            raise ValueError("Rod OD maximum exceeds cylinder ID minimum: possible interference.")
        if inputs.bottom_radius.maximum > inputs.groove_depth.minimum:
            raise ValueError("Bottom radius exceeds minimum physical groove depth.")
    cavity_height = Range(
        (gland.minimum - rod.maximum) / 2,
        (gland.nominal - rod.nominal) / 2,
        (gland.maximum - rod.minimum) / 2,
    )
    if cavity_height.minimum <= 0:
        raise ValueError("Radial cavity height is zero or negative at a tolerance extreme.")
    installed = Range(rod.minimum, rod.nominal, rod.maximum)
    has_depth_datum = inputs.mode == 'cylinder_and_depth' or inputs.cylinder_id is not None
    legacy_radius = Dimension(0.0) if has_depth_datum else inputs.bottom_radius
    common = _calculate_common(
        cavity_height, inputs.gland_width, inputs.o_ring_id,
        inputs.o_ring_section, legacy_radius, installed,
    )
    result = FemaleRectangularResults(gland, *common)
    from .profile_geometry import evaluate_female_gland, with_profile_results
    if inputs.mode == 'gland_id' and inputs.cylinder_id is None:
        if inputs.wall_angle_deg.minimum != 0 or inputs.wall_angle_deg.maximum != 0 or inputs.entrance_radius.maximum:
            raise ValueError('Direct gland ID with wall angle or entrance radius also requires Cylinder ID.')
        return result
    envelopes = evaluate_female_gland(
        inputs, inputs.wall_angle_deg, inputs.bottom_radius, inputs.entrance_radius)
    return with_profile_results(result, envelopes, inputs.o_ring_section)
