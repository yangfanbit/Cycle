# AUTO_CANDIDATE_TRIAL_2026-10-07.md

> | 项目 | 值 |
> |---|---|
> | 性质 | **试跑记录（Trial）** —— 为一个「当前研究对象」跑完整管线 |
> | 日期 | 2026-10-07 |
> | 方向 | **汽车 —— 智能驾驶合规化** |
> | 沙箱 | `/tmp/auto/threec`（**仓库未被改动**，`git status` 0 改动） |
> | 状态 | ⚠️ **草稿，未经 Research 轮次审核**；**未进入 canonical** |

---

## 1. 做了什么

按 `docs/RESEARCH_PIPELINE_SAFETY.md` 的安全做法，在**沙箱副本**里补齐三份输入并跑完两个阶段：

| # | 输入 | 内容 |
|---|---|---|
| 1 | `current_candidates.json` | 新增 `CC-2026-AUTO-SMARTDRIVE`（3 条真实证据，按时间排序） |
| 2 | `structural_analogy_candidate_events_v0_1.json` | 按规则**派生 3 个事件**（policy / industry / policy） |
| 3 | `structural_analogy_candidate_market_map_v0_1.json` | 按**产品段**判定：`PARTIAL`，series = `AUTO_ETF_516110` + `DESAYSV` |

**证据（全部真实、有日期）**：
- `2025-09-30` 工信部等八部门《汽车行业稳增长工作方案》→ L3「准生证」（POLICY）
- `2026-06-30` 北上深等地开放 L3 有条件自动驾驶测试与准入试点（INDUSTRY）
- `2026-08-04` 工信部《智能网联汽车 自动驾驶系统安全要求》**GB 44721—2026** 强制国标落地（POLICY）

**产物**：6 候选 · **474 条比对**（6 × 79）· 全部在沙箱内。

---

## 2. ★ 结果：汽车候选的 79 条结构比对

### ★ 补证据前 → 后（质变）

| 状态 | 3 条证据 | **7 条证据** |
|---|---|---|
| **`STRUCTURAL_SUPPORTED`** | **0** | **1** |
| `STRUCTURAL_PARTIAL` | 5 | **7** |
| `THEME_ONLY` | 5 | 5 |
| `INSUFFICIENT_EVIDENCE` | 23 | 23 |
| `NO_VALID_CORRESPONDENCE` | 46 | 43 |

### ★★ 唯一的结构支持：`C-2023-AD`（智能驾驶/无人驾驶）· **同大主题**

| 维度 | 结果 |
|---|---|
| lifecycle | **MATCH**（历史在可比观测点同为 `THEME_FORMING`） |
| mechanism_driver | **MATCH · `CORE_EQUIVALENT`**（交集 `[POLICY_DRIVEN, TECH_BREAKTHROUGH]`） |
| evidence_sequence | **MATCH · `SEQUENCE_MATCH`** |
| event_structure | PARTIAL · `MULTI_TYPE_WITH_CHRONOLOGY` |

### 7 条「有结构对应」（`STRUCTURAL_PARTIAL`）

| 历史对象 | 大主题关系 | lifecycle | mechanism | seq | event |
|---|---|---|---|---|---|
| `C-2019-COMM-5G`（5G 网络建设） | **跨大主题** | MATCH | PARTIAL | **MATCH** | MISMATCH |
| `C-2019-MIL-GROUP-RESTRUCTURE`（军工重组） | 跨大主题 | MISMATCH | PARTIAL | PARTIAL | PARTIAL |
| `C-2020-POWER-NE`（光伏/新能源发电） | **跨大主题** | MATCH | PARTIAL | **MATCH** | MISMATCH |
| `C-2020-RE-DEBT-RISK`（地产债务） | 跨大主题 | MISMATCH | PARTIAL | **MATCH** | PARTIAL |
| `C-2022-POLICY`（购置税刺激） | 同大主题 | MATCH | PARTIAL | MATCH | MISMATCH |
| `C-2022-RE-POLICY-THREE`（地产三支箭） | 跨大主题 | MISMATCH | PARTIAL | MATCH | MISMATCH |
| `C-2023-HIEQ-HUMANOID`（人形机器人） | 跨大主题 | MISMATCH | PARTIAL | PARTIAL | PARTIAL |

