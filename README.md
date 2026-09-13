# Cycle-Research

**A股历史题材 / 行业季节性研究数据库（先行版）**

> ⚠️ 本项目（`Cycle-Research`）与生产项目 `yangfanbit/Cycle` 完全独立。禁止直接修改 `Cycle` 及直接写入其 `data/verified/`。

## 定位（HDP v1 更新）

**Cycle-Research 是"持续生产历史研究数据的研究层"**，最终服务于 **A股机会时间轴**（主 Cycle Timeline MVP）：

1. 看某个时间点历史上发生过什么
2. 看某类主题通常如何形成
3. 看提前多久出现信号
4. 看 Campaign 如何发展
5. 看什么时候进入退潮
6. 为主 Cycle 的时间轴提供可靠历史数据

> **产品价值 > 研究工程复杂度**。研究严谨性必须保留，但不能成为数据生产瓶颈。

### 生产哲学（正式改变）

过去：`Research → Human Review → Verified`

现在：

```
Raw → Multi-source Collection → Cross-check → PROVISIONAL
    ├── 无冲突 → PROVISIONAL
    ├── 有冲突 → CONFLICT
    └── 来源不足 → INSUFFICIENT
→ Human Review → VERIFIED
```

**PROVISIONAL ≠ VERIFIED**，但 **PROVISIONAL 可以用于研究预览和主 Cycle 开发预览**。
**人工 Review 不再是批量生产的前置条件**（不再"等人工 Review 后再继续下一个年份"）。

研究级状态（`RAW / PROVISIONAL / CONFLICT / INSUFFICIENT / VERIFIED`）表达在 `research/batch/` 与 export manifest 层，**不改 SQLite 正式 schema**。

```
Cycle-Research → Raw Evidence → Research Fact → Campaign Draft
    → 人工 Review → Confirmed Historical Fact → Cycle / data/verified/
```

---

## 1. 定位（第一/当前阶段）

第一阶段只研究一条规则：

- **Rule**: `rule_auto_summer`
- **Base Pattern**: 汽车
- **观察窗口**: 6—8 月

核心不是证明"6—8 月汽车一定上涨"，而是回答：

1. 该窗口历史上是否更容易出现汽车相关机会？
2. 每一年发生了什么？
3. 行业趋势还是题材炒作？
4. 当年的 Annual Theme 是什么？
5. 何时启动、何时结束、是否有多个 Campaign / Wave / 二次启动？
6. 什么事件催化？龙头是谁？
7. 有没有失败 / 无明显行情年份（反例）？
8. 原始"6—8 月汽车"经验到底有多强？

## 2. 严格区分概念

| 概念 | 说明 |
|---|---|
| Source | 来源（Tier 1–4） |
| Evidence | 证据（supporting / contradicting / context；high / medium / low） |
| Historical Fact | 被多来源核对后的事实 |
| Campaign | 一轮可识别的行情（须满足：主题可识别 + 持续性 + 市场关注 + 可解释启动/结束 + 有证据） |
| Rule | Base Pattern（如"汽车"） |
| Statistics | 跨年统计（不预设正确） |

> 媒体描述 ≠ 市场事实；单日板块上涨 ≠ Campaign。

## 3. 目录结构

