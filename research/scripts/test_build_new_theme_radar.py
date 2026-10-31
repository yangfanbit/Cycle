#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""test_build_new_theme_radar.py —— 新题材雷达的口径与增量合并回归（v0.67）。

只测**纯函数**（不联网、不读大库）：
  T1  保守时点：事件日为交易日 → 基准=当日、起点=次一交易日（事件日涨跌不计入反应）
  T2  保守时点：事件日非交易日 → 基准=事件前最近交易日、起点=事件后首个交易日
  T3  关联只在标题命中时建立；正文命中只进 rejected（不建关联）
  T4  状态机：无关联 / 行情不足 / 观察日不足 / 过窗口 / 超额非正 / 全部 DIRECT 为正
  T5  增量合并：上一版事件本次未再出现 → 保留为 HISTORICAL_ONLY，且 first_seen 不被刷新

运行：`python research/scripts/test_build_new_theme_radar.py`
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_new_theme_radar_v0_1 as B  # noqa: E402

CAL = ["2026-09-22", "2026-09-23", "2026-09-24", "2026-09-28", "2026-09-29", "2026-09-30"]


def mk_event(**kw):
    e = {"event_id": "EVT-T-1", "event_date": "2026-09-24", "title": "t",
         "doc_type": "POLICY_INSTRUMENT", "theme_links": [], "markets": [], "gaps": []}
    e.update(kw)
    return e


def mk_market(**kw):
    m = {"board_series": "BK881145", "board_name": "电力", "relation": "DIRECT",
         "status": "OBSERVED", "observation_trading_days": 3,
         "board_ret_pct": -1.0, "bench_ret_pct": -2.0, "excess_pp": 1.0,
         "window": ["2026-09-24", "2026-09-30"], "gaps": []}
    m.update(kw)
    return m


class TestTimeBasis(unittest.TestCase):
    def test_T1_trading_day_excludes_event_day_move(self):
        tb = B.time_basis_of("2026-09-24", CAL)
        self.assertEqual(tb["basis_day"], "2026-09-24")      # 以事件日收盘为基准
        self.assertEqual(tb["observe_from"], "2026-09-28")    # 从次一交易日起观察（09-25 非交易日）
        self.assertIn("不计入", tb["note"])
        self.assertTrue(tb["rule"].endswith("TRADING_DAY"))

    def test_T2_non_trading_day_uses_prior_close(self):
        tb = B.time_basis_of("2026-09-26", CAL)              # 周六
        self.assertEqual(tb["basis_day"], "2026-09-24")
        self.assertEqual(tb["observe_from"], "2026-09-28")
        self.assertTrue(tb["rule"].endswith("NON_TRADING_DAY"))

    def test_T2b_no_calendar(self):
        tb = B.time_basis_of("2026-09-24", [])
        self.assertEqual(tb["rule"], "NO_CALENDAR")
        self.assertIsNone(tb["basis_day"])


class TestPublishedTime(unittest.TestCase):
    """★ v0.69：有到分钟的发布时间时，只在无歧义情形使用。"""

    def test_T2c_after_close_uses_event_day_close(self):
        tb = B.time_basis_of("2026-09-24", CAL, {"time": "18:00", "precision": "MINUTE"})
        self.assertEqual(tb["rule"], "PUBLISHED_AFTER_CLOSE")
        self.assertEqual(tb["basis_day"], "2026-09-24")
        self.assertEqual(tb["observe_from"], "2026-09-28")

    def test_T2d_before_open_uses_prior_close(self):
        tb = B.time_basis_of("2026-09-24", CAL, {"time": "08:30", "precision": "MINUTE"})
        self.assertEqual(tb["rule"], "PUBLISHED_BEFORE_OPEN")
        self.assertEqual(tb["basis_day"], "2026-09-23")
        self.assertEqual(tb["observe_from"], "2026-09-24")

    def test_T2e_intraday_falls_back_to_conservative(self):
        """盘中发布无法判断先后 → 退回保守规则（事件日涨跌不计入）。"""
        tb = B.time_basis_of("2026-09-24", CAL, {"time": "11:00", "precision": "MINUTE"})
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))


class TestNature(unittest.TestCase):
    """★ v0.69：事件性质只在证据明确时分类。"""

    def test_T6a_routine_recurring(self):
        n = B.nature_of("2026年9月24日国家继续实施调控，成品油价格适当调整", "OTHER", [])
        self.assertEqual(n["kind"], "ROUTINE_RECURRING")
        self.assertIn("成品油价格", n["basis"])

    def test_T6b_policy_instrument_is_new_catalyst(self):
        n = B.nature_of("关于印发《新型电力系统建设规划》的通知", "POLICY_INSTRUMENT", [])
        self.assertEqual(n["kind"], "NEW_CATALYST")

    def test_T6c_activity_words_override_to_background(self):
        """「大赛名单」文档类型像政策工具，但本质是活动 → 只算背景。"""
        n = B.nature_of("2026全球脑机接口×医保创新场景大赛决赛入围项目名单", "POLICY_INSTRUMENT", [])
        self.assertEqual(n["kind"], "BACKGROUND")
        self.assertIn("大赛", n["basis"])

    def test_T6d_meeting_is_background(self):
        self.assertEqual(B.nature_of("国家发展改革委举行10月份新闻发布会", "PRESS", [])["kind"],
                         "BACKGROUND")


