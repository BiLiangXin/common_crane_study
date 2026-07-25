# -*- coding: utf-8 -*-
"""
site_classification.py
----------------------
把聚类簇（cluster_id）汇总为“站点表”，并根据规则分类：
- 越冬地
- 繁殖地
- 关键停留地
- 临时停留地

分类依据（可在 config.py 调参）：
- 先用 duration（持续天数）筛长驻站点（越冬/繁殖）
- 再结合月份区分越冬季/繁殖季
- 其余按 14天阈值（关键停留）与 2天阈值（临时停留）区分
"""

from __future__ import annotations

from typing import Tuple, Set

import pandas as pd


def classify_sites_by_rules(
    sites: pd.DataFrame,
    breeding_months: Set[int],
    wintering_months: Set[int],
    breeding_min_days: float,
    wintering_min_days: float,
    key_stop_days: float,
    min_stop_days: float,
) -> pd.DataFrame:
    """
    给站点表增加 event_type 字段。
    """
    out = sites.copy()

    # 站点中位时间，用于判定季节
    mid_time = out["start_time"] + (out["end_time"] - out["start_time"]) / 2
    out["mid_month"] = mid_time.dt.month

    def _label(row):
        dur = row["duration_days"]
        m = int(row["mid_month"])

        # 先判定长驻
        if dur >= breeding_min_days and m in breeding_months:
            return "繁殖地"
        if dur >= wintering_min_days and m in wintering_months:
            return "越冬地"

        # 再判定停留等级
        if dur >= key_stop_days:
            return "关键停留地"
        if dur >= min_stop_days:
            return "临时停留地"
        return "非栖息地"

    out["event_type"] = out.apply(_label, axis=1)
    return out


def build_sites_table(
    points: pd.DataFrame,
    cluster_col: str,
    lon_col: str,
    lat_col: str,
    time_col: str,
) -> pd.DataFrame:
    """
    从点表汇总站点表（每个 cluster_id 一行）。
    """
    df = points[points[cluster_col] != -1].copy()
    if df.empty:
        return pd.DataFrame(columns=[
            "site_id", "n_points", "start_time", "end_time",
            "duration_days", "mean_lon", "mean_lat"
        ])

    sites = (
        df.groupby(cluster_col)
        .agg(
            n_points=(cluster_col, "size"),
            start_time=(time_col, "min"),
            end_time=(time_col, "max"),
            mean_lon=(lon_col, "mean"),
            mean_lat=(lat_col, "mean"),
        )
        .reset_index()
        .rename(columns={cluster_col: "site_id"})
    )
    sites["duration_days"] = (sites["end_time"] - sites["start_time"]).dt.total_seconds() / 86400.0
    return sites


def attach_site_type_to_points(
    points: pd.DataFrame,
    sites: pd.DataFrame,
    cluster_col: str = "cluster_id",
) -> pd.DataFrame:
    """
    把站点分类结果回写到点表：
    - event_type：栖息地类型；对飞行点/噪声点填“飞行轨迹”
    - is_habitat：是否为栖息地（cluster_id!=-1）
    """
    out = points.copy()
    out["is_habitat"] = out[cluster_col] != -1
    out["event_type"] = "飞行轨迹"

    if not sites.empty:
        mapper = sites.set_index("site_id")["event_type"].to_dict()
        out.loc[out["is_habitat"], "event_type"] = out.loc[out["is_habitat"], cluster_col].map(mapper).fillna("栖息地(未分类)")

    return out
