# R01 Governance Gates v0.1

> **规则集 ID**：`governance-gates-v0.1`
> **性质**：**新增独立治理规则版本**，**不覆盖任何冻结基座**。
> **未修改**：Research Model v1.0 · Timeline Export Contract v1.0 · CMTR v1 · Intake Protocol v0.1 ·
> Intake Schema · taxonomy（`themes` 仍为 52 行 / 11 root）。
> **未修改**：任何 canonical Campaign / Evidence / Source / Theme 数据；未重新研究 R01；未重做 Candidate Decision。
> **来源**：`docs/R01_GOVERNANCE_CONSISTENCY_REVIEW_v0_1.md` 的 G1-1 / G1-3 / G1-5 / G2-1。
> **机器可读产物**：`research/research/reports/governance_classification_v0_1.json`
> **校验器**：`research/scripts/validate_governance_gates.py`
> **构建器**：`research/scripts/build_governance_classification_v0_1.py`

---

## 0. 总则

1. **本规则只作用于 strength / date_confidence / 表达规范，不改变 Campaign 的存废**。
2. **不回溯修改 R01-01 ~ R01-06 的既有 Campaign 结论**。
3. **不因规则上线而回填新的 peak / end / date**。
4. **不虚构**任何高于实测水平的证据等级（特别：Beta Level 2 / 3）。
5. 规则落地为「**决策层规则 + 机器可读清单 + 校验器**」，**不改 DB Schema**。

---

## 1. G1-1 Market Attention / 市场侧证据（**软门槛**）

### 1.1 定位

> **市场侧证据是 Canonical `strength` 与 `date_confidence` 的影响因素，
> 但不是 Canonical Campaign 的绝对硬门槛。**

即：
- ✅ **不得**仅因「无 A 股市场侧证据」就把一个已通过 Independence Gate Q1–Q5 的 Campaign 降级为 Research Only；
- ✅ **必须**把市场侧证据的有无，反映到 `strength` 与 `date_confidence` 的取值与 `research_notes` 的披露上。

### 1.2 三态定义

| 状态 | 判定 | 判据（须可复核） |
|---|---|---|
| **`A_SHARE_MARKET`** | **有 A 股市场侧证据** | 至少一条 evidence 属于以下任一：<br>① 个股行情（涨停 / 一字板 / 封板 / 收于 X 元 / 盘中最高 X 元 / 前复权价）<br>② A 股板块或行业指数涨跌（申万 / 中证 / 中信 / 概念指数）<br>③ 资金与广度（基金持仓比例、成交额、市值、两融）<br>④ 相对宽基基准（沪深300 / 上证 / 中证全指 / 万得全A）的超额 |
| **`INDUSTRY_COMPANY_ONLY`** | **只有行业 / 公司证据** | 全部 evidence 属以下类别，**无一条**满足上表：<br>· 产量 / 销量 / 产能 / 开工率<br>· 商品价格（元/吨、美元/吨、元/公斤、万元/吨、美元/片）<br>· 订单 / 营收 / 利润 / 业绩预告<br>· 政策文件 / 事件公告 / 集团重组事项 |
| **`NONE`** | **完全没有市场侧证据** | 无 evidence（或 evidence 均不可归属市场 / 行业任一侧） |

**★ 关键区分**：**商品价格 ≠ A 股市场侧证据**。
面板价格、碳酸锂价格、稀土价格、猪价、染料中间体价格 —— 均为**产业侧价格**，不计入 `A_SHARE_MARKET`。

### 1.3 对 strength / date_confidence 的影响（软门槛规则）

| 市场侧证据状态 | `strength` 取值规则 | `date_confidence` 取值规则 | 强制披露 |
|---|---|---|---|
| `A_SHARE_MARKET` | 可评 `medium` **或** `strong` | 可评 `high` / `medium` / `low` | 若市场层**全为 Tier 3 二手整理**或**全为非同期**，须在 `research_notes` 写明 |
| `INDUSTRY_COMPANY_ONLY` | **上限 `medium`**（不得 `strong`） | **上限 `medium`** | **必须**写明「无 A 股市场侧证据 / 无行情核验」 |
| `NONE` | 上限 `medium` | 上限 `low` | 必须写明 |

> 既有 Campaign（R01-01~06）已满足上述约束（无 `INDUSTRY_COMPANY_ONLY` 被评 `strong`），
> 故**本轮无需调整任何既有取值**。

### 1.4 两条禁止

1. **不得把「市场上涨」直接等同于独立 Campaign** —— 上涨是现象，Campaign 需要 Gate Q1–Q5 的独立结构证据。
2. **不得把相对收益直接表述为 Alpha** —— 见 §2。

