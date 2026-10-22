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
EVIDENCE_PATH = os.path.join(CURRENT, "participant_evidence_v0_3.json")
PIT_CSV = os.path.join(REPO, "research", "research", "c2", "point_in_time_leaders.csv")
GENERATED_AT = "2026-10-22"
EVIDENCE_REL = "research/current/participant_evidence_v0_3.json"

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
    "date_semantics": {
        "catalyst_date": "★★ catalyst.date 是**事实日期**（采访日 / 盘面日），不是报道发布日",
        "published_at": "★★ 报道发布日：从 catalyst.source 文本解析或「同上」继承；无法确定 → null",
        "identified_date": "★★ PIT 可识别日 = published_at（媒体报道）或**首次连板的第二个涨停日**（盘面）",
        "rule": "published_at ≤ identified_date；identified_date 晚于窗口结束 → pit_safe=false",
    },
    "derivation": {
        "RESEARCHED_PIT": "有正式 PIT 研究记录（CSV + 方法论文档）—— 以研究记录为准，不混入自动盘面角色",
        "DERIVED_FROM_REPORT": "由参与者证据的**报道背书**派生（要求 reported_move_backed 且 published_at 可定）",
        "DERIVED_FROM_MARKET": "只有盘面可观察信息（窗口内 ≥2 次涨停且至少一次连板）",
        "NOT_RESEARCHED": "两者皆无 —— 合法状态，不设角色",
    },
    "market_observed_rule": {
        "trigger": "窗口内涨停 ≥2 次，且至少一次**相邻交易日**连板",
        "identified_date": "首次连板的第二个涨停日（此时「连板」才可观察）",
        "limit_band": "主板 9.8–10.6%；创业板 2020-08-24 前 9.8–10.6%、之后 19.5–21.2%；科创板 19.5–21.2%",
        "why_band": "★ 用「带」而非「≥阈值」：qfq 噪声会产生 13%/16% 这类非涨停跳变（实测已排除）",
        "excluded": "ST（5%）无法从库内判定 → 不检测（宁可漏，不误报）",
    },
    "slice_match_scope": {
        "FULL": "原始研究篮子全部可在地图绑定，且状态一致 → matches_document=true",
        "SUBSET": "地图只覆盖其中一部分（not_in_map 非空）→ **不是**不一致，但不得说成完全一致",
        "MISMATCH": "已绑定部分与推导结果不一致（真问题）",
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
        "★★ 不得用 catalyst 的事实日期冒充报道发布日（v0.30 修复：超级真菌 04-08 → 04-11）",
        "★★ ID 相同但名称冲突 → 不自动绑定（ID_CONFLICT_NAME_MISMATCH）",
        "★★ 盘面可观察 ≠ 媒体报道，也 ≠ 龙头",
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


def load_securities(conn) -> dict:
    """注册表：security_id → {name, ticker}。用于**发现 ID 与名称冲突**。"""
    out = {}
    for r in conn.execute("SELECT security_id, name, ticker FROM securities"):
        out[r["security_id"]] = {"name": r["name"], "ticker": r["ticker"]}
    return out


def bind_pit_ids(event_id, rows, participants, secs=None):
    """★★ 把 PIT CSV 的 `security_id` 绑到**地图参与者**上 —— id 与名称都必须自洽。

    v0.29 只按名称绑定；v0.30 补两条**身份安全不变量**：
      ① `security_id` 与地图参与者相同 → **仍要核对名称**；名称不一致不得自动绑定
         （标 `ID_CONFLICT_NAME_MISMATCH`，等人工确认）；
      ② 注册表里该 id 的名称与 CSV 名称不一致 → 记 `registry_name_conflict`，
         即使最终按名称绑上，也保留「该 id 指向另一家公司」的证据。

    实测冲突（2024 Robotaxi）：
      · CSV `DAZHONGTONG`（大众交通）在注册表叫 `DADONGTRAFFIC`；
      · CSV `JINJIANG`（名称「锦江在线」）在注册表 `JINJIANG` = **锦江酒店 600754**（另一家公司，
        锦江在线是 `JINJIANGONLINE` / 600650）。
    """
    secs = secs or {}
    by_id = {p["security_id"]: p for p in participants}
    by_name = {}
    for p in participants:
        by_name.setdefault(p.get("name"), []).append(p)

    def _reg_conflict(sid, name):
        reg = secs.get(sid)
        if reg and reg.get("name") and reg["name"] != name:
            return {"registry_name": reg["name"], "registry_ticker": reg.get("ticker")}
        return None

    out = {}
    for r in rows:
        sid, name = r["security_id"], r["name"]
        reg_conflict = _reg_conflict(sid, name)
        if sid in by_id:
            pname = by_id[sid].get("name")
            if pname == name:
                out[sid] = {"bound_to": sid, "status": "BOUND",
                            "method": "SECURITY_ID_AND_NAME_IN_EVENT_PARTICIPANTS",
                            "note": "CSV 的 security_id 与名称同时与本事件参与者一致"}
            else:
                out[sid] = {"bound_to": None, "status": "ID_CONFLICT_NAME_MISMATCH",
                            "method": "SECURITY_ID_IN_EVENT_PARTICIPANTS",
                            "note": ("★ ID 与参与者相同但**名称不一致**（CSV「%s」vs 地图「%s」）"
                                     "→ 不自动绑定，等人工确认" % (name, pname)),
                            "review": "ID_CONFLICT_NAME_MISMATCH"}
            if reg_conflict:
                out[sid]["registry_name_conflict"] = reg_conflict
            continue
        hits = by_name.get(name) or []
        if len(hits) == 1:
            rec = {"bound_to": hits[0]["security_id"], "status": "BOUND_BY_NAME",
                   "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                   "note": ("CSV security_id 与注册表不一致，按名称精确相等绑定到本事件参与者；"
                            "CSV 无 ticker 可交叉核对"),
                   "review": "NAME_MATCH_ONLY"}
            if reg_conflict:
                rec["registry_name_conflict"] = reg_conflict
                rec["note"] += ("；★ 注册表 `%s` 实为「%s」（%s），该 id **指向另一家公司**"
                                % (sid, reg_conflict["registry_name"],
                                   reg_conflict.get("registry_ticker") or "无代码"))
            out[sid] = rec
        elif len(hits) > 1:
            out[sid] = {"bound_to": None, "status": "AMBIGUOUS",
                        "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                        "note": "同一名称在本事件参与者中命中多只 → 不绑定"}
        else:
            out[sid] = {"bound_to": None, "status": "UNBOUND",
                        "method": "NAME_EXACT_IN_EVENT_PARTICIPANTS",
                        "note": "本事件参与者中无该名称 → 该角色不在地图覆盖范围内（不强行挂靠）"}
        if reg_conflict:
            out[sid].setdefault("registry_name_conflict", reg_conflict)
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


ROLE_PRECEDENCE = {"PIT_MEDIA_NAMED_LEADER": 3, "PIT_MEDIA_NAMED_MOVER": 2,
                   "PIT_MARKET_OBSERVED": 1, "INSUFFICIENT": 0}


def derive_report_roles(evidence_ev, event):
    """从参与者证据的**报道背书**推导 PIT 角色（识别日 = 报道发布日）。

    ★★ v0.30：识别日**只能**是 `report.published_at`（发布日），不得用 `fact_date`（事实日）。
      · 没有 `published_at` → 不产生角色（宁可留白，不用事实日冒充）；
      · `reported_move_backed=false`（报道对不上该股）→ 不产生角色；
      · 角色上限 `PIT_MEDIA_NAMED_MOVER`：报道点名 + 涨跌 ≠ 龙头。
    """
    out = []
    for sid, p in (evidence_ev.get("participants") or {}).items():
        mp = p["market_participation"]
        if not str(mp.get("source_kind", "")).startswith("REPORT_"):
            continue
        if not mp.get("reported_move_backed"):
            continue
        rep = mp.get("report") or {}
        pub = rep.get("published_at")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(pub or "")):
            continue
        st = mp["status"]
        conf = ("high" if st == "REPORT_CONFIRMED_LIMIT_UP" and mp.get("attribution") == "NAME_IN_TEXT"
                else "medium" if st == "REPORT_CONFIRMED_LIMIT_UP"
                else "low")
        out.append({
            "security_id": sid,
            "source_security_id": sid,
            "name": p.get("name"),
            "binding": {"bound_to": sid, "status": "BOUND",
                        "method": "FROM_EVENT_PARTICIPANTS",
                        "note": "角色由该事件参与者的报道背书直接派生，id 一致"},
            "role": "PIT_MEDIA_NAMED_MOVER",
            "identified_date": pub,
            "identification_type": "media_identified",
            "confidence": conf,
            "evidence": {
                "source_type": ("同期报道（正文点名该股）"
                                if mp.get("attribution") == "NAME_IN_TEXT"
                                else "同期报道（多股汇总，个股归属依研究记录转录）"),
                "source_text": rep.get("publisher") or mp.get("source_text"),
                "url": rep.get("url"),
                "published_at": pub,
                "fact_date": rep.get("fact_date"),
                "attribution": mp.get("attribution"),
                "summary": rep.get("text"),
            },
            "pit_safe": True,
            "posthoc": False,
            "notes": ("报道点名并给出涨跌幅（%s）；报道**未**称其为龙头，故只记「被报道点名的参与者」"
                      % {"REPORT_CONFIRMED_LIMIT_UP": "报道明确涨停",
                         "REPORT_CONFIRMED_GAIN": "报道给出当日涨幅",
                         "REPORT_CONFIRMED_WINDOW_GAIN": "报道给出区间涨幅",
                         "REPORT_CONFIRMED_NAMED": "报道点名"}.get(st, "报道点名"))
                     + ("；★ 无原文链接 → 尚无法独立核验" if not rep.get("url") else ""),
            "source_record": "research/current/participant_evidence_v0_3.json",
        })
    return out


