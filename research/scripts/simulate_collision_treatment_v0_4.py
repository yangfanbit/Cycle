#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""simulate_collision_treatment_v0_4.py —— 剩余 5 项 collision 的**处理方案模拟**（只读，不改产物）。

**候选方案**（基于 `analyze_residual_collisions_v0_3.py` 的实测数据）
  P1 `增长` / `负增长`   → **C 最小上下文消歧**：否定语境抑制 `增长`
  P2 `整治` / `整治提升` → **B 删词**：删除 `整治提升`（零增量、零影响）
  P3 `出口` / `出口管制` → **C 最小上下文消歧**：限制语境抑制 `出口`
  P4 `采购` / `装备采购` → **B 删词**：删除 `装备采购`（零增量，删除后语义更正确）
  P5 `储备` / `黄金储备` → **B 删词**：删除 `黄金储备`（零增量，删除后语义更正确）

★ 上下文抑制**只做减法**（不新增任何 canonical 映射）→ **不引入新 vocabulary**。

用法：python research/scripts/simulate_collision_treatment_v0_4.py
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

# ★ v0.4 候选：删除的关键词
DELETE_KEYWORDS = {"整治提升", "装备采购", "黄金储备"}

# ★ v0.4 候选：上下文抑制（**只做减法**）
#   语义：当关键词的**该次出现**处于指定语境时，该次命中不计入。
#   · `增长`：否定语境 —— 前置 1 字 ∈ {负, 零, 不, 未, 无}
#   · `出口`：限制/管制语境 —— 前置 ≤8 字内出现 {管制, 限制, 禁令, 配额, 禁止, 制裁, 收紧}
NEGATION_PREFIX = set("负零不未无")
RESTRICTION_MARKERS = ("管制", "限制", "禁令", "配额", "禁止", "制裁", "收紧")
SUPPRESSION = {"增长": "NEGATION_PREFIX", "出口": "RESTRICTION_WINDOW"}


def occurrences_count(text, kw):
    """关键词 `kw` 在 `text` 中**未被抑制**的出现次数（v0.4 语境抑制规则）。"""
    rule = SUPPRESSION.get(kw)
    n = 0
    start = 0
    while True:
        i = text.find(kw, start)
        if i < 0:
            break
        ok = True
        if rule == "NEGATION_PREFIX":
            ok = not (i > 0 and text[i - 1] in NEGATION_PREFIX)
        elif rule == "RESTRICTION_WINDOW":
            window = text[max(0, i - 8):i]
            ok = not any(m in window for m in RESTRICTION_MARKERS)
        if ok:
            n += 1
        start = i + 1
    return n


def table(v04: bool):
    t = {}
    for k, v in V01.items():
        t[k] = [w for w in v if not (v04 and w in DELETE_KEYWORDS)]
    for k, kws in ADDED.items():
        for kw in kws:
            if v04 and kw in DELETE_KEYWORDS:
                continue
            if kw not in t.setdefault(k, []):
                t[k].append(kw)
    return t


def classify(text, rules, v04):
    if not text.strip() or any(n in text for n in NON_MECHANISM):
        return "NOT_AVAILABLE", None, []
    hits = []
    for c, kws in rules.items():
        for kw in kws:
            if v04:
                if occurrences_count(text, kw) > 0:
                    hits.append(c)
                    break
            else:
                if kw in text or kw.lower() in text.lower():
                    hits.append(c)
                    break
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


def run(v04):
    rules = table(v04)
    return [dict(cycle_id=e["cycle_id"], bucket=e["bucket"], seq=e["seq"], raw_driver=e["raw_driver"],
                 matched_rules=classify(e["raw_driver"] or "", rules, v04)[2],
                 mapping_status=classify(e["raw_driver"] or "", rules, v04)[0],
                 canonical_driver=classify(e["raw_driver"] or "", rules, v04)[1]) for e in L3]


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


S0, S1 = run(False), run(True)
M0 = {(r["cycle_id"], r["bucket"], r["seq"]): r for r in S0}

print("=" * 90)
print("v0.3 → v0.4 候选方案：逐条差异")
print("=" * 90)
diffs = []
for r in S1:
    x = M0[(r["cycle_id"], r["bucket"], r["seq"])]
    if x["mapping_status"] != r["mapping_status"] or x["canonical_driver"] != r["canonical_driver"] \
            or x["matched_rules"] != r["matched_rules"]:
        diffs.append((x, r))
        print("  %-30s %-11s seq=%d" % (r["cycle_id"], r["bucket"], r["seq"]))
        print("     raw   : %s" % (r["raw_driver"] or "")[:110])
        print("     hits  : %s → %s" % (x["matched_rules"], r["matched_rules"]))
        print("     status: %-13s → %-13s | canon: %s → %s"
              % (x["mapping_status"], r["mapping_status"], x["canonical_driver"], r["canonical_driver"]))
print("  共 %d 条" % len(diffs))
print()
c0, c1 = canon_set(S0), canon_set(S1)
print("=" * 90)
print("canonical_drivers 变化")
print("=" * 90)
ch = [c for c in set(c0) | set(c1) if c0.get(c, set()) != c1.get(c, set())]
print("  %d 个 cycle 变化" % len(ch))
for c in sorted(ch):
    print("     %-32s %s → %s %s" % (c, sorted(c0.get(c, set())) or "[]",
                                     sorted(c1.get(c, set())) or "[]", "(campaign)" if c in CAMP else "(RC)"))
print()
p0, p1 = primary(S0), primary(S1)
print("primary_mechanism 变化:", [(c, p0.get(c), p1.get(c)) for c in set(p0) | set(p1) if p0.get(c) != p1.get(c)] or "无")
print()
print("=" * 90)
print("五态分布")
print("=" * 90)
print("  v0.3:", dict(collections.Counter(r["mapping_status"] for r in S0)))
print("  v0.4:", dict(collections.Counter(r["mapping_status"] for r in S1)))
print()
print("有 canonical driver 的 cycle:", len(c0), "→", len(c1),
      "| campaign:", len([c for c in c0 if c in CAMP]), "→", len([c for c in c1 if c in CAMP]))
neg = [d for d in diffs if d[1]["mapping_status"] in ("UNKNOWN", "NOT_AVAILABLE")
       and d[0]["mapping_status"] not in ("UNKNOWN", "NOT_AVAILABLE")]
print("★ 负面变化（→ UNKNOWN/NOT_AVAILABLE）:", len(neg))
for x, r in neg:
    print("     %-30s %-11s seq=%d | %s → %s" % (r["cycle_id"], r["bucket"], r["seq"],
                                                 x["mapping_status"], r["mapping_status"]))
print()
print("★ 新增 DIRECT:", len([d for d in diffs if d[1]["mapping_status"] == "DIRECT" and d[0]["mapping_status"] != "DIRECT"]))
for x, r in diffs:
    if r["mapping_status"] == "DIRECT" and x["mapping_status"] != "DIRECT":
        print("     %-30s %-11s seq=%d | %s → DIRECT/%s" % (r["cycle_id"], r["bucket"], r["seq"],
                                                            x["mapping_status"], r["canonical_driver"]))
