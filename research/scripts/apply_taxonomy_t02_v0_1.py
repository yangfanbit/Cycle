#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""apply_taxonomy_t02_v0_1.py —— T02 Taxonomy Gap Resolution（R02-01 医药健康）。

## 目的

补齐 R02-01 Intake Package 入库所需的 taxonomy：新增 **1 个子主题**
`TH-PHARMA-GLP1`（减重 / GLP-1），挂到既有 Macro Theme `TH-PHARMA`（医药健康）下。

## 边界（严格，与 T01 同）

- **只写 `themes` 表**。不改 Campaign / Evidence / Lifecycle / 任何其它表。
- **不改既有行**（含 `TH-PHARMA` 与既有 15+ 子主题的语义）。
- **不改 `theme_taxonomy.py`（CMTR v1）**。
- 幂等：已存在则跳过，重复运行结果一致。

## 设计原则（沿用 T01）

> **Macro Theme root = 机制家族**；子主题 = 该家族内**可分辨的结构**。

`减重 / GLP-1` 与既有 `TH-PHARMA-INNOV`（创新药产业链升级）、`TH-PHARMA-CXO`（CXO）、
`TH-PHARMA-TCM`（中医药）在**驱动机制上可分辨**：
后者为国内制度供给 / 研发外包 / 品牌中药，本主题为**海外需求外溢 + 事件催化**。
故作为独立子主题，而非并入 `TH-PHARMA-INNOV`。

## 用法

    python research/scripts/apply_taxonomy_t02_v0_1.py --dry-run
    python research/scripts/apply_taxonomy_t02_v0_1.py
    python research/scripts/apply_taxonomy_t02_v0_1.py --verify
"""

from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")

DECISION_ROUND = "T02"

# (theme_id, name, theme_type, parent_theme_id, description)
ROWS = [
    (
        "TH-PHARMA-GLP1",
        "减重 / GLP-1",
        "concept",
        "TH-PHARMA",
        "子主题：以 GLP-1 受体激动剂（司美格鲁肽 / 替尔泊肽）为核心的减重与降糖叙事，"
        "及上游多肽原料药。驱动机制为**海外需求外溢 + 事件催化**（临床数据 / 学术会议 / 监管），"
        "与 TH-PHARMA-INNOV（国内制度供给驱动）机制可分辨。"
        "来源：R02-01 Intake Package（2026-10-07），审查结论 ACCEPT_WITH_CHANGES。",
    ),
]


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    verify = "--verify" in argv
    if not os.path.exists(DB_PATH):
        print("FAIL  DB 不存在: %s" % DB_PATH)
        return 1

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("ThreeC · Taxonomy %s —— R02-01 医药健康" % DECISION_ROUND)
    print("-" * 62)

    if verify:
        ok = True
        for tid, name, _t, parent, _d in ROWS:
            r = cur.execute(
                "SELECT name, parent_theme_id FROM themes WHERE theme_id=?", (tid,)
            ).fetchone()
            if r is None:
                print("FAIL  %s 不存在" % tid)
                ok = False
            else:
                print("OK    %s → %s（parent=%s）" % (tid, r[0], r[1]))
        p = cur.execute("SELECT name FROM themes WHERE theme_id='TH-PHARMA'").fetchone()
        print("OK    父主题 TH-PHARMA → %s" % (p[0] if p else "✗ 缺失"))
        conn.close()
        return 0 if ok else 1

    added, skipped = 0, 0
    for tid, name, ttype, parent, desc in ROWS:
        if cur.execute("SELECT 1 FROM themes WHERE theme_id=?", (tid,)).fetchone():
            print("SKIP  %s 已存在（幂等）" % tid)
            skipped += 1
            continue
        if not cur.execute("SELECT 1 FROM themes WHERE theme_id=?", (parent,)).fetchone():
            print("FAIL  父主题 %s 不存在 → 拒绝写入（不猜）" % parent)
            conn.close()
            return 1
        if dry:
            print("DRY   INSERT themes(%s, %s, %s, parent=%s)" % (tid, name, ttype, parent))
        else:
            cur.execute(
                "INSERT INTO themes (theme_id, name, theme_type, parent_theme_id, description) "
                "VALUES (?,?,?,?,?)",
                (tid, name, ttype, parent, desc),
            )
            print("ADD   %s → %s（parent=%s）" % (tid, name, parent))
        added += 1

    if not dry:
        conn.commit()
    print("-" * 62)
    print("%s新增 %d · 跳过 %d · 共 %d 行" % ("[dry-run] " if dry else "", added, skipped, len(ROWS)))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
