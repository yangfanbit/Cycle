#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_peak_referent_v0_2.py —— 为每个历史对象的 `peak_date` 声明**参照物**。

## v0_1 → v0_2 的唯一变化：**依据的形态**

v0_1 的 `referent_basis` 是**手写摘要，且用「」加了引号** —— 但摘要里带 `…` 省略号，
**引号内的文字并不是原文**。ThreeC Agent 审查的 C2（引文可溯源）把它抓了出来：
**27 条「引文」在记录原文中找不到。**

→ v0_2 把依据**拆成两件东西**：

| 字段 | 性质 | 可否证伪 |
|---|---|---|
| `referent_basis_note` | **注**（我的判断说明）—— **禁止使用「」**，不得伪装成引文 | 检查「不得含引号」 |
| `referent_evidence` | **逐字摘录**（机械取自记录的 evidence / event 原文） | 子串匹配，可机械证伪 |

## ★ 平局规则（v0_2 显式写死）

同一周内**既提到指数、又提到个股**时（实测 5 处：白酒 / 半导体本地化 / 有色 / 军工 / 减肥药）：

> **只要记录点名了「已登记标的」的股价高点 → 判 `SECURITY_HIGH`**；
> 仅当记录**只**提指数时，才判 `SECTOR_INDEX_HIGH`。

理由：`peak_referent` 的作用是**决定「股价检验是否适用」**。已登记标的被点名时，
股价检验就是适用的、有意义的 —— 此时把它归为「指数」会让本该暴露的问题被掩盖。

## 参照物封闭枚举

`SECURITY_HIGH` · `SECTOR_INDEX_HIGH` · `PRICE_HIGH` · `POLICY_EVENT` ·
`COMPANY_EVENT` · `SECTOR_MOVE` · `INDUSTRY_INDICATOR` · `UNSPECIFIED`

## 用法

    python research/scripts/build_peak_referent_v0_2.py
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
OUT = os.path.join(REP, "peak_referent_v0_2.json")
TOL = 7
EXCERPT_MAX = 220

REFERENTS = ("SECURITY_HIGH", "SECTOR_INDEX_HIGH", "PRICE_HIGH", "POLICY_EVENT",
             "COMPANY_EVENT", "SECTOR_MOVE", "INDUSTRY_INDICATOR", "UNSPECIFIED")
LABEL = {
    "SECURITY_HIGH": "代表标的股价高点",
    "SECTOR_INDEX_HIGH": "板块 / 行业指数高点",
    "PRICE_HIGH": "商品或行业产品价格高点",
    "POLICY_EVENT": "政策事件日",
    "COMPANY_EVENT": "公司事件日",
    "SECTOR_MOVE": "板块级异动日",
    "INDUSTRY_INDICATOR": "行业指标拐点",
    "UNSPECIFIED": "未界定",
}

