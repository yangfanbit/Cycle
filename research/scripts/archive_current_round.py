#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""archive_current_round.py —— 把「当前研究对象」的每一轮**原样落袋**（不可变归档）。

## 为什么需要它（2026-10-08 实测暴露）

`research/current/current_candidates.json` 是**单文件、原地覆盖**的。实测后果：

- `0479661` 那一轮**加了汽车候选（`last_updated=2026-10-07`）却没改 `snapshot_date`（仍是 2026-09-15）**
  → `refresh_current_research.py --check` **报 FAIL**，而**没有任何流程会发现**；
- 更根本的是：**「上一轮当时记录的是什么」在项目里查不到** ——
  只能靠 `git show <commit>:research/current/current_candidates.json` 找回。

> ★ 用户 2026-10-08 的要求：「**之前的观察台内容也要落袋**」——
> 没有归档，就**无法回看**「当时记录的阶段/维度，后来怎么走的」。

## 它做什么

把 `current_candidates.json` **原样复制**到
`research/current/candidates_archive/current_candidates_<snapshot_date>.json`，
并在 `archive_index.json` 里登记 `{snapshot_date, candidates, sha256, archived_at, note}`。

## ★ 不可变纪律

- 同一 `snapshot_date` **已存在且内容不同** → **拒绝**（`--force` 才覆盖），
  避免「同名不同内容」把归档变成又一个会被悄悄改写的文件；
- 归档**只读**：本脚本**不改** `current_candidates.json`。

## 用法

    python research/scripts/archive_current_round.py                    # 归档当前轮
    python research/scripts/archive_current_round.py --from-git <sha>   # 归档历史某一轮
    python research/scripts/archive_current_round.py --list             # 列出已归档轮次
    python research/scripts/archive_current_round.py --force            # 允许覆盖同名
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

ROOT = db.ROOT
CANON = os.path.join(ROOT, "current", "current_candidates.json")
ARCH = os.path.join(ROOT, "current", "candidates_archive")
INDEX = os.path.join(ARCH, "archive_index.json")
REL = "research/current/current_candidates.json"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_index() -> dict:
    if not os.path.exists(INDEX):
        return {"artifact": "current_candidates_archive_index", "artifact_version": "0.1", "rounds": []}
    return json.load(io.open(INDEX, encoding="utf-8"))


def main(argv):
    if "--list" in argv:
        idx = load_index()
        print("已归档轮次：%d" % len(idx["rounds"]))
        for r in idx["rounds"]:
            print("  %s | 候选 %d | sha %s | %s" % (
                r["snapshot_date"], r["candidates"], r["sha256"][:12], r.get("note") or ""))
        return 0

    from_git = None
    if "--from-git" in argv:
        from_git = argv[argv.index("--from-git") + 1]

    if from_git:
        text = subprocess.run(["git", "show", "%s:%s" % (from_git, REL)],
                              cwd=os.path.dirname(ROOT), capture_output=True, text=True).stdout
        if not text.strip():
            print("✗ 取不到 %s:%s" % (from_git, REL))
            return 1
        note = "从 git %s 恢复" % from_git[:7]
    else:
        text = io.open(CANON, encoding="utf-8").read()
        note = None

    data = json.loads(text)
    snap = data.get("snapshot_date")
    if not snap:
        print("✗ 数据集缺 snapshot_date，无法归档")
        return 1

    os.makedirs(ARCH, exist_ok=True)
    dest = os.path.join(ARCH, "current_candidates_%s.json" % snap)
    h = sha(text)

    if os.path.exists(dest) and not ("--force" in argv):
        old = sha(io.open(dest, encoding="utf-8").read())
        if old != h:
            print("✗ %s 已存在且内容不同（旧 %s / 新 %s）—— 拒绝覆盖。" % (
                os.path.basename(dest), old[:12], h[:12]))
            print("  ★ 不可变纪律：同一 snapshot_date 不得有两种内容。若确要覆盖，加 --force。")
            return 1
        print("= %s 已归档且内容一致，跳过" % os.path.basename(dest))
    else:
        io.open(dest, "w", encoding="utf-8", newline="\n").write(text)
        print("✓ 已归档 %s（候选 %d）" % (os.path.basename(dest), len(data.get("candidates") or [])))

    idx = load_index()
    idx["rounds"] = [r for r in idx["rounds"] if r["snapshot_date"] != snap]
    idx["rounds"].append({
        "snapshot_date": snap,
        "candidates": len(data.get("candidates") or []),
        "candidate_ids": [c.get("candidate_id") for c in (data.get("candidates") or [])],
        "generated_at": data.get("generated_at"),
        "sha256": h,
        "archived_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
        "source": ("git:%s" % from_git[:7]) if from_git else "canonical",
        "note": note,
        "file": os.path.basename(dest),
    })
    idx["rounds"].sort(key=lambda r: r["snapshot_date"])
    io.open(INDEX, "w", encoding="utf-8", newline="\n").write(
        json.dumps(idx, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("  索引已更新：%d 轮" % len(idx["rounds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