### 1.5 实测分布（52 Campaign）

| 状态 | 数量 | Campaign |
|---|---:|---|
| `A_SHARE_MARKET` | **48** | 其余全部 |
| `INDUSTRY_COMPANY_ONLY` | **4** | `C-2019-MIL-GROUP-RESTRUCTURE` · `C-2018-HIEQ-ROBOT-DOWN` · `C-2016-PANEL-CYCLE` · `C-2020-RES-RAREEARTH` |
| `NONE` | **0** | — |

---

## 2. G1-3 Beta / Market Evidence Level（**Level 0–3**）

### 2.1 定义

| Level | 定义 | 能否支撑 Alpha 判断 | 强制 caveat |
|---|---|---|---|
| **L0** | 只有绝对涨跌 / 价格证据（含产业侧价格） | ❌ | — |
| **L1** | 存在**相对宽基基准**的超额收益，但：<br>· **未做 Beta 调整**；<br>· **未剥离风格因子** | ❌ **Relative Return ≠ Beta-neutral Alpha** | **必须**写明三者 |
| **L2** | 存在**明确的 Beta / 风格调整方法**，并有**可复核结果** | ⚠️ 可作参考，仍非 Alpha 定论 | 须给出方法与结果 |
| **L3** | 能**较强支持「独立行业市场表现」**判断（多基准 + 因子剥离 + 稳健性） | ✅ | 须给出完整论证 |

### 2.2 L1 强制 caveat 模板

凡 `beta_level = 1`，其 `research_notes` 必须包含（语义等价即可）：

```
相对收益 ≠ 行业 Alpha；未做 Beta 调整；未剥离风格因子。
```

### 2.3 实测分布（52 Campaign，**不虚构 L2/L3**）

| Level | 数量 | Campaign |
|---|---:|---|
| **L0** | **43** | 其余全部 |
| **L1** | **9** | `C-2020-FIN-BANK-CREDIT` · `C-2020-RE-DEBT-RISK` · `C-2022-RE-POLICY-THREE` · `C-2023-FIN-SOE-VALUATION` · `C-2023-HIEQ-ROBOT-PLUS` · `C-2024-FIN-BANK-DIVIDEND` · `C-2024-FIN-BROKER-POLICY` · `C-2025-FIN-INSURANCE` · `C-2025-ROBOTAXI` |
| **L2** | **0** | — |
| **L3** | **0** | — |

**★ 对 Governance Review v0.1 预估的两处修正**（本规则实现后的精确复核结果）：

| 项 | Review 预估 | 本规则实测 | 说明 |
|---|---|---|---|
| `C-2020-MIL-EQUIP-ORDER` | L1 | **L0** | 其市场证据为**中证军工指数绝对涨跌**，**无**沪深300 / 上证对比 → 不满足 L1 |
| L1 总数 | 8（R01-05 的 7 + R01-06 的 001） | **9** | 复核新发现 2 个 L1：`C-2023-HIEQ-ROBOT-PLUS`（跑赢沪深300 4.82pct）· `C-2025-ROBOTAXI`（跑赢沪深300）；同时 001 降级为 L0 |

**★ 已排除的伪 L1**（防止误判）：
- `C-2024-SEMI-MEMORY` —— 「上证指数 +4.15%、创业板指 +5.54%」为**绝对指数涨跌**，非相对基准超额 → L0
- `C-2020-SEMI-EQUIPMENT` —— 「**超额配售**」为证券发行术语（greenshoe），**非超额收益** → L0
- `C-2020-RES-LITHIUM` —— 「同期……股价涨幅」的「同期」对比对象是**碳酸锂价格（商品）**，非宽基 → L0

### 2.4 最小实现方案（**不改 Schema**）

**当前 DB `campaigns` 表无 `beta_level` 字段。** 按「不为方便任意改 Schema」原则，采用：

| 层 | 实现 |
|---|---|
| **事实源** | `research/research/reports/governance_classification_v0_1.json`（研究级，非 canonical） |
| **决策层** | 本规则文档 + 校验器 `validate_governance_gates.py`（V4 禁止无 basis 的 L2/L3） |
| **消费层（SA/TO）** | **直接读取研究级 JSON**（与 `time_observation_patterns_v0_1.json` 同类做法），**不经过 Export** |
| **DB Schema** | **不改**。若后续确需落库，建议**独立轮次**新增 `campaigns.beta_level` + `campaigns.market_evidence_state` 两列并做一次性回填，属 Schema 变更需单独评审。 |

### 2.5 ★ 为何**不**把 `governance` 加入 Timeline Export（本轮实测结论）

