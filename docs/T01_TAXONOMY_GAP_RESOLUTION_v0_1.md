# T01 — Historical Universe Taxonomy Gap Resolution v0.1

> **性质**：ThreeC **独立 taxonomy 数据决策轮次**（R00 治理要求：taxonomy 补录属独立轮次，不在 R01 内自动新增）。
> **状态**：**完成**。DB `themes` 表 19 → 52 行；Macro Theme 根节点 4 → **11**。
> **边界**：**只改 `themes` taxonomy 数据**。Campaign / Evidence / Lifecycle / 其它任何表 **零改动**。
> **CMTR v1（`research/scripts/theme_taxonomy.py`）未被修改**；未建立第二套 resolution。

---

## 1. 问题

R01-01 的 canonicalization 被 taxonomy gap 阻断：

```
CMTR v1 → UNRESOLVED_NAME（MT001–MT005 全部）
```

DB `themes` 表（19 行）中不存在 高端装备 / 机器人 / 工业自动化 / 工程机械 /
轨道交通装备 / 半导体 / 电子 / 有色金属 / 基础化工 / 消费 / 金融 / 房地产 / 国防军工 …
**任何**一行。候选级 15 个 `theme_name_candidates` **0 matched**。

R01-02 ~ R01-06 在 Task Manifest 中声明的 `macro_theme_candidates`（共 30 个名称）
同样全部无法解析 —— 即 **整个 R01 轮次都被阻断**，而不只是 R01-01。

---

## 2. 设计原则

> **Macro Theme root = 机制家族（mechanism family）**，用于 ThreeC 的**跨族结构比较**。

因此 root 的划分依据是**驱动机制是否同族**，而不是「行业分类是否同级」。

- **root** = 一个可独立比较的机制家族
- **子主题** = 该家族内可分辨的结构
- **深度不限**（既有 `TH-AUTO → TH-NEV → TH-TESLA-CHAIN` 已为 3 层）
- **别名不建行**（CMTR 对重名一律视为不可解析；别名保留在 `unmatched_names` 中如实报告）

### 为什么不是「机械按行业分类建根」

若按申万一级逐级建根（31 个），跨族比较会退化为「每个子行业都是自己的族」，
`CROSS_MACRO_THEME` 将失去意义。R00 coverage plan 的目标是 **~10 个机制家族**，
本决策最终落到 **11 个根**。

---

## 3. 决策表 —— 新增 33 行

### 3.1 新增 root（7）

| theme_id | name | type | 机制家族 |
|---|---|---|---|
| `TH-HIEQ` | **高端装备** | industry | 制造业资本开支 / 设备更新 / 产业政策 |
| `TH-ELEC` | **电子** | industry | 国产替代 / 技术周期 / 资本开支 |
| `TH-RES` | **资源** | industry | **供给收缩 / 成本驱动的价格周期**（原 4 族完全缺失） |
| `TH-CONSUMER` | **消费** | industry | **纯需求端驱动**（原 4 族完全缺失） |
| `TH-FIN` | **金融** | industry | **流动性 / 市场 Beta**（原 4 族完全缺失） |
| `TH-REALESTATE` | **房地产** | industry | **地产政策周期 + 地产链需求** |
| `TH-DEFENSE` | **国防军工** | industry | **订单 / 事件驱动**（原 4 族完全缺失） |

> **新增根覆盖了 R00 coverage plan 诊断出的四条缺失机制轴** —— 这正是本轮 taxonomy 扩容的真正目的。

### 3.2 子主题（26）