class TestDirections(unittest.TestCase):
    """★ v0.69：研究方向只能由**已映射的序列**推出。"""

    def test_T7a_maps_known_series(self):
        links = [{"board_series": "BK881144"}]
        self.assertEqual(B.directions_of(links), ["医疗器械与脑机接口"])

    def test_T7b_unknown_series_yields_nothing(self):
        self.assertEqual(B.directions_of([{"board_series": "BK999999"}]), [])

    def test_T7c_dedupes(self):
        links = [{"board_series": "BK881280"}, {"board_series": "CPT_fd"}]
        self.assertEqual(B.directions_of(links), ["海上风电与风电设备"])

    def test_T7d_all_mapped_series_exist_in_direction_table(self):
        for d in B.RESEARCH_DIRECTIONS:
            self.assertTrue(d["series"], d["direction"])


class TestLinks(unittest.TestCase):
    def test_T3_title_hit_creates_link(self):
        links, rejected = B.theme_links("关于印发《新型电力系统建设规划》的通知", {})
        self.assertTrue(links)
        self.assertEqual(links[0]["matched_in"], "TITLE")
        self.assertEqual(links[0]["board_series"], "BK881145")
        self.assertEqual(rejected, [])

    def test_T3b_quote_only_does_not_create_link(self):
        """★★ 正文提及不建关联（实测「综合改革试点」正文提到人工智能会被误关联）。"""
        ev = {"quote": "本通知涉及人工智能与集成电路等领域的经验推广。"}
        links, rejected = B.theme_links("关于总结推广综合改革试点创新举措的通知", ev)
        self.assertEqual(links, [])
        self.assertTrue(rejected)
        self.assertTrue(all(r["reason"] for r in rejected))