本轮**已尝试**在 `exports/timeline_export_v1.json` 的 campaign 条目中增加
`governance` 字段（按既有 `lifecycle` / `drivers` 的 backward-compatible 做法），
结果 **`validate_timeline_export` 直接 FAIL（52 处 `field-whitelist`）**：

```
FAIL [field-whitelist] campaign C-… 出现未声明字段: governance（不得伪装成正式 Contract 字段）
```

根因：`validate_timeline_export.py` 的 `CAMPAIGN_FIELDS` 是**严格白名单**，
`lifecycle` / `drivers` 是由 V1.7 **显式加入白名单**才合法的。
→ **在 Export 增加字段 = 事实上的 Export Contract 变更**。

依「**不修改 Timeline Export Contract v1.0**」的明确约束，本轮**已回退该改动**
（`batch_auto_research.py` diff 为空），改为：

- ✅ 治理分类以**研究级 JSON** 交付，SA / TO **直接读取**；
- ⏭️ 若确需进入 Export，须由**独立轮次**将 `governance` 加入 `CAMPAIGN_FIELDS`
  并升级为 Contract v1.1 —— **本轮不做**。

---

## 3. G1-5 `result = weak` 统一语义

### 3.1 正式定义

> **`result = weak` = 行业 / 市场方向为负。**

它 **不代表**：
- ❌ 证据弱；
- ❌ confidence 低；
- ❌ Campaign 不成立。

### 3.2 字段分工（**强制**）

| 字段 | 含义 | 取值 |
|---|---|---|
| `strength` | **证据 / 结构强度** | `strong` / `medium`（**不得 `weak`**） |
| `result` | **方向性结果** | `positive` / `neutral` / `weak` / `failed` / `unknown` |

### 3.3 全库扫描结果

- `result = 'weak'`：**4 个** —— `C-2019-AD`(legacy) · `C-2018-HIEQ-ROBOT-DOWN`(R01-01) · `C-2022-SEMI-DOWNTURN`(R01-02) · `C-2020-RE-DEBT-RISK`(R01-05)
- **`strength = 'weak'` 违例：1 个** —— **`C-2019-AD`**（全库唯一；`strength` 分布 `strong 21 / medium 30 / weak 1`）

**判定**：属 **legacy 历史数据语义残留**（pre-R01 时期 `weak` 既用于 strength 也用于 result），
非本轮规则引入。

**处置**：
- ✅ **本轮不修改**（不与规则实现混合）；
- ✅ 由 `validate_governance_gates.py` **V8 持续告警**（WARN 级，不阻断）；
- ⏭️ **提出独立修复**：将 `C-2019-AD` 的 `strength` 由 `weak` → `medium`，保留 `result = 'weak'`。
  （影响：DB 1 行 / Export 1 条 / SA 轻微；需单独评审后执行。）

---

## 4. G2-1 Peak / End 四态决策树

### 4.1 四态定义

| 态 | 含义 | 触发条件 |
|---|---|---|
| **EXACT** | 有**明确可复核**的日期 | 存在 EXACT_DATE 精度的可复核证据（如指数收盘点位日、公告披露日） |
| **WINDOW** | 只能确定在**某一时间窗口** | 仅 DATE_WINDOW / PHASE_WINDOW 精度（如「2021 年 Q4」「2023 年 5 月前后」） |
| **ALTERNATIVE** | **另一种合理口径被保留**，但**不是 canonical peak/end** | 存在并列口径（如 peak cluster 的多个区间高点、end 的两种判定口径）。<br>→ canonical 取其一，**另一口径连同来源与理由记录在 `alternative`** |
| **NULL / UNKNOWN** | **当前证据不足以确定** | 无任何可靠峰值 / 结束证据，或结构仍在延续 |

**实现约定**：清单中 `peak.state` / `end.state` ∈ {`EXACT`, `WINDOW`, `NULL`}；
**ALTERNATIVE 由非空的 `peak.alternative` / `end.alternative` 表示**（含 `date` + `basis`）。
这样既保留 canonical 态，又完整记录并列口径。

### 4.2 强制约束

1. **商品 peak ≠ A 股 peak**
   `C-2020-RES-LITHIUM`：A 股 peak **2021-09-13**；商品（碳酸锂）peak **2022-11-11** —— 差约 14 个月，**已正确分离**。
2. **行业 / 产业数据 peak ≠ A 股 Campaign peak**
   产量、销量、价格峰值不得充当 A 股 peak。
3. **不允许为了完整性制造精确日期** —— 证据不足时**允许且应当**用 `WINDOW` 或 `NULL`。
4. **peak 无法确定时允许 `NULL`** —— `C-2024-FIN-BANK-DIVIDEND` / `C-2025-FIN-INSURANCE` / `C-2024-RES-GOLD-CB` / `C-2019-MIL-GROUP-RESTRUCTURE`。
5. **alternative 必须保留来源与理由**（校验器 V7 强制 `basis` 非空）。
6. **end 同样遵循本决策树**。

