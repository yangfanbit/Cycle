#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""validate_governance_gates.py —— 校验 `governance-gates-v0.1` 分类清单的一致性（**只读**）。

检查项（G1-1 / G1-3 / G1-5 / G2-1）：
  V1  清单 ruleset 与规则文档版本一致
  V2  清单覆盖 DB 中**全部** campaigns，且无多余条目
  V3  `market_evidence_state` ∈ {A_SHARE_MARKET, INDUSTRY_COMPANY_ONLY, NONE}
  V4  `beta_level` ∈ {0,1,2,3}；且 L2/L3 **必须有** `beta_level_basis` 说明（防虚构）
  V5  `peak.state` / `end.state` ∈ {EXACT, WINDOW, NULL}
  V6  state 与 DB 日期一致：NULL ⇔ peak_date/end_date 为空；非 NULL ⇒ 日期非空
  V7  `alternative` 若存在必须带 `basis`（来源与理由）
  V8  G1-5：`strength` 不得为 `weak`（违例记为 **WARN**，不阻断 —— 属历史残留待独立修复）
  V9  `result='weak'` 的语义声明一致（result_is_weak 与 DB 一致）
  V10 清单与 DB 的 strength / result / classification / date_confidence 一致（防清单漂移）
  V11 无重复 campaign_id

退出码：0 = PASS（可有 WARN）；1 = FAIL。
用法：python research/scripts/validate_governance_gates.py
"""

from __future__ import annotations

import io
import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")
DOC = os.path.join(ROOT, "research", "research", "reports", "governance_classification_v0_1.json")

EXPECT_RULESET = "governance-gates-v0.1"
MES_OK = {"A_SHARE_MARKET", "INDUSTRY_COMPANY_ONLY", "NONE"}
STATE_OK = {"EXACT", "WINDOW", "NULL"}
BETA_OK = {0, 1, 2, 3}


def main():
    if not os.path.exists(DOC):
        print("FAIL  缺少清单: %s" % DOC)
        return 1
    doc = json.load(io.open(DOC, encoding="utf-8"))
    items = doc.get("campaigns") or []
    fails, warns = [], []

    def fail(code, msg):
        fails.append("%s  %s" % (code, msg))

    def warn(code, msg):
        warns.append("%s  %s" % (code, msg))

    # V1
    if doc.get("ruleset") != EXPECT_RULESET:
        fail("V1", "ruleset=%r，期望 %r" % (doc.get("ruleset"), EXPECT_RULESET))

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    db = {r["campaign_id"]: r for r in cur.execute(
        "SELECT campaign_id, peak_date, end_date, strength, result, classification, date_confidence FROM campaigns")}

    ids = [i.get("campaign_id") for i in items]
    # V11
    dup = {x for x in ids if ids.count(x) > 1}
    if dup:
        fail("V11", "重复 campaign_id: %s" % sorted(dup))
    # V2
    missing = sorted(set(db) - set(ids))
    extra = sorted(set(ids) - set(db))
    if missing:
        fail("V2", "清单缺失 %d 个 campaign: %s" % (len(missing), missing[:5]))
    if extra:
        fail("V2", "清单多余 %d 个 campaign: %s" % (len(extra), extra[:5]))

    for i in items:
        cid = i.get("campaign_id")
        r = db.get(cid)
        if not r:
            continue
        # V3
        if i.get("market_evidence_state") not in MES_OK:
            fail("V3", "%s market_evidence_state=%r" % (cid, i.get("market_evidence_state")))
        # V4
        bl = i.get("beta_level")
        if bl not in BETA_OK:
            fail("V4", "%s beta_level=%r" % (cid, bl))
        elif bl in (2, 3) and not (i.get("beta_level_basis") or "").strip():
            fail("V4", "%s beta_level=%s 但缺 basis（禁止虚构 L2/L3）" % (cid, bl))
        # V5 / V6
        for role in ("peak", "end"):
            o = i.get(role) or {}
            st = o.get("state")
            if st not in STATE_OK:
                fail("V5", "%s %s.state=%r" % (cid, role, st))
                continue
            dbv = r["peak_date"] if role == "peak" else r["end_date"]
            if st == "NULL" and dbv is not None:
                fail("V6", "%s %s.state=NULL 但 DB 日期=%s" % (cid, role, dbv))
            if st != "NULL" and dbv is None:
                fail("V6", "%s %s.state=%s 但 DB 日期为空" % (cid, role, st))
            if o.get("date") != dbv:
                fail("V6", "%s %s.date=%r 与 DB %r 不一致" % (cid, role, o.get("date"), dbv))
            # V7
            alt = o.get("alternative")
            if alt is not None:
                if not isinstance(alt, dict) or not (alt.get("basis") or "").strip():
                    fail("V7", "%s %s.alternative 缺 basis（来源与理由）" % (cid, role))
        # V8 / V9
        rw = i.get("result_weak_semantics") or {}
        if r["strength"] == "weak":
            if not rw.get("strength_is_weak"):
                fail("V8", "%s DB strength=weak 但清单未标记" % cid)
            else:
                warn("V8", "%s strength='weak' 违反 governance-gates-v0.1（weak 只能出现在 result）—— 历史残留，待独立修复" % cid)
        if bool(rw.get("result_is_weak")) != (r["result"] == "weak"):
            fail("V9", "%s result_is_weak=%r 与 DB result=%r 不一致" % (cid, rw.get("result_is_weak"), r["result"]))
        # V10
        for k, col in (("strength", "strength"), ("result", "result"),
                       ("classification", "classification"), ("date_confidence", "date_confidence")):
            if i.get(k) != r[col]:
                fail("V10", "%s %s=%r 与 DB %r 不一致" % (cid, k, i.get(k), r[col]))

    conn.close()

    print("=== validate_governance_gates.py（%s）===" % EXPECT_RULESET)
    print("清单条目: %d | DB campaigns: %d" % (len(items), len(db)))
    print("-" * 62)
    for w in warns:
        print("WARN  " + w)
    for f in fails:
        print("FAIL  " + f)
    if warns:
        print("-" * 62)
    print()
    print("结果: %s（FAIL %d / WARN %d）" % ("PASS" if not fails else "FAIL", len(fails), len(warns)))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
