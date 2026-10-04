"""PcClean CLI Interface sharing the core service and safety layer."""

import argparse
import sys
from pathlib import Path

from app.constants import SafetyLevel
from database.repositories import CleanupHistoryRepository
from services.cache_service import CacheService
from services.cleanup_service import CleanupService
from services.developer_service import DeveloperService
from services.drive_service import DriveService
from services.large_file_service import LargeFileService
from services.protection_service import ProtectionService
from services.quarantine_service import QuarantineService
from services.report_service import ReportService
from services.safety_engine import SafetyEngine
from utils.size import format_bytes, parse_size


def run_cli(args_list=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(
        prog="pcclean", description="PcClean - Developer-focused Windows disk cleanup & storage analyzer"
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan storage and caches on a drive")
    p_scan.add_argument("drive_pos", nargs="?", default=None, help="Drive letter (e.g. C:)")
    p_scan.add_argument("--drive", dest="drive_flag", default="C:", help="Drive letter")

    # cleanup
    p_clean = subparsers.add_parser("cleanup", help="Run cleanup operations")
    p_clean.add_argument("--preview", action="store_true", help="Preview / Dry run cleanup candidates")
    p_clean.add_argument("--safe", action="store_true", help="Execute cleanup of verified safe caches")

    # large-files
    p_large = subparsers.add_parser("large-files", help="Search for large files")
    p_large.add_argument("drive", nargs="?", default="C:", help="Drive letter or path")
    p_large.add_argument("--min-size", default="100MB", help="Minimum file size (e.g. 100MB, 1GB)")

    # protected
    p_prot = subparsers.add_parser("protected", help="Manage protected paths")
    p_prot.add_argument("action", choices=["list", "add", "remove"], help="Protection action")
    p_prot.add_argument("path", nargs="?", default=None, help="Path to protect or unprotect")

    # projects (node_modules & build artifacts)
    p_proj = subparsers.add_parser("projects", help="Scan project workspaces for node_modules and build outputs")
    p_proj.add_argument("path", nargs="?", default=".", help="Drive or directory to scan (e.g. D:\\ or .)")
    p_proj.add_argument("--clean", action="store_true", help="Send discovered artifacts to Recycle Bin")
    p_proj.add_argument(
        "--tech",
        default="all",
        choices=["all", "node", "python", "flutter", "rust", "dotnet"],
        help="Filter by technology",
    )

    # report
    p_rep = subparsers.add_parser("report", help="Export system storage audit report")
    p_rep.add_argument("--output", "-o", default="pcclean_report.html", help="Output report file path")

    args = parser.parse_args(args_list)

    if not args.subcommand:
        parser.print_help()
        return 0

    protection_svc = ProtectionService()
    safety_eng = SafetyEngine(protection_svc)
    cache_svc = CacheService(safety_eng)
    cleanup_svc = CleanupService(safety_eng, protection_svc, CleanupHistoryRepository(), QuarantineService())

    if args.subcommand == "scan":
        drive = (args.drive_pos or args.drive_flag or "C:").upper()
        if not drive.endswith(":"):
            drive += ":"
        print("\n=======================================================")
        print(f"  PCCLEAN STORAGE & CACHE SCAN: {drive}")
        print("=======================================================\n")

        drv_info = DriveService.get_drive(drive)
        if drv_info:
            print(f"Drive:      {drv_info.display_name}")
            print(f"Total:      {format_bytes(drv_info.total_bytes)}")
            print(f"Used:       {format_bytes(drv_info.used_bytes)} ({drv_info.percent:.1f}%)")
            print(f"Free:       {format_bytes(drv_info.free_bytes)}\n")

        print("Scanning cache candidates...")
        candidates = cache_svc.scan_all_caches()
        safe_bytes = sum(
            c.size for c in candidates if c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD)
        )
        print(
            f"\nDiscovered {len(candidates)} cleanup locations ({format_bytes(sum(c.size for c in candidates))} total, {format_bytes(safe_bytes)} safe):"
        )
        for c in candidates:
            print(f"  [{c.safety_level.value:^15}] {c.name:<25} {format_bytes(c.size):>10}  |  {c.path}")

        print("\nScanning Developer Environments...")
        dev_tools = DeveloperService.scan_all()
        for t in dev_tools:
            print(f"  [DEV: {t.ecosystem:<8}] {t.name:<25} {format_bytes(t.size):>10} ({t.status}) | {t.path}")

        print("\nScan completed successfully.")
        return 0

    elif args.subcommand == "cleanup":
        candidates = cache_svc.scan_all_caches()
        safe_candidates = [c for c in candidates if c.safety_level in (SafetyLevel.SAFE, SafetyLevel.SAFE_REDOWNLOAD)]

        if args.preview or not args.safe:
            print("\n=======================================================")
            print("  PCCLEAN CLEANUP PREVIEW (DRY RUN - NO DELETIONS)")
            print("=======================================================\n")
            total_sz = sum(c.size for c in safe_candidates)
            print(f"Potential space to reclaim: {format_bytes(total_sz)} ({len(safe_candidates)} safe items):\n")
            for c in safe_candidates:
                print(f"  * {c.name} ({format_bytes(c.size)})")
                print(f"    Path:   {c.path}")
                print(f"    Safety: {c.safety_level.value}")
                print(f"    Note:   {c.explanation}\n")
            print("To execute safe cleanup, run:")
            print("  python -m pcclean cleanup --safe\n")
            return 0

        elif args.safe:
            total_sz = sum(c.size for c in safe_candidates)
            print(f"\nReady to clean {len(safe_candidates)} safe cache categories ({format_bytes(total_sz)}).")
            confirm = input("Move safe files to Windows Recycle Bin? [y/N]: ").strip().lower()
            if confirm != "y":
                print("Cleanup cancelled.")
                return 0

            print("\nExecuting cleanup...")
            res = cleanup_svc.execute_cleanup(safe_candidates, use_recycle_bin=True)
            print("\nCLEANUP RESULT:")
            print(f"  Reclaimed space: {format_bytes(res.cleaned_bytes)}")
            print(f"  Files deleted:   {res.files_deleted:,}")
            print(f"  Files skipped:   {res.files_skipped:,} (in use)")
            print(f"  Errors:          {res.errors_count}")
            return 0

    elif args.subcommand == "large-files":
        drive = args.drive.upper()
        if not drive.endswith(":"):
            drive += ":"
        min_bytes = parse_size(args.min_size) or (100 * 1024 * 1024)
        print(f"\nSearching for files >= {format_bytes(min_bytes)} on {drive}...")
        svc = LargeFileService(safety_eng)
        files = svc.find_large_files(Path(f"{drive}\\"), min_size_bytes=min_bytes)
        print(f"\nFound {len(files)} large files:")
        for f in files[:30]:
            print(f"  {format_bytes(f.size):>10}  [{f.category:<15}]  {f.path}")
        return 0

    elif args.subcommand == "protected":
        if args.action == "list":
            items = protection_svc.get_all_protected()
            print(f"\nProtected Paths ({len(items)}):")
            for p in items:
                print(f"  [PROTECTED] {p.name:<25} | {p.reason:<30} | {p.path}")
        elif args.action == "add":
            if not args.path:
                print("Error: Missing path argument to protect.")
                return 1
            p = Path(args.path)
            protection_svc.protect_path(p, p.name, "CLI Protected")
            print(f"Protected path added: {p.resolve()}")
        elif args.action == "remove":
            if not args.path:
                print("Error: Missing path argument to unprotect.")
                return 1
            protection_svc.unprotect_path(args.path)
            print(f"Protected path removed: {args.path}")
        return 0

    elif args.subcommand == "projects":
        from services.project_service import ProjectScannerService

        target_dir = Path(args.path)
        print(f"\nScanning workspace projects in {target_dir.resolve()}...")
        artifacts = ProjectScannerService.scan_workspace_artifacts(target_dir)

        if args.tech != "all":
            tech_map = {"node": "Node.js", "python": "Python", "flutter": "Flutter", "rust": "Rust", "dotnet": ".NET"}
            wanted = tech_map.get(args.tech, "")
            artifacts = [a for a in artifacts if wanted.lower() in a.tech.lower()]

        total_b = sum(a.size for a in artifacts)
        print(f"\nDiscovered {len(artifacts)} project artifacts ({format_bytes(total_b)} total):")
        print(f"  {'Project':<20} | {'Tech':<10} | {'Folder':<14} | {'Size':<10} | {'Path'}")
        print("  " + "-" * 80)
        for a in artifacts:
            print(
                f"  {a.project_name:<20} | {a.tech:<10} | {a.artifact_name:<14} | {format_bytes(a.size):<10} | {a.path}"
            )

        if args.clean and artifacts:
            print(f"\nCleaning {len(artifacts)} artifacts to Windows Recycle Bin...")
            for a in artifacts:
                success = ProjectScannerService.clean_artifact(a, use_recycle_bin=True)
                res_str = "RECYCLED" if success else "FAILED"
                print(f"  [{res_str}] {a.project_name} -> {a.artifact_name}")
            print("Project cleanup completed.")
        return 0

    elif args.subcommand == "report":
        out_p = Path(args.output)
        fmt = out_p.suffix.lstrip(".").lower() or "html"
        drives = DriveService.get_all_drives()
        candidates = cache_svc.scan_all_caches()
        protected = protection_svc.get_all_protected()
        dev_tools = DeveloperService.scan_all()
        history = CleanupHistoryRepository().get_all(50)

        data = ReportService.generate_report_data(drives, candidates, protected, dev_tools, history)
        if fmt == "html":
            ReportService.export_html(data, out_p)
        elif fmt == "json":
            ReportService.export_json(data, out_p)
        elif fmt == "csv":
            ReportService.export_csv(data, out_p)
        else:
            ReportService.export_txt(data, out_p)
        print(f"Report successfully generated at: {out_p.resolve()}")
        return 0

    return 0