class TestClassify(unittest.TestCase):
    def test_T4_no_link(self):
        st, gaps = B.classify(mk_event(), "2026-10-30")
        self.assertEqual(st, "NO_THEME_LINK")
        self.assertTrue(gaps)

    def test_T4b_insufficient(self):
        e = mk_event(theme_links=[{"board_series": "BK881145"}],
                     markets=[mk_market(status="INSUFFICIENT", gaps=["缺收盘价"])])
        self.assertEqual(B.classify(e, "2026-10-30")[0], "INSUFFICIENT")

    def test_T4c_pending_market(self):
        e = mk_event(theme_links=[{"board_series": "BK881145"}],
                     markets=[mk_market(observation_trading_days=2)])
        st, gaps = B.classify(e, "2026-10-30")
        self.assertEqual(st, "PENDING_MARKET")
        self.assertIn("< 3", gaps[0])

    def test_T4d_old_event_only_kept(self):
        e = mk_event(event_date="2026-08-01", theme_links=[{"board_series": "BK881145"}],
                     markets=[mk_market()])
        self.assertEqual(B.classify(e, "2026-10-30")[0], "WATCH")

    def test_T4e_negative_excess_not_candidate(self):
        e = mk_event(theme_links=[{"board_series": "BK881145"}],
                     markets=[mk_market(excess_pp=-0.35)])
        self.assertEqual(B.classify(e, "2026-10-30")[0], "WATCH")

    def test_T4f_all_direct_positive_is_candidate(self):
        e = mk_event(theme_links=[{"board_series": "BK881145"}],
                     markets=[mk_market(excess_pp=0.57)])
        self.assertEqual(B.classify(e, "2026-10-30")[0], "CANDIDATE")

    def test_T4g_multi_board_requires_all_direct_positive(self):
        """★ 多板块事件不得挑表现好的板块：任一 DIRECT 板块非正 → 不升级。"""
        e = mk_event(theme_links=[{"board_series": "BK881145"}, {"board_series": "BK881279"}],
                     markets=[mk_market(excess_pp=1.0),
                              mk_market(board_series="BK881279", board_name="光伏设备", excess_pp=-0.5)])
        self.assertEqual(B.classify(e, "2026-10-30")[0], "WATCH")

    def test_T4h_assessment_separates_absolute_and_relative(self):
        """★★ 绝对为负、相对为正时必须显式写出「不证明因果」（逐板块）。"""
        a = B.assessment_of_market(mk_market(board_ret_pct=-1.27, excess_pp=0.57))
        self.assertTrue(a["relative_positive"])
        self.assertFalse(a["absolute_positive"])
        self.assertIn("绝对收益为负", a["note"])
        self.assertIn("不证明", a["note"])

    # ── v0.68：必要 DIRECT 板块的边界（缺行情 / 观察期不足 / 非正超额 都不得升级）──
    def test_T4i_missing_market_for_a_direct_board_blocks_candidate(self):
        """一个 DIRECT 正超额、另一个必要 DIRECT 板块**缺行情记录** → 不得 CANDIDATE。"""
        e = mk_event(
            theme_links=[{"board_series": "BK881145", "relation": "DIRECT"},
                         {"board_series": "BK881279", "relation": "DIRECT"}],
            markets=[mk_market(board_series="BK881145", excess_pp=1.0)],   # 缺 BK881279
        )
        st, gaps = B.classify(e, "2026-10-30")
        self.assertEqual(st, "INSUFFICIENT")
        self.assertIn("缺少独立行情记录", gaps[0])

    def test_T4j_one_direct_board_insufficient_blocks_candidate(self):
        """一个已观察、另一个必要 DIRECT 板块行情不可核验 → INSUFFICIENT。"""
        e = mk_event(
            theme_links=[{"board_series": "BK881145", "relation": "DIRECT"},
                         {"board_series": "BK881279", "relation": "DIRECT"}],
            markets=[mk_market(board_series="BK881145", excess_pp=1.0),
                     mk_market(board_series="BK881279", board_name="光伏设备",
                               status="INSUFFICIENT", gaps=["缺收盘价"])],
        )
        st, gaps = B.classify(e, "2026-10-30")
        self.assertEqual(st, "INSUFFICIENT")
        self.assertIn("不可核验", gaps[0])

    def test_T4k_one_direct_board_pending_blocks_candidate(self):
        """一个已观察、另一个必要 DIRECT 板块观察日不足 → PENDING_MARKET（不升级）。"""
        e = mk_event(
            theme_links=[{"board_series": "BK881145", "relation": "DIRECT"},
                         {"board_series": "BK881279", "relation": "DIRECT"}],
            markets=[mk_market(board_series="BK881145", excess_pp=1.0, observation_trading_days=5),
                     mk_market(board_series="BK881279", board_name="光伏设备",
                               excess_pp=2.0, observation_trading_days=1)],
        )
        st, gaps = B.classify(e, "2026-10-30")
        self.assertEqual(st, "PENDING_MARKET")
        self.assertIn("< 3", gaps[0])

    def test_T4l_all_direct_boards_positive_is_candidate(self):
        e = mk_event(
            theme_links=[{"board_series": "BK881145", "relation": "DIRECT"},
                         {"board_series": "BK881279", "relation": "DIRECT"}],
            markets=[mk_market(board_series="BK881145", excess_pp=1.0),
                     mk_market(board_series="BK881279", board_name="光伏设备", excess_pp=0.4)],
        )
        self.assertEqual(B.classify(e, "2026-10-30")[0], "CANDIDATE")

    def test_T4m_proxy_board_does_not_gate_but_is_reported(self):
        """PROXY 不参与必要条件；但只有 PROXY 时退化为「全部关联板块」。"""
        e = mk_event(
            theme_links=[{"board_series": "BK881145", "relation": "DIRECT"},
                         {"board_series": "BK881162", "relation": "PROXY"}],
            markets=[mk_market(board_series="BK881145", excess_pp=1.0),
                     mk_market(board_series="BK881162", board_name="通信服务",
                               status="INSUFFICIENT", gaps=["缺收盘价"])],
        )
        self.assertEqual(B.classify(e, "2026-10-30")[0], "CANDIDATE")

    def test_T4n_single_direct_link_unchanged(self):
        """单一 DIRECT 关联的既有行为不得被改变。"""
        ok = mk_event(theme_links=[{"board_series": "BK881145", "relation": "DIRECT"}],
                      markets=[mk_market(excess_pp=0.57)])
        self.assertEqual(B.classify(ok, "2026-10-30")[0], "CANDIDATE")
        bad = mk_event(theme_links=[{"board_series": "BK881145", "relation": "DIRECT"}],
                       markets=[mk_market(excess_pp=-0.35)])
        self.assertEqual(B.classify(bad, "2026-10-30")[0], "WATCH")


class TestIncremental(unittest.TestCase):
    def test_T5_unseen_events_are_retained_with_first_seen(self):
        prev = {"artifact_version": "0.1", "events": [
            {"event_id": "EVT-OLD-1", "title": "旧事件", "event_date": "2026-01-05",
             "first_seen": "2026-02-01T00:00:00", "last_seen": "2026-02-01T00:00:00",
             "presence": "IN_LATEST_LIST", "source": {"url": "https://x/1.html"},
             "theme_links": [], "markets": [], "status": "NO_THEME_LINK", "gaps": []},
        ]}
        doc = B.build(fetch=False, prev=prev)
        kept = [e for e in doc["events"] if e["event_id"] == "EVT-OLD-1"]
        self.assertEqual(len(kept), 1, "本次未出现的历史事件必须保留")
        self.assertEqual(kept[0]["presence"], "HISTORICAL_ONLY")
        self.assertEqual(kept[0]["first_seen"], "2026-02-01T00:00:00", "first_seen 不得被刷新")
        self.assertTrue(any("历史记录保留" in g for g in kept[0]["gaps"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
