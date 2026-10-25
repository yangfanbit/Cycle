#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_official_index_parallel_v0_1.py —— 半导体地图的官方指数**并列**行情（Wave 2.1）。

## 它做什么

对 `semiconductor_ai_compute_historical_events_v0_6.json` 的**实际事件清单**（当前 7 个，
不硬编码数量），按每个事件**规范字段** `market_performance.window` 计算官方指数的并列行情：

| 项 | 口径（统一，不随事件变） |
|---|---|
| 区间收益 | `末交易日 close / 首交易日 close − 1`（百分点） |
| 基准 | 官方 `000300` 沪深300 同窗口区间收益 |
| 超额 | `H30184 区间收益 − 000300 区间收益`（**pp**） |
| 交易日 | 只取官方序列中**实际存在**的交易日；**不插值、不补造、不缩窗口** |
| 窗口来源 | **只读** `market_performance.window`；缺失即报缺口，**不从 `window_text` 猜** |

## ★★ 授权边界（写进代码，不靠口头约定）

中证官网的接口**公开无 token**，但「可公开访问」≠「许可公开再发布派生数据」。
本轮未找到明确许可 → 默认 `state = UNCLEAR`，**不会**因为命令行开关变成「已确认」。

写入目标只有两个允许范围：

| 目标 | 授权要求 |
|---|---|
| `.tmp/`（既定本地实验目录，默认） | 无需授权 |
| `research/current/`（唯一授权生产目录） | **必须同时**给 `--i-have-license` 与**非空** `--license-basis`，缺一即拒绝 |
| 其余一切（仓库内其他受跟踪目录 / 仓库外） | **FORBIDDEN** —— 不允许「换个目录就绕过」 |

- 拒绝时退出码 **2**，且**不联网、不建目录、不生成任何文件**（闸门在任何 I/O 之前）。
- 目标路径先 `abspath` + `realpath` **解析符号链接**再判定，防止 `.tmp/x -> research/current` 这类别名。
- 生产写入时，`--license-basis` 原样记入 `license.operator_attestation.basis`，并注明
  **这是操作人员提交的依据、程序未独立核验**（`program_verified` 恒为 `false`）。

## 用法

    python research/scripts/build_official_index_parallel_v0_1.py            # 打印（不写）
    python research/scripts/build_official_index_parallel_v0_1.py --write    # 写 .tmp/（本地实验）
    python research/scripts/build_official_index_parallel_v0_1.py --write \
        --out research/current/xxx.json --i-have-license --license-basis "…"  # 仅在许可明确后
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
DEFAULT_OUT = os.path.join(REPO, ".tmp", "official_index_parallel_v0_1.json")

API = ("https://www.csindex.com.cn/csindex-home/perf/index-perf"
       "?indexCode=%s&startDate=%s&endDate=%s")
EVENTS_RE = re.compile(r"semiconductor_ai_compute_historical_events_v0_(\d+)\.json$")

INDEX = {
    "provider": "中证指数有限公司（China Securities Index Co., Ltd.）",
    "index_code": "H30184",
    "index_name": "中证全指半导体产品与设备指数",
    "identity": "OFFICIAL_EXACT",
    "identity_note": ("官方「半导体产品与设备」行业指数（设计/制造/封测/设备/材料全产业链）。"
                      "★ **不是**专门的 AI 算力指数 —— 不得把它的涨跌说成「AI 算力行情」。"),
    "published_from": "2013-07-15",
    "base_date": "2004-12-31",
    "base_value": 1000,
    "price_basis": "官方指数点位（收盘价口径；非前复权股价，无复权概念）",
    "source_url": API % ("H30184", "<startDate>", "<endDate>"),
}
BENCH = {
    "index_code": "000300",
    "index_name": "沪深300指数",
    "published_from": "2005-04-08",
    "base_date": "2004-12-31",
    "base_value": 1000,
    "source_url": API % ("000300", "<startDate>", "<endDate>"),
}

# ★ 授权状态：本轮实测结论，写进产物，避免下游误以为已获许可
#   ★★ 默认 UNCLEAR，**不得**因为命令行开关而改变 —— 开关只代表「操作人员声明」，
#      不代表「程序核验过许可」。
LICENSE_STATUS = {
    "state": "UNCLEAR",
    "checked_at": "2026-10-25",
    "finding": ("中证官网数据接口公开可访问、无需 token；但**未找到**允许「公开再发布派生行情数据」的"
                "明确许可声明。按项目边界：公开可访问 ≠ 许可再发布。"),
    "consequence": ("真实派生收益**不写入** `research/current/` 生产产物、**不在**公开页面展示；"
                    "只落 `.tmp/` 本地实验输出，供内部复核。"),
    "to_resolve": "需人工向中证指数确认授权范围（属治理决策，本轮不做）。",
}

