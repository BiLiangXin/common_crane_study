
# -*- coding: utf-8 -*-
"""
项目总配置文件
你只需要修改这里的参数，就可以控制整套分析流程。
"""

from pathlib import Path

# =========================
# 路径配置
# =========================
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"

# 输入文件
HABITAT_FILE = DATA_DIR / "CLUSTER_fanganA.xlsx"
HABITAT_SHEET = "origin_gps_poi_PairwiseDisso2_E"   # 设为 None 表示读取第一个工作表

CORRIDOR_FILE = DATA_DIR / "corrrider.xlsx"
CORRIDOR_SHEET = "ZonalSt_CorridorExposure_Line50"  # 设为 None 表示读取第一个工作表

# =========================
# 栖息地字段配置
# =========================
GROUP_COLUMN = "event_type"
ID_COLUMN = "OBJECTID"

# 两组比较对象：这正是论文中做 Mann–Whitney 检验的核心比较
GROUP_A = "关键停留地"
GROUP_B = "临时停留地"

# 原始面积字段
AREA_COLUMN = "AREA"
AREA_CLASS_1 = "0_0.5"   # 偏好环境
AREA_CLASS_2 = "0.5_1"   # 潜在影响
AREA_CLASS_3 = "1_5"     # 明确干扰（低暴露）
AREA_CLASS_4 = "5_10"    # 中度暴露
AREA_CLASS_5 = "10+"     # 高暴露

# 论文主指标（建议作为 primary endpoints）
PRIMARY_METRICS = [
    "PCR",
    "STD_HNLPI",
    "ELS",
]

# 补充指标（用于支持性分析）
SECONDARY_METRICS = [
    "MEAN",
    "PCT90",
    "HER",
]

# 若你还想加入其它指标，可在这里统一配置
ALL_TEST_METRICS = PRIMARY_METRICS + SECONDARY_METRICS

# 是否重新按面积字段计算派生指标并做一致性校验
RECALCULATE_METRICS = True

# 浮点数容忍误差：用于判断原表字段和重算字段是否一致
FLOAT_TOLERANCE = 1e-10

# =========================
# Mann–Whitney U 检验配置
# =========================
# 说明：
# 1) manuscript_asymptotic：用于严格复现论文正文里写出的 p 值
# 2) permutation：更适合当前这种“小样本 + 存在 ties/大量 0”的场景
# 3) exact：仅适合无 ties 且小样本；如果有 ties，SciPy 也能算，但官方不建议直接解释
MW_PRIMARY_METHOD = "permutation"
MW_REFERENCE_METHOD = "manuscript_asymptotic"

MW_ALTERNATIVE = "two-sided"
MW_USE_CONTINUITY = True

# permutation 模式下：
# - 设为 "exact"：若组合数允许，则穷举全部重排（本数据 6 vs 10，可穷举）
# - 设为整数：例如 100000，表示随机重排次数
MW_PERMUTATION_RESAMPLES = "exact"
MW_RANDOM_STATE = 42

# 多重比较校正：对 primary metrics 做校正
# 可选：None, "fdr_bh", "holm", "bonferroni"
PRIMARY_P_ADJUST_METHOD = "fdr_bh"
ALPHA = 0.05

# =========================
# 输出文件名
# =========================
CLEAN_HABITAT_CSV = OUTPUT_DIR / "cleaned_habitat_data.csv"
CLEAN_CORRIDOR_CSV = OUTPUT_DIR / "cleaned_corridor_data.csv"

GROUP_COUNTS_CSV = OUTPUT_DIR / "group_counts.csv"
DESCRIPTIVE_STATS_CSV = OUTPUT_DIR / "group_descriptive_stats.csv"
MANN_WHITNEY_CSV = OUTPUT_DIR / "mannwhitney_results.csv"
QC_DIFF_CSV = OUTPUT_DIR / "habitat_metric_qc_diff.csv"
CORRIDOR_SUMMARY_CSV = OUTPUT_DIR / "corridor_summary.csv"

RESULTS_REPORT_MD = OUTPUT_DIR / "results_report_CN.md"

# =========================
# 需要校验/依赖的字段
# =========================
REQUIRED_HABITAT_COLUMNS = [
    ID_COLUMN,
    GROUP_COLUMN,
    "MIN",
    "MAX",
    "RANGE",
    "MEAN",
    "STD",
    "SUM",
    "MEDIAN",
    "PCT75",
    "PCT90",
    "PCT95",
    AREA_COLUMN,
    AREA_CLASS_1,
    AREA_CLASS_2,
    AREA_CLASS_3,
    AREA_CLASS_4,
    AREA_CLASS_5,
    "HNLPI",
    "PCR",
    "HER",
    "STD_HNLPI",
    "NTL_AREA",
    "P1",
    "P2",
    "P3",
    "P4",
    "HER_LIT",
    "ELS",
]

REQUIRED_CORRIDOR_COLUMNS = [
    "OBJECTID_1",
    "COUNT",
    "AREA",
    "CorridorExposure",
]

# 输出时的小数精度
ROUND_DIGITS = 6
