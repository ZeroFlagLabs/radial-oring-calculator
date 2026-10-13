"""Audit-oriented read-only explanations of the *existing* calculated witnesses.

This module does not choose cases, screen pass/fail, or change engineering
algorithms. Calculated values are traced from a selected engine witness.
"""
from dataclasses import dataclass
from math import pi, tan, radians, isclose
from src.calculations.rectangular import Range
from src.calculations.profile_geometry import calculate_profile_area


@dataclass(frozen=True)
class ExplanationStep:
    title: str
    result: float
    unit: str
    symbolic: str
    numeric: str
    note: str = ''
    # Optional single fraction for each displayed equation. The renderer draws
    # real fraction bars; never presents a Python / expression as an equation.
    symbol_fraction: tuple[str, str, str, str] | None = None  # lhs,numerator,denominator,suffix
    numeric_fraction: tuple[str, str, str, str] | None = None


def geometry_records(inputs, output, female):
    """Derived physical quantities only; do not repeat entered dimensions."""
    piston, cylinder = inputs.rod_od, inputs.cylinder_id
    depth_entry = inputs.mode in ('rod_and_depth', 'cylinder_and_depth')
    if depth_entry:
        derived_name = 'Groove ID (in)' if female else 'Groove OD (in)'
        derived = output.gland_id if female else output.gland_od
    else:
        groove = inputs.gland_id if female else inputs.gland_od
        if not female:
            derived = Range((piston.minimum-groove.maximum)/2,
                            (piston.nominal-groove.nominal)/2,
                            (piston.maximum-groove.minimum)/2)
        else:
            derived = Range((groove.minimum-cylinder.maximum)/2,
                            (groove.nominal-cylinder.nominal)/2,
                            (groove.maximum-cylinder.minimum)/2)
        derived_name = 'Groove depth (in)'
    clearance = Range((cylinder.minimum-piston.maximum)/2,
                      (cylinder.nominal-piston.nominal)/2,
                      (cylinder.maximum-piston.minimum)/2)
    rows = [(derived_name, derived, 'in'),
            ('Radial component clearance (in)', clearance, 'in'),
            ('Available radial seal space (in)', output.radial_cavity_height, 'in')]
    if output.surface_opening_width_in is not None and inputs.entrance_radius.maximum > 0:
        rows.append(('Actual opening width (in)', output.surface_opening_width_in, 'in'))
    if output.groove_area_sq_in is not None:
        rows.append(('Groove area (in²)', output.groove_area_sq_in, 'in²'))
    rows.append(('Total available sealing area (in²)', output.cavity_area_sq_in, 'in²'))
    return rows