# ─────────────────────────── 写入闸门（纯函数，不联网/不建目录/不写文件） ───────────────────────────
#
# ★★ 三条硬规则：
#   ① 只有两个允许的目标范围：`.tmp/`（既定本地实验目录）与 `research/current/`（唯一授权生产目录）；
#      仓库内**其他**受 Git 跟踪的路径一律 FORBIDDEN —— 不允许「换个目录就绕过闸门」。
#   ② 生产写入必须**同时**具备 `--i-have-license` 与**非空** `--license-basis`，缺一即拒绝。
#   ③ 目标路径先 `abspath` + `realpath` **解析符号链接**再分类，防止用 `.tmp/xxx -> research/current`
#      这类别名绕过。

REPO_ROOT = os.path.realpath(REPO)
LOCAL_EXPERIMENT_DIR = os.path.realpath(os.path.join(REPO, ".tmp"))
PRODUCTION_DIR = os.path.realpath(CURRENT)


def _is_within(path, parent):
    try:
        return os.path.commonpath([path, parent]) == parent
    except ValueError:      # 跨盘符等
        return False


def classify_target(path):
    """★ 规范化后分类：返回 `(kind, resolved)`。

    - `LOCAL_EXPERIMENT`：仅 `.tmp/` 下 —— 无需授权；
    - `PRODUCTION`：`research/current/` 下 —— 需授权；
    - `FORBIDDEN`：其余一切（仓库内其他受跟踪路径 / 仓库外路径）。
    """
    resolved = os.path.realpath(os.path.abspath(path))
    if _is_within(resolved, LOCAL_EXPERIMENT_DIR):
        return "LOCAL_EXPERIMENT", resolved
    if _is_within(resolved, PRODUCTION_DIR):
        return "PRODUCTION", resolved
    return "FORBIDDEN", resolved


def check_write_gate(path, i_have_license, license_basis):
    """★ 纯函数：返回 `(kind, resolved, problems)`；`problems` 非空 → 必须 REFUSE。

    **不联网、不创建目录、不生成文件** —— 调用方必须在任何 I/O 之前调用它。
    """
    kind, resolved = classify_target(path)
    problems = []
    if kind == "FORBIDDEN":
        problems.append("目标不在允许范围：只允许 `.tmp/`（本地实验）或 `research/current/`（授权生产）；"
                        "实际解析为 %s" % resolved)
    elif kind == "PRODUCTION":
        if not i_have_license:
            problems.append("生产写入缺 `--i-have-license`")
        if not (license_basis or "").strip():
            problems.append("生产写入缺非空 `--license-basis`（须写明授权依据与链接）")
    return kind, resolved, problems


def build_license_record(kind, license_basis):
    """★ 严格区分「操作人员提交的授权依据」与「程序独立核验的许可事实」。

    - `state` / `program_verified` **不因命令行开关而改变**（默认 UNCLEAR / false）；
    - 生产写入时把调用者提供的依据**原样**记进 `operator_attestation`，并注明程序未核验。
    """
    rec = dict(LICENSE_STATUS)
    rec["program_verified"] = False
    rec["target_kind"] = kind
    rec["operator_attestation"] = None
    if kind == "PRODUCTION":
        rec["operator_attestation"] = {
            "claimed": True,
            "basis": (license_basis or "").strip(),
            "note": ("★ 这是**操作人员提交的授权依据**；程序**未**独立核验其真伪与范围，"
                     "因此 `program_verified` 仍为 false、`state` 仍为 `UNCLEAR`。"
                     "不得据此对外声称「已获中证授权」。"),
        }
    return rec


# ─────────────────────────── 纯计算（可单测，无网络） ───────────────────────────

def compute_window(series, window):
    """★ 纯函数：只在实际存在的交易日上计算，不插值、不补造。

    series: `[(YYYY-MM-DD, close), ...]` 升序；window: `(start, end)` 或 None。
    返回 dict：成功时含 `period_return_pct`；失败时 `status` + `error`，**数值字段为 None**（不填 0）。
    """
    if not window or len(window) != 2 or not window[0] or not window[1]:
        return {"status": "NO_WINDOW", "error": "事件缺 `market_performance.window`，未从 window_text 猜测",
                "window": None, "period_return_pct": None, "trading_days": 0}
    start, end = window[0], window[1]
    rows = [(d, c) for d, c in series if start <= d <= end and c]
    if len(rows) < 2:
        return {"status": "INSUFFICIENT_TRADING_DAYS",
                "error": "窗口内交易日不足 2 个（实际 %d）→ 不计算，不插值" % len(rows),
                "window": [start, end], "period_return_pct": None, "trading_days": len(rows)}
    first, last = rows[0], rows[-1]
    return {
        "status": "COMPUTED",
        "error": None,
        "window": [start, end],
        "window_actual": {"first_trade_date": first[0], "last_trade_date": last[0],
                          "first_close": first[1], "last_close": last[1],
                          "trading_days": len(rows)},
        "period_return_pct": round((last[1] / first[1] - 1) * 100, 4),
    }


