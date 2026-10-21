#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_participant_evidence_v0_1.py —— 参与者**证据维度**结构化产物（v0.28）。

## 为什么需要它

历史地图里每只股票身上混着**四种不同性质**的信息，此前只能从自由文本（`rationale` /
`business_mechanism` / `registry_role`）里读出来：

1. 它**参与过**当次行情吗？（同期报道点名 / 报道给出涨幅 / 报道明确涨停）
2. 它的业务与**题材机制**有关吗？（有机制说明 ≠ 驱动了行情）
3. 它在 **Research 对象**里被登记成什么角色？（`leader` / `representative`… —— 这是
   研究对象的内部登记，**不等于**历史炒作龙头）
4. 它是**反例** / **不同机制轴** / **证据不足**吗？

本脚本把四者拆成**独立字段**，每条都带**依据**与**来源**，并显式列出**无法判定**的项。
★ 不新增任何历史事实：只把既有字段（`evidence_level` / `reported_move` / `business_mechanism` /
`registry_role` / `category`）转成机器可读的维度，并**核对 `registry_role` 是否与库内
`campaign_securities.role` 一致**。

## 三维度定义（写进产物合同）

- `market_participation`：**同期报道**能证明的市场表现。
  `REPORTED_LIMIT_UP`（报道明确涨停/连板）> `REPORTED_DAILY_GAIN`（报道给出**当日**涨幅）
  > `REPORTED_WINDOW_GAIN`（报道给出**区间**涨幅）> `REPORTED_NAMED_ONLY`（报道点名但未给涨幅）
  > `NO_REPORTED_EVIDENCE`（本轮**未找到**点名报道 —— **不等于**当日没涨）
  > `UNKNOWN`（证据不足，无法判断）。
- `mechanism_relation`：业务与题材机制的关系。
  `DIRECT`（有机制说明）/ `SPILLOVER`（产业链扩散）/ `UNSPECIFIED`（参与行情但未登记机制说明）
  / `DIFFERENT_AXIS`（反例：机制轴不同）/ `UNKNOWN`。
- `registry_role`：**Research 对象内部登记**的角色 + 出处。
  `VERIFIED_DB`（与 `campaign_securities.role` 逐字一致）/ `SECURITY_IN_OBJECT_ROLE_UNVERIFIED`
  （RC 无角色表：只能确认证券属于该对象，**角色本身无机器可核来源**）/ `null`。

★ `study_standing`（INCLUDED / COUNTER_EXAMPLE / INSUFFICIENT）来自既有 `category`，单独一列。

## 用法

    python research/scripts/build_participant_evidence_v0_1.py --check    # 只读（CI 门禁）
    python research/scripts/build_participant_evidence_v0_1.py --write    # 生成 v0_1（拒绝覆盖）
    python research/scripts/build_participant_evidence_v0_1.py --write --version 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
INDEX_PATH = os.path.join(CURRENT, "historical_event_maps_index.json")
EXPORT_PATH = os.path.join(REPO, "exports", "timeline_export_v1.json")
GENERATED_AT = "2026-10-21"

LIMIT_UP_RE = re.compile(r"涨停|(?:\d+\s*天\s*\d+\s*板)|(?:\d+\s*连板)")
WINDOW_RE = re.compile(r"交易日|(?:\d+\s*天)")
GAIN_RE = re.compile(r"[+\-−]?\s*\d+(?:\.\d+)?\s*%|涨逾|涨超|涨幅")
# ★★ 角色线索可能只写在 `rationale` 里（如「库内 Campaign `C-2023-POWEROP-THERMAL` 登记的标的（role=leader）」）
ROLE_IN_TEXT_RE = re.compile(r"role\s*=\s*(leader|second_leader|representative|follow)")
OBJ_IN_TEXT_RE = re.compile(r"`((?:C|RC)-\d{4}-[A-Z0-9\-]+)`")

# ★ category → 研究立场（三种纳入类别 = INCLUDED）
STUDY_STANDING_OF = {
    "MARKET_PARTICIPANT": "INCLUDED",
    "MECHANISM_DIRECT": "INCLUDED",
    "SPILLOVER": "INCLUDED",
    "COUNTER_EXAMPLE": "COUNTER_EXAMPLE",
    "INSUFFICIENT": "INSUFFICIENT",
}


def load_index():
    return json.load(open(INDEX_PATH, encoding="utf-8"))


def load_theme_docs(index):
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if os.path.exists(path):
            yield entry, json.load(open(path, encoding="utf-8"))


