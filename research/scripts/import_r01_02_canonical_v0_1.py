#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_02_canonical_v0_1.py —— R01-02（半导体 / 电子）Canonical Import。

依据：`docs/R01_02_INTAKE_REVIEW_v0_1.md` + 本轮 Canonical Decision（Independence Gate Q1–Q5）。

结果（8 PROMOTE + 4 RESEARCH_ONLY）：
  PROMOTE → campaigns 表
    001 半导体自主可控（实体清单）      → C-2019-SEMI-LOCALIZATION
    002 设备材料国产替代（扩产周期）    → C-2020-SEMI-EQUIPMENT
    003 面板 LCD 价格上行（2020–22）    → C-2020-PANEL-CYCLE
    005 TWS / 可穿戴消费电子            → C-2019-CONSUMER-TWS
    006 AI 算力半导体                   → C-2023-AI-COMPUTE-SEMI
    007 存储超级周期                    → C-2024-SEMI-MEMORY（附 CF006 Beta 限定）
    009 半导体下行 / 去库存             → C-2022-SEMI-DOWNTURN
    011 面板价格上行（2016–17）         → C-2016-PANEL-CYCLE
  RESEARCH_ONLY → **不入 campaigns 表**（导出层 research_candidates）
    004 缺芯（start 为 PHASE_WINDOW 无日期 + 与 002 时间高度重叠；包内自述「难以独立切分」）→ RC-2022-SEMI-CHIPSHORTAGE
    008 大基金三期（confidence low + 与 007 区间高度重叠 + 无独立结束点）→ RC-2024-SEMI-FUND3
    010 2015 杠杆牛（INSUFFICIENT，0 securities）→ RC-2015-SEMI-LEVERAGE
    012 2017 显卡矿机（INSUFFICIENT，0 securities + CF008 归属争议）→ RC-2017-GPU-MINING

边界：不改 schema · 不改 Research Model v1.0 · 不改 Export Contract · 不改 CMTR v1 · 不改 taxonomy。
幂等：已存在则跳过。
用法：
  python research/scripts/import_r01_02_canonical_v0_1.py --dry-run |  (apply)  --verify
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-02")

RULE_ID = "rule_semiconductor"
PROV = "R01-02 Intake Package（source_commit 2153f6d）｜Canonical Decision docs/R01_02_INTAKE_REVIEW_v0_1.md"

