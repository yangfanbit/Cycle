#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""monthly_candidate_ledger.py —— **季节性候选追踪的月度刷新入口**（v0.51）。

## 与 `monthly_refresh.py` 的分工（别混）

| 脚本 | 管什么 |
|---|---|
| `monthly_refresh.py` | `current_candidates.json`（研究候选数据集）的契约校验 / diff / 归档 |
| **本脚本** | **季节性候选账本**（`candidate_formation_log_v0_1` + `candidate_ledger_v0_2`）的滚动刷新 |

两者互不替代：前者管「研究候选」，后者管「按季节结构形成的可追踪实例」。

## ★ 它做什么

```
① 前置检查   行情库是否存在 / 账本与形成日志是否可读
② 推进判定   DB 最后交易日 vs 账本 market_as_of → 决定「有没有新东西要结算」
③ 上游判定   pattern_discovery.as_of vs DB 最后交易日 → 决定「能不能形成新批次」
④ 结算+形成  build_candidate_ledger_v0_2.py --write
⑤ 派生摘要   build_pattern_summary_v0_1.py --write（产品数据）
⑥ 双校验     两个 --check（形成稳定性 + 结算一致性 + 摘要一致）
⑦ 报告       research/research/reports/candidate_ledger_refresh_<market_as_of>.json
```

## ★★ 三条纪律

1. **本脚本不生成研究结论**：只搬运既有产物，不改任何 `selection_basis`。
2. **上游没刷新就不形成新批次**：`pattern_discovery.as_of ≠ 行情最后交易日` 时只结算、不形成，
   并显式说明原因（`--with-discovery` 才转发上游重跑）。
3. **冻结快照不可覆盖**：由 `build_candidate_ledger_v0_2.py` 的 `_write_guard` 强制；本脚本失败即停。

## 用法

    python research/scripts/monthly_candidate_ledger.py              # 只看会做什么（不写）
    python research/scripts/monthly_candidate_ledger.py --write      # 执行
    python research/scripts/monthly_candidate_ledger.py --write --with-discovery   # 先重跑上游发现
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
REP = os.path.join(REPO, "research", "research", "reports")
DB = os.path.join(REPO, "research", "database", "history_scan.db")
LEDGER = os.path.join(CURRENT, "candidate_ledger_v0_2.json")
LOG = os.path.join(CURRENT, "candidate_formation_log_v0_1.json")
PY = sys.executable
LEDGER_PY = os.path.join("research", "scripts", "build_candidate_ledger_v0_2.py")
SUMMARY_PY = os.path.join("research", "scripts", "build_pattern_summary_v0_1.py")
DISCOVER_PY = os.path.join("research", "scripts", "discover_seasonal_patterns_v0_5.py")


