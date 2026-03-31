"""Top-level Streamlit entrypoint.

This shim makes the app runnable from the repository root without requiring
manual PYTHONPATH tweaks.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Importing this module executes the Streamlit app definition.
import epicc.__main__  # noqa: F401
