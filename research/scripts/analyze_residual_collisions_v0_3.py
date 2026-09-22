#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""analyze_residual_collisions_v0_3.py —— 剩余 5 项 substring collision 的**逐项影响分析**（只读）。

5 项：`增长/负增长` · `整治/整治提升` · `出口/出口管制` · `采购/装备采购` · `储备/黄金储备`

对每个关键词：
  · 真实命中文本（cycle / bucket / raw_driver / matched_rules / status / canon / refs）
  · canonical 归属
  · 是否跨 canonical
  · **零增量覆盖判定**（其命中集合是否为对偶词的子集）
  · **删除该词的影响**（逐条 diff：hits / status / canon / canonical_drivers / primary）

用法：python research/scripts/analyze_residual_collisions_v0_3.py
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(ROOT, "research", "research", "reports")

L3 = json.load(io.open(os.path.join(REP, "historical_driver_evidence_ledger_v0_3.json"), encoding="utf-8"))["entries"]
C3 = json.load(io.open(os.path.join(REP, "historical_driver_canonicalization_v0_3.json"), encoding="utf-8"))
EXP = json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))
CAMP = {c["campaign_id"] for c in EXP["campaigns"]}

PAIRS = [
    ("增长", "负增长"),
    ("整治", "整治提升"),
    ("出口", "出口管制"),
    ("采购", "装备采购"),
    ("储备", "黄金储备"),
]

V01 = {
    "POLICY_DRIVEN": ["政策", "规划", "通知", "指导意见", "国常会", "政治局", "工信部", "部委", "发改委", "能源局",
                      "医保局", "中医药局", "交通部", "财政部", "税务总局", "五部门", "四部委", "国务院", "国资委",
                      "补贴", "试点", "牌照", "法规", "集采", "医保", "标准体系", "标准化", "双碳", "碳达峰", "碳中和",
                      "核准", "备案", "平价上网", "新政", "专项行动", "实景实训", "吹风"],
    "TECH_BREAKTHROUGH": ["技术", "突破", "首发", "首次", "亮相", "GTC", "量产", "ADS", "天神之眼", "智驾", "算法",
                          "刀片电池", "超级电驱", "DE-i", "CPO", "NPO", "1.6T", "800G", "400G", "结构迁移",
                          "光引擎", "算电协同", "具身智能", "人形机器人", "脑机接口", "标准体系（2026 版）"],
    "INDUSTRY_UPGRADE": ["结构迁移", "升级", "渗透率", "国产化", "规模化", "代际", "产业链", "环节", "全链条",
                         "生态", "一体化", "扩围", "迁移", "供应链", "国产替代"],
    "DEMAND_SURGE": ["需求", "订单", "销量", "出货", "装机", "景气", "放量", "增长", "翻倍", "出口", "刚需",
                     "刚", "营收", "净利润", "业绩", "并网", "招标", "采购", "付费", "试运营", "客座率"],
    "SUPPLY_CONTRACTION": ["产能", "供给", "过剩", "涨价", "价格", "库存", "缺芯", "出清", "挤压", "利润", "售价",
                           "降价", "成本", "硅料", "多晶硅", "限产"],
    "VALUATION_RESET": ["估值", "低估值", "修复", "估值杀", "泡沫", "破万亿", "市值", "倍", "x ", "抱团", "高估值",
                        "虹吸", "风格"],
    "CYCLE_REVERSAL": ["见顶", "见底", "退潮", "衰减", "回调", "反转", "结束", "出清完成", "分化", "回落", "回撤",
                       "震荡", "亏钱效应", "断板", "跌停", "低点", "高点"],
    "EVENT_CATALYST": ["发布会", "上市", "展会", "催化", "开工", "启动仪式", "峰会", "论坛", "大会", "嘉年华",
                       "跑出圈", "中标", "获批"],
}
ADDED = {k: [x["keyword"] for x in v] for k, v in C3["rules"]["added_rules"].items()}
CANONICAL = ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
             "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL", "EVENT_CATALYST", "UNKNOWN"]
