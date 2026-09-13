# Promotion Gate v1.1

> Historical Fact Promotion Gate：定义 Research Campaign 何时允许进入 Cycle。
> 版本：v1.1
> 日期：2026-09-13
> v1.1 修正：重新定义三状态语义——READY_FOR_HUMAN_REVIEW 不再含"日期已人工确认"，
> Start/End/Peak 人工最终确认是 READY_FOR_PROMOTION 的条件；新增日期三层术语与 Blocker 分类法。

---

## 1. 目的

本文档定义 Research Campaign 进入 Cycle 的晋级标准（Promotion Gate），确保只有经过严格人工/研究确认的历史事实才能进入 Cycle 生产环境。

---

## 2. 三个状态（v1.1 重定义）

### 2.1 RESEARCH_CANDIDATE

**定义**：研究不足，尚不能进入人工最终审核流程的候选。

**特征**：
- 证据不足（evidence < 2 或独立证据组 < 2）
- 未达到正式 Campaign 门槛
- 需要进一步研究

**示例**：
- RC-2023-HUAWEI（Huawei Auto 2023）
- RC-2024-SECONDARY（2024 Robotaxi Secondary，09-05~06）

---

### 2.2 READY_FOR_HUMAN_REVIEW

**定义**：**研究材料已经准备好，可以交给人工做最终事实确认。**

**含义（必须准确理解）**：
- ✅ 证据已达到人工审核条件（数量、独立性、绑定、来源合法性齐备）
- ✅ 结构完整（manifest、mapping、checklist 齐备）
- ❌ **不代表正式事实已最终确认**
- ❌ **不代表 Start/End/Peak 已确认**

**允许**：
- 允许存在 candidate date conflict（DB Candidate Date 与 Research Review Date Candidate 不一致）
- 允许 reviewer = "pending"
- 允许 reviewed_at = null

**示例**：
- C-2022-POLICY（2022 Auto Policy）
- C-2023-AD（2023 Smart Driving）
- C-2024-ROBOTAXI（2024 Robotaxi）

---

### 2.3 READY_FOR_PROMOTION

**定义**：人工最终确认已经完成，满足 L2 事实核验标准，可以进入 Cycle verified。

**必须**：
- reviewer ≠ "pending"（已填写真实 reviewer）
- reviewed_at ≠ null（已填写）
- **Start / End / Peak 已经人工最终确认（Verified Date 已产生）**
- 全部 RESEARCH_UNCERTAINTY 已裁决
- 无未解除的 MAPPING_BLOCKER

**约束**：
- 只有 READY_FOR_PROMOTION 才允许进入 `Cycle/data/verified/`

---

## 3. 晋级标准（Promotion Gate）

### 3.A 进入 READY_FOR_HUMAN_REVIEW 的条件（研究完整性）

1. **Campaign 已达到历史事实核验标准**：符合 Campaign 判定标准（非 Observation）；有明确主题、持续性、市场关注；可解释 start/end
2. **至少 2 个独立 Evidence**：evidence_count >= 2 且 independent_evidence_groups >= 2
3. **Evidence 显式通过 campaign_evidences 绑定**：不允许 unbound evidence 作为晋级依据
4. **Source / Tier 合法**：tier 在 1–4 范围内，source_type 与 tier 不矛盾
5. **Point-in-Time 与 Retrospective 没有混淆**：PIT 仅用当时已公开信息；Retrospective 明确标注 hindsight；两者不混用
6. **Campaign ≠ Observation**：不得为个股异动/单日脉冲/零散新闻
7. **不存在未解决的关键时间因果错误**：无 look-ahead bias / survivorship bias / beta contamination
8. **date_confidence 不为 low**：当前三条正式候选均为 medium（campaigns.date_confidence），满足

### 3.B 进入 READY_FOR_PROMOTION 的条件（人工最终确认）

在 3.A 全部满足的基础上，还必须：

9. **Start / End / Peak 已有人工作出最终判断**：Verified Date 已产生（见第 4 节三层术语）
10. **人工 reviewer 与 reviewed_at 已明确**：reviewer ≠ "pending" 且 reviewed_at ≠ null
11. **全部 RESEARCH_UNCERTAINTY 已裁决**：候选日期冲突已有人工结论
12. **无未解除的 MAPPING_BLOCKER**：映射个案已逐条人工确认