def explain_case(evaluation, metric, condition, entered=None, places=3):
    """Build formula, numerical substitution and result from the same case.

    Formatting is visual only: the engine's original float values always feed
    subsequent steps; the selected precision never alters a calculation.
    """
    f = lambda v: f'{v:.{places}f}'
    male = evaluation.male
    key = 'Fit' if metric in ('ID stretch', 'OD interference') else metric
    case = evaluation.cases[(key, condition)]
    s = dict(case.values)
    piston, cylinder = s['rod'], s['cylinder']
    groove = (s['gland'] if 'gland' in s else
              piston-2*s['depth'] if male else cylinder+2*s['depth'])
    depth = (piston-groove)/2 if male else (groove-cylinder)/2
    clearance = (cylinder-piston)/2
    space = (cylinder-groove)/2 if male else (groove-piston)/2
    free_id, free_section = s['ring_id'],s['section']
    area_section = case.equivalent_area_section
    profile = calculate_profile_area(s['width'],depth,clearance,s['angle'],s['bottom'],s['top'])
    if abs(profile.area_sq_in-case.cavity_area) > 1e-9:
        raise AssertionError('Area details disagree with installed calculation witness')
    ring_area = pi*area_section**2/4
    g_label = 'Groove OD' if male else 'Groove ID'
    values = {'Cylinder ID':(cylinder,'in'), 'Piston OD':(piston,'in'),
              g_label:(groove,'in'), 'O-ring free ID':(free_id,'in'),
              'O-ring cross-section':(free_section,'in')}
    if metric == 'Squeeze':
        names = (('Cylinder ID',g_label,'O-ring free ID','O-ring cross-section') if male
                 else ('Piston OD',g_label,'O-ring cross-section'))
    elif metric == 'Gland fill':
        names = ('Cylinder ID','Piston OD',g_label,'O-ring free ID','O-ring cross-section')
    else:
        names = ((g_label,'O-ring free ID') if male else (g_label,'O-ring free ID','O-ring cross-section'))
    inputs = [(name,*values[name]) for name in names]
    if 'depth' in s:
        comp = 'Piston OD' if male else 'Cylinder ID'
        if comp not in names:
            inputs.insert(0,(comp,*values[comp]))
        inputs.insert(1,('Groove depth',s['depth'],'in'))
    if metric == 'Gland fill':
        angle_name = ('Groove dovetail angle' if entered is not None and hasattr(entered,'angle_deg')
                      else 'Groove wall angle')
        additions = [('Groove width',s['width'],'in'),(angle_name,s['angle'],'deg'),
                     ('Groove base radius',s['bottom'],'in'),
                     ('Groove opening radius',s['top'],'in')]
        # Group physical components, groove dimensions, then free O-ring values.
        ring_inputs = [x for x in inputs if x[0].startswith('O-ring')]
        original = [x for x in inputs if not x[0].startswith('O-ring')]
        originals = {item[0]: item for item in original}
        ordered_names = ('Cylinder ID','Piston OD','Groove OD','Groove ID','Groove depth')
        inputs = ([originals[name] for name in ordered_names if name in originals]
                  + additions + ring_inputs)
    steps=[]
    def add(title,result,unit,symbolic,numeric,note='',sym_frac=None,num_frac=None):
        steps.append(ExplanationStep(title,result,unit,symbolic,numeric,note,sym_frac,num_frac))
    if metric == 'Squeeze':
        if male:
            stretch = case.install_fit_pct
            add('O-ring ID stretch',stretch,'%', 'ID stretch', 'ID stretch',
                'Determines how much the free O-ring ID is extended around the groove.',
                ('ID stretch','Groove OD − O-ring free ID','O-ring free ID','× 100'),
                ('ID stretch',f'{f(groove)} − {f(free_id)}',f(free_id),'× 100'))
            # Exactly the existing two fitted branches (and its clamp at zero).
            if stretch <= 0:
                raw_reduction=0.0
                formula='R = 0 (no positive ID stretch)'
                sub='R = 0'
            elif stretch <= 3 or isclose(stretch, 3.0, rel_tol=0.0, abs_tol=1e-10):
                raw_reduction = (-0.005+1.19*stretch-0.19*stretch**2
                                 -0.001*stretch**3+0.008*stretch**4)
                formula='R = −0.005 + 1.19s − 0.19s² − 0.001s³ + 0.008s⁴'
                sub=(f'R = −0.005 + 1.19 × {f(stretch)} − 0.19 × {f(stretch)}² '
                     f'− 0.001 × {f(stretch)}³ + 0.008 × {f(stretch)}⁴')
            else:
                raw_reduction=0.56+0.59*stretch-0.0046*stretch**2
                formula='R = 0.56 + 0.59s − 0.0046s²'
                sub=f'R = 0.56 + 0.59 × {f(stretch)} − 0.0046 × {f(stretch)}²'
            reduction=max(raw_reduction,0.0)
            add('Installed-section reduction',reduction,'%',formula,sub,
                's is ID stretch (%); R is the section reduction (%) from the selected empirical relationship. ' +
                ('This tolerance extreme is evaluated immediately beside the 3% branch transition; ' +
                 'the displayed stretch value is rounded.' if condition != 'Nominal' and abs(stretch-3) < 1e-5 else ''))
            add('Installed compression section',case.compression_section,'in',
                'dᵢ = d₀ × (1 − R ÷ 100)',
                f'dᵢ = {f(free_section)} × (1 − {f(reduction)} ÷ 100)',
                'The installed section is used for radial squeeze, not for the material-area calculation.')
        else:
            add('Installed compression section',case.compression_section,'in',
                'dᵢ = d₀',f'dᵢ = {f(free_section)}',
                'For a cylinder groove, no ID-stretch correction is applied to the free section.')
        a,b=(('Cylinder ID','Groove OD') if male else ('Groove ID','Piston OD'))
        x,y=((cylinder,groove) if male else (groove,piston))
        add('Available radial seal space',space,'in','h','h',
            'Radial separation between the groove base and the opposing sealing surface.',
            ('h',a+' − '+b,'2',''),('h',f(x)+' − '+f(y),'2',''))
        add('Radial squeeze',case.squeeze_in,'in','S = dᵢ − h',
            f'S = {f(case.compression_section)} − {f(space)}',
            'Installed compression section minus available radial seal space.')
        add('Squeeze percentage',case.squeeze_pct,'%','Squeeze','Squeeze',
            'Expresses the radial squeeze as a percentage of installed compression section.',
            ('Squeeze','S','dᵢ','× 100'),
            ('Squeeze',f(case.squeeze_in),f(case.compression_section),'× 100'))
    elif metric in ('ID stretch','OD interference'):
        if male:
            add('ID stretch',case.install_fit_pct,'%','ID stretch','ID stretch',
                'Compares the groove diameter against the free O-ring ID.',
                ('ID stretch','Groove OD − O-ring free ID','O-ring free ID','× 100'),
                ('ID stretch',f'{f(groove)} − {f(free_id)}',f(free_id),'× 100'))
        else:
            outer=free_id+2*free_section
            add('O-ring free OD',outer,'in','OD₀ = ID₀ + 2d₀',
                f'OD₀ = {f(free_id)} + 2 × {f(free_section)}',
                'Free outside diameter before installation.')
            add('OD interference',case.install_fit_pct,'%','OD interference','OD interference',
                'Compares the free O-ring OD with the cylinder groove ID.',
                ('OD interference','O-ring free OD − Groove ID','O-ring free OD','× 100'),
                ('OD interference',f'{f(outer)} − {f(groove)}',f(outer),'× 100'))
    else:
        if male:
            installed_id=groove
            if installed_id <= free_id:
                add('O-ring material section',area_section,'in','dₐ = d₀',
                    f'dₐ = {f(free_section)}',
                    'No positive ID stretch; the material-area model retains the free section.')
            else:
                add('Installed O-ring material section',area_section,'in',
                    'dₐ² × (IDᵢ + dₐ) = d₀² × (ID₀ + d₀)',
                    f'{f(area_section)}² × ({f(installed_id)} + {f(area_section)}) = '
                    f'{f(free_section)}² × ({f(free_id)} + {f(free_section)})',
                    'The displayed value dₐ solves the constant-volume relationship.')
        else:
            add('O-ring material section',area_section,'in','dₐ = d₀',
                f'dₐ = {f(free_section)}',
                'The free O-ring section is used for the material-area calculation.')
        add('O-ring material area',ring_area,'in²','Aᵣ','Aᵣ',
            'Two-dimensional O-ring material cross-sectional area.',
            ('Aᵣ','π × dₐ²','4',''),('Aᵣ',f'π × {f(area_section)}²','4',''))
        theta=radians(s['angle']); beta=pi/2-theta
        factor=1/tan(beta/2)-(pi-beta)/2
        add('Groove wall angle in radians',theta,'rad',
            'θ = angle × π ÷ 180',f'θ = {f(s["angle"])} × π ÷ 180',
            'Converts the entered angle in degrees to radians for the trigonometric functions.')
        add('Groove corner angle',beta,'rad','β = ½π − θ',
            f'β = ½π − {f(theta)}',
            'Corner angle used by the tangent-radius geometry.')
        add('Corner-area factor',factor,'',
            'f(β) = cot(½β) − ½(π − β)',
            f'f(β) = cot(½ × {f(beta)}) − ½(π − {f(beta)})',
            'Accounts for tangent corner radii in the two-dimensional groove area.')
        add('Groove profile area',profile.groove_area_sq_in,'in²',
            'A𝗀 = w × d + tan(θ) × d² + 2f(β) × (rₒ² − rᵦ²)',
            f'A𝗀 = {f(s["width"])} × {f(depth)} + tan({f(theta)}) × {f(depth)}² '
            f'+ 2 × {f(factor)} × ({f(s["top"])}² − {f(s["bottom"])}²)',
            'Two-dimensional groove area, including wall angle and opening/base radii.')
        opening_factor=1/tan(beta/2)
        add('Actual groove opening width',profile.opening_width_in,'in',
            'wₒ = w + 2rₒ × cot(½β)',
            f'wₒ = {f(s["width"])} + 2 × {f(s["top"])} × cot(½ × {f(beta)})',
            'Opening width after the groove opening radii are applied.')
        add('Total available sealing area',profile.area_sq_in,'in²',
            'Aₛ = A𝗀 + c × wₒ',
            f'Aₛ = {f(profile.groove_area_sq_in)} + {f(clearance)} × {f(profile.opening_width_in)}',
            'Includes the groove area and the component-clearance strip above its opening.')
        add('Gland fill',case.gland_fill_pct,'%','Gland fill','Gland fill',
            'O-ring material area divided by total available two-dimensional sealing area.',
            ('Gland fill','Aᵣ','Aₛ','× 100'),
            ('Gland fill',f(ring_area),f(profile.area_sq_in),'× 100'))
    result = (case.squeeze_pct if metric=='Squeeze' else case.install_fit_pct
              if key=='Fit' else case.gland_fill_pct)
    if abs(result-steps[-1].result)>1e-8:
        raise AssertionError('Displayed explanation does not match installed-engine witness')
    return result,inputs,steps
