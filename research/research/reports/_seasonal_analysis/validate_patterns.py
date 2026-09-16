# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码。**

任务：对**每一个具体候选 Pattern**做完整验证卡：
  样本量 / 年份列表 / 中位数 / 均值 / P25 / P75 / IQR / MAD / 最早 / 最晚 /
  月份分布 / 窗口(A 分位数 / B MAD k=1,1.5,2 / C 月 / C2 月旬) /
  窗口内外对照 / historical recurrence / 稳定性(前后半段 + 漂移) /
  留一法(单年主导检验) / permutation 经验 p / 均匀基准对照 /
  数据质量(anchor 来源 / 日期精度 / provisional 比例) / 机制假设标签
纪律：只读。不做预测 / 概率 / 收益 / 买卖信号。
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

# ------------------------------------------------------------------ 工具

def doy_norm(dd):
    n = dd.timetuple().tm_yday
    if dd.month >= 3 and (dd.year % 4 == 0 and (dd.year % 100 != 0 or dd.year % 400 == 0)):
        n -= 1
    return n


def from_doy(n):
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD))


def md(n):
    return from_doy(n).strftime("%m-%d") if n is not None else None


def month_of(n):
    return from_doy(n).month


def decade_of(n):
    dd = from_doy(n)
    return "上旬" if dd.day <= 10 else ("中旬" if dd.day <= 20 else "下旬")


