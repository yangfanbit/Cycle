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

## v0.32 变更（PIT 全路径封口）

- **legacy CSV 不再豁免**：`point_in_time_leaders.csv` 升级为显式日期字段
  （`evidence_as_of_date` / `supporting_evidence(_dates)` / `posthoc_background(_dates)` / `support_level`），
  识别日之后的后续事实只能进 `posthoc_background`。
- 新增 `validate_pit_contract()`：对**所有角色类别**校验截止日、逐条证据日期、
  事后字段日期、以及「事后日期泄漏进支持性文字」，`--check` 直接失败。
- `derive_report_roles` 的 `source_record` 改为**本次实际加载的输入路径**（不再硬编码 v0_3）。

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
# ★★ v0.32：输入路径**只有一个真相**（版本常量）—— 不再在派生函数里硬编码旧版文件名。
EVIDENCE_VERSION = "0_4"
EVIDENCE_REL = "research/current/participant_evidence_v%s.json" % EVIDENCE_VERSION
EVIDENCE_PATH = os.path.join(REPO, EVIDENCE_REL)
PIT_CSV_REL = "research/research/c2/point_in_time_leaders.csv"
PIT_CSV = os.path.join(REPO, *PIT_CSV_REL.split("/"))
GENERATED_AT = "2026-10-23"

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
    # ★★ v0.43：新增 5 个事件的 PIT 研究记录（每事件一份 CSV + 一份方法记录）。
    #    只收**同期报道明确点名**的标的；未点名的一律留缺口，不用行情/涨停倒推角色。
    "ROBOTICS-2023-HUMANOID": {
        "csv": "research/research/c2/point_in_time_robotics_2023_humanoid.csv",
        "record": "research/research/c2/2023_humanoid_point_in_time.md",
        "slices": [
            {"date": "2023-08-29", "documented_members": ["KINCO", "LEADERDRIVE"],
             "documented_status": "USABLE",
             "documented_note": "2 只：步科股份（20cm 涨停）、绿的谐波（涨超 10–12%）；均为当日报道点名"},
        ],
    },
    "SEMI-2025-MEMORY": {
        "csv": "research/research/c2/point_in_time_semi_2025_memory.csv",
        "record": "research/research/c2/2025_memory_point_in_time.md",
        "slices": [
            {"date": "2025-10-27", "documented_members": ["LONGYS", "GIGADEVICE", "BIWIN"],
             "documented_status": "USABLE",
             "documented_note": "3 只：江波龙 +19.82%、兆易创新 +10%、佰维存储 +7.31%（当日收盘报道）"},
        ],
    },
    "RES-2024-GOLD": {
        "csv": "research/research/c2/point_in_time_res_2024_gold.csv",
        "record": "research/research/c2/2024_gold_point_in_time.md",
        "slices": [
            {"date": "2024-04-12", "documented_members": ["CFGOLD", "SDGOLD", "ZJGOLD"],
             "documented_status": "USABLE",
             "documented_note": "3 只：赤峰（涨超 6%）、山东（涨幅居前）、中金（跟涨）"},
            {"date": "2025-04-21", "documented_members": ["CFGOLD", "SDGOLD", "ZJGOLD", "ZIJIN"],
             "documented_status": "USABLE",
             "documented_note": "4 只：新增紫金矿业（涨幅超 5%）；赤峰当日涨停"},
        ],
    },
    "CONS-2019-BAIJIU-CORE": {
        "csv": "research/research/c2/point_in_time_cons_2019_baijiu.csv",
        "record": "research/research/c2/2019_baijiu_point_in_time.md",
        "slices": [
            {"date": "2020-01-13", "documented_members": ["MOUTAI", "WULIANGYE", "FENJIU"],
             "documented_status": "USABLE",
             "documented_note": "3 只：2019 全年累计涨幅 >100% 的年度回顾报道点名（区间统计，非当日涨停）"},
        ],
    },
    "MEDIA-2018-GAMELICENSE": {
        "csv": "research/research/c2/point_in_time_media_2018_gamelicense.csv",
        "record": "research/research/c2/2018_gamelicense_point_in_time.md",
        "slices": [
            {"date": "2018-12-22", "documented_members": ["PERFECTWORLD", "SANQI"],
             "documented_status": "USABLE",
             "documented_note": "2 只：完美世界 +6.67%、三七互娱 +3.13%（版号重启消息次日收盘报道）"},
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
    "pit_evidence_closure": {
        "rule": ("★★ PIT 角色的成立判断**只能**使用 `evidence_date <= identified_date` 的证据；"
                 "识别日之后的价格记录**不得**进入支持性证据集合，也不得参与成立判断。"),
        "fields": {
            "identified_date": "PIT 可识别日",
            "evidence_as_of_date": "支持性证据的截止日（= identified_date）",
            "supporting_evidence": ("★ 统一的支持性证据清单 `[{date, text, kind}]` —— "
                                    "每条都带自己的事实日期，且 `date <= identified_date`"),
            "posthoc_background": ("★ 识别日**之后**才发生的后续事实 `[{date, text, kind}]` —— "
                                   "仅作事后背景，日期必须 `> identified_date`"),
            "limit_up_days_as_of": "★ 截至识别日的信号 —— **支持**角色成立（自动盘面角色）",
            "retrospective_limit_up_days": "★ 识别日之后的信号 —— **仅事后观察**，不参与成立判断",
        },
        "pit_safe": ("★ 由**支持性证据的时点**决定（全部 ≤ 识别日），"
                     "不是只检查 identified_date 是否早于事件窗口结束日"),
        "v031_fix": ("v0.30 曾把整窗涨停列表混在 evidence.limit_up_days 里并标 pit_safe=true"
                     "（21 条中 17 条含识别日之后的数据）→ v0.31 拆开并加断言"),
        "v032_fix": ("★★ v0.31 的封口只覆盖**自动盘面角色**（结构化信号列表），"
                     "legacy CSV 的 `market_breadth` 记录因没有信号明细被测试跳过 —— "
                     "`AUTO-2024-ROBOTAXI/DAZHONGTONG` 的识别日 2024-07-08 的支持性来源里"
                     "同时写了 7/9 一字板与媒体归因，仍标 pit_safe=true。"
                     "v0.32 把 CSV 升级为**显式日期字段**（支持性证据 / 事后背景各自带日期），"
                     "并对**所有角色类别**跑同一套 PIT 合同，`market_breadth` 不再是例外。"),
    },
    "support_levels": {
        "AUTO_RULE_MET": "自动盘面判据满足（窗口内 ≥2 次信号且至少一次相邻交易日连板）",
        "MEDIA_NAMED_SAME_DAY": "同期报道当日点名（报道日 = 识别日，CSV 人工研究记录）",
        "REPORT_BACKED": "由参与者证据的报道背书派生（`published_at` = 识别日）",
        "EARLY_LOW_CONFIDENCE_OBSERVATION": (
            "★ 早期低置信观察：当日有盘面/研究记录，但**不满足**自动盘面判据"
            "（未涨停 / 未连板）→ 只作早期线索，不构成「当时已确认的盘面核心」"),
    },
    "legacy_pit_records": {
        "csv": "research/research/c2/point_in_time_leaders.csv",
        "rule": ("★ 人工 PIT 研究记录必须用**显式字段**区分「当时已知的支持性证据」"
                 "与「识别日之后的后续事实」，不依赖对任意文字做日期正则来证明安全；"
                 "两类字段各自带日期，逐条进入 `supporting_evidence` / `posthoc_background`。"),
        "example": ("AUTO-2024-ROBOTAXI / DAZHONGTONG：识别日 2024-07-08 只能引用 7/8 放量 +6.12%；"
                    "7/9 一字板与媒体归因归入 `posthoc_background`（date=2024-07-09），"
                    "且 `support_level = EARLY_LOW_CONFIDENCE_OBSERVATION`（未涨停、未连板）。"),
    },
    "market_observed_rule": {
        "trigger": "窗口内信号 ≥2 次，且至少一次**相邻交易日**连板",
        "identified_date": "首次连板的第二个信号日（此时「连板」才可观察）",
        "limit_band": "主板 9.8–10.6%；创业板 2020-08-24 前 9.8–10.6%、之后 19.5–21.2%；科创板 19.5–21.2%",
        "why_band": "★ 用「带」而非「≥阈值」：qfq 噪声会产生 13%/16% 这类非涨停跳变（实测已排除）",
        "excluded": ("ST 状态无法从库内判定（`securities` 无 ST 标记）。★ 但「ST 一律 5% → 一律漏报」"
                     "**不成立**：主板 ST 5%（≤2026-07-05）/10%（≥2026-07-06）、"
                     "创业板 ST 5%（≤2020-08-23）/20%（≥2020-08-24）、科创板 ST 20% "
                     "⇒ 只有主板新规前与创业板改革前的 ST 落在带外（漏报方向）。"
                     "详见 research/research/reports/limit_up_audit_v0_2.json 的 `st_rules`"),
    },
    "slice_match_scope": {
        "FULL": "原始研究篮子全部可在地图绑定，且状态一致 → matches_document=true",
        "SUBSET": "地图只覆盖其中一部分（not_in_map 非空）→ **不是**不一致，但不得说成完全一致",
        "MISMATCH": "已绑定部分与推导结果不一致（真问题）",
    },
    "pit_rules": [
        "identified_date 只能使用当时已公开的信息日期",
        "pit_safe 要求 identified_date ≤ 事件窗口结束日，且**所有支持性证据**的日期 ≤ identified_date",
        "★★ 每条 pit_safe 角色必须有 `evidence_as_of_date` 与 `supporting_evidence`（逐条带日期）",
        "★★ 识别日之后的事实只能进 `posthoc_background` / `retrospective_limit_up_days`，"
        "不得出现在 `source_text` / `notes` / `summary` / `supporting_evidence[].text` 里",
        "★★ PIT 合同对**所有角色类别**统一生效 —— `market_breadth` 不是例外",
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
        "★★ 不得把识别日之后的后续事实写进支持性来源/说明（v0.32 修复：大众交通 7/8 vs 7/9）",
        "★★ 不得把「计算基础与产物一致」说成「交易所官方涨停事实证实」",
    ],
}


def load_index():
    return json.load(open(INDEX_PATH, encoding="utf-8"))


def load_theme_docs(index):
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if os.path.exists(path):
            yield entry, json.load(open(path, encoding="utf-8"))


def load_pit_rows(path=None):
    """读取 PIT 研究记录 CSV。★ v0.43：支持**按事件**指定路径（每个事件一份 CSV）。"""
    rows = []
    with open(path or PIT_CSV, encoding="utf-8-sig") as fh:
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


def _split_dates(raw):
    """CSV 里的日期列表（分号分隔）→ list。"""
    return [x.strip() for x in str(raw or "").split(";") if x.strip()]


def derive_pit_roles(event_id, rows, binding, source_record=None):
    """把 PIT CSV 行转成本产物的角色记录（保留原始识别类型与置信度）。

    ★★ v0.32：人工 PIT 记录也必须满足**同一套**时点合同 ——
      · 支持性证据只取 CSV 的 `supporting_evidence`（每条带 `supporting_evidence_dates` 里的日期）；
      · 识别日之后的后续事实只能进 `posthoc_background`（带日期），
        **不得**留在 `source_text` / `notes` 里（`validate_pit_contract` 会检查泄漏）；
      · `published_at` 只对 `media_identified` 记录给值（盘面记录没有「发布日」，不得伪造）；
      · `support_level` 由 CSV 显式声明；`market_breadth` 默认是
        `EARLY_LOW_CONFIDENCE_OBSERVATION`（不满足自动判据 → 只作早期线索）。
    """
    out = []
    for r in rows:
        role = PIT_TYPE_TO_ROLE.get(r["identification_type"], "INSUFFICIENT")
        b = binding.get(r["security_id"], {"bound_to": None, "status": "UNBOUND",
                                           "method": "-", "note": "未尝试绑定"})
        ident = r["identified_date"]
        as_of = (r.get("evidence_as_of_date") or ident).strip()
        sup_text = (r.get("supporting_evidence") or "").strip()
        sup_dates = _split_dates(r.get("supporting_evidence_dates")) or ([ident] if sup_text else [])
        ph_text = (r.get("posthoc_background") or "").strip()
        ph_dates = _split_dates(r.get("posthoc_background_dates"))
        # ★ v0.43：CSV 可带 `sources_json`（每来源 publisher/url/published_at/text/source_group/tier），
        #   有则逐来源生成支持性证据（每条日期 ≤ 识别日），并把独立来源组计数写进证据。
        raw_sources = (r.get("sources_json") or "").strip()
        sources = json.loads(raw_sources) if raw_sources else []
        if sources:
            supporting = [{"date": (s.get("published_at") or ident),
                           "text": s.get("text") or "",
                           "kind": "SUPPORTING",
                           "publisher": s.get("publisher"),
                           "url": s.get("url"),
                           "source_group": s.get("source_group"),
                           "source_tier": s.get("tier")} for s in sources]
        else:
            supporting = [{"date": d, "text": sup_text, "kind": "SUPPORTING"} for d in sup_dates]
        posthoc = [{"date": d, "text": ph_text, "kind": "SUBSEQUENT_FACT"} for d in ph_dates]
        support_level = (r.get("support_level") or "").strip() or (
            "MEDIA_NAMED_SAME_DAY" if r["identification_type"] == "media_identified"
            else "EARLY_LOW_CONFIDENCE_OBSERVATION")
        limits = []
        if support_level == "EARLY_LOW_CONFIDENCE_OBSERVATION":
            limits.append("★ 早期低置信观察：当日只有盘面异动（未涨停 / 未连板），"
                          "不满足自动盘面判据（≥2 次信号且至少一次连板）→ "
                          "**不构成**「当时已确认的盘面核心」")
        out.append({
            "security_id": b["bound_to"],
            "source_security_id": r["security_id"],
            "name": r["name"],
            "binding": b,
            "role": role,
            "identified_date": ident,
            "identification_type": r["identification_type"],
            "confidence": r["confidence"],
            "support_level": support_level,
            "evidence": {
                "source_type": ("同期报道（媒体归因）" if r["identification_type"] == "media_identified"
                                else "当日盘面可观察信息（无媒体定性）"),
                "source_text": r["identification_source"],
                "url": ((sources[0].get("url") if sources else None) or r.get("url") or None),
                "sources": sources or None,
                "independent_source_groups": (
                    len({s.get("source_group") for s in sources if s.get("source_group")})
                    if sources else None),
                # ★ 盘面记录没有「报道发布日」→ 不得把识别日冒充成发布日
                "published_at": ident if r["identification_type"] == "media_identified" else None,
                "evidence_as_of_date": as_of,
                "supporting_evidence": supporting,
                "posthoc_background": posthoc,
                "posthoc_note": ("★ 以下是**识别日之后**才发生的后续事实，仅作事后背景，"
                                 "不参与本角色成立判断，也不得用来证明当时已可识别"
                                 if posthoc else None),
                "summary": r["notes"],
            },
            # ★ 由**支持性证据的时点**决定，不再无条件写 True
            "pit_safe": bool(supporting) and as_of <= ident
            and all(x["date"] <= ident for x in supporting),
            "posthoc": False,
            "support_limits": limits,
            "notes": r["notes"],
            "source_record": source_record or PIT_CSV_REL,
        })
    return out


ROLE_PRECEDENCE = {"PIT_MEDIA_NAMED_LEADER": 3, "PIT_MEDIA_NAMED_MOVER": 2,
                   "PIT_MARKET_OBSERVED": 1, "INSUFFICIENT": 0}

# ---------------------------------------------------------------- PIT 合同校验
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# ★ 支持性文字里**不允许**出现的字段（识别日之后的事实只能进 posthoc_background）
SUPPORT_TEXT_FIELDS = ("source_text", "notes", "summary")


def _date_forms(d):
    """`2024-07-09` → {`2024-07-09`, `7/9`, `07-09`}（用于检出泄漏，不是用来证明安全）。"""
    y, m, dd = d.split("-")
    return {d, "%d/%d" % (int(m), int(dd)), "%s-%s" % (m, dd)}


def _leaked_dates(text, posthoc_dates):
    t = str(text or "")
    return sorted(d for d in posthoc_dates if any(f in t for f in _date_forms(d)))


def validate_pit_contract(doc, cal_index=None):
    """★★ v0.32：对**所有角色类别**跑同一套 PIT 时点合同，返回错误列表（空 = 通过）。

    合同（每条 `pit_safe=true` 的角色都必须满足）：
      1. 有 `evidence_as_of_date`，且 `<= identified_date`；
      2. `supporting_evidence` 非空，且每条都有 `date` 且 `<= identified_date`；
      3. `posthoc_background` / `retrospective_limit_up_days` 的日期必须 `> identified_date`；
      4. 识别日之后的日期**不得**出现在 `source_text` / `notes` / `summary` /
         `supporting_evidence[].text` 里（结构性字段优先，正则只用来查泄漏）；
      5. `support_level=AUTO_RULE_MET` 的盘面角色：截至识别日 ≥2 次信号，且至少一次相邻交易日连板
         （给了 `cal_index` 才校验连板，否则只校验信号数）。
    ★ `market_breadth`（人工 PIT 记录）**没有**豁免。
    """
    errs = []
    for eid, ev in (doc.get("events") or {}).items():
        for r in ev.get("roles") or []:
            sid = r.get("security_id") or r.get("source_security_id")
            tag = "%s/%s" % (eid, sid)
            evd = r.get("evidence") or {}
            if r.get("role") == "POSTHOC_LEADER_SET" and r.get("pit_safe"):
                errs.append("%s 事后角色被标 pit_safe" % tag)
            if not r.get("pit_safe"):
                continue
            ident = str(r.get("identified_date") or "")
            if not DATE_RE.match(ident):
                errs.append("%s identified_date 非法：%r" % (tag, ident))
                continue
            as_of = str(evd.get("evidence_as_of_date") or "")
            if not DATE_RE.match(as_of):
                errs.append("%s pit_safe 但缺 evidence_as_of_date" % tag)
            elif as_of > ident:
                errs.append("%s evidence_as_of_date %s 晚于识别日 %s" % (tag, as_of, ident))
            sup = evd.get("supporting_evidence") or []
            if not sup:
                errs.append("%s pit_safe 但没有任何支持性证据" % tag)
            for x in sup:
                d = str(x.get("date") or "")
                if not DATE_RE.match(d):
                    errs.append("%s 支持性证据缺日期：%r" % (tag, d))
                elif d > ident:
                    errs.append("%s 支持性证据 %s 晚于识别日 %s" % (tag, d, ident))
            ph_dates = {str(x.get("date") or "") for x in (evd.get("posthoc_background") or [])}
            ph_dates |= {str(x.get("date") or "")
                         for x in (evd.get("retrospective_limit_up_days") or [])}
            ph_dates = {d for d in ph_dates if DATE_RE.match(d)}
            for d in sorted(ph_dates):
                if d <= ident:
                    errs.append("%s 事后字段里出现不晚于识别日的日期 %s" % (tag, d))
            # ★ 泄漏检查：事后日期不得出现在支持性文字里
            for fld in SUPPORT_TEXT_FIELDS:
                for d in _leaked_dates(evd.get(fld), ph_dates):
                    errs.append("%s 支持性字段 `%s` 泄漏了识别日之后的日期 %s" % (tag, fld, d))
            for d in _leaked_dates(r.get("notes"), ph_dates):
                errs.append("%s `notes` 泄漏了识别日之后的日期 %s" % (tag, d))
            for i, x in enumerate(sup):
                for d in _leaked_dates(x.get("text"), ph_dates):
                    errs.append("%s 支持性证据[%d] 文本泄漏了识别日之后的日期 %s" % (tag, i, d))
            # ★ 自动判据
            if r.get("role") == "PIT_MARKET_OBSERVED" and r.get("support_level") == "AUTO_RULE_MET":
                days = [str(x.get("date") or "")
                        for x in (evd.get("limit_up_days_as_of") or [])]
                if len(days) < 2:
                    errs.append("%s AUTO_RULE_MET 但截至识别日信号不足 2 次" % tag)
                elif cal_index is not None:
                    pairs = [(a, b) for a, b in zip(days, days[1:])
                             if cal_index.get(b, -99) - cal_index.get(a, -99) == 1]
                    if not pairs:
                        errs.append("%s AUTO_RULE_MET 但截至识别日没有连板" % tag)
                    elif ident != pairs[0][1]:
                        errs.append("%s AUTO_RULE_MET 但识别日不是首次连板的第二个信号日" % tag)
    return errs


def derive_report_roles(evidence_ev, event, ev_rel=None):
    """从参与者证据的**报道背书**推导 PIT 角色（识别日 = 报道发布日）。

    ★★ v0.30：识别日**只能**是 `report.published_at`（发布日），不得用 `fact_date`（事实日）。
      · 没有 `published_at` → 不产生角色（宁可留白，不用事实日冒充）；
      · `reported_move_backed=false`（报道对不上该股）→ 不产生角色；
      · 角色上限 `PIT_MEDIA_NAMED_MOVER`：报道点名 + 涨跌 ≠ 龙头。
    ★★ v0.32：`source_record` 取**本次实际加载的输入路径**（`ev_rel`），
      不再硬编码旧版 `participant_evidence_v0_3.json`。
    """
    ev_rel = ev_rel or EVIDENCE_REL
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
            "support_level": "REPORT_BACKED",
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
                # ★★ v0.32：统一的支持性证据清单（带日期）+ 截止日
                "evidence_as_of_date": pub,
                "supporting_evidence": [{
                    "date": pub,
                    "text": ("%s（发布日 %s；事实日 %s）"
                             % (rep.get("publisher") or "同期报道", pub,
                                rep.get("fact_date") or "未标注")),
                    "kind": "REPORT",
                }],
                "posthoc_background": [],
                "posthoc_note": None,
            },
            "pit_safe": True,
            "posthoc": False,
            "support_limits": [],
            "notes": ("报道点名并给出涨跌幅（%s）；报道**未**称其为龙头，故只记「被报道点名的参与者」"
                      % {"REPORT_CONFIRMED_LIMIT_UP": "报道明确涨停",
                         "REPORT_CONFIRMED_GAIN": "报道给出当日涨幅",
                         "REPORT_CONFIRMED_WINDOW_GAIN": "报道给出区间涨幅",
                         "REPORT_CONFIRMED_NAMED": "报道点名"}.get(st, "报道点名"))
                     + ("；★ 无原文链接 → 尚无法独立核验" if not rep.get("url") else ""),
            # ★★ v0.32：与**实际输入**一致（原为硬编码 v0_3，与事件级 source_records 的 v0_4 冲突）
            "source_record": ev_rel,
        })
    return out


