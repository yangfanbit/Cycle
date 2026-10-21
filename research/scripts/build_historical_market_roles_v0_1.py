#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_historical_market_roles_v0_1.py —— 历史**市场角色**证据层（v0.29）。

## 它解决什么

v0.28 已经能说清「谁被报道点名 / 谁业务相关 / 谁在对象里登记成什么」，
但**没有任何地方**回答：**在当时那个时点，谁是可以被识别出来的市场核心？**
以及：**哪些「龙头」其实是行情结束后才总结出来的？**

本产物把「历史市场角色」做成**独立维度**（与 `market_participation` /
`mechanism_relation` / `registry_role` / `study_standing` / 行情表现**严格分开**），
并强制 Point-in-Time 纪律。

## 角色分类（与 PIT 方法论文档一致）

| role | 含义 | 可识别时点 |
|---|---|---|
| `PIT_MEDIA_NAMED_LEADER` | 同期报道**明确称**其为龙头 / 领涨 / 核心 | 报道日 |
| `PIT_MEDIA_NAMED_MOVER` | 同期报道点名且给出涨停 / 涨幅（**未**称龙头） | 报道日 |
| `PIT_MARKET_OBSERVED` | 只有盘面可观察异动（放量 / 涨停 / 连板），无报道定性 | 当日 |
| `POSTHOC_LEADER_SET` | 行情结束后回看总结出的龙头集合 | **事后**（明确标注） |
| `INSUFFICIENT` | 有研究但证据不足以定角色 | — |

★ 本库**没有任何**同期材料明确称某股为「龙头」→ `PIT_MEDIA_NAMED_LEADER` 当前 **0 条**。
   不得为了凑数把「涨停」写成「龙头」。

## 时间前推（PIT）规则（写进产物、由 `--check` 校验）

1. 角色的 `identified_date` 只能是**当时已公开**的信息日期（报道日 / 当日盘面）。
2. `pit_safe = identified_date <= 该事件窗口结束日`，且证据发布时间 ≤ `identified_date`。
3. `POSTHOC_LEADER_SET` 的成员一律 `posthoc=true`、`pit_safe=false`，
   **不得**用来证明早期已形成同样的股票池。
4. 切片（slice）只用 `identified_date <= 切片日` 的成员；成员不足 2 只或没有媒体识别 →
   `basket_status = NOT_USABLE`（与 `2024_robotaxi_point_in_time.md` 的 07-08 结论一致）。

## 数据来源

- `research/research/c2/point_in_time_leaders.csv`（2024 Robotaxi，5 只，含识别日 / 类型 / 置信度）；
- `research/research/c2/2024_robotaxi_point_in_time.md`（切片结论，用于交叉校验）；
- `research/current/participant_evidence_v0_2.json`（同期报道背书 + 报道日期 / URL）；
- 题材文档的 `catalysts`（报道日期 + 来源 + URL）。

## 用法

    python research/scripts/build_historical_market_roles_v0_1.py --check
    python research/scripts/build_historical_market_roles_v0_1.py --write
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
INDEX_PATH = os.path.join(CURRENT, "historical_event_maps_index.json")
EVIDENCE_PATH = os.path.join(CURRENT, "participant_evidence_v0_2.json")
PIT_CSV = os.path.join(REPO, "research", "research", "c2", "point_in_time_leaders.csv")
GENERATED_AT = "2026-10-22"

