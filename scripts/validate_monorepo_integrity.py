"""validate_monorepo_integrity.py —— ThreeC Monorepo 完整性校验。

校验 Monorepo Integration 是否达成全部结构 / 数据流 / 边界要求。
不修改任何数据；仅检查。

用法（在仓库根执行）:
    python scripts/validate_monorepo_integrity.py

退出码: 0 = 全部通过；1 = 存在 FAIL。

对应 MONOREPO 迁移要求（15 项）：
  1. 只有一个 .git
  2. origin 正确
  3. research/ 存在
  4. exports/ 存在
  5. canonical export 唯一
  6. research database 存在
  7. schema 存在
  8. AGENTS 存在（根 + research）
  9. PROJECT_STATE 存在
 10. PRODUCT_PURPOSE 存在
 11. Contract 存在
 12. Research → Export → Cycle 路径完整
 13. 没有旧 Cycle-Research 根副本
 14. 没有 duplicate timeline_export_v1
 15. 没有误删研究目录
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILS = []
WARNS = []
PASSES = []


def ok(item):
    PASSES.append(item)


def fail(item, msg):
    FAILS.append((item, msg))


def warn(item, msg):
    WARNS.append((item, msg))


def git(*args):
    try:
        r = subprocess.run(
            ["git"] + list(args),
            capture_output=True, text=True, cwd=ROOT,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:  # pragma: no cover
        return 1, "", str(e)


def find_all(name, skip_dirs=(".git", "node_modules", "dist")):
    """递归查找指定文件名，跳过 skip_dirs。返回相对路径列表。"""
    hits = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        if name in files:
            hits.append(os.path.relpath(os.path.join(base, name), ROOT).replace("\\", "/"))
    return sorted(hits)


# ---------------------------------------------------------------- 1. 只有一个 .git
def check_single_git():
    gits = []
    for base, dirs, files in os.walk(ROOT):
        if ".git" in dirs:
            rel = os.path.relpath(os.path.join(base, ".git"), ROOT).replace("\\", "/")
            gits.append(rel)
            dirs.remove(".git")
        if "node_modules" in dirs:
            dirs.remove("node_modules")
    if len(gits) == 1 and gits[0] == ".git":
        ok("1. 只有一个 .git（根 .git）")
    else:
        fail("1. .git 唯一性", f"发现多个或位置异常: {gits}")


# ---------------------------------------------------------------- 2. origin 正确
def check_origin():
    code, out, _ = git("remote", "-v")
    if code != 0:
        fail("2. origin", "无法读取 git remote")
        return
    expected = "github.com/yangfanbit/Cycle"
    if expected in out and "Cycle-Research" not in out:
        ok(f"2. origin 正确（{expected}，无 Cycle-Research 远程）")
    else:
        fail("2. origin", f"origin 不符合预期（应仅含 {expected}）:\n{out}")


# ---------------------------------------------------------------- 3/4/6/7/15. 目录存在
def check_paths():
    if os.path.isdir(os.path.join(ROOT, "research")):
        ok("3. research/ 存在")
    else:
        fail("3. research/", "目录缺失")

    if os.path.isdir(os.path.join(ROOT, "exports")):
        ok("4. exports/ 存在")
    else:
        fail("4. exports/", "目录缺失")

    db = os.path.join(ROOT, "research", "database", "cycle_research.db")
    if os.path.isfile(db):
        ok("6. research database 存在")
    else:
        fail("6. research database", f"缺失: {os.path.relpath(db, ROOT)}")

    schema = os.path.join(ROOT, "research", "schema", "schema.sql")
    if os.path.isfile(schema):
        ok("7. schema 存在")
    else:
        fail("7. schema", f"缺失: {os.path.relpath(schema, ROOT)}")

    # 15. 研究目录未被误删
    expect_dirs = [
        "research/research/annual",
        "research/research/batch",
        "research/research/c2",
        "research/research/methodology",
        "research/research/promotion",
        "research/research/summary",
        "research/scripts",
        "research/data/market/raw",
        "research/data/market/normalized",
    ]
    missing = [d for d in expect_dirs if not os.path.isdir(os.path.join(ROOT, d))]
    if not missing:
        ok("15. 研究目录完整（未误删）")
    else:
        fail("15. 研究目录完整性", f"缺失: {missing}")


# ---------------------------------------------------------------- 5/14. canonical export 唯一
def check_canonical_export():
    canonical = os.path.join(ROOT, "exports", "timeline_export_v1.json")
    if not os.path.isfile(canonical):
        fail("5. canonical export", "exports/timeline_export_v1.json 缺失")
        return
    copies = find_all("timeline_export_v1.json")
    if copies == ["exports/timeline_export_v1.json"]:
        ok("5. canonical export 唯一（exports/timeline_export_v1.json）")
        ok("14. 无 duplicate timeline_export_v1（仓库内仅一份）")
    else:
        fail("5/14. canonical export 唯一性",
             f"发现 {len(copies)} 份副本: {copies}")


# ---------------------------------------------------------------- 8/9/10/11. 文档存在
def check_docs():
    required = {
        "8. 根 AGENTS.md": "AGENTS.md",
        "8. research/AGENTS.md": "research/AGENTS.md",
        "9. PROJECT_STATE": "docs/PROJECT_STATE.md",
        "10. PRODUCT_PURPOSE": "docs/PRODUCT_PURPOSE.md",
        "11. Contract": "contracts/timeline_export_v1.md",
    }
    for label, rel in required.items():
        if os.path.isfile(os.path.join(ROOT, rel)):
            ok(f"{label} 存在")
        else:
            fail(label, f"缺失: {rel}")

    # README / ROADMAP / CHANGELOG
    for rel in ("README.md", "docs/ROADMAP.md", "docs/CHANGELOG.md"):
        if os.path.isfile(os.path.join(ROOT, rel)):
            ok(f"docs: {rel} 存在")
        else:
            warn(f"docs: {rel}", "缺失")


# ---------------------------------------------------------------- 12. 数据流完整
def check_dataflow():
    """Research（生成）→ exports（canonical）→ Cycle Adapter（消费）。"""
    gen = os.path.join(ROOT, "research", "scripts", "batch_auto_research.py")
    if not os.path.isfile(gen):
        fail("12. 数据流", "Research 生成脚本缺失: research/scripts/batch_auto_research.py")
        return

    # Research 生成脚本应指向 canonical 路径
    with open(gen, "r", encoding="utf-8") as f:
        src = f.read()
    if "db.TIMELINE_EXPORT_PATH" in src:
        ok("12a. Research 生成端指向 canonical（db.TIMELINE_EXPORT_PATH）")
    else:
        fail("12a. Research 生成端", "未使用 db.TIMELINE_EXPORT_PATH")

    adapter = os.path.join(ROOT, "src", "data", "timeline", "timelinePreview.ts")
    if not os.path.isfile(adapter):
        fail("12. 数据流", "Cycle Adapter 缺失: src/data/timeline/timelinePreview.ts")
        return
    with open(adapter, "r", encoding="utf-8") as f:
        asrc = f.read()
    if "@exports/timeline_export_v1.json" in asrc:
        ok("12b. Cycle 消费端指向 canonical（@exports/timeline_export_v1.json）")
    else:
        fail("12b. Cycle 消费端", "未通过 @exports alias 消费 canonical export")

    # Cycle 侧不得再引用旧的手工副本路径
    if "./data/timeline_export_v1.json" in asrc:
        fail("12c. Cycle 消费端", "仍引用已删除的手工副本路径")
    else:
        ok("12c. Cycle 消费端无残留手工副本引用")

    # Vite / tsconfig alias 存在
    vite = os.path.join(ROOT, "vite.config.ts")
    tsconfig = os.path.join(ROOT, "tsconfig.json")
    if os.path.isfile(vite) and "@exports" in open(vite, encoding="utf-8").read():
        ok("12d. Vite alias @exports 已配置")
    else:
        fail("12d. Vite alias", "vite.config.ts 缺少 @exports alias")
    if os.path.isfile(tsconfig) and "@exports/*" in open(tsconfig, encoding="utf-8").read():
        ok("12e. tsconfig paths @exports/* 已配置")
    else:
        fail("12e. tsconfig paths", "tsconfig.json 缺少 @exports/* paths")


# ---------------------------------------------------------------- 13. 无旧根副本
def check_no_legacy_roots():
    bad = []
    for name in ("Cycle", "Cycle-research", "Cycle-Research"):
        p = os.path.join(ROOT, name)
        if os.path.isdir(p):
            bad.append(name)
    if bad:
        fail("13. 无旧根副本", f"仍存在旧项目根目录: {bad}")
    else:
        ok("13. 无旧 Cycle / Cycle-Research 根副本")

    # 不能有内层 .git
    for name in ("Cycle", "Cycle-research", "research/Cycle-research"):
        p = os.path.join(ROOT, name, ".git")
        if os.path.exists(p):
            fail("13. 内层 .git", f"仍存在: {name}/.git")


# ---------------------------------------------------------------- Git 历史
def check_history():
    code, out, _ = git("rev-list", "--count", "HEAD")
    if code == 0:
        try:
            n = int(out)
            if n >= 39:
                ok(f"Git 历史：HEAD 含 {n} 个提交（≥ 11 Cycle + 28 Research）")
            else:
                warn("Git 历史", f"提交数偏少: {n}")
        except ValueError:
            warn("Git 历史", f"无法解析提交数: {out}")
    else:
        warn("Git 历史", "无法读取提交数（可能尚无提交）")

    # 原 Cycle-Research HEAD 必须可达
    code, _, _ = git("merge-base", "--is-ancestor",
                     "eadf06a1555b2c46817c543c3e8454d4326a5efb", "HEAD")
    if code == 0:
        ok("Git 历史：原 Cycle-Research HEAD（eadf06a）可达")
    else:
        code2, _, _ = git("rev-parse", "--verify", "HEAD")
        if code2 == 0:
            warn("Git 历史", "原 Cycle-Research HEAD 不可达（检查是否已被 squash）")


# ---------------------------------------------------------------- main
def main():
    print("=== validate_monorepo_integrity.py ===")
    print(f"ROOT = {ROOT}")
    print("-" * 60)

    check_single_git()
    check_origin()
    check_paths()
    check_canonical_export()
    check_docs()
    check_dataflow()
    check_no_legacy_roots()
    check_history()

    print(f"\nPASS ({len(PASSES)}):")
    for p in PASSES:
        print(f"  [OK] {p}")

    if WARNS:
        print(f"\nWARN ({len(WARNS)}):")
        for item, msg in WARNS:
            print(f"  [!!] {item}: {msg}")

    if FAILS:
        print(f"\nFAIL ({len(FAILS)}):")
        for item, msg in FAILS:
            print(f"  [XX] {item}: {msg}")
        print(f"\n结果: FAIL（{len(FAILS)} 项失败，{len(WARNS)} 项警告）")
        return 1

    print(f"\n结果: PASS（{len(PASSES)} 项通过，{len(WARNS)} 项警告）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
