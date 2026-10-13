"""Interactive nominal radial-gland schematic. NOT a manufacturing drawing.

Shows the correct input datums and groove direction. Display proportions and
fillets are deliberately illustrative; validated calculations are independent.
"""
from math import tan, radians
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget, QSizePolicy

from src.ui.precision import format_input


class GrooveDiagram(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(520, 385)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.config = 'male'
        self.groove = 'rectangular'
        self.entry = 'rod_and_depth'
        self.values = {}
        self.active_key = 'width'
        self.invalid = False
        self.setToolTip('Schematic only: nominal dimensions and feature locations, not a scale drawing or CAD profile.')

    def set_model(self, config: str, groove: str, entry: str, values: dict, invalid=False):
        self.config, self.groove, self.entry = config, groove, entry
        self.values = dict(values)
        self.invalid = invalid
        self.update()

    def set_active_key(self, key: str):
        self.active_key = {
            'groove_depth':'depth',
            'direct_cylinder_id':'cylinder_id',
            'direct_rod_od':'piston_od',
        }.get(key,key)
        self.update()

    def to_pixmap(self, width=800, height=490):
        pix = QPixmap(width, height)
        pix.fill(QColor('#ffffff'))
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(width / 760, height / 460)
        self._paint(painter)
        painter.end()
        return pix

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('#ffffff'))
        painter.scale(self.width()/760, self.height()/460)
        self._paint(painter)
        painter.end()

    def _paint(self, p):
        V = self.values
        def get(name, fallback=0):
            return float(V.get(name, fallback))
        def dim(name):
            return format_input(get(name)) + '″'
        accent = QColor('#0c72c9')
        neutral = QColor('#4c647f')
        metal = QColor('#e1e9f2')
        navy = QColor('#193e66')
        green = QColor('#1580a5')
        female = self.config == 'female'
        title = 'Female gland · bore groove' if female else 'Male gland · piston groove'
        p.setPen(navy)
        p.setFont(QFont('Segoe UI', 13, QFont.Weight.DemiBold))
        p.drawText(22, 27, title + (' · double dovetail' if self.groove == 'dovetail' else ' · rectangular'))
        p.setFont(QFont('Segoe UI', 9))
        p.setPen(QColor('#72859c'))
        p.drawText(22, 45, 'Nominal dimension locations  •  schematic, not to scale')
        if self.invalid:
            p.setPen(QColor('#b42318'))
            p.drawText(200, 230, 'Invalid dimensions. Please check inputs.')
            return

        # Nominal relationships, never take a calculated dimension as an
        # independent user input. Only the primary dimensions are shown.
        w = max(get('width', .145), .001)
        d = max(get('depth', .082), .001)
        a = get('angle')
        theta = tan(radians(max(-55, min(55, a))))
        scale = min(195/d, 300/(w + 2*d*abs(theta)))
        top_half = w*scale/2
        floor_half = (w + 2*d*theta)*scale/2
        depth_px = d*scale
        cx, top_y = 384, 153
        bottom_y = top_y + depth_px
        lip_l, lip_r = cx-top_half, cx+top_half
        floor_l, floor_r = cx-floor_half, cx+floor_half
        radius = min(get('radius')*scale, 0.25*depth_px, 35)
        entrance = min(get('entrance_radius')*scale, 0.23*depth_px, 34)
        if female:
            # Mirror the *profile* across the local surface. Preserve right-side-up text.
            mirror = lambda y: 460-y
            lip_y, floor_y, exterior_y = mirror(top_y), mirror(bottom_y), mirror(top_y-38)
        else:
            mirror = lambda y: y
            lip_y, floor_y, exterior_y = top_y, bottom_y, top_y-38

        def pt(x,y): return QPointF(x,mirror(y))
        # The following curves indicate the presence and location of tangent
        # radii, but are not asserted as a fillet-accurate CAD construction.
        ltop = lip_l-entrance
        rtop = lip_r+entrance
        path=QPainterPath()
        path.moveTo(pt(ltop,top_y))
        if entrance:
            path.quadTo(pt(lip_l,top_y),pt(lip_l+entrance*.22,top_y+entrance))
        else:
            path.lineTo(pt(lip_l,top_y))
        if radius:
            path.lineTo(pt(floor_l-radius*.30,bottom_y-radius))
            path.quadTo(pt(floor_l,bottom_y),pt(floor_l+radius,bottom_y))
        else:
            path.lineTo(pt(floor_l,bottom_y))
        if radius:
            path.lineTo(pt(floor_r-radius,bottom_y))
            path.quadTo(pt(floor_r,bottom_y),pt(floor_r+radius*.30,bottom_y-radius))
        else:
            path.lineTo(pt(floor_r,bottom_y))
        if entrance:
            path.lineTo(pt(lip_r-entrance*.22,top_y+entrance))
            path.quadTo(pt(lip_r,top_y),pt(rtop,top_y))
        else:
            path.lineTo(pt(lip_r,top_y))
        path.closeSubpath()

        # Base material with a white cavity cutout, so male and female profiles
        # mirror correctly without pretending diameter dimensions are local widths.
        metalpath=QPainterPath()
        top_rect=min(lip_y,floor_y)-45 if female else lip_y-23
        bottom_rect=max(lip_y,floor_y)+45 if not female else lip_y+23
        if female:
            metalpath.addRect(QRectF(150, floor_y-45, 468,lip_y-(floor_y-45)+18))
        else:
            metalpath.addRect(QRectF(150,lip_y-18,468,floor_y-lip_y+63))
        metalpath.setFillRule(Qt.FillRule.OddEvenFill)
        metalpath.addPath(path)
        p.fillPath(metalpath,metal)
        p.setPen(QPen(QColor('#8095aa'),1))
        p.drawPath(metalpath)
        p.fillPath(path,QColor('#effaff'))
        p.setPen(QPen(green,2.2))
        p.drawPath(path)

        # Opposing ungrooved component is a simple straight section.
        p.fillRect(QRectF(150, exterior_y-7,468,8),QColor('#bac8d8'))
        p.setPen(QPen(QColor('#647a93'),1.3))
        p.drawLine(QPointF(150,exterior_y),QPointF(618,exterior_y))
        # Cross-section of installed seal is indicative only.
        ring_y = (lip_y+floor_y)/2
        p.setBrush(QColor('#6daecc'))
        p.setPen(QPen(accent if self.active_key in ('ring_id','section') else QColor('#236f9a'),
                      3 if self.active_key in ('ring_id','section') else 2))
        p.drawEllipse(QRectF(cx-48,ring_y-44,96,88))
        p.setBrush(Qt.BrushStyle.NoBrush)

        def label(x, y, text, key=None, align='left', size=10):
            active = key == self.active_key or (self.active_key in ('rod_od','direct_rod_od') and key=='piston_od')
            p.setFont(QFont('Segoe UI', size, QFont.Weight.DemiBold if active else QFont.Weight.Normal))
            p.setPen(accent if active else navy)
            if align=='center':
                p.drawText(QRectF(x-105,y-15,210,23),Qt.AlignmentFlag.AlignCenter,text)
            elif align=='right':
                p.drawText(QRectF(x-160,y-15,160,23),Qt.AlignmentFlag.AlignRight,text)
            else:
                p.drawText(x,y,text)

        def arrow_line(x1,y1,x2,y2,key=None):
            sel = key == self.active_key
            p.setPen(QPen(accent if sel else neutral,2.4 if sel else 1.2))
            p.drawLine(QPointF(x1,y1),QPointF(x2,y2))
            if abs(x2-x1)>abs(y2-y1):
                p.drawLine(QPointF(x1,y1),QPointF(x1+6,y1-4))
                p.drawLine(QPointF(x1,y1),QPointF(x1+6,y1+4))
                p.drawLine(QPointF(x2,y2),QPointF(x2-6,y2-4))
                p.drawLine(QPointF(x2,y2),QPointF(x2-6,y2+4))
            else:
                sign=1 if y2>y1 else -1
                p.drawLine(QPointF(x1,y1),QPointF(x1-4,y1+sign*6))
                p.drawLine(QPointF(x1,y1),QPointF(x1+4,y1+sign*6))
                p.drawLine(QPointF(x2,y2),QPointF(x2-4,y2-sign*6))
                p.drawLine(QPointF(x2,y2),QPointF(x2+4,y2-sign*6))

        # Width is measured at the theoretical *sharp* mouth intersections,
        # before the fillets. Draw a datum line across those points.
        arrow_y=110 if not female else 417
        p.setPen(QPen(QColor('#a1b1c2'),1,Qt.PenStyle.DashLine))
        p.drawLine(QPointF(lip_l,lip_y),QPointF(lip_l,arrow_y))
        p.drawLine(QPointF(lip_r,lip_y),QPointF(lip_r,arrow_y))
        arrow_line(lip_l,arrow_y,lip_r,arrow_y,'width')
        label(cx,arrow_y-13 if not female else arrow_y+22,'Groove width  '+dim('width'),'width',align='center')

        # Radial depth line, from theoretical surface down to floor.
        dx=128
        arrow_line(dx,lip_y,dx,floor_y,'depth')
        label(22, (lip_y+floor_y)/2-9,'Groove depth','depth')
        label(22,(lip_y+floor_y)/2+8,dim('depth'),'depth')
        # Hardware data are diameters, so shown as identifying callouts rather
        # than falsely drawn as distances across the 2D groove sketch.
        if female:
            info=[('Piston OD',get('rod_od')),('Cylinder ID',get('cylinder_id')),('Gland ID',get('gland_id'))]
        else:
            info=[('Piston OD',get('piston_od')),('Cylinder ID',get('cylinder_id')),('Gland OD',get('gland_od'))]
        for idx,(text,value) in enumerate(info):
            key={'Piston OD':('rod_od' if female else 'piston_od'),'Cylinder ID':'cylinder_id','Gland OD':'gland_od','Gland ID':'gland_id'}[text]
            y=360+idx*21 if not female else 62+idx*21
            label(535,y,text+'  '+format_input(value)+'″',key, size=10)
        # O-ring dimensions come from the free-state catalogue/manual fields;
        # the pictured installed ellipse is illustrative and not to scale.
        if self.active_key in ('ring_id','section'):
            label(284,ring_y+7,'O-ring section',self.active_key,align='right',size=10)
        # Fillet / flank callouts on right side.
        fillet_y=137 if not female else 329
        label(538,fillet_y,'Opening R  '+dim('entrance_radius'),'entrance_radius',size=10)
        label(538,fillet_y+21,'Base R  '+dim('radius'),'radius',size=10)
        key='angle' if self.groove=='dovetail' else 'rect_angle'
        label(538,fillet_y+42,'Wall angle  '+f"{get('angle'):.1f}°",key,size=10)
        p.setPen(QColor('#72859c'))
        p.setFont(QFont('Segoe UI',9))
        p.drawText(22,448,'Blue highlight indicates the selected input. Diameters are callouts, not sketch distances.')
