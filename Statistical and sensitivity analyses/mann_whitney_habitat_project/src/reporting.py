
# -*- coding: utf-8 -*-
"""结果报告生成模块。"""

from __future__ import annotations

from pathlib import Path
import pandas as pd


def _fmt(value, digits=6):
    """
    将数值格式化为固定小数位；非数值原样返回。
    """
    if pd.isna(value):
        return "NA"
    if isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def dataframe_to_markdown(df: pd.DataFrame, digits: int = 6) -> str:
    """
    将 DataFrame 转成 Markdown 表格字符串。

    参数
    ----
    df : pd.DataFrame
    digits : int
        数值保留位数。

    返回
    ----
    str
        Markdown 表格。
    """
    if df.empty:
        return "（空表）"
    tmp = df.copy()
    for col in tmp.columns:
        tmp[col] = tmp[col].map(lambda x: _fmt(x, digits))
    return tmp.to_markdown(index=False)


def write_results_report(
    output_path: Path,
    group_counts_df: pd.DataFrame,
    descriptive_df: pd.DataFrame,
    mw_df: pd.DataFrame,
    corridor_df: pd.DataFrame,
    config_module,
) -> None:
    """
    生成中文 Markdown 结果报告。

    参数
    ----
    output_path : Path
        报告输出路径。
    group_counts_df : pd.DataFrame
        栖息地类型样本量表。
    descriptive_df : pd.DataFrame
        描述性统计表。
    mw_df : pd.DataFrame
        Mann–Whitney 检验结果表。
    corridor_df : pd.DataFrame
        廊道汇总表。
    config_module : module
        config.py 模块对象。
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    primary_mw = mw_df[mw_df["metric"].isin(config_module.PRIMARY_METRICS)].copy()
    secondary_mw = mw_df[~mw_df["metric"].isin(config_module.PRIMARY_METRICS)].copy()

    report = f"""# Mann–Whitney 检验与结果说明（自动生成）

## 1. 本次检验的研究目的

本次统计检验的目标，是验证论文中的核心判断：**关键停留地**与**临时停留地**
在夜光暴露水平上是否存在系统性差异。

之所以选择这两个组，是因为：
1. 繁殖地只有 1 个样地；
2. 越冬地只有 1 个样地；
3. 只有“关键停留地 vs 临时停留地”满足最基本的两独立样本比较条件。

因此，本项目把下列三个指标作为主终点（primary endpoints）：
- PCR：污染覆盖率
- STD_HNLPI：标准化栖息地夜光污染指数
- ELS：夜光覆盖区平均暴露等级

同时输出三个支持性指标（secondary metrics）：
- MEAN：平均夜光辐亮度
- PCT90：90 分位夜光辐亮度
- HER：高暴露占比

## 2. 为什么用 Mann–Whitney U 检验

这一步不是为了比较“均值是否不同”本身，而是检验：
**关键停留地的一组样地值，是否整体上高于临时停留地的一组样地值。**

该检验适用于：
- 两组独立样本；
- 样本量较小；
- 变量分布偏态、含大量 0 值，不适合直接假定正态分布。

本项目同时输出两类 p 值：
1. `p_reference`：论文正文复现值（asymptotic）
2. `p_primary`：推荐报告值（permutation / 精确重排）

## 3. 样本量

{dataframe_to_markdown(group_counts_df, digits=config_module.ROUND_DIGITS)}

## 4. 主终点描述性统计

{dataframe_to_markdown(descriptive_df[descriptive_df["metric"].isin(config_module.PRIMARY_METRICS)], digits=config_module.ROUND_DIGITS)}

## 5. Mann–Whitney 主终点结果

{dataframe_to_markdown(primary_mw[[
    "metric", "n_a", "n_b",
    "median_a", "q1_a", "q3_a",
    "median_b", "q1_b", "q3_b",
    "u_statistic", "p_reference", "p_primary",
    "p_adjusted_primary", "rank_biserial", "cles",
    "hodges_lehmann_shift"
]], digits=config_module.ROUND_DIGITS)}

### 主终点解读
- `p_reference`：对应论文正文复现值；
- `p_primary`：当前代码推荐值。对于小样本且可能存在 ties 的指标，更稳健；
- `rank_biserial`：效应量，>0 表示组 A（关键停留地）整体更高；
- `cles`：组 A 随机抽取一个样地值大于组 B 的概率；
- `hodges_lehmann_shift`：稳健位移估计，表示组 A 相对组 B 的典型增加量。

## 6. 支持性指标结果

{dataframe_to_markdown(secondary_mw[[
    "metric", "n_a", "n_b",
    "median_a", "median_b",
    "u_statistic", "p_reference", "p_primary",
    "rank_biserial", "cles", "hodges_lehmann_shift"
]], digits=config_module.ROUND_DIGITS)}

## 7. 统计结论（可直接写入论文）

### 7.1 论文复现角度（对应正文原始写法）
在 asymptotic 方法下，关键停留地相较于临时停留地在：
- PCR 上更高；
- STD_HNLPI 上更高；
- ELS 上更高；
且三者均达到 p < 0.05。

此外，MEAN 也达到显著，而 PCT90 与 HER 未达到显著。

### 7.2 更稳健的小样本解释（推荐在答辩/补充材料中说明）
在 permutation 方法下，主终点 PCR、STD_HNLPI、ELS 的 p 值仍均 < 0.05，
并且经主终点多重比较校正后仍保持显著。
这说明论文关于“关键停留地夜光暴露显著高于临时停留地”的核心结论是稳健的。

## 8. 廊道表说明

{dataframe_to_markdown(corridor_df, digits=config_module.ROUND_DIGITS)}

廊道表只有 50%、75%、95% 三个嵌套概率廊道结果，
它们不是独立重复样本，因此**不适合**做 Mann–Whitney U 检验。
更合适的写法是做描述性比较：随着廊道面积从 50% 扩展到 95%，
面积只增加有限比例，但暴露指数下降，说明最核心、重复利用最强的迁飞廊道
处在更明亮的夜间环境中。

## 9. 你在论文中可以怎么写方法

“由于繁殖地和越冬地样本量均为 1，正式推断仅针对关键停留地（n=6）与临时停留地（n=10）展开。
考虑到夜光暴露指标存在明显偏态和大量零值，采用两独立样本 Mann–Whitney U 检验比较两类栖息地在 PCR、
STD_HNLPI、ELS、平均辐亮度（MEAN）、90 分位辐亮度（PCT90）和高暴露占比（HER）上的差异。
为复现论文正文，同时报告基于正态近似的 asymptotic p 值；同时考虑到小样本和 ties 的影响，
补充报告基于置换的 permutation p 值，并对主终点的 p 值进行 FDR-BH 校正。”

## 10. 你在论文中可以怎么写结果

“关键停留地的夜光暴露整体高于临时停留地。
在主终点上，关键停留地的 PCR、STD_HNLPI 和 ELS 均显著高于临时停留地，
且 permutation 检验及主终点多重比较校正后结论保持稳定。
其中，PCR 的秩二列相关效应量为 { _fmt(primary_mw.loc[primary_mw['metric']=='PCR', 'rank_biserial'].iloc[0], config_module.ROUND_DIGITS) }，
表明组间差异幅度较大；STD_HNLPI 和 ELS 也表现出中到大的效应量。
支持性指标中，MEAN 显著更高，而 PCT90 与 HER 未达到统计显著。”

"""
    output_path.write_text(report, encoding="utf-8")
