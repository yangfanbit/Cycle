# CHANGELOG.md — 变更记录

## 2026-09-12 · V1.5 第一阶段：历史规律核验基础建设（第四轮）

### 新增：核验规范与数据结构

- `docs/HISTORICAL_VALIDATION.md`（新）：Historical Campaign 定义（含 peak_date）、
  启动/结束日期判定（observed / inferred / official_event / unknown + confidence）、
  结果分类（允许失败年份）、Base Pattern ≠ Annual Theme、Cross-Year 规则、
  Evidence 概念、人工优先原则、统计预留（本轮不计算）。
- 模型新增：`Evidence`（src/models/evidence.ts）、`ValidationRecord` / `PilotPlan`
  （src/models/validation.ts）、`RawExcerpt`（src/models/source.ts）。
- `HistoricalCampaign` 扩展可选字段：peak_date、start_date_basis、end_date_basis、date_confidence。
  既有种子数据回填真实判定：cmp_auto_2023/2024 = inferred/low，cmp_media_2026_2027 = unknown/low。

### 新增：data/ 四层数据目录（自 src/data 迁入）

```
data/raw/        sources.ts（来源注册表）、excerpts.ts（材料原文摘录，13 条）
data/candidate/  rules.ts、campaigns.ts、themes.ts、events.ts（V1 种子整体迁入）
data/verified/   campaigns.ts（L2 已核验事实，当前 0 条）
data/validation/ evidence.ts（6 条证据）、records.ts（3 条核验记录）、pilot.ts（3 条 Pilot）
```

- `src/data/index.ts` 改为纯 re-export barrel，所有应用代码 import 路径不变，零 UI 改动。
- 诚信处理：材料"提及广电 2021/2022/2023"但无任何细节 → 仅登记 L1 证据线索，
  **不创建 Campaign**（防编造最小事实原则）。

### 3 条 Pilot 核验数据骨架

| Pilot | evidence_status | verification_status | 说明 |
|-------|-----------------|---------------------|------|
| 夏季汽车 | L1 | not_tested | 材料：2023减速器 / 2024自动驾驶；候选 Campaign 日期 inferred/low |
| 年底广电 | L1 | not_tested | 材料：2021—2023 年份提及，无细节，未建 Campaign |
| 国庆后大消费 | L0 | not_tested | 仅经验窗口，无年份案例证据 |

### 文档修订

- AGENTS.md：概念链加入 Evidence；阅读顺序加入 HISTORICAL_VALIDATION.md；
  data/ 修改留痕义务。
- DATA_MODEL.md：新增第 11/12 节（Evidence / ValidationRecord / PilotPlan）、
  Campaign 字段更新、数据位置说明。
- DATA_GOVERNANCE.md：Evidence 原则、数据目录治理、V1.5 核验数据基线。
- ARCHITECTURE.md：数据层目录结构、测试覆盖更新。
- ROADMAP.md：V1.5 拆分为三阶段，第一阶段标记完成。

### 测试

- 23 → 33 项（新增「V1.5 核验数据完整性」10 项：证据引用、跨年日期约束、
  unknown/null 合法性、L2 ≠ statistically_supported 不变式、失败年份不过滤、
  Base Pattern 与 Annual Theme 并存、一 Base 多 Theme、Pilot 骨架、verified 层为空、
  仅年份提及不产生 Campaign）。
- 验证：`npx tsc -b` 通过；`npm test` 33/33 通过；`npm run build` 成功。

### 未做（按阶段边界停止）

- 未做历史行情数据接入 / 全市场回测 / 自动识别 Campaign / UI 改造 / SQLite 迁移。
- 3 条 Pilot 的历史事实核验等待人工 Review 后启动。

---

## 2026-09-12 · 规范微调（第三轮）

规范微调：区分 Evidence Status 与 Verification Status；重新定义前瞻性分析与确定性预测的边界。

### 文档修改（仅文档，未改业务代码）

