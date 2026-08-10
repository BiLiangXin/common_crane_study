
# 字段说明（FIELD DICTIONARY）

## 一、输入文件 1：`CLUSTER_fanganA.xlsx`

### 原始字段说明

| 字段名 | 含义 | 单位/类型 | 说明 |
|---|---|---|---|
| OBJECTID | 栖息地样地唯一编号 | 整数 | 每个栖息地面一个编号 |
| event_type | 栖息地类型 | 文本 | 繁殖地 / 越冬地 / 关键停留地 / 临时停留地 |
| MIN | 栖息地内夜光最小值 | nW·cm⁻²·sr⁻¹ | ArcGIS 分区统计结果 |
| MAX | 栖息地内夜光最大值 | nW·cm⁻²·sr⁻¹ | ArcGIS 分区统计结果 |
| RANGE | 极差 | nW·cm⁻²·sr⁻¹ | MAX - MIN |
| MEAN | 平均夜光辐亮度 | nW·cm⁻²·sr⁻¹ | ArcGIS 分区统计结果 |
| STD | 标准差 | nW·cm⁻²·sr⁻¹ | 栖息地内夜光离散程度 |
| SUM | 夜光总和 | 数值 | 分区统计累计值 |
| MEDIAN | 中位数 | nW·cm⁻²·sr⁻¹ | 栖息地内夜光中位数 |
| PCT75 | 75 分位数 | nW·cm⁻²·sr⁻¹ | 上四分位 |
| PCT90 | 90 分位数 | nW·cm⁻²·sr⁻¹ | 用于表征局部高亮斑块 |
| PCT95 | 95 分位数 | nW·cm⁻²·sr⁻¹ | 更强调极亮区域 |
| AREA | 栖息地总面积 | m² | 栖息地面真实面积 |
| 0_0.5 | 0–0.5 夜光等级面积 | m² | 偏好环境面积 |
| 0.5_1 | 0.5–1 夜光等级面积 | m² | 潜在影响区面积 |
| 1_5 | 1–5 夜光等级面积 | m² | 明确干扰（低暴露）面积 |
| 5_10 | 5–10 夜光等级面积 | m² | 中度暴露面积 |
| 10+ | >10 夜光等级面积 | m² | 高暴露面积 |
| HNLPI | 栖息地夜光污染指数 | 比值 | `(1*S2 + 2*S3 + 3*S4 + 4*S5) / A` |
| PCR | 污染覆盖率 | 比值 | `(S2 + S3 + S4 + S5) / A` |
| HER | 高暴露占比 | 比值 | `(S4 + S5) / A` |
| STD_HNLPI | 标准化栖息地夜光污染指数 | 0–1 | `HNLPI / 4` |
| NTL_AREA | 夜光覆盖总面积 | m² | `S2 + S3 + S4 + S5` |
| P1 | 夜光覆盖区中 0.5–1 的比例 | 比值 | `S2 / NTL_AREA` |
| P2 | 夜光覆盖区中 1–5 的比例 | 比值 | `S3 / NTL_AREA` |
| P3 | 夜光覆盖区中 5–10 的比例 | 比值 | `S4 / NTL_AREA` |
| P4 | 夜光覆盖区中 >10 的比例 | 比值 | `S5 / NTL_AREA` |
| HER_LIT | 夜光覆盖区内部高暴露占比 | 比值 | `(S4 + S5) / NTL_AREA` |
| ELS | 夜光覆盖区平均暴露等级 | 0–1 | `(1*S2 + 2*S3 + 3*S4 + 4*S5) / (4*NTL_AREA)` |

### 本项目新增字段（`cleaned_habitat_data.csv` 里会出现）

| 字段名 | 含义 |
|---|---|
| NTL_AREA_calc | 根据面积字段重新计算得到的夜光覆盖总面积 |
| HNLPI_calc | 根据面积字段重算的 HNLPI |
| PCR_calc | 根据面积字段重算的 PCR |
| HER_calc | 根据面积字段重算的 HER |
| STD_HNLPI_calc | 根据面积字段重算的 STD_HNLPI |
| P1_calc | 根据面积字段重算的 P1 |
| P2_calc | 根据面积字段重算的 P2 |
| P3_calc | 根据面积字段重算的 P3 |
| P4_calc | 根据面积字段重算的 P4 |
| HER_LIT_calc | 根据面积字段重算的 HER_LIT |
| ELS_calc | 根据面积字段重算的 ELS |

