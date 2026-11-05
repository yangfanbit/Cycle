#!/usr/bin/env python3
"""build_workbench_basis_v0_1.py —— 研究工作台的**确定性派生**数据（v0.74）。

从**既有产物**生成两个轻量文件，不新增任何事实、不训练模型、不改动源产物：

  research/current/workbench_index_v0_1.json       检索索引（默认页面加载）
  research/current/workbench_eval_basis_v0_1.json  内部评估基准（**仅评估视图按需加载**）

★★ 口径（`docs/EVALUATION_FRAMEWORK_v0_1.md`）：
  · 有效性 = **研究增量**，不是 5/10/20 日板块超额。
  · 内部排序/评分只允许出现在评估视图；索引产物里**不得**含任何评分字段。
  · priority_score = Wilson 95% 区间下界（历史 hit_rate / n_years），
    是启发式排序，**不是概率、不是预测、未校准**。

用法：
  python build_workbench_basis_v0_1.py --write    生成两份产物
  python build_workbench_basis_v0_1.py --check    只读复算并对账（忽略 generated_at）
"""
import argparse
import glob
import hashlib
import json
import math
import os
import re
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_INDEX = os.path.join(CURRENT, "workbench_index_v0_1.json")
OUT_EVAL = os.path.join(CURRENT, "workbench_eval_basis_v0_1.json")

def _latest_versioned(prefix):
    """★★ v0.76：源产物会随行情刷新升版，**不得硬编码「当前版本」**。
    用 glob + 版本号数字排序取最新（不能按文件名字符串排序，否则 v0_9 < v0_12）。"""
    fs = glob.glob(os.path.join(CURRENT, "%s_v0_*.json" % prefix))
    fs = [f for f in fs if re.search(r"_v0_(\d+)\.json$", f)]
    if not fs:
        raise SystemExit("找不到 %s 的版本化产物" % prefix)
    return os.path.relpath(max(fs, key=lambda f: int(re.search(r"_v0_(\d+)\.json$", f).group(1))), REPO)


INPUTS = {
    "timeline": "exports/timeline_export_v1.json",
    # 展示包文件名带 `_view`，单独取最新版本
    "radar": _latest_versioned("new_theme_radar").replace(".json", "_view.json"),
    "patterns": _latest_versioned("pattern_discovery"),
    "maps_index": "research/current/historical_event_maps_index.json",
}


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return json.load(fh)


