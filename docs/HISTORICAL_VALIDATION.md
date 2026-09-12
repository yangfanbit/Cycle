# HISTORICAL_VALIDATION.md — 历史规律核验规范

本文件定义"经验 → 证据 → 历史事实 → 验证 → 统计"链条中，**核验阶段**的全部规范。
任何 Agent 录入 / 修改核验数据（`data/`）前必须先阅读本文件。

概念链：

```
Source（来源） → Evidence（证据） → Historical Fact / Campaign（历史事实） → Verification（验证） → 统计
```

---

## 1. 什么是 Historical Campaign

一次真实发生的、具有一定持续性的板块 / 题材行情过程。

字段（`src/models/campaign.ts`，实体定义见 docs/DATA_MODEL.md）：

| 字段 | 说明 |
|------|------|
| campaign_id | 主键 |
| rule_id | 所属候选规律 |
| season_id | 行情季：年内如 "2023"，跨年如 "2026-2027" |
| campaign_year | 起始年份 |
| start_date / end_date | 完整 ISO 日期（YYYY-MM-DD） |
| peak_date | 行情峰值日期；未核验时为 null（合法状态） |
| cross_year | 是否跨自然年 |
| strength | strong / medium / weak |
| result | positive / neutral / weak / failed / unknown |
| start_date_basis / end_date_basis | 日期判定方式（见第 2、3 节） |
| date_confidence | high / medium / low |
| description / source_id | 描述与来源 |

**Campaign ≠ Rule**：Rule 是待验证的规律假设；Campaign 是具体某年发生过（或材料提及）的行情记录。一条 Rule 下可以有多个年份的 Campaign，包括失败年份。

## 2. 启动（start_date）定义

V1.5 第一阶段采用**人工核验机制**，不做自动识别。

启动日期必须标注判定方式（`start_date_basis`）：

| basis | 含义 |
|-------|------|
| observed | 人工从行情数据中观察确认 |
| inferred | 由典型窗口 / 材料推断（近似值） |
| official_event | 依据官方事件日期（如披露期起止） |
| unknown | 未知 |

同时记录 `date_confidence`（high / medium / low）。

**禁止伪造精确日期**：无法确认时用 `unknown` + 低 confidence，或干脆不创建 Campaign 记录。

## 3. 结束（end_date）定义

同第 2 节（`end_date_basis` + `date_confidence`）。

约束：`end_date >= start_date`（不允许负持续时间）；跨年时 `cross_year = true` 且 end 年份 > start 年份。

## 4. 结果分类

`result`：`positive | neutral | weak | failed | unknown`

**必须允许失败案例**。历史案例表不得只保存成功年份，例如一条 Rule 的逐年记录：

```
2018: failed
2019: weak
2020: unknown
2021: positive
2022: positive
```

为了让规律"看起来成立"而删除失败年份，属于最严重的治理违规（见 DATA_GOVERNANCE.md）。

## 5. Base Pattern 与 Annual Theme

- **Base Pattern**：底层季节性方向（如"汽车""大消费""广电 / 传媒"），对应 Theme 树的 sector 层。
- **Annual Theme**：某一年实际出现的具体炒作题材（如 2023 减速器、2024 自动驾驶），对应 concept 层，通过 `parent_theme_id` 挂在 Base Pattern 下。

两者**不能混淆**：同一年汽车行情的题材是"减速器"而非"汽车"；同一年大消费行情可能由"食品饮料"或"旅游"不同子方向驱动。模型上通过 Theme 父子层级 + CampaignTheme（role: main / secondary / catalyst / related）表达。

## 6. Cross-Year

自然年 ≠ Campaign 生命周期。

- 一场跨年行情是**一条完整记录**：`2026-11-01 → 2027-01-15` 记为 `season_id: "2026-2027"`、`campaign_year: 2026`、`cross_year: true`，不得拆成两条。
- 跨年形态不写死：11月→次年1月、12月→次年2月、春节前→春节后等任意形态都必须支持。
- UI 上两段共享视觉延续；详情必须显示完整生命周期。

## 7. Evidence（证据）

**Evidence 是证据，不是结论**。它只记录"某来源在某时说了 / 显示了什么"。

字段（`src/models/evidence.ts`）：evidence_id, source_id, evidence_type, description, date（可 null）, confidence, 可选关联（rule_id / campaign_id / theme_id）。

evidence_type：`market_data | article | official | news | manual_review | other`

关系：Source → Evidence → Historical Fact / Campaign。Evidence 是从来源通往历史事实的中间层：人工核验时，一条 Campaign 的日期 / 强度 / 结果应能指向支撑它的 Evidence。

## 8. 人工优先，程序校验

第一阶段**不做自动判断**：程序不得自动认定"某板块涨了 X% = 一个 Campaign"。

程序只负责：

- 数据结构承载
- 完整性校验（引用存在性）
- 日期校验（起止顺序、跨年一致性）
- 跨年校验（不拆条）
- 关系校验（Rule / Campaign / Theme / Evidence / Source 引用链）

