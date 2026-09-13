# Cycle Mapping v1.1

> Cycle HistoricalCampaign ↔ Cycle-Research campaigns 字段映射表（Red Team v1.1 修正版）。
> 版本：v1.1
> 日期：2026-09-13
> Cycle 侧事实来源：`Cycle/src/models/*.ts`（已只读核实）。
> v1.1 修正：Phase 不再声称 1:1 可映射；Source 改为 TRANSFORM（见 source_mapping_v1.md）；
> Campaign 字段逐一按 Cycle 真实模型核对；新增日期三层术语。

---

## 1. 目的

定义 Cycle HistoricalCampaign 与 Cycle-Research campaigns 之间的字段映射关系，确保晋级时字段正确转换。
全实体总览见 [promotion_mapping_matrix_v1.md](promotion_mapping_matrix_v1.md)；Source 细则见 [source_mapping_v1.md](source_mapping_v1.md)。

---

## 2. Campaign 核心字段映射（按 Cycle 真实模型逐字段核对）

| Cycle HistoricalCampaign | Research campaigns | Mapping | 说明 |
|---|---|---|---|
| campaign_id | campaign_id | DIRECT | |
| rule_id | rule_id | DIRECT | |
| season_id | season_id | **TRANSFORM** | 格式不同：Cycle 用 `2024` / `2026-2027`；Research 用 `summer_2023` / `season_2022`。晋级时转换格式 |
| campaign_year | campaign_year | DIRECT | |
| start_date | start_date | DIRECT（字段）/ 值待人工确认 | 见第 4 节日期三层术语 |
| end_date | end_date | DIRECT（字段）/ 值待人工确认 | 同上 |
| peak_date | peak_date | DIRECT（字段）/ 值待人工确认 | Cycle 允许 null |
| **cross_year** | （无此列） | **TRANSFORM（计算）** | `year(end_date) > year(start_date)`，由 promotion layer 计算，不得人工复制空值 |
| strength | strength | DIRECT | 枚举一致：strong/medium/weak |
| result | result | DIRECT | 枚举一致：positive/neutral/weak/failed/unknown |
| description | description | DIRECT | |
| **source_id** | （campaigns 无此列） | **TRANSFORM（派生）** | Cycle 必填；Research campaigns 表无 source_id 列。由 promotion manifest 的 `source_id`（锚定来源）派生 |
| start_date_basis | start_date_basis | **TRANSFORM** | Research 为长文本；Cycle 为枚举 observed/inferred/official_event/unknown。晋级时映射到枚举，原文留 package |
| end_date_basis | end_date_basis | **TRANSFORM** | 同上 |
| date_confidence | date_confidence | DIRECT | 枚举一致：high/medium/low；Cycle 可选 |
| （Cycle 无此字段） | classification | **NOT_SUPPORTED** | theme_campaign/industry_trend/... 在 Cycle 无落点。保留在 promotion package；如人工需要可并入 description，不静默丢弃 |
| （Cycle 无此字段） | annual_review_id / drift_* / research_notes / created_at | RESEARCH_ONLY | 留在 Research |

---

## 3. cross_year 计算

### 定义

```python
cross_year = year(end_date) > year(start_date)
```

### 当前候选

| Campaign | start_date（DB Candidate） | end_date（DB Candidate） | cross_year |
|---|---|---|---|
| C-2022-POLICY | 2022-04-27 | 2022-08-31 | false |
| C-2023-AD | 2023-06-12 | 2023-07-19 | false |
| C-2024-ROBOTAXI | 2024-07-08 | 2024-07-31 | false |

**约束**：
- cross_year 由 promotion layer 计算
- 不得人工复制空值
- 当前三条候选全部为 false
- 若人工 Review 改判日期（如 2024 end 改 08-23），cross_year 必须重新计算而非手工编辑

---

## 4. 日期三层术语（v1.1 新增）

晋级全流程中，任何日期必须标明所处层级，禁止混称"已确认"：

| 层级 | 定义 | 当前状态 |
|---|---|---|
| **DB Candidate Date** | campaigns 表中当前记录的研究候选日期（冻结 DB 值） | 已固定，不改 |
| **Research Review Date Candidate** | 研究报告中提出的备选口径（如 2022 的 05-23；2024 的 peak 08-05 / end 08-23） | 已记录，待裁决 |
| **Verified Date** | 人工最终确认后的日期；写入 Cycle 的唯一合法值 | 不存在（reviewer=pending） |

- 只有 Verified Date 允许进入 Cycle。
- campaign_date_observations 中三条候选的 verified_date 全部为 NULL，与此一致。

---

## 5. Campaign Phase 映射（v1.1 修正）

### 结论

```
Phase mapping: NOT PERSISTED IN CURRENT CYCLE
```

- Research 有 `campaign_phases` 实体（startup/acceleration/main_rise/diffusion/retracement/secondary_rally/decline/unclear）。
- **当前 Cycle 没有独立 CampaignPhase 实体/正式落点**（已核实 `Cycle/src/models/`，无任何 Phase 模型）。
- 因此 Research Campaign Phase = **Research-only information**，不进入 Cycle。

