# Historical Data Production v1 — Batch Research Report

> 项目：Cycle-Research（`rule_auto_summer`，汽车，历史观察窗口 6–8 月）
> 日期：2026-09-13 · 契约：HDP v1（生产哲学：Raw → Multi-source → Cross-check → PROVISIONAL → Human Review → VERIFIED）
> 范围：2018–2025 一次性批量研究（不等待人工 Review）

---

## 0. 执行摘要

本轮完成 **2018–2025 八年度批量研究**：8 个正式 Campaign + 2018 反例年份全部保留；新增**批量研究层**（`research/batch/`）与 **Research → Cycle Timeline 导出契约 v1.0**（`exports/timeline_export_v1.json`）；补齐 2019/2020/2021/2025 缺失行情（`market_daily` 由 4,934 行增至 **16,266 行**，覆盖 2018–2025 全部年度）。全部校验 PASS。

**结论：READY FOR CYCLE TIMELINE MVP**（见 §17）。

---

## 1. Campaign 总数（2018–2025）

**8 个正式 Campaign**（2019–2025 每年 1–2 个；2018 无 Campaign，属反例年份，保留为年度级条目 `Y2018-NO-CLEAR`）。

## 2. PROVISIONAL 数量

**7**：Y2018-NO-CLEAR（年度反例结论）、C-2019-AD、C-2020-NEV、C-2021-NEV、C-2023-AD、C-2024-V2X、C-2025-ROBOTAXI。

## 3. CONFLICT 数量

**2**（3 条字段冲突）：C-2022-POLICY（start）、C-2024-ROBOTAXI（peak / end）。详见 §12 与 `research/batch/conflicts.json`。

## 4. INSUFFICIENT 数量

**0**。全部年度均有可识别主题、证据与来源（2018 反例结论亦有 3 条 contradicting + 1 条 context 证据支撑）。

## 5. 当前 VERIFIED 数量

**0**。本轮产出全部为 PROVISIONAL / CONFLICT（研究层）；VERIFIED 仅由人工最终 Review 产生，本轮未发生。**PROVISIONAL ≠ VERIFIED。**

## 6–8. 每年 Campaign / 主要 Theme / 数据缺口

| 年份 | Campaign | 状态 | 主要 Theme | 数据缺口 |
|---|---|---|---|---|
| 2018 | （无）`Y2018-NO-CLEAR` | PROVISIONAL | 反例年份（板块下行） | 无 Campaign 行情快照（如实 unavailable）；板块下行证据来自媒体/行业数据 S-2018-01/02 |
| 2019 | C-2019-AD | PROVISIONAL | 智能驾驶/无人驾驶 | 行业代理不可得（AUTO_SW 腾讯无数据、516110 未成立），用龙头万安科技作参考；事件驱动强度弱、日期置信度 low |
| 2020 | C-2020-NEV | PROVISIONAL | 新能源汽车/电池 + 特斯拉产业链 | 行业代理不可得（516110 未成立），用龙头比亚迪作参考；全年视角 4 月底提前启动为线索待核验 |
| 2021 | C-2021-NEV | PROVISIONAL | 新能源汽车/电池 | 行业代理不可得，用龙头比亚迪作参考；end 09-30 为暂定边界，主升 8/6 峰值后高位衰减 |
| 2022 | C-2022-POLICY | **CONFLICT** | 汽车消费/购置税刺激 | start 04-27 vs 05-23 冲突；end 08-31 为暂定边界（7 月后分化） |
| 2023 | C-2023-AD | PROVISIONAL | 智能驾驶/无人驾驶 | Huawei Auto 为研究候选未入正式库（RC-2023-HUAWEI）；08-29 Early Signal 存在 Beta contamination |
| 2024 | C-2024-V2X | PROVISIONAL | 车路云一体化/车路协同 | 快涨快退（约 2 周）；公司多公告"未参与"，题材属性；行情代理仅通用汽车ETF（非 V2X 专用） |
| 2024 | C-2024-ROBOTAXI | **CONFLICT** | Robotaxi/无人驾驶 | peak 07-29 vs 08-05、end 07-31 vs 08-23 冲突；09-05/06 Secondary 为弱候选 |
| 2025 | C-2025-ROBOTAXI | PROVISIONAL | Robotaxi/无人驾驶 | 大盘 β contamination（8 月沪指 +8%）；FSD 2025 未落地（2026-05-21 才宣布）；end 08-31 为暂定边界（9/12 月另有催化） |