| 父 | 子主题 |
|---|---|
| `TH-HIEQ` 高端装备 | 工程机械 · 工业自动化 · **机器人**（→ **人形机器人**）· 轨道交通装备 |
| `TH-ELEC` 电子 | **半导体**（→ 半导体设备 · 半导体材料）· 面板/显示 |
| `TH-RES` 资源 | **有色金属**（→ 贵金属 · 稀有金属/稀土）· **基础化工**（→ 农化） |
| `TH-CONSUMER` 消费 | 食品饮料 · 家用电器 · 农林牧渔 · 社会服务 |
| `TH-FIN` 金融 | 银行 · 非银金融 |
| `TH-REALESTATE` 房地产 | 房地产开发 · 建筑材料 |
| `TH-DEFENSE` 国防军工 | 航空装备 · 航天装备 · 船舶制造 · 军工电子 |

### 3.3 明确**不创建**（保留为 unresolved proposal / 别名）

| 名称 | 理由 |
|---|---|
| 机器人（作为 root） | SUB_THEME 已足以承接；独立成 root 会与「汽车」下的 Robotaxi/智能驾驶 产生**跨族冲突** |
| 半导体 / 半导体设备 / 半导体材料（作为 root） | 「电子」下的层级（半导体 → 设备/材料，3 层） |
| 银行 / 非银金融（作为 root） | 「金融」下的子主题 —— **不机械按行业分类建根** |
| 贵金属 / 稀有金属·稀土（作为 root） | 「有色金属」下的子主题 |
| 农化（作为 root） | 「基础化工」下的子主题 |
| 航空装备 / 航天装备 / 船舶制造 / 军工电子（作为 root） | 「国防军工」下的子主题 |
| 食品饮料 / 家用电器 / 农林牧渔 / 社会服务（作为 root） | 「消费」下的子主题 |
| 建筑材料（作为 root） | 「房地产」下的地产链子主题 |
| **工业机器人** | ★ **刻意不建** —— R01-01 已把「机器人 vs 工业自动化」的 Q1 Anti-example 风险记为 `CF007 UNRESOLVED`；建立该行会**预先坐实一个尚未裁决的区分** |
| 装备制造 / 高端装备制造 / 挖掘机 / 建筑机械 / 工控设备 / 自动化设备 / 通用自动化 / 轨交设备 / 铁路装备 / 具身智能 / 机器人+ / 设备更新 | **别名 / 政策项目名**，非独立主题；保留在 `unmatched_names` 中如实报告 |

---

## 4. 五组特别审查

### A. `高端装备` / `机器人` / `工业自动化` / `工程机械`

**不全部合并，也不全部拆开。** 采用「**1 根 + 4 子**」：

- `高端装备` 成为 root（MT001 是 5 个提案中**唯一** `NEW_MACRO_CANDIDATE`）
- 其余 4 个按各自提案的 `SUB_THEME` 归属置于其下
- **机器人不独立成 root** 的理由：会与「汽车」下的 `TH-ROBOTAXI` / `TH-AD` 产生跨族冲突
  （Robotaxi 与机器人共享产业链环节），且 R00 coverage plan 明确警告过该交叉
- **工程机械不并入工业自动化**：驱动机制不同（设备更新+基建+环保 vs 制造业资本开支+渗透率），
  生命周期不同步（工程机械 2021Q1 见顶时工业自动化仍处景气）→ 见 R01-01 `CF004` / `MT004` rationale

### B. `半导体` / `电子` / `半导体设备`

明确 **3 层**：

```
电子（root）
└─ 半导体
   ├─ 半导体设备
   └─ 半导体材料
   面板/显示（与半导体同级，挂 电子）
```

- `电子` 为 root（申万一级口径，与既有 root 风格一致）
- `半导体设备` **不归入「高端装备」** —— 其买方为晶圆厂（资本开支周期），
  与通用装备的买方（制造业）机制不同 → 见 R01-01 `CT001` 边界声明

### C. `有色金属` / `基础化工` / `贵金属` / `稀土`

- **`资源` 作为单一 root**：四者的共同机制是**供给/成本驱动的价格周期** ——
  正是 R00 诊断出的**缺失机制轴**。合并为一个家族使该机制的跨族比较成为可能。
