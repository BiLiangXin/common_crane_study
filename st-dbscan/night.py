# -*- coding: utf-8 -*-
"""
night.py
--------
夜间点识别。

你提出的需求是：输出一个“夜间点识别属性”，方便后续配置：
- 只用夜间点做聚类（更接近夜栖地/栖息地核心）
- 或用全部点做聚类（更接近站点/觅食范围）

本模块实现两套夜间判定：
1) solar：基于太阳高度角（推荐，科学可解释）
2) clock：基于固定时段（18:00-06:00），用于快速对照/容错
"""

from __future__ import annotations

from typing import Tuple
import numpy as np
import pandas as pd


def _solar_elevation_deg(
    dt_utc: pd.Series,
    lat_deg: pd.Series,
    lon_deg: pd.Series,
) -> np.ndarray:
    """
    计算太阳高度角（度），参考 NOAA Solar Calculator 常用公式（近似精度足够做昼夜判别）。

    输入：
    - dt_utc：UTC 时区的 pandas datetime（tz-aware）
    - lat_deg / lon_deg：纬度/经度（度）

    输出：
    - elevation_deg：太阳高度角（度）
    """
    # 转为 UTC naive，便于计算儒略日
    dt_utc_naive = dt_utc.dt.tz_convert("UTC").dt.tz_localize(None)

    jd = pd.DatetimeIndex(dt_utc_naive).to_julian_date().to_numpy(dtype=float)  # Julian Day
    T = (jd - 2451545.0) / 36525.0  # Julian Century

    # 太阳几何平均黄经（deg）
    L0 = 280.46646 + T * (36000.76983 + T * 0.0003032)
    L0 = np.mod(L0, 360.0)

    # 太阳几何平均近点角（deg）
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    M = np.mod(M, 360.0)
    M_rad = np.radians(M)

    # 地球轨道偏心率
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)

    # 太阳方程中心差（deg）
    C = (
        np.sin(M_rad) * (1.914602 - T * (0.004817 + 0.000014 * T))
        + np.sin(2 * M_rad) * (0.019993 - 0.000101 * T)
        + np.sin(3 * M_rad) * 0.000289
    )

    # 太阳真黄经（deg）
    true_long = L0 + C

    # 章动修正
    omega = 125.04 - 1934.136 * T
    lambda_app = true_long - 0.00569 - 0.00478 * np.sin(np.radians(omega))

    # 黄赤交角（deg）
    mean_obliq = 23.0 + (26.0 + ((21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60.0)) / 60.0
    obliq_corr = mean_obliq + 0.00256 * np.cos(np.radians(omega))

    # 太阳赤纬（rad）
    decl = np.arcsin(np.sin(np.radians(obliq_corr)) * np.sin(np.radians(lambda_app)))

    # 时间方程 EqTime（minutes）
    y = np.tan(np.radians(obliq_corr) / 2.0) ** 2
    eq_time = 4.0 * np.degrees(
        y * np.sin(2.0 * np.radians(L0))
        - 2.0 * e * np.sin(M_rad)
        + 4.0 * e * y * np.sin(M_rad) * np.cos(2.0 * np.radians(L0))
        - 0.5 * y ** 2 * np.sin(4.0 * np.radians(L0))
        - 1.25 * e ** 2 * np.sin(2.0 * M_rad)
    )

    # UTC 时刻换算为分钟
    hour = dt_utc_naive.dt.hour.to_numpy(dtype=float)
    minute = dt_utc_naive.dt.minute.to_numpy(dtype=float)
    second = dt_utc_naive.dt.second.to_numpy(dtype=float)
    utc_minutes = hour * 60.0 + minute + second / 60.0

    lon = lon_deg.to_numpy(dtype=float)
    lat = lat_deg.to_numpy(dtype=float)
    lat_rad = np.radians(lat)

    # 真太阳时（minutes）
    true_solar_time = np.mod(utc_minutes + eq_time + 4.0 * lon, 1440.0)

    # 时角（deg）
    hour_angle = true_solar_time / 4.0 - 180.0
    ha_rad = np.radians(hour_angle)

    # 天顶角
    cos_zenith = np.sin(lat_rad) * np.sin(decl) + np.cos(lat_rad) * np.cos(decl) * np.cos(ha_rad)
    cos_zenith = np.clip(cos_zenith, -1.0, 1.0)
    zenith = np.arccos(cos_zenith)

    # 高度角（deg）
    elevation = 90.0 - np.degrees(zenith)
    return elevation


def add_night_attributes(
    df: pd.DataFrame,
    time_is_utc: bool,
    local_tz: str,
    lat_col: str,
    lon_col: str,
    night_method: str = "solar",
    sun_elev_threshold_deg: float = -6.0,
    clock_start_hour: int = 18,
    clock_end_hour: int = 6,
) -> pd.DataFrame:
    """
    给点表增加夜间判定字段：
    - datetime_utc：UTC时间（便于跨时区、跨区域计算）
    - sun_elev_deg：太阳高度角（仅 solar 需要）
    - is_night_solar / is_night_clock
    - is_night：按 night_method 选出的最终夜间标记

    参数：
    - time_is_utc：你的 time 字段是否已经是 UTC
    - local_tz：当 time_is_utc=False，用它把本地时间转成UTC
    """
    out = df.copy()

    # 统一得到 UTC 时区时间
    if time_is_utc:
        out["datetime_utc"] = out["datetime"].dt.tz_localize("UTC")
        out["datetime_local"] = out["datetime_utc"].dt.tz_convert(local_tz)
    else:
        out["datetime_local"] = out["datetime"].dt.tz_localize(local_tz)
        out["datetime_utc"] = out["datetime_local"].dt.tz_convert("UTC")

    # 固定时段夜间
    local_hour = out["datetime_local"].dt.hour
    out["local_hour"] = local_hour
    out["is_night_clock"] = (local_hour >= clock_start_hour) | (local_hour < clock_end_hour)

    # 太阳高度角夜间
    out["sun_elev_deg"] = _solar_elevation_deg(
        out["datetime_utc"],
        out[lat_col],
        out[lon_col],
    )
    out["is_night_solar"] = out["sun_elev_deg"] < sun_elev_threshold_deg

    # 最终夜间字段
    if night_method.lower() == "solar":
        out["is_night"] = out["is_night_solar"]
    elif night_method.lower() == "clock":
        out["is_night"] = out["is_night_clock"]
    else:
        raise ValueError(f"night_method 只能是 'solar' 或 'clock'，当前={night_method}")

    return out