# ---------------------------------------------------------------- 盘面可观察角色

def limit_band(ticker, date):
    """A 股涨跌停幅度区间带（按板块与日期；**用带不用阈值**）。

    ★ 创业板 2020-08-24 前 10%、之后 20%；科创板（688）20%；主板 10%。
    ★ ST（5%）无法从库内判定（`securities` 无 ST 标记）→ 落在带外，天然不被识别
      （漏报方向，可接受）；qfq 噪声把价格拉到带内时才可能误报，由双口径核验兜底。
    """
    t = ticker or ""
    if t.startswith("688"):
        return (19.5, 21.2)
    if t.startswith("300"):
        return (19.5, 21.2) if date >= "2020-08-24" else (9.8, 10.6)
    return (9.8, 10.6)


# ★ 公司行为日判定阈值：原始价单日跳变超出 A 股日涨跌停可能范围 → 拆股 / 送转 / 大额除权
ACTION_DAY_PCT = 21.6


def daily_change(conn, sid, dt, ticker):
    """单日涨跌幅（**双口径交叉核验**）—— 返回 None 表示无法计算。

    v0.31 审计发现（`research/research/reports/limit_up_audit_v0_1.json`）：
      · 库内**没有** `pre_close`，官方涨跌幅只能近似；
      · 该 provider 的前复权是**仿射**变换（`adj_close ≈ k·raw_close − c`，k/c 只在公司行为日变化），
        所以 `adj_close` 比值会**系统性偏离**官方涨跌幅（偏移越大越明显）；
      · 原始价收盘环比在**非行为日**等于官方涨跌幅。
    ⇒ 规则：
      · 行为日（|raw 环比| > 21.6%）→ 用复权环比（`adjusted_ratio_action_day`）；
      · 非行为日 → 用原始价环比；同时用复权环比**交叉核验**：
          · 两者都落在涨停带 → `both_series_agree`（最可信）；
          · 只有复权在带内、原始价略低 → 当日除息，官方应以复权为准
            （`adjusted_ratio_ex_dividend`）；
          · 只有原始价在带内 → **不确认**（复权说没有，可能是复权噪声）；
          · 都不在带内 → 非信号。
    """
    cur = conn.execute(
        "SELECT a.trade_date td, r.close raw_close, a.adj_close adj_close "
        "FROM market_daily a JOIN market_daily r "
        "  ON r.series_id=a.series_id AND r.trade_date=a.trade_date AND r.price_type='raw' "
        "WHERE a.series_id=? AND a.price_type='adjusted' AND a.trade_date=?",
        (sid, dt)).fetchone()
    prv = conn.execute(
        "SELECT a.trade_date td, r.close raw_close, a.adj_close adj_close "
        "FROM market_daily a JOIN market_daily r "
        "  ON r.series_id=a.series_id AND r.trade_date=a.trade_date AND r.price_type='raw' "
        "WHERE a.series_id=? AND a.price_type='adjusted' AND a.trade_date<? "
        "ORDER BY a.trade_date DESC LIMIT 1", (sid, dt)).fetchone()
    if not (cur and prv):
        return None
    raw_pct = adj_pct = None
    if cur["raw_close"] and prv["raw_close"]:
        raw_pct = (cur["raw_close"] / prv["raw_close"] - 1.0) * 100.0
    if cur["adj_close"] and prv["adj_close"]:
        adj_pct = (cur["adj_close"] / prv["adj_close"] - 1.0) * 100.0
    if raw_pct is None and adj_pct is None:
        return None
    lo, hi = limit_band(ticker, dt)
    if raw_pct is not None and abs(raw_pct) > ACTION_DAY_PCT:
        if adj_pct is None:
            return None
        return {"pct": adj_pct, "basis": "adjusted_ratio_action_day",
                "raw_pct": round(raw_pct, 3), "adjusted_pct": round(adj_pct, 3),
                "corroborated": False, "prev_date": prv["td"]}
    in_raw = raw_pct is not None and lo <= raw_pct <= hi
    in_adj = adj_pct is not None and lo <= adj_pct <= hi
    if in_raw and in_adj:
        return {"pct": raw_pct, "basis": "both_series_agree",
                "raw_pct": round(raw_pct, 3), "adjusted_pct": round(adj_pct, 3),
                "corroborated": True, "prev_date": prv["td"]}
    if in_adj and not in_raw:
        return {"pct": adj_pct, "basis": "adjusted_ratio_ex_dividend",
                "raw_pct": round(raw_pct, 3) if raw_pct is not None else None,
                "adjusted_pct": round(adj_pct, 3),
                "corroborated": False, "prev_date": prv["td"]}
    return None


