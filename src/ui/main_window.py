"""PySide6 user interface: deliberately separate from the calculation engine."""

from PySide6.QtCore import Qt, QEvent, QFile, QIODevice, QSize, QSignalBlocker, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from PySide6.QtUiTools import QUiLoader
from pathlib import Path
from decimal import Decimal
from html import escape as _escape_html
import re
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPlainTextEdit,
    QPushButton, QScrollArea, QStackedWidget, QSizePolicy, QVBoxLayout, QWidget,
)

from src.app_info import APP_TITLE, APP_VERSION
from src.ui.spin_suffix import protect_suffix
from src.ui.update_checker import UpdateChecker
from src.catalog.as568 import load_as568
from src.catalog.matching import matching_sizes
from src.calculations.installed import calculate_installed, installed_result_traces
from src.ui.snapshot_view import render_snapshot, save_snapshot_to_png
from src.ui.inspect_results import build_inspect_results
from src.ui.groove_diagram import GrooveDiagram
from src.ui.precision import format_input, format_result
from src.ui.size_guide import SizeGuide
from src.ui.dialog_style import set_standard_action_width
from src.ui.settings_dialog import SettingsDialog
from src.calculations.criteria import ScreeningResults, screen_rectangular
from src.calculations.profile_geometry import SignedDimension
from src.calculations.rectangular import (
    Dimension, MaleRectangularInputs, MaleRectangularResults,
    FemaleRectangularInputs, FemaleRectangularResults,
    calculate_male_rectangular, calculate_female_rectangular,
)
from src.calculations.dovetail import (
    MaleDovetailInputs, FemaleDovetailInputs,
    calculate_male_dovetail, calculate_female_dovetail,
)


class AdaptiveSpinBox(QDoubleSpinBox):
    """Compact dimension entry, retaining precision after mode conversions.

    Manually entered values normally use six decimal places. Converting
    six-place *limits* to nominal +/- tolerance can require seven places:
    e.g. 0.141001 to 0.148500 -> 0.1447505 +/- 0.0037495.
    Preserve that half-microinch instead of silently rounding the endpoints.
    """

    def __init__(self, parent=None):
        self.minimum_display_decimals = 3
        super().__init__(parent)
        protect_suffix(self)

    def textFromValue(self, value: float) -> str:
        if self.decimals() <= 6:
            return format_input(value, self.minimum_display_decimals)
        # Keep existing compact three/one-place presentation unless extra
        # precision is genuinely required to represent the converted value.
        exact = Decimal(str(value)).normalize()
        needed = max(0, -exact.as_tuple().exponent)
        displayed = max(self.minimum_display_decimals,
                        min(self.decimals(), needed))
        return f'{value:.{displayed}f}'

    def set_display_decimals(self, decimals: int):
        self.minimum_display_decimals = decimals
        # Repaint text without re-assigning the value and rounding a tolerance.
        self.lineEdit().setText(self.textFromValue(self.value()) + self.suffix())

    def wheelEvent(self, event):
        """Never change a dimension through accidental mouse-wheel scrolling.

        The up/down stepper buttons and keyboard arrows remain enabled. Ignoring
        (rather than accepting) this event lets any parent scroll area scroll.
        """
        event.ignore()


class DimensionRow(QWidget):
    """One nominal field and one symmetrical +/- tolerance field, in inches."""

    def __init__(self, nominal: float, tolerance: float, on_change, parent=None, suffix=" in", signed=False):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.signed = signed
        self.nominal = self._spin(nominal, suffix, signed)
        self.tolerance = self._spin(tolerance, suffix)
        self.nominal.setToolTip("Nominal dimension in inches")
        self.tolerance.setToolTip("Symmetrical +/- tolerance in inches")
        self.tolerance.setMaximumWidth(118)
        layout.addWidget(self.nominal, 3)
        layout.addWidget(QLabel("±"))
        layout.addWidget(self.tolerance, 2)
        self.nominal.valueChanged.connect(on_change)
        self.tolerance.valueChanged.connect(on_change)

    @staticmethod
    def _spin(value: float, suffix: str = " in", signed=False) -> QDoubleSpinBox:
        item = AdaptiveSpinBox()
        item.setRange(-74.999 if signed else 0.0, 74.999 if signed else 10000.0)
        item.setDecimals(6)
        item.setSingleStep(0.001)
        item.setValue(value)
        item.setSuffix(suffix)
        item.setKeyboardTracking(False)
        item.setMinimumHeight(24)
        return item

    def set_display_decimals(self, decimals: int):
        self.nominal.set_display_decimals(decimals)
        self.tolerance.set_display_decimals(decimals)

    def dimension(self) -> Dimension | SignedDimension:
        kind = SignedDimension if self.signed else Dimension
        return kind(self.nominal.value(), self.tolerance.value())


class BoundDimensionRow:
    """Binds native Qt Designer field widgets to the existing calculation API."""
    def __init__(self, widget, nominal, tolerance, on_change, signed=False):
        self.widget = widget
        self.nominal = nominal
        self.tolerance = tolerance
        self.signed = signed
        nominal.valueChanged.connect(on_change)
        tolerance.valueChanged.connect(on_change)

    def set_display_decimals(self, decimals):
        self.nominal.set_display_decimals(decimals)
        self.tolerance.set_display_decimals(decimals)
        for name in ('limit_min', 'limit_max'):
            editor = getattr(self, name, None)
            if editor is not None:
                editor.set_display_decimals(decimals)

    def effective_nominal(self):
        # Limits have no independent nominal entry. Their midpoint is the
        # precisely defined reference used for the Nominal result column.
        if getattr(self, 'limit_mode', False):
            return (self.limit_min.value() + self.limit_max.value()) / 2
        return self.nominal.value()

    def dimension(self):
        kind = SignedDimension if self.signed else Dimension
        if getattr(self, 'limit_mode', False):
            low = self.limit_min.value()
            high = self.limit_max.value()
            if low > high:
                name = getattr(self, 'field_name', self.widget.objectName())
                raise ValueError(f'{name}: minimum limit exceeds maximum limit.')
            return kind((low + high) / 2, (high - low) / 2)
        return kind(self.nominal.value(), self.tolerance.value())


