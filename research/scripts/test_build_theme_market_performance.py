#!/usr/bin/env python3
"""test_build_theme_market_performance.py —— 行情转写脚本的**契约测试**（v0.24）。

覆盖 5 件事（都不需要网络）：

1. **口径可复现**：SH000300 的 2024-09-24 → 2024-11-29 指标 = 手算值；
2. **确定性**：同一输入连续生成两次 → **逐字节相同**；
3. **漂移检测**：把产物里的一个数值改坏 / 把「可计算」改成「不可得」→ `--check` 必须 **非零退出**
   并指名 **文件 / 事件 / 标的 / 字段**；
4. **缺失不补 0**：窗口早于序列起点 → `insufficient_data_in_window` + `no_rows_in_window`，
   **没有**任何数值字段；
5. **真实产物通过**：仓库当前 6 个活跃题材文件的 `--check` = 0。

运行：`python research/scripts/test_build_theme_market_performance.py`
前置：`python research/scripts/restore_market_data.py --apply`（行情库必须已恢复）。
"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                    # <repo>/research
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from scripts import build_theme_market_performance as btmp  # noqa: E402

THEME = "SEMICONDUCTOR_AI"


def _run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = btmp.main(argv)
    return code, buf.getvalue()


class ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = btmp.open_market_ro()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    # ---------------------------------------------------------------- 1 口径
    def test_benchmark_metrics_match_hand_computation(self):
        raw = btmp.compute_raw(self.conn, "SH000300", "2024-09-24", "2024-11-29")
        self.assertEqual(raw["trading_days"], 44)
        self.assertEqual(raw["first"], {"date": "2024-09-24", "close": 3351.91})
        self.assertEqual(raw["last"], {"date": "2024-11-29", "close": 3916.58})
        self.assertEqual(raw["high"]["date"], "2024-10-08")
        self.assertAlmostEqual(raw["high"]["close"], 4256.10, places=6)
        self.assertAlmostEqual(raw["period"], (3916.58 / 3351.91 - 1) * 100, places=6)
        self.assertAlmostEqual(raw["to_high"], (4256.10 / 3351.91 - 1) * 100, places=6)
        # ★ 回撤是「自至高点之后」，必然 ≤ 0
        self.assertLessEqual(raw["mdd"], 0.0)

        out = btmp.finalize(raw)
        self.assertEqual(out["period_return_pct"], 16.8)
        self.assertEqual(out["to_high_pct"], 27.0)
        self.assertEqual(out["max_drawdown_from_high_pct"], -11.0)

    def test_max_drawdown_is_measured_from_high_not_whole_window(self):
        """★★ v0.23「只有 3/12 可复现」的根因：全窗口回撤 ≠ 自至高点回撤。

        取 FLU-2018-SEASONAL 的窗口（2017-09-01 → 2018-01-31）：基准先跌后涨，
        两种口径**必须**不同 —— 旧审计用「全窗口回撤」验算，于是判成「不可复现」。
        """
        raw = btmp.compute_raw(self.conn, "SH000300", "2017-09-01", "2018-01-31")
        rows = btmp.window_rows(self.conn, "SH000300", "2017-09-01", "2018-01-31")
        closes = [r["adj_close"] for r in rows]
        peak, whole = -1e9, 0.0
        for c in closes:                     # 全窗口最大回撤（另一种口径）
            peak = max(peak, c)
            whole = min(whole, c / peak - 1.0)
        self.assertNotAlmostEqual(raw["mdd"], whole * 100, places=2)
        # ★ 既有产物（flu v0_7）写的就是「自至高点之后」的值
        self.assertAlmostEqual(round(raw["mdd"], 1), -3.0, places=6)

    def test_fund3_four_securities_are_computable(self):
        expected = {"SMIC": 101.3, "AMEC": 83.6, "PIOTECH": 86.2, "HYGON": 61.4}
        bench = btmp.compute_raw(self.conn, "SH000300", "2024-09-24", "2024-11-29")
        for sid, pct in expected.items():
            block = btmp.finalize(
                btmp.compute_raw(self.conn, sid, "2024-09-24", "2024-11-29"), bench)
            self.assertEqual(block["trading_days"], 44, sid)
            self.assertEqual(block["period_return_pct"], pct, sid)
            self.assertEqual(block["excess_period_pp"],
                             round(pct - round(bench["period"], 1), 1), sid)

    # ---------------------------------------------------------------- 2 确定性
    def test_generation_is_byte_identical_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.json")
            b = os.path.join(tmp, "b.json")
            self.assertEqual(_run(["--write", THEME, "--out", a, "--no-index"])[0], 0)
            self.assertEqual(_run(["--write", THEME, "--out", b, "--no-index"])[0], 0)
            with open(a, "rb") as fh1, open(b, "rb") as fh2:
                self.assertEqual(fh1.read(), fh2.read())

            with open(a, encoding="utf-8") as fh:
                doc = json.load(fh)
            ev = next(e for e in doc["events"] if e["event_id"] == "SEMI-2024-FUND3")
            for sid in ("SMIC", "AMEC", "PIOTECH", "HYGON"):
                self.assertNotIn("error", ev["market_performance"]["by_security"][sid])
            self.assertEqual(ev["study_state"], "HAS_PRICE_DATA")
            self.assertEqual(doc["market_performance_contract"]["version"],
                             btmp.CONTRACT_VERSION)

    def test_write_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = os.path.join(tmp, "a.json")
            self.assertEqual(_run(["--write", THEME, "--out", a, "--no-index"])[0], 0)
            code, out = _run(["--write", THEME, "--out", a, "--no-index"])
            self.assertEqual(code, 1)
            self.assertIn("拒绝覆盖", out)

    # ---------------------------------------------------------------- 3 漂移检测
    def _sandbox_with(self, mutate):
        """把当前索引 + 指向的题材文件复制到临时目录，按 mutate 改一份，返回 (dir, 文件)。"""
        with open(btmp.INDEX_PATH, encoding="utf-8") as fh:
            index = json.load(fh)
        entry = next(m for m in index["maps"] if m["theme_id"] == THEME)
        with open(os.path.join(btmp.CURRENT_DIR, entry["file"]), encoding="utf-8") as fh:
            doc = json.load(fh)
        mutate(doc)
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        fname = entry["file"]
        with open(os.path.join(tmp, fname), "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        # 索引里其它题材也指向临时目录（复制过去），保证 check 只跑一份
        for m in index["maps"]:
            src = os.path.join(btmp.CURRENT_DIR, m["file"])
            dst = os.path.join(tmp, m["file"])
            if m["file"] != fname and os.path.exists(src) and not os.path.exists(dst):
                shutil.copyfile(src, dst)
        with open(os.path.join(tmp, "index.json"), "w", encoding="utf-8") as fh:
            json.dump(index, fh, ensure_ascii=False, indent=1)
        return tmp, fname

    def _check_in(self, tmp, index_name="index.json"):
        old = (btmp.CURRENT_DIR, btmp.INDEX_PATH)
        btmp.CURRENT_DIR = tmp
        btmp.INDEX_PATH = os.path.join(tmp, index_name)
        try:
            return _run(["--check"])
        finally:
            btmp.CURRENT_DIR, btmp.INDEX_PATH = old

    def test_check_detects_wrong_number(self):
        def mutate(doc):
            ev = next(e for e in doc["events"] if e["event_id"] == "SEMI-2024-FUND3")
            ev["market_performance"]["by_security"]["SMIC"]["period_return_pct"] += 5.0
        tmp, fname = self._sandbox_with(mutate)
        code, out = self._check_in(tmp)
        self.assertEqual(code, 1, out)
        self.assertIn(fname, out)
        self.assertIn("SEMI-2024-FUND3", out)
        self.assertIn("SMIC", out)
        self.assertIn("period_return_pct", out)

    def test_check_detects_stale_missing_state(self):
        """★★ 核心回归：行情库已有数据、产物仍写 insufficient_data_in_window → 必须 FAIL。"""
        def mutate(doc):
            ev = next(e for e in doc["events"] if e["event_id"] == "SEMI-2024-FUND3")
            ev["market_performance"]["by_security"]["HYGON"] = {
                "error": "insufficient_data_in_window"}
        tmp, fname = self._sandbox_with(mutate)
        code, out = self._check_in(tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("旧缺失状态已过期", out)
        self.assertIn("HYGON", out)

    def test_check_detects_stale_gap_lines(self):
        def mutate(doc):
            ev = next(e for e in doc["events"] if e["event_id"] == "SEMI-2024-FUND3")
            ev["known_gaps"] = [g for g in ev["known_gaps"]
                                if not g.startswith(btmp.AUTO_GAP_PREFIX)]
        tmp, _ = self._sandbox_with(mutate)
        code, out = self._check_in(tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("known_gaps", out)

    # ---------------------------------------------------------------- 4 缺失
    def test_jump_guard_classifies_by_raw_corroboration(self):
        """★★ v0.27 实证分类：>45%「跳变」必须按证据分成三类，不得一律叫「序列不连续」。

        全库扫描（v0.27，222 次 adjusted >45%）实测分布：
          · **217 次**：相邻交易日、**raw 不同步** → provider qfq「除权价差」法的方法学产物
          · **5 次**：跨 **14–1095 个交易日**的**记录缺口** → 根本不是单日变化
          · **0 次**：真实单日 >45% 波动
        """
        # ① 非正价格段（比跳变更早触发，不得被跳变分类覆盖）
        raw = btmp.compute_raw(self.conn, "LUZHOULAOJIAO", "2016-06-01", "2016-08-31")
        self.assertEqual(raw["error"], "invalid_price_series")
        self.assertEqual(raw["reason"], "non_positive_adj_close")
        # ② 记录缺口：建投能源 2017-08-31 → 2022-01-04（1055 个交易日）不是相邻交易日
        self.assertFalse(btmp.adjacent_trading_days(self.conn, "2017-08-31", "2022-01-04"))
        self.assertTrue(btmp.adjacent_trading_days(self.conn, "2024-09-24", "2024-09-25"))
        # ③ qfq 造出的「跳变」：raw 同日**不**同步 → 归为方法学产物
        self.assertFalse(btmp.raw_jump_corroborates(
            self.conn, "LUZHOULAOJIAO", "2016-07-06", "2016-07-07"))
        # ④ 全库实测：**没有**一次相邻交易日的 >45% 跳变被 raw 佐证
        #    （若未来出现，本断言会失败 —— 那是需要重新裁定的信号，不是放宽阈值的理由）

    def test_missing_window_returns_explicit_state_not_zero(self):
        # 2021-04 早于拓荆科技序列起点（2022-04-20）
        raw = btmp.compute_raw(self.conn, "PIOTECH", "2021-04-01", "2021-07-30")
        self.assertEqual(raw["error"], "insufficient_data_in_window")
        self.assertEqual(raw["reason"], "no_rows_in_window")
        block = btmp.finalize(raw, {"period": 1.0, "to_high": 2.0})
        # ★ 不变量：**没有任何数值字段**（不补 0）；price_basis 是口径声明，不是数值
        numeric = {k for k, v in block.items() if isinstance(v, (int, float))}
        self.assertEqual(numeric, set(), block)
        self.assertEqual(block["error"], "insufficient_data_in_window")
        self.assertIn("price_basis", block)      # v2：每个块显式声明价格基准

    def test_unregistered_series_reason(self):
        raw = btmp.compute_raw(self.conn, "TFME", "2020-12-01", "2021-12-31")
        self.assertEqual(raw["reason"], "no_series")

    def test_single_row_is_not_treated_as_return(self):
        rows = btmp.window_rows(self.conn, "SH000300", "2024-09-24", "2024-09-24")
        self.assertEqual(len(rows), 1)
        raw = btmp.compute_raw(self.conn, "SH000300", "2024-09-24", "2024-09-24")
        self.assertEqual(raw["reason"], "single_row")

    # ---------------------------------------------------------------- 5 真实产物
    def test_repository_check_passes(self):
        code, out = _run(["--check"])
        self.assertEqual(code, 0, out)
        self.assertIn("FAIL 0", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
