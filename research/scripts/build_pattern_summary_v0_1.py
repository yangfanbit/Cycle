#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_pattern_summary_v0_1.py —— 从完整季节性产物派生**前端摘要**（v0.42）。

## 为什么需要
`DiscoveredPatterns.tsx` 原本静态 import 完整的 `pattern_discovery_v0_*.json`（~5.7MB），
但组件只用到：统计计数、覆盖信息、资格标准、限制说明、以及按中位超额排序的前 6 个窗口。
把 5.7MB 打进主包毫无收益 —— 本脚本生成一份**确定性**摘要，完整产物仍留在仓库供研究/审计。

## 确定性
- 不写入任何「当前时间」：`source.generated_at` 直接取自源产物；
- 键序固定（sort_keys）+ 固定缩进 + 尾换行；
- `source.sha256` 记录源产物指纹 → 源产物一变，摘要就必须重建（`--check` 会失败）。

## 用法
    python research/scripts/build_pattern_summary_v0_1.py            # 打印摘要规模（不写）
    python research/scripts/build_pattern_summary_v0_1.py --write    # 写文件（覆盖派生缓存）
    python research/scripts/build_pattern_summary_v0_1.py --check    # 与磁盘逐字节比对 + 校验源指纹

★ 这是**派生缓存**（类似 `market_snapshots/index.json`），不是研究产物：
  可原地重建，但必须与源产物一致；研究结论仍以完整产物为准。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"pattern_discovery_v0_(\d+)\.json$")
OUT_NAME = "pattern_discovery_summary_v0_1.json"
LEDGER_RE = re.compile(r"candidate_ledger_v0_(\d+)\.json$")
TOP_N = 6          # 与组件现有排序/切片逻辑一致：按 median_excess_pct 降序取前 6
REALIZED_N = 3     # 本月已开始窗口里再取 3 条展示「实际结果」（同样按历史中位超额，不做结果排名）

# 组件真正渲染的窗口字段（其余一律不进摘要）
WINDOW_FIELDS = (
    "pattern_id", "board", "month", "kind", "tier", "current_status",
    "n_years", "years", "median_excess_pct", "hit_rate", "best_year", "worst_year",
    "oos_tests", "oos_hit_rate", "oos_median_excess_pct", "oos_status", "oos_note",
    "oos_by_train_tier", "pit_eligible_years", "pit_first_year",
    "representative_stocks", "rep_stock_gap",
)
COVERAGE_KEYS = ("stocks", "industry_boards", "concept_baskets", "indices")


def latest_source() -> str:
    files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                   key=lambda f: int(OUT_RE.match(f).group(1)))
    if not files:
        raise SystemExit("FAIL: 找不到 pattern_discovery 产物")
    return os.path.join(CURRENT, files[-1])


def latest_ledger():
    """候选账本（可选）：存在就带上「5/10/20 日实际结果」，不存在则摘要照常生成。"""
    files = [f for f in os.listdir(CURRENT) if LEDGER_RE.match(f)]
    if not files:
        return None, None
    path = os.path.join(CURRENT, sorted(files, key=lambda f: int(LEDGER_RE.match(f).group(1)))[-1])
    return path, json.loads(io.open(path, "rb").read().decode("utf-8"))


def _outcome_of(entry):
    """只保留前端要用的字段（不含代表股票逐只明细）。"""
    hz = {}
    for h in ("5", "10", "20"):
        o = (entry.get("outcome") or {}).get(h) or {}
        hz[h] = {k: o.get(k) for k in
                 ("status", "settle_date", "board_ret", "bench_ret", "excess_pp",
                  "rep_median_excess_pp", "n_reps") if k in o}
    return {
        "outcome_type": entry.get("outcome_type"),
        "anchor": entry.get("anchor"),
        "window_note": (entry.get("window") or {}).get("note"),
        "horizons": hz,
    }


def _tracking(ledger):
    """★★ 连续追踪：**全部形成批次**的实例（不只当前窗口），形成字段来自不可变日志。

    v0_1 的账本只跟着 `current_windows` 走 → 上一批候选在新一版里直接消失，
    产品上根本无法「连续追踪」。这里按形成日志的全量实例输出，跨月滚动。
    """
    if not ledger:
        return None
    s = ledger["summary"]
    inst = []
    for c in ledger["candidates"]:
        sb = c.get("selection_basis") or {}
        hz = {}
        for h in ("5", "10", "20"):
            o = (c.get("outcome") or {}).get(h) or {}
            hz[h] = {"status": o.get("status"), "board_ret": o.get("board_ret"),
                     "excess_pp": o.get("excess_pp"), "settle_date": o.get("settle_date")}
        inst.append({
            "instance_id": c["instance_id"], "board": c["board"], "month": c["month"],
            "window_year": c["window_year"], "formed_at": c["formed_at"],
            "batch_id": c.get("batch_id"), "kind": c["kind"],
            "tier": sb.get("tier"), "n_years": sb.get("n_years"),
            "median_excess_pct": sb.get("median_excess_pct"),
            "hit_rate": sb.get("hit_rate"), "evidence_grade": sb.get("evidence_grade"),
            "anchor": c.get("anchor"), "status": c.get("status"),
            "outcome_type": c.get("outcome_type"), "horizons": hz,
        })
    inst.sort(key=lambda x: (x["batch_id"] or "", x["window_year"], x["month"], x["board"]))
    return {
        "market_as_of": ledger["market_as_of"],
        "formation_log": ledger.get("formation_log"),
        "formation_run": ledger.get("formation_run"),
        "batches": s.get("batches"),
        "settled": s.get("settled"),
        "pending": s.get("pending"),
        "by_outcome_type": s.get("by_outcome_type"),
        "instances": inst,
    }