# ---------------------------------------------------------------- Campaign 决策表
# intake 后缀 → (canonical_id, year, start, peak, end, classification, strength,
#                 result, date_confidence, season_id, theme_cycle_id, themes, notes)
CAMPAIGNS = [
    dict(
        k="001", cid="C-2019-SEMI-LOCALIZATION", year=2019,
        start="2019-05-16", peak="2020-07-14", end="2020-09-30",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        season="semi_localization_2019_2021",
        cycle="semi_localization_2019_2021",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "★ CF001/CF010 裁决：**判为一个长周期内的第一个独立 Campaign**（非整个 2019–2021 周期）。"
            "依据：Q1 注意力中心为「华为实体清单 → 国产替代认知建立（设计/制造/封测全线）」，"
            "与 002 的「中芯国际回A + 晶圆厂扩产 → 设备材料」不同；Q2 代表标的不同（本 Campaign 覆盖设计与封测，"
            "002 集中于设备材料）；Q4 生命周期独立（主升 2019-05→2020-07，回撤 2020-07→2020-09）。"
            "★ peak = 2020-07-14（申万半导体 5869.83，E011 同期行情数据）。"
            "**不采用** 2020-02 底（研报口径）与 2021-07-30（7642.58，属 002）——两者已作为 "
            "alternative_dates 保留，不得预设其中任何一个为本 Campaign 的 canonical peak。"
            "★ 与 002 允许时间重叠（theme_campaign_separation 规则 5）。"
        ),
    ),
    dict(
        k="002", cid="C-2020-SEMI-EQUIPMENT", year=2020,
        start="2020-07-16", peak="2021-07-30", end="2021-09-30",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        season="semi_localization_2019_2021",
        cycle="semi_localization_2019_2021",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "secondary"), ("TH-ELEC-SEMI-EQUIP", "main")],
        notes=(
            "★ CF001/CF010 裁决：**与 001 为同一 Theme Cycle 下的 Sequential Campaign**（非 Sub-theme）。"
            "依据：Q1 注意力中心为「中芯国际回A + 晶圆厂扩产 → 设备材料『卡脖子』上游」；"
            "Q2 代表标的集中于中微 / 拓荆 / 沪硅（与 001 的设计封测群不同）；Q4 生命周期独立"
            "（主升 2021-04→2021-07-30 = 7642.58，随后 2021-08 起下行至 2022-10 = 3605.80）；"
            "Q5 Residual Test：剔除设备材料后 001 仍自洽，剔除 001 后本 Campaign 亦自洽。"
            "★ 包内 Q5 存疑点已记录：两者资金池与叙事高度重叠，亦支持 Sub-theme 读法 —— 本轮按 Gate 多数成立判为独立 Campaign，"
            "若后续轮次推翻需另起决策，不得静默改动。"
            "★ 证据 E056（2024-05-24 大基金三期）由本包绑定至本 Campaign，日期与本 Campaign 区间不符 —— "
            "按「不改研究内容」原则原样导入并在此标注，供后续轮次复核。"
        ),
    ),
    dict(
        k="003", cid="C-2020-PANEL-CYCLE", year=2020,
        start="2020-06-01", peak="2021-07-31", end="2021-08-31",
        cls="industry_trend", strength="strong", result="positive", dc="medium",
        season="panel_price_cycle_2016_2022",
        cycle="panel_price_cycle_2016_2022",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-PANEL", "main")],
        notes=(
            "★ CF004/CF007：面板按**独立机制族**处理（产能周期 + 库存周期驱动的价格周期），"
            "与半导体设计/设备机制不同步（65 吋面板 2021-07 = 294 美元峰值，而京东方股价峰值 2021-04；"
            "面板 2021-08 起跌至 2022-09 = 106 美元。"
            "★ CF007 裁决：与 011（2016–2017）为**同一机制族的两个独立 Campaign**（同一 Theme Cycle 的两轮实例）。"
            "依据：驱动结构不同（本轮 = 疫情宅经济 + 上游材料短缺 + 韩厂彻底关停）"
            "★ CF005 裁决：与 004（缺芯）为**两个独立结构**——供给曲线不同（面板产能 vs 晶圆代工产能）；"
            "代表标的（京东方/TCL vs 卓胜微/长电/通富微电）不重叠；Q5 Residual Test 成立。"
            "（004 因 start 为 PHASE_WINDOW 且包内自述难以独立切分 → 本轮 RESEARCH_ONLY。）"
        ),
    ),
    dict(
        k="005", cid="C-2019-CONSUMER-TWS", year=2019,
        start="2019-01-04", peak="2020-10-13", end="2021-03-31",
        cls="theme_campaign", strength="strong", result="positive", dc="medium",
        season="electronics_tws_2019_2020",
        cycle="electronics_tws_2019_2020",
        themes=[("TH-ELEC", "main")],
        notes=(
            "机制 = 终端产品创新 + 单一大客户订单 → **纯需求端驱动**（当前 4 个 Macro Theme 完全缺失的机制轴之一。"
            "★ CT005：与 R01-04（消费）边界 —— 本 Campaign 只取零部件与上游芯片环节，明确排除品牌整机。"
            "★ peak 采用 2020-10-13（龙头月内高点；与 2020-11-09 构成 peak cluster）。"
        ),
    ),
    dict(
        k="006", cid="C-2023-AI-COMPUTE-SEMI", year=2023,
        start="2023-01-30", peak="2023-04-10", end="2023-08-25",
        cls="theme_campaign", strength="medium", result="positive", dc="medium",
        season="ai_compute_semi_2023",
        cycle="ai_compute_semi_2023",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "★ CT003（跨任务边界）：2023 AI 行情中光模块与半导体由同一事件驱动、共享资金池、同期见顶。"
            "本 Campaign **只取半导体侧**；光模块已有 canonical `C-2023-COMM-OPTICAL`（Macro Theme = 信息通信）。"
            "两者分属不同 Macro Theme，本轮**不合并**；若后续认为应合并，需另起 cross-family 决策。"
            "★ peak = 2023-04-10（申万半导体 5154.69，E032 同期行情数据）。"
        ),
    ),
    dict(
        k="007", cid="C-2024-SEMI-MEMORY", year=2024,
        start="2024-09-24", peak="2025-10-31", end=None,
        cls="theme_campaign", strength="medium", result="positive", dc="medium",
        season="memory_supercycle_2024_2025",
        cycle="memory_supercycle_2024_2025",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "★ CF006 **保留 UNRESOLVED**（本轮不消解）。"
            "两侧证据：P1 独立基本面 —— 2025-10 申万半导体 7964.33，**超过 2021-07 的 7642.58 创指数新高（E037）**，"
            "叠加存储价格与江波龙业绩（E038/E040）；P2 Beta 无法排除 —— 2024-09-24 至 2025-09-23 期间北证50、"
            "科创50、创业板指涨幅均超 100%，申万 31 个一级行业**全线上涨**（E036，subsequent）。"
            "按 historical_campaign_validation_v1.md §4.3「无法排除时保持限定」，本 Campaign **以 medium 置信度进入"
            "canonical 并保留该限定**；**不得**据此宣称已与市场 Beta 分离。"
            "★ end 未确认：2025-12-31 收 6950.35（指数回落约 12.7%），未确认结束 → end_date = NULL。"
        ),
    ),
    dict(
        k="009", cid="C-2022-SEMI-DOWNTURN", year=2022,
        start="2022-01-04", peak="2022-08-31", end="2022-10-12",
        cls="industry_trend", strength="medium", result="weak", dc="medium",
        season="semi_inventory_downturn_2022",
        cycle="semi_inventory_downturn_2022",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "★ CF009 裁决：**进入 canonical campaigns 表**，与 R01-01 的 `C-2018-HIEQ-ROBOT-DOWN` 同一处理口径。"
            "理由：2022 下行具明确起止（2022-01-04 高点 6511.51 → 2022-10-12 低点 3605.80，全年 -37.11%）与"
            "可解释机制（库存 + 需求收缩），且「库存周期 / 需求收缩型下行」是当前 Historical Universe 缺失的机制轴。"
            "★ 这是**下行结构而非机会型结构** —— `result = weak`（与 R01-01 口径一致），不得解读为正向机会。"
        ),
    ),
    dict(
        k="011", cid="C-2016-PANEL-CYCLE", year=2016,
        start="2016-02-01", peak="2017-06-30", end="2017-06-30",
        cls="industry_trend", strength="medium", result="positive", dc="low",
        season="panel_price_cycle_2016_2022",
        cycle="panel_price_cycle_2016_2022",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-PANEL", "main")],
        notes=(
            "★ CF007 裁决：与 003 为**同一机制族（面板价格周期）的两个独立 Campaign**（同一 Theme Cycle 的两轮实例）。"
            "依据：驱动结构不同（本轮 = 韩厂转产 OLED + 电视大尺寸化）；中间 2017H2—2019H2 存在长达两年的独立下行期；"
            "Q3 Independent Persistence 成立。"
            "★ Priority B：证据偏薄（3 evidence / 2 independence_group，恰达门槛），peak 只能定位到半年窗口（2017H1）"
            "→ `date_confidence = low`，后续轮次应优先补齐面板价格月度序列。"
        ),
    ),
]

