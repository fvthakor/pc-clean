"""TreeSize-style Storage Analyzer View."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.file_item import FolderItem
from utils.formatting import format_timestamp
from utils.size import format_bytes


class StorageView(QWidget):
    item_selected = Signal(object)  # Emits selected FolderItem
    scan_drive_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.root_item: FolderItem | None = None
        self.total_drive_size: int = 1
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title bar & Controls
        top_bar = QHBoxLayout()
        v_title = QVBoxLayout()
        title = QLabel("STORAGE ANALYZER")
        title.setProperty("class", "heading1")
        sub = QLabel("TreeSize-style hierarchical directory tree analysis")
        sub.setProperty("class", "muted")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        top_bar.addLayout(v_title)
        top_bar.addStretch()

        # Search filter
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter folders...")
        self.txt_search.setFixedWidth(200)
        self.txt_search.textChanged.connect(self._filter_tree)
        top_bar.addWidget(self.txt_search)

        # Min size combo
        self.combo_min_size = QComboBox()
        self.combo_min_size.addItems(["All Sizes", "> 100 MB", "> 500 MB", "> 1 GB", "> 5 GB"])
        self.combo_min_size.currentIndexChanged.connect(self._filter_tree)
        top_bar.addWidget(self.combo_min_size)

        self.btn_expand_all = QPushButton("Expand")
        self.btn_expand_all.clicked.connect(lambda: self.tree.expandAll())
        top_bar.addWidget(self.btn_expand_all)

        self.btn_collapse_all = QPushButton("Collapse")
        self.btn_collapse_all.clicked.connect(lambda: self.tree.collapseAll())
        top_bar.addWidget(self.btn_collapse_all)

        layout.addLayout(top_bar)

        # Tree View
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Size", "Size %", "Files", "Folders", "Modified", "Safety", "Path"])
        self.tree.setSortingEnabled(True)
        self.tree.setAnimated(True)
        self.tree.setAlternatingRowColors(True)

        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.resizeSection(0, 240)
        header.resizeSection(1, 90)
        header.resizeSection(2, 70)
        header.resizeSection(3, 70)
        header.resizeSection(4, 70)
        header.resizeSection(5, 130)
        header.resizeSection(6, 90)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def populate_tree(self, root: FolderItem, total_drive_size: int = 0) -> None:
        """Populate tree widget with hierarchical FolderItem data."""
        self.root_item = root
        self.total_drive_size = total_drive_size if total_drive_size > 0 else (root.size or 1)

        self.tree.blockSignals(True)
        self.tree.clear()

        root_node = self._create_tree_node(root)
        self.tree.addTopLevelItem(root_node)
        root_node.setExpanded(True)

        # Expand first level children
        for i in range(root_node.childCount()):
            root_node.child(i).setExpanded(True)

        self.tree.blockSignals(False)
        self.tree.sortItems(1, Qt.DescendingOrder)

    def _create_tree_node(self, item: FolderItem) -> QTreeWidgetItem:
        pct = (item.size / self.total_drive_size) * 100 if self.total_drive_size > 0 else 0
        safety_str = item.safety_result.level.value if item.safety_result else "REVIEW"

        node = QTreeWidgetItem(
            [
                item.name,
                format_bytes(item.size),
                f"{pct:.1f}%",
                f"{item.files_count:,}",
                f"{item.subfolders_count:,}",
                format_timestamp(item.modified),
                safety_str,
                str(item.path),
            ]
        )
        # Store item reference
        node.setData(0, Qt.UserRole, item)

        # Align numeric columns right
        node.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
        node.setTextAlignment(2, Qt.AlignRight | Qt.AlignVCenter)
        node.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
        node.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)

        # Style safety text
        if safety_str in ("SAFE", "SAFE_REDOWNLOAD"):
            node.setForeground(6, Qt.green)
        elif safety_str == "IMPORTANT":
            node.setForeground(6, Qt.cyan)
        elif safety_str in ("DANGEROUS", "BLOCKED"):
            node.setForeground(6, Qt.red)

        for child in item.children:
            child_node = self._create_tree_node(child)
            node.addChild(child_node)

        return node

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        folder_item = item.data(0, Qt.UserRole)
        if folder_item:
            self.item_selected.emit(folder_item)

    def _filter_tree(self) -> None:
        search = self.txt_search.text().lower()
        min_idx = self.combo_min_size.currentIndex()
        min_bytes = [0, 100 * 1024**2, 500 * 1024**2, 1024**3, 5 * 1024**3][min_idx]

        def check_node(node: QTreeWidgetItem) -> bool:
            f_item = node.data(0, Qt.UserRole)
            matches = True
            if f_item:
                if search and search not in f_item.name.lower() and search not in str(f_item.path).lower():
                    matches = False
                if f_item.size < min_bytes:
                    matches = False

            child_matches = False
            for i in range(node.childCount()):
                if check_node(node.child(i)):
                    child_matches = True

            visible = matches or child_matches
            node.setHidden(not visible)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            check_node(self.tree.topLevelItem(i))
