# 试点报告：2018 / 2019 / 2020 汽车夏季窗口

> 依据任务停止条件：完成数据库结构、研究脚本、模板后，仅进行 2018–2019–2020 三年试运行，**不**一口气批量写完其余年份。
> 本报告是对三年试运行经验的评估，含：数据模型是否够用、哪些歧义、是否出现 Wave、字段调整建议、三年初步结果。

---

## 0. v1.5 Schema Fix（数据关系修复，已实施）

试运行暴露的核心问题是 **Campaign ↔ Evidence 无显式关联**：旧 `export.py` 会把全库证据导入每个 Campaign。本轮已完成修复：

```
Campaign  ↕  CampaignEvidence  ↕  Evidence  ↕  Source
```

- **新增 `campaign_evidences(campaign_id, evidence_id, role)` 桥表**，显式绑定每个 Campaign 与其真实证据；`export.py` 现只经桥表取证据（隔离测试 PASS：C-2019-AD 3 条 / C-2020-NEV 4 条，无交叉）。
- **`evidences.independence_group`**：同源转引（`same_origin_xxx`）与真正独立来源（不同 group）分开标记。**“媒体数量” ≠ “独立证据数量”。**
- **Confirmed 门槛程序化检查**：`scripts/validate_db.py` 校验 Confirmed Campaign 需 ≥2 条证据且 ≥2 个独立组。
- **Source Tier 修复**：`S-2020-03` / `S-2020-04` 由 `media_tier3` 改为 `media_tier4`（实属雪球经验帖 Tier4）；sources 表已全局复核，`source_type` 与 `tier` 一致。
- **日期 basis 兼容设计**：未来推荐拆分为 `*_basis_code`（observed/inferred/official_event/unknown）+ `*_basis_note`，本轮未迁移旧文本字段（不破坏试点）。
- **2018–2020 结论未变化**：2018 `no_clear_campaign`、2019 `weak`、2020 `strong`，保持不变。

---

## 1. 数据模型是否够用

**基本够用。** `sources → evidences → research_rules → annual_reviews → campaigns → (themes/events/securities/phases)` 关系能承载大多数场景。

能覆盖的能力：
- **反例年份**：2018 判为 `no_clear_campaign`，能在不创建 Campaign 的情况下保存 `contradicting` 证据——这是最关键的纪律验证点。
- **弱窗口尾部**：2019 判为 `weak`，用 `event_driven` 而非 `theme_campaign`，避免把一次脉冲误当主线。
- **强主题**：2020 判为 `strong`，干净地承载 `theme_campaign` + 龙头 + Wave。

**不够用 / 缺省的三处：**
1. **Campaign ↔ Evidence 关联未建模**。`evidences` 目前靠 `date`/`source` 与年份松散关联，缺少 `campaign_id`（或 `annual_review_id`）外键。要回答"这个 Campaign 到底由哪几条证据支撑"（尤其"至少 2 条独立证据"判定），需要一个显式的 `campaign_evidences` 桥表。
2. **证据独立性标签**。要求"至少 2 条独立证据"，但 `evidences` 没有 `independence_source`（是否是同一份来源转引）字段。建议加 `independence_notes`。
3. **Season 概念松散**。`campaigns.season_id` 目前只是文本（`summer_2019`）。后续若扩展到多个 Base Pattern，建议单独 `seasons` 表。

## 2. 出现哪些歧义

- **2019 到底是"无 Campaign"还是"一个弱 Campaign"？**
  - 倾向：8 月中下旬—9 月的无人驾驶/智能汽车行情更像**事件驱动脉冲**而非整车主线。已判 `weak` + `event_driven`，并在 research_notes 说明。
  - 待定：如果后续加入 8–9 月完整日线数据，可能需合并进"9 月智能驾驶"或拆分多段。**不要急于合并。**

- **2020 的窗口真实起点**。
  - 明确信号是 6/11 特斯拉涨停潮；但 Tier4 线索提示整车全年或自 4 月底启动。
  - 结论：`start_date=2020-06-01` 是"观察窗口内信号鲜明"的保守起点，需用日线行情二次核验是否提前到 4 月底。**"典型启动日期"研究必须在日线数据上映证后下沉为 Fact。**

