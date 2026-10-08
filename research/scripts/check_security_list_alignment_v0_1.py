#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_security_list_alignment_v0_1.py —— 检验「代表标的清单」与「记录自己的依据」是否一致。

## 它回答什么

对每个 campaign：**记录里点名的标的**与**实际登记的标的**，哪一个能解释记录的 peak？

- `named`：从该 campaign 的 evidence 正文里抽取 6 位代码，**且该代码存在于 `securities` 表** ——
  避免把日期、金额、指数代码误当股票代码。
- `listed`：`campaign_securities` 里实际登记的标的。
- 对两侧分别算：**在 campaign 窗口内，原始价 `high` 的峰值日与记录 peak 相差 ≤7 日的个数**。

## 判定（封闭）

| 结论 | 含义 |
|---|---|
| `LISTED_EXPLAINS` | 已登记标的能解释（≥1 个同周） |
| **`NAMED_ONLY_EXPLAINS`** | ★ 只有**点名**的能解释，**已登记的不能** → 清单与依据不符 |
| `NEITHER_EXPLAINS` | 两者都不能 → 属参照物 / 日期问题（由确认器另行处理） |
| `NO_NAMED` | 记录里没有点名的已存在标的 |
| `NO_DATA` | 任一侧无行情数据 |

★ **只读**：本脚本不修改任何数据。发现属**研究侧 intake 复核事项**，不代为更正。

## 用法

    python research/scripts/check_security_list_alignment_v0_1.py
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
REFERENT = os.path.join(REP, "peak_referent_v0_2.json")
OUT = os.path.join(REP, "security_list_alignment_v0_1.json")
TOL = 7