def run(args):
    p = subprocess.run([PY] + args, cwd=REPO, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def read(path):
    return json.load(io.open(path, encoding="utf-8"))


def latest(pattern_prefix):
    """★ 必须按**数字**排序：字符串排序会把 v0_10 排到 v0_9 前面（已踩）。"""
    import re
    rx = re.compile(re.escape(pattern_prefix) + r"(\d+)\.json$")
    hits = [(int(rx.match(f).group(1)), f) for f in os.listdir(CURRENT) if rx.match(f)]
    return os.path.join(CURRENT, sorted(hits)[-1][1]) if hits else None


def db_last_day():
    import sqlite3
    con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    try:
        r = con.execute("SELECT MAX(trade_date) FROM scan_daily WHERE series_id='CSI300'").fetchone()
    finally:
        con.close()
    d = r[0] if r else None
    return d if (d and "-" in d) else ("%s-%s-%s" % (d[:4], d[4:6], d[6:]) if d else None)


def main(argv):
    write = "--write" in argv
    with_disc = "--with-discovery" in argv
    print("ThreeC · 季节性候选追踪 —— 月度刷新")
    print("-" * 78)

    # ① 前置
    if not os.path.exists(DB):
        print("SKIP: history_scan.db 不存在（CI 不携带 1.3GB 库）→ 本机才可刷新")
        return 0
    if not os.path.exists(LEDGER) or not os.path.exists(LOG):
        print("FAIL: 缺账本或形成日志 → 首次请先跑 "
              "`build_candidate_ledger_v0_2.py --bootstrap`")
        return 1
    old = read(LEDGER)
    log = read(LOG)
    prev_as_of = old["market_as_of"]
    last = db_last_day()
    print("  账本结算日 : %s（候选 %d · 批次 %d）"
          % (prev_as_of, old["summary"]["candidates"], len(log["batches"])))
    print("  行情最后日 : %s" % last)

    pd_path = latest("pattern_discovery_v0_")
    pd_as_of = read(pd_path)["as_of"] if pd_path else None
    pd_as_of = pd_as_of if (pd_as_of and "-" in pd_as_of) else (
        "%s-%s-%s" % (pd_as_of[:4], pd_as_of[4:6], pd_as_of[6:]) if pd_as_of else None)
    print("  候选源 as_of: %s（%s）" % (pd_as_of, os.path.basename(pd_path) if pd_path else "缺"))

    # ②③ 判定
    advanced = bool(last and last > prev_as_of)
    can_form = bool(pd_as_of and last and pd_as_of == last)
    print("-" * 78)
    print("  ② 行情推进 : %s" % ("是，有新交易日要结算" if advanced else "否，无新结算"))
    print("  ③ 可形成新批次: %s" % ("是" if can_form else
                                  "否 —— 候选源落后于行情，需先重跑发现（--with-discovery）"))
    if not advanced and not can_form:
        print("-" * 78)
        print("本轮无需刷新：行情未推进且候选源已是最新。")
        return 0

    if not write:
        print("-" * 78)
        print("[dry-run] 将执行：%s→ 账本 --write → 摘要 --write → 双校验 → 报告"
              % ("发现 --write → " if (with_disc and not can_form) else ""))
        return 0

    # ③' 可选：先重跑上游发现
    if with_disc and not can_form:
        print("-" * 78)
        rc, out = run([DISCOVER_PY, "--write"])
        print("  ⊕ 上游发现 : %s" % ("OK" if rc == 0 else "FAIL"))
        if rc != 0:
            print(out[-1200:])
            return 1
        pd_path = latest("pattern_discovery_v0_")
        a = read(pd_path)["as_of"]
        pd_as_of = a if "-" in a else "%s-%s-%s" % (a[:4], a[4:6], a[6:])
        can_form = pd_as_of == last
        print("  → 新候选源 %s（as_of %s，可形成=%s）"
              % (os.path.basename(pd_path), pd_as_of, can_form))

    # ④ 结算 + 形成
    print("-" * 78)
    rc, out = run([LEDGER_PY, "--write"])
    print("  ④ 账本刷新 : %s" % ("OK" if rc == 0 else "FAIL"))
    print("     " + "\n     ".join(l for l in out.strip().split("\n") if l.strip()))
    if rc != 0:
        return 1

    new = read(LEDGER)
    new_log = read(LOG)
    ns, os_ = new["summary"], old["summary"]

    # ⑤ 派生摘要（产品数据）
    rc2, out2 = run([SUMMARY_PY, "--write"])
    print("  ⑤ 产品摘要 : %s" % ("OK" if rc2 == 0 else "FAIL"))
    if rc2 != 0:
        print(out2[-800:])
        return 1

    # ⑥ 双校验
    print("-" * 78)
    ok = True
    for label, args in (("形成稳定性", [LEDGER_PY, "--check-formations"]),
                        ("结算一致性", [LEDGER_PY, "--check-settlement"]),
                        ("摘要一致性", [SUMMARY_PY, "--check"])):
        rc3, out3 = run(args)
        line = [l for l in out3.strip().split("\n") if l.strip()]
        print("  ⑥ %s : %s" % (label, "PASS" if rc3 == 0 else "FAIL"))
        if rc3 != 0:
            print("     " + "\n     ".join(line[-6:]))
            ok = False
        elif any(l.startswith("WARN") for l in line):
            print("     " + "\n     ".join(l for l in line if l.startswith("WARN")))
    if not ok:
        return 1

    # ⑦ 报告
    batches_new = len(new_log["batches"]) - len(log["batches"])
    inst_new = ns["candidates"] - os_["candidates"]
    settled_new = {h: ns["settled"][h] - os_["settled"][h] for h in ns["settled"]}
    payload = {
        "artifact": "candidate_ledger_refresh",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/monthly_candidate_ledger.py",
        "market_as_of": new["market_as_of"],
        "previous_market_as_of": prev_as_of,
        "market_advanced": advanced,
        "upstream_can_form": can_form,
        "new_batches": batches_new,
        "new_instances": inst_new,
        "reappeared_instances": (new.get("formation_run") or {}).get("reappeared"),
        "formation_skipped": (new.get("formation_run") or {}).get("skipped"),
        "settled_new": settled_new,
        "settled_total": ns["settled"],
        "pending_total": ns["pending"],
        "instances_total": ns["candidates"],
        "batches_total": len(new_log["batches"]),
        "by_outcome_type": ns["by_outcome_type"],
        "position": ("机械刷新记录：只搬运既有产物，不改任何 selection_basis；"
                     "冻结快照不可覆盖。★ 本报告不是业绩评价，不含排名或信号。"),
    }
    os.makedirs(REP, exist_ok=True)
    rep = os.path.join(REP, "candidate_ledger_refresh_%s.json" % new["market_as_of"])
    io.open(rep, "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("  ⑦ 报告     : %s" % os.path.relpath(rep, REPO))
    print("-" * 78)
    print("本轮完成：新增批次 %d · 新增实例 %d · 重现 %d · 新结算 %s"
          % (batches_new, inst_new, payload["reappeared_instances"], settled_new))
    print("累计：实例 %d · 5/10/20 已结算 %s · 待结算 %s"
          % (ns["candidates"], ns["settled"], ns["pending"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
