# MARKET_REGIME_AI_INTERFACE_v0.1.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **AI 生成接口规范（Design Contract · 面向自动化）** |
> | 版本 | `0.1` |
> | 日期 | 2026-09-26 |
> | 上游 | `docs/MARKET_SNAPSHOT_CONTRACT_v0.1.md` §2.1（`market_regime` 字段定义）· `docs/THREEC_1_1_MARKET_SNAPSHOT_ARCHITECTURE.md` |
> | 定位 | **AI 离线产生 → 机器校验 → 人工审核 → CANONICAL** |
> | 更新节奏 | **每月一次（频次由用户主导；不建自动化定时）** |
> | 状态 | 待确认（Phase 1.2 实现） |
>
> **本文件回答一件事**：让 AI 稳定地产出 `market_regime`，并且**可被机器校验、可被人工审核**。

---

## 0. 边界（先讲清楚，再谈接口）

| ✅ 是 | ❌ 不是 |
|---|---|
| 对**已发生区间**的市场状态做离散分类 | 对未来的预测 |
| 研究过程的输入（背景上下文） | 结构判定的依据 |
| 必须逐维度挂证据 | 可以凭印象填写 |
| **可 `UNKNOWN`**（且优先于猜测） | 必须填满 |

**硬约束（沿用既有红线）**：

1. `market_regime` **不参与 Structural Status**（SA Rule Set §12；Market/Temporal 为非正式维度）。
2. **禁止**输出 `score` / `ranking` / `probability` / `prediction` / `signal`。
3. AI **只**在**离线生成端**运行；**产品运行时不联网、不调 LLM**。
4. AI **不得**据此确认结构相似、不得 Promotion、不得评分排名。

---

## 1. 为什么需要「规则」而不是「让 AI 自己判断」

AI 直接给结论有三个问题：**不可复现**（同样输入两次不同结果）、**不可审计**（不知道依据）、**不可证伪**（无从判断对错）。

因此本接口的设计原则是：

> **AI 负责「收集证据 + 按规则归类」；规则负责「确定性」；校验器负责「可机器校验」；人负责「签发」。**

---

## 2. 四个维度的操作化定义（Operational Definitions）

> ⚠️ 说明：以下**区间与分档是为了可复现的分类边界**（与「生命周期阶段」同性质），
> **不是评分、不是概率、不是预测**。任何维度在证据不足时**必须**为 `UNKNOWN`。

### 2.1 通用测量口径

| 项 | 规定 |
|---|---|
| 观测窗口 | 以 `snapshot_date` 为**右端点**回溯；**不得**使用任何 `date > snapshot_date` 的数据（Temporal Firewall） |
| 交易日 | 以 A 股交易日历为准；非交易日不计入 |
| 指标口径 | 区间口径优先（20 / 60 交易日），**禁止**用单日数据定档（单日受噪声与 β 影响过大） |
| 数据来源 | Tier 1（交易所 / 统计局 / 央行 / 官方指数公司）> Tier 2（交易所行情数据、Wind/同花顺口径统计）> Tier 3（财经媒体，仅转述 T1/T2） |

### 2.2 `broad_index_state`（宽基方向）

- **标的**：沪深 300 指数（`SH000300`）为主；上证指数为辅
- **窗口**：近 **20 交易日**区间涨跌
- **分档**：

| 区间涨跌 | 取值 |
|---|---|
| ≥ +5% | `UP` |
| ≤ −5% | `DOWN` |
| 其余 | `FLAT` |
| 数据不可得 / 口径冲突 | `UNKNOWN` |

### 2.3 `breadth_state`（市场广度）

- **指标**：全市场**上涨家数占比**（周度均值，覆盖近 4 周）
- **分档**：

| 上涨家数占比（周均） | 取值 |
|---|---|
| ≥ 60% | `BROAD` |
| 40% – 60% | `NORMAL` |
| < 40% | `NARROW` |
| 数据不可得 | `UNKNOWN` |

### 2.4 `liquidity_state`（流动性）

- **指标**：两市**日均成交额**，与过去 **60 交易日均值**比较
- **分档**：

| 相对 60 日均值 | 取值 |
|---|---|
| ≥ +15% | `EXPANDING` |
| ≤ −15% | `CONTRACTING` |
| 其余 | `STABLE` |
| 数据不可得 | `UNKNOWN` |

### 2.5 `risk_appetite_state`（风险偏好）

> 本维度**定性成分最高**，因此门槛也最高。

- **要求 ≥2 个独立信号**，否则一律 `UNKNOWN`（**禁止**单信号定档）
- 可选信号（任选 ≥2，须逐条记录）：

| 信号 | 说明 |
|---|---|
| 高 β 板块 vs 低 β 板块 20 日相对表现 | 题材/成长 vs 权重/红利 |
| 涨停家数 / 炸板率（周度） | 情绪强度与承接力 |
| 融资余额变化（月度） | 杠杆意愿 |
| 新股/次新相对表现 | 投机偏好 |

- **判定**：≥2 个信号同向 → 取该方向；信号冲突 → `NEUTRAL`；信号不足 2 个 → `UNKNOWN`

### 2.6 `beta_note`（β 不可分离说明 · **必填**）

