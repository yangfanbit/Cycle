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
ARTIFACT = os.path.join(CURRENT, "participant_evidence_v0_3.json")
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
        self.assertEqual(c["version"], "participant_evidence_v1")  # 合同名不随产物版本变
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

    def test_report_status_requires_report_source(self):
        """★★ 核心不变量：`REPORT_CONFIRMED_*` **只允许**出现在 `REPORT_*` 来源上。

        这条正是 v0.28 的缺陷：`evidence_level=REPORT_NAMED` 但 source 是
        「DB campaign_securities / 本轮研究」，却被写成「报道点名」。
        """
        bad = []
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                st, kind = mp["status"], mp["source_kind"]
                if st.startswith("REPORT_CONFIRMED_") and not kind.startswith("REPORT_"):
                    bad.append((eid, sid, st, kind))
                if kind == "DB_OR_RESEARCH_ONLY" and st.startswith("REPORT_CONFIRMED_"):
                    bad.append((eid, sid, st, kind))
                if kind == "NOT_RECORDED" and st != "NOT_RECORDED":
                    bad.append((eid, sid, st, kind))
        self.assertEqual(bad, [], "报道状态与来源类型不一致：%s" % bad[:5])

    def test_limit_up_requires_reported_move(self):
        """涨停只能来自报道原文，不能靠推测"""
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                if mp["status"] == "REPORT_CONFIRMED_LIMIT_UP":
                    self.assertTrue(mp.get("reported_move"), "%s/%s 无 reported_move" % (eid, sid))
                    self.assertRegex(mp["reported_move"], LIMIT_UP_RE,
                                     "%s/%s 报道文本不含涨停特征" % (eid, sid))
                elif mp["status"].startswith("REPORT_CONFIRMED_"):
                    # 报道类状态且给了涨幅 → 必须有出处
                    if mp.get("reported_move"):
                        self.assertTrue(mp.get("reported_move_backed"),
                                        "%s/%s 报道状态 %s 却标为无出处" % (eid, sid, mp["status"]))
                else:
                    # ★ 非报道状态却有涨跌幅文本 → **必须**标为「无报道出处」
                    if mp.get("reported_move"):
                        self.assertFalse(mp.get("reported_move_backed"),
                                         "%s/%s 状态 %s 却标成有报道出处" % (eid, sid, mp["status"]))

    def test_traceable_report_has_url_and_date(self):
        """声称有 URL 的报道，必须真的带 URL + 日期（可追溯性不能只写在文案里）"""
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                if mp["source_kind"] != "REPORT_WITH_URL":
                    continue
                rep = mp.get("report") or {}
                self.assertTrue(str(rep.get("url") or "").startswith("http"),
                                "%s/%s 声称有 URL 却没有" % (eid, sid))
                self.assertRegex(str(rep.get("published_at") or ""), r"^\d{4}-\d{2}-\d{2}$",
                                 "%s/%s 报道日期缺失或格式不对" % (eid, sid))

    def test_mechanism_status_matches_research_category(self):
        """★★ 机制关系必须来自**研究分类**，不能因 business_mechanism 非空就判直接机制。"""
        # ★ 全库建一张 (event, security) → category 的对照表（跨题材）
        cats = {}
        for doc in self.theme_docs.values():
            for e in doc["events"]:
                for p in e["participants"]:
                    cats[(e["event_id"], p["security_id"])] = p.get("category")
        bad = []
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mr = p["mechanism_relation"]["status"]
                cat = cats.get((eid, sid))
                if cat is None:
                    bad.append((eid, sid, mr, "NO_CATEGORY"))
                elif mr == "DIRECT_CONFIRMED" and cat != "MECHANISM_DIRECT":
                    bad.append((eid, sid, mr, cat))
                elif mr == "BUSINESS_DESCRIBED_UNCONFIRMED" and cat != "MARKET_PARTICIPANT":
                    bad.append((eid, sid, mr, cat))
                elif mr == "INDIRECT_CONFIRMED" and cat not in ("SPILLOVER", "MECHANISM_DIRECT"):
                    bad.append((eid, sid, mr, cat))
        self.assertEqual(bad, [], "机制状态与研究分类不一致：%s" % bad[:5])

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
        # ★ v0.29：该 +233% 来自研究记录（export securities + 公开资料），无同期报道背书
        self.assertEqual(p["market_participation"]["status"], "RESEARCH_OR_DB_ONLY")
        self.assertFalse(p["market_participation"]["reported_move_backed"])
        # ★ 反例身份必须进 unknowns 之外，还要**保留**角色出处（可核）
        self.assertEqual(p["registry_role"]["role_source"], "participant.registry_role")
        self.assertTrue(any(u["field"] == "mechanism_relation" for u in p["unknowns"])
                        or p["mechanism_relation"]["status"] == "DIFFERENT_AXIS")

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
            [sys.executable, os.path.join(HERE, "build_participant_evidence_v0_1.py"),
             "--check"],
            capture_output=True, text=True).returncode
        self.assertEqual(code, 0)


    # ---------------------------------------------------------------- v0.30 时间与归属

    def _catalyst_sources(self, eid):
        for doc in self.theme_docs.values():
            for e in doc["events"]:
                if e["event_id"] == eid:
                    return " ".join((c.get("source") or "") for c in (e.get("catalysts") or []))
        return ""

    def test_published_at_is_never_the_catalyst_fact_date(self):
        """★★ v0.30 核心不变量：报道**发布日**不得被 catalyst 的**事实日期**静默替代。

        机械判据：
          · 每条报道背书都必须写出 `published_at_source`；
          · `SOURCE_TEXT` 时，`published_at` 必须真的出现在该事件的 catalyst source 文本里；
          · `identified_date` 必须 == `published_at`。
        """
        checked = 0
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                rep = mp.get("report") or {}
                if not rep:
                    continue
                checked += 1
                self.assertIn(rep.get("published_at_source"),
                              ("SOURCE_TEXT", "INHERITED_FROM_PREVIOUS_CATALYST", "MISSING",
                               "INHERIT_WITHOUT_PREVIOUS"),
                              "%s/%s 未声明发布日来源" % (eid, sid))
                if rep.get("published_at_source") == "SOURCE_TEXT":
                    self.assertIn(rep["published_at"], self._catalyst_sources(eid),
                                  "%s/%s 声称发布日来自文本，但该日期不在任何 catalyst source 里"
                                  % (eid, sid))
                if mp.get("identified_date"):
                    self.assertEqual(mp["identified_date"], rep.get("published_at"),
                                     "%s/%s identified_date 必须等于 published_at" % (eid, sid))
        self.assertGreater(checked, 0, "没有任何报道背书记录 → 测试失效")

    def test_superfungus_dates_fixed(self):
        """★★ 已确认的错配：8 条识别日曾是 2019-04-08（catalyst 事实日），报道实际发布于 04-11。"""
        ev = self.doc["events"]["SUPERFUNGUS-2019-CANDIDA"]["participants"]
        self.assertEqual(len(ev), 8)
        for sid, p in ev.items():
            mp = p["market_participation"]
            rep = mp.get("report") or {}
            self.assertEqual(rep.get("published_at"), "2019-04-11", "%s 发布日未修正" % sid)
            self.assertEqual(mp.get("identified_date"), "2019-04-11", "%s 识别日未修正" % sid)
            self.assertIn(rep.get("fact_date"), ("2019-04-10", "2019-04-11"),
                          "%s 事实日期应保留" % sid)
            self.assertEqual(mp.get("attribution"), "NAME_IN_TEXT",
                             "%s 应由报道正文点名支持" % sid)

    def test_backed_requires_matching_report(self):
        """★★ `reported_move_backed` 必须由**能支持该股**的报道决定，不能只看来源类型。"""
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                if mp.get("reported_move_backed"):
                    self.assertIsNotNone(mp.get("report"), "%s/%s backed 却无报道" % (eid, sid))
                    self.assertIn(mp.get("attribution"), ("NAME_IN_TEXT", "REPORT_LIST_AGGREGATE"),
                                  "%s/%s 关联级别非法" % (eid, sid))
                    self.assertTrue(mp["status"].startswith("REPORT_CONFIRMED_"),
                                    "%s/%s backed 但状态 %s" % (eid, sid, mp["status"]))
                if mp["status"] == "UNVERIFIED_REPORT_ATTRIBUTION":
                    self.assertFalse(mp.get("reported_move_backed"),
                                     "%s/%s 未核验归属却标 backed" % (eid, sid))
                    self.assertIsNone(mp.get("identified_date"),
                                      "%s/%s 未核验归属却给了识别日" % (eid, sid))

    def test_report_status_requires_publication_date(self):
        """没有发布日 → 不得出现 `REPORT_CONFIRMED_*`（宁可留白，不用事实日冒充）。"""
        for eid, ev in self.doc["events"].items():
            for sid, p in ev["participants"].items():
                mp = p["market_participation"]
                if mp["status"].startswith("REPORT_CONFIRMED_"):
                    self.assertTrue(mp.get("identified_date"),
                                    "%s/%s 报道状态却无识别日" % (eid, sid))


if __name__ == "__main__":
    unittest.main(verbosity=2)