def load_campaign_roles(conn):
    return {(c, s): r for c, s, r in
            conn.execute("SELECT campaign_id, security_id, role FROM campaign_securities")}


def load_rc_securities():
    doc = json.load(open(EXPORT_PATH, encoding="utf-8"))
    out = {}
    for rc in doc.get("research_candidates") or []:
        oid = rc.get("campaign_id") or rc.get("object_id")
        out[oid] = set(rc.get("security_ids") or [])
    return out


def market_participation(p: dict) -> dict:
    """同期报道能证明什么 —— **只按字段实况分类，不推测**。"""
    move = (p.get("reported_move") or "").strip()
    lvl = p.get("evidence_level")
    if move:
        if LIMIT_UP_RE.search(move):
            return {"status": "REPORTED_LIMIT_UP", "reported_move": move,
                    "basis": "同期报道明确涨停 / 连板"}
        if WINDOW_RE.search(move) and GAIN_RE.search(move):
            return {"status": "REPORTED_WINDOW_GAIN", "reported_move": move,
                    "basis": "同期报道给出**区间**涨幅（非单日）"}
        if GAIN_RE.search(move):
            return {"status": "REPORTED_DAILY_GAIN", "reported_move": move,
                    "basis": "同期报道给出涨幅"}
        return {"status": "REPORTED_NAMED_ONLY", "reported_move": move,
                "basis": "同期报道点名（未给出可解析涨幅）"}
    if lvl == "REPORT_NAMED":
        return {"status": "REPORTED_NAMED_ONLY", "reported_move": None,
                "basis": "同期报道点名（未给出涨幅）"}
    if p.get("category") == "COUNTER_EXAMPLE":
        return {"status": "NO_REPORTED_EVIDENCE", "reported_move": None,
                "basis": "反例：本轮未找到其参与当次行情的点名报道"}
    if p.get("category") == "INSUFFICIENT":
        return {"status": "UNKNOWN", "reported_move": None,
                "basis": "证据不足，无法判断是否参与当次行情"}
    return {"status": "NO_REPORTED_EVIDENCE", "reported_move": None,
            "basis": "★ 本轮**未找到**点名报道 —— 不代表当日未上涨，也不代表不是参与者"}


def mechanism_relation(p: dict) -> dict:
    cat = p.get("category")
    mech = p.get("business_mechanism")
    if cat == "COUNTER_EXAMPLE":
        return {"status": "DIFFERENT_AXIS", "basis": "反例：机制轴与本题材不同",
                "caveat": p.get("business_mechanism_caveat")}
    if cat == "INSUFFICIENT":
        return {"status": "UNKNOWN", "basis": "证据不足，机制关系未确认", "caveat": None}
    if cat == "SPILLOVER":
        return {"status": "SPILLOVER", "basis": mech or "产业链扩散（未登记逐条说明）",
                "caveat": p.get("business_mechanism_caveat")}
    if mech:
        return {"status": "DIRECT", "basis": mech,
                "caveat": p.get("business_mechanism_caveat")}
    return {"status": "UNSPECIFIED", "basis": "参与行情但未登记机制说明",
            "caveat": None}


def registry_role_of(p: dict, object_id, object_kind, roles, rc_secs) -> dict | None:
    """对象登记角色 + 出处。

    ★ v0.28 修：角色线索**可能只写在 `rationale` 里**（「…登记的标的（role=leader）」）。
      此时把它解析出来，但**必须**与库内 `campaign_securities` 对齐才算可核；
      对不上就如实标 `SECURITY_NOT_IN_OBJECT` / `ROLE_MISMATCH`，绝不直接采信文本。
    """
    role = p.get("registry_role")
    role_src = "participant.registry_role"
    if not role:
        m = ROLE_IN_TEXT_RE.search(p.get("rationale") or "")
        if not m:
            return None
        role = m.group(1)
        role_src = "participant.rationale 文本"
        if not object_id:
            om = OBJ_IN_TEXT_RE.search(p.get("rationale") or "")
            if om:
                object_id = om.group(1)
                object_kind = "campaign" if object_id.startswith("C-") else "research_candidate"
    sid = p["security_id"]
    if object_kind == "campaign" and object_id:
        dbv = roles.get((object_id, sid))
        if dbv == role:
            return {"role": role, "object_id": object_id, "object_kind": object_kind,
                    "verification": "VERIFIED_DB", "role_source": role_src,
                    "source": "cycle_research.db · campaign_securities.role（逐字一致；"
                              "角色声明来自 %s）" % role_src}
        if dbv is None:
            return {"role": role, "object_id": object_id, "object_kind": object_kind,
                    "verification": "SECURITY_NOT_IN_OBJECT", "role_source": role_src,
                    "source": "库内该对象无此证券登记 → 角色**无机器可核来源**"}
        return {"role": role, "object_id": object_id, "object_kind": object_kind,
                "verification": "ROLE_MISMATCH", "role_source": role_src,
                "source": "库内为 %s，文档写 %s" % (dbv, role)}
    # Research Candidate：库内无角色表，只能确认「证券属于该对象」
    if object_id and sid in (rc_secs.get(object_id) or set()):
        return {"role": role, "object_id": object_id, "object_kind": object_kind,
                "verification": "SECURITY_IN_OBJECT_ROLE_UNVERIFIED", "role_source": role_src,
                "source": "RC 无角色表：仅能确认证券属于该对象；**角色本身无机器可核来源**"}
    return {"role": role, "object_id": object_id, "object_kind": object_kind,
            "verification": "UNSOURCED", "role_source": role_src,
            "source": "未能在库内或导出中确认该证券属于该对象"}


