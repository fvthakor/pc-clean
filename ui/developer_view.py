"""Developer Ecosystem Manager View: Node/NVM, Python, Android, Flutter, Docker, VSCode, AI."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from models.developer_tool import DeveloperTool
from utils.size import format_bytes
from utils.windows import open_in_explorer


class DeveloperToolCard(QFrame):
    def __init__(self, tool: DeveloperTool, on_inspect, on_clean_leftover=None):
        super().__init__()
        self.setProperty("class", "card")
        self.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 8px; padding: 12px;")
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        top = QHBoxLayout()
        lbl_name = QLabel(tool.name)
        lbl_name.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        top.addWidget(lbl_name)

        # Status badge
        lbl_status = QLabel(tool.status)
        if tool.status == "ACTIVE":
            lbl_status.setStyleSheet(
                "background: #1F2544; color: #7C8CFF; border: 1px solid #2F3866; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700;"
            )
        elif tool.status in ("CACHE", "SAFE"):
            lbl_status.setStyleSheet(
                "background: #163B26; color: #36D399; border: 1px solid #22543D; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700;"
            )
        elif tool.status == "DANGEROUS":
            lbl_status.setStyleSheet(
                "background: #3D1217; color: #FF5C5C; border: 1px solid #5C1D24; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700;"
            )
        else:
            lbl_status.setStyleSheet(
                "background: #3D2D0C; color: #F5B942; border: 1px solid #5C4312; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 700;"
            )
        top.addWidget(lbl_status)
        top.addStretch()

        lbl_sz = QLabel(format_bytes(tool.size))
        lbl_sz.setStyleSheet("font-size: 15px; font-weight: 700; color: #4F8CFF;")
        top.addWidget(lbl_sz)
        layout.addLayout(top)

        # Path
        lbl_p = QLabel(str(tool.path))
        lbl_p.setStyleSheet("font-family: Consolas, monospace; font-size: 11px; color: #8B98A7;")
        layout.addWidget(lbl_p)

        # Explanation
        if tool.explanation:
            lbl_exp = QLabel(tool.explanation)
            lbl_exp.setStyleSheet(
                "font-size: 12px; color: #CBD5E1; background: #17222E; padding: 6px; border-radius: 4px;"
            )
            lbl_exp.setWordWrap(True)
            layout.addWidget(lbl_exp)

        # Packages / Subcomponents table if any
        if tool.packages:
            pkg_lbl = QLabel(f"Detected Components & Packages ({len(tool.packages)}):")
            pkg_lbl.setStyleSheet("font-weight: 600; font-size: 11px; color: #8B98A7;")
            layout.addWidget(pkg_lbl)

            pkg_table = QTableWidget()
            pkg_table.setColumnCount(4)
            pkg_table.setHorizontalHeaderLabels(["Name", "Size", "Type", "Action"])
            pkg_table.setRowCount(min(len(tool.packages), 15))  # display top 15
            pkg_table.setFixedHeight(min(150, 30 + len(tool.packages) * 26))
            pkg_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            pkg_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            pkg_table.horizontalHeader().resizeSection(1, 80)
            pkg_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            pkg_table.horizontalHeader().resizeSection(2, 140)
            pkg_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            pkg_table.setColumnWidth(3, 90)

            for r, pkg in enumerate(tool.packages[:15]):
                item_n = QTableWidgetItem(pkg.name)
                if pkg.is_broken:
                    item_n.setForeground(Qt.red)
                pkg_table.setItem(r, 0, item_n)

                item_s = QTableWidgetItem(format_bytes(pkg.size))
                item_s.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                pkg_table.setItem(r, 1, item_s)

                item_d = QTableWidgetItem(pkg.description)
                pkg_table.setItem(r, 2, item_d)

                if pkg.is_broken and on_clean_leftover:
                    btn_rem = QPushButton("Remove")
                    btn_rem.setFixedSize(70, 22)
                    btn_rem.setProperty("class", "danger")
                    btn_rem.clicked.connect(lambda ch, p=pkg: on_clean_leftover(p))
                    pkg_table.setCellWidget(r, 3, btn_rem)
                else:
                    btn_open = QPushButton("Open")
                    btn_open.setFixedSize(70, 22)
                    btn_open.clicked.connect(lambda ch, p=pkg: open_in_explorer(str(p.path)))
                    pkg_table.setCellWidget(r, 3, btn_open)

            layout.addWidget(pkg_table)

        # Footer Actions
        footer = QHBoxLayout()
        footer.addStretch()

        btn_inspect = QPushButton("Inspect in Details")
        btn_inspect.clicked.connect(lambda: on_inspect(tool))
        footer.addWidget(btn_inspect)

        btn_open = QPushButton("Open Folder")
        btn_open.clicked.connect(lambda: open_in_explorer(str(tool.path)))
        footer.addWidget(btn_open)

        layout.addLayout(footer)


class DeveloperView(QWidget):
    item_selected = Signal(object)
    refresh_requested = Signal()
    clean_broken_package_requested = Signal(object)

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
        title = QLabel("DEVELOPER ENVIRONMENT CLEANUP")
        title.setProperty("class", "heading1")
        sub = QLabel("Manage Node.js/NVM, Python, Android, Flutter, Docker, VS Code, and AI/ML model caches")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top.addLayout(v_title)
        top.addStretch()

        self.btn_refresh = QPushButton("🔄 Refresh Developer Tools")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        # Tab widget by Ecosystem
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_names = ["All", "Node.js", "Python", "Android", "Flutter", "Docker", "VS Code", "AI/ML"]
        self.tab_containers = {}

        for t_name in self.tab_names:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)

            c_widget = QWidget()
            c_layout = QVBoxLayout(c_widget)
            c_layout.setContentsMargins(0, 8, 0, 8)
            c_layout.setSpacing(10)
            c_layout.addStretch()

            scroll.setWidget(c_widget)
            self.tabs.addTab(scroll, t_name)
            self.tab_containers[t_name] = c_layout

    def populate_tools(self, tools: list[DeveloperTool]) -> None:
        # Clear containers
        for c_layout in self.tab_containers.values():
            while c_layout.count() > 1:
                item = c_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        for tool in tools:
            card = DeveloperToolCard(
                tool,
                on_inspect=lambda t: self.item_selected.emit(t),
                on_clean_leftover=lambda p: self.clean_broken_package_requested.emit(p),
            )
            # Add to All
            self.tab_containers["All"].insertWidget(self.tab_containers["All"].count() - 1, card)

            # Add to matching tab
            eco = tool.ecosystem
            if eco in self.tab_containers:
                card_eco = DeveloperToolCard(
                    tool,
                    on_inspect=lambda t: self.item_selected.emit(t),
                    on_clean_leftover=lambda p: self.clean_broken_package_requested.emit(p),
                )
                self.tab_containers[eco].insertWidget(self.tab_containers[eco].count() - 1, card_eco)
