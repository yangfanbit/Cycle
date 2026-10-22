#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_participant_evidence_v0_1.py —— 参与者**证据维度**结构化产物（v0.28）。

## 为什么需要它

历史地图里每只股票身上混着**四种不同性质**的信息，此前只能从自由文本（`rationale` /
`business_mechanism` / `registry_role`）里读出来：

1. 它**参与过**当次行情吗？（同期报道点名 / 报道给出涨幅 / 报道明确涨停）
2. 它的业务与**题材机制**有关吗？（有机制说明 ≠ 驱动了行情）
3. 它在 **Research 对象**里被登记成什么角色？（`leader` / `representative`… —— 这是
   研究对象的内部登记，**不等于**历史炒作龙头）
4. 它是**反例** / **不同机制轴** / **证据不足**吗？

本脚本把四者拆成**独立字段**，每条都带**依据**与**来源**，并显式列出**无法判定**的项。
★ 不新增任何历史事实：只把既有字段（`evidence_level` / `reported_move` / `business_mechanism` /
`registry_role` / `category`）转成机器可读的维度，并**核对 `registry_role` 是否与库内
`campaign_securities.role` 一致**。

## 三维度定义（写进产物合同）

- `market_participation`：**同期报道**能证明的市场表现。
  `REPORTED_LIMIT_UP`（报道明确涨停/连板）> `REPORTED_DAILY_GAIN`（报道给出**当日**涨幅）
  > `REPORTED_WINDOW_GAIN`（报道给出**区间**涨幅）> `REPORTED_NAMED_ONLY`（报道点名但未给涨幅）
  > `NO_REPORTED_EVIDENCE`（本轮**未找到**点名报道 —— **不等于**当日没涨）
  > `UNKNOWN`（证据不足，无法判断）。
- `mechanism_relation`：业务与题材机制的关系。
  `DIRECT`（有机制说明）/ `SPILLOVER`（产业链扩散）/ `UNSPECIFIED`（参与行情但未登记机制说明）
  / `DIFFERENT_AXIS`（反例：机制轴不同）/ `UNKNOWN`。
- `registry_role`：**Research 对象内部登记**的角色 + 出处。
  `VERIFIED_DB`（与 `campaign_securities.role` 逐字一致）/ `SECURITY_IN_OBJECT_ROLE_UNVERIFIED`
  （RC 无角色表：只能确认证券属于该对象，**角色本身无机器可核来源**）/ `null`。

★ `study_standing`（INCLUDED / COUNTER_EXAMPLE / INSUFFICIENT）来自既有 `category`，单独一列。

## 用法

    python research/scripts/build_participant_evidence_v0_1.py --check    # 只读（CI 门禁）
    python research/scripts/build_participant_evidence_v0_1.py --write    # 生成 v0_1（拒绝覆盖）
    python research/scripts/build_participant_evidence_v0_1.py --write --version 2
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db  # noqa: E402

REPO = db.REPO_ROOT
CURRENT = os.path.join(REPO, "research", "current")
INDEX_PATH = os.path.join(CURRENT, "historical_event_maps_index.json")
EXPORT_PATH = os.path.join(REPO, "exports", "timeline_export_v1.json")
GENERATED_AT = "2026-10-21"

LIMIT_UP_RE = re.compile(r"涨停|(?:\d+\s*天\s*\d+\s*板)|(?:\d+\s*连板)")
WINDOW_RE = re.compile(r"交易日|(?:\d+\s*天)")
GAIN_RE = re.compile(r"[+\-−]?\s*\d+(?:\.\d+)?\s*%|涨逾|涨超|涨幅")
# ★★ 角色线索可能只写在 `rationale` 里（如「库内 Campaign `C-2023-POWEROP-THERMAL` 登记的标的（role=leader）」）
ROLE_IN_TEXT_RE = re.compile(r"role\s*=\s*(leader|second_leader|representative|follow)")
OBJ_IN_TEXT_RE = re.compile(r"`((?:C|RC)-\d{4}-[A-Z0-9\-]+)`")

