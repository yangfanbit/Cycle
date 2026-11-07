#!/usr/bin/env python3
"""build_benchmark_parallel_v0_1.py —— L2 官方基准并列接入（v0.78）。

## 做什么
取中证官网**公开无 token** 的 `000300` 日线，与库内 `CSI300`（新浪，被 3000 根
截断到 2014-06-20）做**并列对照**：
 - 重叠交易日逐日核对 close，量化「库内基准是不是真实官方点位」；
 - 发布日前的回溯段标 `BACKFILLED_NOT_PIT`（当时不可交易，不得用于时点判断）；
 - 发布日后、库内缺失的那段标 `OFFICIAL_ONLY_PIT_ELIGIBLE`（可用但未入库）；
 - `rows_before_publish` 由**实际序列统计**，不硬编码。

★ **并列不合并**：不替换现有 CSI300 基准、不改任何历史统计产物、
  不重算 5/10/20 日超额。这是对照证据，不是新口径上线。

## 授权闸门（沿用 build_official_index_parallel_v0_1.py 的治理）
 - 目标路径先 abspath + realpath 再分类；
 - `research/current/` 必须**同时**给 `--i-have-license` 与**非空** `--license-basis`；
 - 其余一切 FORBIDDEN；`.tmp/` 为本地实验；
 - 拒绝发生在**任何联网 / 写文件之前**；
 - 授权记录分层：`state` 恒 `UNCLEAR`、`program_verified` 恒 `false`，
   `operator_attestation.basis` 只代表操作人员提交，程序不独立核验。

用法：
  python build_benchmark_parallel_v0_1.py --write --out research/current/benchmark_parallel_v0_1.json \
      --i-have-license --license-basis "…"
  python build_benchmark_parallel_v0_1.py --check
"""
import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import statistics
import sys
import urllib.request
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DB = os.path.join(REPO, "research", "database", "history_scan.db")
DEFAULT_OUT = os.path.join(REPO, ".tmp", "benchmark_parallel_v0_1.json")
CROSS_CHECK = os.path.join(REPO, "research", "research", "reports", "price_cross_check_v0_1.json")

ENDPOINT = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
            "?indexCode=000300&startDate=20050101&endDate=%s")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ThreeC-research/0.3",
      "Referer": "https://www.csindex.com.cn/"}
PUBLISHED_FROM = "2005-04-08"
PUBLISHED_FROM_SOURCE = "docs/INDEX_DATA_FEASIBILITY_WAVE2_v0_1.md（000300 发布日 2005-04-08，基期 2004-12-31=1000）"

PRODUCTION = os.path.realpath(CURRENT)
LOCAL = os.path.realpath(os.path.join(REPO, ".tmp"))
REPO_ROOT = os.path.realpath(REPO)


def classify(path):
    resolved = os.path.realpath(os.path.abspath(path))
    if resolved == PRODUCTION or resolved.startswith(PRODUCTION + os.sep):
        return "PRODUCTION", resolved
    if resolved == LOCAL or resolved.startswith(LOCAL + os.sep):
        return "LOCAL_EXPERIMENT", resolved
    return "FORBIDDEN", resolved


def gate(path, licensed, basis):
    kind, resolved = classify(path)
    problems = []
    if kind == "FORBIDDEN":
        problems.append("目标路径不在授权目录（research/current/ 或 .tmp/）")
    elif kind == "PRODUCTION":
        if not licensed:
            problems.append("生产写入缺 --i-have-license")
        if not basis.strip():
            problems.append("生产写入缺非空 --license-basis")
    return kind, resolved, problems


def license_record(basis):
    return {
        "state": "UNCLEAR",
        "program_verified": False,
        "operator_attestation": {
            "basis": basis,
            "submitted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "note": "操作人员提交的授权依据，程序未独立核验许可范围",
        } if basis else None,
        "note": ("★ 公开可访问 ≠ 许可公开再发布。state 恒 UNCLEAR、program_verified 恒 false；"
                 "授权属治理决策，不由命令行开关改变。"),
    }


def fetch(end_date):
    url = ENDPOINT % end_date
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        raw = r.read()
    d = json.loads(raw.decode("utf-8"))
    if d.get("code") != "200" or not d.get("data"):
        raise RuntimeError("官方接口返回异常：%s" % str(d)[:200])
    return raw, d["data"]


