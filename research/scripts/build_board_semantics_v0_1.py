#!/usr/bin/env python3
"""build_board_semantics_v0_1.py —— 板块语义 / 可解释性登记（v0.79）。

## 为什么存在
使用者质疑「其他社会服务是什么鬼？」：`BK881179` 是同花顺行业分类的**杂项桶**，
12 年 11 月跑赢 9 次、OOS 7 次命中 0.857，统计上"最显著"，却没有单一产业对象，
也没有个股参照 → Top 6 把它排到第 1 是**统计假象**。

本脚本给所有名称含「其他 / 综合」的行业板块建**人工声明的语义表**：
 - `interpretable = false`（不进精选），但**不删除**，在页面下方单独展示；
 - 逐条写清分类口径、为什么不适合作为研究线索、来源；
 - 对能查证的板块补**外部可核描述**（不是成分名单、不是 PIT 证据），
   并把示例个股**自动校验库内存在**，让它至少"不模糊"。

## 零编造
 - 板块清单 / 名称 / 成分数全部来自库内 `scan_series` 与 `cache_v0_1.json`；
 - 当前成分名单：实测同花顺 ajax 接口 401、详情页是 JS 跳转壳 → **不可得**；
 - 历史成分名单 `ACCESS_GATED`；
 - 外部描述只用于解释分类口径，标 `EXTERNAL_DESCRIPTIVE_NOT_PIT`。

用法：--write 生成 research/current/board_semantics_v0_1.json；--check 只读复算。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(REPO, "research", "database", "history_scan.db")
CACHE = os.path.join(REPO, "research", "data", "forward_scan", "cache_v0_1.json")
OUT = os.path.join(REPO, "research", "current", "board_semantics_v0_1.json")

FUZZY_RE = re.compile(r"其他|综合")
GENERIC_NOTE = ("同花顺行业分类的兜底/杂项桶：把无法归入更细行业的公司合并成一个指数，"
                "不是单一产业，名称本身不指向可研究的产业机制。")
EXCLUDE_REASON = ("名称含「其他 / 综合」→ 属分类兜底桶，无单一产业对象；"
                  "统计显著性可能来自成分混杂，不能作为「值得关注的概念板块」推出")

# ★ 人工声明的外部可核描述（只用于解释「这个桶大概装了什么」，不是成分名单）
EXTERNAL_RESEARCH = {
    "BK881179": {
        "name": "其他社会服务",
        "classification": ("同花顺二级行业，挂在「社会服务 / 公用事业」大类下，与电力、燃气、"
                           "环境治理、环保设备、教育并列；属民生服务类的兜底细分。"),
        "observed_business_types": ["检验检测认证", "安保服务", "其他专业服务"],
        "external_source": {
            "publisher": "同花顺财经（行业周报）",
            "date": "2026-05-22",
            "url": "http://news.10jqka.com.cn/20260522/c676902739.shtml",
            "claim": "该板块指数周报列出的前五大上涨个股为实朴检测、苏试试验、安邦护卫、"
                     "联检科技、国检集团 → 指向检验检测 / 安保服务类公司",
        },
        "classification_source": {
            "publisher": "知乎（第三方分类整理，低层级资料）",
            "url": "https://zhuanlan.zhihu.com/p/1950607904064386561",
            "claim": "同花顺二级行业清单中「其他社会服务」与电力/燃气/环境治理/综合/教育并列",
        },
        "example_stocks": ["实朴检测", "苏试试验", "安邦护卫", "联检科技", "国检集团"],
        "evidence_grade": "EXTERNAL_DESCRIPTIVE_NOT_PIT",
        "note": ("★ 这些是外部周报里的**当日上涨个股示例**，不是板块成分名单，"
                 "更不是历史成分；不得用于时点判断或当作当时的候选池。"),
    },
}

KNOWN_GAPS = [
    {"id": "CURRENT_CONSTITUENTS_UNAVAILABLE",
     "detail": "同花顺板块详情页是 JS 跳转壳，成分 ajax 接口实测 HTTP 401（需 cookie / 反爬）；"
               "库内 scan_meta 只有 173 个概念篮子的成员名单，没有任何 BK_* 成员。",
     "blocks": "给出行业板块的当前成分名单"},
    {"id": "HISTORICAL_CONSTITUENTS_ACCESS_GATED",
     "detail": "官方只给逐日成分数量 + 最新快照 + 调样公告，按历史日期取名单不可得。",
     "blocks": "重建板块当年的真实候选池"},
    {"id": "BOARD_INDEX_NOT_TRADABLE",
     "detail": "BK_* 是同花顺编制指数（provider=ths、price_type=raw），不是可交易标的。",
     "blocks": "把板块指数收益直接当成个股可交易收益"},
]


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def build():
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        rows = con.execute(
            "SELECT series_id,name,first_date,last_date,rows FROM scan_series "
            "WHERE kind='industry_board' ORDER BY series_id").fetchall()
        # 示例个股必须能按名称精确校验库内存在
        stock_by_name = dict(con.execute(
            "SELECT name,series_id FROM scan_series WHERE kind='stock'").fetchall())
    finally:
        con.close()
    cache = json.load(open(CACHE, encoding="utf-8"))
    boards_cache = cache.get("boards") or {}

    entries = []
    for sid, name, first, last, nrows in rows:
        if not FUZZY_RE.search(name or ""):
            continue
        code = sid.replace("BK", "")
        n = (boards_cache.get(code) or {}).get("n")
        # ★ 零编造的「不模糊」层：从名称本身拆出父级产业方向，
        #   让 26 个没查到外部资料的板块也能看出「是哪个大类下的兜底桶」。
        m = re.match(r"^其他(.+)$", name or "")
        m2 = re.match(r"^(.+)综合$", name or "")
        m3 = re.match(r"^(.+)及其他$", name or "")
        if m:
            parent, how = m.group(1), "去掉前缀「其他」得到的父级类目"
        elif m2:
            parent, how = m2.group(1), "去掉后缀「综合」得到的父级类目"
        elif m3:
            parent, how = m3.group(1), "去掉后缀「及其他」得到的父级类目"
        else:
            parent, how = None, "名称本身即兜底词（如「综合」），无可拆的更细父级"
        e = {
            "series_id": sid, "name": name,
            "interpretable": False,
            "classification_note": GENERIC_NOTE,
            "inferred_parent_sector": {
                "parent": parent, "derivation": how,
                "grade": "NAME_DERIVED_NOT_EXTERNAL",
                "note": "由板块名称确定性拆出，只是「属于哪个大类的兜底」，"
                        "不是成分名单，也不代表该板块只有这一类公司",
            },
            "exclude_reason": EXCLUDE_REASON,
            "source": {
                "provider": "ths", "symbol": "bk_" + code,
                "classification_page": "http://q.10jqka.com.cn/thshy/detail/code/%s/" % code,
                "series_first_date": first, "series_last_date": last, "rows": nrows,
                "member_count_current_snapshot": n,
                "member_count_note": "来自 cache_v0_1.json 的当前目录条目；不是成员名单" if n else "上游目录未列该板块",
            },
            "research": None,
        }
        r = EXTERNAL_RESEARCH.get(sid)
        if r:
            checked = [{"name": nm, "series_id": stock_by_name.get(nm),
                        "in_local_db": nm in stock_by_name}
                       for nm in r["example_stocks"]]
            e["research"] = {
                "classification": r["classification"],
                "observed_business_types": r["observed_business_types"],
                "external_source": r["external_source"],
                "classification_source": r["classification_source"],
                "example_stocks_checked": checked,
                "evidence_grade": r["evidence_grade"],
                "note": r["note"],
            }
        entries.append(e)

    return {
        "artifact": "board_semantics", "artifact_version": "0.1", "generated_at": now,
        "purpose": "给名称不可解释的行业板块登记口径与排除理由；不删除、不隐藏，单独展示",
        "rule": {
            "fuzzy_name_pattern": "其他|综合",
            "top6_gate": "interpretable == true 才允许进入精选；false 的仍保留在全量区与下方待解释区",
            "not_deleted": True,
        },
        "counts": {
            "fuzzy_boards": len(entries),
            "with_external_research": sum(1 for e in entries if e["research"]),
            "example_stocks_in_db": sum(
                sum(1 for s in (e["research"] or {}).get("example_stocks_checked", [])
                    if s["in_local_db"]) for e in entries),
        },
        "known_gaps": KNOWN_GAPS,
        "limits": [
            "★ 这里只登记**名称口径与研究线索**，不是板块成分名单，也不是历史候选池。",
            "★ 外部描述来自公开事后资料，标 EXTERNAL_DESCRIPTIVE_NOT_PIT；不得用于时点判断。",
            "★ 示例个股由库内名称精确校验存在，只是「这个桶大概装了什么公司」的参照。",
            "★ 排除出 Top 6 ≠ 删除；全量区与下方专区都可查，统计数字一字不改。",
        ],
        "entries": entries,
        "source_sha256_16": {os.path.basename(CACHE): _sha(CACHE)},
    }


def check():
    if not os.path.exists(OUT):
        print("FAIL 产物不存在：%s" % OUT)
        return 1
    cur, want = json.load(open(OUT, encoding="utf-8")), build()
    def norm(o):
        o = dict(o); o.pop("generated_at", None)
        return json.dumps(o, ensure_ascii=False, sort_keys=True)
    errs = []
    if norm(cur) != norm(want):
        errs.append("board_semantics 与重新派生不一致")
    for e in cur["entries"]:
        if e["interpretable"] is not False:
            errs.append("%s 应标 interpretable=false" % e["series_id"])
        if not e["classification_note"] or not e["exclude_reason"]:
            errs.append("%s 缺口径 / 排除理由" % e["series_id"])
        p = e.get("inferred_parent_sector")
        if not p or p.get("grade") != "NAME_DERIVED_NOT_EXTERNAL" or not p.get("derivation"):
            errs.append("%s 缺从名称派生的父级类目（不模糊层）" % e["series_id"])
        for s in (e["research"] or {}).get("example_stocks_checked", []):
            if not s["in_local_db"] or not s["series_id"]:
                errs.append("%s 示例个股 %s 未通过库内校验" % (e["series_id"], s["name"]))
    if cur["counts"]["fuzzy_boards"] < 20:
        errs.append("模糊板块数量异常")
    if errs:
        for x in errs: print("  FAIL", x)
        print("--check：%d 项 FAIL" % len(errs)); return 1
    print("--check PASS · 模糊板块 %d 个 · 外部研究 %d 个 · 示例个股库内存在 %d 只"
          % (cur["counts"]["fuzzy_boards"], cur["counts"]["with_external_research"],
             cur["counts"]["example_stocks_in_db"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check: return check()
    d = build()
    if not a.write:
        print(json.dumps(d, ensure_ascii=False, indent=1)[:2200]); return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
    print("已生成 research/current/board_semantics_v0_1.json")
    return check()


if __name__ == "__main__":
    sys.exit(main())
