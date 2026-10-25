#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_candidate_ledger_v0_2.py —— 候选账本 v0_2 的**负向对照**测试。

★ 为什么必须有负向对照：v0_1 的 `--check` 要求「最新账本 == 最初快照」，
  一旦行情推进就永久 FAIL，只能靠覆盖快照「修复」→ 那是个**假检查**。
  本文件的每一条都在证明「检查确实会失败」，而不是只证明「干净数据能 PASS」。

覆盖：
  T1  干净副本 PASS（基线）
  T2  改冻结形成快照 → F6 FAIL
  T3  同一实例被两次登记为新实例 → F3 FAIL
  T4  instance_id 与 (board_series, window_year, month) 不符 → F2 FAIL
  T5  账本里改已结算数字 → S1 FAIL
  T6  把 IN_WINDOW_PARTIAL 改成 FORWARD_PENDING → S4 FAIL
  T7  结算日晚于 market_as_of → S3 FAIL
  T8  冻结文件内容不同 → `_write_guard` 拒绝（返回 False，不覆盖）
  T9  instance_id 稳定性：同一板块同一目标月在不同 as_of 下 id 相同
  T10 追加式日志：改动历史批次 → `save_log` 拒绝

运行：
    python research/scripts/test_candidate_ledger_v0_2.py
    python research/scripts/test_candidate_ledger_v0_2.py -v
