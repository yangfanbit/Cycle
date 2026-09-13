# Promotion Summary

> Historical Fact Promotion Summary: Research Campaign 晋级状态总结（Red Team v1.1 修正版）。
> 日期：2026-09-13
> v1.1 修正：Phase 不再声称 1:1 映射（NOT PERSISTED IN CURRENT CYCLE）；
> 日期不再描述为"已确认"（三层术语：DB Candidate / Research Review Candidate / Verified）；
> Mapping 状态按 promotion_mapping_matrix_v1.md 真实结论标注。

---

## 1. 晋级状态总览

| Research Campaign | Status | Target Cycle ID | Date（DB Candidate） | Evidence | Mapping | Blocker |
|---|---|---|---|---|---|---|
| **C-2022-POLICY** | READY_FOR_HUMAN_REVIEW | null | 2022-04-27 ~ 2022-08-31 | 5 evidences, 4 groups | TRANSFORM（规则已备） | HUMAN_REVIEW_BLOCKER + RESEARCH_UNCERTAINTY（start 口径） |
| **C-2023-AD** | READY_FOR_HUMAN_REVIEW | null | 2023-06-12 ~ 2023-07-19 | 7 evidences, 7 groups | TRANSFORM（规则已备） | HUMAN_REVIEW_BLOCKER |
| **C-2024-ROBOTAXI** | READY_FOR_HUMAN_REVIEW | null | 2024-07-08 ~ 2024-07-31 | 4 evidences, 4 groups | TRANSFORM（规则已备） | HUMAN_REVIEW_BLOCKER + RESEARCH_UNCERTAINTY（peak/end 口径） |
| **RC-2023-HUAWEI** | RESEARCH_CANDIDATE | null | 2023-09-12 ~ (ongoing) | 0 evidences | 研究候选，不映射 | 未达到正式 Campaign 门槛 |
| **RC-2024-SECONDARY** | RESEARCH_CANDIDATE | null | 2024-09-05 ~ 2024-09-06 | 0 evidences | 研究候选，不映射 | 未达到正式 Campaign 门槛 |

---

## 2. 详细说明

### 2.1 READY_FOR_HUMAN_REVIEW（3 个）

> READY_FOR_HUMAN_REVIEW = **研究材料已准备好，可以交给人工做最终事实确认**。
> 不代表日期已最终确认。允许 candidate date conflict；允许 reviewer=pending。

#### C-2022-POLICY
- **状态**: READY_FOR_HUMAN_REVIEW
- **DB Candidate Date**: 2022-04-27 ~ 2022-08-31，peak 2022-06-10
- **证据**: 5 条，4 个独立组
- **阻碍**: HUMAN_REVIEW_BLOCKER（reviewer=pending）；RESEARCH_UNCERTAINTY（start 口径）

**说明**: 2022 Auto Policy Campaign，04-27 行业修复/Setup，05-23 国常会购置税政策启动，06-10 峰值，08-31 结束。中通客车为 Observation（核酸检测车概念），不计入 Campaign 主线。

**待人工裁决（RESEARCH_UNCERTAINTY）**：start 的 DB Candidate = 2022-04-27（Setup 起点）；Research Review Date Candidate = 2022-05-23（Theme Formation / 政策催化日）。manifest 严格镜像冻结 DB，不自行升级日期。

#### C-2023-AD
- **状态**: READY_FOR_HUMAN_REVIEW
- **DB Candidate Date**: 2023-06-12 ~ 2023-07-19，peak 2023-07-11
- **证据**: 7 条，7 个独立组
- **阻碍**: HUMAN_REVIEW_BLOCKER（reviewer=pending）

**说明**: 2023 Smart Driving Campaign，06-12 启动，07-11 峰值，07-19 结束。Huawei Auto 为 Research Candidate (RC-2023-HUAWEI)，不进入正式 Campaign。

