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

Wave 2.1.1（闸门加固）追加：
  T9  无任何授权参数 → 拒绝；T10 只有 `--i-have-license` → 拒绝；T11 只有 `--license-basis` → 拒绝
  T12 合法组合 → 判定 PRODUCTION，且产物区分「操作人员提交的依据」与「程序核验」
  T13 符号链接 / 仓库内其他受跟踪路径**不能**绕过
  T14 拒绝时**不联网**（fetch 计数为 0）、不建目录、不生成文件
  T15 默认 `.tmp/` 本地实验输出不受影响（无需授权即可写）

运行：`python research/scripts/test_official_index_parallel.py`
"""
from __future__ import annotations

import datetime as _dt
import io
import json
import os
import shutil
import sys
import tempfile
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


class TestLicenseGate(unittest.TestCase):
    """★★ Wave 2.1.1：写入闸门的六种拒绝/放行情形（纯函数 + 集成，均不联网）。"""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="oi_gate_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._saved = (B.PRODUCTION_DIR, B.LOCAL_EXPERIMENT_DIR, B.REPO_ROOT,
                       B.fetch_series, B.latest_events_path)

    def tearDown(self):
        (B.PRODUCTION_DIR, B.LOCAL_EXPERIMENT_DIR, B.REPO_ROOT,
         B.fetch_series, B.latest_events_path) = self._saved

    # ── 纯函数：分类 ──
    def test_T9_no_license_args_refused(self):
        kind, _, problems = B.check_write_gate(os.path.join(B.CURRENT, "x.json"), False, "")
        self.assertEqual(kind, "PRODUCTION")
        self.assertEqual(len(problems), 2, "缺两个条件必须都报出来：%s" % problems)
        self.assertTrue(any("--i-have-license" in p for p in problems))
        self.assertTrue(any("--license-basis" in p for p in problems))

    def test_T10_only_flag_refused(self):
        kind, _, problems = B.check_write_gate(os.path.join(B.CURRENT, "x.json"), True, "")
        self.assertEqual(kind, "PRODUCTION")
        self.assertEqual(len(problems), 1)
        self.assertIn("--license-basis", problems[0])

    def test_T11_only_basis_refused(self):
        kind, _, problems = B.check_write_gate(os.path.join(B.CURRENT, "x.json"), False,
                                              "some basis")
        self.assertEqual(kind, "PRODUCTION")
        self.assertEqual(len(problems), 1)
        self.assertIn("--i-have-license", problems[0])

    def test_T11b_blank_basis_refused(self):
        _, _, problems = B.check_write_gate(os.path.join(B.CURRENT, "x.json"), True, "   ")
        self.assertEqual(len(problems), 1, "空白 basis 必须视为「未提供」")

    def test_T12_legit_combo_passes_and_record_distinguishes(self):
        kind, resolved, problems = B.check_write_gate(os.path.join(B.CURRENT, "x.json"),
                                                      True, "TEST-BASIS https://example.invalid/lic")
        self.assertEqual(kind, "PRODUCTION")
        self.assertEqual(problems, [])
        self.assertTrue(resolved.endswith("x.json"))
        rec = B.build_license_record(kind, "TEST-BASIS https://example.invalid/lic")
        # ★ 程序不得因为开关就宣称「已核验许可」
        self.assertEqual(rec["state"], "UNCLEAR")
        self.assertIs(rec["program_verified"], False)
        self.assertEqual(rec["operator_attestation"]["basis"],
                         "TEST-BASIS https://example.invalid/lic")
        self.assertIn("操作人员提交", rec["operator_attestation"]["note"])
        # 本地实验不产生 operator_attestation
        self.assertIsNone(B.build_license_record("LOCAL_EXPERIMENT", "")["operator_attestation"])

    def test_T13_symlink_and_other_tracked_paths_cannot_bypass(self):
        # ① 指向 research/current 的符号链接 → 必须识别为 PRODUCTION 并要求授权
        link = os.path.join(self.tmp, "alias_to_current")
        os.symlink(B.PRODUCTION_DIR, link)
        kind, resolved, problems = B.check_write_gate(os.path.join(link, "x.json"), False, "")
        self.assertEqual(kind, "PRODUCTION", "符号链接必须解析后再判定（resolved=%s）" % resolved)
        self.assertTrue(problems)
        # ② 仓库内其他受 Git 跟踪的路径 → FORBIDDEN
        for p in ("research/research/reports/x.json", "docs/x.json", "src/x.json"):
            kind2, _, problems2 = B.check_write_gate(os.path.join(B.REPO_ROOT, p), True,
                                                    "basis")
            self.assertEqual(kind2, "FORBIDDEN", p)
            self.assertTrue(problems2, p)
        # ③ 仓库外路径 → FORBIDDEN
        kind3, _, problems3 = B.check_write_gate(os.path.join(self.tmp, "outside.json"), True,
                                                "basis")
        self.assertEqual(kind3, "FORBIDDEN")
        self.assertTrue(problems3)

    def test_T14_refusal_does_not_fetch_or_create(self):
        calls = {"n": 0}

        def bomb(*a, **k):
            calls["n"] += 1
            raise AssertionError("拒绝路径不得联网取数")

        B.fetch_series = bomb
        target = os.path.join(B.CURRENT, "_gate_should_not_exist.json")
        for argv in (["--write", "--out", target],                                    # 无授权
                     ["--write", "--out", target, "--i-have-license"],                # 只有开关
                     ["--write", "--out", target, "--license-basis", "b"]):           # 只有依据
            rc = B.main(argv)
            self.assertEqual(rc, 2, argv)
            self.assertFalse(os.path.exists(target), "拒绝时不得创建文件：%s" % argv)
        self.assertEqual(calls["n"], 0, "拒绝路径不得联网")
        # 仓库内其他受跟踪路径同样拒绝（且不联网）
        rc2 = B.main(["--write", "--out", os.path.join(B.REPO_ROOT, "docs", "_no.json"),
                      "--i-have-license", "--license-basis", "b"])
        self.assertEqual(rc2, 2)
        self.assertEqual(calls["n"], 0)
        self.assertFalse(os.path.exists(os.path.join(B.REPO_ROOT, "docs", "_no.json")))

    def test_T15_local_experiment_unaffected(self):
        kind, _, problems = B.check_write_gate(B.DEFAULT_OUT, False, "")
        self.assertEqual(kind, "LOCAL_EXPERIMENT")
        self.assertEqual(problems, [])
        # 集成：把取数与事件源都替换为合成数据，写到 .tmp 下的临时子目录
        out = os.path.join(B.LOCAL_EXPERIMENT_DIR, "_gate_test", "ok.json")
        self.addCleanup(shutil.rmtree, os.path.dirname(out), True)
        B.fetch_series = lambda code, *a, **k: (SERIES if code == "H30184" else BENCH)
        ev = os.path.join(self.tmp, "events.json")
        io.open(ev, "w", encoding="utf-8").write(json.dumps(
            {"events": [{"event_id": "FAKE-1",
                         "market_performance": {"window": ["2020-01-02", "2020-01-06"]}}]}))
        B.latest_events_path = lambda: ev
        rc = B.main(["--write", "--out", out])
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.exists(out))
        doc = json.loads(io.open(out, encoding="utf-8").read())
        self.assertEqual(doc["license"]["target_kind"], "LOCAL_EXPERIMENT")
        self.assertIsNone(doc["license"]["operator_attestation"])
        self.assertIs(doc["license"]["program_verified"], False)
        self.assertEqual(doc["summary"]["computed"], 1)

    def test_T16_production_write_records_operator_basis(self):
        """合法组合的**集成**路径：产物必须记录操作人员依据，且 state 仍 UNCLEAR。"""
        prod = os.path.join(self.tmp, "fake_current")
        os.makedirs(prod)
        B.PRODUCTION_DIR = os.path.realpath(prod)
        B.fetch_series = lambda code, *a, **k: (SERIES if code == "H30184" else BENCH)
        ev = os.path.join(self.tmp, "events.json")
        io.open(ev, "w", encoding="utf-8").write(json.dumps(
            {"events": [{"event_id": "FAKE-1",
                         "market_performance": {"window": ["2020-01-02", "2020-01-06"]}}]}))
        B.latest_events_path = lambda: ev
        out = os.path.join(prod, "official.json")
        rc = B.main(["--write", "--out", out, "--i-have-license",
                     "--license-basis", "TEST-BASIS https://example.invalid/lic"])
        self.assertEqual(rc, 0)
        doc = json.loads(io.open(out, encoding="utf-8").read())
        self.assertEqual(doc["license"]["target_kind"], "PRODUCTION")
        self.assertEqual(doc["license"]["state"], "UNCLEAR", "不得因开关自动改为已确认")
        self.assertIs(doc["license"]["program_verified"], False)
        self.assertEqual(doc["license"]["operator_attestation"]["basis"],
                         "TEST-BASIS https://example.invalid/lic")


if __name__ == "__main__":
    unittest.main(verbosity=2)

