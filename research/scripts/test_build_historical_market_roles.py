#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""历史市场角色产物的 **Point-in-Time 不变量测试**（v0.29）。

只测「时间前推纪律不能被绕过」的硬规则：

1. 每个事件都有 `research_status`；未研究的必须写明缺什么；
2. `POSTHOC_LEADER_SET` 一律 `posthoc=true` / `pit_safe=false`；
3. 任何角色的 `identified_date` 都不得晚于事件窗口结束日还被标 `pit_safe`；
4. `PIT_MEDIA_NAMED_LEADER` 必须真的有「龙头/领涨/核心」字样（当前应为 0 条）；
5. 切片只收 `identified_date ≤ 切片日` 的成员，且与原始研究记录**逐条一致**；
6. 角色不得凭空出现：每个 role 的 security_id 必须在该事件的参与者里。

运行：`python research/scripts/test_build_historical_market_roles.py`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
CURRENT = os.path.join(REPO, "research", "current")
ARTIFACT = os.path.join(CURRENT, "historical_market_roles_v0_3.json")
INDEX = os.path.join(CURRENT, "historical_event_maps_index.json")
EVIDENCE = os.path.join(CURRENT, "participant_evidence_v0_4.json")


class MarketRolesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.load(open(ARTIFACT, encoding="utf-8"))
        cls.evid = json.load(open(EVIDENCE, encoding="utf-8"))
        idx = json.load(open(INDEX, encoding="utf-8"))
        cls.events = {}
        for entry in idx["maps"]:
            doc = json.load(open(os.path.join(CURRENT, entry["file"]), encoding="utf-8"))
            for e in doc["events"]:
                cls.events[e["event_id"]] = e

    def test_every_event_has_status_and_gaps(self):
        self.assertEqual(len(self.doc["events"]), 33)
        for eid, ev in self.doc["events"].items():
            self.assertIn(ev["research_status"],
                          ("RESEARCHED_PIT", "DERIVED_FROM_REPORT",
                           "DERIVED_FROM_MARKET", "NOT_RESEARCHED"), eid)
            if ev["research_status"] == "NOT_RESEARCHED":
                self.assertTrue(ev["gaps"], "%s 未研究却没写缺什么" % eid)
            if not ev["roles"]:
                self.assertTrue(ev["gaps"], "%s 无角色却没写原因" % eid)

    def test_posthoc_never_pit_safe(self):
        for eid, ev in self.doc["events"].items():
            ph = ev["posthoc_leader_set"]
            if not ph:
                continue
            self.assertTrue(ph["posthoc"], eid)
            self.assertFalse(ph["pit_safe"], "%s 事后集合被标为 pit_safe" % eid)
            for r in ev["roles"]:
                if r["role"] == "POSTHOC_LEADER_SET":
                    self.assertFalse(r["pit_safe"], "%s/%s" % (eid, r["security_id"]))

    def test_pit_safe_respects_window_end(self):
        for eid, ev in self.doc["events"].items():
            w = ev["window"]
            if not w:
                continue
            for r in ev["roles"]:
                if r["identified_date"] > w[1]:
                    self.assertFalse(r["pit_safe"],
                                     "%s/%s 识别日 %s 晚于窗口末 %s 却标 pit_safe"
                                     % (eid, r["security_id"], r["identified_date"], w[1]))

    def test_leader_role_requires_leader_wording(self):
        """★ 「龙头」不能靠涨停推出来 —— 必须原文有「龙头/领涨/核心」字样。"""
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if r["role"] != "PIT_MEDIA_NAMED_LEADER":
                    continue
                blob = " ".join(str(r["evidence"].get(k) or "") for k in
                                ("summary", "source_text", "url"))
                self.assertTrue(any(k in blob for k in ("龙头", "领涨", "核心")),
                                "%s/%s 声称「报道称龙头」但原文无相应字样" % (eid, r["security_id"]))
        # 当前库内应为 0 条（没有同期材料明确称龙头）
        n = sum(1 for ev in self.doc["events"].values()
                for r in ev["roles"] if r["role"] == "PIT_MEDIA_NAMED_LEADER")
        self.assertEqual(n, 0, "出现了「报道称龙头」记录 → 请确认原文确实如此")

    def test_slices_match_documented_study(self):
        """★★ 切片与原始 PIT 研究记录的关系必须**三态明确**（FULL / SUBSET / MISMATCH）。

        v0.29 用 `matches_document` 一个布尔，且只与「已绑定子集」比对 → 会把
        「地图只覆盖 2/4」显示成「完全一致」。v0.30 拆成 `match_scope`：
          · Robotaxi 07-08  → FULL（1 只，全部可绑定）
          · Robotaxi 07-10  → SUBSET（原始 4 只，地图覆盖 2 只：星网宇达 / 天迈科技 不在参与者里）
          · Robotaxi 07-15  → SUBSET（原始 5 只，地图覆盖 3 只）
        ★ 任何切片都不允许出现 MISMATCH（真不一致），且 `matches_document` 只在 FULL 为真。
        """
        for eid, ev in self.doc["events"].items():
            for s in ev["pit_slices"]:
                self.assertIn(s["match_scope"], ("FULL", "SUBSET", "MISMATCH"),
                              "%s %s scope 非法" % (eid, s["date"]))
                self.assertNotEqual(s["match_scope"], "MISMATCH",
                                    "%s %s 与原始研究不一致：推导 %s vs 文档 %s"
                                    % (eid, s["date"], s["members"], s["documented_members"]))
                self.assertEqual(s["matches_document"], s["match_scope"] == "FULL",
                                 "%s %s matches_document 与 scope 不符" % (eid, s["date"]))
                # 成员只能来自 identified_date ≤ 切片日 的角色
                for sid in s["members"]:
                    r = next(x for x in ev["roles"] if x["security_id"] == sid)
                    self.assertLessEqual(r["identified_date"], s["date"])

    def test_robotaxi_slice_coverage_gap_is_visible(self):
        """★★ 覆盖缺口必须出现在数据里（不是只写在说明文字里）。"""
        ev = self.doc["events"]["AUTO-2024-ROBOTAXI"]
        by_date = {s["date"]: s for s in ev["pit_slices"]}
        self.assertEqual(by_date["2024-07-08"]["match_scope"], "FULL")
        for d in ("2024-07-10", "2024-07-15"):
            s = by_date[d]
            self.assertEqual(s["match_scope"], "SUBSET", d)
            self.assertEqual(sorted(s["not_in_map"]), ["TIANMAI", "XINGYUYUDA"], d)
            self.assertEqual(sorted(s["not_in_map_names"]), ["天迈科技", "星网宇达"], d)
            self.assertEqual(s["documented_count"], len(s["documented_members"]), d)
            self.assertLess(s["bound_count"], s["documented_count"], d)

    def test_media_role_date_is_publication_date(self):
        """★★ 媒体角色的识别日 == 报道发布日，且不得早于发布日（防时间泄漏）。"""
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if not r["role"].startswith("PIT_MEDIA"):
                    continue
                pub = (r.get("evidence") or {}).get("published_at")
                self.assertRegex(str(pub or ""), r"^\d{4}-\d{2}-\d{2}$",
                                 "%s/%s 媒体角色缺发布日" % (eid, r["security_id"]))
                self.assertEqual(r["identified_date"], pub,
                                 "%s/%s 识别日必须等于发布日" % (eid, r["security_id"]))
                self.assertGreaterEqual(r["identified_date"], pub,
                                        "%s/%s 识别日早于发布日（时间泄漏）" % (eid, r["security_id"]))
                fact = (r.get("evidence") or {}).get("fact_date")
                if fact:
                    self.assertLessEqual(fact, r["identified_date"],
                                         "%s/%s 事实日期晚于识别日" % (eid, r["security_id"]))

    def test_superfungus_roles_use_correct_date(self):
        """★ 已确认错配案例：超级真菌 8 条角色识别日必须是 2019-04-11（不是 04-08）。"""
        ev = self.doc["events"]["SUPERFUNGUS-2019-CANDIDA"]
        self.assertEqual(ev["research_status"], "DERIVED_FROM_REPORT")
        self.assertEqual(len(ev["roles"]), 8)
        for r in ev["roles"]:
            self.assertEqual(r["identified_date"], "2019-04-11", r["security_id"])

    def test_market_role_requires_consecutive_limit_up(self):
        """★★ 盘面角色（PIT_MARKET_OBSERVED）必须满足**可复核判据**：
        截至识别日 ≥2 次信号且至少一次相邻交易日连板，识别日 = 首次连板的第二个信号日。
        """
        cal = self._calendar()
        checked = 0
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if r["role"] != "PIT_MARKET_OBSERVED":
                    continue
                days_ev = (r["evidence"].get("limit_up_days_as_of") or [])
                if not days_ev:
                    # CSV 里的 market_breadth 角色（人工研究结论）没有信号明细
                    self.assertEqual(r.get("identification_type"), "market_breadth",
                                     "%s/%s 无信号明细却不是 CSV market_breadth" % (eid, r["security_id"]))
                    self.assertNotIn("同期报道", r["evidence"].get("source_type") or "")
                    continue
                checked += 1
                days = [d["date"] for d in days_ev]
                self.assertGreaterEqual(len(days), 2, "%s/%s 截至识别日信号不足 2" % (eid, r["security_id"]))
                pairs = [(a, b) for a, b in zip(days, days[1:])
                         if cal.get(b, -99) - cal.get(a, -99) == 1]
                self.assertTrue(pairs, "%s/%s 无连板" % (eid, r["security_id"]))
                self.assertEqual(r["identified_date"], pairs[0][1],
                                 "%s/%s 识别日应为首次连板第二个信号日" % (eid, r["security_id"]))
                self.assertEqual(r["evidence"].get("evidence_as_of_date"), r["identified_date"],
                                 "%s/%s evidence_as_of_date 必须等于识别日" % (eid, r["security_id"]))
        self.assertGreater(checked, 0, "没有任何盘面角色 → 测试失效")

    def test_pit_safe_evidence_never_after_identified_date(self):
        """★★★ v0.31 PIT 封口：`pit_safe=true` 的角色，其**支持性证据**不得晚于识别日。

        必须覆盖「识别日之后还有更多行情数据」的真实事件
        （SEMI-2019-LOCALIZATION / AUTO-2024-V2X / RES-2020-RAREEARTH 等）。
        """
        checked = 0
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if r["role"] != "PIT_MARKET_OBSERVED" or not r.get("pit_safe"):
                    continue
                evd = r.get("evidence") or {}
                ident = r["identified_date"]
                for x in (evd.get("limit_up_days_as_of") or []):
                    self.assertLessEqual(x["date"], ident,
                                         "%s/%s PIT 证据含识别日之后的信号 %s"
                                         % (eid, r["security_id"], x["date"]))
                # 识别日之后的信号必须**只**出现在 retrospective 里，且带事后说明
                retro = evd.get("retrospective_limit_up_days") or []
                for x in retro:
                    self.assertGreater(x["date"], ident,
                                       "%s/%s retrospective 里混了识别日之前的信号" % (eid, r["security_id"]))
                if retro:
                    checked += 1
                    self.assertIn("事后", evd.get("retrospective_note") or "",
                                  "%s/%s 缺事后说明" % (eid, r["security_id"]))
        # ★ 至少 3 个真实事件的识别日之后还有行情数据（否则测试没覆盖到目标场景）
        self.assertGreaterEqual(checked, 3,
                                "识别日之后仍有行情数据的角色不足 3 个 → 未覆盖目标场景")

    def test_retrospective_signals_not_in_supporting_set(self):
        """★ 事后信号不得进入支持性证据集合（两个列表不得重叠）。"""
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if r["role"] != "PIT_MARKET_OBSERVED":
                    continue
                evd = r.get("evidence") or {}
                a = {x["date"] for x in (evd.get("limit_up_days_as_of") or [])}
                b = {x["date"] for x in (evd.get("retrospective_limit_up_days") or [])}
                self.assertEqual(a & b, set(), "%s/%s 支持性证据与事后观察重叠" % (eid, r["security_id"]))

    def test_signal_basis_is_recorded(self):
        """★ 每个信号都必须带计算基础（双口径核验结果），不得只给一个百分比。"""
        for eid, ev in self.doc["events"].items():
            for r in ev["roles"]:
                if r["role"] != "PIT_MARKET_OBSERVED":
                    continue
                for x in ((r.get("evidence") or {}).get("limit_up_days_as_of") or []):
                    self.assertIn(x.get("basis"),
                                  ("both_series_agree", "adjusted_ratio_ex_dividend",
                                   "adjusted_ratio_action_day"),
                                  "%s/%s 信号缺计算基础" % (eid, r["security_id"]))
                    self.assertTrue(x.get("corroborated") in (True, False))

    def test_window_semantics_separates_market_and_pit(self):
        """★★ 三种窗口必须分开记录；Robotaxi 的 PIT 观察窗口早于行情窗口（不得删）。"""
        for eid, ev in self.doc["events"].items():
            ws = ev.get("window_semantics") or {}
            self.assertIn("market_performance_window", ws, eid)
            self.assertIn("pit_observation_window", ws, eid)
        rb = self.doc["events"]["AUTO-2024-ROBOTAXI"]
        ws = rb["window_semantics"]
        self.assertEqual(ws["market_performance_window"], ["2024-07-11", "2024-07-29"])
        # PIT 研究切片从 07-08 开始 → 观察窗口必须早于行情窗口且被保留
        self.assertEqual(ws["pit_observation_window"][0], "2024-07-08")
        self.assertLess(ws["pit_observation_window"][0], ws["market_performance_window"][0])

    def _calendar(self):
        import sqlite3
        conn = sqlite3.connect(os.path.join(REPO, "research", "database", "market_data.db"))
        try:
            return {r[0]: i for i, r in enumerate(
                conn.execute("SELECT trade_date FROM trading_calendar ORDER BY trade_date"))}
        finally:
            conn.close()

    def test_id_conflict_is_not_bound(self):
        """★★ 身份安全：**ID 相同但名称不同**不得自动绑定（回归 v0.29 的隐患）。

        用真实数据构造反例：把 CSV 的 `JINLONG`（金龙汽车）名称改成「锦江在线」，
        它与地图参与者 `JINLONG` 的 id 相同但名称不同 → 必须 `ID_CONFLICT_NAME_MISMATCH`。
        """
        sys.path.insert(0, os.path.join(REPO, "research"))
        from scripts import build_historical_market_roles_v0_1 as roles  # noqa: E402
        participants = [{"security_id": "JINLONG", "name": "金龙汽车", "ticker": "600686"},
                        {"security_id": "JINJIANGONLINE", "name": "锦江在线", "ticker": "600650"}]
        rows = [{"security_id": "JINLONG", "name": "锦江在线"},
                {"security_id": "JINJIANG", "name": "锦江在线"}]
        secs = {"JINLONG": {"name": "金龙汽车", "ticker": "600686"},
                "JINJIANG": {"name": "锦江酒店", "ticker": "600754"},
                "JINJIANGONLINE": {"name": "锦江在线", "ticker": "600650"}}
        b = roles.bind_pit_ids("TEST", rows, participants, secs)
        self.assertEqual(b["JINLONG"]["status"], "ID_CONFLICT_NAME_MISMATCH")
        self.assertIsNone(b["JINLONG"]["bound_to"])
        # 名称正确的那条 → 按名称绑定，但必须暴露「该 id 指向另一家公司」
        self.assertEqual(b["JINJIANG"]["status"], "BOUND_BY_NAME")
        self.assertEqual(b["JINJIANG"]["bound_to"], "JINJIANGONLINE")
        self.assertEqual(b["JINJIANG"]["registry_name_conflict"]["registry_name"], "锦江酒店")

    def test_robotaxi_binding_flags_review(self):
        """★ Robotaxi 的两条名称绑定必须带 `NAME_MATCH_ONLY`，未绑定的必须有原因。"""
        ev = self.doc["events"]["AUTO-2024-ROBOTAXI"]
        by_src = {r["source_security_id"]: r for r in ev["roles"]}
        self.assertEqual(by_src["JINJIANG"]["binding"]["review"], "NAME_MATCH_ONLY")
        self.assertEqual(by_src["JINJIANG"]["binding"]["registry_name_conflict"]["registry_name"],
                         "锦江酒店")
        self.assertEqual(by_src["DAZHONGTONG"]["binding"]["status"], "BOUND_BY_NAME")
        for sid in ("XINGYUYUDA", "TIANMAI"):
            self.assertEqual(by_src[sid]["binding"]["status"], "UNBOUND")
            self.assertIsNone(by_src[sid]["security_id"])

    def test_role_binding_is_explicit(self):
        """★ 角色要么绑到本事件参与者上，要么**显式**标未绑定并写明原因。

        这条是为了防「按 ID 硬匹配」张冠李戴：实测 CSV `JINJIANG`（锦江在线）
        在注册表里是**锦江酒店 600754**（另一家公司）。
        """
        for eid, ev in self.doc["events"].items():
            part = set(self.evid["events"].get(eid, {}).get("participants", {}))
            for r in ev["roles"]:
                b = r.get("binding") or {}
                self.assertIn(b.get("status"), ("BOUND", "BOUND_BY_NAME", "UNBOUND", "AMBIGUOUS"),
                              "%s/%s 绑定状态非法" % (eid, r["source_security_id"]))
                if r["security_id"]:
                    self.assertIn(r["security_id"], part,
                                  "%s/%s 绑定到了非参与者" % (eid, r["security_id"]))
                else:
                    self.assertTrue(b.get("note"), "%s/%s 未绑定却没写原因" % (eid, r["source_security_id"]))
                # ★ 名称绑定必须标注 review（名称比对没有证明力，需人工确认）
                if b.get("status") == "BOUND_BY_NAME":
                    self.assertEqual(b.get("review"), "NAME_MATCH_ONLY")

    def test_check_passes(self):
        code = subprocess.run(
            [sys.executable, os.path.join(HERE, "build_historical_market_roles_v0_1.py"), "--check"],
            capture_output=True, text=True).returncode
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
