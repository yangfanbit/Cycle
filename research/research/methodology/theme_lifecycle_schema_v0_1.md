# Theme Lifecycle Schema Proposal v0.1（Pilot 1-C1.6：设计方案 + Red Team）

> 纯设计提案。**不改** `schema.sql` / `db.py` / 正式数据 / 不创建 `theme_cycles` / `campaign_relations` 表。
> 基于 2022 / 2023 / 2024 三个真实案例，目标是提出**下一版 Theme Lifecycle 模型**的候选设计，并对它做红队压力测试。
> 层级目标：`Seasonal Rule → Theme Cycle → Campaign → Phase → Event / Evidence / Security`。

---

## 1. Entity Definitions（对象语义）

| Entity | 回答的问题 | 本质 | 例子 |
|---|---|---|---|
| **SeasonalRule** | 历史上什么时间/条件值得观察 | **Research Hypothesis / Prior** | rule_auto_summer（6-8月观察窗口，非结论） |
| **ThemeCycle** | 一段时期内、同属主题家族、可能含多 Campaign 的研究归组 | **Research Entity（归组）** | auto_intelligence_2023（Smart Driving→Huawei Auto） |
| **Campaign** | 历史上是否发生一轮有持续性的主题行情 | **核心 Historical Market Event** | 2023 Huawei Auto（09-12起）、2024 Robotaxi Main（07-08→08-23） |
| **Phase** | Campaign 内部发生了什么阶段变化 | **Campaign 的组成阶段**（非线性，非硬编码状态机） | EARLY_SIGNAL / THEME_FORMING / CONFIRMED / MAIN_RISE / PEAK / DECLINING / SECONDARY / ENDED |
| **Event** | 什么可能触发/强化/解释行情 | **因子/背景** | 05-23 国常会600亿；09-12 M7上市 |
| **Evidence** | 凭什么知道 | **支撑**（supporting/contradicting/context；temporal_relation） | 当日行情数据、媒体报道 |
| **Security** | 行情载体 | **标的** | 赛力斯、德赛西威、比亚迪 |

> 三层：SeasonalRule=Prior（假设）；ThemeCycle=Grouping（第3层）；Campaign/Phase=Interpretation（第2层）；Event/Evidence/Security/Market 数据=第1层（Fact）。

## 2. 关键属性

**ThemeCycle**：`theme_cycle_id, year(可空,允许多年), name, theme_family, description, status, confidence`
- `status ∈ candidate/under_review/confirmed/weak/rejected`（**confirmed=研究确认，非市场事实**）；`confidence ∈ high/medium/low`。
- 归属 rule：`theme_cycle_id.rule_id → research_rules(rule_id)`（可空：若某 cycle 不严格附属于单一 rule）。

**Campaign**（沿用现有 campaigns，新增 `theme_cycle_id` 外键、可选）：`start/end/peak, strength, classification, result, confidence/status`。
- peak/end **可空**（进行中/未定）。

**Phase（campaign_phases，已有表）**：`phase_id, campaign_id, phase_type(EARLY_SIGNAL/THEME_FORMING/CONFIRMED/MAIN_RISE/PEAK/DECLINING/SECONDARY/ENDED), start_date, end_date(可空), confidence, notes`。
- **非线性**：真实 A 股可 Peak→Secondary，或 MAIN_RISE→Retracement→再 MAIN_RISE；故 Phase 是**有序记录列表**，非状态机状枚举。

**CampaignRelation（一等研究对象）**：`relation_id, from_campaign_id, to_campaign_id, relation_type(overlap/theme_drift/continuation/secondary/replacement/unrelated), confidence, notes`。
- overlap/theme_drift 不是 Campaign 字段，而是**关系**，可显式表达。

**Point-in-Time（Research Observation）**：`campaign_id(可空), phase_id(可空), security_id(可空), observation_date, identified_securities, evidence`——不是替代 ThemeCycle/Campaign 的对象，而是可关联它们的研究观测。

**Event / Evidence / Security**：沿用现有（events / evidences / securities）。

## 3. ERD（Entity Relationship Diagram）

