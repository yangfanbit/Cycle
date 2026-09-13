# Promotion Mapping Red Team v1.1

> Research → Cycle 映射红队重审最终报告。
> 日期：2026-09-13
> 基线：Promotion Gate = 76d26e8；Cycle 侧事实经 `Cycle/src/models/*.ts` 只读核实。
> 本轮不做数据迁移；未修改 Cycle / Schema / SQLite 数据 / verified / Research Model；未新增历史数据。

---

## 执行摘要

上一轮（76d26e8）的映射结论存在四处认知错误，本轮全部纠正：

1. **Phase "1:1 可映射" → 错误**。Cycle 当前没有 CampaignPhase 实体，Phase = research-only。
2. **Source "直接映射" → 错误**。source_type 12→6 需显式转换；tier/publisher 无落点。
3. **"Start/End/Peak 已确认" → 错误**。当前只有 DB Candidate Date 与 Research Review Date Candidate；Verified Date 不存在。
4. **Campaign 字段"直接映射" → 部分错误**。season_id 格式不同、source_id 需派生、classification 无落点、date_basis 文本→枚举。

真正经得起核实的 DIRECT 只有两项：**Theme、Security**。

---

## 十四问回答

### 1. Phase 为什么不是 Direct Mapping

Cycle 的 `src/models/` 中不存在任何 CampaignPhase/Phase 实体（已逐文件核实：campaign.ts 仅有 HistoricalCampaign 与 CampaignSecurity）。Research 的 `campaign_phases` 在 Cycle 没有落点。因此 Phase 定义为 **RESEARCH_ONLY**：保留在 Research 供审计与未来研究，不进入 Cycle，未来如需展示由 Cycle 项目单独设计。Phase 不再是 Promotion Gate 的必要条件。

### 2. Source 是否 Direct / Transform

**TRANSFORM**。Research source_type 12 类 → Cycle 6 类（personal/article/official/research/market_data/quant_verification），逐类映射规则与判定原则见 [source_mapping_v1.md](research/promotion/source_mapping_v1.md)。`other` 及边界个案（协会/媒体细分/个人站点）不允许静默映射，构成 MAPPING_BLOCKER，晋级执行前逐条人工确认。

### 3. Tier 在 Cycle 中如何处理

Cycle Source 无 tier 字段。三方案比较（A 丢弃 / B 编码进 description / C 未来扩 schema）后，默认推荐：**现在不扩 Cycle Schema，不用 B 污染正文字段；promotion package 必须保留 research source_id + research tier**（经 evidence_id → source_id → tier 可完整回溯），审计链不断。详见 source_mapping_v1.md 第 4 节。

### 4. Evidence 哪些字段丢失/转换

- DIRECT：evidence_id、source_id（经 Source 转换）、description、date、confidence（枚举一致）。
- TRANSFORM：evidence_type（中文自由文本 → 枚举 market_data/article/official/news/manual_review/other，规则见 cycle_mapping_v1.md 第 6 节，个案需人工确认）。
- 丢失（NOT_SUPPORTED，留 promotion package）：**evidence_role、independence_group、temporal_relation**、created_at。
- 原则：Research Evidence = 完整研究审计数据；Cycle Evidence = 生产展示最小实体；package 保留原始 ID 与完整信息。

### 5. campaign_evidences 如何处理

Cycle 无桥表，仅有 Evidence.campaign_id 单值可选 FK。在当前条件下**可以**写入，条件：(1) 每条 evidence 唯一归属一个 Campaign（validate_promotion_manifest.py 第 6 项已强制不跨 Campaign）；(2) 桥表 role 留 package；(3) 未来出现多归属证据时由 Cycle 重新设计，不得擅自加表。

### 6. Theme 是否 Direct

**DIRECT（经逐值核实）**。theme_type 枚举一致（sector/concept/industry，Research 实际仅用 concept/industry）；Theme 字段一一对应；CampaignTheme 桥表 role 枚举一致（main/secondary/catalyst/related）。

### 7. Security 是否 Direct

**DIRECT（经逐值核实）**。Research securities 的 exchange 全部为 SH/SZ，落在 Cycle 枚举（SH/SZ/BJ）内；CampaignSecurity role 枚举一致（leader/second_leader/representative/follow）；Cycle 的 sector? 可选留空。
注意：Research 的 Historical Leader Set 是**事后整理的代表性标的集合**，不得自动等同于 Point-in-Time Leader（PIT 识别链见 campaign_date_observations 与 point_in_time_leaders.csv，两者分离）。

### 8. Validation 是否 Direct / Transform

**TRANSFORM（晋级时新建）**。Research 没有 ValidationRecord 实体——核验事实散见于 promotion manifest（reviewer/reviewed_at）与 campaign_date_observations（candidate vs verified 日期）。逐字段映射规则见 cycle_mapping_v1.md 第 8 节：validation_scope='campaign'、evidence_status='L2'、reviewer/reviewed_at 来自人工、method_version 必填。
**关键：L2 事实核验 ≠ statistically_supported**（Cycle 模型注释明确此约束），verification_status 只能写 under_review / not_tested。两维度不得混淆。

### 9. Point-in-Time 是否 Research-only

