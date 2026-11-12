#!/usr/bin/env python3
"""check_derived_chain_v0_1.py —— 周更派生链「声明 vs 实际」只读对账（v0.83）。

## 为什么存在
v0.81 主交付首跑 CI 变红，根因是 `build_candidate_ledger_v0_2.py --write`
把 `market_as_of` 推进到 11-06 后，`pattern_discovery_summary_v0_1.json`
里的 `ledger.sha256` 没同步 —— **下游声明的是上游当时的指纹，上游变了下游没重算**。
本地有 1.8 GB 大库时部分脚本会连带重算，容易漏掉，CI 无库才暴露。

本校验器把「谁依赖谁、重算顺序、声明在哪个字段」写进**代码可查的注册表**，
逐项对账「声明的 sha256 vs 实际文件 sha256」，并对重算顺序做有向无环断言。
只做只读核对，不写任何产物、不重算。

## 两类指纹必须分清（否则误报）
- `EXTERNAL`：声明的是**另一个文件**的 sha256（sha16 或 sha64）→ 逐项对账。
- `INTERNAL`：声明的是**自身 payload** 的摘要（雷达 view 的 `source_sha256_16`）→
  **显式 SKIP 并打印**，不是依赖，不对账。

## 边界
- 不读 `history_scan.db`（1.3 GB 未入库）；CI 与本地行为一致，无需 SKIP 降级。
- 产物缺失时**显式 SKIP 降级并打印范围**，不静默通过、不直接崩。
- ★ `cache_v0_1.json` 由本地抓数生成、**不入库**（`git ls-files` 无此文件），
  CI 干净 checkout 必然缺 → 登记为 `optional_missing`，该项跳过并打印范围，
  **其余 20 项声明仍逐项核对**。此规则是 v0.83 首跑 CI 变红后补的实测结论。
- 不新增 CI Job：由 `.github/workflows/deploy.yml` 现有只读门禁 step 调用。

用法：--check
"""
import argparse
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(ROOT, "research", "current")


def _sha(path, n=16):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:n]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ★★ 唯一真相：产物 → (重算序号, 上游声明检查规格)
# spec: (artifact 文件名, 声明字段路径, 指纹宽度, 类型, 文件所在目录)
#  类型 EXTERNAL_FILE: 声明值是 {文件名: sha} 或 单值；逐项核对实际文件
#  类型 EXTERNAL_SINGLE: 声明值是单个 sha，核对 spec 里指定的文件
# ★ 顺序按 docs/FRONTIER_CADENCE_v0_1.md 的周更 SOP：雷达重抓 → 板块语义/日历 →
#   theme_market → frontier_board → 周更视图 → 主题挖掘；统计轨账本 → 摘要 → 评估基础。
#   上游 order 必须严格小于下游，否则「下游声明依赖一个后算的产物」即为倒置。
CHAIN = [
    {
        "artifact": "new_theme_radar_v0_10_view.json", "order": 1,
        # ★ 内部 payload 自证摘要，不是上游依赖；显式 SKIP
        "decl": {"kind": "INTERNAL", "path": ("source_sha256_16",),
                 "reason": "构建器对自身展示 payload 取 sha，用于确定性自检，不是上游指纹"},
    },
    {
        "artifact": "board_semantics_v0_1.json", "order": 2,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT, os.path.join(ROOT, "research", "data", "forward_scan")],
                 # ★ cache_v0_1.json 由本地抓数生成、不入库（git ls-files 无此文件）。
                 #   CI 干净 checkout 里必然缺失 → 显式 SKIP 并打印范围，不得静默通过或直接崩。
                 "optional_missing": ["cache_v0_1.json"]},
    },
    {
        "artifact": "event_calendar_v0_1.json", "order": 3,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT]},
    },
    {
        "artifact": "theme_market_v0_1.json", "order": 4,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT]},
    },
    {
        "artifact": "frontier_board_v0_1.json", "order": 5,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT]},
    },
    {
        "artifact": "weekly_research_v0_1.json", "order": 6,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT]},
    },
    {
        "artifact": "theme_discovery_v0_1.json", "order": 7,
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT]},
    },
    {
        "artifact": "candidate_ledger_v0_2.json", "order": 8,
        # 账本本身不声明上游指纹，但必须进顺序图：摘要依赖它（v0.81 CI 失败点）
        "decl": {"kind": "NO_DECL",
                 "reason": "账本由行情库结算生成，无 source_sha256_16 声明；仅参与顺序图"},
    },
    {
        "artifact": "pattern_discovery_summary_v0_1.json", "order": 9,
        "decl": [
            {"kind": "EXTERNAL_SINGLE", "path": ("source", "sha256"), "width": 64,
             "file_key": ("source", "file"),
             "reason": "完整季节性产物指纹"},
            # ★ v0.81 CI 失败点：账本推进后必须同步
            {"kind": "EXTERNAL_SINGLE", "path": ("ledger", "sha256"), "width": 64,
             "file_key": ("ledger", "file"),
             "reason": "候选账本指纹（账本 --write 后必须重算摘要）"},
        ],
    },
    {
        "artifact": "workbench_eval_basis_v0_1.json", "order": 10,
        "decl": {"kind": "EXTERNAL_SINGLE", "path": ("source", "sha256_16"), "width": 16,
                 "file_key": ("source", "file"),
                 "reason": "评估基础数据引用的完整季节性产物指纹"},
    },
    {
        "artifact": "historical_replay_v0_1.json", "order": 11,
        # ★ v0.84：独立研究产物（非周更派生链），但声明了上游门槛与设计文档指纹；
        #   设计文档在 docs/ 下，需加入 search 才能对账「改口径必被抓到」。
        "decl": {"kind": "EXTERNAL_FILE", "path": ("source_sha256_16",), "width": 16,
                 "search": [CURRENT, os.path.join(ROOT, "docs")],
                 "optional_missing": []},
    },
]


