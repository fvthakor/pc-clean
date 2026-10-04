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
        self.setMinimumSize(560, 480)
        self.candidates = candidates
        self.total_size = sum(c.size for c in candidates)
        self.total_files = sum(c.files_count for c in candidates)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("CLEANUP PREVIEW")
        title.setProperty("class", "heading1")
        layout.addWidget(title)

        subtitle = QLabel("Review items to be removed. Safe actions default to the Windows Recycle Bin.")
        subtitle.setProperty("class", "muted")
        layout.addWidget(subtitle)

        # Overview banner card
        banner = QFrame()
        banner.setStyleSheet("background: #17222E; border: 1px solid #26313D; border-radius: 6px; padding: 12px;")
        b_layout = QHBoxLayout(banner)

        v_sz = QVBoxLayout()
        v_sz.addWidget(QLabel("TOTAL SPACE TO FREE"))
        lbl_sz = QLabel(format_bytes(self.total_size))
        lbl_sz.setStyleSheet("font-size: 20px; font-weight: 700; color: #36D399;")
        v_sz.addWidget(lbl_sz)
        b_layout.addLayout(v_sz)

        v_fl = QVBoxLayout()
        v_fl.addWidget(QLabel("TOTAL FILES"))
        lbl_fl = QLabel(f"{self.total_files:,}")
        lbl_fl.setStyleSheet("font-size: 18px; font-weight: 600; color: #E6EDF3;")
        v_fl.addWidget(lbl_fl)
        b_layout.addLayout(v_fl)

        layout.addWidget(banner)

        # Scrollable items list
        layout.addWidget(QLabel("ITEMS TO CLEAN"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(180)
        scroll.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 6px;")

        items_container = QWidget()
        items_layout = QVBoxLayout(items_container)
        items_layout.setContentsMargins(8, 8, 8, 8)
        items_layout.setSpacing(6)

        for c in self.candidates:
            item_card = QFrame()
            item_card.setStyleSheet("background: #0B0F14; border: 1px solid #1F2A38; border-radius: 4px; padding: 6px;")
            ic_layout = QHBoxLayout(item_card)
            ic_layout.setContentsMargins(6, 4, 6, 4)

            v_info = QVBoxLayout()
            lbl_name = QLabel(c.name)
            lbl_name.setStyleSheet("font-weight: 600; color: #FFFFFF;")
            v_info.addWidget(lbl_name)

            lbl_p = QLabel(str(c.path))
            lbl_p.setStyleSheet("font-family: Consolas, monospace; font-size: 10px; color: #8B98A7;")
            v_info.addWidget(lbl_p)
            ic_layout.addLayout(v_info)

            ic_layout.addStretch()

            lbl_sz_item = QLabel(format_bytes(c.size))
            lbl_sz_item.setStyleSheet("font-weight: 600; color: #4F8CFF;")
            ic_layout.addWidget(lbl_sz_item)

            items_layout.addWidget(item_card)

        items_layout.addStretch()
        scroll.setWidget(items_container)
        layout.addWidget(scroll)

        # Deletion method options
        layout.addWidget(QLabel("DELETION DESTINATION"))
        opt_box = QFrame()
        opt_box.setStyleSheet("background: #111820; border: 1px solid #26313D; border-radius: 6px; padding: 10px;")
        opt_layout = QVBoxLayout(opt_box)

        self.btn_group = QButtonGroup(self)

        self.rb_recycle = QRadioButton("Move to Windows Recycle Bin (Recommended - Easy restore)")
        self.rb_recycle.setChecked(True)
        self.btn_group.addButton(self.rb_recycle, 1)
        opt_layout.addWidget(self.rb_recycle)

        self.rb_quarantine = QRadioButton("Move to PcClean Quarantine (Isolated with metadata)")
        self.btn_group.addButton(self.rb_quarantine, 2)
        opt_layout.addWidget(self.rb_quarantine)

        self.rb_permanent = QRadioButton("Permanently Delete (Irreversible)")
        self.btn_group.addButton(self.rb_permanent, 3)
        opt_layout.addWidget(self.rb_permanent)

        layout.addWidget(opt_box)

        # Dangerous verification input if permanent deletion chosen
        self.txt_confirm_delete = QLineEdit()
        self.txt_confirm_delete.setPlaceholderText("Type DELETE here to confirm permanent deletion")
        self.txt_confirm_delete.setVisible(False)
        layout.addWidget(self.txt_confirm_delete)

        self.rb_permanent.toggled.connect(lambda checked: self.txt_confirm_delete.setVisible(checked))

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_confirm = QPushButton("Confirm & Clean")
        self.btn_confirm.setProperty("class", "danger")
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
