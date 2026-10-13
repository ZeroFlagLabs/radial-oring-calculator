"""Stage 6: exact planar straight-flank/circular-fillet groove profile.

Datum: width is measured at the THEORETICAL sharp intersection of the
sidewalls with the nominal rod/bore surface. Positive angle means the groove
WIDENS WITH DEPTH; a negative angle is wider at its opening. Each side uses
the same angle and fillet radii; the profile is symmetric left-to-right.

The opposite (ungrooved) surface is parallel, a clearance c above the
nominal grooved surface. The clearance strip is rectangular with width equal
to the ACTUAL opening at that surface, accounting for entrance roundovers.
This is a planar area model, NOT the exact 3D annular seal volume.
"""
from dataclasses import dataclass
from math import cos, isfinite, pi, radians, sin, tan
from itertools import product
from typing import Callable


@dataclass(frozen=True)
class SignedDimension:
    """Signed nominal with symmetric tolerance, useful for wall angles."""
    nominal: float
    tolerance: float = 0.0

    def __post_init__(self):
        if not (isfinite(self.nominal) and isfinite(self.tolerance)) or self.tolerance < 0:
            raise ValueError('Angle and tolerance must be finite; tolerance must be nonnegative.')

    @property
    def minimum(self):
        return self.nominal - self.tolerance

    @property
    def maximum(self):
        return self.nominal + self.tolerance


@dataclass(frozen=True)
class ProfileSection:
    area_sq_in: float
    groove_area_sq_in: float
    opening_width_in: float


def _corner_loss_factor(interior_angle: float) -> float:
    """Area between a sharp polygon corner and a tangent circular fillet,
    divided by radius squared. Interior_angle measured on the removed side.
    At 90 degrees: 1 - pi/4, familiar square-minus-quarter-circle result.
    """
    return 1 / tan(interior_angle / 2) - (pi - interior_angle) / 2


def calculate_profile_area(width: float, depth: float, clearance: float,
                           angle_deg: float, bottom_radius: float = 0.0,
                           entrance_radius: float = 0.0) -> ProfileSection:
    """Exact planar area for a symmetric straight-sided groove and tangent arcs.

    The *entrance* fillets round away material from the exposed surface lip,
    increasing surface opening and the available groove area. The *bottom*
    fillets replace cavity with material and decrease area.

    All widths are measured perpendicular to the radial depth axis. Angle is
    measured from the radial depth axis (not from the horizontal face).
    """
    vals = (width, depth, clearance, angle_deg, bottom_radius, entrance_radius)
    if not all(isfinite(n) for n in vals):
        raise ValueError('All profile inputs must be finite.')
    if width <= 0 or depth <= 0 or clearance < -1e-10 or bottom_radius < 0 or entrance_radius < 0:
        raise ValueError('Width/depth must be positive; clearance/radii cannot be negative.')
    if not -75 < angle_deg < 75:
        raise ValueError('Wall angle must be strictly between -75 and +75 degrees.')
    theta = radians(angle_deg)
    slope = tan(theta)
    floor_width = width + 2 * depth * slope
    if floor_width <= 0:
        raise ValueError('Tapered groove closes or crosses at the floor.')

    # At both the top lip (metal convex corner) and at the internal floor
    # corner (groove concave corner), the relevant interior angle is 90°-theta.
    beta = pi / 2 - theta
    tangent_factor = 1 / tan(beta / 2)  # = sec(theta)+tan(theta)
    side_tangent_y = (1 + sin(theta)) * (entrance_radius + bottom_radius)
    if side_tangent_y > depth + 1e-10:
        raise ValueError('Entrance and floor fillets overlap along the sidewall.')
    if 2 * bottom_radius * tangent_factor >= floor_width - 1e-12:
        raise ValueError('Bottom fillets overlap or consume the entire groove floor.')

    factor = _corner_loss_factor(beta)
    # Width at original theoretical lip intersection, integrated through d.
    sharp_groove_area = width * depth + slope * depth * depth
    # Both top corners remove metal (ADD cavity); both bottom corners add
    # metal (REMOVE cavity). Exactly circular segments, not bounding boxes.
    groove_area = sharp_groove_area + 2 * factor * (entrance_radius**2 - bottom_radius**2)
    # Rounded lip moves its tangency on the ungrooved surface outward.
    actual_opening = width + 2 * entrance_radius * tangent_factor
    total_area = groove_area + max(0.0, clearance) * actual_opening
    if groove_area <= 0 or total_area <= 0:
        raise ValueError('Groove area must be positive.')
    return ProfileSection(total_area, groove_area, actual_opening)


