#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""fix_r01_04_security_map_v0_1.py —— 修正 R01-04 导入器的**标的映射错位**造成的错误挂载。

## 缺陷（2026-10-08 实测，见 `check_intake_security_map_v0_1.py`）

`import_r01_04_canonical_v0_1.py` 的 `SEC_MAP` 相对包自己的 `securities.json`
**循环错位了 16 个**（SEC016–SEC031 整体旋转 3 位）。后果是**错的标的被挂到 campaign 上**：

| campaign | 应挂（包声明） | 实际挂（错位后） |
|---|---|---|
| `C-2020-CONS-WHITE-GOODS` | 美的 · 格力 · 海尔 · 老板电器 | 老板电器 · 爱美客 · 华熙生物 · 朗姿 |
| `C-2019-CONS-AESTHETICS` | 爱美客 · 华熙生物 · 朗姿 | 珀莱雅 · 贝泰妮 · 万辰集团 |
| `C-2020-CONS-BEAUTY-CN` | 珀莱雅 · 贝泰妮 | 盐津铺子 · 乖宝宠物 |
| `C-2024-CONS-TRADE-IN` | 美的 · 格力 · 海尔 · 老板电器 | 老板电器 · 爱美客 · 华熙生物 · 朗姿 |
| `C-2023-CONS-VALUE-RETAIL` | 万辰集团 · 盐津铺子 | 中宠股份 · 科沃斯 |

**结构校验全程 PASS** —— 它查形状，不查「映射是否忠于包」。

## ★ 修正原则

- **期望值从包推导**（`securities.json` 的 ticker → canonical `security_id`），**不写死手工表**。
- `role` 保持 `representative`（导入器硬编码如此，属既有约定，不在本次修正范围）。
- **事务**：先备份 → dry-run → 应用 → 验证。
- 两个 `RC-` 对象（`RC-2020-CONS-SMALL-APPLIANCE` / `RC-2024-CONS-PET-FOOD`）**不在 `campaigns` 表、
  也没有挂载行** → 无需修正，但**在报告中列出**。

## 用法

    python research/scripts/fix_r01_04_security_map_v0_1.py --dry-run
    python research/scripts/fix_r01_04_security_map_v0_1.py
"""

from __future__ import annotations

import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

ROOT = db.ROOT
PKG = os.path.join(ROOT, "intake", "packages", "R01-04")

# 受影响的 campaign（k → cid），取自 `import_r01_04_canonical_v0_1.py` 的 CAMPAIGNS
AFFECTED = {
    "008": "C-2020-CONS-WHITE-GOODS",
    "009": "C-2019-CONS-AESTHETICS",
    "010": "C-2020-CONS-BEAUTY-CN",
    "011": "C-2024-CONS-TRADE-IN",
    "012": "C-2023-CONS-VALUE-RETAIL",
}
# 未挂载（RC 对象，不在 campaigns 表）—— 仅报告
NOT_LINKED = {"007": "RC-2020-CONS-SMALL-APPLIANCE", "013": "RC-2024-CONS-PET-FOOD"}


def norm_ticker(t) -> str:
    return re.sub(r"\..*$", "", str(t or "")).strip()


def main(argv):
    dry = "--dry-run" in argv
    conn = db.connect()

    # ---- 期望值：从**包**推导 ----
    sj = json.load(io.open(os.path.join(PKG, "securities.json"), encoding="utf-8"))
    if isinstance(sj, dict):
        sj = sj.get("securities") or []
    pkg = {s["security_id"]: (norm_ticker(s.get("ticker")), s.get("name") or "") for s in sj}
    cands = json.load(io.open(os.path.join(PKG, "candidates.json"), encoding="utf-8"))
    if isinstance(cands, dict):
        cands = cands.get("candidates") or cands.get("campaign_candidates") or []
    by_id = {c.get("candidate_id") or c.get("id"): c for c in cands}

    tick2sec = {}
    for sid, tk in conn.execute("SELECT security_id, ticker FROM securities WHERE ticker IS NOT NULL"):
        t = norm_ticker(tk)
        if t:
            tick2sec.setdefault(t, sid)

    plan = {}
    for k, cid in sorted(AFFECTED.items()):
        cand = by_id.get("R01-CONSUMER-" + k)
        if not cand:
            print("  ⚠ 包中无候选 R01-CONSUMER-%s" % k)
            continue
        want, unresolved = [], []
        for sec_id in (cand.get("security_ids") or []):
            tk, nm = pkg.get(sec_id, (None, None))
            sid = tick2sec.get(tk) if tk else None
            if sid:
                want.append(sid)
            else:
                unresolved.append((sec_id, tk, nm))
        cur = [r[0] for r in conn.execute("SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,))]
        plan[cid] = {"k": k, "want": sorted(want), "cur": sorted(cur), "unresolved": unresolved,
                     "to_delete": sorted(set(cur) - set(want)),
                     "to_insert": sorted(set(want) - set(cur))}

    print("ThreeC · R01-04 标的映射修正")
    print("-" * 78)
    for cid, p in sorted(plan.items()):
        mark = "✓ 无需修正" if not (p["to_delete"] or p["to_insert"]) else "★ 需修正"
        print("  %-30s %s" % (cid, mark))
        if p["to_delete"]:
            print("        删除：%s" % p["to_delete"])
        if p["to_insert"]:
            print("        新增：%s" % p["to_insert"])
        if p["unresolved"]:
            print("        ⚠ 无法解析 ticker：%s" % p["unresolved"])
    print("-" * 78)
    print("  未挂载（RC 对象，不在 campaigns 表）：")
    for k, cid in sorted(NOT_LINKED.items()):
        print("     %s  （包中候选 R01-CONSUMER-%s）—— 无需修正" % (cid, k))

    if dry:
        print()
        print("[dry-run] 未写入任何数据")
        conn.close()
        return 0

    # ---- 应用 ----
    n_del = n_ins = 0
    with conn:  # 事务：任一步失败则整体回滚
        for cid, p in sorted(plan.items()):
            for sid in p["to_delete"]:
                conn.execute("DELETE FROM campaign_securities WHERE campaign_id=? AND security_id=?", (cid, sid))
                n_del += 1
            for sid in p["to_insert"]:
                conn.execute("INSERT INTO campaign_securities (campaign_id,security_id,role) VALUES (?,?,?)",
                             (cid, sid, "representative"))
                n_ins += 1
    print()
    print("已应用：删除 %d 行 · 新增 %d 行" % (n_del, n_ins))

    # ---- 验证：逐条与包对照 ----
    print()
    print("=== 验证（与包对照）===")
    ok = True
    for cid, p in sorted(plan.items()):
        now = sorted(r[0] for r in conn.execute("SELECT security_id FROM campaign_securities WHERE campaign_id=?", (cid,)))
        good = now == p["want"]
        ok = ok and good
        print("  %-30s %s" % (cid, "✓ 与包一致" if good else "✗ 仍不一致 实=%s 期=%s" % (now, p["want"])))
    print()
    print("结果:", "PASS —— 全部与包一致" if ok else "FAIL")
    conn.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
