
# -*- coding: utf-8 -*-
"""统计检验工具模块。"""

from __future__ import annotations

from math import comb
import numpy as np
from scipy.stats import mannwhitneyu, PermutationMethod
from statsmodels.stats.multitest import multipletests


def pooled_has_ties(x: np.ndarray, y: np.ndarray) -> bool:
    """
    判断两组数据合并后是否存在 ties（相同数值）。

    参数
    ----
    x, y : np.ndarray
        两组独立样本。

    返回
    ----
    bool
        True 表示存在 ties，False 表示不存在。
    """
    pooled = np.concatenate([x, y])
    return len(np.unique(pooled)) < len(pooled)


def common_language_effect(u_statistic: float, n1: int, n2: int) -> float:
    """
    Common-Language Effect Size（CLES）：
    表示“从组 A 随机抽 1 个值大于组 B 随机抽 1 个值”的概率。

    公式
    ----
    CLES = U / (n1 * n2)

    参数
    ----
    u_statistic : float
        Mann–Whitney U 统计量（对应第一组）。
    n1, n2 : int
        两组样本量。

    返回
    ----
    float
        CLES，范围约为 [0, 1]。
    """
    return float(u_statistic) / float(n1 * n2)


def rank_biserial_from_u(u_statistic: float, n1: int, n2: int) -> float:
    """
    由 U 统计量计算 rank-biserial correlation（秩二列相关效应量）。

    公式
    ----
    r_rb = 2 * U / (n1 * n2) - 1

    解释
    ----
    - > 0：组 A 值整体偏大
    - < 0：组 A 值整体偏小
    - 绝对值越大，组间差异越强

    参数
    ----
    u_statistic : float
        Mann–Whitney U 统计量（对应第一组）。
    n1, n2 : int
        两组样本量。

    返回
    ----
    float
        rank-biserial correlation。
    """
    return 2.0 * float(u_statistic) / float(n1 * n2) - 1.0


def hodges_lehmann_shift(x: np.ndarray, y: np.ndarray) -> float:
    """
    计算 Hodges–Lehmann shift estimator（两组位移的稳健估计）。

    计算方法
    --------
    枚举所有 x_i - y_j 的差值，并取其中位数。

    参数
    ----
    x, y : np.ndarray
        两组独立样本。

    返回
    ----
    float
        位移估计值。
    """
    diffs = np.subtract.outer(x, y).ravel()
    return float(np.median(diffs))


def choose_mw_method(x: np.ndarray, y: np.ndarray, config_module, mode: str):
    """
    根据配置和当前数据情况，生成 SciPy 可接受的 method 参数。

    参数
    ----
    x, y : np.ndarray
        两组独立样本。
    config_module : module
        config.py 模块对象。
    mode : str
        支持：
        - "permutation"
        - "manuscript_asymptotic"
        - "exact"
        - "auto"

    返回
    ----
    object
        可直接传给 scipy.stats.mannwhitneyu(method=...) 的对象。
    """
    if mode == "permutation":
        total_n = len(x) + len(y)
        n_small = min(len(x), len(y))
        total_partitions = comb(total_n, n_small)

        if config_module.MW_PERMUTATION_RESAMPLES == "exact":
            n_resamples = np.inf
        else:
            n_resamples = int(config_module.MW_PERMUTATION_RESAMPLES)

        return PermutationMethod(
            n_resamples=n_resamples,
            random_state=config_module.MW_RANDOM_STATE,
        )

    if mode == "manuscript_asymptotic":
        return "asymptotic"
    if mode == "exact":
        return "exact"
    return "auto"