def _dig(obj, path):
    for k in path:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def _resolve(fname, search_dirs):
    """文件名可能在 research/current/ 之外（如 cache_v0_1.json 在 forward_scan/）。"""
    if os.path.isabs(fname) and os.path.exists(fname):
        return fname
    for d in search_dirs:
        p = os.path.join(d, os.path.basename(fname))
        if os.path.exists(p):
            return p
    p = os.path.join(ROOT, fname)
    return p if os.path.exists(p) else None


def check():
    errs, skips, checked = [], [], 0
    present = {}
    for node in CHAIN:
        art = node["artifact"]
        p = os.path.join(CURRENT, art)
        if not os.path.exists(p):
            skips.append("%s 缺失（本环境未产出）" % art)
            continue
        present[art] = node
        doc = _load(p)
        specs = node["decl"] if isinstance(node["decl"], list) else [node["decl"]]
        for spec in specs:
            kind = spec["kind"]
            if kind in ("INTERNAL", "NO_DECL"):
                val = _dig(doc, spec["path"]) if spec.get("path") else None
                skips.append("%s 的 %s %s"
                             % (art, ".".join(spec["path"]) if spec.get("path") else "无声明字段",
                                spec["reason"]))
                if kind == "INTERNAL" and val is None:
                    errs.append("%s 缺内部自证摘要 %s" % (art, ".".join(spec["path"])))
                continue
            val = _dig(doc, spec["path"])
            if val is None:
                errs.append("%s 缺声明字段 %s" % (art, ".".join(spec["path"])))
                continue
            if kind == "EXTERNAL_FILE":
                if not isinstance(val, dict):
                    errs.append("%s 的 %s 应为 {文件名: sha}，实为 %s"
                                % (art, ".".join(spec["path"]), type(val).__name__))
                    continue
                for fname, declared in sorted(val.items()):
                    target = _resolve(fname, spec["search"])
                    if not target:
                        if fname in spec.get("optional_missing", ()):
                            skips.append("%s 的可选上游 %s 未入库（CI 干净 checkout 必然缺失），"
                                         "该项指纹不计入核对；其余声明照常校验"
                                         % (art, fname))
                        else:
                            errs.append("%s 声明的上游文件找不到：%s" % (art, fname))
                        continue
                    actual = _sha(target, spec["width"])
                    checked += 1
                    if actual != declared:
                        errs.append("%s 上游指纹漂移：%s 声明 %s / 实际 %s"
                                    "（上游重算后需按 SOP 顺序重算本产物）"
                                    % (art, fname, declared, actual))
            elif kind == "EXTERNAL_SINGLE":
                fname = _dig(doc, spec["file_key"])
                if not fname:
                    errs.append("%s 缺上游文件名 %s" % (art, ".".join(spec["file_key"])))
                    continue
                target = _resolve(fname, [CURRENT, os.path.dirname(p)])
                if not target:
                    errs.append("%s 声明的上游文件找不到：%s" % (art, fname))
                    continue
                actual = _sha(target, spec["width"])
                checked += 1
                if actual != str(val):
                    errs.append("%s 上游指纹漂移：%s 声明 %s / 实际 %s（%s）"
                                % (art, os.path.basename(str(fname)), str(val)[:16],
                                   actual[:16], spec["reason"]))

    # ★ 重算顺序有向无环：被声明为上游的「同链产物」序号必须更小
    for art, node in present.items():
        doc = _load(os.path.join(CURRENT, art))
        specs = node["decl"] if isinstance(node["decl"], list) else [node["decl"]]
        upstreams = []
        for spec in specs:
            if spec["kind"] == "EXTERNAL_FILE":
                val = _dig(doc, spec["path"]) or {}
                if isinstance(val, dict):
                    upstreams.extend(val.keys())
            elif spec["kind"] == "EXTERNAL_SINGLE":
                v = _dig(doc, spec["file_key"])
                if v:
                    upstreams.append(str(v))
        for fname in upstreams:
            base = os.path.basename(fname)
            if base in present and present[base]["order"] >= node["order"]:
                errs.append("重算顺序倒置：%s(order=%d) 声明依赖 %s(order=%d)"
                            % (art, node["order"], base, present[base]["order"]))

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL · 已核对 %d 项上游指纹" % (len(errs), checked))
        return 1
    scope = ("周更派生链声明化：%d 个产物 / %d 项上游指纹 / 重算顺序 DAG / 内部自证摘要区分"
             % (len(present), checked))
    if skips:
        scope += "（SKIP：%s）" % "；".join(skips)
    print("--check PASS · 范围：%s" % scope)
    print("顺序：%s" % " → ".join(
        "%d:%s" % (n["order"], a) for a, n in sorted(present.items(),
                                                     key=lambda kv: kv[1]["order"])))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.parse_args()
    return check()


if __name__ == "__main__":
    sys.exit(check())
