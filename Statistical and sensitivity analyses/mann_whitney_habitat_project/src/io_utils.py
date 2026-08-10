
# -*- coding: utf-8 -*-
"""输入输出工具模块。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd


def ensure_output_dir(output_dir: Path) -> None:
    """
    确保输出目录存在。

    参数
    ----
    output_dir : Path
        输出目录路径。
    """
    output_dir.mkdir(parents=True, exist_ok=True)


def resolve_sheet_name(excel_path: Path, preferred_sheet: Optional[str] = None) -> str:
    """
    解析要读取的工作表名称。

    逻辑：
    1. 如果 preferred_sheet 存在且在工作簿中，直接使用；
    2. 否则读取第一个工作表。

    参数
    ----
    excel_path : Path
        Excel 文件路径。
    preferred_sheet : str | None
        期望读取的工作表名称。

    返回
    ----
    str
        最终使用的工作表名称。
    """
    excel_file = pd.ExcelFile(excel_path)
    if preferred_sheet and preferred_sheet in excel_file.sheet_names:
        return preferred_sheet
    return excel_file.sheet_names[0]


def read_excel_table(excel_path: Path, preferred_sheet: Optional[str] = None) -> pd.DataFrame:
    """
    读取 Excel 中的一个工作表为 DataFrame。

    参数
    ----
    excel_path : Path
        Excel 文件路径。
    preferred_sheet : str | None
        指定工作表名称；若不存在则读取第一个工作表。

    返回
    ----
    pd.DataFrame
        读取后的数据表。
    """
    sheet_name = resolve_sheet_name(excel_path, preferred_sheet)
    return pd.read_excel(excel_path, sheet_name=sheet_name)


def save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    """
    将 DataFrame 保存为 CSV（UTF-8-SIG，兼容中文 Excel 打开）。

    参数
    ----
    df : pd.DataFrame
        需要保存的数据。
    output_path : Path
        输出文件路径。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
