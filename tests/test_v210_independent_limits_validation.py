"""Independent engineering checks for v2.1.0 mixed limit entry.

Reference calculations use literal input endpoints, geometric relationships and
an independently written exhaustive Cartesian endpoint enumerator, NOT the
calculator's conversion/data-model/installed-case implementations.
"""
import math
import unittest
from itertools import product

from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from gui_sample import seed_sample


MALE = {
    'cylinder':(.749,.751), 'rod':(.747,.749),
    'gland':(.583,.585), 'depth':(.081,.083),
}
FEMALE = {
    'cylinder':(.5765,.5775),'rod':(.574,.576),
    'gland':(.740,.742),'depth':(.08175,.08225),
}
SHARED = {
    'width':(.1415,.1473), 'bottom':(.002,.005),
    'top':(.001,.003), 'ring_id':(.559,.570),
    'section':(.099,.106),
    'angle_rect':(-1.,3.),'angle_dovetail':(22.,26.),
}


def section_area(width, depth, gap, degrees, bottom, entrance):
    """Independent analytical cavity area for a trapezoid and tangent fillets."""
    rad=degrees*math.pi/180.0
    tangent=math.tan(rad)
    interior=math.pi/2-rad
    extra_factor=1.0/math.tan(interior/2.0) - (math.pi-interior)/2.0
    opening_width=width + 2.0*entrance/math.tan(interior/2.0)
    return (width*depth + depth*depth*tangent +
            2.0*extra_factor*(entrance*entrance-bottom*bottom)
            +gap*opening_width)


def cubic_area_section(free_id,section,diameter):
    if diameter<=free_id:
        return section
    vol=(free_id+section)*section*section
    lower,upper=0.0,section
    for _ in range(80):
        mid=(lower+upper)/2
        if (diameter+mid)*mid*mid>vol:
            upper=mid
        else:
            lower=mid
    return (lower+upper)/2


def compression_section(free_section,fit):
    if fit<=0:
        return free_section
    if fit<=3.0+1e-10:
        x=min(fit,3.)
        drop=(-.005+1.19*x-.19*x*x-.001*x**3+.008*x**4)
    else:
        drop=.56+.59*fit-.0046*fit*fit
    return free_section*(1-max(0,drop)/100)


def reference_case(s,*,female,method):
    if female:
        groove=s.get('gland',s.get('cylinder',0)+2*s.get('depth',0))
        depth=(groove-s['cylinder'])/2 if 'gland' in s else s['depth']
        gap=(s['cylinder']-s['rod'])/2
        cavity_height=(groove-s['rod'])/2
        ring_od=s['ring_id']+2*s['section']
        fit=100*(ring_od-groove)/ring_od
        comp=s['section']; material=s['section']
    else:
        groove=s.get('gland',s['rod']-2*s.get('depth',0))
        depth=(s['rod']-groove)/2 if 'gland' in s else s['depth']
        gap=(s['cylinder']-s['rod'])/2
        cavity_height=(s['cylinder']-groove)/2
        fit=100*(groove/s['ring_id']-1)
        comp=(compression_section(s['section'],fit)
              if method=='detailed' else s['section'])
        material=(cubic_area_section(s['ring_id'],s['section'],groove)
                  if method=='detailed' else s['section'])
    area=section_area(s['width'],depth,gap,s['angle'],s['bottom'],s['top'])
    assert area>0,(s,area)
    squeeze=comp-cavity_height
    return {'squeeze_percent':100*squeeze/comp,
            'stretch_percent':fit,
            'gland_fill_percent':100*math.pi*material*material/(4*area),
            'squeeze_in':squeeze,
            'cavity_area_sq_in':area}


def reference_envelopes(spec,*,female,method):
    names=tuple(spec)
    values=[(spec[x] if spec[x][0]!=spec[x][1] else (spec[x][0],)) for x in names]
    corners=[reference_case(dict(zip(names,each)),female=female,method=method)
             for each in product(*values)]
    centre={name:(low+high)/2 for name,(low,high) in spec.items()}
    nominal=reference_case(centre,female=female,method=method)
    squeeze_candidates=list(corners)+[nominal]
    # The nominal input is a meaningful physical state, and at an exactly
    # 3% stretch midpoint it can be the limiting sample. Do not omit it.
    # The empirical compression-diameter relation has a small discontinuity
    # at 3% ID stretch. Independently sample its left/right limits wherever
    # the *entered* ring-ID interval contains that physical state.
    if method=='detailed' and not female:
        ring_lo,ring_hi=spec['ring_id']
        others={k:v for k,v in spec.items() if k!='ring_id'}
        other_names=tuple(others)
        for other in product(*(others[k] for k in other_names)):
            state=dict(zip(other_names,other))
            groove=state['gland'] if 'gland' in state else state['rod']-2*state['depth']
            for offset in (-1e-7,1e-7):
                ring=groove/(1+(3+offset)/100)
                if ring_lo<=ring<=ring_hi:
                    state2=dict(state,ring_id=ring)
                    squeeze_candidates.append(
                        reference_case(state2,female=False,method=method))
    result={}
    for name in ('squeeze_percent','stretch_percent','gland_fill_percent',
                 'squeeze_in','cavity_area_sq_in'):
        candidates=(squeeze_candidates if name in ('squeeze_percent','squeeze_in')
                    else corners)
        result[name]=(min(item[name] for item in candidates),
                      nominal[name],
                      max(item[name] for item in candidates))
    return result


