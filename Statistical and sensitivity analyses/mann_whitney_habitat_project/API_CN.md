
# API 文档（中文）

## 一、入口脚本

### `main.py`

#### `main() -> None`
执行完整流程：

1. 读取 Excel；
2. 预处理；
3. 重算夜光指标；
4. 输出 QC 表；
5. 计算描述性统计；
6. 执行 Mann–Whitney U 检验；
7. 生成廊道汇总；
8. 导出 CSV 和 Markdown 报告。

---

## 二、模块：`src/io_utils.py`

### `ensure_output_dir(output_dir: Path) -> None`
确保输出目录存在。

### `resolve_sheet_name(excel_path: Path, preferred_sheet: Optional[str] = None) -> str`
选择实际读取的 sheet 名：
- 如果 `preferred_sheet` 存在，优先用它；
- 否则读取第一个 sheet。

### `read_excel_table(excel_path: Path, preferred_sheet: Optional[str] = None) -> pd.DataFrame`
读取 Excel 工作表为 DataFrame。

### `save_dataframe(df: pd.DataFrame, output_path: Path) -> None`
将 DataFrame 保存为 UTF-8-SIG 编码 CSV。

---

## 三、模块：`src/preprocess.py`

### `standardize_column_names(df: pd.DataFrame) -> pd.DataFrame`
清洗列名，去首尾空格。

### `validate_required_columns(df: pd.DataFrame, required_columns: Iterable[str], table_name: str) -> None`
检查输入表是否缺字段。
- 若缺字段，抛出 `ValueError`。

### `coerce_numeric(df: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame`
将指定列强制转为数值型。

### `preprocess_habitat_table(df: pd.DataFrame, config_module) -> pd.DataFrame`
预处理栖息地表：
- 列名标准化；
- 字段检查；
- 数值转换；
- `event_type` 清洗；
- 按 `OBJECTID` 排序。

### `preprocess_corridor_table(df: pd.DataFrame, config_module) -> pd.DataFrame`
预处理廊道表：
- 列名标准化；
- 字段检查；
- 字段重命名；
- 数值转换；
- 按概率等级排序。

---

## 四、模块：`src/metrics.py`

### `safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series`
安全除法：
- 分母为 0 时返回 0；
- 避免生成 `inf` 和 `NaN`。

### `add_recalculated_habitat_metrics(df: pd.DataFrame, config_module) -> pd.DataFrame`
根据面积分级字段重新计算：
- `NTL_AREA_calc`
- `HNLPI_calc`
- `PCR_calc`
- `HER_calc`
- `STD_HNLPI_calc`
- `P1_calc`
- `P2_calc`
- `P3_calc`
- `P4_calc`
- `HER_LIT_calc`
- `ELS_calc`

### `build_habitat_qc_table(df_with_calc: pd.DataFrame, config_module) -> pd.DataFrame`
对“原始字段 vs 重算字段”逐项比较，输出 QC 明细表。

---

## 五、模块：`src/stats_utils.py`

### `pooled_has_ties(x: np.ndarray, y: np.ndarray) -> bool`
判断两组数据合并后是否存在 ties。

### `common_language_effect(u_statistic: float, n1: int, n2: int) -> float`
计算 CLES：
- 表示从组 A 随机抽一个值大于组 B 随机抽一个值的概率。

### `rank_biserial_from_u(u_statistic: float, n1: int, n2: int) -> float`
根据 U 统计量计算 rank-biserial correlation。

### `hodges_lehmann_shift(x: np.ndarray, y: np.ndarray) -> float`
计算两独立样本的 Hodges–Lehmann 位移估计。

### `choose_mw_method(x: np.ndarray, y: np.ndarray, config_module, mode: str)`
根据配置生成 `scipy.stats.mannwhitneyu` 的 `method` 参数。

支持：
- `"permutation"`
- `"manuscript_asymptotic"`
- `"exact"`
- `"auto"`

