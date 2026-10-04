"""PcClean Sidebar Navigation Component."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from models.drive import DriveInfo
from utils.windows import is_admin


class Sidebar(QFrame):
    page_changed = Signal(int)  # Emits target page index
    drive_changed = Signal(str)  # Emits selected drive letter (e.g. "C:")

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet("background-color: #0E141B; border-right: 1px solid #1F2A38;")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(12)

        # Brand header
        brand_layout = QHBoxLayout()
        lbl_logo = QLabel("🧹")
        lbl_logo.setStyleSheet("font-size: 22px;")
        brand_layout.addWidget(lbl_logo)

        v_title = QVBoxLayout()
        lbl_title = QLabel("PCCLEAN")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #4F8CFF; letter-spacing: 1px;")
        lbl_sub = QLabel("Developer Storage Suite")
        lbl_sub.setStyleSheet("font-size: 10px; color: #64748B; font-weight: 500;")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)
        brand_layout.addLayout(v_title)
        brand_layout.addStretch()
        layout.addLayout(brand_layout)

        # Admin status badge
        has_admin = is_admin()
        lbl_admin = QLabel("🛡️ Administrator" if has_admin else "👤 Standard User")
        if has_admin:
            lbl_admin.setStyleSheet(
                "background: #163B26; color: #36D399; border: 1px solid #22543D; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: 600;"
            )
            lbl_admin.setToolTip("Running with elevated permissions. System folders can be cleaned when approved.")
        else:
            lbl_admin.setStyleSheet(
                "background: #17222E; color: #8B98A7; border: 1px solid #26313D; border-radius: 4px; padding: 4px 8px; font-size: 11px;"
            )
            lbl_admin.setToolTip(
                "Running normally without elevation. Elevation requested only for actions that require it."
            )
        layout.addWidget(lbl_admin)

        # Drive selector box
        drive_box = QVBoxLayout()
        lbl_drv = QLabel("ACTIVE DRIVE")
        lbl_drv.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B;")
        drive_box.addWidget(lbl_drv)

        self.combo_drives = QComboBox()
        self.combo_drives.setFixedHeight(32)
        self.combo_drives.currentIndexChanged.connect(self._on_drive_index_changed)
        drive_box.addWidget(self.combo_drives)
        layout.addLayout(drive_box)

        # Navigation menu items
        layout.addWidget(QLabel("NAVIGATION"))
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_buttons: list[QPushButton] = []
        pages = [
            ("📊  Dashboard", 0),
            ("💾  Storage", 1),
            ("🧹  Cleanup", 2),
            ("⚡  Developer", 3),
            ("📦  Applications", 4),
            ("📁  Large Files", 5),
            ("👥  Duplicates", 6),
            ("🛡️  Protected", 7),
            ("📜  History", 8),
            ("⚙️  Settings", 9),
        ]

        for text, index in pages:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setStyleSheet(
                "QPushButton { text-align: left; padding-left: 12px; border: none; border-radius: 6px; font-weight: 500; } "
                "QPushButton:hover { background-color: #17222E; color: #4F8CFF; } "
                "QPushButton:checked { background-color: #1C2D42; color: #4F8CFF; font-weight: 700; border-left: 3px solid #4F8CFF; }"
            )
            btn.clicked.connect(lambda checked, idx=index: self.page_changed.emit(idx))
            self.nav_group.addButton(btn, index)
            self.nav_buttons.append(btn)
            layout.addWidget(btn)

        # Default select Dashboard
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

        layout.addStretch()

        # Footer version
        lbl_ver = QLabel("PcClean v1.0.0")
        lbl_ver.setStyleSheet("font-size: 10px; color: #475569; text-align: center;")
        lbl_ver.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_ver)

    def populate_drives(self, drives: list[DriveInfo], active_letter: str = "C:") -> None:
        """Populate the drives dropdown."""
        self.combo_drives.blockSignals(True)
        self.combo_drives.clear()
        selected_idx = 0
        for i, d in enumerate(drives):
            self.combo_drives.addItem(d.display_name, d.letter)
            if d.letter.upper() == active_letter.upper():
                selected_idx = i
        self.combo_drives.setCurrentIndex(selected_idx)
        self.combo_drives.blockSignals(False)

    def _on_drive_index_changed(self, idx: int) -> None:
        letter = self.combo_drives.itemData(idx)
        if letter:
            self.drive_changed.emit(letter)

    def set_active_page(self, index: int) -> None:
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)