def build(src_path: str) -> dict:
    raw = io.open(src_path, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    windows = sorted(doc["current_windows"], key=lambda p: -p["median_excess_pct"])[:TOP_N]
    ledger_path, ledger = latest_ledger()
    led_by_id = {c["candidate_id"]: c for c in (ledger or {}).get("candidates") or []}
    strict = sum(1 for p in doc["patterns"] if p["tier"] == "STRICT")
    expl = sum(1 for p in doc["patterns"] if p["tier"] == "EXPLORATORY")
    return {
        "artifact": "pattern_discovery_summary",
        "summary_version": "0.1",
        "note": ("★ 派生缓存：由完整产物确定性生成，仅供前端渲染；研究结论以源产物为准。"
                 "本文件只含统计计数、覆盖、资格标准、限制说明与排序前 6 的窗口。"),
        "source": {
            "artifact": doc.get("artifact"),
            "file": os.path.basename(src_path),
            "artifact_version": doc.get("artifact_version"),
            "protocol": doc.get("protocol"),
            "as_of": doc.get("as_of"),
            "generated_at": doc.get("generated_at"),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "as_of": doc.get("as_of"),
        "coverage_detail": {k: doc["coverage_detail"][k] for k in COVERAGE_KEYS
                            if k in doc.get("coverage_detail", {})},
        "criteria": doc.get("criteria"),
        "counts": {
            "patterns": len(doc["patterns"]),
            "strict": strict,
            "exploratory": expl,
            "current_windows": len(doc["current_windows"]),
            "top_windows": len(windows),
        },
        "pit_only_count": doc.get("pit_only_count"),
        "pit_only_summary": doc.get("pit_only_summary"),
        "tier_note": doc.get("tier_note"),
        "limitations": doc.get("limitations"),
        "ledger": ({
            "file": os.path.basename(ledger_path),
            "as_of": ledger.get("as_of"),
            "market_as_of": ledger.get("market_as_of"),
            "sha256": hashlib.sha256(io.open(ledger_path, "rb").read()).hexdigest(),
            "caliber": ledger.get("caliber"),
            "summary": {k: ledger["summary"].get(k) for k in
                        ("candidates", "by_outcome_type", "horizon_status")},
        } if ledger else None),
        # ★ 连续追踪（全量形成批次；形成字段来自不可变日志）
        "tracking": _tracking(ledger),
        "top_windows": [
            dict({k: p.get(k) for k in WINDOW_FIELDS if k in p},
                 outcome=(_outcome_of(led_by_id[p["pattern_id"]])
                          if p["pattern_id"] in led_by_id else None))
            for p in windows
        ],
        # ★ 本月已开始的窗口：**按历史中位超额**取前 N（不按结果排序，避免变成「业绩榜」）
        "realized_windows": [
            dict({k: p.get(k) for k in ("pattern_id", "board", "month", "kind", "tier",
                                        "median_excess_pct", "hit_rate", "current_status")},
                 outcome=_outcome_of(led_by_id[p["pattern_id"]]))
            for p in sorted([p for p in doc["current_windows"]
                             if p["pattern_id"] in led_by_id
                             and led_by_id[p["pattern_id"]].get("outcome_type") == "IN_WINDOW_PARTIAL"],
                            key=lambda p: -p["median_excess_pct"])[:REALIZED_N]
        ],
    }


def dump(doc: dict) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode("utf-8")


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="季节性产物 → 前端摘要（确定性派生）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)

    src = latest_source()
    blob = dump(build(src))
    out = os.path.join(CURRENT, OUT_NAME)

    if a.check:
        if not os.path.exists(out):
            print("FAIL: 摘要不存在，请先 --write：%s" % OUT_NAME); return 1
        existing = io.open(out, "rb").read()
        if existing != blob:
            print("FAIL: 摘要与源产物不一致（源已更新或摘要被手改）—— 请重跑 --write")
            return 1
        d = json.loads(blob.decode("utf-8"))
        print("PASS: 摘要与源产物一致（%s ← %s · %d 窗口摘要 · %.1f KB / 源 %.1f MB）"
              % (OUT_NAME, d["source"]["file"], d["counts"]["top_windows"],
                 len(blob) / 1024.0, d["source"]["bytes"] / 1048576.0))
        return 0

    d = json.loads(blob.decode("utf-8"))
    print("源: %s（%.2f MB, sha256 %s…）" % (d["source"]["file"], d["source"]["bytes"] / 1048576.0,
                                          d["source"]["sha256"][:12]))
    print("摘要: %.1f KB · 窗口摘要 %d 条 · 压缩比 %.0f×"
          % (len(blob) / 1024.0, d["counts"]["top_windows"],
             d["source"]["bytes"] / max(len(blob), 1)))
    if a.write:
        with open(out, "wb") as f:
            f.write(blob)
        print("已写出 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
