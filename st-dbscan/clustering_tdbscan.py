# -*- coding: utf-8 -*-
"""
clustering_tdbscan.py
---------------------
T-DBSCAN（基于最小停留时长的时空聚类）实现。

说明（与你的需求对齐）：
- 传统 DBSCAN 使用 minPts（最小点数）控制簇密度；
- 在动物轨迹里采样并不均匀，minPts 容易失真；
- 因此我们用“最小停留时长 min_stay”替代 minPts，
  同时用“最大连续时间间隔 max_interval”避免缺失点把簇连在一起。

实现策略（计算上更高效，也更适配轨迹）：
- 对每条轨迹按时间排序；
- 在时间窗口 max_interval 内，若两点空间距离 <= eps，则建立连接；
- 连接图的连通分量即为候选停留簇；
- 对每个连通分量计算持续时间 duration，>= min_stay 的保留为栖息地簇，否则为噪声(-1)。

这套实现与你提供的 T-DBSCAN 思想一致：空间阈值 + 时间连续性约束 + 最小停留时长。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd


def haversine_m_vec(lon1, lat1, lon2, lat2) -> np.ndarray:
    """向量化 Haversine 距离（米），lon/lat 单位：度。"""
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


class DSU:
    """并查集（Union-Find）用于快速计算连通分量。"""
    def __init__(self, n: int):
        self.parent = np.arange(n, dtype=int)
        self.rank = np.zeros(n, dtype=int)

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra
        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


def _tdbscan_unionfind_one_track(
    track: pd.DataFrame,
    lon_col: str,
    lat_col: str,
    time_col: str,
    eps_m: float,
    max_interval_h: float,
    min_stay_h: float,
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    对单条轨迹（已按 time_col 升序）做 T-DBSCAN。

    返回：
    - labels：每个点的 cluster_id（从0开始，-1为噪声）
    - comp_stats：连通分量统计表（root为内部编号）
    """
    n = len(track)
    if n == 0:
        return np.array([], dtype=int), pd.DataFrame()

    lon = track[lon_col].to_numpy(dtype=float)
    lat = track[lat_col].to_numpy(dtype=float)

    # 时间转为秒（int64），必须单调递增
    times_int = track[time_col].values.astype("datetime64[s]").astype("int64")

    dsu = DSU(n)
    max_interval_sec = int(max_interval_h * 3600)

    # 对每个点 i，只检查未来 max_interval 内的点
    j_end = np.searchsorted(times_int, times_int + max_interval_sec, side="right")

    for i in range(n):
        end = int(j_end[i])
        if end <= i + 1:
            continue

        idx = np.arange(i + 1, end)
        dist = haversine_m_vec(lon[i], lat[i], lon[idx], lat[idx])

        close_idx = idx[dist <= eps_m]
        for j in close_idx:
            dsu.union(i, int(j))

    # 计算每个点的 root
    roots = np.array([dsu.find(i) for i in range(n)], dtype=int)

    comp = pd.DataFrame({"root": roots, "t": times_int})
    comp_stats = comp.groupby("root")["t"].agg(["min", "max", "count"]).reset_index()
    comp_stats["duration_h"] = (comp_stats["max"] - comp_stats["min"]) / 3600.0

    # 只保留停留时长 >= min_stay_h 的分量作为簇
    keep_roots = comp_stats.loc[comp_stats["duration_h"] >= min_stay_h, "root"].tolist()

    root_to_cluster = {int(r): cid for cid, r in enumerate(keep_roots)}
    labels = np.array([root_to_cluster.get(int(r), -1) for r in roots], dtype=int)

    return labels, comp_stats


def tdbscan(
    df: pd.DataFrame,
    bird_id_col: str,
    lon_col: str,
    lat_col: str,
    time_col: str,
    eps_m: float,
    max_interval_h: float,
    min_stay_h: float,
    use_night_only: bool = False,
    night_col: str = "is_night",
    day_assign_radius_m: float = 15000.0,
) -> pd.DataFrame:
    """
    对多只个体（bird_id）执行 T-DBSCAN，并写回 df 的 cluster_id 字段（全局唯一）。

    如果 use_night_only=True：
    1) 仅对夜间点聚类（得到“夜栖核心簇”）
    2) 再把同一时间段内、距离簇均值中心 <= day_assign_radius_m 的白天点归入该簇
       （得到“站点范围”更完整的栖息地点集）
    """
    out = df.copy()
    out["cluster_id"] = -1

    global_offset = 0

    for bird_id, g in out.groupby(bird_id_col, sort=False):
        g_sorted = g.sort_values(time_col).copy()

        if not use_night_only:
            labels, comp_stats = _tdbscan_unionfind_one_track(
                g_sorted, lon_col, lat_col, time_col, eps_m, max_interval_h, min_stay_h
            )
            # 加全局偏移
            labels_global = np.where(labels >= 0, labels + global_offset, -1)
            out.loc[g_sorted.index, "cluster_id"] = labels_global

            n_clusters = int(labels.max() + 1) if len(labels) else 0
            global_offset += n_clusters
            continue

        # ---- 夜间点聚类 ----
        g_night = g_sorted[g_sorted[night_col] == True].copy()  # noqa: E712
        labels_night, _ = _tdbscan_unionfind_one_track(
            g_night, lon_col, lat_col, time_col, eps_m, max_interval_h, min_stay_h
        )
        labels_night_global = np.where(labels_night >= 0, labels_night + global_offset, -1)
        out.loc[g_night.index, "cluster_id"] = labels_night_global

        n_clusters = int(labels_night.max() + 1) if len(labels_night) else 0

        # ---- 白天点归并到夜间簇（可选）----
        if n_clusters > 0:
            # 先算每个簇的时间范围与均值中心
            tmp = g_night.copy()
            tmp["cluster_id"] = labels_night_global
            site_stats = (
                tmp[tmp["cluster_id"] != -1]
                .groupby("cluster_id")
                .agg(
                    start_time=(time_col, "min"),
                    end_time=(time_col, "max"),
                    mean_lon=(lon_col, "mean"),
                    mean_lat=(lat_col, "mean"),
                )
                .reset_index()
            )

            # 对每个簇，把时间在 [start,end] 且距离中心 <= day_assign_radius 的点归入
            for _, row in site_stats.iterrows():
                cid = int(row["cluster_id"])
                t0 = row["start_time"]
                t1 = row["end_time"]
                lon0 = float(row["mean_lon"])
                lat0 = float(row["mean_lat"])

                mask_time = (g_sorted[time_col] >= t0) & (g_sorted[time_col] <= t1)
                candidates = g_sorted.loc[mask_time]

                if candidates.empty:
                    continue

                dist = haversine_m_vec(lon0, lat0, candidates[lon_col].to_numpy(), candidates[lat_col].to_numpy())
                within = candidates.index[dist <= day_assign_radius_m]

                # 仅对尚未分到其它簇的点赋值（避免覆盖）
                unassigned = within[out.loc[within, "cluster_id"] == -1]
                out.loc[unassigned, "cluster_id"] = cid

        global_offset += n_clusters

    return out
