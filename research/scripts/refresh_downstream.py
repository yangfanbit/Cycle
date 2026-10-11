#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""refresh_downstream.py —— **canonical 变更后，一次跑完所有下游 + 一致性自检**。

## 为什么需要它（2026-10-11 实测，R02-03 那轮踩出来的）

canonical DB 变更后，下游是一条**多层嵌入投影**的链：

```
DB（canonical）
  → ① lifecycle / drivers   build_lifecycle_from_intake_v0_2.py
  → ② canonical export      batch_auto_research.py
  → ③ SA research           build_structural_analogy_research_v0_N.py
  → ④ SA explanations       build_structural_analogy_explanation_v0_N.py（产品消费）
  → ⑤ 快照 candidates 投影    project_sa_to_candidates_v0_N.py
  → ⑥ 快照 objects 投影       project_cc_to_objects_v0_1.py
  → ⑦ Market Snapshot       build_market_snapshot_v0_1.py
  → ⑧ 产品侧                structuralAnalogy.ts / buildProvenance.ts / themeColors.ts / 计数断言
```

**每一层都嵌入了上游的投影**，所以 DB 一变，**每一层都要重跑**。
此前**全靠手工按序执行**，而**每一层都硬编码了上游版本** ——
R02-03 那一轮我在**三处**各踩一次：

| # | 坑 | 后果 | 是否有报错 |
|---|---|---|---|
| 1 | `batch_auto_research.RULES` 白名单**漏登记新 rule** | 导出**静默少 2 条 Campaign**（57 → 55） | ❌ 无 |
| 2 | 产品侧 **7 处**硬编码 `explanations_v0_10`（含 `buildProvenance.ts`） | 产品仍读旧 SA | ❌ 无 |
| 3 | 投影器 `SA_ARTIFACT_REL` 硬编码 v0_10 | 快照回指旧 SA | ❌ 无 |

**三个坑的共同点：不报错。** 所以本脚本的重点**不是「按序跑」**，
而是**「跑之前先把这三类不一致查出来」**。

## 用法

    python research/scripts/refresh_downstream.py --check    # 只做前置自检（不写任何文件）
    python research/scripts/refresh_downstream.py --apply    # 按序跑 + 跑后自检

★ `--check` 是**只读**的，应作为每次 DB 变更后的**第一件事**。
★ 版本号**自动发现**（扫 reports 目录取最大 N），不硬编码 —— 从根上避免坑 2/3。

## 边界

