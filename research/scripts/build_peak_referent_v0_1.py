#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_peak_referent_v0_1.py —— 为每个历史对象的 `peak_date` 声明**参照物**。

## 它解决什么问题

2026-10-08 用真实 K 线对照 53 个历史对象的 `peak_date` 后发现：
**17 个「未被股价证实」的对象里，14 个在记录里明确有依据** —— 读原文才知道它指的是什么峰值：

- 「65 英寸 LCD **面板价格**…最高涨至 2021-07」
- 「**氧化镨钕价格**飙升至 76.26 万元/吨」
- 「**猪价**创年内新高」
- 「**申万半导体板块指数** 2025-10 月内最高」
- 「工信部**印发**《人形机器人创新发展指导意见》」
- 「A股无人驾驶**板块全线爆发**」

> **`peak_date` 一个字段承载了至少 6 种语义，而记录里没有一处说清是哪种。**
> 任何「用股价验证 peak」的自动检查，都会把其中 5 种误判为「未证实」。

**本 artifact 就是把那个缺失的声明补上**，并逐条附上**原文依据**以便复核。

## ★ 纪律

- **只读** DB，**不改** `campaigns` 表、**不改** `schema.sql`、**不改**任何日期数值。
- 参照物是**研究判断**，故逐条标注 `assigned_by` 与 `review_status`（**PROVISIONAL**，待 ThreeC Agent 审查）。
- 判定规则**确定性**（见 `rules.assignment_rule`），不依赖关键词猜测：
  以「记录在 peak 日 ±7 日内**明确写了什么**」为准。
- **无依据即 `UNSPECIFIED`** —— 不猜。

## 参照物封闭枚举

| 值 | 含义 |
|---|---|
| `SECURITY_HIGH` | 代表标的的**股价高点** |
| `SECTOR_INDEX_HIGH` | 板块 / 行业**指数**高点 |
| `PRICE_HIGH` | **商品或行业产品价格**高点（非股票） |
| `POLICY_EVENT` | **政策事件**日 |
| `COMPANY_EVENT` | **公司事件**日 |
| `SECTOR_MOVE` | **板块级异动**日（未归结到单一标的或指数） |
| `INDUSTRY_INDICATOR` | **行业指标**拐点（产量 / 景气） |
| `UNSPECIFIED` | **未界定**（记录在 peak 日 ±7 日内无依据） |

