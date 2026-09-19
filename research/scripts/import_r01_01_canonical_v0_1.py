#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""import_r01_01_canonical_v0_1.py —— 将 R01-01 Intake Package 导入 ThreeC Canonical DB。

## 依据

- 审查结论：`docs/R01_01_INTAKE_REVIEW_v0_1.md`（5 PROMOTE + 2 RESEARCH_ONLY）
- taxonomy：`docs/T01_TAXONOMY_GAP_RESOLUTION_v0_1.md`（T01 已补齐 11 个 root）
- 模型：Research Model v1.0 · schema：`research/schema/schema.sql`（**未修改**）

## 边界

- 严格遵守 `schema.sql`；**不新增表 / 列**。
- **不修改** 既有 13 个 Campaign / 既有 Evidence / 既有 Theme / 既有 Rule。
- 2 个 `INSUFFICIENT` 候选 **不得升级** → 写为 `research_candidates`（`RC-*`）。
- canonical ID 使用 ThreeC 既有规则：`C-<YYYY>-<SLUG>` / `RC-<YYYY>-<SLUG>` /
  `E-HIEQ-NN` / `S-HIEQ-NN` / `EV-HIEQ-NN` / `PH-HIEQ-NN` / `AR-HIEQ-<YYYY>` / `rule_*`。
- **不使用** `R01-HIEQ-*` 作为 canonical ID；通过 `research_notes` 保留 intake provenance 映射。
- 幂等：已存在则跳过；重复运行结果一致。

## 用法

    python research/scripts/import_r01_01_canonical_v0_1.py --dry-run
    python research/scripts/import_r01_01_canonical_v0_1.py
    python research/scripts/import_r01_01_canonical_v0_1.py --verify