def unknowns_of(p: dict, mp: dict, mr: dict, rr) -> list:
    out = []
    if mp["status"] in ("NO_REPORTED_EVIDENCE", "UNKNOWN"):
        out.append({"field": "market_participation",
                    "reason": "无同期报道可证明其在当次行情中的表现"
                              "（≠ 当日未上涨；需补当时行情报道或交易所披露）"})
    if mr["status"] in ("UNSPECIFIED", "UNKNOWN"):
        out.append({"field": "mechanism_relation",
                    "reason": "未登记业务与题材机制的逐条说明"})
    if rr and rr["verification"] != "VERIFIED_DB":
        out.append({"field": "registry_role",
                    "reason": "角色无机器可核来源（%s）—— 只能作为**对象内部登记**引用，"
                              "不得当作历史炒作龙头" % rr["verification"]})
    if not rr:
        out.append({"field": "registry_role",
                    "reason": "该证券未在任何 Research 对象中登记角色"})
    return out


def build(conn) -> dict:
    index = load_index()
    roles = load_campaign_roles(conn)
    rc_secs = load_rc_securities()
    events = {}
    tally = {"market": {}, "mechanism": {}, "registry": {}, "standing": {}}
    for entry, doc in load_theme_docs(index):
        for e in doc.get("events") or []:
            cf = e.get("campaign_facts") or {}
            oid = cf.get("object_id") or cf.get("campaign_id")
            kind = cf.get("object_kind") or ("campaign" if cf.get("campaign_id") else None)
            parts = {}
            for p in e.get("participants") or []:
                mp = market_participation(p)
                mr = mechanism_relation(p)
                rr = registry_role_of(p, oid, kind, roles, rc_secs)
                parts[p["security_id"]] = {
                    "name": p.get("name"),
                    "ticker": p.get("ticker"),
                    "evidence_level": p.get("evidence_level"),
                    # ★ 三种「纳入」类别都算 INCLUDED；只有反例 / 证据不足另列
                    "study_standing": STUDY_STANDING_OF.get(p.get("category"), "UNKNOWN"),
                    "market_participation": mp,
                    "mechanism_relation": mr,
                    "registry_role": rr,
                    "source_text": p.get("source"),
                    "unknowns": unknowns_of(p, mp, mr, rr),
                }
                tally["market"][mp["status"]] = tally["market"].get(mp["status"], 0) + 1
                tally["mechanism"][mr["status"]] = tally["mechanism"].get(mr["status"], 0) + 1
                v = rr["verification"] if rr else "NO_REGISTRY_ROLE"
                tally["registry"][v] = tally["registry"].get(v, 0) + 1
                st = parts[p["security_id"]]["study_standing"]
                tally["standing"][st] = tally["standing"].get(st, 0) + 1
            events[e["event_id"]] = {
                "theme_id": entry["theme_id"],
                "theme_file": entry["file"],
                "object_id": oid,
                "object_kind": kind,
                "participants": parts,
            }
    return {
        "artifact": "participant_evidence",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_participant_evidence_v0_1.py",
        "supersedes": None,
        "participant_evidence_contract": {
            "version": "participant_evidence_v1",
            "purpose": "把「同期市场表现 / 业务机制关系 / Research 对象登记角色 / 研究立场 / 无法判定」"
                       "拆成互不冒充的独立维度，并逐条给出依据与出处",
            "market_participation": {
                "REPORTED_LIMIT_UP": "同期报道明确涨停 / 连板（最强，但仍只是「被报道点名」级别的证据）",
                "REPORTED_DAILY_GAIN": "同期报道给出当日涨幅",
                "REPORTED_WINDOW_GAIN": "同期报道给出**区间**涨幅（非单日）",
                "REPORTED_NAMED_ONLY": "同期报道点名但未给涨幅",
                "NO_REPORTED_EVIDENCE": "★ 本轮未找到点名报道 —— **不等于**当日没涨、**不等于**不是参与者",
                "UNKNOWN": "证据不足，无法判断",
            },
            "mechanism_relation": {
                "DIRECT": "有业务机制说明（业务与题材机制有关 ≠ 驱动了当次行情）",
                "SPILLOVER": "产业链扩散",
                "UNSPECIFIED": "参与行情但未登记机制说明",
                "DIFFERENT_AXIS": "反例：机制轴不同",
                "UNKNOWN": "证据不足",
            },
            "registry_role": {
                "VERIFIED_DB": "与 cycle_research.db · campaign_securities.role 逐字一致",
                "SECURITY_IN_OBJECT_ROLE_UNVERIFIED": "RC 无角色表：只能确认证券属于该对象，角色本身无机器可核来源",
                "SECURITY_NOT_IN_OBJECT": "库内该对象无此证券登记",
                "ROLE_MISMATCH": "库内角色与文档不一致（需人工裁定）",
                "UNSOURCED": "未能在库内或导出中确认归属",
                "★ 语义": "这是**Research 对象内部登记**，不是「历史炒作龙头」；两者必须分开显示",
            },
            "study_standing": "INCLUDED / COUNTER_EXAMPLE / INSUFFICIENT（来自既有 category）",
            "must_not": [
                "不得把 registry_role=leader 当作「当时的龙头」",
                "不得把 BUSINESS_VERIFIED 当作「参与过当次行情」",
                "不得把 NO_REPORTED_EVIDENCE 当作「当日没涨」",
                "不得用事后涨幅反推角色",
            ],
        },
        "summary": {
            "events": len(events),
            "participants": sum(len(v["participants"]) for v in events.values()),
            "market_participation": tally["market"],
            "mechanism_relation": tally["mechanism"],
            "registry_role_verification": tally["registry"],
            "study_standing": tally["standing"],
        },
        "events": events,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="构建参与者证据维度产物")
    ap.add_argument("--check", action="store_true", help="只读：重新推导并与已发布产物比对")
    ap.add_argument("--write", action="store_true", help="写入新版本（拒绝覆盖）")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)

    conn = db.connect()
    try:
        doc = build(conn)
    finally:
        conn.close()

    out = os.path.join(CURRENT, "participant_evidence_v0_%d.json" % a.version)
    if a.check:
        if not os.path.exists(out):
            print("FAIL: 产物不存在：%s" % os.path.relpath(out, REPO))
            return 1
        cur = json.load(open(out, encoding="utf-8"))
        diffs = []
        if cur.get("events") != doc["events"]:
            for eid, ev in doc["events"].items():
                if cur["events"].get(eid) != ev:
                    diffs.append(eid)
            for eid in cur["events"]:
                if eid not in doc["events"]:
                    diffs.append(eid)
        if cur.get("summary") != doc["summary"]:
            diffs.append("<summary>")
        if diffs:
            print("FAIL: 产物与重新推导不一致（%d 处）：%s" % (len(diffs), ", ".join(diffs[:8])))
            return 1
        print("PASS: 参与者证据产物与重新推导一致（%d 事件 / %d 条参与者记录）"
              % (doc["summary"]["events"], doc["summary"]["participants"]))
        return 0

    if not a.write:
        print("用法：--check 或 --write [--version N]")
        return 2
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    doc["artifact_version"] = "0.%d" % a.version
    if a.version > 1:
        doc["supersedes"] = "research/current/participant_evidence_v0_%d.json" % (a.version - 1)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    s = doc["summary"]
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("  %d 事件 / %d 条参与者记录" % (s["events"], s["participants"]))
    print("  同期市场表现: %s" % s["market_participation"])
    print("  机制关系: %s" % s["mechanism_relation"])
    print("  对象登记核验: %s" % s["registry_role_verification"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
