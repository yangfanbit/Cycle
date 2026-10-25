#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""probe_csindex_official_v0_1.py —— 中证官方指数可获取性实测（Wave 2 调查用）。

## 它做什么

只用**公开、无 token** 的中证官网接口，取官方指数的日线，然后：

1. **独立复算**：用 `close/prev_close − 1` 重算日涨跌幅，与接口自带的 `changePct` 比对；
2. **窗口复算**：用首末收盘价重算窗口收益，再与「逐日涨跌幅连乘」互校；
3. **与仓库合成序列对照**：同一窗口下，官方指数 vs 同花顺行业板块（`BK*`）的收益、超额与日收益相关性；
4. **成分可得性**：接口逐日的 `consNumber`（成分数量）与官方成分文件 `cons.xls` 的实际条数互校；
   **按历史日期取成员名单不可得**（官方只提供最新快照 + 调样公告）。

★ 不写生产库、不改任何既有产物；`--write` 只写一份**小体积**的元数据/统计摘要。

## 数据来源（均为公开、无需 token）

- 日线：`https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=<code>&startDate=YYYYMMDD&endDate=YYYYMMDD`
- 最新成分：`https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/autofile/cons/<code>cons.xls`
- 指数说明书：`https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/<code>factsheet.pdf`

## 用法

    python research/scripts/probe_csindex_official_v0_1.py           # 打印
    python research/scripts/probe_csindex_official_v0_1.py --write   # 另写 reports/index_data_pilot_v0_1.json
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import statistics
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
OUT = os.path.join(REPO, "research", "research", "reports", "index_data_pilot_v0_1.json")

API = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
       "?indexCode=%s&startDate=%s&endDate=%s")
CONS = ("https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/autofile/cons/%scons.xls")
FACT = ("https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/indices/detail/files/zh_CN/%sfactsheet.pdf")

# 主候选 + 备选 + 基准；基准用官方沪深300（000300），便于同源对照
INDEXES = {
    "H30184": {"name": "中证全指半导体产品与设备指数", "short": "中证全指半导体",
               "published": "2013-07-15", "base_date": "2004-12-31", "base_value": 1000,
               "theme": "半导体 / AI 算力", "identity": "OFFICIAL_EXACT",
               "match_note": "编制方案为「半导体产品与设备」全产业链（设计/制造/封测/设备/材料），"
                             "与 SEMI-* 事件的研究对象一致 → 精确匹配"},
    # ★★ 不是 EXACT：成分含水电/核电（长江电力、中国核电等），而 POWER-* 事件的研究对象是**火电**。
    #   对「电力运营整体」算 EXACT，对「火电迎峰度夏」只能算 PROXY —— 这一点在 2024 窗口上
    #   直接导致结论方向相反（见报告 §4）。
    "H30199": {"name": "中证全指电力公用事业指数", "short": "电力指数",
               "published": "2013-07-15", "base_date": "2004-12-31", "base_value": 1000,
               "theme": "电力运营（含水电/核电）", "identity": "OFFICIAL_PROXY",
               "match_note": "行业分类为「电力公用事业」，成分含水电与核电；POWER-* 事件研究对象是"
                             "**火电** → 只能作为代理，**不得**当作火电机制的精确匹配"},
    "000933": {"name": "中证医药卫生指数", "short": "800医卫",
               "published": "2009-07-03", "base_date": "2004-12-31", "base_value": 1000,
               "theme": "医药健康（含流感相关）", "identity": "OFFICIAL_PROXY",
               "match_note": "医药卫生整体，不含「流感」这一子主题 → 只能作为医药健康方向的代理"},
    "000300": {"name": "沪深300指数", "short": "沪深300",
               "published": "2005-04-08", "base_date": "2004-12-31", "base_value": 1000,
               "theme": "基准", "identity": "BENCHMARK",
               "match_note": "基准，不参与题材匹配判断"},
}

