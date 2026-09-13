# Source Mapping v1.0

> Research Source → Cycle Source 映射提案（Red Team v1.1）。
> 版本：v1.0
> 日期：2026-09-13
> 性质：**提案文档**。不修改 Cycle，不修改 Research Schema，不写 verified。

---

## 1. 结论先行

**Source 不是直接映射（不是 DIRECT）。**

Research `source_type` 有 12 类，Cycle `source_type` 只有 6 类；
Research 有 `tier`（1–4）与 `publisher`，Cycle 没有。

因此 Source 映射 = **TRANSFORM**：类型枚举需显式转换规则，`tier` / `publisher` 在 Cycle 当前模型中无落点。

---

## 2. 两侧模型对照（以真实代码为准）

### Research `sources`（schema.sql）

| 字段 | 说明 |
|---|---|
| source_id | PK |
| source_type | 12 类：exchange / regulator / company_announcement / industry_association / media_tier2 / media_tier3 / media_tier4 / research_report / website / forum_blog / social_media / other |
| title / author / url / published_at / captured_at / publisher / description | |
| **tier** | 1–4（Tier 4 只能做线索） |

### Cycle `Source`（Cycle/src/models/source.ts，已只读核实）

| 字段 | 说明 |
|---|---|
| source_id | |
| source_type | 6 类：personal / article / official / research / market_data / quant_verification |
| title / author? / url? / published_at? / captured_at / description? | |

**Cycle 没有 `tier`，没有 `publisher`。**

---

## 3. source_type 映射提案

| Research source_type | Cycle source_type | 判定原则 |
|---|---|---|
| exchange | official | 交易所披露 = 官方 |
| regulator | official | 监管机构 = 官方 |
| company_announcement | official | 公司公告 = 官方 |
| industry_association | official（默认）/ research | 协会发布的政策说明、统计、标准 → official；协会发布的研究性报告 → research |
| media_tier2 | article | 权威媒体报道 = 文章 |
| media_tier3 | article（默认）/ research | 普通媒体 → article；深度研究性报道 → research |
| media_tier4 | article / personal | 正规媒体渠道 → article；署名自媒体评论 → personal。**不改变证据等级含义**：tier 4「只能做线索」的语义不随类型映射丢失（见第 4 节） |
| research_report | research | 研报 = 研究 |
| website | article（默认）/ personal | 机构网站 → article；个人站点 → personal |
| forum_blog | personal（默认）/ article | 论坛/个人博客 → personal；机构博客 → article |
| social_media | personal | 社交媒体 = 个人表达 |
| other | 不允许静默映射 | 必须逐条人工指定，否则留在 promotion package 不导入 |

**反向说明**：Cycle 的 `market_data` / `quant_verification` 两类在 Research `source_type` 中无对应。
Research 的行情数据经由 `market_series.provider` + `market_daily` 承载，不走 `sources.source_type`。
晋级时如需为行情证据配 Source，应新建 `market_data` 类型 Source（属晋级执行动作，本轮不执行）。

**通用判定原则**：
1. 官方性优先：发布主体是公权力/交易所/公司/协会官方 → official。
2. 研究属性其次：内容是研究分析而非消息报道 → research。
3. 发表形式兜底：署名个人/社交表达 → personal；其余媒体内容 → article。
4. 个案存疑 → 不映射，保留在 promotion package，等待人工裁决（MAPPING_BLOCKER）。

---

## 4. tier 的处理（Cycle 无 tier 字段）

`tier = 1–4` 是 Research 证据分级体系的核心事实，**不允许丢失**。

三种方案比较：

| 方案 | 做法 | 优点 | 缺点 |
|---|---|---|---|
| A | 导入 Cycle 时丢弃 tier | 零成本 | 审计链断裂，证据等级含义永久丢失。**不可接受** |
| B | 把 tier 编码进 description | 不扩 schema | 污染正文字段，机器不可读，违背 Cycle「description 保留来源口吻」的语义 |
| C | 未来 Cycle 新增 evidence provenance metadata | 语义正确 | 需要改 Cycle，超出本轮权限 |

**默认推荐**：

- **现在不扩 Cycle Schema**（方案 C 留给未来，由 Cycle 项目自行决策）。
- **不采用 A；不采用 B 作为正式机制**。
- **promotion package 必须保留 `research source_id` + `research tier`**：
  - `promotion_manifest.json` 的每条 Campaign 保留 `source_id` 与 `evidence_ids`；
  - 每条 Evidence 的 tier 可通过 `evidence_id → evidences.source_id → sources.tier` 在 Research 库中完整回溯；
  - 晋级执行时，在 Cycle Evidence 之外交付一份 provenance 清单（research source_id ↔ cycle source_id ↔ tier），保证审计链不断。

---

## 5. publisher 的处理

Cycle Source 无 `publisher` 字段。

- publisher 信息保留在 Research `sources` 表与 promotion package。
- 不向 Cycle `description` 拼接 publisher（避免污染原始口吻字段）。
- 判定为 MODEL_BLOCKER（轻）：字段无落点，但不阻碍晋级，因为审计链由 promotion package 承载。

---

## 6. 约束

- 本文档仅为映射提案，**不修改 Cycle 任何文件**。
- 个案映射（industry_association / media_tier3 / media_tier4 / website / forum_blog / other）在晋级执行时必须逐条人工确认。
- tier 语义（Tier 4 只能做线索）不因映射而改变。

---

**版本**：v1.0
**状态**：PROPOSAL（待人工确认）
