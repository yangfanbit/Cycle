#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""历史冻结重放 v0.3：只把信息侧事件表换成 v0.86 补的历史数据源。

★ 设计：docs/HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md §4（先于本脚本冻结）。
★ 结构性保证「阈值与检验族一字不改」：本脚本**直接复用 v0.2 模块的计算函数与常量**
  （load_market / features_at / settle_row / _build_main / _build_sensitivity /
  _cluster_scores / _bootstrap / _calibration / build），只覆盖 `load_info_events`。
  因此 PRE_DAYS / STEP / HORIZON / EMBARGO / MIN_TRAIN / MIN_CROSS_SECTION /
  INFO_LOOKBACK_DAYS / BOOTSTRAP_B / seed / TRIAL_COUNT / Holm / 校准容差 /
  C1-C3 必要条件 / ③层六条升级条件全部与 v0.2 同源，不重新声明、不调参。
★ 唯一变化：事件表 = NDRC 60 页历史分页的 L1 命中 + 现有雷达 L1 + 历史角色窗口；
  另给 F3_EXT（L3 名称自匹配）敏感性对照，标 SENSITIVITY_ONLY，不进主口径与③层。
★ v0.1 / v0.2 的设计 / 脚本 / 产物逐字节保留，--check 逐份核对基线指纹。

用法：
  python research/scripts/build_historical_replay_v0_3.py --write
  python research/scripts/build_historical_replay_v0_3.py --check
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(ROOT, "research", "current")
DOCS = os.path.join(ROOT, "docs")
SCRIPTS = os.path.join(ROOT, "research", "scripts")
DB = os.path.join(ROOT, "research", "database", "history_scan.db")

OUT = os.path.join(CURRENT, "historical_replay_v0_3.json")
INFO_EVENTS = os.path.join(CURRENT, "historical_info_events_v0_1.json")
HR2_SCRIPT = os.path.join(SCRIPTS, "build_historical_replay_v0_2.py")
DESIGN_V3 = os.path.join(DOCS, "HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md")
DESIGN_V2 = os.path.join(DOCS, "HISTORICAL_REPLAY_DESIGN_v0_2.md")
SEM = os.path.join(CURRENT, "board_semantics_v0_1.json")
TD = os.path.join(CURRENT, "theme_discovery_v0_1.json")

LOCKED_DESIGNS = {
    "HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md": "74928a7191bebf26",
    "HISTORICAL_REPLAY_DESIGN_v0_2.md": "32ad700f0e0a2692",
}
V02_BASELINE_SHA16 = {
    "HISTORICAL_REPLAY_DESIGN_v0_2.md": "32ad700f0e0a2692",
    "historical_replay_v0_2.json": "f951ba23dbb531ed",
    "build_historical_replay_v0_2.py": "8fa91afae280a638",
}
C1_REQUIRED = 0.05   # 设计 §4：不得回头改 5% 阈值

BANNED = ("买入", "卖出", "目标价", "仓位", "胜率", "准确性", "荐股", "选股清单",
          "龙头", "弹性", "大概率", "未来概率", "TODO", "TBD", "PLACEHOLDER")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, indent=1)
        f.write("\n")


