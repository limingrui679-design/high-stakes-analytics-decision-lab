#!/usr/bin/env python3
"""Stable compatibility facade for the modular project runtime."""

from __future__ import annotations

from portfolio_core import *
from portfolio_clinical import *
from portfolio_modeling import *
from portfolio_finance import *
from portfolio_governance_spatial import *
from portfolio_reporting import *

__all__ = [name for name in globals() if not name.startswith("__")]