# ★ category → 研究立场（三种纳入类别 = INCLUDED）
STUDY_STANDING_OF = {
    "MARKET_PARTICIPANT": "INCLUDED",
    "MECHANISM_DIRECT": "INCLUDED",
    "SPILLOVER": "INCLUDED",
    "COUNTER_EXAMPLE": "COUNTER_EXAMPLE",
    "INSUFFICIENT": "INSUFFICIENT",
}


def load_index():
    return json.load(open(INDEX_PATH, encoding="utf-8"))


def load_theme_docs(index):
    for entry in index.get("maps") or []:
        path = os.path.join(CURRENT, entry["file"])
        if os.path.exists(path):
            yield entry, json.load(open(path, encoding="utf-8"))


def load_campaign_roles(conn):
    return {(c, s): r for c, s, r in
            conn.execute("SELECT campaign_id, security_id, role FROM campaign_securities")}


def load_rc_securities():
    doc = json.load(open(EXPORT_PATH, encoding="utf-8"))
    out = {}
    for rc in doc.get("research_candidates") or []:
        oid = rc.get("campaign_id") or rc.get("object_id")
        out[oid] = set(rc.get("security_ids") or [])
    return out


DB_MARKERS = ("DB ", "export", "注册表", "本轮研究", "工作流", "库内", "securities")
REPORT_MARKERS = ("报", "新闻", "证券网", "每经", "财经", "时报", "日报")
INDIRECT_CAVEAT = ("偏间接", "未找到其产品", "未找到其", "不同轴", "非直接", "运营侧")


URL_RE = re.compile(r"https?://[^\s（）()]+")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
INHERIT_MARKERS = ("同上", "同上报")
# ★ 「多股汇总」型描述：能支持「该报道列了多只股票及其涨跌」，但**不能**证明某只股票在其中
AGGREGATE_RE = re.compile(r"(?:多只|十余只|\d+\s*只)个股|个股[^。；]{0,14}涨停|"
                          r"板块[^。；]{0,14}(?:大涨|拉升|活跃)|概念股[^。；]{0,10}(?:走强|拉升|爆发)")


def parse_catalysts(event: dict) -> list:
    """把事件 `catalysts` 解析成**事实日期 / 发布日期 / 媒体 / URL** 四件事分开的结构。

    ★★ v0.30 修复的根因：`catalyst.date` 是**事实日期**（采访日 / 盘面日），
       **不是**报道发布日期。发布日只能从 `source` 文本里读，或从「同上」继承。
       v0.29 把 catalyst.date 当报道日 → 超级真菌 8 条记录的识别日变成 2019-04-08，
       而它们依据的报道实际发布于 2019-04-11（**识别日早于报道存在 = 时间泄漏**）。
    """
    out, prev_pub, prev_publisher = [], None, None
    for i, c in enumerate(event.get("catalysts") or []):
        src = (c.get("source") or "").strip()
        inherit = any(m in src for m in INHERIT_MARKERS)
        m = DATE_RE.search(src)
        if m:
            pub, pub_src = m.group(1), "SOURCE_TEXT"
            publisher = re.split(r"[（(]", src[:m.start()])[0].strip(" ·、") or None
        elif inherit and prev_pub:
            pub, pub_src, publisher = prev_pub, "INHERITED_FROM_PREVIOUS_CATALYST", prev_publisher
        else:
            pub = None
            pub_src = "INHERIT_WITHOUT_PREVIOUS" if inherit else "MISSING"
            publisher = re.split(r"[（(]", src)[0].strip(" ·、") or None
        u = URL_RE.search(src)
        out.append({
            "index": i,
            "fact_date": c.get("date"),
            "published_at": pub,
            "published_at_source": pub_src,
            "publisher": publisher,
            "url": u.group(0) if u else None,
            "text": c.get("text"),
            "raw_source": src,
        })
        if pub:
            prev_pub, prev_publisher = pub, publisher
    return out