#### C-2024-ROBOTAXI
- **状态**: READY_FOR_HUMAN_REVIEW
- **DB Candidate Date**: 2024-07-08 ~ 2024-07-31，peak 2024-07-29
- **证据**: 4 条，4 个独立组
- **阻碍**: HUMAN_REVIEW_BLOCKER（reviewer=pending）；RESEARCH_UNCERTAINTY（peak/end 口径）

**说明**: 2024 Robotaxi Campaign，07-08 萝卜快跑武汉跑出圈，07-29 峰值（DB Candidate），07-31 结束（DB Candidate）。09-05~06 为 Weak Secondary Campaign Candidate，不进入正式 Campaign。

**待人工裁决（RESEARCH_UNCERTAINTY）**：peak/end 的 DB Candidate = 2024-07-29 / 2024-07-31；Research Review Date Candidate = peak 2024-08-05（EW 等权指数 raw 峰值）、first decline 2024-08-06、Main End 2024-08-23。两套口径留待人工 Review 最终判断。

---

### 2.2 RESEARCH_CANDIDATE（2 个）

#### RC-2023-HUAWEI
- **状态**: RESEARCH_CANDIDATE
- **日期**: 2023-09-12 ~ (ongoing)
- **证据**: 0 条
- **阻碍**: 未达到正式 Campaign 门槛

**说明**: Huawei Auto 2023 Research Candidate，08-29 Early Signal Candidate，09-04 Theme Formation，09-12 Campaign Start Candidate。当前仍为研究候选，未达到正式 Campaign 门槛。

#### RC-2024-SECONDARY
- **状态**: RESEARCH_CANDIDATE
- **日期**: 2024-09-05 ~ 2024-09-06
- **证据**: 0 条
- **阻碍**: 未达到正式 Campaign 门槛

**说明**: 2024 Robotaxi Secondary Campaign Candidate，09-05~06 Weak Secondary。当前仍为研究候选，未达到正式 Campaign 门槛。

---

## 3. Promotion Blocker（分类法见 promotion_gate_v1.md 第 6 节）

### 当前阻碍

| 类别 | 实例 | 影响范围 |
|---|---|---|
| HUMAN_REVIEW_BLOCKER | reviewer=pending；reviewed_at=null；Verified Date 未产生 | 3 条正式候选 |
| RESEARCH_UNCERTAINTY | 2022 start（04-27 vs 05-23）；2024 peak/end（07-29/07-31 vs 08-05/08-23） | 2 条正式候选 |
| MODEL_BLOCKER | Phase 无 Cycle 落点；classification 无落点；Evidence 三审计字段无落点；Source tier/publisher 无落点 | 全部（默认接受，审计链由 promotion package 承载） |
| MAPPING_BLOCKER | source_type 个案；evidence_type 中文→枚举规则 | 晋级执行前需人工逐条确认 |
| DATA_BLOCKER | 无 | — |

### 解除阻碍的条件

要进入 READY_FOR_PROMOTION，必须：

1. 人工 reviewer 最终确认，填写 reviewer 与 reviewed_at
2. Start / End / Peak 人工最终确认（Verified Date 产生，含两套口径的裁决）
3. MAPPING_BLOCKER 个案逐条人工确认
4. 将 promotion_status 从 READY_FOR_HUMAN_REVIEW 升级为 READY_FOR_PROMOTION

---

## 4. Cycle 字段映射（摘要；详见 promotion_mapping_matrix_v1.md / cycle_mapping_v1.md）

| 实体 | Mapping | 要点 |
|---|---|---|
| Campaign | TRANSFORM | season_id 格式转换；cross_year 计算；source_id 由 manifest 派生；classification 无落点留 package |
| Theme | DIRECT | theme_type / role 枚举经核实一致 |
| Security | DIRECT | exchange 全部 SH/SZ；role 枚举一致 |
| Source | TRANSFORM | 12→6 source_type 映射（source_mapping_v1.md）；tier/publisher 无落点，审计链由 package 保留 |
| Evidence | TRANSFORM | evidence_type 中文→枚举；evidence_role/independence_group/temporal_relation 留 package |
| CampaignEvidence | TRANSFORM | 桥表 → Evidence.campaign_id 单值 FK（条件：evidence 唯一归属 Campaign，validator 已强制） |
| Phase | RESEARCH_ONLY | **NOT PERSISTED IN CURRENT CYCLE** |
| Event | NOT_SUPPORTED | Research 具体日期事件 ≠ Cycle 日历规则事件 |
| Validation | TRANSFORM（晋级时新建） | scope=campaign；evidence_status=L2；**verification_status ≠ statistically_supported** |
| Point-in-Time | RESEARCH_ONLY | PIT 基础设施整体留 Research |