### 约束

- Phase 保留在 Research，供审计与未来研究使用。
- Cycle 当前仅承载 HistoricalCampaign 主体。
- 未来如需在 Cycle 展示 Phase，再单独设计（属 Cycle 项目决策，本轮不新增任何 Phase schema）。
- **Phase 不构成当前 Promotion Gate 的必要条件**：checklist 中 Phase 项标记为 N/A（research-only）。

---

## 6. Evidence 映射（v1.1 修正）

### 定位

- **Research Evidence = 完整研究审计数据**（含 evidence_role / independence_group / temporal_relation）。
- **Cycle Evidence = 生产展示所需的最小证据实体**（evidence_id/source_id/evidence_type/description/date?/confidence/rule_id?/campaign_id?/theme_id?/notes?）。

### 字段级映射

| Research evidences | Cycle Evidence | Mapping |
|---|---|---|
| evidence_id | evidence_id | DIRECT |
| source_id | source_id | DIRECT（其 Source 经 source_mapping_v1.md 转换） |
| evidence_type（中文自由文本） | evidence_type（枚举） | TRANSFORM：行情数据→market_data；政策文件→official；行业月度产销数据/行业数据→market_data 或 other（逐条人工确认） |
| description | description | DIRECT |
| date | date? | DIRECT（均可空） |
| confidence | confidence | DIRECT（枚举一致） |
| evidence_role | （无字段） | NOT_SUPPORTED → 留 promotion package |
| independence_group | （无字段） | NOT_SUPPORTED → 留 promotion package |
| temporal_relation | （无字段） | NOT_SUPPORTED → 留 promotion package |
| created_at | （无字段） | N/A |
| （桥表 campaign_evidences） | campaign_id? | 见第 7 节 |
| （可派生） | rule_id? / theme_id? | TRANSFORM：晋级时可附带所属 rule/theme |

### 约束

- 只把真正属于 Campaign 的 Evidence 作为 promotion prerequisite。
- Unbound Evidence 不强行绑定。
- 未来导入时只映射 Cycle 支持的字段，但 **promotion package 必须保留 Research Evidence 原始 ID 与完整信息**，审计链不断。

---

## 7. CampaignEvidence 桥表问题（v1.1 新增）

- Research：`campaign_evidences` 是显式多对多桥表（campaign_id + evidence_id + role）。
- Cycle：Evidence 上有单值可选 `campaign_id`，**没有 campaign_evidences 桥表**。

### 判断

在当前条件下**可以**把 Research 的绑定关系写入 Cycle `Evidence.campaign_id`，条件是：

1. **每条 evidence 唯一归属一个 Campaign**（`validate_promotion_manifest.py` 第 6 项已强制：evidence 不跨 Campaign）；
2. 桥表 `role`（supporting/contradicting/context）在 Cycle 无落点，完整保留在 promotion package；
3. 若未来出现一条证据服务多个 Campaign，单值 FK 即不足——届时由 Cycle 项目重新设计，**不得擅自新增桥表**。

---

## 8. ValidationRecord 映射（v1.1 修正）

- **Research 没有 ValidationRecord 实体**。核验事实散见于 promotion manifest（reviewer/reviewed_at）与 campaign_date_observations（candidate vs verified 日期）。
- Cycle 有 ValidationRecord（validation_scope/rule_id/campaign_id?/evidence_status/verification_status/reviewer/created_at/reviewed_at/notes/method_version）。

### 映射方式：晋级时新建（TRANSFORM）

| Cycle ValidationRecord | 来源 | 取值规则 |
|---|---|---|
| validation_id | 晋级时生成 | 新 ID |
| validation_scope | 固定 | `campaign` |
| rule_id | manifest.rule_id | DIRECT |
| campaign_id | Cycle 侧 campaign_id | scope=campaign 时必填 |
| evidence_status | 固定 | `L2`（历史事实已核验） |
| verification_status | 固定 | `under_review` 或 `not_tested`。**禁止写 statistically_supported** —— L2 事实核验 ≠ 规律统计成立（Cycle 模型注释明确约束） |
| reviewer | 人工填写 | pending 不允许 |
| created_at | 晋级时生成 | ISO date |
| reviewed_at | 人工填写 | 与 reviewer 同时存在 |
| notes | 晋级时撰写 | 含 Research 原始 ID 引用 |
| method_version | 晋级时指定 | 如 `promotion-gate-v1.1` |

### 约束

- reviewer = "pending" 或 reviewed_at = null → 不得 READY_FOR_PROMOTION，必须停留在 READY_FOR_HUMAN_REVIEW。

---

## 9. 禁止事项

- 禁止修改 Cycle
- 禁止修改 Cycle-Research 核心 Schema
- 禁止修改 Research Model
- 禁止写入 Cycle/data/verified/
- 禁止强行转换无法映射的字段（标记 NOT_SUPPORTED 并留 package）
- 禁止为晋级新增 Phase / 桥表等 schema

---

**版本**：v1.1
**状态**：ACTIVE（Red Team v1.1 修正版，替代 v1.0）