def resolve_participant_sources(participants: list) -> list:
    """★★ 参与者 source 的「同上 / 同上报」要**在参与者列表内**继承，不能靠第一条 catalyst 猜。

    返回与 participants 等长的列表：{raw, resolved, inherited}。
    第一条就写「同上报」→ `resolved=None`（下文再按「事件只有一篇报道」兜底，否则视为无法定位）。
    """
    out, prev = [], None
    for p in participants:
        raw = (p.get("source") or "").strip()
        if any(m in raw for m in INHERIT_MARKERS):
            out.append({"raw": raw, "resolved": prev, "inherited": True})
        else:
            out.append({"raw": raw, "resolved": raw or None, "inherited": False})
            if raw:
                prev = raw
    return out


def match_backing(p: dict, resolved_src, cats: list) -> dict | None:
    """★★ v0.30：把「这只股票的涨跌事实」与**能支持它**的那篇报道对上。

    禁止的两条捷径（v0.29 的 bug）：
      · 取第一条报道型 catalyst；
      · 媒体名相同就当成依据。

    允许的两级关联：
      1. `NAME_IN_TEXT` —— 报道正文**点名该股**（最强；若来源写了日期，优先该日发布的那篇）。
      2. `REPORT_LIST_AGGREGATE` —— 报道正文明确是「多股汇总（列出多只个股及其涨跌）」，
         且能唯一定位到一篇（来源日期 / 媒体名匹配，或事件只有这一篇汇总型报道）。
         ★ 这一级只支持「该股属于当次被报道的群体」，个股归属仍依赖研究记录的转录。
      对不上 → `None`（→ `UNVERIFIED_REPORT_ATTRIBUTION`）。
    """
    name = p.get("name") or ""
    claim_date = None
    if resolved_src:
        m = DATE_RE.search(resolved_src)
        claim_date = m.group(1) if m else None

    named = [c for c in cats if name and name in (c.get("text") or "")]
    if named:
        if claim_date:
            on_claim = [c for c in named if c.get("published_at") == claim_date]
            if on_claim:
                named = on_claim
        c = sorted(named, key=lambda x: (x.get("published_at") or "9999-12-31", x["index"]))[0]
        return {"attribution": "NAME_IN_TEXT", "catalyst": c}

    media = None
    if resolved_src:
        media = re.split(r"[（(]", resolved_src)[0].strip(" ·、") or None
    cands = []
    for c in cats:
        if not AGGREGATE_RE.search(c.get("text") or ""):
            continue
        if claim_date and c.get("published_at") != claim_date:
            continue
        if not claim_date and media:
            src = c.get("raw_source") or ""
            if media not in src and c.get("publisher") != media:
                continue
        cands.append(c)
    if len(cands) == 1:
        return {"attribution": "REPORT_LIST_AGGREGATE", "catalyst": cands[0]}
    if len(cands) > 1 and claim_date:
        return {"attribution": "REPORT_LIST_AGGREGATE",
                "catalyst": sorted(cands, key=lambda x: x["index"])[0]}
    return None


def classify_source(p: dict, resolved_src, cats: list) -> dict:
    """来源类型 + **可支持该股的报道**。`kind` 只描述来源文本性质，不等于有背书。

    · `REPORT_WITH_URL` / `REPORT_NAMED_NO_URL` —— 来源指向同期报道（是否有 URL 另说）
    · `DB_OR_RESEARCH_ONLY` —— 只有数据库 / 注册表 / 研究轮次说明（**不是**同期报道）
    · `NOT_RECORDED` —— 无任何来源记录（≠ 已检索未找到）
    · `UNKNOWN_SOURCE` —— 有文本但无法归类
    """
    src = (resolved_src or "").strip()
    raw = (p.get("source") or "").strip()
    if not raw:
        return {"kind": "NOT_RECORDED", "text": None, "backing": None}
    if any(m in raw for m in DB_MARKERS):
        # ★★ v0.30 决定**不**从「事件催化剂正文点名」升级为报道背书：
        #   实测这些催化剂多为「库内 events（market）· 来源：东方财富历史行情接口」这类**行情数据源**
        #   或**无发布日**的转述，且出现过「跌停报道被当成参与证据」（CONS-2016-BAIJIU / 贵州茅台）。
        #   ⇒ 只有当参与者**自己的来源**指向报道时才算报道背书；催化剂的点名另在角色层处理。
        return {"kind": "DB_OR_RESEARCH_ONLY", "text": raw, "backing": None}
    if any(m in raw for m in INHERIT_MARKERS) or any(m in src for m in REPORT_MARKERS):
        backing = match_backing(p, src or None, cats)
        if backing:
            c = backing["catalyst"]
            kind = "REPORT_WITH_URL" if c.get("url") else "REPORT_NAMED_NO_URL"
        else:
            # 来源指向报道，但无法把任何一篇报道与这只股票的涨跌事实对上
            kind = "REPORT_WITH_URL" if any(c.get("url") for c in cats) else "REPORT_NAMED_NO_URL"
        return {"kind": kind, "text": src or raw, "backing": backing}
    return {"kind": "UNKNOWN_SOURCE", "text": src or raw, "backing": None}


