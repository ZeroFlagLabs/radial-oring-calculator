"""Stage 8 installed-condition correction for radial elastomer O-ring glands.

Separate from the validated sharp/tangent profile geometry. All tolerance
bounds use exhaustive *input endpoint* combinations. For piston squeeze,
the discontinuous 3% Parker stretch boundary is also tested on both sides
whenever dimensional tolerances permit the transition.
Male groove: Parker ORD 5700A Figure 3-3 observed compression-diameter curve
for squeeze; volume-conservation circular-equivalent area for gland fill.
Female groove: free-state OD interference relative to bore groove diameter;
no ID-stretch correction to section (Freudenberg p.3).

A stretched seal can flatten: its measured COMPRESSION DIAMETER and its
cross-sectional AREA are *not* the same geometric object. Never square the
Parker compression diameter to derive material area.
"""
from dataclasses import dataclass, replace
from itertools import product
from math import pi, isclose

from .rectangular import (
    Dimension, Range, MaleRectangularInputs, FemaleRectangularInputs,
    calculate_male_rectangular, calculate_female_rectangular,
)
from .dovetail import (
    MaleDovetailInputs, FemaleDovetailInputs,
    calculate_male_dovetail, calculate_female_dovetail,
)
from .profile_geometry import calculate_profile_area


@dataclass(frozen=True)
class InstalledCase:
    values: tuple[tuple[str, float], ...]
    squeeze_in: float
    squeeze_pct: float
    install_fit_pct: float
    gland_fill_pct: float
    compression_section: float
    equivalent_area_section: float
    cavity_area: float


@dataclass(frozen=True)
class InstalledEvaluation:
    results: object
    cases: dict  # keys: ("Squeeze", "Minimum"), ("Gland fill", ...) etc.
    male: bool


def observed_compression_section(free_section: float, stretch_pct: float) -> float:
    """Parker ORD 5700A Fig. 3-3 observed-curve *approximation*.

    The 0-3% and 3-25% published fits do not join exactly at 3%.
    This piecewise empirical relation is appropriate for a screen, not a
    prediction of exact compression diameter or seal deformation.
    """
    if stretch_pct <= 0:
        return free_section
    x = 3.0 if isclose(stretch_pct, 3.0, rel_tol=0.0, abs_tol=1e-10) else stretch_pct
    if x <= 3.0:
        reduction_pct = -0.005 + 1.19*x - 0.19*x*x - 0.001*x**3 + 0.008*x**4
    elif x <= 25.0:
        reduction_pct = 0.56 + .59*x - .0046*x*x
    else:
        raise ValueError('Installed ID stretch exceeds 25%; Parker compression-diameter approximation not applicable.')
    return free_section * (1 - max(reduction_pct, 0.0)/100)


def volume_equivalent_section(free_id: float, free_cs: float, installed_id: float) -> float:
    """Circular-area equivalent for fixed torus material volume.

    The model uses V proportional to (ID+CS)*CS²; solve for the installed
    equivalent CS (the model assumes an approximately circular section only
    for the purpose of calculating area, not squeeze).
    """
    if installed_id <= free_id:
        return free_cs  # this model does not predict OD-compression buckling
    target = free_cs**2 * (free_id + free_cs)
    lo, hi = 0.0, free_cs
    for _ in range(70):
        mid = (lo+hi)/2
        if mid*mid*(installed_id+mid) > target:
            hi = mid
        else:
            lo = mid
    return (lo+hi)/2


def _dimension_states(dimensions):
    keys = tuple(dimensions)
    ends = [((v.minimum, v.maximum) if v.tolerance else (v.nominal,)) for v in dimensions.values()]
    for combo in product(*ends):
        yield dict(zip(keys, combo))


# Branch limits are evaluated just below and above 3%, using actual
# dimensional states inside the user-entered tolerance envelope.  The small
# offset is in percentage POINTS of stretch; it distinguishes the two Parker
# relationships without changing either published polynomial.
_PARKER_TRANSITION_PCT = 3.0
_PARKER_SIDE_OFFSET_PCT = 1e-7