NON_MECHANISM = ["unknown", "暂无", "未知", "无（", "获利盘", "暂定", "（暂定）"]
PRICE_ACTION = ["涨停", "跌停", "连板", "20cm", "天地板", "断板", "涨", "跌", "走强", "活跃", "爆发",
                "大涨", "回调", "调整", "见顶", "见底", "回撤", "新高", "低点", "高点", "板块", "指数",
                "市值", "涨幅", "倍", "板"]
REF_RE = re.compile(r"(EV-[A-Z0-9\-]+|E-[A-Z0-9\-]+|S-[A-Z0-9\-]+)")


def base_table():
    t = {k: list(v) for k, v in V01.items()}
    for k, kws in ADDED.items():
        for kw in kws:
            if kw not in t.setdefault(k, []):
                t[k].append(kw)
    return t


def owner_of(kw, rules):
    return [c for c, kws in rules.items() if kw in kws]


def classify(text, rules):
    if not text.strip() or any(n in text for n in NON_MECHANISM):
        return "NOT_AVAILABLE", None, []
    hits = [c for c, kws in rules.items() if any(k in text or k.lower() in text.lower() for k in kws)]
    hits = [h for h in CANONICAL if h in hits]
    refs = sorted(set(REF_RE.findall(text)))
    if (len(hits) == 0 and any(p in text for p in PRICE_ACTION)) or \
       (len(hits) == 1 and hits[0] == "CYCLE_REVERSAL" and any(p in text for p in PRICE_ACTION) and not refs):
        return "NOT_AVAILABLE", None, hits
    if len(hits) == 0:
        return "UNKNOWN", None, hits
    if len(hits) == 1:
        return ("DIRECT" if refs else "DERIVED"), hits[0], hits
    if len(hits) >= 4:
        return "AMBIGUOUS", None, hits
    return "DERIVED", None, hits


def run(rules):
    out = []
    for e in L3:
        st, canon, hits = classify(e["raw_driver"] or "", rules)
        out.append(dict(cycle_id=e["cycle_id"], bucket=e["bucket"], seq=e["seq"],
                        raw_driver=e["raw_driver"], matched_rules=hits,
                        mapping_status=st, canonical_driver=canon,
                        refs=sorted(set(REF_RE.findall(e["raw_driver"] or "")))))
    return out


def canon_set(rows):
    d = collections.defaultdict(set)
    for r in rows:
        if r["bucket"] in ("start", "accelerator") and r["mapping_status"] in ("DIRECT", "DERIVED") \
                and r["canonical_driver"]:
            d[r["cycle_id"]].add(r["canonical_driver"])
    return d


def primary(rows):
    cnt = collections.defaultdict(lambda: collections.Counter())
    for r in rows:
        if r["bucket"] in ("start", "accelerator") and r["mapping_status"] == "DIRECT" and r["canonical_driver"]:
            cnt[r["cycle_id"]][r["canonical_driver"]] += 1
    return {c: (sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if v else "UNKNOWN")
            for c, v in cnt.items()}


BASE_T = base_table()
S0 = run(BASE_T)
S0MAP = {(r["cycle_id"], r["bucket"], r["seq"]): r for r in S0}
S0CANON = canon_set(S0)
S0PRIM = primary(S0)

report = {"artifact": "residual_collision_analysis", "artifact_version": "0.3",
          "generated_by": "research/scripts/analyze_residual_collisions_v0_3.py",
          "position": "Research-only 分析件 —— 只读；不修改任何产物。",
          "pairs": []}