---

## 二、输入文件 2：`corrrider.xlsx`

| 字段名 | 含义 | 单位/类型 | 说明 |
|---|---|---|---|
| OBJECTID_1 | 廊道百分位等级 | 数值 | 0.50 / 0.75 / 0.95 |
| COUNT | 栅格像元数 | 整数 | 对应廊道面内的像元个数 |
| AREA | 廊道面积 | m² | 高概率廊道总面积 |
| CorridorExposure | 廊道期望夜光暴露指数 | 数值 | 由密度面和夜光面叠加得到 |

### 本项目清洗后字段（`cleaned_corridor_data.csv`）

| 字段名 | 含义 |
|---|---|
| corridor_percentile | 廊道概率等级 |
| count | 像元数 |
| area_m2 | 廊道面积（m²） |
| corridor_exposure | 廊道期望夜光暴露指数 |

---

## 三、输出文件字段说明

### 1）`group_counts.csv`

| 字段名 | 含义 |
|---|---|
| event_type | 栖息地类型 |
| n_sites | 该类型样地数量 |

### 2）`group_descriptive_stats.csv`

| 字段名 | 含义 |
|---|---|
| group | 组名 |
| metric | 指标名 |
| n | 样本数 |
| mean | 均值 |
| sd | 标准差 |
| median | 中位数 |
| q1 | 25 分位数 |
| q3 | 75 分位数 |
| min | 最小值 |
| max | 最大值 |

### 3）`mannwhitney_results.csv`

| 字段名 | 含义 |
|---|---|
| metric | 指标名 |
| group_a | 第一组（默认关键停留地） |
| group_b | 第二组（默认临时停留地） |
| n_a / n_b | 两组样本量 |
| mean_a / mean_b | 两组均值 |
| sd_a / sd_b | 两组标准差 |
| median_a / median_b | 两组中位数 |
| q1_a / q3_a | 第一组四分位数 |
| q1_b / q3_b | 第二组四分位数 |
| u_statistic | Mann–Whitney U 统计量 |
| p_reference | 论文复现用 p 值（asymptotic） |
| p_primary | 推荐报告的 p 值（permutation） |
| reference_method | 复现方法名称 |
| primary_method | 主分析方法名称 |
| has_ties | 合并后是否存在 ties |
| cles | Common-Language Effect Size |
| rank_biserial | 秩二列相关效应量 |
| mean_diff_a_minus_b | 均值差 |
| median_diff_a_minus_b | 中位数差 |
| hodges_lehmann_shift | Hodges–Lehmann 位移估计 |
| is_primary_metric | 是否为主终点 |
| p_adjust_method | 多重比较校正方法 |
| p_adjusted_primary | 主终点校正后 p 值 |
| reject_primary | 在给定 alpha 下是否拒绝原假设 |

### 4）`habitat_metric_qc_diff.csv`

| 字段名 | 含义 |
|---|---|
| OBJECTID | 样地编号 |
| event_type | 样地类型 |
| metric_name | 被校验的指标名 |
| raw_value | 原始表中的值 |
| recalculated_value | 代码重算值 |
| abs_diff | 绝对差 |
| within_tolerance | 是否在容差内一致 |

### 5）`corridor_summary.csv`

| 字段名 | 含义 |
|---|---|
| corridor_percentile | 廊道百分位等级 |
| count | 像元数 |
| area_m2 | 面积（m²） |
| corridor_exposure | 廊道期望夜光暴露 |
| area_km2 | 面积（km²） |
| delta_area_vs_prev_pct | 相对上一层廊道的面积变化率 |
| delta_exposure_vs_prev_pct | 相对上一层廊道的暴露变化率 |
| delta_area_vs_50_pct | 相对 50% 廊道的面积变化率 |
| delta_exposure_vs_50_pct | 相对 50% 廊道的暴露变化率 |

### 6）`results_report_CN.md`

这是自动生成的中文结果说明文档，包含：
- 研究目的；
- 为什么用 Mann–Whitney；
- 各组样本量；
- 主终点和支持性指标结果；
- 廊道结果解释；
- 可直接写进论文的方法和结果段落。