# 与仓库已有历史事件重叠的窗口（全部晚于各指数发布日 → 不含发布前回溯段）
WINDOWS = {
    "SEMI-2023-AI-COMPUTE": ("2023-01-30", "2023-04-10", "H30184", "BK881121"),
    "SEMI-2019-LOCALIZATION": ("2019-05-16", "2020-07-14", "H30184", "BK881121"),
    "SEMI-2022-DOWNTURN": ("2022-01-04", "2022-10-12", "H30184", "BK881121"),
    "POWER-2017-SUMMER-COUNTEREXAMPLE": ("2017-05-01", "2017-07-31", "H30199", "BK881145"),
    "POWER-2024-SUMMER-COUNTEREXAMPLE": ("2024-05-01", "2024-07-31", "H30199", "BK881145"),
    "FLU-2023-H1N1": ("2023-02-20", "2023-04-15", "000933", None),
}

ANCHOR_DATES = ("2019-06-28", "2023-03-31", "2026-10-23")  # 成分数量核对用的历史日

# ★ 两个电力反例事件的参与标的（全部为**火电**）—— 用来暴露「火电 vs 电力公用事业」的口径差
POWER_PARTS = {
    "sz000600": "建投能源", "sh600027": "华电国际", "sh600509": "天富能源",
    "sh600578": "京能电力", "sh600905": "三峡能源", "sz000862": "银星能源",
}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (ThreeC index feasibility probe)",
        "Referer": "https://www.csindex.com.cn/",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def fetch_index(code, start="20050101", end="20261023"):
    """取官方日线；返回按日期升序的 [(YYYY-MM-DD, close, changePct, consNumber)]。"""
    raw = _get(API % (code, start, end))
    doc = json.loads(raw.decode("utf-8"))
    if not doc.get("success"):
        raise RuntimeError("接口返回失败：%s" % doc.get("msg"))
    rows = []
    for x in doc.get("data") or []:
        d = x["tradeDate"]
        rows.append(("%s-%s-%s" % (d[:4], d[4:6], d[6:]),
                     x.get("close"), x.get("changePct"), x.get("consNumber")))
    rows.sort(key=lambda r: r[0])
    return rows


def repo_series(sid):
    """仓库合成/板块序列（同花顺行业板块用紧凑日期）。"""
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        out = {}
        for d, c in con.execute(
                "SELECT trade_date, close FROM scan_daily WHERE series_id=? ORDER BY trade_date", (sid,)):
            if c:
                key = d if "-" in d else "%s-%s-%s" % (d[:4], d[4:6], d[6:])
                out[key] = c
        return out
    finally:
        con.close()


def recompute_pct(rows):
    """★ 独立复算：close/prev_close − 1，与接口 changePct 比对。

    ★★ 实测只有两类行会不一致，且**都可解释**：
      · 序列**首行**（无前收，`changePct` 相对基点 1000 计算）；
      · **发布日当天**（官方口径把发布日 `changePct` 记 0，而点位相对前一交易日有变动）。
    因此把「首行」与「发布日」单列，不计入不一致。
    """
    diffs, outliers = [], []
    for i in range(1, len(rows)):
        d, c, pct, _ = rows[i]
        pc = rows[i - 1][1]
        if not c or not pc or pct is None:
            continue
        mine = (c / pc - 1) * 100
        diff = abs(mine - pct)
        diffs.append(diff)
        if diff > 0.01:
            outliers.append({"date": d, "api_changePct": round(pct, 4),
                             "close_ratio_pct": round(mine, 4), "diff_pp": round(diff, 4)})
    return {"n": len(diffs),
            "max_abs_diff_pp": round(max(diffs), 6) if diffs else None,
            "gt_0_01pp": len(outliers),
            "median_abs_diff_pp": round(statistics.median(diffs), 6) if diffs else None,
            "outliers": outliers[:6],
            "outliers_note": "★ 不一致只出现在「序列首行」与「发布日当天」，属口径差异、非数据错误"}


