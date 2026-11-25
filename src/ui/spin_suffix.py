"""Keep native Qt spin-box suffixes visible but outside the editable selection."""

def protect_suffix(spin):
    editor = spin.lineEdit()
    adjusting = False

    def limit_selection(*_):
        nonlocal adjusting
        suffix = spin.suffix()
        text = editor.text()
        if adjusting or not suffix or not text.endswith(suffix):
            return
        end = len(text) - len(suffix)
        cursor = editor.cursorPosition()
        start = editor.selectionStart()
        if start < 0:
            if cursor <= end:
                return
            adjusting = True
            try:
                editor.setCursorPosition(end)
            finally:
                adjusting = False
            return
        stop = start + len(editor.selectedText())
        anchor = stop if cursor == start else start
        clamped_cursor = min(cursor, end)
        clamped_anchor = min(anchor, end)
        if cursor == clamped_cursor and anchor == clamped_anchor:
            return
        adjusting = True
        try:
            if clamped_cursor == clamped_anchor:
                editor.setCursorPosition(clamped_cursor)
                editor.deselect()
            else:
                editor.setSelection(clamped_anchor, clamped_cursor - clamped_anchor)
        finally:
            adjusting = False

    editor.selectionChanged.connect(limit_selection)
    editor.cursorPositionChanged.connect(limit_selection)
