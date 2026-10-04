"""Duplicate Files Detection & Management View."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.duplicate_service import DuplicateGroup
from utils.formatting import format_timestamp
from utils.size import format_bytes


class DuplicateView(QWidget):
    item_selected = Signal(object)
    scan_duplicates_requested = Signal(str)  # drive_letter
    delete_file_requested = Signal(object)  # FileItem

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.groups: list[DuplicateGroup] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("DUPLICATE FILE FINDER")
        title.setProperty("class", "heading1")
        sub = QLabel("Two-stage detection: Exact byte size grouping followed by streaming SHA-256 validation")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        self.btn_scan = QPushButton("🔍 Find Duplicates")
        self.btn_scan.setProperty("class", "primary")
        self.btn_scan.clicked.connect(lambda: self.scan_duplicates_requested.emit("C:"))
        top.addWidget(self.btn_scan)
        layout.addLayout(top)

        # Summary label
        self.lbl_summary = QLabel("Run a duplicate scan to detect identical files.")
        self.lbl_summary.setProperty("class", "muted")
        layout.addWidget(self.lbl_summary)

        # Tree View
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["File / Hash Group", "Size", "Modified", "SHA-256 Hash", "Path"])
        self.tree.setAlternatingRowColors(True)

        hdr = self.tree.header()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.resizeSection(0, 260)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.resizeSection(1, 100)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.resizeSection(2, 140)
        hdr.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr.resizeSection(3, 160)
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)

        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def populate_duplicates(self, groups: list[DuplicateGroup]) -> None:
        self.groups = groups
        self.tree.blockSignals(True)
        self.tree.clear()

        total_waste = sum(g.size_bytes * (len(g.files) - 1) for g in groups)
        self.lbl_summary.setText(
            f"Found {len(groups)} duplicate sets. Potential reclaimable space: {format_bytes(total_waste)}"
        )

        for g in groups:
            # Group root node
            group_node = QTreeWidgetItem(
                [
                    f"Duplicate Set ({len(g.files)} copies)",
                    format_bytes(g.size_bytes),
                    f"Wasted: {format_bytes(g.size_bytes * (len(g.files) - 1))}",
                    f"{g.hash_sha256[:16]}...",
                    "",
                ]
            )
            group_node.setForeground(0, Qt.yellow)
            self.tree.addTopLevelItem(group_node)

            for f in g.files:
                file_node = QTreeWidgetItem(
                    [
                        f.name,
                        format_bytes(f.size),
                        format_timestamp(f.modified),
                        g.hash_sha256[:16] + "...",
                        str(f.path),
                    ]
                )
                file_node.setData(0, Qt.UserRole, f)
                group_node.addChild(file_node)

            group_node.setExpanded(True)

        self.tree.blockSignals(False)

    def _on_item_clicked(self, item: QTreeWidgetItem, col: int) -> None:
        file_item = item.data(0, Qt.UserRole)
        if file_item:
            self.item_selected.emit(file_item)