# ---------------------------------------------------------------------------
# 逐条判定（Research Agent 角色 · 2026-10-08）
#   ★ `note` 是**判断说明**，不得使用「」引号 —— 引文一律由 `referent_evidence` 逐字提供。
# ---------------------------------------------------------------------------
R = {
    # ---- UNSPECIFIED ----
    "C-2016-CONS-BAIJIU-UPGRADE": ("UNSPECIFIED", "peak 日 ±7 日内无 evidence / event；最近标的差 15 日"),
    "C-2016-HIEQ-CONSTR": ("UNSPECIFIED", "peak 日 ±7 日内无 evidence / event；最近标的差 17 日"),
    "C-2019-AD": ("UNSPECIFIED", "peak 日 ±7 日内无 evidence / event；最近标的差 84 日"),
    "C-2019-MIL-GROUP-RESTRUCTURE": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2024-FIN-BANK-DIVIDEND": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2024-RES-GOLD-CB": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2025-FIN-INSURANCE": ("UNSPECIFIED", "记录未标注 peak"),

    # ---- SECURITY_HIGH ----
    "C-2016-PANEL-CYCLE": ("SECURITY_HIGH", "已登记标的 BOE 于同日创区间高点；记录内该日无 evidence"),
    "C-2018-CONS-HOG-AFRICAN": ("SECURITY_HIGH", "记录写明牧原股份当日盘中触及历史最高价（不复权）"),
    "C-2019-COMM-5G": ("SECURITY_HIGH", "记录为逐只标的的行情复核（前复权），逐只给出区间高点日"),
    "C-2019-CONS-AESTHETICS": ("SECURITY_HIGH", "记录写明三只个股的盘中最高价；★ 点名的标的未登记进本 campaign"),
    "C-2019-CONS-BAIJIU-CORE": ("SECURITY_HIGH", "★ 平局：同一 evidence 既记指数亦记个股，且点名的茅台/五粮液/泸州老窖均已登记 → 按平局规则判股价"),
    "C-2019-CONSUMER-TWS": ("SECURITY_HIGH", "记录写明立讯精密月内最高价"),
    "C-2019-PHARMA-INNOV": ("SECURITY_HIGH", "记录为逐只标的的行情复核，给出药明康德 / 泰格医药前复权区间最高"),
    "C-2020-CONS-BEAUTY-CN": ("SECURITY_HIGH", "记录写明珀莱雅盘中历史最高；★ 点名的标的未登记进本 campaign"),
    "C-2020-CONS-DUTYFREE": ("SECURITY_HIGH", "记录写明中国中免当日盘中最高为历史最高价"),
    "C-2020-CONS-WHITE-GOODS": ("SECURITY_HIGH", "记录写明美的/海尔/格力的区间盘中最高；★ 点名标的均未登记进本 campaign"),
    "C-2020-NEV": ("SECURITY_HIGH", "记录写明当日整车走强、个股涨停；已登记标的 JAC / XUSHENG 同周创区间高点"),
    "C-2020-POWER-NE": ("SECURITY_HIGH", "记录为逐只标的的行情复核（前复权），逐只给出区间高点日"),
    "C-2021-NEV": ("SECURITY_HIGH", "记录写明比亚迪创历史新高；CATL 于同周创区间高点"),
    "C-2022-CONS-SERVICE-REBOUND": ("SECURITY_HIGH", "记录写明中国中免月内最高价为该脉冲期间股价高点"),
    "C-2022-POLICY": ("SECURITY_HIGH", "记录写明比亚迪市值首破万亿及当日报价涨幅"),
    "C-2022-POWER-GRID": ("SECURITY_HIGH", "记录为逐只标的的行情复核（前复权），逐只给出区间高点日"),
    "C-2023-AD": ("SECURITY_HIGH", "记录写明德赛西威于 7/11 创该段最高价"),
    "C-2023-COMM-OPTICAL": ("SECURITY_HIGH", "记录为逐只标的的行情复核（前复权），给出中际旭创 / 新易盛高点"),
    "C-2023-CONS-VALUE-RETAIL": ("SECURITY_HIGH", "记录写明万辰集团当日收盘为该区间最高；★ 点名的标的未登记进本 campaign"),
    "C-2024-CONS-TRADE-IN": ("SECURITY_HIGH", "记录写明白电等标的当日同时出现区间最高价；ROBAM 已登记"),

    # ---- SECTOR_INDEX_HIGH ----
    "C-2019-SEMI-LOCALIZATION": ("SECTOR_INDEX_HIGH", "记录只提申万半导体板块指数的年内最高"),
    "C-2020-MIL-EQUIP-ORDER": ("SECTOR_INDEX_HIGH", "记录只提中证军工指数的该轮区间高点"),
    "C-2020-RES-LITHIUM": ("SECTOR_INDEX_HIGH", "记录给出能源金属指数的区间最高点"),
    "C-2020-RES-NONFERROUS": ("SECTOR_INDEX_HIGH", "记录给出中证有色金属指数的区间最高点"),
    "C-2020-SEMI-EQUIPMENT": ("SECTOR_INDEX_HIGH", "记录只提申万半导体板块指数月内最高"),
    "C-2022-SEMI-DOWNTURN": ("SECTOR_INDEX_HIGH", "记录只提申万半导体板块指数的年内反弹高点"),
    "C-2023-AI-COMPUTE-SEMI": ("SECTOR_INDEX_HIGH", "记录只提申万半导体板块指数的年内最高"),
    "C-2023-PHARMA-GLP1": ("SECTOR_INDEX_HIGH", "记录只提 Wind 减肥药指数的区间涨幅与顶点"),
    "C-2024-SEMI-MEMORY": ("SECTOR_INDEX_HIGH", "记录只提申万半导体板块指数月内最高"),

    # ---- PRICE_HIGH ----
    "C-2020-PANEL-CYCLE": ("PRICE_HIGH", "记录给的是 65 英寸 LCD 面板价格的高点与随后的下跌"),
    "C-2020-RES-RAREEARTH": ("PRICE_HIGH", "记录给的是氧化镨钕挂牌价的高点"),
    "C-2021-CONS-HOG-REVERSAL": ("PRICE_HIGH", "记录给的是生猪价格创年内新高"),
    "C-2021-RES-CHEM-DUALCTRL": ("PRICE_HIGH", "记录给的是能耗双控下多种化工原料价格飙升"),

    # ---- POLICY_EVENT ----
    "C-2019-RES-DYE-SHOCK": ("POLICY_EVENT", "记录为江苏盐城市委常委会决定关闭响水化工园区"),
    "C-2022-RE-POLICY-THREE": ("POLICY_EVENT", "记录为证监会宣布恢复涉房上市公司并购重组及配套融资，次日板块暴涨"),
    "C-2023-HIEQ-HUMANOID": ("POLICY_EVENT", "记录为工业和信息化部印发人形机器人创新发展指导意见"),

    # ---- COMPANY_EVENT ----
    "C-2020-RE-DEBT-RISK": ("COMPANY_EVENT", "记录为中国恒大未能偿付债券构成违约"),

    # ---- SECTOR_MOVE ----
    "C-2020-FIN-BANK-CREDIT": ("SECTOR_MOVE", "记录为 A 股银行股全线大涨、多只个股涨幅居前"),
    "C-2023-FIN-SOE-VALUATION": ("SECTOR_MOVE", "记录为券商中期策略描述保险领涨与中特估定价因素"),
    "C-2023-HIEQ-ROBOT-PLUS": ("SECTOR_MOVE", "记录为券商双周报给出机械设备与机器人子行业的区间涨幅与估值"),
    "C-2024-FIN-BROKER-POLICY": ("SECTOR_MOVE", "记录为复市当日大幅高开后回落、成交额创历史新高"),
    "C-2024-ROBOTAXI": ("SECTOR_MOVE", "记录为龙头梯队的连续涨幅与连板数，未归结到单一标的的高点"),
    "C-2024-V2X": ("SECTOR_MOVE", "记录为车路云概念全线爆发、多股涨停，源文记为行情高峰"),
    "C-2025-ROBOTAXI": ("SECTOR_MOVE", "记录为板块全线爆发的板块级启动"),

    # ---- INDUSTRY_INDICATOR ----
    "C-2018-HIEQ-ROBOT-DOWN": ("INDUSTRY_INDICATOR", "记录为工业机器人产量同比下滑，次月转正（下行段结束）"),
    "C-2020-HIEQ-AUTOMATION": ("INDUSTRY_INDICATOR", "记录为通用自动化行业景气见顶"),
}