def main():
    conn = db.connect()
    ref = json.load(io.open(REFERENT, encoding="utf-8"))

    # 全部「存在且为 6 位 A 股代码」的标的
    tick2sec, sec2tick = {}, {}
    for sid, tk in conn.execute("SELECT security_id, ticker FROM securities WHERE ticker IS NOT NULL"):
        t = (tk or "").strip()[:6]
        if re.fullmatch(r"\d{6}", t):
            tick2sec[t] = sid
            sec2tick[sid] = t
    # ★ 按**公司名**匹配：实测 evidence 常只写公司名不写代码
    #   （如「万辰集团股价…」「美的集团、格力电器、海尔智家」），只按代码抽会漏掉。
    name2sec = {}
    for sid, nm in conn.execute("SELECT security_id, name FROM securities WHERE name IS NOT NULL AND name <> ''"):
        nm = nm.strip()
        if len(nm) >= 2:
            name2sec[nm] = sid
            # 去掉末尾的 A/B 标记（如「万科A」→「万科」）作为别名，仍要求长度 ≥2
            if len(nm) >= 3 and nm[-1] in "AB":
                name2sec.setdefault(nm[:-1], sid)

    def raw_high_peak(sid, s, e):
        r = conn.execute(
            "SELECT trade_date, high FROM market_daily WHERE series_id=? AND price_type='raw' "
            "AND high IS NOT NULL AND trade_date BETWEEN ? AND ? ORDER BY trade_date", (sid, s, e)).fetchall()
        return max(r, key=lambda x: x[1]) if r else None

    rows = conn.execute("SELECT campaign_id, start_date, peak_date, end_date FROM campaigns ORDER BY campaign_id").fetchall()
    out, tally = {}, {}
    for cid, s, p, e in rows:
        listed = [x[0] for x in conn.execute("SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,))]
        texts = [d or "" for (d,) in conn.execute(
            """SELECT e.description FROM campaign_evidences ce
               JOIN evidences e ON e.evidence_id = ce.evidence_id WHERE ce.campaign_id=?""", (cid,))]
        blob = "\n".join(texts)
        mentioned = set()
        for t in set(re.findall(r"(?<!\d)(\d{6})(?!\d)", blob)):
            if t in tick2sec:
                mentioned.add(tick2sec[t])
        for nm, sid in name2sec.items():
            if nm in blob:
                mentioned.add(sid)
        named = sorted(mentioned - set(listed))

        rec = {"campaign_id": cid, "recorded_peak": p,
               "peak_referent": (ref["by_campaign"].get(cid) or {}).get("peak_referent"),
               "listed": listed, "named_not_listed": named}

        if not p:
            rec["verdict"] = "NO_PEAK"
            tally["NO_PEAK"] = tally.get("NO_PEAK", 0) + 1
            out[cid] = rec
            continue
        if not named:
            rec["verdict"] = "NO_NAMED"
            tally["NO_NAMED"] = tally.get("NO_NAMED", 0) + 1
            out[cid] = rec
            continue

        def hits(ids):
            got = []
            for sid in ids:
                x = raw_high_peak(sid, s, e or "2025-12-31")
                if not x:
                    continue
                dd = abs((date.fromisoformat(p) - date.fromisoformat(x[0])).days)
                if dd <= TOL:
                    got.append({"security_id": sid, "peak_date": x[0], "delta_days": dd})
            return got

        lh, nh = hits(listed), hits(named)
        rec["listed_hits"] = lh
        rec["named_hits"] = nh
        if lh:
            rec["verdict"] = "LISTED_EXPLAINS"
        elif nh:
            rec["verdict"] = "NAMED_ONLY_EXPLAINS"
        else:
            rec["verdict"] = "NEITHER_EXPLAINS"
        tally[rec["verdict"]] = tally.get(rec["verdict"], 0) + 1
        out[cid] = rec

    res = {
        "artifact": "security_list_alignment",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/check_security_list_alignment_v0_1.py",
        "source_referent": "research/research/reports/peak_referent_v0_2.json",
        "position": ("Research-only 只读检查 —— 比较「记录点名的标的」与「实际登记的标的」谁解释得了记录 peak。"
                     "**不修改任何数据**；发现属研究侧 intake 复核事项。"),
        "rules": {
            "tolerance_days": TOL,
            "named_extraction": ("从 evidence 正文两路抽取：① 6 位数字**且必须存在于 `securities` 表**"
                                 "（避免把日期 / 金额 / 指数代码误当股票代码）；"
                                 "② **公司名**匹配 `securities.name`（实测 evidence 常只写公司名不写代码）。"
                                 "两者并集再减去已登记的，得到「点名但未登记」。"),
            "price_basis": "原始价 high（盘中最高），与 evidence 表述一致",
            "verdicts": {
                "LISTED_EXPLAINS": "已登记标的能解释（≥1 个同周）",
                "NAMED_ONLY_EXPLAINS": "★ 只有点名的能解释，已登记的不能 → 清单与依据不符",
                "NEITHER_EXPLAINS": "两者都不能 → 属参照物 / 日期问题",
                "NO_NAMED": "记录里没有点名的已存在标的",
                "NO_PEAK": "记录未标注峰值",
            },
            "no_score": "本 artifact **不含** score / ranking / probability。",
        },
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    print("=== ★ NAMED_ONLY_EXPLAINS（清单与依据不符）===")
    for cid, r in sorted(out.items()):
        if r["verdict"] == "NAMED_ONLY_EXPLAINS":
            print("  %-30s peak=%s ref=%s" % (cid, r["recorded_peak"], r["peak_referent"]))
            print("        已登记 %s（无一同周）" % r["listed"])
            print("        ★点名  %s → %s" % (r["named_not_listed"], [(h["security_id"], h["peak_date"]) for h in r["named_hits"]]))
    print()
    print("=== ★★ 两侧都能解释，但**是不同标的**（需人工判断哪一侧才是代表标的）===")
    for cid, r in sorted(out.items()):
        if r["verdict"] == "LISTED_EXPLAINS" and r.get("named_hits"):
            print("  %-30s peak=%s" % (cid, r["recorded_peak"]))
            print("        已登记同周 %s" % [(h["security_id"], h["peak_date"], h["delta_days"]) for h in r["listed_hits"]])
            print("        ★点名同周 %s" % [(h["security_id"], h["peak_date"], h["delta_days"]) for h in r["named_hits"]])
            print("        点名但未登记 %s" % r["named_not_listed"])
    print()
    print("=== NEITHER_EXPLAINS（两者都不能，属参照物/日期问题）===")
    for cid, r in sorted(out.items()):
        if r["verdict"] == "NEITHER_EXPLAINS":
            print("  %-30s peak=%s ref=%s named=%s" % (cid, r["recorded_peak"], r["peak_referent"], r["named_not_listed"]))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
