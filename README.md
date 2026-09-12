# Cycle-Research

**A股历史题材 / 行业季节性研究数据库（先行版）**

> ⚠️ 本项目（`Cycle-Research`）与生产项目 `yangfanbit/Cycle` 完全独立。禁止直接修改 `Cycle` 及直接写入其 `data/verified/`。本项目的结论为研究候选，必须经人工 Review 后才转入 `Cycle`。

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
│   └── schema.sql               # SQLite 建库脚本
├── database/
│   └── cycle_research.db        # 研究数据库
├── scripts/
│   ├── db.py                    # 连接/建库/插入工具
│   ├── seed.py                  # 录入 2018–2020 种子数据
│   ├── export.py                # 导出 CSV + verified_candidates.json
│   └── gen_annual.py            # 生成年度研究报告
├── research/
│   ├── templates/annual_template.md
│   ├── annual/{2018..2025}.md   # 年度研究报告
│   └── summary/auto_2018_2025.csv
├── exports/
│   └── cycle_verified_candidates.json  # 待人工确认的候选（非 Cycle 正式 verified）
├── data/                        # 原始抓取源（预留）
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
```

## 7. 当前状态（试点：2018–2020）

已完成 2018、2019、2020 三年试运行并生成：
`research/annual/2018.md`、`2019.md`、`2020.md`、`research/summary/auto_2018_2025.csv`、`exports/cycle_verified_candidates.json`。

**试点结论（含歧义与调整项）见 `research/pilot_report.md`。** 在人工 Review 前，继续批量研究被暂停（停止条件）。