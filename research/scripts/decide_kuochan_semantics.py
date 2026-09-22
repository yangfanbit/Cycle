#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""decide_kuochan_semantics.py —— `扩产` / `扩产周期` 语义裁决的**最小影响分析**（只读模拟，不修改任何产物）。

**模拟场景**（★ 本脚本**显式重建**三个场景，因此对当前词表状态**不敏感**、可重复运行）
  S0 = **修改前**：`扩产`→DEMAND_SURGE，`扩产周期`→SUPPLY_CONTRACTION
  S1 = **已实施**：删除 `扩产周期`（`扩产` 保留在 DEMAND_SURGE）   ← 本脚本裁决方案
  S2 = 对照：删除 `扩产` 与 `扩产周期`（两个都删）

对每个场景重算 541 条 ledger 条目的 `matched_rules` / `mapping_status` / `canonical_driver`，
并逐条比对差异（**含负面变化**）。

用法：python research/scripts/decide_kuochan_semantics.py
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
CAMP = {c["campaign_id"] for c in json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))["campaigns"]}

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


def table(scenario):
    """★ 显式重建：先由 v0.1 基表 + v0.3 added_rules 构成**当前**词表，再按场景回放/推进。"""
    t = {k: list(v) for k, v in V01.items()}
    for k, kws in ADDED.items():
        for kw in kws:
            if kw not in t.setdefault(k, []):
                t[k].append(kw)
    # 当前 v0.3 已删除「扩产周期」→ S0 需**回放**加入；S1 保持现状；S2 再删「扩产」
    if scenario == "S0" and "扩产周期" not in t["SUPPLY_CONTRACTION"]:
        t["SUPPLY_CONTRACTION"].append("扩产周期")
    if scenario == "S2":
        t["DEMAND_SURGE"] = [w for w in t["DEMAND_SURGE"] if w != "扩产"]
    return t


def classify(text, rules):
    if not text.strip() or any(n in text for n in NON_MECHANISM):
        return "NOT_AVAILABLE", None, []
    hits = []
    for canon, kws in rules.items():
        if any(kw in text or kw.lower() in text.lower() for kw in kws):
            hits.append(canon)
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


def run(scenario):
    rules = table(scenario)
    return [dict(cycle_id=e["cycle_id"], bucket=e["bucket"], seq=e["seq"],
                 raw_driver=e["raw_driver"],
                 matched_rules=classify(e["raw_driver"] or "", rules)[2],
                 mapping_status=classify(e["raw_driver"] or "", rules)[0],
                 canonical_driver=classify(e["raw_driver"] or "", rules)[1]) for e in L3]


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
    out = {}
    for c in {x["cycle_id"] for x in rows}:
        cc = cnt.get(c)
        out[c] = sorted(cc.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if cc else "UNKNOWN"
    return out


S = {s: run(s) for s in ("S0", "S1", "S2")}


def diff(a, b, label):
    ka = {(r["cycle_id"], r["bucket"], r["seq"]): r for r in a}
    out = []
    for r in b:
        x = ka[(r["cycle_id"], r["bucket"], r["seq"])]
        if x["mapping_status"] != r["mapping_status"] or x["canonical_driver"] != r["canonical_driver"] \
                or x["matched_rules"] != r["matched_rules"]:
            out.append({"cycle_id": r["cycle_id"], "bucket": r["bucket"], "seq": r["seq"],
                        "raw_driver": (r["raw_driver"] or "")[:120],
                        "old_matched_rules": x["matched_rules"], "new_matched_rules": r["matched_rules"],
                        "old_mapping_status": x["mapping_status"], "new_mapping_status": r["mapping_status"],
                        "old_canonical_driver": x["canonical_driver"],
                        "new_canonical_driver": r["canonical_driver"]})
    print("=" * 78)
    print("差异：%s（%d 条）" % (label, len(out)))
    print("=" * 78)
    for d in out:
        print("  %-30s %-11s seq=%d" % (d["cycle_id"], d["bucket"], d["seq"]))
        print("     raw   : %s" % d["raw_driver"])
        print("     hits  : %s  →  %s" % (d["old_matched_rules"], d["new_matched_rules"]))
        print("     status: %-13s → %-13s | canon: %s → %s"
              % (d["old_mapping_status"], d["new_mapping_status"],
                 d["old_canonical_driver"], d["new_canonical_driver"]))
    return out


D1 = diff(S["S0"], S["S1"], "S0（修改前）→ S1（删除「扩产周期」，保留「扩产」）【已实施】")
print()
D2 = diff(S["S0"], S["S2"], "S0（修改前）→ S2（对照：删除「扩产」+「扩产周期」）")

print()
print("=" * 78)
print("canonical_drivers 变化")
print("=" * 78)
for tag, rows in (("S1", S["S1"]), ("S2", S["S2"])):
    cs0, cs1 = canon_set(S["S0"]), canon_set(rows)
    ch = [c for c in set(cs0) | set(cs1) if cs0.get(c, set()) != cs1.get(c, set())]
    print("  %s: %d 个 cycle 的 driver 集合变化" % (tag, len(ch)))
    for c in sorted(ch):
        print("     %-30s %s → %s %s" % (c, sorted(cs0.get(c, set())) or "[]",
                                         sorted(cs1.get(c, set())) or "[]",
                                         "(campaign)" if c in CAMP else "(RC)"))
print()
print("=" * 78)
print("primary_mechanism 变化")
print("=" * 78)
p0 = primary(S["S0"])
for tag, rows in (("S1", S["S1"]), ("S2", S["S2"])):
    p1 = primary(rows)
    ch = [c for c in p0 if p0[c] != p1.get(c)]
    print("  %s: %d 个 cycle 变化 %s" % (tag, len(ch), [(c, p0[c], p1.get(c)) for c in ch] or "无"))

print()
print("=" * 78)
print("五态分布")
print("=" * 78)
for s in ("S0", "S1", "S2"):
    print("  %s: %s" % (s, dict(collections.Counter(r["mapping_status"] for r in S[s]))))
print()
print("有 canonical driver 的 cycle 数:")
for s in ("S0", "S1", "S2"):
    cs = canon_set(S[s])
    n_camp = len([c for c in cs if c in CAMP])
    print("  %s: %d / 79（其中 campaign %d / 52）" % (s, len(cs), n_camp))

# 写审计产物
out = {
    "artifact": "kuochan_semantics_decision", "artifact_version": "0.3",
    "generated_by": "research/scripts/decide_kuochan_semantics.py",
    "position": "Research-only 裁决分析件 —— **只读模拟**；不修改任何产物。",
    "scenarios": {
        "S0": "修改前：扩产→DEMAND_SURGE，扩产周期→SUPPLY_CONTRACTION",
        "S1": "**已实施**：删除「扩产周期」（保留「扩产」在 DEMAND_SURGE）",
        "S2": "对照：删除「扩产」与「扩产周期」",
    },
    "decision": {
        "扩产": "A —— 可作为 DEMAND_SURGE 的有效机制词（客户侧产能投资 → 上游需求）",
        "扩产周期": "D —— 从 canonical keyword mapping 中删除",
        "implemented": "S1",
        "implemented_in": "canonicalize_historical_drivers_v0_3.py（revision v0.3-r2）",
    },
    "diff_S0_S1": D1, "diff_S0_S2": D2,
}
p = os.path.join(REP, "kuochan_semantics_decision_v0_3.json")
with io.open(p, "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write("\n")
print()
print("written", p)
