
# -*- coding: utf-8 -*-
"""数据预处理模块。"""

from __future__ import annotations

from typing import Iterable
import pandas as pd


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化列名：
    - 去掉首尾空格
    - 保留原始核心命名，不做激进改名，避免和论文表头/ArcGIS 字段脱节

    参数
    ----
    df : pd.DataFrame

    返回
    ----
    pd.DataFrame
        列名处理后的副本。
    """
    data = df.copy()
    data.columns = [str(col).strip() for col in data.columns]
    return data


def validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str], table_name: str) -> None:
    """
    检查表中是否包含全部必需字段。

    参数
    ----
    df : pd.DataFrame
        待检查数据表。
    required_columns : Iterable[str]
        必需字段名列表。
    table_name : str
        表名，用于报错信息。

    异常
    ----
    ValueError
        当缺少必需字段时抛出。
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{table_name} 缺少必需字段: {missing}")


def coerce_numeric(df: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame:
    """
    将指定列强制转换为数值类型；无法转换的内容设为 NaN。

    参数
    ----
    df : pd.DataFrame
        输入数据表。
    numeric_columns : Iterable[str]
        需要转为数值的列。

    返回
    ----
    pd.DataFrame
        转换后的副本。
    """
    data = df.copy()
    for col in numeric_columns:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")
    return data


def preprocess_habitat_table(df: pd.DataFrame, config_module) -> pd.DataFrame:
    """
    预处理栖息地表。

    处理内容
    --------
    1. 标准化列名
    2. 校验字段完整性
    3. 将数值列转为数值类型
    4. 对 event_type 去空格
    5. 按 OBJECTID 排序

    参数
    ----
    df : pd.DataFrame
        原始栖息地表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        处理后的栖息地表。
    """
    data = standardize_column_names(df)
    validate_required_columns(data, config_module.REQUIRED_HABITAT_COLUMNS, "栖息地表")

    numeric_cols = [
        "MIN", "MAX", "RANGE", "MEAN", "STD", "SUM", "MEDIAN", "PCT75", "PCT90", "PCT95",
        config_module.AREA_COLUMN,
        config_module.AREA_CLASS_1,
        config_module.AREA_CLASS_2,
        config_module.AREA_CLASS_3,
        config_module.AREA_CLASS_4,
        config_module.AREA_CLASS_5,
        "HNLPI", "PCR", "HER", "STD_HNLPI", "NTL_AREA", "P1", "P2", "P3", "P4", "HER_LIT", "ELS",
    ]
    data = coerce_numeric(data, numeric_cols)
    data[config_module.GROUP_COLUMN] = data[config_module.GROUP_COLUMN].astype(str).str.strip()
    data = data.sort_values(by=config_module.ID_COLUMN).reset_index(drop=True)
    return data


def preprocess_corridor_table(df: pd.DataFrame, config_module) -> pd.DataFrame:
    """
    预处理廊道表。

    处理内容
    --------
    1. 标准化列名
    2. 校验字段完整性
    3. 规范字段命名
    4. 数值转换
    5. 百分位排序

    参数
    ----
    df : pd.DataFrame
        原始廊道表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        处理后的廊道表。
    """
    data = standardize_column_names(df)
    validate_required_columns(data, config_module.REQUIRED_CORRIDOR_COLUMNS, "廊道表")

    rename_map = {
        "OBJECTID_1": "corridor_percentile",
        "COUNT": "count",
        "AREA": "area_m2",
        "CorridorExposure": "corridor_exposure",
    }
    data = data.rename(columns=rename_map)
    numeric_cols = ["corridor_percentile", "count", "area_m2", "corridor_exposure"]
    data = coerce_numeric(data, numeric_cols)
    data = data.sort_values(by="corridor_percentile").reset_index(drop=True)
    return data
