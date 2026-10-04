"""Cleanup History Audit View."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from utils.size import format_bytes


class HistoryView(QWidget):
    clear_history_requested = Signal()
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("CLEANUP HISTORY & AUDIT LOG")
        title.setProperty("class", "heading1")
        sub = QLabel("Record of past deletions, space reclaimed, skipped locked files, and safety events")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        self.btn_clear = QPushButton("Clear History")
        self.btn_clear.clicked.connect(self.clear_history_requested.emit)
        top.addWidget(self.btn_clear)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Timestamp", "Category", "Reclaimed Size", "Files", "Action", "Result", "Path / Details"]
        )
        self.table.setAlternatingRowColors(True)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.resizeSection(0, 140)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.resizeSection(1, 130)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.resizeSection(2, 100)
        hdr.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr.resizeSection(3, 70)
        hdr.setSectionResizeMode(4, QHeaderView.Interactive)
        hdr.resizeSection(4, 90)
        hdr.setSectionResizeMode(5, QHeaderView.Interactive)
        hdr.resizeSection(5, 120)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)

        layout.addWidget(self.table)

    def populate_history(self, entries: list[dict]) -> None:
        self.table.setRowCount(len(entries))
        for row, e in enumerate(entries):
            ts = e.get("timestamp", "")[:19].replace("T", " ")
            self.table.setItem(row, 0, QTableWidgetItem(ts))
            self.table.setItem(row, 1, QTableWidgetItem(e.get("category", "")))

            sz = e.get("size_bytes", 0)
            item_sz = QTableWidgetItem(format_bytes(sz))
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, item_sz)

            self.table.setItem(row, 3, QTableWidgetItem(f"{e.get('file_count', 0):,}"))
            self.table.setItem(row, 4, QTableWidgetItem(e.get("action", "")))

            res = e.get("result", "")
            item_res = QTableWidgetItem(res)
            if "Success" in res:
                item_res.setForeground(Qt.green)
            elif "Partial" in res or "Skipped" in res:
                item_res.setForeground(Qt.yellow)
            else:
                item_res.setForeground(Qt.red)
            self.table.setItem(row, 5, item_res)

            path_details = e.get("path", "")
            if e.get("error_message"):
                path_details += f" ({e['error_message']})"
            self.table.setItem(row, 6, QTableWidgetItem(path_details))