# ---------------------------------------------------------------- 盘面可观察角色

def limit_band(ticker, date):
    """A 股涨跌停幅度（返回允许的**涨跌幅区间带**）。

    ★ 用「带」而不是「≥阈值」：qfq 复权噪声会产生 13% / 16% 这类**非涨停**跳变，
      用 ≥9.8% 会把它们误判成涨停（v0.30 实测：13.45% / 16.37% 都不是涨停）。
    ★ 板块规则随日期变化：科创板 20%（2019-07-22 起）；创业板 10% → 20%（2020-08-24 起）；
      主板 10%。ST（5%）无法从库内判定 → **不检测**（宁可漏，不误报）。
    """
    t = ticker or ""
    if t.startswith("688"):
        return (19.5, 21.2)
    if t.startswith("300"):
        return (19.5, 21.2) if date >= "2020-08-24" else (9.8, 10.6)
    return (9.8, 10.6)


def limit_up_days(conn, sid, ticker, start, end):
    """窗口内该股的涨停日（按 adjusted 收盘的日变化，落在板块涨跌停带内）。"""
    rows = conn.execute(
        "SELECT trade_date, adj_close FROM market_daily "
        "WHERE series_id=? AND price_type='adjusted' AND trade_date BETWEEN ? AND ? "
        "ORDER BY trade_date", (sid, start, end)).fetchall()
    out, prev = [], None
    for r in rows:
        c = r["adj_close"]
        if prev and prev > 0 and c and c > 0:
            pct = (c / prev - 1.0) * 100.0
            lo, hi = limit_band(ticker, r["trade_date"])
            if lo <= pct <= hi:
                out.append({"date": r["trade_date"], "pct": round(pct, 2)})
        prev = c
    return out