### 4.3 用户点名 6 处的审计结论（**不补日期，只确认合规**）

| Campaign | peak | end | 结论 |
|---|---|---|---|
| `C-2024-SEMI-MEMORY` | EXACT 2025-10-31（alt 2025-11-11） | WINDOW（截至 2025-12-31 未出现明确结束信号） | ✅ 符合四态；**不回填 end** |
| `C-2020-RES-LITHIUM` | EXACT 2022-11-11（alt 2021-09-01 / 2021-09-13） | WINDOW（2023 年碳酸锂价格快速下行） | ✅ **商品 peak 已与 A 股 peak 分离**；alt 已保留 |
| `C-2024-RES-GOLD-CB` | **NULL** | **NULL** | ✅ 正确 —— 未把商品峰值当 A 股 peak |
| `C-2020-RES-NONFERROUS` | EXACT 2021-05-10（alt 2021-09-13） | WINDOW（2021 Q4 高位震荡后转弱） | ✅ 符合；**商品（LME 铜 2021-05-10）与 A 股 peak 已分别记录** |
| R01-05 银行 / 保险 | `C-2024-FIN-BANK-DIVIDEND` peak **NULL** / end NULL · `C-2025-FIN-INSURANCE` peak **NULL** / end NULL | — | ✅ 正确 —— 结构可能仍在延续，**不得用观察窗口结束** |
| `C-2019-MIL-GROUP-RESTRUCTURE` | **NULL**（PHASE_WINDOW，具体峰值不可考） | EXACT 2019-11-26（alt 2019-10-25） | ✅ 正确 —— **未制造精确 peak** |

### 4.4 实测分布（52 Campaign）

| 态 | peak | end |
|---|---:|---:|
| **EXACT** | 22 | 16 |
| **WINDOW** | 26 | 30 |
| **NULL** | 4 | 6 |
| **带 alternative** | 13 | 3 |

---

## 5. 机器可读清单

**路径**：`research/research/reports/governance_classification_v0_1.json`

```jsonc
{
  "ruleset": "governance-gates-v0.1",
  "counts": { "campaigns": 52, "market_evidence_state": {...}, "beta_level": {...}, ... },
  "campaigns": [
    {
      "campaign_id": "C-2020-MIL-EQUIP-ORDER",
      "market_evidence_state": "A_SHARE_MARKET",
      "market_evidence_basis": "...",
      "beta_level": 0,
      "beta_level_basis": "...",
      "peak": { "state": "EXACT", "date": "2021-12-01",
                "alternative": { "date": "2021-08-24", "basis": "..." } },
      "end":  { "state": "WINDOW", "date": "2022-12-31", "alternative": null },
      "result_weak_semantics": { "result_is_weak": false, "strength_is_weak": false,
                                 "conforms_to_gate": true, "note": null },
      "needs_historical_fix": false
    }
  ]
}
```

**构建**：`python research/scripts/build_governance_classification_v0_1.py`
**校验**：`python research/scripts/validate_governance_gates.py`

---

## 6. 与冻结基座的关系（合规声明）

| 基座 | 状态 |
|---|---|
| Research Model v1.0 | **未修改** |
| Timeline Export Contract v1.0 | **未修改**（顶层结构仍为 rules / signals / campaigns / research_candidates / events / securities；`CAMPAIGN_FIELDS` 白名单**未新增**，详见 §2.5） |
| CMTR v1 | **未修改** |
| Intake Protocol v0.1 / Intake Schema | **未修改** |
| Validator C01–C25 | **未修改** |
| `validate_timeline_export.py` | **未修改**（本轮曾尝试加字段 → 触发白名单 FAIL → **已回退**） |
| `batch_auto_research.py` | **未修改**（diff 为空） |** |
| taxonomy（`themes`） | **未扩展**（仍 52 行 / 11 root） |
| canonical DB（campaigns / evidences / sources / themes） | **未修改** |
| Intake Packages（R01-01~06） | **未修改** |
| Structural Analogy / Time Observation | **未刷新** |

**新增文件**：
- `docs/R01_GOVERNANCE_GATES_v0_1.md`（本文件）
- `research/research/reports/governance_classification_v0_1.json`
- `research/scripts/build_governance_classification_v0_1.py`
- `research/scripts/validate_governance_gates.py`

**未改动**：`research/scripts/batch_auto_research.py`、`research/scripts/validate_timeline_export.py`、
DB Schema、DB 业务数据、Intake Packages —— 均已核验 diff 为空。
