#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""backfill_concepts_v0_1.py —— 概念指数（自建等权）+ 板块清单补齐（v0.34.1）。

## 为什么自建概念指数

同花顺概念板块（详情码 30xxxx）**没有**可用的历史 K 线接口（`bk_300066/01/<year>.js` 全 404），
884xxx 是行业二级码、不是概念。因此概念层改用**可复现的自建等权指数**：

1. 新浪概念节点（`gn_*`）给出**当前**成分（页面已声明成分偏差）；
2. 用 `history_scan.db` 里已有的全市场个股日线，按**等权**合成概念日线
   （每日取当日有行情的成分股的收益均值，基期 1000）；
3. 落库为 `kind='concept_basket'`，并在 `note` 里写清成分来源与偏差。

★ 这不是官方概念指数：**当前成分回溯**（幸存者/成分变更偏差），只用于「结构发现」，
  不能当成「当年概念指数的真实走势」。产物与页面必须同时展示这条限制。

## 板块清单补齐

列表页会 403；改为**枚举代码**：`last.js` 里带 `name`，命中即存在。
覆盖 881101–881400（行业一级/二级）与 884001–884200（行业细分）。

用法：
    python research/scripts/backfill_concepts_v0_1.py --boards     # 枚举补齐板块
    python research/scripts/backfill_concepts_v0_1.py --concepts   # 自建概念等权指数
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import sys
import time
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
UA = {"User-Agent": "Mozilla/5.0"}
PACING = 0.12


def _get(url, referer="http://q.10jqka.com.cn", timeout=20):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={**UA, "Referer": referer}), timeout=timeout).read()


def board_probe(code):
    """返回 (name, rows) 或 None。"""
    try:
        t = _get("http://d.10jqka.com.cn/v6/line/bk_%s/01/last.js" % code).decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r'"name":"([^"]+)"', t)
    if not m:
        return None
    return json.loads('"%s"' % m.group(1))