---

## 5. cross_year 计算

### 定义

```python
cross_year = year(end_date) > year(start_date)
```

### 当前候选（按 DB Candidate Date）

| Campaign | start_date | end_date | cross_year |
|---|---|---|---|
| C-2022-POLICY | 2022-04-27 | 2022-08-31 | false |
| C-2023-AD | 2023-06-12 | 2023-07-19 | false |
| C-2024-ROBOTAXI | 2024-07-08 | 2024-07-31 | false |

**约束**：
- cross_year 由 promotion layer 计算，不得人工复制空值
- 当前三条候选全部为 false
- 若人工 Review 改判日期，cross_year 重新计算

---

## 6. Phase 处理（v1.1 修正）

**Phase mapping: NOT PERSISTED IN CURRENT CYCLE**

- Research 有 campaign_phases；当前 Cycle 无 CampaignPhase 实体/正式落点（已核实 Cycle/src/models/）。
- Phase 保留在 Research；Cycle 当前仅承载 HistoricalCampaign 主体。
- 未来如需展示 Phase，再单独设计。
- Phase 不构成当前 Promotion Gate 的必要条件。

---

## 7. Evidence 映射（v1.1 修正）

- Research Evidence = 完整研究审计数据；Cycle Evidence = 生产展示所需的最小证据实体。
- 字段级映射与桥表处理见 cycle_mapping_v1.md 第 6/7 节。
- 审计链保证：promotion package 保留 Research Evidence 原始 ID 与完整信息（含 role / independence_group / temporal_relation / tier）。

---

## 8. ValidationRecord 映射（v1.1 修正）

- Research 无 ValidationRecord 实体；晋级时在 Cycle 新建。
- validation_scope='campaign'；evidence_status='L2'；verification_status **禁止 statistically_supported**（L2 事实核验 ≠ 规律统计成立）。
- reviewer=pending 或 reviewed_at=null → 不得 READY_FOR_PROMOTION。

---

## 9. 三条 Campaign 是否都准备好人工最终 Review

**✅ 是的（按 v1.1 定义）**

READY_FOR_HUMAN_REVIEW 的准确含义：**研究材料已齐，可交付人工做最终事实确认**。

- ✅ Campaign 判定成立
- ✅ 候选日期已整理（DB Candidate + Research Review Candidate 均已记录）
- ⏳ Start / End / Peak **未最终确认**（Verified Date 待人工产生——这是人工 Review 的任务，不是前置条件）
- ✅ Evidence >= 2
- ✅ independent_group >= 2
- ✅ Source Tier 合法
- ✅ Point-in-Time 边界明确
- ✅ 无严重 temporal conflict
- ✅ Cycle mapping 规则已备（TRANSFORM 项均已定义）
- ✅ Theme / Security mapping 完整（DIRECT）
- ℹ️ Phase = research-only，不持久化，非必要条件
- ⏳ reviewer 未填写（pending）
- ⏳ reviewed_at 未填写（null）

**下一步**：人工 reviewer 最终确认 → 裁决 RESEARCH_UNCERTAINTY → 填写 reviewer/reviewed_at → 升级为 READY_FOR_PROMOTION。

---

## 10. 是否实际修改 Cycle

**✅ 未修改**

**确认**：
- Cycle 未修改
- Cycle/data/verified 未修改
- 本轮仅修正映射文档认知，未实际写入 Cycle

---

**版本**：v1.1
**状态**：READY_FOR_HUMAN_REVIEW