### 5 条「仅主题相同」（`THEME_ONLY`）—— **同主题但结构不成立**

`C-2020-NEV` · `C-2021-NEV` · `C-2024-ROBOTAXI` · `C-2024-V2X` · `C-2025-ROBOTAXI`

（`C-2024-V2X` 机制为 `PERIPHERAL_OVERLAP` —— **不计入**结构支持）

### ★★★ 这次结果与前一次（3 条证据）的差别，说明了一件重要的事

补证据**不是**「把分数刷上去」，而是**让判定真正可做**：

| 变化 | 原因 |
|---|---|
| `C-2023-AD`：PARTIAL → **SUPPORTED** | 机制轴改对 + 序列补齐 |
| **机制轴此前只到 `PRIMARY_MECHANISM_OVERLAP`** | ★ 我把 `TECH_BREAKTHROUGH` 写在了 `drivers[].category`（**补充轴**）里；而机制轴读的是 **`narrative_types`** |
| **序列此前 `MISMATCH`** | 只有 3 条证据；补到 7 条（policy→industry→industry→policy→company→policy→company）后才形成可比序列 |

> ★ **一个真实的可用性陷阱**：`drivers[].category` 与 `narrative_types` **都叫「驱动」，但只有后者参与机制判定**
> （`build_structural_analogy_research_v0_5.py` L224–226 有明示）。
> 写错位置不会报错，只会**静默降级**。

---

## 3. ★★ 这个结果说明什么

### 1. 「智能驾驶合规化」的结构对应，不在汽车板块内部

- 最强的两条是 **`C-2019-COMM-5G`** 与 **`C-2020-POWER-NE`** —— **完全不同的大主题**，
  但都是「**政策/制度驱动 + 标准先行 + 产业验证滞后**」的结构。
- 而同主题的 `C-2020-NEV` / `C-2021-NEV` / `C-2024-ROBOTAXI` / `C-2025-ROBOTAXI`
  **只是名字像**（`THEME_ONLY`）—— 生命周期与机制都对不上。

> 与医药健康那一次**同一个模式**：**「名字像」的不像，「看起来不像」的才像。**

### 2. 但要诚实：**这次没有 `STRUCTURAL_SUPPORTED`**，且**机制只到 `PARTIAL`**

原因是**我的草稿证据太薄**（3 条 vs 其他候选的 6–9 条）：
- 机制只有 `POLICY + STANDARDIZATION`，与历史交集仅 `POLICY` → `PRIMARY_MECHANISM_OVERLAP`（非 `CORE_EQUIVALENT`）
- `event_structure` **全部 `MISMATCH`** —— 事件结构维度没有可比信息

**结论：要得到 `SUPPORTED`，需要把证据补到与其他候选同量级**（公司层验证、产业订单等）。

---

## 4. 这条链现在**通了**（这是本轮最重要的确认）

```
current_candidates.json（含汽车）
   + candidate_events（派生）
   + candidate_market_map（按产品段判定）
        ↓  阶段 2：build_structural_analogy_research_v0_5.py
   research_v0_5.json（profiles + 474 行 matrix）
        ↓  阶段 3：build_structural_analogy_explanation_v0_5.py
   explanations_v0_5.json（Product-facing）
```

**全程在沙箱内完成，仓库零改动。**

---

## 5. 要真正采纳，还差什么（诚实清单）

| # | 事项 |
|---|---|
| 1 | **Research 轮次审核**：候选的 `attention_state` / `phase_evidence` 应由研究侧推导，而非人工判断 |
| 2 | **证据补到同量级**：至少 6–7 条，含公司层与产业层验证 |
| 3 | **artifact 版本化**：新内容应产出 **`v0_6`**（旧版 `v0_5` 逐字节保留），而非就地修改 |
| 4 | **Product 接线**：快照的 `candidates_source` 指向新版本；页面自动跟随 |
| 5 | **沙箱产物须人工审阅后显式采纳** |

---

*试跑记录 · 2026-10-07 · 沙箱 `/tmp/auto/threec` · 仓库未被改动*
