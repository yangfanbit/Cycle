# C-2024-ROBOTAXI — Human Review Decision Proposal

> **性质**：本文件为 **Human Decision Proposal（人工审核建议记录）**。
> **不是** Verified Fact；**不产生** Verified Date；**不修改** campaigns / annual_reviews / schema.sql / database / Cycle / data/verified。
> 依据仅限现有材料：Historical Leader Equal-Weight Index（EW，5 只历史核心等权，base 2024-07-08=100，raw close）、已有 Evidence、Point-in-Time Review、Continuity Review。**未新增研究。**

---

## 1. 最终建议（Proposed）

| 日期层级 | 日期 | 语义 |
|---|---|---|
| **Campaign Start（建议）** | **2024-07-08** | Early Start / 起势（EW 基准日；大众交通放量 +6.12% 启动） |
| Broad Confirmation | **2024-07-10** | 主题广泛确认（PIT 可辩护）：天迈获当日证券时报点名（E-2024-05）、板块 +4%、萝卜快跑媒体全面发酵 |
| **Peak（建议）** | **2024-08-05** | Market Data Peak：EW raw 峰值 **234.8**（大众 08-05 见顶 11.22） |
| First Decline | **2024-08-06** | 首个显著回撤：EW 234.8→214.1（-8.8%）；**独立概念，不是 End** |
| **Main Campaign End（建议）** | **2024-08-23** | Major Breakpoint：08-21/22 重新活跃（EW 207.6/207.3）被 08-23 单日 -4.6%（197.8）打断，其后持续走弱、无新高、个股不再同步 |
| Secondary Campaign Candidate | **2024-09-05 ~ 2024-09-06** | Weak Secondary（same theme cycle）：FSD 入华预期 + Robotaxi 10 月 + 萝卜扩容；3/5 核心同步、2 日即回吐；**不并入 Main Campaign** |
| classification | theme_campaign | Robotaxi 题材行情（EW +122.4% vs AutoETF +3.6% vs HS300 +1.2%，07-08→07-31） |
| strength | strong | — |
| result | positive | — |

## 2. 明确排除的日期

| 日期 | 排除理由 |
|---|---|
| **2024-07-29** | 叙事/媒体高点候选（E-2024-06 焦点复盘报道日，EW 当日 210.8）；**不是最终 HistoricalCampaign peak**（价格峰值在 08-05） |
| **2024-07-31** | 中途回撤（EW 230.3→218.2，被 08-05 新高覆盖）；**不是最终 End** |
| **2024-08-06** | **First Decline，不是 End**（此后 08-15、08-21/22 仍有部分个股二次活跃） |
| **2024-09-05/06** | Weak Secondary Campaign Candidate（RC-2024-SECONDARY）；**不并入 Main Campaign** |

## 3. 证据依据（仅引用已有材料）

- **Historical Leader Equal-Weight Index**：07-08=100 → 07-09 110.1 → 07-30 230.3（中途高）→ 07-31 218.2（中途回撤）→ **08-05 234.8（峰值）** → 08-06 214.1（First Decline）→ 08-21/22 207.6/207.3 → **08-23 197.8（跳水 -4.6%）** → 08-30 188.6（持续走弱）。
- **Evidence**：E-2024-05（07-10，orig_robotaxi_momentum，contemporaneous，high）；E-2024-06（07-29，orig_robotaxi_leader，叙事高点）；E-2024-07（07-31，orig_robotaxi_retreat，contradicting）；E-2024-08（10-11，context，subsequent）。
- **Point-in-Time Review**：07-08 basket=unavailable；07-10 basket={大众/锦江/星网/天迈}；07-15 basket=5 只。07-09 "广泛"为 retrospective 增强，07-10 为 PIT 可辩护的 Broad Confirmation。
- **Continuity Review**：08-23 后约 2 周冷却 → 09-05/06 同主题次级再启动（weak），09-09/10 完全回吐；08-23 = Main Campaign End，**非 Final Theme Cycle End**。

## 4. 最终 Review Decision 表

| Field | DB Candidate | Human Review Proposal | Decision Status |
|---|---|---|---|
| Start | 2024-07-08 | 2024-07-08 | proposed |
| Peak | 2024-07-29 | 2024-08-05 | proposed |
| First Decline | null | 2024-08-06 | research phase |
| End | 2024-07-31 | 2024-08-23 | proposed |

> **Human Review Proposal 不是 Verified Date。** Decision Status = proposed，尚待人工 reviewer 正式确认并填写 reviewer / reviewed_at 后，方可转为 Verified Date。

## 5. Promotion 状态

- `promotion_manifest.json` **不修改**：C-2024-ROBOTAXI 保持 **READY_FOR_HUMAN_REVIEW**。
- **不升级为 READY_FOR_PROMOTION**：reviewer / reviewed_at 尚未正式填写，Verified Date 尚未产生。

## 6. 最终说明

**本轮完成研究判断，但尚未产生 Verified Date，也未完成数据库晋级。**

---

*未修改 schema.sql / database/cycle_research.db / campaigns / annual_reviews / Research Model v1.0；未写入 data/verified；未填写 reviewer / reviewed_at；未触碰 2022 / 2023。*