"""

from __future__ import annotations

import json
import io
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
PKG = os.path.join(ROOT, "research", "intake", "packages", "R01-01")

PROV = "R01-01 Intake Package（source_commit 2153f6d）｜审查 docs/R01_01_INTAKE_REVIEW_v0_1.md"
RULE_ID = "rule_high_end_equipment"
SEASON_PREFIX = "hieq"

# ------------------------------------------------------------------ Campaign 决策表
# canonical_id, intake_id, year, start, peak, end, classification, strength, result,
# date_confidence, season_id, themes[(theme_id, role)], title, why_campaign, why_not
CAMPAIGNS = [
    dict(
        cid="C-2016-HIEQ-CONSTR", intake="R01-HIEQ-001", year=2016,
        start="2016-08-01", peak="2021-01-25", end="2021-12-31",
        classification="industry_trend", strength="strong", result="positive",
        date_confidence="medium", season="hieq_constr_2016_2021",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-CONSTR", "main")],
        title="工程机械景气周期（更新周期 + 基建需求 + 环保淘汰三重叠加）",
        notes=(
            "★ campaign_year 取 start 年份（既有 13/13 口径）；包内提案为 2021（峰值年），"
            "此处按既有口径取 2016。★ peak_date 取代表资产股价高点（2021-01-25，三一重工/恒立液压）；"
            "产业销量峰值为 2021-03-31（7.9 万台、同比 +60%）—— 二者非事实矛盾，而是产业指标与资产价格不同步"
            "（CONFLICT R01-HIEQ-CF004，KEEP_BOTH）。★ end_date = 2021-12-31 为 RETRACEMENT 段末（最后有证据的日期），"
            "**不主张**该周期已在某确定日期「结束」；2022-01 之后阶段为 UNKNOWN。"
        ),
    ),
    dict(
        cid="C-2018-HIEQ-ROBOT-DOWN", intake="R01-HIEQ-002", year=2018,
        start="2018-09-30", peak="2019-09-30", end="2019-12-31",
        classification="industry_trend", strength="medium", result="weak",
        date_confidence="medium", season="hieq_robot_2018_2019",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-ROBOT", "main")],
        title="工业机器人产量下行周期（2018-09 至 2019-09，制造业资本开支收缩）",
        notes=(
            "★ 这是 ThreeC 首个「下行周期」型结构：`result = weak` 表示该段**行情为负向**，"
            "不是「弱 Campaign」。★ `peak_date` 语义在此为「下行段低点（产量转正前）」而非行情高点 —— "
            "包内 why_not ① 已显式标注该语义偏移。★ 包内 year 提案为 2019；此处按既有 start 年份口径取 2018。"
            "★ 分类为 industry_trend 而非 theme_campaign：本包证据不足证明该段形成了独立的主题叙事。"
        ),
    ),
    dict(
        cid="C-2020-HIEQ-AUTOMATION", intake="R01-HIEQ-003", year=2020,
        start="2020-04-01", peak="2021-07-01", end="2022-12-31",
        classification="industry_trend", strength="strong", result="positive",
        date_confidence="medium", season="hieq_automation_2020_2022",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-AUTOMATION", "main")],
        title="工业自动化复苏周期（疫情后制造业资本开支回补 + 自动化渗透率提升）",
        notes=(
            "★ 与 C-2018-HIEQ-ROBOT-DOWN 同属 ThemeCycle `hieq_robot_2018_2022`，"
            "Pattern = **Sequential（顺序型）**：低谷分隔、方向相反、驱动变量不同 → 两个独立 Campaign，非同一 Campaign 的两阶段。"
            "★ 行业盈利质量存在反证：2020 年行业营收 +6.0% 而利润 -26.9%（量增价跌），已记入 why_not。"
            "★ 跨 Campaign 证据归属：intake E009（2018/2019 产量）与 E016（2022/2023 产量）"
            "同属本候选与 C-2018-HIEQ-ROBOT-DOWN / C-2023-HIEQ-ROBOT-PLUS；"
            "按 canonical 1 evidence : 1 campaign 规则，二者分别归属前两者；"
            "本候选对应事实由 E-HIEQ-11（2020 年产量 237068 套）与 E-HIEQ-14（2022 上半年 -11%）覆盖。"
        ),
    ),
    dict(
        cid="C-2023-HIEQ-ROBOT-PLUS", intake="R01-HIEQ-004", year=2023,
        start="2023-01-19", peak="2023-02-03", end=None,
        classification="event_driven", strength="medium", result="positive",
        date_confidence="medium", season="hieq_robot_2023",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-ROBOT", "main")],
        title="「机器人+」政策驱动行情（2023-01 十七部门应用行动实施方案）",
        notes=(
            "★ `end_date = NULL`：本候选与 C-2023-HIEQ-HUMANOID 在 2023-03~04 的边界**无法切分**"
            "（intake cross_task_note R01-HIEQ-CT005），按协议**不虚构边界**。"
            "★ 二者同属 ThemeCycle `hieq_robot_2023`，Pattern = Sequential。"
            "★ 政策为唯一显性驱动，而产业侧当时仍处产量负增长（2023 年 1-2 月 -19.2%）。"
            "★ 跨 Campaign 证据归属：intake E016（2022/2023 产量数据）同属本候选与 C-2020-HIEQ-AUTOMATION，"
            "按 canonical 规则归属本候选（政策低位背景）。"
        ),
    ),
    dict(
        cid="C-2023-HIEQ-HUMANOID", intake="R01-HIEQ-005", year=2023,
        start="2023-05-01", peak="2023-11-02", end="2023-12-31",
        classification="theme_campaign", strength="medium", result="positive",
        date_confidence="medium", season="hieq_robot_2023",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-ROBOT", "secondary"), ("TH-HIEQ-HUMANOID", "main")],
        title="人形机器人产业叙事形成段（2023-05 具身智能表述起至 2023-12 Optimus Gen2 / 指导意见）",
        notes=(
            "★ start 依赖回顾性来源（2023-05 事件的同期性无法证明）→ 采用 DATE_WINDOW，取窗口左沿 2023-05-01。"
            "★ 2023-08-29 的市场反应存在 Beta Contamination（当日沪指 +1.20%、超 4700 只个股上涨）"
            "（CONFLICT R01-HIEQ-CF002，KEEP_BOTH）—— 已单列 contradicting 证据 E-HIEQ-26。"
            "★ 与 C-2023-HIEQ-ROBOT-PLUS 的边界未切分；与人形机器人量产段（RC-2024-HIEQ-HUMANOID-MASS）"
            "是否同一 Campaign 属 CONFLICT R01-HIEQ-CF008（UNRESOLVED），**保留不裁决**。"
        ),
    ),
]

RESEARCH_CANDIDATES = [
    dict(
        cid="RC-2024-HIEQ-EQUIP-UPDATE", intake="R01-HIEQ-006", year=2024,
        start="2024-03-07", peak="2024-07-24", end=None,
        classification="mixed", strength="weak", result="unknown",
        date_confidence="low", season="hieq_equip_update_2024",
        themes=[("TH-HIEQ", "main")],
        title="大规模设备更新政策驱动的装备需求（2024-03 行动方案至 2024-07 资金加码）",
        notes=(
            "★ **RESEARCH_ONLY（INSUFFICIENT）** —— 不得升级为 Campaign。理由："
            "① 市场侧证据 **0 条** → Campaign Independence Gate Q1（独立注意力中心）**无法验证**；"
            "② 行业口径过宽（11 个重点行业，含钢铁/有色/石化/化工/建材/电力）→ 与 R01-03 及「电力设备」实质重叠；"
            "③ 政策与需求之间缺少可验证的传导证据；④ 标的与 C-2016-HIEQ-CONSTR **完全重合**。"
            "★ 保留为 Research Candidate，供后续轮次在补齐市场侧证据后重新评估。"
        ),
    ),
    dict(
        cid="RC-2024-HIEQ-HUMANOID-MASS", intake="R01-HIEQ-007", year=2024,
        start="2024-09-01", peak="2025-07-01", end=None,
        classification="mixed", strength="weak", result="unknown",
        date_confidence="low", season="hieq_humanoid_mass_2024_2025",
        themes=[("TH-HIEQ", "related"), ("TH-HIEQ-HUMANOID", "main")],
        title="人形机器人量产预期与国产产业链加速段（2024-09 至 2025）",
        notes=(
            "★ **RESEARCH_ONLY（INSUFFICIENT）** —— 不得升级为 Campaign。理由："
            "① 市场侧证据 **0 条** → Gate Q1 无法验证；"
            "② 证据 E-HIEQ-33 与 E-HIEQ-34 实为同源（仅 1 个有效 independence_group）→ 不满足 ≥2 独立组门槛；"
            "③ start / end 均依赖回顾性来源（low）；"
            "④ 与 C-2023-HIEQ-HUMANOID 的边界未切分（CONFLICT R01-HIEQ-CF008 UNRESOLVED）。"
            "★ campaign_year 按既有 start 年份口径取 2024（包内提案为 2025）。"
        ),
    ),
]

# ------------------------------------------------------------------ annual_reviews
ANNUAL = {
    2016: ("medium", "工程机械景气周期启动（Priority B 段，逐月一手序列未取得，start 仅 DATE_WINDOW）。"),
    2018: ("weak", "工业机器人产量下行周期启动；无独立主题叙事证据。"),
    2020: ("strong", "工业自动化复苏周期：证据强度最高（国家统计局月度序列 + 券商月报 + 一手公司披露）。"),
    2023: ("medium", "「机器人+」政策行情 + 人形机器人产业叙事形成；市场侧证据有限。"),
    2024: ("weak", "设备更新政策 + 人形机器人量产段：市场侧证据均为 0，两条均判 INSUFFICIENT。"),
}

# ------------------------------------------------------------------ securities
SECURITIES = [
    ("SANY", "600031", "三一重工", "SH"), ("ZOOMLION", "000157", "中联重科", "SZ"),
    ("XCMG", "000425", "徐工机械", "SZ"), ("HENGLI", "601100", "恒立液压", "SH"),
    ("ESTUN", "002747", "埃斯顿", "SZ"), ("INOVANCE", "300124", "汇川技术", "SZ"),
    ("SIASUN", "300024", "机器人", "SZ"), ("TOPSTAR", "300607", "拓斯达", "SZ"),
    ("LEADERDRIVE", "688017", "绿的谐波", "SH"), ("KINCO", "688160", "步科股份", "SH"),
    ("XINBANG", "300753", "信邦智能", "SZ"), ("TECHLONG", "002209", "达意隆", "SZ"),
    ("SHUANGHUAN", "002472", "双环传动", "SZ"), ("LEADSHINE", "002979", "雷赛智能", "SZ"),
    ("ZHAOWEI", None, "兆威机电", None), ("EFORT", None, "埃夫特", None),
]

# intake security_id → canonical security_id（SEC017 与 SEC008 为同一标的「拓斯达」→ 合并）
SEC_MAP = {
    "R01-HIEQ-SEC001": "SANY", "R01-HIEQ-SEC002": "ZOOMLION", "R01-HIEQ-SEC003": "XCMG",
    "R01-HIEQ-SEC004": "HENGLI", "R01-HIEQ-SEC005": "ESTUN", "R01-HIEQ-SEC006": "INOVANCE",
    "R01-HIEQ-SEC007": "SIASUN", "R01-HIEQ-SEC008": "TOPSTAR", "R01-HIEQ-SEC009": "LEADERDRIVE",
    "R01-HIEQ-SEC010": "KINCO", "R01-HIEQ-SEC011": "XINBANG", "R01-HIEQ-SEC012": "TECHLONG",
    "R01-HIEQ-SEC013": "SHUANGHUAN", "R01-HIEQ-SEC014": "LEADSHINE", "R01-HIEQ-SEC015": "ZHAOWEI",
    "R01-HIEQ-SEC016": "EFORT",
    # SEC017「拓斯达（国产产业链签约方，见 SEC008）」与 SEC008 为同一标的 → 合并至 TOPSTAR
    "R01-HIEQ-SEC017": "TOPSTAR",
}
SEC_ROLE_MAP = {  # (candidate intake id) → [(canonical sec id, role)]
    "R01-HIEQ-001": [("SANY", "leader"), ("ZOOMLION", "second_leader"),
                     ("XCMG", "representative"), ("HENGLI", "representative")],
    "R01-HIEQ-002": [("ESTUN", "leader"), ("INOVANCE", "leader"), ("SIASUN", "representative")],
    "R01-HIEQ-003": [("ESTUN", "leader"), ("INOVANCE", "leader"), ("TOPSTAR", "second_leader"),
                     ("LEADERDRIVE", "representative"), ("KINCO", "representative")],
    "R01-HIEQ-004": [("ESTUN", "leader"), ("XINBANG", "representative"),
                     ("TECHLONG", "representative"), ("SHUANGHUAN", "representative")],
    "R01-HIEQ-005": [("LEADERDRIVE", "representative"), ("KINCO", "representative"),
                     ("LEADSHINE", "follow"), ("ZHAOWEI", "representative"), ("EFORT", "representative")],
    "R01-HIEQ-006": [("SANY", "leader"), ("ZOOMLION", "second_leader"),
                     ("XCMG", "representative"), ("HENGLI", "representative")],
    "R01-HIEQ-007": [("LEADERDRIVE", "representative"), ("KINCO", "representative"),
                     ("LEADSHINE", "follow"), ("ZHAOWEI", "representative"),
                     ("EFORT", "representative"), ("TOPSTAR", "follow")],
}

# ------------------------------------------------------------------ events（19）
# (canonical event_id, date, name, event_type, intake evidence id → 其 source)
EVENTS = [
    ("EV-HIEQ-01", "2016-08-01", "工程机械 2016-08 起持续热销（「十三五」基建开工 + 2009-2012 设备更新周期 + 环保淘汰）", "industry", "R01-HIEQ-E002"),
    ("EV-HIEQ-02", "2021-03-31", "2021 年 3 月挖掘机销量 7.9 万台、同比 +60%，创历史峰值", "industry", "R01-HIEQ-E003"),
    ("EV-HIEQ-03", "2021-11-19", "三一重工 2021Q2/Q3 归母净利润同比 -28.56% / -35.31%，股价较高点跌近 60%", "company", "R01-HIEQ-E006"),
    ("EV-HIEQ-04", "2018-09-30", "2018 年 9 月中国工业机器人单月产量首次负增长（此后连续 13 个月负增长）", "industry", "R01-HIEQ-E007"),
    ("EV-HIEQ-05", "2019-08-31", "2019 世界机器人大会：新松机器人曲道奎指汽车行业增速放缓为机器人行业放缓主因", "industry", "R01-HIEQ-E040"),
    ("EV-HIEQ-06", "2019-10-01", "2019 年 10 月中国工业机器人产量转为正增长（+1.7%），下行段结束", "industry", "R01-HIEQ-E007"),
    ("EV-HIEQ-07", "2020-06-30", "2020 年 6 月工业机器人单月产量 20761 套、同比 +29.2%，为年内单月最高增速", "industry", "R01-HIEQ-E010"),
    ("EV-HIEQ-08", "2020-07-31", "2020 年 7 月工业机器人产量 21170 套、同比 +19.4%；机器人板块月涨 18.2%", "market", "R01-HIEQ-E012"),
    ("EV-HIEQ-09", "2021-07-01", "通用自动化行业景气于 2021 年 Q3 见顶（埃斯顿年报自述）；2021-07 起受上游通胀与出口订单下滑影响", "industry", "R01-HIEQ-E015"),
    ("EV-HIEQ-10", "2023-01-18", "工信部等十七部门印发《「机器人+」应用行动实施方案》（工信部联通装〔2022〕187号）", "policy", "R01-HIEQ-E017"),
    ("EV-HIEQ-11", "2023-01-19", "机器人概念早盘放量跳空高开、板块指数创 2 月来新高；信邦智能 20% 涨停", "market", "R01-HIEQ-E018"),
    ("EV-HIEQ-12", "2023-08-22", "2023 世界机器人大会（8/16-22）国产人形机器人集中亮相；北京市设立 100 亿机器人产业基金", "industry", "R01-HIEQ-E025"),
    ("EV-HIEQ-13", "2023-11-02", "工信部印发《人形机器人创新发展指导意见》", "policy", "R01-HIEQ-E021"),
    ("EV-HIEQ-14", "2023-12-13", "特斯拉第二代人形机器人 Optimus Gen2 正式亮相", "company", "R01-HIEQ-E022"),
    ("EV-HIEQ-15", "2023-12-29", "优必选登陆港交所（人形机器人领域首家上市企业）；傅利叶智能 GR-1 开启预售", "company", "R01-HIEQ-E023"),
    ("EV-HIEQ-16", "2024-03-07", "国务院印发《推动大规模设备更新和消费品以旧换新行动方案》（国发〔2024〕7号）", "policy", "R01-HIEQ-E027"),
    ("EV-HIEQ-17", "2024-07-24", "发改委、财政部印发《关于加力支持大规模设备更新和消费品以旧换新的若干措施》", "policy", "R01-HIEQ-E028"),
    ("EV-HIEQ-18", "2024-11-15", "华为具身智能创新中心正式运营，与乐聚机器人、拓斯达、埃夫特、兆威机电等 16 家企业签约", "company", "R01-HIEQ-E031"),
    ("EV-HIEQ-19", "2025-07-31", "智元、宇树中标中国移动人形双足机器人代工服务采购项目，合计 1.24 亿元", "company", "R01-HIEQ-E033"),
]

# (canonical campaign id, event_id, role)
CAMPAIGN_EVENTS = [
    ("C-2016-HIEQ-CONSTR", "EV-HIEQ-01", "context"),
    ("C-2016-HIEQ-CONSTR", "EV-HIEQ-02", "trigger"),
    ("C-2016-HIEQ-CONSTR", "EV-HIEQ-03", "follow_up"),
    ("C-2018-HIEQ-ROBOT-DOWN", "EV-HIEQ-04", "trigger"),
    ("C-2018-HIEQ-ROBOT-DOWN", "EV-HIEQ-05", "context"),
    ("C-2018-HIEQ-ROBOT-DOWN", "EV-HIEQ-06", "follow_up"),
    ("C-2020-HIEQ-AUTOMATION", "EV-HIEQ-07", "trigger"),
    ("C-2020-HIEQ-AUTOMATION", "EV-HIEQ-08", "catalyst"),
    ("C-2020-HIEQ-AUTOMATION", "EV-HIEQ-09", "follow_up"),
    ("C-2023-HIEQ-ROBOT-PLUS", "EV-HIEQ-10", "trigger"),
    ("C-2023-HIEQ-ROBOT-PLUS", "EV-HIEQ-11", "catalyst"),
    ("C-2023-HIEQ-HUMANOID", "EV-HIEQ-12", "catalyst"),
    ("C-2023-HIEQ-HUMANOID", "EV-HIEQ-13", "trigger"),
    ("C-2023-HIEQ-HUMANOID", "EV-HIEQ-14", "catalyst"),
    ("C-2023-HIEQ-HUMANOID", "EV-HIEQ-15", "catalyst"),
    ("RC-2024-HIEQ-EQUIP-UPDATE", "EV-HIEQ-16", "trigger"),
    ("RC-2024-HIEQ-EQUIP-UPDATE", "EV-HIEQ-17", "catalyst"),
    ("RC-2024-HIEQ-HUMANOID-MASS", "EV-HIEQ-18", "catalyst"),
    ("RC-2024-HIEQ-HUMANOID-MASS", "EV-HIEQ-19", "trigger"),
]

# phase 映射：package stage → schema phase_type（PEAK 不入 campaign_phases，由 campaigns.peak_date 承载）
PHASE_MAP = {
    "MAIN_RISE": "main_rise", "RETRACEMENT": "retracement", "DECLINING": "decline",
    "SECONDARY": "secondary_rally", "UNKNOWN": "unclear", "EARLY_SIGNAL": "startup",
}

# 需要 PEAK 显式跳过的候选（PEAK 由 campaigns.peak_date 表达）
SKIP_PEAK = True


def load_pkg():
    out = {}
    for name in ("candidates", "evidence", "sources", "securities"):
        with io.open(os.path.join(PKG, name + ".json"), encoding="utf-8") as fh:
            out[name] = json.load(fh)
    return out


def main(argv):
    dry = "--dry-run" in argv
    verify_only = "--verify" in argv
    pkg = load_pkg()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    def have(table, col, val):
        return cur.execute("SELECT 1 FROM %s WHERE %s=?" % (table, col), (val,)).fetchone() is not None

    plan = []

    cand_by_intake = {c["candidate_id"]: c for c in pkg["candidates"]}
    ev_by_intake = {e["evidence_id"]: e for e in pkg["evidence"]}

    # ★ Research Model v1.0 §4：Campaign Candidate「不能进入 campaigns 表」。
    #   既有 4 个 RC-*（RC-2023-HUAWEI 等）在 DB 中**零存在**，仅由导出脚本的
    #   RESEARCH_CANDIDATES 承载。本导入遵循同一设计：
    #   RESEARCH_ONLY 的 2 个候选 → 不写 campaigns / 不写任何 campaign_* 桥表，
    #   其**专属** evidence / source / event 亦不入 DB（避免孤儿证据告警）。
    rc_ev = set()
    for c in RESEARCH_CANDIDATES:
        rc_ev |= set(cand_by_intake[c["intake"]]["evidence_ids"])
    camp_ev = set()
    for c in CAMPAIGNS:
        camp_ev |= set(cand_by_intake[c["intake"]]["evidence_ids"])
    RC_ONLY_EV = rc_ev - camp_ev

    # ★ 跨 Campaign 证据消歧：`validate_batch_research.py` 强制 **1 evidence : 1 campaign**。
    #   intake 中 R01-HIEQ-E009 同属 002/003、R01-HIEQ-E016 同属 003/004 ——
    #   canonical 化须指定唯一归属（另一 Campaign 的需求由其自身证据覆盖）。
    EVIDENCE_OWNER = {
        "R01-HIEQ-E009": "R01-HIEQ-002",   # 2018/2019 产量数据 → 下行周期；003 的 2020 数据由 E011 覆盖
        "R01-HIEQ-E016": "R01-HIEQ-004",   # 2022/2023 产量数据 → 政策低位背景；003 的 2022 下行由 E014 覆盖
    }
    RC_ONLY_SRC = ({ev_by_intake[e]["source_id"] for e in RC_ONLY_EV}
                   - {ev_by_intake[e]["source_id"] for e in camp_ev})

    # ---- rule ----
    if not have("research_rules", "rule_id", RULE_ID):
        plan.append(("research_rules", RULE_ID, lambda: cur.execute(
            "INSERT INTO research_rules (rule_id,name,base_pattern,description,status) VALUES (?,?,?,?,?)",
            (RULE_ID, "高端装备历史周期观察", "高端装备",
             "R01-01（高端装备 / 机器人）历史周期观察窗口。" + PROV, "under_review"))))

    # ---- annual_reviews ----
    for yr in sorted(ANNUAL):
        arid = "AR-HIEQ-%d" % yr
        if not have("annual_reviews", "annual_review_id", arid):
            st, summary = ANNUAL[yr]
            plan.append(("annual_reviews", arid, (lambda a=arid, y=yr, s=st, m=summary:
                cur.execute("INSERT INTO annual_reviews (annual_review_id,rule_id,year,status,summary,review_notes)"
                            " VALUES (?,?,?,?,?,?)", (a, RULE_ID, y, s, m, PROV)))))

    # ---- campaigns（仅 PROMOTE；RESEARCH_ONLY 见上方说明，不入 campaigns 表）----
    for c in CAMPAIGNS:
        cid = c["cid"]
        if not have("campaigns", "campaign_id", cid):
            plan.append(("campaigns", cid, (lambda cc=c: cur.execute(
                "INSERT INTO campaigns (campaign_id,annual_review_id,rule_id,season_id,campaign_year,"
                "start_date,end_date,peak_date,strength,result,classification,start_date_basis,end_date_basis,"
                "date_confidence,description,research_notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (cc["cid"], "AR-HIEQ-%d" % cc["year"], RULE_ID, cc["season"], cc["year"],
                 cc["start"], cc["end"], cc["peak"], cc["strength"], cc["result"], cc["classification"],
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 "研究候选日期（intake date_candidates）；未经行情核验",
                 cc["date_confidence"],
                 "%s［intake %s］" % (cc["title"], cc["intake"]),
                 cc["notes"] + "｜provenance: " + PROV)))))

    # ---- themes ----
    for c in CAMPAIGNS:
        for tid, role in c["themes"]:
            if not have("campaign_themes", "campaign_id", c["cid"]) or \
               not cur.execute("SELECT 1 FROM campaign_themes WHERE campaign_id=? AND theme_id=?",
                               (c["cid"], tid)).fetchone():
                plan.append(("campaign_themes", "%s/%s" % (c["cid"], tid),
                             (lambda cc=c, t=tid, r=role: cur.execute(
                                 "INSERT INTO campaign_themes (campaign_id,theme_id,role) VALUES (?,?,?)",
                                 (cc["cid"], t, r)))))

    # ---- securities ----
    for sid, ticker, name, exch in SECURITIES:
        if not have("securities", "security_id", sid):
            plan.append(("securities", sid, (lambda s=sid, t=ticker, n=name, e=exch: cur.execute(
                "INSERT INTO securities (security_id,ticker,name,exchange) VALUES (?,?,?,?)", (s, t, n, e)))))

    # ---- sources ----
    src_map = {}
    for i, s in enumerate(pkg["sources"], start=1):
        sid = "S-HIEQ-%02d" % i
        if s["source_id"] in RC_ONLY_SRC:
            continue  # RC 专属来源不入 DB（见上）
        src_map[s["source_id"]] = sid
        if not have("sources", "source_id", sid):
            plan.append(("sources", sid, (lambda x=s, y=sid: cur.execute(
                "INSERT INTO sources (source_id,source_type,title,author,url,published_at,captured_at,"
                "publisher,description,tier) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (y, x["source_type"], x["title"], x.get("author"), x.get("url"), x.get("published_at"),
                 None, x["publisher"], "%s［intake %s］" % (x.get("description") or "", x["source_id"]),
                 x["tier"])))))

    # ---- evidences ----
    ev_map = {}
    for i, e in enumerate(pkg["evidence"], start=1):
        eid = "E-HIEQ-%02d" % i
        if e["evidence_id"] in RC_ONLY_EV:
            continue  # RC 专属证据不入 DB（见上）
        ev_map[e["evidence_id"]] = eid
        if not have("evidences", "evidence_id", eid):
            desc = "%s［intake %s｜role=%s｜independence=%s］" % (
                e["claim"], e["evidence_id"], e["evidence_role"], e["independence_group"])
            if e.get("point_in_time_note"):
                desc += "｜PIT: " + e["point_in_time_note"]
            plan.append(("evidences", eid, (lambda x=e, y=eid, d=desc, s=src_map[e["source_id"]]: cur.execute(
                "INSERT INTO evidences (evidence_id,source_id,date,evidence_type,description,evidence_role,"
                "confidence,independence_group,temporal_relation) VALUES (?,?,?,?,?,?,?,?,?)",
                (y, s, x.get("event_date"), x["evidence_type"], d, x["evidence_role"],
                 x["confidence"], x["independence_group"], x["temporal_relation"])))))

    # ---- events ----
    ev_src = {e["evidence_id"]: e["source_id"] for e in pkg["evidence"]}
    for eid, date, name, etype, intake_ev in EVENTS:
        if intake_ev in RC_ONLY_EV:
            continue  # RC 事件不入 DB（见上）
        if not have("events", "event_id", eid):
            plan.append(("events", eid, (lambda a=eid, d=date, n=name, t=etype, s=ev_src[intake_ev]: cur.execute(
                "INSERT INTO events (event_id,date,name,event_type,description,source_id) VALUES (?,?,?,?,?,?)",
                (a, d, n, t, "%s｜provenance: %s" % (intake_ev, PROV), src_map[s])))))

    # ---- bridges: campaign_evidences ----
    for c in CAMPAIGNS:
        for ieid in cand_by_intake[c["intake"]]["evidence_ids"]:
            owner = EVIDENCE_OWNER.get(ieid)
            if owner is not None and owner != c["intake"]:
                continue  # 该证据唯一归属于另一 Campaign
            eid = ev_map[ieid]
            if not cur.execute("SELECT 1 FROM campaign_evidences WHERE campaign_id=? AND evidence_id=?",
                               (c["cid"], eid)).fetchone():
                role = next(x["evidence_role"] for x in pkg["evidence"] if x["evidence_id"] == ieid)
                plan.append(("campaign_evidences", "%s/%s" % (c["cid"], eid),
                             (lambda a=c["cid"], b=eid, r=role: cur.execute(
                                 "INSERT INTO campaign_evidences (campaign_id,evidence_id,role) VALUES (?,?,?)",
                                 (a, b, r)))))

    # ---- bridges: campaign_events（RC 专属事件已跳过，桥表同样跳过）----
    rc_event_ids = {eid for eid, _d, _n, _t, intake_ev in EVENTS if intake_ev in RC_ONLY_EV}
    for cid, eid, role in CAMPAIGN_EVENTS:
        if eid in rc_event_ids:
            continue
        if not cur.execute("SELECT 1 FROM campaign_events WHERE campaign_id=? AND event_id=?",
                           (cid, eid)).fetchone():
            plan.append(("campaign_events", "%s/%s" % (cid, eid),
                         (lambda a=cid, b=eid, r=role: cur.execute(
                             "INSERT INTO campaign_events (campaign_id,event_id,role) VALUES (?,?,?)", (a, b, r)))))

    # ---- bridges: campaign_securities ----
    for c in CAMPAIGNS:
        for sid, role in SEC_ROLE_MAP[c["intake"]]:
            if not cur.execute("SELECT 1 FROM campaign_securities WHERE campaign_id=? AND security_id=?",
                               (c["cid"], sid)).fetchone():
                plan.append(("campaign_securities", "%s/%s" % (c["cid"], sid),
                             (lambda a=c["cid"], b=sid, r=role: cur.execute(
                                 "INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                                 (a, b, r)))))

    # ---- campaign_phases ----
    ph_n = 0
    for c in CAMPAIGNS:
        for l in cand_by_intake[c["intake"]]["lifecycle"]:
            stage = l["stage_proposal"]
            if stage == "PEAK" or l["start"] is None or l["end"] is None:
                continue
            ptype = PHASE_MAP.get(stage)
            if not ptype:
                continue
            ph_n += 1
            pid = "PH-HIEQ-%02d" % ph_n
            if not have("campaign_phases", "phase_id", pid):
                plan.append(("campaign_phases", pid, (lambda a=pid, b=c["cid"], t=ptype, s=l["start"], e=l["end"]:
                    cur.execute("INSERT INTO campaign_phases (phase_id,campaign_id,phase_type,start_date,end_date,"
                                "description) VALUES (?,?,?,?,?,?)",
                                (a, b, t, s, e, "%s（intake lifecycle）｜%s" % (stage, PROV))))))

    # ---- campaign_date_observations ----
    for c in CAMPAIGNS:
        for role, val in (("start", c["start"]), ("peak", c["peak"]), ("end", c["end"])):
            if val is None:
                continue
            oid = "OBS-%s-%s" % (c["cid"], role)
            if not have("campaign_date_observations", "observation_id", oid):
                plan.append(("campaign_date_observations", oid, (lambda a=oid, b=c["cid"], r=role, v=val:
                    cur.execute("INSERT INTO campaign_date_observations (observation_id,campaign_id,date_role,"
                                "candidate_date,verified_date,verification_method,confidence,evidence_id,notes)"
                                " VALUES (?,?,?,?,?,?,?,?,?)",
                                (a, b, r, v, None, "unknown", c["date_confidence"], None,
                                 "candidate 快照自 R01-01 intake date_candidates；未经行情核验。｜" + PROV)))))

    print("=== 计划写入 %d 行 ===" % len(plan))
    from collections import Counter
    for t, n in sorted(Counter(p[0] for p in plan).items()):
        print("  %-28s %d" % (t, n))
    for t, k, _ in plan:
        print("    + %-26s %s" % (t, k))

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

    # 安全校验：既有 13 个 Campaign 未被改动
    conn.commit()
    print("=== 写入完成 ===")
    for t in ("themes", "research_rules", "annual_reviews", "campaigns", "sources", "evidences",
              "events", "securities", "campaign_themes", "campaign_evidences", "campaign_events",
              "campaign_securities", "campaign_phases", "campaign_date_observations"):
        print("  %-28s %d" % (t, cur.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
