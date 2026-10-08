#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_kline_confirmation_v0_1.py —— 每个 campaign 的「K 线证实状态」（**只读产物**）。

## 它做什么

读 `kline_alignment_v0_2.json`（测量）+ DB 里的 evidence / event（依据），
为每个 campaign 产出一条**可展示**的证实记录：

- `confirmation`：`CONFIRMED` / `UNCONFIRMED` / `NO_PEAK_RECORDED` / `NO_DATA`
- `nearest`：最接近记录 peak 的**已登记标的**峰（含差几日）
- `evidence_anchors`：**±7 日内**的 evidence / event 行 —— **原文摘录，不做归类**

## ★ 纪律

- **只读**：不改任何 campaign / evidence / 记录口径；本脚本不写 DB。
- **不给 score / probability**：只有「证实 / 未证实」与**原文依据**。
- **不替研究侧下结论**：`UNCONFIRMED` 只表示「**未被已登记标的的价格高点证实**」，
  **不等于**「日期错误」—— 峰值可能锚定在指数、商品价、行业价或政策事件上，
  这些依据由 `evidence_anchors` **原文呈现**，判断留给读者。
- **不做启发式归类**：不给 evidence 打「这是猪价 / 这是政策」的标签 —— 只给原文。
  （归类若需要，应由研究侧正式定义口径，而不是由脚本猜。）

## 用法

    python research/scripts/build_kline_confirmation_v0_1.py
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
IN = os.path.join(REP, "kline_alignment_v0_2.json")
OUT = os.path.join(REP, "kline_confirmation_v0_1.json")

ANCHOR_DAYS = 7      # ★ 用户 2026-10-08：历史日期按**周**粒度即可
EXCERPT_MAX = 220


def clean_excerpt(text: str) -> str:
    """截去**来源标注尾巴**，只留正文。

    ★ 实测：`evidences.description` 普遍以 `［intake R01-…｜role=…｜independence=…］｜PIT: …`
      结尾 —— 那是**来源指针**，不是研究内容。展示时截去可读性更好，
      但**规则必须显式记录**（见 artifact 的 `excerpt_rule`），不得静默改写。
    """
    t = (text or '').strip()
    for cut in ('［', '｜PIT:'):
        i = t.find(cut)
        if i > 0:
            t = t[:i]
    return t.strip()[:EXCERPT_MAX]


def main():
    conn = db.connect()
    al = json.load(io.open(IN, encoding="utf-8"))

    # evidence / event 索引（按 campaign）
    # ★ event 用 `name`（人类可读标题）—— 实测 R01 导入把**来源指针**写进了 `description`，
    #   4 个不同事件共用同一串 provenance，直接用 description 会得到无意义文本。
    ev = {}
    for cid, dt, et, desc in conn.execute(
        """SELECT ce.campaign_id, e.date, e.evidence_type, e.description
           FROM campaign_evidences ce JOIN evidences e ON e.evidence_id = ce.evidence_id"""
    ):
        ev.setdefault(cid, []).append(
            {"kind": "evidence", "date": dt, "type": et,
             "excerpt": clean_excerpt(desc), "source_field": "evidences.description"})
    for cid, dt, et, nm, desc in conn.execute(
        """SELECT ce.campaign_id, ev.date, ev.event_type, ev.name, ev.description
           FROM campaign_events ce JOIN events ev ON ev.event_id = ce.event_id"""
    ):
        text = nm if (nm or "").strip() else (desc or "")
        ev.setdefault(cid, []).append(
            {"kind": "event", "date": dt, "type": et,
             "excerpt": clean_excerpt(text),
             "source_field": "events.name" if (nm or "").strip() else "events.description"})

    out = {}
    tally = {"CONFIRMED": 0, "UNCONFIRMED": 0, "NO_PEAK_RECORDED": 0, "NO_DATA": 0}
    for cid, v in al["by_campaign"].items():
        rec = v.get("recorded", {})
        peak = rec.get("peak")
        row = {"campaign_id": cid, "campaign_year": v.get("campaign_year"),
               "recorded": {"start": rec.get("start"), "peak": peak, "end": rec.get("end")}}

        ok = [x for x in (v.get("per_security") or []) if x.get("status") == "OK"]
        row["coverage"] = {"securities": (v.get("coverage") or {}).get("securities"),
                           "with_data": (v.get("coverage") or {}).get("with_data")}

        if not ok:
            row["confirmation"] = "NO_DATA"
        elif not peak:
            row["confirmation"] = "NO_PEAK_RECORDED"
        else:
            best = min(ok, key=lambda x: abs((date.fromisoformat(peak) - date.fromisoformat(x["peak_date"])).days))
            delta = abs((date.fromisoformat(peak) - date.fromisoformat(best["peak_date"])).days)
            row["nearest"] = {"security_id": best["security_id"], "peak_date": best["peak_date"], "delta_days": delta}
            row["confirmation"] = "CONFIRMED" if delta <= ANCHOR_DAYS else "UNCONFIRMED"
            # 若未证实，附上记录里 ±7 日的依据原文（不改写、不归类）
            if row["confirmation"] == "UNCONFIRMED":
                anchors = []
                for a in ev.get(cid, []):
                    if not a["date"]:
                        continue
                    if abs((date.fromisoformat(peak) - date.fromisoformat(a["date"])).days) <= ANCHOR_DAYS:
                        anchors.append({"kind": a["kind"], "date": a["date"], "type": a["type"],
                                        "excerpt": a["excerpt"], "source_field": a["source_field"]})
                anchors.sort(key=lambda x: (x["date"], x["kind"]))
                row["evidence_anchors"] = anchors
                row["anchor_note"] = ("记录峰值在 ±%d 日内**有记录依据**（原文见 evidence_anchors）；"
                                      "但**没有任何已登记标的**在该周创出价格高点。"
                                      "两者可以同时成立 —— 依据可能锚定在指数 / 商品价 / 行业价 / 政策事件上。"
                                      "★ 本字段不做归类，判断留给读者。" % ANCHOR_DAYS)
        tally[row["confirmation"]] = tally.get(row["confirmation"], 0) + 1
        out[cid] = row

    res = {
        "artifact": "kline_confirmation",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_kline_confirmation_v0_1.py",
        "source_alignment": "research/research/reports/kline_alignment_v0_2.json",
        "position": ("Research-only 只读产物 —— 供产品与研究侧**看见**「记录峰值是否被 K 线证实」。"
                     "**不改动任何研究数据**；**不含** score / ranking / probability。"),
        "rules": {
            "price_basis": "原始价 high（盘中最高）—— 与 evidence 表述一致",
            "tolerance_days": ANCHOR_DAYS,
            "meaning": ("CONFIRMED = 某个**已登记标的**的价格高点落在记录 peak 的 ±%d 日内；"
                        "UNCONFIRMED = 没有；**不等于**日期错误。" % ANCHOR_DAYS),
            "excerpt_rule": ("evidence 取 `evidences.description`、event 取 `events.name`（实测 R01 导入把**来源指针**"
                             "写进了 events.description，4 个不同事件共用同一串 provenance，故不用它）；"
                             "两者均**截去来源标注尾巴**（首个 `［` 或 `｜PIT:` 之前为正文），上限 %d 字。"
                             "规则显式记录，不静默改写。" % EXCERPT_MAX),
            "no_score": "只有证实状态与原文依据，无评分 / 排序 / 概率",
        },
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