> 说明：第 9–12 项**不是** READY_FOR_HUMAN_REVIEW 的条件。当前三条正式候选停留在 READY_FOR_HUMAN_REVIEW 正是因为第 9–11 项未完成。

---

## 4. 日期三层术语（v1.1 新增）

| 层级 | 定义 | 当前状态 |
|---|---|---|
| **DB Candidate Date** | campaigns 表中当前记录的研究候选日期（冻结 DB 值） | 已固定，不改 |
| **Research Review Date Candidate** | 研究报告中提出的备选口径 | 已记录，待裁决 |
| **Verified Date** | 人工最终确认后的日期；写入 Cycle 的唯一合法值 | 不存在 |

当前 RESEARCH_UNCERTAINTY 实例：

| Campaign | 字段 | DB Candidate Date | Research Review Date Candidate |
|---|---|---|---|
| C-2022-POLICY | start | 2022-04-27（Setup 起点） | 2022-05-23（Theme Formation / 政策催化日） |
| C-2024-ROBOTAXI | peak | 2024-07-29 | 2024-08-05（EW 等权指数 raw 峰值） |
| C-2024-ROBOTAXI | end | 2024-07-31 | 2024-08-23（Main Campaign End Candidate，首次回落 08-06 之后） |

**禁止**：在人工 Review 完成前，把任何一层日期描述为"已经最终确认"。

---

## 5. Promotion Checklist

每个 Campaign 晋级前必须完成以下检查（详见 checklists/ 目录逐 Campaign 清单）：

- [ ] Campaign 判定成立
- [ ] Start 最终确认（→ Verified Date）
- [ ] End 最终确认（→ Verified Date）
- [ ] Peak 最终确认（→ Verified Date）
- [ ] Evidence >= 2
- [ ] independent_group >= 2
- [ ] Source Tier 合法
- [ ] Point-in-Time 边界明确
- [ ] 无严重 temporal conflict
- [ ] reviewer 已填写
- [ ] reviewed_at 已填写
- [ ] Cycle mapping 完整（含 TRANSFORM 项规则确认）
- [ ] Phase 处理已明确（当前 = research-only，不持久化，非晋级必要条件）
- [ ] Theme mapping 完整
- [ ] Security mapping 完整

---

## 6. Promotion Blocker 分类法（v1.1 新增）

| 类别 | 定义 | 当前实例 |
|---|---|---|
| DATA_BLOCKER | 晋级所需数据缺失或不合法 | 当前无 |
| MAPPING_BLOCKER | 映射规则未定或个案歧义 | source_type 个案；evidence_type 中文→枚举规则 |
| HUMAN_REVIEW_BLOCKER | 等待人工最终确认 | reviewer=pending；reviewed_at=null；Verified Date 未产生 |
| MODEL_BLOCKER | Cycle 当前模型无落点 | Phase 无实体；classification 无字段；Evidence 三审计字段无落点；Source tier/publisher 无落点 |
| RESEARCH_UNCERTAINTY | 研究内部口径未收敛 | 2022 start（04-27 vs 05-23）；2024 peak/end（07-29/07-31 vs 08-05/08-23） |

**解除路径**：HUMAN_REVIEW_BLOCKER 与 RESEARCH_UNCERTAINTY 由人工 Review 解除；MAPPING_BLOCKER 由人工逐条确认解除；MODEL_BLOCKER 默认接受（审计链由 promotion package 承载）。

---

## 7. 默认策略

当前三条正式候选：
- C-2022-POLICY
- C-2023-AD
- C-2024-ROBOTAXI

**默认状态**：READY_FOR_HUMAN_REVIEW

**原因**：研究材料已齐（3.A 全部满足），但人工最终 reviewer 尚未正式写入、Verified Date 尚未产生（3.B 未完成）。

---

## 8. 禁止事项

- 禁止修改 Cycle
- 禁止修改 Cycle-Research 核心 Schema
- 禁止修改 Research Model
- 禁止写入 Cycle/data/verified/
- 禁止正式提升任何 Research Candidate
- 禁止在人工确认前把候选日期描述为"已确认"

---

**版本**：v1.1
**状态**：ACTIVE（Red Team v1.1 修正版，替代 v1.0）
