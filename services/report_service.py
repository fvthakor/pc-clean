"""Export Report Service (JSON, CSV, TXT, HTML)."""

import csv
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.size import format_bytes


class ReportService:
    @classmethod
    def generate_report_data(
        cls,
        drives: list[Any],
        cleanup_candidates: list[Any],
        protected_paths: list[Any],
        developer_tools: list[Any],
        cleanup_history: list[dict],
    ) -> dict[str, Any]:
        """Aggregate system and scan data into a unified structure."""
        return {
            "generated_at": datetime.now().isoformat(),
            "system_info": {
                "computer_name": platform.node(),
                "os": platform.platform(),
                "windows_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
            },
            "drives": [
                {
                    "letter": d.letter,
                    "name": d.name,
                    "filesystem": d.fstype,
                    "type": str(d.drive_type.value if hasattr(d.drive_type, "value") else d.drive_type),
                    "total": format_bytes(d.total_bytes),
                    "used": format_bytes(d.used_bytes),
                    "free": format_bytes(d.free_bytes),
                    "percent": f"{d.percent:.1f}%",
                }
                for d in drives
            ],
            "cleanup_candidates": [
                {
                    "name": c.name,
                    "path": str(c.path),
                    "category": str(c.category.value if hasattr(c.category, "value") else c.category),
                    "size": format_bytes(c.size),
                    "files": c.files_count,
                    "safety": str(c.safety_level.value if hasattr(c.safety_level, "value") else c.safety_level),
                    "reason": c.reason,
                    "explanation": c.explanation,
                }
                for c in cleanup_candidates
            ],
            "protected_paths": [
                {
                    "name": p.name,
                    "path": p.path,
                    "reason": p.reason,
                }
                for p in protected_paths
            ],
            "developer_environments": [
                {
                    "ecosystem": t.ecosystem,
                    "name": t.name,
                    "path": str(t.path),
                    "size": format_bytes(t.size),
                    "status": t.status,
                    "safety": str(t.safety_level.value if hasattr(t.safety_level, "value") else t.safety_level),
                    "explanation": t.explanation,
                }
                for t in developer_tools
            ],
            "cleanup_history": cleanup_history[:50],
        }

    @classmethod
    def export_json(cls, data: dict[str, Any], output_path: Path) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def export_txt(cls, data: dict[str, Any], output_path: Path) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("                      WINCLEAN AUDIT REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Generated: {data['generated_at']}\n")
            f.write(f"Computer:  {data['system_info']['computer_name']}\n")
            f.write(f"OS:        {data['system_info']['os']} ({data['system_info']['architecture']})\n\n")

            f.write("-" * 70 + "\nDRIVES\n" + "-" * 70 + "\n")
            for d in data["drives"]:
                f.write(
                    f"  {d['letter']} [{d['name']}] ({d['type']}): Used {d['used']} / {d['total']} ({d['percent']})\n"
                )

            f.write("\n" + "-" * 70 + "\nCLEANUP CANDIDATES\n" + "-" * 70 + "\n")
            for c in data["cleanup_candidates"]:
                f.write(f"  [{c['safety']}] {c['name']} ({c['size']})\n")
                f.write(f"    Path: {c['path']}\n")
                f.write(f"    Note: {c['explanation']}\n\n")

            f.write("\n" + "-" * 70 + "\nDEVELOPER ENVIRONMENTS\n" + "-" * 70 + "\n")
            for t in data["developer_environments"]:
                f.write(f"  {t['ecosystem']} | {t['name']} ({t['size']}) - Status: {t['status']}\n")
                f.write(f"    Path: {t['path']}\n")

    @classmethod
    def export_csv(cls, data: dict[str, Any], output_path: Path) -> None:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Name", "Path", "Size", "Safety", "Files", "Reason"])
            for c in data["cleanup_candidates"]:
                writer.writerow([c["category"], c["name"], c["path"], c["size"], c["safety"], c["files"], c["reason"]])

    @classmethod
    def export_html(cls, data: dict[str, Any], output_path: Path) -> None:
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PcClean Audit Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #0B0F14; color: #E6EDF3; padding: 30px; margin: 0; }}
h1, h2 {{ color: #4F8CFF; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #111820; border-radius: 8px; overflow: hidden; }}
th, td {{ padding: 10px 14px; border: 1px solid #26313D; text-align: left; font-size: 13px; }}
th {{ background: #17222E; color: #4F8CFF; }}
.badge {{ padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; }}
.SAFE {{ background: #1A7F37; color: white; }}
.SAFE_REDOWNLOAD {{ background: #0969DA; color: white; }}
.REVIEW {{ background: #9A6700; color: white; }}
.IMPORTANT {{ background: #7C8CFF; color: white; }}
.DANGEROUS {{ background: #CF222E; color: white; }}
code {{ font-family: Consolas, monospace; background: #17222E; padding: 2px 6px; border-radius: 4px; }}
</style>
</head>
<body>
<h1>PcClean Storage & Cleanup Report</h1>
<p>Generated at: {data["generated_at"]} | Computer: {data["system_info"]["computer_name"]} ({data["system_info"]["os"]})</p>

<h2>Drives</h2>
<table>
<tr><th>Drive</th><th>Name</th><th>Type</th><th>Filesystem</th><th>Used</th><th>Free</th><th>Total</th><th>Used %</th></tr>
"""
        for d in data["drives"]:
            html += f"<tr><td><b>{d['letter']}</b></td><td>{d['name']}</td><td>{d['type']}</td><td>{d['filesystem']}</td><td>{d['used']}</td><td>{d['free']}</td><td>{d['total']}</td><td>{d['percent']}</td></tr>\n"
        html += "</table>\n<h2>Cleanup Candidates</h2>\n<table>\n<tr><th>Safety</th><th>Name</th><th>Category</th><th>Size</th><th>Files</th><th>Path</th><th>Explanation</th></tr>\n"
        for c in data["cleanup_candidates"]:
            html += f"<tr><td><span class='badge {c['safety']}'>{c['safety']}</span></td><td><b>{c['name']}</b></td><td>{c['category']}</td><td>{c['size']}</td><td>{c['files']}</td><td><code>{c['path']}</code></td><td>{c['explanation']}</td></tr>\n"
        html += "</table>\n</body>\n</html>"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
