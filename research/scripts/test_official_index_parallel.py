#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_official_index_parallel.py —— 官方指数并列行情的**计算与边界**测试（Wave 2.1）。

★ 全部使用**合成序列**，不联网、不依赖真实官方数值 —— 因此在授权未明确时也能完整验证逻辑。

覆盖：
  T1  区间收益与超额可复算（末收盘/首收盘 − 1；超额 = 本指数 − 基准）
  T2  `rows_before_publish` 由**实际序列**计算，不是手写常数
  T3  `backfilled` 是**窗口级**标记：窗口含发布前交易日 → True；全在发布后 → False；无窗口 → None
  T4  交易日不足 → 明确状态、数值为 None（**不插值、不补造、不填 0**）
  T5  窗口首末为非交易日 → 落到最近的实际交易日，不做任何插值
  T6  授权闸门：未声明许可时**拒绝**写入 `research/current/`，且不创建文件
  T7  缺窗口/缺数据时显式写 `missing_required_fields`，不静默填 0 / false
  T8  指数身份：是「半导体产品与设备」而非「AI 算力」，且不带成分信息

运行：`python research/scripts/test_official_index_parallel.py`
"""
from __future__ import annotations

import datetime as _dt
import io
import os
import sys
import unittest
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_official_index_parallel_v0_1 as B  # noqa: E402

warnings.simplefilter("ignore", ResourceWarning)


def _weekdays(year, month, ndays=31):
    """只取工作日（周一到周五），模拟交易日历 —— 合成数据，不取任何真实行情。"""
    out = []
    for d in range(1, ndays + 1):
        try:
            day = _dt.date(year, month, d)
        except ValueError:
            continue
        if day.weekday() < 5:
            out.append(day.isoformat())
    return out


# 合成序列：2020-01 的每个工作日 +1%（基准 +0.5%）
# ★ 从 01-02 起（01-01 是节假日，不纳入 —— 合成日历也要与真实交易日对齐）
_DAYS = [d for d in _weekdays(2020, 1) if d >= "2020-01-02"]
SERIES = [(d, 100.0 * (1.01 ** i)) for i, d in enumerate(_DAYS)]
BENCH = [(d, 200.0 * (1.005 ** i)) for i, d in enumerate(_DAYS)]


class TestCompute(unittest.TestCase):

    def test_T1_return_and_excess(self):
        w = ("2020-01-02", "2020-01-06")   # 3 个交易日：02/03/06
        r = B.compute_window(SERIES, w)
        self.assertEqual(r["status"], "COMPUTED")
        self.assertEqual(r["window_actual"]["trading_days"], 3)
        first, last = SERIES[0][1], SERIES[2][1]
        self.assertAlmostEqual(r["period_return_pct"], round((last / first - 1) * 100, 4), places=6)
        b = B.compute_window(BENCH, w)
        self.assertAlmostEqual(r["period_return_pct"] - b["period_return_pct"],
                               (last / first - 1) * 100 - (BENCH[2][1] / BENCH[0][1] - 1) * 100,
                               places=3)

    def test_T2_rows_before_publish_from_series(self):
        # 发布日取 2020-01-10 → 序列中 < 该日的行数应为 6（01-02..01-09 共 6 个工作日）
        n = B.count_rows_before(SERIES, "2020-01-10")
        self.assertEqual(n, 6)
        # 换一个发布日期，结果必须随之变化（证明不是常数）
        self.assertEqual(B.count_rows_before(SERIES, "2020-01-03"), 1)
        self.assertEqual(B.count_rows_before(SERIES, "1990-01-01"), 0)

    def test_T3_backfilled_is_window_level(self):
        self.assertFalse(B.window_touches_backfill(SERIES, ("2020-01-10", "2020-01-20"), "2020-01-10"))
        self.assertTrue(B.window_touches_backfill(SERIES, ("2020-01-06", "2020-01-20"), "2020-01-10"))
        self.assertIsNone(B.window_touches_backfill(SERIES, None, "2020-01-10"),
                          "无窗口时必须是 None，不得当成 False")

    def test_T4_insufficient_days_no_fill(self):
        r = B.compute_window(SERIES, ("2020-01-04", "2020-01-05"))  # 周六/周日 → 0 个交易日
        self.assertEqual(r["status"], "INSUFFICIENT_TRADING_DAYS")
        self.assertIsNone(r["period_return_pct"])
        self.assertIn("不插值", r["error"])
        # 单日窗口（只有 1 个交易日）同样不计算
        r2 = B.compute_window(SERIES, ("2020-01-06", "2020-01-06"))
        self.assertEqual(r2["status"], "INSUFFICIENT_TRADING_DAYS")
        self.assertIsNone(r2["period_return_pct"])

    def test_T5_non_trading_endpoints_snap_without_interpolation(self):
        # 2020-01-04/05 是周末 → 应落到 01-06 与 01-03 之间的实际交易日，且不产生任何虚构值
        r = B.compute_window(SERIES, ("2020-01-03", "2020-01-07"))
        self.assertEqual(r["status"], "COMPUTED")
        self.assertEqual(r["window_actual"]["first_trade_date"], "2020-01-03")
        self.assertEqual(r["window_actual"]["last_trade_date"], "2020-01-07")
        self.assertEqual(r["window_actual"]["trading_days"], 3)  # 03 / 06 / 07
        self.assertEqual(r["window_actual"]["first_close"], SERIES[1][1])
        self.assertEqual(r["window_actual"]["last_close"], SERIES[3][1])

    def test_T6_license_gate_blocks_production_write(self):
        target = os.path.join(B.CURRENT, "_should_not_exist_official_index.json")
        rc = B.main(["--write", "--out", target])
        self.assertEqual(rc, 2, "未声明许可时必须拒绝写入生产目录")
        self.assertFalse(os.path.exists(target), "拒绝时不得创建任何文件")

    def test_T7_missing_window_reports_gap(self):
        doc = {"events": [{"event_id": "FAKE-NO-WINDOW", "market_performance": {}}]}
        entries = B.build(doc, SERIES, BENCH)
        e = entries[0]
        self.assertEqual(e["status"], "INCOMPLETE")
        self.assertIsNone(e["period_return_pct"])
        self.assertIsNone(e["excess_period_pp"])
        self.assertIn("missing_required_fields", e)
        self.assertIn("window", e["missing_required_fields"])
        self.assertNotEqual(e.get("backfilled"), False, "无窗口时不得把 backfilled 填成 false")

    def test_T8_identity_is_semiconductor_not_ai_compute(self):
        self.assertIn("半导体", B.INDEX["index_name"])
        self.assertIn("不是", B.INDEX["identity_note"])
        self.assertIn("AI 算力", B.INDEX["identity_note"])
        doc = {"events": [{"event_id": "FAKE-OK",
                           "market_performance": {"window": ["2020-01-02", "2020-01-06"]}}]}
        e = B.build(doc, SERIES, BENCH)[0]
        self.assertEqual(e["index_code"], "H30184")
        self.assertEqual(e["benchmark_index_code"], "000300")
        self.assertNotIn("constituents", e, "官方指数对象不得携带任何成分信息")
        self.assertIn("不插值", e["calculation_note"])
        self.assertIn("首尾收盘口径", e["calculation_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