> 强制说明本快照期 β 的干扰程度。至少覆盖：
> 宽基是否处于单边/极端区间 · 是否存在全市场普跌或普涨日 · 单日数据是否已排除。
> **缺失即校验 FAIL。**

---

## 3. AI 输出契约（严格 JSON）

```jsonc
{
  "contract": "market_regime_draft",
  "market_regime_version": "0.1",
  "snapshot_date": "2026-09-30",                 // 右端点；所有证据 <= 此日
  "generated_by": "ai-offline",
  "generated_at": "2026-09-30T20:00:00",
  "ai_model": "<模型标识，可空但建议填>",

  "market_regime": {
    "broad_index_state":    "UP|FLAT|DOWN|UNKNOWN",
    "breadth_state":        "BROAD|NORMAL|NARROW|UNKNOWN",
    "liquidity_state":      "EXPANDING|STABLE|CONTRACTING|UNKNOWN",
    "risk_appetite_state":  "RISK_ON|NEUTRAL|RISK_OFF|UNKNOWN",
    "beta_note": "……",                            // ★ 必填
    "evidence_refs": ["MR-EV-01", "MR-EV-02"]     // ★ 至少 1 条
  },

  "evidence": [
    {
      "evidence_id": "MR-EV-01",
      "dimension": "broad_index_state",           // 该证据支撑哪个维度
      "metric": "沪深300 近20交易日区间涨跌",
      "value_text": "+6.2%",                      // 文本表述（不要求精确数值）
      "window": "2026-09-01 ~ 2026-09-30",
      "source_tier": "T1|T2|T3",
      "source_title": "……",
      "source_date": "2026-09-30",                // ★ <= snapshot_date
      "claim": "……"                                // 只写事实
    }
  ],

  "unknown_notes": {
    // 任一维度为 UNKNOWN 时必填原因
    "risk_appetite_state": "仅有 1 个独立信号（涨停家数），不满足 ≥2 信号门槛"
  },

  "review": {
    "status": "PENDING",                          // PENDING -> ACCEPTED|REJECTED|NEEDS_EVIDENCE
    "reviewer": null,
    "decided_at": null,
    "rationale": null
  }
}
```

---

## 4. 机器校验规则（Validator Invariants）

> Phase 1.2 实现为脚本；**任一 FAIL 即不得进入人工审核**。

| # | 规则 | 级别 |
|---|---|---|
| **V1** | `contract == "market_regime_draft"` 且 `market_regime_version` 合法 | FAIL |
| **V2** | 四个维度取值必须落在各自枚举内（含 `UNKNOWN`） | FAIL |
| **V3** | `beta_note` 非空 | FAIL |
| **V4** | `evidence_refs` 至少 1 条，且全部能在 `evidence[]` 中找到 | FAIL |
| **V5** | 每条 evidence 的 `source_date <= snapshot_date`（**PIT 硬约束**） | FAIL |
| **V6** | 任一维度非 `UNKNOWN` → 该维度**必须**有 ≥1 条 `dimension` 匹配的证据 | FAIL |
| **V7** | 任一维度为 `UNKNOWN` → `unknown_notes.<维度>` 必须非空（**说明为什么不知道**） | FAIL |
| **V8** | `risk_appetite_state != UNKNOWN` → 该维度证据须覆盖 **≥2 个独立信号** | FAIL |
| **V9** | 产物中不得出现 `score` / `probability` / `prediction` / `signal` / `ranking` 字段或关键词 | FAIL |
| **V10** | `generated_by` 必须为 `ai-offline`（**AI 产物必须显式标注**） | FAIL |
| **W1** | 证据全部为 T3 来源 | WARN |
| **W2** | 任一维度用单日数据定档 | WARN |

---

## 5. 流程（自动化友好）

```
① 触发（用户主导，每月一次）
      ↓
② AI 离线采集 + 按 §2 规则归类  ──→  market_regime.draft.json
      ↓
③ Validator（§4）自动校验            FAIL → 打回 AI 重做（不得人工放行）
      ↓
④ 人工审核（必过）                    ACCEPTED / REJECTED / NEEDS_EVIDENCE
      ↓
⑤ 写入 Market Snapshot 的 market_regime，快照状态 DRAFT
      ↓
⑥ 快照整体经 Human Review → CANONICAL
      ↓
⑦ Product 只读消费（仅 CANONICAL）
```

**自动化边界**：

- ✅ 可自动化：② 采集与归类（AI）、③ 校验（脚本）、⑤ 装配
- ❌ 不可自动化：④ 人工审核、⑥ CANONICAL 签发

---

## 6. 落点（已批准结构）

```
research/current/market_snapshots/
├── README.md
├── schema/                       （Phase 1.2：JSON Schema draft-07）
├── market_regime/
│   ├── 2026-09.draft.json
│   └── 2026-09.json              （人工审核通过后）
└── snapshots/
    └── MS-2026-09-30-01.json     （完整 Market Snapshot）
```

---

## 7. 明确不做

- ❌ 不接入实时行情 API（保持静态 PWA）
- ❌ 不在产品运行端调用 AI
- ❌ 不让 `market_regime` 参与 Structural Status
- ❌ 不产出 score / probability / prediction
- ❌ 不建立定时自动化（**更新频次由用户主导**）

---

*接口规范结束 · Market Regime AI Interface v0.1 · 2026-09-26 · 待确认*
