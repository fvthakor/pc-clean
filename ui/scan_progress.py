"""Developer Command Center / Log Output Panel."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CommandOutputPanel(QFrame):
    cancel_requested = Signal()
    export_report_requested = Signal(str, Path)  # format, path

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setFixedHeight(180)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header bar
        header = QHBoxLayout()
        title = QLabel("TERMINAL OUTPUT / LOG")
        title.setProperty("class", "heading2")
        title.setStyleSheet("font-size: 12px; color: #4F8CFF; font-weight: 700;")
        header.addWidget(title)

        self.lbl_status = QLabel("Idle")
        self.lbl_status.setProperty("class", "muted")
        header.addWidget(self.lbl_status)
        header.addStretch()

        self.btn_copy = QPushButton("Copy Log")
        self.btn_copy.setFixedHeight(24)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        header.addWidget(self.btn_copy)

        self.btn_export = QPushButton("Export Report")
        self.btn_export.setFixedHeight(24)
        self.btn_export.clicked.connect(self._on_export_clicked)
        header.addWidget(self.btn_export)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(24)
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        header.addWidget(self.btn_cancel)

        layout.addLayout(header)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Terminal text area
        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet(
            "background-color: #06090D; color: #A0C0E0; border: 1px solid #1E293B; "
            "font-family: Consolas, Cascadia Code, monospace; font-size: 11px; padding: 4px;"
        )
        layout.addWidget(self.txt_log)

    def log(self, message: str) -> None:
        """Append log message with timestamp."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.appendPlainText(f"[{ts}] {message}")
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    def set_progress(self, percent: int, status_text: str = "") -> None:
        self.progress_bar.setValue(percent)
        if status_text:
            self.lbl_status.setText(status_text)

    def set_busy(self, is_busy: bool, status_text: str = "") -> None:
        self.btn_cancel.setEnabled(is_busy)
        if is_busy:
            self.progress_bar.setRange(0, 0)  # indeterminate
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
        if status_text:
            self.lbl_status.setText(status_text)

    def clear_log(self) -> None:
        self.txt_log.clear()

    def _on_copy_clicked(self) -> None:
        QApplication.clipboard().setText(self.txt_log.toPlainText())

    def _on_export_clicked(self) -> None:
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Audit Report",
            "PcClean_Report.html",
            "HTML Report (*.html);;JSON Data (*.json);;CSV Summary (*.csv);;Text Log (*.txt)",
        )
        if file_path:
            p = Path(file_path)
            fmt = p.suffix.lstrip(".").lower()
            self.export_report_requested.emit(fmt, p)
