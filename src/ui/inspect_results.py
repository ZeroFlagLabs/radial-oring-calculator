"""Designer-owned Inspect Results window with independently auditable steps."""
from html import escape
from pathlib import Path
from PySide6.QtCore import Qt, QFile, QIODevice
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QHeaderView,
                               QPushButton, QTabWidget, QTableWidget,
                               QTableWidgetItem, QTextBrowser, QLabel)
from PySide6.QtUiTools import QUiLoader
from src.ui.inspection_data import geometry_records, explain_case


def _math(text):
    """Escaped, readable equation text; fractions use Qt's HTML table engine."""
    return escape(text).replace('  ', '&nbsp;&nbsp;')


def _math_equation(expression, fraction):
    """Use 10 pt for equations and fractions, matching the dimension inputs."""
    if fraction is None:
        return ('<p style="margin:3px 0 3px 14px;font-size:10pt;color:#233a50;">'
                + _math(expression) + '</p>')
    lhs, numer, denom, suffix = fraction
    return ('<table cellspacing="0" cellpadding="0" style="margin-left:13px;">'
            '<tr><td rowspan="3" valign="middle" style="font-size:10pt;">'
            + _math(lhs) + '&nbsp;=&nbsp;</td>'
            '<td align="center" style="font-size:10pt;padding:0 5px;">'
            + _math(numer) + '</td>'
            '<td rowspan="3" valign="middle" style="font-size:10pt;">'
            + '&nbsp;' + _math(suffix) + '</td></tr>'
            '<tr><td><hr style="height:1px;color:#385a78;"/></td></tr>'
            '<tr><td align="center" style="font-size:10pt;padding:0 5px;">'
            + _math(denom) + '</td></tr></table>')


def _section_rule():
    """An understated divider separating the three Inspector sections."""
    return '<hr style="color:#D8E1EA;background-color:#D8E1EA;height:1px;"/>'


def _html_breakdown(metric, condition, result, dimensions, steps, places,
                    screening_check=None):
    fmt = lambda x: f'{x:.{places}f}'
    heading = (escape(metric) + ' / ' + escape(condition) + ': '
               + fmt(result) + ' %')
    lines = [
        '<html><body style="font-family:Segoe UI,Arial,sans-serif;'
        'color:#233a50;font-size:10pt;">',
    ]
    if screening_check is not None:
        status = 'PASS' if screening_check.within_limits else 'REVIEW'
        colour = '#18805b' if screening_check.within_limits else '#bb2b23'
        # A table gives QTextBrowser/Qt-rich-text reliable right alignment.
        # The status concerns the entire tolerance envelope, not the single
        # Minimum/Nominal/Maximum result displayed in the left heading.
        lines += [
            '<table width="100%" cellspacing="0" cellpadding="0" '
            'style="margin:0;">',
            '<tr><td width="78%" valign="middle">'
            '<p style="font-size:12pt;color:#164f8a;margin:3px 0 4px 0;">'
            '<b>' + heading + '</b></p></td>',
            '<td align="right" valign="middle">'
            '<p style="font-size:12pt;color:' + colour + ';margin:3px 0 4px 0;">'
            '<b>' + status + '</b></p></td></tr></table>',
            '<p style="font-size:9pt;color:#657a91;margin:4px 0 12px 0;">'
            'Full tolerance-range screening: '
            + escape(screening_check.criterion) + '</p>',
        ]
    else:
        lines += [
            '<p style="font-size:12pt;color:#164f8a;margin:3px 0 12px 0;">'
            '<b>' + heading + '</b></p>',
        ]

    # Main heading / status, inputs, and calculations each form a distinct
    # visual section. The individual calculation steps remain unboxed.
    lines += [
        _section_rule(),
        '<p style="font-size:10pt;margin:13px 0 18px 0;color:#164f8a;">'
        '<b>Input Values</b></p>',
        # Qt rich-text can collapse the lower margin when a paragraph is
        # immediately followed by a table. The same small, explicit spacer
        # used below the input table preserves a clear heading-to-first-row
        # gap without affecting table rows or the approved divider spacing.
        '<p style="font-size:1pt;margin:0 0 12px 0;">&nbsp;</p>',
        '<table cellspacing="0" cellpadding="3" width="100%" '
        'style="font-size:10pt;">',
    ]
    for label, value, unit in dimensions:
        lines.append(
            '<tr><td style="font-size:10pt;">' + escape(label) + '</td>'
            '<td style="font-size:10pt;" align="right">'
            + fmt(value) + ' ' + escape(unit) + '</td></tr>'
        )
    lines += [
        '</table>',
        # QTextBrowser's rich-text layout does not reliably apply a bottom
        # margin directly to a table. A compact spacer keeps the final input
        # row the same distance from its divider as the neighbouring text.
        '<p style="font-size:1pt;margin:0 0 12px 0;">&nbsp;</p>',
        _section_rule(),
        '<p style="font-size:10pt;margin:13px 0 13px 0;color:#164f8a;">'
        '<b>Calculation Breakdown</b></p>',
    ]
    for n, step in enumerate(steps, 1):
        lines.append('<p style="font-size:10pt;margin:18px 0 7px 0;color:#164f8a;">'
                     '<b>' + str(n) + '. ' + escape(step.title) + '</b></p>')
        lines.append(_math_equation(step.symbolic, step.symbol_fraction))
        if step.title == 'Installed-section reduction':
            lines.append('<p style="font-size:9pt;color:#667f94;margin:3px 0 4px 13px;">'
                         'Source: Parker Hannifin, Parker O-Ring Handbook, '
                         'Catalog ORD 5700A/US, Fig. 3-3, p. 3-7.</p>')
        lines.append('<p style="font-size:9pt;color:#667f94;margin:6px 0 4px 13px;">'
                     'Substitution</p>')
        lines.append(_math_equation(step.numeric, step.numeric_fraction))
        lines.append('<p style="font-size:10pt;margin:7px 0 3px 13px;color:#164f8a;">'
                     '<b>Result: ' + fmt(step.result)
                     + (' ' + escape(step.unit) if step.unit else '') + '</b></p>')
        if step.note:
            lines.append('<p style="font-size:9pt;margin:5px 0 12px 13px;'
                         'color:#577189;">' + escape(step.note) + '</p>')
    lines.append('</body></html>')
    return '\n'.join(lines)


