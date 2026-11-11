#!/usr/bin/env python3
"""check_real_use_protocol_v0_1.py —— 真实使用验证协议只读校验器（v0.83）。

## 为什么存在
项目已实现工具形态，但有效性证据链断在「0 条真实使用记录」。
比记录更早要做的是把「怎么算有效」在看到结果之前锁死，否则事后可以挑口径、
挑阈值、挑样本。本校验器负责：

  1. 锁定 `docs/REAL_USE_DECISION_RULE_v0_1.md` 的 sha256（改口径必须升版 + 留痕）；
  2. 对账规则文本里的阈值与校验器常量一致（防「只改文档不改代码」的两份真相）；
  3. 检查轻量 3 字段模板 / 冻结机制代码的关键不变量仍在；
  4. 读取本地导出记录，按「首次判断才计分 / cluster 为观察单位 / <20 不下结论」
     输出**状态标签**，绝不输出有效性结论、绝不生成任何记录。

## 边界
- **只读**。不写 `.tmp/real_use/`、不创建模板、不生成记录。
- CI 无 `.tmp/real_use/records/`（gitignore）→ 显式 `SKIP` 并打印范围，
  不静默通过、不把「0 条」说成「有效性 PASS」。
- 已结算 cluster < 20 时只输出触发量与数据限制，这是纪律不是错误。

用法：--check
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RULE = os.path.join(ROOT, "docs", "REAL_USE_DECISION_RULE_v0_1.md")
LITE_PROTOCOL = os.path.join(ROOT, "docs", "REAL_USE_LITE_v0_1.md")
LITE_TEMPLATE = os.path.join(ROOT, "docs", "templates", "REAL_USE_RECORD_LITE_TEMPLATE_v0_1.md")
RECORDS_TS = os.path.join(ROOT, "src", "workbench", "records.ts")
RECORDS_DIR = os.path.join(ROOT, ".tmp", "real_use", "records")

# ★★ 规则文件全文指纹。改口径 → 此值不变就会 FAIL；必须升 v0.2 + 改常量 + 留痕。
RULE_SHA256_16 = "d6d13499795a0634"

# ★★ 事前冻结的阈值（与规则文本逐项对账，防止两份真相）
THRESHOLDS = {
    "new_lead_rate_min": 0.20,
    "min_independent_clusters": 3,
    "hours_saved_median_max": -0.5,
    "verifiability_min": 0.80,
    "min_settled_clusters": 20,
    "compliance_target": 0.70,
    "compliance_biased_below": 0.50,
}
TYPES = ("LEAD", "CONFIRM", "REJECT", "NO_LEAD", "BLOCKED", "UI_FRICTION")


def _sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def check_rule(errs, skips):
    """规则文件必须存在、指纹未变、文本阈值与常量一致。"""
    if not os.path.exists(RULE):
        errs.append("事前判定规则文件缺失：docs/REAL_USE_DECISION_RULE_v0_1.md")
        return
    if _sha16(RULE) != RULE_SHA256_16:
        errs.append("事前判定规则已被改动（sha16 %s != 锁定值 %s）；"
                    "必须新建 v0.2 并保留原文件、同步常量与 PROJECT_STATE"
                    % (_sha16(RULE), RULE_SHA256_16))
    text = open(RULE, encoding="utf-8").read()
    # ★★ 不只看「短语在不在」：从规则文本**解析出数值**，与 THRESHOLDS 常量逐项对账，
    #     防止「改了文档没改常量」或反过来形成两份真相（本项目已踩过形状 PASS 语义错）。
    #     捕获组拿到的是展示值，负号用 U+2212，统一归一后再比。
    patterns = {
        "new_lead_rate_min": r"≥\s*([0-9.]+).{0,80}?至少\s*\*\*(\d+)\s*个独立\s*cluster\*\*",
        "hours_saved_median_max": r"≤\s*([−\-][0-9.]+)\s*小时",
        "verifiability_min": r"≥\s*([0-9.]+)；「口径不清」",
        "min_settled_clusters": r"已结算\s*cluster\s*≥\s*(\d+)",
        "compliance_target": r"\|\s*目标\s*\|\s*≥\s*([0-9.]+)",
        "compliance_biased_below": r"<\s*([0-9.]+)\s*→\s*`BIASED_SAMPLE`",
    }
    parsed = {}
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if not m:
            errs.append("规则文本无法解析阈值 %s（正则 %s）" % (key, pat))
            continue
        raw = m.group(1).replace("−", "-")
        parsed[key] = float(raw)
        if key == "new_lead_rate_min":
            parsed["min_independent_clusters"] = float(m.group(2))
    for key, expected in THRESHOLDS.items():
        if key not in parsed:
            continue  # 上面已报「无法解析」
        if abs(parsed[key] - expected) > 1e-9:
            errs.append("阈值两份真相：规则文本 %s=%s / 校验器常量=%s"
                        % (key, parsed[key], expected))
    for t in TYPES:
        if t not in text:
            errs.append("规则文本缺记录类型 %s" % t)
    for phrase in ("首次判断才计分", "cluster", "多基线", "不得编造", "不入库"):
        if phrase not in text:
            errs.append("规则文本缺关键纪律：%s" % phrase)


def check_mechanism(errs, skips):
    """模板 / 协议 / 冻结代码的关键不变量。"""
    if not os.path.exists(LITE_TEMPLATE):
        errs.append("轻量 3 字段模板缺失（旧 13 字段模板不得作为日常记录入口）")
    else:
        t = open(LITE_TEMPLATE, encoding="utf-8").read()
        for f in ("question", "verdict_at_T", "posthoc_check", "type", "cluster_id"):
            if f not in t:
                errs.append("轻量模板缺字段 %s" % f)
        if "12 个通用必填字段" in t:
            errs.append("轻量模板混入了旧 13 字段协议的说明")
        if "本文件是空白模板" not in t:
            errs.append("轻量模板未声明「空白模板，不构成验证」")
    if os.path.exists(LITE_PROTOCOL):
        p = open(LITE_PROTOCOL, encoding="utf-8").read()
        if "REAL_USE_DECISION_RULE_v0_1.md" not in p:
            errs.append("轻量协议未指向事前判定规则")
    if os.path.exists(RECORDS_TS):
        c = open(RECORDS_TS, encoding="utf-8").read()
        for phrase in ("RECORDS_KEY", "EVALS_KEY", "frozen_at: now.toISOString()",
                       "rows.some((x) => x.record_id === r.record_id)"):
            if phrase not in c:
                errs.append("冻结机制不变量缺失：%s" % phrase)
    else:
        errs.append("records.ts 缺失")


def _first_evals(evals):
    """首次判断才计分：同一 record_id 只取 checked_at 最早的一条。"""
    out = {}
    for e in sorted(evals, key=lambda x: str(x.get("checked_at") or "")):
        rid = e.get("record_id")
        if rid and rid not in out:
            out[rid] = e
    return out


def read_logs(errs, skips):
    """只读地汇总本地导出记录；返回 (status, detail)。绝不写文件。"""
    if not os.path.isdir(RECORDS_DIR):
        skips.append("本地真实使用记录目录不存在（CI 环境，.tmp 被忽略）")
        return "NO_RECORDS", {"reason": "记录目录不存在；不下结论"}
    files = sorted(glob.glob(os.path.join(RECORDS_DIR, "*.json")))
    if not files:
        skips.append("本地真实使用记录 0 条（尚未开展，不是有效性结论）")
        return "NO_RECORDS", {"reason": "本轮未开展；不下结论"}

    records, evals = [], []
    for p in files:
        try:
            d = _load(p)
        except Exception as e:
            errs.append("导出文件无法解析：%s（%s）" % (os.path.basename(p), e))
            continue
        if d.get("protocol") != "REAL_USE_LITE_v0_1":
            errs.append("导出文件 protocol 不符：%s" % os.path.basename(p))
        records.extend(d.get("records") or [])
        evals.extend(d.get("evals") or [])

    if errs:
        return "INVALID", {"files": len(files)}

    # 形状不变量
    ids = [r.get("record_id") for r in records]
    if len(ids) != len(set(ids)):
        errs.append("record_id 重复（append-only 被破坏）")
    for r in records:
        for f in ("question", "verdict_at_T", "frozen_at", "data_as_of"):
            if not r.get(f):
                errs.append("记录缺字段 %s：%s" % (f, r.get("record_id")))
        if "posthoc_check" in r or "posthoc" in r:
            errs.append("正文混入事后核对字段：%s" % r.get("record_id"))
        if r.get("type") not in TYPES:
            errs.append("记录类型非法：%s / %s" % (r.get("record_id"), r.get("type")))
    first = _first_evals(evals)
    for rid, e in first.items():
        frozen = next((r.get("frozen_at") for r in records
                       if r.get("record_id") == rid), None)
        if frozen and str(e.get("checked_at") or "") <= str(frozen):
            errs.append("可疑时间顺序（回填风险）：%s" % rid)

    clusters = {r.get("cluster_id") for r in records if r.get("cluster_id")}
    settled = {rid for rid in first
               if first[rid].get("is_new_correspondence") in ("YES", "NO")}
    settled_clusters = {next((r.get("cluster_id") for r in records
                              if r.get("record_id") == rid), None) for rid in settled}
    settled_clusters.discard(None)
    by_type = {t: sum(1 for r in records if r.get("type") == t) for t in TYPES}
    detail = {
        "export_files": len(files),
        "records": len(records),
        "evals": len(evals),
        "evals_revision_excluded": len(evals) - len(first),
        "by_type": by_type,
        "independent_clusters": len(clusters),
        "settled_clusters": len(settled_clusters),
        "min_settled_clusters": THRESHOLDS["min_settled_clusters"],
    }
    if errs:
        return "INVALID", detail
    missing = [t for t in ("NO_LEAD", "BLOCKED", "UI_FRICTION")
               if by_type.get(t, 0) == 0]
    if missing:
        detail["biased_reason"] = "缺负向/摩擦类别：" + " ".join(missing)
        return "BIASED_SAMPLE", detail
    if len(settled_clusters) < THRESHOLDS["min_settled_clusters"]:
        detail["reason"] = "样本量不足，只输出触发量与数据限制，不下结论"
        return "INSUFFICIENT_SAMPLE", detail
    return "ELIGIBLE", detail


def check():
    errs, skips = [], []
    check_rule(errs, skips)
    check_mechanism(errs, skips)
    status, detail = read_logs(errs, skips)

    if errs:
        for e in errs:
            print("FAIL " + e)
        print("--check：%d 项 FAIL" % len(errs))
        return 1

    scope = "规则指纹/阈值对账 / 轻量模板 / 冻结机制不变量 / 防回填与首次判断计分"
    if skips:
        scope += "（SKIP：%s）" % "；".join(skips)
    print("--check PASS · 范围：%s" % scope)
    print("状态标签 %s · %s" % (status, json.dumps(detail, ensure_ascii=False, sort_keys=True)))
    print("★ 本校验器只输出状态标签，不输出有效性结论；"
          "INSUFFICIENT_SAMPLE / NO_RECORDS 时不得写「工具有效」或「工具无效」。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", required=True)
    ap.parse_args()
    return check()


if __name__ == "__main__":
    sys.exit(main())