def _male_transition_cases(dimensions):
    """Yield squeeze witnesses immediately on either side of 3% stretch.

    A transition can lie in the interior of the ring ID, groove OD, piston OD
    or depth tolerance interval. Hold all other independent dimensions at
    permitted endpoints and solve each of those dimensions for both sides of
    the transition. This samples the boundary faces of the tolerance box,
    not arbitrary out-of-range or independently stacked extrema.
    """
    movable = ['ring_id']
    if 'gland' in dimensions:
        movable.append('gland')
    else:
        movable.extend(('rod', 'depth'))
    for endpoint in _dimension_states(dimensions):
        for dimension_name in movable:
            dim = dimensions[dimension_name]
            if dim.tolerance == 0:
                continue
            for pct in (_PARKER_TRANSITION_PCT - _PARKER_SIDE_OFFSET_PCT,
                        _PARKER_TRANSITION_PCT + _PARKER_SIDE_OFFSET_PCT):
                factor = 1.0 + pct / 100.0
                groove = (endpoint['gland'] if 'gland' in endpoint else
                          endpoint['rod'] - 2*endpoint['depth'])
                if dimension_name == 'ring_id':
                    value = groove / factor
                elif dimension_name == 'gland':
                    value = endpoint['ring_id'] * factor
                elif dimension_name == 'rod':
                    value = endpoint['ring_id'] * factor + 2*endpoint['depth']
                else:  # depth; gland OD = rod OD - 2 * depth
                    value = (endpoint['rod'] - endpoint['ring_id']*factor) / 2
                if dim.minimum <= value <= dim.maximum:
                    state = dict(endpoint)
                    state[dimension_name] = value
                    candidate = _male_case(state)
                    # Reject rounding-only cases in which the wrong Parker
                    # branch could have been selected at exactly 3%.
                    if abs(candidate.install_fit_pct - pct) < 1e-8:
                        yield candidate


def _male_specs(inputs):
    dovetail = isinstance(inputs, MaleDovetailInputs)
    angle = inputs.angle_deg if dovetail else inputs.wall_angle_deg
    dims = dict(cylinder=inputs.cylinder_id, width=inputs.gland_width,
                angle=angle, bottom=inputs.bottom_radius, top=inputs.entrance_radius)
    if inputs.mode == 'rod_and_depth':
        dims.update(rod=inputs.rod_od, depth=inputs.groove_depth)
    else:
        dims.update(rod=inputs.rod_od, gland=inputs.gland_od)
    return dims


def _male_case(s):
    gland = s['gland'] if 'gland' in s else s['rod'] - 2*s['depth']
    depth = s['depth'] if 'depth' in s else (s['rod']-gland)/2
    clearance = (s['cylinder']-s['rod'])/2
    area = calculate_profile_area(s['width'], depth, clearance,
                                  s['angle'], s['bottom'], s['top']).area_sq_in
    height = (s['cylinder']-gland)/2
    stretch = 100*(gland/s['ring_id']-1)
    compress_cs = observed_compression_section(s['section'], stretch)
    area_cs = volume_equivalent_section(s['ring_id'], s['section'], gland)
    sq = compress_cs-height
    return InstalledCase(tuple(s.items()), sq, 100*sq/compress_cs,
                         stretch, 100*pi*area_cs**2/(4*area), compress_cs,
                         area_cs, area)


def _female_case(s):
    gland = s['gland'] if 'gland' in s else s['cylinder'] + 2*s['depth']
    depth = s['depth'] if 'depth' in s else (gland-s['cylinder'])/2
    clearance = (s['cylinder']-s['rod'])/2
    area = calculate_profile_area(s['width'], depth, clearance,
                                  s['angle'], s['bottom'], s['top']).area_sq_in
    height = (gland-s['rod'])/2
    section = s['section']; outer = s['ring_id']+2*section
    if outer <= 0:
        raise ValueError('O-ring free outside diameter must be positive.')
    interference = 100*(outer-gland)/outer
    sq = section-height
    return InstalledCase(tuple(s.items()), sq, 100*sq/section,
                         interference, 100*pi*section**2/(4*area),
                         section, section, area)


def _female_specs(inputs):
    dovetail = isinstance(inputs, FemaleDovetailInputs)
    angle = inputs.angle_deg if dovetail else inputs.wall_angle_deg
    dims = dict(rod=inputs.rod_od, width=inputs.gland_width,
                angle=angle, bottom=inputs.bottom_radius, top=inputs.entrance_radius)
    if inputs.mode == 'cylinder_and_depth':
        dims.update(cylinder=inputs.cylinder_id, depth=inputs.groove_depth)
    else:
        dims.update(cylinder=inputs.cylinder_id, gland=inputs.gland_id)
    return dims


