"""PcClean Main Window: Master UI orchestrator, async workers, event routing."""

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.config import AppConfig
from app.constants import SafetyLevel
from database.repositories import CleanupHistoryRepository
from models.application import AppLeftoverCandidate, InstalledApp
from models.cleanup_item import CleanupCandidate
from models.developer_tool import DeveloperTool, DevPackage
from models.drive import DriveInfo
from models.file_item import FileItem, FolderItem
from models.scan_result import ScanSummary
from services.application_service import ApplicationService
from services.cache_service import CacheService
from services.cleanup_service import CleanupService
from services.developer_service import DeveloperService
from services.drive_service import DriveService
from services.duplicate_service import DuplicateService
from services.large_file_service import LargeFileService
from services.protection_service import ProtectionService
from services.quarantine_service import QuarantineService
from services.report_service import ReportService
from services.safety_engine import SafetyEngine
from services.storage_scanner import StorageScanner
from services.uninstall_detector import UninstallDetector
from ui.applications_view import ApplicationsView
from ui.cleanup_view import CleanupView
from ui.dashboard_view import DashboardView
from ui.details_panel import DetailsPanel
from ui.developer_view import DeveloperView
from ui.dialogs.cleanup_preview import CleanupPreviewDialog
from ui.duplicate_view import DuplicateView
from ui.history_view import HistoryView
from ui.large_files_view import LargeFilesView
from ui.protected_view import ProtectedView
from ui.scan_progress import CommandOutputPanel
from ui.settings_view import SettingsView
from ui.sidebar import Sidebar
from ui.storage_view import StorageView
from utils.size import format_bytes

logger = logging.getLogger("PcClean.MainWindow")


class WorkerSignals(QObject):
    progress = Signal(str, int)  # status_msg, percent
    log = Signal(str)
    finished = Signal(object)  # result payload
    error = Signal(str)