class MainWindow(QMainWindow):
    def __init__(self):
        # The Designer UI deliberately uses a light colour scheme. On Windows
        # dark mode, otherwise unstyled labels inherit white system text over
        # the white form panels, and combo popups inherit dark system colours.
        # Request Qt's native *application-only* light scheme before creating
        # any widgets. This does not change Windows theme settings or the
        # established colours, dimensions, or calculations in light mode.
        app = QApplication.instance()
        if app is not None and app.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1000, 830)
        self.rows = {}
        self.female_rows = {}
        self.shared_rows = {}
        self.as568_sizes = load_as568()
        self._last_result: MaleRectangularResults | FemaleRectangularResults | None = None
        self._last_evaluation = None
        self._last_inputs = None
        self._last_screening: ScreeningResults | None = None
        self.update_checker = UpdateChecker(self)
        # Keep track of the previous component selection so an unused
        # counterpart can inherit shared physical dimensions on first use.
        self._previous_configuration = None
        self._build_ui()
        self._reset_dimensions()
        # Parent-owned timer cannot fire after the window is closed (also
        # important for short-lived test windows).
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self.update_checker.check_on_launch)
        self._update_timer.start(1500)
        self._stabilise_input_heights()
        self._align_dimension_frames()
        self._fix_main_window_size()
        # Designer finalises the header-label width on first show. Position
        # once then, so the button sits after the actual visible label text.
        QTimer.singleShot(0, self._position_calculation_method_info_icon)

    def _position_calculation_method_info_icon(self):
        """Position the info button immediately after the actual label text."""
        label = self.findChild(QLabel,'selector_calculation_method_label')
        button = self.calculation_method_info_button
        x = min(label.width()-button.width(),
                label.fontMetrics().horizontalAdvance(label.text())+4)
        button.move(max(0,x),2)
        button.raise_()

    def _stabilise_input_heights(self):
        """Hold stacked entry fields and dimension panels at their natural heights."""
        for stack in (self.entry_mode_stack, self.gland_entry, self.female_gland_entry):
            stack.ensurePolished()
            for i in range(stack.count()):
                page = stack.widget(i)
                if page.layout() is not None: page.layout().activate()
            height = max(stack.sizeHint().height(), stack.minimumSizeHint().height())
            if height > 0: stack.setFixedHeight(height)
        groups = (self.male_group, self.female_group,
                  self.findChild(QGroupBox, 'shared_group'), self.ring_group,
                  self.findChild(QGroupBox, 'overview_box'))
        for group in groups:
            group.ensurePolished()
            if group.layout() is not None: group.layout().activate()
            height = max(group.sizeHint().height(), group.minimumSizeHint().height())
            if height > 0: group.setFixedHeight(height)
        # The left column is precisely the three visible frames and two gaps.
        # Do not use QFrame.sizeHint here: its old expanding bottom spacer
        # introduced unwanted space above the screening results.
        panel = self.findChild(QWidget, 'input_panel')
        left = panel.layout()
        margin = left.contentsMargins()
        group_height = max(self.male_group.height(), self.female_group.height())
        dimension_height = (group_height + self.findChild(QGroupBox, 'shared_group').height()
                            + self.ring_group.height() + 2 * left.spacing()
                            + margin.top() + margin.bottom())
        panel.setFixedHeight(dimension_height)

    def _align_dimension_frames(self):
        """Align guide borders with the fixed dimension column, not its content."""
        panel = self.findChild(QWidget, 'input_panel')
        guide = self.findChild(QGroupBox, 'drawing_group')
        content = self.findChild(QHBoxLayout, 'contentLayout')
        if panel is None or guide is None or content is None:
            raise RuntimeError('Designer is missing dimension/guide layout controls')
        guide_panel = self.findChild(QWidget, 'guide_panel')
        guide_layout = self.findChild(QVBoxLayout, 'guidePanelLayout')
        if guide_panel is None or guide_layout is None:
            raise RuntimeError('Designer guide-panel layout missing')
        content.setAlignment(panel, Qt.AlignmentFlag.AlignTop)
        content.setAlignment(guide_panel, Qt.AlignmentFlag.AlignTop)
        guide_layout.setAlignment(guide, Qt.AlignmentFlag.AlignTop)
        # A nested QHBoxLayout can otherwise absorb surplus vertical space
        # despite its two fixed-height children. Pin the *layout item* to its
        # natural height, so the following screening frame is placed at the
        # main layout's ordinary 4px gap, just like setup -> dimension guide.
        self._root_layout.setAlignment(content, Qt.AlignmentFlag.AlignTop)
        # Use the stabilised fixed height rather than pre-show geometry.
        guide.setFixedHeight(panel.maximumHeight())
        guide_panel.setFixedHeight(panel.maximumHeight())

    def _fix_main_window_size(self):
        """STAGE_95_FIXED_WINDOW: fit visible controls without a scroll area."""
        layout = self.centralWidget().layout()
        layout.activate()
        minimum = self.centralWidget().minimumSizeHint()
        chrome = self.statusBar().sizeHint().height()
        width = max(1000, minimum.width())
        # Do not impose the old 680px height floor: spare height allocated to
        # the nested dimension-row layout created a visually oversized gap
        # above screening. The actual minimum includes every visible control.
        height = minimum.height() + chrome + 1
        self.setFixedSize(width, height)

    def _build_ui(self):
        """Load every layout/control from Designer; wire behavior by stable names.

        Users may edit src/ui/forms/main_window.ui using Qt Designer.  Do not
        build parallel hand-coded layouts or regenerate the .ui at startup.
        """
        filename = Path(__file__).resolve().parent / 'forms' / 'main_window.ui'
        loader = QUiLoader()
        loader.registerCustomWidget(AdaptiveSpinBox)
        file = QFile(str(filename))
        if not file.open(QIODevice.OpenModeFlag.ReadOnly):
            raise RuntimeError(f'Unable to open Qt Designer layout: {filename}')
        try:
            surface = loader.load(file)
            if surface is None:
                raise RuntimeError(f'Qt Designer layout cannot be loaded: {loader.errorString()}')
        finally:
            file.close()
        # Direct Designer surface: the main window is fixed-size and never scrolls.
        self.setCentralWidget(surface)
        # Stage 9.1 applied its theme at MainWindow level. The Designer UI
        # stores the editable theme on appSurface, so mirror it onto this
        # window to retain disabled-spinbox styling and the existing GUI
        # contract. Read it from the .ui every launch: layout and colours
        # remain editable in Qt Designer rather than duplicated in Python.
        # Keep icon paths working in Designer, normal runs and packaged EXEs.
        icon_dir = Path(__file__).resolve().parents[1] / 'resources' / 'icons'
        sheet = surface.styleSheet()
        for icon_name in ('spin-chevron-up.png', 'spin-chevron-down.png',
                          'spin-chevron-up-disabled.png', 'spin-chevron-down-disabled.png'):
            sheet = sheet.replace(f'url(src/resources/icons/{icon_name})',
                                  f'url("{(icon_dir / icon_name).as_posix()}")')
        surface.setStyleSheet(sheet)
        self.setStyleSheet(surface.styleSheet())
        def get(name, kind=QWidget):
            found = surface.findChild(kind, name)
            if found is None:
                raise RuntimeError(f'The Designer layout is missing the required element: {name}')
            return found

        # Fixed widget names connect the editable layout with the calculation
        # engine. Users may alter positions/text/spacing but must not rename.
        for name in ('calculation_method','application','configuration','groove_type','entry_mode',
                     'female_entry_mode','ring_size'):
            setattr(self,name,get(name,QComboBox))
        for name in ('entry_mode_stack','gland_entry','female_gland_entry'):
            setattr(self,name,get(name,QStackedWidget))
        for name in ('guide_button','trace_button','snapshot_button',
                     'save_snapshot_button','reset_button','settings_button',
                     'calculation_method_info_button'):
            setattr(self,name,get(name,QPushButton))
        for name in ('male_group','female_group'):
            setattr(self,name,get(name,QGroupBox))
        for name in ('shared_note','match_note','overview_note'):
            setattr(self,name,get(name,QLabel))
        for name in ('match_slot','guide_placeholder'):
            setattr(self,name,get(name))
        for name in ('male_direct_form','female_direct_form','shared_form',
                     'overview_grid'):
            layout_type = QFormLayout if name.endswith('_form') else QGridLayout
            setattr(self,name,get(name,layout_type))
        self._root_layout = get('mainLayout',QVBoxLayout)

        # Both calculation methods share the existing input layout and report
        # formats. The calculation engine supplies method-specific witnesses.
        self.calculation_method.addItem('Detailed', 'detailed')
        self.calculation_method.addItem('Simplified', 'simplified')
        self.calculation_method.setToolTip(
            'Detailed: manufacturer-informed installed-condition corrections. '
            'Simplified: free-state O-ring section for squeeze and gland fill.')
        self.application.addItem('Static', 'static')
        self.application.addItem('Dynamic (reciprocating)', 'dynamic')
        self.configuration.addItem('Piston groove (male)', 'male')
        self.configuration.addItem('Cylinder groove (female)', 'female')
        self.groove_type.addItem('Rectangular', 'rectangular')
        self.groove_type.addItem('Double dovetail', 'dovetail')
        self.entry_mode.addItem('OD', 'gland_od')
        self.entry_mode.addItem('Depth', 'rod_and_depth')
        self.female_entry_mode.addItem('ID', 'gland_id')
        self.female_entry_mode.addItem('Depth', 'cylinder_and_depth')
        self.ring_size.addItem('Manual entry', None)
        for size in self.as568_sizes:
            self.ring_size.addItem(size.label, size.dash)
        self.ring_size.setMaxVisibleItems(20)
        # Prevent long dropdown item texts from enlarging the six-column
        # Application setup grid. Actual widths remain Designer-owned.
        for selector in (self.calculation_method, self.application,
                         self.configuration, self.groove_type,
                         self.entry_mode, self.female_entry_mode,
                         self.ring_size):
            selector.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            selector.setMinimumContentsLength(8)
        self.ring_size.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Keep the O-ring selector and its guide button together at the left
        # of their wider grid column, aligned with the O-ring heading.
        for name in ('oringHeaderLayout', 'oringGuideLayout'):
            get(name, QHBoxLayout).setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.rows = {}
        self.female_rows = {}
        self.shared_rows = {}
        male = ('gland_od','direct_rod_od','rod_od','groove_depth',
                'cylinder_id','ring_id','section')
        female = ('gland_id','direct_cylinder_id','cylinder_id',
                  'groove_depth','rod_od')
        shared = ('width','radius','entrance_radius','rect_angle','angle')
        for stem,names,mapping in (('male',male,self.rows),
                                   ('female',female,self.female_rows),
                                   ('shared',shared,self.shared_rows)):
            for key in names:
                container=get(f'dim_{stem}_{key}')
                nominal=get(f'spin_{stem}_{key}_nom',AdaptiveSpinBox)
                tolerance=get(f'spin_{stem}_{key}_tol',AdaptiveSpinBox)
                angle=key in ('rect_angle','angle')
                row = BoundDimensionRow(container,nominal,tolerance,
                    on_change=self._recalculate, signed=key=='rect_angle')
                # Only physically positive linear dimensions treat a lone
                # zero limit as incomplete on an explicit mode conversion.
                # Radii and both flank angles retain literal zero endpoints.
                row.zero_limit_is_incomplete = key in (
                    'gland_od', 'direct_rod_od', 'rod_od', 'groove_depth',
                    'cylinder_id', 'ring_id', 'section', 'gland_id',
                    'direct_cylinder_id', 'width')
                mapping[key] = row
                # Qt Designer owns the approved 106px input boxes and
                # 92px +/- / Limits selector; only values are converted here.
                base = f'{stem}_{key}'
                row.mode_sym = get(f'mode_{base}_sym', QPushButton)
                row.mode_limits = get(f'mode_{base}_limits', QPushButton)
                row.nominal_stack = get(f'nominal_stack_{base}', QStackedWidget)
                row.mode_stack = get(f'tolerance_stack_{base}', QStackedWidget)
                # Both full-sized input areas must exactly match the nominal
                # spinbox's native Windows or offscreen height. Qt Designer
                # owns their widths, locations, and the middle toggle.
                native_row_height = nominal.sizeHint().height()
                row.nominal_stack.setFixedHeight(native_row_height)
                row.mode_stack.setFixedHeight(native_row_height)
                get(f'tolerance_mode_{base}').setFixedHeight(native_row_height)
                row.limit_min = get(f'limit_{base}_min', AdaptiveSpinBox)
                row.limit_max = get(f'limit_{base}_max', AdaptiveSpinBox)
                # Use the exact same native arrowed spinbox and units as the
                # symmetrical inputs. MIN/MAX appears on its right, before
                # the stepper arrows, without obscuring the dimension value.
                for which, editor in (('min', row.limit_min),
                                      ('max', row.limit_max)):
                    editor.setFixedHeight(native_row_height)
                    editor.setSuffix(nominal.suffix())
                    editor.setSingleStep(nominal.singleStep())
                    editor.set_display_decimals(
                        1 if angle else nominal.minimum_display_decimals)
                    editor.lineEdit().setTextMargins(0, 0, 21, 0)
                    tag = get(f'limit_tag_{base}_{which}', QLabel)
                    tag.setAttribute(
                        Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                    tag.raise_()
                row.limit_mode = False
                row.limits_initialized = False
                row.field_name = get(f'label_{base}', QLabel).text()
                # Native spinboxes retain typed precision and units and only
                # commit their user-edited values once per completed edit.
                row.limit_min.setKeyboardTracking(False)
                row.limit_max.setKeyboardTracking(False)
                row.limit_min.valueChanged.connect(self._recalculate)
                row.limit_max.valueChanged.connect(self._recalculate)
                row.mode_sym.clicked.connect(
                    lambda checked=False, target=row:
                    self._set_tolerance_mode(target, False))
                row.mode_limits.clicked.connect(
                    lambda checked=False, target=row:
                    self._set_tolerance_mode(target, True))
                if angle:
                    row.set_display_decimals(1)
                # Keep visible numeric zeros at startup and after Reset
                # Dimensions. Optional radii, wall-angle and dovetail angle all
                # remain user-editable with an explicit zero starting value.
                nominal.setToolTip('Nominal dimension')
                tolerance.setToolTip('Symmetrical ± tolerance')

        self.ring_group = get('ring_group', QGroupBox)
        # Designer owns this header: never detach and float its label at
        # runtime.  A fixed-size match slot beside the O-ring selector means
        # that toggling a catalogue match cannot change any panel's height.
        self.match_slot.setFixedHeight(17)
        self.match_note.setFixedHeight(17)
        self.match_note.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.match_note.setStyleSheet('color:#18805b; font-size:10px; font-weight:600;')
        self.match_note.hide()
        # Stacked pages otherwise consume surplus height when an AS568
        # selection changes child size hints. Preserve the user's chosen
        # Designer heights and control spacing: constrain only expansion.
        for widget in (get('setup_group',QGroupBox),self.entry_mode_stack,
                       self.gland_entry,self.female_gland_entry,
                       self.male_group,self.female_group,self.ring_group,
                       get('shared_group',QGroupBox),get('input_panel')):
            policy = widget.sizePolicy()
            if policy.verticalPolicy() != QSizePolicy.Policy.Fixed:
                policy.setVerticalPolicy(QSizePolicy.Policy.Maximum)
                widget.setSizePolicy(policy)
        # Slightly larger note, with a modestly condensed font so the agreed
        # wording still fits on one line in the fixed-width Designer frame.
        self.shared_note.setFixedHeight(17)
        self.shared_note.setStyleSheet('color:#667c94;')
        note_font = self.shared_note.font()
        note_font.setPixelSize(10)
        note_font.setStretch(88)
        self.shared_note.setFont(note_font)
        self.shared_note.setWordWrap(False)
        get('window_title',QLabel).setStyleSheet('font-size:19px; font-weight:700; color:#123b6c;')
        get('version_label',QLabel).setStyleSheet('color:#6c7e94; font-size:11px;')
        get('version_label',QLabel).setText('v' + APP_VERSION)
        self.calculation_method_info_button.setIcon(QIcon(str(icon_dir / 'info-guide.png')))
        self.calculation_method_info_button.setIconSize(QSize(13, 13))
        self.calculation_method_info_button.setToolTip('About calculation methods')
        self.calculation_method_info_button.clicked.connect(self._show_calculation_method_info)
        self.guide_button.setToolTip('Open O-Ring Size Reference (currently AS568 sizes)')
        self.guide_button.setIcon(QIcon(str(icon_dir / 'info-guide.png')))
        self.guide_button.setIconSize(QSize(18, 18))
        self.settings_button.setIcon(QIcon(str(icon_dir / 'settings-gear.png')))
        self.settings_button.setIconSize(QSize(18, 18))
        self.settings_button.setToolTip('Settings · assumptions, references, updates and about')
        self.settings_button.setStyleSheet('''QPushButton#settings_button {
            background: transparent; border: 1px solid transparent;
            border-radius: 5px; min-height: 0px; padding: 0px;
        } QPushButton#settings_button:hover {
            background: #e5f1fc; border: 1px solid #bfd4e9;
        }''')
        self.settings_button.clicked.connect(self._show_settings)
        get('placeholder_title',QLabel).setAlignment(Qt.AlignmentFlag.AlignCenter)
        get('placeholder_note',QLabel).setAlignment(Qt.AlignmentFlag.AlignCenter)
        get('placeholder_note',QLabel).setWordWrap(True)
        get('placeholder_title',QLabel).setStyleSheet('color:#436789; font-size:13px; font-weight:600;')
        get('placeholder_note',QLabel).setStyleSheet('color:#71879c; font-size:11px;')
        self.guide_placeholder.setStyleSheet("""QFrame#guide_placeholder {
            background:#f7fafc; border:1px dashed #b5c7d9; border-radius:5px;
        }""")
        # Eight user-authored SolidWorks reference sketches. A new picture is
        # chosen for each combination; no engineering dimension is drawn from
        # the current numerical values, and no calculation changes occur.
        guide_directory = Path(__file__).resolve().parents[1] / 'resources' / 'guides'
        guide_files = {
            ('male', 'rectangular', 'gland_od'): 'piston_rectangular_od.png',
            ('male', 'rectangular', 'rod_and_depth'): 'piston_rectangular_depth.png',
            ('male', 'dovetail', 'gland_od'): 'piston_dovetail_od.png',
            ('male', 'dovetail', 'rod_and_depth'): 'piston_dovetail_depth.png',
            ('female', 'rectangular', 'gland_id'): 'cylinder_rectangular_id.png',
            ('female', 'rectangular', 'cylinder_and_depth'): 'cylinder_rectangular_depth.png',
            ('female', 'dovetail', 'gland_id'): 'cylinder_dovetail_id.png',
            ('female', 'dovetail', 'cylinder_and_depth'): 'cylinder_dovetail_depth.png',
        }
        self._reference_pixmaps = {state: QPixmap(str(guide_directory / filename))
                                   for state, filename in guide_files.items()}
        missing = [filename for state, filename in guide_files.items()
                   if self._reference_pixmaps[state].isNull()]
        if missing:
            raise RuntimeError('Missing or invalid dimension guide images: ' + ', '.join(missing))
        self.guide_picture = QLabel(self.guide_placeholder)
        self.guide_picture.setObjectName('guide_picture')
        self.guide_picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.guide_picture.setMinimumSize(0, 0)
        self.guide_picture.setSizePolicy(QSizePolicy.Policy.Expanding,
                                         QSizePolicy.Policy.Expanding)
        get('placeholderLayout',QVBoxLayout).insertWidget(0,self.guide_picture,1)
        self.trace_button.clicked.connect(self._show_tolerance_trace)
        self.snapshot_button.setStyleSheet("""QPushButton#snapshot_button {
            color:#176bc0; background:#f3f8fe; border:1px solid #bed4ee; padding:3px 10px;
        } QPushButton#snapshot_button:hover {background:#e3f1fd;}""")
        self.save_snapshot_button.setStyleSheet("""QPushButton#save_snapshot_button {
            color:white; background:#176bc0; border:1px solid #176bc0; padding:3px 12px;
        } QPushButton#save_snapshot_button:hover {background:#0e5ba7;}
        QPushButton#save_snapshot_button:disabled {
            color:#8795a5; background:#eff2f5; border:1px solid #c4cdd8;
        }""")
        self.reset_button.setToolTip('Clear all entered dimensions and tolerances; keep the selected application and geometry.')
        self.reset_button.clicked.connect(self._reset_dimensions)
        self.snapshot_button.clicked.connect(self._copy_snapshot)
        self.save_snapshot_button.clicked.connect(self._save_snapshot)
        self.guide_button.clicked.connect(self._show_size_guide)

        self.overview_cells={}
        for key,part in (('Squeeze','squeeze'),('Fit','fit'),('Gland fill','fill')):
            name=get(f'overview_{part}_name',QLabel)
            name.setStyleSheet('color:#17436b; font-weight:600;')
            # Preserve the released compact results-row presentation.
            # The full criterion stays visible without line wrapping.
            name.setWordWrap(False)
            self.overview_cells[(key,0)]=name
            for col in (1,2,3,4):
                cell=get(f'overview_{part}_{col}',QLabel)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setStyleSheet('font-size:12px;')
                self.overview_cells[(key,col)]=cell
        for col in range(5):
            get(f'overview_header_{col}',QLabel).setStyleSheet(
                'color:#657c94; font-size:11px; font-weight:600;')
        # Preserve the 140px Minimum/Nominal/Maximum column-centre spacing.
        # Inset each numerical label's text by 8px (16px left content margin)
        # so the left edge of 'Nominal' aligns with the Dimension Guide frame.
        # Adjust label contents only; never change the grid cell geometry.
        for col in (1, 2, 3):
            get(f'overview_header_{col}', QLabel).setContentsMargins(16, 0, 0, 0)
            for part in ('squeeze', 'fit', 'fill'):
                get(f'overview_{part}_{col}', QLabel).setContentsMargins(16, 0, 0, 0)
        # Shift rendered Status text 20px right so its visual centre equals
        # the centre of Save PNG, while keeping the results grid untouched.
        status_header = get('overview_header_4', QLabel)
        status_header.setFixedWidth(102)  # Existing released Status-column width.
        status_header.setContentsMargins(40, 0, 0, 0)
        for col in range(6): self.overview_grid.setColumnStretch(col,0)
        for col,width in ((0,326),(1,136),(2,136),(3,136),(5,102)):
            self.overview_grid.setColumnMinimumWidth(col,width)
        self.overview_grid.setColumnStretch(4,1)
        for row_index in (1,2,3):
            self.overview_grid.setRowMinimumHeight(row_index,39)
        get('overview_header_0',QLabel).setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col in (1,2,3,4): get(f'overview_header_{col}',QLabel).setAlignment(Qt.AlignmentFlag.AlignCenter)
        for key in ('squeeze','fit','fill'):
            status = get(f'overview_{key}_4', QLabel)
            status.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            status.setFixedWidth(102)  # Keep oversized offscreen font hints from widening the grid.
            status.setContentsMargins(40, 3, 0, 0)
        self.overview_note.setStyleSheet('color:#657a91; font-size:11px;')
        self.overview_note.setWordWrap(False)
        self.overview_note.hide()

        self.female_group.hide()

        # Retain the Stage 9 model for drawing data/focus tests, but do not
        # display the sketch until it is reviewed and properly dimensioned.
        self.diagram=GrooveDiagram(self)
        self.diagram.hide()
        self._register_focus_inputs()
        self._set_dimension_tab_order()
        self.statusBar().showMessage(
            'Example inputs only; not approved dimensions. Mouse wheel cannot change dimension values.')
        self.entry_mode.currentIndexChanged.connect(self._change_mode)
        self.female_entry_mode.currentIndexChanged.connect(self._change_female_mode)
        self.configuration.currentIndexChanged.connect(self._change_configuration)
        self.groove_type.currentIndexChanged.connect(self._change_groove)
        self.application.currentIndexChanged.connect(self._recalculate)
        self.calculation_method.currentIndexChanged.connect(self._recalculate)
        self.ring_size.currentIndexChanged.connect(self._change_ring_size)
        self._change_groove()
        # Qt Designer is allowed to save either stacked page as the visible
        # preview. Set the runtime page from the actual application selection,
        # rather than relying on QUiLoader's initial currentIndex.
        # This also ensures correct male/female hardware visibility at startup.
        self._change_configuration()

    @staticmethod
    def _set_converted_spin_value(spin, exact: Decimal):
        """Write a converted value without losing a needed half-micro unit.

        Qt's QDoubleSpinBox rounds inputs to its configured decimals. Raise
        that display/storage precision only when the computed result needs
        it. Never update the screen dimensions, font or report layout.
        """
        digits = max(0, -exact.normalize().as_tuple().exponent)
        if digits > 12:
            raise ValueError('Converted tolerance exceeds 12 decimal places.')
        with QSignalBlocker(spin):
            spin.setDecimals(max(6, digits))
            spin.setValue(float(exact))

    def _set_tolerance_mode(self, row, use_limits: bool):
        """Convert this row's *current* visible entry on every mode switch.

        +/- -> Min/Max: nominal - tolerance, nominal + tolerance.
        Min/Max -> +/-: (minimum + maximum)/2, (maximum - minimum)/2.
        For positive-only dimensions, a lone zero endpoint denotes an
        incomplete entry only during this explicit representation switch.
        The screen layout, engineering input model and report remain unchanged.
        """
        if row.limit_mode == use_limits:
            return

        # The toggles are NoFocus buttons. Commit a pending typed spinbox
        # edit before reading it (keyboardTracking is deliberately False).
        source = ((row.nominal, row.tolerance)
                  if use_limits else (row.limit_min, row.limit_max))
        for spin in source:
            spin.interpretText()
        first, second = (Decimal(str(spin.value())) for spin in source)

        if use_limits:
            converted = (first - second, first + second)
            targets = (row.limit_min, row.limit_max)
        else:
            if row.zero_limit_is_incomplete and (
                    (first == 0 and second > 0) or
                    (second == 0 and first > 0)):
                converted = (max(first, second), Decimal(0))
            else:
                if first > second:
                    # A reversed range has no equivalent non-negative tolerance.
                    # Keep the erroneous limits visible for correction.
                    row.mode_limits.setChecked(True)
                    self._recalculate()
                    return
                converted = ((first + second)/2, (second - first)/2)
            targets = (row.nominal, row.tolerance)

        # Preflight both results before changing EITHER field. In particular,
        # a 12-place pair may need a 13th decimal at its midpoint; never
        # partly update one field before failing on the other.
        for editor, value in zip(targets, converted):
            too_precise = max(0, -value.normalize().as_tuple().exponent) > 12
            out_of_range = not (
                Decimal(str(editor.minimum())) <= value <=
                Decimal(str(editor.maximum())))
            if too_precise or out_of_range:
                (row.mode_sym if not row.limit_mode
                 else row.mode_limits).setChecked(True)
                reason = ('requires more than 12 decimal places'
                          if too_precise else
                          'is outside the permitted input range')
                self.statusBar().showMessage(
                    f'Cannot convert {row.field_name}: the resulting '
                    f'dimension {reason}.')
                return

        for spin, exact in zip(targets, converted):
            self._set_converted_spin_value(spin, exact)

        row.limits_initialized = True
        row.limit_mode = use_limits
        row.mode_sym.setChecked(not use_limits)
        row.mode_limits.setChecked(use_limits)
        row.nominal_stack.setCurrentIndex(1 if use_limits else 0)
        row.mode_stack.setCurrentIndex(1 if use_limits else 0)
        self._recalculate()

    def _has_active_limits(self):
        """Only dimensions used in this selected geometry contribute limits."""
        female = self.configuration.currentData() == 'female'
        mode = (self.female_entry_mode.currentData() if female
                else self.entry_mode.currentData())
        if female:
            names = (('rod_od', 'gland_id', 'direct_cylinder_id')
                     if mode == 'gland_id' else
                     ('rod_od', 'cylinder_id', 'groove_depth'))
            active = self.female_rows
        else:
            names = (('gland_od', 'direct_rod_od', 'cylinder_id')
                     if mode == 'gland_od' else
                     ('rod_od', 'groove_depth', 'cylinder_id'))
            active = self.rows
        selected = [active[name] for name in names]
        selected.extend(self.shared_rows[name] for name in
            ('width', 'radius', 'entrance_radius',
             'angle' if self.groove_type.currentData() == 'dovetail'
             else 'rect_angle'))
        selected.extend(self.rows[name] for name in ('ring_id', 'section'))
        return any(row.limit_mode for row in selected)

    def _register_focus_inputs(self):
        self._focus_fields={}
        for rows in (self.rows,self.female_rows,self.shared_rows):
            for key,row in rows.items():
                for spin in (row.nominal, row.limit_min,
                             row.tolerance, row.limit_max):
                    self._focus_fields[spin]=key
                    spin.installEventFilter(self)

    def _set_dimension_tab_order(self):
        """Preserve the original dimension sequence in every tolerance mode.

        Each row has two alternate editors for its first value (nominal/min)
        and two for its second (tolerance/max). Include all four in the
        focus chain, in that order. Qt skips hidden stacked-page controls,
        inactive geometry rows and disabled catalogue editors automatically.
        No rebuild of the chain is required when a representation changes.
        """
        ordered_rows = [
            self.rows[key] for key in
            ('cylinder_id', 'direct_rod_od', 'rod_od',
             'gland_od', 'groove_depth')
        ]
        ordered_rows.extend(self.female_rows[key] for key in
            ('direct_cylinder_id', 'cylinder_id', 'rod_od',
             'gland_id', 'groove_depth'))
        ordered_rows.extend(self.shared_rows[key] for key in
            ('width', 'radius', 'entrance_radius', 'rect_angle', 'angle'))
        ordered_rows.extend(self.rows[key] for key in ('ring_id', 'section'))

        sequence = [
            self.calculation_method, self.application, self.configuration,
            self.groove_type, self.entry_mode, self.female_entry_mode,
            self.ring_size, self.guide_button,
        ]
        for row in ordered_rows:
            sequence.extend((row.nominal, row.limit_min,
                             row.tolerance, row.limit_max))
        for current, following in zip(sequence, sequence[1:]):
            self.setTabOrder(current, following)

    def eventFilter(self,obj,event):
        if (event.type()==QEvent.Type.FocusIn and
                obj in getattr(self,'_focus_fields',{}) and
                hasattr(self,'diagram')):
            self.diagram.set_active_key(self._focus_fields[obj])
        return super().eventFilter(obj,event)

    @staticmethod
    def _fill_unused_dimension(source, target):
        """Carry a physical dimension into an unused counterpart only.

        A source entered as Min/Max retains its exact two limits and selected
        representation in the new configuration, without overwriting any
        previously entered destination dimension.
        """
        if target.effective_nominal() != 0 or source.effective_nominal() <= 0:
            return
        try:
            dim = source.dimension()
        except ValueError:
            return
        with QSignalBlocker(target.nominal):
            target.nominal.setValue(dim.nominal)
        if target.tolerance.value() == 0:
            with QSignalBlocker(target.tolerance):
                target.tolerance.setValue(dim.tolerance)
        if source.limit_mode:
            for target_spin, source_spin in (
                (target.limit_min, source.limit_min),
                (target.limit_max, source.limit_max),
            ):
                with QSignalBlocker(target_spin):
                    target_spin.setValue(source_spin.value())
            target.limits_initialized = True
            target.limit_mode = True
            target.nominal_stack.setCurrentIndex(1)
            target.mode_stack.setCurrentIndex(1)
            target.mode_sym.setChecked(False)
            target.mode_limits.setChecked(True)

    def _fill_other_configuration(self, old_configuration, new_configuration):
        """Carry common hardware inputs into empty fields of the new view.

        Groove OD/ID values are independent; a first-use radial groove depth
        can be carried across to the corresponding empty depth field. The
        source and destination remain separately editable afterwards.
        """
        if old_configuration == 'male' and new_configuration == 'female':
            # Prefer the currently selected male mode, with fallback if blank.
            piston = (self.rows['direct_rod_od'] if
                      self.entry_mode.currentData() == 'gland_od' else self.rows['rod_od'])
            alternate = (self.rows['rod_od'] if piston is self.rows['direct_rod_od']
                         else self.rows['direct_rod_od'])
            if piston.nominal.value() <= 0:
                piston = alternate
            self._fill_unused_dimension(piston, self.female_rows['rod_od'])
            cylinder = self.rows['cylinder_id']
            self._fill_unused_dimension(cylinder, self.female_rows['direct_cylinder_id'])
            self._fill_unused_dimension(cylinder, self.female_rows['cylinder_id'])
            # The depth entries have identical physical units and meanings.
            # Retain the entered depth when switching component, without
            # replacing a depth already entered for the female groove.
            self._fill_unused_dimension(self.rows['groove_depth'],
                                        self.female_rows['groove_depth'])
        elif old_configuration == 'female' and new_configuration == 'male':
            piston = self.female_rows['rod_od']
            self._fill_unused_dimension(piston, self.rows['direct_rod_od'])
            self._fill_unused_dimension(piston, self.rows['rod_od'])
            cylinder = (self.female_rows['direct_cylinder_id'] if
                        self.female_entry_mode.currentData() == 'gland_id'
                        else self.female_rows['cylinder_id'])
            alternate = (self.female_rows['cylinder_id'] if cylinder is
                         self.female_rows['direct_cylinder_id'] else
                         self.female_rows['direct_cylinder_id'])
            if cylinder.nominal.value() <= 0:
                cylinder = alternate
            self._fill_unused_dimension(cylinder, self.rows['cylinder_id'])
            # Female Depth -> Male Depth is the explicit regression case;
            # use the same first-use, no-overwrite rule in both directions.
            self._fill_unused_dimension(self.female_rows['groove_depth'],
                                        self.rows['groove_depth'])

    def _change_configuration(self, *_):
        selected = self.configuration.currentData()
        previous = self._previous_configuration
        if previous is not None and previous != selected:
            self._fill_other_configuration(previous, selected)
        self._previous_configuration = selected
        female = selected == "female"
        self.male_group.setVisible(not female)
        self.female_group.setVisible(female)
        # Resolve by widget, not page index: Designer can reorder stack pages.
        self.entry_mode_stack.setCurrentWidget(
            self.female_entry_mode if female else self.entry_mode)
        self._update_groove_entry_rows()
        self._refresh_dimension_guide()
        self._update_intro()
        self._recalculate()

    def _update_intro(self):
        # Retained as a no-op for the configuration callbacks; selectors now
        # communicate all setup information without a duplicate subtitle.
        pass

    def _change_groove(self, *_):
        dovetail = self.groove_type.currentData() == "dovetail"
        self.shared_form.setRowVisible(self.shared_rows["angle"].widget, dovetail)
        self.shared_form.setRowVisible(self.shared_rows["radius"].widget, True)
        self.shared_form.setRowVisible(self.shared_rows["entrance_radius"].widget, True)
        self.shared_form.setRowVisible(self.shared_rows["rect_angle"].widget, not dovetail)
        self._update_groove_entry_rows()
        self._refresh_dimension_guide()
        # A real depth datum is needed for an angled/radiused section, also in
        # direct gland-diameter mode. Keep it visible for both groove types.
        self.male_direct_form.setRowVisible(self.rows["direct_rod_od"].widget, True)
        self.female_direct_form.setRowVisible(self.female_rows["direct_cylinder_id"].widget, True)
        self.shared_note.setText(
            'Width is measured between theoretical sharp intersections (opening radii excluded where present).'
        )
        self.shared_note.setToolTip(
            'Groove width is measured at the opening, between the theoretical '
            'intersections of the side walls with the component surface, '
            'before applying the opening corner radii.'
        )
        self._update_intro()
        self._recalculate()

    def _refresh_dimension_guide(self):
        """Show the user's matching reference sketch for all eight combinations."""
        if not hasattr(self, 'guide_picture'):
            return
        female = self.configuration.currentData() == 'female'
        mode = self.female_entry_mode.currentData() if female else self.entry_mode.currentData()
        state = (self.configuration.currentData(), self.groove_type.currentData(), mode)
        source = self._reference_pixmaps.get(state)
        if source is None or source.isNull():
            raise RuntimeError('No dimension guide exists for: ' + repr(state))
        self.guide_picture.setPixmap(source.scaled(
            408, 405, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        self.guide_picture.show()
        self.guide_picture.setToolTip(
            f'{self.configuration.currentText()} · {self.groove_type.currentText()} · '
            f'{self.female_entry_mode.currentText() if female else self.entry_mode.currentText()}')
        self.findChild(QLabel, 'placeholder_title').hide()
        note = self.findChild(QLabel, 'placeholder_note')
        note.setText('Indicative geometry only - not to scale')
        note.show()

    def _update_groove_entry_rows(self):
        """Show the selected groove dimension in Groove Dimensions only.

        Preserve the existing field widgets and their live model bindings.
        The other three rows are completely hidden (no blank layout rows).
        """
        female = self.configuration.currentData() == 'female'
        male_direct = self.entry_mode.currentData() == 'gland_od'
        female_direct = self.female_entry_mode.currentData() == 'gland_id'
        for row, shown in (
            (self.rows['gland_od'], not female and male_direct),
            (self.rows['groove_depth'], not female and not male_direct),
            (self.female_rows['gland_id'], female and female_direct),
            (self.female_rows['groove_depth'], female and not female_direct),
        ):
            self.shared_form.setRowVisible(row.widget, shown)

    @staticmethod
    def _format_snapshot_dimension(row):
        """Give every physical input its own unit; omit a genuinely zero tolerance.

        The UI stores six decimal places. Suppress only values rounding to
        0.000000 at that storage resolution. Never omit a small non-zero
        tolerance or lose significant user-entered decimal places.
        """
        dimension = row.dimension()
        nominal = format_input(dimension.nominal)
        tolerance = dimension.tolerance
        if tolerance > 0.0000005:
            return f'{nominal} {chr(177)} {format_input(tolerance)}'
        return nominal

    def _capture_inputs(self):
        pairs = []
        female = self.configuration.currentData() == 'female'
        rows = self.female_rows if female else self.rows
        mode = self.female_entry_mode.currentData() if female else self.entry_mode.currentData()
        keys = (('rod_od','gland_id','direct_cylinder_id') if mode=='gland_id' else
                ('rod_od','cylinder_id','groove_depth') if female else
                ('gland_od','direct_rod_od','cylinder_id') if mode=='gland_od' else
                ('rod_od','groove_depth','cylinder_id'))
        names = {'rod_od':'Piston OD','gland_od':'Groove OD','gland_id':'Groove ID',
                 'direct_rod_od':'Piston OD','direct_cylinder_id':'Cylinder ID',
                 'groove_depth':'Groove depth','cylinder_id':'Cylinder ID',
                 'width':'Groove width','radius':'Base radius',
                 'entrance_radius':'Opening radius','angle':'Dovetail angle',
                 'rect_angle':'Wall angle','ring_id':'O-ring ID','section':'O-ring section'}
        for key in keys:
            row=rows[key]
            pairs.append((names[key]+' (in)', self._format_snapshot_dimension(row)))
        for key in ('width','radius','entrance_radius',
                    'angle' if self.groove_type.currentData()=='dovetail' else 'rect_angle'):
            row=self.shared_rows[key]
            pairs.append((names[key]+(' (°)' if key in ('angle','rect_angle') else ' (in)'),
                          self._format_snapshot_dimension(row)))
        for key in ('ring_id','section'):
            row=self.rows[key]
            pairs.append((names[key]+' (in)', self._format_snapshot_dimension(row)))
        return pairs

    def _snapshot_pixmap(self):
        """Generate the clean report without showing any preview window."""
        if self._last_result is None or self._last_screening is None:
            return None
        result = self._last_result
        checks = self._last_screening.checks
        fit = 'OD interference (%)' if self.configuration.currentData() == 'female' else 'ID stretch (%)'
        def vals(measure):
            return tuple(format_result(getattr(measure, key),'percent') + '%'
                         for key in ('minimum','nominal','maximum'))
        rows = [('Squeeze (%)', vals(result.squeeze_percent), checks[0]),
                (fit, vals(result.stretch_percent), checks[1]),
                ('Gland fill (%)', vals(result.gland_fill_percent), checks[2])]
        selected = self.ring_size.currentData()
        size = 'Manual' if selected is None else f'AS568{selected}'
        desc = (f'{self.application.currentText()}  •  {self.configuration.currentText()}  •  '
                f'{self.groove_type.currentText()}  •  O-ring: {size}')
        female = self.configuration.currentData() == 'female'
        state = (self.configuration.currentData(), self.groove_type.currentData(),
                 self.female_entry_mode.currentData() if female else self.entry_mode.currentData())
        sketch = self._reference_pixmaps[state]
        entry_mode = self.female_entry_mode if female else self.entry_mode
        context = [
            ('Calculation method', self.calculation_method.currentText()),
            ('Application', self.application.currentText()),
            ('Gland type', self.configuration.currentText()),
            ('Groove profile', self.groove_type.currentText()),
            ('Groove dimension', entry_mode.currentText()),
            ('O-ring size', self.ring_size.currentText() if selected is not None else 'Manual'),
        ]
        # Reuse the same correlated witnesses shown in the main results table.
        details = [
            [f'{self._correlated_physical_value("Squeeze", case):.3f} in'
             for case in ('Minimum','Nominal','Maximum')],
            [f'{self._correlated_physical_value("Fit", case):.3f} in'
             for case in ('Minimum','Nominal','Maximum')],
            None,
        ]
        return render_snapshot(desc, rows, self._last_screening, self._capture_inputs(),
                               sketch=sketch, context=context, detail_rows=details)

    def _copy_snapshot(self):
        from PySide6.QtWidgets import QApplication
        image = self._snapshot_pixmap()
        if image is not None and not image.isNull():
            QApplication.clipboard().setPixmap(image)
            self.statusBar().showMessage('Calculation snapshot copied to clipboard.', 5000)

    def _save_snapshot(self):
        from PySide6.QtWidgets import QFileDialog
        image = self._snapshot_pixmap()
        if image is None or image.isNull():
            return
        method = 'Simplified' if self.calculation_method.currentData() == 'simplified' else 'Detailed'
        application = 'Dynamic' if self.application.currentData() == 'dynamic' else 'Static'
        component = 'Cylinder' if self.configuration.currentData() == 'female' else 'Piston'
        profile = 'Double Dovetail' if self.groove_type.currentData() == 'dovetail' else 'Rectangular'
        designation = self.ring_size.currentText() if self.ring_size.currentData() is not None else ''
        suggested = ' - '.join(part for part in (method,application,component,profile,designation) if part)
        suggested = re.sub(r'[^A-Za-z0-9 ._\-]', '-', suggested) + '.png'
        path, _ = QFileDialog.getSaveFileName(self, 'Save calculation snapshot',
                                              suggested, 'PNG images (*.png)')
        if path:
            try:
                save_snapshot_to_png(image, path)
            except OSError as exc:
                self.statusBar().showMessage(str(exc), 10000)
                return
            self.statusBar().showMessage(f'Snapshot saved: {path}', 5000)

    def _reset_dimensions(self, *_):
        """Set all numeric input values back to zero without changing the
        selected seal configuration.

        This is not a reset of screening criteria, application or groove type.
        """
        for rows in (self.rows, self.female_rows, self.shared_rows):
            for row in rows.values():
                for spin in (row.nominal, row.tolerance,
                             row.limit_min, row.limit_max):
                    with QSignalBlocker(spin):
                        spin.setDecimals(6)
                        spin.setValue(0.0)
                row.limit_mode = False
                row.limits_initialized = False
                row.nominal_stack.setCurrentIndex(0)
                row.mode_stack.setCurrentIndex(0)
                row.mode_sym.setChecked(True)
                row.mode_limits.setChecked(False)
        # Drop any selected AS568 designation after clearing the dimensions.
        self.ring_size.setCurrentIndex(0)
        self._change_ring_size()
        self._recalculate()

    def _missing_required_dimensions(self):
        female = self.configuration.currentData() == 'female'
        mode = self.female_entry_mode.currentData() if female else self.entry_mode.currentData()
        if female:
            keys = ('rod_od', 'direct_cylinder_id', 'gland_id') if mode == 'gland_id' else (
                   'rod_od', 'cylinder_id', 'groove_depth')
            active = self.female_rows
        else:
            keys = ('gland_od', 'direct_rod_od', 'cylinder_id') if mode == 'gland_od' else (
                   'rod_od', 'groove_depth', 'cylinder_id')
            active = self.rows
        missing = [k for k in keys if active[k].effective_nominal() <= 0]
        missing.extend(k for k in ('width',) if self.shared_rows[k].effective_nominal() <= 0)
        if self.groove_type.currentData() == 'dovetail' and self.shared_rows['angle'].effective_nominal() <= 0:
            missing.append('angle')
        missing.extend(k for k in ('ring_id','section') if self.rows[k].effective_nominal() <= 0)
        return missing

    def _align_screening_numbers(self, pending):
        """Top-align placeholder dashes with the row label and status.

        The minimum/nominal/maximum cells normally display two lines of
        calculated information centred vertically. A lone dash otherwise
        looks lower than the row label and status. Restore centre alignment
        for real percentage results without changing their layout.
        """
        alignment = (Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
                     if pending else Qt.AlignmentFlag.AlignCenter)
        for name in ('Squeeze', 'Fit', 'Gland fill'):
            for col in (1, 2, 3):
                cell = self.overview_cells[(name, col)]
                cell.setAlignment(alignment)
                # Preserve the matching 8px visible text offset after each
                # pending/valid recalculation, as well as at initial setup.
                cell.setContentsMargins(16, 3 if pending else 0, 0, 0)

    def _show_pending_results(self):
        """Neutral initial/reset state, distinct from an invalid calculation."""
        self._last_inputs = None
        self._last_evaluation = None
        self._last_result = None
        self._last_screening = None
        self.overview_note.clear()
        self.overview_note.hide()
        self.statusBar().showMessage('Enter the required dimensions to calculate.')
        self._align_screening_numbers(pending=True)
        for name in ('Squeeze', 'Fit', 'Gland fill'):
            title = (('O-ring OD interference' if self.configuration.currentData() == 'female'
                      else 'O-ring ID stretch') if name == 'Fit'
                     else ('O-ring squeeze' if name == 'Squeeze' else name))
            self.overview_cells[(name, 0)].setText(self._screening_label_markup(title, ' '))
            for col in range(1, 4):
                self.overview_cells[(name, col)].setText('—')
            cell = self.overview_cells[(name, 4)]
            cell.setText('—')
            cell.setStyleSheet('color:#7a8a9a;')
            cell.setToolTip('Enter the required dimensions to calculate.')
        self.trace_button.setEnabled(False)
        self.snapshot_button.setEnabled(False)
        self.save_snapshot_button.setEnabled(False)
        self._update_diagram(invalid=True)

    def _make_calculation_method_info_dialog(self):
        """Quiet compact dialog matching Settings / O-Ring Size Reference."""
        dialog = QDialog(self)
        dialog.setObjectName('calculation_method_info_dialog')
        dialog.setWindowTitle(f'Calculation Method | {APP_TITLE}')
        dialog.setFixedWidth(485)

        # Same heading/rule/subtitle positions as Settings and Size Reference.
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(11, 11, 11, 11)
        layout.setSpacing(6)

        heading = QLabel('Calculation Method', dialog)
        heading.setObjectName('method_dialog_heading')
        heading.setStyleSheet('font-size:17px; font-weight:700; color:#164f8a;')
        layout.addWidget(heading)

        rule = QFrame(dialog)
        rule.setObjectName('method_dialog_heading_rule')
        rule.setFrameShape(QFrame.Shape.HLine)
        rule.setFrameShadow(QFrame.Shadow.Plain)
        layout.addWidget(rule)

        app_name = QLabel(APP_TITLE, dialog)
        app_name.setObjectName('method_dialog_app_name')
        app_name.setStyleSheet('color:#71849a; font-size:11px;')
        layout.addWidget(app_name)
        layout.addSpacing(4)

        for title, explanation in (
            ('Detailed',
             'Uses manufacturer-informed installed-condition calculations, '
             'including cross-section and material-area corrections for stretched O-rings.'),
            ('Simplified',
             'Uses the free-state O-ring cross-section for radial squeeze and gland fill.'),
        ):
            title_label = QLabel(title, dialog)
            title_label.setObjectName('method_heading_' + title.lower())
            title_label.setStyleSheet('font-weight:600; color:#164f8a;')
            layout.addWidget(title_label)

            description = QLabel(explanation, dialog)
            description.setObjectName('method_description_' + title.lower())
            description.setWordWrap(True)
            description.setFixedHeight(
                max(description.fontMetrics().height(),
                    description.heightForWidth(dialog.width()-22)))
            layout.addWidget(description)

            if title == 'Detailed':
                layout.addSpacing(4)

        footer = QHBoxLayout()
        close = QPushButton('Close', dialog)
        close.setObjectName('close_method_information')
        set_standard_action_width(close)
        close.setFixedHeight(30)
        close.clicked.connect(dialog.accept)
        footer.addStretch()
        footer.addWidget(close)
        layout.addLayout(footer)
        dialog.adjustSize()
        dialog.setFixedHeight(dialog.sizeHint().height())
        return dialog

    def _show_calculation_method_info(self):
        self._make_calculation_method_info_dialog().exec()

    def _show_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def _show_size_guide(self):
        dialog = SizeGuide(self.as568_sizes, self)
        if dialog.exec() and dialog.chosen_dash is not None:
            index = self.ring_size.findData(dialog.chosen_dash)
            if index >= 0:
                self.ring_size.setCurrentIndex(index)

    def _change_female_mode(self, index):
        # Both entries use the same physical Cylinder ID but separate widgets.
        source = (self.female_rows['cylinder_id'] if index == 0 else
                  self.female_rows['direct_cylinder_id'])
        target = (self.female_rows['direct_cylinder_id'] if index == 0 else
                  self.female_rows['cylinder_id'])
        self._fill_unused_dimension(source, target)
        self.female_gland_entry.setCurrentIndex(index)
        self._update_groove_entry_rows()
        self._refresh_dimension_guide()
        self._recalculate()

    def _change_mode(self, index):
        # Both entries use the same physical Piston OD but separate widgets.
        source = self.rows['rod_od'] if index == 0 else self.rows['direct_rod_od']
        target = self.rows['direct_rod_od'] if index == 0 else self.rows['rod_od']
        self._fill_unused_dimension(source, target)
        self.gland_entry.setCurrentIndex(index)
        self._update_groove_entry_rows()
        self._refresh_dimension_guide()
        self._recalculate()

    def _change_ring_size(self, *_):
        """Apply catalogue dimensions without locking the tolerance-mode toggle.

        AS568 values are never editable when a designation is selected, but
        either nominal +/- tolerance or Min/Max *display* can be chosen for
        each O-ring field independently. On every catalogue selection update
        both representations to the new catalogue endpoints to prevent any
        stale manually entered limits from being used in calculations.
        """
        dash = self.ring_size.currentData()
        manual = dash is None
        if not manual:
            size = next(item for item in self.as568_sizes if item.dash == dash)
            for name, nominal, tolerance in (
                ("ring_id", size.id_in, size.id_tol_in),
                ("section", size.cs_in, size.cs_tol_in),
            ):
                row = self.rows[name]
                for editor, value in (
                    (row.nominal, nominal),
                    (row.tolerance, tolerance),
                    (row.limit_min, nominal - tolerance),
                    (row.limit_max, nominal + tolerance),
                ):
                    with QSignalBlocker(editor):
                        editor.setDecimals(6)  # Catalogue has six-place data
                        editor.setValue(value)
                # The selected representation is preserved on each new
                # designation, but both values are always catalogue-derived.
                row.limits_initialized = True
        for name in ("ring_id", "section"):
            row = self.rows[name]
            for editor in (row.nominal, row.tolerance,
                           row.limit_min, row.limit_max):
                editor.setEnabled(manual)
            # Only the representation toggle remains enabled for a selected
            # catalogue O-ring. No editable dimension can override AS568.
            row.mode_sym.setEnabled(True)
            row.mode_limits.setEnabled(True)
        self._recalculate()

    def _update_manual_match_note(self):
        """Informational only: manual dimensions are never modified or locked."""
        if self.ring_size.currentData() is not None:
            self.match_note.setText('')
            self.match_note.hide()
            return
        id_dim = self.rows['ring_id'].dimension()
        cs_dim = self.rows['section'].dimension()
        matches = matching_sizes(
            self.as568_sizes,
            id_dim.nominal, id_dim.tolerance, cs_dim.nominal, cs_dim.tolerance,
        )
        if matches:
            labels = ', '.join(size.label for size in matches)
            self.match_note.setText(f'✓ {matches[0].label}' if len(matches)==1 else f'✓ {len(matches)} matches')
            self.match_note.setToolTip(f'Manual dimensions match: {labels}. Catalogue size is not selected.')
            self.match_note.show()
        else:
            self.match_note.setText('')
            self.match_note.hide()

    def _show_tolerance_trace(self):
        dialog = self._make_tolerance_trace_dialog()
        if dialog is not None:
            dialog.exec()

    def _make_tolerance_trace_dialog(self):
        """Editable two-tab inspector, keeping complete tolerance witnesses."""
        if self._last_evaluation is None or self._last_result is None:
            return None
        return build_inspect_results(self._last_evaluation, self._last_result,
                                     self.configuration.currentData() == 'female', self._last_inputs, self,
                                     screening=self._last_screening)

    def _collect(self) -> MaleRectangularInputs | FemaleRectangularInputs | MaleDovetailInputs | FemaleDovetailInputs:
        shared = lambda name: self.shared_rows[name].dimension()
        ring_id = self.rows["ring_id"].dimension()
        section = self.rows["section"].dimension()
        dovetail = self.groove_type.currentData() == "dovetail"
        if self.configuration.currentData() == "female":
            dim = lambda name: self.female_rows[name].dimension()
            mode = self.female_entry_mode.currentData()
            if dovetail:
                return FemaleDovetailInputs(
                    rod_od=dim("rod_od"), gland_width=shared("width"),
                    o_ring_id=ring_id, o_ring_section=section,
                    angle_deg=shared("angle"),
                    bottom_radius=shared("radius"), entrance_radius=shared("entrance_radius"), mode=mode,
                    gland_id=dim("gland_id") if mode == "gland_id" else None,
                    cylinder_id=dim("direct_cylinder_id") if mode == "gland_id" else dim("cylinder_id"),
                    groove_depth=dim("groove_depth") if mode == "cylinder_and_depth" else None,
                )
            return FemaleRectangularInputs(
                rod_od=dim("rod_od"), gland_width=shared("width"),
                o_ring_id=ring_id, o_ring_section=section,
                bottom_radius=shared("radius"), entrance_radius=shared("entrance_radius"),
                wall_angle_deg=shared("rect_angle"), mode=mode,
                gland_id=dim("gland_id") if mode == "gland_id" else None,
                cylinder_id=dim("direct_cylinder_id") if mode == "gland_id" else dim("cylinder_id"),
                groove_depth=dim("groove_depth") if mode == "cylinder_and_depth" else None,
            )
        dim = lambda name: self.rows[name].dimension()
        mode = self.entry_mode.currentData()
        if dovetail:
            return MaleDovetailInputs(
                cylinder_id=dim("cylinder_id"), gland_width=shared("width"),
                o_ring_id=ring_id, o_ring_section=section,
                angle_deg=shared("angle"),
                bottom_radius=shared("radius"), entrance_radius=shared("entrance_radius"), mode=mode,
                gland_od=dim("gland_od") if mode == "gland_od" else None,
                rod_od=dim("direct_rod_od") if mode == "gland_od" else dim("rod_od"),
                groove_depth=dim("groove_depth") if mode == "rod_and_depth" else None,
            )
        return MaleRectangularInputs(
            cylinder_id=dim("cylinder_id"), gland_width=shared("width"),
            o_ring_id=ring_id, o_ring_section=section,
            bottom_radius=shared("radius"), entrance_radius=shared("entrance_radius"),
            wall_angle_deg=shared("rect_angle"), mode=mode,
            gland_od=dim("gland_od") if mode == "gland_od" else None,
            rod_od=dim("direct_rod_od") if mode == "gland_od" else dim("rod_od"),
            groove_depth=dim("groove_depth") if mode == "rod_and_depth" else None,
        )

    def _recalculate(self, *_):
        # Manual AS568 matching is advisory. A temporarily reversed Min/Max
        # must be treated as an input error, not an uncaught GUI exception.
        try:
            self._update_manual_match_note()
        except ValueError:
            self.match_note.hide()
        if self._missing_required_dimensions():
            self._show_pending_results()
            return
        try:
            inputs = self._collect()
            method = self.calculation_method.currentData()
            evaluation = calculate_installed(inputs, method=method)
            output = evaluation.results
            female = self.configuration.currentData() == "female"
            screening = screen_rectangular(output, self.application.currentData(), female=female)
        except ValueError as exc:
            self._last_inputs = None
            self._last_evaluation = None
            self._last_result = None
            self._last_screening = None
            self._update_diagram(invalid=True)
            # The fixed-size results panel must not grow for an invalid ring.
            # Show the actual error in the status bar and existing row statuses.
            raw = str(exc).lower()
            if 'stretch exceeds' in raw or 'compression-diameter' in raw or 'parker' in raw:
                reason = 'installed O-ring stretch is outside the supported calculation range'
            elif 'tolerance endpoints' in raw or 'installed condition' in raw:
                reason = 'invalid installed conditions at one or more permitted tolerance combinations'
            elif 'groove' in raw or 'radius' in raw or 'cavity' in raw:
                reason = 'invalid groove geometry'
            else:
                reason = 'invalid input geometry'
            message = (f'Invalid limits: {exc}' if
                       'minimum limit exceeds maximum limit' in raw else
                       f'Cannot evaluate geometry: {reason}.')
            self.overview_note.clear()
            self.overview_note.hide()
            self.statusBar().showMessage(message)
            self._align_screening_numbers(pending=True)
            for name in ('Squeeze','Fit','Gland fill'):
                title = ('O-ring OD interference' if self.configuration.currentData() == 'female'
                         else 'O-ring ID stretch') if name == 'Fit' else ('O-ring squeeze' if name == 'Squeeze' else name)
                label = self.overview_cells[(name,0)]
                label.setText(self._screening_label_markup(title, ' '))
                for col in range(1,4):
                    self.overview_cells[(name,col)].setText(
                        '<span style=\"font-size:12px;\">—</span><br/>'
                        '<span style=\"font-size:10px;\">&#160;</span>')
                status = self.overview_cells[(name,4)]
                status.setText('INVALID')
                status.setStyleSheet('color:#bb2b23;font-weight:700;')
                status.setToolTip(message)
            self.trace_button.setEnabled(False)
            self.snapshot_button.setEnabled(False)
            self.save_snapshot_button.setEnabled(False)
            return
        if self._has_active_limits():
            self.statusBar().showMessage(
                'Limits: Nominal results use the midpoint of entered Min/Max; '
                'all tolerance extrema use the actual entered limits.')
        else:
            self.statusBar().showMessage(
                'Symmetrical: Nominal results use the entered dimensions; '
                'tolerance extrema use nominal ± tolerance.')
        self._last_inputs = inputs
        self._last_evaluation = evaluation
        self._last_result = output
        self._last_screening = screening
        self.trace_button.setEnabled(True)
        self.snapshot_button.setEnabled(True)
        self.save_snapshot_button.setEnabled(True)
        self._align_screening_numbers(pending=False)
        # Fit label is updated with stable two-line markup below.
        check_pairs = (('Squeeze',output.squeeze_percent,screening.checks[0]),
                       ('Fit',output.stretch_percent,screening.checks[1]),
                       ('Gland fill',output.gland_fill_percent,screening.checks[2]))
        for name, nums, check in check_pairs:
            # Screening criteria come from the exact check used for PASS/REVIEW,
            # not a second set of hardcoded engineering limits.
            title = ('O-ring OD interference' if female else 'O-ring ID stretch') if name == 'Fit' else ('O-ring squeeze' if name == 'Squeeze' else name)
            criterion = _escape_html(check.criterion)
            title_label = self.overview_cells[(name,0)]
            title_label.setText(self._screening_label_markup(title, check.criterion))
            title_label.setToolTip(check.criterion)
            title_label.setWordWrap(False)
            for col, (condition, val) in enumerate(zip(
                    ('Minimum', 'Nominal', 'Maximum'),
                    (nums.minimum, nums.nominal, nums.maximum)), 1):
                percent = f'{val:.2f}%' # strictly two DP in the main screening table
                cell = self.overview_cells[(name,col)]
                if name in ('Squeeze', 'Fit'):
                    inches = self._correlated_physical_value(name, condition)
                    # Physical value is a subordinate line, smaller than the
                    # screening percentage; the full witness is unchanged.
                    cell.setText(f'<span style="font-size:12px;">{percent}</span>'
                                 f'<br/><span style="font-size:10px;color:#71849a;">{inches:.3f} in</span>')
                    cell.setToolTip(f'Exact witness: {val:.9f}% / {inches:.9f} in')
                else:
                    cell.setText(f'<span style="font-size:12px;">{percent}</span>'
                                 f'<br/><span style="font-size:10px;">&#160;</span>')
                    cell.setToolTip(f'Calculated: {val:.9f}%')
            cell=self.overview_cells[(name,4)]
            cell.setText('PASS' if check.within_limits else 'REVIEW')
            cell.setToolTip(check.criterion)
            cell.setStyleSheet('color:#18805b;font-weight:700;' if check.within_limits else
                               'color:#bb2b23;font-weight:700;')
        self._update_diagram()
        # The full methodology and screening limits are in Settings; do not
        # reserve a permanently empty footer underneath the results.
        self.overview_note.setText('')
        self.overview_note.hide()

    @staticmethod
    def _screening_label_markup(title, criterion):
        return (f'<span style="color:#17436b;font-size:12px;font-weight:600;">{_escape_html(title)}</span>'
                f'<br/><span style="color:#71849a;font-size:10px;">{_escape_html(criterion)}</span>')

    def _correlated_physical_value(self, name: str, condition: str) -> float:
        """Inches at the *same witness* that governs displayed % extrema.

        In particular, squeeze_in min/max endpoints can differ from the
        endpoints governing squeeze_pct, so never mix unrelated extrema.
        """
        key = 'Squeeze' if name == 'Squeeze' else 'Fit'
        case = self._last_evaluation.cases[(key, condition)]
        if key == 'Squeeze':
            return case.squeeze_in
        inputs = dict(case.values)
        if 'gland' in inputs:
            gland = inputs['gland']
        elif self._last_evaluation.male:
            gland = inputs['rod'] - 2 * inputs['depth']
        else:
            gland = inputs['cylinder'] + 2 * inputs['depth']
        if self._last_evaluation.male:
            return gland - inputs['ring_id']  # diametral ID stretch, in
        return inputs['ring_id'] + 2 * inputs['section'] - gland  # OD interference, in

    def _update_diagram(self, invalid=False):
        female=self.configuration.currentData()=='female'
        direct=(self.female_entry_mode.currentData()=='gland_id' if female else
                self.entry_mode.currentData()=='gland_od')
        if female:
            source=self.female_rows
            cylinder=source['direct_cylinder_id'].effective_nominal() if direct else source['cylinder_id'].effective_nominal()
            rod=source['rod_od'].effective_nominal()
            gland=source['gland_id'].effective_nominal() if direct else cylinder+2*source['groove_depth'].effective_nominal()
            depth=(gland-cylinder)/2
            diam={'rod_od':rod,'cylinder_id':cylinder,'gland_id':gland}
            mode=self.female_entry_mode.currentData()
        else:
            source=self.rows
            cylinder=source['cylinder_id'].effective_nominal()
            rod=source['direct_rod_od'].effective_nominal() if direct else source['rod_od'].effective_nominal()
            gland=source['gland_od'].effective_nominal() if direct else rod-2*source['groove_depth'].effective_nominal()
            depth=(rod-gland)/2
            diam={'piston_od':rod,'cylinder_id':cylinder,'gland_od':gland}
            mode=self.entry_mode.currentData()
        angle=self.shared_rows['angle' if self.groove_type.currentData()=='dovetail' else 'rect_angle'].effective_nominal()
        features={'width':self.shared_rows['width'].effective_nominal(),
                  'radius':self.shared_rows['radius'].effective_nominal(),
                  'entrance_radius':self.shared_rows['entrance_radius'].effective_nominal(),
                  'angle':angle,'depth':depth,**diam}
        self.diagram.set_model('female' if female else 'male',
                               self.groove_type.currentData(),mode,features,invalid)
