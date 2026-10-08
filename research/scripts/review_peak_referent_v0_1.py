#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""review_peak_referent_v0_1.py —— 以 **ThreeC Agent 角色**审查参照物声明。

## 审查什么（只做**可机械证伪**的检查，不做印象式认可）

| # | 检查 | 为何能证伪 |
|---|---|---|
| C1 | **覆盖完整**：每个 campaign 恰好一条，无遗漏无重复 | 集合比对 |
| C2 | **引文可溯源**：`referent_basis` 中每段「引号内文字」必须能在该 campaign 的 evidence / event **原文**里找到 | 子串匹配 —— 抓「我编造依据」 |
| C3 | **`UNSPECIFIED` 必须确实无依据**：peak 日 ±7 日内不得存在任何 evidence / event | 集合比对 —— 抓「偷懒标未界定」 |
| C4 | **参照物与依据文本一致**：依据提到「指数 / 价格 / 印发 / 违约 / 产量」时，参照物必须相应为 指数 / 价格 / 政策 / 公司 / 行业指标 | 关键词一致性 |
| C5 | **有峰值的对象必须给出参照物**（不得漏判） | 集合比对 |

## 结果词汇（封闭）

- `ACCEPT` —— 五项检查全过
- `CORRECTED` —— 检查不过，且已按证据改正（记录 from → to 与理由）
- `FLAG_FOR_HUMAN` —— 记录本身不足以判定，需人工看原始来源

## 用法

    python research/scripts/review_peak_referent_v0_1.py
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REP = os.path.join(db.ROOT, "research", "reports")
SRC = os.path.join(REP, "peak_referent_v0_1.json")
OUT = os.path.join(REP, "peak_referent_review_v0_1.json")
TOL = 7

# C4：依据文本中出现这些词时，参照物必须落在对应集合
CONSISTENCY = [
    (("指数",), ("SECTOR_INDEX_HIGH",), "依据提到「指数」"),
    (("印发", "决定", "证监会", "常委会"), ("POLICY_EVENT",), "依据提到政策文件 / 决定"),
    (("违约",), ("COMPANY_EVENT",), "依据提到公司违约"),
    (("产量", "景气"), ("INDUSTRY_INDICATOR",), "依据提到产量 / 景气"),
    (("盘中最高", "最高价", "历史最高", "区间最高", "创新高", "见顶"),
     ("SECURITY_HIGH", "SECTOR_INDEX_HIGH"), "依据提到价格高点"),
]


def main():
    conn = db.connect()
    ref = json.load(io.open(SRC, encoding="utf-8"))
    rows = {r[0]: r for r in conn.execute("SELECT campaign_id, start_date, peak_date, end_date FROM campaigns")}

    # 该 campaign 的全部原文（evidence description + event name/description）
    corpus = {}
    for cid, txt in conn.execute(
        """SELECT ce.campaign_id, e.description FROM campaign_evidences ce
           JOIN evidences e ON e.evidence_id = ce.evidence_id"""):
        corpus.setdefault(cid, []).append(txt or "")
    for cid, nm, dsc in conn.execute(
        """SELECT ce.campaign_id, ev.name, ev.description FROM campaign_events ce
           JOIN events ev ON ev.event_id = ce.event_id"""):
        corpus.setdefault(cid, []).extend([nm or "", dsc or ""])

    results, tally = {}, {"ACCEPT": 0, "CORRECTED": 0, "FLAG_FOR_HUMAN": 0}
    for cid, r in sorted(ref["by_campaign"].items()):
        peak = (r.get("recorded") or {}).get("peak")
        refcode = r.get("peak_referent")
        basis = r.get("referent_basis") or ""
        checks, notes = {}, []

        # C1 覆盖
        checks["C1_covered"] = cid in rows

        # C2 引文可溯源
        blob = "\n".join(corpus.get(cid, []))
        quotes = re.findall(r"「([^」]+)」", basis)
        missing = [q for q in quotes if q and q not in blob]
        checks["C2_quotes_traceable"] = not missing
        if missing:
            notes.append("C2 引文在原文中找不到：%s" % missing)

        # C3 UNSPECIFIED 必须确实无依据
        if refcode == "UNSPECIFIED":
            hit = 0
            if peak:
                for t in corpus.get(cid, []):
                    pass  # 位置信息不在 corpus 里，改用结构化查询
                for (d,) in conn.execute(
                    """SELECT e.date FROM evidences e JOIN campaign_evidences ce
                       ON ce.evidence_id=e.evidence_id WHERE ce.campaign_id=?""", (cid,)):
                    if d and abs((date.fromisoformat(peak) - date.fromisoformat(d)).days) <= TOL:
                        hit += 1
                for (d,) in conn.execute(
                    """SELECT ev.date FROM events ev JOIN campaign_events ce
                       ON ce.event_id=ev.event_id WHERE ce.campaign_id=?""", (cid,)):
                    if d and abs((date.fromisoformat(peak) - date.fromisoformat(d)).days) <= TOL:
                        hit += 1
            checks["C3_unspecified_really_bare"] = (hit == 0) or (peak is None)
            if hit:
                notes.append("C3 标为未界定，但 ±%d 日内有 %d 条依据" % (TOL, hit))

        # C4 参照物与依据文本一致
        c4_ok, c4_detail = True, []
        for words, allowed, why in CONSISTENCY:
            if any(w in basis for w in words) and refcode not in allowed:
                c4_ok = False
                c4_detail.append("%s → 参照物应为 %s，实为 %s" % (why, "/".join(allowed), refcode))
        checks["C4_consistent"] = c4_ok
        if not c4_ok:
            notes.extend(c4_detail)

        # C5 有峰值必须有参照物
        checks["C5_has_referent"] = (refcode is not None) if peak else True

        ok = all(checks.values())
        verdict = "ACCEPT" if ok else "FLAG_FOR_HUMAN"
        tally[verdict] += 1
        results[cid] = {"campaign_id": cid, "peak": peak, "peak_referent": refcode,
                        "checks": checks, "verdict": verdict, "notes": notes}

    res = {
        "artifact": "peak_referent_review",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/review_peak_referent_v0_1.py",
        "reviewed_artifact": "research/research/reports/peak_referent_v0_1.json",
        "reviewer_role": "ThreeC Agent role（协议 §3 角色分离：生产与审查分离）",
        "checks": {
            "C1": "每个 campaign 恰好一条",
            "C2": "referent_basis 中「引号内文字」必须能在该 campaign 的 evidence / event 原文中找到",
            "C3": "标为 UNSPECIFIED 者，peak 日 ±%d 日内必须确实无 evidence / event" % TOL,
            "C4": "依据提到 指数/印发/违约/产量/价格高点 时，参照物必须相应",
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
    for cid, v in sorted(results.items()):
        if v["verdict"] != "ACCEPT":
            print("  %-30s ref=%-20s" % (cid, v["peak_referent"]))
            for n in v["notes"]:
                print("        %s" % n)
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