- `有色金属` / `基础化工` 为子主题；`贵金属` / `稀有金属·稀土` 挂 `有色金属`；`农化` 挂 `基础化工`
- **贵金属不独立成 root**：其货币/避险机制由 Campaign 级 `drivers` 表达，不需要单独的家族轴

### D. `金融` / `房地产` / `银行` / `非银金融`

★ 本组是**唯一偏离** R00 coverage plan「金融 / 地产」单一方向的决策。

- **拆为 2 个 root**：`金融`（流动性 / 市场 Beta）与 `房地产`（地产政策周期 + 地产链）
- 理由：R00 coverage plan 把「金融/地产」列为**任务方向**，不是 taxonomy 强制。
  合并会让**Beta Contamination 风险在结构上不可见** —— 而 R01-05 的
  `known_ambiguity` 明确指出该风险「最高」。独立成族使「券商行情是否只是市场 Beta」
  成为一个**可被结构比较检验**的问题。
- `银行` / `非银金融` **不建 root**（§4.D 明确要求「不要机械按行业分类建立根节点」）
- `建筑材料` 挂 `房地产`（地产链），不挂「资源」

### E. `国防军工` / `航空装备` / `航天装备` / `船舶制造` / `军工电子`

- **`国防军工` 单一 root**，5 个名称中 4 个为子主题
- 机制为**订单 / 事件驱动**（采购与订单节奏），与「政策驱动」需区分 —— 本族使其可被比较
- `船舶制造` 归 `国防军工`（军民两用，含民用造船周期），**不归「高端装备」** ——
  与 R01-06 manifest 的分配一致
- `军工电子` 为 `concept`（买方为军方，与「电子」的国产替代机制不同）

---

## 5. 执行与边界验证

**应用器**：`research/scripts/apply_taxonomy_t01_v0_1.py`（幂等 · 可 `--dry-run` / `--verify`）

```bash
python research/scripts/apply_taxonomy_t01_v0_1.py --dry-run   # 33 行待新增
python research/scripts/apply_taxonomy_t01_v0_1.py             # 应用
python research/scripts/apply_taxonomy_t01_v0_1.py --verify    # PASS
```

### 零副作用验证（对比应用前备份）

| 项 | 结果 |
|---|---|
| 既有 19 行 `themes` | **被改动：无** ✓ |
| 新增 `themes` 行 | 33 |
| `campaigns` 13 · `campaign_themes` 31 · `evidences` 83 · `campaign_evidences` 76 | **全部不变** ✓ |
| `events` 49 · `campaign_events` 42 · `securities` 48 · `campaign_securities` 51 | **全部不变** ✓ |
| `sources` 85 · `research_rules` 4 · `annual_reviews` 28 · `campaign_phases` 48 | **全部不变** ✓ |
| `market_series` 56 · `market_daily` 79466 · `trading_calendar` 371 · `campaign_date_observations` 24 | **全部不变** ✓ |

**幂等性**：重复运行 → 「将新增 0 行；已存在跳过 33 行」✓

### Provenance

每行的 `themes.description` 携带：

```text
<机制家族定位>【T01 taxonomy 决策｜来源：R01-0X <MT00X / manifest macro_theme_candidates>】
```

决策全文见本文件；应用器内含完整决策表（`NEW_THEMES`）与**不创建清单**（`NOT_CREATED`）。

---

## 6. 验证结果

| 检查 | 结果 |
|---|---|
| `validate_db` | **PASS** |
| `validate_timeline_export` | **PASS** |
| `validate_batch_research` | **PASS** |
| `validate_promotion_manifest` | **PASS** |
| `check_doc_schema_consistency` | **PASS** |
| `validate_current_research` | **PASS** |
| `validate_monorepo_integrity` | **PASS**（25 项） |
| `refresh --check` | **PASS** |
| intake `--check` | **PASS** |

> ⚠️ 任务书 §7 写的 `research/scripts/monorepo_integrity.py` **路径不存在**；
> 真实位置为仓库根 **`scripts/validate_monorepo_integrity.py`**。

