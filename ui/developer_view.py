"""Developer Ecosystem Manager View: Node/NVM, Python, Android, Flutter, Docker, VSCode, AI, and Workspace Projects."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from models.developer_tool import DeveloperTool
from models.project_artifact import ProjectArtifact
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
            pkg_table.setRowCount(len(tool.packages))
            pkg_table.setColumnCount(4)
            pkg_table.setHorizontalHeaderLabels(["Name", "Size", "Description", "Actions"])
            pkg_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            pkg_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            pkg_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            pkg_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            pkg_table.setColumnWidth(3, 80)
            pkg_table.setMaximumHeight(min(140, len(tool.packages) * 32 + 28))
            pkg_table.verticalHeader().setVisible(False)

            for r, pkg in enumerate(tool.packages):
                item_n = QTableWidgetItem(pkg.name)
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
    scan_projects_requested = Signal(str)
    clean_artifacts_requested = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.all_artifacts: list[ProjectArtifact] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header
        top = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("DEVELOPER ENVIRONMENT & WORKSPACE CLEANUP")
        title.setProperty("class", "heading1")
        sub = QLabel("Manage Node.js/NVM, Python, project node_modules, build outputs, Docker, and AI models")
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

        # 1. Projects Workspace Tab (Folder-wise node_modules & build outputs)
        self._init_projects_tab()

        # 2. Ecosystem tabs
        self.tab_names = ["All Tools", "Node.js", "Python", "Android", "Flutter", "Docker", "VS Code", "AI/ML"]
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

    def _init_projects_tab(self) -> None:
        proj_widget = QWidget()
        p_layout = QVBoxLayout(proj_widget)
        p_layout.setContentsMargins(10, 12, 10, 10)
        p_layout.setSpacing(10)

        # Top Control Bar
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 8px; padding: 10px;")
        c_layout = QHBoxLayout(ctrl_card)
        c_layout.setSpacing(10)

        lbl_dir = QLabel("Scan Location:")
        lbl_dir.setStyleSheet("font-weight: 700; color: #E6EDF3;")
        c_layout.addWidget(lbl_dir)

        self.txt_project_dir = QLineEdit()
        self.txt_project_dir.setText("D:\\")
        self.txt_project_dir.setPlaceholderText("Drive or Project root (e.g. D:\\ or C:\\Users\\...\\Projects)")
        self.txt_project_dir.setMinimumWidth(260)
        c_layout.addWidget(self.txt_project_dir)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._on_browse_projects_dir)
        c_layout.addWidget(btn_browse)

        self.btn_scan_projects = QPushButton("🔍 Scan node_modules & Builds")
        self.btn_scan_projects.setProperty("class", "primary")
        self.btn_scan_projects.setStyleSheet(
            "QPushButton { background-color: #4F8CFF; color: #FFFFFF; font-weight: 700; border-radius: 6px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #659DFF; }"
        )
        self.btn_scan_projects.clicked.connect(self._on_scan_projects_clicked)
        c_layout.addWidget(self.btn_scan_projects)

        c_layout.addStretch()

        # Tech Filter Dropdown
        lbl_filt = QLabel("Filter Tech:")
        lbl_filt.setStyleSheet("color: #8B98A7;")
        c_layout.addWidget(lbl_filt)

        self.combo_tech_filter = QComboBox()
        self.combo_tech_filter.addItems(
            [
                "All Technologies",
                "Node.js (node_modules)",
                "Python (.venv / caches)",
                "Flutter / Dart (build)",
                "Rust / Gradle / .NET",
            ]
        )
        self.combo_tech_filter.currentIndexChanged.connect(self._apply_filter)
        c_layout.addWidget(self.combo_tech_filter)

        p_layout.addWidget(ctrl_card)

        # Action bar above table
        act_bar = QHBoxLayout()
        self.chk_select_all = QCheckBox("Select All Artifacts")
        self.chk_select_all.toggled.connect(self._on_select_all_toggled)
        act_bar.addWidget(self.chk_select_all)

        self.lbl_projects_summary = QLabel("0 artifacts discovered (0 B total)")
        self.lbl_projects_summary.setStyleSheet("color: #36D399; font-weight: 600; font-size: 13px;")
        act_bar.addWidget(self.lbl_projects_summary)
        act_bar.addStretch()

        self.btn_clean_projects = QPushButton("🧹 Clean Selected to Recycle Bin")
        self.btn_clean_projects.setProperty("class", "danger")
        self.btn_clean_projects.setStyleSheet(
            "QPushButton { background-color: #CF222E; color: #FFFFFF; font-weight: 700; border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background-color: #E5534B; }"
        )
        self.btn_clean_projects.clicked.connect(self._on_clean_projects_clicked)
        act_bar.addWidget(self.btn_clean_projects)
        p_layout.addLayout(act_bar)

        # Table of project artifacts
        self.table_projects = QTableWidget()
        self.table_projects.setColumnCount(7)
        self.table_projects.setHorizontalHeaderLabels(
            ["Select", "Project Name", "Tech", "Artifact Folder", "Size", "Recreate Command", "Full Path"]
        )
        self.table_projects.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table_projects.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table_projects.verticalHeader().setVisible(False)
        p_layout.addWidget(self.table_projects)

        self.tabs.addTab(proj_widget, "📦 Projects (node_modules & Builds)")

    def _on_browse_projects_dir(self) -> None:
        picked = QFileDialog.getExistingDirectory(self, "Select Projects Root Directory", self.txt_project_dir.text())
        if picked:
            self.txt_project_dir.setText(picked)

    def _on_scan_projects_clicked(self) -> None:
        target_dir = self.txt_project_dir.text().strip()
        if not target_dir:
            return
        self.scan_projects_requested.emit(target_dir)

    def populate_project_artifacts(self, artifacts: list[ProjectArtifact]) -> None:
        self.all_artifacts = artifacts
        self._apply_filter()

    def remove_cleaned_artifacts(self, cleaned: list[ProjectArtifact]) -> None:
        """Remove cleaned artifacts from the active list and refresh table immediately."""
        cleaned_paths = {str(a.path).lower() for a in cleaned}
        self.all_artifacts = [a for a in self.all_artifacts if str(a.path).lower() not in cleaned_paths]
        self._apply_filter()

    def _apply_filter(self) -> None:
        filt = self.combo_tech_filter.currentText()
        if filt.startswith("Node.js"):
            visible_artifacts = [a for a in self.all_artifacts if a.tech == "Node.js"]
        elif filt.startswith("Python"):
            visible_artifacts = [a for a in self.all_artifacts if "Python" in a.tech]
        elif filt.startswith("Flutter"):
            visible_artifacts = [a for a in self.all_artifacts if a.tech == "Flutter"]
        elif filt.startswith("Rust"):
            visible_artifacts = [a for a in self.all_artifacts if a.tech in ("Rust", "Gradle", ".NET")]
        else:
            visible_artifacts = self.all_artifacts

        total_bytes = sum(a.size for a in visible_artifacts)
        self.lbl_projects_summary.setText(
            f"{len(visible_artifacts)} artifacts ({format_bytes(total_bytes)} reclaimable)"
        )

        self.table_projects.setRowCount(len(visible_artifacts))
        for r, art in enumerate(visible_artifacts):
            # Checkbox item
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            chk_item.setCheckState(Qt.Checked if art.is_selected else Qt.Unchecked)
            self.table_projects.setItem(r, 0, chk_item)

            # Project Name
            item_proj = QTableWidgetItem(art.project_name)
            item_proj.setData(Qt.UserRole, art)
            self.table_projects.setItem(r, 1, item_proj)

            # Tech
            item_tech = QTableWidgetItem(art.tech)
            self.table_projects.setItem(r, 2, item_tech)

            # Artifact
            item_art = QTableWidgetItem(art.artifact_name)
            self.table_projects.setItem(r, 3, item_art)

            # Size
            item_sz = QTableWidgetItem(format_bytes(art.size))
            item_sz.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_projects.setItem(r, 4, item_sz)

            # Recreate Command
            item_rec = QTableWidgetItem(art.recreate_command)
            self.table_projects.setItem(r, 5, item_rec)

            # Path
            item_path = QTableWidgetItem(str(art.path))
            item_path.setToolTip(str(art.path))
            self.table_projects.setItem(r, 6, item_path)

    def _on_select_all_toggled(self, checked: bool) -> None:
        state = Qt.Checked if checked else Qt.Unchecked
        for r in range(self.table_projects.rowCount()):
            item = self.table_projects.item(r, 0)
            if item:
                item.setCheckState(state)

    def _on_clean_projects_clicked(self) -> None:
        selected: list[ProjectArtifact] = []
        for r in range(self.table_projects.rowCount()):
            chk = self.table_projects.item(r, 0)
            if chk and chk.checkState() == Qt.Checked:
                proj_item = self.table_projects.item(r, 1)
                art = proj_item.data(Qt.UserRole)
                if art:
                    selected.append(art)

        if not selected:
            QMessageBox.information(self, "No Selection", "Please check at least one project artifact to clean.")
            return

        total_bytes = sum(a.size for a in selected)
        reply = QMessageBox.question(
            self,
            "Confirm Project Clean",
            f"Are you sure you want to clean {len(selected)} project artifacts ({format_bytes(total_bytes)})?\n\n"
            "Source code will NOT be touched. Items will be sent to the Windows Recycle Bin and can be restored or redownloaded anytime.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if reply == QMessageBox.Yes:
            self.clean_artifacts_requested.emit(selected)

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
            # Add to All Tools
            self.tab_containers["All Tools"].insertWidget(self.tab_containers["All Tools"].count() - 1, card)

            # Add to matching tab
            eco = tool.ecosystem
            if eco in self.tab_containers:
                card_eco = DeveloperToolCard(
                    tool,
                    on_inspect=lambda t: self.item_selected.emit(t),
                    on_clean_leftover=lambda p: self.clean_broken_package_requested.emit(p),
                )
                self.tab_containers[eco].insertWidget(self.tab_containers[eco].count() - 1, card_eco)
