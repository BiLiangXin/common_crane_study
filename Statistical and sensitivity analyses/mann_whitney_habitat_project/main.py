
# -*- coding: utf-8 -*-
"""项目主入口：读取数据、预处理、重算指标、执行 Mann–Whitney 检验并导出报告。"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

import config
from src.io_utils import ensure_output_dir, read_excel_table, save_dataframe
from src.preprocess import preprocess_habitat_table, preprocess_corridor_table
from src.metrics import add_recalculated_habitat_metrics, build_habitat_qc_table
from src.analysis import build_group_counts, descriptive_stats_by_group, run_pairwise_mannwhitney, summarize_corridor_table
from src.reporting import write_results_report


def main() -> None:
    """
    执行完整分析流程。
    """
    ensure_output_dir(config.OUTPUT_DIR)

    # 1) 读入数据
    habitat_raw = read_excel_table(config.HABITAT_FILE, config.HABITAT_SHEET)
    corridor_raw = read_excel_table(config.CORRIDOR_FILE, config.CORRIDOR_SHEET)

    # 2) 预处理
    habitat_df = preprocess_habitat_table(habitat_raw, config)
    corridor_df = preprocess_corridor_table(corridor_raw, config)

    # 3) 指标重算与 QC
    if config.RECALCULATE_METRICS:
        habitat_df = add_recalculated_habitat_metrics(habitat_df, config)
        qc_df = build_habitat_qc_table(habitat_df, config)
        save_dataframe(qc_df, config.QC_DIFF_CSV)
    else:
        qc_df = pd.DataFrame()

    # 4) 描述性统计
    group_counts_df = build_group_counts(habitat_df, config.GROUP_COLUMN)
    descriptive_df = descriptive_stats_by_group(
        habitat_df,
        group_col=config.GROUP_COLUMN,
        metrics=config.ALL_TEST_METRICS,
    )

    # 5) Mann–Whitney U 检验
    mw_df = run_pairwise_mannwhitney(
        habitat_df,
        group_col=config.GROUP_COLUMN,
        group_a=config.GROUP_A,
        group_b=config.GROUP_B,
        metrics=config.ALL_TEST_METRICS,
        config_module=config,
    )

    # 6) 廊道描述性汇总
    corridor_summary_df = summarize_corridor_table(corridor_df)

    # 7) 导出结果
    save_dataframe(habitat_df, config.CLEAN_HABITAT_CSV)
    save_dataframe(corridor_df, config.CLEAN_CORRIDOR_CSV)
    save_dataframe(group_counts_df, config.GROUP_COUNTS_CSV)
    save_dataframe(descriptive_df, config.DESCRIPTIVE_STATS_CSV)
    save_dataframe(mw_df, config.MANN_WHITNEY_CSV)
    save_dataframe(corridor_summary_df, config.CORRIDOR_SUMMARY_CSV)

    # 8) 写 Markdown 结果报告
    write_results_report(
        output_path=config.RESULTS_REPORT_MD,
        group_counts_df=group_counts_df,
        descriptive_df=descriptive_df,
        mw_df=mw_df,
        corridor_df=corridor_summary_df,
        config_module=config,
    )

    print("分析完成。输出文件如下：")
    for path in [
        config.CLEAN_HABITAT_CSV,
        config.CLEAN_CORRIDOR_CSV,
        config.GROUP_COUNTS_CSV,
        config.DESCRIPTIVE_STATS_CSV,
        config.MANN_WHITNEY_CSV,
        config.QC_DIFF_CSV,
        config.CORRIDOR_SUMMARY_CSV,
        config.RESULTS_REPORT_MD,
    ]:
        print(f" - {path}")


if __name__ == "__main__":
    main()
