"""Historical Driver Canonicalization v0.1（deterministic，只读）。

**目标**：把历史侧自由文本 driver 映射到**仓库既有的** canonical driver vocabulary，
使 historical cycle 与 current candidate 可在同一 driver 词表下比较。

## 语义前提（用户 §四 —— 最重要）
**Event Type ≠ Driver。**
  Event Type = 发生了什么类型的事件（policy / industry / company / market / macro …）
  Driver     = 该周期由什么机制推动（POLICY_DRIVEN / DEMAND_SURGE / …）
因此本脚本**不建立** `event_type → driver` 的硬映射，**不**用 event_type、**不**用价格结果反推 driver。

## Canonical vocabulary（复用，不新造）
`research/current/schema.json` 的 `narrativeType` 枚举（candidate 侧 `narrative_types` 已在用）：
  POLICY_DRIVEN · INDUSTRY_UPGRADE · TECH_BREAKTHROUGH · DEMAND_SURGE · SUPPLY_CONTRACTION
  · VALUATION_RESET · CYCLE_REVERSAL · EVENT_CATALYST · UNKNOWN

## 规则
显式、可审计的关键词规则（下表 RULES）。**不使用** event_type / 价格 / 涨跌。
mapping_status：
  DIRECT      —— 恰好命中 1 条规则，且该文本可追溯到 evidence/event/source 引用（EV-/E-/S-）
  DERIVED     —— 命中 ≥2 条规则（需从多处提及综合判断）
  AMBIGUOUS   —— 命中 ≥4 条规则（无法收敛）
  UNKNOWN     —— 有文本但无规则命中
  NOT_AVAILABLE —— 文本为空或纯非机制表述（unknown / 获利盘 等）

产物：
  research/research/reports/historical_driver_canonicalization_v0_1.json
  research/research/reports/historical_driver_evidence_ledger_v0_1.json
"""
import collections
import io
import json
import os
import re
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_CANON = f"{REP}/historical_driver_canonicalization_v0_1.json"
OUT_LEDGER = f"{REP}/historical_driver_evidence_ledger_v0_1.json"

# ---- canonical vocabulary（复用 research/current/schema.json 的 narrativeType 枚举）----
CANONICAL_DRIVERS = ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
                     "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL",
                     "EVENT_CATALYST", "UNKNOWN"]

# ---- 显式关键词规则（可审计；不使用 event_type / 价格 / 涨跌）----
RULES = {
    "POLICY_DRIVEN": [
        "政策", "规划", "通知", "指导意见", "国常会", "政治局", "工信部", "部委", "发改委", "能源局",
        "医保局", "中医药局", "交通部", "财政部", "税务总局", "五部门", "四部委", "国务院", "国资委",
        "补贴", "试点", "牌照", "法规", "集采", "医保", "标准体系", "标准化", "双碳", "碳达峰", "碳中和",
        "核准", "备案", "平价上网", "新政", "专项行动", "实景实训", "吹风",
    ],
    "TECH_BREAKTHROUGH": [
        "技术", "突破", "首发", "首次", "亮相", "GTC", "量产", "ADS", "天神之眼", "智驾", "算法",
        "刀片电池", "超级电驱", "DE-i", "CPO", "NPO", "1.6T", "800G", "400G", "结构迁移",
        "光引擎", "算电协同", "具身智能", "人形机器人", "脑机接口", "标准体系（2026 版）",
    ],
    "INDUSTRY_UPGRADE": [
        "结构迁移", "升级", "渗透率", "国产化", "规模化", "代际", "产业链", "环节", "全链条",
        "生态", "一体化", "扩围", "迁移", "供应链", "国产替代",
    ],
    "DEMAND_SURGE": [
        "需求", "订单", "销量", "出货", "装机", "景气", "放量", "增长", "翻倍", "出口", "刚需",
        "刚", "营收", "净利润", "业绩", "并网", "招标", "采购", "付费", "试运营", "客座率",
    ],
    "SUPPLY_CONTRACTION": [
        "产能", "供给", "过剩", "涨价", "价格", "库存", "缺芯", "出清", "挤压", "利润", "售价",
        "降价", "成本", "硅料", "多晶硅", "限产",
    ],
    "VALUATION_RESET": [
        "估值", "低估值", "修复", "估值杀", "泡沫", "破万亿", "市值", "倍", "x ", "抱团", "高估值",
        "虹吸", "风格",
    ],
    "CYCLE_REVERSAL": [
        "见顶", "见底", "退潮", "衰减", "回调", "反转", "结束", "出清完成", "分化", "回落", "回撤",
        "震荡", "亏钱效应", "断板", "跌停", "低点", "高点",
    ],
    "EVENT_CATALYST": [
        "发布会", "上市", "展会", "催化", "开工", "启动仪式", "峰会", "论坛", "大会", "嘉年华",
        "跑出圈", "中标", "获批",
    ],
}