## 9. Evidence 数量

**46 条**（`evidences`），全部通过 `campaign_evidences` 桥表显式绑定（39 条绑定，0 条跨 Campaign；无 orphan supporting 证据）。

## 10. Source 数量

**49 个**（`sources`），Tier 1–4，`source_type` 与 `tier` 一致性由 validate_db 强制（0 FAIL）。

## 11. Market Data 覆盖情况

`market_series` 32 条（新增 7：LUCHANG / NINGDE / GREATWALL / XIAOKANG / GUANGQI / XUSHENG / YATAI）；`market_daily` 16,266 行（raw + adjusted(qfq) 双口径）。

| 年份 | 基准/代理 | 龙头个股行情 | 快照 |
|---|---|---|---|
| 2018 | SH000300 全区间 ✅ | （无 Campaign） | 反例结论（无 Campaign 快照） |
| 2019 | SH000300 ✅ | 万安/路畅/亚太 ✅ | WANAN raw close + adjusted return ✅ |
| 2020 | SH000300 ✅ | 比亚迪/宁德/江淮/旭升 ✅ | BIDI 快照 ✅（start→peak +77.6%） |
| 2021 | SH000300 ✅ | 比亚迪/宁德/长安/长城/小康 ✅ | BIDI 快照 ✅ |
| 2022 | SH000300 + AUTO_ETF ✅ | 比亚迪/长安/长城/广汽/中通 ✅ | AUTO_ETF 快照 ✅ |
| 2023 | SH000300 + AUTO_ETF ✅ | 德赛/万安/浙江世宝/华为链 ✅ | AUTO_ETF 快照 ✅ |
| 2024 | SH000300 + AUTO_ETF ✅ | 大众交通/锦江/金龙/天迈/星网宇达 ✅ | AUTO_ETF 快照 ✅ |
| 2025 | SH000300 + AUTO_ETF ✅ | 德赛/浙江世宝 ✅ | AUTO_ETF 快照 ✅ |

- **AUTO_SW（申万汽车 801880）**：腾讯/公共免费源不可得，**如实 unavailable，未伪造**（符合 `market_data_validation.md`）。
- **516110（汽车ETF）**：成立于 2021-11 之后，**仅用于 2022 之后**，未回溯使用。
- 每个 Campaign 的 `market_data.raw_close`（Start/Peak/End + Phase 起止）与 `adjusted_returns`（start→peak / start→end / peak→end）已写入 manifest。
- 说明：2024 Robotaxi 行情代理为通用汽车 ETF（非 Robotaxi 专用指数），收益被稀释（start→peak +1.8%），不反映题材本身强度；2023-08-29 / 2025-08 需人工排除 β contamination。

## 12. 哪些日期冲突（不强行解决）

记录于 `research/batch/conflicts.json`，`decision = pending_human_review`（Blockers 类型 `RESEARCH_UNCERTAINTY`）：

| Campaign | 字段 | candidate_a（DB 冻结） | candidate_b（研究复核候选） |
|---|---|---|---|
| C-2022-POLICY | start | 2022-04-27（Setup 起点） | 2022-05-23（Theme Formation/政策催化日） |
| C-2024-ROBOTAXI | peak | 2024-07-29 | 2024-08-05（EW 等权指数 raw 峰值） |
| C-2024-ROBOTAXI | end | 2024-07-31 | 2024-08-23（Main Campaign End） |

## 13. 哪些年份仍然不足

