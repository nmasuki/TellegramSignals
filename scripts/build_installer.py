"""
Build script for creating self-extracting installers
- Windows: Uses Inno Setup to create .exe installer
- macOS: Creates .dmg disk image

Run this after build_exe.py has created the application.
"""
import subprocess
import sys
import shutil
from pathlib import Path

IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'

VERSION = "1.0.0"


def find_inno_setup() -> Path | None:
    """Find Inno Setup compiler on Windows"""
    possible_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 5\ISCC.exe"),
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Try to find in PATH
    iscc = shutil.which("ISCC")
    if iscc:
        return Path(iscc)

    return None


def build_windows_installer(project_root: Path) -> int:
    """Build Windows installer using Inno Setup"""
    print("\n" + "=" * 60)
    print("Building Windows Installer (Inno Setup)")
    print("=" * 60)

    # Check if PyInstaller output exists
    dist_dir = project_root / "dist" / "TelegramSignals"
    if not dist_dir.exists():
        print(f"ERROR: Build output not found: {dist_dir}")
        print("Please run 'python scripts/build_exe.py' first")
        return 1

    # Find Inno Setup
    iscc = find_inno_setup()
    if not iscc:
        print("ERROR: Inno Setup not found!")
        print("\nPlease install Inno Setup from:")
        print("  https://jrsoftware.org/isdl.php")
        print("\nOr add ISCC.exe to your PATH")
        return 1

    print(f"Found Inno Setup: {iscc}")

    # Create installer output directory
    installer_dir = project_root / "installer"
    installer_dir.mkdir(exist_ok=True)

    # Check for license file, create if missing
    license_file = project_root / "LICENSE"
    if not license_file.exists():
        print("Creating placeholder LICENSE file...")
        license_file.write_text(
            "MIT License\n\n"
            "Copyright (c) 2024 TelegramSignals\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE.\n"
        )

    # Run Inno Setup compiler
    iss_file = project_root / "scripts" / "installer.iss"
    print(f"\nCompiling: {iss_file}")

    result = subprocess.run(
        [str(iscc), str(iss_file)],
        cwd=str(project_root / "scripts"),
        capture_output=False
    )

    if result.returncode != 0:
        print("\nERROR: Inno Setup compilation failed!")
        return result.returncode

    installer_path = installer_dir / f"TelegramSignals_Setup_{VERSION}.exe"
    print(f"\n{'=' * 60}")
    print("Windows installer created successfully!")
    print(f"{'=' * 60}")
    print(f"Output: {installer_path}")

    return 0


def build_macos_installer(project_root: Path) -> int:
    """Build macOS DMG installer"""
    print("\n" + "=" * 60)
    print("Building macOS DMG Installer")
    print("=" * 60)

    # Check if .app bundle exists
    app_path = project_root / "dist" / "TelegramSignals.app"
    if not app_path.exists():
        print(f"ERROR: App bundle not found: {app_path}")
        print("Please run 'python scripts/build_exe.py' first")
        return 1

    # Create installer output directory
    installer_dir = project_root / "installer"
    installer_dir.mkdir(exist_ok=True)

    dmg_path = installer_dir / f"TelegramSignals_{VERSION}.dmg"
    staging_dir = project_root / "dist" / "dmg_staging"

    # Clean up existing
    if dmg_path.exists():
        dmg_path.unlink()
    if staging_dir.exists():
        shutil.rmtree(staging_dir)

    # Create staging directory
    staging_dir.mkdir()

    print("Copying app bundle to staging...")
    shutil.copytree(app_path, staging_dir / "TelegramSignals.app")

    # Copy README if exists
    readme_path = project_root / "dist" / "README.txt"
    if readme_path.exists():
        shutil.copy(readme_path, staging_dir / "README.txt")

    # Create Applications symlink
    (staging_dir / "Applications").symlink_to("/Applications")

    print("Creating DMG...")
    result = subprocess.run(
        [
            "hdiutil", "create",
            "-volname", "Telegram Signal Extractor",
            "-srcfolder", str(staging_dir),
            "-ov",
            "-format", "UDZO",
            str(dmg_path)
        ],
        capture_output=False
    )

    # Clean up staging
    shutil.rmtree(staging_dir)

    if result.returncode != 0:
        print("\nERROR: DMG creation failed!")
        return result.returncode

    print(f"\n{'=' * 60}")
    print("macOS DMG created successfully!")
    print(f"{'=' * 60}")
    print(f"Output: {dmg_path}")

    return 0


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent

    if IS_WINDOWS:
        return build_windows_installer(project_root)
    elif IS_MACOS:
        return build_macos_installer(project_root)
    else:
        print("ERROR: Installer creation is only supported on Windows and macOS")
        return 1


if __name__ == "__main__":
    sys.exit(main())