def market_participation(p: dict, event: dict, cats: list, resolved_src) -> dict:
    """同期报道能证明什么 —— ★ 三层判定：来源性质 → **报道能否支持该股** → 涨幅文本。

    ★★ v0.30：`reported_move_backed` **不再**只看来源类型是不是 `REPORT_*`；
      必须存在能支持「这只股票 + 这个涨跌事实」的报道（`match_backing` 非空）。
      来源指向报道但对不上任何一篇 → `UNVERIFIED_REPORT_ATTRIBUTION`（新状态，诚实留白）。
    """
    backing = classify_source(p, resolved_src, cats)
    move = (p.get("reported_move") or "").strip()
    bk = backing["backing"]
    out = {
        "source_kind": backing["kind"],
        "source_kind_from": backing.get("kind_from", "PARTICIPANT_SOURCE"),
        "source_text": backing["text"],
        "reported_move": move or None,
        "reported_move_backed": bool(move) and bk is not None,
        "attribution": bk["attribution"] if bk else None,
    }
    if bk:
        c = bk["catalyst"]
        out["report"] = {
            "published_at": c.get("published_at"),
            "published_at_source": c.get("published_at_source"),
            "fact_date": c.get("fact_date"),
            "publisher": c.get("publisher"),
            "url": c.get("url"),
            "text": c.get("text"),
            "attribution": bk["attribution"],
        }
        out["identified_date"] = c.get("published_at")

    report_kind = backing["kind"] in ("REPORT_WITH_URL", "REPORT_NAMED_NO_URL")
    if report_kind and bk is None:
        st = "UNVERIFIED_REPORT_ATTRIBUTION"
        basis = ("来源指向同期报道，但**无法把任何一篇报道与这只股票的涨跌事实对上**"
                 "（报道正文未点名该股，且没有可定位的「多股汇总」报道）"
                 "—— 不等于当日没涨，只表示这条涨跌**没有可核验的报道出处**")
    elif report_kind and not out.get("identified_date"):
        st = "UNVERIFIED_REPORT_ATTRIBUTION"
        basis = ("报道可对上该股，但**发布日不可确定**（来源未写日期 / 「同上」无前文）"
                 "—— 不给识别日，避免用事实日期冒充报道日")
        out["reported_move_backed"] = False
    elif report_kind:
        att = ("报道正文点名该股" if bk["attribution"] == "NAME_IN_TEXT"
               else "该报道为**多股汇总**（个股归属依研究记录转录，未逐只原文核验）")
        pub = out["identified_date"]
        fact = out["report"].get("fact_date")
        if move:
            if LIMIT_UP_RE.search(move):
                st, lvl = "REPORT_CONFIRMED_LIMIT_UP", "报道明确涨停 / 连板"
            elif WINDOW_RE.search(move) and GAIN_RE.search(move):
                st, lvl = "REPORT_CONFIRMED_WINDOW_GAIN", "报道给出**区间**涨幅（非单日）"
            elif GAIN_RE.search(move):
                st, lvl = "REPORT_CONFIRMED_GAIN", "报道给出涨幅"
            else:
                st, lvl = "REPORT_CONFIRMED_NAMED", "报道点名（未给出可解析涨幅）"
        else:
            st, lvl = "REPORT_CONFIRMED_NAMED", "报道点名（未给出涨幅）"
        basis = "%s；报道发布于 **%s**（事实日期 %s）；%s" % (lvl, pub, fact or "未记录", att)
    elif backing["kind"] == "DB_OR_RESEARCH_ONLY":
        st = "RESEARCH_OR_DB_ONLY"
        basis = ("只有数据库 / 注册表 / 研究轮次记录，**没有**同期报道背书"
                 + ("（附带的涨跌幅亦无报道出处）" if move else ""))
    elif backing["kind"] == "NOT_RECORDED":
        st, basis = "NOT_RECORDED", "本库无任何来源记录 —— 不等于已检索未找到，也不等于当日没涨"
    else:
        st, basis = "UNKNOWN", "来源文本无法归类"
    out["status"] = st
    out["basis"] = basis
    return out


