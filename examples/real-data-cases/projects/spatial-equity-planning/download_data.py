#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
from portfolio_runtime import project_main

raise SystemExit(project_main("download", __file__))
