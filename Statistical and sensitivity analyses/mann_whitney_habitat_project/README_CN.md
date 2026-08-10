
# 灰鹤栖息地夜光暴露 Mann–Whitney 检验复现项目

## 1. 这个项目解决什么问题

这个项目专门复现并解释论文正文里提到的 **Mann–Whitney U 检验**，并把整套统计过程整理成一个可以直接复跑的 Python 工程。

它解决的是下面这个具体问题：

> 在你已经完成 ArcGIS/遥感提取之后，**关键停留地** 与 **临时停留地** 的夜光暴露水平是否存在统计学差异？

这一步的目标不是重新做 GPS 轨迹聚类，而是对你已经提取好的结果表进行：
1. 数据预处理；
2. 夜光指标重算与质量控制；
3. 描述性统计；
4. Mann–Whitney U 检验；
5. 多重比较校正；
6. 输出论文可直接引用的结果表。

---

## 2. 研究逻辑

整篇研究在统计层面可以拆成两层：

### 第一层：上游空间生态流程（你已经完成）
1. 基于 GPS 轨迹识别栖息地；
2. 将栖息地划分为繁殖地、越冬地、关键停留地、临时停留地；
3. 将 VNP46A4 夜光数据与栖息地面叠加；
4. 在每个栖息地上提取夜光连续统计量和各夜光等级面积；
5. 得到 `CLUSTER_fanganA.xlsx`；
6. 对高概率迁飞廊道提取 `CorridorExposure`，得到 `corrrider.xlsx`。

### 第二层：本项目负责的统计验证流程
1. 读取 `CLUSTER_fanganA.xlsx` 和 `corrrider.xlsx`；
2. 检查字段是否完整；
3. 将面积分级字段重新计算成 `HNLPI / PCR / HER / STD_HNLPI / ELS` 等指标；
4. 用 QC 表验证“原表字段”和“重算字段”是否完全一致；
5. 仅针对 **关键停留地 (n=6)** 与 **临时停留地 (n=10)** 做两独立样本比较；
6. 输出：
   - 描述性统计表；
   - Mann–Whitney 检验表；
   - 多重比较校正结果；
   - 廊道描述性汇总表；
   - 中文结果说明。

---

## 3. 为什么这里要用 Mann–Whitney U 检验

本数据有三个明显特征：

1. **组间样本量小**  
   繁殖地只有 1 个，越冬地只有 1 个；能正式比较的只有关键停留地和临时停留地。

2. **指标分布偏态、零值很多**  
   例如 PCR、HER、PCT90 等变量中存在大量 0，直接用 t 检验不稳。

3. **比较目标是两组独立样本整体水平是否不同**  
   也就是判断关键停留地这一组的值是否系统性高于临时停留地。

因此，采用两独立样本的 Mann–Whitney U 检验更合理。

---

## 4. 为什么代码里同时给两种 p 值

这个项目同时输出两种 p 值，是为了兼顾“论文复现”和“统计稳健性”。

### 4.1 `p_reference`
- 使用 **asymptotic** 方法；
- 这个值对应论文正文里写出的 p 值；
- 目的是让你可以逐项对照论文中的数字。

### 4.2 `p_primary`
- 使用 **permutation** 方法；
- 更适合当前这种“小样本 + 大量 ties/大量 0”的场景；
- 你这组数据的 6 vs 10 样本组合数可穷举，因此这里实际上做的是**精确重排**。

---

## 5. 本项目使用的主指标公式

记：
- `A` = 栖息地总面积
- `S1` = 0–0.5 面积（偏好环境）
- `S2` = 0.5–1 面积
- `S3` = 1–5 面积
- `S4` = 5–10 面积
- `S5` = 10+ 面积

则：

### 5.1 总夜光覆盖面积
`NTL_AREA = S2 + S3 + S4 + S5`

### 5.2 栖息地夜光污染指数
`HNLPI = (1*S2 + 2*S3 + 3*S4 + 4*S5) / A`

### 5.3 标准化栖息地夜光污染指数
`STD_HNLPI = HNLPI / 4`

### 5.4 污染覆盖率
`PCR = (S2 + S3 + S4 + S5) / A`

### 5.5 高暴露占比
`HER = (S4 + S5) / A`