- **2019**：唯一 `weak` 年份，事件驱动、强度不足、日期置信度 low → 需人工 Review 决定是否保留为 Campaign。
- **2024-V2X**：题材属性强（多公司澄清未参与），Campaign 语义偏题材脉冲。
- **2025**：end（08-31）为暂定边界，8 月受大盘 β 强干扰；9/12 月另有催化波次待日线切分。
- **2018**：无 Campaign，反例结论依赖媒体/行业数据，无行情快照（设计如此，非缺口）。

## 14. timeline_export_v1 是否生成成功

✅ **生成成功**：`exports/timeline_export_v1.json`（`timeline_export_version = "1.0"`），8 个 Campaign、5 组研究信号、全部 events/securities 可导出；`validate_timeline_export.py` **PASS（0 FAIL）**（机器可解析、字段白名单校验、2019–2025 全覆盖）。

## 15. Research → Cycle 接口是否稳定

✅ **稳定**：
- 导出契约 v1.0 明确 `rules / signals / campaigns / events / securities`，`status`（Cycle 侧 promotion 状态）与 `research_status`（PROVISIONAL/CONFLICT/INSUFFICIENT）**严格分离**，research-only 字段不伪装成正式字段。
- 与 `promotion_gate_v1.md` / `cycle_mapping_v1.md`（v1.1）映射一致；Phase 为 research-only，不进入 Cycle。
- 契约版本化（`timeline_export_version`），未来修改走 1.1 / 2.0，保持向后兼容。
- 校验器 `validate_timeline_export.py` 作为接口守门人。

## 16. 是否偏离项目初心

✅ **未偏离**。经 `research/methodology/product_purpose_checkpoint.md` 四问检查：
1. 帮助构建时间轴？→ 是（8 年 Campaign/日期/事件/证据/行情全部可被时间轴消费）
2. 提高历史可比性？→ 是（统一状态、证据独立组、行情双口径）
3. 有助于识别提前信号？→ 是（Research Signal 保留在 manifest/signals）
4. 只是工程复杂化？→ 否（未新增正式 Schema，模型 v1.0 冻结，未计算任何统计指标）

本轮**禁止清单**全部遵守：无 AI 预测、无实时行情、无资金流、无胜率/seasonality、无新库/新 Schema、无自动交易、无微信推送。

---

## 17. 验证结果

```
validate_db.py                → PASS（0 FAIL, 0 WARNING）
check_doc_schema_consistency  → PASS（0 FAIL）
test_doc_schema_checker       → PASS（0 FAIL, 0 WARNING）
validate_batch_research.py    → PASS（0 FAIL）
validate_timeline_export.py   → PASS（0 FAIL）
```

验证目标（HDP v1 §26）：唯一 ID ✅ ｜ Evidence 不跨 Campaign ✅ ｜ Source 可追溯 ✅ ｜ Market data 无重复 ✅ ｜ Candidate/Verified 不混淆 ✅ ｜ PROVISIONAL 不进 verified ✅ ｜ CONFLICT 不伪装确定日期 ✅ ｜ timeline JSON 可机器解析 ✅ ｜ 不生成不存在的 Cycle 字段 ✅ ｜ 2018–2025 全部可导出 ✅

---

# READY FOR CYCLE TIMELINE MVP

**状态汇总**：Campaign 8（PROVISIONAL 6 / CONFLICT 2）＋ 2018 年度反例条目 1（PROVISIONAL）＝ 9 条目；Evidence 46；Source 49；Market daily 16,266 行（2018–2025 全覆盖）；timeline_export_v1 校验通过；Research → Cycle 接口契约 v1.0 稳定。

主 Cycle Timeline MVP 可直接消费 `exports/timeline_export_v1.json`；VERIFIED 层（0 条）等待人工最终 Review（与 PROMOTION GATE 对齐，不阻塞时间轴开发预览）。

> 备注：`source_commit` 指向本批次数据状态对应的提交（67b5adc），本轮交付文件提交后将在 Git 历史中可见。
