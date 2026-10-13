"""Searchable reference table using the project's AS568 catalogue data."""

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QHeaderView, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout,
)


class DashItem(QTableWidgetItem):
    """Sort AS568 dash numbers numerically, including the -001 1/2 entry."""

    def __init__(self, dash: str):
        super().__init__(f"AS568{dash}")
        self.setData(Qt.ItemDataRole.UserRole, dash)
        match = re.fullmatch(r"-(\d{3})(?:\s+(1/2))?", dash)
        if match is None:
            raise ValueError(f"Unsupported AS568 label: {dash}")
        self.order = (int(match.group(1)), 1 if match.group(2) else 0)
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, DashItem):
            return self.order < other.order
        return super().__lt__(other)


class NumericItem(QTableWidgetItem):
    """Sort dimensions numerically, not alphabetically."""

    def __init__(self, value: float):
        super().__init__(f"{value:.3f}")
        self.number = value
        self.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            return self.number < other.number
        return super().__lt__(other)


class SizeGuide(QDialog):
    def __init__(self, sizes, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"O-Ring Size Reference | Static & Dynamic Radial O-Ring Calculator")
        self.resize(560, 620)
        self.chosen_dash = None
        self.sizes = sizes

        layout = QVBoxLayout(self)
        heading = QLabel('O-Ring Size Reference')
        heading.setStyleSheet('font-size:17px; font-weight:700; color:#164f8a;')
        layout.addWidget(heading)
        rule = QFrame()
        rule.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(rule)
        app_name = QLabel('Static & Dynamic Radial O-Ring Calculator')
        app_name.setStyleSheet('color:#71849a; font-size:11px;')
        layout.addWidget(app_name)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search dash number, ID or cross-section…")
        layout.addWidget(self.search)
        self.table = QTableWidget(len(sizes), 3)
        self.table.setHorizontalHeaderLabels(["O-Ring Designation", "ID (in)", "Section (in)"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        for index, item in enumerate(sizes):
            self.table.setItem(index, 0, DashItem(item.dash))
            self.table.setItem(index, 1, NumericItem(item.id_in))
            self.table.setItem(index, 2, NumericItem(item.cs_in))
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSortingEnabled(True)
        self.table.sortItems(0, Qt.SortOrder.AscendingOrder)
        layout.addWidget(self.table)

        self.summary = QLabel(f"{len(sizes)} listed O-ring sizes. Double-click to use a size.")
        layout.addWidget(self.summary)
        buttons = QHBoxLayout()
        self.choose = QPushButton("Use selected size")
        self.choose.clicked.connect(self._choose)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        buttons.addWidget(self.choose)
        buttons.addStretch()
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.search.textChanged.connect(self._filter)
        self.table.itemDoubleClicked.connect(lambda _: self._choose())
        self.table.itemSelectionChanged.connect(self._selection_changed)
        self.table.selectRow(0)

    def _selection_changed(self):
        self.choose.setEnabled(self.table.currentRow() >= 0 and not self.table.isRowHidden(self.table.currentRow()))

    def _filter(self, query: str):
        query = query.strip().lower()
        count = 0
        for row in range(self.table.rowCount()):
            label = self.table.item(row, 0).text().lower()
            id_text = self.table.item(row, 1).text()
            cs_text = self.table.item(row, 2).text()
            match = not query or any(query in item for item in (label, id_text, cs_text))
            self.table.setRowHidden(row, not match)
            count += int(match)
        self.summary.setText(f"{count} matching sizes. Double-click to use a size.")
        self._selection_changed()

    def _choose(self):
        row = self.table.currentRow()
        if row < 0 or self.table.isRowHidden(row):
            return
        self.chosen_dash = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.accept()
