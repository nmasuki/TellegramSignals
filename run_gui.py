"""Launch the GUI application"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Import and run GUI
from src.gui.app import main

if __name__ == "__main__":
    main()
