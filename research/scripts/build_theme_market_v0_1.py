#!/usr/bin/env python3
"""build_theme_market_v0_1.py —— 当前主题：产业阶段 vs 市场层实测并列（v0.79）。

## 回答使用者两个问题
1. 「阶段当初怎么定的？」→ 产物里写清**两套来源**：
   · 研究侧声明 `attention_state` / `stage_review`（ai-offline 人工离线轮次，
     依据 evidence[] 产业层证据 + phase_evidence 三维定性；10-23 Round 月度刷新
     REVIEWED_MAINTAINED，明确把 10-22 回调记 NEUTRAL、不作反向证据）；
   · 产品端推导 `currentPhaseInference` R0–R8 透明规则引擎（7 维证据矩阵，
     **禁止 `涨幅>X ⇒ EXPANSION`**，证据不足返回 UNKNOWN，声明与推导不一致时并列）。
2. 「阶段为什么不随行情更新？」→ 因为阶段**不在派生链里**（人工产物），
   且阶段语义是**产业机制阶段**，不是行情状态。本脚本**不自动改阶段**，
   只做：① 人工声明关联标的 → 自动校验库内存在；② 周更算真实行情并列展示；
   ③ 输出「待人工重评」与「产业/市场背离」信号；④ 写清后续更新 SOP。

## 零编造
 - 标的清单是**人工声明**，每条带 basis；自动校验 series_id + 名称精确相等、
   且库内有行情；校验失败即 FAIL（不静默丢弃）。
 - 行情取 history_scan.db 的 raw 收盘（既有口径，不偷偷换复权）；
   交易日历用 CSI300 自身日期序列；as_of = 库内 CSI300 最后一根。
 - 只是事实陈列，不改阶段、不输出概率、不推断因果。

用法：--write / --check
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import date, datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
CANDIDATES = os.path.join(REPO, "research", "current", "current_candidates.json")
OUT = os.path.join(REPO, "research", "current", "theme_market_v0_1.json")
HORIZONS = (5, 10, 20)
STALE_DAYS = 7
DIVERGENCE_PP = -10.0

PHASE_LABEL = {
    "THEME_FORMING": "主题形成中", "BROAD_CONFIRMATION": "广泛确认",
    "EXPANSION": "扩散", "PEAK": "峰值", "COOLING": "降温",
    "DORMANT": "沉寂", "UNKNOWN": "未分类",
}
EXPANSIVE = {"EXPANSION", "BROAD_CONFIRMATION", "PEAK"}

# ★★ 人工声明的关联标的池（不是板块成分、不是选股清单、不参与阶段判定）
# basis 说明每条依据；脚本会按 series_id + name 精确校验库内存在。
REFERENCE_STOCKS = {
    "CC-2026-OPTICAL-LINK": [
        ("sz300502", "新易盛", "EXPLICIT_IN_STAGE_REVIEW"),
        ("sz300308", "中际旭创", "EXPLICIT_IN_STAGE_REVIEW"),
        ("sz300394", "天孚通信", "EXPLICIT_IN_STAGE_REVIEW"),
        ("sz002281", "光迅科技", "EXPLICIT_IN_STAGE_REVIEW"),
    ],
    "CC-2026-OFFSHORE-WIND": [
        ("sh601615", "明阳智能", "EXPLICIT_IN_NARRATIVE"),
        ("sz001289", "龙源电力", "EXPLICIT_IN_NARRATIVE"),
        ("sz002487", "大金重工", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
        ("sz002531", "天顺风能", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
    ],
    "CC-2026-EMBODIED-AI": [
        ("sh688836", "宇树科技", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
        ("sz002600", "领益智造", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
        ("sh688322", "奥比中光", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
    ],
    "CC-2026-BCI-MEDTECH": [
        ("sh688273", "麦澜德", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
        ("sh688626", "翔宇医疗", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
    ],
    "CC-2026-COMPUTE-POWER": [
        ("sh600941", "中国移动", "EXPLICIT_IN_NARRATIVE"),
    ],
    "CC-2026-AUTO-SMARTDRIVE": [
        ("sz000625", "长安汽车", "NARRATIVE_ENTITY_MAPPED（正文「长安」）"),
        ("sh600733", "北汽蓝谷", "NARRATIVE_ENTITY_MAPPED（正文「北汽」）"),
        ("sz002594", "比亚迪", "RESEARCHER_DECLARED_SUPPLY_CHAIN"),
    ],
}

PHASE_GOVERNANCE = {
    "research_declared": {
        "fields": ["attention_state", "stage_review", "phase_evidence", "core_narrative"],
        "source": "current_candidates.json（generated_by=ai-offline，人工离线研究轮次）",
        "criteria": "依据 evidence[] 的产业层证据（政策 / 订单 / 交付 / 产能）与 "
                    "phase_evidence 三维定性（narrative / breadth / information_marginal）；"
                    "阶段是**产业机制阶段**，不是行情状态",
        "last_review": "Round 2026-10-23（月度刷新）",
        "last_verdict": "REVIEWED_MAINTAINED（6 个主题全部维持）",
        "market_exclusion": "10-22 板块回调无法与全市场普跌分离（当日上涨家数占比 9.6%）"
                            "→ 记 NEUTRAL、明确不作反向证据；"
                            "stage_review.basis 写明若当作反向证据，规则引擎会推出 UNKNOWN，本轮不采用",
    },
    "product_inferred": {
        "engine": "src/data/timeline/currentPhaseInference.ts（R0_INSUFFICIENT_EVIDENCE … R8_UNCLASSIFIED）",
        "input": "PhaseEvidenceMatrix 七维证据（叙事 / 政策 / 产业 / 市场 / 资金 / 广度 / 公司层）"
                 "+ 新增信息边际",
        "r4_expansion": "market ≥ PRESENT 且 breadth ≥ PRESENT 且 narrative ≥ PRESENT",
        "forbidden": "明确禁止 `涨幅 > X ⇒ EXPANSION`；证据不足返回 UNKNOWN",
        "ui_rule": "agreesWithDeclared = false 时 UI **必须并列显示**研究声明与推导值，不得静默取一",
    },
    "update_policy": {
        "auto_change_phase": False,
        "reason": "避免把行情回调当事后证据去改产业机制判定（v0.79 使用者确认「不自动改阶段」）",
        "weekly": "周更只刷新 market_performance / price_as_of / research_days_old / signals；"
                  "阶段字段一字不改",
        "manual_round": "人工研究轮次改阶段时必须同时更新 attention_state、stage_review.basis、"
                        "reviewed_at、status、last_updated、snapshot_date，并写明依据与来源",
        "triggers": ["research_days_old > 7 → REVIEW_STALE",
                     "产业阶段属扩散/广泛确认/峰值 且 20 日相对超额 < -10pp → DIVERGENCE_INDUSTRY_VS_MARKET"],
        "signals_are_not_verdicts": "信号只提示人工复核，不构成阶段变更、不参与验收",
    },
}


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _norm(d):
    return str(d).replace("-", "")


def _series(con, sid):
    return {_norm(d): float(c) for d, c in con.execute(
        "SELECT trade_date,close FROM scan_daily WHERE series_id=? AND close>0", (sid,))}


def _ret(px, cal, n):
    """as_of 往前 n 个交易日的收益（%）；缺任一端 → None。"""
    if len(cal) <= n:
        return None
    a, b = cal[-1 - n], cal[-1]
    if a not in px or b not in px:
        return None
    return round((px[b] / px[a] - 1) * 100, 2)


def build():
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    cand = json.load(open(CANDIDATES, encoding="utf-8"))
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        bench = _series(con, "CSI300")
        cal = sorted(bench)
        if len(cal) < max(HORIZONS) + 1:
            raise RuntimeError("CSI300 序列过短")
        as_of = cal[-1]
        name_by_id = dict(con.execute(
            "SELECT series_id,name FROM scan_series WHERE kind='stock'").fetchall())
        themes = []
        for c in cand["candidates"]:
            cid = c["candidate_id"]
            declared = c.get("attention_state") or "UNKNOWN"
            sr = c.get("stage_review") or {}
            reviewed = c.get("snapshot_date") or sr.get("reviewed_at") or c.get("last_updated")
            days_old = (date.fromisoformat(as_of[:4] + "-" + as_of[4:6] + "-" + as_of[6:])
                        - date.fromisoformat(reviewed)).days if reviewed else None
            stocks = []
            for sid, name, basis in REFERENCE_STOCKS.get(cid, []):
                actual = name_by_id.get(sid)
                ok = actual == name
                px = _series(con, sid) if ok else {}
                rets = {str(n): _ret(px, cal, n) for n in HORIZONS} if ok else {}
                excess = {str(n): (round(rets[str(n)] - _ret(bench, cal, n), 2)
                                   if rets[str(n)] is not None and _ret(bench, cal, n) is not None
                                   else None) for n in HORIZONS}
                stocks.append({
                    "series_id": sid, "name": name, "name_in_db": actual,
                    "verified": ok, "basis": basis,
                    "rows": len(px), "limited_history": len(px) < 60,
                    "return_pct": rets, "excess_pp": excess,
                })
            valid = [s for s in stocks if s["verified"]]
            basket = {}
            for n in HORIZONS:
                vals = [s["excess_pp"][str(n)] for s in valid
                        if s["excess_pp"][str(n)] is not None]
                bvals = [s["return_pct"][str(n)] for s in valid
                         if s["return_pct"][str(n)] is not None]
                basket[str(n)] = {
                    "covered": len(vals), "total": len(valid),
                    "equal_weight_return_pct": round(sum(bvals) / len(bvals), 2) if bvals else None,
                    "equal_weight_excess_pp": round(sum(vals) / len(vals), 2) if vals else None,
                }
            signals = []
            if days_old is not None and days_old > STALE_DAYS:
                signals.append({"id": "REVIEW_STALE", "detail": "阶段判定距今 %d 天（> %d）→ 待人工重评"
                                % (days_old, STALE_DAYS)})
            ex20 = basket["20"]["equal_weight_excess_pp"]
            if declared in EXPANSIVE and ex20 is not None and ex20 < DIVERGENCE_PP:
                signals.append({"id": "DIVERGENCE_INDUSTRY_VS_MARKET",
                                "detail": "产业机制阶段=%s，关联标的 20 日等权相对超额 %.2f pp（< %.0f）"
                                          % (PHASE_LABEL.get(declared, declared), ex20, DIVERGENCE_PP)})
            themes.append({
                "candidate_id": cid, "display_name": c.get("display_name"),
                "industry_phase": {
                    "declared": declared, "label": PHASE_LABEL.get(declared, declared),
                    "source": "研究侧人工声明（ai-offline），不是行情推导",
                    "reviewed_at": reviewed, "research_days_old": days_old,
                    "review_status": sr.get("status"), "review_round": sr.get("review_round"),
                    "basis": sr.get("basis"),
                    "phase_evidence": c.get("phase_evidence"),
                    "market_excluded_from_phase": True,
                },
                "market_layer": {
                    "as_of": as_of, "price_type": "raw（未复权，既有口径）",
                    "benchmark": "CSI300",
                    "horizons_trading_days": list(HORIZONS),
                    "equal_weight": basket,
                    "note": "只是事实陈列；不参与阶段判定、不预测未来",
                },
                "reference_stocks": stocks,
                "signals": signals,
                "core_narrative_excerpt": (c.get("core_narrative") or "")[:260],
            })
    finally:
        con.close()
    return {
        "artifact": "theme_market", "artifact_version": "0.1", "generated_at": now,
        "purpose": "把研究侧『产业机制阶段』与『市场层实测』并列；不自动改阶段",
        "as_of": as_of, "cadence": "WEEKLY",
        "phase_governance": PHASE_GOVERNANCE,
        "counts": {
            "themes": len(themes),
            "declared_stocks": sum(len(t["reference_stocks"]) for t in themes),
            "verified_stocks": sum(sum(1 for s in t["reference_stocks"] if s["verified"])
                                  for t in themes),
            "with_divergence": sum(1 for t in themes
                                   if any(s["id"] == "DIVERGENCE_INDUSTRY_VS_MARKET"
                                          for s in t["signals"])),
            "with_stale_review": sum(1 for t in themes
                                     if any(s["id"] == "REVIEW_STALE" for s in t["signals"])),
        },
        "limits": [
            "★ 阶段是**产业机制阶段**（研究侧人工声明），不是行情状态；市场层不参与定档。",
            "★ 关联标的池是人工声明的**参照池**，不是板块成分、不是选股清单、不参与阶段判定。",
            "★ 行情用 raw 未复权收盘、基准对齐 CSI300 交易日历；除权日可能有跳变。",
            "★ 信号只提示人工复核，不构成阶段变更，也不参与有效性验收。",
            "★ 周更只刷新行情与信号；改阶段必须走人工研究轮次并留痕（见 phase_governance.update_policy）。",
        ],
        "themes": themes,
        "source_sha256_16": {os.path.basename(CANDIDATES): _sha(CANDIDATES)},
    }


def check():
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    cur, want = json.load(open(OUT, encoding="utf-8")), build()
    def norm(o):
        o = dict(o); o.pop("generated_at", None)
        return json.dumps(o, ensure_ascii=False, sort_keys=True)
    errs = []
    if norm(cur) != norm(want): errs.append("theme_market 与重新派生不一致")
    if cur["counts"]["declared_stocks"] != cur["counts"]["verified_stocks"]:
        errs.append("有标的未通过库内校验")
    for t in cur["themes"]:
        if not t["reference_stocks"]:
            errs.append("%s 缺关联标的声明" % t["candidate_id"])
        if t["industry_phase"]["declared"] not in PHASE_LABEL:
            errs.append("%s 阶段不在枚举内" % t["candidate_id"])
        if t["industry_phase"]["market_excluded_from_phase"] is not True:
            errs.append("%s 未标明市场层不参与定档" % t["candidate_id"])
        for s in t["reference_stocks"]:
            if not s["verified"] or s["name"] != s["name_in_db"]:
                errs.append("%s/%s 名称校验失败" % (t["candidate_id"], s["series_id"]))
    if cur["phase_governance"]["update_policy"]["auto_change_phase"] is not False:
        errs.append("阶段被允许自动改写（违反决策）")
    if errs:
        for x in errs: print("  FAIL", x)
        print("--check：%d 项 FAIL" % len(errs)); return 1
    print("--check PASS · 主题 %d · 标的 %d/%d 已校验 · 背离 %d · 待重评 %d · as_of %s"
          % (cur["counts"]["themes"], cur["counts"]["verified_stocks"],
             cur["counts"]["declared_stocks"], cur["counts"]["with_divergence"],
             cur["counts"]["with_stale_review"], cur["as_of"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check: return check()
    d = build()
    if not a.write:
        print(json.dumps(d, ensure_ascii=False, indent=1)[:2600]); return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("已生成 research/current/theme_market_v0_1.json")
    return check()


if __name__ == "__main__":
    sys.exit(main())
