import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from applied_runtime import entry

if __name__ == "__main__":
    entry("analyze", __file__)
