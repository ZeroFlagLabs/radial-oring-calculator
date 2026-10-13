from gui_sample import seed_sample
"""Stage 9.5.1: structural and Windows GUI regressions for approved UI refinement."""
from pathlib import Path
from xml.etree import ElementTree as ET
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
QT = importlib.util.find_spec('PySide6') is not None
APP = 'Static & Dynamic Radial O-Ring Calculator'


def get(name, root):
    found = root.find(f'.//*[@name="{name}"]')
    if found is None: raise AssertionError(f'Missing {name}')
    return found


def form_fields(layout):
    return {item[0].get('name') for item in layout.findall('item') if len(item)}


class Stage951Structure(unittest.TestCase):
    def test_component_and_groove_fields_have_unique_designer_owners(self):
        ui=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        names=[node.get('name') for node in ui.iter('widget')]
        self.assertEqual(len(names),len(set(names)))
        for mode, pname in [('male_direct_form','dim_male_direct_rod_od'),
                            ('male_depth_form','dim_male_rod_od'),
                            ('female_direct_form','dim_female_direct_cylinder_id'),
                            ('female_depth_form','dim_female_cylinder_id')]:
            values=form_fields(get(mode,ui))
            self.assertEqual({v for v in values if v.startswith('dim_')},{pname})
            self.assertNotIn('groove_depth',str(values))
        shared=form_fields(get('shared_form',ui))
        for name in ('dim_male_gland_od','dim_male_groove_depth',
                     'dim_female_gland_id','dim_female_groove_depth',
                     'dim_shared_width','dim_shared_radius','dim_shared_entrance_radius'):
            self.assertIn(name,shared)
        male=get('maleLayout',ui)
        self.assertEqual(male.findall('item')[0][0].get('name'),'male_common_form')
        female=get('femaleLayout',ui)
        self.assertEqual(female.findall('item')[0][0].get('name'),'female_gland_entry')
        self.assertEqual(get('male_group',ui).find('./property[@name="title"]/string').text,'Component dimensions')
        self.assertEqual(get('female_group',ui).find('./property[@name="title"]/string').text,'Component dimensions')

    def test_application_identity_tabs_names_and_note(self):
        ui=ET.parse(ROOT/'src/ui/forms/main_window.ui').getroot()
        self.assertEqual(get('window_title',ui).find('./property[@name="text"]/string').text,APP)
        self.assertIn('theoretical sharp intersections',get('shared_note',ui).find('./property[@name="text"]/string').text)
        settings=ET.parse(ROOT/'src/ui/forms/settings_dialog.ui').getroot()
        tabs=get('settings_tabs',settings)
        self.assertEqual([w.get('name') for w in tabs.findall('widget')],
                         ['assumptions_tab','references_tab','updates_tab','about_tab'])
        inspector=ET.parse(ROOT/'src/ui/forms/inspect_results.ui').getroot()
        self.assertEqual(get('inspect_app_name',inspector).find('./property[@name="text"]/string').text,APP)
        overview=get('overview_grid',ui)
        self.assertEqual([i.get('column') for i in overview.findall('item') if i[0].get('name')=='overview_squeeze_4'],['5'])
        setup=get('setupLayout',ui)
        self.assertEqual(setup.find('./property[@name="leftMargin"]/number').text,'7')
        guide=get('oringGuideLayout',ui)
        self.assertEqual([i[0].get('name') for i in guide.findall('item')],
                         ['ring_size','oring_info_edge_spacer','guide_button'])
        self.assertEqual(get('overviewLayout',ui).find('./property[@name="bottomMargin"]/number').text,'4')
        main=(ROOT/'src/ui/main_window.py').read_text()
        self.assertIn("self.shared_form.setRowVisible(row.widget, shown)",main)
        self.assertIn('self._update_groove_entry_rows()',main)
        self.assertIn('self.setFixedSize(width, height)',main)


@unittest.skipUnless(QT,'Requires Windows PySide6')
class Stage951Gui(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_all_four_modes_move_only_appropriate_groove_field(self):
        from src.ui.main_window import MainWindow
        from PySide6.QtWidgets import QFormLayout
        w=MainWindow();seed_sample(w)
        w.show()
        try:
            self.app.processEvents()
            grp=w.findChild(type(w.male_group),'shared_group')
            ring_y=w.ring_group.y()
            for female, selected in ((False,0),(False,1),(True,0),(True,1),(False,0)):
                w.configuration.setCurrentIndex(int(female))
                (w.female_entry_mode if female else w.entry_mode).setCurrentIndex(selected)
                self.app.processEvents()
                expected = ('dim_female_gland_id' if selected==0 else 'dim_female_groove_depth') if female else ('dim_male_gland_od' if selected==0 else 'dim_male_groove_depth')
                self.assertEqual(w.configuration.currentData(),'female' if female else 'male')
                for row in (w.rows['gland_od'],w.rows['groove_depth'],
                            w.female_rows['gland_id'],w.female_rows['groove_depth']):
                    self.assertIs(row.widget.parentWidget(),grp)
                    self.assertEqual(row.widget.isVisible(),row.widget.objectName()==expected)
                self.assertEqual(w.ring_group.y(),ring_y)
                self.assertEqual(w.minimumSize(),w.maximumSize())
            w.groove_type.setCurrentIndex(1)
            self.app.processEvents()
            self.assertEqual(w.ring_group.y(),ring_y)
        finally:w.close()

    def test_reference_settings_inspector_and_status_position(self):
        from src.ui.main_window import MainWindow
        from src.ui.size_guide import SizeGuide
        from src.ui.settings_dialog import SettingsDialog
        from PySide6.QtWidgets import QTabWidget
        w=MainWindow();seed_sample(w)
        try:
            self.assertEqual(w.windowTitle(),APP)
            self.assertEqual(w.configuration.itemText(0),'Piston groove (male)')
            self.assertEqual(w.configuration.itemText(1),'Cylinder groove (female)')
            size=SizeGuide(w.as568_sizes,w)
            self.assertEqual(size.table.horizontalHeaderItem(0).text(),'O-Ring Designation')
            size.close()
            dlg=SettingsDialog(w).dialog
            self.assertEqual([dlg.findChild(QTabWidget,'settings_tabs').tabText(x) for x in range(4)],
                             ['Assumptions','References','Updates','About'])
            dlg.close()
            inspect=w._make_tolerance_trace_dialog()
            self.assertIn(APP,inspect.windowTitle())
            inspect.close()
            from PySide6.QtCore import Qt
            self.assertTrue(w.overview_cells[('Fit',4)].alignment() & Qt.AlignmentFlag.AlignTop)
        finally:w.close()

if __name__=='__main__':unittest.main()
