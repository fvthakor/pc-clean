"""Dashboard View: System drive overview, telemetry cards, developer snapshot."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.drive import DriveInfo
from models.scan_result import ScanSummary
from utils.size import format_bytes


class MetricCard(QFrame):
    def __init__(self, title: str, value: str, subtext: str, color_hex: str = "#4F8CFF"):
        super().__init__()
        self.setProperty("class", "card")
        self.setStyleSheet(
            f"QFrame.card {{ background-color: #111820; border: 1px solid #26313D; "
            f"border-radius: 8px; padding: 12px; }} "
            f"QFrame.card:hover {{ border-color: {color_hex}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #8B98A7; letter-spacing: 0.5px;")
        layout.addWidget(lbl_title)

        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {color_hex};")
        layout.addWidget(self.lbl_value)

        self.lbl_sub = QLabel(subtext)
        self.lbl_sub.setStyleSheet("font-size: 11px; color: #64748B;")
        layout.addWidget(self.lbl_sub)

    def set_value(self, value: str, subtext: str | None = None) -> None:
        self.lbl_value.setText(value)
        if subtext:
            self.lbl_sub.setText(subtext)


class DashboardView(QWidget):
    scan_requested = Signal(str)
    quick_clean_requested = Signal()
    open_storage_requested = Signal()
    scan_all_drives_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header Title & Quick Action Buttons
        header = QHBoxLayout()
        v_titles = QVBoxLayout()
        title = QLabel("SYSTEM DASHBOARD")
        title.setProperty("class", "heading1")
        sub = QLabel("Comprehensive disk usage, cache telemetry, and developer environment safety")
        sub.setProperty("class", "muted")
        v_titles.addWidget(title)
        v_titles.addWidget(sub)
        header.addLayout(v_titles)
        header.addStretch()

        self.btn_scan = QPushButton("🔍 Scan Now")
        self.btn_scan.setProperty("class", "primary")
        self.btn_scan.setFixedHeight(34)
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        header.addWidget(self.btn_scan)

        self.btn_quick_clean = QPushButton("⚡ Quick Clean")
        self.btn_quick_clean.setProperty("class", "success")
        self.btn_quick_clean.setFixedHeight(34)
        self.btn_quick_clean.clicked.connect(self.quick_clean_requested.emit)
        header.addWidget(self.btn_quick_clean)

        self.btn_storage_analyzer = QPushButton("📊 Storage Analyzer")
        self.btn_storage_analyzer.setFixedHeight(34)
        self.btn_storage_analyzer.clicked.connect(self.open_storage_requested.emit)
        header.addWidget(self.btn_storage_analyzer)

        layout.addLayout(header)

        # Main Storage Drive Hero Card
        self.hero_card = QFrame()
        self.hero_card.setProperty("class", "card")
        self.hero_card.setStyleSheet(
            "background: #111820; border: 1px solid #26313D; border-radius: 8px; padding: 16px;"
        )
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setSpacing(12)

        hero_top = QHBoxLayout()
        self.lbl_hero_drive = QLabel("C: System Drive")
        self.lbl_hero_drive.setProperty("class", "heading2")
        hero_top.addWidget(self.lbl_hero_drive)
        hero_top.addStretch()

        self.lbl_hero_usage_text = QLabel("Used: 0 GB / Free: 0 GB")
        self.lbl_hero_usage_text.setStyleSheet("color: #8B98A7; font-weight: 600;")
        hero_top.addWidget(self.lbl_hero_usage_text)
        hero_layout.addLayout(hero_top)

        # Big Storage Progress Bar
        self.hero_progress = QProgressBar()
        self.hero_progress.setFixedHeight(22)
        self.hero_progress.setRange(0, 100)
        self.hero_progress.setValue(0)
        self.hero_progress.setStyleSheet(
            "QProgressBar { background: #17222E; border: 1px solid #26313D; border-radius: 6px; text-align: center; font-weight: 700; color: #FFFFFF; } "
            "QProgressBar::chunk { background-color: #4F8CFF; border-radius: 5px; }"
        )
        hero_layout.addWidget(self.hero_progress)

        hero_metrics = QHBoxLayout()
        self.lbl_hero_total = QLabel("Total: 0 GB")
        self.lbl_hero_total.setStyleSheet("color: #E6EDF3; font-weight: 600;")
        self.lbl_hero_used = QLabel("Used: 0 GB")
        self.lbl_hero_used.setStyleSheet("color: #F5B942; font-weight: 600;")
        self.lbl_hero_free = QLabel("Free: 0 GB")
        self.lbl_hero_free.setStyleSheet("color: #36D399; font-weight: 600;")

        hero_metrics.addWidget(self.lbl_hero_total)
        hero_metrics.addSpacing(20)
        hero_metrics.addWidget(self.lbl_hero_used)
        hero_metrics.addSpacing(20)
        hero_metrics.addWidget(self.lbl_hero_free)
        hero_metrics.addStretch()
        hero_layout.addLayout(hero_metrics)

        layout.addWidget(self.hero_card)

        # 6 Telemetry Metric Cards in Grid
        grid = QGridLayout()
        grid.setSpacing(12)

        self.card_potential = MetricCard("Potential Cleanup", "0 B", "All unneeded cache candidates", "#4F8CFF")
        grid.addWidget(self.card_potential, 0, 0)

        self.card_safe = MetricCard("Safe Cleanup", "0 B", "Zero-risk caches (ready to clean)", "#36D399")
        grid.addWidget(self.card_safe, 0, 1)

        self.card_review = MetricCard("Review Required", "0 B", "Old versions & uninstalled remnants", "#F5B942")
        grid.addWidget(self.card_review, 0, 2)

        self.card_protected = MetricCard("Protected Paths", "8 items", "Blocked from automatic deletion", "#7C8CFF")
        grid.addWidget(self.card_protected, 1, 0)

        self.card_large = MetricCard("Large Files", "0 B", "Files exceeding 100 MB", "#E6EDF3")
        grid.addWidget(self.card_large, 1, 1)

        self.card_leftovers = MetricCard("Possible Leftovers", "0 B", "Remnants of uninstalled apps", "#FF5C5C")
        grid.addWidget(self.card_leftovers, 1, 2)

        layout.addLayout(grid)

        # Multi-Drive Section
        drv_header = QHBoxLayout()
        drv_title = QLabel("CONNECTED STORAGE DRIVES")
        drv_title.setProperty("class", "heading2")
        drv_header.addWidget(drv_title)
        drv_header.addStretch()

        btn_scan_all = QPushButton("Scan All Drives")
        btn_scan_all.clicked.connect(self.scan_all_drives_requested.emit)
        drv_header.addWidget(btn_scan_all)
        layout.addLayout(drv_header)

        self.drives_container = QVBoxLayout()
        self.drives_container.setSpacing(10)
        layout.addLayout(self.drives_container)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self.current_drive_letter = "C:"

    def update_drive_hero(self, drive: DriveInfo) -> None:
        self.current_drive_letter = drive.letter
        self.lbl_hero_drive.setText(f"{drive.letter} - {drive.name or 'Local Drive'} ({drive.drive_type.value})")
        self.lbl_hero_total.setText(f"Total: {format_bytes(drive.total_bytes)}")
        self.lbl_hero_used.setText(f"Used: {format_bytes(drive.used_bytes)} ({drive.percent:.1f}%)")
        self.lbl_hero_free.setText(f"Free: {format_bytes(drive.free_bytes)}")
        self.lbl_hero_usage_text.setText(
            f"{format_bytes(drive.used_bytes)} Used / {format_bytes(drive.free_bytes)} Free"
        )
        self.hero_progress.setValue(int(drive.percent))
        if drive.percent > 90:
            self.hero_progress.setStyleSheet(
                "QProgressBar { background: #17222E; border: 1px solid #26313D; border-radius: 6px; text-align: center; color: white; } "
                "QProgressBar::chunk { background-color: #CF222E; border-radius: 5px; }"
            )
        else:
            self.hero_progress.setStyleSheet(
                "QProgressBar { background: #17222E; border: 1px solid #26313D; border-radius: 6px; text-align: center; color: white; } "
                "QProgressBar::chunk { background-color: #4F8CFF; border-radius: 5px; }"
            )

    def update_telemetry(self, summary: ScanSummary) -> None:
        self.card_potential.set_value(format_bytes(summary.potential_cleanup_bytes))
        self.card_safe.set_value(format_bytes(summary.safe_cleanup_bytes))
        self.card_review.set_value(format_bytes(summary.review_required_bytes))
        self.card_protected.set_value(
            f"{summary.protected_bytes} items"
            if summary.protected_bytes < 1000
            else format_bytes(summary.protected_bytes)
        )
        if summary.large_files_bytes > 0:
            self.card_large.set_value(format_bytes(summary.large_files_bytes))
        if summary.leftovers_bytes > 0:
            self.card_leftovers.set_value(format_bytes(summary.leftovers_bytes))

    def populate_multi_drives(self, drives: list[DriveInfo]) -> None:
        # Clear existing
        while self.drives_container.count():
            item = self.drives_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for d in drives:
            d_card = QFrame()
            d_card.setProperty("class", "card")
            d_card.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 6px; padding: 10px;")
            dc_layout = QHBoxLayout(d_card)

            v_info = QVBoxLayout()
            lbl_l = QLabel(f"{d.letter}  {d.name or 'Drive'} ({d.drive_type.value})")
            lbl_l.setStyleSheet("font-weight: 700; color: #FFFFFF;")
            lbl_fs = QLabel(f"Filesystem: {d.fstype} | Total: {format_bytes(d.total_bytes)}")
            lbl_fs.setProperty("class", "muted")
            v_info.addWidget(lbl_l)
            v_info.addWidget(lbl_fs)
            dc_layout.addLayout(v_info)

            # Bar
            bar = QProgressBar()
            bar.setFixedWidth(180)
            bar.setFixedHeight(14)
            bar.setValue(int(d.percent))
            bar.setTextVisible(True)
            dc_layout.addWidget(bar)

            # Details
            lbl_uf = QLabel(f"{format_bytes(d.free_bytes)} Free ({100 - d.percent:.0f}%)")
            lbl_uf.setStyleSheet("font-weight: 600; color: #36D399;")
            dc_layout.addWidget(lbl_uf)

            # Action button
            btn_scan_d = QPushButton("Scan")
            btn_scan_d.setFixedWidth(70)
            btn_scan_d.clicked.connect(lambda ch, ltr=d.letter: self.scan_requested.emit(ltr))
            dc_layout.addWidget(btn_scan_d)

            self.drives_container.addWidget(d_card)

    def _on_scan_clicked(self) -> None:
        self.scan_requested.emit(self.current_drive_letter)
