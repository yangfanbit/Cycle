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
    """★ v0.69：有到分钟的发布时间时，只在无歧义情形使用。

    ★★ v0.71 收紧：**三条门槛同时成立**才用精确时间 ——
    来源语义为 `PUBLICATION_TIME`、有到分钟时间、且 `published_date == event_date`。
    """

    @staticmethod
    def pub(t, d="2026-09-24"):
        return {"date": d, "time": t, "precision": "MINUTE"}

    def test_T2c_after_close_uses_event_day_close(self):
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("18:00"), "PUBLICATION_TIME")
        self.assertEqual(tb["rule"], "PUBLISHED_AFTER_CLOSE")
        self.assertEqual(tb["basis_day"], "2026-09-24")
        self.assertEqual(tb["observe_from"], "2026-09-28")
        self.assertEqual(tb["time_certainty"], "EXACT")

    def test_T2d_before_open_uses_prior_close(self):
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("08:30"), "PUBLICATION_TIME")
        self.assertEqual(tb["rule"], "PUBLISHED_BEFORE_OPEN")
        self.assertEqual(tb["basis_day"], "2026-09-23")
        self.assertEqual(tb["observe_from"], "2026-09-24")
        self.assertEqual(tb["time_certainty"], "EXACT")

    def test_T2e_intraday_falls_back_to_conservative(self):
        """盘中发布无法判断先后 → 退回保守规则（事件日涨跌不计入）。"""
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("11:00"), "PUBLICATION_TIME")
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))
        self.assertEqual(tb["time_certainty"], "CONSERVATIVE")


class TestDateMismatchGate(unittest.TestCase):
    """★★ v0.71 P0：`published_date != event_date` 时**禁止**用该元数据的时分判断盘前/盘后。

    实测 v0.5 有 58 条违反（NEA 51 / MIIT 7）：列表上网日 2025-12-18、文章成文 2025-06-22，
    却用成文日的 08:xx 判定「开盘前」→ 事件日的反应窗口被错位。
    """

    @staticmethod
    def pub(t, d):
        return {"date": d, "time": t, "precision": "MINUTE"}

    def test_T2f_mismatch_blocks_after_close(self):
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("18:00", "2026-09-10"), "PUBLICATION_TIME")
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"),
                        "日期不一致时不得用盘后规则")
        self.assertEqual(tb["precise_time_rejected"]["reason"], "DATE_MISMATCH")
        self.assertIn("2026-09-10", tb["precise_time_rejected"]["note"])

    def test_T2g_mismatch_blocks_before_open(self):
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("08:30", "2026-09-10"), "PUBLICATION_TIME")
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"),
                        "日期不一致时不得用盘前规则")
        self.assertEqual(tb["precise_time_rejected"]["reason"], "DATE_MISMATCH")

    def test_T2h_untrusted_semantics_blocks_precise_rules(self):
        """成文时间语义 + 同一天 + 精确时间 → 仍不能用盘前/盘后。"""
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("18:00", "2026-09-24"),
                             "DOCUMENT_CREATION_TIME")
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))
        self.assertEqual(tb["precise_time_rejected"]["reason"], "SEMANTICS_UNTRUSTED")
        # UNKNOWN 同样不可信
        tb2 = B.time_basis_of("2026-09-24", CAL, self.pub("08:30", "2026-09-24"), "UNKNOWN")
        self.assertEqual(tb2["precise_time_rejected"]["reason"], "SEMANTICS_UNTRUSTED")

    def test_T2i_no_precise_time_reports_reason(self):
        tb = B.time_basis_of("2026-09-24", CAL, {"date": "2026-09-24", "precision": "DATE"},
                             "PUBLICATION_TIME")
        self.assertEqual(tb["precise_time_rejected"]["reason"], "PRECISION_UNAVAILABLE")


