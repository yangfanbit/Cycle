#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""monthly_refresh.py —— **月度研究刷新流程的唯一入口**（`PROJECT_STATE §7` 的 1.2e）。

## 它解决什么

`refresh_current_research.py` 是刷新循环的**机械动作**入口，但它**不做研究判断**，
也**没有把「一轮完整的月度流程」串起来**。实测（2026-10-08）：

- `0479661` 那一轮**加了候选却没推进 `snapshot_date`** → 契约检查 **FAIL**，**无人发现**；
- 检查器**存在但不在任何自动链路里**；
- 数据集**原地覆盖**，上一轮内容只能靠 git 找回。

→ 本脚本把「一轮」串成**一条可执行、可失败、可追溯**的路径。

## ★ 它做什么（机械动作，不做研究判断）

```
① 取「上一轮」归档（candidates_archive/ 里最新的一份）
② 校验当前数据集      refresh_current_research.py --check        （**失败即停**）
③ 与上一轮做 diff      refresh_current_research.py --diff --baseline <上一轮>
④ 归档当前轮           archive_current_round.py                  （不可变）
⑤ 写本轮报告           research/research/reports/monthly_refresh_<日期>.json
```

★ **不写 canonical**。`current_candidates.json` 的内容必须**由离线研究准备好**；
本脚本只在 `--write-canonical` **显式**给出时转发该动作（默认不做）。

## ★★ 研究侧要做的（本脚本**不代替**）

| # | 动作 | 谁做 |
|---|---|---|
| 1 | 检索新证据（≤ 新快照日，Temporal Firewall） | 离线研究 |
| 2 | 更新候选的 `evidence` / `phase_evidence` / `research_questions` | 离线研究 |
| 3 | **推进 `snapshot_date`**（新增/修改内容时必须同步推进） | 离线研究 |
| 4 | 把内容写入 `current_candidates.json` | 离线研究（或 `--write-canonical`） |

## 用法

    python research/scripts/monthly_refresh.py                # 走完整流程
    python research/scripts/monthly_refresh.py --dry-run      # 只看会做什么
    python research/scripts/monthly_refresh.py --write-canonical   # 额外转发写入
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

ROOT = db.ROOT
REPO = os.path.dirname(ROOT)
ARCH = os.path.join(ROOT, "current", "candidates_archive")
INDEX = os.path.join(ARCH, "archive_index.json")
CANON = os.path.join(ROOT, "current", "current_candidates.json")
REP = os.path.join(ROOT, "research", "reports")
PY = sys.executable


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run([PY] + args, cwd=REPO, capture_output=True, text=True)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def archived_rounds() -> list[dict]:
    if not os.path.exists(INDEX):
        return []
    return json.load(io.open(INDEX, encoding="utf-8")).get("rounds") or []


def main(argv):
    dry = "--dry-run" in argv
    rounds = archived_rounds()
    cur = json.load(io.open(CANON, encoding="utf-8"))
    cur_snap = cur.get("snapshot_date")

    # ① 上一轮 = 归档里日期最早的、且**不等于**当前快照日的那一份
    baseline = None
    for r in sorted(rounds, key=lambda x: x["snapshot_date"]):
        if r["snapshot_date"] != cur_snap:
            baseline = r
    if baseline is None and rounds:
        baseline = rounds[0]

    print("ThreeC · 月度研究刷新流程")
    print("-" * 74)
    print("  当前快照日 : %s（候选 %d）" % (cur_snap, len(cur.get("candidates") or [])))
    print("  上一轮     : %s" % (baseline["snapshot_date"] if baseline else "（无归档，首次运行）"))
    print("  已归档轮次 : %d" % len(rounds))
    print("-" * 74)

    if dry:
        print("  [dry-run] 将执行：check → diff → archive → 报告")
        return 0

    # ② 校验（**失败即停**）
    rc, out = run([os.path.join("research", "scripts", "refresh_current_research.py"), "--check"])
    ok = "结果: PASS" in out
    print("  ② 契约校验 : %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        print(out[-800:])
        print("-" * 74)
        print("★ 契约未通过 —— **流程在此停止**（不归档、不 diff）。")
        print("  常见原因：新增/修改了候选但**没有同步推进 `snapshot_date`**。")
        return 1

    # ③ diff
    diff_out = ""
    if baseline:
        bp = os.path.join(ARCH, baseline["file"])
        _, diff_out = run([os.path.join("research", "scripts", "refresh_current_research.py"),
                           "--diff", "--baseline", bp])
        seg = diff_out.split("Candidate Diff")[-1]
        print("  ③ 与上一轮 diff:")
        for line in seg.split("\n"):
            if any(k in line for k in ("baseline", "NEW", "UPDATED", "UNCHANGED", "REJECTED", "MERGED", "stable")):
                print("       " + line.strip())

    # ④ 归档
    rc, out = run([os.path.join("research", "scripts", "archive_current_round.py")])
    print("  ④ 归档     : %s" % ("OK" if rc == 0 else "FAIL"))
    if rc != 0:
        print(out[-500:])
        return 1

    # ⑤ 报告
    os.makedirs(REP, exist_ok=True)
    rep = os.path.join(REP, "monthly_refresh_%s.json" % cur_snap)
    payload = {
        "artifact": "monthly_refresh",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/monthly_refresh.py",
        "snapshot_date": cur_snap,
        "candidate_count": len(cur.get("candidates") or []),
        "baseline_snapshot_date": baseline["snapshot_date"] if baseline else None,
        "contract_check": "PASS",
        "diff_raw": diff_out,
        "position": ("Research-only —— 月度刷新流程的**机械动作**记录。"
                     "**不做研究判断**；内容由离线研究准备。"),
    }
    io.open(rep, "w", encoding="utf-8", newline="\n").write(
        json.dumps(payload, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("  ⑤ 报告     : %s" % os.path.relpath(rep, REPO))

    if "--write-canonical" in argv:
        rc, out = run([os.path.join("research", "scripts", "refresh_current_research.py"),
                       "--check", "--write-canonical"])
        print("  ⊕ 写入 canonical : %s" % ("OK" if rc == 0 else "FAIL"))

    print("-" * 74)
    print("本轮完成。★ 别忘了：**新增/修改内容时同步推进 `snapshot_date`** —— 上一轮正是漏了这一步。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
