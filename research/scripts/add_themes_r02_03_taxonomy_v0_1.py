#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""add_themes_r02_03_taxonomy_v0_1.py —— taxonomy 轮次（R02-03 后续）：向 DB `themes` 插入 4 行。

## 为什么需要这一步

R02-03 提交的四条 `macro_theme_proposal` 经 **CMTR v1** 解析**全部为 `UNRESOLVED_NAME`** ——
DB `themes` 表里**一个都没有**。协议 §3.4 / 覆盖计划 §3.3：

> 若某新族在 DB `themes` 中**不存在对应根节点** → 这是**数据决策**，
> 必须**单独轮次**处理，**不在**研究任务内自动新增 taxonomy 行。

→ 于是 R02-03 的 9 条候选**无法写入 canonical**（不是因为候选不成立，是**根节点不存在**）。
本脚本就是那个「单独轮次」。

## 决策依据

`docs/TAXONOMY_ROUND_PROPOSAL_R02_03_v0_1.md`（ThreeC Agent 建议，用户 2026-10-10 批准）：

> **根 = 机制族；子 = 具体行业 / 题材。**
> 判据不是「方向重不重要」，而是「**它的机制轴在现有 11 个根里有没有被代表**」。

★ 决定性先例：**`半导体` 在 DB 里是 `电子` 的子节点**（`TH-ELEC-SEMI`）。
A 股最标志性的题材之一都不是根 → 「标志性」不足以成为根。

| 方向 | 处置 | 理由 |
|---|---|---|
| **电力（运营端）** | **新增根** `TH-POWER-OP` | 机制（受管制价格下的成本×电价×利用率）在 11 个根中**零代表** |
| **文化传媒** | **新增根** `TH-MEDIA` | 机制（**监管周期**）在 11 个根中**零代表** |
| 煤炭 | **子** `TH-RES-COAL` → `TH-RES` | 机制（供给收缩/涨价）已由 `资源` 代表 |
| 流感疫苗 | **子** `TH-PHARMA-FLU` → `TH-PHARMA` | 机制（事件+季节性需求）已由同根 `疫情医疗` 代表 |

## ★★ 命名坑（必须避开）

DB 里**没有**「电力」，但有「**电力设备**」（`TH-POWER`）。
**任何字面 / 子串匹配都会把「电力」误判进「电力设备」。**
→ 新根名称必须带限定词：**`电力（运营端）`**，**不得**使用裸「电力」。
（`themes` 表已允许括号与斜杠，如既有 `CXO(研发外包)` · `减重 / GLP-1`。）

## 本脚本做什么 / 不做什么

**做**：只向 `themes` 表 **INSERT 4 行**。

**不做**：
- ❌ 不改 `research/schema/schema.sql`（表结构无需变 —— 只加数据）
- ❌ 不改任何既有 theme 行
- ❌ 不改任何 Campaign / Evidence / 日期
- ❌ 不把任何 R02-03 候选写入 `campaigns`（那要等候选级改动 + 独立性闸门）
- ❌ 不重出 `exports/`（本次不新增任何 `campaign_themes` 关联 → 导出不变）

## 安全设计

1. **幂等**：`theme_id` 已存在且**四列完全相同** → 跳过；**不同** → **拒绝**（不静默改写）。
2. **重名防护**：CMTR 的 `ambiguous_names` 会让**重名主题不可解析** ——
   插入前逐一校验新名称在表中**尚不存在**。
3. **父节点存在性**：子主题的 `parent_theme_id` 必须在表中存在，且**必须是根节点**。
4. **单事务**：任何一步失败即 `ROLLBACK`，DB 保持原样。
5. **验收**：插入后跑 CMTR v1，确认四个方向由 `UNRESOLVED_NAME` → **`RESOLVED`**。

## 用法

    python research/scripts/add_themes_r02_03_taxonomy_v0_1.py --dry-run   # 只看计划
    python research/scripts/add_themes_r02_03_taxonomy_v0_1.py --apply     # 真正写入
    python research/scripts/add_themes_r02_03_taxonomy_v0_1.py --verify    # 只做 CMTR 验收