def count_rows_before(series, published_from):
    """★ 由**实际获取的完整序列**计算发布前的行数（不是手写常数）。"""
    return sum(1 for d, _ in series if d < published_from)


def window_touches_backfill(series, window, published_from):
    """★ 事件窗口级标记：窗口内**只要有一个实际交易日**早于发布日期 → True。"""
    if not window:
        return None
    return any(window[0] <= d <= window[1] and d < published_from for d, _ in series)


# ─────────────────────────── 取数 ───────────────────────────

def fetch_series(code, start="20050101", end="20261023"):
    req = urllib.request.Request(API % (code, start, end), headers={
        "User-Agent": "Mozilla/5.0 (ThreeC official-index parallel)",
        "Referer": "https://www.csindex.com.cn/",
    })
    with urllib.request.urlopen(req, timeout=40) as r:
        doc = json.loads(r.read().decode("utf-8"))
    if not doc.get("success"):
        raise SystemExit("FAIL: 中证接口返回失败：%s" % doc.get("msg"))
    out = []
    for x in doc.get("data") or []:
        d = x["tradeDate"]
        out.append(("%s-%s-%s" % (d[:4], d[4:6], d[6:]), x.get("close")))
    out.sort(key=lambda r: r[0])
    return out


def latest_events_path():
    hits = [(int(EVENTS_RE.match(f).group(1)), f) for f in os.listdir(CURRENT) if EVENTS_RE.match(f)]
    if not hits:
        raise SystemExit("FAIL: 找不到 semiconductor_ai_compute_historical_events 产物")
    return os.path.join(CURRENT, sorted(hits)[-1][1])


# ─────────────────────────── 组装 ───────────────────────────