def clean_excerpt(text: str) -> str:
    """截去来源标注尾巴（首个 `［` 或 `｜PIT:` 之前为正文）。规则显式记录。"""
    t = (text or "").strip()
    for cut in ("［", "｜PIT:"):
        i = t.find(cut)
        if i > 0:
            t = t[:i]
    return t.strip()[:EXCERPT_MAX]


def main():
    conn = db.connect()
    al = json.load(io.open(ALIGN, encoding="utf-8"))

    ev = {}
    for cid, dt, et, desc in conn.execute(
        """SELECT ce.campaign_id, e.date, e.evidence_type, e.description
           FROM campaign_evidences ce JOIN evidences e ON e.evidence_id = ce.evidence_id"""):
        ev.setdefault(cid, []).append({"kind": "evidence", "date": dt, "type": et,
                                       "excerpt": clean_excerpt(desc),
                                       "source_field": "evidences.description"})
    for cid, dt, et, nm, desc in conn.execute(
        """SELECT ce.campaign_id, ev.date, ev.event_type, ev.name, ev.description
           FROM campaign_events ce JOIN events ev ON ev.event_id = ce.event_id"""):
        text = nm if (nm or "").strip() else (desc or "")
        ev.setdefault(cid, []).append({"kind": "event", "date": dt, "type": et,
                                       "excerpt": clean_excerpt(text),
                                       "source_field": "events.name" if (nm or "").strip() else "events.description"})

    rows = conn.execute("SELECT campaign_id, start_date, peak_date, end_date FROM campaigns ORDER BY campaign_id").fetchall()
    out, tally = {}, {k: 0 for k in REFERENTS}
    for cid, s, p, e in rows:
        v = al["by_campaign"].get(cid, {})
        ok = [x for x in (v.get("per_security") or []) if x.get("status") == "OK"]
        coincide, nearest = [], None
        if p and ok:
            for x in ok:
                dd = abs((date.fromisoformat(p) - date.fromisoformat(x["peak_date"])).days)
                if dd <= TOL:
                    coincide.append({"security_id": x["security_id"], "peak_date": x["peak_date"], "delta_days": dd})
            best = min(ok, key=lambda x: abs((date.fromisoformat(p) - date.fromisoformat(x["peak_date"])).days))
            nearest = {"security_id": best["security_id"], "peak_date": best["peak_date"],
                       "delta_days": abs((date.fromisoformat(p) - date.fromisoformat(best["peak_date"])).days)}

        ref, note = R.get(cid, ("UNSPECIFIED", "未在本表中声明"))
        # ★ 逐字摘录：机械取自记录，与手写 note 分离
        evidence = []
        if p:
            for a in ev.get(cid, []):
                if a["date"] and abs((date.fromisoformat(p) - date.fromisoformat(a["date"])).days) <= TOL:
                    evidence.append(a)
            evidence.sort(key=lambda x: (x["date"], x["kind"]))
        tally[ref] += 1
        out[cid] = {
            "campaign_id": cid,
            "recorded": {"start": s, "peak": p, "end": e},
            "peak_referent": ref,
            "peak_referent_label": LABEL[ref],
            "referent_basis_note": note,
            "referent_evidence": evidence,
            "referent_assigned_by": "Research Agent role（AI 离线判定，2026-10-08）",
            "referent_review_status": "PROVISIONAL",
            "securities_coincide": coincide,
            "nearest_security": nearest,
            "coverage": {"securities": (v.get("coverage") or {}).get("securities"),
                         "with_data": (v.get("coverage") or {}).get("with_data")},
        }

    res = {
        "artifact": "peak_referent",
        "artifact_version": "0.2",
        "generated_by": "research/scripts/build_peak_referent_v0_2.py",
        "supersedes": "research/research/reports/peak_referent_v0_1.json",
        "source_alignment": "research/research/reports/kline_alignment_v0_2.json",
        "position": ("Research-only —— 为 `peak_date` 补上**参照物**声明。"
                     "**不改** `campaigns` 表、**不改** `schema.sql`、**不改**任何日期数值。"),
        "why": ("2026-10-08 实测：53 个历史对象的 `peak_date` 中，17 个未被股价证实，"
                "而其中 14 个在记录里有明确依据 —— 依据指向指数 / 商品价 / 行业价 / 政策事件 / 板块级异动。"
                "`peak_date` 一个字段承载了至少 6 种语义而记录未声明是哪一种。"),
        "v0_1_to_v0_2": ("★ ThreeC Agent 审查 C2（引文可溯源）发现：v0_1 的 `referent_basis` 是**手写摘要**，"
                         "却用「」加了引号，且含 `…` 省略号 —— **27 条「引文」并非原文**。"
                         "v0_2 据此把依据拆为 `referent_basis_note`（注，禁止使用引号）与 "
                         "`referent_evidence`（**逐字摘录**，可机械证伪）。参照物取值本身**未变**。"),
        "rules": {
            "tolerance_days": TOL,
            "assignment_rule": ("以记录在 peak 日 ±%d 日内**明确写了什么**为准，确定性判定，不依赖关键词猜测。" % TOL),
            "tie_break": ("同一周内**既提到指数、又提到个股**时：只要记录点名了**已登记标的**的股价高点 → "
                          "判 `SECURITY_HIGH`；仅当记录**只**提指数时才判 `SECTOR_INDEX_HIGH`。"
                          "理由：参照物的作用是决定「股价检验是否适用」，已登记标的被点名时该检验适用且有信息量。"
                          "实测受影响 1 处（白酒：同 evidence 既记中证白酒指数亦记茅台/五粮液/泸州老窖）。"),
            "excerpt_rule": "evidence 取 `evidences.description`、event 取 `events.name`；均截去来源标注尾巴，上限 %d 字。" % EXCERPT_MAX,
            "note_rule": "`referent_basis_note` 是判断说明，**不得使用「」引号** —— 引文一律由 `referent_evidence` 逐字提供。",
            "review": "参照物属研究判断，全部标 `PROVISIONAL`，待 ThreeC Agent 按协议 §3 审查。",
            "no_score": "本 artifact **不含** score / ranking / probability。",
        },
        "enum": {k: LABEL[k] for k in REFERENTS},
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    # 自检：note 不得含引号
    bad = [c for c, r in out.items() if "「" in (r["referent_basis_note"] or "")]
    print("自检 note 含引号的:", bad if bad else "（无 ✓）")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