class TestDateConflict(unittest.TestCase):
    """★★ v0.71：日期冲突必须分级，且冲突严重的档案**不得伪造精确反应时点**。"""

    def test_T2j_ordinary_difference_keeps_date_usable(self):
        c = B.date_conflict_of("2025-12-18", {"date": "2025-06-22"}, "DOCUMENT_CREATION_TIME")
        self.assertEqual(c["kind"], "PUBLISHED_DATE_DIFFERS")
        self.assertEqual(c["delta_days"], -179)
        # 普通差异仍可用保守规则（日期可信）
        tb = B.time_basis_of("2025-12-18", CAL, {"date": "2025-06-22"}, "DOCUMENT_CREATION_TIME", c)
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))
        self.assertEqual(tb["time_certainty"], "CONSERVATIVE")

    def test_T2k_archive_conflict_is_uncertain(self):
        c = B.date_conflict_of("2006-08-04", {"date": "2023-05-12"}, "DOCUMENT_CREATION_TIME")
        self.assertEqual(c["kind"], "ARCHIVE_METADATA_CONFLICT")
        tb = B.time_basis_of("2006-08-04", CAL, {"date": "2023-05-12"}, "DOCUMENT_CREATION_TIME", c)
        self.assertEqual(tb["rule"], "DATE_CONFLICT_UNCERTAIN")
        self.assertEqual(tb["time_certainty"], "UNCERTAIN")
        self.assertIn("不计算", tb["note"])

    def test_T2l_bulk_migration_value_is_flagged(self):
        """同一 published_date 被多条共享且差异超阈值 → 批量赋值（网站迁移）。

        ★ 只共享日期但差异不大（如同一天成文的多份答复函）**不算**迁移污染。
        """
        bulk = {"2023-05-12": 6}
        c = B.date_conflict_of("2006-08-04", {"date": "2023-05-12"}, "DOCUMENT_CREATION_TIME", bulk)
        self.assertEqual(c["kind"], "BULK_MIGRATION_ARTIFACT")
        self.assertEqual(c["shared_by"], 6)
        tb = B.time_basis_of("2006-08-04", CAL, {"date": "2023-05-12"}, "DOCUMENT_CREATION_TIME", c)
        self.assertEqual(tb["time_certainty"], "UNCERTAIN")
        # 反例：差异小于阈值时，共享日期只算普通不一致（不能判成迁移污染）
        c2 = B.date_conflict_of("2022-09-29", {"date": "2023-05-12"}, "DOCUMENT_CREATION_TIME", bulk)
        self.assertEqual(c2["kind"], "PUBLISHED_DATE_DIFFERS")
        self.assertEqual(c2["delta_days"], 225)

    def test_T2m_same_day_is_not_a_conflict(self):
        self.assertIsNone(B.date_conflict_of("2026-09-24", {"date": "2026-09-24"},
                                             "PUBLICATION_TIME"))
        self.assertIsNone(B.date_conflict_of("2026-09-24", None, "UNKNOWN"))


class TestTimeFieldSemantics(unittest.TestCase):
    """★★ v0.71：来源注册表必须**明确声明**时间字段语义（不得凭字段名推定）。"""

    def test_T2n_every_source_declares_semantics(self):
        allowed = {"PUBLICATION_TIME", "DOCUMENT_CREATION_TIME", "UNKNOWN"}
        for s in B.SOURCES:
            tf = s.get("time_field") or {}
            self.assertIn(tf.get("semantics"), allowed, "%s 未声明时间语义" % s["id"])
            self.assertTrue(tf.get("evidence"), "%s 的时间语义缺实测依据" % s["id"])

    def test_T2o_semantics_match_observed_consistency(self):
        """实证一致性：声明 PUBLICATION_TIME 的来源，其事件日期应与文章日期同源。"""
        pub_srcs = {s["id"] for s in B.SOURCES
                    if (s.get("time_field") or {}).get("semantics") == "PUBLICATION_TIME"}
        # NDRC / NHSA 实测 100% 一致；NEA / MIIT 实测存在不一致 → 必须标成文时间
        self.assertIn("NDRC_ZCFB_TZ", pub_srcs)
        self.assertIn("NHSA_NOTICE", pub_srcs)
        for sid in ("NEA_XNY", "MIIT_KJS"):
            self.assertNotIn(sid, pub_srcs, "%s 实测日期不一致，不得声明为公开时间" % sid)


