"""Installed Applications discovery via Windows Registry and official uninstaller invocation."""

import logging
import subprocess
import winreg

from models.application import InstalledApp

logger = logging.getLogger("PcClean.ApplicationService")


class ApplicationService:
    @classmethod
    def get_installed_applications(cls) -> list[InstalledApp]:
        """Enumerate installed applications from Windows Registry uninstall entries."""
        apps: list[InstalledApp] = []
        seen_names = set()

        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for root_key, subkey_path in registry_paths:
            try:
                with winreg.OpenKey(root_key, subkey_path) as root:
                    num_subkeys = winreg.QueryInfoKey(root)[0]
                    for i in range(num_subkeys):
                        try:
                            key_name = winreg.EnumKey(root, i)
                            with winreg.OpenKey(root, key_name) as app_key:
                                name = cls._get_reg_val(app_key, "DisplayName")
                                if not name:
                                    continue

                                # Clean name and check deduplication
                                name_clean = name.strip()
                                if name_clean.lower() in seen_names:
                                    continue
                                seen_names.add(name_clean.lower())

                                version = cls._get_reg_val(app_key, "DisplayVersion") or ""
                                publisher = cls._get_reg_val(app_key, "Publisher") or ""
                                install_date = cls._get_reg_val(app_key, "InstallDate") or ""
                                install_loc = cls._get_reg_val(app_key, "InstallLocation") or ""
                                uninstall_str = cls._get_reg_val(app_key, "UninstallString") or ""
                                sys_comp = bool(cls._get_reg_val(app_key, "SystemComponent") or 0)

                                size_val = cls._get_reg_val(app_key, "EstimatedSize")
                                size_bytes = (int(size_val) * 1024) if size_val else 0

                                apps.append(
                                    InstalledApp(
                                        name=name_clean,
                                        version=version,
                                        publisher=publisher,
                                        install_date=install_date,
                                        install_location=install_loc,
                                        uninstall_string=uninstall_str,
                                        estimated_size=size_bytes,
                                        is_system_component=sys_comp,
                                    )
                                )
                        except Exception:
                            continue
            except Exception as e:
                logger.error(f"Error reading registry key {subkey_path}: {e}")

        return sorted(apps, key=lambda a: a.name.lower())

    @classmethod
    def launch_uninstaller(cls, app: InstalledApp) -> bool:
        """Launch the official application uninstaller. NEVER deletes the folder directly."""
        if not app.uninstall_string:
            return False
        try:
            import shlex

            cmd = app.uninstall_string.strip()
            logger.info(f"Launching official uninstaller: {cmd}")
            try:
                args = shlex.split(cmd, posix=False)
                subprocess.Popen(args)  # nosec B603
            except Exception:
                subprocess.Popen(cmd, shell=True)  # nosec B602
            return True
        except Exception as e:
            logger.error(f"Failed to launch uninstaller for {app.name}: {e}")
            return False

    @staticmethod
    def _get_reg_val(key, val_name: str):
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except Exception:
            return None
