#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""涨停识别审计的 **ST 规则说明**测试（v0.32）。

背景：v0.31 的审计把 ST 写成「一律 5% → 天然不被识别」，这与交易所规则不符：
  · 主板风险警示股票 5%（≤2026-07-05）→ **2026-07-06 起 10%**；
  · 创业板风险警示股票 5%（改革前）→ **2020-08-24 起 20%**；
  · 科创板风险警示股票 **20%**（与普通股同带）。

本测试锁三件事：
1. 审计产物里的 `st_rules` 必须按**板块 × 时期**给出比例，并带可追溯来源 URL；
2. 「不能独立核实的例外」必须进 `not_verified`（不擅自补事实）；
3. 审计产物必须声明它审的是**哪个版本的角色产物**，且该文件存在。

运行：`python research/scripts/test_audit_market_limit_up.py`
"""

from __future__ import annotations

import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
REPORTS = os.path.join(REPO, "research", "research", "reports")


def latest_audit():
    files = [f for f in os.listdir(REPORTS) if re.match(r"limit_up_audit_v0_(\d+)\.json$", f)]
    files.sort(key=lambda f: int(re.search(r"v0_(\d+)", f).group(1)))
    return os.path.join(REPORTS, files[-1])


class StRuleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = latest_audit()
        with open(cls.path, encoding="utf-8") as fh:
            cls.doc = json.load(fh)
        cls.st = cls.doc["st_rules"]

    def test_bands_are_board_and_period_specific(self):
        bands = self.st["bands_by_board_and_period"]
        self.assertEqual({b["limit_pct"] for b in bands["MAIN"]}, {5, 10})
        self.assertEqual({b["limit_pct"] for b in bands["GEM"]}, {5, 20})
        self.assertEqual({b["limit_pct"] for b in bands["STAR"]}, {20})

    def test_main_board_st_switch_on_2026_07_06(self):
        main = {b["period"]: b for b in self.st["bands_by_board_and_period"]["MAIN"]}
        self.assertEqual(main["<= 2026-07-05"]["limit_pct"], 5)
        self.assertEqual(main[">= 2026-07-06"]["limit_pct"], 10)
        # 10% 与主板普通股同带 → 不再是漏报
        self.assertIn("不漏报", main[">= 2026-07-06"]["consequence"])
        self.assertIn("漏报", main["<= 2026-07-05"]["consequence"])

    def test_gem_st_switch_on_2020_08_24(self):
        gem = {b["period"]: b for b in self.st["bands_by_board_and_period"]["GEM"]}
        self.assertEqual(gem["<= 2020-08-23"]["limit_pct"], 5)
        self.assertEqual(gem[">= 2020-08-24"]["limit_pct"], 20)
        self.assertIn("不漏报", gem[">= 2020-08-24"]["consequence"])

    def test_sources_are_citable(self):
        srcs = self.st["sources"]
        self.assertGreaterEqual(len(srcs), 3)
        for s in srcs:
            self.assertTrue(s.get("url", "").startswith("https://"), s)
            self.assertRegex(s.get("date", ""), r"^\d{4}-\d{2}-\d{2}$")
            self.assertTrue(s.get("quote"), "缺原文引用：%s" % s.get("title"))

    def test_unverified_items_are_declared(self):
        nv = self.st["not_verified"]
        self.assertGreaterEqual(len(nv), 3)
        blob = " ".join(nv)
        for token in ("特别规定", "退市整理期", "北交所"):
            self.assertIn(token, blob, "未声明的未知项：%s" % token)

    def test_audited_artifact_is_traceable(self):
        rel = self.doc.get("audited_roles_artifact")
        self.assertTrue(rel, "审计产物必须声明它审的是哪个角色产物")
        self.assertTrue(os.path.exists(os.path.join(REPO, rel)), rel)
        self.assertRegex(rel, r"historical_market_roles_v0_\d+\.json$")

    def test_no_blanket_st_claim(self):
        """★ 不得再出现「ST 一律 5%」这类笼统说法。"""
        blob = json.dumps(self.doc, ensure_ascii=False)
        self.assertNotIn("ST（5%）无法从库内判定", blob)
        self.assertIn("不会被漏掉", blob)


if __name__ == "__main__":
    unittest.main(verbosity=2)
