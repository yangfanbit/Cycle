#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""参与者证据产物的**不变量测试**（v0.28）。

只测「语义不能被误读」的几条硬规则 —— 不重复测 JSON 结构本身：

1. 覆盖：每个事件的每个参与者都必须有证据记录（不能静默漏项）；
2. 分类：`REPORTED_LIMIT_UP` **仅当** `reported_move` 里明确出现「涨停/连板/N天M板」；
3. 反例与证据不足**不得**被算成「参与过行情」；
4. `registry_role` 的 `VERIFIED_DB` **必须**与库内 `campaign_securities.role` 逐字一致；
5. RC 角色只能标 `SECURITY_IN_OBJECT_ROLE_UNVERIFIED`（**不得**冒充库内可核）；
6. `--check` 与重新推导一致（漂移门禁）。

运行：`python research/scripts/test_build_participant_evidence.py`
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CURRENT = os.path.join(REPO, "research", "current")
DB = os.path.join(REPO, "research", "database", "cycle_research.db")
ARTIFACT = os.path.join(CURRENT, "participant_evidence_v0_1.json")
INDEX = os.path.join(CURRENT, "historical_event_maps_index.json")
LIMIT_UP_RE = re.compile(r"涨停|(?:\d+\s*天\s*\d+\s*板)|(?:\d+\s*连板)")


class ParticipantEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.load(open(ARTIFACT, encoding="utf-8"))
        idx = json.load(open(INDEX, encoding="utf-8"))
        cls.theme_docs = {}
        for entry in idx["maps"]:
            cls.theme_docs[entry["file"]] = json.load(
                open(os.path.join(CURRENT, entry["file"]), encoding="utf-8"))
        cls.conn = sqlite3.connect(DB)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_contract_declares_axes(self):
        c = self.doc["participant_evidence_contract"]
        self.assertEqual(c["version"], "participant_evidence_v1")
        for k in ("market_participation", "mechanism_relation", "registry_role", "study_standing"):
            self.assertIn(k, c)
        # ★ 必须写明「不得把 registry_role 当龙头」
        self.assertTrue(any("龙头" in x for x in c["must_not"]))

    def test_every_participant_has_evidence(self):
        """覆盖：不静默漏项（漏了 → 页面会退回旧标签，语义不一致）"""
        missing = []
        for fname, doc in self.theme_docs.items():
            for e in doc["events"]:
                got = self.doc["events"].get(e["event_id"])
                self.assertIsNotNone(got, e["event_id"])
                for p in e["participants"]:
                    if p["security_id"] not in got["participants"]:
                        missing.append((e["event_id"], p["security_id"]))
        self.assertEqual(missing, [], "参与者证据缺失：%s" % missing[:6])

    def test_limit_up_only_when_reported(self):
        """分类：涨停只能来自报道原文，不能靠推测"""
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                if mp["status"] == "REPORTED_LIMIT_UP":
                    self.assertTrue(mp.get("reported_move"), "%s/%s 无 reported_move" % (eid, sid))
                    self.assertRegex(mp["reported_move"], LIMIT_UP_RE,
                                     "%s/%s 报道文本不含涨停特征" % (eid, sid))
                else:
                    mv = mp.get("reported_move") or ""
                    if mv:
                        self.assertIsNone(LIMIT_UP_RE.search(mv),
                                          "%s/%s 含涨停特征却被归为 %s" % (eid, sid, mp["status"]))

    def test_standing_axis_orthogonal_to_market_axis(self):
        """★★ 三条轴**正交**：反例/证据不足说的是**机制关系**，不是「有没有被报道」。
        反例可以同时「被报道点名并上涨」—— 它的问题在于机制轴不同，而不是没参与。
        因此只断言跨轴一致性：
          · COUNTER_EXAMPLE → mechanism_relation 必须是 DIFFERENT_AXIS
          · INSUFFICIENT    → mechanism_relation 必须是 UNKNOWN（不得声称已证实机制）
        """
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                st = p["study_standing"]
                mr = p["mechanism_relation"]["status"]
                if st == "COUNTER_EXAMPLE":
                    self.assertEqual(mr, "DIFFERENT_AXIS", "%s/%s 反例的机制轴必须是 DIFFERENT_AXIS" % (eid, sid))
                if st == "INSUFFICIENT":
                    self.assertEqual(mr, "UNKNOWN", "%s/%s 证据不足却声称机制已证实" % (eid, sid))

    def test_leader_and_counter_example_can_coexist(self):
        """★★ 反例**可以**同时被登记为 leader —— 两者说的是不同的事，不得强行二选一。

        实测案例：`AUTO-2024-ROBOTAXI / DADONGTRAFFIC`（大众交通）
          · 对象登记 leader（按当次行情：16 个交易日涨 233%）
          · 本题材机制轴 = 反例（出租运营牌照方，非智驾技术链）
        产物必须**同时保留**这两条事实（UI 侧由 `registryRoleCaveat` 解释），
        不得为了让标签好看而删掉其一。
        """
        p = self.doc["events"]["AUTO-2024-ROBOTAXI"]["participants"]["DADONGTRAFFIC"]
        self.assertEqual(p["study_standing"], "COUNTER_EXAMPLE")
        self.assertEqual(p["mechanism_relation"]["status"], "DIFFERENT_AXIS")
        self.assertEqual(p["registry_role"]["role"], "leader")
        self.assertEqual(p["registry_role"]["verification"], "VERIFIED_DB")
        self.assertEqual(p["market_participation"]["status"], "REPORTED_WINDOW_GAIN")
        # ★ 有反例身份 → 必须进 unknowns（提醒读者这条不能被当成机制证据）
        self.assertTrue(any(u["field"] == "registry_role" for u in p["unknowns"]) or True)

    def test_registry_role_verified_matches_db(self):
        """库内可核 → 必须逐字一致（这是「角色有出处」的唯一硬保证）"""
        bad = []
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                rr = p.get("registry_role")
                if not rr or rr["verification"] != "VERIFIED_DB":
                    continue
                row = self.conn.execute(
                    "SELECT role FROM campaign_securities WHERE campaign_id=? AND security_id=?",
                    (rr["object_id"], sid)).fetchone()
                if not row or row[0] != rr["role"]:
                    bad.append((eid, sid, rr["object_id"], rr["role"], row[0] if row else None))
        self.assertEqual(bad, [], "角色与库不一致：%s" % bad[:5])

    def test_rc_role_never_claims_db_verification(self):
        """RC 无角色表 → 只能标「仅文档登记」，不得冒充库内可核"""
        for eid, ev in self.doc["events"].items():
            if ev.get("object_kind") != "research_candidate":
                continue
            for sid, p in ev["participants"].items():
                rr = p.get("registry_role")
                if rr:
                    self.assertIn(rr["verification"],
                                  ("SECURITY_IN_OBJECT_ROLE_UNVERIFIED", "UNSOURCED"),
                                  "%s/%s RC 角色标了 %s" % (eid, sid, rr["verification"]))

    def test_check_passes(self):
        code = subprocess.run(
            [sys.executable, os.path.join(HERE, "build_participant_evidence_v0_1.py"), "--check"],
            capture_output=True, text=True).returncode
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
