"""Applications & Uninstalled Program Leftovers View."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from models.application import AppLeftoverCandidate, InstalledApp
from utils.size import format_bytes


class ApplicationsView(QWidget):
    item_selected = Signal(object)
    uninstall_app_requested = Signal(object)  # Emits InstalledApp
    clean_leftover_requested = Signal(object)  # Emits AppLeftoverCandidate
    refresh_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.installed_apps: list[InstalledApp] = []
        self.leftovers: list[AppLeftoverCandidate] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("APPLICATIONS & LEFTOVERS")
        title.setProperty("class", "heading1")
        sub = QLabel("Installed software audit and uninstalled program residual folder detector")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # --- TAB 1: Installed Applications ---
        tab_installed = QWidget()
        ti_layout = QVBoxLayout(tab_installed)
        ti_layout.setContentsMargins(0, 8, 0, 0)

        # Search box
        self.txt_app_search = QLineEdit()
        self.txt_app_search.setPlaceholderText("Search installed applications...")
        self.txt_app_search.textChanged.connect(self._filter_apps)
        ti_layout.addWidget(self.txt_app_search)

        self.table_apps = QTableWidget()
        self.table_apps.setColumnCount(6)
        self.table_apps.setHorizontalHeaderLabels(
            ["Application", "Version", "Publisher", "Size", "Install Date", "Action"]
        )
        self.table_apps.setAlternatingRowColors(True)
        self.table_apps.setSelectionBehavior(QTableWidget.SelectRows)

        hdr_apps = self.table_apps.horizontalHeader()
        hdr_apps.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr_apps.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr_apps.resizeSection(1, 100)
        hdr_apps.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr_apps.resizeSection(2, 160)
        hdr_apps.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr_apps.resizeSection(3, 90)
        hdr_apps.setSectionResizeMode(4, QHeaderView.Interactive)
        hdr_apps.resizeSection(4, 110)
        hdr_apps.setSectionResizeMode(5, QHeaderView.Fixed)
        self.table_apps.setColumnWidth(5, 100)

        ti_layout.addWidget(self.table_apps)
        self.tabs.addTab(tab_installed, "Installed Applications")

        # --- TAB 2: Uninstalled Program Leftovers ---
        tab_leftovers = QWidget()
        tl_layout = QVBoxLayout(tab_leftovers)
        tl_layout.setContentsMargins(0, 8, 0, 0)

        lbl_lo_info = QLabel(
            "Folders in AppData/ProgramData with no matching registered application. Always review before removing."
        )
        lbl_lo_info.setProperty("class", "muted")
        tl_layout.addWidget(lbl_lo_info)

        self.table_leftovers = QTableWidget()
        self.table_leftovers.setColumnCount(7)
        self.table_leftovers.setHorizontalHeaderLabels(
            ["Leftover App", "Size", "Files", "Confidence", "Status", "Location", "Action"]
        )
        self.table_leftovers.setAlternatingRowColors(True)
        self.table_leftovers.setSelectionBehavior(QTableWidget.SelectRows)

        hdr_lo = self.table_leftovers.horizontalHeader()
        hdr_lo.setSectionResizeMode(0, QHeaderView.Interactive)
        hdr_lo.resizeSection(0, 160)
        hdr_lo.setSectionResizeMode(1, QHeaderView.Interactive)
        hdr_lo.resizeSection(1, 80)
        hdr_lo.setSectionResizeMode(2, QHeaderView.Interactive)
        hdr_lo.resizeSection(2, 70)
        hdr_lo.setSectionResizeMode(3, QHeaderView.Interactive)
        hdr_lo.resizeSection(3, 100)
        hdr_lo.setSectionResizeMode(4, QHeaderView.Interactive)
        hdr_lo.resizeSection(4, 140)
        hdr_lo.setSectionResizeMode(5, QHeaderView.Stretch)
        hdr_lo.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table_leftovers.setColumnWidth(6, 90)

        tl_layout.addWidget(self.table_leftovers)
        self.tabs.addTab(tab_leftovers, "Uninstalled Leftovers")

    def populate_apps(self, apps: list[InstalledApp]) -> None:
        self.installed_apps = apps
        self.table_apps.setRowCount(len(apps))

        for row, app in enumerate(apps):
            item_name = QTableWidgetItem(app.name)
            item_name.setData(Qt.UserRole, app)
            self.table_apps.setItem(row, 0, item_name)

            self.table_apps.setItem(row, 1, QTableWidgetItem(app.version))
            self.table_apps.setItem(row, 2, QTableWidgetItem(app.publisher))

            sz_str = format_bytes(app.estimated_size) if app.estimated_size > 0 else "-"
            item_sz = QTableWidgetItem(sz_str)
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_apps.setItem(row, 3, item_sz)

            self.table_apps.setItem(row, 4, QTableWidgetItem(app.install_date or "-"))

            # Official uninstaller button
            btn_un = QPushButton("Uninstall")
            btn_un.setFixedSize(80, 24)
            btn_un.setEnabled(bool(app.uninstall_string))
            btn_un.clicked.connect(lambda ch, a=app: self.uninstall_app_requested.emit(a))
            self.table_apps.setCellWidget(row, 5, btn_un)

    def populate_leftovers(self, leftovers: list[AppLeftoverCandidate]) -> None:
        self.leftovers = leftovers
        self.table_leftovers.setRowCount(len(leftovers))

        for row, lo in enumerate(leftovers):
            item_name = QTableWidgetItem(lo.app_name)
            item_name.setData(Qt.UserRole, lo)
            self.table_leftovers.setItem(row, 0, item_name)

            item_sz = QTableWidgetItem(format_bytes(lo.size))
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_leftovers.setItem(row, 1, item_sz)

            self.table_leftovers.setItem(row, 2, QTableWidgetItem(f"{lo.files_count:,}"))

            conf_str = f"{lo.confidence * 100:.0f}% likely"
            item_c = QTableWidgetItem(conf_str)
            if lo.confidence >= 0.90:
                item_c.setForeground(Qt.green)
            else:
                item_c.setForeground(Qt.yellow)
            self.table_leftovers.setItem(row, 3, item_c)

            item_st = QTableWidgetItem(lo.status)
            self.table_leftovers.setItem(row, 4, item_st)

            item_p = QTableWidgetItem(str(lo.path))
            item_p.setToolTip(str(lo.path))
            self.table_leftovers.setItem(row, 5, item_p)

            btn_clean = QPushButton("Clean")
            btn_clean.setFixedSize(70, 24)
            btn_clean.setProperty("class", "danger")
            btn_clean.clicked.connect(lambda _ch, item=lo: self.clean_leftover_requested.emit(item))
            self.table_leftovers.setCellWidget(row, 6, btn_clean)

    def _filter_apps(self, query: str) -> None:
        q = query.lower()
        for r in range(self.table_apps.rowCount()):
            item = self.table_apps.item(r, 0)
            if item:
                self.table_apps.setRowHidden(r, q not in item.text().lower())