class GenericWorker(QRunnable):
    def __init__(self, task_fn, *args, **kwargs):
        super().__init__()
        self.task_fn = task_fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.is_cancelled_flag = False

    def cancel(self):
        self.is_cancelled_flag = True

    def is_cancelled(self) -> bool:
        return self.is_cancelled_flag

    def run(self):
        try:
            res = self.task_fn(*self.args, is_cancelled=self.is_cancelled, progress_signal=self.signals, **self.kwargs)
            self.signals.finished.emit(res)
        except Exception as e:
            logger.error(f"Worker exception: {e}", exc_info=True)
            self.signals.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PcClean - Developer Storage & Safe Cleanup Suite")
        self.resize(1300, 840)
        self.setMinimumSize(1000, 650)

        # Services & State
        self.config = AppConfig.load()
        self.thread_pool = QThreadPool.globalInstance()
        self.current_worker: GenericWorker | None = None
        self._active_workers: set[GenericWorker] = set()

        self.protection_service = ProtectionService()
        self.safety_engine = SafetyEngine(self.protection_service)
        self.history_repo = CleanupHistoryRepository()
        self.quarantine_service = QuarantineService()
        self.cleanup_service = CleanupService(
            self.safety_engine, self.protection_service, self.history_repo, self.quarantine_service
        )

        self.all_drives: list[DriveInfo] = []
        self.active_drive_letter = self.config.default_drive or "C:"
        self.latest_candidates: list[CleanupCandidate] = []
        self.latest_dev_tools: list[DeveloperTool] = []
        self.latest_summary: ScanSummary | None = None

        self._init_ui()
        self._load_stylesheet()
        self._initial_refresh()

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.sidebar.drive_changed.connect(self._on_drive_changed)
        root_layout.addWidget(self.sidebar)

        # 2. Center Content Area (Split into Pages + Bottom Command Panel)
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Stacked Pages
        self.stack = QStackedWidget()

        self.view_dashboard = DashboardView()
        self.view_dashboard.scan_requested.connect(self.start_fast_scan)
        self.view_dashboard.quick_clean_requested.connect(self.start_quick_clean)
        self.view_dashboard.open_storage_requested.connect(
            lambda: self.sidebar.set_active_page(1) or self._on_page_changed(1)
        )
        self.view_dashboard.scan_all_drives_requested.connect(self.start_scan_all_drives)
        self.stack.addWidget(self.view_dashboard)  # 0

        self.view_storage = StorageView()
        self.view_storage.item_selected.connect(self._on_folder_inspected)
        self.stack.addWidget(self.view_storage)  # 1

        self.view_cleanup = CleanupView()
        self.view_cleanup.item_selected.connect(self._on_candidate_inspected)
        self.view_cleanup.clean_single_requested.connect(self._clean_single_candidate)
        self.view_cleanup.clean_batch_requested.connect(self._clean_candidate_batch)
        self.view_cleanup.preview_batch_requested.connect(self._preview_candidate_batch)
        self.stack.addWidget(self.view_cleanup)  # 2

        self.view_developer = DeveloperView()
        self.view_developer.item_selected.connect(self._on_dev_tool_inspected)
        self.view_developer.refresh_requested.connect(self.scan_developer_tools)
        self.view_developer.clean_broken_package_requested.connect(self._clean_broken_package)
        self.view_developer.scan_projects_requested.connect(self.scan_workspace_projects)
        self.view_developer.clean_artifacts_requested.connect(self.clean_workspace_artifacts)
        self.stack.addWidget(self.view_developer)  # 3

        self.view_applications = ApplicationsView()
        self.view_applications.item_selected.connect(self._on_generic_item_inspected)
        self.view_applications.uninstall_app_requested.connect(self._uninstall_application)
        self.view_applications.clean_leftover_requested.connect(self._clean_app_leftover)
        self.view_applications.refresh_requested.connect(self.scan_applications)
        self.stack.addWidget(self.view_applications)  # 4

        self.view_large_files = LargeFilesView()
        self.view_large_files.item_selected.connect(self._on_generic_item_inspected)
        self.view_large_files.scan_large_files_requested.connect(self.scan_large_files)
        self.view_large_files.delete_large_file_requested.connect(self._delete_large_file)
        self.stack.addWidget(self.view_large_files)  # 5

        self.view_duplicates = DuplicateView()
        self.view_duplicates.item_selected.connect(self._on_generic_item_inspected)
        self.view_duplicates.scan_duplicates_requested.connect(self.scan_duplicates)
        self.stack.addWidget(self.view_duplicates)  # 6

        self.view_protected = ProtectedView()
        self.view_protected.add_protection_requested.connect(self._add_protection)
        self.view_protected.unprotect_requested.connect(self._unprotect_path)
        self.view_protected.refresh_requested.connect(self._refresh_protected)
        self.stack.addWidget(self.view_protected)  # 7

        self.view_history = HistoryView()
        self.view_history.clear_history_requested.connect(self._clear_history)
        self.view_history.refresh_requested.connect(self._refresh_history)
        self.stack.addWidget(self.view_history)  # 8

        self.view_settings = SettingsView(self.config)
        self.view_settings.settings_saved.connect(self._on_settings_saved)
        self.stack.addWidget(self.view_settings)  # 9

        center_layout.addWidget(self.stack, 1)

        # Bottom Command Output / Terminal Panel
        self.cmd_panel = CommandOutputPanel()
        self.cmd_panel.cancel_requested.connect(self._cancel_active_worker)
        self.cmd_panel.export_report_requested.connect(self._export_report)
        center_layout.addWidget(self.cmd_panel)

        root_layout.addWidget(center_widget, 1)

        # 3. Right Details Inspector Panel
        self.details_panel = DetailsPanel(self)
        self.details_panel.clean_requested.connect(self._on_details_clean)
        self.details_panel.protect_requested.connect(self._on_details_protect)
        self.details_panel.preview_requested.connect(self._on_details_preview)
        root_layout.addWidget(self.details_panel)

    def _load_stylesheet(self) -> None:
        qss_path = Path(__file__).parent.parent / "resources" / "styles" / "theme.qss"
        if qss_path.exists():
            try:
                with open(qss_path, encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                logger.error(f"Error loading stylesheet: {e}")

    def _initial_refresh(self) -> None:
        self.refresh_drives()
        self._refresh_protected()
        self._refresh_history()
        self.start_fast_scan(self.active_drive_letter)
        self.scan_developer_tools()
        self.scan_applications()

    def refresh_drives(self) -> None:
        self.all_drives = DriveService.get_all_drives()
        self.sidebar.populate_drives(self.all_drives, self.active_drive_letter)
        self.view_dashboard.populate_multi_drives(self.all_drives)
        drv = DriveService.get_drive(self.active_drive_letter)
        if drv:
            self.view_dashboard.update_drive_hero(drv)

    # --- Navigation and Drive Selection ---
    def _on_page_changed(self, idx: int) -> None:
        self.stack.setCurrentIndex(idx)
        if idx == 7:
            self._refresh_protected()
        elif idx == 8:
            self._refresh_history()

    def _on_drive_changed(self, letter: str) -> None:
        self.active_drive_letter = letter
        drv = DriveService.get_drive(letter)
        if drv:
            self.view_dashboard.update_drive_hero(drv)
            self.view_developer.txt_project_dir.setText(f"{letter}\\")
            self.cmd_panel.log(f"Active drive switched to {letter} ({drv.name})")

    def _start_worker(self, worker: GenericWorker) -> None:
        """Start worker in threadpool while retaining reference to prevent Python GC."""
        self.current_worker = worker
        self._active_workers.add(worker)

        def _cleanup(*_):
            self._active_workers.discard(worker)
            if self.current_worker is worker:
                self.current_worker = None

        worker.signals.finished.connect(_cleanup)
        worker.signals.error.connect(_cleanup)
        self.thread_pool.start(worker)

    # --- Scanning Pipelines ---
    def start_fast_scan(self, drive_letter: str) -> None:
        self.cmd_panel.set_busy(True, f"Scanning caches & storage on {drive_letter}...")
        self.cmd_panel.log(f"Initiating fast system & cache scan on {drive_letter}...")

        def _task(is_cancelled, progress_signal):
            cache_svc = CacheService(self.safety_engine)
            candidates = cache_svc.scan_all_caches(
                is_cancelled=is_cancelled, progress_callback=lambda msg: progress_signal.log.emit(msg)
            )

            # Build drive hierarchy tree
            root_p = Path(f"{drive_letter}\\")
            scanner = StorageScanner(self.safety_engine)
            tree_root = scanner.scan_directory_tree(
                root_p,
                max_depth=1,
                is_cancelled=is_cancelled,
                progress_callback=lambda p, s: progress_signal.log.emit(f"Inspecting {p}..."),
            )

            drv = DriveService.get_drive(drive_letter)
            tot_sp = drv.total_bytes if drv else 1
            used_sp = drv.used_bytes if drv else 0
            free_sp = drv.free_bytes if drv else 0

            safe_bytes = sum(
                c.size for c in candidates if c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD)
            )
            review_bytes = sum(c.size for c in candidates if c.safety_level == SafetyLevel.REVIEW)

            summary = ScanSummary(
                drive_letter=drive_letter,
                total_space=tot_sp,
                used_space=used_sp,
                free_space=free_sp,
                potential_cleanup_bytes=sum(c.size for c in candidates),
                safe_cleanup_bytes=safe_bytes,
                review_required_bytes=review_bytes,
                protected_bytes=len(self.protection_service.get_all_protected()),
                candidates=candidates,
            )
            return summary, tree_root

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.finished.connect(self._on_fast_scan_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_fast_scan_finished(self, result) -> None:
        summary, tree_root = result
        self.latest_summary = summary
        self.latest_candidates = summary.candidates

        self.view_dashboard.update_telemetry(summary)
        self.view_storage.populate_tree(tree_root, summary.total_space)
        self.view_cleanup.populate_candidates(summary.candidates)

        self.cmd_panel.set_busy(False, "Scan completed")
        self.cmd_panel.log(
            f"Scan finished. Found {len(summary.candidates)} cleanup candidates ({format_bytes(summary.potential_cleanup_bytes)})."
        )

    def start_scan_all_drives(self) -> None:
        self.cmd_panel.log("Initiating scan across all detected Windows drives...")
        for d in self.all_drives:
            self.cmd_panel.log(f"Drive {d.letter}: {format_bytes(d.used_bytes)} used of {format_bytes(d.total_bytes)}")
        self.start_fast_scan(self.active_drive_letter)

    def scan_developer_tools(self) -> None:
        self.cmd_panel.log("Scanning developer ecosystems (Node, Python, Android, Flutter, Docker, VS Code, AI)...")

        def _task(is_cancelled, progress_signal):
            return DeveloperService.scan_all()

        worker = GenericWorker(_task)
        worker.signals.finished.connect(self._on_dev_scan_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_dev_scan_finished(self, tools: list[DeveloperTool]) -> None:
        self.latest_dev_tools = tools
        self.view_developer.populate_tools(tools)
        self.cmd_panel.log(f"Developer environments scanned. Discovered {len(tools)} environments & tools.")

    def scan_workspace_projects(self, dir_path: str) -> None:
        self.cmd_panel.set_busy(True, f"Scanning project artifacts (node_modules, builds) in {dir_path}...")
        self.cmd_panel.log(f"Searching for project workspaces in {dir_path}...")

        def _task(is_cancelled, progress_signal):
            from services.project_service import ProjectScannerService

            return ProjectScannerService.scan_workspace_artifacts(
                Path(dir_path),
                max_depth=5,
                is_cancelled=is_cancelled,
                progress_callback=lambda msg: progress_signal.log.emit(msg),
            )

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.finished.connect(self._on_projects_scan_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_projects_scan_finished(self, artifacts) -> None:
        self.cmd_panel.set_busy(False, f"Project scan completed ({len(artifacts)} artifacts)")
        total_b = sum(a.size for a in artifacts)
        self.cmd_panel.log(f"Discovered {len(artifacts)} project artifacts ({format_bytes(total_b)} total).")
        self.view_developer.populate_project_artifacts(artifacts)

    def clean_workspace_artifacts(self, artifacts) -> None:
        if not artifacts:
            return
        total = len(artifacts)
        self.cmd_panel.set_busy(True, f"Cleaning {total} project artifacts...")
        self.cmd_panel.log(f"Initiating cleanup for {total} project artifacts to Windows Recycle Bin...")

        def _task(is_cancelled, progress_signal):
            from services.project_service import ProjectScannerService

            cleaned_count = 0
            cleaned_bytes = 0
            cleaned_arts = []
            for i, art in enumerate(artifacts, 1):
                if is_cancelled and is_cancelled():
                    progress_signal.log.emit("⚠️ Project cleanup cancelled by user.")
                    break
                pct = int((i / total) * 100)
                progress_signal.progress.emit(f"Cleaning ({i}/{total}): {art.project_name}/{art.artifact_name}", pct)
                progress_signal.log.emit(
                    f"[{i}/{total}] Cleaning {art.project_name}/{art.artifact_name} ({format_bytes(art.size)})..."
                )
                if ProjectScannerService.clean_artifact(art, use_recycle_bin=True):
                    cleaned_count += 1
                    cleaned_bytes += art.size
                    cleaned_arts.append(art)
            return cleaned_count, cleaned_bytes, cleaned_arts

        def _on_done(res):
            cnt, sz, cleaned_arts = res
            self.cmd_panel.set_busy(False, f"Project cleanup complete ({cnt}/{total})")
            self.cmd_panel.set_progress(100, f"Completed: {cnt}/{total}")
            self.cmd_panel.log(
                f"🎉 Successfully cleaned {cnt} artifacts ({format_bytes(sz)} reclaimed) to Recycle Bin."
            )
            self.view_developer.remove_cleaned_artifacts(cleaned_arts)
            self.refresh_drives()
            QMessageBox.information(
                self,
                "Project Cleanup Complete",
                f"Successfully cleaned {cnt} of {total} project artifact(s)!\n\n"
                f"Reclaimed Disk Space: {format_bytes(sz)}\n"
                f"Destination: Windows Recycle Bin\n\n"
                "Artifacts can be restored from the Recycle Bin if needed, or reinstalled with your build tools.",
            )

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.progress.connect(self.cmd_panel.on_progress)
        worker.signals.finished.connect(_on_done)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def scan_applications(self) -> None:
        def _task(is_cancelled, progress_signal):
            apps = ApplicationService.get_installed_applications()
            leftovers = UninstallDetector.scan_leftovers()
            return apps, leftovers

        worker = GenericWorker(_task)
        worker.signals.finished.connect(self._on_apps_scan_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_apps_scan_finished(self, res) -> None:
        apps, leftovers = res
        self.view_applications.populate_apps(apps)
        self.view_applications.populate_leftovers(leftovers)
        if self.latest_summary:
            lo_bytes = sum(item.size for item in leftovers)
            self.latest_summary.leftovers_bytes = lo_bytes
            self.view_dashboard.update_telemetry(self.latest_summary)
        self.cmd_panel.log(
            f"Applications indexed: {len(apps)} installed, {len(leftovers)} possible leftovers detected."
        )

    def scan_large_files(self, drive_letter: str, min_bytes: int) -> None:
        self.cmd_panel.set_busy(True, f"Searching for files > {format_bytes(min_bytes)}...")
        self.cmd_panel.log(f"Scanning {drive_letter} for large files...")

        def _task(is_cancelled, progress_signal):
            svc = LargeFileService(self.safety_engine)
            return svc.find_large_files(
                Path(f"{drive_letter}\\"),
                min_size_bytes=min_bytes,
                is_cancelled=is_cancelled,
                progress_callback=lambda p, count: progress_signal.log.emit(f"Found {count} large files..."),
            )

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.finished.connect(self._on_large_files_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_large_files_finished(self, files: list[FileItem]) -> None:
        self.view_large_files.populate_files(files)
        self.cmd_panel.set_busy(False, f"Found {len(files)} large files")
        self.cmd_panel.log(f"Large file scan complete. {len(files)} files discovered.")

    def scan_duplicates(self, drive_letter: str) -> None:
        self.cmd_panel.set_busy(True, f"Running two-stage duplicate scan on {drive_letter}...")
        self.cmd_panel.log(f"Stage 1: Grouping by size on {drive_letter}...")

        def _task(is_cancelled, progress_signal):
            svc = DuplicateService(self.safety_engine)
            # Scan user profile folder or drive root
            target = Path(os.environ.get("USERPROFILE", f"{drive_letter}\\"))
            return svc.find_duplicates(
                target,
                min_size_bytes=5 * 1024 * 1024,  # 5MB threshold for responsive scan
                is_cancelled=is_cancelled,
                progress_callback=lambda msg: progress_signal.log.emit(msg),
            )

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.finished.connect(self._on_duplicates_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_duplicates_finished(self, groups) -> None:
        self.view_duplicates.populate_duplicates(groups)
        self.cmd_panel.set_busy(False, "Duplicate scan completed")
        self.cmd_panel.log(f"Duplicate scan finished. Found {len(groups)} sets of duplicate files.")

    # --- Inspection & Details Panel ---
    def _on_folder_inspected(self, folder_item: FolderItem) -> None:
        safety = self.safety_engine.evaluate_path(folder_item.path)
        self.details_panel.set_folder_item(folder_item, safety)

    def _on_candidate_inspected(self, candidate: CleanupCandidate) -> None:
        self.details_panel.set_cleanup_candidate(candidate)

    def _on_dev_tool_inspected(self, tool: DeveloperTool) -> None:
        safety = (
            self.safety_engine.evaluate_path(tool.path) if isinstance(tool.path, Path) and tool.path.exists() else None
        )
        item = FolderItem(
            path=tool.path if isinstance(tool.path, Path) else Path("."),
            name=tool.name,
            size=tool.size,
            category=tool.ecosystem,
            safety_result=safety,
        )
        self.details_panel.set_folder_item(item, safety)

    def _on_generic_item_inspected(self, item) -> None:
        p = getattr(item, "path", None)
        if p and isinstance(p, Path) and p.exists():
            safety = self.safety_engine.evaluate_path(p)
            f_item = FolderItem(path=p, name=p.name, size=getattr(item, "size", 0), safety_result=safety)
            self.details_panel.set_folder_item(f_item, safety)

    # --- Cleanup Actions & Safety Pipeline ---
    def _clean_single_candidate(self, candidate: CleanupCandidate) -> None:
        self._clean_candidate_batch([candidate])

    def _preview_candidate_batch(self, candidates: list[CleanupCandidate]) -> None:
        dlg = CleanupPreviewDialog(candidates, self)
        dlg.exec()

    def _clean_candidate_batch(self, candidates: list[CleanupCandidate]) -> None:
        # 1. Preview Dialog
        dlg = CleanupPreviewDialog(candidates, self)
        if dlg.exec() != CleanupPreviewDialog.Accepted:
            self.cmd_panel.log("Cleanup cancelled by user.")
            return

        use_rb, use_q, is_perm = dlg.get_options()

        # 2. Check if admin required
        requires_admin = any(self.safety_engine.evaluate_path(c.path).requires_admin for c in candidates)
        if requires_admin and not sys.platform == "win32":
            pass

        self.cmd_panel.set_busy(True, f"Cleaning {len(candidates)} items...")
        self.cmd_panel.log(
            f"Executing cleanup across {len(candidates)} items (RecycleBin={use_rb}, Quarantine={use_q})..."
        )

        def _task(is_cancelled, progress_signal):
            return self.cleanup_service.execute_cleanup(
                candidates,
                use_recycle_bin=use_rb,
                use_quarantine=use_q,
                is_cancelled=is_cancelled,
                progress_callback=lambda name, idx, tot: progress_signal.log.emit(f"Cleaning ({idx}/{tot}): {name}"),
            )

        worker = GenericWorker(_task)
        worker.signals.log.connect(self.cmd_panel.log)
        worker.signals.finished.connect(self._on_cleanup_finished)
        worker.signals.error.connect(self._on_worker_error)
        self._start_worker(worker)

    def _on_cleanup_finished(self, result) -> None:
        self.cmd_panel.set_busy(False, "Cleanup finished")
        self.cmd_panel.log(
            f"CLEANUP COMPLETED: Freed {format_bytes(result.cleaned_bytes)} ({result.files_deleted} files deleted, "
            f"{result.files_skipped} skipped, {result.errors_count} errors)."
        )
        if result.skipped_reasons:
            for reason in result.skipped_reasons[:5]:
                self.cmd_panel.log(f"  Note: {reason}")

        QMessageBox.information(
            self,
            "Cleanup Complete",
            f"Successfully reclaimed {format_bytes(result.cleaned_bytes)} of disk space.\n\n"
            f"Deleted files: {result.files_deleted:,}\n"
            f"Skipped in-use files: {result.files_skipped:,}\n"
            f"Errors: {result.errors_count}",
        )

        self._refresh_history()
        self.refresh_drives()
        self.start_fast_scan(self.active_drive_letter)

    def start_quick_clean(self) -> None:
        """Run Quick Clean on safe candidates only."""
        safe_candidates = [
            c
            for c in self.latest_candidates
            if c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD) and not c.is_protected
        ]
        if not safe_candidates:
            QMessageBox.information(self, "Quick Clean", "No safe cleanup candidates currently available.")
            return

        self._clean_candidate_batch(safe_candidates)

    def _clean_broken_package(self, pkg: DevPackage) -> None:
        """Remove broken pip artifact (~package)."""
        reply = QMessageBox.question(
            self,
            "Remove Broken Artifact",
            f"Are you sure you want to remove the broken leftover package artifact?\n\nPath: {pkg.path}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            candidate = CleanupCandidate(
                id=f"broken_{pkg.name}",
                name=f"Broken Leftover {pkg.name}",
                description="Broken pip installation leftover",
                path=pkg.path,
                category="Python & pip",
                size=pkg.size,
                files_count=1,
                safety_level=SafetyLevel.REVIEW,
                reason="Broken pip remnant",
            )
            self._clean_candidate_batch([candidate])

    def _uninstall_application(self, app: InstalledApp) -> None:
        reply = QMessageBox.question(
            self,
            "Launch Official Uninstaller",
            f"PcClean will launch the official Windows uninstaller for:\n\n{app.name}\n\nProceed?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            success = ApplicationService.launch_uninstaller(app)
            if success:
                self.cmd_panel.log(f"Launched uninstaller for {app.name}.")
            else:
                QMessageBox.warning(self, "Uninstall Error", f"Could not launch uninstaller for {app.name}.")

    def _clean_app_leftover(self, lo: AppLeftoverCandidate) -> None:
        candidate = CleanupCandidate(
            id=f"leftover_{lo.app_name}",
            name=f"Leftover: {lo.app_name}",
            description="Uninstalled application residual folder",
            path=lo.path,
            category="App Leftovers",
            size=lo.size,
            files_count=lo.files_count,
            safety_level=SafetyLevel.REVIEW,
            reason=lo.reason,
        )
        self._clean_candidate_batch([candidate])

    def _delete_large_file(self, file_item: FileItem) -> None:
        candidate = CleanupCandidate(
            id=f"large_{file_item.name}",
            name=file_item.name,
            description="Large file cleanup",
            path=file_item.path,
            category="Large Files",
            size=file_item.size,
            files_count=1,
            safety_level=SafetyLevel.REVIEW,
            reason="Individual large file selected by user",
        )
        self._clean_candidate_batch([candidate])

    # --- Details Panel Callbacks ---
    def _on_details_clean(self, item) -> None:
        if isinstance(item, CleanupCandidate):
            self._clean_candidate_batch([item])
        elif isinstance(item, FolderItem):
            candidate = CleanupCandidate(
                id=f"folder_{item.name}",
                name=item.name,
                description="User selected folder",
                path=item.path,
                category="Other",
                size=item.size,
                files_count=item.files_count,
                safety_level=item.safety_result.level if item.safety_result else SafetyLevel.REVIEW,
                reason=item.safety_result.reason if item.safety_result else "Manual cleanup",
            )
            self._clean_candidate_batch([candidate])

    def _on_details_protect(self, path: Path) -> None:
        self._add_protection(str(path.resolve()), path.name, "Protected via Details Inspector")

    def _on_details_preview(self, item) -> None:
        if isinstance(item, CleanupCandidate):
            self._preview_candidate_batch([item])

    # --- Protection Management ---
    def _add_protection(self, path: str, name: str, reason: str) -> None:
        p = Path(path)
        if self.protection_service.protect_path(p, name, reason):
            self.cmd_panel.log(f"Protected path added: {path}")
            self._refresh_protected()
            QMessageBox.information(self, "Path Protected", f"'{name}' is now protected against all cleanup actions.")

    def _unprotect_path(self, path_or_id: str) -> None:
        self.protection_service.unprotect_path(path_or_id)
        self.cmd_panel.log(f"Removed protection for: {path_or_id}")
        self._refresh_protected()

    def _refresh_protected(self) -> None:
        items = self.protection_service.get_all_protected()
        self.view_protected.populate_protected(items)

    def _refresh_history(self) -> None:
        entries = self.history_repo.get_all(limit=100)
        self.view_history.populate_history(entries)

    def _clear_history(self) -> None:
        self.history_repo.clear()
        self._refresh_history()
        self.cmd_panel.log("Cleanup history cleared.")

    def _cancel_active_worker(self) -> None:
        if self.current_worker:
            self.current_worker.cancel()
            self.cmd_panel.log("Cancellation signal sent to active background worker.")

    def _on_worker_error(self, err_msg: str) -> None:
        self.cmd_panel.set_busy(False, "Error encountered")
        self.cmd_panel.log(f"ERROR: {err_msg}")

    def _on_settings_saved(self, cfg: AppConfig) -> None:
        self.config = cfg
        self.cmd_panel.log("Settings successfully updated and saved.")

    def _export_report(self, fmt: str, output_path: Path) -> None:
        data = ReportService.generate_report_data(
            drives=self.all_drives,
            cleanup_candidates=self.latest_candidates,
            protected_paths=self.protection_service.get_all_protected(),
            developer_tools=self.latest_dev_tools,
            cleanup_history=self.history_repo.get_all(50),
        )
        try:
            if fmt == "html":
                ReportService.export_html(data, output_path)
            elif fmt == "json":
                ReportService.export_json(data, output_path)
            elif fmt == "csv":
                ReportService.export_csv(data, output_path)
            else:
                ReportService.export_txt(data, output_path)
            self.cmd_panel.log(f"Audit report exported to: {output_path}")
            QMessageBox.information(self, "Report Exported", f"Report successfully saved to:\n{output_path}")
        except Exception as e:
            self.cmd_panel.log(f"Export error: {e}")
            QMessageBox.critical(self, "Export Failed", str(e))
