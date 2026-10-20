#!/usr/bin/env python3
"""build_theme_map_v0_1.py —— 从**库内既有 Campaign** 生成题材事件地图（v0.25）。

## 为什么需要它

`research/current/*_historical_events_v0_*.json` 此前是逐份手写的：日期、催化、
标的清单都靠人抄，抄错无法自动发现。本脚本把「从 DB 取事实」这一步固定下来：

- `campaign_facts`（start / peak / end / MAIN_RISE）→ 直接读 `campaigns` + `campaign_phases`；
- `catalysts` → 直接读 `campaign_events` JOIN `events`（**原文照录**，不改写）；
- `participants` → 直接读 `campaign_securities` JOIN `securities`，名称 / 代码再与
  canonical export 的 securities 注册表**逐条对齐**（对不上就报错，不猜）；
- `market_performance` → 复用 v0.24 合同 `theme_market_performance_v1`
  （`build_theme_market_performance.compute_raw/finalize`），与 `--check` 同一口径。

## 硬边界

- **只读 DB**：不写 `cycle_research.db` / `market_data.db` / export / schema。
- **不发明文本**：`business_mechanism` / `rationale` 由本文件的人写部分提供，
  且必须是**当前时点可核实的产业事实**；每条都带「业务机制 ≠ 因果」caveat。
- **不按涨幅选标的**：标的清单 = 库内该 Campaign 已登记的 `campaign_securities`，
  不额外挑「涨得多的」。
- **不覆盖历史版本**：目标文件已存在 → 拒绝写入。

用法：`python research/scripts/build_theme_map_v0_1.py [--only THEME_ID]`
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from scripts import db  # noqa: E402
from scripts.build_theme_market_performance import (  # noqa: E402
    BENCHMARK_ID, CONTRACT_VERSION, AUTO_GAP_PREFIX, auto_gap_lines, coverage_text,
    compute_raw, event_study_state, finalize,
)

CURRENT = os.path.join(ROOT, "current")
EXPORT = os.path.join(REPO, "exports", "timeline_export_v1.json")
GENERATED_AT = "2026-10-19"

SOURCE_DISCIPLINE = (
    "Source ≠ Evidence ≠ Rule ≠ Historical Fact ≠ Verification ≠ Prediction。"
    "每只标的的 `category` 只描述「关系性质」：直接机制（MECHANISM_DIRECT）/ 产业链扩散（SPILLOVER）/ "
    "历史市场参与（MARKET_PARTICIPANT）/ 反例（COUNTER_EXAMPLE）/ 证据不足（INSUFFICIENT）"
    "—— **不是**评分、不是排名、不构成买卖信号。"
)
BIZ_NOTE = (
    "★★ 下列标的的「业务机制」是**事后核实**的产业事实；它**不**证明该机制驱动了本事件窗口的行情。"
    "业务机制相关 ≠ 因果。每只标的的 `business_mechanism_caveat` 逐条重申此边界。"
)
BIZ_CAVEAT = "★ 业务机制相关 ≠ 已证明该机制驱动了当次行情。"

# ---------------------------------------------------------------- 人写部分（研究判断）
#
# 每个事件：label / 窗口 / 参与者（security_id, category, rationale, 业务机制）
# ★ 参与者 = 库内该 Campaign 已登记的 security_ids，**不额外挑涨幅高的**。
THEMES = [
    {
        "theme_id": "CONSUMER_SEASON",
        "artifact": "consumer_season_historical_events",
        "label": "消费旺季 / 大众消费",
        "position": (
            "历史题材地图第 7 个题材（v0.25）。题材 = **消费旺季 / 大众消费**（食品饮料 · 免税 · 服务消费 · 家电）。"
            "★★ **事件窗口 = Campaign 的 MAIN_RISE 主升段，不是春节 / 五一 / 十一 / 双十一的月份窗口** —— "
            "本图**不**证明「消费旺季」季节性规律成立；季节性结论见外部日历 v0_2 的 EXT-02 / 07 / 08 / 15 / 18。"
            "数据 = 库内既有 Campaign（`campaigns` / `campaign_phases` / `campaign_events` / `campaign_securities`）"
            "+ `market_data.db` 实测行情（adjusted / 前复权）。★ 不新增研究结论、不生成评分 / 排名 / 概率 / 预测。"
        ),
        "note": (
            "本区展示**消费旺季 / 大众消费**相关历史事件（来源：库内 Campaign + 实测行情）。"
            "★★ **关系性质不是评分**：`category` 只描述直接机制 / 产业链扩散 / 历史市场参与 / 反例 / 证据不足。"
            "★★ **事件窗口是 Campaign 主升段**，与「1–2 月春节」「10–11 月双十一」等外部季节性窗口**不是同一件事** —— "
            "不得把本图当作季节性规律的证据。★ 本图不含跨年份比较 / 经验基准概率（未建立该口径）。"
        ),
        "known_gaps_topic": [
            "★★ 5 个事件的窗口均为 **Campaign MAIN_RISE**（多为 1–2 年），**不是**季节性月份窗口 —— 不能据此判定「春节/国庆/双十一消费行情」成立",
            "★ 2024 家电以旧换新的窗口止于 2024-10-08（Campaign 主升段结束），2024-10 之后的政策延续期未纳入",
            "★ 本图不含跨年份比较 / 经验基准概率（未建立该口径）",
        ],
        "events": [
            {
                "event_id": "CONS-2016-BAIJIU",
                "label": "白酒 / 大众消费升级与白马蓝筹（2016–2018）",
                "campaign_id": "C-2016-CONS-BAIJIU-UPGRADE",
                "window": ["2016-06-01", "2017-12-31"],
                "participants": [
                    ("MOUTAI", "MECHANISM_DIRECT", "库内 representative；高端白酒龙头，消费升级主线的核心定价标的", "高端白酒（酱香型）生产与销售"),
                    ("WULIANGYE", "MECHANISM_DIRECT", "库内 representative；浓香型白酒龙头，渠道与价格带升级", "浓香型白酒生产与销售"),
                    ("LUZHOULAOJIAO", "MECHANISM_DIRECT", "库内 representative；次高端/中端白酒，受益于价格带抬升", "浓香型白酒生产与销售（中高端价格带）"),
                ],
                "gaps": [
                    "★ 窗口 = Campaign MAIN_RISE（2016-06-01 → 2017-12-31），**不是**「春节消费」月份窗口",
                    "★ 2018 年回撤段（2018-09-01 → 2018-12-31）未纳入本窗口",
                    "★★ **本事件行情不可用**：上游前复权（qfq）按「除权价差」计算，三只白酒在 2015–2016 年**出现非正价格**（分红累计超过当时股价）→ 按合同 `invalid_price_series` 如实留空，**不用负价算收益率**。要覆盖该段须改用后复权或原始价（本轮未引入，属数据源方法学限制）",
                ],
            },
            {
                "event_id": "CONS-2019-BAIJIU-CORE",
                "label": "白酒 / 食品饮料核心资产主升（2019–2021）",
                "campaign_id": "C-2019-CONS-BAIJIU-CORE",
                "window": ["2019-03-01", "2020-12-31"],
                "participants": [
                    ("MOUTAI", "MECHANISM_DIRECT", "库内 representative；核心资产定价锚", "高端白酒（酱香型）生产与销售"),
                    ("WULIANGYE", "MECHANISM_DIRECT", "库内 representative；浓香龙头，渠道改革", "浓香型白酒生产与销售"),
                    ("FENJIU", "MECHANISM_DIRECT", "库内 representative；清香型白酒，全国化扩张", "清香型白酒生产与销售"),
                    ("HAITIAN", "SPILLOVER", "库内 representative；调味品龙头，与食品饮料核心资产同属「确定性溢价」交易", "酱油 / 调味品生产与销售"),
                    ("YILI", "SPILLOVER", "库内 representative；乳制品龙头，同属食品饮料核心资产", "液态奶 / 乳制品生产与销售"),
                ],
                "gaps": [
                    "★ 窗口 = Campaign MAIN_RISE（2019-03-01 → 2020-12-31）；2021-02 起的回撤段未纳入",
                    "★ 「核心资产」是**市场交易结构**描述，不是单一产业机制；跨行业（白酒 / 调味品 / 乳制品）并列时不得当作同一机制",
                ],
            },
            {
                "event_id": "CONS-2020-DUTYFREE",
                "label": "离岛免税额度提升（2020）",
                "campaign_id": "C-2020-CONS-DUTYFREE",
                "window": ["2020-06-01", "2021-02-18"],
                "participants": [
                    ("CTGDF", "MECHANISM_DIRECT", "库内 representative；离岛免税牌照与门店运营主体", "免税品零售（离岛免税 / 机场免税）"),
                ],
                "gaps": [
                    "★ 单一标的（库内该 Campaign 只登记 1 只），无同业对照 —— 无法区分「政策驱动」与「个股自身因素」",
                    "★ 窗口 = Campaign MAIN_RISE（2020-06-01 → 2021-02-18）；2021-07 起的回撤段未纳入",
                ],
            },
            {
                "event_id": "CONS-2022-SERVICE-REBOUND",
                "label": "疫后服务消费修复脉冲（2022-12 – 2023）",
                "campaign_id": "C-2022-CONS-SERVICE-REBOUND",
                "window": ["2022-12-07", "2023-01-31"],
                "participants": [
                    ("CTGDF", "MECHANISM_DIRECT", "库内 representative；免税零售，出行链修复的直接受益方", "免税品零售（离岛免税 / 机场免税）"),
                    ("BTG", "MECHANISM_DIRECT", "库内 representative；酒店运营，出行链", "酒店运营与管理"),
                    ("JINJIANG", "MECHANISM_DIRECT", "库内 representative；连锁酒店，出行链", "连锁酒店运营"),
                    ("SONGCHENG", "MECHANISM_DIRECT", "库内 representative；文旅演艺，线下客流敏感", "主题公园 / 文旅演艺"),
                ],
                "gaps": [
                    "★ 窗口仅 2 个月（2022-12-07 → 2023-01-31），样本期短；「弱复苏证伪」发生在 2023-05 之后，未纳入",
                    "★ 4 只标的同属出行链，**不是**独立样本 —— 不得当作「4 次独立验证」",
                ],
            },
            {
                "event_id": "CONS-2024-TRADE-IN",
                "label": "消费品以旧换新（2024–2025）",
                "campaign_id": "C-2024-CONS-TRADE-IN",
                "window": ["2024-08-24", "2024-10-08"],
                "participants": [
                    ("GREE", "MECHANISM_DIRECT", "库内 representative；空调 / 白电，以旧换新补贴直接品类", "空调 / 家用电器制造与销售"),
                    ("HAIER", "MECHANISM_DIRECT", "库内 representative；冰洗 / 白电，补贴直接品类", "冰洗 / 家用电器制造与销售"),
                    ("MIDEA", "MECHANISM_DIRECT", "库内 representative；全品类家电", "家用电器制造与销售"),
                    ("ROBAM", "MECHANISM_DIRECT", "库内 representative；厨电，补贴覆盖品类", "厨房电器制造与销售"),
                ],
                "gaps": [
                    "★ 窗口 = Campaign MAIN_RISE（2024-08-24 → 2024-10-08），**仅 45 天**；政策延续期（2025）未纳入",
                    "★★ 该窗口与 2024-09-24 起的全市场普涨重叠 —— **Beta Contamination 无法排除**，不得把区间涨幅当作政策效果",
                ],
            },
        ],
    },
    {
        "theme_id": "RESOURCE_METAL",
        "artifact": "resource_metal_historical_events",
        "label": "资源品 / 黄金 · 稀土",
        "position": (
            "历史题材地图第 8 个题材（v0.25）。题材 = **资源品（黄金 / 稀土）**。"
            "★ 两个事件的机制**不同**（贵金属避险与官方购金 vs 战略小金属总量控制 + 新能源需求），"
            "并列只为「同属资源品」，**不得**当作同一机制。★ 事件窗口 = Campaign MAIN_RISE，"
            "**不是**外部日历 EXT-20 声称的「10 月」窗口 —— 本图**不**证明该季节性说法。"
            "数据 = 库内既有 Campaign + `market_data.db` 实测行情（adjusted）。"
        ),
        "note": (
            "本区展示**资源品（黄金 / 稀土）**相关历史事件（来源：库内 Campaign + 实测行情）。"
            "★★ 黄金与稀土**机制不同**，并列 ≠ 同轴。★★ 窗口 = Campaign MAIN_RISE，"
            "与外部「10 月资源品」季节性说法**不是同一件事**。"
        ),
        "known_gaps_topic": [
            "★★ 黄金（官方部门购金 / 实际利率）与稀土（总量控制指标 / 新能源需求）**机制不同**，不得合并解释",
            "★ 外部日历 EXT-20 声称「10 月」，而库内两个 Campaign 分别起始于 5 月与 2 月 —— **窗口不吻合**，不支持该季节性说法",
            "★ 本图不含跨年份比较 / 经验基准概率（未建立该口径）",
        ],
        "events": [
            {
                "event_id": "RES-2020-RAREEARTH",
                "label": "稀土景气上行（总量控制 + 新能源需求）",
                "campaign_id": "C-2020-RES-RAREEARTH",
                "window": ["2020-05-01", "2021-10-01"],
                "participants": [
                    ("NPRARE", "MECHANISM_DIRECT", "库内 representative；轻稀土龙头，配额与挂牌价主体", "稀土（轻稀土）采选与冶炼分离"),
                    ("CNRAREEARTH", "MECHANISM_DIRECT", "库内 representative；中重稀土平台", "稀土（中重稀土）冶炼分离"),
                    ("GUANGSHENG", "MECHANISM_DIRECT", "库内 representative；南方稀土冶炼分离", "稀土冶炼分离"),
                    ("SHENGHE", "MECHANISM_DIRECT", "库内 representative；稀土冶炼分离与贸易", "稀土冶炼分离与金属加工"),
                ],
                "gaps": [
                    "★ 窗口 = Campaign MAIN_RISE（2020-05-01 → 2021-10-01），**不是**「10 月」季节性窗口",
                    "★ 4 只标的同属稀土产业链，**不是**独立样本",
                ],
            },
            {
                "event_id": "RES-2024-GOLD",
                "label": "黄金：官方部门结构性购金驱动（2024–2025）",
                "campaign_id": "C-2024-RES-GOLD-CB",
                "window": ["2024-02-01", "2025-12-26"],
                "participants": [
                    ("ZIJIN", "MECHANISM_DIRECT", "库内 representative；金 / 铜矿龙头，产量与金价双敏感", "黄金 / 铜矿采选"),
                    ("SDGOLD", "MECHANISM_DIRECT", "库内 representative；黄金采选", "黄金采选与冶炼"),
                    ("CFGOLD", "MECHANISM_DIRECT", "库内 representative；黄金采选", "黄金采选"),
                    ("ZJGOLD", "MECHANISM_DIRECT", "库内 representative；黄金采选（央企）", "黄金采选与冶炼"),
                ],
                "gaps": [
                    "★ 窗口 = Campaign MAIN_RISE（2024-02-01 → 2025-12-26），跨越约 23 个月 —— 区间收益包含多轮波动，不能当作单次事件",
                    "★ 金价驱动的**外生性**（美元实际利率 / 央行购金）无法用 A 股个股数据检验",
                ],
            },
        ],
    },
]


# ---------------------------------------------------------------- 生成

def load_export_registry() -> dict:
    with open(EXPORT, encoding="utf-8") as fh:
        doc = json.load(fh)
    return {s["security_id"]: s for s in doc["securities"]}


def campaign_facts(conn, campaign_id: str) -> dict:
    c = conn.execute(
        "SELECT campaign_id, campaign_year, start_date, end_date, peak_date, description, "
        "start_date_basis, date_confidence FROM campaigns WHERE campaign_id=?",
        (campaign_id,)).fetchone()
    if c is None:
        raise SystemExit("FAIL: 库内无 Campaign %s" % campaign_id)
    ph = conn.execute(
        "SELECT start_date, end_date FROM campaign_phases WHERE campaign_id=? AND phase_type='main_rise' "
        "ORDER BY start_date LIMIT 1", (campaign_id,)).fetchone()
    return {
        "object_id": c["campaign_id"],
        "object_kind": "campaign",
        "status": "CAMPAIGN",
        "main_rise": ({"start": ph["start_date"], "end": ph["end_date"], "precision": "PHASE_WINDOW"}
                      if ph else None),
        "start": c["start_date"],
        "peak_date": c["peak_date"],
        "end": c["end_date"],
        "note": "库内正式 Campaign（非 Research Candidate）。%s" % (c["description"] or ""),
    }


def catalysts_of(conn, campaign_id: str) -> list:
    rows = conn.execute(
        "SELECT e.date, e.name, e.event_type, e.description, s.title AS src_title, s.url AS src_url "
        "FROM campaign_events ce JOIN events e ON e.event_id=ce.event_id "
        "LEFT JOIN sources s ON s.source_id=e.source_id "
        "WHERE ce.campaign_id=? ORDER BY e.date", (campaign_id,)).fetchall()
    out = []
    for r in rows:
        text = r["name"] if not r["description"] else "%s：%s" % (r["name"], r["description"])
        src = "库内 events（%s）" % (r["event_type"] or "other")
        if r["src_title"]:
            src += " · 来源：%s" % r["src_title"]
            if r["src_url"]:
                src += "（%s）" % r["src_url"]
        out.append({"date": r["date"], "text": text, "source": src})
    return out


def participants_of(conn, campaign_id: str, spec, registry: dict) -> list:
    rows = conn.execute(
        "SELECT cs.security_id, cs.role, s.name, s.ticker FROM campaign_securities cs "
        "JOIN securities s ON s.security_id=cs.security_id WHERE cs.campaign_id=? "
        "ORDER BY cs.role, cs.security_id", (campaign_id,)).fetchall()
    by_id = {r["security_id"]: r for r in rows}
    out = []
    for sid, category, rationale, mechanism in spec:
        r = by_id.get(sid)
        reg = registry.get(sid)
        if r is None:
            raise SystemExit("FAIL: %s 未在 Campaign %s 的登记标的中" % (sid, campaign_id))
        if reg is None:
            raise SystemExit("FAIL: %s 不在 canonical export 的 securities 注册表" % sid)
        out.append({
            "security_id": sid,
            "ticker": reg["ticker"],
            "name": reg["name"],
            "exchange": "SH" if str(reg["ticker"]).startswith("6") else "SZ",
            "category": category,
            "evidence_level": "BUSINESS_VERIFIED",
            "rationale": rationale,
            "source": "canonical export securities 注册表 + 库内 campaign_securities（role=%s）" % r["role"],
            "registry_role": r["role"],
            "business_mechanism": mechanism,
            "business_mechanism_caveat": BIZ_CAVEAT,
        })
    return out


def build_event(conn, theme, ev, registry) -> dict:
    cid = ev["campaign_id"]
    facts = campaign_facts(conn, cid)
    window = ev["window"]
    bench_raw = compute_raw(conn, BENCHMARK_ID, window[0], window[1])
    by = {}
    for sid, _cat, _r, _m in ev["participants"]:
        by[sid] = finalize(compute_raw(conn, sid, window[0], window[1]), bench_raw)
    event = {
        "event_id": ev["event_id"],
        "event_class": "THEME_DIRECT",
        "label": ev["label"],
        "year": int(window[0][:4]),
        "window_text": "%s → %s（Campaign MAIN_RISE，PHASE_WINDOW）" % (window[0], window[1]),
        "external_window_ref": None,
        "evidence_basis": "库内 Campaign %s（%s）+ 实测行情；★ 事件窗口 = Campaign 主升段，**不是**季节性月份窗口。"
                          % (cid, (conn.execute("SELECT description FROM campaigns WHERE campaign_id=?", (cid,))
                                   .fetchone()["description"] or "")),
        "study_state": None,
        "source_discipline_note": SOURCE_DISCIPLINE,
        "campaign_facts": facts,
        "catalysts": catalysts_of(conn, cid),
        "participants": participants_of(conn, cid, ev["participants"], registry),
        "observed_performance": {
            "note": "直引库内 Campaign 记录；未核实到可引用的「同期报道点名当日涨幅」→ 留空，不补造数字。",
            "by_security": None,
        },
        "known_gaps": list(ev["gaps"]),
        "market_performance": {
            "window": window,
            "is_campaign_ruling": False,
            "note": "★ **事件窗口内**的实测行情（事后描述，非 Campaign 裁定）。窗口 = Campaign MAIN_RISE，"
                    "**不是**季节性月份窗口。★ 口径见文档 `market_performance_contract`"
                    "（theme_market_performance_v1）。★★ 不得把「区间上涨」解释为题材因果。",
            "benchmark": {BENCHMARK_ID: finalize(bench_raw)},
            "by_security": by,
            "contract_version": CONTRACT_VERSION,
        },
    }
    event["study_state"] = event_study_state(event, finalize(bench_raw))
    # ★ AUTO 缺口行（与 --check 同一函数生成，避免手写漂移）
    auto = auto_gap_lines(event, {}, conn, window)
    event["known_gaps"] = auto + event["known_gaps"]
    # 参与者行情文案（与 --check 同一函数）
    for p in event["participants"]:
        p["market_data"] = coverage_text(conn, p["security_id"], window[0], window[1])
    return event


def build_doc(conn, theme, registry) -> dict:
    events = [build_event(conn, theme, ev, registry) for ev in theme["events"]]
    return {
        "artifact": theme["artifact"],
        "artifact_version": "v0.1",
        "theme": {"theme_id": theme["theme_id"], "label": theme["label"]},
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_theme_map_v0_1.py（v0.25）",
        "supersedes": None,
        "position": theme["position"],
        "event_classes": [{
            "code": "THEME_DIRECT",
            "label": theme["label"],
            "meaning": "本题材直接机制或产业链相邻的历史事件（窗口 = Campaign MAIN_RISE）。",
        }],
        "source_discipline": SOURCE_DISCIPLINE,
        "business_mechanism_note": BIZ_NOTE,
        "known_gaps_topic": theme["known_gaps_topic"],
        "events": events,
        "market_performance_contract": {
            "version": CONTRACT_VERSION,
            "price_series": "market_daily.price_type='adjusted' → adj_close（前复权收盘）",
            "window": "market_performance.window [start, end]，双端包含",
            "trading_days": "窗口内该序列实际行数（不是日历天数、不是基准交易日数）",
            "high": "窗口内 adj_close 最大值（首次出现）；不是 high 列、不是 Campaign peak_date",
            "period_return_pct": "(last.close / first.close - 1) × 100",
            "to_high_pct": "(high.close / first.close - 1) × 100",
            "max_drawdown_from_high_pct": "★ 自至高点「之后」的最大回撤 = min over t>=high.date of (close_t/high.close - 1) × 100；不是全窗口最大回撤",
            "benchmark": "SH000300，同窗口、同价格口径；excess = 个股 − 基准（区间与至高点两列口径不同，不得混用）",
            "rounding": "百分比 1 位小数（Python round）；超额由已舍入的两个百分比相减后再舍入",
            "missing": "窗口内 < 2 行 → error=insufficient_data_in_window + reason（no_series / no_rows_in_window / single_row），不补 0",
            "source": "research/database/market_data.db（由被跟踪的便携快照恢复）",
            "generated_by": "research/scripts/build_theme_map_v0_1.py",
        },
    }


def main(argv):
    ap = argparse.ArgumentParser(description="从库内 Campaign 生成题材事件地图")
    ap.add_argument("--only", help="只生成指定 theme_id")
    ap.add_argument("--version", type=int, default=1,
                    help="产物版本号（默认 1；旧版本已存在时升版，**不覆盖**）")
    a = ap.parse_args(argv)

    registry = load_export_registry()
    conn = db.connect()
    db.require_market(conn)
    try:
        for theme in THEMES:
            if a.only and theme["theme_id"] != a.only:
                continue
            out = os.path.join(CURRENT, "%s_v0_%d.json" % (theme["artifact"], a.version))
            if os.path.exists(out):
                print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
                return 1
            doc = build_doc(conn, theme, registry)
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
            print("已生成 %-52s %d 事件 / %d 参与记录"
                  % (os.path.relpath(out, REPO), len(doc["events"]),
                     sum(len(e["participants"]) for e in doc["events"])))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
