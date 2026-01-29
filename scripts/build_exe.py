"""
Build script for creating portable executable (Windows and macOS)
"""
import subprocess
import sys
import shutil
from pathlib import Path

IS_WINDOWS = sys.platform == 'win32'
IS_MACOS = sys.platform == 'darwin'


def main():
    """Build the portable executable"""
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "TelegramSignals.spec"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    platform_name = "Windows" if IS_WINDOWS else "macOS" if IS_MACOS else "Linux"
    print("=" * 60)
    print(f"Building Telegram Signal Extractor for {platform_name}")
    print("=" * 60)

    # Check if spec file exists
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return 1

    # Check for macOS icon
    if IS_MACOS:
        icns_file = project_root / "src" / "gui" / "resources" / "icons" / "app.icns"
        if not icns_file.exists():
            print(f"\nWARNING: macOS icon not found: {icns_file}")
            print("  The app will use a default icon.")
            print("  To create an .icns file from app.ico, use:")
            print("    sips -s format icns app.ico --out app.icns")
            print("  Or use an online converter.\n")

    # Clean previous builds
    print("\n[1/4] Cleaning previous builds...")
    if dist_dir.exists():
        try:
            shutil.rmtree(dist_dir)
            print(f"  Removed: {dist_dir}")
        except PermissionError as e:
            print(f"  Warning: Could not remove {dist_dir}")
            print(f"  {e}")
            print(f"  Please close the application and try again.")
            return 1
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"  Removed: {build_dir}")

    # Run PyInstaller
    print("\n[2/4] Running PyInstaller...")
    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(spec_file)
        ],
        cwd=str(project_root),
        capture_output=False
    )

    if result.returncode != 0:
        print("\nERROR: PyInstaller failed!")
        return result.returncode

    # Copy additional files
    print("\n[3/4] Copying additional files...")

    if IS_MACOS:
        output_dir = dist_dir / "TelegramSignals.app" / "Contents" / "MacOS"
        app_bundle = dist_dir / "TelegramSignals.app"
    else:
        output_dir = dist_dir / "TelegramSignals"
        app_bundle = None

    if output_dir.exists():
        # Copy config template
        config_dest = output_dir / "config"
        config_dest.mkdir(exist_ok=True)

        # Copy .env.example
        env_example = project_root / "config" / ".env.example"
        if env_example.exists():
            shutil.copy(env_example, config_dest / ".env.example")
            print(f"  Copied: .env.example")

        # Create empty directories
        (output_dir / "output").mkdir(exist_ok=True)
        (output_dir / "logs").mkdir(exist_ok=True)
        (output_dir / "data").mkdir(exist_ok=True)
        (output_dir / "sessions").mkdir(exist_ok=True)
        print("  Created: output/, logs/, data/, sessions/ directories")

        # Create README for portable version
        readme_content = create_readme(IS_MACOS)
        readme_name = "README.txt"
        if IS_MACOS and app_bundle:
            # Put README next to the .app bundle
            (dist_dir / readme_name).write_text(readme_content)
        else:
            (output_dir / readme_name).write_text(readme_content)
        print(f"  Created: {readme_name}")

    # Summary
    print("\n[4/4] Build complete!")
    print("=" * 60)

    if IS_MACOS:
        print(f"Output: {dist_dir / 'TelegramSignals.app'}")
        print(f"\nTo distribute:")
        print(f"  1. Create a DMG: hdiutil create -volname 'TelegramSignals' \\")
        print(f"       -srcfolder dist -ov -format UDZO TelegramSignals.dmg")
        print(f"  2. Or zip the .app bundle")
    else:
        print(f"Output: {output_dir}")
        print(f"\nTo distribute, zip the entire 'TelegramSignals' folder.")

    print("=" * 60)

    return 0


def create_readme(is_macos: bool) -> str:
    """Create platform-specific README content"""
    if is_macos:
        return """# Telegram Signal Extractor - macOS Version

## First Time Setup

1. Create a `.env` file in the app's config folder with your Telegram credentials:

   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+1234567890

   Config folder location: Right-click app > Show Package Contents > Contents/MacOS/config/

   Get API credentials from: https://my.telegram.org
   (Go to "API development tools" and create an app)

2. (Optional) Edit `config/config.yaml` to add channels to monitor.
   You can also use the Settings dialog in the app.

3. Double-click TelegramSignals.app to run

4. On first run, log in to Telegram when prompted (enter verification code)

## Gatekeeper Warning

If macOS shows "TelegramSignals can't be opened because it is from an unidentified developer":
1. Right-click (or Control-click) the app
2. Select "Open" from the menu
3. Click "Open" in the dialog

## Folders (inside app bundle)

- `config/` - Configuration files (.env, config.yaml)
- `output/` - Extracted signals CSV files
- `logs/` - Application logs
- `data/` - Signal store for MT5 integration
- `sessions/` - Telegram session files (KEEP PRIVATE!)

## Important Notes

- Keep your `sessions/` folder private - it contains your Telegram login
- The app will create config.yaml automatically if it doesn't exist
- You can use environment variables in .env to configure everything
- Default signal server runs on http://localhost:4726/signals

## Troubleshooting

- If the app doesn't start, check that config/.env exists with valid credentials
- If you get "No channels configured" error, add channels in config.yaml
- Check logs/app.log for detailed error messages
"""
    else:
        return """# Telegram Signal Extractor - Portable Version

## First Time Setup

1. Create a `.env` file in the `config` folder with your Telegram credentials:

   TELEGRAM_API_ID=your_api_id_here
   TELEGRAM_API_HASH=your_api_hash_here
   TELEGRAM_PHONE=+1234567890

   Get API credentials from: https://my.telegram.org
   (Go to "API development tools" and create an app)

2. (Optional) Edit `config/config.yaml` to add channels to monitor.
   You can also use the Settings dialog in the app.

3. Run `TelegramSignals.exe`

4. On first run, log in to Telegram when prompted (enter verification code)

## Folders

- `config/` - Configuration files (.env, config.yaml)
- `output/` - Extracted signals CSV files
- `logs/` - Application logs
- `data/` - Signal store for MT5 integration
- `sessions/` - Telegram session files (KEEP PRIVATE!)

## Important Notes

- Keep your `sessions/` folder private - it contains your Telegram login
- The app will create config.yaml automatically if it doesn't exist
- You can use environment variables in .env to configure everything
- Default signal server runs on http://localhost:4726/signals

## Troubleshooting

- If the app doesn't start, check that config/.env exists with valid credentials
- If you get "No channels configured" error, add channels in config.yaml
- Check logs/app.log for detailed error messages
"""


if __name__ == "__main__":
    sys.exit(main())