# 纯非机制表述（→ NOT_AVAILABLE）
NON_MECHANISM = ["unknown", "暂无", "未知", "无（", "获利盘", "暂定", "（暂定）"]

# ★ §十五：价格 / 行情**结果**描述 —— **不得**作为 driver（禁止用结果变量反推机制）
PRICE_ACTION = [
    "涨停", "跌停", "连板", "20cm", "天地板", "断板", "涨", "跌", "走强", "活跃", "爆发",
    "大涨", "回调", "调整", "见顶", "见底", "回撤", "新高", "低点", "高点", "板块", "指数",
    "市值", "涨幅", "倍", "板",
]
# 驱动相位（用于 driver 比较）：start + accelerator = 「什么推动了该周期」
DRIVING_BUCKETS = ("start", "accelerator")
# 终结相位：turning + ending = 「什么终结了该周期」（**不与 driver 混用**）
TERMINAL_BUCKETS = ("turning", "ending")

REF_RE = re.compile(r"(EV-[A-Z0-9\-]+|E-[A-Z0-9\-]+|S-[A-Z0-9\-]+)")

# ---------------------------------------------------------------- 输入
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
EV = {e["event_id"]: e for e in (exp.get("events") or [])}
SE = {s["security_id"]: s for s in (exp.get("securities") or [])}
ALL_OBJ = exp["campaigns"] + exp["research_candidates"]


def oid(o):
    return o.get("campaign_id") or o.get("research_candidate_id")