class TestDocClass(unittest.TestCase):
    """★ v0.71 P1：低信号文档分类（默认视图据此隐藏，但不删除、不丢统计）。"""

    def test_T10a_admin_reply(self):
        for t in ("关于全国政协十四届四次会议第01463号（城乡建设类037号）提案答复的函",
                  "对十四届全国人大三次会议第8532号建议的答复",
                  "关于政协第十四届全国委员会第三次会议第02983号提案的答复摘要"):
            self.assertEqual(B.doc_class_of(t, B.doc_type_of(t)), "ADMIN_REPLY", t)

    def test_T10b_activity_is_low_signal_but_classified(self):
        self.assertEqual(B.doc_class_of("2026全球脑机接口×医保创新场景大赛决赛入围项目名单",
                                        "POLICY_INSTRUMENT"), "ACTIVITY_PROMO")

    def test_T10c_standard_procedure_and_data(self):
        self.assertEqual(B.doc_class_of("关于公开征求《重型汽车自动紧急制动系统技术要求及试验方法》"
                                        "强制性国家标准（报批稿）意见的公示", "POLICY_INSTRUMENT"),
                         "STANDARD_PROCEDURE")
        self.assertEqual(B.doc_class_of("2026年一季度光伏发电建设情况", "OTHER"), "INDUSTRY_DATA")

    def test_T10d_policy_action_not_filtered(self):
        t = "关于同意南方区域电力市场转入正式运行的复函(发改办体改〔2026〕715号)"
        self.assertEqual(B.doc_class_of(t, B.doc_type_of(t)), "POLICY_ACTION")
        # ★ 默认视图只隐藏 ADMIN_REPLY，政策行动绝不能被当成低信号
        self.assertNotIn("POLICY_ACTION", B.LOW_SIGNAL_DOC_CLASSES)
        self.assertNotIn("STANDARD_PROCEDURE", B.LOW_SIGNAL_DOC_CLASSES)

    def test_T10e_every_class_has_legend(self):
        self.assertEqual(set(B.DOC_CLASS_LEGEND),
                         {"ADMIN_REPLY", "ACTIVITY_PROMO", "STANDARD_PROCEDURE",
                          "INDUSTRY_DATA", "POLICY_ACTION", "OTHER"})
        for c in B.LOW_SIGNAL_DOC_CLASSES:
            self.assertIn(c, B.DOC_CLASS_LEGEND)


