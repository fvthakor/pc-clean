"""PcClean entrypoint for 'python -m pcclean'."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("--gui", "-g"):
        from pcclean.cli import run_cli

        sys.exit(run_cli())
    else:
        from PySide6.QtWidgets import QApplication

        from ui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("PcClean")
        app.setApplicationDisplayName("PcClean")

        window = MainWindow()
        window.show()
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