# RESEARCH_ONLY：**不进 campaigns 表**；仅在导出层 research_candidates（与既有 4 个 RC-* 同一设计）
RESEARCH_CANDIDATES = [
    dict(
        k="004", cid="RC-2022-SEMI-CHIPSHORTAGE", year=2022,
        start=None, peak=None, end="2022-12-31",
        cls="industry_trend", status="INSUFFICIENT",
        cycle="supply_constraint_2020_2022",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由（包内自述 + 本轮复核）：① start 为 PHASE_WINDOW（无日期锚点），"
            "peak 亦为 PHASE_WINDOW；② 包内 why_not 明确「A 股侧市场映射与 001/002 行情高度重合，**难以独立切分出**"
            "属于缺芯本身的行情区间；③ CF005 虽判其与 003 为不同供给曲线，但独立时间边界不成立 → Q4 不成立。"
            "「供给约束」机制由 003（面板）与 007（存储）承载。"
        ),
    ),
    dict(
        k="008", cid="RC-2024-SEMI-FUND3", year=2024,
        start="2024-05-24", peak="2024-12-31", end=None,
        cls="mixed", status="INSUFFICIENT",
        cycle="semi_localization_2019_2021",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "secondary"), ("TH-ELEC-SEMI-EQUIP", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① 包内 confidence = **low**；② 与 007 市场区间**高度重叠**"
            "（本候选 MAIN_RISE 2024-09-24→2024-11-29，落在 007 的 2024-09-24→2025-12 区间内）；③ 无独立结束点"
            "（包内 end = PHASE「叙事并入存储与 AI 主线」。"
            "★ CF002 附带结论：2019–20「首次被封锁」与 2024–25「大基金三期 + 出口管制升级」按 Gate **倾向为两个不同结构**"
            "（中间 2022-01—2024-01 近两年独立下行，驱动性质与目标环节迁移）；但 008 因上述 Beta 与重叠问题本轮不 Promotion。"

        ),
    ),
    dict(
        k="010", cid="RC-2015-SEMI-LEVERAGE", year=2015,
        start="2015-01-05", peak="2015-06-03", end="2015-12-31",
        cls="unclear", status="INSUFFICIENT",
        cycle="liquidity_cycle_2015",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① **0 个 securities**；② evidence 2 / IG 2 恰在门槛；"
            "③ 无法排除 Beta Contamination —— 2015 为全面杠杆牛市，缺半导体自身基本面证据（产能/出货/价格）；"
            "④ Priority B 资料不足。不得为增加 Campaign 数量强行提升。"
        ),
    ),
    dict(
        k="012", cid="RC-2017-GPU-MINING", year=2017,
        start="2017-06-01", peak="2017-11-14", end="2018-06-30",
        cls="unclear", status="INSUFFICIENT",
        cycle="crypto_spillover_2017",
        themes=[("TH-ELEC", "related"), ("TH-ELEC-SEMI", "main")],
        notes=(
            "RESEARCH_ONLY（不进 campaigns 表）。理由：① **0 个 securities**；② 2017 年 A 股主要映射为「区块链/数字货币」概念，"
            "区块链不属本任务 scope；CF008 归属争议**保留未裁决**；③ 缺乏半导体行业数据支撑，包内自述证据不足。"
        ),
    ),
]