### 5.6 夜光覆盖区内部平均暴露等级
`ELS = (1*S2 + 2*S3 + 3*S4 + 4*S5) / (4*NTL_AREA)`

---

## 6. 本次实际检验对象

### 主终点（primary endpoints）
- `PCR`
- `STD_HNLPI`
- `ELS`

### 支持性指标（secondary metrics）
- `MEAN`
- `PCT90`
- `HER`

---

## 7. 这次数据跑出来的核心结果

### 7.1 样本量
- 关键停留地：6
- 临时停留地：10
- 繁殖地：1
- 越冬地：1

### 7.2 主终点结果
- **PCR**  
  - U = 52.0  
  - 论文复现 p = 0.017929  
  - permutation p = 0.015485  
  - FDR-BH 校正后 p = 0.029720  
  - rank-biserial = 0.733333

- **STD_HNLPI**  
  - U = 51.0  
  - 论文复现 p = 0.024010  
  - permutation p = 0.021479  
  - FDR-BH 校正后 p = 0.029720  
  - rank-biserial = 0.700000

- **ELS**  
  - U = 49.5  
  - 论文复现 p = 0.035043  
  - permutation p = 0.029720  
  - FDR-BH 校正后 p = 0.029720  
  - rank-biserial = 0.650000

### 7.3 支持性指标
- **MEAN**：显著更高
- **PCT90**：未达显著
- **HER**：未达显著

### 7.4 结论
论文中“关键停留地夜光暴露显著高于临时停留地”的主结论是成立的，
而且在更稳健的 permutation 检验下仍然成立。

---

## 8. 为什么繁殖地和越冬地没有做 Mann–Whitney

因为两类样本量都只有 1，不能满足两独立样本推断检验的基本条件。
所以本项目只对 `关键停留地 vs 临时停留地` 做正式检验，
繁殖地和越冬地只做描述性解释。

---

## 9. 为什么廊道没有做 Mann–Whitney

`corrrider.xlsx` 里只有 3 行：
- 50% 廊道
- 75% 廊道
- 95% 廊道

它们是同一条廊道概率面的嵌套结果，不是独立样本重复。
因此这里应做描述性比较，而不是做 Mann–Whitney U 检验。

---

## 10. 项目目录结构

```text
mann_whitney_habitat_project/
├── config.py
├── main.py
├── requirements.txt
├── README_CN.md
├── API_CN.md
├── FIELD_DICTIONARY_CN.md
├── data/
│   ├── CLUSTER_fanganA.xlsx
│   └── corrrider.xlsx
├── src/
│   ├── __init__.py
│   ├── io_utils.py
│   ├── preprocess.py
│   ├── metrics.py
│   ├── stats_utils.py
│   ├── analysis.py
│   └── reporting.py
└── outputs/
    ├── cleaned_habitat_data.csv
    ├── cleaned_corridor_data.csv
    ├── group_counts.csv
    ├── group_descriptive_stats.csv
    ├── mannwhitney_results.csv
    ├── habitat_metric_qc_diff.csv
    ├── corridor_summary.csv
    └── results_report_CN.md
```

---

## 11. 如何运行

在项目目录下执行：

```bash
python main.py
```

如果你要改参数，直接修改 `config.py` 即可，最常改的包括：

- `GROUP_A`, `GROUP_B`
- `PRIMARY_METRICS`
- `SECONDARY_METRICS`
- `MW_PRIMARY_METHOD`
- `PRIMARY_P_ADJUST_METHOD`
- `ALPHA`

---

## 12. 你论文里可以怎么写

### 方法部分
由于繁殖地与越冬地样本量均为 1，正式统计推断仅针对关键停留地与临时停留地开展。
考虑到夜光暴露指标存在明显偏态分布及大量零值，采用两独立样本 Mann–Whitney U 检验比较
两类栖息地在 PCR、STD_HNLPI、ELS 及支持性夜光指标上的差异。
为与正文结果保持一致，同时报告 asymptotic p 值；考虑到样本量较小且存在 ties，
进一步采用置换法计算稳健 p 值，并对主终点进行 FDR-BH 校正。

### 结果部分
关键停留地的 PCR、STD_HNLPI 和 ELS 均显著高于临时停留地，
且在 permutation 检验及主终点 FDR-BH 校正后仍保持显著，
说明关键停留地整体暴露于更高的夜光污染环境中。

