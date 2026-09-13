# Promotion Gate v1.0

> Historical Fact Promotion Gate：定义 Research Campaign 何时允许进入 Cycle。
> 版本：v1.0
> 日期：2026-09-13

---

## 1. 目的

本文档定义 Research Campaign 进入 Cycle 的晋级标准（Promotion Gate），确保只有经过严格人工/研究确认的历史事实才能进入 Cycle 生产环境。

---

## 2. 三个状态

### 2.1 RESEARCH_CANDIDATE

**定义**：尚不能进入 Cycle 的研究候选。

**特征**：
- 证据不足
- 未达到正式 Campaign 门槛
- 需要进一步研究

**示例**：
- RC-2023-HUAWEI（Huawei Auto 2023）
- 2024 Robotaxi Secondary（09-05~06）

---

### 2.2 READY_FOR_HUMAN_REVIEW

**定义**：研究证据与结构已齐，等待人工最终确认。

**特征**：
- 满足所有研究标准
- 等待人工 reviewer 最终确认
- 尚未写入 reviewer / reviewed_at

**示例**：
- C-2022-POLICY（2022 Auto Policy）
- C-2023-AD（2023 Smart Driving）
- C-2024-ROBOTAXI（2024 Robotaxi）

---

### 2.3 READY_FOR_PROMOTION

**定义**：人工确认完成，满足 L2，可以进入 Cycle verified。

**特征**：
- 人工 reviewer 已填写
- reviewed_at 已填写
- 所有晋级标准已满足

**约束**：
- 只有 READY_FOR_PROMOTION 才允许进入 `Cycle/data/verified/`

---

## 3. 晋级标准（Promotion Gate）

一个 Research Campaign 允许进入 Cycle，必须至少满足以下全部条件：

### 3.1 Campaign 已达到历史事实核验标准

- 符合 Campaign 判定标准（非 Observation）
- 有明确主题、持续性、市场关注
- 可解释 start/end

### 3.2 Start / End / Peak 已有人工作出最终判断

- start_date 已经人工确认
- end_date 已经人工确认
- peak_date 已经人工确认（如适用）

### 3.3 date_confidence 满足要求

- date_confidence 为 high 或 medium
- 不允许 low

### 3.4 至少 2 个独立 Evidence

- evidence_count >= 2
- independent_evidence_groups >= 2

### 3.5 Evidence 显式通过 campaign_evidences 绑定

- 所有 evidence 必须通过 campaign_evidences 桥表显式绑定
- 不允许 unbound evidence 作为晋级依据

### 3.6 Source / Tier 合法

- 所有 source 的 tier 必须在 1-4 范围内
- source_type 与 tier 不矛盾

### 3.7 Point-in-Time 与 Retrospective 没有混淆

- PIT 研究仅用当时已公开信息
- Retrospective 研究明确标注使用 hindsight
- 两者不得混用

### 3.8 Campaign ≠ Observation

- 必须符合 Campaign 判定标准
- 不得为个股异动/单日脉冲/零散新闻

### 3.9 不存在未解决的关键时间因果错误

- 无 look-ahead bias
- 无 survivorship bias
- 无 beta contamination

### 3.10 人工 reviewer 与 reviewed_at 已明确

- reviewer 已填写
- reviewed_at 已填写
- 不允许 reviewer = "pending" 或 reviewed_at = null

---

## 4. Promotion Checklist

每个 Campaign 晋级前必须完成以下检查：

- [ ] Campaign 判定成立
- [ ] Start 最终确认
- [ ] End 最终确认
- [ ] Peak 最终确认
- [ ] Evidence >= 2
- [ ] independent_group >= 2
- [ ] Source Tier 合法
- [ ] Point-in-Time 边界明确
- [ ] 无严重 temporal conflict
- [ ] reviewer 已填写
- [ ] reviewed_at 已填写
- [ ] Cycle mapping 完整
- [ ] Phase mapping 完整
- [ ] Theme mapping 完整
- [ ] Security mapping 完整

---

## 5. Promotion Blocker

以下情况将阻止晋级：

1. **证据不足**：evidence_count < 2 或 independent_evidence_groups < 2
2. **日期未确认**：start_date / end_date / peak_date 未经人工最终确认
3. **reviewer 未填写**：reviewer = "pending" 或 reviewed_at = null
4. **mapping 不完整**：Cycle mapping / Phase mapping / Theme mapping / Security mapping 未完成
5. **研究候选**：promotion_status = RESEARCH_CANDIDATE

---

## 6. 默认策略

当前三条正式候选：
- C-2022-POLICY
- C-2023-AD
- C-2024-ROBOTAXI

**默认状态**：READY_FOR_HUMAN_REVIEW

**原因**：当前人工最终 reviewer 尚未正式写入。

---

## 7. 禁止事项

- 禁止修改 Cycle
- 禁止修改 Cycle-Research 核心 Schema
- 禁止修改 Research Model
- 禁止写入 Cycle/data/verified/
- 禁止正式提升任何 Research Candidate

---

**版本**：v1.0
**状态**：ACTIVE