```
Cycle-research/
├── schema/
│   └── schema.sql               # SQLite 建库脚本（模型 v1.0 冻结，不新增实体）
├── database/
│   └── cycle_research.db        # 研究数据库
├── scripts/
│   ├── db.py                    # 连接/建库/迁移/插入工具
│   ├── seed.py                  # 录入 2018–2025 种子数据
│   ├── seed_market_series.py    # 注册行情序列(Market Series)
│   ├── seed_campaign_dates.py   # 快照候选日期(Date Observation)
│   ├── market_metrics.py        # 基础行情指标函数库
│   ├── fetch_market_tx.py       # 腾讯行情拉取（Pilot 1-C1 校准）
│   ├── fetch_market_batch.py    # 批量补齐 2018–2025 行情（幂等）
│   ├── batch_auto_research.py   # 批量研究：生成 manifest/conflicts/timeline_export
│   ├── validate_batch_research.py    # 批量研究输出校验
│   ├── validate_timeline_export.py   # 时间轴导出契约校验
│   ├── export.py                # 导出 CSV + verified_candidates.json
│   ├── gen_annual.py            # 生成年度研究报告
│   ├── gen_summary.py           # 生成年度汇总
│   └── validate_db.py           # 一致性检查（含行情基建 11 项）
├── research/
│   ├── templates/annual_template.md
│   ├── annual/{2018..2025}.md   # 年度研究报告
│   ├── batch/                   # 批量研究层（HDP v1）
│   │   ├── README.md
│   │   ├── auto_2018_2025_batch_manifest.json  # 研究状态/日期候选/证据/行情快照
│   │   └── conflicts.json       # 日期口径冲突（candidate_a vs candidate_b）
│   ├── summary/auto_2018_2025.csv / .md
│   └── methodology/market_data_validation.md  # 行情核验方法学(Pilot 1-C1)
├── exports/
│   ├── cycle_verified_candidates.json  # 待人工确认的候选（非 Cycle 正式 verified）
│   └── timeline_export_v1.json         # Research → Cycle Timeline MVP 导出契约 v1.0
├── data/
│   └── market/
│       ├── raw/                 # 原始下载行情（未统一字段，可追溯）
│       └── normalized/          # 统一字段后的行情（对应 market_daily）
└── README.md
```

## 4. 数据库核心表

`research_rules` → `annual_reviews`（每年一条母记录）→ `campaigns` → `campaign_themes` / `campaign_events` / `campaign_evidences` / `campaign_securities` / `campaign_phases`；以及 `sources` / `evidences` / `themes` / `events` / `securities`。

**Campaign ↔ Evidence 显式关联（v1.5）**：

```
Campaign  ↕  CampaignEvidence  ↕  Evidence  ↕  Source
```

- `campaign_evidences(campaign_id, evidence_id, role)` 桥表显式绑定每个 Campaign 与其真实证据。
- **一个 Campaign 只能引用它自己的证据；export.py 只经桥表取证据，不会混入全库。**
- **“媒体数量” ≠ “独立证据数量”。** `evidences.independence_group` 标记同源转引（`same_origin_xxx`）与真正独立来源（不同 group）。同一事实被多个媒体转载，不得自动算作多条独立证据。
- Confirmed Campaign 门槛：**≥2 条 Evidence 且 ≥2 个 independence_group**，否则不得标 `confirmed`（由 `scripts/validate_db.py` 程序化检查）。

关键判定枚举：
- `annual_reviews.status`: `strong / medium / weak / no_clear_campaign / unknown`（`no_clear_campaign` 是合法结果）
- `campaigns.classification`: `theme_campaign / industry_trend / event_driven / mixed / unclear`
- `campaigns.result`: `positive / neutral / weak / failed / unknown`
- `evidences.evidence_role`: `supporting / contradicting / context`

Campaign 判定**至少**需：主题可识别、持续性、市场关注、可解释的启动与结束、有 Evidence。若能只证明"行业上涨"，`classification=industry_trend`。

**日期 basis（v1.5 兼容设计，未强制迁移）**：未来推荐将 `start_date_basis` / `end_date_basis` 拆分为 `start_date_basis_code` / `start_date_basis_note` 与 `end_date_basis_code` / `end_date_basis_note`；`code ∈ {observed, inferred, official_event, unknown}`。当前旧长文本字段保留，不破坏试点。

### 行情核验基础设施（Pilot 1-C1）

数据流：`Market Series → Daily Market Data → Date Verification → Historical Campaign`

新增四表（详见 `research/methodology/market_data_validation.md`）：