def derive_market_roles(conn, event, evidence_ev, cal_index):
    """从**行情库**识别「当时盘面可观察的市场核心」—— 判据：**连板**（连续交易日涨停 ≥2）。

    ★★ 这是 `PIT_MARKET_OBSERVED`，与「报道点名」严格分开：
      · 不声称任何媒体定性，也不声称是龙头；
      · 识别日 = **首次连板的第二个涨停日**（此时「连板」才成为可观察事实）；
      · 只对「窗口内有 ≥2 个涨停日且至少一次相邻交易日连板」的参与者给出；
      · 已有更强报道角色的参与者**不重复**给盘面角色（媒体报道优先）。
    """
    window = (event.get("market_performance") or {}).get("window")
    if not window:
        return []
    already = {r["security_id"] for r in
               (derive_report_roles(evidence_ev, event)) if r["security_id"]}
    out = []
    for p in event.get("participants") or []:
        sid = p["security_id"]
        if sid in already:
            continue
        days = limit_up_days(conn, sid, p.get("ticker"), window[0], window[1])
        if len(days) < 2:
            continue
        pairs = [(a, b) for a, b in zip(days, days[1:])
                 if cal_index.get(b["date"], -99) - cal_index.get(a["date"], -99) == 1]
        if not pairs:
            continue
        first_pair = pairs[0]
        out.append({
            "security_id": sid,
            "source_security_id": sid,
            "name": p.get("name"),
            "binding": {"bound_to": sid, "status": "BOUND",
                        "method": "FROM_EVENT_PARTICIPANTS",
                        "note": "角色由该事件参与者的行情序列直接计算，id 一致"},
            "role": "PIT_MARKET_OBSERVED",
            "identified_date": first_pair[1]["date"],
            "identification_type": "market_observed",
            "confidence": "medium",
            "evidence": {
                "source_type": "当日盘面可观察信息（无媒体定性）",
                "source_text": "market_data.db · adjusted 收盘日变化（板块涨跌停带内）",
                "url": None,
                "published_at": first_pair[1]["date"],
                "summary": ("窗口内涨停 %d 次（%s ~ %s），首次连板 %s→%s"
                            % (len(days), days[0]["date"], days[-1]["date"],
                               first_pair[0]["date"], first_pair[1]["date"])),
                "limit_up_days": days,
                "rule": ("涨停带按板块与日期判定（主板 9.8–10.6%；创业板 2020-08-24 前 9.8–10.6%、"
                         "之后 19.5–21.2%；科创板 19.5–21.2%）；ST 不检测"),
            },
            "pit_safe": True,
            "posthoc": False,
            "notes": ("★ 盘面可观察：窗口内 %d 次涨停、至少一次连板 → 当时「有资金持续参与」是可观察事实；"
                      "**但没有任何媒体定性**，也不等于龙头" % len(days)),
            "source_record": "research/database/market_data.db（market_daily.adjusted）",
        })
    return out


