#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""audit_driver_keyword_collisions_v0_3.py —— v0.3 新增关键词 **碰撞审计**（只读，不修改任何产物）。

**范围**：仅审计 v0.3 `ADDED_RULES` 中的关键词（**不重新扩展词表**）。

**数据来源（全部只读）**
  · `historical_driver_canonicalization_v0_3.json`（`rules.added_rules` / `keyword_collision_audit`）
  · `historical_driver_evidence_ledger_v0_3.json`（541 条 `raw_driver` + `matched_rules`）
  · `historical_driver_canonicalization_v0_2.json`（primary mechanism 对照）
  · `historical_driver_evidence_ledger_v0_2.json`（v0.2 对照）

**审计维度（对应用户 §2）**
  A. 同一 `raw_driver` 是否同时命中多个 canonical driver（co-hit）
  B. 新增关键词各自：命中文本数 / 作为**唯一命中**的文本数 / co-hit 分布
  C. 「宽关键词」风险：命中数高但**不具决定性**（同文本另有多机制命中）或与其他 canonical 存在**子串冲突**
  D. 语义风险词（用户点名 16 词）逐词审计
  E. 对 Canonical Campaign 的 `primary_mechanism` 影响（v0.2 → v0.3）
  F. 新增 `AMBIGUOUS`
  G. `DIRECT → DERIVED`（已有 DIRECT 被新增词破坏）

