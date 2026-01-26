"""
Build script for creating portable Windows executable
"""
import subprocess
import sys
import shutil
from pathlib import Path


def main():
    """Build the portable executable"""
    project_root = Path(__file__).parent.parent
    spec_file = project_root / "TelegramSignals.spec"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    print("=" * 60)
    print("Building Telegram Signal Extractor")
    print("=" * 60)

    # Check if spec file exists
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return 1

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
    output_dir = dist_dir / "TelegramSignals"

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
        readme_content = """# Telegram Signal Extractor - Portable Version

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
        (output_dir / "README.txt").write_text(readme_content)
        print("  Created: README.txt")

    # Summary
    print("\n[4/4] Build complete!")
    print("=" * 60)
    print(f"Output: {output_dir}")
    print(f"\nTo distribute, zip the entire 'TelegramSignals' folder.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
