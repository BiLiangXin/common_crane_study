# -*- coding: utf-8 -*-
"""
run_pipeline.py
---------------
一键运行整套流程：
1) 读取 & 清洗（剔除缺失/异常）
2) 计算速度并剔除速度异常值
3) 分段（处理缺失导致的断裂）
4) 夜间点识别（输出 is_night 及相关字段）
5) T-DBSCAN 聚类识别栖息地簇
6) 站点表输出 + 类型划分（越冬/繁殖/关键/临时）
7) 输出点表（含 cluster_id、is_habitat）与站点表（sites.csv）

运行：
    python run_pipeline.py
"""

from __future__ import annotations

import pandas as pd

import config as cfg
from preprocessing import (
    parse_datetime,
    clean_invalid_points,
    compute_step_metrics,
    filter_speed_outliers,
    add_segment_id,
)
from night import add_night_attributes
from clustering_tdbscan import tdbscan
from site_classification import (
    build_sites_table,
    classify_sites_by_rules,
    attach_site_type_to_points,
)
from io_utils import save_csv


def main() -> None:
    # ---------- 1) 读取 ----------
    df_raw = pd.read_csv(cfg.INPUT_CSV)

    # ---------- 2) 时间解析 ----------
    df = parse_datetime(df_raw, cfg.COL_TIME)

    # ---------- 3) 清洗无效点 ----------
    df_valid, df_removed_invalid = clean_invalid_points(
        df,
        lon_col=cfg.COL_LON,
        lat_col=cfg.COL_LAT,
        available_col=cfg.COL_AVAILABLE,
        available_ok_values=cfg.AVAILABLE_OK_VALUES,
        lon_range=cfg.LON_RANGE,
        lat_range=cfg.LAT_RANGE,
    )

    # ---------- 4) 计算速度/距离 ----------
    df_metrics = compute_step_metrics(
        df_valid,
        bird_id_col=cfg.COL_BIRD_ID,
        lon_col=cfg.COL_LON,
        lat_col=cfg.COL_LAT,
        datetime_col="datetime",
        min_dt_seconds=cfg.MIN_DT_SECONDS,
    )

    # ---------- 5) 剔除速度异常 ----------
    df_kept, df_removed_speed = filter_speed_outliers(df_metrics, cfg.MAX_SPEED_KMH)

    # ---------- 6) 分段 ----------
    df_seg = add_segment_id(
        df_kept,
        bird_id_col=cfg.COL_BIRD_ID,
        gap_hours=cfg.SEGMENT_GAP_HOURS,
    )

    # ---------- 7) 夜间点识别 ----------
    df_night = add_night_attributes(
        df_seg,
        time_is_utc=cfg.TIME_IS_UTC,
        local_tz=cfg.LOCAL_TIMEZONE,
        lat_col=cfg.COL_LAT,
        lon_col=cfg.COL_LON,
        night_method=cfg.NIGHT_METHOD,
        sun_elev_threshold_deg=cfg.NIGHT_SUN_ELEV_THRESHOLD_DEG,
        clock_start_hour=cfg.NIGHT_CLOCK_START_HOUR,
        clock_end_hour=cfg.NIGHT_CLOCK_END_HOUR,
    )

    # ---------- 8) T-DBSCAN 聚类 ----------
    df_clustered = tdbscan(
        df_night,
        bird_id_col=cfg.COL_BIRD_ID,
        lon_col=cfg.COL_LON,
        lat_col=cfg.COL_LAT,
        time_col="datetime",
        eps_m=cfg.TDBSCAN_EPS_METERS,
        max_interval_h=cfg.TDBSCAN_MAX_INTERVAL_HOURS,
        min_stay_h=cfg.TDBSCAN_MIN_STAY_HOURS,
        use_night_only=cfg.CLUSTER_USE_NIGHT_ONLY,
        night_col="is_night",
        day_assign_radius_m=cfg.DAY_ASSIGN_RADIUS_METERS,
    )

    # ---------- 9) 站点表 & 分类 ----------
    sites_all = build_sites_table(
        df_clustered,
        cluster_col="cluster_id",
        lon_col=cfg.COL_LON,
        lat_col=cfg.COL_LAT,
        time_col="datetime",
    )
    sites_all = classify_sites_by_rules(
        sites_all,
        breeding_months=cfg.BREEDING_MONTHS,
        wintering_months=cfg.WINTERING_MONTHS,
        breeding_min_days=cfg.BREEDING_MIN_DAYS,
        wintering_min_days=cfg.WINTERING_MIN_DAYS,
        key_stop_days=cfg.KEY_STOP_DAYS,
        min_stop_days=cfg.MIN_STOP_DAYS,
    )

    df_final = attach_site_type_to_points(df_clustered, sites_all, cluster_col="cluster_id")

    # ---------- 10) 输出 ----------
    # 点表字段（你也可以按需增删）
    keep_cols = [
        cfg.COL_BIRD_ID,
        cfg.COL_TIME,
        "datetime",
        "datetime_utc",
        cfg.COL_LON,
        cfg.COL_LAT,
        "segment_id",
        "dt_seconds",
        "dt_hours",
        "dist_m",
        "speed_kmh",
        "local_hour",
        "sun_elev_deg",
        "is_night",
        "is_night_solar",
        "is_night_clock",
        "cluster_id",
        "is_habitat",
        "event_type",
    ] + [c for c in cfg.KEEP_EXTRA_COLS if c in df_final.columns]

    points_out = df_final[keep_cols].copy()
    save_csv(points_out, cfg.OUT_POINTS_CSV)

    # 非栖息地（飞行轨迹）点：用于线密度/廊道
    flight_points = points_out[points_out["is_habitat"] == False].copy()  # noqa: E712
    save_csv(flight_points, cfg.OUT_FLIGHT_POINTS_CSV)

    # 全部站点（含临时停留地）
    save_csv(sites_all, cfg.OUT_SITES_ALL_CSV)

    # 站点.csv（仅越冬/繁殖/关键停留地）
    sites_key = sites_all[sites_all["event_type"].isin(["越冬地", "繁殖地", "关键停留地"])].copy()
    # 按你的字段要求输出（不含 mid_month）
    sites_key = sites_key[[
        "site_id", "n_points", "start_time", "end_time",
        "duration_days", "mean_lon", "mean_lat", "event_type"
    ]]
    save_csv(sites_key, cfg.OUT_SITES_CSV)

    # 可选：输出被剔除点（便于写论文的数据质量控制）
    save_csv(df_removed_invalid, cfg.OUTPUT_DIR / "removed_invalid_points.csv")
    save_csv(df_removed_speed, cfg.OUTPUT_DIR / "removed_speed_outliers.csv")

    print("✅ 处理完成！输出目录：", cfg.OUTPUT_DIR)
    print("点表：", cfg.OUT_POINTS_CSV.name)
    print("飞行点表：", cfg.OUT_FLIGHT_POINTS_CSV.name)
    print("站点表(全部)：", cfg.OUT_SITES_ALL_CSV.name)
    print("站点表(越冬/繁殖/关键)：", cfg.OUT_SITES_CSV.name)


if __name__ == "__main__":
    main()