用法：python research/scripts/audit_driver_keyword_collisions_v0_3.py
"""
from __future__ import annotations

import collections
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REP = os.path.join(ROOT, "research", "research", "reports")

C3 = json.load(io.open(os.path.join(REP, "historical_driver_canonicalization_v0_3.json"), encoding="utf-8"))
L3 = json.load(io.open(os.path.join(REP, "historical_driver_evidence_ledger_v0_3.json"), encoding="utf-8"))["entries"]
C2 = json.load(io.open(os.path.join(REP, "historical_driver_canonicalization_v0_2.json"), encoding="utf-8"))
L2 = json.load(io.open(os.path.join(REP, "historical_driver_evidence_ledger_v0_2.json"), encoding="utf-8"))["entries"]

ADDED = {c: [x["keyword"] for x in v] for c, v in C3["rules"]["added_rules"].items()}
ADDED_NOTES = {c: {x["keyword"]: x["coverage_note"] for x in v} for c, v in C3["rules"]["added_rules"].items()}
ALL_ADDED = sorted({kw for v in ADDED.values() for kw in v})
KW_OWNER = {}
for c, kws in ADDED.items():
    for kw in kws:
        KW_OWNER.setdefault(kw, set()).add(c)
KW_OWNER = {k: sorted(v) for k, v in KW_OWNER.items()}

# 用户点名重点词
FOCUS = ["政策", "方案", "财政", "限制", "配置", "持仓", "渠道", "用户", "储备", "扩产",
         "军费", "阅兵", "高股息", "资产荒", "关联交易", "合同负债", "实际利率"]

# 每 canonical 的**全量**关键词（v0.1 + 新增）—— 从 artifact 的 added_index + 词表引用推断不可得，
# 故直接读取 v0.1 词表与新增词拼接（**只读**，不修改）。
V01_RULES = {
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
FULL = {c: list(v) for c, v in V01_RULES.items()}
for c, kws in ADDED.items():
    for kw in kws:
        if kw not in FULL.setdefault(c, []):
            FULL[c].append(kw)
FULL_OWNER = collections.defaultdict(list)
for c, kws in FULL.items():
    for kw in kws:
        FULL_OWNER[kw].append(c)


def hits_of(text):
    """该文本命中的 canonical 集合（**按全量词表重算**，用于独立于 ledger 的复核）。"""
    out = []
    for c, kws in FULL.items():
        if any(kw in text or kw.lower() in text.lower() for kw in kws):
            out.append(c)
    return out


def main():
    print("=" * 78)
    print("Driver Canonicalization v0.3 —— 新增关键词碰撞审计")
    print("=" * 78)
    print("新增关键词总数: %d | ledger 条目: %d" % (len(ALL_ADDED), len(L3)))

    # ---------- A/B：逐词统计 ----------
    per_kw = []
    for kw in ALL_ADDED:
        owners = KW_OWNER[kw]
        matched = [e for e in L3 if kw in (e["raw_driver"] or "")]
        only = [e for e in matched if set(e["matched_rules"]) == set(owners)]
        cohit = collections.Counter()
        for e in matched:
            for c in e["matched_rules"]:
                if c not in owners:
                    cohit[c] += 1
        per_kw.append({
            "keyword": kw, "canonical": owners,
            "n_texts_matched": len(matched),
            "n_texts_where_decisive": len(only),
            "co_hit_canonicals": dict(cohit),
            "cross_canonical_duplicate": len(owners) > 1,
        })
    per_kw.sort(key=lambda x: (-x["n_texts_matched"], x["keyword"]))

    # ---------- C：宽关键词风险 ----------
    substr = C3["keyword_collision_audit"]["substring_conflicts_across_canonical"]
    substr_by_added = [s for s in substr
                       if s["shorter"] in ALL_ADDED or s["longer"] in ALL_ADDED]
    wide = []
    for x in per_kw:
        if x["n_texts_matched"] >= 2 and x["n_texts_where_decisive"] < x["n_texts_matched"]:
            wide.append(x)
    wide.sort(key=lambda x: -(x["n_texts_matched"] - x["n_texts_where_decisive"]))

    # ---------- D：语义风险词（用户点名） ----------
    focus = []
    for kw in FOCUS:
        row = next((x for x in per_kw if x["keyword"] == kw), None)
        if row:
            focus.append(row)
        else:
            focus.append({"keyword": kw, "canonical": KW_OWNER.get(kw, []),
                          "n_texts_matched": 0, "n_texts_where_decisive": 0,
                          "co_hit_canonicals": {}, "cross_canonical_duplicate": False,
                          "note": "未在 v0.3 新增词中（可能属 v0.1 原有词）"})

    # ---------- E：Canonical Campaign primary_mechanism 影响 ----------
    def direct_cnt(led):
        d = collections.defaultdict(lambda: collections.Counter())
        for e in led:
            if e["bucket"] in ("start", "accelerator") and e["mapping_status"] == "DIRECT" and e["canonical_driver"]:
                d[e["cycle_id"]][e["canonical_driver"]] += 1
        return d
    D2, D3 = direct_cnt(L2), direct_cnt(L3)

    def prim(dc, cyc):
        c = dc.get(cyc)
        if not c:
            return "UNKNOWN"
        best = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        return best[0][0] if best and best[0][1] > 0 else "UNKNOWN"
    KIND = {}
    for x in C3["per_cycle"]:
        KIND[x["cycle_id"]] = x["cycle_id"]
    exp = json.load(io.open(os.path.join(ROOT, "exports", "timeline_export_v1.json"), encoding="utf-8"))
    CAMP = {c["campaign_id"] for c in exp["campaigns"]}
    prim_changes = []
    for cyc in sorted(CAMP):
        a, b = prim(D2, cyc), prim(D3, cyc)
        if a != b:
            prim_changes.append({"cycle_id": cyc, "primary_v0_2": a, "primary_v0_3": b,
                                 "is_canonical_campaign": True})

    # ---------- F：新增 AMBIGUOUS ----------
    amb3 = {e["cycle_id"] + "|" + e["bucket"] + "|" + str(e["seq"]) for e in L3
            if e["mapping_status"] == "AMBIGUOUS"}
    amb2 = {e["cycle_id"] + "|" + e["bucket"] + "|" + str(e["seq"]) for e in L2
            if e["mapping_status"] == "AMBIGUOUS"}
    new_amb = sorted(amb3 - amb2)

    # ---------- G：DIRECT → DERIVED ----------
    k2 = {(e["cycle_id"], e["bucket"], e["seq"]): e for e in L2}
    d2d = []
    for e in L3:
        a = k2.get((e["cycle_id"], e["bucket"], e["seq"]))
        if a and a["mapping_status"] == "DIRECT" and e["mapping_status"] == "DERIVED":
            d2d.append({"cycle_id": e["cycle_id"], "bucket": e["bucket"], "seq": e["seq"],
                        "raw_driver": (e["raw_driver"] or "")[:150],
                        "was_canonical": a["canonical_driver"], "now_hits": e["matched_rules"]})

    # ---------- 汇总 ----------
    print()
    print("【A/B】新增关键词命中分布（按命中文本数降序，前 25）")
    print("  %-14s %-26s %6s %8s  %s" % ("keyword", "canonical", "命中", "决定性", "co-hit"))
    for x in per_kw[:25]:
        print("  %-14s %-26s %6d %8d  %s" % (x["keyword"], ",".join(x["canonical"]),
                                             x["n_texts_matched"], x["n_texts_where_decisive"],
                                             x["co_hit_canonicals"] or "-"))
    print()
    print("【A】命中多个 canonical 的新增关键词: %d %s"
          % (len([x for x in per_kw if x["cross_canonical_duplicate"]]),
             [x["keyword"] for x in per_kw if x["cross_canonical_duplicate"]]))
    print("【C】宽关键词风险（命中≥2 且存在非决定性）: %d" % len(wide))
    for x in wide[:15]:
        print("     %-14s 命中 %d / 决定性 %d | co-hit=%s"
              % (x["keyword"], x["n_texts_matched"], x["n_texts_where_decisive"], x["co_hit_canonicals"]))
    print("【C】跨 canonical 子串冲突（含新增词）: %d" % len(substr_by_added))
    for s in substr_by_added:
        tag = " ★新增" if (s["shorter"] in ALL_ADDED or s["longer"] in ALL_ADDED) else ""
        print("     %-10s ⊂ %-14s | %s → %s%s"
              % (s["shorter"], s["longer"], s["shorter_owner"], s["longer_owner"], tag))
    print()
    print("【D】语义风险词（用户点名 %d 词）" % len(FOCUS))
    print("  %-12s %-24s %6s %8s  %s" % ("keyword", "canonical", "命中", "决定性", "co-hit"))
    for x in focus:
        print("  %-12s %-24s %6d %8d  %s" % (x["keyword"], ",".join(x["canonical"]),
                                             x["n_texts_matched"], x["n_texts_where_decisive"],
                                             x["co_hit_canonicals"] or "-"))
    print()
    print("【E】Canonical Campaign primary_mechanism 变化: %d" % len(prim_changes))
    for p in prim_changes:
        print("     %-32s %s → %s" % (p["cycle_id"], p["primary_v0_2"], p["primary_v0_3"]))
    print()
    print("【F】新增 AMBIGUOUS: %d %s" % (len(new_amb), new_amb))
    print("【G】DIRECT → DERIVED: %d" % len(d2d))
    for d in d2d:
        print("     %-30s %-11s seq=%d | was=%s → hits=%s"
              % (d["cycle_id"], d["bucket"], d["seq"], d["was_canonical"], d["now_hits"]))

    # ---------- 写审计产物 ----------
    out = {
        "artifact": "driver_keyword_collision_audit", "artifact_version": "0.3",
        "generated_by": "research/scripts/audit_driver_keyword_collisions_v0_3.py",
        "position": "Research-only 审计件 —— **只读**；不修改任何词表 / 产物 / DB / export。",
        "scope": {"added_keywords": len(ALL_ADDED), "ledger_entries": len(L3)},
        "per_keyword": per_kw,
        "cross_canonical_duplicate_added": [x["keyword"] for x in per_kw if x["cross_canonical_duplicate"]],
        "wide_keyword_risk": wide,
        "substring_conflicts_involving_added": substr_by_added,
        "pre_existing_cross_canonical_duplicate": C3["keyword_collision_audit"]["cross_canonical_duplicate_keywords_all"],
        "focus_words": focus,
        "primary_mechanism_changes_canonical_campaigns": prim_changes,
        "new_ambiguous": new_amb,
        "direct_to_derived": d2d,
    }
    p = os.path.join(REP, "driver_keyword_collision_audit_v0_3.json")
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print()
    print("written", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