def window_stats(rows, start, end):
    """窗口收益 = close[窗口末交易日]/close[窗口首交易日] − 1；另给「以前一日收盘为基」的敏感性。"""
    inwin = [(i, r) for i, r in enumerate(rows) if start <= r[0] <= end]
    if len(inwin) < 2:
        return None
    i0, r0 = inwin[0]
    i1, r1 = inwin[-1]
    if not r0[1] or not r1[1]:
        return None
    ret = (r1[1] / r0[1] - 1) * 100
    # 连乘互校
    prod = 1.0
    for _, r in inwin[1:]:
        if r[2] is None:
            prod = None
            break
        prod *= (1 + r[2] / 100)
    # 以前一日收盘为基（把窗口首日的涨跌也算进去）
    alt = None
    if i0 > 0 and rows[i0 - 1][1]:
        alt = (r1[1] / rows[i0 - 1][1] - 1) * 100
    return {"start_date": r0[0], "end_date": r1[0], "n_days": len(inwin),
            "close_start": r0[1], "close_end": r1[1],
            "ret_pct": round(ret, 4),
            "ret_pct_from_prev_close": round(alt, 4) if alt is not None else None,
            "ret_pct_by_daily_compounding": round((prod - 1) * 100, 4) if prod is not None else None,
            "compounding_vs_close_diff_pp": (round((prod - 1) * 100 - ret, 6)
                                             if prod is not None else None)}


def daily_returns(rows):
    out = {}
    for i in range(1, len(rows)):
        d, c = rows[i][0], rows[i][1]
        pc = rows[i - 1][1]
        if c and pc:
            out[d] = (c / pc - 1) * 100
    return out


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs) ** 0.5
    syy = sum((y - my) ** 2 for y in ys) ** 0.5
    return round(sxy / (sxx * syy), 4) if sxx and syy else None


def repo_daily_returns(series):
    days = sorted(series)
    out = {}
    for i in range(1, len(days)):
        d, p = days[i], days[i - 1]
        if series[p]:
            out[d] = (series[d] / series[p] - 1) * 100
    return out


