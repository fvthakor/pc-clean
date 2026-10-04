"""PcClean Desktop Application Entrypoint."""

import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger("PcClean")

# Ensure project root is in path
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def main():
    # If command-line arguments are passed, route to CLI
    if len(sys.argv) > 1 and sys.argv[1] not in ("--gui", "-g"):
        from pcclean.cli import run_cli

        sys.exit(run_cli())

    # Launch PySide6 GUI
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from ui.main_window import MainWindow

    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("PcClean")
    app.setOrganizationName("PcClean")

    # Set icon if exists
    icon_path = project_root / "resources" / "icons" / "pcclean.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    logger.info("PcClean Desktop GUI started successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