class V210IndependentLimitsValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.w=MainWindow()
        seed_sample(self.w)

    def tearDown(self):
        self.w.close()

    def compare(self,expected,model,tag):
        for metric in ('squeeze_percent','stretch_percent',
                       'gland_fill_percent','squeeze_in','cavity_area_sq_in'):
            got=getattr(model,metric)
            for label,value in zip(('minimum','nominal','maximum'),expected[metric]):
                self.assertAlmostEqual(getattr(got,label),value,delta=1e-8,
                    msg=f'{tag} {metric}.{label}: actual={getattr(got,label)}, independent={value}')

    def test_all_16_configurations_against_independent_asymmetric_oracle(self):
        cases=0
        for female in (False,True):
            for dovetail in (False,True):
                for method in ('simplified','detailed'):
                    for depth_mode in (False,True):
                        w=self.w
                        w.configuration.setCurrentIndex(1 if female else 0)
                        w.groove_type.setCurrentIndex(1 if dovetail else 0)
                        w.calculation_method.setCurrentIndex(
                            w.calculation_method.findData(method))
                        entry=w.female_entry_mode if female else w.entry_mode
                        mode=('cylinder_and_depth' if female else 'rod_and_depth') if depth_mode else ('gland_id' if female else 'gland_od')
                        entry.setCurrentIndex(entry.findData(mode))
                        base=dict(FEMALE if female else MALE)
                        if depth_mode:
                            del base['gland']
                        else:
                            del base['depth']
                        shared=dict(SHARED)
                        angle=shared.pop('angle_dovetail' if dovetail else 'angle_rect')
                        shared.pop('angle_rect' if dovetail else 'angle_dovetail')
                        base.update(shared)
                        base['angle']=angle
                        active=('angle' if dovetail else 'rect_angle')
                        for key,limits in (
                            ('width',SHARED['width']),
                            ('radius',SHARED['bottom']),
                            ('entrance_radius',SHARED['top']),
                            (active,angle)):
                            r=w.shared_rows[key]
                            if not r.limit_mode:r.mode_limits.click()
                            with QSignalBlocker(r.limit_min):
                                r.limit_min.setValue(limits[0])
                            with QSignalBlocker(r.limit_max):
                                r.limit_max.setValue(limits[1])
                        for key,limits in (
                            ('ring_id',SHARED['ring_id']),('section',SHARED['section'])):
                            r=w.rows[key]
                            if not r.limit_mode:r.mode_limits.click()
                            with QSignalBlocker(r.limit_min):
                                r.limit_min.setValue(limits[0])
                            with QSignalBlocker(r.limit_max):
                                r.limit_max.setValue(limits[1])
                        w._recalculate()
                        self.assertIsNotNone(w._last_result,
                            f'{female=} {dovetail=} {method=} {depth_mode=} {w.statusBar().currentMessage()}')
                        ref=reference_envelopes(base,female=female,method=method)
                        tag=f'{female=} {dovetail=} {method=} {depth_mode=}'
                        self.compare(ref,w._last_result,tag)
                        cases+=1
        self.assertEqual(cases,16)

    def test_crossing_three_percent_transition_with_limits_is_sampled(self):
        # This asymmetric free-ring-ID range crosses 3% stretch for a gland
        # fixed at 0.515 in, without using the engine's transition helper.
        w=self.w
        w.calculation_method.setCurrentIndex(w.calculation_method.findData('detailed'))
        for row,value in ((w.rows['cylinder_id'],.681),
                          (w.rows['direct_rod_od'],.667),
                          (w.rows['gland_od'],.515),
                          (w.shared_rows['width'],.146),
                          (w.rows['section'],.103)):
            with QSignalBlocker(row.nominal):row.nominal.setValue(value)
            with QSignalBlocker(row.tolerance):row.tolerance.setValue(0)
        row=w.rows['ring_id']
        row.mode_limits.click()
        with QSignalBlocker(row.limit_min):row.limit_min.setValue(.49955)
        with QSignalBlocker(row.limit_max):row.limit_max.setValue(.50045)
        w._recalculate()
        self.assertIsNotNone(w._last_result)
        independent=reference_envelopes({
            'cylinder':(.681,.681),'rod':(.667,.667),'gland':(.515,.515),
            'width':(.146,.146),'angle':(0.,0.),
            'bottom':(0.,0.),'top':(0.,0.),
            'ring_id':(.49955,.50045),'section':(.103,.103)
        },female=False,method='detailed')
        self.compare(independent,w._last_result,'3pct-transition')
        w.calculation_method.setCurrentIndex(w.calculation_method.findData('simplified'))
        w._recalculate()
        simp=reference_envelopes({
            'cylinder':(.681,.681),'rod':(.667,.667),'gland':(.515,.515),
            'width':(.146,.146),'angle':(0.,0.),
            'bottom':(0.,0.),'top':(0.,0.),
            'ring_id':(.49955,.50045),'section':(.103,.103)
        },female=False,method='simplified')
        self.compare(simp,w._last_result,'3pct-simplified')


if __name__=='__main__':unittest.main()