def build_slices(event_id, roles, slices_doc):
    """按 `identified_date ≤ 切片日` 生成切片，并把**地图覆盖缺口**显式拆出来。

    ★★ v0.30：`match_scope` 三态（FULL / SUBSET / MISMATCH）
      · `FULL`     —— 原始研究篮子**全部**能在地图里绑定，且状态一致；
      · `SUBSET`   —— 地图只覆盖其中一部分（`not_in_map` 非空），**不是**不一致；
      · `MISMATCH` —— 已绑定部分与推导结果不一致（真问题）。
      `matches_document` 只在 `FULL` 时为真 —— 不许用「子集匹配」冒充「完全一致」。
    """
    out = []
    name_of = {r["source_security_id"]: r.get("name") for r in roles}
    for s in slices_doc:
        members = sorted(r["security_id"] for r in roles
                         if r["security_id"] and r["role"] != "POSTHOC_LEADER_SET"
                         and r["identified_date"] <= s["date"])
        media = [r for r in roles if r["role"] in ("PIT_MEDIA_NAMED_MOVER", "PIT_MEDIA_NAMED_LEADER")
                 and r["identified_date"] <= s["date"]]
        usable = len(members) >= 2 and len(media) >= 1
        derived_status = "USABLE" if usable else "NOT_USABLE"
        # ★ 原始研究记录的成员用的是 **CSV 的 id**（可能已过时/与注册表冲突），
        #   先按 roles 的绑定关系映射到地图 id，再判断「文档成员里有哪些落在本地图覆盖内」。
        csv_to_map = {r["source_security_id"]: r["security_id"] for r in roles}
        bound_doc = [csv_to_map[m] for m in s["documented_members"] if csv_to_map.get(m)]
        not_in_map = [m for m in s["documented_members"] if not csv_to_map.get(m)]
        same_members = sorted(members) == sorted(bound_doc)
        same_status = derived_status == s["documented_status"]
        if same_members and same_status and not not_in_map:
            scope = "FULL"
        elif same_members and same_status:
            scope = "SUBSET"
        else:
            scope = "MISMATCH"
        out.append({
            "date": s["date"],
            "members": members,
            "basket_status": derived_status,
            "documented_members": s["documented_members"],
            "documented_status": s["documented_status"],
            "match_scope": scope,
            # ★ 只有 FULL 才算「与原始研究完全一致」
            "matches_document": scope == "FULL",
            "documented_count": len(s["documented_members"]),
            "bound_count": len(bound_doc),
            "not_in_map": not_in_map,
            "not_in_map_names": [name_of.get(m) or m for m in not_in_map],
            "note": s["documented_note"],
        })
    return out