def _sha16(rel):
    with open(os.path.join(REPO, rel), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def wilson(k, n, z=1.96):
    """Wilson score interval（95%）。k/n 为历史命中数与年份数；返回 (low, high)。"""
    if not n or n <= 0:
        return None, None
    p = k / n
    den = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = (z / den) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(max(0.0, center - half), 6), round(min(1.0, center + half), 6)


def _short(x, limit=160):
    """把任意源字段压成可展示的短字符串（不改写含义，只截断并标注）。"""
    if x is None:
        return None
    if isinstance(x, str):
        return x if len(x) <= limit else x[:limit] + "…"
    s = json.dumps(x, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= limit else s[:limit] + "…"


# ─────────────────────────── 检索索引 ───────────────────────────
def _historical_objects(t):
    out = []
    for c in t.get("campaigns", []) + t.get("research_candidates", []):
        themes = [x.get("name") for x in (c.get("themes") or []) if x.get("name")]
        main = next((x.get("name") for x in (c.get("themes") or [])
                     if x.get("role") == "main"), themes[0] if themes else None)
        title = c.get("title") or ("%s · %s" % (main or c.get("campaign_id"), c.get("year")))
        status = c.get("research_status") or c.get("status") or "UNKNOWN"
        out.append({
            "id": c["campaign_id"],
            "kind": "HISTORICAL_OBJECT",
            "title": title,
            "date": c.get("start_date"),
            "year": c.get("year"),
            "themes": themes,
            "source": {"name": "Cycle-Research canonical export",
                       "publisher": "ThreeC Research", "url": None,
                       "source_kind": "INTERNAL_STRUCTURED_OBJECT"},
            "why": "库内 Campaign / Research Candidate 的机制段；主题与窗口来自结构化研究对象，"
                   "不是外部报道。追溯：旧站「历史题材 / 事件」→ 查看对象详情。",
            "uncertainty": "HIGH" if status in ("PROVISIONAL", "provisional") else "MEDIUM",
            "uncertainty_reason": "research_status = %s；库内对象含 PROVISIONAL / CONFLICT，非正式历史事实" % status,
            "board_series": None,
            "url": None,
        })
    return out


def _policy_events(v):
    out = []
    for e in v.get("events", []):
        src = e.get("source") or {}
        links = e.get("theme_links") or []
        tags = e.get("theme_tags") or []
        tm = e.get("time") or {}
        certainty = tm.get("time_certainty")
        if certainty == "UNCERTAIN":
            unc, reason = "HIGH", "日期冲突严重，时点不确定 → 不计算数值行情窗口"
        elif tm.get("precise_time_rejected"):
            unc, reason = "MEDIUM", "精确发布时间被拒（%s），采用保守日期口径" % (
                (tm.get("precise_time_rejected") or {}).get("reason"))
        else:
            unc, reason = "LOW", "时点口径已确定（%s）" % (tm.get("reaction_basis") or "UNKNOWN")
        if links:
            l = links[0]
            why = ("标题命中「%s」→ 关联 %s（%s，%s）；属显式关键词映射，不是语义判定，"
                   "也不是因果结论" % (l.get("keyword"), l.get("board_name"),
                                    l.get("board_series"), l.get("relation")))
        else:
            why = ("标题未命中显式关键词表 → 未建立板块关联；产业指向可能在正文，"
                   "需人工核对原始 URL")
        out.append({
            "id": e["event_id"],
            "kind": "POLICY_EVENT",
            "title": e.get("title"),
            "date": e.get("event_date"),
            "year": int((e.get("event_date") or "0")[:4]) or None,
            "themes": tags,
            "doc_class": e.get("doc_class"),
            "status": e.get("status"),
            "source": {"name": src.get("name"), "publisher": src.get("publisher"),
                       "url": src.get("url"), "source_kind": "PUBLIC_POLICY_PAGE",
                       "source_id": src.get("id")},
            "why": why,
            "uncertainty": unc,
            "uncertainty_reason": reason,
            "board_series": (links[0].get("board_series") if links else None),
            "url": src.get("url"),
        })
    return out


def _theme_map_events():
    idx = _load(INPUTS["maps_index"])
    out = []
    for m in idx.get("maps", []):
        rel = os.path.join("research", "current", m["file"])
        if not os.path.exists(os.path.join(REPO, rel)):
            continue
        d = _load(rel)
        for e in d.get("events", []):
            gaps = e.get("known_gaps")
            state = e.get("study_state")
            unc = "HIGH" if (gaps or state in ("INSUFFICIENT", "NOT_RESEARCHED")) else "MEDIUM"
            out.append({
                "id": e["event_id"],
                "kind": "THEME_MAP_EVENT",
                "title": e.get("label"),
                "date": "%s" % e.get("year"),
                "year": e.get("year"),
                "themes": [m["label"]],
                "source": {"name": "历史题材地图 · %s" % m["label"],
                           "publisher": "ThreeC Research", "url": None,
                           "source_kind": "INTERNAL_THEME_MAP", "file": m["file"]},
                "why": _short(e.get("evidence_basis"), 300),
                "uncertainty": unc,
                "uncertainty_reason": "study_state = %s；%s" % (
                    state, "有已知缺口" if gaps else "无显式缺口"),
                "board_series": None,
                "url": None,
            })
    return out


def build_index():
    t = _load(INPUTS["timeline"])
    v = _load(INPUTS["radar"])
    items = _historical_objects(t) + _policy_events(v) + _theme_map_events()
    items.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    sources = [{"file": rel, "sha256_16": _sha16(rel)} for rel in INPUTS.values()]
    sources += [{"file": os.path.relpath(f, REPO), "sha256_16": _sha16(os.path.relpath(f, REPO))}
                for f in sorted(glob.glob(os.path.join(CURRENT, "*historical_events_v0_*.json")))]
    return {
        "artifact": "workbench_index", "artifact_version": "0.1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "as_of": v.get("as_of"),
        "source_artifacts": sources,
        "caliber": {
            "purpose": "研究增量验证的**检索索引**；只提供可追溯的线索与来源，不是结论",
            "effectiveness_definition": "研究增量（docs/EVALUATION_FRAMEWORK_v0_1.md），不是行情超额",
            "not": ["不含行情超额结论", "不含概率", "不含内部排序或评分",
                    "不含买入/卖出/推荐语义"],
            "url_policy": "url 为 null 表示内部结构化对象，没有外部报道 URL；不编造来源",
            "uncertainty_levels": "LOW 时点已确定 / MEDIUM 时点或证据有限 / HIGH 冲突或显式缺口",
        },
        "counts": {
            "total": len(items),
            "by_kind": {k: sum(1 for x in items if x["kind"] == k)
                        for k in ("HISTORICAL_OBJECT", "POLICY_EVENT", "THEME_MAP_EVENT")},
            "with_external_url": sum(1 for x in items if x.get("url")),
        },
        "items": items,
    }


# ─────────────────────────── 内部评估基准 ───────────────────────────
def build_eval():
    d = _load(INPUTS["patterns"])
    rows = []
    for p in d.get("patterns", []):
        n = int(p.get("n_years") or 0)
        hr = p.get("hit_rate")
        if not n or hr is None:
            continue
        # k 优先由 per_year 逐年超额精确计数，并与产物 hit_rate 对账
        per = p.get("per_year") or []
        k = None
        k_source = None
        if per and all(isinstance(x, dict) and "excess_pct" in x for x in per):
            k = sum(1 for x in per if (x.get("excess_pct") or 0) > 0)
            k_source = "COUNTED_FROM_PER_YEAR"
            if abs(k / n - float(hr)) > 0.02:
                k = int(round(float(hr) * n))
                k_source = "ROUNDED_FROM_PRODUCT_HIT_RATE_COUNT_MISMATCH"
        else:
            k = int(round(float(hr) * n))
            k_source = "ROUNDED_FROM_PRODUCT_HIT_RATE"
        k = max(0, min(n, k))
        low, high = wilson(k, n)
        rows.append({
            "board_series": p.get("board_series"),
            "board": p.get("board"),
            "month": p.get("month"),
            "kind": p.get("kind"),
            "tier": p.get("tier"),
            "hit_rate": hr,
            "n_years": n,
            "k": k,
            "k_source": k_source,
            "wilson_low": low,
            "wilson_high": high,
            "median_excess_pct": p.get("median_excess_pct"),
            "oos_tests": p.get("oos_tests"),
            "oos_status": p.get("oos_status"),
            "evidence_grade": p.get("evidence_grade"),
            "discovery_basis": p.get("discovery_basis"),
            "pit_basis": p.get("pit_basis"),
            # ★ 唯一打分定义：Wilson 下界；小样本与高不确定性自动降权
            "priority_score": low,
            "priority_reason": "Wilson 95%% 下界（k=%d / n=%d）· OOS 检验 %s 次 · PIT %s"
                               % (k, n, p.get("oos_tests"), p.get("pit_basis")),
            "usage": "INTERNAL_EVAL_ONLY",
            "calibrated": False,
            "is_probability": False,
        })
    rows.sort(key=lambda r: (-(r["priority_score"] or 0), r["board_series"] or "", r["month"] or 0))
    return {
        "artifact": "workbench_eval_basis", "artifact_version": "0.1",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {"file": INPUTS["patterns"], "sha256_16": _sha16(INPUTS["patterns"]),
                   "artifact_version": d.get("artifact_version"), "as_of": d.get("as_of")},
        "caliber": {
            "usage": "INTERNAL_EVAL_ONLY",
            "purpose": "只用于生成对照实验的**内部排序材料**，不参与验收判定",
            "score_definition": "priority_score = Wilson 95% 区间下界（历史 hit_rate / n_years）",
            "is_probability": False,
            "calibrated": False,
            "not": ["不是未来概率", "不是胜率", "不是预测模型", "不是推荐或买卖信号",
                    "不代表事件与行情有因果关系"],
            "why_allowed": "不排序无法做对照；但排序**不得**出现在默认页面",
            "primary_metrics": "有效性由研究增量判定（新线索率 / 耗时变化 / 事后可核性），见 EVALUATION_FRAMEWORK_v0_1.md",
            # ★ 自查补：产物里带 median_excess_pct，必须写明它只是行情附注，
            #   否则容易被读成「评分依据」或「有效性证明」。
            "market_excess_note": "median_excess_pct 是历史行情附注，不参与 priority_score、"
                                  "不参与有效性判定，也不显示在评估视图表格中",
        },
        "counts": {"rows": len(rows),
                   "with_oos_tests": sum(1 for r in rows if (r.get("oos_tests") or 0) > 0)},
        "rows": rows,
    }


# ─────────────────────────── 校验 / 写入 ───────────────────────────
def _payload(d):
    return {k: v for k, v in d.items() if k != "generated_at"}


def check():
    errs = []
    for path, builder in ((OUT_INDEX, build_index), (OUT_EVAL, build_eval)):
        if not os.path.exists(path):
            errs.append("缺少产物 %s" % os.path.relpath(path, REPO))
            continue
        got = json.load(open(path, encoding="utf-8"))
        want = builder()
        if _payload(got) != _payload(want):
            errs.append("%s 与源产物重算不一致（需重跑 --write）" % os.path.basename(path))
    if os.path.exists(OUT_INDEX):
        idx = json.load(open(OUT_INDEX, encoding="utf-8"))
        banned = ("priority_score", "wilson_low", "hit_rate", "calibrated")
        blob = json.dumps(idx, ensure_ascii=False)
        for b in banned:
            if b in blob:
                errs.append("索引产物不得含评分字段：%s（内部排序只能存在于评估视图）" % b)
        for it in idx.get("items", []):
            for f in ("id", "kind", "title", "date", "why", "uncertainty", "source"):
                if f not in it:
                    errs.append("索引条目 %s 缺字段 %s" % (it.get("id"), f))
            if it.get("url") and not str(it["url"]).startswith("http"):
                errs.append("索引条目 %s 的 url 不可核" % it.get("id"))
        c = idx.get("counts") or {}
        if c.get("total") != len(idx.get("items", [])):
            errs.append("索引 counts.total 与 items 长度不符")
    if os.path.exists(OUT_EVAL):
        ev = json.load(open(OUT_EVAL, encoding="utf-8"))
        for r in ev.get("rows", []):
            low, high = wilson(r["k"], r["n_years"])
            if r["wilson_low"] != low or r["wilson_high"] != high:
                errs.append("Wilson 复算不符 %s/%s" % (r.get("board_series"), r.get("month")))
            if r["priority_score"] != r["wilson_low"]:
                errs.append("priority_score 必须等于 Wilson 下界 %s" % r.get("board_series"))
            if r.get("usage") != "INTERNAL_EVAL_ONLY" or r.get("calibrated") is not False \
                    or r.get("is_probability") is not False:
                errs.append("评估行缺 INTERNAL_EVAL_ONLY / 未校准 / 非概率标记")
        if (ev.get("counts") or {}).get("rows") != len(ev.get("rows", [])):
            errs.append("评估 counts.rows 与实际行数不符")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.write and not a.check:
        print("需要 --write 或 --check")
        return 2
    if a.check:
        errs = check()
        if errs:
            for e in errs[:20]:
                print("FAIL:", e)
            print("FAIL 共 %d 项" % len(errs))
            return 1
        idx = json.load(open(OUT_INDEX, encoding="utf-8"))
        ev = json.load(open(OUT_EVAL, encoding="utf-8"))
        print("PASS workbench_basis --check")
        print("  索引 %d 条（%s），外部 URL %d 条" % (
            idx["counts"]["total"], idx["counts"]["by_kind"], idx["counts"]["with_external_url"]))
        print("  评估 %d 行，其中有 OOS 检验 %d 行；priority=Wilson 下界复算一致" % (
            ev["counts"]["rows"], ev["counts"]["with_oos_tests"]))
        print("  ★ 索引产物零评分字段；内部排序仅在评估视图按需加载")
        return 0
    for path, builder, name in ((OUT_INDEX, build_index, "index"),
                                (OUT_EVAL, build_eval, "eval")):
        d = builder()
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
        print("已生成 %-56s %8d bytes (%s)" % (
            os.path.relpath(path, REPO), os.path.getsize(path), name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
