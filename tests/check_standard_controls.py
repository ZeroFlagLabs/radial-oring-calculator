import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication,QPushButton,QDialogButtonBox,QGroupBox
from PySide6.QtCore import QSize,QSettings,QPoint
from PySide6.QtTest import QTest
kind="OR"
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'src'))
def buttons(w, names):
    for name in names:
        b=next(b for b in w.findChildren(QPushButton) if b.text().replace(chr(8230),"...").rstrip(".")==name.rstrip("."))
        assert b.size()==QSize(106,30),(name,b.size())
        print(name,b.size().toTuple(),flush=True)
def show(w):
    w.show();QTest.qWait(40)
def grab(w,name):
    pass
def finish(w,d):
    d.close();w.close();QTest.qWait(20)
if kind=="OR":
    from src.ui.main_window import MainWindow
    from src.ui.settings_dialog import SettingsDialog
    from src.ui.size_guide import SizeGuide
    app=QApplication([])
    w=MainWindow();show(w)
    def state():
        return (tuple(getattr(w,k).currentData() for k in w._startup_selectors),
                tuple((r.limit_mode,r.limits_initialized,tuple((s.value(),s.decimals(),s.isEnabled()) for s in (r.nominal,r.tolerance,r.limit_min,r.limit_max))) for group in (w.rows,w.female_rows,w.shared_rows) for r in group.values()),
                tuple(b.isEnabled() for b in (w.trace_button,w.snapshot_button,w.save_snapshot_button)),w.statusBar().currentMessage())
    base=state()
    buttons(w,("Reset","Inspect results","Copy snapshot","Save PNG..."))
    grab(w,"standard-startup.png")
    w.calculation_method.setCurrentIndex(1)
    w.application.setCurrentIndex(1)
    w.configuration.setCurrentIndex(1)
    w.groove_type.setCurrentIndex(1)
    w.entry_mode.setCurrentIndex(1);w.female_entry_mode.setCurrentIndex(1)
    w.ring_size.setCurrentIndex(1)
    for row in (w.female_rows['rod_od'],w.shared_rows['width']):
        row.nominal.setValue(1.25);row.tolerance.setValue(.01);row.mode_limits.click()
    w.reset_button.click();QTest.qWait(50)
    assert state()==base,(state(),base)
    d=SettingsDialog(w).dialog;show(d);buttons(d,("Close",));grab(d,"standard-settings.png")
    method=w._make_calculation_method_info_dialog();show(method);buttons(method,("Close",));method.close()
    guide=SizeGuide(w.as568_sizes,w);show(guide);buttons(guide,("Close",));print("Use selected size exception",guide.choose.size().toTuple());guide.close()
    finish(w,d)
elif kind=="PV":
    from main import MainWindow
    app=QApplication([]);app.setStyle("Fusion")
    w=MainWindow();show(w)
    def state():
        return (tuple((k,row.mode,row.a.value(),row.b.value(),row.derived,row.a.isEnabled(),row.b.isEnabled()) for k,row in w.dims.items()),
                tuple((k,f.value() if hasattr(f,'value') else f.currentText()) for k,f in w.fields.items()),
                w.derived,w.result,w.raw,w.used,tuple(b.isEnabled() for b in (w.inspect_button,w.copy_button,w.save_button)),w.statusBar().currentMessage())
    base=state()
    buttons(w,("Reset","Inspect results","Copy snapshot","Save PNG..."))
    grab(w,"standard-startup.png")
    w.sample();QTest.qWait(40)
    assert w.result is not None
    d=w.make_inspector();show(d);buttons(d,("Close",));grab(d,"standard-inspector.png");d.close()
    w.dims["od"].limits.click();w.fields["pressure_type"].setCurrentText("external");w.fields["end_condition"].setCurrentText("open")
    for k,v in [("derating_factor",".9"),("axial_load","1000")]:w.fields[k].setText(v)
    next(b for b in w.findChildren(QPushButton) if b.text()=="Reset").click()
    QTest.qWait(50)
    assert state()==base,(state(),base)
    d=w.make_settings();show(d);buttons(d,("Close",));grab(d,"standard-settings.png");finish(w,d)
elif kind=="CTR":
    from main import make_app,Window
    from tempfile import TemporaryDirectory
    app=make_app()
    with TemporaryDirectory() as t:
        w=Window(QSettings(str(Path(t)/"prefs.ini"),QSettings.Format.IniFormat));show(w)
        print("Duration",w.weeks.size().toTuple(),"Quantity",w.quantities[0].size().toTuple(),"Hours/task",w.rates[0].size().toTuple(),"Other hours",w.additional.size().toTuple())
        assert w.weeks.size()==QSize(106,30)
        assert all(s.size()==QSize(64,30) for s in (*w.quantities,*w.rates,w.additional))
        buttons(w,("Reset",));grab(w,"standard-startup.png")
        base=tuple(f.text() for f in w.fields)
        w.quantities[0].setText("10");w.rates[0].setText("6");w.weeks.setText("2");w.reset.click();QTest.qWait(30)
        assert tuple(f.text() for f in w.fields)==base
        d=w.make_settings();show(d);buttons(d,("Close","Restore defaults","Save defaults"))
        assert all(f.size()==QSize(106,30) for f in d.default_fields)
        grab(d,"standard-settings.png");finish(w,d)
print(kind,"PASS")
