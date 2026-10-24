#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""前瞻观察的**聚焦**检查（v0.33.1）：只测这次改的三件事，不建通用套件。

1. `merge_series`：旧缓存能被新行情**追加**与**覆盖**（不是条数够了就永久跳过）；
2. `event_study`：pre / event_day / post 三段**独立**（事件前上涨不会算进响应）；
3. `_cluster_stages`：同一轮窗口重叠的事件归入一个阶段（不重复计数）。

运行：python research/scripts/test_forward_observation.py
"""
from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from scripts import build_forward_observation_v0_1 as B  # noqa: E402


class ForwardObservationTest(unittest.TestCase):
    def test_merge_series_appends_and_overwrites(self):
        old = [["2024-01-02", 1, 10.0, 1, 1, 1], ["2024-01-03", 1, 11.0, 1, 1, 1]]
        new = [["2024-01-03", 1, 11.5, 1, 1, 1], ["2024-01-04", 1, 12.0, 1, 1, 1]]
        m = B.merge_series(old, new)
        self.assertEqual([r[0] for r in m], ["2024-01-02", "2024-01-03", "2024-01-04"])
        self.assertEqual(m[1][2], 11.5, "同日新值必须覆盖旧值")
        self.assertEqual(len(B.merge_series(m, [])), 3, "空刷新不得丢数据")

    def test_event_study_segments_are_independent(self):
        # 基准走平；成员在事件前大涨、事件日下跌、事件后小涨
        import datetime
        days = [(datetime.date(2024, 2, 1) + datetime.timedelta(days=i)).isoformat()
                for i in range(50)]
        bench = [[d, 1, 100.0, 1, 1, 1] for d in days]
        rows = []
        px = 10.0
        for i, d in enumerate(days):
            if 15 <= i < 25:
                px *= 1.05      # 事件前 10 天每天 +5%
            elif i == 25:
                px *= 0.95      # 事件日 -5%
            else:
                px *= 0.999   # 事件后走弱 → post20 超额为负
            rows.append([d, px, px, px, px, 1])
        members = {"X": rows}
        st = B.event_study(members, bench, days[25])
        self.assertEqual(st["status"], "OK")
        self.assertGreater(st["pre"]["median_excess_pct"], 5, "事件前应有正超额")
        self.assertLess(st["event_day"]["median_excess_pct"], 0, "事件日应单独为负")
        self.assertIsNotNone(st["post"]["post5"]["median_excess_pct"])
        # ★ 响应只看 post20；事件前的正超额不得把 responded 变真
        self.assertFalse(st["responded"])

    def test_cluster_stages_merges_overlapping_rounds(self):
        ev = [{"event_id": "A", "event_date": "2022-08-02"},
              {"event_id": "B", "event_date": "2022-08-04"},
              {"event_id": "C", "event_date": "2023-04-08"}]
        stages = B._cluster_stages(ev)
        self.assertEqual(len(stages), 2, "相邻两日应归入同一阶段")
        self.assertEqual(stages[0]["events"], ["A", "B"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
