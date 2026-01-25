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
        shutil.rmtree(dist_dir)
        print(f"  Removed: {dist_dir}")
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

1. Copy `.env.example` to `.env` in the `config` folder
2. Edit `.env` with your Telegram API credentials:
   - Get API ID and Hash from https://my.telegram.org
   - Add your phone number

3. Edit `config.yaml` to configure:
   - Channels to monitor
   - Output settings
   - Extraction parameters

4. Run `TelegramSignals.exe`

## Folders

- `config/` - Configuration files (.env, config.yaml)
- `output/` - Extracted signals CSV files
- `logs/` - Application logs
- `data/` - Signal store for MT5 integration
- `sessions/` - Telegram session files (keep private!)

## Note

Keep your `sessions/` folder private - it contains your Telegram login!
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
