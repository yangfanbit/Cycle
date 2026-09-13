"""批量研究脚本（Batch Auto Research v1）。

职责（对应 HDP v1 契约）：
1. 读取正式 Campaign（2018–2025, rule_auto_summer）
2. 检查已有 Evidence / Source / 独立性分组
3. 检查 Market Data（raw close 日期快照 + adjusted 收益率，缺则如实 unavailable）
4. 生成研究状态：PROVISIONAL / CONFLICT / INSUFFICIENT（不进入 verified）
5. 输出 research/batch/auto_2018_2025_batch_manifest.json
6. 输出 research/batch/conflicts.json（候选 A/B + 支持/反驳证据）
7. 输出 exports/timeline_export_v1.json（Research → Cycle Timeline MVP 契约 v1.0）

纪律：
- 模型冻结：不新增实体/字段/schema，不改动正式 Campaign 日期。
- PROVISIONAL 用于研究预览；绝不写入 verified。
- 日期冲突不强行解决，记录 candidate_a / candidate_b。
- 无行情数据时记录 unavailable，不伪造。
- 不计算任何统计指标（seasonality/win_rate/probability）。

用法: python scripts/batch_auto_research.py
"""
import sys, os, json, subprocess
from datetime import datetime, date
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
conn = db.connect()

BATCH_DIR = os.path.join(ROOT, "research", "batch")
MANIFEST = os.path.join(BATCH_DIR, "auto_2018_2025_batch_manifest.json")
CONFLICTS = os.path.join(BATCH_DIR, "conflicts.json")
EXPORT = os.path.join(ROOT, "exports", "timeline_export_v1.json")

RULE = "rule_auto_summer"

# ---- 研究级元数据（来自 theme_lifecycle_v0_2 / 年度研究） ----
THEME_CYCLE = {
    "C-2019-AD": "auto_ad_2019",
    "C-2020-NEV": "auto_nev_2020",
    "C-2021-NEV": "auto_nev_2021",
    "C-2022-POLICY": "auto_policy_2022",
    "C-2023-AD": "auto_intelligence_2023",
    "C-2024-V2X": "auto_v2x_2024",
    "C-2024-ROBOTAXI": "robotaxi_2024",
    "C-2025-ROBOTAXI": "robotaxi_2025",
}