# ★ PIT CSV 的 identification_type → 本产物 role
PIT_TYPE_TO_ROLE = {
    "media_identified": "PIT_MEDIA_NAMED_MOVER",
    "market_breadth": "PIT_MARKET_OBSERVED",
}
# ★ 事件 → PIT 研究记录（只有做过 PIT 研究的事件才有）
PIT_SOURCE_BY_EVENT = {
    "AUTO-2024-ROBOTAXI": {
        "csv": "research/research/c2/point_in_time_leaders.csv",
        "record": "research/research/c2/2024_robotaxi_point_in_time.md",
        "slices": [
            {"date": "2024-07-08", "documented_members": ["DAZHONGTONG"],
             "documented_status": "NOT_USABLE",
             "documented_note": "仅大众交通有 market_breadth 低置信异动，不足以认定已形成题材篮子"},
            {"date": "2024-07-10",
             "documented_members": ["DAZHONGTONG", "JINJIANG", "XINGYUYUDA", "TIANMAI"],
             "documented_status": "USABLE", "documented_note": "4 只；金龙 07-12 才被公开识别"},
            {"date": "2024-07-15",
             "documented_members": ["DAZHONGTONG", "JINJIANG", "XINGYUYUDA", "TIANMAI", "JINLONG"],
             "documented_status": "USABLE", "documented_note": "5 只；至此与事后集合一致（识别顺序有先后）"},
        ],
    },
}

CONTRACT = {
    "version": "historical_market_roles_v1",
    "axes_are_separate": [
        "market_participation（同期报道能证明什么）",
        "mechanism_relation（业务与题材机制的关系）",
        "registry_role（Research 对象内部登记）",
        "study_standing（纳入 / 反例 / 证据不足）",
        "historical_market_role（本产物：当时可识别的市场角色）",
        "行情表现（价格结果，**不得**反推角色）",
    ],
    "roles": {
        "PIT_MEDIA_NAMED_LEADER": "同期报道**明确称**其为龙头 / 领涨 / 核心（当前库内 0 条）",
        "PIT_MEDIA_NAMED_MOVER": "同期报道点名且给出涨停 / 涨幅（**未**称龙头）",
        "PIT_MARKET_OBSERVED": "只有盘面可观察异动（放量 / 涨停 / 连板），无报道定性",
        "POSTHOC_LEADER_SET": "行情结束后回看总结出的龙头集合 —— **后验**，不得当作当时可知",
        "INSUFFICIENT": "有研究但证据不足",
    },
    "pit_rules": [
        "identified_date 只能使用当时已公开的信息日期",
        "pit_safe 要求 identified_date ≤ 事件窗口结束日，且证据发布时间 ≤ identified_date",
        "POSTHOC_LEADER_SET 一律 posthoc=true / pit_safe=false",
        "切片只收 identified_date ≤ 切片日 的成员；成员 <2 或没有媒体识别 → NOT_USABLE",
        "不得用完整事件结束后的龙头集合证明早期已形成同样的股票池",
    ],
    "must_not": [
        "不得把「报道涨停」写成「龙头」",
        "不得用事后涨幅反推当时可识别的角色",
        "不得把 registry_role=leader 当作历史市场角色",
        "不得用事后集合证明早期 basket",
    ],
}


def load_index():
    return json.load(open(INDEX_PATH, encoding="utf-8"))


def load_theme_docs(index):
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if os.path.exists(path):
            yield entry, json.load(open(path, encoding="utf-8"))


