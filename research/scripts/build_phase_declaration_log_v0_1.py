#!/usr/bin/env python3
"""build_phase_declaration_log_v0_1.py —— 阶段声明日志（v0.80）。

## 为什么需要它
`current_candidates.json` 的 `stage_review` 是**原地覆盖**字段：下一次人工改档，
2026-10-23 那条声明（连同 basis 里「板块回调不作反向证据」的推理）就只剩 git 历史。
git 历史不是可查询的研究数据，撑不起「日后回测研究的准确性 / 胜率」。

本产物把人工阶段声明做成**追加式日志**：只增不改，供内部评估视图与日后回测消费。
默认页不再展示阶段声明（v0.80 使用者决策），因为行情持续更新时静态旧声明没有信息量。

## 三条硬约束
1. **append-only**：已有 declaration_id 若内容不一致 → 拒绝（零修改），绝不覆盖。
   取代关系写在**新条**的 `supersedes`（新 → 旧），不回头改旧条。
2. **PIT 锚点**：`market_anchor.as_of` = `declared_at`，是「当时可知信息的上界」，
   **不是行情数据日期**。回测窗口起点必须严格晚于声明日；
   ★ 绝不可拿 `theme_market.as_of`（事后行情）当锚点 —— 那是 look-ahead。
3. **结算分离**：本日志**不含任何结算 / 收益 / 命中字段**。回测时按声明日 + 前向窗口
   另算，沿用 `candidate_formation_log` / `candidate_ledger` 的既有模式。
   「胜率」须按 AGENTS.md §3.1 写全口径七要素 + Wilson + 未校准声明。

## 确定性
产物**不写 `generated_at`**（记录类产物不该带生成时刻）；时间信息全部来自源
`current_candidates.json` 的 `snapshot_date` / `generated_at`。

用法：--write / --check
"""
import argparse
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
CC = os.path.join(CURRENT, "current_candidates.json")
OUT = os.path.join(CURRENT, "phase_declaration_log_v0_1.json")
OUT_VIEW = os.path.join(CURRENT, "phase_declaration_log_v0_1_view.json")

# ★ 结算字段白名单：出现任一即视为「形成与结算混写」，--check 直接 FAIL。
SETTLEMENT_FORBIDDEN = frozenset({
    "settlement", "settled", "forward_return", "excess_pp", "hit_rate",
    "win_rate", "outcome", "result", "verdict", "accuracy", "realized",
    "performance", "pnl", "return_pct", "equal_weight", "market_layer",
})

CALIBER = {
    "what": "产业机制阶段的人工声明历史；不是行情状态、不是概率、不是预测，不含启发式排序",
    "append_only": "只增不改；取代关系写在新条的 supersedes，旧条永不修改",
    "pit": "market_anchor.as_of = 声明日，是当时可知信息的上界；回测窗口起点必须严格晚于此日",
    "settlement_rule": "结算字段不写入本日志；回测时按声明日 + 前向窗口另行重算",
    "win_rate_caveat": "任何事后核对比例的表述必须写明口径七要素 + 95% Wilson + 未校准；"
                       "本产物不提供该比例",
    "not": [
        "不是买卖信号 / 荐股 / 选股清单",
        "不是对未来涨跌的预测",
        "不是已验证模型（ThreeC 目前没有这一层）",
    ],
}

KNOWN_GAPS = [
    {
        "id": "DECLARATION_TIME_PRICE_CUTOFF_NOT_RECORDED",
        "detail": "声明当时可见的最新行情截止日未单独落盘；故以声明日作为 PIT 上界（更保守）。"
                  "回测时窗口起点一律取声明日之后的第一个交易日，不得用 theme_market.as_of 回填。",
        "blocks": "声称「声明日当时已知某段行情」",
    },
    {
        "id": "SINGLE_ROUND_NOT_INDEPENDENT",
        "detail": "现有 6 条声明同属 2026-10-23 一个研究轮次，不构成 6 个独立观察；"
                  "同轮同日的多主题声明共享同一批宏观信息与同一次判断，样本内相关。",
        "blocks": "把 6 条声明当作 n=6 独立样本直接算比例",
    },
    {
        "id": "SETTLEMENT_NOT_ATTACHED",
        "detail": "本产物只保留声明，不附结算。事后核对比例必须另立一轮，"
                  "先声明观察窗口、分母、排除规则，再按 §3.1 输出未校准经验基准。",
        "blocks": "直接从本日志读出任何「准确率」数字",
    },
]

