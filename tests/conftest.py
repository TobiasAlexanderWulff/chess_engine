import os
import sys


# Ensure the repository's src/ is on sys.path for `from src...` imports
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC_PATH = os.path.join(REPO_ROOT, "src")
SRC_PATH = os.path.abspath(SRC_PATH)
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
