#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""季节性发现 v0_5 的**校验器不变量测试**（v0.42）。

只测「校验器是否真的在把关」，不重复测产物结构：

1. 改 `criteria.exploratory.min_hit_rate` → `--check` 必须失败（此前只查 median，能蒙混过关）；
2. `scan_audit` 年限分组**互斥且可加总**，并与 `records` / 产物条数对得上；
3. OOS 检验数不足时**不得**被标成 REPORTED，也不得用历史统计替代（双向都测）；
4. 数据库可用时，窗口关键指标漂移（改一个中位超额）必须报错；
5. 数据库缺失时，输出必须明确「仅结构 + SKIP 源数据核对」，不得说成源数据已重算。

运行：`python research/scripts/test_discover_seasonal_patterns_v0_5.py`
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)

from research.scripts import discover_seasonal_patterns_v0_5 as m  # noqa: E402

DB_PRESENT = os.path.exists(m.DB) and os.environ.get("SEAS_NO_DB") != "1"   # 便于本地模拟 CI 场景
SRC = os.path.join(m.CURRENT, sorted(
    [f for f in os.listdir(m.CURRENT) if m.OUT_RE.match(f)],
    key=lambda f: int(m.OUT_RE.match(f).group(1)))[-1])


def _read_json(path):
    """显式关闭文件句柄（消除 ResourceWarning）。"""
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def _run_check(doc_mutator=None, src_checked=True):
    """在临时目录里放一份（可被改坏的）产物，调用 check() 并捕获输出。"""
    tmp = tempfile.mkdtemp(prefix="seas_check_")
    try:
        doc = _read_json(SRC)
        if doc_mutator:
            doc_mutator(doc)
        dst = os.path.join(tmp, os.path.basename(SRC))
        with open(dst, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        old_current = m.CURRENT
        m.CURRENT = tmp
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                if src_checked:
                    conn = m.sqlite3.connect(m.DB)
                    bench = m.load(conn, "CSI300")
                    as_of = bench[-1][0]
                    bounds = m.month_bounds(bench)
                    bh = {ym: v for ym, v in bounds.items() if ym < as_of[:6]}
                    br = m.month_returns(bench, bh)
                    rc = m.check(conn, as_of, bh, br)
                    conn.close()
                else:
                    rc = m.check(None, None, None, None)
        finally:
            m.CURRENT = old_current
        return rc, buf.getvalue()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class TestCriteriaGate(unittest.TestCase):
    """1 · 阈值校验遗漏（exploratory.min_hit_rate）"""

    def test_exploratory_min_hit_rate_mismatch_fails(self):
        def mutate(doc):
            doc["criteria"]["exploratory"]["min_hit_rate"] = 0.5
        rc, out = _run_check(mutate, src_checked=False)
        self.assertEqual(rc, 1, "改 exploratory.min_hit_rate 后 check 必须失败，实际通过：%s" % out)
        self.assertIn("min_hit_rate", out)

    def test_exploratory_min_median_mismatch_fails(self):
        def mutate(doc):
            doc["criteria"]["exploratory"]["min_median_excess"] = 0.5
        rc, out = _run_check(mutate, src_checked=False)
        self.assertEqual(rc, 1)
        self.assertIn("min_median_excess", out)

    def test_unmodified_artifact_passes_structure(self):
        rc, out = _run_check(None, src_checked=False)
        self.assertEqual(rc, 0, out)


class TestScanAudit(unittest.TestCase):
    """2 · 年限互斥分组与总量关系"""

    @classmethod
    def setUpClass(cls):
        cls.doc = _read_json(SRC)
        cls.sa = cls.doc["scan_audit"]

    def test_groups_are_mutually_exclusive_and_sum(self):
        yg = self.sa["years_group"]
        self.assertEqual(yg["lt_6"] + yg["6_to_7"] + yg["ge_8"], self.sa["pairs_with_data"],
                         "年限分组之和必须等于有数据的组合数")
        self.assertEqual(self.sa["pairs_scanned"], self.sa["series"] * 12,
                         "扫描量必须是「序列数 × 12 个月」")
        self.assertGreaterEqual(yg["lt_6"], 0)
        eg = self.sa["eligibility_group"]
        self.assertEqual(eg["pit_eligible"] + eg["never_eligible"],
                         self.sa["pairs_with_data"] - yg["lt_6"],
                         "资格分组之和必须等于「可检验」的组合数（≥6 年）")
        pd = self.sa["pit_eligible_detail"]
        self.assertEqual(pd["history_lt_8"] + pd["history_ge_8"], eg["pit_eligible"])
        hg = self.sa["history_group"]
        self.assertEqual(hg["strict"] + hg["exploratory"] + hg["below_threshold"], yg["ge_8"])

    def test_records_match_artifact_arrays(self):
        rec = self.sa["records"]
        self.assertEqual(rec["patterns"], len(self.doc["patterns"]))
        self.assertEqual(rec["pit_only"], len(self.doc["pit_only_patterns"]))
        self.assertEqual(rec["patterns"], rec["patterns_point_in_time"] + rec["patterns_full_sample_only"])
        self.assertEqual(rec["pit_only"], rec["pit_only_insufficient_history"] + rec["pit_only_below_threshold"])

    def test_reconcile_all_true(self):
        rc = self.sa.get("reconcile") or {}
        self.assertTrue(rc, "缺 reconcile 自洽断言")
        self.assertEqual([k for k, v in rc.items() if v is not True], [])

    def test_broken_reconcile_fails_check(self):
        def mutate(doc):
            doc["scan_audit"]["records"]["patterns"] += 1
        rc, out = _run_check(mutate, src_checked=False)
        self.assertEqual(rc, 1, out)
        self.assertIn("records.patterns", out)


class TestOOSInsufficiency(unittest.TestCase):
    """3 · OOS 样本不足不得被历史统计替代"""

    @classmethod
    def setUpClass(cls):
        cls.doc = _read_json(SRC)

    def test_no_reported_below_threshold(self):
        bad = [p["pattern_id"] for p in self.doc["patterns"]
               if p.get("oos_status") == "REPORTED" and p["oos_tests"] < m.MIN_OOS_TESTS]
        self.assertEqual(bad, [], "检验数不足却标 REPORTED：%s" % bad[:5])

    def test_insufficient_marked_insufficient(self):
        bad = [p["pattern_id"] for p in self.doc["patterns"]
               if p.get("oos_status") == "INSUFFICIENT_OOS" and p["oos_tests"] >= m.MIN_OOS_TESTS]
        self.assertEqual(bad, [], "检验数已达标却标 INSUFFICIENT_OOS：%s" % bad[:5])

    def test_pit_only_also_checked(self):
        bad = [p["pattern_id"] for p in self.doc["pit_only_patterns"]
               if p.get("oos_status") == "REPORTED" and p.get("oos_tests", 0) < m.MIN_OOS_TESTS]
        self.assertEqual(bad, [], "pit_only 里检验数不足却 REPORTED：%s" % bad[:5])

    def test_forged_reported_fails_check(self):
        """把一个 OOS 不足的模式硬改成 REPORTED → 校验必须失败（不能靠历史统计充数）。"""
        target = next(p for p in self.doc["patterns"] if p.get("oos_tests", 0) < m.MIN_OOS_TESTS)

        def mutate(doc):
            for p in doc["patterns"]:
                if p["pattern_id"] == target["pattern_id"]:
                    p["oos_status"] = "REPORTED"
                    p["oos_hit_rate"] = 0.99
        rc, out = _run_check(mutate, src_checked=False)
        self.assertEqual(rc, 1, out)
        self.assertIn("OOS 年数不足却报告", out)

    def test_tier_split_sums_to_oos_tests(self):
        bad = []
        for p in self.doc["patterns"] + self.doc["pit_only_patterns"]:
            by = p.get("oos_by_train_tier") or {}
            s = (by.get("STRICT") or {}).get("tests", 0)
            e = (by.get("EXPLORATORY") or {}).get("tests", 0)
            if s + e != p.get("oos_tests", 0):
                bad.append((p["pattern_id"], s, e, p.get("oos_tests")))
        self.assertEqual(bad, [], "两层检验数之和不等于 oos_tests：%s" % bad[:5])


@unittest.skipUnless(DB_PRESENT, "history_scan.db 不存在（CI 场景）→ 跳过源数据核对用例")
class TestSourceDataCheck(unittest.TestCase):
    """4 · 数据库可用时，窗口关键指标漂移必须报错"""

    def test_clean_artifact_passes_window_metric_check(self):
        rc, out = _run_check(None, src_checked=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("窗口指标核对", out)
        self.assertIn("不是", out)   # 必须声明「不是完整复现」

    def test_median_drift_detected(self):
        def mutate(doc):
            w = doc["current_windows"][0]
            w["median_excess_pct"] = round(w["median_excess_pct"] + 1.23, 2)
        rc, out = _run_check(mutate, src_checked=True)
        self.assertEqual(rc, 1, out)
        self.assertIn("median_excess_pct", out)

    def test_pit_years_drift_detected(self):
        def mutate(doc):
            w = doc["current_windows"][0]
            w["pit_eligible_years"] = w["pit_eligible_years"] + 1
        rc, out = _run_check(mutate, src_checked=True)
        self.assertEqual(rc, 1, out)
        self.assertIn("pit_eligible_years", out)

    def test_tier_split_drift_detected(self):
        def mutate(doc):
            w = doc["current_windows"][0]
            w["oos_by_train_tier"]["STRICT"]["tests"] += 1
        rc, out = _run_check(mutate, src_checked=True)
        self.assertEqual(rc, 1, out)
        self.assertIn("oos_by_train_tier", out)


class TestNoDatabase(unittest.TestCase):
    """5 · 数据库缺失时必须明确区分结构检查与 SKIP"""

    def test_skip_message_is_explicit(self):
        rc, out = _run_check(None, src_checked=False)
        self.assertEqual(rc, 0, out)
        self.assertIn("SKIP 源数据核对", out)
        self.assertIn("仅结构", out)
        self.assertNotIn("窗口指标核对", out, "无库时不得声称做了窗口指标核对")

    def test_skip_still_catches_structure_errors(self):
        def mutate(doc):
            doc["protocol"] = "some_other_protocol"
        rc, out = _run_check(mutate, src_checked=False)
        self.assertEqual(rc, 1, out)
        self.assertIn("protocol", out)


class TestSyntheticDatabase(unittest.TestCase):
    """★ A3：用**小型临时 SQLite** 跑与真实数据相同的核对逻辑（不依赖 1.3GB 大库）。

    合成口径：2012–2022 共 11 个 3 月样本；板块 A 每月 3 月 +3%（STRICT），
    板块 B +1%（EXPLORATORY）→ 训练 5 年后逐年具资格，检验年 2017–2022 共 6 个（可报告）。
    基准为平盘，故超额 = 板块月收益。
    """

    YEARS = list(range(2012, 2023))
    MARCH_PCT = {"BK_TEST_A": 3.0, "BK_TEST_B": 1.0}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="seas_fixture_")
        self.db = os.path.join(self.tmp, "fixture.db")
        self._build_db()
        self._old = (m.DB, m.CURRENT)
        m.DB, m.CURRENT = self.db, self.tmp
        rc = m.main(["--write", "--version", "1"])
        self.assertEqual(rc, 0, "合成库上生成产物失败")
        self.art = os.path.join(self.tmp, "pattern_discovery_v0_1.json")

    def tearDown(self):
        m.DB, m.CURRENT = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---------- fixture ----------
    def _build_db(self):
        conn = sqlite3.connect(self.db)
        cur = conn.cursor()
        cur.execute("CREATE TABLE scan_series (series_id TEXT PRIMARY KEY, name TEXT, kind TEXT, "
                    "provider TEXT, symbol TEXT, price_type TEXT, first_date TEXT, last_date TEXT, "
                    "rows INTEGER, fetched_at TEXT, status TEXT, note TEXT)")
        cur.execute("CREATE TABLE scan_daily (series_id TEXT, trade_date TEXT, open REAL, high REAL, "
                    "low REAL, close REAL, volume REAL)")
        cur.execute("CREATE TABLE scan_meta (k TEXT PRIMARY KEY, v TEXT)")
        days = (5, 15, 25)
        bench = {}
        for y in self.YEARS:
            for mo in range(1, 13):
                for d in days:
                    bench["%04d%02d%02d" % (y, mo, d)] = 1000.0 + y + mo
        for d in days:                      # as_of 落点：2023-03（当月未走完）
            bench["202303%02d" % d] = 1000.0 + 2023 + 3
        cur.executemany("INSERT INTO scan_daily VALUES (?,?,?,?,?,?,?)",
                        [("CSI300", ds, cl, cl, cl, cl, 0.0) for ds, cl in bench.items()])
        cur.execute("INSERT INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("CSI300", "沪深300", "index", "fixture", "sh000300", "raw",
                     "20120105", "20230325", len(bench), "fixture", "OK", None))
        for sid, pct in self.MARCH_PCT.items():
            rows = []
            for y in self.YEARS:
                for mo in range(1, 13):
                    mult = 1.0 + (pct / 100.0 if mo == 3 else 0.0)
                    for d in days:
                        ds = "%04d%02d%02d" % (y, mo, d)
                        cl = 1000.0 * (mult if d == 25 else 1.0)
                        rows.append((sid, ds, cl, cl, cl, cl, 0.0))
            cur.executemany("INSERT INTO scan_daily VALUES (?,?,?,?,?,?,?)", rows)
            cur.execute("INSERT INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (sid, "测试板块" + sid[-1], "industry_board", "fixture", sid.lower(),
                         "raw", "20120105", "20221225", len(rows), "fixture", "OK", None))
        conn.commit()
        conn.close()

    # ---------- helpers ----------
    def _check(self):
        conn = sqlite3.connect(self.db)
        try:
            bench = m.load(conn, "CSI300")
            as_of = bench[-1][0]
            bounds = m.month_bounds(bench)
            bh = {ym: v for ym, v in bounds.items() if ym < as_of[:6]}
            br = m.month_returns(bench, bh)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = m.check(conn, as_of, bh, br)
            return rc, buf.getvalue()
        finally:
            conn.close()

    def _mutate(self, fn):
        doc = _read_json(self.art)
        fn(doc)
        with io.open(self.art, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)

    # ---------- cases ----------
    def test_fixture_artifact_is_wellformed(self):
        doc = _read_json(self.art)
        self.assertEqual(len(doc["current_windows"]), 2, "两个板块的 3 月窗口都应进入 current_windows")
        win = {p["board_series"]: p for p in doc["current_windows"]}
        a, b = win["BK_TEST_A"], win["BK_TEST_B"]
        self.assertEqual(a["tier"], "STRICT")
        self.assertEqual(b["tier"], "EXPLORATORY")
        self.assertEqual(a["n_years"], 11)
        self.assertEqual(a["oos_tests"], 6)
        self.assertEqual(a["oos_status"], "REPORTED")
        self.assertEqual(a["oos_hit_rate"], 1.0)
        self.assertEqual(a["oos_median_excess_pct"], 3.0)
        self.assertEqual(a["oos_by_train_tier"]["STRICT"]["tests"], 6)
        self.assertEqual(a["oos_by_train_tier"]["EXPLORATORY"]["tests"], 0)
        self.assertEqual(b["oos_by_train_tier"]["EXPLORATORY"]["tests"], 6)

    def test_clean_fixture_passes(self):
        rc, out = self._check()
        self.assertEqual(rc, 0, out)
        self.assertIn("窗口指标核对", out)

    # ★★ B（v0.44）：**历史窗口指标**漂移的负向回归 —— 数据库不动、只改产物
    def test_history_median_drift_detected(self):
        """只改 current_windows 的 median_excess_pct（历史中位超额）→ 必须失败并指出字段。"""
        self._mutate(lambda d: d["current_windows"][0].update(median_excess_pct=8.8))
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("median_excess_pct", out)
        self.assertIn("产物 8.8 ≠ 重算", out)

    def test_history_hit_rate_drift_detected(self):
        """只改历史命中率（hit_rate）→ 必须失败并指出字段。"""
        self._mutate(lambda d: d["current_windows"][0].update(hit_rate=0.5))
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("hit_rate", out)
        self.assertIn("产物 0.5 ≠ 重算", out)

    def test_history_n_years_drift_detected(self):
        """只改历史样本年数（n_years）→ 必须失败并指出字段。"""
        def mut(d):
            d["current_windows"][0]["n_years"] += 1
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("n_years", out)
        self.assertIn("≠ 重算", out)

    def test_oos_hit_rate_drift_detected(self):
        self._mutate(lambda d: d["current_windows"][0].update(oos_hit_rate=0.5))
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("oos_hit_rate", out)

    def test_oos_years_drift_detected(self):
        def mut(d):
            d["current_windows"][0]["oos_years"] = d["current_windows"][0]["oos_years"][:-1]
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("oos_years", out)

    def test_tier_median_drift_detected(self):
        def mut(d):
            d["current_windows"][0]["oos_by_train_tier"]["STRICT"]["median_excess_pct"] = 9.9
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("oos_by_train_tier.STRICT.median_excess_pct", out)

    def test_tier_status_drift_detected(self):
        def mut(d):
            d["current_windows"][0]["oos_by_train_tier"]["EXPLORATORY"]["status"] = "REPORTED"
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("oos_by_train_tier.EXPLORATORY.status", out)

    # ★ A1 负向：只改分组计数、保留 reconcile=true → 必须失败
    def test_forged_reconcile_cannot_hide_lt6_error(self):
        def mut(d):
            d["scan_audit"]["years_group"]["lt_6"] += 1     # reconcile 仍是全 true
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("分组计数不自洽", out)
        self.assertIn("years_group_sums_to_with_data", out)

    def test_forged_reconcile_cannot_hide_eligible_error(self):
        def mut(d):
            d["scan_audit"]["eligibility_group"]["pit_eligible"] += 1
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("分组计数不自洽", out)

    def test_stale_true_flag_detected_even_if_relation_holds(self):
        """关系本身成立、但记录值与重算不一致（例如少记一条键）→ 必须失败。"""
        def mut(d):
            d["scan_audit"]["reconcile"].pop("pit_only_splits")
        self._mutate(mut)
        rc, out = self._check()
        self.assertEqual(rc, 1, out)
        self.assertIn("键集合", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