def mechanism_relation(p: dict) -> dict:
    """★ v0.29：**不再**因 `business_mechanism` 非空就判直接机制。

    判据优先级：既有研究分类（`category`）→ caveat 里的反向结论 → 业务说明是否只是描述。
      · `DIRECT_CONFIRMED`              —— 研究已明确判定为直接机制相关
      · `INDIRECT_CONFIRMED`            —— 产业链扩散 / 研究自述偏间接
      · `BUSINESS_DESCRIBED_UNCONFIRMED`—— 有业务说明，但与本题材的直接关系**未被研究确认**
      · `NOT_STUDIED`                   —— 连业务说明都没有
      · `DIFFERENT_AXIS` / `UNKNOWN`
    """
    cat = p.get("category")
    mech = p.get("business_mechanism")
    caveat = p.get("business_mechanism_caveat") or ""
    if cat == "COUNTER_EXAMPLE":
        return {"status": "DIFFERENT_AXIS", "basis": "反例：机制轴与本题材不同", "caveat": caveat or None}
    if cat == "INSUFFICIENT":
        return {"status": "UNKNOWN", "basis": "证据不足，机制关系未确认", "caveat": caveat or None}
    if cat == "SPILLOVER":
        return {"status": "INDIRECT_CONFIRMED", "basis": mech or "产业链扩散（未登记逐条说明）",
                "caveat": caveat or None}
    if cat == "MECHANISM_DIRECT":
        if any(k in caveat for k in INDIRECT_CAVEAT):
            return {"status": "INDIRECT_CONFIRMED",
                    "basis": "研究分类为直接机制，但 caveat 自述偏间接 / 不同轴 → 按间接记",
                    "caveat": caveat}
        return {"status": "DIRECT_CONFIRMED", "basis": mech or "研究判定为直接机制相关",
                "caveat": caveat or None}
    # MARKET_PARTICIPANT：研究只判定「参与行情」，**没有**判定机制类别
    if mech:
        return {"status": "BUSINESS_DESCRIBED_UNCONFIRMED",
                "basis": "有业务说明，但该业务与本题材的**直接关系未被研究确认**"
                         "（category = MARKET_PARTICIPANT）", "caveat": caveat or None}
    return {"status": "NOT_STUDIED", "basis": "未登记业务机制说明，也未判定机制类别",
            "caveat": None}


