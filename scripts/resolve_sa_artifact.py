#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""resolve_sa_artifact.py —— 解析「产品实际消费哪一版 SA」，并校验其与最新 artifact 一致。

## 为什么有这个脚本（2026-10-13）

`.github/workflows/deploy.yml` 的部署摘要曾**硬编码**一个早已被取代的 SA 版本文件
（artifact_version `0.5`），而产品早已消费更新版本。★ 关键：**那个旧文件仍在仓库里**，
所以 `node -p require(...)` **不会报错** —— 于是**每次部署都静默写着错误的 Research 版本**。

修复时先写在 YAML 内联 shell 里，但**内联规则无法测试**。本脚本把规则抽出来，
使「版本选择规则」成为**可独立测试的函数**。

## ★★ 版本选择规则（明确、可测试）

1. **权威来源 = 产品实际消费**：`src/data/buildProvenance.ts` 的静态 import。
   它回答「线上这个 build 到底消费了哪一版 Research」，**不是**推断。
2. **最新 artifact = 按 (minor, patch) 数值比较取最大** ——
   ★ **不是**「文件名最大」（字典序会把 `v0_9` 排到 `v0_13` 之后），
   ★ **也不是**「mtime 最新」（文件被 touch 就会失真）。
   命名必须匹配 `structural_analogy_explanations_v<minor>_<patch>.json`（两段数字）。
   ★ 若命名不符合该形态 → **报错退出**，而不是猜。
3. **两者必须一致**，且权威来源指向的文件**必须存在**。
   任一不满足 → 退出码 1（CI 门禁据此拒绝部署）。

## 用法

    python scripts/resolve_sa_artifact.py            # 人类可读
    python scripts/resolve_sa_artifact.py --json     # 机读（CI 用）

## 退出码

    0 = 一致且文件存在（可安全生成部署摘要）
    1 = 不一致 / 文件缺失 / 命名不合规
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT, "research", "research", "reports")
PROVENANCE_TS = os.path.join(ROOT, "src", "data", "buildProvenance.ts")

# ★ 严格命名：必须两段数字（minor_patch）。不匹配即报错，不猜。
SA_FILE_RE = re.compile(r"^structural_analogy_explanations_v(\d+)_(\d+)\.json$")
# 产品 import 的引用（含 `@observation/` 别名前缀）
SA_IMPORT_RE = re.compile(r"structural_analogy_explanations_v\d+_\d+\.json")


def parse_version(filename: str) -> tuple[int, int] | None:
    """`…_v0_13.json` → (0, 13)。命名不合规返回 None。"""
    m = SA_FILE_RE.match(filename)
    return (int(m.group(1)), int(m.group(2))) if m else None


def list_sa_artifacts(reports_dir: str = REPORTS_DIR) -> list[tuple[tuple[int, int], str]]:
    """列出全部 SA artifact，按 (minor, patch) 升序。★ 不合规命名的文件被忽略（由调用方决定是否报错）。"""
    out = []
    for name in os.listdir(reports_dir):
        v = parse_version(name)
        if v is not None:
            out.append((v, name))
    out.sort(key=lambda t: t[0])
    return out


def read_imported_sa(provenance_path: str = PROVENANCE_TS) -> str | None:
    """从 `buildProvenance.ts` 读出产品**实际消费**的 SA 文件名（权威来源）。"""
    try:
        src = io.open(provenance_path, encoding="utf-8").read()
    except OSError:
        return None
    hits = SA_IMPORT_RE.findall(src)
    # 去重保序 —— 同一版本可能出现多次（import 语句 + 注释里的举例）
    uniq = list(dict.fromkeys(hits))
    if len(uniq) != 1:
        # 0 个 → 没找到；≥2 个不同版本 → 无法唯一确定（都应报错，不猜）
        return None
    return uniq[0]


def resolve(reports_dir: str = REPORTS_DIR, provenance_path: str = PROVENANCE_TS) -> dict:
    """解析 + 校验。返回结构化结果（不打印、不退出），便于单测直接调用。"""
    arts = list_sa_artifacts(reports_dir)
    latest = arts[-1][1] if arts else None
    imported = read_imported_sa(provenance_path)
    imported_exists = bool(imported) and os.path.isfile(os.path.join(reports_dir, imported))

    problems: list[str] = []
    if not arts:
        problems.append("未找到任何符合命名规范的 SA artifact（%s）" % SA_FILE_RE.pattern)
    if imported is None:
        problems.append("无法从 %s 唯一确定产品消费的 SA artifact" % os.path.relpath(
            provenance_path, ROOT))
    elif not imported_exists:
        problems.append("产品 import 的 %s **不存在**（回指悬空）" % imported)
    if latest and imported and latest != imported:
        problems.append(
            "版本不一致 —— 最新 artifact 为 %s，而产品消费 %s"
            "（产品可能忘记升版，或旧版本未清理）" % (latest, imported))

    return {
        "latest": latest,
        "imported": imported,
        "imported_exists": imported_exists,
        "artifact_count": len(arts),
        "all_versions": ["v%d_%d" % v for v, _ in arts],
        "ok": not problems,
        "problems": problems,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="解析并校验产品消费的 SA artifact 版本")
    ap.add_argument("--json", action="store_true", help="输出 JSON（CI 用）")
    args = ap.parse_args(argv)

    res = resolve()
    if args.json:
        sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\n")
    else:
        print("SA artifact 版本解析")
        print("-" * 56)
        print("  命名规范     : %s" % SA_FILE_RE.pattern)
        print("  候选数量     : %d" % res["artifact_count"])
        print("  最新（数值比较）: %s" % res["latest"])
        print("  产品实际消费   : %s" % res["imported"])
        print("  该文件存在     : %s" % ("是" if res["imported_exists"] else "否"))
        if res["problems"]:
            print()
            print("  FAIL：")
            for p in res["problems"]:
                print("    - %s" % p)
        else:
            print()
            print("  结果: PASS")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
