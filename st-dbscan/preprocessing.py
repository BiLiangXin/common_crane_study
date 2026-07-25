# -*- coding: utf-8 -*-
"""
preprocessing.py
----------------
数据预处理：读取、清洗、计算速度/距离/时间差、分段。

输出：
- 清洗后的点（保留原始字段 + 计算字段）
- 可选：被剔除的点（方便你在论文补充材料报告数据质量）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np
import pandas as pd


def haversine_m(lon1, lat1, lon2, lat2) -> float:
    """
    计算两点球面距离（米），Haversine 公式。
    lon/lat 单位：度。
    """
    R = 6371000.0
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl / 2.0) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))


def haversine_m_vec(lon1, lat1, lon2, lat2) -> np.ndarray:
    """向量化 Haversine（米），lon/lat 单位：度。"""
    R = 6371000.0
    lon1 = np.asarray(lon1, dtype=float)
    lat1 = np.asarray(lat1, dtype=float)
    lon2 = np.asarray(lon2, dtype=float)
    lat2 = np.asarray(lat2, dtype=float)

    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl / 2.0) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def parse_datetime(df: pd.DataFrame, time_col: str) -> pd.DataFrame:
    """解析时间字段为 pandas datetime（naive）。"""
    out = df.copy()
    out["datetime"] = pd.to_datetime(out[time_col], errors="coerce")
    return out


def clean_invalid_points(
    df: pd.DataFrame,
    lon_col: str,
    lat_col: str,
    available_col: str,
    available_ok_values: set,
    lon_range: tuple,
    lat_range: tuple,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    清洗无效点：
    - Available != ok
    - lon/lat 超范围
    - datetime 解析失败
    """
    df2 = df.copy()

    # 类型转换（有些csv会读成字符串）
    df2[lon_col] = pd.to_numeric(df2[lon_col], errors="coerce")
    df2[lat_col] = pd.to_numeric(df2[lat_col], errors="coerce")

    cond_available = df2[available_col].isin(available_ok_values)
    cond_lon = df2[lon_col].between(lon_range[0], lon_range[1], inclusive="both")
    cond_lat = df2[lat_col].between(lat_range[0], lat_range[1], inclusive="both")
    cond_time = df2["datetime"].notna()

    keep = cond_available & cond_lon & cond_lat & cond_time
    removed = df2.loc[~keep].copy()
    kept = df2.loc[keep].copy()
    return kept, removed


def compute_step_metrics(
    df: pd.DataFrame,
    bird_id_col: str,
    lon_col: str,
    lat_col: str,
    datetime_col: str = "datetime",
    min_dt_seconds: int = 30,
) -> pd.DataFrame:
    """
    计算相邻两点的：
    - dt_seconds / dt_hours
    - dist_m
    - speed_kmh

    注意：
    - 必须先按 bird_id + datetime 排序
    - 对 dt<=0 或 dt<min_dt_seconds 的点，speed 置为 NaN
    """
    out = df.sort_values([bird_id_col, datetime_col]).copy()

    out["lon_prev"] = out.groupby(bird_id_col)[lon_col].shift(1)
    out["lat_prev"] = out.groupby(bird_id_col)[lat_col].shift(1)
    out["time_prev"] = out.groupby(bird_id_col)[datetime_col].shift(1)

    dt_seconds = (out[datetime_col] - out["time_prev"]).dt.total_seconds()
    out["dt_seconds"] = dt_seconds
    out["dt_hours"] = dt_seconds / 3600.0

    # 距离（米）
    out["dist_m"] = haversine_m_vec(out["lon_prev"], out["lat_prev"], out[lon_col], out[lat_col])

    # 速度（km/h）
    out["speed_kmh"] = (out["dist_m"] / 1000.0) / out["dt_hours"]

    # dt<=0 / dt太小：速度无意义
    bad_dt = (out["dt_seconds"].isna()) | (out["dt_seconds"] <= 0) | (out["dt_seconds"] < min_dt_seconds)
    out.loc[bad_dt, ["dist_m", "speed_kmh"]] = np.nan
    return out


def filter_speed_outliers(df: pd.DataFrame, max_speed_kmh: float) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    剔除速度异常点（speed_kmh > max_speed_kmh）。
    返回：(保留点, 被剔除点)
    """
    out = df.copy()
    # speed_kmh 为 NaN 的点保留（通常是首点或 dt异常）
    keep = (out["speed_kmh"].isna()) | (out["speed_kmh"] <= max_speed_kmh)
    removed = out.loc[~keep].copy()
    kept = out.loc[keep].copy()
    return kept, removed


def add_segment_id(
    df: pd.DataFrame,
    bird_id_col: str,
    gap_hours: float,
) -> pd.DataFrame:
    """
    根据相邻点时间间隔是否超过 gap_hours 来分段。
    segment_id：同一只鸟内从0开始递增。
    """
    out = df.sort_values([bird_id_col, "datetime"]).copy()
    gap = (out["dt_hours"].isna()) | (out["dt_hours"] > gap_hours)
    # 同一只鸟内累加
    out["segment_id"] = gap.groupby(out[bird_id_col]).cumsum().astype(int)
    return out