# annual_reviews（按 campaign 年份聚合）
ANNUAL = {
    2016: ("medium", "面板价格上行周期启幕（韩厂转产 OLED + 大尺寸化）；Priority B，证据偏薄。"),
    2019: ("strong", "半导体自主可控（实体清单）与 TWS/可穿戴消费电子两条独立结构并起；国产替代认知建立年。"),
    2020: ("strong", "设备材料国产替代（晶圆厂扩产）与面板 LCD 价格上行周期并行。"),
    2022: ("weak", "半导体下行 / 主动去库存；同时为面板周期下行段。"),
    2023: ("medium", "AI 算力驱动的半导体行情（ChatGPT → GTC）。"),
    2024: ("medium", "存储超级周期启幕（2024-09-24 起）；**CF006 市场 Beta 未排除，置信度受限。**"),
}

# 证券助记符（沿用既有大写助记符惯例）
SEC_CANON = {
    "R01-SEMICONDUCTOR-SEC001": ("SMIC", "688981", "中芯国际", "SH"),
    "R01-SEMICONDUCTOR-SEC002": ("WILLSEMI", "603501", "韦尔股份", "SH"),
    "R01-SEMICONDUCTOR-SEC003": ("SGMC", "300661", "圣邦股份", "SZ"),
    "R01-SEMICONDUCTOR-SEC004": ("GIGADEVICE", "603986", "兆易创新", "SH"),
    "R01-SEMICONDUCTOR-SEC005": ("NAURA", "002371", "北方华创", "SZ"),
    "R01-SEMICONDUCTOR-SEC006": ("MAXSCEND", "300782", "卓胜微", "SZ"),
    "R01-SEMICONDUCTOR-SEC007": ("BOE", "000725", "京东方A", "SZ"),
    "R01-SEMICONDUCTOR-SEC008": ("JCET", "600584", "长电科技", "SH"),
    "R01-SEMICONDUCTOR-SEC009": ("AMEC", "688012", "中微公司", "SH"),
    "R01-SEMICONDUCTOR-SEC010": ("PIOTECH", "688072", "拓荆科技", "SH"),
    "R01-SEMICONDUCTOR-SEC011": ("NSIG", "688126", "沪硅产业", "SH"),
    "R01-SEMICONDUCTOR-SEC012": ("TCLTECH", "000100", "TCL科技", "SZ"),
    "R01-SEMICONDUCTOR-SEC013": ("TFME", "002156", "通富微电", "SZ"),
    "R01-SEMICONDUCTOR-SEC014": ("LUXSHARE", "002475", "立讯精密", "SZ"),
    "R01-SEMICONDUCTOR-SEC015": ("GOERTEK", "002241", "歌尔股份", "SZ"),
    "R01-SEMICONDUCTOR-SEC016": ("CAMBRICON", "688256", "寒武纪", "SH"),
    "R01-SEMICONDUCTOR-SEC017": ("LONGYS", "301308", "江波龙", "SZ"),
    "R01-SEMICONDUCTOR-SEC018": ("BIWIN", "688525", "佰维存储", "SH"),
    "R01-SEMICONDUCTOR-SEC019": ("HYGON", "688041", "海光信息", "SH"),
}

