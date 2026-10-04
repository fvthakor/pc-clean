"""Folder & Item Details Inspector Panel."""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.constants import SafetyLevel
from models.safety_result import SafetyResult
from utils.size import format_bytes
from utils.windows import open_in_explorer


class DetailsPanel(QFrame):
    clean_requested = Signal(object)  # emits target Path or item
    protect_requested = Signal(object)
    preview_requested = Signal(object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumWidth(320)
        self.setMaximumWidth(400)
        self.current_item = None
        self.current_path: Path | None = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("INSPECTOR DETAILS")
        title.setProperty("class", "heading2")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.clicked.connect(self.hide)
        header_layout.addWidget(self.btn_close)
        layout.addLayout(header_layout)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)

        # Item Name
        self.lbl_name = QLabel("Select an item to inspect")
        self.lbl_name.setProperty("class", "heading1")
        self.lbl_name.setWordWrap(True)
        self.content_layout.addWidget(self.lbl_name)

        # Badges row (Safety & Protected)
        badge_layout = QHBoxLayout()
        self.lbl_safety_badge = QLabel("READY")
        self.lbl_safety_badge.setProperty("class", "badge-safe")
        badge_layout.addWidget(self.lbl_safety_badge)

        self.lbl_protected_badge = QLabel("UNPROTECTED")
        self.lbl_protected_badge.setStyleSheet(
            "background: #17222E; color: #8B98A7; border: 1px solid #26313D; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 600;"
        )
        badge_layout.addWidget(self.lbl_protected_badge)
        badge_layout.addStretch()
        self.content_layout.addLayout(badge_layout)

        # Key metrics row (Size, Files, Folders)
        metrics_box = QFrame()
        metrics_box.setStyleSheet("background: #17222E; border: 1px solid #26313D; border-radius: 6px; padding: 10px;")
        m_layout = QHBoxLayout(metrics_box)
        m_layout.setContentsMargins(8, 8, 8, 8)

        v1 = QVBoxLayout()
        l_sz_title = QLabel("SIZE")
        l_sz_title.setProperty("class", "muted")
        self.lbl_size = QLabel("0 B")
        self.lbl_size.setStyleSheet("font-size: 16px; font-weight: 700; color: #4F8CFF;")
        v1.addWidget(l_sz_title)
        v1.addWidget(self.lbl_size)
        m_layout.addLayout(v1)

        v2 = QVBoxLayout()
        l_fl_title = QLabel("FILES")
        l_fl_title.setProperty("class", "muted")
        self.lbl_files = QLabel("0")
        self.lbl_files.setStyleSheet("font-size: 14px; font-weight: 600;")
        v2.addWidget(l_fl_title)
        v2.addWidget(self.lbl_files)
        m_layout.addLayout(v2)

        v3 = QVBoxLayout()
        l_fo_title = QLabel("FOLDERS")
        l_fo_title.setProperty("class", "muted")
        self.lbl_folders = QLabel("0")
        self.lbl_folders.setStyleSheet("font-size: 14px; font-weight: 600;")
        v3.addWidget(l_fo_title)
        v3.addWidget(self.lbl_folders)
        m_layout.addLayout(v3)

        self.content_layout.addWidget(metrics_box)

        # Category & Status
        meta_layout = QVBoxLayout()
        self.lbl_category = QLabel("Category: -")
        self.lbl_category.setProperty("class", "muted")
        meta_layout.addWidget(self.lbl_category)

        self.lbl_status = QLabel("Status: -")
        self.lbl_status.setProperty("class", "muted")
        meta_layout.addWidget(self.lbl_status)
        self.content_layout.addLayout(meta_layout)

        # Exact Path Box
        self.content_layout.addWidget(QLabel("EXACT PATH"))
        self.txt_path = QTextEdit()
        self.txt_path.setReadOnly(True)
        self.txt_path.setFixedHeight(65)
        self.txt_path.setStyleSheet(
            "background: #0B0F14; border: 1px solid #26313D; font-family: Consolas, monospace; font-size: 11px; color: #8B98A7;"
        )
        self.content_layout.addWidget(self.txt_path)

        # Smart Assistant Explanation Box
        self.content_layout.addWidget(QLabel("CLEANUP IMPACT & EXPLANATION"))
        self.txt_explanation = QTextEdit()
        self.txt_explanation.setReadOnly(True)
        self.txt_explanation.setFixedHeight(110)
        self.txt_explanation.setStyleSheet(
            "background: #17222E; border: 1px solid #26313D; border-radius: 6px; padding: 6px; font-size: 12px; line-height: 1.4;"
        )
        self.content_layout.addWidget(self.txt_explanation)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Action Buttons
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)

        h_actions = QHBoxLayout()
        self.btn_open = QPushButton("Open Folder")
        self.btn_open.clicked.connect(self._on_open_clicked)
        h_actions.addWidget(self.btn_open)

        self.btn_copy = QPushButton("Copy Path")
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        h_actions.addWidget(self.btn_copy)
        btn_layout.addLayout(h_actions)

        self.btn_protect = QPushButton("⭐ Mark Important / Protect")
        self.btn_protect.clicked.connect(self._on_protect_clicked)
        btn_layout.addWidget(self.btn_protect)

        self.btn_preview = QPushButton("Preview Cleanup")
        self.btn_preview.clicked.connect(self._on_preview_clicked)
        btn_layout.addWidget(self.btn_preview)

        self.btn_clean = QPushButton("CLEAN NOW")
        self.btn_clean.setProperty("class", "danger")
        self.btn_clean.clicked.connect(self._on_clean_clicked)
        btn_layout.addWidget(self.btn_clean)

        layout.addLayout(btn_layout)

    def set_folder_item(self, item, safety: SafetyResult | None = None) -> None:
        """Display a FolderItem from the Storage Analyzer."""
        self.current_item = item
        self.current_path = Path(item.path)
        self.lbl_name.setText(item.name)
        self.txt_path.setText(str(item.path))
        self.lbl_size.setText(format_bytes(item.size))
        self.lbl_files.setText(f"{item.files_count:,}")
        self.lbl_folders.setText(f"{item.subfolders_count:,}")
        self.lbl_category.setText(f"Category: {item.category}")
        self.lbl_status.setText("Status: Inspected")

        # Evaluate safety
        s = safety or item.safety_result
        self._apply_safety_result(s)
        self.show()

    def set_cleanup_candidate(self, candidate) -> None:
        """Display a CleanupCandidate."""
        self.current_item = candidate
        self.current_path = Path(candidate.path)
        self.lbl_name.setText(candidate.name)
        self.txt_path.setText(str(candidate.path))
        self.lbl_size.setText(format_bytes(candidate.size))
        self.lbl_files.setText(f"{candidate.files_count:,}")
        self.lbl_folders.setText("-")
        self.lbl_category.setText(
            f"Category: {candidate.category.value if hasattr(candidate.category, 'value') else candidate.category}"
        )
        self.lbl_status.setText(f"Status: {candidate.status}")

        level = candidate.safety_level
        self._update_safety_badge(level, candidate.reason)

        if candidate.explanation:
            self.txt_explanation.setText(candidate.explanation)
        else:
            self.txt_explanation.setText(candidate.reason)

        can_clean = (level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD)) and not candidate.is_protected
        self.btn_clean.setEnabled(can_clean)
        self.btn_preview.setEnabled(True)
        self.show()

    def _apply_safety_result(self, s: SafetyResult | None) -> None:
        if not s:
            self.lbl_safety_badge.setText("REVIEW")
            self.lbl_safety_badge.setProperty("class", "badge-review")
            self.txt_explanation.setText("Folder contents have not been classified. Review carefully before removing.")
            self.btn_clean.setEnabled(False)
            return

        self._update_safety_badge(s.level, s.reason)
        exp = s.reason
        if s.recommendation:
            exp += f"\n\nRecommendation: {s.recommendation}"
        self.txt_explanation.setText(exp)

        # Deletion safety guard
        self.btn_clean.setEnabled(s.can_delete and not s.is_protected)
        if not s.can_delete:
            self.btn_clean.setToolTip(f"Cleanup disabled: {s.reason}")
        else:
            self.btn_clean.setToolTip("")

    def _update_safety_badge(self, level: SafetyLevel, reason: str) -> None:
        val = level.value if hasattr(level, "value") else str(level)
        self.lbl_safety_badge.setText(val)
        if level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD):
            self.lbl_safety_badge.setStyleSheet(
                "background: #163B26; color: #36D399; border: 1px solid #22543D; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;"
            )
        elif level == SafetyLevel.REVIEW:
            self.lbl_safety_badge.setStyleSheet(
                "background: #3D2D0C; color: #F5B942; border: 1px solid #5C4312; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;"
            )
        elif level == SafetyLevel.IMPORTANT:
            self.lbl_safety_badge.setStyleSheet(
                "background: #1F2544; color: #7C8CFF; border: 1px solid #2F3866; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;"
            )
        else:
            self.lbl_safety_badge.setStyleSheet(
                "background: #3D1217; color: #FF5C5C; border: 1px solid #5C1D24; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 11px;"
            )

    def _on_open_clicked(self) -> None:
        if self.current_path and self.current_path.exists():
            open_in_explorer(str(self.current_path))

    def _on_copy_clicked(self) -> None:
        if self.current_path:
            QApplication.clipboard().setText(str(self.current_path.resolve()))

    def _on_protect_clicked(self) -> None:
        if self.current_path:
            self.protect_requested.emit(self.current_path)

    def _on_preview_clicked(self) -> None:
        if self.current_item:
            self.preview_requested.emit(self.current_item)

    def _on_clean_clicked(self) -> None:
        if self.current_item:
            self.clean_requested.emit(self.current_item)
