# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码。**
用途：
  1) 主题族下钻（Sub-theme / Cycle 级）——区分「汽车智能化」与「新能源」等不同机制
  2) 选择偏差量化：ThreeC 记录的对象全部是「成功/有关注」的主题，
     故必须与「随机主题也会集中在夏季」的基准对照 → 检验窗口宽度 vs 全年均匀基准
  3) 农历 / 节假日检查（把公历窗口换算为农历与节日相对位置）
  4) 月份 vs 月-旬 退化窗口
纪律：只读。不做预测 / 概率 / 收益。
"""

import csv
import json
import math
import os
import random
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(20260916)
PERIOD = 365

# ------------------------------------------------------------ 农历近似换算
# 说明：不做精确农历换算（只用标准库，无第三方依赖）。
# 这里用「春节日期表」作为农历锚点，把公历 Doy 与春节的**相对天数**算出来，
# 用于检验「所谓月份规律是否其实是春节相对规律」。
SPRING_FESTIVAL = {
    2018: "2018-02-16", 2019: "2019-02-05", 2020: "2020-01-25", 2021: "2021-02-12",
    2022: "2022-02-01", 2023: "2023-01-22", 2024: "2024-02-10", 2025: "2025-01-29",
    2026: "2026-02-17", 2027: "2027-02-06",
}

# 固定 / 半固定日历锚点（公历）
FIXED_ANCHORS = {
    "元旦": "01-01",
    "春节(近似上限)": "02-20",
    "两会(3月上)": "03-05",
    "清明": "04-05",
    "五一": "05-01",
    "618": "06-18",
    "中报预告窗口(7/15前)": "07-15",
    "中报披露(7-8月)": "08-31",
    "国庆": "10-01",
    "双十一": "11-11",
    "中央经济工作会议(12月中)": "12-15",
    "年报预告(1月底前)": "01-31",
}


def d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def doy_norm(dd):
    n = dd.timetuple().tm_yday
    if dd.month >= 3 and (dd.year % 4 == 0 and (dd.year % 100 != 0 or dd.year % 400 == 0)):
        n -= 1
    return n


def md_to_doy_norm(mmdd):
    mm, dd = mmdd.split("-")
    return doy_norm(date(2025, int(mm), int(dd)))


# ------------------------------------------------------------ 载入

def load_rows():
    with open(os.path.join(HERE, "observation_anchors_raw.csv"), "r", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("anchor_doy_norm")]


# ------------------------------------------------------------ 主题族下钻

FAMILY_DEFS = {
    # Level 3 探索：同机制但名称不同的主题族
    "AUTO_SMART_DRIVING": {  # 自动驾驶 / 智能驾驶 / 车路云 / Robotaxi
        "cycles": ["auto_ad_2019", "auto_intelligence_2023", "auto_v2x_2024", "robotaxi_2024", "robotaxi_2025"],
        "macro": "汽车",
    },
    "AUTO_NEV_ELECTRIFICATION": {  # 新能源 / 电池 / 特斯拉链
        "cycles": ["auto_nev_2020", "auto_nev_2021"],
        "macro": "汽车",
    },
    "AUTO_POLICY_DEMAND": {  # 购置税 / 消费刺激
        "cycles": ["auto_policy_2022"],
        "macro": "汽车",
    },
    "AUTO_ALL": {
        "cycles": [
            "auto_ad_2019", "auto_intelligence_2023", "auto_v2x_2024", "robotaxi_2024",
            "robotaxi_2025", "auto_nev_2020", "auto_nev_2021", "auto_policy_2022",
        ],
        "macro": "汽车",
    },
    "PHARMA_ALL": {
        "cycles": ["medical_structural_upgrade_2019_2022"],
        "macro": "医药健康",
    },
}

# 显式年度级观测（人工确认口径；同一年一主题只保留最早锚点）
EXPLICIT = {
    "AUTO_SMART_DRIVING": [
        (2019, "2019-08-15", "C-2019-AD", "ANCHOR_A_EARLY_SIGNAL", "无人驾驶事件驱动（弱）"),
        (2023, "2023-06-12", "C-2023-AD", "ANCHOR_A_EARLY_SIGNAL", "L3 政策预期 + 智驾预热"),
        (2024, "2024-06-11", "C-2024-V2X", "ANCHOR_A_EARLY_SIGNAL", "车路云 170 亿备案"),
        (2024, "2024-07-08", "C-2024-ROBOTAXI", "ANCHOR_A_EARLY_SIGNAL", "萝卜快跑出圈"),
        (2025, "2025-06-22", "C-2025-ROBOTAXI", "ANCHOR_A_EARLY_SIGNAL", "特斯拉奥斯汀试点"),
    ],
    "AUTO_NEV_ELECTRIFICATION": [
        (2020, "2020-06-01", "C-2020-NEV", "ANCHOR_A_EARLY_SIGNAL", "特斯拉国产化"),
        (2021, "2021-06-01", "C-2021-NEV", "ANCHOR_A_EARLY_SIGNAL", "新能源渗透率跃升"),
    ],
    "AUTO_POLICY_DEMAND": [
        (2022, "2022-04-27", "C-2022-POLICY", "ANCHOR_A_EARLY_SIGNAL", "购置税减征 600 亿（复工预期）"),
    ],
}


def run_family_analysis(rows, label, cycles):
    sel = [r for r in rows if r["theme_cycle_id"] in cycles]
    sel = sorted(sel, key=lambda r: (int(r["year"]), int(r["anchor_doy_norm"])))
    # 年度去重
    by_year = {}
    for r in sel:
        y = int(r["year"])
        if y not in by_year:
            by_year[y] = r
    sel = [by_year[y] for y in sorted(by_year)]
    if len(sel) < 2:
        return None
    years = [int(r["year"]) for r in sel]
    xs = [int(r["anchor_doy_norm"]) for r in sel]
    n = len(xs)
    s = sorted(xs)
    med = st_median(xs)
    p25, p75 = st_quantile(xs, 0.25), st_quantile(xs, 0.75)
    lo, hi, span = circ_min_max(xs)
    return {
        "label": label,
        "n_years": n,
        "years": years,
        "campaigns": [r["campaign_id"] for r in sel],
        "md_list": [md(x) for x in xs],
        "doy_norm": xs,
        "median": med,
        "median_md": md(med),
        "p25": p25, "p25_md": md(p25),
        "p75": p75, "p75_md": md(p75),
        "iqr_days": p75 - p25,
        "mad_days": st_mad(xs),
        "span_days": span,
        "earliest_md": md(lo),
        "latest_md": md(hi),
        "month_distribution": month_dist(xs),
        "decade_distribution": decade_dist(xs),
        "spread_ratio": span / (PERIOD * (n - 1) / (n + 1)),
        "span_p": None,  # filled below
    }


def month_dist(xs):
    out = {}
    for x in xs:
        k = f"{month_of(x):02d}"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def decade_dist(xs):
    out = {}
    for x in xs:
        k = f"{month_of(x):02d}-{decade_of(x)}"
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


# 复用 analyze.py 的统计工具（保持实现一致）
def st_median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


def st_quantile(xs, q):
    s = sorted(xs)
    n = len(s)
    if n == 1:
        return float(s[0])
    pos = q * (n - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    if lo == hi:
        return float(s[lo])
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def st_mad(xs):
    m = st_median(xs)
    return st_median([abs(x - m) for x in xs])


def month_of(n):
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD)).month


def decade_of(n):
    dd = date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD))
    return "上旬" if dd.day <= 10 else ("中旬" if dd.day <= 20 else "下旬")


def md(n):
    if n is None:
        return None
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD)).strftime("%m-%d")


def circ_min_max(xs):
    s = sorted(x % PERIOD for x in xs)
    n = len(s)
    best_gap, best_i = -1, 0
    for i in range(n):
        gap = (s[(i + 1) % n] - s[i]) % PERIOD
        if gap > best_gap:
            best_gap, best_i = gap, i
    return s[(best_i + 1) % n], s[best_i], (s[best_i] - s[(best_i + 1) % n]) % PERIOD


def span_perm_p(xs, b=50000):
    n = len(xs)
    if n < 2:
        return None, None
    _, _, span = circ_min_max(xs)
    exp = PERIOD * (n - 1) / (n + 1)
    cnt = sum(1 for _ in range(b) if circ_min_max([random.randrange(1, PERIOD + 1) for _ in range(n)])[2] <= span)
    return span / exp, cnt / b


def main():
    rows = load_rows()
    draft = {}

    print("#" * 78)
    print("A. 主题族下钻（年度去重）")
    for label, spec in FAMILY_DEFS.items():
        a = run_family_analysis(rows, label, spec["cycles"])
        if not a:
            print(f"\n-- {label}: N<2，不足以分析")
            continue
        r, p = span_perm_p(a["doy_norm"])
        a["spread_ratio"], a["span_p"] = r, p
        draft[label] = a
        print(f"\n-- {label}  N={a['n_years']}  cycles={spec['cycles']}")
        print(f"   years={a['years']}  anchors={a['md_list']}")
        print(f"   median={a['median_md']}  P25={a['p25_md']}  P75={a['p75_md']}  IQR={a['iqr_days']}d  MAD={a['mad_days']}d")
        print(f"   span={a['span_days']}d ({a['earliest_md']}~{a['latest_md']})  months={a['month_distribution']}  decades={a['decade_distribution']}")
        print(f"   spread_ratio={r:.3f}  empirical_p={p:.4f}")

    print("\n" + "#" * 78)
    print("B. 农历 / 节假日相对位置检查")
    lp = {}
    for label, a in draft.items():
        rel = []
        for y, m in zip(a["years"], a["md_list"]):
            ad = date(2025, int(m[:2]), int(m[3:]))
            doy = doy_norm(ad)
            sf = doy_norm(d(SPRING_FESTIVAL[y]))
            rel.append({"year": y, "anchor_md": m, "days_after_spring_festival": doy - sf})
        lp[label] = rel
        print(f"\n-- {label}: 距春节（自然日）")
        for x in rel:
            print(f"   {x['year']}  锚点 {x['anchor_md']}  →  春节后第 {x['days_after_spring_festival']} 天")

    print("\n" + "#" * 78)
    print("C. 与固定日历锚点距离")
    fixed = {k: md_to_doy_norm(v) for k, v in FIXED_ANCHORS.items()}
    for label, a in draft.items():
        rows_out = []
        for x in a["doy_norm"]:
            nearest = min(fixed.items(), key=lambda kv: min(abs(x - kv[1]), PERIOD - abs(x - kv[1])))
            dist = min(abs(x - nearest[1]), PERIOD - abs(x - nearest[1]))
            rows_out.append((md(x), nearest[0], dist))
        print(f"\n-- {label}")
        for m, nm, dist in rows_out:
            print(f"   {m}  最近固定锚点={nm}  距离={dist}d")

    out = {"families": draft, "lunar_proximity": lp, "fixed_anchor_doy": fixed}
    with open(os.path.join(HERE, "family_analysis.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)


if __name__ == "__main__":
    main()