## 用法

    python research/scripts/build_peak_referent_v0_1.py
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
OUT = os.path.join(REP, "peak_referent_v0_1.json")
TOL = 7

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
#   规则：以「记录在 peak 日 ±7 日内**明确写了什么**」为准（见 rules.assignment_rule）。
#   每条附 basis：原文要点，供 ThreeC Agent 复核。
# ---------------------------------------------------------------------------
R = {
    # ---- UNSPECIFIED：peak 日 ±7 日内无任何 evidence / event 依据 ----
    "C-2016-CONS-BAIJIU-UPGRADE": ("UNSPECIFIED", "记录在 peak ±7 日内无 evidence / event；最近标的差 15 日"),
    "C-2016-HIEQ-CONSTR": ("UNSPECIFIED", "记录在 peak ±7 日内无 evidence / event；最近标的差 17 日"),
    "C-2019-AD": ("UNSPECIFIED", "记录在 peak ±7 日内无 evidence / event；最近标的差 84 日"),
    "C-2019-MIL-GROUP-RESTRUCTURE": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2024-FIN-BANK-DIVIDEND": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2024-RES-GOLD-CB": ("UNSPECIFIED", "记录未标注 peak"),
    "C-2025-FIN-INSURANCE": ("UNSPECIFIED", "记录未标注 peak"),

    # ---- SECURITY_HIGH：记录明确写的是（某只）股票的价格高点 ----
    "C-2016-PANEL-CYCLE": ("SECURITY_HIGH", "已登记标的 BOE 于同日创区间高点（记录内该日无 evidence）"),
    "C-2018-CONS-HOG-AFRICAN": ("SECURITY_HIGH", "「牧原股份于 2020-03-09 盘中触及历史最高价 139.92 元（不复权）」"),
    "C-2019-COMM-5G": ("SECURITY_HIGH", "「代表标的行情复核（前复权）」：中际旭创 2020-02-24 区间高点、中兴通讯 2020-02-25"),
    "C-2019-CONS-AESTHETICS": ("SECURITY_HIGH", "「爱美客 2021-02-18 盘中最高 1331.02 元（不复权历史最高）；华熙生物 2021-07-05 盘中最高 314.99 元」★ 点名的标的**未登记**进本 campaign"),
    "C-2019-CONS-BAIJIU-CORE": ("SECURITY_HIGH", "「贵州茅台盘中最高 2627.88 元、五粮液 357.19 元、泸州老窖 327.66 元」（同 evidence 亦记中证白酒指数 21663.85）"),
    "C-2019-CONSUMER-TWS": ("SECURITY_HIGH", "「立讯精密月内最高价 62.73 元出现在 2020-10」"),
    "C-2019-PHARMA-INNOV": ("SECURITY_HIGH", "「药明康德 / 泰格医药 前复权价于 2021-07-01 达区间最高（161.83 / 202.49）」"),
    "C-2020-CONS-BEAUTY-CN": ("SECURITY_HIGH", "「珀莱雅 2021-10-29 盘中最高 224.43 元（历史最高）」★ 点名的标的**未登记**进本 campaign"),
    "C-2020-CONS-DUTYFREE": ("SECURITY_HIGH", "「中国中免 2021-02-18 盘中最高 403.78 元（不复权），为历史最高价」"),
    "C-2020-CONS-WHITE-GOODS": ("SECURITY_HIGH", "「美的集团 2021-02-10 盘中最高 108.00；海尔智家 2021-02-18 盘中最高 35.95；格力电器 2021-01-06 盘中最高 66.78」★ 点名标的**均未登记**进本 campaign"),
    "C-2020-NEV": ("SECURITY_HIGH", "「7/13 汽车整车走强，比亚迪首板涨停、江淮两连板」；已登记标的 JAC / XUSHENG 同周创区间高点"),
    "C-2020-POWER-NE": ("SECURITY_HIGH", "「代表标的行情复核（前复权）」：阳光电源 2021-10-27、隆基绿能 2021-11-01、金风科技 2021-11-04"),
    "C-2021-NEV": ("SECURITY_HIGH", "「8/6 比亚迪大涨逾 5% 创历史新高」；CATL 于 2021-07-30 创区间高点"),
    "C-2022-CONS-SERVICE-REBOUND": ("SECURITY_HIGH", "「2023 年 1 月中国中免月内最高价 239.99 元，为该疫后修复脉冲期间的股价高点」"),
    "C-2022-POLICY": ("SECURITY_HIGH", "「6/10 比亚迪 A 股市值首破万亿（报 348.80 元 +8.19%）」"),
    "C-2022-POWER-GRID": ("SECURITY_HIGH", "「代表标的行情复核（前复权）」：国电南瑞 2024-10-08、平高电气 2024-10-14、许继电气 2024-07-09"),
    "C-2023-AD": ("SECURITY_HIGH", "「德赛西威 5 月上旬不足百元→7/11 最高 179.50（约 80%）」"),
    "C-2023-COMM-OPTICAL": ("SECURITY_HIGH", "「代表标的行情复核（前复权）」：中际旭创 2025-12-25 达 638.80、新易盛 2025-12-22 达 329.99"),
    "C-2023-CONS-VALUE-RETAIL": ("SECURITY_HIGH", "「万辰集团…2025-08-29 收于 210.81 元（区间最高）」★ 点名的标的**未登记**进本 campaign"),
    "C-2024-CONS-TRADE-IN": ("SECURITY_HIGH", "「2024-10-08 上述标的（美的/格力/海尔/海信家电/华帝/老板电器）同时出现区间最高价」；ROBAM 已登记"),

    # ---- SECTOR_INDEX_HIGH：记录明确写的是**指数**高点 ----
    "C-2019-SEMI-LOCALIZATION": ("SECTOR_INDEX_HIGH", "「申万半导体板块指数 2020-07-14 创 5869.83 的年内最高」"),
    "C-2020-MIL-EQUIP-ORDER": ("SECTOR_INDEX_HIGH", "「中证军工指数在 2021-12-01 达到 14748 点，为该轮区间高点」"),
    "C-2020-RES-LITHIUM": ("SECTOR_INDEX_HIGH", "「能源金属指数(399366.SZ)…指数区间最高点 3448.36 点（2021-09-13）」"),
    "C-2020-RES-NONFERROUS": ("SECTOR_INDEX_HIGH", "「中证有色金属指数(000819.SH)…区间最高点 8603.88 点（2021-09-13）」"),
    "C-2020-SEMI-EQUIPMENT": ("SECTOR_INDEX_HIGH", "「申万半导体板块指数 2021-07 月内最高 7642.58（2019–2021 全周期最高）」"),
    "C-2022-SEMI-DOWNTURN": ("SECTOR_INDEX_HIGH", "「申万半导体板块指数在 2022-08 出现年内唯一反弹高点 5380.53」"),
    "C-2023-AI-COMPUTE-SEMI": ("SECTOR_INDEX_HIGH", "「申万半导体板块指数 2023-04-10 达 5154.69，为 2023 年内最高」"),
    "C-2023-PHARMA-GLP1": ("SECTOR_INDEX_HIGH", "「Wind 减肥药指数 2023-09-08 至 10-16 共 21 个交易日上涨 26.43%…达顶点」"),
    "C-2024-SEMI-MEMORY": ("SECTOR_INDEX_HIGH", "「申万半导体板块指数 2025-10 月内最高 7964.33…为该指数新高」"),

    # ---- PRICE_HIGH：记录写的是**商品 / 行业产品价格**（非股票） ----
    "C-2020-PANEL-CYCLE": ("PRICE_HIGH", "「65 英寸 LCD 面板价格由 2020-01 的 162 美元/片最高涨至 2021-07 的 294 美元/片」"),
    "C-2020-RES-RAREEARTH": ("PRICE_HIGH", "「2021-11-09 北方稀土更新挂牌价，氧化镨钕价格飙升至 76.26 万元/吨」"),
    "C-2021-CONS-HOG-REVERSAL": ("PRICE_HIGH", "「2022 年 10 月中旬猪价创年内新高」"),
    "C-2021-RES-CHEM-DUALCTRL": ("PRICE_HIGH", "「受能耗双控政策影响…纯碱、黄磷、环氧丙烷、环氧树脂等多个化工原料价格一度飙升」"),

    # ---- POLICY_EVENT ----
    "C-2019-RES-DYE-SHOCK": ("POLICY_EVENT", "「2019-04-04 江苏盐城市委常委会决定彻底关闭响水化工园区」"),
    "C-2022-RE-POLICY-THREE": ("POLICY_EVENT", "「2022-11-28 证监会宣布…恢复涉房上市公司并购重组及配套融资」→ 11-29『第三支箭』次日板块暴涨"),
    "C-2023-HIEQ-HUMANOID": ("POLICY_EVENT", "「工业和信息化部于 2023-11-02 印发《人形机器人创新发展指导意见》」"),

    # ---- COMPANY_EVENT ----
    "C-2020-RE-DEBT-RISK": ("COMPANY_EVENT", "「中国恒大集团于 2021-12-03 未能偿付 2.6 亿美元债券偿付义务，构成违约」"),

    # ---- SECTOR_MOVE：板块级异动（未归结到单一标的或指数） ----
    "C-2020-FIN-BANK-CREDIT": ("SECTOR_MOVE", "「2021-03-03，A 股银行股全线大涨，宁波银行、南京银行等涨幅居前」"),
    "C-2023-FIN-SOE-VALUATION": ("SECTOR_MOVE", "「2023-05-11 非银金融行业中期策略：4 月以来保险明显领涨…『中特估』成为重要定价因素」"),
    "C-2023-HIEQ-ROBOT-PLUS": ("SECTOR_MOVE", "「2023-01-14 至 02-03 机械设备行业上涨 6.47%…机器人三级子行业上涨 13.48% 居前」"),
    "C-2024-FIN-BROKER-POLICY": ("SECTOR_MOVE", "「2024-10-08 A 股复市大幅高开后回落，同日成交额 3.5 万亿元创历史新高」"),
    "C-2024-ROBOTAXI": ("SECTOR_MOVE", "「7 月下旬高峰：大众交通 16 日涨 233%、锦江 15 天 9 板、金龙 12 天 7 板」"),
    "C-2024-V2X": ("SECTOR_MOVE", "「6/18 车路云全线爆发…10 余股涨停、多股 2 连板——源文记为『行情高峰』」"),
    "C-2025-ROBOTAXI": ("SECTOR_MOVE", "「6/24 A 股无人驾驶板块全线爆发…板块级启动」"),

    # ---- INDUSTRY_INDICATOR：行业指标（产量 / 景气）拐点 ----
    "C-2018-HIEQ-ROBOT-DOWN": ("INDUSTRY_INDICATOR", "「2019 年上半年前三季度中国工业机器人产量同比下滑 9.1%」；2019-10 产量转正（下行段结束）"),
    "C-2020-HIEQ-AUTOMATION": ("INDUSTRY_INDICATOR", "「通用自动化行业景气于 2021 年 Q3 见顶（埃斯顿年报自述）」"),
}


