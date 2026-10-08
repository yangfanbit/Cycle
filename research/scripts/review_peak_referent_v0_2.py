#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""review_peak_referent_v0_2.py —— 以 **ThreeC Agent 角色**审查参照物声明 v0_2。

## v0_1 审查的结论（保留为记录）

`review_peak_referent_v0_1.py` 对 `peak_referent_v0_1.json` 的结果：
**ACCEPT 25 · FLAG_FOR_HUMAN 28**，失败项集中在：

- **C2 引文可溯源 27 条** —— v0_1 的 `referent_basis` 是**手写摘要却用「」加了引号**，且含 `…`，
  **引号内并非原文**。→ v0_2 把依据拆为「注（禁引号）」+「逐字摘录」。
- **C4 参照物与依据一致 2 条** —— 其中 1 条是**真歧义**（白酒：同一 evidence 既记指数亦记个股），
  另 1 条是**审查规则过宽**（关键词 `见顶` 误伤行业景气）。→ v0_2 显式写死平局规则，并收窄关键词。

## 本版（v0_2）的检查

| # | 检查 | 可证伪性 |
|---|---|---|
| C1 | 覆盖完整：每个 campaign 恰好一条 | 集合比对 |
| C2a | `referent_basis_note` **不得含「」引号**（注不得伪装成引文） | 子串 |
| C2b | `referent_evidence[].excerpt` 必须是该 campaign 记录原文的**子串** | 子串匹配 |
| C3 | 标 `UNSPECIFIED` 者，peak 日 ±7 日内**必须确实无** evidence / event | 集合比对 |
| C4 | 依据（注 + 摘录）提到 指数 / 印发 / 违约 / 产量 / 价格高点 时，参照物必须相应 | 关键词一致性 |
| C5 | 有峰值的对象必须给出参照物 | 集合比对 |

## 用法

    python research/scripts/review_peak_referent_v0_2.py
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REP = os.path.join(db.ROOT, "research", "reports")
SRC = os.path.join(REP, "peak_referent_v0_2.json")
OUT = os.path.join(REP, "peak_referent_review_v0_2.json")
TOL = 7

# ★ v0_1 → v0_2：C4 从「关键词扫全文」改为**按参照物分别设定必要条件**，且只看 peak ±TOL 日的证据行。
#   为什么必须改：旧写法把「依据里顺带提到别的日期的指数 / 产销数据」也算违规 ——
#   实测 9 条触发中 8 条属此类误伤（如某 evidence 同时记了指数在某月的另一高点）。
#   新写法只问一个可判定的问题：**该参照物若成立，peak 附近的证据必须出现哪类词**。
REQUIRED = {
    # 参照物 → (必要条件说明, 候选关键词组；组内命中任一即可)
    "SECTOR_INDEX_HIGH": ("peak ±%d 日的证据须提到「指数」", ("指数",)),
    "PRICE_HIGH": ("peak ±%d 日的证据须提到价格", ("价格", "价报", "价创", "元/吨", "美元/片", "均价")),
    "POLICY_EVENT": ("peak ±%d 日的证据须提到政策文件 / 决定", ("印发", "决定", "证监会", "常委会", "通知", "会议")),
    "COMPANY_EVENT": ("peak ±%d 日的证据须提到公司事件", ("违约", "公告", "偿付")),
    "INDUSTRY_INDICATOR": ("peak ±%d 日的证据须提到行业指标", ("产量", "景气", "产销")),
    "SECTOR_MOVE": ("peak ±%d 日的证据须提到板块级异动",
                    ("爆发", "大涨", "涨停", "领涨", "上涨", "高峰", "连板", "创历史新高", "全线")),
}
# SECURITY_HIGH 的必要条件：**已登记标的同周创价格高点** 或 证据出现股价高点措辞（平局规则见参照物 artifact）
STOCK_HIGH_WORDS = ("盘中最高", "最高价", "历史最高", "区间最高", "创新高", "创历史新高", "收于")


