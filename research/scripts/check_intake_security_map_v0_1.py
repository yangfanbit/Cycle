#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_intake_security_map_v0_1.py —— 核对**导入器的标的映射**与 **intake 包自己的声明**。

## 它回答什么

`import_r01_0X_canonical_v0_1.py` 里有一张「intake security_id → canonical security_id / ticker」
的映射表。**如果它与包里的 `securities.json` 不一致，导入就会把错的标的挂到 campaign 上** ——
而且**不会有任何报错**：标的合法、日期合法、结构校验全过。

## ★ 为什么必须有这个检查（2026-10-08 实测）

`import_r01_04_canonical_v0_1.py` 的 `SEC_MAP` 相对包声明**循环错位了 16 个**
（SEC016–SEC031 整体旋转 3 位）。后果：

- `C-2020-CONS-WHITE-GOODS`（家用电器）被挂上 **医美三只 + 老板电器**，而不是美的/格力/海尔/老板电器
- `C-2020-CONS-BEAUTY-CN`（美妆）被挂上 **宠物食品 + 零食**
- 两条不同 campaign 的标的清单**完全相同**

**结构校验（`validate_db`）全程 PASS** —— 它查的是形状，不是「映射是否忠于包」。

## 判据

对每个 R01-0X 包：

| 结果 | 含义 |
|---|---|
| `MATCH` | 导入器映射与包声明**逐条一致**（ticker 归一化后比较） |
| `MISMATCH` | ★ 存在不一致 —— **导入会把错的标的挂上去** |
| `MERGED` | 包内多个 SEC 映射到同一 canonical 标的（**须有注释说明**，视为有意） |

## 用法

    python research/scripts/check_intake_security_map_v0_1.py