def load_pit_rows():
    rows = []
    with open(PIT_CSV, encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    return rows


def bind_pit_ids(event_id, rows, participants):
    """★★ 把 PIT CSV 的 `security_id` 绑到**地图参与者**上 —— 只按名称精确相等，并留痕。

    为什么不能按 ID 直接匹配（v0.29 实测）：
      · CSV `DAZHONGTONG`（大众交通）在注册表里叫 `DADONGTRAFFIC`；
      · CSV `JINJIANG`（锦江在线）在注册表里 `JINJIANG` = **锦江酒店 600754**（另一家公司！）
        —— 按 ID 匹配会把锦江在线的角色挂到锦江酒店上；
      · CSV `XINGYUYUDA` / `TIANMAI` 在注册表与本事件参与者中都不存在。
    ⇒ 只允许「名称精确相等 + 该名称在本事件参与者中唯一」的绑定，其余标 `UNBOUND` 并写明原因。
    """
    by_name = {}
    for p in participants:
        by_name.setdefault(p.get("name"), []).append(p)
    out = {}
    for r in rows:
        sid, name = r["security_id"], r["name"]
        if sid in {p["security_id"] for p in participants}:
            out[sid] = {"bound_to": sid, "status": "BOUND",
                        "method": "SECURITY_ID_IN_EVENT_PARTICIPANTS",
                        "note": "CSV 的 security_id 与地图参与者完全一致"}
            continue
        hits = by_name.get(name) or []
        if len(hits) == 1:
            out[sid] = {"bound_to": hits[0]["security_id"], "status": "BOUND_BY_NAME",
                        "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                        "note": ("CSV security_id 与注册表不一致（注册表可能指向另一家公司），"
                                 "按名称精确相等绑定到本事件参与者；CSV 无 ticker 可交叉核对"),
                        "review": "NAME_MATCH_ONLY"}
        elif len(hits) > 1:
            out[sid] = {"bound_to": None, "status": "AMBIGUOUS",
                        "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                        "note": "同一名称在本事件参与者中命中多只 → 不绑定"}
        else:
            out[sid] = {"bound_to": None, "status": "UNBOUND",
                        "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                        "note": "本事件参与者中无该名称 → 该角色不在地图覆盖范围内（不强行挂靠）"}
    return out


def derive_pit_roles(event_id, rows, binding):
    """把 PIT CSV 行转成本产物的角色记录（保留原始识别类型与置信度）。"""
    out = []
    for r in rows:
        role = PIT_TYPE_TO_ROLE.get(r["identification_type"], "INSUFFICIENT")
        b = binding.get(r["security_id"], {"bound_to": None, "status": "UNBOUND",
                                           "method": "-", "note": "未尝试绑定"})
        out.append({
            "security_id": b["bound_to"],
            "source_security_id": r["security_id"],
            "name": r["name"],
            "binding": b,
            "role": role,
            "identified_date": r["identified_date"],
            "identification_type": r["identification_type"],
            "confidence": r["confidence"],
            "evidence": {
                "source_type": ("同期报道（媒体归因）" if r["identification_type"] == "media_identified"
                                else "当日盘面可观察信息（无媒体定性）"),
                "source_text": r["identification_source"],
                "url": None,
                "published_at": r["identified_date"],
                "summary": r["notes"],
            },
            "pit_safe": True,
            "posthoc": False,
            "notes": r["notes"],
            "source_record": "research/research/c2/point_in_time_leaders.csv",
        })
    return out


def derive_report_roles(evidence_ev, event):
    """从 v0_2 的同期报道背书推导 PIT 角色（报道日 = 可识别日）。

    ★ 只收 `REPORT_WITH_URL` / `REPORT_NAMED_NO_URL` 且**带报道日期**的记录；
      角色上限是 `PIT_MEDIA_NAMED_MOVER`（报道点名 + 涨幅），**不**升级为「龙头」。
    """
    out = []
    for sid, p in (evidence_ev.get("participants") or {}).items():
        mp = p["market_participation"]
        if not str(mp.get("source_kind", "")).startswith("REPORT_"):
            continue
        rep = mp.get("report") or {}
        date = rep.get("date")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(date or "")):
            continue
        st = mp["status"]
        conf = ("high" if st == "REPORT_CONFIRMED_LIMIT_UP"
                else "medium" if st in ("REPORT_CONFIRMED_GAIN", "REPORT_CONFIRMED_WINDOW_GAIN")
                else "low")
        out.append({
            "security_id": sid,
            # ★ 由参与者列表直接派生 → id 天然一致；仍显式留绑定记录（便于统一校验）
            "source_security_id": sid,
            "name": p.get("name"),
            "binding": {"bound_to": sid, "status": "BOUND",
                        "method": "FROM_EVENT_PARTICIPANTS",
                        "note": "角色由该事件参与者的同期报道直接派生，id 一致"},
            "role": "PIT_MEDIA_NAMED_MOVER",
            "identified_date": date,
            "identification_type": "media_identified",
            "confidence": conf,
            "evidence": {
                "source_type": "同期报道",
                "source_text": rep.get("source"),
                "url": rep.get("url"),
                "published_at": date,
                "summary": rep.get("text"),
            },
            "pit_safe": True,
            "posthoc": False,
            "notes": "报道点名并给出涨跌幅（%s）；报道**未**称其为龙头，故只记「被报道点名的参与者」"
                     % {"REPORT_CONFIRMED_LIMIT_UP": "报道明确涨停",
                        "REPORT_CONFIRMED_GAIN": "报道给出当日涨幅",
                        "REPORT_CONFIRMED_WINDOW_GAIN": "报道给出区间涨幅",
                        "REPORT_CONFIRMED_NAMED": "报道点名"}.get(st, "报道点名"),
            "source_record": "research/current/participant_evidence_v0_2.json",
        })
    return out


def build_slices(event_id, roles, slices_doc):
    """按 `identified_date ≤ 切片日` 生成切片，并与文档记载的成员**逐一比对**。"""
    out = []
    for s in slices_doc:
        members = sorted(r["security_id"] for r in roles
                         if r["security_id"] and r["role"] != "POSTHOC_LEADER_SET"
                         and r["identified_date"] <= s["date"])
        media = [r for r in roles if r["role"] == "PIT_MEDIA_NAMED_MOVER"
                 and r["identified_date"] <= s["date"]]
        usable = len(members) >= 2 and len(media) >= 1
        derived_status = "USABLE" if usable else "NOT_USABLE"
        # ★ 原始研究记录的成员用的是 **CSV 的 id**（可能已过时/与注册表冲突），
        #   先按 roles 的绑定关系映射到地图 id，再判断「文档成员里有哪些落在本地图覆盖内」。
        csv_to_map = {r["source_security_id"]: r["security_id"] for r in roles}
        bound_doc = [csv_to_map[m] for m in s["documented_members"] if csv_to_map.get(m)]
        not_in_map = [m for m in s["documented_members"] if not csv_to_map.get(m)]
        out.append({
            "date": s["date"],
            "members": members,
            "basket_status": derived_status,
            "documented_members": s["documented_members"],
            "documented_status": s["documented_status"],
            # ★ 只与「文档成员 ∩ 本地图已绑定成员」比对 —— 覆盖缺口单独列出，不算不一致
            "matches_document": sorted(members) == sorted(bound_doc)
            and derived_status == s["documented_status"],
            "not_in_map": not_in_map,
            "note": s["documented_note"],
        })
    return out


def build() -> dict:
    index = load_index()
    evid = json.load(open(EVIDENCE_PATH, encoding="utf-8"))
    pit_rows = load_pit_rows()
    events = {}
    tally = {"RESEARCHED_PIT": 0, "DERIVED_FROM_REPORT": 0, "NOT_RESEARCHED": 0}
    for entry, doc in load_theme_docs(index):
        for e in doc.get("events") or []:
            eid = e["event_id"]
            cf = e.get("campaign_facts") or {}
            oid = cf.get("object_id") or cf.get("campaign_id")
            window = (e.get("market_performance") or {}).get("window")
            ev_e = evid["events"].get(eid, {})
            roles = []
            source = PIT_SOURCE_BY_EVENT.get(eid)
            if source:
                binding = bind_pit_ids(eid, pit_rows, e.get("participants") or [])
                roles = derive_pit_roles(eid, pit_rows, binding)
                status = "RESEARCHED_PIT"
            else:
                roles = derive_report_roles(ev_e, e)
                status = "DERIVED_FROM_REPORT" if roles else "NOT_RESEARCHED"
            tally[status] += 1
            # 时间前推校验：识别日不得晚于窗口结束日
            for r in roles:
                if window and r["identified_date"] > window[1]:
                    r["pit_safe"] = False
                    r["notes"] = (r["notes"] or "") + "；★ 识别日晚于事件窗口结束日 → 非 PIT"
            slices = build_slices(eid, roles, source["slices"]) if source else []
            posthoc = None
            if source:
                posthoc = {
                    "basis": "行情结束后回看总结的核心集合（%s 第 1 节）" % source["record"],
                    "members": [r["security_id"] or r["source_security_id"] for r in roles],
                    "posthoc": True,
                    "pit_safe": False,
                    "survivorship_note": "★ 该集合是**后验**结论：成员按事后表现与叙事回看选出，"
                                         "含幸存者偏差，**不得**用来证明窗口早期已可识别同样的股票池。",
                }
            report_backed = sum(1 for p in (ev_e.get("participants") or {}).values()
                                if str(p["market_participation"].get("source_kind", "")).startswith("REPORT_"))
            gaps = []
            if status == "NOT_RESEARCHED":
                gaps.append("该事件尚未做 PIT 角色研究：需要同期报道（带日期与 URL）或当日盘面数据")
            if status == "DERIVED_FROM_REPORT" and not roles:
                gaps.append("事件有报道基础，但没有参与者同时具备「报道日期 + 涨幅」→ 无法定位识别日")
            if roles and all(r["role"] != "PIT_MEDIA_NAMED_LEADER" for r in roles):
                gaps.append("★ 没有任何同期材料**明确称**某股为龙头 → 不设「龙头」角色（只记被点名参与者）")
            events[eid] = {
                "theme_id": entry["theme_id"],
                "object_id": oid,
                "window": window,
                "research_status": status,
                "source_records": ([source["csv"], source["record"]] if source else
                                   (["research/current/participant_evidence_v0_2.json"] if roles else [])),
                "roles": roles,
                "pit_slices": slices,
                "posthoc_leader_set": posthoc,
                "coverage": {
                    "participants": len(ev_e.get("participants") or {}),
                    "report_backed_participants": report_backed,
                    "pit_roles": len(roles),
                    "pit_roles_bound": sum(1 for r in roles if r["security_id"]),
                    "pit_roles_unbound": sum(1 for r in roles if not r["security_id"]),
                },
                "gaps": gaps,
            }
    return {
        "artifact": "historical_market_roles",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_historical_market_roles_v0_1.py",
        "supersedes": None,
        "historical_market_roles_contract": CONTRACT,
        "summary": {
            "events": len(events),
            "by_research_status": tally,
            "roles_by_type": {},
            "events_with_pit_slices": sum(1 for v in events.values() if v["pit_slices"]),
            "events_with_posthoc_set": sum(1 for v in events.values() if v["posthoc_leader_set"]),
        },
        "events": events,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="构建历史市场角色证据层")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)
    doc = build()
    by_type: dict = {}
    for v in doc["events"].values():
        for r in v["roles"]:
            by_type[r["role"]] = by_type.get(r["role"], 0) + 1
    doc["summary"]["roles_by_type"] = by_type

    out = os.path.join(CURRENT, "historical_market_roles_v0_%d.json" % a.version)
    if a.check:
        if not os.path.exists(out):
            print("FAIL: 产物不存在：%s" % os.path.relpath(out, REPO))
            return 1
        cur = json.load(open(out, encoding="utf-8"))
        if cur.get("events") != doc["events"]:
            diff = [k for k in doc["events"] if cur["events"].get(k) != doc["events"][k]]
            print("FAIL: 角色产物与重新推导不一致（%d 事件）：%s" % (len(diff), diff[:5]))
            return 1
        # ★ PIT 纪律：事后集合不得标 pit_safe
        for eid, ev in cur["events"].items():
            for r in ev["roles"]:
                if r["role"] == "POSTHOC_LEADER_SET" and r.get("pit_safe"):
                    print("FAIL: %s/%s 事后角色被标为 pit_safe" % (eid, r["security_id"]))
                    return 1
        print("PASS: 角色产物一致（%d 事件 · %d 条角色 · %s）"
              % (doc["summary"]["events"], sum(by_type.values()), by_type))
        return 0
    if not a.write:
        print("用法：--check 或 --write [--version N]")
        return 2
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    doc["artifact_version"] = "0.%d" % a.version
    if a.version > 1:
        doc["supersedes"] = "research/current/historical_market_roles_v0_%d.json" % (a.version - 1)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("  事件 %d | 研究状态 %s" % (doc["summary"]["events"], doc["summary"]["by_research_status"]))
    print("  角色 %d 条：%s" % (sum(by_type.values()), by_type))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
