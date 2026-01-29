"""Cross-platform autostart utility for Windows and macOS"""
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# App identifier
APP_NAME = "TelegramSignals"
MACOS_BUNDLE_ID = "com.telegramdignals.app"


def get_executable_path() -> str:
    """Get the path to the current executable or script"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable (PyInstaller)
        return sys.executable
    else:
        # Running as Python script - return python and script path
        return sys.executable


def get_executable_args() -> list:
    """Get the arguments needed to run the app"""
    if getattr(sys, 'frozen', False):
        return []
    else:
        # Running as Python script
        return [sys.argv[0]]


# =============================================================================
# Windows Implementation
# =============================================================================

def _set_autostart_windows(enable: bool, app_name: str) -> bool:
    """Windows: Add or remove app from registry autostart"""
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        exe_path = get_executable_path()
        args = get_executable_args()

        # Build full command
        if args:
            full_cmd = f'"{exe_path}" "{args[0]}"'
        else:
            full_cmd = f'"{exe_path}"'

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_READ
        )

        try:
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, full_cmd)
                logger.info(f"Autostart enabled for {app_name} (Windows)")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    logger.info(f"Autostart disabled for {app_name} (Windows)")
                except FileNotFoundError:
                    pass
            return True
        finally:
            winreg.CloseKey(key)

    except PermissionError:
        logger.error("Permission denied when modifying autostart registry")
        return False
    except Exception as e:
        logger.error(f"Failed to set Windows autostart: {e}")
        return False


def _is_autostart_enabled_windows(app_name: str) -> bool:
    """Windows: Check if autostart is enabled in registry"""
    try:
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ
        )

        try:
            winreg.QueryValueEx(key, app_name)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)

    except Exception as e:
        logger.error(f"Failed to check Windows autostart status: {e}")
        return False


# =============================================================================
# macOS Implementation
# =============================================================================

def _get_launchagent_path(app_name: str) -> Path:
    """Get the path to the Launch Agent plist file"""
    return Path.home() / "Library" / "LaunchAgents" / f"{MACOS_BUNDLE_ID}.plist"


def _create_launchagent_plist(app_name: str) -> str:
    """Create the Launch Agent plist content"""
    exe_path = get_executable_path()
    args = get_executable_args()

    # Build program arguments array
    program_args = [f"        <string>{exe_path}</string>"]
    for arg in args:
        program_args.append(f"        <string>{arg}</string>")
    program_args_str = "\n".join(program_args)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{MACOS_BUNDLE_ID}</string>
    <key>ProgramArguments</key>
    <array>
{program_args_str}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/{app_name}.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/{app_name}.stderr.log</string>
</dict>
</plist>
"""


def _set_autostart_macos(enable: bool, app_name: str) -> bool:
    """macOS: Add or remove Launch Agent plist"""
    try:
        plist_path = _get_launchagent_path(app_name)

        # Ensure LaunchAgents directory exists
        plist_path.parent.mkdir(parents=True, exist_ok=True)

        if enable:
            # Create the plist file
            plist_content = _create_launchagent_plist(app_name)
            plist_path.write_text(plist_content)
            logger.info(f"Autostart enabled for {app_name} (macOS)")
        else:
            # Remove the plist file if it exists
            if plist_path.exists():
                plist_path.unlink()
                logger.info(f"Autostart disabled for {app_name} (macOS)")

        return True

    except PermissionError:
        logger.error("Permission denied when modifying Launch Agent")
        return False
    except Exception as e:
        logger.error(f"Failed to set macOS autostart: {e}")
        return False


def _is_autostart_enabled_macos(app_name: str) -> bool:
    """macOS: Check if Launch Agent plist exists"""
    try:
        plist_path = _get_launchagent_path(app_name)
        return plist_path.exists()
    except Exception as e:
        logger.error(f"Failed to check macOS autostart status: {e}")
        return False


# =============================================================================
# Public API
# =============================================================================

def set_autostart(enable: bool, app_name: str = APP_NAME) -> bool:
    """
    Add or remove the app from system autostart.

    Supports:
    - Windows: Registry key in HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
    - macOS: Launch Agent plist in ~/Library/LaunchAgents/

    Args:
        enable: True to enable autostart, False to disable
        app_name: Name to use for the autostart entry

    Returns:
        True if successful, False otherwise
    """
    if sys.platform == 'win32':
        return _set_autostart_windows(enable, app_name)
    elif sys.platform == 'darwin':
        return _set_autostart_macos(enable, app_name)
    else:
        logger.warning(f"Autostart not supported on platform: {sys.platform}")
        return False


def is_autostart_enabled(app_name: str = APP_NAME) -> bool:
    """
    Check if autostart is enabled for the app.

    Args:
        app_name: Name to check for

    Returns:
        True if autostart is enabled, False otherwise
    """
    if sys.platform == 'win32':
        return _is_autostart_enabled_windows(app_name)
    elif sys.platform == 'darwin':
        return _is_autostart_enabled_macos(app_name)
    else:
        logger.warning(f"Autostart not supported on platform: {sys.platform}")
        return False


def is_autostart_supported() -> bool:
    """Check if autostart is supported on the current platform"""
    return sys.platform in ('win32', 'darwin')