def backfill_boards(c):
    have = {r[0] for r in c.execute("SELECT series_id FROM scan_series WHERE kind='industry_board'")}
    found = []
    for lo, hi in ((881101, 881400), (884001, 884200)):
        for code in range(lo, hi + 1):
            sid = "BK%d" % code
            if sid in have:
                continue
            name = board_probe(str(code))
            if not name:
                continue
            rows = []
            for y in range(2010, 2027):
                try:
                    t = _get("http://d.10jqka.com.cn/v6/line/bk_%s/01/%d.js" % (code, y)).decode("utf-8", "replace")
                    m = re.search(r'"data":"([^"]*)"', t)
                    if not m:
                        continue
                    for seg in m.group(1).split(";"):
                        p = seg.split(",")
                        if len(p) >= 7:
                            rows.append([p[0], float(p[1]), float(p[2]), float(p[3]), float(p[4]), float(p[5])])
                except Exception:
                    continue
                time.sleep(PACING)
            rows = sorted({r[0]: r for r in rows}.values(), key=lambda r: r[0])
            c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (sid, name, "industry_board", "ths", "bk_%s" % code, "raw",
                       rows[0][0] if rows else None, rows[-1][0] if rows else None, len(rows),
                       time.strftime("%Y-%m-%d %H:%M:%S"), "OK" if rows else "EMPTY", None))
            if rows:
                c.executemany("INSERT OR REPLACE INTO scan_daily VALUES (?,?,?,?,?,?,?)",
                              [(sid, r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows])
            c.commit()
            found.append((sid, name, len(rows)))
            if len(found) % 10 == 0:
                print("  +%d 板块（最新 %s %s）" % (len(found), name, len(rows)), flush=True)
            time.sleep(PACING)
    print("新增板块 %d 个" % len(found))


def fetch_concept_list():
    t = _get("http://money.finance.sina.com.cn/q/view/newFLJK.php?param=class",
             referer="https://finance.sina.com.cn").decode("gbk", "replace")
    out = []
    for node, _, name, cnt in re.findall(r'"(gn_[A-Za-z0-9_]+)":"(gn_[A-Za-z0-9_]+),([^,]{1,30}),(\d+)', t):
        out.append({"node": node, "name": name, "count": int(cnt)})
    return out


def fetch_members(node):
    out, page = [], 1
    while page <= 3:
        url = ("https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
               "Market_Center.getHQNodeData?page=%d&num=100&sort=symbol&asc=1&node=%s" % (page, node))
        try:
            d = json.loads(_get(url, referer="https://finance.sina.com.cn").decode("utf-8", "replace"))
        except Exception:
            break
        if not d:
            break
        out.extend(d)
        page += 1
        time.sleep(0.1)
    return out


def build_concepts(c, min_members=8, max_members=120):
    concepts = fetch_concept_list()
    print("概念节点 %d 个" % len(concepts))
    built = 0
    for cpt in concepts:
        if not (min_members <= cpt["count"] <= max_members):
            continue
        members = fetch_members(cpt["node"])
        syms = [m["symbol"] for m in members if m.get("symbol")]
        if len(syms) < min_members:
            continue
        # 等权合成：逐日按「同标的昨收→今收」的收益均值累乘
        q = ",".join("?" * len(syms))
        out = []
        series = {}
        for sid, d, close in c.execute(
                "SELECT series_id, trade_date, close FROM scan_daily WHERE series_id IN (%s) "
                "AND close>0 ORDER BY series_id, trade_date" % q, syms):
            series.setdefault(d, {})[sid] = close
        prev_map = {}
        level = 1000.0
        raw = []          # [(date, level, covered)]
        n = len(syms)
        min_need = max(3, int(0.2 * n))
        for d in sorted(series):
            cur = series[d]
            rets = [cur[s] / prev_map[s] - 1.0 for s in cur if s in prev_map and prev_map[s] > 0]
            if rets:
                level *= 1.0 + statistics.fmean(rets)
            raw.append((d, level, len(rets)))
            prev_map = cur
        # ★★ 只保留「覆盖达到下限」的交易日；早年被少量成分主导的区段**截掉**（不伪造历史）
        start_i = next((i for i, (_, _, cov_i) in enumerate(raw) if cov_i >= min_need), None)
        if start_i is None:
            out, cov = [], []
        else:
            kept = raw[start_i:]
            out = [[d, lv, lv, lv, lv, 0.0] for d, lv, _ in kept]
            cov = [c for _, _, c in kept]
        med_cov = statistics.median(cov) if cov else 0
        ok = len(out) >= 250 and med_cov >= max(min_need, 0.5 * n)
        if not ok:
            # ★ 覆盖不合格：删除旧序列并标 REJECTED（不静默留旧数据给扫描器）
            sid_bad = "CPT_" + cpt["node"].replace("gn_", "")
            c.execute("DELETE FROM scan_daily WHERE series_id=?", (sid_bad,))
            c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                      (sid_bad, cpt["name"], "concept_basket", "sina+selfbuild", cpt["node"], "raw",
                       None, None, 0, time.strftime("%Y-%m-%d %H:%M:%S"), "REJECTED",
                       "重建未达标（有效日 %d，中位覆盖 %.0f%%，需 ≥250 日且 ≥50%%）"
                       % (len(out), (med_cov / n * 100) if n else 0)))
            c.commit()
            continue
        sid = "CPT_" + cpt["node"].replace("gn_", "")
        c.execute("INSERT OR REPLACE INTO scan_series VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (sid, cpt["name"], "concept_basket", "sina+selfbuild", cpt["node"], "raw",
                   out[0][0], out[-1][0], len(out), time.strftime("%Y-%m-%d %H:%M:%S"), "OK",
                   "等权自建（当前成分 %d 只；成分偏差见 limitations）" % len(syms)))
        c.executemany("INSERT OR REPLACE INTO scan_daily VALUES (?,?,?,?,?,?,?)",
                      [(sid, r[0], r[1], r[2], r[3], r[4], r[5]) for r in out])
        c.execute("INSERT OR REPLACE INTO scan_meta VALUES (?,?)",
                  ("members:" + sid, json.dumps(syms, ensure_ascii=False)))
        c.execute("INSERT OR REPLACE INTO scan_meta VALUES (?,?)",
                  ("coverage:" + sid, json.dumps({"members": len(syms),
                                                  "avg_daily_covered": round(sum(cov) / len(cov), 1) if cov else 0,
                                                  "min_daily_covered": min(cov) if cov else 0,
                                                  "required_min_covered": min_need,
                                                  "median_covered": med_cov,
                                                  "valid_days": len(out),
                                                  "coverage_rule": "仅统计可计算收益的交易日（排除首日/停牌）",
                                                  "snapshot_at": time.strftime("%Y-%m-%d %H:%M:%S")},
                                                 ensure_ascii=False)))
        c.commit()
        built += 1
        if built % 10 == 0:
            print("  +%d 概念（%s · %d 只 · %d 行）" % (built, cpt["name"], len(syms), len(out)), flush=True)
    print("自建概念指数 %d 个" % built)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", action="store_true")
    ap.add_argument("--concepts", action="store_true")
    a = ap.parse_args(argv)
    c = sqlite3.connect(DB)
    if a.boards:
        backfill_boards(c)
    if a.concepts:
        build_concepts(c)
    for kind in ("industry_board", "concept_basket", "stock", "index"):
        n, rows = c.execute("SELECT COUNT(*), SUM(rows) FROM scan_series WHERE kind=? AND rows>0", (kind,)).fetchone()
        print("%-16s %4d 条 · %s 行" % (kind, n or 0, rows or 0))
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