**是（RESEARCH_ONLY）**。campaign_date_observations / market_series / market_daily / trading_calendar 整套 PIT 基础设施在 Cycle 无对应实体，整体留 Research。这是设计使然，非阻碍。

### 10. READY_FOR_HUMAN_REVIEW 的新定义

**"研究材料已经准备好，可以交给人工做最终事实确认"**。
不是"日期已经确认"。允许 candidate date conflict；允许 reviewer=pending / reviewed_at=null。
Start/End/Peak 人工最终确认（Verified Date 产生）+ reviewer/reviewed_at 填写 + RESEARCH_UNCERTAINTY 裁决 + MAPPING_BLOCKER 解除，是 **READY_FOR_PROMOTION** 的条件。已写入 promotion_gate_v1.md v1.1 第 2/3 节。

### 11. 哪些是 HUMAN_REVIEW_BLOCKER

- 三条正式候选（C-2022-POLICY / C-2023-AD / C-2024-ROBOTAXI）：reviewer=pending、reviewed_at=null、Verified Date 未产生。
- 解除 = 人工最终 Review。

### 12. 哪些是 RESEARCH_UNCERTAINTY

| Campaign | 字段 | DB Candidate | Research Review Candidate |
|---|---|---|---|
| C-2022-POLICY | start | 2022-04-27 | 2022-05-23 |
| C-2024-ROBOTAXI | peak | 2024-07-29 | 2024-08-05 |
| C-2024-ROBOTAXI | end | 2024-07-31 | 2024-08-23 |

不阻断 READY_FOR_HUMAN_REVIEW；阻断 READY_FOR_PROMOTION，直到人工裁决。

### 13. 哪些是 MODEL_BLOCKER

- Phase 无 Cycle 落点（research-only）
- Campaign.classification 无 Cycle 落点（留 package，可人工并入 description）
- Evidence 三审计字段（evidence_role / independence_group / temporal_relation）无落点
- Source tier / publisher 无落点（审计链由 package 承载）
- Research Event（具体日期事件）≠ Cycle Event（日历规则事件），NOT_SUPPORTED

默认全部接受，不扩 Cycle Schema。

### 14. 当前是否可以开始人工最终 Review

**可以。** 三条正式候选的研究材料（证据、绑定、来源合法性、mapping 规则、checklist、日期双口径记录）已全部齐备，处于 READY_FOR_HUMAN_REVIEW。人工 Review 的任务清单：裁决 2 项日期口径 → 确认 Start/End/Peak 为 Verified Date → 确认 MAPPING_BLOCKER 个案 → 填写 reviewer/reviewed_at。

---

## 本轮产出

### 新增

1. `research/promotion/source_mapping_v1.md` — Source 12→6 映射提案 + tier 三方案比较
2. `research/promotion/promotion_mapping_matrix_v1.md` — 11 实体映射矩阵 + Blocker 分类法
3. `PROMOTION_MAPPING_RED_TEAM_V1_1.md` — 本报告

### 更新

4. `research/promotion/cycle_mapping_v1.md` → v1.1（Phase 修正、Source/Evidence/桥表/Validation 修正、日期三层术语、Campaign 字段逐一核对）
5. `research/promotion/promotion_gate_v1.md` → v1.1（三状态重定义、晋级条件分层 3.A/3.B、日期三层术语、Blocker 分类法）
6. `research/promotion/promotion_summary.md` → v1.1（状态表按真实 mapping 标注、删除"日期已确认"、Blocker 分类）
7. `research/promotion/checklists/*_promotion_checklist.md`（3 份：Phase → research-only；Cycle mapping → TRANSFORM 口径）
8. `HISTORICAL_FACT_PROMOTION_GATE.md`（顶部勘误声明，原文保留作历史记录）

### 未更新（经判断不需要）

- `RESEARCH_MODEL_V1_FREEZE_REPORT.md`：本轮不涉及 Research Model 语义变更，Phase 属于 Research Model 的事实不变（变的只是它不进 Cycle）。
- `promotion_manifest.json` / `validate_promotion_manifest.py`：状态名与校验逻辑在 v1.1 语义下仍然成立（READY_FOR_HUMAN_REVIEW 允许 reviewer=pending），无需改动。

---

## 不变确认

- ❌ 未修改 Cycle（任何文件）
- ❌ 未修改 Cycle-Research Schema / SQLite 数据 / campaigns / annual_reviews
- ❌ 未写入 Cycle/data/verified
- ❌ 未修改 Research Model v1.0
- ❌ 未新增历史数据

---

## 测试结果

| 测试项 | 结果 |
|---|---|
| validate_promotion_manifest.py | ✅ PASS（5/5） |
| validate_db.py | ✅ PASS（0 警告） |
| export.py | ✅ PASS（evidence isolation 通过） |
| gen_annual.py / gen_summary.py | ✅ PASS |
| check_doc_schema_consistency.py | ✅ PASS（0 FAIL） |
| test_doc_schema_checker.py | ✅ PASS |
| calibrate_robotaxi.py | ✅ PASS（9/9） |
| point_in_time_robotaxi.py | ✅ PASS |
| test_consistency.py | ✅ PASS（0 FAIL, 0 WARNING） |

**总计：0 FAIL，0 WARNING**

---

**版本**：Promotion Mapping Red Team v1.1
**状态**：文档修正完成，等待人工最终 Review
