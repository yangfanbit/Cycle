#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""theme_taxonomy.py —— Canonical Macro Theme Resolution v1（单一事实来源）。

## 为什么需要本模块

ThreeC 曾同时存在两种 Macro Theme 解析口径：

- `direct`   —— 检查对象的 `themes[]` 中是否**字面出现** Macro Theme 名称（如「汽车」）
- `resolved` —— 沿 DB `themes.parent_theme_id` 链上溯至根节点

两者**不等价**：一个只登记子主题（如「智能驾驶/无人驾驶」）的对象，
在 `direct` 下被判为「无 Macro Theme」，在 `resolved` 下正确归入「汽车」。

`Historical Coverage Audit v0.1` 已确认该差异影响 4 个对象
（`C-2019-AD` / `RC-2024-SECONDARY` / `RC-2020-PANDEMIC` / `RC-2021-TCM`），
并指出这正是 `Time Observation Discovery v0.2` 中 3 条候选被判「口径脆弱」的根本原因。

## Canonical 规则（CMTR v1）

    对象 Macro Theme = themes[] 名称
                       → DB `themes` 表归一化为 theme_id
                       → 沿 parent_theme_id 上溯至根
                       → 根节点集合

- **唯一事实来源是 DB `themes` 表**。不接受任何硬编码的「主题族名称表」。
- **不使用** `direct`（字面名称匹配）口径。
- 名称无法在 taxonomy 中解析时**不静默丢弃** —— 必须显式报告
  （`status = UNRESOLVED_NAME` 或 `unmatched_names` 非空）。
- 解析**不修改**任何数据：本模块只读，且不改变锚点定义与统计量。

## status

    RESOLVED         恰好 1 个根节点
    CONFLICT         ≥2 个根节点（跨 Macro Theme，不可归属）
    UNRESOLVED_NAME  0 个根节点，且存在 taxonomy 中不存在的主题名称
    NO_THEME         0 个根节点，且对象未登记任何主题

`unmatched_names` 在**任何** status 下都会列出未解析名称；
`has_taxonomy_gap` 标记「已解析出根，但仍有名称未解析」的情形。

## 已知 taxonomy 缺口（不在本模块修复）

`F7`：`RC-2023-HUAWEI` 的题材「华为汽车」不在 DB `themes` 表中 →
本模块如实报 `UNRESOLVED_NAME`，**不发明 taxonomy 行**。
补录属数据决策，须走独立轮次（见 `docs/PROJECT_STATE.md`）。

用法:
    import theme_taxonomy
    tax = theme_taxonomy.load(conn)
    tax.resolve_names(["智能驾驶/无人驾驶"])   # -> {'macro_theme_ids': ['TH-AUTO'], ...}
