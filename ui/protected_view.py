"""Protected Paths Management View."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.protected_path import ProtectedPath


class ProtectedView(QWidget):
    add_protection_requested = Signal(str, str, str)  # path, name, reason
    unprotect_requested = Signal(str)  # path or id
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.protected_items: list[ProtectedPath] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("PROTECTED PATHS & SAFETY POLICIES")
        title.setProperty("class", "heading1")
        sub = QLabel("Locations marked as Protected are strictly blocked from all automated and manual cleanup actions")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        self.btn_add_folder = QPushButton("+ Protect Folder")
        self.btn_add_folder.setProperty("class", "primary")
        self.btn_add_folder.clicked.connect(self._on_add_folder)
        top.addWidget(self.btn_add_folder)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Item Name", "Protected Path", "Protection Reason", "Created At", "Action"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.resizeSection(0, 180)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.resizeSection(2, 220)
        hdr.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr.resizeSection(3, 140)
        hdr.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 100)

        layout.addWidget(self.table)

    def populate_protected(self, items: list[ProtectedPath]) -> None:
        self.protected_items = items
        self.table.setRowCount(len(items))

        for row, p in enumerate(items):
            item_name = QTableWidgetItem(f"⭐ {p.name}")
            item_name.setForeground(Qt.cyan)
            self.table.setItem(row, 0, item_name)

            item_path = QTableWidgetItem(p.path)
            item_path.setToolTip(p.path)
            self.table.setItem(row, 1, item_path)

            self.table.setItem(row, 2, QTableWidgetItem(p.reason))
            self.table.setItem(row, 3, QTableWidgetItem(p.created_at[:19].replace("T", " ") if p.created_at else "-"))

            btn_unprotect = QPushButton("Unprotect")
            btn_unprotect.setFixedSize(85, 24)
            btn_unprotect.clicked.connect(lambda ch, item=p: self.unprotect_requested.emit(item.path))
            self.table.setCellWidget(row, 4, btn_unprotect)

    def _on_add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Protect")
        if folder:
            p = Path(folder)
            self.add_protection_requested.emit(str(p.resolve()), p.name, "User Defined Protection")