class TestRejectReasonExhaustive(unittest.TestCase):
    """★★ v0.72 P0：**保守时点必须穷尽解释**。

    v0.6 实测有 19 条（全部 NHSA）满足「有分钟级时间 + 可信语义 + 日期同天」，
    却退回保守规则且 `precise_time_rejected = null` —— 无法解释为什么不用精确时间。
    其中 15 条是**盘中**、4 条是**盘后但事件日非交易日**。
    """

    @staticmethod
    def pub(t, d="2026-09-24"):
        return {"date": d, "time": t, "precision": "MINUTE"}

    def test_T2p_intraday_has_reason_and_keeps_window(self):
        tb = B.time_basis_of("2026-09-24", CAL, self.pub("12:00"), "PUBLICATION_TIME")
        self.assertEqual(tb["precise_time_rejected"]["reason"], "INTRADAY_AMBIGUOUS")
        # ★ 口径不得因补原因而改变：仍是「当日收盘为基准、次一交易日起观察」
        self.assertEqual(tb["rule"], "DATE_ONLY_CONSERVATIVE_TRADING_DAY")
        self.assertEqual(tb["basis_day"], "2026-09-24")
        self.assertEqual(tb["observe_from"], "2026-09-28")
        self.assertEqual(tb["time_certainty"], "CONSERVATIVE")
        for t in ("09:30", "10:00", "11:59", "13:13", "14:59"):
            x = B.time_basis_of("2026-09-24", CAL, self.pub(t), "PUBLICATION_TIME")
            self.assertEqual(x["precise_time_rejected"]["reason"], "INTRADAY_AMBIGUOUS", t)

    def test_T2q_after_close_on_non_trading_day_has_reason(self):
        tb = B.time_basis_of("2026-09-26", CAL, self.pub("18:00", "2026-09-26"),
                             "PUBLICATION_TIME")   # 周六
        self.assertEqual(tb["precise_time_rejected"]["reason"], "EVENT_DATE_NON_TRADING")
        # ★ 口径不变：基准 = 事件前最近交易日收盘，起点 = 事件后首个交易日
        self.assertEqual(tb["rule"], "DATE_ONLY_CONSERVATIVE_NON_TRADING_DAY")
        self.assertEqual(tb["basis_day"], "2026-09-24")
        self.assertEqual(tb["observe_from"], "2026-09-28")

    def test_T2r_before_open_without_prior_day_has_reason(self):
        """盘前但日历里没有更早的交易日 → 取不到前一收盘（边界情形）。"""
        cal = ["2026-09-22", "2026-09-23"]
        tb = B.time_basis_of("2026-09-22", cal, self.pub("08:00", "2026-09-22"),
                             "PUBLICATION_TIME")
        self.assertEqual(tb["precise_time_rejected"]["reason"], "CALENDAR_EDGE")
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))

    def test_T2s_precise_rules_keep_no_reject(self):
        """真正用上精确规则时不应有拒绝原因（避免两套说法并存）。"""
        for t, rule in (("15:00", "PUBLISHED_AFTER_CLOSE"), ("08:00", "PUBLISHED_BEFORE_OPEN")):
            tb = B.time_basis_of("2026-09-24", CAL, self.pub(t), "PUBLICATION_TIME")
            self.assertEqual(tb["rule"], rule, t)
            self.assertIsNone(tb["precise_time_rejected"], t)

    def test_T2t_every_reject_reason_has_legend(self):
        """所有可能产生的拒绝原因都必须在图例里（否则用户看不懂）。"""
        self.assertEqual(set(B.REJECT_REASON_LEGEND),
                         {"SEMANTICS_UNTRUSTED", "DATE_MISMATCH", "PRECISION_UNAVAILABLE",
                          "INTRADAY_AMBIGUOUS", "EVENT_DATE_NON_TRADING", "CALENDAR_EDGE"})
        self.assertIn("reject_reason_legend", B.RULES)

    def test_T2u_conservative_with_precise_inputs_always_explained(self):
        """穷举：只要满足三条门槛而最终保守，就必须有原因（本轮 P0 的核心不变量）。"""
        cases = [("09:30", "2026-09-24"), ("12:00", "2026-09-24"), ("14:59", "2026-09-24"),
                 ("15:00", "2026-09-26"), ("18:00", "2026-09-26"), ("23:59", "2026-09-26")]
        for t, d in cases:
            tb = B.time_basis_of(d, CAL, self.pub(t, d), "PUBLICATION_TIME")
            if tb["rule"] not in ("PUBLISHED_AFTER_CLOSE", "PUBLISHED_BEFORE_OPEN"):
                self.assertTrue(tb["precise_time_rejected"],
                                "%s %s 退回保守却没有拒绝原因" % (d, t))
                self.assertIn(tb["precise_time_rejected"]["reason"], B.REJECT_REASON_LEGEND)


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