- `AGENTS.md`
  - 第 2 节新增「两个独立维度：证据 ≠ 验证」（Evidence L0–L4 / Verification 五态，强调 L2 ≠ 规律成立）。
  - 「永不输出预测」改写为「前瞻性分析 ≠ 确定性预测」：禁止确定性预测/保证收益/买卖建议/必涨必跌/自动交易信号；
    允许历史统计、情景分析、前瞻性观察窗口。
  - 第 6 节红线同步补充。
- `docs/DATA_GOVERNANCE.md` — 数据等级重构为 Evidence Status + Verification Status 双维度，
  增加与当前 `Rule.status` 字段的映射表（字段拆分列入 ROADMAP，本轮不改代码）。
- `docs/DATA_MODEL.md` — Rule 章节与差异记录补充双维度说明。
- `docs/PRODUCT.md` — 新增「前瞻性分析 ≠ 确定性预测」章节（禁止项 / 允许项 / UI 文案边界）。
- `docs/ROADMAP.md` — V1.5 补充双字段评估与"历史统计特征"表述约束；V3 改为情景分析框架表述。

### 业务代码

- 无修改。现有 `Rule.status` 字段与新双维度语义无冲突（映射表已记录，拆分留待 V1.5）。

### 验证

- `npm test`：23/23 通过。
- `npx tsc -b`：通过。

---

## 2026-09-12 · 规范补救与架构一致性检查（第二轮）

### 新增（治理文档体系）

- `AGENTS.md` — 项目宪法：定位、数据认知边界（Source ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction）、
  Agent 开发原则、冲突处理、最小修改原则、产品红线。
- `docs/PRODUCT.md` — 产品定义：核心价值、核心对象、四层时间轴、跨年原则、V1 不做清单。
- `docs/DATA_MODEL.md` — 10 个实体的当前实际字段 + 差异记录。
- `docs/DATA_GOVERNANCE.md` — 数据等级 L0–L4、Source 原则、禁止行为、「缺少数据是合法状态」、种子数据诚信边界。
- `docs/ARCHITECTURE.md` — 当前实际架构（非理想状态）：技术栈、组件结构、跨年/Pre-heat 实现方式、测试方式。
- `docs/UI_SPEC.md` — UI 原则：时间轴为视觉中心、四层视觉、跨年延续表达、文案红线。
- `docs/ROADMAP.md` — V1 / V1.5 / V2 / V3 / V4 阶段划分。

### 边界明确

- Source / Rule / Historical Fact / Verification / Prediction 的语义边界写入 AGENTS.md 第 2 节。
- 跨年规则（自然年只是显示容器、Campaign 不得拆条）写入 PRODUCT.md 与 DATA_MODEL.md。

### 代码修改（最小修复）

- `src/components/RuleDetail/RuleDetail.tsx`
  - 修复：相对事件窗口的详情文案原样显示内部 ID（`evt_spring_festival`），
    现通过 `eventById` 解析为事件名（「春节」）。属于数据语义/可用性 Bug 的最小修复。

### 测试

- 扩展 `src/utils/__tests__/timeline.test.ts`：18 → 23 个用例，新增「数据治理规范」分组：
  种子数据零 verified、缺失案例返回空数组、CampaignTheme 引用完整、缺失关联不抛异常、
  跨年种子行情双视图年延续分段。
- 未引入第二套测试框架。

### 未做的事

- 未重构任何业务模块；未改变产品定位；未接入实时行情/资金流/AI；未新增功能。

---

## 2026-09-12 · V1 第一阶段开发（第一轮）

- 初始化 Vite + React 18 + TypeScript 项目。
- 建立 10 个实体数据模型（`src/models/`）。
- 录入种子数据：2 来源 / 16 题材 / 7 事件 / 10 候选规律 + 窗口 / 3 历史行情。
- 实现四层时间轴、TODAY、跨年延续渲染、Pre-heat 四态、详情抽屉、未来关注窗口。
- 建立 18 个 Vitest 单元测试。