def run_mann_whitney_single_metric(
    x: np.ndarray,
    y: np.ndarray,
    metric_name: str,
    group_a: str,
    group_b: str,
    config_module,
) -> dict:
    """
    对单个指标执行 Mann–Whitney U 检验，并返回完整结果字典。

    该函数会同时输出：
    1. 论文可复现的 asymptotic p 值
    2. 更适合当前小样本/有 ties 场景的 permutation p 值（若配置如此）
    3. 效应量（CLES、rank-biserial）
    4. 中位数差、均值差、Hodges–Lehmann 位移估计

    参数
    ----
    x, y : np.ndarray
        两组独立样本。
    metric_name : str
        指标名。
    group_a, group_b : str
        组名。
    config_module : module
        config.py 模块对象。

    返回
    ----
    dict
        单指标统计结果。
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    ref_method = choose_mw_method(x, y, config_module, config_module.MW_REFERENCE_METHOD)
    primary_method = choose_mw_method(x, y, config_module, config_module.MW_PRIMARY_METHOD)

    ref_res = mannwhitneyu(
        x,
        y,
        alternative=config_module.MW_ALTERNATIVE,
        use_continuity=config_module.MW_USE_CONTINUITY,
        method=ref_method,
    )
    primary_res = mannwhitneyu(
        x,
        y,
        alternative=config_module.MW_ALTERNATIVE,
        use_continuity=config_module.MW_USE_CONTINUITY,
        method=primary_method,
    )

    u = float(ref_res.statistic)
    n1 = len(x)
    n2 = len(y)

    result = {
        "metric": metric_name,
        "group_a": group_a,
        "group_b": group_b,
        "n_a": n1,
        "n_b": n2,
        "mean_a": float(np.mean(x)),
        "mean_b": float(np.mean(y)),
        "sd_a": float(np.std(x, ddof=1)) if n1 > 1 else np.nan,
        "sd_b": float(np.std(y, ddof=1)) if n2 > 1 else np.nan,
        "median_a": float(np.median(x)),
        "median_b": float(np.median(y)),
        "q1_a": float(np.quantile(x, 0.25)),
        "q3_a": float(np.quantile(x, 0.75)),
        "q1_b": float(np.quantile(y, 0.25)),
        "q3_b": float(np.quantile(y, 0.75)),
        "u_statistic": u,
        "p_reference": float(ref_res.pvalue),
        "p_primary": float(primary_res.pvalue),
        "reference_method": config_module.MW_REFERENCE_METHOD,
        "primary_method": config_module.MW_PRIMARY_METHOD,
        "has_ties": pooled_has_ties(x, y),
        "cles": common_language_effect(u, n1, n2),
        "rank_biserial": rank_biserial_from_u(u, n1, n2),
        "mean_diff_a_minus_b": float(np.mean(x) - np.mean(y)),
        "median_diff_a_minus_b": float(np.median(x) - np.median(y)),
        "hodges_lehmann_shift": hodges_lehmann_shift(x, y),
    }
    return result


def adjust_primary_pvalues(result_df, config_module):
    """
    对 primary metrics 的 p 值做多重比较校正。

    说明
    ----
    只对 config.PRIMARY_METRICS 中定义的主终点进行校正；
    这样既符合论文中“主指标优先”的写法，也避免把探索性指标
    和主结论混在一起过度保守。

    参数
    ----
    result_df : pd.DataFrame
        Mann–Whitney 检验结果表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        增加了 p_adjusted_primary 和 reject_primary 的副本。
    """
    data = result_df.copy()
    data["is_primary_metric"] = data["metric"].isin(config_module.PRIMARY_METRICS)
    data["p_adjust_method"] = None
    data["p_adjusted_primary"] = np.nan
    data["reject_primary"] = None

    if config_module.PRIMARY_P_ADJUST_METHOD is None:
        return data

    mask = data["is_primary_metric"]
    if mask.sum() == 0:
        return data

    corrected = multipletests(
        data.loc[mask, "p_primary"].to_numpy(),
        alpha=config_module.ALPHA,
        method=config_module.PRIMARY_P_ADJUST_METHOD,
    )
    data.loc[mask, "p_adjust_method"] = config_module.PRIMARY_P_ADJUST_METHOD
    data.loc[mask, "p_adjusted_primary"] = corrected[1]
    data.loc[mask, "reject_primary"] = corrected[0]
    return data
