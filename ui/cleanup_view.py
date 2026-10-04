"""Cleanup View: Safe junk, package manager, and framework cache cleanup table."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants import CleanupCategory, SafetyLevel
from models.cleanup_item import CleanupCandidate
from utils.size import format_bytes


class CleanupView(QWidget):
    item_selected = Signal(object)  # Emits CleanupCandidate
    clean_single_requested = Signal(object)  # Emits single candidate
    clean_batch_requested = Signal(list)  # Emits list of selected candidates
    preview_batch_requested = Signal(list)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.candidates: list[CleanupCandidate] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header Bar & Developer Presets
        top_bar = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("SYSTEM & CACHE CLEANUP")
        title.setProperty("class", "heading1")
        sub = QLabel("Select safe caches, build artifacts, and package stores to reclaim storage")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top_bar.addLayout(v_title)
        top_bar.addStretch()

        top_bar.addWidget(QLabel("Developer Preset:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItems(
            [
                "Safe Caches (Recommended)",
                "Full Stack Developer",
                "Python / AI Developer",
                "Android Developer",
                "Select All Safe",
            ]
        )
        self.combo_presets.currentIndexChanged.connect(self._apply_preset)
        top_bar.addWidget(self.combo_presets)

        layout.addLayout(top_bar)

        # Candidates Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Sel", "Category", "Name", "Size", "Safety", "Path", "Action"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.resizeSection(1, 120)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.resizeSection(2, 180)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.resizeSection(3, 90)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.resizeSection(4, 100)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 110)

        self.table.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.table)

        # Bottom Summary & Action Bar
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 8px; padding: 10px;")
        b_layout = QHBoxLayout(bottom_bar)

        self.lbl_selected_summary = QLabel("Selected: 0 B (0 items)")
        self.lbl_selected_summary.setStyleSheet("font-size: 14px; font-weight: 700; color: #4F8CFF;")
        b_layout.addWidget(self.lbl_selected_summary)
        b_layout.addStretch()

        self.btn_select_all = QPushButton("Select All")
        self.btn_select_all.clicked.connect(self._select_all)
        b_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("Deselect All")
        self.btn_deselect_all.clicked.connect(self._deselect_all)
        b_layout.addWidget(self.btn_deselect_all)

        self.btn_preview = QPushButton("Preview Cleanup")
        self.btn_preview.clicked.connect(self._on_preview_batch)
        b_layout.addWidget(self.btn_preview)

        self.btn_clean_selected = QPushButton("Clean Selected")
        self.btn_clean_selected.setProperty("class", "danger")
        self.btn_clean_selected.clicked.connect(self._on_clean_batch)
        b_layout.addWidget(self.btn_clean_selected)

        layout.addWidget(bottom_bar)

    def populate_candidates(self, candidates: list[CleanupCandidate]) -> None:
        self.candidates = candidates
        self.table.setRowCount(len(candidates))

        for row, c in enumerate(candidates):
            # Checkbox
            chk = QCheckBox()
            chk.setChecked(c.is_selected)
            chk.stateChanged.connect(lambda state, cand=c: self._on_check_changed(cand, state))
            chk_widget = QWidget()
            chk_layout = QHBoxLayout(chk_widget)
            chk_layout.addWidget(chk)
            chk_layout.setAlignment(Qt.AlignCenter)
            chk_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, chk_widget)

            # Category
            cat_str = c.category.value if hasattr(c.category, "value") else str(c.category)
            item_cat = QTableWidgetItem(cat_str)
            item_cat.setData(Qt.UserRole, c)
            self.table.setItem(row, 1, item_cat)

            # Name
            item_name = QTableWidgetItem(c.name)
            item_name.setToolTip(c.description)
            self.table.setItem(row, 2, item_name)

            # Size
            item_size = QTableWidgetItem(format_bytes(c.size))
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, item_size)

            # Safety
            safety_str = c.safety_level.value if hasattr(c.safety_level, "value") else str(c.safety_level)
            item_safety = QTableWidgetItem(safety_str)
            if c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD):
                item_safety.setForeground(Qt.green)
            elif c.safety_level == SafetyLevel.REVIEW:
                item_safety.setForeground(Qt.yellow)
            else:
                item_safety.setForeground(Qt.red)
            self.table.setItem(row, 4, item_safety)

            # Path
            item_path = QTableWidgetItem(str(c.path))
            item_path.setToolTip(str(c.path))
            self.table.setItem(row, 5, item_path)

            # Action
            btn_clean = QPushButton("Clean")
            btn_clean.setFixedSize(70, 24)
            btn_clean.setProperty("class", "danger")
            btn_clean.clicked.connect(lambda ch, cand=c: self.clean_single_requested.emit(cand))
            self.table.setCellWidget(row, 6, btn_clean)

        self._update_selected_summary()

    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        cand = self.table.item(item.row(), 1).data(Qt.UserRole)
        if cand:
            self.item_selected.emit(cand)

    def _on_check_changed(self, cand: CleanupCandidate, state: int) -> None:
        cand.is_selected = state == Qt.Checked.value or state == 2
        self._update_selected_summary()

    def _update_selected_summary(self) -> None:
        selected = [c for c in self.candidates if c.is_selected]
        tot_bytes = sum(c.size for c in selected)
        self.lbl_selected_summary.setText(f"Selected: {format_bytes(tot_bytes)} ({len(selected)} items)")
        self.btn_clean_selected.setEnabled(len(selected) > 0)
        self.btn_preview.setEnabled(len(selected) > 0)

    def _select_all(self) -> None:
        for c in self.candidates:
            c.is_selected = True
        self._refresh_checkboxes()

    def _deselect_all(self) -> None:
        for c in self.candidates:
            c.is_selected = False
        self._refresh_checkboxes()

    def _apply_preset(self, index: int) -> None:
        for c in self.candidates:
            if index == 0:  # Safe Caches
                c.is_selected = c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD)
            elif index == 1:  # Full Stack
                c.is_selected = c.category in (
                    CleanupCategory.NODE_CACHE,
                    CleanupCategory.BROWSER_CACHE,
                    CleanupCategory.GRADLE_CACHE,
                    CleanupCategory.USER_TEMP,
                )
            elif index == 2:  # Python / AI
                c.is_selected = c.category in (
                    CleanupCategory.PYTHON_CACHE,
                    CleanupCategory.USER_TEMP,
                    CleanupCategory.AI_MODELS,
                )
            elif index == 3:  # Android
                c.is_selected = c.category in (
                    CleanupCategory.ANDROID_SDK,
                    CleanupCategory.GRADLE_CACHE,
                    CleanupCategory.FLUTTER_CACHE,
                )
            elif index == 4:  # All Safe
                c.is_selected = c.safety_level == SafetyLevel.SAFE
        self._refresh_checkboxes()

    def _refresh_checkboxes(self) -> None:
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                chk = widget.findChild(QCheckBox)
                if chk and row < len(self.candidates):
                    chk.blockSignals(True)
                    chk.setChecked(self.candidates[row].is_selected)
                    chk.blockSignals(False)
        self._update_selected_summary()

    def _on_clean_batch(self) -> None:
        selected = [c for c in self.candidates if c.is_selected]
        if selected:
            self.clean_batch_requested.emit(selected)

    def _on_preview_batch(self) -> None:
        selected = [c for c in self.candidates if c.is_selected]
        if selected:
            self.preview_batch_requested.emit(selected)
