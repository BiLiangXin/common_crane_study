
# -*- coding: utf-8 -*-
"""夜光指标重算与质量控制模块。"""

from __future__ import annotations

import numpy as np
import pandas as pd


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """
    安全除法：分母为 0 时返回 0，避免出现 inf 和 NaN。

    参数
    ----
    numerator : pd.Series
    denominator : pd.Series

    返回
    ----
    pd.Series
    """
    result = numerator / denominator.replace(0, np.nan)
    return result.fillna(0.0)


def add_recalculated_habitat_metrics(df: pd.DataFrame, config_module) -> pd.DataFrame:
    """
    基于面积分级字段，重新计算论文中的核心夜光指标。

    指标定义
    --------
    记：
    - A  = 栖息地总面积
    - S1 = 0–0.5 nW·cm⁻²·sr⁻¹ 面积
    - S2 = 0.5–1
    - S3 = 1–5
    - S4 = 5–10
    - S5 = 10+

    则：
    - NTL_AREA   = S2 + S3 + S4 + S5
    - HNLPI      = (1*S2 + 2*S3 + 3*S4 + 4*S5) / A
    - PCR        = (S2 + S3 + S4 + S5) / A
    - HER        = (S4 + S5) / A
    - STD_HNLPI  = HNLPI / 4
    - P1         = S2 / NTL_AREA
    - P2         = S3 / NTL_AREA
    - P3         = S4 / NTL_AREA
    - P4         = S5 / NTL_AREA
    - HER_LIT    = (S4 + S5) / NTL_AREA
    - ELS        = (1*S2 + 2*S3 + 3*S4 + 4*S5) / (4*NTL_AREA)

    注意
    ----
    这里将 0–0.5 视为“偏好环境”，不计入污染得分。

    参数
    ----
    df : pd.DataFrame
        栖息地表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        增加了 *_calc 字段的副本。
    """
    data = df.copy()

    area = data[config_module.AREA_COLUMN]
    s1 = data[config_module.AREA_CLASS_1]
    s2 = data[config_module.AREA_CLASS_2]
    s3 = data[config_module.AREA_CLASS_3]
    s4 = data[config_module.AREA_CLASS_4]
    s5 = data[config_module.AREA_CLASS_5]

    weighted_score = 1.0 * s2 + 2.0 * s3 + 3.0 * s4 + 4.0 * s5
    ntl_area = s2 + s3 + s4 + s5

    data["NTL_AREA_calc"] = ntl_area
    data["HNLPI_calc"] = safe_divide(weighted_score, area)
    data["PCR_calc"] = safe_divide(ntl_area, area)
    data["HER_calc"] = safe_divide(s4 + s5, area)
    data["STD_HNLPI_calc"] = data["HNLPI_calc"] / 4.0

    data["P1_calc"] = safe_divide(s2, ntl_area)
    data["P2_calc"] = safe_divide(s3, ntl_area)
    data["P3_calc"] = safe_divide(s4, ntl_area)
    data["P4_calc"] = safe_divide(s5, ntl_area)
    data["HER_LIT_calc"] = safe_divide(s4 + s5, ntl_area)
    data["ELS_calc"] = safe_divide(weighted_score, 4.0 * ntl_area)

    return data


def build_habitat_qc_table(df_with_calc: pd.DataFrame, config_module) -> pd.DataFrame:
    """
    构建质量控制（QC）表，比较原始字段和重算字段是否一致。

    参数
    ----
    df_with_calc : pd.DataFrame
        已包含 *_calc 字段的数据表。
    config_module : module
        config.py 模块对象。

    返回
    ----
    pd.DataFrame
        每个样地在每个派生指标上的“原值 / 重算值 / 差值”明细表。
    """
    compare_pairs = [
        ("NTL_AREA", "NTL_AREA_calc"),
        ("HNLPI", "HNLPI_calc"),
        ("PCR", "PCR_calc"),
        ("HER", "HER_calc"),
        ("STD_HNLPI", "STD_HNLPI_calc"),
        ("P1", "P1_calc"),
        ("P2", "P2_calc"),
        ("P3", "P3_calc"),
        ("P4", "P4_calc"),
        ("HER_LIT", "HER_LIT_calc"),
        ("ELS", "ELS_calc"),
    ]

    rows = []
    for _, row in df_with_calc.iterrows():
        for raw_col, calc_col in compare_pairs:
            raw_value = float(row[raw_col]) if pd.notna(row[raw_col]) else np.nan
            calc_value = float(row[calc_col]) if pd.notna(row[calc_col]) else np.nan
            diff = abs(raw_value - calc_value) if (pd.notna(raw_value) and pd.notna(calc_value)) else np.nan
            rows.append(
                {
                    config_module.ID_COLUMN: row[config_module.ID_COLUMN],
                    config_module.GROUP_COLUMN: row[config_module.GROUP_COLUMN],
                    "metric_name": raw_col,
                    "raw_value": raw_value,
                    "recalculated_value": calc_value,
                    "abs_diff": diff,
                    "within_tolerance": bool(diff <= config_module.FLOAT_TOLERANCE) if pd.notna(diff) else False,
                }
            )
    return pd.DataFrame(rows)