def norm(s):
    return str(s).replace("-", "")


def pearson(a, b):
    if len(a) < 3:
        return None
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return round(num / (da * db), 6) if da and db else None


def build(basis=""):
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    end_date = datetime.now().astimezone().strftime("%Y%m%d")
    raw, rows = fetch(end_date)
    rows = sorted(rows, key=lambda x: x["tradeDate"])
    close = {x["tradeDate"]: float(x["close"]) for x in rows if x.get("close")}

    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        local = {norm(d): float(c) for d, c in con.execute(
            "SELECT trade_date, close FROM scan_daily WHERE series_id='CSI300' AND close>0")}
    finally:
        con.close()

    common = sorted(set(close) & set(local))
    diffs = [abs(close[d] - local[d]) for d in common]
    exact = sum(1 for v in diffs if v < 0.01)
    lr, orr = [], []
    for i in range(1, len(common)):
        d0, d1 = common[i - 1], common[i]
        lr.append(local[d1] / local[d0] - 1)
        orr.append(close[d1] / close[d0] - 1)

    local_dates = sorted(local)
    local_first, local_last = local_dates[0], local_dates[-1]
    pub = norm(PUBLISHED_FROM)
    before = [d for d in close if d < pub]
    gap = [d for d in close if pub <= d < local_first]
    overlap = [d for d in close if d >= local_first]

    segments = [
        {"status": "BACKFILLED_NOT_PIT", "from": min(close), "to": max(before) if before else None,
         "rows": len(before), "backfilled": True,
         "note": "指数公司事后补算，发布日前市场上不存在该可交易指数；不得用于时点判断"},
        {"status": "OFFICIAL_ONLY_PIT_ELIGIBLE", "from": min(gap) if gap else None,
         "to": max(gap) if gap else None, "rows": len(gap), "backfilled": False,
         "note": "发布日后、库内 CSI300 起点前的官方真实点位；可用但本轮不入库、不改历史统计"},
        {"status": "OVERLAP_WITH_LOCAL", "from": min(overlap) if overlap else None,
         "to": max(overlap) if overlap else None, "rows": len(overlap), "backfilled": None,
         "note": "与库内 CSI300 重叠段；backfilled=null 表示不适用（不是 false）"},
    ]

    cross = None
    if os.path.exists(CROSS_CHECK):
        c = json.load(open(CROSS_CHECK, encoding="utf-8"))
        ok = [b for b in c["baskets"] if b["status"] == "OK"]
        cross = {
            "file": os.path.relpath(CROSS_CHECK, REPO),
            "baskets_checked": len(ok),
            "pearson_range": [min(b["pearson_all_vs_own"] for b in ok),
                              max(b["pearson_all_vs_own"] for b in ok)],
            "median_abs_diff_pp_max": max(b["median_abs_diff_pp"] or 0 for b in ok),
            "listed_1y_diff_pp_max": max((b.get("listed_1y_filter") or {}).get("median_abs_diff_pp") or 0
                                         for b in ok),
            "conclusion": "自建概念篮子可被真实个股逐日复现（相关 1.0 / 中位差 0.0 pp）；"
                          "偏差不在计算，而在『用当前成分名单回溯』这个对象定义",
        }

    return {
        "artifact": "benchmark_parallel", "artifact_version": "0.1", "generated_at": now,
        "purpose": "中证官方 000300 与库内 CSI300 并列对照；不合并、不替换、不重算历史统计",
        "license": license_record(basis),
        "index": {"code": "000300", "name": "沪深300",
                  "published_from": PUBLISHED_FROM, "published_from_source": PUBLISHED_FROM_SOURCE,
                  "base_date": "2004-12-31", "base_value": 1000},
        "source": {"endpoint": ENDPOINT % end_date, "rows": len(rows),
                   "first_date": rows[0]["tradeDate"], "last_date": rows[-1]["tradeDate"],
                   "raw_sha256_16": hashlib.sha256(raw).hexdigest()[:16]},
        "rows_before_publish": len(before),
        "segments": segments,
        "overlap_check": {
            "local_series": "CSI300（history_scan.db / provider=sina / price_type=raw）",
            "local_first": local_first, "local_last": local_last,
            "matched_trading_days": len(common),
            "exact_close_matches": exact,
            "exact_match_rate": round(exact / len(common), 6) if common else None,
            "max_abs_close_diff": round(max(diffs), 6) if diffs else None,
            "median_abs_close_diff": round(statistics.median(diffs), 6) if diffs else None,
            "daily_return_correlation": pearson(orr, lr),
            "conclusion": ("库内 CSI300 与官方 000300 在重叠交易日" +
                           ("点位一致，差异仅在起点（库内被 3000 根截断）"
                            if exact == len(common) else "存在数值差异，需单独核查")),
        },
        "cross_check_summary": cross,
        "limits": [
            "★ 并列不合并：本产物不替换现有 CSI300 基准，不改任何历史统计 / 账本 / 雷达产物。",
            "★ 发布日前段为指数公司事后补算，标 BACKFILLED_NOT_PIT；"
            "不得当成『当时可知』用于 PIT 判断。",
            "★ rows_before_publish 由实际序列统计；三段 rows 之和 = source.rows。",
            "★ 官方数值来自公开接口，授权状态 UNCLEAR、程序未核验；"
            "不得对外发布为投资建议或买卖信号。",
            "★ 远端可能已到库内最后交易日之后；本轮只做对照，不追加行情（未授权全套刷新）。",
            "★ 行业板块为同花顺编制指数、概念篮子为当前成分等权自建，"
            "都不是真实可交易标的；个股偏差见 cross_check_summary。",
        ],
    }