"""
from __future__ import annotations

import copy
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import warnings

# 本仓库统一用 io.open(...).read() 的紧凑写法（不显式 close）→ 屏蔽 ResourceWarning 噪声
warnings.simplefilter("ignore", ResourceWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_candidate_ledger_v0_2 as L  # noqa: E402

HAS_DB = os.path.exists(L.DB)
HAS_LOG = os.path.exists(os.path.join(L.CURRENT, L.LOG_NAME))
HAS_LEDGER = os.path.exists(os.path.join(L.CURRENT, L.OUT_NAME))


def setUpModule():
    # 本仓库统一用 io.open(...).read() 的紧凑写法（不显式 close）→ 屏蔽 ResourceWarning 噪声
    warnings.simplefilter("ignore", ResourceWarning)


def _latest_in(pattern, folder):
    """按版本号（数字）取某个目录下的最新产物 —— `L._latest` 只会读全局 CURRENT。"""
    hits = [(int(pattern.match(f).group(1)), f) for f in os.listdir(folder) if pattern.match(f)]
    if not hits:
        raise AssertionError("缺产物 %s in %s" % (pattern.pattern, folder))
    return os.path.join(folder, sorted(hits)[-1][1])


class _Temp:
    """把 CURRENT / SNAP_DIR 指到临时目录，并在退出时还原。"""

    def __init__(self):
        self.tmp = tempfile.mkdtemp(prefix="ledger_v0_2_")

    def __enter__(self):
        self.old = (L.CURRENT, L.SNAP_DIR)
        L.CURRENT = os.path.join(self.tmp, "current")
        L.SNAP_DIR = os.path.join(L.CURRENT, "candidate_ledger_snapshots")
        os.makedirs(L.SNAP_DIR, exist_ok=True)
        for name in (L.LOG_NAME, L.OUT_NAME):
            src = os.path.join(self.old[0], name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(L.CURRENT, name))
        src_snap = os.path.join(self.old[1])
        if os.path.isdir(src_snap):
            for f in os.listdir(src_snap):
                if f.endswith(".json"):
                    shutil.copy2(os.path.join(src_snap, f), os.path.join(L.SNAP_DIR, f))
        return self

    def __exit__(self, *a):
        L.CURRENT, L.SNAP_DIR = self.old
        shutil.rmtree(self.tmp, ignore_errors=True)
        return False

    # 便捷读写
    def log(self):
        return json.load(io.open(os.path.join(L.CURRENT, L.LOG_NAME), encoding="utf-8"))

    def set_log(self, doc):
        io.open(os.path.join(L.CURRENT, L.LOG_NAME), "w", encoding="utf-8", newline="\n").write(
            L._dump(doc))

    def ledger(self):
        return json.load(io.open(os.path.join(L.CURRENT, L.OUT_NAME), encoding="utf-8"))

    def set_ledger(self, doc):
        io.open(os.path.join(L.CURRENT, L.OUT_NAME), "w", encoding="utf-8", newline="\n").write(
            L._dump(doc))

    def snap(self, name):
        return os.path.join(L.SNAP_DIR, name)


@unittest.skipUnless(HAS_LOG and HAS_LEDGER, "缺账本产物 → 跳过")
class TestLedgerV02(unittest.TestCase):

    # ── T1 基线 ──
    def test_T1_clean_copy_passes(self):
        with _Temp() as t:
            f, w, n = L.check_formations(t.log())
            self.assertEqual(f, [], "干净副本的形成检查不应失败")
            if HAS_DB:
                f2, w2, n2 = L.check_settlement(t.log(), t.ledger(), t.ledger()["market_as_of"])
                self.assertEqual(f2, [], "干净副本的结算检查不应失败")

    # ── T2 冻结形成快照被改 ──
    def test_T2_tampered_formation_snapshot_fails(self):
        with _Temp() as t:
            log = t.log()
            bid = log["batches"][0]["batch_id"]
            p = t.snap("%s.json" % bid)
            d = json.load(io.open(p, encoding="utf-8"))
            d["instances"][0]["selection_basis"]["hit_rate"] = 0.99
            io.open(p, "w", encoding="utf-8", newline="\n").write(L._dump(d))
            f, _, _ = L.check_formations(log)
            self.assertTrue(any(x.startswith("F6") for x in f),
                            "改冻结快照必须被 F6 抓到，实际：%s" % f)

    # ── T3 同一实例被两次登记为新实例 ──
    def test_T3_duplicate_instance_registration_fails(self):
        with _Temp() as t:
            log = t.log()
            b0 = log["batches"][0]
            dup = copy.deepcopy(b0["instances"][0])
            b1 = {"batch_id": "CF-2099-01-01-01", "formed_at": "2099-01-01",
                  "source": {"pattern_discovery": None, "candidate_digest": None,
                             "migrated_from": None},
                  "counts": {"new_instances": 1, "reappeared": 0, "by_kind": {}},
                  "reappearances": [], "instances": [dup]}
            log["batches"].append(b1)
            t.set_log(log)
            # 同步写一个匹配的快照，确保失败原因**只**是 F3 而不是 F6
            io.open(t.snap("%s.json" % b1["batch_id"]), "w", encoding="utf-8",
                    newline="\n").write(L._dump(b1))
            f, _, _ = L.check_formations(log)
            self.assertTrue(any(x.startswith("F3") for x in f),
                            "重复登记必须被 F3 抓到，实际：%s" % f)
            self.assertFalse(any(x.startswith("F6") for x in f),
                             "本用例不应触发 F6（快照已同步）：%s" % f)

    # ── T4 instance_id 不自洽 ──
    def test_T4_instance_id_mismatch_fails(self):
        with _Temp() as t:
            log = t.log()
            b0 = log["batches"][0]
            b0["instances"][0]["instance_id"] = "WRONG__1999-01"
            t.set_log(log)
            io.open(t.snap("%s.json" % b0["batch_id"]), "w", encoding="utf-8",
                    newline="\n").write(L._dump(b0))
            f, _, _ = L.check_formations(log)
            self.assertTrue(any(x.startswith("F2") for x in f),
                            "instance_id 不自洽必须被 F2 抓到，实际：%s" % f)

    # ── T5 改已结算数字 ──
    @unittest.skipUnless(HAS_DB, "缺 history_scan.db → 跳过结算类用例")
    def test_T5_tampered_settlement_value_fails(self):
        with _Temp() as t:
            led = t.ledger()
            victim = next(c for c in led["candidates"] if c["settled_horizons"])
            old = victim["outcome"]["5"]["excess_pp"]
            victim["outcome"]["5"]["excess_pp"] = round((old or 0) + 9.99, 2)
            t.set_ledger(led)
            io.open(t.snap("CL-%s-v0_2.json" % led["market_as_of"]), "w", encoding="utf-8",
                    newline="\n").write(L._dump(led))
            f, _, _ = L.check_settlement(t.log(), led, led["market_as_of"])
            self.assertTrue(any(x.startswith("S1") for x in f),
                            "改结算数字必须被 S1 抓到，实际：%s" % f)

    # ── T6 结果类型被改写 ──
    @unittest.skipUnless(HAS_DB, "缺 history_scan.db → 跳过结算类用例")
    def test_T6_wrong_outcome_type_fails(self):
        with _Temp() as t:
            led = t.ledger()
            victim = next(c for c in led["candidates"] if c["outcome_type"] == "IN_WINDOW_PARTIAL")
            victim["outcome_type"] = "FORWARD_PENDING"   # 把「窗口内观察」伪装成「真前瞻」
            t.set_ledger(led)
            io.open(t.snap("CL-%s-v0_2.json" % led["market_as_of"]), "w", encoding="utf-8",
                    newline="\n").write(L._dump(led))
            f, _, _ = L.check_settlement(t.log(), led, led["market_as_of"])
            self.assertTrue(any(x.startswith("S4") for x in f),
                            "改写结果类型必须被 S4 抓到，实际：%s" % f)

    # ── T7 结算日晚于 market_as_of（时间泄漏）──
    @unittest.skipUnless(HAS_DB, "缺 history_scan.db → 跳过结算类用例")
    def test_T7_settle_date_after_market_as_of_fails(self):
        with _Temp() as t:
            led = t.ledger()
            victim = next(c for c in led["candidates"] if c["settled_horizons"])
            victim["outcome"]["5"]["settle_date"] = "2099-12-31"
            t.set_ledger(led)
            io.open(t.snap("CL-%s-v0_2.json" % led["market_as_of"]), "w", encoding="utf-8",
                    newline="\n").write(L._dump(led))
            f, _, _ = L.check_settlement(t.log(), led, led["market_as_of"])
            self.assertTrue(any(x.startswith("S3") for x in f),
                            "结算日晚于结算日必须被 S3 抓到，实际：%s" % f)

    # ── T8 冻结文件拒绝覆盖 ──
    def test_T8_write_guard_refuses_overwrite(self):
        with _Temp() as t:
            p = os.path.join(L.SNAP_DIR, "CF-FROZEN.json")
            self.assertTrue(L._write_guard(p, "A\n", "测试冻结文件"))
            before = io.open(p, encoding="utf-8").read()
            self.assertFalse(L._write_guard(p, "B\n", "测试冻结文件"),
                             "内容不同时必须拒绝覆盖")
            self.assertEqual(io.open(p, encoding="utf-8").read(), before,
                             "拒绝后文件内容不得改变")
            self.assertTrue(L._write_guard(p, "A\n", "测试冻结文件"),
                            "内容相同应视为幂等成功")

    # ── T9 实例 ID 稳定性 ──
    def test_T9_instance_id_stable_across_runs(self):
        # 同一板块 + 同一目标年月 → 同一 id（与「哪一天形成的」无关）
        self.assertEqual(L.instance_id("CPT_lk", 2026, 11), L.instance_id("CPT_lk", 2026, 11))
        self.assertEqual(L.instance_id("CPT_lk", 2026, 11), "CPT_lk__2026-11")
        self.assertNotEqual(L.instance_id("CPT_lk", 2026, 11), L.instance_id("CPT_lk", 2027, 11),
                            "同一月份不同年份必须是不同实例（v0_1 的 candidate_id 做不到）")
        self.assertNotEqual(L.instance_id("CPT_lk", 2026, 11), L.instance_id("CPT_li", 2026, 11))

    # ── T10 追加式日志：历史批次不可改 ──
    def test_T10_log_is_append_only(self):
        with _Temp() as t:
            log = t.log()
            self.assertTrue(L.save_log(log), "原样重写应成功")
            bad = copy.deepcopy(log)
            bad["batches"][0]["instances"][0]["formed_at"] = "1999-01-01"
            self.assertFalse(L.save_log(bad), "改动历史批次必须被拒绝")
            self.assertEqual(t.log()["batches"][0]["instances"][0]["formed_at"],
                             log["batches"][0]["instances"][0]["formed_at"],
                             "拒绝后磁盘上的形成记录不得改变")

    # ── T11 账本落后于行情 → 只 WARN，不 FAIL ──
    @unittest.skipUnless(HAS_DB, "缺 history_scan.db → 跳过结算类用例")
    def test_T11_stale_ledger_warns_not_fails(self):
        """★ v0_1 的核心缺陷：行情推进后「最新账本 == 最初快照」必然 FAIL。
        v0_2 必须把「落后」判为 WARN（快照本身没错），把「同一结算日算错」判为 FAIL。"""
        with _Temp() as t:
            log = t.log()
            old_day = "2026-10-20"
            led_old = L.build_ledger(log, old_day)          # 钉在更早的结算日重建
            t.set_ledger(led_old)
            io.open(t.snap("CL-%s-v0_2.json" % old_day), "w", encoding="utf-8",
                    newline="\n").write(L._dump(led_old))
            f, w, _ = L.check_settlement(log, led_old, old_day)
            self.assertEqual(f, [], "自洽的旧结算日不应 FAIL：%s" % f)
            self.assertTrue(any(x.startswith("S5") for x in w),
                            "账本落后于行情必须给出 S5 WARN，实际：%s" % w)
            self.assertIn("落后", " ".join(w))

    # ── T12 ★★ 拒绝写入时不得留下部分修改（v0.52 修复的正是这个）──
    @unittest.skipUnless(HAS_DB, "缺 history_scan.db → 跳过写入类用例")
    def test_T12_refusal_leaves_no_partial_write(self):
        """预置同日冻结结算快照 → 模拟上游产物改变（多出一条窗口）→ 执行 --write。

        旧顺序会「先写形成快照、再追加形成日志、最后才发现结算快照冲突」→
        **拒绝却已改了形成日志**。本用例断言：拒绝 + 四个目标文件逐字节未变。
        """
        import contextlib
        import hashlib

        def sha(p):
            return hashlib.sha256(io.open(p, "rb").read()).hexdigest()

        with _Temp() as t:
            real_current = t.old[0]
            # 摘要与候选源都要就位（main 会读 _latest(PD_RE) / _latest(DIGEST_RE)）
            for pat in (L.PD_RE, L.DIGEST_RE):
                src = _latest_in(pat, real_current)
                shutil.copy2(src, os.path.join(L.CURRENT, os.path.basename(src)))

            log_p = os.path.join(L.CURRENT, L.LOG_NAME)
            out_p = os.path.join(L.CURRENT, L.OUT_NAME)
            led = t.ledger()
            cl_p = t.snap("CL-%s-v0_2.json" % led["market_as_of"])
            cf_p = t.snap("%s.json" % t.log()["batches"][0]["batch_id"])
            before = {k: sha(p) for k, p in
                      (("log", log_p), ("latest", out_p), ("CL", cl_p), ("CF", cf_p))}

            # 对照 1：没有上游改动时，同一条路径应当成功且**零修改**（幂等）
            buf0 = io.StringIO()
            with contextlib.redirect_stdout(buf0):
                rc0 = L.main(["--write"])
            self.assertEqual(rc0, 0, "无冲突时应成功：%s" % buf0.getvalue()[-600:])
            for name, p in (("log", log_p), ("latest", out_p), ("CL", cl_p), ("CF", cf_p)):
                self.assertEqual(sha(p), before[name], "无冲突重跑不应改变 %s" % name)

            # 模拟上游改变：多出一条窗口 → 形成内容变化 → 同日结算快照必然不同
            pd_src = _latest_in(L.PD_RE, real_current)
            pd = json.load(io.open(pd_src, encoding="utf-8"))
            extra = copy.deepcopy(pd["current_windows"][0])
            extra.update({"pattern_id": "SEAS-BK881121-M12", "board": "半导体",
                          "board_series": "BK881121", "kind": "industry_board",
                          "month": 12, "representative_stocks": None,
                          "rep_stock_gap": "行业板块无历史成分 → 不绑个股"})
            pd["current_windows"] = list(pd["current_windows"]) + [extra]
            new_pd = os.path.join(L.CURRENT, "pattern_discovery_v0_99.json")
            io.open(new_pd, "w", encoding="utf-8", newline="\n").write(
                json.dumps(pd, ensure_ascii=False, indent=1, sort_keys=True) + "\n")

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = L.main(["--write"])
            out = buf.getvalue()

            self.assertEqual(rc, 2, "冲突必须返回非零退出码，实际 %r\n%s" % (rc, out[-800:]))
            self.assertIn("未修改任何文件", out)
            self.assertIn("结算快照", out, "拒绝原因应指向结算快照冲突")
            for name, p in (("log", log_p), ("latest", out_p), ("CL", cl_p), ("CF", cf_p)):
                self.assertEqual(sha(p), before[name],
                                 "%s 在拒绝后仍被修改了（这就是 v0.52 要修的缺陷）" % name)
            # 新批次的形成快照**不得**被创建（旧顺序会留下它）
            self.assertFalse(os.path.exists(t.snap("CF-2026-10-23-02.json")),
                             "拒绝时不得创建新批次的形成快照")

            # ★★ 反证「场景非空」：把**两个**冲突的冻结目标（同日结算快照 + 同日 latest）挪开再跑 ——
            #    若这时确实新增了批次，就说明上一步的拒绝不是「本来无事可做」，而是真的被冲突挡住了。
            #    ★ 注意 latest 与结算快照是**两个独立**的冲突源（都按同一 market_as_of 拒绝）。
            os.rename(cl_p, cl_p + ".bak")
            os.rename(out_p, out_p + ".bak")
            buf3 = io.StringIO()
            with contextlib.redirect_stdout(buf3):
                rc3 = L.main(["--write"])
            self.assertEqual(rc3, 0, "移开两个冲突源后应成功：%s" % buf3.getvalue()[-800:])
            self.assertEqual(len(t.log()["batches"]), 2,
                             "该场景本应新增 1 个批次 —— 否则 T12 是空断言")
            self.assertTrue(os.path.exists(t.snap("CF-2026-10-23-02.json")),
                            "成功路径应当写出新批次的形成快照")
            self.assertNotEqual(sha(log_p), before["log"], "成功路径应当追加了形成日志")
            self.assertEqual(t.ledger()["summary"]["candidates"], 205,
                             "成功路径的账本应当包含新实例")


if __name__ == "__main__":
    unittest.main(verbosity=2)