退出码：0 = 成功；1 = 失败（含拒绝写入）。
"""

import argparse
import io
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")

sys.path.insert(0, SCRIPT_DIR)
from theme_taxonomy import Taxonomy, load_from_cursor  # noqa: E402

# ================================================================ 本次要新增的 4 行

NEW_THEMES = [
    {
        "theme_id": "TH-POWER-OP",
        "name": "电力（运营端）",
        "theme_type": "industry",
        "parent_theme_id": None,
        "description": (
            "公用事业运营端：发电与电网运营的成本、电价与利用率。"
            "机制轴 = 受管制价格下的成本—电价剪刀差 × 利用小时 / 来水 / 消纳。"
            "★ 与 TH-POWER「电力设备」（制造端：设备需求与产能）**不同机制、不得互相替代**。"
            "★ 名称刻意带限定词「（运营端）」—— 裸「电力」会与「电力设备」发生字面/子串误判。"
            "（taxonomy 轮次 · R02-03 后续 · 2026-10-10）"
        ),
    },
    {
        "theme_id": "TH-MEDIA",
        "name": "文化传媒",
        "theme_type": "industry",
        "parent_theme_id": None,
        "description": (
            "文化传媒：政策 / 监管周期 + 内容供给 + 平台经济（游戏版号 · 影视 · 出版 · 广告）。"
            "机制轴 = **监管周期** —— 该轴在既有 11 个根节点中零代表。"
            "★ 全库此前零覆盖；「广电 / 传媒」仅存在于 legacy `data/` 层（无消费者），不在 canonical。"
            "（taxonomy 轮次 · R02-03 后续 · 2026-10-10）"
        ),
    },
    {
        "theme_id": "TH-RES-COAL",
        "name": "煤炭",
        "theme_type": "industry",
        "parent_theme_id": "TH-RES",
        "description": (
            "煤炭（动力煤 / 焦煤）。机制轴 = 供给收缩 / 价格驱动"
            "（长协履约 · 保供核增 · 进口配额 · 安监限产 · 煤电联动）。"
            "★ 挂 `资源` 下而非独立成根：该机制轴已由 `资源` 代表"
            "（有色金属 / 贵金属 / 稀有金属·稀土）。依覆盖计划 §1.3 原则 6"
            "「与已有案例机制高度重复 → 结构上等于没有扩容」。"
            "★ 保留升级路径：若将来出现「煤电联动」这类**真正新增**的机制，再议升根。"
            "（taxonomy 轮次 · R02-03 后续 · 2026-10-10）"
        ),
    },
    {
        "theme_id": "TH-PHARMA-FLU",
        "name": "流感疫苗",
        "theme_type": "concept",
        "parent_theme_id": "TH-PHARMA",
        "description": (
            "流感疫苗 / 流感（含抗流感药物）。机制轴 = 公共卫生事件 + 季节性需求"
            "（毒株预测 · 批签发 · 接种率）。"
            "★ 挂 `医药健康` 下而非独立成根：机制已由同根 `疫情医疗` 代表，"
            "且本品类很窄（做根会造出只有 1–2 个对象的族）；"
            "医药健康是**最薄的一族**，按覆盖计划 §2.1「需补强」应加子主题而非另立新根。"
            "（taxonomy 轮次 · R02-03 后续 · 2026-10-10）"
        ),
    },
]

# CMTR 验收用的名称（四个方向的全部候选名，含预期**仍然未解析**的）
VERIFY_NAMES = {
    "煤炭": ["煤炭", "动力煤", "煤炭开采", "焦煤"],
    "电力（运营端）": ["电力", "绿色电力", "绿电", "新能源运营商", "电力体制改革", "虚拟电厂"],
    "流感疫苗": ["流感疫苗", "流感", "抗流感", "疫苗"],
    "文化传媒": ["文化传媒", "传媒", "游戏", "影视", "出版", "广告"],
}


def read_themes(cur):
    cur.execute("SELECT theme_id, name, theme_type, parent_theme_id FROM themes")
    return cur.fetchall()


def cmtr_snapshot(cur, names):
    tax = load_from_cursor(cur)
    return tax.resolve_names(names), tax


def print_cmtr(label, names, res):
    print("  %-22s status=%-16s roots=%s" % (label, res["status"], res["macro_theme_names"]))
    if res["unmatched_names"]:
        print("  %-22s   未解析: %s" % ("", res["unmatched_names"]))


def main(argv):
    ap = argparse.ArgumentParser(description="taxonomy 轮次：向 themes 插入 4 行（R02-03 后续）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="只打印计划与前置校验，不写入")
    g.add_argument("--apply", action="store_true", help="真正写入")
    g.add_argument("--verify", action="store_true", help="只做 CMTR 验收")
    args = ap.parse_args(argv)

    if not os.path.isfile(DB_PATH):
        raise SystemExit("找不到 DB：%s" % DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # ---------- 1) 前置校验 ----------
    rows = read_themes(cur)
    by_id = {r[0]: r for r in rows}
    name_count = {}
    for r in rows:
        name_count[r[1]] = name_count.get(r[1], 0) + 1
    dup_names = sorted(n for n, c in name_count.items() if c > 1)

    print("=" * 78)
    print("taxonomy 轮次（R02-03 后续）· DB themes 插入 4 行")
    print("=" * 78)
    print("现状：themes 行数 = %d" % len(rows))
    if dup_names:
        print("!! 表中已存在重名主题（CMTR 会判 ambiguous）：%s" % dup_names)

    problems = []
    plan = []
    for t in NEW_THEMES:
        tid, nm = t["theme_id"], t["name"]
        existing = by_id.get(tid)
        if existing:
            same = (existing[1], existing[2], existing[3]) == (nm, t["theme_type"], t["parent_theme_id"])
            if same:
                plan.append(("SKIP(已存在且一致)", t))
                continue
            problems.append("theme_id %s 已存在但内容不同：现=%s 欲=%s"
                            % (tid, existing[1:], (nm, t["theme_type"], t["parent_theme_id"])))
            continue
        if name_count.get(nm, 0) > 0:
            problems.append("名称 %r 在表中已存在 → 会造成 CMTR ambiguous，拒绝插入" % nm)
            continue
        p = t["parent_theme_id"]
        if p is not None:
            if p not in by_id:
                problems.append("%s 的父节点 %s 不存在" % (tid, p))
                continue
            if by_id[p][3] is not None:
                problems.append("%s 的父节点 %s 不是根节点（它自己还有 parent）" % (tid, p))
                continue
        plan.append(("INSERT", t))

    print()
    print("计划：")
    for action, t in plan:
        print("  %-20s %-12s %-10s %-12s parent=%s"
              % (action, t["theme_id"], t["name"], t["theme_type"], t["parent_theme_id"]))
    if problems:
        print()
        print("!! 前置校验失败：")
        for p in problems:
            print("   - %s" % p)
        return 1

    # ---------- 2) CMTR 前快照 ----------
    print()
    print("CMTR v1 · 插入前：")
    before = {}
    for label, names in VERIFY_NAMES.items():
        res, _ = cmtr_snapshot(cur, names)
        before[label] = res
        print_cmtr(label, names, res)

    if args.verify:
        return 0
    if args.dry_run:
        print()
        print("--dry-run：未写入任何内容。")
        return 0

    # ---------- 3) 写入（单事务） ----------
    inserted = 0
    try:
        for action, t in plan:
            if action != "INSERT":
                continue
            cur.execute(
                "INSERT INTO themes (theme_id, name, theme_type, parent_theme_id, description)"
                " VALUES (?, ?, ?, ?, ?)",
                (t["theme_id"], t["name"], t["theme_type"], t["parent_theme_id"], t["description"]),
            )
            inserted += 1
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print()
        print("!! 写入失败，已 ROLLBACK：%s" % exc)
        return 1

    print()
    print("✓ 已插入 %d 行（单事务提交）" % inserted)

    # ---------- 4) CMTR 验收 ----------
    rows2 = read_themes(cur)
    print()
    print("CMTR v1 · 插入后（themes 行数 = %d）：" % len(rows2))
    ok = True
    for label, names in VERIFY_NAMES.items():
        res, _ = cmtr_snapshot(cur, names)
        print_cmtr(label, names, res)
        # ★ 验收标准：新增的那一个名称必须由「未解析」变为「已解析」且可上溯到根
        key = label if label != "电力（运营端）" else None
        if key is not None:
            if key not in res["matched_names"]:
                ok = False
                print("     ✗ 验收失败：%r 仍未解析" % key)
            else:
                print("     ✓ %r 已解析 → 根 %s" % (key, res["macro_theme_names"]))

    # 「电力（运营端）」用全名单独验收
    res, _ = cmtr_snapshot(cur, ["电力（运营端）"])
    print_cmtr("电力（运营端）· 全名", ["电力（运营端）"], res)
    if res["status"] != "RESOLVED":
        ok = False
        print("     ✗ 验收失败：全名未 RESOLVED")
    else:
        print("     ✓ 已解析 → 根 %s" % res["macro_theme_names"])

    # ★★ 关键回归：裸「电力」必须**仍然未解析**（不得因新增根而被误判进「电力设备」）
    res, _ = cmtr_snapshot(cur, ["电力"])
    print_cmtr("回归：裸「电力」", ["电力"], res)
    if res["status"] != "UNRESOLVED_NAME":
        ok = False
        print("     ✗ 回归失败：裸「电力」不应被解析（会与「电力设备」混淆）")
    else:
        print("     ✓ 裸「电力」仍未解析 —— 未与「电力设备」混淆")

    # ★ 子主题必须上溯到正确的根
    for label, want_root in (("煤炭", "资源"), ("流感疫苗", "医药健康")):
        res, _ = cmtr_snapshot(cur, [label])
        got = res["macro_theme_names"]
        if got != [want_root]:
            ok = False
            print("     ✗ %s 上溯到 %s，期望 [%s]" % (label, got, want_root))
        else:
            print("     ✓ %s → 根 %s" % (label, want_root))

    print()
    print("CMTR 验收：%s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
