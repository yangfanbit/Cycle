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
ARTIFACT = os.path.join(CURRENT, "historical_market_roles_v0_1.json")
INDEX = os.path.join(CURRENT, "historical_event_maps_index.json")
EVIDENCE = os.path.join(CURRENT, "participant_evidence_v0_2.json")


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
                          ("RESEARCHED_PIT", "DERIVED_FROM_REPORT", "NOT_RESEARCHED"), eid)
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
        """切片必须与原始 PIT 研究记录逐条一致（防推导规则悄悄漂移）。"""
        for eid, ev in self.doc["events"].items():
            for s in ev["pit_slices"]:
                self.assertTrue(s["matches_document"],
                                "%s %s 切片与原始记录不一致：推导 %s vs 文档 %s"
                                % (eid, s["date"], s["members"], s["documented_members"]))
                # 成员只能来自 identified_date ≤ 切片日 的角色
                for sid in s["members"]:
                    r = next(x for x in ev["roles"] if x["security_id"] == sid)
                    self.assertLessEqual(r["identified_date"], s["date"])

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
