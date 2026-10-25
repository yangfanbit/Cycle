#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_limit_up_action_day_v0_48.py —— 公司行为日分支的针对性回归（v0.48）。

## 背景（真实缺陷，不是假设）

`classify()` / `daily_change()` 在「公司行为日」分支（`|raw_pct| > ACTION_DAY_PCT = 21.6`）
**直接返回 `adj_pct`，没有校验它是否落在当前板块当日的涨停带内**。
实测后果：`+2.00%`（卓胜微 2021-04-30）、`+3.67%`（卓胜微 2022-06-30）、
`−3.37%`（圣邦股份 2022-06-22）都被当成「涨停信号」。

## 本测试覆盖

1. 三个实测误报值必须返回「无信号」（两个实现各测一遍）；
2. 公司行为日但复权涨幅**确实落在带内**（+10.00% / 科创板 +20.00%）→ 仍返回信号（原有行为不变）；
3. 板块/日期边界不变：创业板 2020-08-24 前 10%、之后 20%；科创板 20%；主板 10%；
4. 非行为日的既有三条分支（both_series_agree / adjusted_ratio_ex_dividend / 无信号）不受影响。

运行：`python research/scripts/test_limit_up_action_day_v0_48.py`
"""
import importlib.util
import os
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load('roles_mod', 'build_historical_market_roles_v0_1.py')
A = _load('audit_mod', 'audit_market_limit_up_v0_1.py')


class TestAuditClassifyActionDay(unittest.TestCase):
    """审计侧 `classify()`：纯函数，直接测。"""

    def test_real_false_positives_are_not_signals(self):
        # 三个实测误报值：原始价大跳（除权）+ 复权残差不在涨停带内
        for adj in (2.00, 3.67, -3.37):
            for raw in (25.0, -25.0, 60.0):
                kind, pct = A.classify(raw, adj, 9.8, 10.6)
                self.assertIsNone(kind, 'adj=%s raw=%s 不应被识别为涨停' % (adj, raw))
                self.assertIsNone(pct)

    def test_action_day_inside_band_still_signal(self):
        kind, pct = A.classify(25.0, 10.00, 9.8, 10.6)
        self.assertEqual(kind, 'adjusted_ratio_action_day')
        self.assertAlmostEqual(pct, 10.00)

    def test_action_day_star_band(self):
        # 科创板 20% 档：+20.00% 合法，+10.00% 不合法
        self.assertEqual(A.classify(-30.0, 20.00, 19.5, 21.2)[0], 'adjusted_ratio_action_day')
        self.assertIsNone(A.classify(-30.0, 10.00, 19.5, 21.2)[0])

    def test_action_day_adj_missing(self):
        self.assertEqual(A.classify(25.0, None, 9.8, 10.6), (None, None))

    def test_non_action_day_branches_unchanged(self):
        self.assertEqual(A.classify(10.00, 10.00, 9.8, 10.6), ('both_series_agree', 10.00))
        self.assertEqual(A.classify(9.60, 10.00, 9.8, 10.6)[0], 'adjusted_ratio_ex_dividend')
        self.assertIsNone(A.classify(9.60, 9.70, 9.8, 10.6)[0])


class TestRolesDailyChange(unittest.TestCase):
    """角色侧 `daily_change()`：需要 market_daily 双口径行，用临时库。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='lu_action_')
        self.db = os.path.join(self.tmp, 'm.db')
        con = sqlite3.connect(self.db)
        con.execute("CREATE TABLE market_daily (series_id TEXT, trade_date TEXT, close REAL, "
                    "adj_close REAL, price_type TEXT)")
        con.commit()
        con.close()
        self.con = sqlite3.connect(self.db)
        self.con.row_factory = sqlite3.Row

    def tearDown(self):
        self.con.close()
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _rows(self, sid, d0, raw0, adj0, d1, raw1, adj1):
        self.con.executemany(
            "INSERT INTO market_daily VALUES (?,?,?,?,?)",
            [(sid, d0, raw0, adj0, 'raw'), (sid, d0, raw0, adj0, 'adjusted'),
             (sid, d1, raw1, adj1, 'raw'), (sid, d1, raw1, adj1, 'adjusted')])
        self.con.commit()

    def test_action_day_residual_not_signal(self):
        # 主板：原始价 −60%（送转）+ 复权残差 +2.00% → 无信号
        self._rows('X', '2021-04-29', 100.0, 100.0, '2021-04-30', 40.0, 102.0)
        self.assertIsNone(R.daily_change(self.con, 'X', '2021-04-30', '600000'))

    def test_action_day_negative_residual_not_signal(self):
        # 原始价 +60% + 复权 −3.37% → 无信号（不能把负收益算成涨停）
        self._rows('Y', '2022-06-21', 100.0, 100.0, '2022-06-22', 160.0, 96.63)
        self.assertIsNone(R.daily_change(self.con, 'Y', '2022-06-22', '300661'))

    def test_action_day_inside_band_is_signal(self):
        # 原始价 −60% + 复权 +10.00% → 仍是信号（原有行为）
        self._rows('Z', '2021-04-29', 100.0, 100.0, '2021-04-30', 40.0, 110.0)
        got = R.daily_change(self.con, 'Z', '2021-04-30', '600000')
        self.assertIsNotNone(got)
        self.assertEqual(got['basis'], 'adjusted_ratio_action_day')
        self.assertAlmostEqual(got['pct'], 10.0, places=6)

    def test_action_day_gem_band_boundary(self):
        # 创业板：2020-08-24 前 10% 档、之后 20% 档
        self._rows('G', '2020-08-20', 100.0, 100.0, '2020-08-21', 40.0, 110.0)
        self.assertIsNotNone(R.daily_change(self.con, 'G', '2020-08-21', '300001'))
        self._rows('H', '2021-04-29', 100.0, 100.0, '2021-04-30', 40.0, 110.0)
        self.assertIsNone(R.daily_change(self.con, 'H', '2021-04-30', '300001'))

    def test_bands_unchanged(self):
        self.assertEqual(R.limit_band('600000', '2026-01-01'), (9.8, 10.6))
        self.assertEqual(R.limit_band('688256', '2026-01-01'), (19.5, 21.2))
        self.assertEqual(R.limit_band('300001', '2020-08-21'), (9.8, 10.6))
        self.assertEqual(R.limit_band('300001', '2020-08-24'), (19.5, 21.2))
        self.assertEqual(A.limit_band('600000', '2026-01-01'), R.limit_band('600000', '2026-01-01'))
        self.assertEqual(A.limit_band('688256', '2026-01-01'), R.limit_band('688256', '2026-01-01'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
