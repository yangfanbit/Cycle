# Promotion Mapping Matrix v1.0

> Research → Cycle 全实体映射矩阵（Red Team v1.1 终审版）。
> 版本：v1.0
> 日期：2026-09-13
> Cycle 侧事实来源：`Cycle/src/models/*.ts`（本轮已只读核实）。
> Mapping 取值：DIRECT / TRANSFORM / RESEARCH_ONLY / NOT_SUPPORTED。

---

## 1. 总览矩阵

| Entity | Research | Cycle | Mapping | Loss / Transform | Blocker |
|---|---|---|---|---|---|
| Rule | research_rules | Rule | TRANSFORM | base_pattern→base_sector；status `confirmed`↛`verified`（Cycle 规定 verified 需真实统计来源）；rule_type / tags / updated_at 晋级时生成 | MAPPING_BLOCKER（status、rule_type 规则待定；本轮不晋级 Rule） |
| Theme | themes + campaign_themes | Theme + CampaignTheme | **DIRECT** | 无。theme_type 枚举一致（sector/concept/industry），role 枚举一致（main/secondary/catalyst/related） | 无 |
| Campaign | campaigns | HistoricalCampaign | TRANSFORM | season_id 格式转换（`summer_2023`→`2023`）；cross_year 由 promotion layer 计算；source_id 由 manifest 派生（Research campaigns 无此列，Cycle 必填）；classification **无落点**；start/end_date_basis 长文本→枚举（observed/inferred/official_event/unknown）；drift_* / research_notes / annual_review_id 留 Research | HUMAN_REVIEW_BLOCKER（reviewer pending）；RESEARCH_UNCERTAINTY（2022 start、2024 peak/end 口径）；MODEL_BLOCKER（classification 无落点） |
| Phase | campaign_phases | **无实体** | **RESEARCH_ONLY** | 不持久化。Phase 保留在 Research；Cycle 当前仅承载 HistoricalCampaign 主体；未来如需展示再单独设计 | MODEL_BLOCKER（仅当未来需要展示时才构成阻碍；当前非晋级必要条件） |
| Event | events + campaign_events（具体日期事件：policy/company/market） | Event（**日历规则**事件：date_rule = fixed/range/variable） | **NOT_SUPPORTED** | 语义不同：Research Event 是"某年某月某日发生的具体事件"，Cycle Event 是"每年重复的日历规则"。不映射 | MODEL_BLOCKER（如未来需要） |
| Evidence | evidences | Evidence | TRANSFORM | evidence_type 中文自由文本→枚举（行情数据→market_data；政策文件→official；行业月度产销数据/行业数据→market_data 或 other，需逐条确认）；evidence_role / independence_group / temporal_relation **无落点**，完整保留在 promotion package | MAPPING_BLOCKER（evidence_type 个案规则）；MODEL_BLOCKER（3 个审计字段无落点） |
| CampaignEvidence | campaign_evidences 桥表（多对多 + role） | Evidence.campaign_id（单值可选 FK，无桥表） | TRANSFORM（**条件：evidence 唯一归属一个 Campaign**） | 桥表 role 丢失，留 package。当前形式成立：validator 已强制 evidence 不跨 Campaign；若未来一条证据服务多 Campaign，单值 FK 将不足，届时需 Cycle 侧重新设计（不得擅自加表） | MODEL_BLOCKER（多归属场景；当前不触发） |
| Security | securities + campaign_securities | Security + CampaignSecurity | **DIRECT**（已核实） | 无。exchange 全部为 SH/SZ ⊆ Cycle 枚举（SH/SZ/BJ）；role 枚举一致（leader/second_leader/representative/follow）；Cycle sector? 可选留空 | 无 |
| Source | sources | Source | TRANSFORM | source_type 12→6 映射（见 source_mapping_v1.md）；tier / publisher **无落点**；审计链由 promotion package 保留（source_id + tier） | MODEL_BLOCKER（tier/publisher 无落点）；MAPPING_BLOCKER（other 及个案类型需人工指定） |
| Validation | 无 ValidationRecord 实体；核验事实散见于 promotion manifest（reviewer/reviewed_at）与 campaign_date_observations | ValidationRecord | TRANSFORM（**晋级时新建**） | validation_scope='campaign'；campaign_id 必填；evidence_status='L2'（事实核验完成）；verification_status **不得写 statistically_supported**（L2 ≠ 规律成立，Cycle 模型注释明确规定）；reviewer/reviewed_at 来自人工确认；method_version 必填 | HUMAN_REVIEW_BLOCKER（reviewer/reviewed_at 未填写） |
| Point-in-Time | campaign_date_observations / market_series / market_daily / trading_calendar | **无对应实体** | RESEARCH_ONLY | PIT 基础设施整体留在 Research，不进入 Cycle | 无（设计如此，非阻碍） |

---

## 2. 关键红队结论

1. **真正 DIRECT 的只有 Theme 与 Security**（枚举与桥表角色经逐值核实一致）。
2. **Campaign 是 TRANSFORM 而非直接映射**：season_id 格式、cross_year 计算、source_id 派生、classification 无落点，四处都必须显式处理。
3. **Phase / Event / Point-in-Time 在当前 Cycle 无落点**：RESEARCH_ONLY 或 NOT_SUPPORTED，不伪装成可映射。
4. **Evidence 映射是有损的**：evidence_role、independence_group、temporal_relation 三个审计字段在 Cycle 无落点，必须依赖 promotion package 保留完整审计链。
5. **Validation 是晋级时新建**：Research 没有现成 ValidationRecord 可搬；且 L2 事实核验 ≠ statistically_supported，两者不得混淆（Cycle 模型层即有此约束）。

---

## 3. Promotion Blocker 分类法

| 类别 | 定义 | 当前实例 |
|---|---|---|
| DATA_BLOCKER | 晋级所需数据缺失或不合法 | 当前无（三条正式候选的必填数据已齐） |
| MAPPING_BLOCKER | 映射规则未定或存在个案歧义 | source_type 个案（other/协会/媒体细分）；evidence_type 中文→枚举逐条规则；Rule status/rule_type 规则（本轮不涉及 Rule 晋级） |
| HUMAN_REVIEW_BLOCKER | 等待人工最终确认 | 三条正式候选 reviewer=pending、reviewed_at=null；Start/End/Peak 待最终确认 |
| MODEL_BLOCKER | Cycle 当前模型无落点 | Phase 无实体；classification 无字段；Evidence 三审计字段无落点；Source tier/publisher 无落点；Event 语义不同 |
| RESEARCH_UNCERTAINTY | 研究内部口径未收敛 | C-2022-POLICY start：04-27（DB Candidate）vs 05-23（Research Review Candidate）；C-2024-ROBOTAXI peak/end：07-29/07-31（DB Candidate）vs 08-05/08-23（Research Review Candidate） |

**解除路径**：

- HUMAN_REVIEW_BLOCKER + RESEARCH_UNCERTAINTY → 人工最终 Review 解除（下一轮）。
- MAPPING_BLOCKER → 晋级执行前由人工逐条确认映射个案。
- MODEL_BLOCKER → 默认接受（审计链由 promotion package 承载）；仅当 Cycle 未来扩模型时解除。
- DATA_BLOCKER → 当前无。

---

**版本**：v1.0
**状态**：ACTIVE（Red Team v1.1 终审）
