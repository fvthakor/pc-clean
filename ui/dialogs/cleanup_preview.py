"""Cleanup Preview Dialog: Provides full transparency before deletion."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from models.cleanup_item import CleanupCandidate
from utils.size import format_bytes


class CleanupPreviewDialog(QDialog):
    def __init__(self, candidates: list[CleanupCandidate], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("PcClean - Cleanup Preview")
        self.resize(620, 580)
        self.setMinimumSize(560, 520)
        self.candidates = candidates
        self.total_size = sum(c.size for c in candidates)
        self.total_files = sum(c.files_count for c in candidates)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 20, 22, 20)

        title = QLabel("CLEANUP PREVIEW")
        title.setProperty("class", "heading1")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;")
        layout.addWidget(title)

        subtitle = QLabel("Review items to be removed. Safe actions default to the Windows Recycle Bin.")
        subtitle.setStyleSheet("font-size: 12px; color: #8B98A7;")
        layout.addWidget(subtitle)

        # Overview banner card
        banner = QFrame()
        banner.setObjectName("previewBanner")
        banner.setStyleSheet(
            "QFrame#previewBanner { background: #17222E; border: 1px solid #26313D; border-radius: 8px; }"
        )
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(24)

        # Space Metric Card
        v_sz = QVBoxLayout()
        v_sz.setSpacing(4)
        lbl_sz_title = QLabel("TOTAL SPACE TO FREE")
        lbl_sz_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #8B98A7; background: transparent; border: none; padding: 0;"
        )
        v_sz.addWidget(lbl_sz_title)

        lbl_sz = QLabel(format_bytes(self.total_size))
        lbl_sz.setStyleSheet(
            "font-size: 24px; font-weight: 800; color: #36D399; background: transparent; border: none; padding: 0;"
        )
        v_sz.addWidget(lbl_sz)
        b_layout.addLayout(v_sz)

        # Files Metric Card
        v_fl = QVBoxLayout()
        v_fl.setSpacing(4)
        lbl_fl_title = QLabel("TOTAL FILES")
        lbl_fl_title.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #8B98A7; background: transparent; border: none; padding: 0;"
        )
        v_fl.addWidget(lbl_fl_title)

        lbl_fl = QLabel(f"{self.total_files:,}")
        lbl_fl.setStyleSheet(
            "font-size: 24px; font-weight: 800; color: #E6EDF3; background: transparent; border: none; padding: 0;"
        )
        v_fl.addWidget(lbl_fl)
        b_layout.addLayout(v_fl)

        layout.addWidget(banner)

        # Scrollable items list
        lbl_items_header = QLabel("ITEMS TO CLEAN")
        lbl_items_header.setStyleSheet("font-size: 11px; font-weight: 700; color: #8B98A7;")
        layout.addWidget(lbl_items_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(130)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #111820; border: 1px solid #26313D; border-radius: 8px; }"
            "QWidget#itemsContainer { background-color: #111820; }"
        )

        items_container = QWidget()
        items_container.setObjectName("itemsContainer")
        items_layout = QVBoxLayout(items_container)
        items_layout.setContentsMargins(10, 10, 10, 10)
        items_layout.setSpacing(8)

        for c in self.candidates:
            item_card = QFrame()
            item_card.setObjectName("itemCard")
            item_card.setStyleSheet(
                "QFrame#itemCard { background-color: #0B0F14; border: 1px solid #1F2A38; border-radius: 6px; }"
            )
            ic_layout = QHBoxLayout(item_card)
            ic_layout.setContentsMargins(12, 10, 12, 10)

            v_info = QVBoxLayout()
            v_info.setSpacing(3)
            lbl_name = QLabel(c.name)
            lbl_name.setStyleSheet(
                "font-weight: 600; color: #FFFFFF; font-size: 13px; background: transparent; border: none; padding: 0;"
            )
            v_info.addWidget(lbl_name)

            lbl_p = QLabel(str(c.path))
            lbl_p.setStyleSheet(
                "font-family: Consolas, monospace; font-size: 11px; color: #8B98A7; background: transparent; border: none; padding: 0;"
            )
            v_info.addWidget(lbl_p)
            ic_layout.addLayout(v_info)

            ic_layout.addStretch()

            lbl_sz_item = QLabel(format_bytes(c.size))
            lbl_sz_item.setStyleSheet(
                "font-weight: 700; color: #4F8CFF; font-size: 14px; background: transparent; border: none; padding: 0;"
            )
            ic_layout.addWidget(lbl_sz_item)

            items_layout.addWidget(item_card)

        items_layout.addStretch()
        scroll.setWidget(items_container)
        layout.addWidget(scroll)

        # Deletion method options
        lbl_dest_header = QLabel("DELETION DESTINATION")
        lbl_dest_header.setStyleSheet("font-size: 11px; font-weight: 700; color: #8B98A7;")
        layout.addWidget(lbl_dest_header)

        opt_box = QFrame()
        opt_box.setObjectName("destOptBox")
        opt_box.setStyleSheet(
            "QFrame#destOptBox { background-color: #111820; border: 1px solid #26313D; border-radius: 8px; }"
        )
        opt_layout = QVBoxLayout(opt_box)
        opt_layout.setContentsMargins(14, 14, 14, 14)
        opt_layout.setSpacing(10)

        self.btn_group = QButtonGroup(self)

        self.rb_recycle = QRadioButton("Move to Windows Recycle Bin (Recommended — Easy restore)")
        self.rb_recycle.setChecked(True)
        self.rb_recycle.setStyleSheet(
            "QRadioButton { color: #E6EDF3; font-size: 13px; font-weight: 500; background: transparent; border: none; padding: 2px 0px; }"
        )
        self.btn_group.addButton(self.rb_recycle, 1)
        opt_layout.addWidget(self.rb_recycle)

        self.rb_quarantine = QRadioButton("Move to PcClean Quarantine (Isolated with backup metadata)")
        self.rb_quarantine.setStyleSheet(
            "QRadioButton { color: #E6EDF3; font-size: 13px; font-weight: 500; background: transparent; border: none; padding: 2px 0px; }"
        )
        self.btn_group.addButton(self.rb_quarantine, 2)
        opt_layout.addWidget(self.rb_quarantine)

        self.rb_permanent = QRadioButton("Permanently Delete (Irreversible — Immediate space release)")
        self.rb_permanent.setStyleSheet(
            "QRadioButton { color: #E6EDF3; font-size: 13px; font-weight: 500; background: transparent; border: none; padding: 2px 0px; }"
        )
        self.btn_group.addButton(self.rb_permanent, 3)
        opt_layout.addWidget(self.rb_permanent)

        layout.addWidget(opt_box)

        # Dangerous verification input if permanent deletion chosen
        self.txt_confirm_delete = QLineEdit()
        self.txt_confirm_delete.setPlaceholderText("Type DELETE here to confirm permanent deletion")
        self.txt_confirm_delete.setStyleSheet(
            "QLineEdit { border: 1px solid #FF5C5C; background: #17222E; color: #FFFFFF; font-weight: 600; padding: 8px 12px; border-radius: 6px; }"
        )
        self.txt_confirm_delete.setVisible(False)
        layout.addWidget(self.txt_confirm_delete)

        self.rb_permanent.toggled.connect(lambda checked: self.txt_confirm_delete.setVisible(checked))

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedSize(90, 36)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("Confirm Clean")
        self.btn_confirm.setFixedSize(130, 36)
        self.btn_confirm.setProperty("class", "danger")
        self.btn_confirm.setStyleSheet(
            "QPushButton { background-color: #CF222E; color: #FFFFFF; font-weight: 700; border-radius: 6px; }"
            "QPushButton:hover { background-color: #E5534B; }"
        )
        self.btn_confirm.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self.btn_confirm)

        layout.addLayout(btn_layout)

    def _on_confirm(self) -> None:
        if self.rb_permanent.isChecked():
            if self.txt_confirm_delete.text().strip() != "DELETE":
                QMessageBox.warning(
                    self,
                    "Confirmation Required",
                    "To permanently delete files, you must type 'DELETE' in the confirmation box.",
                )
                return
        self.accept()

    def get_options(self) -> tuple[bool, bool, bool]:
        """Returns (use_recycle_bin, use_quarantine, is_permanent)."""
        if self.rb_quarantine.isChecked():
            return False, True, False
        elif self.rb_permanent.isChecked():
            return False, False, True
        return True, False, False