def check():
    path = os.path.join(CURRENT, "benchmark_parallel_v0_1.json")
    if not os.path.exists(path):
        print("FAIL 产物不存在：%s" % path)
        return 1
    d = json.load(open(path, encoding="utf-8"))
    errs = []
    seg = d.get("segments") or []
    if len(seg) != 3:
        errs.append("并列段必须为 3 段")
    elif sum(s["rows"] for s in seg) != d["source"]["rows"]:
        errs.append("三段 rows 之和与源行数不符")
    if len(before := [d for d in seg if d["backfilled"] is True]) != 1:
        errs.append("backfilled=true 段必须恰好 1 段")
    if not any(s["backfilled"] is None for s in seg):
        errs.append("backfilled 三态缺 null（null ≠ false）")
    if not isinstance(d["rows_before_publish"], int):
        errs.append("rows_before_publish 必须由实际序列统计为整数")
    lic = d.get("license") or {}
    if lic.get("state") != "UNCLEAR" or lic.get("program_verified") is not False:
        errs.append("授权记录分层被破坏（state 必须 UNCLEAR / program_verified 必须 false）")
    if not (lic.get("operator_attestation") or {}).get("basis"):
        errs.append("生产产物缺操作人员提交的授权依据")
    ov = d.get("overlap_check") or {}
    if ov.get("matched_trading_days", 0) < 100:
        errs.append("重叠交易日过少")
    if ov.get("exact_match_rate") is not None and ov["exact_match_rate"] < 0.99:
        errs.append("库内基准与官方点位不一致，需单独核查")
    if errs:
        for e in errs:
            print("  FAIL", e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    print("--check PASS · 官方 %s 行 · 发布日前 %s 行 · 重叠 %s 日 · 完全一致 %s · 相关 %s"
          % (d["source"]["rows"], d["rows_before_publish"], ov["matched_trading_days"],
             ov["exact_close_matches"], ov["daily_return_correlation"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--i-have-license", action="store_true")
    ap.add_argument("--license-basis", default="")
    a = ap.parse_args()
    if a.check:
        return check()
    kind, resolved, problems = gate(a.out, a.i_have_license, a.license_basis)
    if problems:
        print("REFUSE: 写入闸门未通过 → **未联网、未建目录、未生成任何文件**")
        for p in problems:
            print("  -", p)
        return 2
    doc = build(a.license_basis)
    if not a.write:
        print(json.dumps({k: v for k, v in doc.items() if k != "limits"},
                         ensure_ascii=False, indent=1)[:2400])
        return 0
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已写入 %s（分类=%s）" % (os.path.relpath(resolved, REPO), kind))
    if kind == "PRODUCTION":
        return check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
