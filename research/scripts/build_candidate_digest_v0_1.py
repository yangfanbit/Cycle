#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_candidate_digest_v0_1.py —— 统一「当前候选前瞻」汇总产物（v0.38）。

把四类来源合并成**一份**候选池，按可解释规则分组排序：
  · current_candidates.json       当前研究对象（6 个，研究记录 2026-10-23）
  · forward_observation_v0_2.json 专项前瞻候选（生肖 / 流感 / 台海）
  · pattern_discovery_v0_9.json   自动发现的当前/下月窗口（204 条，含双层时点资格）
  · market_snapshots/index.json   本期快照状态（已签发/草稿）

★ 合并只按**明确 ID**；名称相近不合并（宁可分开）。
★ 排序是**研究浏览优先顺序**，不是收益预测：G1 历史重复+OOS+时间优势 → G2 结构参照/催化临近 →
  G3 有当前事实但历史证据不足 → G4 探索/陈旧/无法检验/时点不可发现。
★ ★★ G1/G2 额外要求 `pit_eligible_years >= 1`：只在回看时成立（当年无法被发现）的窗口一律降到 G4，
  否则等于用未来信息给它排序。
★ 所有日期原样保留（price_as_of / research_as_of / snapshot_status），不把旧数据改成最新。
"""
from __future__ import annotations

import argparse, json, os, re, sqlite3, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"candidate_digest_v0_(\d+)\.json$")
SEC_DB = os.path.join(REPO, "research", "database", "cycle_research.db")

# ★★ v0.65：三类对象**不再共用一组六条精选**。
#   `sections` 明确给出三个互不替代的入口：当前研究主题（全部）/ 季节窗口预览 / 专项假设。
#   卡片同时带 `discovery`（来源类别 · 方法版本 · as_of · 覆盖 · 跟踪入口）与
#   `stock_gap_reason`（缺股**原因**，不是一律「没有成分」）。
SOURCE_CLASS = {
    "SEASONAL_WINDOW": "MONTHLY_RETURN_PATTERN",      # 月度收益模式（自动发现）
    "SPECIAL_HYPOTHESIS": "SPECIAL_HYPOTHESIS",        # 人工预设假设的历史检验
    "CURRENT_OBJECT": "CURRENT_THEME_EVIDENCE",        # 当前主题证据研究
}
# ★ 缺股原因三分 —— 前端必须分开显示，不能统一写成「没有可核实的成分」
STOCK_GAP_TEXT = {
    "NO_HISTORICAL_CONSTITUENTS":
        "行业板块没有已接入的历史成分数据 → 不绑个股（不用当前成分冒充当年成分）",
    "NO_SECURITY_MAPPING":
        "当前研究主题尚未建立 A 股标的映射 → 不列个股",
    "HYPOTHESIS_NO_SECURITY_LINK":
        "专项假设未接入个股列表 → 不列个股",
}
# ★★ 当前研究主题的**可核验**标的映射（v0.65 新增）。
#   每条 = (security_id, 名称, 出处字段)。构建时逐条校验：
#     ① security_id 必须存在于 `securities` 注册表，且名称与注册表**完全一致**；
#     ② 名称必须在指定出处文本里**逐字出现**（出处 = `core_narrative` 或某个 `evidence_id`）。
#   校验不过 → 丢弃并写入 `dropped[]`（含原因），**绝不**静默输出。
#   ★ 只收「研究正文点名的公司」，**不是**历史代表股、不是推荐、不参与排序。
#   ★ 不用子串匹配自动抽取：实测会把「智元机器人」误判为新松机器人（300024）、
#     把「东方财富网」当成分股 —— 名字比对没有证明力。
RELATED_SECURITIES_BY_CANDIDATE = {
    "CC-2026-OPTICAL-LINK": [
        ("EOPTOLINK", "新易盛", "core_narrative"),
        ("INNOLIGHT", "中际旭创", "core_narrative"),
        ("TFC", "天孚通信", "core_narrative"),
        ("ACCELINK", "光迅科技", "core_narrative"),
    ],
    "CC-2026-AUTO-SMARTDRIVE": [
        ("BIDI", "比亚迪", "E-AUTO-03"),
    ],
}


def load_securities():
    """只读打开 canonical 研究库取证券注册表；库不存在时返回 {}（不崩、不静默通过）。"""
    if not os.path.exists(SEC_DB):
        return {}
    con = sqlite3.connect("file:%s?mode=ro" % SEC_DB, uri=True)
    try:
        return {r[0]: {"name": r[1], "ticker": r[2]}
                for r in con.execute("SELECT security_id, name, ticker FROM securities")}
    finally:
        con.close()


def _field_text(x, field):
    if field == "core_narrative":
        return x.get("core_narrative") or ""
    for e in (x.get("evidence") or []):
        if e.get("evidence_id") == field:
            return e.get("claim") or ""
    return ""


def _quote(text, name, pad=14):
    i = text.find(name)
    if i < 0:
        return None
    return text[max(0, i - pad): i + len(name) + pad]


def related_securities_of(x, secs):
    """当前研究主题 → 可核验的「当前相关标的」；无映射时给出**为什么**与下一步。"""
    items, dropped = [], []
    for sid, name, field in RELATED_SECURITIES_BY_CANDIDATE.get(x.get("candidate_id"), []):
        reg = secs.get(sid)
        text = _field_text(x, field)
        if not reg:
            dropped.append({"security_id": sid, "reason": "securities 注册表中无该 security_id"})
            continue
        if reg["name"] != name:
            dropped.append({"security_id": sid,
                            "reason": "注册表名称与映射不一致（%s ≠ %s）" % (reg["name"], name)})
            continue
        q = _quote(text, name)
        if q is None:
            dropped.append({"security_id": sid, "reason": "出处文本中未逐字出现该名称（%s）" % field})
            continue
        items.append({
            "security_id": sid, "name": name, "ticker": reg["ticker"],
            "basis": ("研究正文枚举点名" if field == "core_narrative" else "证据条目点名"),
            "evidence_id": (None if field == "core_narrative" else field),
            "quote": q,
        })
    out = {
        "status": "MAPPED" if items else "NOT_MAPPED",
        "label": "当前相关标的",
        "nature": "研究正文点名的公司；**不是**历史代表股，不是推荐，也不参与排序",
        "basis_rule": ("仅收录能在 securities 注册表按名称精确对应、且名称在研究正文中逐字出现的公司；"
                       "每条附出处字段与原文片段"),
        "as_of": iso(x.get("snapshot_date")),
        "items": items,
    }
    if not items:
        out["reason"] = ("本主题研究正文未出现可与 securities 注册表精确对应的公司名 "
                         "→ 尚未建立标的映射")
        out["what_is_needed"] = ("需把正文点名的公司解析为证券代码并登记到 securities 注册表，"
                                 "再逐条标注出处；未解析前不列个股")
    if dropped:
        out["dropped"] = dropped
    return out


def _has_stocks(card):
    """★★ 个股有无的口径**按类型分开**：
    - 当前研究主题 → `related_securities.status == MAPPED`（「当前相关标的」，不是历史代表股）
    - 季节窗口 / 专项假设 → `representative_stocks` 非空
    两套语义不得互相顶替，所以不能只看一个字段。"""
    if card.get("kind") == "CURRENT_OBJECT":
        return (card.get("related_securities") or {}).get("status") == "MAPPED"
    return bool(card.get("representative_stocks"))


def discovery_of(kind, src, method_version, as_of, coverage, tracking, horizons=None):
    """所有发现结果的公共元信息（来源类别 / 方法 / 时点 / 覆盖 / 跟踪入口）。"""
    return {
        "source_class": SOURCE_CLASS[kind],
        "source": src,
        "method_version": method_version,
        "as_of": as_of,
        "coverage": coverage,
        "tracking": tracking,
        "settlement_horizons": horizons,
    }



def iso(d):
    """20261023 / 2026-10-23 / 2026-10-23T.. → 2026-10-23"""
    if not d:
        return None
    d = str(d)[:10]
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if "-" not in d else d


def days_old(d, ref):
    from datetime import date
    try:
        a = date.fromisoformat(iso(d)); b = date.fromisoformat(iso(ref))
        return (b - a).days
    except Exception:
        return None


def _non_negative(n):
    """★ 负数天数一律置空：研究记录日**晚于**行情基准时，「早 N 天」的说法不成立。"""
    return None if (isinstance(n, int) and n < 0) else n


def load(name):
    p = os.path.join(CURRENT, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def latest(prefix):
    files = sorted([f for f in os.listdir(CURRENT) if re.match(prefix + r"_v0_(\d+)\.json$", f)],
                   key=lambda f: int(re.search(r"v0_(\d+)", f).group(1)))
    return files[-1] if files else None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    pd_file = latest("pattern_discovery")
    pd = load(pd_file)
    # ★★ v0.60：原硬编码 `forward_observation_v0_2.json` —— 前瞻产物升到 v0_3/v0_4 后，
    #   摘要里的 `price_as_of` / `data_as_of` 会**停在旧版**（实测仍显示 2026-10-20），
    #   与页面其他位置显示的行情日期自相矛盾。改为取版本号最大的。
    fwd_file = latest("forward_observation")
    fwd = load(fwd_file) if fwd_file else None
    cand = load("current_candidates.json")
    snap = load(os.path.join("market_snapshots", "index.json"))

    cards = []

    # ① 自动发现的当前/下月窗口
    for p in pd["current_windows"]:
        oos_ok = p.get("oos_status") == "REPORTED" and (p.get("oos_hit_rate") or 0) >= 0.5
        # ★★ 时点可发现性是**独立门槛**：只在回看时成立（当年无法被发现）的窗口，
        #    不得进 G1/G2 —— 否则等于用未来信息给它排序。
        discoverable = (p.get("pit_eligible_years") or 0) >= 1
        g = ("G1" if (discoverable and p["tier"] == "STRICT" and oos_ok) else
             "G2" if (discoverable and p["tier"] == "STRICT") else "G4")
        cards.append({
            "id": p["pattern_id"], "source": ["pattern_discovery"], "kind": "SEASONAL_WINDOW",
            "title": "%s · %d 月" % (p["board"], p["month"]),
            "subtitle": ("自建概念等权" if p["kind"] == "concept_basket" else "行业板块"),
            "why_now": "进入历史 %d 月窗口（%s）" % (p["month"], "当月" if p["current_status"] == "IN_WINDOW" else "下月"),
            "time_position": p["current_status"], "group": g,
            "history": {"n_years": p["n_years"], "median_excess_pct": p["median_excess_pct"],
                        "hit_rate": p["hit_rate"], "tier": p["tier"],
                        "oos_status": p.get("oos_status"), "oos_tests": p.get("oos_tests"),
                        "oos_hit_rate": p.get("oos_hit_rate"),
                        "oos_median_excess_pct": p.get("oos_median_excess_pct"),
                        "years": p.get("years"),
                        # ★ 时点可发现性 + 证据等级（新方法新增，产品据此降级）
                        "pit_eligible_years": p.get("pit_eligible_years"),
                        "pit_first_year": p.get("pit_first_year"),
                        "pit_basis": p.get("pit_basis"),
                        "discovery_basis": p.get("discovery_basis"),
                        "evidence_grade": p.get("evidence_grade"),
                        # ★ 两层训练的样本外统计分开保留（不把两类混成一个数）
                        "oos_by_train_tier": p.get("oos_by_train_tier"),
                        "oos_scope": p.get("oos_scope")},
            "representative_stocks": p.get("representative_stocks") or [],
            # ★★ v0.65：缺股要说明**原因**（行业板块无历史成分 ≠ 没数据）
            "stock_gap_reason": (None if (p.get("representative_stocks") or []) else
                                 ("NO_HISTORICAL_CONSTITUENTS" if p["kind"] != "concept_basket"
                                  else "NO_SECURITY_MAPPING")),
            "discovery": discovery_of(
                "SEASONAL_WINDOW", ["pattern_discovery"], pd.get("artifact_version"), iso(pd["as_of"]),
                # ★ 不重复 `history` 里的 n_years / tier（213 张卡片逐条重复会让摘要虚胖）
                ("自建概念等权" if p["kind"] == "concept_basket" else "行业板块") + " · 历史重复统计",
                "CANDIDATE_LEDGER", ["5d", "10d", "20d"]),
            "gap": ("；".join(x for x in (
                        ("行业板块无历史成分 → 不绑个股" if p["kind"] != "concept_basket" else p.get("rep_stock_gap")),
                        "时点资格为「按当前序列、只用过去数据」的统计资格，不代表当时分类/成分可得") if x)),
            "watch_next": "窗口内该板块相对沪深300的 20 日超额与广度",
            "invalidate_if": "窗口结束前中位超额 ≤ 0 且广度 < 0.5",
            "trigger_type": "CALENDAR_WINDOW",
            "dates": {"price_as_of": iso(pd["as_of"]), "data_as_of": iso(pd["as_of"]),
                      "research_as_of": None,   # ★ 模式统计不是「研究对象记录日」
                      "artifact_generated_at": iso(pd["generated_at"])},
            "evidence_ref": {"artifact": pd_file, "pattern_id": p["pattern_id"]},
        })

    # ② 专项前瞻候选（人工预设假设）
    for c in (fwd or {}).get("candidates", []):
        st = c.get("evidence_status")
        g = "G2" if st == "PRE_OBSERVATION" else "G4"
        cards.append({
            "id": c["candidate_id"], "source": ["forward_observation"], "kind": "SPECIAL_HYPOTHESIS",
            "title": c["title"], "subtitle": "专项假设（非全部规律）",
            "why_now": c.get("why_now"), "time_position": st, "group": g,
            "history": c.get("historical_stats") or {},
            "current_performance": c.get("current_performance"),
            # ★ v0.65：专项假设本轮未接入个股列表 —— 与「行业板块无历史成分」是不同原因
            "stock_gap_reason": "HYPOTHESIS_NO_SECURITY_LINK",
            "discovery": discovery_of(
                "SPECIAL_HYPOTHESIS", ["forward_observation"], (fwd or {}).get("method_version"),
                iso((fwd or {}).get("as_of")),
                "预设假设 · 观察窗口 %s → %s" % ((c.get("window") or {}).get("start"),
                                                (c.get("window") or {}).get("end")),
                "FORWARD_OBSERVATION", None),
            "gap": c.get("not_a_candidate_reason"),
            "watch_next": c.get("what_to_watch"), "invalidate_if": c.get("invalidate_if"),
            "trigger_type": "ASSUMPTION",
            "dates": {"price_as_of": iso((c.get("current_performance") or {}).get("price_as_of")),
                      "data_as_of": iso((fwd or {}).get("as_of")),
                      "research_as_of": None,
                      "artifact_generated_at": iso((fwd or {}).get("as_of"))},
            "evidence_ref": {"artifact": fwd_file, "candidate_id": c["candidate_id"]},
        })

    # ③ 当前研究对象
    secs = load_securities()
    for x in (cand or {}).get("candidates", []):
        refs = x.get("reference_cases") or []
        drivers = x.get("drivers") or []
        scheduled = [d for d in drivers if d.get("category") in ("POLICY", "INDUSTRY", "STANDARD", "EVENT")]
        g = "G2" if refs else "G3"
        rel = related_securities_of(x, secs)
        cards.append({
            "id": x["candidate_id"], "source": ["current_candidates"], "kind": "CURRENT_OBJECT",
            "title": x.get("display_name"), "subtitle": x.get("theme_type") or "",
            "why_now": x.get("core_narrative") or "",   # ★ 保留全文（首页用 CSS line-clamp 控制行数）
            "time_position": x.get("attention_state") or "UNKNOWN", "group": g,
            "history": {"reference_cases": refs},
            # ★★ v0.65：当前研究主题的「当前相关标的」（可核验、带出处）+ 缺股原因
            "related_securities": rel,
            "stock_gap_reason": (None if rel["status"] == "MAPPED" else "NO_SECURITY_MAPPING"),
            "discovery": discovery_of(
                "CURRENT_OBJECT", ["current_candidates"], (cand or {}).get("current_candidates_version"),
                iso(x.get("snapshot_date") or (cand or {}).get("generated_at")),
                "当前主题证据研究（研究记录日 %s）· 不含历史重复统计"
                % iso(x.get("snapshot_date") or (cand or {}).get("generated_at")),
                "NONE", None),
            "trigger": {"type": "CURRENT_FACT+EXPECTATION",
                        "items": [{"category": d.get("category"), "note": (d.get("note") or "")[:160]}
                                  for d in scheduled[:3]]},
            "watch_next": (x.get("research_questions") or [None])[0],
            "invalidate_if": None,
            "trigger_type": "CURRENT_FACT",
            "watchboard": {
                "attention_state": x.get("attention_state"),
                "candidate_status": x.get("candidate_status"),
                "theme_type": x.get("theme_type"),
                "phase_window": x.get("phase_window"),
                "phase_evidence": x.get("phase_evidence"),
                "narrative_types": x.get("narrative_types"),
                "conflict_notes": x.get("conflict_notes"),
                "uncertainty_notes": x.get("uncertainty_notes"),
                "research_questions": x.get("research_questions"),
                "source_summary": x.get("source_summary"),
                "reference_cases": x.get("reference_cases"),
            },
            "dates": {"research_as_of": iso(x.get("snapshot_date") or (cand or {}).get("generated_at")),
                      "price_as_of": None},
            "evidence_ref": {"artifact": "current_candidates.json", "candidate_id": x["candidate_id"]},
        })

    # ④ 快照状态（只作数据日期披露，不生成候选）
    snaps = (snap or {}).get("snapshots") or []
    canonical = [s for s in snaps if s.get("status") == "CANONICAL"]

    for c in cards:
        d = c["dates"].get("research_as_of")
        n = days_old(d, pd["as_of"]) if d else None
        if n is not None and n < 0:
            n = None   # ★ 研究记录日晚于行情基准 → 不作为「陈旧天数」，也不显示负数
        c["dates"]["research_days_old"] = n
        c["dates"]["research_stale"] = bool(n is not None and n > 7)
    order = {"G1": 0, "G2": 1, "G3": 2, "G4": 3}

    def rank_key(c):
        """★ 精选排序：样本外证据 > 检验样本数 > 历史复现年数 > 当前时间位置 > 中位超额（不是只看收益）。"""
        h = c["history"]
        oos_ok = 1 if h.get("oos_status") == "REPORTED" else 0
        oos_tests = h.get("oos_tests") or 0
        oos_hit = h.get("oos_hit_rate") or 0
        n_years = h.get("n_years") or 0
        pos = {"IN_WINDOW": 3, "PRE_WINDOW": 2}.get(c["time_position"], 1)
        # ★ 顺序与 featured_note 逐字一致：样本外证据（可报告 → 检验年数 → 命中率）→ 历史年数 → 时间位置 → 中位超额 → 分组
        return (-oos_ok, -oos_tests, -oos_hit, -n_years, -pos,
                -(h.get("median_excess_pct") or -99), order[c["group"]])

    cards.sort(key=rank_key)

    # ★★ v0.65：三类对象**各自成段**，不再共用一组六条精选。
    #   原实现把 213 张卡片混排后取前 6（同月 ≤2 / 同类型 ≤3 / 当前题材保底 1）——
    #   季节窗口一旦占满，6 个当前研究主题里就有 4 个被挤出主入口。
    #   现在：当前主题**全部**展示；季节窗口只给预览（另附全量规模）；专项假设单独一段。
    def _pick_seasonal(limit=6):
        picked, months = [], {}
        for c in cards:
            if len(picked) >= limit:
                break
            if c["kind"] != "SEASONAL_WINDOW":
                continue
            m = re.search(r"·\s*(\d+)\s*月", c["title"])
            mk = m.group(1) if m else None
            # 预览要有月份多样性：同月份最多 3 条（原混合精选是 2 条；这里只放季节窗口，故放宽 1 条）
            if mk and months.get(mk, 0) >= 3:
                continue
            picked.append(c["id"])
            if mk:
                months[mk] = months.get(mk, 0) + 1
        return picked

    seasonal_preview = _pick_seasonal(6)
    cur_ids = [c["id"] for c in cards if c["kind"] == "CURRENT_OBJECT"]
    hyp_ids = [c["id"] for c in cards if c["kind"] == "SPECIAL_HYPOTHESIS"]
    sections = {
        "current_objects": {
            "ids": cur_ids,
            "note": ("当前研究主题：独立入口、**全部展示**（不受统计候选数量影响）；属于当前主题证据研究，"
                     "不是算法发现的季节窗口，也**不适用** 5/10/20 交易日结算。"),
        },
        "seasonal_preview": {
            "ids": seasonal_preview,
            "note": ("季节性统计窗口：这里只是**预览 %d 条**（同月份 ≤3 条，保证月份多样性），"
                     "全量 %d 条当前/下月窗口见「查看全部」—— 预览不等于系统只发现了这几条。"
                     % (len(seasonal_preview), len(pd["current_windows"]))),
        },
        "special_hypotheses": {
            "ids": hyp_ids,
            "note": ("专项假设的历史检验：**人工预设**假设（生肖名称 / 台海事件 / 流感季节性），"
                     "不是通用主题挖掘器；与月度收益模式（季节窗口）的分母不同，不得混算。"),
        },
    }
    _sa = pd.get("scan_audit") or {}
    seasonal_scale = {
        "patterns_total": len(pd["patterns"]),
        "patterns_strict": (_sa.get("history_group") or {}).get("strict"),
        "patterns_exploratory": (_sa.get("history_group") or {}).get("exploratory"),
        "current_windows": len(pd["current_windows"]),
        "oos_reportable": sum(1 for p in pd["patterns"] if p.get("evidence_grade") == "OOS_REPORTED"),
        "pit_only": (_sa.get("records") or {}).get("pit_only"),
        "note": ("四个数互不替代：全量模式统计 / 当前或下月窗口 / 样本外可报告 / 仅时点资格。"
                 "**结算结果不在本产物**，见候选账本 `candidate_ledger_v0_2.json`。"),
    }
    doc = {
        "artifact": "candidate_digest", "artifact_version": "0.1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of": iso(pd["as_of"]),
        "group_rule": {
            "G1": "历史重复 STRICT + 样本外 REPORTED 且命中≥50% + 当前/下月窗口",
            "G2": "历史重复 STRICT（无合格 OOS）或有结构参照的当前对象 / 前置观察",
            "G3": "有当前事实与驱动，但历史重复证据不足",
            "G4": "探索线索 / 数据陈旧 / 证据不足 / 无法检验",
            "note": "排序=研究浏览优先顺序，不是收益预测；同组按中位超额与 OOS 命中排序",
        },
        "counts": {g: sum(1 for c in cards if c["group"] == g) for g in ("G1", "G2", "G3", "G4")},
        # ★ 时点资格的规模与质量分层（不把 960 条塞进首页，先交代数量与口径）
        "pattern_pit_summary": (pd.get("pit_only_summary") or {}),
        "pattern_scan_audit": (pd.get("scan_audit") or {}),
        "data_dates": {
            "price_as_of": pd["as_of"],
            # ★ 研究记录日 = 研究侧的 PIT 基准（`snapshot_date`），**不是**产物写出时间。
            #   用 generated_at 会把「今天写文件」当成「今天做了研究」，刷新后立刻出现负天数。
            "research_candidates_as_of": iso((cand or {}).get("snapshot_date") or (cand or {}).get("generated_at")),
            "research_candidates_generated_at": iso((cand or {}).get("generated_at")),
            "research_candidates_days_old": _non_negative(
                days_old((cand or {}).get("snapshot_date") or (cand or {}).get("generated_at"), pd["as_of"])),
            "pattern_discovery_generated_at": iso(pd["generated_at"]),
            "snapshot_latest_canonical": (canonical[-1] if canonical else None),
            "snapshot_latest_any": (snaps[-1] if snaps else None),
            # ★ 不再写死日期：行情基准与快照日都由数据决定，避免字段之间互相矛盾。
            "market_strip_note": "市场状态条行情截至 %s；最新已签发快照 %s" % (
                iso(pd["as_of"]), (canonical[-1] or {}).get("snapshot_date") if canonical else "—"),
        },
        "sources": [
            {"id": "current_candidates", "file": "current_candidates.json", "count": len((cand or {}).get("candidates", [])),
             "date": (cand or {}).get("generated_at", "")[:10]},
            {"id": "forward_observation", "file": fwd_file,
             "count": len((fwd or {}).get("candidates", [])), "date": (fwd or {}).get("as_of")},
            {"id": "pattern_discovery", "file": pd_file, "count": len(pd["current_windows"]), "date": pd["as_of"]},
            {"id": "market_snapshots", "file": "market_snapshots/index.json", "count": len(snaps),
             "date": (snaps[-1] or {}).get("snapshot_date") if snaps else None},
        ],
        "cards": cards,
        # ★★ v0.65：三个入口各自成段（取代原 `featured` 单一 6 条混合精选）
        "sections": sections,
        # ★ 全量规模：避免「只有 6 条精选」被读成「系统只发现了 6 条」
        "seasonal_scale": seasonal_scale,
        "limitations": [
            "★ 不同来源日期不同（研究记录 / 行情 / 快照），卡片分别标注，不统一改写为最新。",
            "★ 分组是研究浏览优先顺序，不是概率、胜率或荐股。",
            "★ 缺股原因分三种：行业板块无历史成分 / 当前主题未建标的映射 / 专项假设未接入个股 —— "
            "卡片按 `stock_gap_reason` 分别说明，不统一写成「没有成分」。",
            "★ 当前相关标的是**研究正文点名的公司**（附出处），不是历史代表股，也不参与排序。",
            "★ 外部线索的内部同月结构支持 ≠ 外部报告已验证。",
        ],
    }

    if a.check:
        files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                       key=lambda f: int(OUT_RE.match(f).group(1)))
        if not files:
            print("FAIL: 汇总产物不存在")
            return 1
        d = json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))
        errs = []
        for c in d["cards"]:
            if c["group"] not in ("G1", "G2", "G3", "G4"):
                errs.append("%s 分组非法" % c["id"])
            if c["group"] == "G1":
                h = c["history"]
                if h.get("tier") != "STRICT" or h.get("oos_status") != "REPORTED":
                    errs.append("%s 进 G1 但证据不足" % c["id"])
                if (h.get("pit_eligible_years") or 0) < 1:
                    errs.append("%s 进 G1 但时点不可发现（只在回看时成立）" % c["id"])
            # ★★ v0.65：公共元信息必须齐全；缺股必须写清原因（不写就是「统一说没成分」）
            disc = c.get("discovery") or {}
            if disc.get("source_class") not in SOURCE_CLASS.values():
                errs.append("%s 缺 discovery.source_class" % c["id"])
            if not disc.get("tracking"):
                errs.append("%s 缺 discovery.tracking" % c["id"])
            if not _has_stocks(c) and not c.get("stock_gap_reason"):
                errs.append("%s 无个股但未写 stock_gap_reason" % c["id"])
            if c.get("stock_gap_reason") and c.get("stock_gap_reason") not in STOCK_GAP_TEXT:
                errs.append("%s stock_gap_reason 非法（%s）" % (c["id"], c.get("stock_gap_reason")))
            # ★ 当前研究主题**不适用** 5/10/20 日结算
            if c["kind"] == "CURRENT_OBJECT":
                if disc.get("settlement_horizons"):
                    errs.append("%s 当前主题不得带结算期限" % c["id"])
                rel = c.get("related_securities") or {}
                if rel.get("status") == "MAPPED" and not (rel.get("items") or []):
                    errs.append("%s 标的映射标 MAPPED 但 items 为空" % c["id"])
                for it in (rel.get("items") or []):
                    if not it.get("ticker") or not it.get("quote"):
                        errs.append("%s 标的 %s 缺 ticker 或原文出处" % (c["id"], it.get("name")))
        # ★ 三个入口必须覆盖全部同类对象（当前主题不得被精选挤出）
        sec = d.get("sections") or {}
        for key, kind in (("current_objects", "CURRENT_OBJECT"),
                          ("special_hypotheses", "SPECIAL_HYPOTHESIS")):
            want = [c["id"] for c in d["cards"] if c["kind"] == kind]
            got = (sec.get(key) or {}).get("ids") or []
            if sorted(got) != sorted(want):
                errs.append("%s 未覆盖全部 %s（%d/%d）" % (key, kind, len(got), len(want)))
        if not ((sec.get("seasonal_preview") or {}).get("ids")):
            errs.append("seasonal_preview 为空")
        if len(d["cards"]) < 100:
            errs.append("候选过少（%d）—— 自动发现窗口未接入？" % len(d["cards"]))
        if errs:
            print("FAIL: %s" % errs[:5])
            return 1
        print("PASS: 候选汇总一致（%d 张 · %s · 当前主题 %d / 专项假设 %d / 季节预览 %d）"
              % (len(d["cards"]), d["counts"],
                 len((sec.get("current_objects") or {}).get("ids") or []),
                 len((sec.get("special_hypotheses") or {}).get("ids") or []),
                 len((sec.get("seasonal_preview") or {}).get("ids") or [])))
        return 0

    print("候选 %d 张 · 分组 %s" % (len(cards), doc["counts"]))
    for c in cards[:5]:
        print("  [%s] %s · %s" % (c["group"], c["title"], c["time_position"]))
    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        out = os.path.join(CURRENT, "candidate_digest_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
