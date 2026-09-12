# CHANGELOG.md — 变更记录

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