程序化识别（L3 统计）留待模型稳定后的后续阶段。

## 9. 数据真实性原则

禁止：编造历史案例、编造启动 / 结束日期、编造龙头、编造涨幅、编造胜率、编造统计分数。

合法空状态：`null` / `unknown` / `pending` / `not_verified` / "待补充"。

**不要为了让页面好看而补数据。**

## 10. ValidationRecord（核验记录）

字段（`src/models/validation.ts`）：validation_id, rule_id, campaign_id?, evidence_status, verification_status, reviewer, created_at, reviewed_at, notes, method_version。

记录的是"事实是否核验"，**不计算 seasonality_score 等统计分数**。

审计字段语义：

- `created_at`：核验记录的**建立日期**。
- `reviewed_at`：**人工核验完成日期**（`string | null`）。
  未核验时 `reviewer = 'pending'` 且 `reviewed_at = null`——
  **没有核验人就不得有核验完成日期**，两者必须同时成立。

两个独立维度（详见 DATA_GOVERNANCE.md）：

- Evidence Status（L0—L4）：掌握了多少历史证据
- Verification Status（not_tested / under_review / statistically_supported / cross_validated / unsupported）：规律是否已通过验证

**L2 ≠ statistically_supported**：完成历史事实核验只说明"历史事实已被整理"，是否构成稳定规律需要统计验证。

## 11. 统计预留

未来支持：launch_date_median, launch_date_std, duration_median, excess_return, repeat_rate, seasonality_score 等。

**本轮全部不计算、不产生任何数值**。所有 Rule 的 statistics 保持 `{ status: 'not_verified' }`，直到有可追溯的统计方法论（写入 methodology 字段）。

## 12. 数据目录

```
data/
  raw/         原始数据（sources 来源注册表 + excerpts 材料摘录）
  candidate/   未经核验的候选知识（rules + windows, campaigns, themes, events）
  verified/    已人工核验的历史事实（当前 0 条）
  validation/  证据（evidence）、核验记录（records）、Pilot 计划（pilot）
```

升层（candidate → verified）必须在 CHANGELOG.md 留痕。

## 12A. Preflight 数据语义决策（2026-09-12，历史核验前清理）

本轮解决"候选经验 / 测试示例 / 历史事实"之间的语义污染，为人工核验做准备：

### 方案 A：未核验线索不进入行情层

- **结构示例不是历史行情**：需求文档的跨年结构示例（2026-11-01 → 2027-01-15）
  已从 `data/candidate/campaigns.ts` 移至 `tests/fixtures/campaignFixtures.ts`，
  生产层与测试数据彻底分离。禁止测试数据回到 `data/` 目录。
- **candidate 层不再承载未核验 HistoricalCampaign**：材料提及的年度题材
  （2023 汽车=减速器、2024 汽车=自动驾驶）只保留在 Evidence 记录中，
  不以 Campaign 形态存在——避免 `inferred/low` 日期被误读为历史事实。
- **人工核验完成后**，真实 HistoricalCampaign 直接写入 `data/verified/campaigns.ts`（L2），
  不经过 candidate 层。生产层聚合入口 `allCampaigns = [...verifiedCampaigns]`。
- Timeline 第三层语义改为「**已核验历史行情**」：verifiedCampaigns 为空时显示
  「暂无已核验历史行情（历史核验尚未开始）」，不为填充页面而混入 candidate 数据。
- 未来如需展示候选线索，应另做「候选历史线索」视图并采用明显区别于
  verified 的视觉样式（列入 ROADMAP，本轮不做）。

### 市场日期基准

- A 股"今天"统一使用 `marketTodayISO()`（Asia/Shanghai），不依赖用户机器时区。
- 纯日期运算（diffDays / addDaysISO 等）仍使用 UTC 毫秒，两者分离。

## 13. V1.5 Pilot（3 条样本规律）

| Pilot | 规律 | 窗口 | 用途 | 当前状态 |
|-------|------|------|------|----------|
| 1 夏季汽车 | rule_auto_summer | 约6—8月 | 季节性行业 + Annual Theme 切换 | L1：材料提及 2023减速器 / 2024自动驾驶，仅存 Evidence（无 Campaign） |
| 2 年底广电 | rule_media_year_end | 约11月—次年1月中旬 | 跨年 + 小板块 + 题材 + 龙头 + 生命周期 | L1：材料提及 2021/2022/2023，但无任何年份细节，未创建 Campaign |
| 3 国庆后大消费 | rule_consumption_year_end | 国庆后—春节 | 大行业 + 多 Theme + 跨年 | L0：仅经验窗口描述，无年份案例证据 |

三条 Pilot 均为 `verification_status: not_tested`，等待人工 Review 后进入历史事实核验。

大消费核验特别注意：**不要先验地**把食品饮料 / 商业零售 / 旅游 / 纺织服装 / 教育 / 传媒归并为同一 Campaign——一个 Base Pattern 可对应多个 Theme，一个时间窗口可包含多个相关 Campaign，以核验到的事实为准。
