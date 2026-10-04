"""Large Files Finder View."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.file_item import FileItem
from utils.formatting import format_timestamp
from utils.size import format_bytes


class LargeFilesView(QWidget):
    item_selected = Signal(object)
    scan_large_files_requested = Signal(str, int)  # drive_letter, min_bytes
    delete_large_file_requested = Signal(object)  # FileItem

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.files: list[FileItem] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("LARGE FILE FINDER")
        title.setProperty("class", "heading1")
        sub = QLabel("Discover massive disk-consuming files, ISOs, weights, installers, and archives")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        top.addWidget(QLabel("Min Size:"))
        self.combo_size = QComboBox()
        self.combo_size.addItems(["> 100 MB", "> 500 MB", "> 1 GB", "> 5 GB", "> 10 GB"])
        top.addWidget(self.combo_size)

        self.btn_scan = QPushButton("🔍 Find Large Files")
        self.btn_scan.setProperty("class", "primary")
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        top.addWidget(self.btn_scan)
        layout.addLayout(top)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["File Name", "Size", "Category", "Modified", "Safety", "Path", "Action"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr.resizeSection(0, 220)
        hdr.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr.resizeSection(1, 90)
        hdr.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr.resizeSection(2, 120)
        hdr.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr.resizeSection(3, 130)
        hdr.setSectionResizeMode(4, QHeaderView.Interactive)
        hdr.resizeSection(4, 90)
        hdr.setSectionResizeMode(5, QHeaderView.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 90)

        self.table.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.table)

    def populate_files(self, files: list[FileItem]) -> None:
        self.files = files
        self.table.setRowCount(len(files))

        for row, f in enumerate(files):
            item_name = QTableWidgetItem(f.name)
            item_name.setData(Qt.UserRole, f)
            self.table.setItem(row, 0, item_name)

            item_sz = QTableWidgetItem(format_bytes(f.size))
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, item_sz)

            self.table.setItem(row, 2, QTableWidgetItem(f.category))
            self.table.setItem(row, 3, QTableWidgetItem(format_timestamp(f.modified)))

            safety_str = f.safety_result.level.value if f.safety_result else "REVIEW"
            item_sf = QTableWidgetItem(safety_str)
            if safety_str in ("SAFE", "SAFE_REDOWNLOAD"):
                item_sf.setForeground(Qt.green)
            elif safety_str == "IMPORTANT":
                item_sf.setForeground(Qt.cyan)
            else:
                item_sf.setForeground(Qt.red)
            self.table.setItem(row, 4, item_sf)

            item_p = QTableWidgetItem(str(f.path))
            item_p.setToolTip(str(f.path))
            self.table.setItem(row, 5, item_p)

            btn_del = QPushButton("Recycle")
            btn_del.setFixedSize(70, 24)
            btn_del.setProperty("class", "danger")
            btn_del.clicked.connect(lambda ch, item=f: self.delete_large_file_requested.emit(item))
            self.table.setCellWidget(row, 6, btn_del)

    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        file_item = self.table.item(item.row(), 0).data(Qt.UserRole)
        if file_item:
            self.item_selected.emit(file_item)

    def _on_scan_clicked(self) -> None:
        idx = self.combo_size.currentIndex()
        min_bytes = [100 * 1024**2, 500 * 1024**2, 1024**3, 5 * 1024**3, 10 * 1024**3][idx]
        self.scan_large_files_requested.emit("C:", min_bytes)