def build(conn=None) -> dict:
    index = load_index()
    evid = json.load(open(EVIDENCE_PATH, encoding="utf-8"))
    pit_rows = load_pit_rows()
    own_conn = conn is None
    if own_conn:
        conn = db.connect()
        db.require_market(conn)
    try:
        secs = load_securities(conn)
        cal_index = {r[0]: i for i, r in enumerate(
            conn.execute("SELECT trade_date FROM trading_calendar ORDER BY trade_date"))}
        events = {}
        tally = {"RESEARCHED_PIT": 0, "DERIVED_FROM_REPORT": 0,
                 "DERIVED_FROM_MARKET": 0, "NOT_RESEARCHED": 0}
        for entry, doc in load_theme_docs(index):
            for e in doc.get("events") or []:
                eid = e["event_id"]
                cf = e.get("campaign_facts") or {}
                oid = cf.get("object_id") or cf.get("campaign_id")
                window = (e.get("market_performance") or {}).get("window")
                ev_e = evid["events"].get(eid, {})
                source = PIT_SOURCE_BY_EVENT.get(eid)
                media_roles = derive_report_roles(ev_e, e)
                if source:
                    # 有正式 PIT 研究的事件：以**研究记录**为准，不混入自动盘面角色
                    binding = bind_pit_ids(eid, pit_rows, e.get("participants") or [], secs)
                    roles = derive_pit_roles(eid, pit_rows, binding)
                    status = "RESEARCHED_PIT"
                else:
                    market_roles = derive_market_roles(conn, e, ev_e, cal_index)
                    roles = media_roles + market_roles
                    if media_roles:
                        status = "DERIVED_FROM_REPORT"
                    elif market_roles:
                        status = "DERIVED_FROM_MARKET"
                    else:
                        status = "NOT_RESEARCHED"
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
                                    if p["market_participation"].get("reported_move_backed"))
                gaps = []
                if status == "NOT_RESEARCHED":
                    gaps.append("该事件尚未做 PIT 角色研究：需要同期报道（带日期与 URL），"
                                "或窗口内至少一次**连板**的盘面数据")
                if status == "DERIVED_FROM_REPORT" and not roles:
                    gaps.append("事件有报道基础，但没有参与者同时具备「报道发布日 + 可对上该股的涨跌」"
                                "→ 无法定位识别日")
                if roles and all(r["role"] != "PIT_MEDIA_NAMED_LEADER" for r in roles):
                    gaps.append("★ 没有任何同期材料**明确称**某股为龙头 → 不设「龙头」角色（只记被点名参与者 / 盘面异动）")
                unbound = [r for r in roles if not r["security_id"]]
                if unbound:
                    gaps.append("原始研究篮子里有 %d 只不在本地图参与者中：%s"
                                % (len(unbound), " / ".join(sorted(
                                    r.get("name") or r["source_security_id"] for r in unbound))))
                events[eid] = {
                    "theme_id": entry["theme_id"],
                    "object_id": oid,
                    "window": window,
                    "research_status": status,
                    "source_records": ([source["csv"], source["record"]] if source else
                                       ([EVIDENCE_REL] if media_roles else []) +
                                       (["research/database/market_data.db（market_daily.adjusted）"]
                                        if any(r["role"] == "PIT_MARKET_OBSERVED" for r in roles) else [])),
                    "roles": roles,
                    "pit_slices": slices,
                    "posthoc_leader_set": posthoc,
                    "coverage": {
                        "participants": len(ev_e.get("participants") or {}),
                        "report_backed_participants": report_backed,
                        "media_roles": sum(1 for r in roles if r["role"].startswith("PIT_MEDIA")),
                        "market_roles": sum(1 for r in roles if r["role"] == "PIT_MARKET_OBSERVED"),
                        "pit_roles": len(roles),
                        "pit_roles_bound": sum(1 for r in roles if r["security_id"]),
                        "pit_roles_unbound": sum(1 for r in roles if not r["security_id"]),
                        "name_review_required": sum(
                            1 for r in roles
                            if (r.get("binding") or {}).get("review")),
                    },
                    "gaps": gaps,
                }
    finally:
        if own_conn:
            conn.close()
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
    version = a.version
    if a.check:
        # ★ 与参与者证据一致：`--check` 默认对齐**最新已发布版本**
        existing = sorted(int(m.group(1)) for m in
                          (re.match(r"historical_market_roles_v0_(\d+)\.json$", f)
                           for f in os.listdir(CURRENT)) if m)
        if existing:
            version = existing[-1]
    doc = build()
    by_type: dict = {}
    for v in doc["events"].values():
        for r in v["roles"]:
            by_type[r["role"]] = by_type.get(r["role"], 0) + 1
    doc["summary"]["roles_by_type"] = by_type

    out = os.path.join(CURRENT, "historical_market_roles_v0_%d.json" % version)
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
