#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_kline_confirmation_v0_2.py —— 「K 线证实状态」，**随参照物而变**。

## v0_1 → v0_2 的变化（这是本轮的核心）

v0_1 只有 4 个状态，把「记录峰值未被股价证实」一律标成 `UNCONFIRMED`。
但 2026-10-08 实测发现：**17 个未证实里 14 个在记录里有明确依据，且依据指向的不是股价**
（指数 / 商品价 / 行业价 / 政策事件 / 板块级异动）。

→ 那 14 个不是「未通过检验」，而是**用错了检验工具**。

v0_2 读 `peak_referent_v0_1.json`，按参照物决定检验是否适用：

| 参照物 | 未同周时的状态 | 含义 |
|---|---|---|
| `SECURITY_HIGH` | **`UNCONFIRMED`** | ★ **真问题** —— 参照物就是股价，股价却不支持 |
| `UNSPECIFIED` | **`UNCONFIRMED`** | ★ **真问题** —— 记录没说参照物，且股价不支持 |
| 其余（指数 / 商品价 / 政策 / 公司 / 板块 / 行业指标） | **`NOT_APPLICABLE`** | K 线**不是**合适的检验工具 |

## 五个状态（封闭集合）

- `CONFIRMED` —— 有**已登记标的**在同周（±7 日）创出价格高点（无论参照物是什么）
- `UNCONFIRMED` —— 未同周，**且参照物是股价或未界定** → 真问题
- `NOT_APPLICABLE` —— 未同周，但**参照物不是股价** → 口径不同，非问题
- `NO_PEAK_RECORDED` —— 记录未标注峰值（合法空状态）
- `NO_DATA` —— 无行情数据

## ★ 纪律

- **只读**；不改任何研究数据；**不含** score / ranking / probability。
- 依据（`evidence_anchors`）**只给原文摘录**，**不做归类** —— 归类已由 `peak_referent` 显式声明并标注 PROVISIONAL。

## 用法

    python research/scripts/build_kline_confirmation_v0_2.py
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
ALIGN = os.path.join(REP, "kline_alignment_v0_2.json")
REFERENT = os.path.join(REP, "peak_referent_v0_1.json")
OUT = os.path.join(REP, "kline_confirmation_v0_2.json")

TOL = 7
EXCERPT_MAX = 220
# 参照物属于这两类时，股价检验才是合适的工具
SECURITY_LIKE = ("SECURITY_HIGH", "UNSPECIFIED")


def clean_excerpt(text: str) -> str:
    """截去来源标注尾巴（首个 `［` 或 `｜PIT:` 之前为正文）。规则显式记录，不静默改写。"""
    t = (text or "").strip()
    for cut in ("［", "｜PIT:"):
        i = t.find(cut)
        if i > 0:
            t = t[:i]
    return t.strip()[:EXCERPT_MAX]