```
SeasonalRule (research_rules)
   ├─1─* ─ ThemeCycle ─1─*─ Campaign ─1─*─ Phase(campaign_phases)
   │                      │  ├─1─*─ campaign_relations (self: from→to Campaign)
   │                      │  ├─*─*─ Event  (campaign_events)
   │                      │  ├─*─*─ Evidence(campaign_evidences)
   │                      │  └─*─*─ Security(campaign_securities)
   │                      └─ *─ Point-in-Time observations (campaign_id/phase_id/security_id 可空引用)
   └─ (事实层) Evidence─*─1 Source ; Security; Event
```

## 4. Cardinality

- SeasonalRule 1..* ThemeCycle（一个观察窗口可跨年产生多个 theme cycle）
- ThemeCycle 1..* Campaign
- Campaign 1..* Phase（0..* 允许）
- Campaign M..N Campaign（经 campaign_relations，自引用）
- Campaign M..N Event / Evidence / Security（桥表）
- ThemeCycle  0..* Point-in-Time observations

## 5. Foreign Keys

- `theme_cycles.rule_id → research_rules(rule_id)`（可空）
- `campaigns.theme_cycle_id → theme_cycles(theme_cycle_id)`（可空，兼容既有 Campaign）
- `campaign_phases.campaign_id → campaigns`
- `campaign_relations.from_campaign_id / to_campaign_id → campaigns`（均非空，且 `from<>to`）
- 既有桥表（campaign_events/evidences/securities）沿用外键。
- Point-in-Time：`campaign_id/phase_id/security_id` 可空引用对应表。

## 6. Nullable Rules

- ThemeCycle.year 可空（多年 cycle）；status 默认 `candidate`；confidence 默认 `low`。
- Campaign.peak/end 可空；classification/result 非空。
- Phase.end_date 可空（进行中）；start_date 非空。
- campaign_relations：from/to、relation_type 非空；confidence 可空默认 low。
- 既有表不新增必填约束以免破坏。

## 7. Fact vs Interpretation vs Grouping（三层）

| 层 | 内容 | 例 | 特征 |
|---|---|---|---|
| **1 Fact** | 可核验的客观数据 | “赛力斯 2023-09-04 收 40.58，当日+10.7%” | 由行情/交易所/公告确定 |
| **2 Interpretation** | 对 Fact 的解释 | “09-04 是华为汽车 Theme Formation” | 可商榷，需证据 |
| **3 Grouping** | 把对象归到研究组 | “Smart Driving 与 Huawei Auto 同属 auto_intelligence_2023” | 纯研究归组，最不可直接当作市场事实 |

**ThemeCycle 最属于第 3 层（Grouping）**。任何对第3层的统计都应标注“基于研究归组，非市场客观结论”。

## 8. ThemeCycle（重点设计）
- 作为 **Research Entity（归组）**，带 status + confidence。
- **不要把“主题变化”自动当成“新 Theme Cycle”**：Smart Driving → Huawei Auto 的迁移记为 ThemeCycle 内部事件（theme_drift），仍属同一 cycle。

## 9. CampaignRelation
- `from→to + relation_type`，一等研究对象。**不把 overlap/theme_drift/continuation/secondary/replacement 塞进 Campaign 字段**。
- 表达力：2023 Smart Driving → Huawei Auto＝`theme_drift`（+时间 overlap）；2024 Main → Secondary＝`secondary`；2022 中通客车 vs 主 line＝`unrelated`（或可略）。

## 10. CampaignPhase
- 已有表（campaign_phases），新增 phase_type 枚举（EARLY_SIGNAL/THEME_FORMING/CONFIRMED/MAIN_RISE/PEAK/DECLINING/SECONDARY/ENDED）作为扩展；**保持非线性记录式**。

## 11. Point-in-Time
- Research Observation，可关联 campaign/phase/security；**不是替代对象**。用于表达“某历史日期当时可识别的 core set”（如 07-10 4 只、08-29 华为 early candidate）。

## 12. 2022 压力测试
用模型表达（不改既有事实）：
- Phase：04-27＝`EARLY_SIGNAL/THEME_FORMING`（行业修复 Setup）→ 05-23＝`THEME_FORMING`（国常会600亿）→ 05-31＝Event(`policy`，细则) → 06-23/06-28＝Phase `PEAK`（cluster，可记两条或标注 cluster）→ 07＝`DECLINING` → 08＝`ENDED/decline_cluster`。
- 中通客车：独立 `Campaign`（classification=`event_driven`），与主 line 关系＝`unrelated`；不并入主 theme 强度。
- ✅ 可表达，无需改事实。