def registry_role_of(p: dict, object_id, object_kind, roles, rc_secs) -> dict | None:
    """对象登记角色 + 出处。

    ★ v0.28 修：角色线索**可能只写在 `rationale` 里**（「…登记的标的（role=leader）」）。
      此时把它解析出来，但**必须**与库内 `campaign_securities` 对齐才算可核；
      对不上就如实标 `SECURITY_NOT_IN_OBJECT` / `ROLE_MISMATCH`，绝不直接采信文本。
    """
    role = p.get("registry_role")
    role_src = "participant.registry_role"
    if not role:
        m = ROLE_IN_TEXT_RE.search(p.get("rationale") or "")
        if not m:
            return None
        role = m.group(1)
        role_src = "participant.rationale 文本"
        if not object_id:
            om = OBJ_IN_TEXT_RE.search(p.get("rationale") or "")
            if om:
                object_id = om.group(1)
                object_kind = "campaign" if object_id.startswith("C-") else "research_candidate"
    sid = p["security_id"]
    if object_kind == "campaign" and object_id:
        dbv = roles.get((object_id, sid))
        if dbv == role:
            return {"role": role, "object_id": object_id, "object_kind": object_kind,
                    "verification": "VERIFIED_DB", "role_source": role_src,
                    "source": "cycle_research.db · campaign_securities.role（逐字一致；"
                              "角色声明来自 %s）" % role_src}
        if dbv is None:
            return {"role": role, "object_id": object_id, "object_kind": object_kind,
                    "verification": "SECURITY_NOT_IN_OBJECT", "role_source": role_src,
                    "source": "库内该对象无此证券登记 → 角色**无机器可核来源**"}
        return {"role": role, "object_id": object_id, "object_kind": object_kind,
                "verification": "ROLE_MISMATCH", "role_source": role_src,
                "source": "库内为 %s，文档写 %s" % (dbv, role)}
    # Research Candidate：库内无角色表，只能确认「证券属于该对象」
    if object_id and sid in (rc_secs.get(object_id) or set()):
        return {"role": role, "object_id": object_id, "object_kind": object_kind,
                "verification": "SECURITY_IN_OBJECT_ROLE_UNVERIFIED", "role_source": role_src,
                "source": "RC 无角色表：仅能确认证券属于该对象；**角色本身无机器可核来源**"}
    return {"role": role, "object_id": object_id, "object_kind": object_kind,
            "verification": "UNSOURCED", "role_source": role_src,
            "source": "未能在库内或导出中确认该证券属于该对象"}


def unknowns_of(p: dict, mp: dict, mr: dict, rr) -> list:
    out = []
    if mp["status"] in ("NOT_RECORDED", "UNKNOWN", "RESEARCH_OR_DB_ONLY",
                        "UNVERIFIED_REPORT_ATTRIBUTION"):
        out.append({"field": "market_participation",
                    "reason": "本库无同期报道背书（来源类型 %s）—— 需补当时报道 / 交易所披露"
                              "才能证明其在当次行情中的表现" % mp["source_kind"]})
    if mr["status"] in ("BUSINESS_DESCRIBED_UNCONFIRMED", "NOT_STUDIED", "UNKNOWN"):
        out.append({"field": "mechanism_relation",
                    "reason": "业务与本题材的**直接关系未被研究确认**"
                              "（有业务说明 ≠ 机制相关）"})
    if rr and rr["verification"] != "VERIFIED_DB":
        out.append({"field": "registry_role",
                    "reason": "角色无机器可核来源（%s）—— 只能作为**对象内部登记**引用，"
                              "不得当作历史炒作龙头" % rr["verification"]})
    if not rr:
        out.append({"field": "registry_role",
                    "reason": "该证券未在任何 Research 对象中登记角色"})
    return out