for a, b in PAIRS:
    oa, ob = owner_of(a, BASE_T), owner_of(b, BASE_T)
    ta = [r for r in S0 if a in (r["raw_driver"] or "")]
    tb = [r for r in S0 if b in (r["raw_driver"] or "")]
    sa = {id(r) for r in ta}
    subset = all(any(x is r for x in ta) for r in tb)   # tb ⊆ ta ?
    print("=" * 90)
    print("COLLISION: %s (%s)  ⊂  %s (%s)" % (a, ",".join(oa), b, ",".join(ob)))
    print("=" * 90)
    print("  %-10s canonical=%-24s 命中=%d" % (a, ",".join(oa), len(ta)))
    print("  %-10s canonical=%-24s 命中=%d  %s" % (b, ",".join(ob), len(tb),
                                                   "★ 其命中集合是「%s」的**子集 → 零增量覆盖**" % a if subset else ""))
    for tag, rows in ((a, ta), (b, tb)):
        for r in rows:
            print("    [%s] %-30s %-11s seq=%d" % (tag, r["cycle_id"], r["bucket"], r["seq"]))
            print("         raw   : %s" % (r["raw_driver"] or "")[:110])
            print("         hits  : %s | status=%s canon=%s refs=%s"
                  % (r["matched_rules"], r["mapping_status"], r["canonical_driver"], r["refs"]))
    # 删除影响
    effects = {}
    for kw in (a, b):
        rules2 = {k: [w for w in v if w != kw] for k, v in BASE_T.items()}
        S1 = run(rules2)
        diffs = []
        for r in S1:
            x = S0MAP[(r["cycle_id"], r["bucket"], r["seq"])]
            if x["mapping_status"] != r["mapping_status"] or x["canonical_driver"] != r["canonical_driver"] \
                    or x["matched_rules"] != r["matched_rules"]:
                diffs.append({"cycle_id": r["cycle_id"], "bucket": r["bucket"], "seq": r["seq"],
                              "raw_driver": (r["raw_driver"] or "")[:110],
                              "old_hits": x["matched_rules"], "new_hits": r["matched_rules"],
                              "old_status": x["mapping_status"], "new_status": r["mapping_status"],
                              "old_canon": x["canonical_driver"], "new_canon": r["canonical_driver"]})
        cs1 = canon_set(S1)
        cdiff = {c: (sorted(S0CANON.get(c, set())), sorted(cs1.get(c, set())))
                 for c in set(S0CANON) | set(cs1) if S0CANON.get(c, set()) != cs1.get(c, set())}
        p1 = primary(S1)
        pdiff = {c: (S0PRIM.get(c), p1.get(c)) for c in set(S0PRIM) | set(p1)
                 if S0PRIM.get(c) != p1.get(c)}
        neg = [d for d in diffs if d["new_status"] in ("UNKNOWN", "NOT_AVAILABLE") and d["old_status"] not in ("UNKNOWN", "NOT_AVAILABLE")]
        print("  ── 删除「%s」的影响：%d 条条目变化 · %d 个 cycle driver 集合变化 · %d 个 primary 变化 · %d 条负面"
              % (kw, len(diffs), len(cdiff), len(pdiff), len(neg)))
        for d in diffs:
            print("       %-30s %-11s seq=%d  hits %s → %s | %s → %s | canon %s → %s"
                  % (d["cycle_id"], d["bucket"], d["seq"], d["old_hits"], d["new_hits"],
                     d["old_status"], d["new_status"], d["old_canon"], d["new_canon"]))
        for c, (x, y) in sorted(cdiff.items()):
            print("       driver: %-30s %s → %s %s" % (c, x, y, "(campaign)" if c in CAMP else "(RC)"))
        effects[kw] = {"changed_entries": len(diffs), "canonical_driver_changes": cdiff,
                       "primary_changes": pdiff, "negative": len(neg), "detail": diffs}
    print()
    report["pairs"].append({"shorter": a, "longer": b,
                            "shorter_canonical": oa, "longer_canonical": ob,
                            "shorter_hits": len(ta), "longer_hits": len(tb),
                            "longer_is_subset_of_shorter": subset,
                            "delete_effect": effects})

p = os.path.join(REP, "residual_collision_analysis_v0_3.json")
with io.open(p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("written", p)