def limit_up_signals(conn, sid, ticker, start, end):
    """窗口内的涨停信号日（双口径核验后的**候选**，不是交易所官方认定）。"""
    out = []
    for r in conn.execute(
            "SELECT trade_date FROM market_daily "
            "WHERE series_id=? AND price_type='adjusted' AND trade_date BETWEEN ? AND ? "
            "ORDER BY trade_date", (sid, start, end)).fetchall():
        chg = daily_change(conn, sid, r["trade_date"], ticker)
        if chg:
            out.append({"date": r["trade_date"], "pct": round(chg["pct"], 2),
                        "basis": chg["basis"], "corroborated": chg["corroborated"]})
    return out


def derive_market_roles(conn, event, evidence_ev, cal_index, ev_rel=None):
    """从**行情库**识别「当时盘面可观察的市场核心」—— 判据：**连板**（相邻交易日信号 ≥2）。

    ★★ v0.31 PIT 时间封口：
      · 角色的成立判断**只用** `date <= identified_date` 的信号；
      · 证据拆成两部分：`limit_up_days_as_of`（截至识别日，**支持**角色）与
        `retrospective_limit_up_days`（识别日之后，**仅事后观察**，不参与成立判断）；
      · `evidence_as_of_date` = `identified_date`；
      · `pit_safe` 由**支持性证据的时点**决定（全部 ≤ 识别日），
        不是只检查识别日是否早于窗口结束日。
    ★ 这是「复权/原始价区间信号」，**不是**交易所官方涨停认定，也不等于龙头。
    """
    window = (event.get("market_performance") or {}).get("window")
    if not window:
        return []
    already = {r["security_id"] for r in derive_report_roles(evidence_ev, event, ev_rel)
               if r["security_id"]}
    out = []
    for p in event.get("participants") or []:
        sid = p["security_id"]
        if sid in already:
            continue
        signals = limit_up_signals(conn, sid, p.get("ticker"), window[0], window[1])
        if len(signals) < 2:
            continue
        pairs = [(a, b) for a, b in zip(signals, signals[1:])
                 if cal_index.get(b["date"], -99) - cal_index.get(a["date"], -99) == 1]
        if not pairs:
            continue
        first_pair = pairs[0]
        ident = first_pair[1]["date"]
        # ★★ 只用识别日之前（含）的信号作为**支持性证据**
        as_of = [x for x in signals if x["date"] <= ident]
        retro = [x for x in signals if x["date"] > ident]
        out.append({
            "security_id": sid,
            "source_security_id": sid,
            "name": p.get("name"),
            "binding": {"bound_to": sid, "status": "BOUND",
                        "method": "FROM_EVENT_PARTICIPANTS",
                        "note": "角色由该事件参与者的行情序列直接计算，id 一致"},
            "role": "PIT_MARKET_OBSERVED",
            "identified_date": ident,
            "identification_type": "market_observed",
            "confidence": "medium",
            "support_level": "AUTO_RULE_MET",
            "evidence": {
                "source_type": "当日盘面可观察信息（无媒体定性）",
                "source_text": "market_data.db · raw/adjusted 收盘日变化（双口径交叉核验）",
                "url": None,
                "published_at": ident,
                "evidence_as_of_date": ident,
                "summary": ("首次连板 %s→%s（%.2f%% → %.2f%%）；截至识别日的信号 %d 次"
                            % (first_pair[0]["date"], first_pair[1]["date"],
                               first_pair[0]["pct"], first_pair[1]["pct"], len(as_of))),
                # ★★ PIT 支持性证据（≤ 识别日）
                "limit_up_days_as_of": as_of,
                # ★★ v0.32：统一的支持性证据清单（与 CSV / 报道角色同构）
                "supporting_evidence": [
                    {"date": x["date"],
                     "text": ("涨停信号 %.2f%%（%s）" % (x["pct"], x["basis"])),
                     "kind": "LIMIT_UP_SIGNAL"} for x in as_of
                ],
                # ★★ 事后观察（> 识别日）—— 不得参与成立判断
                "retrospective_limit_up_days": retro,
                "posthoc_background": [
                    {"date": x["date"],
                     "text": ("识别日之后的涨停信号 %.2f%%（%s）—— 仅事后统计"
                              % (x["pct"], x["basis"])),
                     "kind": "SUBSEQUENT_FACT"} for x in retro
                ],
                "retrospective_note": ("★ 以下为**识别日之后**才发生的信号，属事后观察，"
                                       "**不**参与本角色的成立判断，也不得用来证明当时已可识别"),
                "rule": ("信号判据：非公司行为日取原始价收盘环比，行为日取复权环比；"
                         "两者都落在板块涨停带内才记 `both_series_agree`，"
                         "仅复权在带内记 `adjusted_ratio_ex_dividend`（当日除息），"
                         "仅原始价在带内**不确认**。板块带：主板 9.8–10.6%；"
                         "创业板 2020-08-24 前 9.8–10.6%、之后 19.5–21.2%；科创板 19.5–21.2%；"
                         "ST 状态无法从库内判定 —— 主板 ST（2026-07-06 前 5%）与创业板改革前 ST（5%）"
                         "落在带外（漏报方向），创业板/科创板 ST 与主板新规后 ST 与普通股同带"),
                "audit": "research/research/reports/limit_up_audit_v0_3.json",
            },
            "pit_safe": bool(all(x["date"] <= ident for x in as_of)),
            "posthoc": False,
            "support_limits": [],
            "notes": ("★ 盘面可观察：截至识别日已有 %d 次涨停信号、至少一次连板 → "
                      "当时「有资金持续参与」是可观察事实；**但没有任何媒体定性**，也不等于龙头"
                      % len(as_of))
                     + ("；★ 另有 %d 次识别日之后的信号，仅为事后统计" % len(retro) if retro else ""),
            "source_record": "research/database/market_data.db（market_daily.raw / .adjusted）",
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
    # ★★ v0.32：来源路径只有一个真相 —— 用**实际加载的产物版本**反推相对路径，
    #   并与常量交叉核对（防止「输入已是 v0_4、派生角色却写 v0_3」再次发生）。
    ev_ver = str(evid.get("artifact_version") or "").replace(".", "_")
    ev_rel = "research/current/participant_evidence_v%s.json" % ev_ver
    if not os.path.exists(os.path.join(REPO, ev_rel)):
        raise SystemExit("FAIL: 输入产物路径不存在：%s" % ev_rel)
    if ev_rel != EVIDENCE_REL:
        raise SystemExit("FAIL: 输入产物版本 %s 与常量 %s 不一致" % (ev_rel, EVIDENCE_REL))
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
                media_roles = derive_report_roles(ev_e, e, ev_rel)
                if source:
                    # 有正式 PIT 研究的事件：以**研究记录**为准，不混入自动盘面角色
                    # ★ v0.43：每个事件读自己的 CSV（此前所有事件共用同一份 → 会串数据）
                    pit_rows = load_pit_rows(os.path.join(REPO, source["csv"]))
                    binding = bind_pit_ids(eid, pit_rows, e.get("participants") or [], secs)
                    roles = derive_pit_roles(eid, pit_rows, binding, source["csv"])
                    status = "RESEARCHED_PIT"
                else:
                    market_roles = derive_market_roles(conn, e, ev_e, cal_index, ev_rel)
                    roles = media_roles + market_roles
                    if media_roles:
                        status = "DERIVED_FROM_REPORT"
                    elif market_roles:
                        status = "DERIVED_FROM_MARKET"
                    else:
                        status = "NOT_RESEARCHED"
                tally[status] += 1
                # ★★ v0.31：pit_safe 由**支持性证据的时点**决定，而不是只看窗口结束日
                for r in roles:
                    evd = r.get("evidence") or {}
                    ev_as_of = evd.get("evidence_as_of_date")
                    sup = evd.get("supporting_evidence") or []
                    if ev_as_of is not None or sup:
                        # ★★ v0.32：截止日 + **每条支持性证据的日期**都要 ≤ 识别日
                        r["pit_safe"] = bool(
                            ev_as_of and ev_as_of <= r["identified_date"]
                            and sup and all(x.get("date") and x["date"] <= r["identified_date"]
                                            for x in sup))
                    if window and r["identified_date"] > window[1]:
                        r["pit_safe"] = False
                        r["notes"] = (r["notes"] or "") + "；★ 识别日晚于事件窗口结束日 → 非 PIT"
                    if not r.get("pit_safe"):
                        r["notes"] = (r["notes"] or "") + "；★ 支持性证据时点不满足 PIT 纪律"
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
                idents = [r["identified_date"] for r in roles]
                events[eid] = {
                    "theme_id": entry["theme_id"],
                    "object_id": oid,
                    "window": window,
                    # ★★ v0.31：三种窗口分开记，不得互相冒充
                    "window_semantics": {
                        "market_performance_window": window,
                        "pit_observation_window": ([min(idents), max(idents)] if idents else None),
                        "note": ("market_performance_window = 行情统计窗口；"
                                 "pit_observation_window = 本产物角色识别日的实际跨度。"
                                 "★ 识别日早于行情窗口起点 ≠ 错误：PIT 研究记录（如 2024 Robotaxi "
                                 "的 07-08 切片）本就可早于行情窗口，其真实日期与来源另行保留。"),
                    },
                    "research_status": status,
                    "source_records": ([source["csv"], source["record"]] if source else
                                       ([ev_rel] if media_roles else []) +
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
            "support_levels": {},
            "pit_safe_roles": 0,
            "pit_safe_violations": 0,
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
    by_level: dict = {}
    pit_safe = 0
    for v in doc["events"].values():
        for r in v["roles"]:
            by_type[r["role"]] = by_type.get(r["role"], 0) + 1
            lv = r.get("support_level") or "UNSPECIFIED"
            by_level[lv] = by_level.get(lv, 0) + 1
            if r.get("pit_safe"):
                pit_safe += 1
    doc["summary"]["roles_by_type"] = by_type
    doc["summary"]["support_levels"] = by_level
    doc["summary"]["pit_safe_roles"] = pit_safe
    # ★★ v0.32：统一 PIT 合同（所有角色类别，含 legacy CSV market_breadth）
    cal_index = None
    try:
        _c = db.connect()
        cal_index = {r[0]: i for i, r in enumerate(
            _c.execute("SELECT trade_date FROM trading_calendar ORDER BY trade_date"))}
        _c.close()
    except Exception:  # noqa: BLE001 —— 无行情库时只跳过连板校验（信号数仍校验）
        cal_index = None
    violations = validate_pit_contract(doc, cal_index)
    doc["summary"]["pit_safe_violations"] = len(violations)

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
        if violations:
            print("FAIL: PIT 时点合同不满足（%d 条）：" % len(violations))
            for x in violations[:8]:
                print("  · " + x)
            return 1
        # ★ PIT 纪律：事后集合不得标 pit_safe
        for eid, ev in cur["events"].items():
            for r in ev["roles"]:
                if r["role"] == "POSTHOC_LEADER_SET" and r.get("pit_safe"):
                    print("FAIL: %s/%s 事后角色被标为 pit_safe" % (eid, r["security_id"]))
                    return 1
                # ★★ v0.31 PIT 封口：pit_safe 角色的支持性证据不得晚于识别日
                if r.get("pit_safe"):
                    evd = r.get("evidence") or {}
                    ident = r.get("identified_date")
                    for x in (evd.get("limit_up_days_as_of") or []):
                        if x["date"] > ident:
                            print("FAIL: %s/%s PIT 证据含识别日之后的信号 %s"
                                  % (eid, r["security_id"], x["date"]))
                            return 1
                    if evd.get("evidence_as_of_date") and evd["evidence_as_of_date"] > ident:
                        print("FAIL: %s/%s evidence_as_of_date 晚于 identified_date"
                              % (eid, r["security_id"]))
                        return 1
        print("PASS: 角色产物一致（%d 事件 · %d 条角色 · %s · support_level %s · PIT 合同 0 违规）"
              % (doc["summary"]["events"], sum(by_type.values()), by_type, by_level))
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