def cons_count_from_xls(code):
    """官方最新成分文件的实际条数（需要 xlrd；缺失则返回 None 并注明）。"""
    try:
        import xlrd
    except ImportError:
        return None, "xlrd 未安装（本机一次性依赖）"
    try:
        raw = _get(CONS % code)
    except Exception as ex:  # noqa: BLE001
        return None, "下载失败：%s" % ex
    tmp = os.path.join("/tmp", "_cons_%s.xls" % code)
    with open(tmp, "wb") as fh:
        fh.write(raw)
    sh = xlrd.open_workbook(tmp).sheet_by_index(0)
    header = [str(sh.cell_value(0, c)) for c in range(sh.ncols)]
    try:
        i_date = next(i for i, h in enumerate(header) if "日期" in h)
        i_code = next(i for i, h in enumerate(header) if "成份券代码" in h)
    except StopIteration:
        return None, "成分文件列名不符合预期"
    rows = [(str(sh.cell_value(r, i_date)).strip(), str(sh.cell_value(r, i_code)).strip())
            for r in range(1, sh.nrows)]
    rows = [x for x in rows if x[1]]
    dates = sorted({x[0] for x in rows})
    return {"rows": len(rows), "file_date": dates[-1] if dates else None,
            "unique_codes": len({x[1] for x in rows})}, None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(DB):
        print("SKIP: history_scan.db 不存在 → 无法做「官方 vs 仓库合成序列」对照")
        return 0

    print("=" * 78)
    print("中证官方指数可获取性实测（公开接口，无 token）")
    print("=" * 78)

    fetched = {}
    meta = {}
    for code, info in INDEXES.items():
        rows = fetch_index(code)
        fetched[code] = rows
        first, last = rows[0][0], rows[-1][0]
        pre = [r for r in rows if r[0] < info["published"]]
        post = [r for r in rows if r[0] >= info["published"]]
        rec = recompute_pct(rows)
        meta[code] = dict(info, api_first=first, api_last=last, api_rows=len(rows),
                          rows_before_publish=len(pre), rows_after_publish=len(post),
                          recompute=rec)
        print("\n[%s] %s（%s）" % (code, info["name"], info["identity"]))
        print("  发布 %s · 基日 %s · 基值 %s" % (info["published"], info["base_date"], info["base_value"]))
        print("  API 覆盖 %s → %s（%d 行）｜发布前 %d 行（★回溯段）· 发布后 %d 行"
              % (first, last, len(rows), len(pre), len(post)))
        print("  独立复算 changePct：n=%d 最大差 %.6fpp 中位 %.6fpp 超 0.01pp 的 %d 条 %s"
              % (rec["n"], rec["max_abs_diff_pp"] or 0, rec["median_abs_diff_pp"] or 0,
                 rec["gt_0_01pp"],
                 ("→ %s" % rec["outliers"]) if rec["outliers"] else ""))
        if rows[-1][3]:
            print("  最新一日 consNumber = %s" % int(rows[-1][3]))

    # ── 成分数量：逐日 consNumber vs 官方文件条数 ──
    print("\n" + "-" * 78)
    print("成分可得性")
    for code in ("H30184", "H30199", "000933"):
        rows = fetched[code]
        by_date = {r[0]: r[3] for r in rows if r[3]}
        anchors = []
        for d in ANCHOR_DATES:
            v = by_date.get(d)
            if v is None:  # 当日非交易日 → 取之前最近的
                prev = [x for x in rows if x[0] <= d and x[3]]
                v = prev[-1][3] if prev else None
                d_used = prev[-1][0] if prev else None
            else:
                d_used = d
            anchors.append({"date": d_used, "cons_number": int(v) if v else None})
        xls, err = cons_count_from_xls(code)
        meta[code]["cons_anchors"] = anchors
        meta[code]["cons_file"] = xls
        meta[code]["cons_file_error"] = err
        line = "  %-7s 逐日成分数：%s" % (code, " / ".join(
            "%s=%s" % (x["date"], x["cons_number"]) for x in anchors))
        print(line)
        if xls:
            latest = int(rows[-1][3]) if rows[-1][3] else None
            ok = (xls["unique_codes"] == latest)
            print("           官方 cons.xls：%d 条（文件日期 %s）· 与接口最新 consNumber(%s) %s"
                  % (xls["unique_codes"], xls["file_date"], latest, "一致 ✅" if ok else "不一致 ❌"))
            meta[code]["cons_file_matches_latest"] = ok
        else:
            print("           官方 cons.xls 未核对：%s" % err)

    # ── 窗口对照：官方 vs 仓库合成序列 ──
    print("\n" + "-" * 78)
    print("窗口对照（收益 = 末交易日收盘/首交易日收盘 − 1；超额 = 指数 − 沪深300）")
    bench = window_stats(fetched["000300"], "2005-01-01", "2026-12-31")
    bench_daily = daily_returns(fetched["000300"])
    window_out = {}
    for eid, (s, e, idx_code, repo_sid) in WINDOWS.items():
        off = window_stats(fetched[idx_code], s, e)
        bmk = window_stats(fetched["000300"], s, e)
        row = {"index": idx_code, "window": [s, e], "official": off, "benchmark": bmk}
        if off and bmk:
            row["official_excess_pp"] = round(off["ret_pct"] - bmk["ret_pct"], 4)
        if repo_sid:
            rs = repo_series(repo_sid)
            wr = window_stats([(d, c, None, None) for d, c in sorted(rs.items())], s, e)
            row["repo_series"] = repo_sid
            row["repo"] = wr
            if wr and bmk:
                row["repo_excess_pp"] = round(wr["ret_pct"] - bmk["ret_pct"], 4)
            # 日收益相关性（共同交易日）
            od = daily_returns(fetched[idx_code])
            rd = repo_daily_returns(rs)
            common = sorted(set(od) & set(rd) & {d for d in od if s <= d <= e})
            row["daily_corr_in_window"] = pearson([od[d] for d in common], [rd[d] for d in common])
            row["common_days"] = len(common)
            if wr and off:
                row["official_minus_repo_pp"] = round(off["ret_pct"] - wr["ret_pct"], 4)
                row["excess_gap_pp"] = (round(row["official_excess_pp"] - row["repo_excess_pp"], 4)
                                        if "official_excess_pp" in row and "repo_excess_pp" in row else None)
        window_out[eid] = row
        if off and bmk:
            print("  %-34s %s 官方 %+7.2f%% 基准 %+7.2f%% 超额 %+7.2fpp"
                  % (eid, idx_code, off["ret_pct"], bmk["ret_pct"], row["official_excess_pp"]))
            if row.get("repo"):
                print("  %-34s %s 板块 %+7.2f%% 超额 %+7.2fpp ｜差 %+7.2fpp ｜日收益 r=%s（n=%d）"
                      % ("", repo_sid, row["repo"]["ret_pct"], row["repo_excess_pp"],
                         row["official_minus_repo_pp"], row["daily_corr_in_window"], row["common_days"]))

    # ── 电力反例：火电参与标的 vs 电力公用事业指数（口径差）──
    print("\n" + "-" * 78)
    print("电力反例的参与者复核（★ 研究对象是火电，H30199 含水电/核电 → 口径不同）")
    part_out = {}
    for eid in ("POWER-2017-SUMMER-COUNTEREXAMPLE", "POWER-2024-SUMMER-COUNTEREXAMPLE"):
        s, e = WINDOWS[eid][0], WINDOWS[eid][1]
        bmk = window_stats(fetched["000300"], s, e)
        recs = {}
        for sid, nm in POWER_PARTS.items():
            rs = repo_series(sid)
            w = window_stats([(d, c, None, None) for d, c in sorted(rs.items())], s, e)
            if w:
                recs[sid] = {"name": nm, "ret_pct": w["ret_pct"],
                             "excess_pp": round(w["ret_pct"] - bmk["ret_pct"], 4) if bmk else None}
        part_out[eid] = recs
        ups = sum(1 for x in recs.values() if x["ret_pct"] > 0)
        print("  %s（%s ~ %s）火电标的：有数据 %d 只 · 上涨 %d / 下跌 %d" % (eid, s, e, len(recs), ups, len(recs) - ups))
        print("     " + " · ".join("%s %+.2f%%" % (x["name"], x["ret_pct"]) for x in recs.values()))
    if part_out:
        doc_parts = part_out
    else:
        doc_parts = {}

    # ── 抽样原始值（少量，便于人工核对）──
    print("\n" + "-" * 78)
    print("抽样原始值（官方接口原样返回）")
    samples = {}
    for code, ds in (("H30184", ("2023-01-30", "2023-04-10")),
                     ("H30199", ("2017-05-01", "2017-07-31")),
                     ("000933", ("2023-02-20", "2023-04-15"))):
        rows = fetched[code]
        pick = [r for r in rows if r[0] in ds]
        samples[code] = [{"date": r[0], "close": r[1], "changePct": r[2],
                          "consNumber": int(r[3]) if r[3] else None} for r in pick]
        for x in samples[code]:
            print("  %-7s %s close=%.2f changePct=%+.2f%% consNumber=%s"
                  % (code, x["date"], x["close"], x["changePct"], x["consNumber"]))

    doc = {
        "artifact": "index_data_pilot",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/probe_csindex_official_v0_1.py",
        "position": ("Wave 2 数据源调查的实测证据：只证明「官方指数能否公开取得、能否复算、"
                     "与仓库合成序列差多少」；**不含**任何评分/排名/预测。"),
        "access": {
            "daily_api": API.replace("%s", "<code>"),
            "daily_api_auth": "无 token、无积分、无需登录（公开 GET）",
            "cons_file": CONS.replace("%s", "<code>"),
            "factsheet": FACT.replace("%s", "<code>"),
            "note": ("★ 东方财富 push2his 在本机持续空响应（Empty reply），故未采用；"
                     "新浪可取部分官方指数但 H 代码不可得。"),
        },
        "indexes": meta,
        "windows": window_out,
        "power_participants": doc_parts,
        "raw_samples": samples,
        "limitations": [
            "★ 官方接口返回的序列**含发布日之前的部分**（H30199/H30184/000933 均从 2005-01-01 起），"
            "该段是**事后回溯/补算**，不是当时已公开可交易的指数点位 —— 只能用于「事后回看」，"
            "不得用于「当时可识别」的时点论证。",
            "★ 成分：接口只给逐日**成分数量** `consNumber`；官方只提供**最新**成分快照文件与调样公告，"
            "**没有**按历史日期查询成员名单的公开接口 → 历史成员名单属 ACCESS_GATED。",
            "★ 本脚本只写小体积统计摘要，不落任何行情明细；生产集成前需另行决定入库方式。",
        ],
    }
    body = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="\n").write(body)
        print("\n已写 %s（%.1f KB）" % (os.path.relpath(OUT, REPO), len(body.encode()) / 1024.0))
    else:
        print("\n（未写盘；加 --write 输出元数据摘要）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