"""

from __future__ import annotations

import glob
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

ROOT = db.ROOT
REP = os.path.join(ROOT, "research", "reports")
OUT = os.path.join(REP, "intake_security_map_check_v0_1.json")


def norm_ticker(t) -> str:
    """去掉交易所后缀：`688981.SH` → `688981`。"""
    return re.sub(r"\..*$", "", str(t or "")).strip()


def package_map(pkg_dir):
    p = os.path.join(pkg_dir, "securities.json")
    if not os.path.exists(p):
        return {}
    sj = json.load(io.open(p, encoding="utf-8"))
    if isinstance(sj, dict):
        sj = sj.get("securities") or []
    return {s["security_id"]: (norm_ticker(s.get("ticker")), s.get("name") or "") for s in sj}


def importer_map(src: str, pkg_prefix: str):
    """两种形态都要认：
    ① `"R01-XXX-SEC0NN": ("ID","ticker","name","EX")`
    ② `"R01-XXX-SEC0NN": "CANONICAL_ID"`（R01-01 的写法）
    """
    out = {}
    # ★ ticker 位置可能是 `None`（指数类无 ticker）—— 必须一并认，否则会误报
    for sid, _idv, tk, nm in re.findall(
        r'"(R01-[A-Z]+-SEC\d+)":\s*\(\s*"([^"]*)"\s*,\s*(None|"[^"]*")\s*,\s*"([^"]*)"', src):
        out[sid] = {"ticker": norm_ticker(tk.strip('"') if tk != "None" else ""), "name": nm, "canonical": None}
    for sid, cid in re.findall(r'"(R01-[A-Z]+-SEC\d+)":\s*"([A-Z0-9_]+)"', src):
        out.setdefault(sid, {"ticker": None, "name": None, "canonical": cid})
    return out


def main():
    conn = db.connect()
    tick_of = {r[0]: norm_ticker(r[1]) for r in conn.execute("SELECT security_id, ticker FROM securities")}
    name_of = {r[0]: (r[1] or "") for r in conn.execute("SELECT security_id, name FROM securities")}

    results, tally = {}, {}
    for i in range(1, 7):
        tag = "R01-%02d" % i
        pkg = os.path.join(ROOT, "intake", "packages", tag)
        imps = sorted(glob.glob(os.path.join(ROOT, "scripts", "import_r01_0%d_canonical_v0_1.py" % i)))
        if not imps:
            results[tag] = {"package": tag, "verdict": "NO_IMPORTER"}
            tally["NO_IMPORTER"] = tally.get("NO_IMPORTER", 0) + 1
            continue
        src = io.open(imps[0], encoding="utf-8").read()
        pkgmap, impmap = package_map(pkg), importer_map(src, tag)

        rows, mismatch, merged = [], [], []
        for sid in sorted(set(pkgmap) | set(impmap)):
            pt, pn = pkgmap.get(sid, (None, None))
            e = impmap.get(sid)
            if e is None:
                rows.append({"security_id": sid, "package_ticker": pt, "package_name": pn,
                             "importer": None, "ok": False})
                mismatch.append(sid)
                continue
            # 导入器侧的 ticker：可能是直接给的，也可能给了 canonical id
            it = e["ticker"] if e["ticker"] else tick_of.get(e["canonical"] or "", "")
            inm = e["name"] if e["name"] else name_of.get(e["canonical"] or "", "")
            ok = (pt == it) or (pt is None and it is not None)   # 包缺 ticker 时只要导入器有值即视为通过
            rows.append({"security_id": sid, "package_ticker": pt, "package_name": pn,
                         "importer_ticker": it, "importer_name": inm, "ok": bool(ok)})
            if not ok:
                mismatch.append(sid)

        # 包内多 SEC → 同一 canonical（如 R01-01 的 SEC008/SEC017 拓斯达）→ 视为「有意合并」而非错
        seen = {}
        for sid, e in impmap.items():
            key = e["ticker"] or e["canonical"]
            if key:
                seen.setdefault(key, []).append(sid)
        for key, sids in seen.items():
            if len(sids) > 1:
                merged.append({"canonical": key, "intake_ids": sorted(sids)})

        verdict = "MATCH" if not mismatch else "MISMATCH"
        # ★ 全为「有意合并」造成的差异时降级为 MERGED
        if mismatch and merged and set(mismatch) <= {s for m in merged for s in m["intake_ids"]}:
            verdict = "MERGED"
        tally[verdict] = tally.get(verdict, 0) + 1
        results[tag] = {"package": tag, "importer": os.path.basename(imps[0]),
                        "package_count": len(pkgmap), "importer_count": len(impmap),
                        "verdict": verdict, "mismatched": mismatch, "merged": merged, "rows": rows}

    res = {
        "artifact": "intake_security_map_check",
        "artifact_version": "0.1",
        "generated_by": "research/scripts/check_intake_security_map_v0_1.py",
        "position": ("Research-only 只读检查 —— 核对**导入器的标的映射**与 **intake 包自己的声明**。"
                     "**不修改任何数据**。"),
        "why": ("2026-10-08 实测：`import_r01_04` 的 SEC_MAP 相对包声明循环错位 16 个，"
                "把错的标的挂到了 7 条对象上，而**结构校验全程 PASS** —— 它查形状，不查映射是否忠于包。"),
        "rules": {
            "ticker_normalization": "去交易所后缀后比较（包写 `688981.SH`，导入器写 `688981`，同一标的）",
            "verdicts": {
                "MATCH": "逐条一致",
                "MISMATCH": "★ 存在不一致 → 导入会把错的标的挂上去",
                "MERGED": "差异全部来自「包内多 SEC → 同一 canonical 标的」的有意合并",
                "NO_IMPORTER": "未找到该包的导入器",
            },
            "no_score": "本 artifact **不含** score / ranking / probability。",
        },
        "summary": tally,
        "by_package": results,
    }
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print("written", OUT)
    print("summary:", json.dumps(tally, ensure_ascii=False))
    print()
    for tag, r in sorted(results.items()):
        if r["verdict"] in ("MATCH", "MERGED"):
            print("  %-7s %-8s ✓" % (tag, r["verdict"]))
            continue
        print("  %-7s %-8s ★ 不一致 %d 个" % (tag, r["verdict"], len(r.get("mismatched") or [])))
        for sid in (r.get("mismatched") or [])[:8]:
            row = next(x for x in r["rows"] if x["security_id"] == sid)
            print("        %s  包=%-8s %-10s  导入器=%-8s %s" % (
                sid, row["package_ticker"], row["package_name"],
                row.get("importer_ticker") or row.get("canonical") or '—', row.get("importer_name") or ''))
        if len(r.get("mismatched") or []) > 8:
            print("        ... 另 %d 个" % (len(r["mismatched"]) - 8))
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