def main():
    conn = db.connect()
    al = json.load(io.open(ALIGN, encoding="utf-8"))
    rows = conn.execute("SELECT campaign_id, start_date, peak_date, end_date FROM campaigns ORDER BY campaign_id").fetchall()

    out, tally = {}, {k: 0 for k in REFERENTS}
    for cid, s, p, e in rows:
        v = al["by_campaign"].get(cid, {})
        ok = [x for x in (v.get("per_security") or []) if x.get("status") == "OK"]
        coincide = []
        nearest = None
        if p and ok:
            for x in ok:
                dd = abs((date.fromisoformat(p) - date.fromisoformat(x["peak_date"])).days)
                if dd <= TOL:
                    coincide.append({"security_id": x["security_id"], "peak_date": x["peak_date"], "delta_days": dd})
            best = min(ok, key=lambda x: abs((date.fromisoformat(p) - date.fromisoformat(x["peak_date"])).days))
            nearest = {"security_id": best["security_id"], "peak_date": best["peak_date"],
                       "delta_days": abs((date.fromisoformat(p) - date.fromisoformat(best["peak_date"])).days)}

        ref, basis = R.get(cid, ("UNSPECIFIED", "未在本表中声明"))
        tally[ref] += 1
        out[cid] = {
            "campaign_id": cid,
            "recorded": {"start": s, "peak": p, "end": e},
            "peak_referent": ref,
            "peak_referent_label": LABEL[ref],
            "referent_basis": basis,
            "referent_assigned_by": "Research Agent role（AI 离线判定，2026-10-08）",
            "referent_review_status": "PROVISIONAL",
            "securities_coincide": coincide,
            "nearest_security": nearest,
            "coverage": {"securities": (v.get("coverage") or {}).get("securities"),
                         "with_data": (v.get("coverage") or {}).get("with_data")},
        }

    res = {
        "artifact": "peak_referent",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_peak_referent_v0_1.py",
        "source_alignment": "research/research/reports/kline_alignment_v0_2.json",
        "position": ("Research-only —— 为 `peak_date` 补上**参照物**声明。"
                     "**不改** `campaigns` 表、**不改** `schema.sql`、**不改**任何日期数值。"),
        "why": ("2026-10-08 实测：53 个历史对象的 `peak_date` 中，17 个未被股价证实，"
                "而其中 14 个在记录里有明确依据 —— 依据指向指数 / 商品价 / 行业价 / 政策事件 / 板块级异动。"
                "`peak_date` 一个字段承载了至少 6 种语义而记录未声明是哪一种。"),
        "rules": {
            "tolerance_days": TOL,
            "assignment_rule": ("以「记录在 peak 日 ±%d 日内**明确写了什么**」为准，确定性判定，不依赖关键词猜测："
                                "写的是（已登记或未登记）**股票**价格高点 → SECURITY_HIGH；写的是**指数**高点 → SECTOR_INDEX_HIGH；"
                                "写的是**商品/行业产品价格** → PRICE_HIGH；写的是**政策文件/会议** → POLICY_EVENT；"
                                "写的是**公司事件** → COMPANY_EVENT；写的是**板块级异动**（未归结到单一标的或指数）→ SECTOR_MOVE；"
                                "写的是**行业产量/景气** → INDUSTRY_INDICATOR；**无依据** → UNSPECIFIED。" % TOL),
            "review": ("参照物属**研究判断**，全部标 `PROVISIONAL`，待 ThreeC Agent 按协议 §3 审查。"
                       "每条附 `referent_basis`（原文要点）以便复核。"),
            "no_score": "本 artifact **不含** score / ranking / probability。",
        },
        "enum": {k: LABEL[k] for k in REFERENTS},
        "summary": tally,
        "by_campaign": out,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