LIMITS = [
    "★ 阶段是**产业机制阶段（研究侧人工声明）**，不是行情状态；市场层不参与定档。",
    "★ 默认页不展示本日志；它只在**内部评估视图**出现，用途是事后可核与回测留痕。",
    "★ 本日志只增不改；行情推进**不得**改写任何历史声明。",
    "★ `supersedes` 由新条指向旧条，旧条不含 `superseded_by`（否则违反只增不改）。",
    "★ 行情推进后 `theme_market` / `frontier_board` 会重算，但本日志必须逐字节不变。",
]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _dump(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def project(cc):
    """从当前人工声明源投影出**本轮**声明；不读任何行情产物。"""
    out = []
    for c in sorted(cc.get("candidates") or [], key=lambda x: x.get("candidate_id") or ""):
        sr = c.get("stage_review") or {}
        declared_at = sr.get("reviewed_at")
        if not declared_at or not sr.get("declared_phase"):
            continue
        out.append({
            "declaration_id": "PD-%s-%s" % (c["candidate_id"], declared_at),
            "candidate_id": c["candidate_id"],
            "display_name": c["display_name"],
            "declared_at": declared_at,
            "declared_phase": sr["declared_phase"],
            "attention_state": c.get("attention_state"),
            "review_round": sr.get("review_round"),
            "review_status": sr.get("status"),
            "basis": sr.get("basis") or "",
            "phase_evidence": c.get("phase_evidence") or {},
            "core_narrative": c.get("core_narrative") or "",
            "market_anchor": {
                "as_of": declared_at,
                "basis": "DECLARATION_DATE_AS_PIT_UPPER_BOUND",
                "price_data_available_at_declaration": "NOT_RECORDED",
                "note": "声明日作为当时可知信息的上界，不是行情数据日期；"
                        "回测窗口起点必须严格晚于此日。",
            },
            "supersedes": None,
            "source_ref": "current_candidates.json:candidates[%s].stage_review" % c["candidate_id"],
        })
    return out


def assemble(cc, declarations):
    declarations = sorted(declarations, key=lambda d: (d["declared_at"], d["declaration_id"]))
    return {
        "artifact": "phase_declaration_log",
        "artifact_version": "0.1",
        "source_kind": "PROJECTION_OF_RESEARCH_DECLARATIONS",
        "append_only": True,
        "purpose": "人工产业机制阶段声明的追加式记录；供内部评估视图与日后回测，默认页不消费",
        "source": {
            "file": os.path.basename(CC),
            "sha256_16": _sha(CC),
            "generated_by": cc.get("generated_by"),
            "snapshot_date": cc.get("snapshot_date"),
            "source_generated_at": cc.get("generated_at"),
        },
        "as_of": max((d["declared_at"] for d in declarations), default=None),
        "caliber": CALIBER,
        "counts": {
            "declarations": len(declarations),
            "candidates": len({d["candidate_id"] for d in declarations}),
            "review_rounds": len({d["review_round"] for d in declarations}),
            "with_settlement_fields": 0,
            "superseded_links": sum(1 for d in declarations if d.get("supersedes")),
        },
        "declarations": declarations,
        "known_gaps": KNOWN_GAPS,
        "limits": LIMITS,
    }


def make_view(doc, doc_sha):
    return {
        "artifact": "phase_declaration_log_view",
        "artifact_version": "0.1",
        "source": {"file": os.path.basename(OUT), "sha256_16": doc_sha},
        "as_of": doc["as_of"],
        "append_only": True,
        "caliber": doc["caliber"],
        "counts": doc["counts"],
        "declarations": [
            {k: d[k] for k in (
                "declaration_id", "candidate_id", "display_name", "declared_at",
                "declared_phase", "attention_state", "review_round", "review_status",
                "basis", "market_anchor", "supersedes", "source_ref")}
            for d in doc["declarations"]
        ],
        "known_gaps": doc["known_gaps"],
        "limits": doc["limits"],
    }


def _forbidden_keys(obj, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in SETTLEMENT_FORBIDDEN:
                hits.append("%s.%s" % (path, k))
            hits.extend(_forbidden_keys(v, "%s.%s" % (path, k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_forbidden_keys(v, "%s[%d]" % (path, i)))
    return hits


def write():
    cc = _load(CC)
    projected = project(cc)
    if not projected:
        print("FAIL 源产物没有可投影的阶段声明")
        return 1
    existing = _load(OUT) if os.path.exists(OUT) else None
    if existing is None:
        merged = projected
    else:
        by_id = {d["declaration_id"]: d for d in existing["declarations"]}
        # ★ 冲突检查全部在写第一个字节之前做完
        for d in projected:
            old = by_id.get(d["declaration_id"])
            if old is not None and old != d:
                print("FAIL 追加式冲突（零修改）：%s 已存在但内容不同" % d["declaration_id"])
                return 1
        merged = list(existing["declarations"]) + [
            d for d in projected if d["declaration_id"] not in by_id]
        # 历史声明必须逐字保留
        for old in existing["declarations"]:
            if old not in merged:
                print("FAIL 历史声明被丢弃：%s" % old["declaration_id"])
                return 1
    doc = assemble(cc, merged)
    bad = _forbidden_keys(doc)
    if bad:
        print("FAIL 出现结算字段：%s" % ", ".join(bad))
        return 1
    _dump(OUT, doc)
    _dump(OUT_VIEW, make_view(doc, _sha(OUT)))
    print("--write OK · 声明 %d 条（新增 %d）· as_of %s · view 已同步"
          % (len(merged), len(merged) - (len(existing["declarations"]) if existing else 0),
             doc["as_of"]))
    return 0


def check():
    """检查范围：声明不变量 / 与当前人工声明源对账 / 视图对账。
    ★ 不重放历史追加 —— 历史声明无法从「当前」源复现，这是 append-only 的性质。
    """
    errs = []
    for p in (OUT, OUT_VIEW, CC):
        if not os.path.exists(p):
            print("FAIL 文件不存在：%s" % p)
            return 1
    doc = _load(OUT)
    view = _load(OUT_VIEW)
    cc = _load(CC)

    # 1 · 元数据与 declarations 自洽（无 generated_at，完全确定性）
    rebuilt = assemble(cc, doc["declarations"])
    if json.dumps(rebuilt, ensure_ascii=False, sort_keys=True) != \
       json.dumps(doc, ensure_ascii=False, sort_keys=True):
        errs.append("产物元数据与 declarations 不自洽（或源 sha256 已变）")

    # 2 · 追加式不变量
    ds = doc.get("declarations") or []
    ids = [d["declaration_id"] for d in ds]
    if len(ids) != len(set(ids)):
        errs.append("declaration_id 重复")
    pairs = [(d["declared_at"], d["declaration_id"]) for d in ds]
    if pairs != sorted(pairs):
        errs.append("declarations 未按 (declared_at, id) 排序")
    known = set(ids)
    for d in ds:
        if d.get("supersedes") and d["supersedes"] not in known:
            errs.append("supersedes 指向不存在的声明：%s" % d["supersedes"])
        if "superseded_by" in d:
            errs.append("旧条不得含 superseded_by（违反只增不改）：%s" % d["declaration_id"])
        if d["market_anchor"]["as_of"] != d["declared_at"]:
            errs.append("PIT 锚点不等于声明日：%s" % d["declaration_id"])
        if d["market_anchor"]["basis"] != "DECLARATION_DATE_AS_PIT_UPPER_BOUND":
            errs.append("PIT 锚点口径被改：%s" % d["declaration_id"])
        if not d.get("basis"):
            errs.append("声明缺 basis：%s" % d["declaration_id"])

    # 3 · 与当前源逐字对账（当前声明不得被覆盖或漂移）
    by_id = {d["declaration_id"]: d for d in ds}
    for d in project(cc):
        old = by_id.get(d["declaration_id"])
        if old is None:
            errs.append("当前源有未入账声明：%s" % d["declaration_id"])
        elif {k: old.get(k) for k in ("declared_phase", "basis", "declared_at",
                                     "review_round", "review_status")} != \
             {k: d[k] for k in ("declared_phase", "basis", "declared_at",
                                "review_round", "review_status")}:
            errs.append("当前源声明与日志漂移：%s" % d["declaration_id"])

    # 4 · 结算字段隔离
    bad = _forbidden_keys(doc)
    if bad:
        errs.append("出现结算字段：%s" % ", ".join(bad))
    if doc["counts"]["with_settlement_fields"] != 0:
        errs.append("counts.with_settlement_fields 必须为 0")

    # 5 · 视图对账（逐条 basis 与计数）
    if view["source"]["sha256_16"] != _sha(OUT):
        errs.append("view.source.sha256_16 与完整产物不一致")
    if view["counts"] != doc["counts"] or view["as_of"] != doc["as_of"]:
        errs.append("view 计数 / as_of 与完整产物不一致")
    if len(view["declarations"]) != len(ds):
        errs.append("view 声明条数不一致")
    for v in view["declarations"]:
        if v["basis"] != by_id[v["declaration_id"]]["basis"]:
            errs.append("view basis 与完整产物不一致：%s" % v["declaration_id"])

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1
    print("--check PASS · 范围：声明不变量 / 当前源对账 / 视图对账（不重放历史追加）"
          " · 声明 %d 条 · as_of %s" % (len(ds), doc["as_of"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    sys.exit(main())