def main():
    conn = db.connect()
    al = json.load(io.open(ALIGN, encoding="utf-8"))
    rf = json.load(io.open(REFERENT, encoding="utf-8"))

    ev = {}
    for cid, dt, et, desc in conn.execute(
        """SELECT ce.campaign_id, e.date, e.evidence_type, e.description
           FROM campaign_evidences ce JOIN evidences e ON e.evidence_id = ce.evidence_id"""
    ):
        ev.setdefault(cid, []).append({"kind": "evidence", "date": dt, "type": et,
                                       "excerpt": clean_excerpt(desc),
                                       "source_field": "evidences.description"})
    for cid, dt, et, nm, desc in conn.execute(
        """SELECT ce.campaign_id, ev.date, ev.event_type, ev.name, ev.description
           FROM campaign_events ce JOIN events ev ON ev.event_id = ce.event_id"""
    ):
        text = nm if (nm or "").strip() else (desc or "")
        ev.setdefault(cid, []).append({"kind": "event", "date": dt, "type": et,
                                       "excerpt": clean_excerpt(text),
                                       "source_field": "events.name" if (nm or "").strip() else "events.description"})

    out = {}
    tally = {k: 0 for k in ("CONFIRMED", "UNCONFIRMED", "NOT_APPLICABLE", "NO_PEAK_RECORDED", "NO_DATA")}
    for cid, v in al["by_campaign"].items():
        rec = v.get("recorded", {})
        peak = rec.get("peak")
        r = rf["by_campaign"].get(cid, {})
        ref = r.get("peak_referent", "UNSPECIFIED")

        row = {
            "campaign_id": cid,
            "campaign_year": v.get("campaign_year"),
            "recorded": {"start": rec.get("start"), "peak": peak, "end": rec.get("end")},
            "peak_referent": ref,
            "peak_referent_label": r.get("peak_referent_label"),
            "referent_basis": r.get("referent_basis"),
            "referent_review_status": r.get("referent_review_status"),
            "coverage": {"securities": (v.get("coverage") or {}).get("securities"),
                         "with_data": (v.get("coverage") or {}).get("with_data")},
        }
        ok = [x for x in (v.get("per_security") or []) if x.get("status") == "OK"]

        if not ok:
            row["confirmation"] = "NO_DATA"
        elif not peak:
            row["confirmation"] = "NO_PEAK_RECORDED"
        else:
            best = min(ok, key=lambda x: abs((date.fromisoformat(peak) - date.fromisoformat(x["peak_date"])).days))
            delta = abs((date.fromisoformat(peak) - date.fromisoformat(best["peak_date"])).days)
            row["nearest"] = {"security_id": best["security_id"], "peak_date": best["peak_date"], "delta_days": delta}
            if delta <= TOL:
                row["confirmation"] = "CONFIRMED"
            elif ref in SECURITY_LIKE:
                row["confirmation"] = "UNCONFIRMED"
            else:
                row["confirmation"] = "NOT_APPLICABLE"
            # 未同周时附上记录里的原文依据（不改写、不归类）
            if row["confirmation"] != "CONFIRMED":
                anchors = []
                for a in ev.get(cid, []):
                    if not a["date"]:
                        continue
                    if abs((date.fromisoformat(peak) - date.fromisoformat(a["date"])).days) <= TOL:
                        anchors.append({"kind": a["kind"], "date": a["date"], "type": a["type"],
                                        "excerpt": a["excerpt"], "source_field": a["source_field"]})
                anchors.sort(key=lambda x: (x["date"], x["kind"]))
                row["evidence_anchors"] = anchors
        tally[row["confirmation"]] += 1
        out[cid] = row

    res = {
        "artifact": "kline_confirmation",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/build_kline_confirmation_v0_2.py",
        "source_alignment": "research/research/reports/kline_alignment_v0_2.json",
        "source_referent": "research/research/reports/peak_referent_v0_1.json",
        "position": ("Research-only 只读产物 —— 供产品与研究侧**看见**「记录峰值是否被 K 线证实」。"
                     "**不改动任何研究数据**；**不含** score / ranking / probability。"),
        "rules": {
            "price_basis": "原始价 high（盘中最高）—— 与 evidence 表述一致",
            "tolerance_days": TOL,
            "states": {
                "CONFIRMED": "有已登记标的在同周（±%d 日）创出价格高点" % TOL,
                "UNCONFIRMED": "未同周，**且参照物是股价或未界定** → 真问题",
                "NOT_APPLICABLE": "未同周，但**参照物不是股价** → K 线不是合适的检验工具",
                "NO_PEAK_RECORDED": "记录未标注峰值（合法空状态）",
                "NO_DATA": "无行情数据",
            },
            "referent_gate": "参照物 ∈ %s 时才把「未同周」判为 UNCONFIRMED" % (SECURITY_LIKE,),
            "excerpt_rule": ("evidence 取 `evidences.description`、event 取 `events.name`"
                             "（实测 R01 导入把来源指针写进了 events.description）；"
                             "均截去来源标注尾巴，上限 %d 字。规则显式记录。" % EXCERPT_MAX),
            "no_score": "只有证实状态与原文依据，无评分 / 排序 / 概率",
        },
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    print("=== 未证实 / 不适用 的清单 ===")
    for cid, r in sorted(out.items()):
        if r["confirmation"] in ("UNCONFIRMED", "NOT_APPLICABLE"):
            print("  %-30s %-15s ref=%-20s 最近差 %3d 日" % (
                cid, r["confirmation"], r["peak_referent"], (r.get("nearest") or {}).get("delta_days", -1)))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