class TestThemeTags(unittest.TestCase):
    """★★ v0.70：具体主题由**实际命中关键词**映射，不得由共享代理序列反推。"""

    def test_T8a_tag_comes_from_keyword_not_series(self):
        links = [{"keyword": "医用耗材", "board_series": "BK881144",
                  "board_name": "医疗器械", "relation": "DIRECT"}]
        self.assertEqual(B.theme_tags_of(links), ["医用耗材分类与价格"])
        # 同一序列、不同关键词 → 必须给出不同主题（这正是 v0.69 的缺陷）
        other = [{"keyword": "脑机接口", "board_series": "BK881144",
                  "board_name": "医疗器械", "relation": "PROXY"}]
        self.assertEqual(B.theme_tags_of(other), ["脑机接口"])
        self.assertNotEqual(B.theme_tags_of(links), B.theme_tags_of(other))
        # 但两者的**上层方向**相同 —— 说明为什么不能只看方向
        self.assertEqual(B.directions_of(links), B.directions_of(other))

    def test_T8b_every_keyword_has_a_tag(self):
        kws = {k[0] for k in B.THEME_KEYWORDS}
        self.assertEqual(kws, set(B.THEME_TAG_BY_KEYWORD), "关键词与主题标签必须一一对应")

    def test_T8c_unknown_keyword_yields_no_tag(self):
        self.assertEqual(B.theme_tags_of([{"keyword": "不存在的词"}]), [])

    def test_T8d_tags_are_deduped_and_ordered(self):
        links = [{"keyword": "光伏"}, {"keyword": "光伏"}, {"keyword": "风电"}]
        self.assertEqual(B.theme_tags_of(links), ["光伏", "风电"])


class TestCoverageDerivation(unittest.TestCase):
    """★★ v0.70：覆盖说明必须由注册表 + 实际产物派生（旧实现是手写常量，加来源后过期）。"""

    def test_T9a_limits_reflect_registry(self):
        pubs = sorted({x["publisher"] for x in B.SOURCES})
        lim = B.coverage_limits([], [], [])
        self.assertIn(str(len(pubs)), lim[0])
        self.assertIn(str(len(B.SOURCES)), lim[0])
        for p in pubs:
            self.assertIn(p, lim[0])
        self.assertNotIn("单一发布机构", lim[0])

    def test_T9b_limits_state_unreachable_sources(self):
        all_txt = " ".join(B.coverage_limits([], [], []))
        self.assertIn("未接入", all_txt)
        self.assertIn("412", all_txt)

    def test_T9c_time_rules_describe_every_emitted_rule(self):
        """time_basis_of 可能返回的每条规则，都必须被 rules.time_rules 描述。"""
        emitted = {
            B.time_basis_of("2026-09-24", CAL)["rule"],                        # 交易日
            B.time_basis_of("2026-09-26", CAL)["rule"],                        # 非交易日
            B.time_basis_of("2026-09-24", CAL, {"time": "15:30", "precision": "MINUTE"})["rule"],
            B.time_basis_of("2026-09-24", CAL, {"time": "08:00", "precision": "MINUTE"})["rule"],
            B.time_basis_of("2026-09-24", CAL, {"time": "10:00", "precision": "MINUTE"})["rule"],
            B.time_basis_of("2026-09-24", [])["rule"],
        }
        for r in emitted:
            self.assertIn(r, B.TIME_RULES, "规则 %s 没有写进 rules.time_rules" % r)

    def test_T9d_intraday_falls_back_so_no_intraday_rule_exists(self):
        """盘中发布退回保守规则 → 不应存在「盘中」专用规则（否则说明判定逻辑被改坏）。"""
        tb = B.time_basis_of("2026-09-24", CAL, {"time": "10:00", "precision": "MINUTE"})
        self.assertTrue(tb["rule"].startswith("DATE_ONLY_CONSERVATIVE"))
        self.assertFalse(any("INTRADAY" in k for k in B.TIME_RULES))

    def test_T9e_status_and_nature_legends_do_not_overlap(self):
        self.assertFalse(set(B.STATUS_LEGEND) & set(B.NATURE_LEGEND),
                         "市场状态与事件性质是两套枚举，不得混用键名")
        self.assertEqual(set(B.NATURE_LEGEND),
                         {"ROUTINE_RECURRING", "NEW_CATALYST", "BACKGROUND", "UNCLASSIFIED"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