**既有历史研究未被破坏**：所有 validator 通过，且上表已逐表确认零改动。

---

## 7. §8 返回 R01-01 —— CMTR v1 复跑

### 根节点（11）

```
['信息通信', '医药健康', '国防军工', '房地产', '汽车', '消费', '电力设备', '电子', '资源', '金融', '高端装备']
```

### 提案级

| proposal | 原状态 | **现状态** | 解析根 |
|---|---|---|---|
| `MT001` 高端装备 | UNRESOLVED_NAME | **RESOLVED** | 高端装备 |
| `MT002` 机器人 | UNRESOLVED_NAME | **RESOLVED** | 高端装备 |
| `MT003` 工业自动化 | UNRESOLVED_NAME | **RESOLVED** | 高端装备 |
| `MT004` 工程机械 | UNRESOLVED_NAME | **RESOLVED** | 高端装备 |
| `MT005` 轨道交通装备 | UNRESOLVED_NAME | **RESOLVED** | 高端装备 |

### 候选级（7/7 全部 RESOLVED）

| candidate | 状态 | 解析根 |
|---|---|---|
| `R01-HIEQ-001` 工程机械 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-002` 工业机器人下行 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-003` 工业自动化复苏 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-004` 机器人+政策 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-005` 人形机器人叙事 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-006` 设备更新政策 | **RESOLVED** | 高端装备 |
| `R01-HIEQ-007` 人形机器人量产 | **RESOLVED** | 高端装备 |

> **`UNRESOLVED_NAME` 已全部消除 → R01-01 的 taxonomy 阻塞解除。**
> 剩余 `unmatched_names`（装备制造 / 挖掘机 / 工控设备 / 具身智能 / 机器人+ / 设备更新 …）
> 均为**别名或政策项目名**，按 §3.3 保留为 unresolved proposal —— 这是 CMTR v1 的**设计行为**
> （`has_taxonomy_gap` 会如实标记「已解析出根，但仍有名称未解析」）。

---

## 8. 未决与后续

### 本轮**未**做的事（严格边界）

- 未决定任何 Campaign · **未导入 R01-01 Campaign** · 未修改 R01-01 candidate
- 未修改 Research Model v1.0 · schema · Structural Analogy Rule Set v0.2 · Time Observation v0.5
- 未创建 ranking / score / probability / prediction
- **未启动 R01-02**

### 解除阻塞后仍待处理

1. **R01-01 Import**（§8.5）：5 个 `PROMOTE` 候选 + 2 个 `RESEARCH_ONLY` + 41 证据 + 35 来源 +
   17 证券（合并 `SEC017`/`SEC008`）+ 新 `research_rules` 1 行 + `annual_reviews` +
   `campaign_*` 桥表 + `events`
2. **Export**：`exports/timeline_export_v1.json` 由 `research/scripts/batch_auto_research.py` 生成，
   该脚本含**硬编码** `RULES`(L39) / `RULE_META` / `CAMPAIGN_LIFECYCLE`(L307) / `CAMPAIGN_DRIVERS`(L467) /
   `SIGNALS` / `RESEARCH_CANDIDATES` / `CONFLICT_MAP` / `scope`(L905)
   → 新增 Campaign 进 Export **须扩展该脚本**
3. **Coverage Audit**：`research/scripts/audit_historical_coverage.py`（其 `DOMAIN_PROBES`
   会因本轮新增而由「缺失」翻为「存在」，输出将变化 —— 属预期）

### 已知限制

- `工业机器人` 刻意未建行（见 §3.3），因此 `R01-HIEQ-002` / `R01-HIEQ-004` 的该别名
  仍在 `unmatched_names` 中 —— 与 `CF007 UNRESOLVED` 保持一致，**待该冲突裁决后再决定**
- `TH-RES` 命名采用「资源」而非「资源化工」；若后续认为需要拆分 `有色金属` / `基础化工`
  为独立 root，须另起 taxonomy 轮次