def build(conn) -> dict:
    index = load_index()
    roles = load_campaign_roles(conn)
    rc_secs = load_rc_securities()
    events = {}
    tally = {"market": {}, "mechanism": {}, "registry": {}, "standing": {}}
    for entry, doc in load_theme_docs(index):
        for e in doc.get("events") or []:
            cf = e.get("campaign_facts") or {}
            oid = cf.get("object_id") or cf.get("campaign_id")
            kind = cf.get("object_kind") or ("campaign" if cf.get("campaign_id") else None)
            parts = {}
            cats = parse_catalysts(e)
            resolved = resolve_participant_sources(e.get("participants") or [])
            for idx, p in enumerate(e.get("participants") or []):
                mp = market_participation(p, e, cats, resolved[idx]["resolved"])
                mr = mechanism_relation(p)
                rr = registry_role_of(p, oid, kind, roles, rc_secs)
                parts[p["security_id"]] = {
                    "name": p.get("name"),
                    "ticker": p.get("ticker"),
                    "evidence_level": p.get("evidence_level"),
                    # ★ 三种「纳入」类别都算 INCLUDED；只有反例 / 证据不足另列
                    "study_standing": STUDY_STANDING_OF.get(p.get("category"), "UNKNOWN"),
                    "market_participation": mp,
                    "mechanism_relation": mr,
                    "registry_role": rr,
                    "source_text": p.get("source"),
                    "unknowns": unknowns_of(p, mp, mr, rr),
                }
                tally["market"][mp["status"]] = tally["market"].get(mp["status"], 0) + 1
                tally["mechanism"][mr["status"]] = tally["mechanism"].get(mr["status"], 0) + 1
                v = rr["verification"] if rr else "NO_REGISTRY_ROLE"
                tally["registry"][v] = tally["registry"].get(v, 0) + 1
                st = parts[p["security_id"]]["study_standing"]
                tally["standing"][st] = tally["standing"].get(st, 0) + 1
            events[e["event_id"]] = {
                "theme_id": entry["theme_id"],
                "theme_file": entry["file"],
                "object_id": oid,
                "object_kind": kind,
                "participants": parts,
            }
    return {
        "artifact": "participant_evidence",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_participant_evidence_v0_1.py",
        "supersedes": None,
        "participant_evidence_contract": {
            "version": "participant_evidence_v1",
            "purpose": "把「同期市场表现 / 业务机制关系 / Research 对象登记角色 / 研究立场 / 无法判定」"
                       "拆成互不冒充的独立维度，并逐条给出依据与出处",
            "date_semantics": {
                "event_date": "事件窗口（题材文档 market_performance.window）",
                "catalyst_date": "★★ catalyst.date = **事实日期**（采访日 / 盘面日），**不是**报道发布日期",
                "published_at": "★★ 报道发布日期：只能从 catalyst.source 文本解析，或从「同上」继承上一条；无法确定 → null",
                "identified_date": "★★ PIT 可识别日 = published_at（**不得**用事实日期冒充）；无 published_at → 不给识别日",
                "rule": "published_at ≤ identified_date，且 identified_date 必须落在事件窗口内才允许 pit_safe",
            },
            "attribution": {
                "NAME_IN_TEXT": "报道正文点名该股（最强）",
                "REPORT_LIST_AGGREGATE": "报道为多股汇总（个股归属依研究记录转录，未逐只原文核验）",
            },
            "source_kind": {
                "REPORT_WITH_URL": "参与者 source 指向同期报道，且事件 catalyst 记录了 URL",
                "REPORT_NAMED_NO_URL": "指向同期报道，但本库未记录 URL（可追溯性弱一档）",
                "DB_OR_RESEARCH_ONLY": "★ 只有数据库 / 注册表 / 研究轮次说明 —— **不是**同期报道",
                "NOT_RECORDED": "★ 无任何来源记录 —— 不等于「已检索未找到」",
                "UNKNOWN_SOURCE": "有来源文本但无法归类",
            },
            "market_participation": {
                "REPORT_CONFIRMED_LIMIT_UP": "同期报道明确涨停 / 连板（仍只是「被报道点名」级别）",
                "REPORT_CONFIRMED_GAIN": "同期报道给出当日涨幅",
                "REPORT_CONFIRMED_WINDOW_GAIN": "同期报道给出**区间**涨幅（非单日）",
                "REPORT_CONFIRMED_NAMED": "同期报道点名但未给涨幅",
                "reported_move_backed": "★★ 涨跌幅文本是否**有能支持该股的报道**（false = 无可核验出处，不得当报道引用）",
                "UNVERIFIED_REPORT_ATTRIBUTION": "★★ 来源指向报道，但无法把任何一篇报道与该股的涨跌事实对上 → 不给报道日、不给识别日",
                "RESEARCH_OR_DB_ONLY": "★ 只有 DB / 注册表 / 研究记录 —— 不得说成「报道确认」",
                "NOT_RECORDED": "★ 无来源记录 —— 不等于当日没涨、不等于不是参与者",
                "UNKNOWN": "来源无法归类",
            },
            "mechanism_relation": {
                "DIRECT_CONFIRMED": "研究已明确判定为直接机制相关（≠ 驱动了当次行情）",
                "INDIRECT_CONFIRMED": "产业链扩散 / 研究自述偏间接",
                "BUSINESS_DESCRIBED_UNCONFIRMED": "★ 有业务说明，但与本题材的**直接关系未被研究确认**",
                "NOT_STUDIED": "未登记业务说明，也未判定机制类别",
                "DIFFERENT_AXIS": "反例：机制轴不同",
                "UNKNOWN": "证据不足",
            },
            "registry_role": {
                "VERIFIED_DB": "与 cycle_research.db · campaign_securities.role 逐字一致",
                "SECURITY_IN_OBJECT_ROLE_UNVERIFIED": "RC 无角色表：只能确认证券属于该对象，角色本身无机器可核来源",
                "SECURITY_NOT_IN_OBJECT": "库内该对象无此证券登记",
                "ROLE_MISMATCH": "库内角色与文档不一致（需人工裁定）",
                "UNSOURCED": "未能在库内或导出中确认归属",
                "★ 语义": "这是**Research 对象内部登记**，不是「历史炒作龙头」；两者必须分开显示",
            },
            "study_standing": "INCLUDED / COUNTER_EXAMPLE / INSUFFICIENT（来自既有 category）",
            "must_not": [
                "不得把 registry_role=leader 当作「当时的龙头」",
                "不得把 BUSINESS_VERIFIED 当作「参与过当次行情」",
                "★ 不得因 `business_mechanism` 非空就判「直接机制」—— 必须看研究分类",
                "★ 不得因 `evidence_level` 写 REPORT_NAMED 就说「报道点名」—— 必须看 source 类型",
                "不得把 NO_REPORTED_EVIDENCE 当作「当日没涨」",
                "不得用事后涨幅反推角色",
            ],
        },
        "summary": {
            "events": len(events),
            "participants": sum(len(v["participants"]) for v in events.values()),
            "market_participation": tally["market"],
            "mechanism_relation": tally["mechanism"],
            "registry_role_verification": tally["registry"],
            "study_standing": tally["standing"],
        },
        "events": events,
    }


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="构建参与者证据维度产物")
    ap.add_argument("--check", action="store_true", help="只读：重新推导并与已发布产物比对")
    ap.add_argument("--write", action="store_true", help="写入新版本（拒绝覆盖）")
    ap.add_argument("--version", type=int, default=1)
    a = ap.parse_args(argv)

    conn = db.connect()
    try:
        doc = build(conn)
    finally:
        conn.close()

    # ★ v0.29.1：`--check` 默认对齐**最新已有版本**（避免「忘了传 --version 就比对旧版」）
    version = a.version
    if a.check:
        existing = sorted(
            int(re.search(r"_v0_(\d+)\.json$", f).group(1))
            for f in os.listdir(CURRENT)
            if re.match(r"participant_evidence_v0_\d+\.json$", f))
        if existing:
            version = existing[-1]
    out = os.path.join(CURRENT, "participant_evidence_v0_%d.json" % version)
    if a.check:
        if not os.path.exists(out):
            print("FAIL: 产物不存在：%s" % os.path.relpath(out, REPO))
            return 1
        cur = json.load(open(out, encoding="utf-8"))
        diffs = []
        if cur.get("events") != doc["events"]:
            for eid, ev in doc["events"].items():
                if cur["events"].get(eid) != ev:
                    diffs.append(eid)
            for eid in cur["events"]:
                if eid not in doc["events"]:
                    diffs.append(eid)
        if cur.get("summary") != doc["summary"]:
            diffs.append("<summary>")
        if diffs:
            print("FAIL: 产物与重新推导不一致（%d 处）：%s" % (len(diffs), ", ".join(diffs[:8])))
            return 1
        print("PASS: 参与者证据产物 v0_%d 与重新推导一致（%d 事件 / %d 条参与者记录）"
              % (version, doc["summary"]["events"], doc["summary"]["participants"]))
        return 0

    if not a.write:
        print("用法：--check 或 --write [--version N]")
        return 2
    if os.path.exists(out):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(out, REPO))
        return 1
    doc["artifact_version"] = "0.%d" % a.version
    if a.version > 1:
        doc["supersedes"] = "research/current/participant_evidence_v0_%d.json" % (a.version - 1)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    s = doc["summary"]
    print("已生成 %s" % os.path.relpath(out, REPO))
    print("  %d 事件 / %d 条参与者记录" % (s["events"], s["participants"]))
    print("  同期市场表现: %s" % s["market_participation"])
    print("  机制关系: %s" % s["mechanism_relation"])
    print("  对象登记核验: %s" % s["registry_role_verification"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