def build(events_doc, idx_series, bench_series):
    entries = []
    for e in events_doc["events"]:
        eid = e["event_id"]
        window = (e.get("market_performance") or {}).get("window")
        idx_w = compute_window(idx_series, window)
        bmk_w = compute_window(bench_series, window)

        backfilled = window_touches_backfill(idx_series, window, INDEX["published_from"])
        ok = idx_w["status"] == "COMPUTED" and bmk_w["status"] == "COMPUTED"
        item = {
            "event_id": eid,
            "provider": INDEX["provider"],
            "index_code": INDEX["index_code"],
            "index_name": INDEX["index_name"],
            "identity": INDEX["identity"],
            "identity_note": INDEX["identity_note"],
            "published_from": INDEX["published_from"],
            "base_date": INDEX["base_date"],
            "base_value": INDEX["base_value"],
            "source_first_date": idx_series[0][0],
            "source_last_date": idx_series[-1][0],
            # ★ 由实际序列计算，非手写常数
            "rows_before_publish": count_rows_before(idx_series, INDEX["published_from"]),
            # ★ 窗口级：窗口内是否含发布前的数据点（None = 无窗口，不得当 false）
            "backfilled": backfilled,
            "window": idx_w["window"],
            "window_actual": idx_w.get("window_actual"),
            "period_return_pct": idx_w["period_return_pct"],
            "benchmark_index_code": BENCH["index_code"],
            "benchmark_index_name": BENCH["index_name"],
            "benchmark_return_pct": bmk_w["period_return_pct"],
            "excess_period_pp": (round(idx_w["period_return_pct"] - bmk_w["period_return_pct"], 4)
                                 if ok else None),
            "price_basis": INDEX["price_basis"],
            "source_url": INDEX["source_url"],
            "benchmark_source_url": BENCH["source_url"],
            "status": "COMPUTED" if ok else "INCOMPLETE",
            "error": None if ok else "；".join(
                x for x in (idx_w.get("error"), bmk_w.get("error")) if x),
            "calculation_note": (
                "区间收益 = 末交易日 close / 首交易日 close − 1；"
                "基准 = 官方 000300 同窗口区间收益；超额 = 本指数 − 基准（pp）。"
                "★ 首尾收盘口径：两端都取**窗口内实际存在的第一个/最后一个交易日**的官方收盘点位，"
                "不含窗口前一日的涨跌；窗口首末若为非交易日，自动落到最近的实际交易日，**不插值**。"
                "★ 该指数是官方**半导体产品与设备**行业指数，不是 AI 算力专用指数。"
                "★ 历史成分名单不可得，本对象**不含**任何成分信息。"),
        }
        # ★ 缺失的强制字段显式报缺口，不静默填 0 / false
        missing = [k for k in ("period_return_pct", "benchmark_return_pct", "excess_period_pp",
                               "backfilled", "rows_before_publish", "window")
                   if item.get(k) is None]
        if missing:
            item["missing_required_fields"] = missing
        entries.append(item)
    return entries


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--i-have-license", action="store_true",
                    help="仅在**已确认**可公开再发布中证派生数据时使用")
    ap.add_argument("--license-basis", default="",
                    help="授权依据与链接（**必须**与 --i-have-license 同时提供，否则拒绝生产写入）")
    a = ap.parse_args(argv)

    # ★★ 闸门必须在**任何 I/O 之前**：拒绝时不联网、不建目录、不生成文件。
    kind, resolved, problems = check_write_gate(a.out, a.i_have_license, a.license_basis)
    if problems:
        print("REFUSE: 写入闸门未通过（授权状态 = %s）→ **未联网、未建目录、未生成任何文件**"
              % LICENSE_STATUS["state"])
        for p in problems:
            print("  - %s" % p)
        print("  %s" % LICENSE_STATUS["finding"])
        print("  允许的目标：`.tmp/`（本地实验，无需授权）或 `research/current/`（需授权）。")
        print("  生产写入示例：--out research/current/<file>.json --i-have-license "
              "--license-basis \"<授权依据与链接>\"")
        return 2

    out_abs = resolved
    license_record = build_license_record(kind, a.license_basis)

    ev_path = latest_events_path()
    events_doc = json.loads(io.open(ev_path, encoding="utf-8").read())
    idx_series = fetch_series("H30184")
    bench_series = fetch_series("000300")
    entries = build(events_doc, idx_series, bench_series)

    n_ok = sum(1 for x in entries if x["status"] == "COMPUTED")
    print("事件源：%s（%d 个事件）" % (os.path.basename(ev_path), len(events_doc["events"])))
    print("官方序列：%s %s→%s（%d 行，发布前 %d 行）"
          % (INDEX["index_code"], idx_series[0][0], idx_series[-1][0], len(idx_series),
             count_rows_before(idx_series, INDEX["published_from"])))
    print("计算完成：%d / %d" % (n_ok, len(entries)))
    for x in entries:
        if x["status"] == "COMPUTED":
            print("  %-30s %s~%s 收益 %+7.2f%% 基准 %+7.2f%% 超额 %+7.2fpp backfilled=%s"
                  % (x["event_id"], x["window"][0], x["window"][1], x["period_return_pct"],
                     x["benchmark_return_pct"], x["excess_period_pp"], x["backfilled"]))
        else:
            print("  %-30s 缺口：%s" % (x["event_id"], x["error"]))

    doc = {
        "artifact": "official_index_parallel",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/build_official_index_parallel_v0_1.py",
        "index": {k: INDEX[k] for k in ("provider", "index_code", "index_name", "identity",
                                       "identity_note", "published_from", "base_date",
                                       "base_value", "price_basis")},
        "benchmark": BENCH,
        "license": license_record,
        "events_source": {"file": os.path.basename(ev_path),
                          "events": len(events_doc["events"])},
        "events": entries,
        "summary": {"events": len(entries), "computed": n_ok,
                    "gaps": [x["event_id"] for x in entries if x["status"] != "COMPUTED"],
                    "windows_with_backfill": [x["event_id"] for x in entries if x["backfilled"]],
                    "target_kind": kind,
                    "note": ("★ 本文件是**本地实验输出**，未提交到仓库；授权明确前不进入生产产物。"
                             if kind == "LOCAL_EXPERIMENT" else
                             "★ 生产写入：授权依据由**操作人员**提交（见 license.operator_attestation），"
                             "程序未独立核验，`state` 仍为 UNCLEAR。")},
    }
    body = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"

    if a.write:
        os.makedirs(os.path.dirname(out_abs), exist_ok=True)
        io.open(out_abs, "w", encoding="utf-8", newline="\n").write(body)
        print("\n已写 %s（%.1f KB）%s" % (
            os.path.relpath(out_abs, REPO), len(body.encode()) / 1024.0,
            "" if kind == "PRODUCTION" else "（本地实验输出，不入库）"))
        if kind == "PRODUCTION":
            print("★ 生产写入已执行。license.state 仍为 %s、program_verified = false；"
                  % license_record["state"])
            print("  operator_attestation.basis = %r（**操作人员提交**，程序未独立核验）"
                  % license_record["operator_attestation"]["basis"])
    else:
        print("\n（未写盘；加 --write 输出到 .tmp/）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