# 事件（EV-SEMI-01..15；与 R01-01 的 EV-HIEQ-* 命名空间隔离）
EVENTS = [
    ("EV-SEMI-01", "2018-04-16", "中兴通讯被美国商务部激活拒绝令（半导体自主可控叙事起点）", "policy", "R01-SEMICONDUCTOR-E001"),
    ("EV-SEMI-02", "2019-05-16", "美国商务部 BIS 将华为列入实体清单（一手 Federal Register 文件）", "policy", "R01-SEMICONDUCTOR-E002"),
    ("EV-SEMI-03", "2019-07-22", "科创板开市，半导体设计公司集中上市", "market", "R01-SEMICONDUCTOR-E007"),
    ("EV-SEMI-04", "2020-07-14", "申万半导体板块指数创 2020 年内最高 5869.83", "market", "R01-SEMICONDUCTOR-E011"),
    ("EV-SEMI-05", "2020-07-16", "中芯国际登陆科创板（A 股半导体制造龙头回归）", "company", "R01-SEMICONDUCTOR-E009"),
    ("EV-SEMI-06", "2021-07-30", "申万半导体板块指数月内最高 7642.58（2019–2021 全周期最高）", "market", "R01-SEMICONDUCTOR-E012"),
    ("EV-SEMI-07", "2019-10-22", "国家大基金二期成立（注册资本 2041.5 亿元）", "policy", "R01-SEMICONDUCTOR-E013"),
    ("EV-SEMI-08", "2020-06-01", "LCD 面板价格起涨（韩厂退出 + 供给收紧）", "industry", "R01-SEMICONDUCTOR-E015"),
    ("EV-SEMI-09", "2021-06-01", "65 吋面板价格见 294 美元/片峰值", "industry", "R01-SEMICONDUCTOR-E016"),
    ("EV-SEMI-10", "2021-09-30", "面板价格自 2021-08 起快速下跌，至 2022-09 跌至 106 美元", "industry", "R01-SEMICONDUCTOR-E022"),
    ("EV-SEMI-11", "2019-01-29", "立讯精密、歌尔股份自 2019 年初进入单边上行（TWS 周期启动）", "market", "R01-SEMICONDUCTOR-E024"),
    ("EV-SEMI-12", "2020-10-13", "立讯精密月内最高 62.73 元、歌尔股份 2020-11 月内最高 49.05 元", "market", "R01-SEMICONDUCTOR-E025"),
    ("EV-SEMI-13", "2023-04-10", "申万半导体板块指数 2023 年内最高 5154.69（AI 算力行情见顶）", "market", "R01-SEMICONDUCTOR-E032"),
    ("EV-SEMI-14", "2025-10-31", "申万半导体板块指数 7964.33，超过 2021-07 的 7642.58 创指数新高", "market", "R01-SEMICONDUCTOR-E037"),
    ("EV-SEMI-15", "2022-10-12", "申万半导体板块指数月内最低 3605.80（去库存下行低点）", "market", "R01-SEMICONDUCTOR-E045"),
]