def _base():
    spec = importlib.util.spec_from_file_location("hr2_v02_base", HR2_SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _merge_inputs():
    return _load(INFO_EVENTS)["merge_inputs_for_replay_v0_3"]


def _l1_l2_series(info):
    """主口径映射序列集合，与 v0.2 的 L1+L2 完全一致。"""
    return ({v["board_series"] for v in info["lexicon_l1"].values()} |
            {v["board_series"] for v in info["lexicon_l2_role_map"].values()})


def load_info_events_v3():
    """★ v0.3 唯一替换点：主口径事件表 = 历史分页 L1 + 雷达 L1 + 历史角色窗口。"""
    info = _load(INFO_EVENTS)
    mi = _merge_inputs()
    by = collections.defaultdict(set)
    for e in (mi["historical_l1_events"] + mi["radar_l1_events"]
              + mi["role_window_events"]):
        by[e["board_series"]].add(e["event_date"])
    mapped = _l1_l2_series(info)
    ev = info["event_counts"]
    report = {
        "data_source": "historical_info_events_v0_1.json（60 页历史列表页快照）",
        "lexicon_is_post_hoc": info["lexicon_is_post_hoc"],
        "not_point_in_time_signal": info["not_point_in_time_signal"],
        "historical_pages": info["page_reconciliation"]["pages_ok"],
        "historical_events": ev["total"],
        "historical_date_min": ev["date_min"],
        "historical_date_max": ev["date_max"],
        "historical_by_year": ev["by_year"],
        "keyword_count": info["lexicon_l1_size"],
        "radar_l1_pairs": len(mi["radar_l1_events"]),
        "historical_l1_pairs": len(mi["historical_l1_events"]),
        "role_window_events": len(mi["role_window_events"]),
        "total_info_events": len({(d, s) for s, ds in by.items() for d in ds}),
        "mapped_series_count": len(mapped),
        "mapped_series": sorted(mapped),
        "no_exact_mapping_themes": info["validation"]["no_exact_mapping_themes"],
        "sources_without_history": [c["source_id"] for c in info["source_coverage"]
                                    if c["status"] != "HISTORICAL_PAGINATION_OK"],
        "rule": "只用标题关键词精确匹配；正文不建关联；L3 名称自匹配仅作敏感性对照",
    }
    return {sid: sorted(ds) for sid, ds in by.items()}, mapped, report


def load_info_events_ext():
    """F3_EXT：L1+L2+L3 事件，映射扩到库内可解释板块名称（弱证据，仅敏感性对照）。"""
    info = _load(INFO_EVENTS)
    mi = _merge_inputs()
    by = collections.defaultdict(set)
    for e in (mi["historical_l1_events"] + mi["radar_l1_events"]
              + mi["role_window_events"] + mi["l3_events_sensitivity_only"]):
        by[e["board_series"]].add(e["event_date"])
    mapped = _l1_l2_series(info) | set(info["lexicon_l3_name_map"].values())
    report = {"layer": "L3_SENSITIVITY_ONLY", "evidence_grade": "WEAK",
              "l3_name_map_size": info["lexicon_l3_size"],
              "l3_title_hits": info["mapping_hits"]["l3_titles"],
              "mapped_series_count": len(mapped)}
    return {sid: sorted(ds) for sid, ds in by.items()}, mapped, report


def _f3_ext_sensitivity():
    """设计 §4：与 v0.2 **同法**（同一个 _build_main）计算覆盖率与三条件，不参与推断。"""
    if not (os.path.exists(DB) and os.path.getsize(DB) > 0):
        return {"status": "SKIPPED_NO_DB",
                "reason": "缺 history_scan.db，敏感性对照无法重算；--check 显式 SKIP"}
    b = _base()
    td, sem = _load(TD), _load(SEM)
    gate = td["rules"]["market_gate"]
    fuzzy = {e["series_id"] for e in (sem.get("entries") or []) if not e.get("interpretable")}
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        cal, _all, bench, series, amount, _meta, _dup = b.load_market(con)
    finally:
        con.close()
    ev, mapped, report = load_info_events_ext()
    clusters, _ex, _rows, mm = b._build_main(
        cal, bench, series, amount, fuzzy, gate, ev, mapped)
    cov = mm["coverage"]
    total, one = cov.get("OBSERVATIONS", 0), cov.get("F3_ONE", 0)
    rate = round(one / total, 6) if total else None
    c1 = bool(total and one / total >= C1_REQUIRED)
    c2 = bool(mm["clusters_with_both_f3"] >= 20)
    c3 = bool(len(mm["series_with_f3_one"]) >= 5)
    return {
        "status": "COMPUTED",
        "label": "SENSITIVITY_ONLY",
        "note": "L3 名称自匹配为 WEAK 检索线索，不等于事件关联该板块；"
                "不参与 bootstrap / Holm / ③层判定",
        "mapping": report,
        "observations_total": total,
        "f3_one": one,
        "f3_zero": cov.get("F3_ZERO", 0),
        "f3_no_coverage": cov.get("F3_NO_COVERAGE", 0),
        "coverage_rate": rate,
        "necessary_conditions": {
            "C1_coverage_ge_5pct": {"value": rate, "required": C1_REQUIRED, "passes": c1},
            "C2_clusters_with_both_ge_20": {"value": mm["clusters_with_both_f3"],
                                            "required": 20, "passes": c2},
            "C3_distinct_series_ge_5": {"value": len(mm["series_with_f3_one"]),
                                        "required": 5, "passes": c3},
        },
        "effective_features_if_used": 3 if (c1 and c2 and c3) else 2,
        "clusters": len([c for c in clusters if not c.get("cluster_excluded")]),
    }


def build():
    b = _base()
    # ★ 唯一替换点：覆盖事件表加载器，其余全部复用 v0.2 的函数与常量
    b.load_info_events = load_info_events_v3
    doc = b.build()

    doc["artifact_version"] = "0.3"
    doc["supersedes"] = "historical_replay_v0_2.json（逐字节保留，未覆盖）"
    doc["purpose"] = ("历史冻结重放 v0.3：沿用 v0.2 全部阈值与检验族，只把信息侧事件表"
                      "换成历史列表页快照；评估覆盖率是否改善，③层状态按预先写死条件判定")
    doc["design"] = "docs/HISTORICAL_INFO_SOURCES_DESIGN_v0_1.md"
    doc["inherited_design"] = "docs/HISTORICAL_REPLAY_DESIGN_v0_2.md"
    doc["design_sha256_16_locked"] = dict(LOCKED_DESIGNS)
    doc["constants_inherited_from_v0_2"] = {
        "pre_days": b.PRE_DAYS, "step": b.STEP, "horizon": b.HORIZON,
        "embargo": b.EMBARGO, "min_train": b.MIN_TRAIN,
        "min_cross_section": b.MIN_CROSS_SECTION,
        "info_lookback_days": b.INFO_LOOKBACK_DAYS,
        "bootstrap_B": b.BOOTSTRAP_B, "bootstrap_seed": b.BOOTSTRAP_SEED,
        "trial_count": b.TRIAL_COUNT, "alpha": b.ALPHA,
        "calib_monotone_tol": b.CALIB_MONOTONE_TOL,
        "calib_max_gap": b.CALIB_MAX_GAP,
        "note": "直接复用 v0.2 模块常量，未在本脚本重新声明，不存在两份真相",
    }
    doc["f3_ext_sensitivity"] = _f3_ext_sensitivity()
    doc["v0_2_baseline_sha256_16"] = {
        name: (_sha16(os.path.join(DOCS, name)) if name.startswith("HISTORICAL")
               else _sha16(os.path.join(CURRENT, name)) if name.endswith(".json")
               else _sha16(os.path.join(SCRIPTS, name)))
        for name in V02_BASELINE_SHA16
    }
    src = doc.setdefault("source_sha256_16", {})
    src[os.path.basename(INFO_EVENTS)] = _sha16(INFO_EVENTS)
    src[os.path.basename(DESIGN_V3)] = _sha16(DESIGN_V3)
    doc["limits"] = list(doc.get("limits") or []) + [
        "★ 历史信息侧事件是 2026 年构建词表对 2017–2026 标题的**事后检索**结果，"
        "不得解读为当时投资者可得的信号；公开列表页最远 2017-12-18。",
        "★ F3_EXT 是 L3 名称自匹配的 WEAK 敏感性对照，标 SENSITIVITY_ONLY，"
        "不参与 bootstrap / Holm / ③层判定。",
        "★ 主口径 C1 的结构性上限为 12/399×49/15474≈3.8%（映射表只覆盖 12 个序列），"
        "与历史事件条数无关；本轮未回头调整 5% 阈值。",
    ]
    # 重新排序键由 _dump 的 sort_keys 保证
    return doc


def _resolve(name):
    for base in (CURRENT, DOCS, SCRIPTS):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    return None


def check():
    errs, skips = [], []
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    doc = _load(OUT)

    # 1 · 两份设计指纹锁定
    for name, want in LOCKED_DESIGNS.items():
        p = _resolve(name)
        if not p:
            errs.append("设计文档缺失：%s" % name)
        elif _sha16(p) != want:
            errs.append("设计文档已被改动：%s → 必须升版留痕" % name)
    if doc.get("design_sha256_16_locked") != dict(LOCKED_DESIGNS):
        errs.append("产物声明的设计指纹与脚本锁定值不一致")

    # 2 · v0.1 / v0.2 基线逐字保留
    for name, want in V02_BASELINE_SHA16.items():
        if (doc.get("v0_2_baseline_sha256_16") or {}).get(name) != want:
            errs.append("产物记录的 v0.2 基线指纹异常：%s" % name)
        p = _resolve(name)
        if not p:
            errs.append("v0.2 基线文件缺失：%s" % name)
        elif _sha16(p) != want:
            errs.append("v0.2 基线文件已被覆盖：%s" % name)
    b = _base()
    for name, want in b.V01_BASELINE_SHA16.items():
        if (doc.get("v0_1_baseline_sha256_16") or {}).get(name) != want:
            errs.append("产物记录的 v0.1 基线指纹异常：%s" % name)

    # 3 · 上游 sha256 声明 vs 实际
    for name, want in (doc.get("source_sha256_16") or {}).items():
        p = _resolve(name)
        if not p:
            skips.append("上游文件不在干净 checkout：%s" % name)
        elif _sha16(p) != want:
            errs.append("上游指纹漂移：%s" % name)

    # 4 · 有库时逐字节重算
    db_ok = os.path.exists(DB) and os.path.getsize(DB) > 0
    if db_ok:
        rebuilt = build()
        if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
           json.dumps(doc, ensure_ascii=False, sort_keys=True):
            errs.append("产物与上游重算不一致（行情/事件推进后需 --write）")
    else:
        skips.append("行情逐字节复算（缺 history_scan.db，CI 环境）")

    # 5 · 常量与 v0.2 逐项一致（防偷偷调参）
    ci = doc.get("constants_inherited_from_v0_2") or {}
    const_pairs = [
        ("pre_days", b.PRE_DAYS), ("step", b.STEP), ("horizon", b.HORIZON),
        ("embargo", b.EMBARGO), ("min_train", b.MIN_TRAIN),
        ("min_cross_section", b.MIN_CROSS_SECTION),
        ("info_lookback_days", b.INFO_LOOKBACK_DAYS),
        ("bootstrap_B", b.BOOTSTRAP_B), ("bootstrap_seed", b.BOOTSTRAP_SEED),
        ("trial_count", b.TRIAL_COUNT), ("alpha", b.ALPHA),
        ("calib_monotone_tol", b.CALIB_MONOTONE_TOL), ("calib_max_gap", b.CALIB_MAX_GAP),
    ]
    for k, want in const_pairs:
        if ci.get(k) != want:
            errs.append("继承常量与 v0.2 不一致：%s" % k)
    fs = doc.get("freeze_schedule") or {}
    for k, want in (("embargo_trading_days", b.EMBARGO), ("step_trading_days", b.STEP),
                    ("horizon_trading_days", b.HORIZON), ("pre_days", b.PRE_DAYS),
                    ("info_lookback_days", b.INFO_LOOKBACK_DAYS)):
        if fs.get(k) != want:
            errs.append("产物 freeze_schedule 与 v0.2 不一致：%s" % k)
    if (doc.get("ex_ante_features", {}).get("necessary_conditions", {})
            .get("C1_coverage_ge_5pct", {}).get("required") != C1_REQUIRED):
        errs.append("C1 阈值被改动（必须保持 0.05）")

    # 6 · PIT + embargo
    cl = doc.get("clusters") or []
    if not cl:
        errs.append("clusters 为空")
    else:
        dates = [c["freeze_date"] for c in cl]
        if dates != sorted(dates):
            errs.append("冻结点未严格递增")
        pools = [c["train_pool_size"] for c in cl]
        if pools[0] != 0:
            errs.append("首个冻结点训练池非空 → 未来信息泄漏")
        if pools != sorted(pools):
            errs.append("训练池大小非单调不减")
        if any(c.get("embargo_trading_days") != b.EMBARGO for c in cl):
            errs.append("embargo 声明与冻结值不一致")

    # 7 · 三态 / 分母 / 逐簇守恒
    ic = doc.get("information_coverage") or {}
    if ic.get("observations_total") != (ic.get("f3_one", 0) + ic.get("f3_zero", 0)
                                        + ic.get("f3_no_coverage", 0)):
        errs.append("F3 三态计数不守恒")
    rec = doc.get("denominator_reconciliation") or {}
    if rec.get("gross_observations") != rec.get("comparable", 0) + rec.get("excluded", 0):
        errs.append("分母守恒不成立")
    hs = doc.get("historical_statistics") or {}
    if hs.get("comparable_observations") != sum(c["comparable_observations"] for c in cl):
        errs.append("逐簇可比观察数之和与顶层不一致")
    for c in cl:
        if not c.get("cluster_excluded") and \
           c["f3_one"] + c["f3_zero"] + c["f3_no_coverage"] != c["comparable_observations"]:
            errs.append("簇内 F3 三态不守恒：%s" % c["freeze_date"])

    # 8 · bootstrap / Holm / 敏感性轨
    boot = doc.get("cluster_bootstrap") or {}
    if boot.get("B") != b.BOOTSTRAP_B or boot.get("seed") != b.BOOTSTRAP_SEED:
        errs.append("bootstrap B / seed 与冻结值不一致")
    if boot.get("trial_count") != b.TRIAL_COUNT or len(boot.get("tests") or []) != b.TRIAL_COUNT:
        errs.append("试验族大小与预先注册不一致")
    for t in boot.get("tests") or []:
        if t["ci95"][0] > t["ci95"][1] or t["ci975_holm"][0] > t["ci975_holm"][1]:
            errs.append("bootstrap 区间倒置：%s" % t["name"])
        if t["passes"] != (t["holm_reject"] and t["holm_upper_lt_zero"]):
            errs.append("检验通过标记与判定不一致：%s" % t["name"])
    for x in (doc.get("calibration") or {}).get("bins") or []:
        if x["n"] == 0 and (x["mean_predicted"] is not None or x["observed_frequency"] is not None):
            errs.append("空箱未写 null：%s" % x["bin"])
    st = doc.get("sensitivity_track") or {}
    if st.get("calendar_start_declared") != b.SENS_START or \
       (st.get("calendar_first") and st["calendar_first"] < b.SENS_START) or \
       st.get("label") != "SENSITIVITY_ONLY":
        errs.append("敏感性轨声明起点或标记异常")

    # 9 · F3_EXT 与主口径隔离
    ext = doc.get("f3_ext_sensitivity") or {}
    if ext.get("label") != "SENSITIVITY_ONLY":
        errs.append("F3_EXT 未标 SENSITIVITY_ONLY")
    if ext.get("status") == "COMPUTED":
        if ext.get("observations_total") != (ext.get("f3_one", 0) + ext.get("f3_zero", 0)
                                             + ext.get("f3_no_coverage", 0)):
            errs.append("F3_EXT 三态不守恒")
        if (ext.get("necessary_conditions", {}).get("C1_coverage_ge_5pct", {})
                .get("required") != C1_REQUIRED):
            errs.append("F3_EXT 的 C1 阈值不是 0.05")
    elif ext.get("status") != "SKIPPED_NO_DB":
        errs.append("F3_EXT 状态异常")
    else:
        skips.append("F3_EXT 敏感性对照（缺大库）")

    # 10 · 三层口径 / ③层判定
    g3 = doc.get("layer3_gate") or {}
    if doc.get("validated_model") is not False:
        errs.append("validated_model 必须为 false")
    if g3.get("meets_threshold") != all(g3.get("conditions", {}).values()):
        errs.append("③ 层汇总判定与逐条条件不一致")
    ef = (doc.get("ex_ante_features") or {}).get("effective_count")
    if g3.get("actual_effective_ex_ante_features") != ef:
        errs.append("③ 层有效特征数与特征判定不一致")
    if b.TRIAL_COUNT != 2:
        errs.append("v0.2 模块的试验族被改动")

    # 11 · 事后检索声明与禁用措辞（v0.3 产物不含原文标题，全文扫描）
    info_side = doc.get("information_side") or {}
    if info_side.get("lexicon_is_post_hoc") is not True or \
       info_side.get("not_point_in_time_signal") is not True:
        errs.append("事后检索声明缺失")
    blob = json.dumps(doc, ensure_ascii=False)
    for w in BANNED:
        if w in blob:
            errs.append("产物出现禁止措辞或占位符：%s" % w)

    if errs:
        for e in errs:
            print("FAIL " + e)
    for s in skips:
        print("SKIP " + s)
    if errs:
        print("--check：%d 项 FAIL · 范围：双设计指纹 / v0.1+v0.2 基线 / 上游对账 / "
              "常量继承 / PIT+embargo / 三态与分母守恒 / bootstrap / F3_EXT / "
              "③层口径 / 事后检索声明 / 禁用措辞" % len(errs))
        return 1
    print("--check PASS · 范围：双设计指纹锁定 / v0.1+v0.2 基线 6 份 / 上游 %d 项 / "
          "常量继承 %d 项 / PIT+embargo / 三态与分母守恒 / bootstrap B=%d / "
          "F3_EXT / ③层口径 / 事后检索 / 禁用措辞 · 簇 %d · 可比 %d · SKIP %d 项"
          % (len(doc.get("source_sha256_16") or {}), len(const_pairs), b.BOOTSTRAP_B,
             len(cl), hs.get("comparable_observations", 0), len(skips)))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        doc = build()
        _dump(OUT, doc)
        print("--write OK: %s · 簇 %d · 可比 %d · F3_ONE %d"
              % (os.path.basename(OUT),
                 len([c for c in doc["clusters"] if not c.get("cluster_excluded")]),
                 doc["historical_statistics"]["comparable_observations"],
                 doc["information_coverage"]["f3_one"]))
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
