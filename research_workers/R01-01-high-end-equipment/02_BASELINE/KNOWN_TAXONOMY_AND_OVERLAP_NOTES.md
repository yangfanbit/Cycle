# KNOWN_TAXONOMY_AND_OVERLAP_NOTES.md

> **只读说明文件。** 描述当前已知的**命名交叉**与**边界争议**。
> 目的：让 Research Worker **提前知道**哪里容易撞车，从而**主动标记** overlap / boundary，
> 而不是**自行裁决**。

- **source_threec_commit**: `2153f6d83b7481300696ab73d792e9e53aa31a07`
- **本任务**: `R01-01`

---

## 1. 核心纪律

> ## Research Worker **可以**提出 `proposal` / `overlap` / `boundary`；
> ## 但 **Macro Theme canonicalization 只能由 ThreeC Agent 的 CMTR v1 完成**。

- CMTR v1 唯一实现：`theme_taxonomy.py`（ThreeC 侧）
- 规则集标识：`canonical-macro-theme-resolution-1`
- **唯一事实来源是 DB `themes` 表**。不接受任何硬编码的「主题族名称表」。
- 名称无法解析时**不静默丢弃** —— 必须显式报告（`UNRESOLVED_NAME` / `unmatched_names`）
- Research Worker **不得**自行发明第二套 Macro Theme Resolution

**正确做法**：提交 `macro_theme_proposals` + `theme_name_candidates`（原始名称），
让 ThreeC Agent 去解析。

---

## 2. 已知交叉：AI / 算力 / 半导体 / 计算机 / 通信 / 机器人 / 高端装备

这 8 个名称之间存在**明显交叉**：

```text
AI · 算力 · 大模型 · 半导体 · 电子 · 计算机 · 通信 · 机器人 · 高端装备
```

### ⚠️ 严禁

**不得**未经判断就把它们**全部**设成新的 Macro Theme。

### 允许的表达层级

| 层级 | 示例 |
|---|---|
| **Theme**（子主题） | 「智能驾驶/无人驾驶」挂 `汽车` 下 |
| **子主题** | 「光模块/高速光互联」挂 `信息通信` 下 |
| **Cross-family research candidate** | 一个 Campaign 的 `theme_name_candidates` 跨越两个族 → 交 CMTR 判定 |
| **Mechanism**（机制轴） | `TECH_BREAKTHROUGH` 是**机制**，不是 Macro Theme |

### 具体交叉关系

| 交叉 | 说明 |
|---|---|
| **AI / 算力 ↔ 半导体 / 计算机 / 通信** | 「算力」不是行业，是**需求侧机制**。同一波行情可能同时落在半导体、光模块、服务器、IDC 上 |
| **半导体 ↔ 电子** | 是否应为一个 Macro Theme —— 交 CMTR v1 判定 |
| **半导体 ↔ 信息通信** | `C-2023-COMM-OPTICAL`（光模块）与半导体设备/材料在产业链上相邻 |
| **半导体设备 ↔ 高端装备** | 半导体设备属装备制造，边界争议 |
| **机器人 ↔ 高端装备** | 「机器人」是独立 Macro Theme，还是「高端装备」下的 Theme / 子主题 —— 交 CMTR 判定 |
| **工业自动化 ↔ 机器人** | 是否同一底层主题的不同命名（**Q1 Anti-example 风险**） |
| **计算机 ↔ 信息通信** | 历史上常被合并为「TMT」，但机制可分离 |

---

## 3. 已知交叉：其它

| 交叉 | 说明 |
|---|---|
| **新能源汽车 ↔ 能源金属** | `C-2020-NEV` / `C-2021-NEV` 与锂钴镍价格周期高度耦合。能源金属行情究竟属「汽车」「电力设备」还是「资源」—— **跨族边界，必须交 ThreeC Agent** |
| **半导体材料 ↔ 化工** | 硅片 / 光刻胶 / 电子特气既是半导体材料也是化工品 |
| **军工电子 ↔ 半导体** | 军工电子与半导体元器件在企业和产品上重叠 |
| **军民两用装备 ↔ 高端装备** | 部分装备制造企业同时具备军民两用属性 |
| **地产后周期 ↔ 消费** | 家电 / 家居 / 建材同时受地产周期与消费需求影响 |
| **建材 ↔ 化工 / 基建** | 「建材」属「地产链」还是独立行业，存在歧义 |
| **流动性 ↔ 市场 Beta** | ★ **风险最高**：全市场行情极易被误判为「金融 Campaign」。无法排除 Beta Contamination 时必须**保持低置信度** |
| **消费医疗 ↔ 医药健康 / 消费** | 医疗服务 / 医美 的归属存在争议 |
| **农业 ↔ 化工（农化）** | 猪周期是否属「历史机会 Campaign」还是「自然周期」—— 需明确判据 |
| **卫星互联网 ↔ 信息通信 / 军工** | 通信属性与国防属性并存 |

---

## 4. 本任务（`R01-01`）已知 overlap

- R01-02（半导体/电子）：自动化设备的电子元器件与工控芯片边界
- R01-06（军工）：部分装备制造企业同时具备军民两用属性
- 已有 family「汽车」：`C-2024-ROBOTAXI` / `C-2025-ROBOTAXI` 与「机器人」在叙事上相邻
- 已有 family「电力设备」：工控与电力自动化存在企业重叠

---

## 5. 本任务（`R01-01`）已知 ambiguity

- 「机器人」是独立 Macro Theme，还是「高端装备」下的 Theme / 子主题 —— 必须交 CMTR v1 判定，不得自行决定
- 「人形机器人」2023–2025 的多次行情是否属同一 Campaign（需走 Independence Gate Q1–Q5）
- 「工业自动化」与「机器人」是否同一底层主题的不同命名（Q1 Anti-example 风险）

---

## 6. 处理方式

发现交叉时，**不要自行裁决**。按下列方式之一记录：

| 情形 | 记录方式 |
|---|---|
| 只是命名相似 | `cross_task_notes` → `OVERLAP` |
| 可能是同一底层对象 | `campaign_candidates[].possible_duplicate_of` |
| 边界争议 | `cross_task_notes` → `BOUNDARY` |
| 主题归属不明 | `macro_theme_proposals` + `theme_name_candidates` |
| 发现跨任务重叠 | `cross_task_notes` → `POSSIBLE_DUPLICATE` / `HANDOFF` |

> **宁可重复提交，也不要因为可能重复而删除候选。**
