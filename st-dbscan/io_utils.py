# -*- coding: utf-8 -*-
"""
io_utils.py
-----------
简单的输入输出封装（写CSV）。
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def save_csv(df: pd.DataFrame, path: Path, encoding: str = "utf-8-sig") -> None:
    """
    保存CSV（默认 utf-8-sig，便于 Windows/ArcGIS 打开不乱码）
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding=encoding)