- **classification 判定在 2019/2023 边界模糊**。
  - 主题"无人驾驶"严格说不属于"整车 Base Pattern"主轴，更偏 `concept`。本试点仍归入 `rule_auto_summer` 底下，因为它是 6—8 月窗口内与汽车关联度最高的资金主线；但建议标记 `industry_trend / event_driven` 以区分。

## 3. Wave / Phase 问题

- **2020 明确出现 Wave**：`startup(6/1) → main_rise(6/11-7/13) → retracement(7/14-8/20) → secondary_rally(8/21-)`，与 Tier4 线索"比亚迪 8/21 二次启动破 100"一致。`campaign_phases` 表能表达。
- **关键缺口**：这些 Phase 数据 80% 来自 Tier4 经验帖，**置信度低**。必须用**个股/板块日线行情**二次核验后才算 Research Fact。决议：Phase 仅"证据充分时"记录——2020 属可记但标 low；2018/2019 不记。
- **二次启动/回流字段不足**：一个 Campaign 若由多个 Wave 组成，建议在 `campaigns` 增加 `wave_count`、`had_secondary_rally`（布尔）两个派生字段，便于跨年统计"多少次行情是先退潮再回流"。

## 4. 字段调整建议（下一阶段实施）

| 位置 | 调整 | 理由 |
|---|---|---|
| `campaign_evidences`（新） | campaign_id + evidence_id + role | 显式绑定 Campaign 与其证据，落实"≥2 独立证据" |
| `evidences` | 加 `independence_notes` | 判断证据是否同源转引 |
| `campaigns` | 加 `wave_count`、`had_secondary_rally` | 支持 Wave 跨年统计 |
| `campaigns` | `strength` 建议收编为枚举（strong/medium/weak）并 `CHECK` | 现为自由文本 |
| `seasons` | 独立表（season_id, name, months, base_pattern_id） | 为多 Base Pattern 扩展铺路 |
| `evidences` | 支持关联 `campaign_id` 或 `annual_review_id` | 默认数据归属清晰 |

> 上述为**建议**，需你在人工 Review 后决定是否采纳；本试点按当前 schema 运行，不加字段。

## 5. 三年初步结果（试运行，未经人工确认）

| 年 | status | Campaign | classification | 起点漂移 | 主主题 | strength/result | 龙头 | 证据质量 |
|---|---|---|---|---|---|---|---|---|
| 2018 | `no_clear_campaign` | — | — | —（无） | 无 | — | — | contradicting ×3，Tier2，high |
| 2019 | `weak` | C-2019-AD | event_driven | +75d / vs6-1 | 智能驾驶/无人驾驶 | weak / weak | 万安科技 | supporting ×2(medium) + contradicting |
| 2020 | `strong` | C-2020-NEV | theme_campaign | 0d / vs6-1 | 特斯拉产业链/新能源 | strong / positive | 比亚迪、宁德时代 | supporting ×2(high) + 线索 ×2(low) |

### 关键观察（非结论）
1. **三年不都是有效年份**：2018 明确无 Campaign（反例）。这直接削弱"6—8 月汽车=每年都有一波"的朴素认知。
2. **主题在演化**：三年里"汽车"被实例化为不同的金额主线——2019 智驾、2020 特斯拉/新能源。印证 **Base Pattern → Annual Theme → Campaign** 模型的必要性。
3. **窗口漂移确实存在**：2019 靠近窗口尾部（约 8/15 起，相对 8/1 +14 天）；2020 在窗口起点。
4. **证据来源以 Tier2/3 为主**，缺 Tier1（交易所/官方口径）与完整日线行情。想进入 `Confirmed`，2020 需补至少 1–2 条独立日线/交易所证据，2019 同理。

## 6. 是否继续 / 停止点

按既定停止条件，**此处暂停批量脚本**。下一步（需人工确认后）：
1. 批准字段调整（第 4 节）；
2. 补齐 2020 日线行情二次核验（确认窗口起点、Wave 精确日期）；
3. 再继续 2021–2025（另含 2015–2017 扩展样本评估）。

---
*本报告将字段调整项与年份结论并列，便于人工 Review。所有当前数据均可通过 `exports/cycle_verified_candidates.json` 复查。*