def build_inspect_results(evaluation, output, female, inputs, parent=None, screening=None):
    form = Path(__file__).resolve().parent/'forms'/'inspect_results.ui'
    file = QFile(str(form))
    if not file.open(QIODevice.OpenModeFlag.ReadOnly):
        raise RuntimeError(f'Cannot open results inspector: {form}')
    try:
        dialog=QUiLoader().load(file,parent)
        if dialog is None:raise RuntimeError(f'Cannot load results inspector: {form}')
    finally:file.close()
    get=dialog.findChild
    selector_layout=get(QHBoxLayout,'traceSelectorsLayout')
    for idx in range(3):selector_layout.setStretch(idx,1)
    precision=get(QComboBox,'trace_precision')
    measure=get(QComboBox,'trace_measure')
    condition=get(QComboBox,'trace_condition')
    text=get(QTextBrowser,'trace_text')
    grid=get(QTableWidget,'geometry_table')
    tabs=get(QTabWidget,'result_tabs')
    close=get(QPushButton,'close_inspection')
    tolerance_footer=get(QLabel,'trace_disclaimer')
    geometry_footer=get(QLabel,'geometry_note')
    if any(x is None for x in (precision,measure,condition,text,grid,tabs,close,
                               tolerance_footer,geometry_footer)):
        raise RuntimeError('Designer results inspector is missing required controls')
    precision_note = ('Full calculation precision is retained; displayed values '
                      'are rounded to the selected precision.')
    for footer in (tolerance_footer, geometry_footer):
        footer.setText(precision_note)
        footer.setStyleSheet('color:#657a91; font-size:10px;')
        footer.setWordWrap(False)
        footer.show()
    text.setOpenExternalLinks(False)
    text.setReadOnly(True)
    measure.addItems(('Squeeze','OD interference' if female else 'ID stretch','Gland fill'))
    condition.addItems(('Minimum','Nominal','Maximum'))
    condition.setCurrentIndex(1)
    precision.addItems([f'{places} DP' for places in range(7)])
    precision.setCurrentIndex(3)
    geometry=geometry_records(inputs,output,female)
    grid.setRowCount(len(geometry))
    grid.verticalHeader().hide()
    grid.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    grid.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    grid.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
    for col in (1,2,3):
        grid.horizontalHeader().setSectionResizeMode(col,QHeaderView.ResizeMode.Fixed)
        grid.setColumnWidth(col,135)
    for i,(name,_,_) in enumerate(geometry):grid.setItem(i,0,QTableWidgetItem(name))

    def redraw(*_):
        places=precision.currentIndex()
        result,dimensions,steps=explain_case(evaluation,measure.currentText(),
                                            condition.currentText(),inputs,places)
        # A check applies to the entire evaluated tolerance envelope, not
        # only to the currently displayed Minimum/Nominal/Maximum witness.
        screening_check = screening.checks[measure.currentIndex()] if screening is not None else None
        text.setHtml(_html_breakdown(measure.currentText(),condition.currentText(),
                                     result,dimensions,steps,places,screening_check))
        for row,(_,rng,unit) in enumerate(geometry):
            for col,key in enumerate(('minimum','nominal','maximum'),1):
                value=getattr(rng,key)
                cell=grid.item(row,col)
                if cell is None:
                    cell=QTableWidgetItem();grid.setItem(row,col,cell)
                cell.setText(f'{value:.{places}f}')
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setToolTip(f'Calculated: {value:.9f} {unit}')
    measure.currentIndexChanged.connect(redraw)
    condition.currentIndexChanged.connect(redraw)
    precision.currentIndexChanged.connect(redraw)
    close.clicked.connect(dialog.accept)
    redraw()
    return dialog