# (canonical campaign id, event_id, role)
CAMPAIGN_EVENTS = [
    ("C-2019-SEMI-LOCALIZATION", "EV-SEMI-01", "context"),
    ("C-2019-SEMI-LOCALIZATION", "EV-SEMI-02", "trigger"),
    ("C-2019-SEMI-LOCALIZATION", "EV-SEMI-03", "catalyst"),
    ("C-2019-SEMI-LOCALIZATION", "EV-SEMI-04", "follow_up"),
    ("C-2020-SEMI-EQUIPMENT", "EV-SEMI-05", "trigger"),
    ("C-2020-SEMI-EQUIPMENT", "EV-SEMI-07", "context"),
    ("C-2020-SEMI-EQUIPMENT", "EV-SEMI-06", "follow_up"),
    ("C-2020-PANEL-CYCLE", "EV-SEMI-08", "trigger"),
    ("C-2020-PANEL-CYCLE", "EV-SEMI-09", "follow_up"),
    ("C-2020-PANEL-CYCLE", "EV-SEMI-10", "follow_up"),
    ("C-2019-CONSUMER-TWS", "EV-SEMI-11", "trigger"),
    ("C-2019-CONSUMER-TWS", "EV-SEMI-12", "follow_up"),
    ("C-2023-AI-COMPUTE-SEMI", "EV-SEMI-13", "follow_up"),
    ("C-2024-SEMI-MEMORY", "EV-SEMI-14", "follow_up"),
    ("C-2022-SEMI-DOWNTURN", "EV-SEMI-15", "follow_up"),
]

# 共享 evidence 的唯一归属（validate_batch_research 强制 1 evidence : 1 campaign）
EVIDENCE_OWNER = {
    "R01-SEMICONDUCTOR-E035": "007",   # 2024-09-24 政策放大 → 007（008 为 RESEARCH_ONLY）
    "R01-SEMICONDUCTOR-E056": "002",   # 按包内绑定归属 002（008 为 RESEARCH_ONLY）
}


def load():
    out = {}
    for name in ("candidates", "evidence", "sources", "securities"):
        with io.open(os.path.join(PKG, name + ".json"), encoding="utf-8") as fh:
            out[name] = json.load(fh)
    return out


