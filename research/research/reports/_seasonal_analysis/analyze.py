# -*- coding: utf-8 -*-
"""
TEMPORARY RESEARCH SCRIPT — Seasonal Observation Pattern Discovery v0.1
========================================================================
STATUS: 临时研究脚本。**不是产品代码。**
用途：对 observation_anchors_raw.csv 做统计验证
      - 时间集中度（中位数 / P25 / P75 / IQR / MAD / 最早 / 最晚 / 月份分布）
      - 典型观察窗口（分位数窗口 / Median±k·MAD / 月份退化）
      - Historical Recurrence（窗口内命中 / 有效年份）
      - 窗口外反事实（均匀基准 + permutation 探索性随机基准）
      - 稳定性 / 漂移（前半段 vs 后半段）
      - 样本量敏感性（N=2 / 3 / 4 / 5+）
纪律：只读，不写 DB / schema / export / contract。不做预测 / 概率 / 收益。
"""

import csv
import json
import math
import os
import random
from datetime import datetime, date

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(20260916)

PERIOD = 365  # 归一化后的年长基准


# ------------------------------------------------------------------ 基础统计

def mean(xs):
    return sum(xs) / len(xs) if xs else None


def median(xs):
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return float(s[n // 2])
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def quantile(xs, q):
    """线性插值分位数（numpy 默认口径）。"""
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    if n == 1:
        return float(s[0])
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(s[lo])
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def mad(xs):
    """中位数绝对偏差（稳健离散度）。"""
    m = median(xs)
    if m is None:
        return None
    return median([abs(x - m) for x in xs])


def circ_min_max(xs):
    """环形意义下的最早 / 最晚（取跨度最小的一年内区间）。"""
    if not xs:
        return None, None, None
    s = sorted(x % PERIOD for x in xs)
    n = len(s)
    # 环形最大空隙
    best_gap, best_i = -1, 0
    for i in range(n):
        nxt = s[(i + 1) % n]
        gap = (nxt - s[i]) % PERIOD
        if gap > best_gap:
            best_gap, best_i = gap, i
    start = s[(best_i + 1) % n]
    end = s[best_i]
    span = (end - start) % PERIOD
    return start, end, span


def circular_center(xs):
    """环形中心（用向量均值，处理 12/1 月边界）。"""
    if not xs:
        return None
    ang = [2 * math.pi * (x % PERIOD) / PERIOD for x in xs]
    sx = sum(math.cos(a) for a in ang)
    sy = sum(math.sin(a) for a in ang)
    if abs(sx) < 1e-12 and abs(sy) < 1e-12:
        return None
    theta = math.atan2(sy, sx)
    if theta < 0:
        theta += 2 * math.pi
    return theta * PERIOD / (2 * math.pi)


def doy_to_md(n, norm=True):
    """把归一化序数转回 MM-DD（非闰年基准）。"""
    n = int(round(n)) % PERIOD
    if n == 0:
        n = PERIOD
    d = date(2025, 1, 1).toordinal() + n - 1
    dd = date.fromordinal(d)
    return dd.strftime("%m-%d")


def month_of(n):
    n = int(round(n))
    return date.fromordinal(date(2025, 1, 1).toordinal() + ((n - 1) % PERIOD)).month


def decade_of(n):
    """上旬 / 中旬 / 下旬。"""
    dd = date.fromordinal(date(2025, 1, 1).toordinal() + ((int(round(n)) - 1) % PERIOD))
    return "上旬" if dd.day <= 10 else ("中旬" if dd.day <= 20 else "下旬")


def in_circular_window(x, ws, we):
    """x 是否在环形窗口 [ws, we] 内（允许跨年）。"""
    x %= PERIOD
    ws %= PERIOD
    we %= PERIOD
    if ws <= we:
        return ws <= x <= we
    return x >= ws or x <= we


# ------------------------------------------------------------------ 窗口构建

def window_quantile(xs):
    """方法 A：P25~P75 分位数窗口。"""
    a, b = quantile(xs, 0.25), quantile(xs, 0.75)
    return a, b, "P25-P75_QUANTILE"


def window_mad(xs, k):
    """方法 B：Median ± k·MAD 稳健窗口。按 1.4826 缩放为 σ 一致估计。"""
    m, md = median(xs), mad(xs)
    if md is None:
        return None, None, f"MEDIAN_PLUS_{k}MAD"
    sd = md * 1.4826
    if sd == 0:
        # MAD=0（高度集中或 N 小）→ 退化为极差窗口
        lo, hi = min(xs), max(xs)
        return float(lo), float(hi), f"MEDIAN_PLUS_{k}MAD(ZERO_MAD_FALLBACK_RANGE)"
    return m - k * sd, m + k * sd, f"MEDIAN_PLUS_{k}MAD"


def window_month(xs):
    """方法 C：月份退化窗口（数据太少时）。"""
    ms = sorted({month_of(x) for x in xs})
    if not ms:
        return None, None, "MONTH_WINDOW"
    return ms[0], ms[-1], "MONTH_WINDOW"


def window_month_decade(xs):
    """方法 C2：月-旬窗口（上/中/下旬）。"""
    keys = sorted({(month_of(x), {"上旬": 0, "中旬": 1, "下旬": 2}[decade_of(x)]) for x in xs})
    if not keys:
        return None, None, "MONTH_DECADE_WINDOW"
    return keys[0], keys[-1], "MONTH_DECADE_WINDOW"


# ------------------------------------------------------------------ 反事实

def uniformity_test(xs, n_bootstrap=20000):
    """
    窗口外反事实 / 均匀性检验（探索性）。
    做法：
      1) 用「最小跨度窗口」= 覆盖全部观测的最小环形区间，衡量集中度
         （任意 N 点都必然能被某窗口覆盖，故必须与随机基准比）。
      2) 随机基准：从 1..365 均匀抽 N 个点，重复 B 次，
         统计「最小覆盖跨度 <= 实际跨度」的比例 → 经验 p 值（单尾）。
    """
    xs = [x % PERIOD for x in xs]
    n = len(xs)
    if n < 2:
        return {
            "min_span": None,
            "expected_span_uniform": None,
            "span_p_value": None,
            "note": "N<2，无法评估集中度",
        }
    _, _, span = circ_min_max(xs)

    # 均匀基准：N 点最小覆盖跨度的期望（解析：E[min span] = (N-1)/(N+1)*PERIOD）
    exp_span = PERIOD * (n - 1) / (n + 1)

    cnt = 0
    for _ in range(n_bootstrap):
        smp = [random.randrange(1, PERIOD + 1) for _ in range(n)]
        _, _, sp = circ_min_max(smp)
        if sp <= span:
            cnt += 1
    p = cnt / n_bootstrap
    return {
        "min_span_days": span,
        "expected_span_uniform": exp_span,
        "span_ratio": span / exp_span if exp_span else None,
        "span_p_value_one_sided": p,
        "n_bootstrap": n_bootstrap,
        "note": "单尾经验 p（越小越集中）；探索性，不作为显著性断言；N 小时仅作描述",
    }


def inside_outside_contrast(xs, ws, we):
    """
    窗口内 / 窗口外对照。
    输出：窗口命中数、窗口宽度、窗口内密度 vs 全年均匀密度、以及
    「窗口占全年比例」与「命中占比」的对比。
    """
    n = len(xs)
    if n == 0 or ws is None:
        return {}
    hit = sum(1 for x in xs if in_circular_window(x, ws, we))
    width = (we - ws) % PERIOD + 1 if ws <= we else PERIOD - (ws - we) + 1
    width = max(1, min(PERIOD, int(round(width))))
    return {
        "n": n,
        "hits_in_window": hit,
        "window_width_days": width,
        "window_share_of_year": width / PERIOD,
        "hit_share": hit / n,
        "density_ratio": (hit / n) / (width / PERIOD) if width else None,
        "uniform_expected_hits": n * width / PERIOD,
        "note": "density_ratio>1 表示窗口内比全年均匀分布更密；这是历史样本描述，不是未来概率",
    }


# ------------------------------------------------------------------ 稳定性

def stability_split(xs, years):
    """前半段 vs 后半段（按年份排序中位数切分）。"""
    pairs = sorted(zip(years, xs), key=lambda p: p[0])
    n = len(pairs)
    if n < 4:
        return {"status": "INSUFFICIENT_SPLIT", "note": f"N={n}<4，不做前后半段比较"}
    k = n // 2
    first = pairs[:k]
    second = pairs[k:]
    f_x = [p[1] for p in first]
    s_x = [p[1] for p in second]
    fm, sm = median(f_x), median(s_x)
    shift = None
    if fm is not None and sm is not None:
        # 环形最短方向位移
        raw = sm - fm
        if raw > PERIOD / 2:
            raw -= PERIOD
        if raw < -PERIOD / 2:
            raw += PERIOD
        shift = raw
    fq = (quantile(f_x, 0.25), quantile(f_x, 0.75))
    sq = (quantile(s_x, 0.25), quantile(s_x, 0.75))
    overlap = None
    if None not in fq and None not in sq:
        lo = max(fq[0], sq[0])
        hi = min(fq[1], sq[1])
        overlap = max(0.0, hi - lo)
    return {
        "status": "SPLIT",
        "first_half_years": [p[0] for p in first],
        "second_half_years": [p[0] for p in second],
        "first_median": fm,
        "second_median": sm,
        "median_shift_days": shift,
        "first_iqr": list(fq) if None not in fq else None,
        "second_iqr": list(sq) if None not in sq else None,
        "iqr_overlap_days": overlap,
        "drift_flag": (
            "DRIFTING"
            if (shift is not None and abs(shift) >= 45)
            else ("MILD_DRIFT" if (shift is not None and abs(shift) >= 21) else "STABLE")
        ),
        "note": "|中位数位移|>=45 天 → DRIFTING；21–44 天 → MILD_DRIFT；<21 天 → STABLE",
    }


def leave_one_out(xs, years, ws, we):
    """留一年法：检查规律是否由单一年份主导。"""
    out = []
    for i in range(len(xs)):
        sub = [x for j, x in enumerate(xs) if j != i]
        m = median(sub)
        hit = sum(1 for x in sub if in_circular_window(x, ws, we))
        out.append(
            {
                "removed_year": years[i],
                "median_after_removal": m,
                "hits_after_removal": hit,
                "n_after": len(sub),
            }
        )
    if not out:
        return {}
    base_hits = sum(1 for x in xs if in_circular_window(x, ws, we))
    meds = [o["median_after_removal"] for o in out if o["median_after_removal"] is not None]
    base_med = median(xs)
    max_shift = max((circ_shift(base_med, m) for m in meds), default=0)
    hit_drop = base_hits - min(o["hits_after_removal"] for o in out)
    return {
        "base_median": base_med,
        "base_hits": base_hits,
        "max_median_shift_on_removal": max_shift,
        "max_hit_drop_on_removal": hit_drop,
        "single_year_dominated": bool(hit_drop >= 2 or max_shift >= 30),
        "per_removal": out,
    }


def circ_shift(a, b):
    if a is None or b is None:
        return 0
    raw = b - a
    if raw > PERIOD / 2:
        raw -= PERIOD
    if raw < -PERIOD / 2:
        raw += PERIOD
    return abs(raw)


# ------------------------------------------------------------------ 主流程

def load_rows():
    path = os.path.join(HERE, "observation_anchors_raw.csv")
    with open(path, "r", encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if r.get("anchor_doy_norm")]


def analyze_family(name, rows):
    """对一个「主题族」做全套统计。"""
    rows = sorted(rows, key=lambda r: int(r["year"]))
    years = [int(r["year"]) for r in rows]
    xs = [int(r["anchor_doy_norm"]) for r in rows]
    n = len(xs)

    # 年份级去重后（同一年取最早锚点）——调用方已按 unit 聚合时不再需要
    res = {
        "family": name,
        "n_years": n,
        "years": years,
        "anchor_doy_norm": xs,
        "anchor_md": [r["anchor_md"] for r in rows],
        "anchor_types": sorted({r["anchor_type"] for r in rows}),
        "campaigns": [r["campaign_id"] for r in rows],
        "anchor_source": sorted({r["anchor_source"] for r in rows}),
    }

    res["mean"] = mean(xs)
    res["median"] = median(xs)
    res["p25"] = quantile(xs, 0.25)
    res["p75"] = quantile(xs, 0.75)
    res["iqr"] = (res["p75"] - res["p25"]) if None not in (res["p25"], res["p75"]) else None
    res["mad"] = mad(xs)
    lo, hi, span = circ_min_max(xs)
    res["circular_earliest"] = lo
    res["circular_latest"] = hi
    res["circular_span_days"] = span
    res["circular_center"] = circular_center(xs)
    res["circular_center_md"] = doy_to_md(res["circular_center"]) if res["circular_center"] else None

    res["md_list"] = [doy_to_md(x) for x in xs]
    res["earliest_md"] = doy_to_md(lo)
    res["latest_md"] = doy_to_md(hi)

    # 月份分布
    mc = {}
    for x in xs:
        m = month_of(x)
        mc[f"{m:02d}"] = mc.get(f"{m:02d}", 0) + 1
    res["month_distribution"] = dict(sorted(mc.items()))
    res["months_distinct"] = len(mc)

    # 月-旬分布
    dc = {}
    for x in xs:
        k = f"{month_of(x):02d}-{decade_of(x)}"
        dc[k] = dc.get(k, 0) + 1
    res["month_decade_distribution"] = dict(sorted(dc.items()))

    # 窗口构建
    wa_s, wa_e, wa_m = window_quantile(xs)
    res["window_A_quantile"] = {"start": wa_s, "end": wa_e, "method": wa_m}
    ws, we, wm = window_mad(xs, 1.0)
    res["window_B_mad_k1"] = {"start": ws, "end": we, "method": wm}
    ws2, we2, _ = window_mad(xs, 1.5)
    res["window_B_mad_k15"] = {"start": ws2, "end": we2, "method": "MEDIAN_PLUS_1.5MAD"}
    ws3, we3, _ = window_mad(xs, 2.0)
    res["window_B_mad_k2"] = {"start": ws3, "end": we3, "method": "MEDIAN_PLUS_2MAD"}
    res["window_C_month"] = {"start": window_month(xs)[0], "end": window_month(xs)[1], "method": "MONTH_WINDOW"}
    res["window_C2_month_decade"] = {
        "start": window_month_decade(xs)[0],
        "end": window_month_decade(xs)[1],
        "method": "MONTH_DECADE_WINDOW",
    }

    # 反事实
    res["uniformity"] = uniformity_test(xs)
    contrast = {}
    for key, (s, e) in {
        "A_quantile": (wa_s, wa_e),
        "B_mad_k1": (ws, we),
        "B_mad_k15": (ws2, we2),
        "B_mad_k2": (ws3, we3),
    }.items():
        if s is None or e is None:
            continue
        c = inside_outside_contrast(xs, s, e)
        c["window"] = {"start": s, "end": e}
        c["window_md"] = {"start": doy_to_md(s), "end": doy_to_md(e)}
        contrast[key] = c
    res["window_contrast"] = contrast

    # historical recurrence（以 P25-P75 为主口径；MAD k=1 为对照）
    if wa_s is not None:
        hits = sum(1 for x in xs if in_circular_window(x, wa_s, wa_e))
        res["historical_recurrence_quantile"] = {
            "hits": hits,
            "n_years": n,
            "ratio": hits / n,
            "hits_years": [years[i] for i, x in enumerate(xs) if in_circular_window(x, wa_s, wa_e)],
            "miss_years": [years[i] for i, x in enumerate(xs) if not in_circular_window(x, wa_s, wa_e)],
            "label": "历史样本中的窗口复现情况（非未来概率）",
        }
    if ws is not None:
        hits = sum(1 for x in xs if in_circular_window(x, ws, we))
        res["historical_recurrence_mad1"] = {
            "hits": hits,
            "n_years": n,
            "ratio": hits / n,
            "hits_years": [years[i] for i, x in enumerate(xs) if in_circular_window(x, ws, we)],
            "miss_years": [years[i] for i, x in enumerate(xs) if not in_circular_window(x, ws, we)],
        }

    # 稳定性
    res["stability"] = stability_split(xs, years)

    # 留一法
    if wa_s is not None and n >= 3:
        res["leave_one_out"] = leave_one_out(xs, years, wa_s, wa_e)

    return res


def families_from_raw(rows, mode, dedup_year=True):
    """
    mode='cycle'   → 按 (rule_id + theme_cycle_id) 聚合，跨年重复主题（Level 2）
    mode='macro'   → 按 macro_theme / rule_id 聚合（Level 3 主题族，含同机制不同 Cycle）
    mode='subtheme'→ 按 main_theme 聚合

    dedup_year=True 时执行**年度主题级聚合**（反 pseudoreplication）：
      同一年内多个 Campaign 不当作多个独立年份样本，只取当年最早有效锚点。
      ——这是研究任务 §14 明确要求的独立性与去重规则。
    """
    g = {}
    for r in rows:
        if mode == "cycle":
            k = r["theme_cycle_id"] or f'{r["rule_id"]}:{r["campaign_id"]}'
        elif mode == "macro":
            k = r["macro_theme"] or r["rule_id"]
        else:
            k = r["main_theme"] or r["rule_id"]
        g.setdefault(k, []).append(r)

    if not dedup_year:
        return g

    out = {}
    for k, v in g.items():
        by_year = {}
        for r in v:
            y = int(r["year"])
            d = int(r["anchor_doy_norm"])
            if y not in by_year or d < int(by_year[y]["anchor_doy_norm"]):
                by_year[y] = r
        out[k] = [by_year[y] for y in sorted(by_year)]
    return out


def main():
    rows = load_rows()

    report = {"period_days": PERIOD, "n_raw_objects": len(rows), "analyses": {}}

    # ---- Level 2：按 Theme Cycle 聚合（跨年重复出现的同一 Cycle）
    cycles = {}
    for r in rows:
        cycles.setdefault(r["theme_cycle_id"], []).append(r)
    report["level2_theme_cycle"] = {}
    for k, v in sorted(cycles.items()):
        yrs = {int(x["year"]) for x in v}
        report["level2_theme_cycle"][k] = {
            "n_objects": len(v),
            "n_distinct_years": len(yrs),
            "years": sorted(yrs),
            "repeat_across_years": len(yrs) >= 2,
            "campaigns": [x["campaign_id"] for x in v],
        }

    # ---- 主题族分析：macro（含同机制不同 cycle）—— 两种口径都跑
    for mode in ("macro", "subtheme"):
        for dedup in (True, False):
            tag = f"families_{mode}" + ("" if dedup else "_RAW_no_dedup")
            fams = families_from_raw(rows, mode, dedup_year=dedup)
            report[tag] = {}
            for name, v in sorted(fams.items()):
                a = analyze_family(name, v)
                report[tag][name] = a

    # ---- 样本量敏感性：对每个主题族，枚举其子集，看 N=2/3/4/5+ 时的集中度
    sens = {}
    for mode in ("macro",):
        for dedup in (True, False):
            fams = families_from_raw(rows, mode, dedup_year=dedup)
            for name, v in sorted(fams.items()):
                v = sorted(v, key=lambda r: int(r["year"]))
                n = len(v)
                if n < 2:
                    continue
                bucket = "N=2" if n == 2 else (f"N={n}" if n in (3, 4) else "N>=5")
                key = f"{bucket}{'' if dedup else ' (no-dedup)'}"
                xs = [int(r["anchor_doy_norm"]) for r in v]
                lo, hi, span = circ_min_max(xs)
                u = uniformity_test(xs, n_bootstrap=5000)
                sens.setdefault(key, []).append(
                    {
                        "family": name,
                        "n": n,
                        "years": [r["year"] for r in v],
                        "span_days": span,
                        "expected_span_uniform": u["expected_span_uniform"],
                        "span_ratio": u["span_ratio"],
                        "span_p_value": u["span_p_value_one_sided"],
                        "iqr": (quantile(xs, 0.75) - quantile(xs, 0.25)),
                        "mad": mad(xs),
                        "month_span": f"{month_of(min(xs))}-{month_of(max(xs))}",
                    }
                )
    report["sample_size_sensitivity"] = sens

    out = os.path.join(HERE, "statistics_results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    # ---------------- 控制台摘要
    print("=" * 78)
    print("LEVEL 2 — Theme Cycle 跨年重复")
    for k, v in report["level2_theme_cycle"].items():
        flag = "★跨年重复" if v["repeat_across_years"] else " 单年"
        print(f"  {flag} {k:44s} n={v['n_objects']} years={v['years']}")

    print("=" * 78)
    print("主题族（Macro，年度去重后）统计")
    for name, a in report["families_macro"].items():
        if a["n_years"] < 2:
            continue
        print(f"\n### {name}  N={a['n_years']}  years={a['years']}")
        print(f"    anchors(md): {a['md_list']}")
        print(f"    median={a['median']:.0f}({doy_to_md(a['median'])})  P25={a['p25']:.0f}({doy_to_md(a['p25'])})  P75={a['p75']:.0f}({doy_to_md(a['p75'])})")
        print(f"    IQR={a['iqr']:.0f}d  MAD={a['mad']:.1f}d  span={a['circular_span_days']}d ({a['earliest_md']}~{a['latest_md']})")
        print(f"    months={a['month_distribution']}")
        u = a["uniformity"]
        print(f"    uniformity: span={u['min_span_days']}d vs E[uniform]={u['expected_span_uniform']:.1f}d  ratio={u['span_ratio']:.3f}  p={u['span_p_value_one_sided']:.4f}")
        q = a.get("historical_recurrence_quantile")
        if q:
            print(f"    recurrence(P25-P75)={q['hits']}/{q['n_years']}  hit={q['hits_years']}  miss={q['miss_years']}")
        st = a["stability"]
        if st["status"] == "SPLIT":
            print(f"    split {st['first_half_years']}={st['first_median']:.0f} vs {st['second_half_years']}={st['second_median']:.0f} → shift={st['median_shift_days']:.0f}d  {st['drift_flag']}")
        lo = a.get("leave_one_out")
        if lo:
            print(f"    LOO: max_median_shift={lo['max_median_shift_on_removal']:.0f}d  max_hit_drop={lo['max_hit_drop_on_removal']}  single_year_dominated={lo['single_year_dominated']}")

    print("=" * 78)
    print("样本量敏感性")
    for b, items in report["sample_size_sensitivity"].items():
        print(f"\n-- {b}")
        for it in items:
            print(f"   {it['family']:34s} n={it['n']} span={it['span_days']}d E={it['expected_span_uniform']:.0f}d ratio={it['span_ratio']:.3f} p={it['span_p_value']:.3f}")


if __name__ == "__main__":
    main()
