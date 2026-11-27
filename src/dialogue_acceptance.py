"""Native/frozen release acceptance for the shared ZeroFlagLabs dialogue standard.
Run only through the explicit diagnostic command line; never populate normal startup.
"""
from pathlib import Path
from collections import Counter
import json, sys, traceback
from tempfile import TemporaryDirectory
from PySide6.QtCore import Qt, QPoint, QSettings, QEventLoop, QTimer
from PySide6.QtGui import QCursor, QPalette, QImage
from PySide6.QtWidgets import (QLabel, QCheckBox, QPushButton, QTabWidget, QComboBox,
                               QTextBrowser, QTableWidget, QScrollBar, QDialog, QVBoxLayout)
from PySide6.QtTest import QTest


def prepare_scheme(app):
    if '--dialogue-test' in sys.argv and '--dialogue-dark' in sys.argv:
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark)


def run(app, w, kind, title, version, github, make_settings, inspectors, theme_dialog):
    output = Path(sys.argv[sys.argv.index('--self-test-output')+1])
    report = dict(app=title, version=version, scheme='dark' if '--dialogue-dark' in sys.argv else 'light', scale=w.devicePixelRatioF(), packaged=bool(getattr(sys,'frozen',False)), dialogs=[], popup_checks=0, scrollbars=0)
    old_cursor=QCursor.pos();checker=w.update_checker;old_prefs=checker.prefs;active=[]
    def wait(ms=50):QTest.qWait(ms)
    def colors(widget):
        im=widget.grab().toImage();return Counter(im.pixelColor(x,y).name() for y in range(im.height()) for x in range(im.width()))
    def shot(widget,name):
        assert widget.grab().save(str(output.with_name(output.stem+'-'+name+'.png')))
    def click(widget,pt):
        QCursor.setPos(widget.mapToGlobal(pt));wait(25);QTest.mouseClick(widget,Qt.MouseButton.LeftButton,pos=pt);wait(130)
    def open_popup(c):
        c.window().activateWindow();c.setFocus();QCursor.setPos(c.mapToGlobal(QPoint(c.width()-10,c.height()//2)));wait(50)
        QTest.keyClick(c,Qt.Key.Key_Down,Qt.KeyboardModifier.AltModifier);wait(180)
        if not c.view().isVisible():click(c,QPoint(c.width()-10,c.height()//2))
        if not c.view().isVisible():
            c.window().activateWindow();c.setFocus();wait(80);QTest.keyClick(c,Qt.Key.Key_Down,Qt.KeyboardModifier.AltModifier);wait(200)
        assert c.view().isVisible(),('open popup',c.objectName())
    def scrollbar(sb):
        if not sb.isVisible() or sb.maximum()<=sb.minimum():return
        co=colors(sb);assert '#909090' in co and '#ffffff' in co,('scrollbar pixels',co.most_common(8));assert sb.width()==12 if sb.orientation()==Qt.Orientation.Vertical else sb.height()==12
        old=sb.value();sb.setValue(sb.maximum());assert sb.value()==sb.maximum();sb.setValue(old);report['scrollbars']+=1
    def close_check(c,bar,pos,idx,case):
        assert not c.view().isVisible() and not c.hasFocus(),('popup focus',case,c.objectName());assert c.currentIndex()==idx,('selection',case,c.objectName());assert bar.value()==pos,('scroll',case,c.objectName(),bar.value(),pos);report['popup_checks']+=1
    try:
        if hasattr(w,'_update_timer'):w._update_timer.stop()
        assert app.styleHints().colorScheme()!=Qt.ColorScheme.Dark
        assert not w.windowIcon().isNull()
        with TemporaryDirectory() as tmp:
            checker.prefs=QSettings(str(Path(tmp)/'prefs.ini'),QSettings.Format.IniFormat)
            checker.set_enabled(True)
            d=make_settings();active.append(d);d.show();d.activateWindow();wait(100)
            tabs=d.findChild(QTabWidget);names=[tabs.tabText(i) for i in range(tabs.count())];assert names[-2:]==['Updates','About']
            assert d.findChild(QLabel,'references_note') is None
            for i,name in enumerate(names):
                tabs.setCurrentIndex(i);wait();QCursor.setPos(d.mapToGlobal(QPoint(3,3)));wait(40)
                for sb in d.findChildren(QScrollBar):scrollbar(sb)
                for lab in tabs.currentWidget().findChildren(QLabel):
                    if lab.isVisible() and lab.wordWrap():assert lab.height()>=lab.heightForWidth(lab.width()),('label clipped',name,lab.objectName())
                shot(d,'settings-'+name.lower());report['dialogs'].append('Settings/'+name)
            tabs.setCurrentIndex(names.index('About'));wait()
            text=d.findChild(QLabel,'about_text').text();parts=text.split('\n\n');assert parts[0]=='ZeroFlagLabs '+title+'  \u00b7  v'+version and len(parts)==4 and parts[2]=='Portable Windows application.' and 'MIT Licence.' in parts[3] and 'third-party' in parts[3]
            link=d.findChild(QLabel,'github_link');assert github in link.text() and link.openExternalLinks()
            tabs.setCurrentIndex(names.index('Updates'));wait();cb=d.findChild(QCheckBox,'check_on_launch');assert cb.isChecked();assert cb.palette().color(cb.foregroundRole()).name()=='#242424';co=colors(cb);assert '#dcecfb' in co and '#144b83' in co,('checkbox',co.most_common(8));cb.click();wait();assert not checker.enabled() and not QSettings(checker.prefs.fileName(),QSettings.Format.IniFormat).value('updates/check_on_launch',True,type=bool);assert '#144b83' not in colors(cb);shot(d,'updates-unchecked');cb.click();assert checker.enabled()
            assert d.findChild(QLabel,'current_version').text()=='Current version: v'+version
            assert d.findChild(QLabel,'update_information').text()=='Checks stable GitHub Releases in the background. Updates are not downloaded or installed automatically; the application remains portable.'
            assert d.findChild(QPushButton,'check_now_button').text()=='Check for updates';download=d.findChild(QPushButton,'open_release_button');assert download.text()=='Download update' and not download.isEnabled()
            if '--live-update-test' in sys.argv:
                loop=QEventLoop();checker.state_changed.connect(lambda:loop.quit() if checker._reply is None else None);d.findChild(QPushButton,'check_now_button').click();QTimer.singleShot(20000,loop.quit)
                if checker._reply is not None:loop.exec()
                assert checker._reply is None and checker.status=='Up to date.' and not download.isEnabled(),('live',checker.status);report['live_update']=checker.status
            d.reject();d.deleteLater();active.remove(d);wait()
            # Inspectors are constructed with the same approved editable examples as the source previews.
            for j,(name,d) in enumerate(inspectors()):
                active.append(d);d.show();d.activateWindow();wait(100);tabs=d.findChild(QTabWidget)
                for i in range(tabs.count()) if tabs else [None]:
                    if i is not None:tabs.setCurrentIndex(i);wait(35)
                    page=tabs.tabText(i) if i is not None else name;report['dialogs'].append(name+'/'+page);QCursor.setPos(d.mapToGlobal(QPoint(3,3)));wait(40)
                    for sb in d.findChildren(QScrollBar):scrollbar(sb)
                    for panel in [*d.findChildren(QTextBrowser),*d.findChildren(QTableWidget)]:
                        if not panel.isVisible():continue
                        assert panel.palette().color(QPalette.ColorRole.Text).name()=='#242424';panel.setFocus();wait(30)
                        if isinstance(panel,QTextBrowser):
                            bar=panel.verticalScrollBar();bar.setValue(0);QTest.keyClick(panel,Qt.Key.Key_PageDown);assert bar.value()>0 or bar.maximum()==0;bar.setValue(0)
                    shot(d,f'inspector-{j}-{i}')
                    for ci,c in enumerate(d.findChildren(QComboBox)):
                        if not c.isVisible():continue
                        panel=next(x for x in d.findChildren(QTextBrowser) if x.isVisible());bar=panel.verticalScrollBar();idx=c.currentIndex();panel.setFocus();bar.setValue(bar.maximum()//2);pos=bar.value();geom=(c.geometry().getRect(),panel.geometry().getRect(),d.size().toTuple())
                        open_popup(c);v=c.view();pop=v.window();assert v.sizeHintForRow(0)==30 and not v.verticalScrollBar().isVisible(),('native popup geometry',v.sizeHintForRow(0),c.objectName());co=colors(pop);assert '#e5f1fc' not in co and ('#f2f2f2' in co or '#f5f5f5' in co);shot(pop,f'popup-{j}-{i}-{ci}')
                        QTest.keyClick(v,Qt.Key.Key_Escape);wait(100);close_check(c,bar,pos,idx,'escape')
                        open_popup(c);v=c.view();click(v.viewport(),v.visualRect(c.model().index(idx,c.modelColumn())).center());close_check(c,bar,pos,idx,'same')
                        open_popup(c);click(c,QPoint(c.width()-10,c.height()//2));close_check(c,bar,pos,idx,'second click')
                        open_popup(c);pop=c.view().window();click(pop,pop.mapFromGlobal(c.mapToGlobal(QPoint(c.width()-10,c.height()//2))));close_check(c,bar,pos,idx,'grabbed second click')
                        open_popup(c);pop=c.view().window();click(pop,pop.mapFromGlobal(panel.viewport().mapToGlobal(QPoint(15,15))));close_check(c,bar,pos,idx,'outside')
                        target=(idx+1)%c.count();open_popup(c);v=c.view();click(v.viewport(),v.visualRect(c.model().index(target,c.modelColumn())).center());close_check(c,bar,0 if kind=='oring' and c.objectName()=='trace_measure' else min(pos,bar.maximum()),target,'changed')
                        c.setCurrentIndex(idx);wait(30);assert geom==(c.geometry().getRect(),panel.geometry().getRect(),d.size().toTuple()),('layout move',c.objectName())
                d.reject();active.remove(d);wait()
            d=QDialog(w);active.append(d);layout=QVBoxLayout(d);c=QComboBox();c.addItems([f'Example {i}' for i in range(100)]);c.setMaxVisibleItems(8);c.setFixedWidth(210);layout.addWidget(c);theme_dialog(d);d.show();d.activateWindow();wait(100);open_popup(c);sb=c.view().verticalScrollBar();assert sb.isVisible() and sb.maximum()>0;QCursor.setPos(c.mapToGlobal(QPoint(2,2)));wait(35);scrollbar(sb);c.hidePopup();d.reject();active.remove(d)
        report['result']='passed';return 0
    except Exception:
        report['result']='failed';report['traceback']=traceback.format_exc();return 1
    finally:
        for d in active:
            for c in d.findChildren(QComboBox):c.hidePopup()
            d.reject()
        checker.prefs=old_prefs;w.close();QCursor.setPos(old_cursor);output.write_text(json.dumps(report,indent=2),encoding='utf8')
"""Explicit sample inputs for legacy GUI tests (production starts at zero)."""
SAMPLE = {'spin_male_cylinder_id_nom': 0.75, 'spin_male_cylinder_id_tol': 0.001, 'spin_male_direct_rod_od_nom': 0.748, 'spin_male_direct_rod_od_tol': 0.001, 'spin_male_rod_od_nom': 0.748, 'spin_male_rod_od_tol': 0.001, 'spin_female_direct_cylinder_id_nom': 0.577, 'spin_female_direct_cylinder_id_tol': 0.0005, 'spin_female_cylinder_id_nom': 0.577, 'spin_female_cylinder_id_tol': 0.0005, 'spin_female_rod_od_nom': 0.575, 'spin_female_rod_od_tol': 0.001, 'spin_shared_width_nom': 0.145, 'spin_shared_width_tol': 0.003, 'spin_shared_radius_nom': 0.0, 'spin_shared_radius_tol': 0.0, 'spin_shared_entrance_radius_nom': 0.0, 'spin_shared_entrance_radius_tol': 0.0, 'spin_shared_rect_angle_nom': 0.0, 'spin_shared_rect_angle_tol': 0.0, 'spin_shared_angle_nom': 24.0, 'spin_shared_angle_tol': 0.5, 'spin_male_gland_od_nom': 0.584, 'spin_male_gland_od_tol': 0.001, 'spin_male_groove_depth_nom': 0.082, 'spin_male_groove_depth_tol': 0.001, 'spin_female_gland_id_nom': 0.741, 'spin_female_gland_id_tol': 0.001, 'spin_female_groove_depth_nom': 0.082, 'spin_female_groove_depth_tol': 0.00025, 'spin_male_ring_id_nom': 0.565, 'spin_male_ring_id_tol': 0.005, 'spin_male_section_nom': 0.103, 'spin_male_section_tol': 0.003}


def seed_sample(window):
    """Populate the former v0.9.7 demo dimensions for tests expecting results."""
    for rows, group in ((window.rows, 'male'), (window.female_rows, 'female'),
                        (window.shared_rows, 'shared')):
        for key, row in rows.items():
            row.nominal.setValue(SAMPLE[f'spin_{group}_{key}_nom'])
            row.tolerance.setValue(SAMPLE[f'spin_{group}_{key}_tol'])
    window._recalculate()



def run_for_window(app,w):
    from src.app_info import APP_TITLE, APP_VERSION, GITHUB_URL
    from src.ui.settings_dialog import SettingsDialog
    from src.ui.size_guide import SizeGuide
    from src.dialog_theme import apply_dialog_theme
    def settings():
        adapter=SettingsDialog(w);adapter.dialog._acceptance_adapter=adapter;return adapter.dialog
    def inspectors():
        seed_sample(w)
        return [('Inspect Results',w._make_tolerance_trace_dialog()),('Calculation Method',w._make_calculation_method_info_dialog()),('O-Ring Size Reference',SizeGuide(w.as568_sizes,w))]
    return run(app,w,'oring',APP_TITLE,APP_VERSION,GITHUB_URL,settings,inspectors,apply_dialog_theme)