def main(argv):
    dry = "--dry-run" in argv
    verify_only = "--verify" in argv
    pkg = load()
    cand_by_k = {c["candidate_id"].split("-")[-1]: c for c in pkg["candidates"]}
    ev_by_id = {e["evidence_id"]: e for e in pkg["evidence"]}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def have(table, col, val):
        return cur.execute("SELECT 1 FROM %s WHERE %s=?" % (table, col), (val,)).fetchone() is not None

    plan = []

    def add(table, key, sql, params):
        """登记一条写入（用默认参数捕获循环变量，避免闭包陷阱）。"""
        plan.append((table, key, lambda s=sql, p=params: cur.execute(s, p)))

    # ---- rule ----
    if not have("research_rules", "rule_id", RULE_ID):
        add("research_rules", RULE_ID,
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "半导体 / 电子历史周期观察", "电子",
             "R01-02（半导体 / 电子）历史周期观察窗口。" + PROV, "under_review"))

    # ---- annual_reviews ----
    for yr in sorted(ANNUAL):
        arid = "AR-SEMI-%d" % yr
        if not have("annual_reviews", "annual_review_id", arid):
            st, summary = ANNUAL[yr]
            add("annual_reviews", arid,
                "INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes) VALUES (?,?,?,?,?,?)",
                (arid, RULE_ID, yr, st, summary, PROV))

    # ---- campaigns（8 PROMOTE）----
    for c in CAMPAIGNS:
        cid = c["cid"]
        if not have("campaigns", "campaign_id", cid):
            add("campaigns", cid,
                "INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,campaign_year,start_date,end_date,peak_date,"
                "strength,result,classification,start_date_basis,end_date_basis,"
                "date_confidence,description,research_notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (cid, "AR-SEMI-%d" % c["year"], RULE_ID, c["season"], c["year"], c["start"], c["end"], c["peak"],
                 c["strength"], c["result"], c["cls"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 c["dc"],
                 "%s［intake R01-SEMICONDUCTOR-%s］" % (cand_by_k[c["k"]]["title"], c["k"]),
                 c["notes"] + "｜theme_cycle_id=%s｜provenance: %s" % (c["cycle"], PROV)))

    # ---- campaign_themes ----
    for c in CAMPAIGNS:
        for tid, role in c["themes"]:
            if not cur.execute("SELECT 1 FROM campaign_themes WHERE campaign_id=? AND theme_id=?",
                               (c["cid"], tid)).fetchone():
                add("campaign_themes", "%s/%s" % (c["cid"], tid),
                    "INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)", (c["cid"], tid, role))

    # ---- securities ----
    for intake_id, (sid, ticker, name, exch) in SEC_CANON.items():
        if not have("securities", "security_id", sid):
            add("securities", sid,
                "INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)", (sid, ticker, name, exch))

    # ---- sources ----
    src_map = {}
    for i, s in enumerate(pkg["sources"], start=1):
        sid = "S-SEMI-%02d" % i
        src_map[s["source_id"]] = sid
        if not have("sources", "source_id", sid):
            add("sources", sid,
                "INSERT INTO sources (source_id,source_type,title,author,url,published_at,captured_at,publisher,description,tier)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sid, s["source_type"], s["title"], s.get("author"), s.get("url"), s.get("published_at"), None,
                 s["publisher"], "%s［intake %s］" % (s.get("description") or "", s["source_id"]), s["tier"]))

    # ---- evidences ----
    # ★ 与 R01-01 同一口径：**RESEARCH_ONLY 候选的专属 evidence 不入 DB**。
    #   理由：这些候选不进 campaigns 表 → 若导入其 supporting 证据会产生
    #   `orphan-supporting-evidence` 警告。研究内容完整保留在 intake Package 中。
    PROMOTED_KS = {c["k"] for c in CAMPAIGNS}
    RC_KS = {r["k"] for r in RESEARCH_CANDIDATES}
    rc_ev, promoted_ev = set(), set()
    for k in RC_KS:
        rc_ev |= set(cand_by_k[k]["evidence_ids"])
    for k in PROMOTED_KS:
        promoted_ev |= set(cand_by_k[k]["evidence_ids"])
    RC_ONLY_EV = rc_ev - promoted_ev

    print("  RESEARCH_ONLY 专属 evidence（不入 DB）: %d 条" % len(RC_ONLY_EV))
    # ---- evidences（全部 56 条入库）----
    ev_map = {}
    for i, e in enumerate(pkg["evidence"], start=1):
        if e["evidence_id"] in RC_ONLY_EV:
            continue  # RESEARCH_ONLY 专属 → 不入 DB（见上）
        eid = "E-SEMI-%02d" % i
        ev_map[e["evidence_id"]] = eid
        if not have("evidences", "evidence_id", eid):
            desc = "%s［intake %s｜role=%s｜independence=%s］" % (
                e["claim"], e["evidence_id"], e["evidence_role"], e["independence_group"])
            if e.get("point_in_time_note"):
                desc += "｜PIT: " + e["point_in_time_note"]
            add("evidences", eid,
                "INSERT INTO evidences (evidence_id,source_id,date,evidence_type,description,evidence_role,confidence,"
                "independence_group,temporal_relation) VALUES (?,?,?,?,?,?,?,?,?)",
                (eid, src_map[e["source_id"]], e.get("event_date"), e["evidence_type"], desc, e["evidence_role"],
                 e["confidence"], e["independence_group"], e["temporal_relation"]))

    # ---- events ----
    ev_src = {e["evidence_id"]: e["source_id"] for e in pkg["evidence"]}
    for eid, date, name, etype, intake_ev in EVENTS:
        if not have("events", "event_id", eid):
            add("events", eid,
                "INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)",
                (eid, date, name, etype, "%s｜provenance: %s" % (intake_ev, PROV), src_map[ev_src[intake_ev]]))

    # ---- campaign_evidences（唯一归属）----
    for c in CAMPAIGNS:
        for ieid in cand_by_k[c["k"]]["evidence_ids"]:
            owner = EVIDENCE_OWNER.get(ieid)
            if owner is not None and owner != c["k"]:
                continue
            eid = ev_map[ieid]
            if not cur.execute("SELECT 1 FROM campaign_evidences WHERE campaign_id=? AND evidence_id=?",
                               (c["cid"], eid)).fetchone():
                add("campaign_evidences", "%s/%s" % (c["cid"], eid),
                    "INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)",
                    (c["cid"], eid, ev_by_id[ieid]["evidence_role"]))

    # ---- campaign_events ----
    for cid, eid, role in CAMPAIGN_EVENTS:
        if not cur.execute("SELECT 1 FROM campaign_events WHERE campaign_id=? AND event_id=?", (cid, eid)).fetchone():
            add("campaign_events", "%s/%s" % (cid, eid),
                "INSERT INTO campaign_events (campaign_id,event_id,role) VALUES (?,?,?)", (cid, eid, role))

    # ---- campaign_securities ----
    for c in CAMPAIGNS:
        for intake_sec in cand_by_k[c["k"]]["security_ids"]:
            sid = SEC_CANON[intake_sec][0]
            if not cur.execute("SELECT 1 FROM campaign_securities WHERE campaign_id=? AND security_id=?",
                               (c["cid"], sid)).fetchone():
                add("campaign_securities", "%s/%s" % (c["cid"], sid),
                    "INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                    (c["cid"], sid, "representative"))

    # ---- campaign_phases ----
    ph_n = 0
    STAGE = {"MAIN_RISE": "main_rise", "RETRACEMENT": "retracement", "DECLINING": "decline",
             "SECONDARY": "secondary_rally", "PEAK": None, "UNKNOWN": None}

    for c in CAMPAIGNS:
        cand = cand_by_k[c["k"]]
        for l in cand["lifecycle"]:
            stage = l["stage_proposal"]
            if stage not in STAGE or STAGE[stage] is None or not l["start"] or not l["end"]:
                continue
            if l["start"] < c["start"]:
                continue
            end = l["end"]
            if c["end"] and end > c["end"]:
                end = c["end"]  # 截断到 campaign end，保持自洽
            if end < l["start"]:
                continue
            ph_n += 1
            pid = "PH-SEMI-%02d" % ph_n
            if not have("campaign_phases", "phase_id", pid):
                add("campaign_phases", pid,
                    "INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,description)"
                    " VALUES (?,?,?,?,?,?)",
                    (pid, c["cid"], STAGE[stage], l["start"], end, "%s（intake lifecycle）｜%s" % (stage, PROV)))

    # ---- campaign_date_observations ----
    for c in CAMPAIGNS:
        for role, val in (("start", c["start"]), ("peak", c["peak"]), ("end", c["end"])):
            if not val:
                continue
            oid = "OBS-%s-%s" % (c["cid"], role)
            if not have("campaign_date_observations", "observation_id", oid):
                add("campaign_date_observations", oid,
                    "INSERT INTO campaign_date_observations (observation_id,campaign_id,date_role,candidate_date,verified_date,"
                    "verification_method,confidence,evidence_id,notes) VALUES (?,?,?,?,?,?,?,?,?)",
                    (oid, c["cid"], role, val, None, "unknown", c["dc"], None,
                     "candidate 快照自 R01-02 intake date_candidates；未经行情核验。｜%s" % PROV))

    print("=== 计划写入 %d 行 ===" % len(plan))
    from collections import Counter
    for t, n in sorted(Counter(p[0] for p in plan).items()):
        print("  %-30s %d" % (t, n))
    for t, k, _ in plan:
        print("    + %-30s %s" % (t, k))

    if verify_only:
        print("verify: %s" % ("PASS（全部已存在）" if not plan else "FAIL（仍有 %d 行待写入）" % len(plan)))
        conn.close()
        return 0 if not plan else 1

    if dry:
        print("--dry-run：未写入。")
        conn.close()
        return 0

    for _t, _k, fn in plan:
        fn()
    conn.commit()
    print("=== 写入完成 ===")
    for t in ("themes", "research_rules", "annual_reviews", "campaigns", "sources", "evidences", "events", "securities",
              "campaign_themes", "campaign_evidences", "campaign_events", "campaign_securities", "campaign_phases",
              "campaign_date_observations"):
        print("  %-30s %d" % (t, cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