- **不写 DB**（DB 由 canonicalization 脚本写）· 不改 `schema.sql` / `contracts/`
- **不签发快照**（快照以 DRAFT 生成；CANONICAL 需人工 `--reviewer`）
- 不改任何**旧版本** artifact（升版 = 新版写新文件）
"""

import argparse
import glob
import io
import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DB = os.path.join(ROOT, "research", "database", "cycle_research.db")
REPORTS = os.path.join(ROOT, "research", "research", "reports")
SNAPDIR = os.path.join(ROOT, "research", "current", "market_snapshots")
EXPORT = os.path.join(ROOT, "exports", "timeline_export_v1.json")

OK, FAIL, WARN = "PASS", "FAIL", "WARN"
_results = []


def rep(level, code, msg):
    _results.append((level, code, msg))
    print("  %-4s %-6s %s" % (level, code, msg))


def read(p):
    with io.open(p, encoding="utf-8") as fh:
        return fh.read()


def load(p):
    return json.loads(read(p))


def latest_version(pattern, group=1):
    """扫目录取最大版本号（**不硬编码**）。"""
    best = None
    for p in glob.glob(pattern):
        m = re.search(r"_v0_(\d+)\.json$", os.path.basename(p))
        if m:
            n = int(m.group(1))
            if best is None or n > best[0]:
                best = (n, p)
    return best  # (n, path) 或 None


def db_object_ids():
    import sqlite3
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT campaign_id FROM campaigns")
    c = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT campaign_id FROM campaigns WHERE campaign_id LIKE 'RC-%'")
    rc = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT DISTINCT rule_id FROM campaigns WHERE rule_id IS NOT NULL")
    rules = sorted(r[0] for r in cur.fetchall())
    cur.execute("SELECT name FROM themes WHERE parent_theme_id IS NULL")
    roots = sorted(r[0] for r in cur.fetchall())
    conn.close()
    return c, rc, rules, roots


# ================================================================ 前置自检（只读）

def preflight():
    print("=" * 78)
    print("① 前置自检（只读）—— 目的是**在跑之前**发现三类「不报错」的不一致")
    print("=" * 78)

    camp, rcs_db, db_rules, db_roots = db_object_ids()
    # ★ 基线取自 **export**（= 产品看到的世界）：
    #   DB `campaigns` 表只有 Campaign；**RC 来自 intake 包**，不在该表里。
    exp0 = load(EXPORT)
    camp = [c["campaign_id"] for c in exp0["campaigns"]]
    rcs = [c["campaign_id"] for c in exp0["research_candidates"]]
    n_objects = len(camp) + len(rcs)
    print("  DB: Campaign(表)=%d · rule=%d · 根主题=%d" % (len(camp), len(db_rules), len(db_roots)))
    print("  export 基线: Campaign=%d · RC=%d · 对象合计=**%d**" % (len(camp), len(rcs), n_objects))
    print()

    # ---- 坑 1：export 的 RULES 白名单是否覆盖 DB 的全部 rule ----
    src = read(os.path.join(SCRIPT_DIR, "batch_auto_research.py"))
    m = re.search(r"^RULES\s*=\s*\[(.*?)\]", src, re.S | re.M)
    listed = set(re.findall(r'"([a-z_]+)"', m.group(1))) if m else set()
    # RULES 里写的是常量名，展开成 rule_id
    for name, val in re.findall(r'^([A-Z_]+_RULE)\s*=\s*"([a-z_]+)"', src, re.M):
        pass
    consts = dict(re.findall(r'^([A-Z_]+_RULE)\s*=\s*"([a-z_]+)"', src, re.M))
    covered = {consts.get(t, t) for t in re.findall(r"\b([A-Z_]+_RULE)\b", m.group(1))} if m else set()
    missing = [r for r in db_rules if r not in covered]
    if missing:
        rep(FAIL, "C1", "batch_auto_research.RULES **未覆盖** DB 的 rule：%s → "
                        "导出会**静默丢**这些族的 Campaign（不报错）。请在 RULES 登记。" % missing)
    else:
        rep(OK, "C1", "batch_auto_research.RULES 覆盖 DB 全部 %d 个 rule" % len(db_rules))

    # ---- 坑 2：产品侧 / 投影器 引用的 SA 版本 vs 最新 SA 产物 ----
    latest = latest_version(os.path.join(REPORTS, "structural_analogy_explanations_v0_*.json"))
    if not latest:
        rep(FAIL, "C2", "找不到 SA explanation 产物")
        return n_objects, None, None
    n, sa_path = latest
    want = "structural_analogy_explanations_v0_%d.json" % n
    print()
    print("  最新 SA explanation 产物：v0_%d（%s）" % (n, os.path.basename(sa_path)))

    refs = [
        ("src/data/timeline/structuralAnalogy.ts", "产品 SA 加载"),
        ("src/data/buildProvenance.ts", "产品 provenance 页脚"),
        ("research/current/market_snapshots/scripts/project_sa_to_candidates_v0_%d.py" % (n + 1), None),
    ]
    # 全局扫 src/** 的 SA 版本引用（含测试）—— 坑 2 的教训：**必须全局搜**
    bad = []
    for p in glob.glob(os.path.join(ROOT, "src", "**", "*.ts"), recursive=True) + \
             glob.glob(os.path.join(ROOT, "src", "**", "*.tsx"), recursive=True):
        for m2 in re.finditer(r"structural_analogy_explanations_v0_(\d+)\.json", read(p)):
            if int(m2.group(1)) != n:   # ★ 按**版本号**比较（原先拿短名比全名，永远不等 → 误报）
                bad.append("%s → v0_%s" % (os.path.relpath(p, ROOT), m2.group(1)))
    if bad:
        rep(FAIL, "C2", "产品/测试仍引用**旧** SA 版本（应为 %s）：\n         %s" % (want, "\n         ".join(bad)))
    else:
        rep(OK, "C2", "产品/测试的 SA 版本引用全部指向 %s" % want)

    # ---- 坑 3：投影器 SA_ARTIFACT_REL ----
    projs = sorted(glob.glob(os.path.join(SNAPDIR, "scripts", "project_sa_to_candidates_v0_*.py")))
    if projs:
        latest_proj = projs[-1]
        rel = re.search(r'SA_ARTIFACT_REL\s*=\s*"([^"]+)"', read(latest_proj))
        got = rel.group(1) if rel else ""
        if got != "research/research/reports/" + want:
            rep(FAIL, "C3", "投影器 %s 的 SA_ARTIFACT_REL 指向 %s（应为 %s）→ 需新建 v0_%d"
                % (os.path.basename(latest_proj), got, want, n + 1))
        else:
            rep(OK, "C3", "投影器 %s 指向最新 SA" % os.path.basename(latest_proj))

    # ---- 坑 4（本轮新发现）：产品主题配色表 vs DB 根主题 ----
    tc = read(os.path.join(ROOT, "src", "components", "SeasonalMap", "themeColors.ts"))
    block = re.search(r"THEME_COLOR[^{]*\{(.*?)\n\};", tc, re.S)
    keys = set(re.findall(r"^\s*'?([^':\n]+)'?:\s*'#", block.group(1), re.M)) if block else set()
    keys = {k.strip().strip("'") for k in keys}
    miss_c = [r for r in db_roots if r not in keys]
    extra_c = sorted(keys - set(db_roots))
    if miss_c:
        rep(FAIL, "C4", "themeColors.THEME_COLOR **缺** DB 根主题 %s → 这些行会渲染成"
                        "**与「未标注」相同的灰色**（不报错）" % miss_c)
    elif extra_c:
        rep(WARN, "C4", "THEME_COLOR 有多余键（DB 已无此根主题）：%s" % extra_c)
    else:
        rep(OK, "C4", "themeColors 与 DB 的 %d 个根主题一一对应" % len(db_roots))

    # ---- 坑 5：lifecycle artifact 是否覆盖全部 DB 对象（或已在 INTAKE_MAP）----
    lfi = os.path.join(REPORTS, "lifecycle_from_intake_v0_2.json")
    if os.path.isfile(lfi):
        doc = load(lfi)
        by = set(doc.get("by_cycle") or {})
        covered_ids = set(by) | set(doc.get("drivers_by_cycle") or {})
        # ★ 早期对象（无 intake 包）的 lifecycle 来自 batch_auto_research 的**静态字典**，
        #   那些是合法的 —— 把它们也算作「已覆盖」，否则会误报。
        basrc = read(os.path.join(SCRIPT_DIR, "batch_auto_research.py"))
        covered_ids |= set(re.findall(r'"(C-[A-Z0-9\-]+|RC-[A-Z0-9\-]+)"\s*:', basrc))
        all_ids = set(camp) | set(rcs)
        not_covered = sorted(all_ids - covered_ids)
        if not_covered:
            rep(WARN, "C5", "以下对象在 lifecycle artifact 中**无 lifecycle/drivers**：\n"
                            "         %s\n         → 若它们是**新入库**的，请确认已在导入器里登记 "
                            "INTAKE_MAP；否则导出里 lifecycle 为空（不报错）。" % not_covered)
        else:
            rep(OK, "C5", "lifecycle artifact 覆盖全部 %d 个对象" % len(all_ids))

    # ---- 一致性基线（供跑后比对）----
    print()
    rep(OK, "C0", "一致性基线：对象数 = **%d**（= export.campaigns + export.research_candidates "
                  "= SA 每候选解释数 = 快照 historical_candidates / 候选数）" % n_objects)
    return n_objects, n, sa_path


# ================================================================ 跑后自检

def postflight(n_objects, sa_n):
    print()
    print("=" * 78)
    print("③ 跑后一致性自检（四层必须都等于 %d）" % n_objects)
    print("=" * 78)

    exp = load(EXPORT)
    got = len(exp["campaigns"]) + len(exp["research_candidates"])
    (rep(OK, "P1", "export 对象数 = %d" % got) if got == n_objects
     else rep(FAIL, "P1", "export 对象数 = %d，应为 %d" % (got, n_objects)))

    sa = load(os.path.join(REPORTS, "structural_analogy_explanations_v0_%d.json" % sa_n))
    per = {c.get("candidate_id"): len(c.get("explanations") or []) for c in (sa.get("candidates") or [])}
    bad = {k: v for k, v in per.items() if v != n_objects}
    (rep(OK, "P2", "SA 每候选解释数 = %d（%d 个候选）" % (n_objects, len(per))) if not bad
     else rep(FAIL, "P2", "SA 每候选解释数不齐：%s（应为 %d）" % (bad, n_objects)))

    idx = load(os.path.join(SNAPDIR, "index.json"))
    latest = sorted(idx["snapshots"], key=lambda s: s["snapshot_date"])[-1]
    snap = load(os.path.join(SNAPDIR, "snapshots", latest["file"]))
    hc = snap.get("historical_candidates") or []
    n_cand = len(snap.get("research_objects") or []) or 1
    if hc and len(hc) % n_cand == 0 and len(hc) // n_cand == n_objects:
        rep(OK, "P3", "快照 %s：historical_candidates=%d / %d 候选 = %d"
            % (latest["snapshot_id"], len(hc), n_cand, n_objects))
    else:
        rep(FAIL, "P3", "快照 %s：historical_candidates=%d / %d 候选 ≠ %d"
            % (latest["snapshot_id"], len(hc), n_cand, n_objects))

    # 校验器
    for label, cmd in (
        ("validate_timeline_export", [sys.executable, "research/scripts/validate_timeline_export.py"]),
        ("validate_market_snapshot", [sys.executable,
                                      "research/current/market_snapshots/scripts/validate_market_snapshot_v0_1.py",
                                      os.path.join(SNAPDIR, "snapshots", latest["file"])]),
    ):
        try:
            r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            (rep(OK, "P4", "%s PASS" % label) if r.returncode == 0
             else rep(FAIL, "P4", "%s FAIL：%s" % (label, (r.stdout or "").strip().splitlines()[-1:])))
        except Exception as exc:  # noqa: BLE001
            rep(WARN, "P4", "%s 无法运行：%s" % (label, exc))


# ================================================================ 主流程

PIPELINE = [
    ("① lifecycle / drivers", ["research/scripts/build_lifecycle_from_intake_v0_2.py"]),
    ("② canonical export", ["research/scripts/batch_auto_research.py"]),
]


def main(argv):
    ap = argparse.ArgumentParser(description="canonical 变更后刷新全部下游 + 一致性自检")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="只做前置自检（只读）")
    g.add_argument("--apply", action="store_true", help="按序跑 + 跑后自检")
    args = ap.parse_args(argv)

    n_objects, sa_n, sa_path = preflight()
    if sa_n is None:
        return 1
    if args.check:
        print()
        print("--check：只读完成。请先修掉上面的 FAIL，再 --apply。")
        return 1 if any(l == FAIL for l, _, _ in _results) else 0

    # ---- ② 按序跑（版本自动发现，不硬编码）----
    print()
    print("=" * 78)
    print("② 按序刷新下游（版本自动发现）")
    print("=" * 78)
    sa_n_new = sa_n + 1
    steps = list(PIPELINE) + [
        ("③ SA research v0_%d" % sa_n_new,
         ["research/scripts/build_structural_analogy_research_v0_%d.py" % sa_n_new]),
        ("④ SA explanations v0_%d" % sa_n_new,
         ["research/scripts/build_structural_analogy_explanation_v0_%d.py" % sa_n_new]),
    ]
    for label, cmd in steps:
        path = os.path.join(ROOT, cmd[0])
        if not os.path.isfile(path):
            rep(FAIL, "R", "%s：脚本不存在 %s（升版时需先新建该版本脚本）" % (label, cmd[0]))
            return 1
        r = subprocess.run([sys.executable] + cmd, cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout or "").strip().splitlines()[-1:]
        (rep(OK, "R", "%s 完成%s" % (label, ("：%s" % tail[0]) if tail else "")) if r.returncode == 0
         else rep(FAIL, "R", "%s 失败：%s" % (label, (r.stderr or "").strip()[-200:])))
        if r.returncode != 0:
            return 1

    print()
    rep(WARN, "R", "⑤⑥⑦ 快照链**未自动执行** —— 它需要 --regime / --observations 两个输入，"
                   "且新快照应以 **DRAFT** 生成、由人工签发。请见 "
                   "`docs/` 或 memory 中记录的四步命令。")
    rep(WARN, "R", "⑧ 产品侧：若 SA 升版，需全局替换 `explanations_v0_N` 引用（含测试）"
                   "并更新计数断言 —— 本脚本已用 C2 检查该一致性。")

    postflight(n_objects, sa_n_new)
    print()
    print("结论：%s" % ("PASS" if not any(l == FAIL for l, _, _ in _results) else "FAIL"))
    return 0 if not any(l == FAIL for l, _, _ in _results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