def macro_theme(o):
    t = next((t for t in (o.get("themes") or [])
              if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None)
    return t["name"] if t else None


# ---------------------------------------------------------------- 逐文本映射
ledger = []
for o in ALL_OBJ:
    cid = oid(o)
    for bucket in ("start", "accelerator", "turning", "ending"):
        for idx, text in enumerate((o.get("drivers") or {}).get(bucket) or []):
            t = str(text)
            low = t.lower()
            hits = []
            for canon, kws in RULES.items():
                for kw in kws:
                    if kw in t or kw.lower() in low:
                        hits.append(canon)
                        break
            hits = [h for h in CANONICAL_DRIVERS if h in hits]
            refs = sorted(set(REF_RE.findall(t)))
            ev_ids = [r for r in refs if r.startswith("EV-")]
            ev_src = []
            for e in ev_ids:
                ev = EV.get(e)
                if ev:
                    ev_src.append({"event_id": e, "date": ev.get("date"),
                                   "event_type": ev.get("event_type")})

            if not t.strip() or any(n in t for n in NON_MECHANISM):
                status, canon = "NOT_AVAILABLE", None
                reason = "文本为空或纯非机制表述（不含可编码的驱动机制）"
            elif (len(hits) == 0 and any(p in t for p in PRICE_ACTION)) \
                    or (len(hits) == 1 and hits[0] == "CYCLE_REVERSAL"
                        and any(p in t for p in PRICE_ACTION) and not refs):
                # ★ §十五：价格/行情结果描述 → 不得作为 driver
                status, canon = "NOT_AVAILABLE", None
                reason = ("价格/行情**结果**描述（非机制）→ 按 §十五 不得作为 driver，"
                          "标记 NOT_AVAILABLE 而非 UNKNOWN")
            elif len(hits) == 0:
                status, canon = "UNKNOWN", None
                reason = "有文本但未命中任何显式规则 → 不强行归类"
            elif len(hits) == 1:
                canon = hits[0]
                if refs:
                    status = "DIRECT"
                    reason = f"命中唯一规则 {canon}，且文本可追溯至 {', '.join(refs)}"
                else:
                    status = "DERIVED"
                    reason = f"命中唯一规则 {canon}，但文本未给出 evidence/event/source 引用 → 降为 DERIVED"
            elif len(hits) >= 4:
                status, canon = "AMBIGUOUS", None
                reason = f"命中 {len(hits)} 条规则（{', '.join(hits)}）→ 无法收敛，保留 AMBIGUOUS，不硬拆"
            else:
                status, canon = "DERIVED", None
                reason = f"命中 {len(hits)} 条规则（{', '.join(hits)}）→ 需综合判断，标记 DERIVED"

            ledger.append({
                "cycle_id": cid, "macro_theme": macro_theme(o), "bucket": bucket, "seq": idx + 1,
                "raw_driver": t, "canonical_driver": canon, "mapping_status": status,
                "matched_rules": hits, "references": refs,
                "event_refs": ev_src,
                "source_type": "event_reference" if refs else "narrative_text",
                "reason": reason,
            })

# ---------------------------------------------------------------- 汇总
by_status = collections.Counter(x["mapping_status"] for x in ledger)
by_canon = collections.Counter(x["canonical_driver"] for x in ledger if x["canonical_driver"])

# 每 cycle 的 canonical driver 集合（DIRECT/DERIVED 才计入）
# ★ 驱动相位（start/accelerator）= 「什么推动了该周期」→ 用于 driver 比较
#   终结相位（turning/ending）= 「什么终结了该周期」→ 单独记 terminal_mechanisms，**不与 driver 混用**
cycle_canon = collections.defaultdict(lambda: collections.defaultdict(set))
cycle_terminal = collections.defaultdict(lambda: collections.defaultdict(set))
for x in ledger:
    if x["mapping_status"] in ("DIRECT", "DERIVED") and x["canonical_driver"]:
        tgt = cycle_canon if x["bucket"] in DRIVING_BUCKETS else cycle_terminal
        tgt[x["cycle_id"]][x["canonical_driver"]].add(x["mapping_status"])

per_cycle = []
for o in ALL_OBJ:
    cid = oid(o)
    rows = [x for x in ledger if x["cycle_id"] == cid]
    st = collections.Counter(r["mapping_status"] for r in rows)
    cd = cycle_canon.get(cid, {})
    tm = cycle_terminal.get(cid, {})
    drv_rows = [r for r in rows if r["bucket"] in DRIVING_BUCKETS]
    drv_st = collections.Counter(r["mapping_status"] for r in drv_rows)
    per_cycle.append({
        "cycle_id": cid, "macro_theme": macro_theme(o),
        "raw_driver_count": len(rows),
        "driving_raw_count": len(drv_rows),
        "canonical_drivers": sorted(cd),
        "canonical_driver_count": len(cd),
        "terminal_mechanisms": sorted(tm),
        "terminal_mechanism_count": len(tm),
        "direct_count": st["DIRECT"], "derived_count": st["DERIVED"],
        "ambiguous_count": st["AMBIGUOUS"], "unknown_count": st["UNKNOWN"],
        "not_available_count": st["NOT_AVAILABLE"],
        "driving_direct_count": drv_st["DIRECT"], "driving_derived_count": drv_st["DERIVED"],
        "mapping_completeness": round(
            (st["DIRECT"] + st["DERIVED"]) / len(rows), 4) if rows else 0.0,
        "driving_mapping_completeness": round(
            (drv_st["DIRECT"] + drv_st["DERIVED"]) / len(drv_rows), 4) if drv_rows else 0.0,
    })

# 驱动相位的 canonical 分布（用于与 candidate narrative_types 比较）
driving_by_canon = collections.Counter(
    x["canonical_driver"] for x in ledger
    if x["canonical_driver"] and x["bucket"] in DRIVING_BUCKETS
    and x["mapping_status"] in ("DIRECT", "DERIVED"))

cand_narr = {c["candidate_id"]: sorted(c.get("narrative_types") or []) for c in cur["candidates"]}
cand_narr_cnt = collections.Counter(n for v in cand_narr.values() for n in v)

canon_doc = {
    "artifact": "historical_driver_canonicalization", "artifact_version": "0.1",
    "generated_by": "research/scripts/canonicalize_historical_drivers_v0_1.py",
    "position": ("Research-only 派生层 —— **不进入** DB / schema.sql / timeline_export_v1.json / "
                 "contracts / src。**不修改**历史原始 driver 文本、**不修改** candidate driver。"),
    "not_a": ["similarity score", "ranking", "weighted score", "best driver match",
              "event_type→driver 硬映射", "价格结果反推 driver"],
    "semantic_rules": {
        "event_type_is_not_driver": ("Event Type = 发生了什么类型的事件；"
                                     "Driver = 该周期由什么机制推动。两者**独立**，不得一对一映射。"),
        "forbidden_inferences": [
            "event_type==industry → DEMAND_IMPROVEMENT",
            "event_type==company → EARNINGS_CONFIRMATION",
            "event_type==capital → CAPEX_EXPANSION",
            "market_series rising → SENTIMENT_POSITIVE",
            "价格涨跌 / 结果变量 → 任何 driver",
        ],
        "sentiment": ("`SENTIMENT` 在历史侧**无可可靠结构化来源** → 保持 **NOT_AVAILABLE**。"
                      "**缺失 sentiment ≠ 没有 sentiment**，而是当前资料不足以可靠编码。"),
        "driver_vs_category": ("candidate 侧 `drivers[].category`（POLICY/INDUSTRY/CAPITAL/…）"
                               "是**来源/类别轴**，不是机制轴；机制轴是 `narrative_types`"
                               "（= 本 artifact 的 canonical vocabulary）。"),
    },
    "canonical_vocabulary": {
        "source": "research/current/schema.json:definitions.narrativeType（**复用，未新造**）",
        "values": CANONICAL_DRIVERS,
        "candidate_side_usage": cand_narr,
        "candidate_side_frequency": dict(cand_narr_cnt),
        "historical_not_available": [d for d in CANONICAL_DRIVERS
                                     if d not in by_canon and d not in cand_narr_cnt],
    },
    "rules": {k: v for k, v in RULES.items()},
    "non_mechanism_markers": NON_MECHANISM,
    "price_action_markers": PRICE_ACTION,
    "bucket_semantics": {
        "driving": list(DRIVING_BUCKETS),
        "terminal": list(TERMINAL_BUCKETS),
        "rule": ("**driver 比较只用 driving（start + accelerator）** —— 即「什么推动了该周期」；"
                 "turning + ending 记录为 `terminal_mechanisms`（「什么终结了该周期」），"
                 "**不与 driver 混用**。"),
        "why": ("v0.1 首次运行时 `CYCLE_REVERSAL` 命中 26 条中 25 条来自 turning/ending —— "
                "那是**周期终结**描述，不是驱动机制。已按相位拆分。"),
    },
    "summary": {
        "historical_raw_driver_count": len(ledger),
        "historical_canonical_driver_count": len(by_canon),
        "driving_raw_count": sum(1 for x in ledger if x["bucket"] in DRIVING_BUCKETS),
        "driving_canonical_driver_count": len(driving_by_canon),
        "by_mapping_status": {k: by_status[k] for k in
                              ("DIRECT", "DERIVED", "AMBIGUOUS", "UNKNOWN", "NOT_AVAILABLE")},
        "by_canonical_driver": dict(by_canon),
        "driving_by_canonical_driver": dict(driving_by_canon),
        "objects": len(ALL_OBJ),
    },
    "per_cycle": per_cycle,
}
ledger_doc = {
    "artifact": "historical_driver_evidence_ledger", "artifact_version": "0.1",
    "generated_by": "research/scripts/canonicalize_historical_drivers_v0_1.py",
    "position": "Research-only —— 每条 mapping 一行，可追溯 raw_driver → canonical_driver → references。",
    "field_spec": ["cycle_id", "macro_theme", "bucket", "raw_driver", "canonical_driver",
                   "mapping_status", "matched_rules", "references", "source_type", "reason"],
    "entries": ledger,
}

canon_body = json.dumps(canon_doc, ensure_ascii=False, indent=1) + "\n"
ledger_body = json.dumps(ledger_doc, ensure_ascii=False, indent=1) + "\n"

if CHECK:
    for p, b in ((OUT_CANON, canon_body), (OUT_LEDGER, ledger_body)):
        if not os.path.exists(p):
            raise SystemExit(f"FAIL —— 产物不存在：{p}")
        if io.open(p, encoding="utf-8").read() != b:
            raise SystemExit(f"FAIL —— 与重算结果不一致：{p}")
    print("PASS —— 两份产物与重算结果逐字节一致（deterministic）。")
else:
    for p, b in ((OUT_CANON, canon_body), (OUT_LEDGER, ledger_body)):
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(b)
        print("written", p)

print()
print("raw driver 文本:", len(ledger))
print("mapping_status:", dict(by_status))
print("canonical driver 分布:", dict(by_canon))
print("candidate narrative_types:", dict(cand_narr_cnt))
print()
print("=== 每 cycle canonical drivers ===")
for r in per_cycle:
    print(f"  {r['cycle_id']:24s} raw={r['raw_driver_count']:2d} canon={r['canonical_driver_count']} "
          f"D{r['direct_count']}/V{r['derived_count']}/A{r['ambiguous_count']}/U{r['unknown_count']}/NA{r['not_available_count']} "
          f"{r['canonical_drivers']}")
