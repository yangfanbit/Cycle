#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""verify_external_claims_v0_1.py —— 外部季节性线索的**证据核验**（v0.37）。

★ 只做一件事：把外部声称的「月份窗口」拿去和**我们自己的多年行情发现**对照，
  明确区分「内部数据支持类似时间结构」与「外部报告的具体说法已被验证」——
  前者只是同月结构存在，后者需要外部原始报告，本库**没有**原始报告 → 永远不标 VERIFIED。

状态定义（写死）：
- `NOT_CALENDAR`       无固定月份窗口（事件驱动）→ 只能核事件，不能核日历；
- `UNTESTABLE_NO_SERIES` 找不到可对照的板块/概念序列（名称不足以匹配，不硬配）；
- `INTERNAL_SUPPORTED` 同月结构在内部数据里达到 STRICT 且有样本外证据（OOS 检验年≥5、命中≥50%）；
- `INTERNAL_WEAK`      同月结构存在但未达 STRICT 或无足够 OOS；
- `NOT_SUPPORTED`      同月结构在内部数据中为负/不足。
★ 所有条目 `external_report_verified = false`（原始报告不在库内）。
"""
from __future__ import annotations

import argparse, json, os, re, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"external_claim_verification_v0_(\d+)\.json$")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    disc_files = sorted([f for f in os.listdir(CURRENT) if re.match(r"pattern_discovery_v0_(\d+)\.json$", f)],
                        key=lambda f: int(re.search(r"v0_(\d+)", f).group(1)))
    if not disc_files:
        print("FAIL: 缺 pattern_discovery 产物")
        return 1
    disc = json.load(open(os.path.join(CURRENT, disc_files[-1]), encoding="utf-8"))
    ext = json.load(open(os.path.join(CURRENT, "external_seasonal_calendar_v0_2.json"), encoding="utf-8"))

    if a.check:
        files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                       key=lambda f: int(OUT_RE.match(f).group(1)))
        if not files:
            print("FAIL: 核验产物不存在")
            return 1
        doc = json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))
        errs = []
        for c in doc["claims"]:
            if c.get("external_report_verified"):
                errs.append("%s 不得声称外部报告已验证" % c["claim_id"])
            if c["status"] == "INTERNAL_SUPPORTED" and not c.get("internal_pattern"):
                errs.append("%s 缺内部结构引用" % c["claim_id"])
        if errs:
            print("FAIL: %s" % errs[:5])
            return 1
        print("PASS: 外部线索核验产物一致（%d 条 · 内部支持 %d · 弱 %d · 不可测 %d）"
              % (len(doc["claims"]),
                 sum(1 for c in doc["claims"] if c["status"] == "INTERNAL_SUPPORTED"),
                 sum(1 for c in doc["claims"] if c["status"] == "INTERNAL_WEAK"),
                 sum(1 for c in doc["claims"] if c["status"] == "UNTESTABLE_NO_SERIES")))
        return 0

    patterns = disc["patterns"]

    def find(entry):
        """按名称**精确子串**找候选板块/概念（弱匹配，如实记录方法）。"""
        name = entry["name"]
        keys = [k for k in re.split(r"[ /、·（）()—-]+", name) if len(k) >= 2]
        best = None
        for p in patterns:
            for k in keys:
                if k and (k in p["board"] or p["board"] in k):
                    if best is None or p["median_excess_pct"] > best[1]["median_excess_pct"]:
                        best = (k, p)
                    break
        return best

    claims = []
    for e in ext["entries"]:
        months = [w for w in (e.get("windows") or []) if w.get("start_month")]
        rec = {
            "claim_id": e["id"], "name": e["name"], "category": e.get("category"),
            "claimed_window": (e["windows"][0].get("raw_text") if e.get("windows") else None),
            "claimed_months": [w["start_month"] for w in months],
            "external_report_verified": False,
            "external_source_ids": e.get("source_ids") or [],
        }
        if not months or e.get("precision") != "MONTH":
            rec.update({"status": "NOT_CALENDAR",
                        "reason": "无固定月份窗口（事件驱动）→ 只能核事件，不能核日历"})
            claims.append(rec)
            continue
        hit = find(e)
        if not hit:
            rec.update({"status": "UNTESTABLE_NO_SERIES",
                        "reason": "内部板块/概念序列中找不到可对照对象（不按名称硬配）"})
            claims.append(rec)
            continue
        key, p = hit
        oos_ok = p.get("oos_status") == "REPORTED" and (p.get("oos_hit_rate") or 0) >= 0.5
        if p["tier"] == "STRICT" and oos_ok:
            status = "INTERNAL_SUPPORTED"
            reason = "内部同月结构达 STRICT 且有样本外证据（%s）" % p["board_series"]
        elif p["median_excess_pct"] > 0:
            status = "INTERNAL_WEAK"
            reason = "内部同月结构为正但未同时满足 STRICT + OOS 门槛"
        else:
            status = "NOT_SUPPORTED"
            reason = "内部同月结构中位超额 ≤ 0"
        rec.update({
            "status": status, "reason": reason,
            "match_method": "NAME_SUBSTRING（弱匹配，仅作对照，不作为验证）",
            "matched_keyword": key,
            "internal_pattern": {
                "pattern_id": p["pattern_id"], "board": p["board"], "kind": p["kind"],
                "month": p["month"], "n_years": p["n_years"],
                "median_excess_pct": p["median_excess_pct"], "hit_rate": p["hit_rate"],
                "oos_status": p.get("oos_status"), "oos_tests": p.get("oos_tests"),
                "oos_hit_rate": p.get("oos_hit_rate"),
            },
        })
        claims.append(rec)

    doc = {
        "artifact": "external_claim_verification",
        "artifact_version": "0.1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "as_of": disc["as_of"],
        "source": {
            "external": "research/current/external_seasonal_calendar_v0_2.json（外部资料，原始报告不在库内）",
            "internal": "research/current/%s（板块×日历月，基准沪深300）" % disc_files[-1],
        },
        "rule": ("★ 内部数据支持「类似时间结构」≠ 外部报告的具体说法已得到验证。"
                 "本库没有外部原始报告 → 所有条目 external_report_verified = false。"),
        "counts": {
            "total": len(claims),
            "internal_supported": sum(1 for c in claims if c["status"] == "INTERNAL_SUPPORTED"),
            "internal_weak": sum(1 for c in claims if c["status"] == "INTERNAL_WEAK"),
            "not_supported": sum(1 for c in claims if c["status"] == "NOT_SUPPORTED"),
            "untestable": sum(1 for c in claims if c["status"] == "UNTESTABLE_NO_SERIES"),
            "not_calendar": sum(1 for c in claims if c["status"] == "NOT_CALENDAR"),
        },
        "claims": claims,
        "limitations": [
            "★ 名称子串匹配是**弱匹配**，仅用于找对照序列，不能证明外部说法正确。",
            "★ 外部报告原件不在库内 → 任何条目都不得标为「已验证」。",
            "★ 板块/概念均为当前分类回溯；概念为自建等权合成序列。",
        ],
    }
    print("外部线索 %d 条：内部支持 %d · 弱 %d · 不支持 %d · 不可测 %d · 非日历 %d"
          % (doc["counts"]["total"], doc["counts"]["internal_supported"], doc["counts"]["internal_weak"],
             doc["counts"]["not_supported"], doc["counts"]["untestable"], doc["counts"]["not_calendar"]))
    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        out = os.path.join(CURRENT, "external_claim_verification_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