def calculate_installed(inputs) -> InstalledEvaluation:
    """Unified Stage 8 entry point, preserving existing profile area results."""
    male = isinstance(inputs, (MaleRectangularInputs, MaleDovetailInputs))
    if isinstance(inputs, MaleRectangularInputs):
        raw = calculate_male_rectangular(inputs)
    elif isinstance(inputs, FemaleRectangularInputs):
        raw = calculate_female_rectangular(inputs)
    elif isinstance(inputs, MaleDovetailInputs):
        raw = calculate_male_dovetail(inputs)
    elif isinstance(inputs, FemaleDovetailInputs):
        raw = calculate_female_dovetail(inputs)
    else:
        raise TypeError('Unknown radial O-ring configuration.')

    dimensions = _male_specs(inputs) if male else _female_specs(inputs)
    # Evaluate every original independent tolerance endpoint, including the
    # TWO O-ring dimensions: section and ID. Those two dimensions are coupled
    # to the installed section and fit and cannot be stacked independently.
    dimensions.update(ring_id=inputs.o_ring_id, section=inputs.o_ring_section)
    casefn = _male_case if male else _female_case
    extrema = []
    for state in _dimension_states(dimensions):
        try:
            extrema.append(casefn(state))
        except ValueError as exc:
            raise ValueError('Invalid installed condition at tolerance endpoints: '+str(exc)) from exc
    nominal = casefn({name: d.nominal for name,d in dimensions.items()})
    squeeze_cases = extrema + [nominal] + (list(_male_transition_cases(dimensions)) if male else [])
    fields = {
        'Squeeze': 'squeeze_pct',
        'Fit': 'install_fit_pct',
        'Gland fill': 'gland_fill_pct',
    }
    witnesses = {}
    ranges = {}
    for name, field in fields.items():
        candidates = squeeze_cases if name == 'Squeeze' else extrema
        low = min(candidates, key=lambda c: getattr(c,field))
        high = max(candidates, key=lambda c: getattr(c,field))
        witnesses.update({(name, 'Minimum'):low, (name,'Nominal'):nominal,
                          (name,'Maximum'):high})
        ranges[name] = Range(getattr(low,field), getattr(nominal,field), getattr(high,field))
    squeeze_min = min(squeeze_cases, key=lambda c: c.squeeze_in)
    squeeze_max = max(squeeze_cases, key=lambda c: c.squeeze_in)
    corrected = replace(raw,
                        squeeze_in=Range(squeeze_min.squeeze_in, nominal.squeeze_in, squeeze_max.squeeze_in),
                        squeeze_percent=ranges['Squeeze'],
                        stretch_percent=ranges['Fit'],
                        gland_fill_percent=ranges['Gland fill'])
    return InstalledEvaluation(corrected, witnesses, male)


def installed_result_traces(evaluation: InstalledEvaluation):
    """Witnesses for the *actual* adjusted values displayed in Stage 8."""
    from .tolerance_trace import ExtremumTrace
    results = evaluation.results
    labels = ('Minimum','Nominal','Maximum')
    attrs = ('minimum','nominal','maximum')
    out = {}
    for label,attr in zip(labels, attrs):
        for metric, value, units, explanation in (
            ('Squeeze', getattr(results.squeeze_percent,attr), '%',
             'Male: Parker observed installed compression diameter; female: free section. '
             'Squeeze is calculated against the assembled radial cavity height.'),
            ('ID stretch' if evaluation.male else 'OD interference',
             getattr(results.stretch_percent,attr), '%',
             'Male: installed gland OD / free O-ring ID - 1. '
             'Female: (free O-ring OD - bore gland ID) / free O-ring OD.'),
            ('Gland fill', getattr(results.gland_fill_percent,attr), '%',
             'Male: constant-volume circular-equivalent material area, not the '
             'empirical compression diameter squared. Female: free-state section area. '
             'Denominator is CAD-validated 2D cavity area.')
        ):
            key = 'Fit' if metric in ('ID stretch','OD interference') else metric
            sample = evaluation.cases[(key,label)]
            extra = (
                ('Installed compression section',sample.compression_section),
                ('Area-equivalent section',sample.equivalent_area_section),
                ('Cavity area (in²)',sample.cavity_area),
            )
            mapping = {'rod':'Rod OD','cylinder':'Cylinder ID','gland':
                       ('Gland OD' if evaluation.male else 'Gland ID'),
                       'depth':'Groove depth', 'width':'Groove width',
                       'angle':'Wall angle (deg)','bottom':'Bottom radius',
                       'top':'Entrance radius','ring_id':'O-ring free ID',
                       'section':'O-ring free section'}
            inputs = tuple((mapping.get(k,k),v) for k,v in sample.values)+extra
            out[(metric,label)] = ExtremumTrace(metric,label,value,units,inputs,
                explanation+(
                    ' Piston squeeze also considers the two sides of the 3% Parker stretch transition.'
                    if evaluation.male and key == 'Squeeze' else
                    ' All evaluated extrema use independent input tolerance endpoints.'))
    return out