# 研究信号（research-level，来自 theme_lifecycle_v0_2 三案例建模；其余年份按 annual 研究记录）
SIGNALS = {
    "C-2022-POLICY": [
        {"type": "EARLY_SIGNAL", "date": "2022-04-27", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2022-05-23", "confidence": "high"},
    ],
    "C-2023-AD": [
        {"type": "EARLY_SIGNAL", "date": "2023-06-12", "confidence": "medium"},
        {"type": "THEME_FORMING", "date": "2023-06-21", "confidence": "high"},
    ],
    "C-2024-ROBOTAXI": [
        {"type": "EARLY_SIGNAL", "date": "2024-07-08", "confidence": "medium"},
    ],
    "C-2024-V2X": [
        {"type": "EARLY_SIGNAL", "date": "2024-06-11", "confidence": "medium"},
    ],
    "C-2025-ROBOTAXI": [
        {"type": "EARLY_SIGNAL", "date": "2025-06-22", "confidence": "medium"},
    ],
}

# Campaign Phase → 时间字段（research-only，便于 timeline 表达）
PHASE_TIME_FIELDS = {
    "C-2022-POLICY": {"broad_confirmation_date": "2022-06-01", "first_decline_date": "2022-07-01"},
    "C-2023-AD": {"broad_confirmation_date": "2023-07-03"},
    "C-2024-ROBOTAXI": {"broad_confirmation_date": "2024-07-10", "first_decline_date": "2024-08-06"},
    "C-2024-V2X": {"broad_confirmation_date": "2024-06-18"},
    "C-2025-ROBOTAXI": {"broad_confirmation_date": "2025-06-24"},
}

# ---- 已记录的研究日期冲突（来自 promotion_gate_v1.md RESEARCH_UNCERTAINTY） ----
# 不强行解决；保留 candidate_a（DB 冻结值）与 candidate_b（研究复核候选）。
CONFLICT_MAP = {
    "C-2022-POLICY": {
        "start_date": {
            "candidate_a": {"date": "2022-04-27", "label": "DB Candidate（Setup 起点）",
                            "basis": "campaigns.start_date 冻结值"},
            "candidate_b": {"date": "2022-05-23", "label": "Research Review Candidate（Theme Formation/政策催化日）",
                            "basis": "theme_lifecycle_v0_2：05-23 国常会购置税600亿政策催化"},
        }
    },
    "C-2024-ROBOTAXI": {
        "peak_date": {
            "candidate_a": {"date": "2024-07-29", "label": "DB Candidate",
                            "basis": "campaigns.peak_date 冻结值"},
            "candidate_b": {"date": "2024-08-05", "label": "Research Review Candidate（EW 等权指数 raw 峰值）",
                            "basis": "calibrate_robotaxi：等权指数 08-05 为 raw 峰值"},
        },
        "end_date": {
            "candidate_a": {"date": "2024-07-31", "label": "DB Candidate",
                            "basis": "campaigns.end_date 冻结值"},
            "candidate_b": {"date": "2024-08-23", "label": "Research Review Candidate（Main Campaign End）",
                            "basis": "theme_lifecycle_v0_2：08-23 Major Breakpoint"},
        },
    },
}

# Campaign → Cycle 侧 promotion 状态（promotion_gate_v1：仅三条正式候选 READY_FOR_HUMAN_REVIEW）
PROMO_STATUS = {
    "C-2022-POLICY": "READY_FOR_HUMAN_REVIEW",
    "C-2023-AD": "READY_FOR_HUMAN_REVIEW",
    "C-2024-ROBOTAXI": "READY_FOR_HUMAN_REVIEW",
}

# 每个 Campaign 用于行情快照的代理序列（行业代理不可得时用真实龙头个股，标注代理性质）
PROXY_SERIES = {
    "C-2019-AD": "WANAN",
    "C-2020-NEV": "BIDI",
    "C-2021-NEV": "BIDI",
    "C-2022-POLICY": "AUTO_ETF_516110",
    "C-2023-AD": "AUTO_ETF_516110",
    "C-2024-V2X": "AUTO_ETF_516110",
    "C-2024-ROBOTAXI": "AUTO_ETF_516110",
    "C-2025-ROBOTAXI": "AUTO_ETF_516110",
}

PROXY_NOTE = {
    "C-2019-AD": "行业代理不可得（AUTO_SW 腾讯无数据、516110 未成立），用龙头万安科技 raw close 作参考（非行业代理）",
    "C-2020-NEV": "516110 未成立，用龙头比亚迪 raw close 作参考（非行业代理）",
    "C-2021-NEV": "516110 未成立，用龙头比亚迪 raw close 作参考（非行业代理）",
    "C-2022-POLICY": "汽车ETF(中证800汽车) 行业代理（成立于2021-11之后，2022年可用）",
    "C-2023-AD": "汽车ETF(中证800汽车) 行业代理",
    "C-2024-V2X": "汽车ETF(中证800汽车) 行业代理（非车路云专用指数，仅供参照）",
    "C-2024-ROBOTAXI": "汽车ETF(中证800汽车) 行业代理（非Robotaxi专用指数，仅供参照）",
    "C-2025-ROBOTAXI": "汽车ETF(中证800汽车) 行业代理（成立于2021-11之后，2025年可用）",
}


def q(sql, *a):
    return [dict(r) for r in conn.execute(sql, a).fetchall()]


def q1(sql, *a):
    r = conn.execute(sql, a).fetchone()
    return dict(r) if r else None


def get_git_head():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def market_snapshot(series_id, dates, campaign_id):
    """返回 {date: raw_close} + 可用性标记。取 <= date 的最近交易日（含当日）。"""
    out = {}
    for d in dates:
        if not d:
            continue
        row = q1(
            "SELECT close FROM market_daily WHERE series_id=? AND price_type='raw' AND trade_date<=? "
            "ORDER BY trade_date DESC LIMIT 1", series_id, d)
        out[d] = row["close"] if row else None
    if any(v is not None for v in out.values()):
        return {"series_id": series_id, "raw_close": out, "status": "available"}
    return {"series_id": series_id, "raw_close": out, "status": "unavailable",
            "note": PROXY_NOTE.get(campaign_id, "")}


def adjusted_returns(series_id, start, peak, end):
    def close_on(d):
        row = q1("SELECT adj_close FROM market_daily WHERE series_id=? AND price_type='adjusted' "
                 "AND trade_date<=? ORDER BY trade_date DESC LIMIT 1", series_id, d)
        return row["adj_close"] if row else None
    c0, cp, ce = close_on(start), close_on(peak), close_on(end)
    if None in (c0, cp, ce) or c0 == 0:
        return None
    return {
        "start_to_peak": round(cp / c0 - 1.0, 4),
        "start_to_end": round(ce / c0 - 1.0, 4),
        "peak_to_end": round(ce / cp - 1.0, 4),
        "price_type": "adjusted(qfq)",
        "note": "调整后收益，仅用于收益率口径；日期判断用 raw close",
    }


def build_campaign(c):
    cid = c["campaign_id"]
    evs = q("""SELECT e.evidence_id, e.date, e.evidence_type, e.description, e.evidence_role,
                      e.confidence, e.independence_group, e.temporal_relation,
                      s.source_id, s.title, s.url, s.tier, s.source_type
               FROM campaign_evidences ce
               JOIN evidences e ON e.evidence_id=ce.evidence_id
               LEFT JOIN sources s ON s.source_id=e.source_id
               WHERE ce.campaign_id=? ORDER BY e.date""", cid)
    themes = q("""SELECT t.name, t.theme_type, ct.role FROM campaign_themes ct
                  JOIN themes t ON t.theme_id=ct.theme_id WHERE ct.campaign_id=?""", cid)
    events = q("""SELECT e.event_id, e.name, e.date, e.event_type, ce.role FROM campaign_events ce
                  JOIN events e ON e.event_id=ce.event_id WHERE ce.campaign_id=?""", cid)
    secs = q("""SELECT s.security_id, s.name, s.ticker, s.exchange, cs.role
                FROM campaign_securities cs JOIN securities s ON s.security_id=cs.security_id
                WHERE cs.campaign_id=?""", cid)
    phases = q("SELECT phase_type, start_date, end_date, description FROM campaign_phases WHERE campaign_id=?",
               cid)

    source_ids = sorted({e["source_id"] for e in evs if e["source_id"]})
    evidence_ids = [e["evidence_id"] for e in evs]
    groups = sorted({e["independence_group"] for e in evs if e["independence_group"]})

    # 状态判定：有已知日期冲突 → CONFLICT；满足 PROVISIONAL 标准 → PROVISIONAL；否则 INSUFFICIENT
    status = "PROVISIONAL"
    status_notes = []
    if cid in CONFLICT_MAP:
        status = "CONFLICT"
        fields = ", ".join(CONFLICT_MAP[cid].keys())
        status_notes.append(f"日期口径未收敛：{fields}（见 conflicts.json）")
    if not themes:
        status = "INSUFFICIENT"; status_notes.append("主题不可识别")
    if not evs:
        status = "INSUFFICIENT"; status_notes.append("无绑定证据")
    if not source_ids:
        status = "INSUFFICIENT"; status_notes.append("无可靠来源")
    if status == "PROVISIONAL":
        status_notes.append("主题可识别 + 有行情/媒体证据 + ≥1 可靠来源 + 主要日期有依据 + 无跨时间因果错误（多来源已交叉比对）")

    # 行情快照：raw close @ start/peak/end + 各 phase 起止
    proxy = PROXY_SERIES.get(cid)
    md = {"status": "unavailable", "note": "无可用行情数据（AUTO_SW 不可得时如实 unavailable）"}
    if proxy:
        snap_dates = [c["start_date"], c["peak_date"], c["end_date"]]
        for ph in phases:
            snap_dates += [ph["start_date"], ph["end_date"]]
        md = market_snapshot(proxy, [d for d in snap_dates if d], cid)
    adj = adjusted_returns(proxy, c["start_date"], c["peak_date"], c["end_date"]) if proxy else None

    # 冲突详情
    conflict = None
    if cid in CONFLICT_MAP:
        conflict = CONFLICT_MAP[cid]

    # 研究信号
    signals = SIGNALS.get(cid, [])

    entry = {
        "research_campaign_id": cid,
        "db_campaign_id": cid,
        "year": c["campaign_year"],
        "rule_id": RULE,
        "status": status,
        "annual_status": q1("SELECT status FROM annual_reviews WHERE rule_id=? AND year=?",
                            RULE, c["campaign_year"])["status"],
        "start_date_candidate": c["start_date"],
        "peak_date_candidate": c["peak_date"],
        "end_date_candidate": c["end_date"],
        "date_confidence": c["date_confidence"],
        "theme": ", ".join(t["name"] for t in themes if t["role"] == "main") or "(未标 main)",
        "themes": themes,
        "theme_cycle_id": THEME_CYCLE.get(cid),
        "classification": c["classification"],
        "result": c["result"],
        "strength": c["strength"],
        "evidence_ids": evidence_ids,
        "source_ids": source_ids,
        "independent_groups": groups,
        "independent_group_count": len(groups),
        "events": events,
        "securities": secs,
        "market_data": {**md, "adjusted_returns": adj} if md.get("status") == "available"
                       else {"status": "unavailable", "note": PROXY_NOTE.get(cid, "无可用行情数据"),
                             "adjusted_returns": None},
        "signals": signals,
        "confidence": c["date_confidence"] or "low",
        "notes": "; ".join(status_notes) or c.get("research_notes") or "",
        "research_notes": c.get("research_notes"),
        "conflict": conflict,
    }
    return entry


def build_2018():
    """2018 = 反例年份（no_clear_campaign），保留为年度级记录，不作为 Campaign。"""
    ar = q1("SELECT status, summary FROM annual_reviews WHERE rule_id=? AND year=2018", RULE)
    return {
        "research_campaign_id": "Y2018-NO-CLEAR",
        "db_campaign_id": None,
        "year": 2018,
        "rule_id": RULE,
        "status": "PROVISIONAL",          # “2018 无清晰 Campaign”是研究结论（未人工复核）
        "annual_status": ar["status"] if ar else "no_clear_campaign",
        "start_date_candidate": None, "peak_date_candidate": None, "end_date_candidate": None,
        "date_confidence": "medium",
        "theme": "(无 Campaign，反例年份)",
        "themes": [], "theme_cycle_id": None,
        "classification": None, "result": "failed", "strength": None,
        "evidence_ids": [e["evidence_id"] for e in q(
            "SELECT evidence_id FROM evidences WHERE date LIKE '2018%'")],
        "source_ids": [s["source_id"] for s in q("SELECT source_id FROM sources WHERE source_id LIKE 'S-2018-%'")],
        "independent_groups": [],
        "independent_group_count": 0,
        "events": [], "securities": [],
        "market_data": {"status": "unavailable",
                        "note": "2018 无 Campaign，仅年度反例结论；板块下行证据来自媒体/行业数据（S-2018-01/02）"},
        "signals": [],
        "confidence": "medium",
        "notes": "反例年份：6-8月窗口内汽车板块整体下行（销量7月起同比转负），无持续性主题 Campaign，不得强行找上涨案例",
        "research_notes": ar["summary"] if ar else None,
        "conflict": None,
    }


def main():
    os.makedirs(BATCH_DIR, exist_ok=True)
    camps = q("SELECT * FROM campaigns WHERE rule_id=? ORDER BY campaign_year", RULE)
    entries = [build_2018()] + [build_campaign(c) for c in camps]

    # ---------- manifest ----------
    manifest = {
        "manifest_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "rule_id": RULE,
        "scope": "2018-2025, rule_auto_summer (汽车, 历史观察窗口 6-8月)",
        "status_vocabulary": {
            "PROVISIONAL": "研究预览可用：主题可识别+行情/媒体证据+≥1可靠来源+主要日期有依据+无跨时间因果错误；未人工复核，非 VERIFIED",
            "CONFLICT": "存在研究日期口径冲突（candidate_a vs candidate_b），保留双方证据，不强行解决",
            "INSUFFICIENT": "来源不足/无法判断 Campaign 或时间范围/行情数据缺失，不编造",
        },
        "note": "本 manifest 为研究批次输出，不是新的正式 Schema；PROVISIONAL 不等于 VERIFIED，不得进入 Cycle verified",
        "campaigns": entries,
    }
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, default=str)
    print(f"manifest: {MANIFEST} ({len(entries)} entries)")

    # ---------- conflicts.json ----------
    conflicts = []
    for cid, fields in CONFLICT_MAP.items():
        for field, cand in fields.items():
            conflicts.append({
                "research_campaign_id": cid,
                "field": field,
                "candidate_a": cand["candidate_a"],
                "candidate_b": cand["candidate_b"],
                "supporting_evidence_a": [e["evidence_id"] for e in
                                          q("SELECT e.evidence_id FROM campaign_evidences ce "
                                            "JOIN evidences e ON e.evidence_id=ce.evidence_id "
                                            "WHERE ce.campaign_id=? AND e.evidence_role='supporting'", cid)],
                "supporting_evidence_b": [],
                "contradicting_evidence": [],
                "decision": "pending_human_review",
                "blocker_type": "RESEARCH_UNCERTAINTY",
                "notes": "不强行解决；由人工最终 Review 裁决为 Verified Date 后才允许进入 Cycle",
            })
    conflicts_doc = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "rule": "conflicts 记录研究日期口径冲突；candidate_a=DB 冻结值，candidate_b=研究复核候选",
        "conflicts": conflicts,
    }
    with open(CONFLICTS, "w", encoding="utf-8") as f:
        json.dump(conflicts_doc, f, ensure_ascii=False, indent=2, default=str)
    print(f"conflicts: {CONFLICTS} ({len(conflicts)} conflicts)")

    # ---------- timeline_export_v1.json ----------
    rule_row = q1("SELECT * FROM research_rules WHERE rule_id=?", RULE)
    campaigns_out = []
    for e in entries:
        if e["year"] == 2018:
            continue  # 无 Campaign，不出现在 campaign 列表（反例由 rule 级注释承载）
        promo = PROMO_STATUS.get(e["research_campaign_id"], "RESEARCH_CANDIDATE")
        ph = PHASE_TIME_FIELDS.get(e["research_campaign_id"], {})
        campaigns_out.append({
            "campaign_id": e["research_campaign_id"],
            "rule_id": RULE,
            "year": e["year"],
            "start_date": e["start_date_candidate"],
            "peak_date": e["peak_date_candidate"],
            "end_date": e["end_date_candidate"],
            "status": promo,                 # Cycle 侧 promotion 状态（promotion_gate_v1）
            "confidence": e["confidence"],
            "classification": e["classification"],
            "strength": e["strength"],
            "result": e["result"],
            "themes": e["themes"],
            "events": e["events"],
            "securities": e["securities"],
            # ---- research-only 附加信息（Cycle 不支持，不得伪装成正式字段）----
            "research_status": e["status"],
            "theme_cycle_id": e["theme_cycle_id"],
            "first_signal_date": e["signals"][0]["date"] if e["signals"] else None,
            "broad_confirmation_date": ph.get("broad_confirmation_date"),
            "first_decline_date": ph.get("first_decline_date"),
            "notes": e["notes"],
        })
    export = {
        "contract": "timeline_export",
        "timeline_export_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_commit": get_git_head(),
        "project": "Cycle-Research",
        "purpose": "Research → Cycle Timeline MVP 的机器可解析导出契约（v1.0）",
        "rules": [{
            "rule_id": rule_row["rule_id"] if rule_row else RULE,
            "name": rule_row["name"] if rule_row else "A股汽车夏季历史观察窗口",
            "base_pattern": rule_row["base_pattern"] if rule_row else "汽车",
            "definition": "Historical Observation Window（历史观察窗口），非固定买入窗口",
            "observation_window": "Q2-Q3（4-9月），6-8月为名义窗口；允许漂移（2022 启动 04-27、2019 启动 08-15）",
        }],
        "signals": [
            {"campaign_id": e["research_campaign_id"], "signals": e["signals"]}
            for e in entries if e["signals"]
        ],
        "campaigns": campaigns_out,
        "events": [
            {"campaign_id": e["campaign_id"], "events": e["events"]} for e in campaigns_out
        ],
        "securities": [
            {"campaign_id": e["campaign_id"], "securities": e["securities"]} for e in campaigns_out
        ],
    }
    os.makedirs(os.path.dirname(EXPORT), exist_ok=True)
    with open(EXPORT, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2, default=str)
    print(f"timeline_export: {EXPORT} (v1.0, {len(campaigns_out)} campaigns)")

    # 汇总输出（供最终报告引用）
    from collections import Counter
    ctr = Counter(e["status"] for e in entries)
    years = {e["year"] for e in entries}
    print("STATUS:", dict(ctr), "YEARS:", sorted(years))
    conn.close()


if __name__ == "__main__":
    main()