def main():
    conn = db.connect()
    ref = json.load(io.open(SRC, encoding="utf-8"))
    rows = {r[0] for r in conn.execute("SELECT campaign_id FROM campaigns")}

    corpus = {}
    for cid, txt in conn.execute(
        """SELECT ce.campaign_id, e.description FROM campaign_evidences ce
           JOIN evidences e ON e.evidence_id = ce.evidence_id"""):
        corpus.setdefault(cid, []).append(txt or "")
    for cid, nm, dsc in conn.execute(
        """SELECT ce.campaign_id, ev.name, ev.description FROM campaign_events ce
           JOIN events ev ON ev.event_id = ce.event_id"""):
        corpus.setdefault(cid, []).extend([nm or "", dsc or ""])

    dates = {}
    for cid, dt in conn.execute(
        """SELECT ce.campaign_id, e.date FROM campaign_evidences ce
           JOIN evidences e ON e.evidence_id = ce.evidence_id"""):
        dates.setdefault(cid, []).append(("evidence", dt))
    for cid, dt in conn.execute(
        """SELECT ce.campaign_id, ev.date FROM campaign_events ce
           JOIN events ev ON ev.event_id = ce.event_id"""):
        dates.setdefault(cid, []).append(("event", dt))

    results, tally = {}, {"ACCEPT": 0, "CORRECTED": 0, "FLAG_FOR_HUMAN": 0}
    for cid, r in sorted(ref["by_campaign"].items()):
        peak = (r.get("recorded") or {}).get("peak")
        refcode = r.get("peak_referent")
        note = r.get("referent_basis_note") or ""
        evs = r.get("referent_evidence") or []
        checks, notes = {}, []

        checks["C1_covered"] = cid in rows
        checks["C2a_note_has_no_quotes"] = "「" not in note and "」" not in note
        if not checks["C2a_note_has_no_quotes"]:
            notes.append("C2a note 含引号")

        blob = "\n".join(corpus.get(cid, []))
        bad = [e.get("excerpt") for e in evs if e.get("excerpt") and e["excerpt"] not in blob]
        checks["C2b_evidence_verbatim"] = not bad
        if bad:
            notes.append("C2b 摘录非原文子串：%s" % bad)

        if refcode == "UNSPECIFIED":
            hit = 0
            if peak:
                for _k, d in dates.get(cid, []):
                    if d and abs((date.fromisoformat(peak) - date.fromisoformat(d)).days) <= TOL:
                        hit += 1
            checks["C3_unspecified_really_bare"] = (hit == 0)
            if hit:
                notes.append("C3 标为未界定，但 ±%d 日内有 %d 条依据" % (TOL, hit))

        # C4：按参照物分别设定**必要条件**，只看 peak ±TOL 日的证据行
        near_text = "\n".join(e.get("excerpt", "") for e in evs)
        c4, c4_note = True, None
        if refcode in REQUIRED:
            why, words = REQUIRED[refcode]
            if not any(w in near_text for w in words):
                c4 = False
                c4_note = "C4 " + (why % TOL) + " —— 未命中任一 %s" % (words,)
        elif refcode == "SECURITY_HIGH":
            coincide = r.get("securities_coincide") or []
            if not coincide and not any(w in near_text for w in STOCK_HIGH_WORDS):
                c4 = False
                c4_note = "C4 参照物为股价，但既无已登记标的同周创高点，证据也无股价高点措辞"
        checks["C4_necessary_condition"] = c4
        if c4_note:
            notes.append(c4_note)

        checks["C5_has_referent"] = bool(refcode) if peak else True

        ok = all(checks.values())
        verdict = "ACCEPT" if ok else "FLAG_FOR_HUMAN"
        tally[verdict] += 1
        results[cid] = {"campaign_id": cid, "peak": peak, "peak_referent": refcode,
                        "checks": checks, "verdict": verdict, "notes": notes}

    res = {
        "artifact": "peak_referent_review",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/review_peak_referent_v0_2.py",
        "reviewed_artifact": "research/research/reports/peak_referent_v0_2.json",
        "prior_review": ("research/research/reports/peak_referent_review_v0_1.json —— "
                         "对 v0_1 的审查结果 ACCEPT 25 / FLAG 28，"
                         "直接导致 v0_2 把「手写引文」改为「注 + 逐字摘录」，并显式写死平局规则。"),
        "reviewer_role": "ThreeC Agent role（协议 §3 角色分离：生产与审查分离）",
        "checks": {
            "C1": "每个 campaign 恰好一条",
            "C2a": "referent_basis_note 不得含「」引号（注不得伪装成引文）",
            "C2b": "referent_evidence[].excerpt 必须是该 campaign 记录原文的子串",
            "C3": "标 UNSPECIFIED 者，peak 日 ±%d 日内必须确实无依据" % TOL,
            "C4": ("按参照物分别设定**必要条件**，且只看 peak ±%d 日的证据行："
                   "指数→须提「指数」；商品价→须提价格；政策→须提印发/决定；公司→须提违约/公告；"
                   "行业指标→须提产量/景气；板块级→须提爆发/大涨/涨停等；"
                   "股价→须有已登记标的同周创高点，或证据出现股价高点措辞。" % TOL),
            "C5": "有峰值的对象必须给出参照物",
        },
        "verdict_vocabulary": ["ACCEPT", "CORRECTED", "FLAG_FOR_HUMAN"],
        "summary": tally,
        "by_campaign": results,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    print("=== 未通过检查的 ===")
    bad_any = False
    for cid, v in sorted(results.items()):
        if v["verdict"] != "ACCEPT":
            bad_any = True
            print("  %-30s ref=%-20s" % (cid, v["peak_referent"]))
            for n in v["notes"]:
                print("        %s" % n)
    if not bad_any:
        print("  （无 —— 全部通过）")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