def evaluate_profile_extremes(dimensions: dict, make_section: Callable[[dict], ProfileSection],
                              return_witnesses: bool = False):
    """Nominal plus ALL vertices of the original dimensional tolerance box.

    This deliberately follows the Stage 7 user-selected endpoint convention.
    It does not search interior values and does not claim that the result is a
    global extremum over continuous manufacturing-tolerance intervals.

    Derived groove depth and clearance remain correlated in direct-diameter
    entry modes because original dimensions, not separately derived ranges,
    are enumerated. Any geometrically invalid corner invalidates the envelope.
    """
    keys = tuple(dimensions)
    vals = tuple(dimensions.values())
    nominal = make_section({k: v.nominal for k, v in dimensions.items()})
    edges = [(v.minimum, v.maximum) if v.tolerance else (v.nominal,) for v in vals]
    samples = []
    for combo in product(*edges):
        state = dict(zip(keys, combo))
        try:
            samples.append((state, make_section(state)))
        except ValueError as exc:
            rendered = ', '.join(f'{key}={state[key]:.6g}' for key in keys)
            raise ValueError(f'Invalid geometry at a tolerance extreme ({rendered}): {exc}') from exc
    min_area = min(samples, key=lambda p: p[1].area_sq_in)
    max_area = max(samples, key=lambda p: p[1].area_sq_in)
    output = (
        (min_area[1].area_sq_in, nominal.area_sq_in, max_area[1].area_sq_in),
        (min(p[1].opening_width_in for p in samples), nominal.opening_width_in,
         max(p[1].opening_width_in for p in samples)),
        (min(p[1].groove_area_sq_in for p in samples), nominal.groove_area_sq_in,
         max(p[1].groove_area_sq_in for p in samples)),
    )
    if return_witnesses:
        return output, {
            'minimum': dict(min_area[0]),
            'nominal': {k: v.nominal for k, v in dimensions.items()},
            'maximum': dict(max_area[0]),
        }
    return output


def evaluate_male_gland(inputs, angle, bottom_radius, entrance_radius,
                        return_witnesses: bool = False):
    """Envelope for the male gland, preserving covariance of dimensions."""
    dims = dict(
        cylinder=inputs.cylinder_id, width=inputs.gland_width,
        angle=angle, bottom=bottom_radius, top=entrance_radius,
    )
    if inputs.mode == 'rod_and_depth':
        if inputs.rod_od is None or inputs.groove_depth is None:
            raise ValueError('Rod OD and groove depth are required.')
        dims.update(rod=inputs.rod_od, depth=inputs.groove_depth)

        def evaluate(s):
            return calculate_profile_area(
                s['width'], s['depth'], (s['cylinder'] - s['rod'])/2,
                s['angle'], s['bottom'], s['top'])
    elif inputs.mode == 'gland_od':
        if inputs.rod_od is None or inputs.gland_od is None:
            raise ValueError('rod OD and gland OD are required for profile geometry in direct mode.')
        dims.update(rod=inputs.rod_od, gland=inputs.gland_od)

        def evaluate(s):
            return calculate_profile_area(
                s['width'], (s['rod'] - s['gland'])/2,
                (s['cylinder'] - s['rod'])/2,
                s['angle'], s['bottom'], s['top'])

    else:
        raise ValueError('Unknown male entry method.')
    return evaluate_profile_extremes(dims, evaluate, return_witnesses=return_witnesses)


def evaluate_female_gland(inputs, angle, bottom_radius, entrance_radius,
                          return_witnesses: bool = False):
    """Envelope for the female gland, preserving covariance of dimensions."""
    dims = dict(
        rod=inputs.rod_od, width=inputs.gland_width,
        angle=angle, bottom=bottom_radius, top=entrance_radius,
    )
    if inputs.mode == 'cylinder_and_depth':
        if inputs.cylinder_id is None or inputs.groove_depth is None:
            raise ValueError('Cylinder ID and groove depth are required.')
        dims.update(cylinder=inputs.cylinder_id, depth=inputs.groove_depth)

        def evaluate(s):
            return calculate_profile_area(
                s['width'], s['depth'], (s['cylinder'] - s['rod'])/2,
                s['angle'], s['bottom'], s['top'])
    elif inputs.mode == 'gland_id':
        if inputs.cylinder_id is None or inputs.gland_id is None:
            raise ValueError('cylinder ID and gland ID are required for profile geometry in direct mode.')
        dims.update(cylinder=inputs.cylinder_id, gland=inputs.gland_id)

        def evaluate(s):
            return calculate_profile_area(
                s['width'], (s['gland'] - s['cylinder'])/2,
                (s['cylinder'] - s['rod'])/2,
                s['angle'], s['bottom'], s['top'])

    else:
        raise ValueError('Unknown female entry method.')
    return evaluate_profile_extremes(dims, evaluate, return_witnesses=return_witnesses)


def with_profile_results(result, envelopes, o_ring_section):
    """Replace just cavity area/fill; squeeze and installed-ID logic is shared."""
    from dataclasses import replace
    from math import pi
    from .rectangular import Range

    area, opening, groove = (Range(*item) for item in envelopes)
    fill = Range(
        100 * pi * o_ring_section.minimum**2 / (4 * area.maximum),
        100 * pi * o_ring_section.nominal**2 / (4 * area.nominal),
        100 * pi * o_ring_section.maximum**2 / (4 * area.minimum),
    )
    return replace(
        result, cavity_area_sq_in=area, gland_fill_percent=fill,
        surface_opening_width_in=opening, groove_area_sq_in=groove,
    )