- **`market_series`**：行情序列定义（series_id/name/series_type/provider/symbol/frequency/price_type/adjustment_method）。只填真实可确认的 `symbol`，不确定留空、不编造。
- **`market_daily`**：日线（open/high/low/close/adj_close/volume/amount），**每行必须明确 `price_type`（raw/adjusted）**；`(series_id, trade_date, price_type)` 唯一，禁止自动覆盖已有数据。
- **`trading_calendar`**：交易日历。只填交易日（`is_trading_day=1`）；无独立源时允许由 benchmark series 的 `distinct trade_date` 推导。
- **`campaign_date_observations`**：Campaign 日期核验观测。`candidate_date`（原始研究日期，保留不改）与 `verified_date`（核验后，可空）分列；`date_role ∈ {start,end,peak}`，不覆盖 `campaigns.*_date`。

**基础指标**：`scripts/market_metrics.py` 提供 `daily_return / cumulative_return / rolling_return / relative_return_vs_benchmark / drawdown / volume_change`；Breadth 仅预留接口（`ThemeBreadthSnapshot`），因缺可靠历史成分数据不生成结果。

## 4.1 Price Policy

- **raw close**：用于日期判断（启动/峰值/终点，在原始交易日序列上识别）与真实成交价叙述。
- **adjusted close**：用于收益率计算（避免股本/送转/分红干扰）。
- 日期判断优先使用**交易日原始价格序列**；收益计算必须明确价格口径。
- **不允许在同一指标中混合不同调整口径**。
- `market_daily` 每一行都带 `price_type` 字段显式声明口径，禁止同源混用。

## 4.2 Trading Day vs Calendar Day

- **Calendar Day（自然日）** = 含周末与节假日的日历日。
- **Trading Day（交易日）** = 该市场实际开市日（跳过周末与法定休市）。
- `market_daily.trade_date` 与 `trading_calendar.trade_date` **均只取交易日**；窗口漂移/启动天数等应基于交易日而非自然日口径。
- 无独立日历源时，可用 benchmark series 的交易日集合推导日平衡。

## 5. 来源优先级

- **Tier 1**：交易所 / 政府监管 / 公司公告 / 权威行业协会
- **Tier 2**：中证报、证券时报、第一财经、财联社、界面、经济观察报等主流财经媒体
- **Tier 3**：券商研报、专业财经网站
- **Tier 4**：论坛 / 博客 / 自媒体（只能做线索，不能单独作为最终事实依据）

## 6. 运行脚本

Python 需含 sqlite3（标准库即可）。示例：

```powershell
python scripts/seed.py          # 初始化并录入当前年份
python scripts/validate_db.py   # 一致性检查（PASS/FAIL，含 confirmed 门槛、source-tier、引用完整性）
python scripts/export.py        # 生成 CSV 与 verified_candidates.json
python scripts/gen_annual.py    # 生成 research/annual/*.md
# HDP v1 批量研究流水线：
python scripts/fetch_market_batch.py       # 补齐缺失行情（幂等，腾讯免费接口）
python scripts/batch_auto_research.py      # 生成 batch manifest / conflicts / timeline_export_v1
python scripts/validate_batch_research.py  # 校验批量研究输出
python scripts/validate_timeline_export.py # 校验时间轴导出契约
```

## 7. 当前状态（HDP v1：2018–2025 批量研究）

已完成 2018–2025 八年度研究（8 个正式 Campaign + 2018 反例年份保留）：
- `research/annual/{2018..2025}.md`、`research/summary/campaign_2018_2025.csv`、`exports/cycle_verified_candidates.json`
- `research/batch/auto_2018_2025_batch_manifest.json`（PROVISIONAL / CONFLICT 研究状态）
- `research/batch/conflicts.json`（C-2022-POLICY start、C-2024-ROBOTAXI peak/end 口径冲突）
- `exports/timeline_export_v1.json`（Research → Cycle Timeline MVP 契约 v1.0）

**最终 Rule 结论**："6–8 月汽车" = **历史观察窗口**（Historical Observation Window），**Partially Supported**，非固定买入窗口。详见 `research/summary/auto_2018_2025_final_review.md`。

> 停止条件已解除：人工 Review 不再是批量生产的前置条件；PROVISIONAL 可用于研究预览与主 Cycle 开发预览。