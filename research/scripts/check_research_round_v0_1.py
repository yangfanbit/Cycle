#!/usr/bin/env python3
"""check_research_round_v0_1.py —— 研究轮次产物的**只读**校验（v0.81）。

检查范围：形状 / 枚举 / 日期窗口 / 来源分级 / 与当前研究对象集合对账 /
阶段维持一致性 / 计数自洽 / PIT 锚点 / 板块映射状态 / 禁用措辞 / 占位符。
★ 不核实外部网页内容（那是离线研究轮次里的人工动作，本脚本不联网）。

用法：--check
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
ROUND = os.path.join(CURRENT, "research_round_2026-11-08_v0_1.json")
CC = os.path.join(CURRENT, "current_candidates.json")

VERDICTS = {
    "MAINTAINED_WITH_NEW_LEAD", "MAINTAINED_ADJACENT_EVIDENCE",
    "MAINTAINED_COVERAGE_GAP",
}
TIERS = {"T1_OFFICIAL_ORIGINAL", "T1_OFFICIAL_LIST_PAGE", "T3_MEDIA_TRANSCRIPT"}
BANNED = ("买入", "卖出", "目标价", "仓位", "胜率", "评分",
          "TODO", "TBD", "PLACEHOLDER", "待回填")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def check():
    errs = []
    if not os.path.exists(ROUND):
        print("FAIL 研究轮次产物不存在：%s" % ROUND)
        return 1
    d = load(ROUND)
    cc = load(CC)
    as_of = d.get("as_of")

    for k in ("artifact", "round_id", "as_of", "purpose", "scope",
              "sources", "theme_reviews", "new_watch_directions", "counts", "limits"):
        if not d.get(k):
            errs.append("缺必需字段 %s" % k)

    sc = d.get("scope") or {}
    if not (sc.get("from", "") <= sc.get("to", "") == as_of):
        errs.append("复查窗口与 as_of 不自洽（from <= to == as_of）")
    if sc.get("market_data_role") and "不参与阶段判定" not in sc["market_data_role"]:
        errs.append("未声明行情数据不参与阶段判定")

    # ① 来源：分级 / URL / 日期 / Tier 3 纪律
    for s in d.get("sources") or []:
        sid = s.get("source_id")
        if s.get("tier") not in TIERS:
            errs.append("非法来源分级：%s" % sid)
        if not str(s.get("url") or "").startswith(("http://", "https://")):
            errs.append("来源缺可核 URL：%s" % sid)
        if (s.get("date") or "") > (as_of or ""):
            errs.append("来源日期超过 as_of：%s" % sid)
        if not s.get("facts") or not s.get("not_claimed"):
            errs.append("来源缺 facts / not_claimed：%s" % sid)
        if s.get("tier") == "T3_MEDIA_TRANSCRIPT" and \
           "不单独承担结论" not in str(s.get("not_claimed")):
            errs.append("Tier 3 媒体转述必须声明不单独承担结论：%s" % sid)

    # ② 主题复查：覆盖 canonical 全部研究对象、阶段维持、PIT 锚点
    cc_ids = {c["candidate_id"] for c in cc.get("candidates") or []}
    cc_phase = {c["candidate_id"]: c.get("attention_state") for c in cc.get("candidates") or []}
    seen = set()
    verdict_counts = {}
    for r in d.get("theme_reviews") or []:
        cid = r.get("candidate_id")
        if cid in seen:
            errs.append("重复的 candidate_id：%s" % cid)
        seen.add(cid)
        if cid not in cc_ids:
            errs.append("复查对象不在 current_candidates：%s" % cid)
        if r.get("verdict") not in VERDICTS:
            errs.append("非法 verdict：%s / %s" % (cid, r.get("verdict")))
        verdict_counts[r.get("verdict")] = verdict_counts.get(r.get("verdict"), 0) + 1
        if r.get("declared_phase") != cc_phase.get(cid):
            errs.append("阶段漂移（本轮应维持）：%s" % cid)
        if not r.get("basis") or not r.get("next_research_question"):
            errs.append("复查缺 basis / 下一步问题：%s" % cid)
        n = r.get("new_evidence_count")
        if r.get("verdict") == "MAINTAINED_COVERAGE_GAP" and n != 0:
            errs.append("覆盖缺口却报新增证据：%s" % cid)
        if r.get("verdict") != "MAINTAINED_COVERAGE_GAP" and (not isinstance(n, int) or n < 1):
            errs.append("有新增证据的复查未计数：%s" % cid)
        a = r.get("market_anchor") or {}
        if a.get("as_of") != as_of or \
           a.get("basis") != "DECLARATION_DATE_AS_PIT_UPPER_BOUND":
            errs.append("PIT 锚点不等于声明日 / 口径被改：%s" % cid)
    if seen != cc_ids:
        errs.append("复查对象集合与 current_candidates 不一致：缺 %s"
                    % ", ".join(sorted(cc_ids - seen)))

    # ③ 新增观察方向：映射状态与板块一致、事件可核
    for w in d.get("new_watch_directions") or []:
        wid = w.get("direction_id")
        bs, st = w.get("board_series"), w.get("board_mapping_status")
        if st == "NOT_MAPPED" and bs:
            errs.append("声明未映射却给了板块序列：%s" % wid)
        if st == "EXACT_TITLE_KEYWORD_MATCH" and not bs:
            errs.append("声明精确匹配却缺板块序列：%s" % wid)
        if st == "NOT_MAPPED" and not w.get("board_mapping_reason"):
            errs.append("未映射必须写原因：%s" % wid)
        e = w.get("event") or {}
        if not str(e.get("url") or "").startswith(("http://", "https://")):
            errs.append("观察方向缺可核事件 URL：%s" % wid)
        if (e.get("date") or "") > (as_of or ""):
            errs.append("观察方向事件日期超过 as_of：%s" % wid)
        if not w.get("reason") or not w.get("caveat"):
            errs.append("观察方向缺理由 / 边界：%s" % wid)

    # ④ 计数自洽
    c = d.get("counts") or {}
    if c.get("sources") != len(d.get("sources") or []):
        errs.append("counts.sources 与列表不一致")
    if c.get("theme_reviews") != len(d.get("theme_reviews") or []):
        errs.append("counts.theme_reviews 与列表不一致")
    if c.get("new_watch_directions") != len(d.get("new_watch_directions") or []):
        errs.append("counts.new_watch_directions 与列表不一致")
    if c.get("verdicts") != verdict_counts:
        errs.append("counts.verdicts 与逐条 verdict 分组不一致")
    if c.get("tier3_media_only") != sum(1 for s in d.get("sources") or []
                                        if s.get("tier") == "T3_MEDIA_TRANSCRIPT"):
        errs.append("counts.tier3_media_only 与实际不一致")

    # ⑤ 引用产物存在
    for f in d.get("referenced_artifacts") or []:
        if not os.path.exists(os.path.join(CURRENT, f)):
            errs.append("引用的产物不存在：%s" % f)

    # ⑥ 禁用措辞 / 占位符 / 裸 Markdown 由前端 RichText 处理，这里只查禁词
    blob = json.dumps(d, ensure_ascii=False)
    for w in BANNED:
        if w in blob:
            errs.append("出现禁止措辞或占位符：%s" % w)

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    print("--check PASS · 范围：形状 / 分级 / 日期 / 主题覆盖 / 阶段维持 / PIT 锚点 /"
          " 计数 / 映射状态 / 禁用词（不联网核实外部网页）"
          " · 复查 %d 主题 · 新增观察方向 %d 条 · 来源 %d 条"
          % (len(d["theme_reviews"]), len(d["new_watch_directions"]), len(d["sources"])))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.parse_args()
    return check()


if __name__ == "__main__":
    sys.exit(main())