### `run_mann_whitney_single_metric(...) -> dict`
对一个指标执行 Mann–Whitney U 检验，并输出完整结果字典：

**输入**
- `x`, `y`：两组样本
- `metric_name`：指标名
- `group_a`, `group_b`：组名
- `config_module`：配置模块

**输出**
- U 统计量
- 复现 p 值
- 推荐 p 值
- 是否有 ties
- CLES
- rank-biserial
- 中位数差
- 均值差
- Hodges–Lehmann shift

### `adjust_primary_pvalues(result_df, config_module)`
对主终点的 `p_primary` 做多重比较校正。

---

## 六、模块：`src/analysis.py`

### `build_group_counts(df: pd.DataFrame, group_col: str) -> pd.DataFrame`
统计各组样本数。

### `descriptive_stats_by_group(df: pd.DataFrame, group_col: str, metrics: list[str]) -> pd.DataFrame`
按组、按指标计算：
- n
- mean
- sd
- median
- q1
- q3
- min
- max

### `run_pairwise_mannwhitney(...) -> pd.DataFrame`
对指定两组、多个指标批量执行 Mann–Whitney U 检验。

**输入**
- `df`
- `group_col`
- `group_a`
- `group_b`
- `metrics`
- `config_module`

**输出**
- 每个指标一行的检验结果表。

### `summarize_corridor_table(df: pd.DataFrame) -> pd.DataFrame`
对廊道结果做描述性汇总，并计算：
- 相对上一层廊道的面积变化率；
- 相对上一层廊道的暴露变化率；
- 相对 50% 廊道的面积变化率；
- 相对 50% 廊道的暴露变化率。

---

## 七、模块：`src/reporting.py`

### `_fmt(value, digits=6)`
内部格式化函数。

### `dataframe_to_markdown(df: pd.DataFrame, digits: int = 6) -> str`
将 DataFrame 转成 Markdown 表格。

### `write_results_report(...) -> None`
自动生成中文结果报告。

**输入**
- `output_path`
- `group_counts_df`
- `descriptive_df`
- `mw_df`
- `corridor_df`
- `config_module`

**输出**
- `results_report_CN.md`

---

## 八、配置模块：`config.py`

`config.py` 是整个项目的总控文件，建议优先修改以下参数：

### 输入/输出
- `HABITAT_FILE`
- `HABITAT_SHEET`
- `CORRIDOR_FILE`
- `CORRIDOR_SHEET`
- `OUTPUT_DIR`

### 组别设置
- `GROUP_COLUMN`
- `GROUP_A`
- `GROUP_B`

### 指标设置
- `PRIMARY_METRICS`
- `SECONDARY_METRICS`
- `ALL_TEST_METRICS`

### Mann–Whitney 设置
- `MW_PRIMARY_METHOD`
- `MW_REFERENCE_METHOD`
- `MW_ALTERNATIVE`
- `MW_USE_CONTINUITY`
- `MW_PERMUTATION_RESAMPLES`
- `MW_RANDOM_STATE`

### 多重比较
- `PRIMARY_P_ADJUST_METHOD`
- `ALPHA`

### 数据校验
- `RECALCULATE_METRICS`
- `FLOAT_TOLERANCE`

---

## 九、最常见的二次开发方式

### 1）改比较组
只改 `config.py`：
- `GROUP_A`
- `GROUP_B`

### 2）改主终点
只改：
- `PRIMARY_METRICS`

### 3）改统计方法
- 复现论文正文：`MW_REFERENCE_METHOD = "manuscript_asymptotic"`
- 更稳健的小样本方案：`MW_PRIMARY_METHOD = "permutation"`

### 4）只输出描述性统计，不做检验
可以在 `main.py` 里注释掉 `run_pairwise_mannwhitney(...)` 那一段。

### 5）加新的夜光指标
如果新指标来自面积分级，可在 `src/metrics.py` 里新增公式；
如果只是已有列，可以直接在 `config.ALL_TEST_METRICS` 中加入列名。
