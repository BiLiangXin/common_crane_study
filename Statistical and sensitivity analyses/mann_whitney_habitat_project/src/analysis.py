
# -*- coding: utf-8 -*-
"""分析主逻辑模块。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stats_utils import run_mann_whitney_single_metric, adjust_primary_pvalues


def build_group_counts(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """
    统计各栖息地类型的样本数。

    参数
    ----
    df : pd.DataFrame
        栖息地表。
    group_col : str
        分组列名，例如 event_type。

    返回
    ----
    pd.DataFrame
        各类型样本数表。
    """
    out = (
        df[group_col]
        .value_counts(dropna=False)
        .rename_axis(group_col)
        .reset_index(name="n_sites")
        .sort_values(by=group_col)
        .reset_index(drop=True)
    )
    return out


def descriptive_stats_by_group(df: pd.DataFrame, group_col: str, metrics: list[str]) -> pd.DataFrame:
    """
    计算各组在各指标上的描述性统计。

    统计项
    ------
    n, mean, sd, median, q1, q3, min, max

    参数
    ----
    df : pd.DataFrame
        栖息地表。
    group_col : str
        分组列名。
    metrics : list[str]
        需要汇总的指标列表。

    返回
    ----
    pd.DataFrame
        长表格式的描述性统计结果。
    """
    rows = []
    for group_name, sub_df in df.groupby(group_col):
        for metric in metrics:
            s = sub_df[metric].dropna().astype(float)
            rows.append(
                {
                    "group": group_name,
                    "metric": metric,
                    "n": int(s.count()),
                    "mean": float(s.mean()),
                    "sd": float(s.std(ddof=1)) if s.count() > 1 else np.nan,
                    "median": float(s.median()),
                    "q1": float(s.quantile(0.25)),
                    "q3": float(s.quantile(0.75)),
                    "min": float(s.min()),
                    "max": float(s.max()),
                }
            )
    return pd.DataFrame(rows)


def run_pairwise_mannwhitney(
    df: pd.DataFrame,
    group_col: str,
    group_a: str,
    group_b: str,
    metrics: list[str],
    config_module,
) -> pd.DataFrame:
    """
    对指定两组、多个指标批量执行 Mann–Whitney U 检验。

    参数
    ----
    df : pd.DataFrame
        栖息地表。
    group_col : str
        分组列名。
    group_a, group_b : str
        两个要比较的组名。
    metrics : list[str]
        需要检验的指标列表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        含原始检验结果和多重比较校正结果的表。
    """
    sub_a = df.loc[df[group_col] == group_a].copy()
    sub_b = df.loc[df[group_col] == group_b].copy()

    results = []
    for metric in metrics:
        x = sub_a[metric].dropna().to_numpy(dtype=float)
        y = sub_b[metric].dropna().to_numpy(dtype=float)
        if len(x) == 0 or len(y) == 0:
            continue
        result = run_mann_whitney_single_metric(
            x=x,
            y=y,
            metric_name=metric,
            group_a=group_a,
            group_b=group_b,
            config_module=config_module,
        )
        results.append(result)

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df

    result_df = adjust_primary_pvalues(result_df, config_module)
    return result_df


def summarize_corridor_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    对廊道表做简单汇总。

    说明
    ----
    廊道表只有 50%、75%、95% 三条嵌套等值范围，
    其值并非独立重复样本，因此不适合做 Mann–Whitney U 检验。
    这里仅做描述性汇总与相对变化量计算。

    参数
    ----
    df : pd.DataFrame
        预处理后的廊道表。

    返回
    ----
    pd.DataFrame
        增加面积、暴露变化率后的表。
    """
    data = df.copy()
    data["area_km2"] = data["area_m2"] / 1_000_000.0
    data["delta_area_vs_prev_pct"] = data["area_m2"].pct_change() * 100.0
    data["delta_exposure_vs_prev_pct"] = data["corridor_exposure"].pct_change() * 100.0

    base_idx = data["corridor_percentile"].idxmin()
    base_area = float(data.loc[base_idx, "area_m2"])
    base_exposure = float(data.loc[base_idx, "corridor_exposure"])

    data["delta_area_vs_50_pct"] = (data["area_m2"] / base_area - 1.0) * 100.0
    data["delta_exposure_vs_50_pct"] = (data["corridor_exposure"] / base_exposure - 1.0) * 100.0
    return data
