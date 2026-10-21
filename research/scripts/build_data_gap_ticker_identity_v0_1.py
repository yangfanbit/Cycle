#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_data_gap_ticker_identity_v0_1.py —— 缺口 A 的**身份层**核验（v0.28，只读）。

## 为什么单独做这一层

`data_gap_audit_v0_1.json` 把 A 类 17 个「旧式标识」判为
**1 PROVISIONAL（YILING）+ 16 UNRESOLVED**，并指出根因是 **owner-scoped 注册表**。
本轮不改那个裁决，只补一件它没有单独做的事：**按 ticker + 交易所做身份核验**。

★ 为什么 ticker 可以、名称不行：ticker 在同一交易所内**唯一**，`002603` 只对应一家公司；
「名字相似」没有证明力（`AGENTS.md` 的既有纪律）。所以本脚本只认
**(ticker, exchange) 精确相等**，不做任何模糊匹配、不按题材推断归属。

## 输出三种结论（不合并、不改数据）

- `IDENTITY_VERIFIED_BY_TICKER`：注册表里存在**同一 ticker + 交易所**的记录
  → 身份可确定（并记录其 owner）。★ 这**只**确定身份，**不**建立 Campaign 归属。
- `OWNERSHIP_GAP`：ticker 在注册表里**完全不存在** → 该证券没有被任何导出对象引用。
  这是**归属覆盖缺口**，不是「证券不存在」，也不是「标识写错」。
- `AMBIGUOUS`：同一 ticker 命中多行且 owner 不同 → 需人工裁定（本轮实测 0 例）。

## 用法

    python research/scripts/build_data_gap_ticker_identity_v0_1.py --write
    python research/scripts/build_data_gap_ticker_identity_v0_1.py --check
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
REPORTS = os.path.join(REPO, "research", "research", "reports")
AUDIT = os.path.join(REPORTS, "data_gap_audit_v0_1.json")
EXPORT = os.path.join(REPO, "exports", "timeline_export_v1.json")
GENERATED_AT = "2026-10-21"


def build() -> dict:
    audit = json.load(open(AUDIT, encoding="utf-8"))
    items = audit["workflows"]["A_registry_miss"]["items"]
    reg = json.load(open(EXPORT, encoding="utf-8"))["securities"]
    by_ticker = {}
    for s in reg:
        by_ticker.setdefault((s.get("ticker"), s.get("exchange")), []).append(s)

    out = []
    tally = {"IDENTITY_VERIFIED_BY_TICKER": 0, "OWNERSHIP_GAP": 0, "AMBIGUOUS": 0}
    for it in items:
        key = (it.get("ticker"), it.get("exchange"))
        rows = by_ticker.get(key, [])
        owners = sorted({r.get("campaign_id") or r.get("research_candidate_id") for r in rows})
        ids = sorted({r.get("security_id") for r in rows})
        if not rows:
            verdict = "OWNERSHIP_GAP"
            next_step = ("需 Research 轮次按**同期报道 + 对象证券记录**决定它属于哪个对象；"
                         "本轮**不**建立归属。缺的具体证据：该证券与某对象的 `security_ids` "
                         "有据可查的交集（或该对象事件明确点名它）")
        elif len(ids) > 1:
            verdict = "AMBIGUOUS"
            next_step = "同一 ticker 命中多个 security_id → 需人工裁定哪个是规范 id"
        else:
            verdict = "IDENTITY_VERIFIED_BY_TICKER"
            next_step = ("身份已确定（ticker+交易所唯一）；**归属不变** —— "
                         "是否并入该对象仍须独立轮次裁定")
        tally[verdict] += 1
        out.append({
            "original_id": it["original_id"],
            "name": it.get("name"),
            "ticker": it.get("ticker"),
            "exchange": it.get("exchange"),
            "participant_rows": it.get("rows"),
            "prior_verdict": it.get("verdict") or it.get("classification"),
            "verdict": verdict,
            "registry_security_ids": ids,
            "registry_owners": owners,
            "evidence": ("(ticker, exchange) 精确相等" if rows else
                         "注册表无该 (ticker, exchange) —— 未被任何导出对象引用"),
            "next_step": next_step,
        })
    return {
        "artifact": "data_gap_ticker_identity",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_data_gap_ticker_identity_v0_1.py",
        "supersedes": None,
        "position": "★ 本产物只核验**身份**，不改 `data_gap_audit_v0_1.json` 的裁决、不写 DB / export / 题材文件",
        "method": {
            "key": "(ticker, exchange) 精确相等",
            "why_ticker": "ticker 在同一交易所内唯一；名称相似没有证明力",
            "not_doing": ["不按名称匹配", "不按题材推断归属", "不自动合并 YILING",
                          "不因身份确定而建立 Campaign 归属"],
        },
        "tally": tally,
        "items": out,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="缺口 A 的身份层核验（ticker 唯一键）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)
    doc = build()
    out = os.path.join(REPORTS, "data_gap_ticker_identity_v0_%d.json" % a.version)
    if a.check:
        if not os.path.exists(out):
            print("FAIL: 产物不存在：%s" % os.path.relpath(out, REPO))
            return 1
        cur = json.load(open(out, encoding="utf-8"))
        if cur.get("items") != doc["items"] or cur.get("tally") != doc["tally"]:
            print("FAIL: 产物与重新核验不一致（应重跑 --write 升版）")
            return 1
        print("PASS: 身份核验与产物一致：%s" % doc["tally"])
        return 0
    if not a.write:
        print("用法：--check 或 --write [--version N]")
        return 2
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    doc["artifact_version"] = "0.%d" % a.version
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("  %s" % doc["tally"])
    for it in doc["items"]:
        if it["verdict"] == "IDENTITY_VERIFIED_BY_TICKER":
            print("  ✓ %s → %s（owner %s）" % (it["original_id"], it["registry_security_ids"], it["registry_owners"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