## 13. 2023 压力测试
- Campaign1＝Smart Driving（合同 theme_cycle_id=auto_intelligence_2023）；Campaign2＝Huawei Auto（同 cycle）。
- Phase（Campaign2）：08-29＝`EARLY_SIGNAL(candidate, medium/low)` → 09-04＝`THEME_FORMING` → 09-12＝Event(`company`) → 09-18＝`CONFIRMED/Broad` → 09-28~10＝`MAIN_RISE`。
- CampaignRelation：Smart Driving → Huawei Auto＝`theme_drift`（overlap 08-29~09-12）→ **支持 overlap，不要求 A.end<B.start**。
- ✅ 可表达（含 overlap + drift），无需改事实。

## 14. 2024 压力测试
- Campaign1＝Robotaxi Main（theme_cycle_id=robotaxi_2024）：Phase 08-06＝`DECLINING`(peak 08-05＝`PEAK`)，08-23＝`ENDED/breakpoint`。
- Campaign2＝Secondary（09-05~06）：Phase `SECONDARY`（weak）；CampaignRelation：Main → Secondary＝`secondary`。
- ✅ 可表达，无需改事实。

## 15. Migration Risks（迁移风险）
1. 现有 `campaigns` 需新增 `theme_cycle_id`（默认 NULL）——不破坏既有。
2. ThemeCycle 归组是**主观解释**，迁移后可能把解释固化，影响未来统计中性。
3. campaign_relations 自引用 + campaign_phases 扩展：表数量增加、查询更复杂。
4. Point-in-Time observations 新表：需从现有 evidence/notes 抽取，重。
5. 既有 2018-2025 annual_reviews/campaigns 日期若与 theme_cycle 归组冲突，需人工调和（本轮**不动**）。

---

## Red Team（反对意见）

1. **是否只是人为归组？** 是——Theme Cycle 完全是解释性归组（第3层）。同一年也可被归为不同 cycle 而不“错”。
2. **是否会过度复杂？** 会——新增 theme_cycles + campaign_relations +（扩展）phases + point-in-time，表结构显著膨胀，收益未必线性。
3. **更简单替代？** 有——把 `theme_cycle_id`、`Theme Drift`、`Overlap` 作为 campaign 上的 **research 标签/research-level 文件**（如现有 2023_theme_timeline.md），不建表。
4. **是否导致未来统计困难？** 会——一旦归组入库，跨 cycle 统计（如 win-rate 按 theme_cycle）会因归组主观性引入偏差/自证；需非常小心地把“分组假设”与“统计结论”切割（当前项目明确不做 seasonality/win-rate，故不迫切）。
5. **CampaignRelation 是否真的需要表？** 可缓——目前仅 2023 出现 overlap+drift；可用 `notes`/research 标签表达；等出现≥3 组真实 relation 再建表更稳。
6. **Phase 是否已经足够？** 大部分够——重叠/漂移本质可用“两个 Campaign 各自有重叠时间区间 + 一条关系注释”表达；Phase 表已有。
7. **ThemeCycle 是否应只是 research-level？** 是——它是 Grouping， резидент研究，天然属于 research-level，不必入库。

### RECOMMENDATION

**B. 保留 research-level（暂不正式进入 Schema）。**

理由：
- ThemeCycle / CampaignRelation 本质是 **Interpretation（第2层）与 Grouping（第3层）**，不是历史事实；入库会把这些解释固化，增加对未来统计中性性的污染风险。
- 当前仅 3 个（且 2 个存在 overlap/drift edge）案例，样本不足以支撑 schema 的普适设计；过度提前形式化会引入“为了建模而建模”。
- 更简单替代（theme_cycle_id 作 research 标签 + 现有 timeline 文件 + 既有 campaign_phases）已能表达三案例，无需新表。
- **路径**：继续以 research-level 收集（theme_cycle_id 标签、关系记录在 report），待人工确认三个案例的 verified 日期、且 overlap/drift 关系累计到足够样本后，再评估是否把 `theme_cycles` + `campaign_relations` 提升为正式 schema（届时最小化：仅这两表 + campaign.theme_cycle_id 外键）。

> 附注：本轮不改 schema / db / 数据；2023-08-29 明确为 **Early Signal Candidate（confidence low→medium）**，不作 confirmed。

---

*本文件为设计方案 + 红队；未被采纳。*