def med(xs):
    s = sorted(xs)
    n = len(s)
    return None if not n else (float(s[n // 2]) if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0)


def q(xs, p):
    s = sorted(xs)
    n = len(s)
    if n == 1:
        return float(s[0])
    pos = p * (n - 1)
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return float(s[lo]) if lo == hi else s[lo] + (s[hi] - s[lo]) * (pos - lo)


def mad_of(xs):
    m = med(xs)
    return med([abs(x - m) for x in xs])


def circ_min_max(xs):
    s = sorted(x % PERIOD for x in xs)
    n = len(s)
    bg, bi = -1, 0
    for i in range(n):
        g = (s[(i + 1) % n] - s[i]) % PERIOD
        if g > bg:
            bg, bi = g, i
    return s[(bi + 1) % n], s[bi], (s[bi] - s[(bi + 1) % n]) % PERIOD


def in_win(x, ws, we=None):
    """支持「数值型窗口 (start_doy, end_doy)」。"""
    if isinstance(ws, (int, float)) and we is not None:
        x %= PERIOD
        ws %= PERIOD
        we %= PERIOD
        if ws <= we:
            return ws <= x <= we
        return x >= ws or x <= we
    return False


def shift(a, b):
    if a is None or b is None:
        return 0
    raw = b - a
    if raw > PERIOD / 2:
        raw -= PERIOD
    if raw < -PERIOD / 2:
        raw += PERIOD
    return raw


# ------------------------------------------------------------------ 候选定义
# 主题族（Level 3，同机制不同 Cycle）— 年度去重
CANDIDATES = {
    "SOP-01": {
        "name": "汽车智能化启动窗口（智能驾驶/车路云/Robotaxi）",
        "theme_key": "汽车/智能驾驶大主题",
        "cycles": ["auto_ad_2019", "auto_intelligence_2023", "auto_v2x_2024", "robotaxi_2024", "robotaxi_2025"],
        "pattern_type": "MIXED",
        "mechanism": [
            "政策/标准日历（工信部吹风、L3 准入、车路云试点城市名单）",
            "国际产业事件（特斯拉 Robotaxi 试点 / FSD 进展）",
            "北京/武汉等地车路云大额招标备案",
        ],
        "exclude_years": [],
    },
    "SOP-02": {
        "name": "汽车电动化启动窗口（新能源/电池/特斯拉产业链）",
        "theme_key": "汽车/新能源",
        "cycles": ["auto_nev_2020", "auto_nev_2021"],
        "pattern_type": "INDUSTRY_CYCLE",
        "mechanism": ["新能源渗透率跃升 + 电池龙头产能/市值里程碑", "特斯拉国产化放量"],
        "exclude_years": [],
    },
    "SOP-03": {
        "name": "汽车全主题夏季启动（跨机制并集）",
        "theme_key": "汽车（Macro Theme）",
        "cycles": [
            "auto_ad_2019", "auto_intelligence_2023", "auto_v2x_2024", "robotaxi_2024",
            "robotaxi_2025", "auto_nev_2020", "auto_nev_2021", "auto_policy_2022",
        ],
        "pattern_type": "MIXED",
        "mechanism": ["多机制叠加：政策刺激 + 电动化 + 智能化 + 事件驱动"],
        "exclude_years": [],
    },
    "SOP-04": {
        "name": "医药健康结构性升级启动窗口",
        "theme_key": "医药健康",
        "cycles": ["medical_structural_upgrade_2019_2022"],
        "pattern_type": "CALENDAR_DRIVEN",
        "mechanism": ["政策/制度日历（集采、科创板、医保谈判）", "疫情外生冲击"],
        "exclude_years": [],
    },
}


def load_rows():
    with open(os.path.join(HERE, "observation_anchors_raw.csv"), "r", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("anchor_doy_norm")]


def select(rows, cycles):
    sel = [r for r in rows if r["theme_cycle_id"] in cycles]
    by_year = {}
    for r in sorted(sel, key=lambda x: (int(x["year"]), int(x["anchor_doy_norm"]))):
        y = int(r["year"])
        if y not in by_year:
            by_year[y] = r
    return [by_year[y] for y in sorted(by_year)]


def permutation_p(xs, b=100000):
    n = len(xs)
    if n < 2:
        return None, None
    _, _, span = circ_min_max(xs)
    exp = PERIOD * (n - 1) / (n + 1)
    cnt = sum(1 for _ in range(b) if circ_min_max([random.randrange(1, PERIOD + 1) for _ in range(n)])[2] <= span)
    return span / exp, cnt / b


def windows(xs):
    n = len(xs)
    out = {}
    # A 分位数
    out["A_quantile_P25_P75"] = {"start": q(xs, .25), "end": q(xs, .75), "method": "P25–P75 分位数窗口"}
    # B MAD
    for k in (1.0, 1.5, 2.0):
        m, mdv = med(xs), mad_of(xs)
        sd = (mdv or 0) * 1.4826
        if sd <= 0:
            out[f"B_mad_k{k}"] = {"start": float(min(xs)), "end": float(max(xs)),
                                  "method": f"Median±{k}·MAD（MAD=0 → 退化为极差）"}
        else:
            out[f"B_mad_k{k}"] = {"start": m - k * sd, "end": m + k * sd, "method": f"Median±{k}·MAD（σ 一致化）"}
    # C 月
    ms = sorted({month_of(x) for x in xs})
    out["C_month"] = {"start": ms[0], "end": ms[-1], "method": "月份窗口（退化）"}
    # C2 月旬
    dk = sorted({(month_of(x), {"上旬": 0, "中旬": 1, "下旬": 2}[decade_of(x)]) for x in xs})
    out["C2_month_decade"] = {"start": f"{dk[0][0]:02d}-{'上中下'[dk[0][1]]}旬",
                              "end": f"{dk[-1][0]:02d}-{'上中下'[dk[-1][1]]}旬",
                              "method": "月-旬窗口（退化）"}
    return out


def recurrence(xs, s, e, years):
    hits = [years[i] for i, x in enumerate(xs) if in_win(x, s, e)]
    return {
        "hits": len(hits), "n_years": len(xs),
        "ratio": len(hits) / len(xs),
        "hits_years": hits,
        "miss_years": [years[i] for i, x in enumerate(xs) if years[i] not in hits],
        "label": "历史样本中的窗口复现情况（不是未来概率）",
    }


def stability(xs, years):
    pairs = sorted(zip(years, xs))
    n = len(pairs)
    if n < 4:
        return {"status": "INSUFFICIENT_N", "note": f"N={n}<4，不做前后半段检验（避免把 2 点说成稳定）"}
    k = n // 2
    f_, s_ = [p[1] for p in pairs[:k]], [p[1] for p in pairs[k:]]
    sh = shift(med(f_), med(s_))
    fq = (q(f_, .25), q(f_, .75))
    sq = (q(s_, .25), q(s_, .75))
    ov = max(0.0, min(fq[1], sq[1]) - max(fq[0], sq[0]))
    flag = "DRIFTING" if abs(sh) >= 45 else ("MILD_DRIFT" if abs(sh) >= 21 else "STABLE")
    return {
        "status": "SPLIT",
        "first_years": [p[0] for p in pairs[:k]], "second_years": [p[0] for p in pairs[k:]],
        "first_median_md": md(med(f_)), "second_median_md": md(med(s_)),
        "median_shift_days": sh, "iqr_overlap_days": ov, "drift_flag": flag,
        "note": "|位移|≥45d→DRIFTING；21–44d→MILD_DRIFT；<21d→STABLE",
    }


def loo(xs, years, s, e):
    n = len(xs)
    if n < 3:
        return {"status": "N<3", "note": "样本太小，不做留一法"}
    base_hits = sum(1 for x in xs if in_win(x, s, e))
    base_med = med(xs)
    per = []
    for i in range(n):
        sub = [x for j, x in enumerate(xs) if j != i]
        per.append({
            "removed_year": years[i],
            "median_after": md(med(sub)),
            "median_shift_days": abs(shift(base_med, med(sub))),
            "hits_after": sum(1 for x in sub if in_win(x, s, e)),
            "n_after": len(sub),
        })
    maxs = max(p["median_shift_days"] for p in per)
    drop = base_hits - min(p["hits_after"] for p in per)
    return {
        "status": "OK", "base_hits": base_hits, "base_median_md": md(base_med),
        "max_median_shift_on_removal_days": maxs, "max_hit_drop_on_removal": drop,
        "single_year_dominated": bool(drop >= 2 or maxs >= 30),
        "per_removal": per,
    }


def main():
    rows = load_rows()
    results = {}

    for pid, spec in CANDIDATES.items():
        sel = select(rows, spec["cycles"])
        if len(sel) < 2:
            results[pid] = {"pattern_id": pid, **spec, "status": "INSUFFICIENT_N", "n_years": len(sel)}
            continue
        years = [int(r["year"]) for r in sel]
        xs = [int(r["anchor_doy_norm"]) for r in sel]
        n = len(xs)
        lo, hi, span = circ_min_max(xs)
        m = med(xs)
        ratio, pval = permutation_p(xs, 20000)
        w = windows(xs)
        rec = {k: recurrence(xs, v["start"], v["end"], years)
               for k, v in w.items() if isinstance(v["start"], (int, float))}
        res = {
            "pattern_id": pid,
            "name": spec["name"],
            "theme_key": spec["theme_key"],
            "pattern_type": spec["pattern_type"],
            "mechanism_hypotheses": spec["mechanism"],
            "cycles": spec["cycles"],
            "n_years": n,
            "years": years,
            "campaigns": [r["campaign_id"] for r in sel],
            "anchor_types": sorted({r["anchor_type"] for r in sel}),
            "anchor_dates": [r["anchor_date"] for r in sel],
            "anchor_md": [r["anchor_md"] for r in sel],
            "anchor_doy_norm": xs,
            "median_doy": m, "median_md": md(m),
            "mean_doy": sum(xs) / n, "mean_md": md(sum(xs) / n),
            "p25": q(xs, .25), "p25_md": md(q(xs, .25)),
            "p75": q(xs, .75), "p75_md": md(q(xs, .75)),
            "iqr_days": q(xs, .75) - q(xs, .25),
            "mad_days": mad_of(xs),
            "earliest_md": md(lo), "latest_md": md(hi), "span_days": span,
            "months_distinct": len({month_of(x) for x in xs}),
            "month_distribution": {f"{mm:02d}": sum(1 for x in xs if month_of(x) == mm) for mm in range(1, 13)
                                   if sum(1 for x in xs if month_of(x) == mm)},
            "month_decade_distribution": {
                f"{mm:02d}-{dcd}": sum(1 for x in xs if month_of(x) == mm and decade_of(x) == dcd)
                for mm in range(1, 13) for dcd in ("上旬", "中旬", "下旬")
                if sum(1 for x in xs if month_of(x) == mm and decade_of(x) == dcd)
            },
            "windows": {k: {"start_md": md(v["start"]) if isinstance(v["start"], (int, float)) else v["start"],
                            "end_md": md(v["end"]) if isinstance(v["end"], (int, float)) else v["end"],
                            "start_doy": v["start"] if isinstance(v["start"], (int, float)) else None,
                            "end_doy": v["end"] if isinstance(v["end"], (int, float)) else None,
                            "method": v["method"]}
                        for k, v in w.items()},
            "historical_recurrence": rec,
            "spread_ratio_vs_uniform": ratio,
            "empirical_span_p_one_sided": pval,
            "stability": stability(xs, years),
            "leave_one_out": loo(xs, years, q(xs, .25), q(xs, .75)),
            "data_quality": {
                "all_provisional": all(r["research_status"] == "PROVISIONAL" for r in sel),
                "has_conflict": any(r["has_conflict"] == "True" for r in sel),
                "anchor_source": sorted({r["anchor_source"] for r in sel}),
                "date_precision": "EXACT_DATE（日级；但 verification_method 多为 unknown → 未经行情人工核验）",
                "provisional_count": sum(1 for r in sel if r["research_status"] == "PROVISIONAL"),
            },
        }
        results[pid] = res

    with open(os.path.join(HERE, "pattern_validation.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    # ---------------- 打印验证卡
    for pid, r in results.items():
        print("=" * 80)
        print(f"[{pid}] {r.get('name')}")
        if r.get("status") == "INSUFFICIENT_N":
            print(f"   INSUFFICIENT_N (n={r['n_years']})")
            continue
        print(f"  N={r['n_years']}  years={r['years']}")
        print(f"  campaigns={r['campaigns']}")
        print(f"  anchors={r['anchor_md']}  (doy_norm={r['anchor_doy_norm']})")
        print(f"  median={r['median_md']}  mean={r['mean_md']}  P25={r['p25_md']}  P75={r['p75_md']}")
        print(f"  IQR={r['iqr_days']:.1f}d  MAD={r['mad_days']:.1f}d  span={r['span_days']}d ({r['earliest_md']}~{r['latest_md']})")
        print(f"  months={r['month_distribution']}  decades={r['month_decade_distribution']}")
        print(f"  spread_ratio={r['spread_ratio_vs_uniform']:.3f}  empirical_p={r['empirical_span_p_one_sided']:.5f}")
        print("  windows:")
        for k, v in r["windows"].items():
            print(f"    {k:22s} {v['start_md']} ~ {v['end_md']}   [{v['method']}]")
        print("  recurrence:")
        for k, v in r["historical_recurrence"].items():
            print(f"    {k:22s} {v['hits']}/{v['n_years']}  hit={v['hits_years']}  miss={v['miss_years']}")
        st = r["stability"]
        if st["status"] == "SPLIT":
            print(f"  stability: {st['first_years']}={st['first_median_md']} vs {st['second_years']}={st['second_median_md']}"
                  f"  shift={st['median_shift_days']:.0f}d  overlap={st['iqr_overlap_days']:.0f}d  → {st['drift_flag']}")
        else:
            print(f"  stability: {st['note']}")
        l = r["leave_one_out"]
        if l.get("status") == "OK":
            print(f"  LOO: max_median_shift={l['max_median_shift_on_removal_days']:.0f}d "
                  f"max_hit_drop={l['max_hit_drop_on_removal']}  single_year_dominated={l['single_year_dominated']}")
        print(f"  data_quality: {json.dumps(r['data_quality'], ensure_ascii=False)}")


if __name__ == "__main__":
    main()
