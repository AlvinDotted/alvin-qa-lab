# -*- coding:utf-8 -*-
"""
File: paths.py
Author: Alvin
Date: 2026-08-22
Description: 路径
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
LOGO_PATH = PROJECT_ROOT / "docs" / "images" / "logo.png"
FAVICON_PATH = PROJECT_ROOT / "docs" / "images" / "favicon.ico"