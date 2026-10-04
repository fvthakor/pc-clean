"""Settings View for PcClean configuration."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig


class SettingsView(QWidget):
    settings_saved = Signal(object)  # Emits updated AppConfig

    def __init__(self, config: AppConfig | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.config = config or AppConfig.load()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        title = QLabel("SETTINGS & PREFERENCES")
        title.setProperty("class", "heading1")
        sub = QLabel("Configure scan behavior, safety policies, and cleanup defaults")
        sub.setProperty("class", "muted")
        main_layout.addWidget(title)
        main_layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # 1. General Section
        sec_gen = QFrame()
        sec_gen.setProperty("class", "card")
        l_gen = QVBoxLayout(sec_gen)
        lbl_g = QLabel("GENERAL")
        lbl_g.setProperty("class", "heading2")
        l_gen.addWidget(lbl_g)

        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("Interface Theme:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["dark", "light", "system"])
        self.combo_theme.setCurrentText(self.config.theme)
        row_theme.addWidget(self.combo_theme)
        row_theme.addStretch()
        l_gen.addLayout(row_theme)

        row_drv = QHBoxLayout()
        row_drv.addWidget(QLabel("Default Drive:"))
        self.combo_def_drive = QComboBox()
        self.combo_def_drive.addItems(["C:", "D:", "E:", "F:"])
        self.combo_def_drive.setCurrentText(self.config.default_drive)
        row_drv.addWidget(self.combo_def_drive)
        row_drv.addStretch()
        l_gen.addLayout(row_drv)

        self.chk_startup = QCheckBox("Run fast scan automatically on application startup")
        self.chk_startup.setChecked(self.config.startup_scan)
        l_gen.addWidget(self.chk_startup)
        layout.addWidget(sec_gen)

        # 2. Scanning Section
        sec_scan = QFrame()
        sec_scan.setProperty("class", "card")
        l_scan = QVBoxLayout(sec_scan)
        lbl_s = QLabel("SCANNING ENGINE")
        lbl_s.setProperty("class", "heading2")
        l_scan.addWidget(lbl_s)

        self.chk_hidden = QCheckBox("Scan hidden files and folders")
        self.chk_hidden.setChecked(self.config.scan_hidden_files)
        l_scan.addWidget(self.chk_hidden)

        self.chk_symlinks = QCheckBox("Follow symbolic links and NTFS junctions (NOT recommended - risk of loops)")
        self.chk_symlinks.setChecked(self.config.follow_symlinks)
        l_scan.addWidget(self.chk_symlinks)

        self.chk_network = QCheckBox("Scan mapped network drives")
        self.chk_network.setChecked(self.config.scan_network_drives)
        l_scan.addWidget(self.chk_network)
        layout.addWidget(sec_scan)

        # 3. Cleanup & Safety Section
        sec_clean = QFrame()
        sec_clean.setProperty("class", "card")
        l_clean = QVBoxLayout(sec_clean)
        lbl_c = QLabel("SAFETY & CLEANUP DEFAULTS")
        lbl_c.setProperty("class", "heading2")
        l_clean.addWidget(lbl_c)

        self.chk_recycle = QCheckBox("Move files to Windows Recycle Bin by default instead of permanent deletion")
        self.chk_recycle.setChecked(self.config.use_recycle_bin)
        l_clean.addWidget(self.chk_recycle)

        self.chk_quarantine = QCheckBox("Use PcClean Quarantine folder (%LOCALAPPDATA%\\PcClean\\Quarantine)")
        self.chk_quarantine.setChecked(self.config.use_quarantine)
        l_clean.addWidget(self.chk_quarantine)

        self.chk_confirm = QCheckBox("Require confirmation and preview dialog before any deletion")
        self.chk_confirm.setChecked(self.config.require_confirmation)
        l_clean.addWidget(self.chk_confirm)

        row_ret = QHBoxLayout()
        row_ret.addWidget(QLabel("Audit history retention (days):"))
        self.spin_ret = QSpinBox()
        self.spin_ret.setRange(7, 365)
        self.spin_ret.setValue(self.config.history_retention_days)
        row_ret.addWidget(self.spin_ret)
        row_ret.addStretch()
        l_clean.addLayout(row_ret)
        layout.addWidget(sec_clean)

        # Save button
        btn_save = QPushButton("Save Settings")
        btn_save.setProperty("class", "primary")
        btn_save.setFixedHeight(34)
        btn_save.clicked.connect(self._on_save_clicked)
        layout.addWidget(btn_save)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _on_save_clicked(self) -> None:
        self.config.theme = self.combo_theme.currentText()
        self.config.default_drive = self.combo_def_drive.currentText()
        self.config.startup_scan = self.chk_startup.isChecked()
        self.config.scan_hidden_files = self.chk_hidden.isChecked()
        self.config.follow_symlinks = self.chk_symlinks.isChecked()
        self.config.scan_network_drives = self.chk_network.isChecked()
        self.config.use_recycle_bin = self.chk_recycle.isChecked()
        self.config.use_quarantine = self.chk_quarantine.isChecked()
        self.config.require_confirmation = self.chk_confirm.isChecked()
        self.config.history_retention_days = self.spin_ret.value()
        self.config.save()
        self.settings_saved.emit(self.config)
