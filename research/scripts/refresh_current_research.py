"""refresh_current_research.py —— Current Research Refresh Loop v0.1 的**唯一入口**。

## 定位
ThreeC 的工作循环：

```
市场新信息 → 离线 Research → Current Candidate Snapshot → Product 静态消费 → 历史结构比较
```

**本脚本不做研究判断**（Collect / Normalize / Evidence / Candidate 由**离线研究**完成），
只负责**确定性的 Refresh 机械动作**：

```
旧 Snapshot → 新 Evidence（人工/离线产出）→ Candidate diff → 校验 → Snapshot 记录
```

## 硬约束
- **确定性**：无随机 · 无当前时间依赖 · **无网络** · 无 LLM。
- **不自动改写研究内容**：`current_candidates.json` 只在**显式** `--write-canonical` 时写入，
  且内容必须已由离线研究准备好。
- **Temporal Firewall 复用既有实现**（`validate_current_research.py`），**不重新实现**。
- **不复制大型冗余文件**：`snapshots/` 只保留 **manifest**（date / version / ids / hash / generated_at）。

## 用法
```
python research/scripts/refresh_current_research.py --check
python research/scripts/refresh_current_research.py --check --snapshot-date 2026-09-15
python research/scripts/refresh_current_research.py --diff --baseline <path.json>
python research/scripts/refresh_current_research.py --check --record
```

## 退出码
0 = 通过；1 = 失败。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

# 复用既有验证器（**不重新实现 Temporal Firewall / schema / namespace 校验**）
import validate_current_research as VCR  # noqa: E402

CANONICAL = os.path.join(ROOT, "research", "current", "current_candidates.json")
SNAPSHOTS_DIR = os.path.join(ROOT, "research", "current", "snapshots")
MANIFEST = os.path.join(SNAPSHOTS_DIR, "manifest.json")

# Candidate 状态（**不新增状态**）
CANDIDATE_STATUSES = ["CANDIDATE", "WATCH", "RESEARCHING", "PROMOTABLE", "REJECTED"]
# 生命周期阶段（**不新增阶段模型**）
PHASES = ["EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "EXPANSION",
          "PEAK", "DECLINE", "UNKNOWN"]
# 命名空间：Current Candidate 必须为 CC-*
CANDIDATE_NS = "CC-"
# 历史命名空间：禁止出现在 candidates[] 中
FORBIDDEN_NS = ("C-", "RC-")


# ---------------------------------------------------------------- 工具

def load_json(path: str):
    with io.open(path, encoding="utf-8") as f:
        return json.load(f)


def canonical_bytes(path: str) -> bytes:
    """规范字节：排序键 + 固定分隔 + 无尾随空白 —— 用于**确定性 hash**。"""
    data = load_json(path)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_of(path: str) -> str:
    return hashlib.sha256(canonical_bytes(path)).hexdigest()


def candidate_fingerprint(c: dict) -> str:
    """单候选内容指纹（用于 UPDATED / UNCHANGED 判定）。"""
    payload = json.dumps(c, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def evidence_dates(c: dict) -> list[str]:
    out = []
    for e in c.get("evidence") or []:
        for k in ("event_date", "source_date"):
            v = e.get(k)
            if isinstance(v, str) and v:
                out.append(v)
    return out


# ---------------------------------------------------------------- Contract 校验

def check_contract(doc: dict) -> list[str]:
    """Refresh Contract：字段语义与必需项（§四 / §七 / §八 / §九）。"""
    errs: list[str] = []
    for k in ("snapshot_date", "generated_at", "research_coverage_until",
              "current_candidates_version"):
        if not doc.get(k):
            errs.append(f"缺少必需字段 {k}")

    snap = doc.get("snapshot_date")
    gen = doc.get("generated_at")
    if snap and gen and gen[:10] < snap:
        errs.append(f"generated_at({gen}) 早于 snapshot_date({snap})")

    cov = doc.get("research_coverage_until")
    if isinstance(cov, int) and snap and int(snap[:4]) <= cov:
        errs.append(f"snapshot_date({snap}) 不晚于 research_coverage_until({cov})")

    seen: set[str] = set()
    for c in doc.get("candidates") or []:
        cid = c.get("candidate_id", "")
        if not cid.startswith(CANDIDATE_NS):
            errs.append(f"命名空间错误：{cid} 必须以 {CANDIDATE_NS} 开头")
        if any(cid.startswith(p) and not cid.startswith(CANDIDATE_NS) for p in FORBIDDEN_NS):
            errs.append(f"禁止历史命名空间：{cid}")
        if cid in seen:
            errs.append(f"重复 candidate_id：{cid}")
        seen.add(cid)

        st = c.get("candidate_status")
        if st and st not in CANDIDATE_STATUSES:
            errs.append(f"{cid} 非法 candidate_status：{st}")
        ph = c.get("attention_state")
        if ph and ph not in PHASES:
            errs.append(f"{cid} 非法 attention_state：{ph}")

        lu = c.get("last_updated")
        if lu and snap and lu > snap:
            errs.append(f"{cid} last_updated({lu}) 晚于 snapshot_date({snap})")

        for d in evidence_dates(c):
            if snap and d > snap:
                errs.append(f"{cid} evidence 日期 {d} 超过 snapshot_date({snap}) —— Temporal Firewall 违规")

    return errs


# ---------------------------------------------------------------- Candidate Diff

def diff_snapshots(old: dict, new: dict) -> dict:
    """旧 Snapshot → 新 Snapshot 的候选差异（**确定性**）。

    NEW / UPDATED / UNCHANGED / REJECTED 可机械判定；
    **MERGED 不可机械判定** —— 按 §十 记录 limitation，不擅自扩展状态机。
    """
    a = {c["candidate_id"]: c for c in old.get("candidates") or []}
    b = {c["candidate_id"]: c for c in new.get("candidates") or []}

    new_ids, updated, unchanged, rejected = [], [], [], []
    for cid, c in b.items():
        if cid not in a:
            new_ids.append(cid)
            continue
        if c.get("candidate_status") == "REJECTED":
            rejected.append(cid)
            continue
        if candidate_fingerprint(a[cid]) == candidate_fingerprint(c):
            unchanged.append(cid)
        else:
            updated.append(cid)
    for cid, c in a.items():
        if cid not in b and c.get("candidate_status") != "REJECTED":
            rejected.append(cid)

    return {
        "baseline_snapshot_date": old.get("snapshot_date"),
        "target_snapshot_date": new.get("snapshot_date"),
        "baseline_version": old.get("current_candidates_version"),
        "target_version": new.get("current_candidates_version"),
        "counts": {
            "NEW": len(new_ids), "UPDATED": len(updated), "UNCHANGED": len(unchanged),
            "REJECTED": len(rejected), "MERGED": 0,
        },
        "NEW": sorted(new_ids),
        "UPDATED": sorted(updated),
        "UNCHANGED": sorted(unchanged),
        "REJECTED": sorted(rejected),
        "MERGED": [],
        "merged_limitation": (
            "MERGED（两个 Candidate 被研究判断为同一对象）**无法由数据结构机械判定** —— "
            "需要离线研究显式声明。本轮按 §十 记录为 limitation，**不扩展状态机**。"
        ),
        "stable": (not new_ids and not updated and not rejected
                   and old.get("snapshot_date") == new.get("snapshot_date")),
    }


# ---------------------------------------------------------------- Snapshot manifest

def load_manifest() -> dict:
    if os.path.exists(MANIFEST):
        return load_json(MANIFEST)
    return {"artifact": "current_research_snapshot_manifest", "artifact_version": "0.1",
            "note": "只记录 snapshot 元信息（date / version / ids / hash / generated_at）；**不复制大型冗余文件**。",
            "snapshots": []}


def record_snapshot(doc: dict, path: str, *, write: bool) -> dict:
    """把当前 canonical snapshot 的**元信息**登记进 manifest（幂等）。"""
    m = load_manifest()
    entry = {
        "snapshot_date": doc.get("snapshot_date"),
        "version": doc.get("current_candidates_version"),
        "generated_at": doc.get("generated_at"),
        "candidate_ids": sorted(c["candidate_id"] for c in doc.get("candidates") or []),
        "candidate_count": len(doc.get("candidates") or []),
        "content_sha256": sha256_of(path),
        "source": os.path.relpath(path, ROOT).replace("\\", "/"),
    }
    existing = [s for s in m["snapshots"] if s.get("snapshot_date") == entry["snapshot_date"]
                and s.get("version") == entry["version"]]
    if existing:
        # 幂等：同一 (snapshot_date, version) 只保留一条；内容相同 → changed=False
        entry["changed_since_last_record"] = (
            existing[0].get("content_sha256") != entry["content_sha256"])
        m["snapshots"] = [x for x in m["snapshots"] if x is not existing[0]] + [entry]
    else:
        entry["changed_since_last_record"] = True
        m["snapshots"].append(entry)

    m["snapshots"] = sorted(m["snapshots"], key=lambda s: (s.get("snapshot_date") or "",
                                                          s.get("version") or ""))
    m["snapshot_count"] = len(m["snapshots"])

    if write:
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
        with io.open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(m, ensure_ascii=False, indent=1) + "\n")
    return m


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="refresh_current_research.py",
        description="ThreeC Current Research Refresh Loop v0.1（确定性 · 离线 · 不联网）")
    ap.add_argument("--check", action="store_true", help="校验 snapshot（默认动作）")
    ap.add_argument("--snapshot-date", default=None, metavar="YYYY-MM-DD",
                    help="期望的 snapshot_date（与 canonical 不一致则失败）")
    ap.add_argument("--diff", action="store_true", help="与 --baseline 做 Candidate diff")
    ap.add_argument("--baseline", default=None, help="用于 diff 的基线 snapshot 路径")
    ap.add_argument("--record", action="store_true",
                    help="把当前 snapshot 元信息登记进 snapshots/manifest.json（幂等）")
    ap.add_argument("--file", default=CANONICAL, help="待处理的 snapshot 路径")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    path = args.file if os.path.isabs(args.file) else os.path.join(ROOT, args.file)
    if not os.path.exists(path):
        print(f"FAIL —— 文件不存在：{path}")
        return 1

    doc = load_json(path)
    errs = check_contract(doc)

    # 复用既有 validator（schema / temporal firewall / theme boundary / similarity …）
    export_ids, export_starts, export_ok = VCR.load_export_ids()
    before = len(VCR.FAILS)
    VCR.validate_dataset(path, "canonical", export_ids, export_starts)
    vcr_fails = VCR.FAILS[before:]

    if args.snapshot_date and doc.get("snapshot_date") != args.snapshot_date:
        errs.append(f"snapshot_date 漂移：期望 {args.snapshot_date}，实际 {doc.get('snapshot_date')}")

    diff = None
    if args.diff or args.baseline:
        base_path = args.baseline or path
        base = load_json(base_path if os.path.isabs(base_path) else os.path.join(ROOT, base_path))
        diff = diff_snapshots(base, doc)

    manifest = record_snapshot(doc, path, write=args.record)

    ok = not errs and not vcr_fails
    if args.json:
        print(json.dumps({
            "path": os.path.relpath(path, ROOT).replace("\\", "/"),
            "snapshot_date": doc.get("snapshot_date"),
            "version": doc.get("current_candidates_version"),
            "candidate_count": len(doc.get("candidates") or []),
            "contract_errors": errs,
            "validator_failures": [m for _, m in vcr_fails],
            "diff": diff,
            "manifest_snapshot_count": manifest.get("snapshot_count", 0),
            "result": "PASS" if ok else "FAIL",
        }, ensure_ascii=False, indent=1))
        return 0 if ok else 1

    print("=" * 68)
    print("Current Research Refresh Loop v0.1")
    print("=" * 68)
    print(f"  snapshot      : {os.path.relpath(path, ROOT).replace(chr(92), '/')}")
    print(f"  snapshot_date : {doc.get('snapshot_date')}")
    print(f"  generated_at  : {doc.get('generated_at')}")
    print(f"  version       : {doc.get('current_candidates_version')}")
    print(f"  coverage_until: {doc.get('research_coverage_until')}")
    print(f"  candidates    : {len(doc.get('candidates') or [])}")
    print(f"  content sha256: {sha256_of(path)[:16]}…")
    print("-" * 68)
    print("  Refresh Contract 检查")
    if errs:
        for e in errs:
            print(f"    FAIL  {e}")
    else:
        print("    PASS  字段语义 / 命名空间 / 必需项 / 重复 ID / 日期一致性")
    print("  既有 validator（复用，未重复实现）")
    if vcr_fails:
        for _, m in vcr_fails:
            print(f"    FAIL  {m}")
    else:
        print("    PASS  schema / Temporal Firewall / Theme Boundary / Similarity / Evidence")
    if not export_ok:
        print("    WARN  exports/timeline_export_v1.json 缺失 → 只做内部一致性检查")
    if diff:
        print("-" * 68)
        print("  Candidate Diff")
        print(f"    baseline {diff['baseline_snapshot_date']} → target {diff['target_snapshot_date']}")
        for k in ("NEW", "UPDATED", "UNCHANGED", "REJECTED", "MERGED"):
            ids = diff[k]
            print(f"    {k:9s} {diff['counts'][k]:2d}  {', '.join(ids) if ids else '—'}")
        print(f"    stable    : {diff['stable']}")
        print(f"    limitation: {diff['merged_limitation']}")
    print("-" * 68)
    print(f"  snapshots 已登记: {manifest.get('snapshot_count', 0)}")
    print(f"结果: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