"""

from __future__ import annotations

RULESET = "canonical-macro-theme-resolution-1"

STATUSES = ("RESOLVED", "CONFLICT", "UNRESOLVED_NAME", "NO_THEME")


class Taxonomy:
    """DB `themes` 表的只读内存视图 + canonical 解析。"""

    def __init__(self, rows):
        # rows: [{"theme_id","name","theme_type","parent_theme_id"}, ...]
        self.rows = list(rows)
        self.name_of = {r["theme_id"]: r["name"] for r in self.rows}
        self.parent_of = {r["theme_id"]: r["parent_theme_id"] for r in self.rows}
        self.type_of = {r["theme_id"]: r["theme_type"] for r in self.rows}

        # 名称 → theme_id（检测重名，重名一律视为不可解析，不猜测）
        by_name = {}
        dup = set()
        for r in self.rows:
            nm = r["name"]
            if nm in by_name and by_name[nm] != r["theme_id"]:
                dup.add(nm)
            by_name.setdefault(nm, r["theme_id"])
        self.ambiguous_names = dup
        self.by_name = {nm: tid for nm, tid in by_name.items() if nm not in dup}

        # 根节点 = parent_theme_id IS NULL
        self.macro_ids = sorted(
            r["theme_id"] for r in self.rows if r["parent_theme_id"] is None
        )
        self.macro_names = {m: self.name_of[m] for m in self.macro_ids}

        # theme_id → root（沿 parent 链上溯；带环保护）
        self.root_of = {r["theme_id"]: self._root(r["theme_id"]) for r in self.rows}

    # ---------------------------------------------------------------- 基础

    def _root(self, tid):
        seen = set()
        while tid is not None and tid not in seen:
            seen.add(tid)
            if self.parent_of.get(tid) is None:
                return tid
            tid = self.parent_of.get(tid)
        return None

    def root_map(self):
        """theme_id → root theme_id（含 Macro Theme 自身 → 自身）。"""
        return dict(self.root_of)

    def name_map(self):
        """theme_id → name。"""
        return dict(self.name_of)

    def parent_map(self):
        """theme_id → parent_theme_id。"""
        return dict(self.parent_of)

    def is_macro(self, tid):
        return tid in self.macro_names

    # ---------------------------------------------------------------- canonical 解析

    def resolve_names(self, names):
        """按 CMTR v1 解析一组主题名称 → Macro Theme 根集合。

        返回 dict：
            macro_theme_ids   sorted list[str]     解析出的根节点
            macro_theme_names sorted list[str]     根节点名称
            status            str                  RESOLVED / CONFLICT / UNRESOLVED_NAME / NO_THEME
            matched_names     sorted list[str]     成功解析的名称
            unmatched_names   sorted list[str]     taxonomy 中不存在的名称
            ambiguous_names   sorted list[str]     taxonomy 中重名、不可解析的名称
            has_taxonomy_gap  bool                 已解析出根，但仍有名称未解析
        """
        roots = set()
        matched = []
        unmatched = []
        ambiguous = []
        for nm in names or []:
            if nm is None:
                continue
            if nm in self.ambiguous_names:
                ambiguous.append(nm)
                continue
            tid = self.by_name.get(nm)
            if tid is None:
                unmatched.append(nm)
                continue
            matched.append(nm)
            r = self.root_of.get(tid)
            if r:
                roots.add(r)

        n = len(roots)
        if n == 1:
            status = "RESOLVED"
        elif n >= 2:
            status = "CONFLICT"
        elif unmatched or ambiguous:
            status = "UNRESOLVED_NAME"
        else:
            status = "NO_THEME"

        unmatched_sorted = sorted(set(unmatched))
        ambiguous_sorted = sorted(set(ambiguous))
        return {
            "macro_theme_ids": sorted(roots),
            "macro_theme_names": sorted(self.macro_names.get(r, r) for r in roots),
            "status": status,
            "matched_names": sorted(set(matched)),
            "unmatched_names": unmatched_sorted,
            "ambiguous_names": ambiguous_sorted,
            "has_taxonomy_gap": bool(n >= 1 and (unmatched_sorted or ambiguous_sorted)),
        }

    def resolve_object(self, obj):
        """解析一个 export 对象（Campaign / Research Candidate）。"""
        names = [t.get("name") for t in (obj.get("themes") or [])]
        return self.resolve_names(names)

    def macro_theme_id_of(self, obj):
        """单值便利接口：仅 RESOLVED 时返回 Macro Theme id，否则 None。

        `CONFLICT` 一律返回 None（不可归属，不得任选其一）。
        """
        res = self.resolve_object(obj)
        if res["status"] == "RESOLVED":
            return res["macro_theme_ids"][0]
        return None


# ================================================================ 装载


def from_rows(rows):
    return Taxonomy(rows)


def load(conn):
    """从 sqlite3 连接装载 taxonomy（只读）。"""
    return load_from_cursor(conn.cursor())


def load_from_cursor(cur):
    """从 sqlite3 游标装载 taxonomy（只读）。"""
    cur.execute(
        "SELECT theme_id, name, theme_type, parent_theme_id FROM themes ORDER BY theme_id"
    )
    rows = [
        {
            "theme_id": r[0],
            "name": r[1],
            "theme_type": r[2],
            "parent_theme_id": r[3],
        }
        for r in cur.fetchall()
    ]
    return Taxonomy(rows)


# ================================================================ 批量报告


def resolution_report(tax, objects):
    """批量解析 + 汇总报告（供 Artifact / Audit 直接落盘）。

    objects: [{"kind","campaign_id","title","year","themes"}...]（export 侧对象）
    """
    per_object = []
    by_status = {}
    unmatched_index = {}
    macro_members = {}

    for o in objects:
        res = tax.resolve_object(o)
        cid = o.get("campaign_id") or o.get("id")
        per_object.append(
            {
                "kind": o.get("kind"),
                "campaign_id": cid,
                "year": o.get("year"),
                "theme_names": sorted(
                    t.get("name") for t in (o.get("themes") or []) if t.get("name")
                ),
                "status": res["status"],
                "macro_theme_ids": res["macro_theme_ids"],
                "macro_theme_names": res["macro_theme_names"],
                "unmatched_names": res["unmatched_names"],
                "ambiguous_names": res["ambiguous_names"],
                "has_taxonomy_gap": res["has_taxonomy_gap"],
            }
        )
        by_status.setdefault(res["status"], []).append(cid)
        for nm in res["unmatched_names"]:
            unmatched_index.setdefault(nm, []).append(cid)
        for m in res["macro_theme_ids"]:
            macro_members.setdefault(m, []).append(cid)

    return {
        "ruleset": RULESET,
        "rule": (
            "对象 Macro Theme = themes[] 名称 → DB themes 表归一化 → 沿 parent_theme_id 上溯至根；"
            "不使用 direct（字面名称匹配）口径。"
        ),
        "not_a": [
            "本解析不修改任何数据（只读 DB themes 表）",
            "本解析不改变锚点定义与统计量",
            "本解析不发明 taxonomy 行；未解析名称一律如实上报",
        ],
        "status_vocabulary": list(STATUSES),
        "macro_themes": [
            {"theme_id": m, "name": tax.macro_names[m]} for m in tax.macro_ids
        ],
        "macro_theme_count": len(tax.macro_ids),
        "objects_resolved": per_object,
        "counts_by_status": {s: len(by_status.get(s, [])) for s in STATUSES},
        "macro_theme_members": {
            m: sorted(set(macro_members.get(m, []))) for m in tax.macro_ids
        },
        "unmatched_theme_names": {
            nm: sorted(set(cids)) for nm, cids in sorted(unmatched_index.items())
        },
        "taxonomy_gap_note": (
            "unmatched_theme_names 非空 = taxonomy 缺口，属数据决策，不在本解析内修复。"
        ),
    }
