"""Verify project setup and readiness"""
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'


def check_file(file_path: Path, description: str) -> bool:
    """Check if a file exists"""
    exists = file_path.exists()
    status = f"{GREEN}[OK]{RESET}" if exists else f"{RED}[X]{RESET}"
    print(f"  {status} {description}: {file_path}")
    return exists


def check_directory(dir_path: Path, description: str) -> bool:
    """Check if a directory exists"""
    exists = dir_path.exists() and dir_path.is_dir()
    status = f"{GREEN}[OK]{RESET}" if exists else f"{RED}[X]{RESET}"
    print(f"  {status} {description}: {dir_path}")
    return exists


def check_env_file(env_path: Path) -> Tuple[bool, List[str]]:
    """Check .env file and required variables"""
    if not env_path.exists():
        return False, []

    with open(env_path, 'r') as f:
        content = f.read()

    required_vars = ['TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE']
    missing_vars = []

    for var in required_vars:
        # Check if variable exists and is not just the example placeholder
        if f"{var}=" not in content or f"{var}=your_" in content or f"{var}=+" in content:
            missing_vars.append(var)

    return True, missing_vars


def verify_setup():
    """Verify complete project setup"""
    project_root = Path(__file__).parent
    checks_passed = 0
    total_checks = 0

    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Telegram Signal Extractor - Setup Verification{RESET}")
    print(f"{BOLD}{'='*60}{RESET}\n")

    # Check core source files
    print(f"{BOLD}1. Core Source Files{RESET}")
    core_files = [
        (project_root / "src" / "main.py", "Main application"),
        (project_root / "src" / "config" / "config_manager.py", "Config manager"),
        (project_root / "src" / "telegram" / "client.py", "Telegram client"),
        (project_root / "src" / "extraction" / "extractor.py", "Signal extractor"),
        (project_root / "src" / "extraction" / "patterns.py", "Pattern matcher"),
        (project_root / "src" / "extraction" / "validators.py", "Validator"),
        (project_root / "src" / "storage" / "csv_writer.py", "CSV writer"),
        (project_root / "src" / "storage" / "error_logger.py", "Error logger"),
        (project_root / "src" / "utils" / "logging_setup.py", "Logging setup"),
    ]

    for file_path, description in core_files:
        total_checks += 1
        if check_file(file_path, description):
            checks_passed += 1

    # Check configuration files
    print(f"\n{BOLD}2. Configuration Files{RESET}")
    config_files = [
        (project_root / "config" / "config.yaml", "Main configuration"),
        (project_root / "config" / ".env.example", "Environment template"),
        (project_root / "requirements.txt", "Python dependencies"),
    ]

    for file_path, description in config_files:
        total_checks += 1
        if check_file(file_path, description):
            checks_passed += 1

    # Check .env file specifically
    total_checks += 1
    env_path = project_root / ".env"
    env_exists, missing_vars = check_env_file(env_path)

    if not env_exists:
        print(f"  {RED}[X]{RESET} .env file: {env_path}")
        print(f"    {YELLOW}[!]{RESET}  Create .env file by copying config/.env.example")
    elif missing_vars:
        print(f"  {YELLOW}[!]{RESET}  .env file: {env_path}")
        print(f"    {YELLOW}[!]{RESET}  Missing or placeholder values for: {', '.join(missing_vars)}")
        checks_passed += 0.5  # Partial credit
    else:
        print(f"  {GREEN}[OK]{RESET} .env file: {env_path}")
        checks_passed += 1

    # Check directories
    print(f"\n{BOLD}3. Directory Structure{RESET}")
    directories = [
        (project_root / "src", "Source code"),
        (project_root / "config", "Configuration"),
        (project_root / "docs", "Documentation"),
        (project_root / "tests", "Tests"),
        (project_root / "output", "Output files (auto-created)"),
        (project_root / "logs", "Log files (auto-created)"),
        (project_root / "sessions", "Telegram sessions (auto-created)"),
    ]

    for dir_path, description in directories:
        total_checks += 1
        if check_directory(dir_path, description):
            checks_passed += 1

    # Check documentation
    print(f"\n{BOLD}4. Documentation{RESET}")
    doc_files = [
        (project_root / "README.md", "User guide"),
        (project_root / "NEXT_STEPS.md", "Getting started"),
        (project_root / "BUILD_COMPLETE.md", "Build summary"),
        (project_root / "TESTING.md", "Testing guide"),
    ]

    for file_path, description in doc_files:
        total_checks += 1
        if check_file(file_path, description):
            checks_passed += 1

    # Check test files
    print(f"\n{BOLD}5. Test Files{RESET}")
    test_files = [
        (project_root / "tests" / "test_extraction.py", "Extraction tests"),
        (project_root / "test_extraction.bat", "Test runner (Windows)"),
    ]

    for file_path, description in test_files:
        total_checks += 1
        if check_file(file_path, description):
            checks_passed += 1

    # Summary
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Summary{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")

    percentage = (checks_passed / total_checks) * 100
    print(f"\nChecks passed: {int(checks_passed)}/{total_checks} ({percentage:.1f}%)")

    if percentage == 100:
        print(f"\n{GREEN}{BOLD}[OK] Setup is complete! You're ready to go.{RESET}")
        print(f"\n{BOLD}Next steps:{RESET}")
        print(f"  1. Ensure .env has your Telegram credentials")
        print(f"  2. Run tests: python tests/test_extraction.py")
        print(f"  3. Start application: python src/main.py")
        print(f"\nSee NEXT_STEPS.md for detailed instructions.")
    elif percentage >= 80:
        print(f"\n{YELLOW}{BOLD}[!] Setup is mostly complete, but some items are missing.{RESET}")
        print(f"\nReview the items marked with {RED}[X]{RESET} or {YELLOW}[!]{RESET} above.")
    else:
        print(f"\n{RED}{BOLD}[X] Setup is incomplete. Please review missing items.{RESET}")
        print(f"\nReview the items marked with {RED}[X]{RESET} above.")

    # Additional checks
    print(f"\n{BOLD}Additional Information:{RESET}")

    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 9):
        print(f"  {GREEN}[OK]{RESET} Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"  {RED}[X]{RESET} Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        print(f"    {YELLOW}[!]{RESET}  Python 3.9+ required")

    # Check if in virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if in_venv:
        print(f"  {GREEN}[OK]{RESET} Virtual environment: Active")
    else:
        print(f"  {YELLOW}[!]{RESET}  Virtual environment: Not active")
        print(f"    {YELLOW}[!]{RESET}  Recommended: Create and activate venv")

    print(f"\n{BOLD}{'='*60}{RESET}\n")


if __name__ == "__main__":
    try:
        verify_setup()
    except Exception as e:
        print(f"\n{RED}Error during verification: {e}{RESET}")
        import traceback
        traceback.print_exc()
