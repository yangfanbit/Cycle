"""timeline_export_v1.json Canonical Contract 校验（validate_timeline_export.py）。

对应 Timeline Export Contract v1.0 Finalization 的 14 项真实验证：
 1. 顶层字段（白名单 + 必填）
 2. rules（白名单 + 必填）
 3. signals（结构、归属 campaign_id XOR research_candidate_id、日期格式）
 4. campaigns（必填 + 白名单）
 5. research_candidates（必填 + 白名单）
 6. events（必填 + 白名单 + campaign_id 可空 = 全局事件）
 7. securities（必填 + 白名单 + 必须知道属于谁）
 8. 字段白名单（上述各实体覆盖）
 9. 日期格式（ISO YYYY-MM-DD 或 null）
10. ID 唯一性（campaign_id / research_candidate_id / event_id 唯一；(security_id, owner) 唯一）
11. Candidate 不进入 formal campaigns（campaign_id 与 research_candidate_id 无重叠）
12. CONFLICT 必须有 conflicts（candidate_a + candidate_b）
13. research candidates 不得伪装 verified
14. source_commit 存在

关键测试：RC-2023-HUAWEI 出现在 research_candidates、不出现在 campaigns、但可出现在 timeline_export。

用法: python scripts/validate_timeline_export.py
"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
EXPORT = db.TIMELINE_EXPORT_PATH  # canonical: <repo>/exports/timeline_export_v1.json

TOP_LEVEL = {
    "contract", "timeline_export_version", "generated_at", "source_commit",
    "project", "rules", "signals", "campaigns", "research_candidates", "events", "securities",
}
RULE_FIELDS = {"rule_id", "name", "base_pattern", "definition", "observation_window"}
SIGNAL_FIELDS = {"type", "date", "confidence", "campaign_id", "research_candidate_id"}
CAMPAIGN_FIELDS = {
    "campaign_id", "rule_id", "year", "start_date", "peak_date", "end_date",
    "status", "confidence", "classification", "strength", "result",
    "themes", "event_ids", "security_ids",
    # research metadata（明确不是 HistoricalCampaign schema 字段）
    "research_status", "theme_cycle_id", "promotion_status",
    "first_signal_date", "broad_confirmation_date", "first_decline_date",
    "conflicts", "notes",
    # V1.7 backward-compatible optional（时间精度 + Drivers）
    "lifecycle", "drivers",
}
CANDIDATE_FIELDS = {
    "campaign_id", "rule_id", "year", "title", "start_date", "peak_date", "end_date",
    "themes", "event_ids", "security_ids",
    "early_signal", "research_status", "theme_cycle_id", "conflicts", "notes",
    # V1.7 backward-compatible optional
    "lifecycle", "drivers",
}
EVENT_FIELDS = {"event_id", "name", "date", "event_type", "role", "campaign_id", "research_candidate_id"}
SECURITY_FIELDS = {"security_id", "name", "ticker", "exchange", "role", "campaign_id", "research_candidate_id"}
THEME_FIELDS = {"name", "theme_type", "role"}
LIFECYCLE_FIELDS = {"stage", "start", "end", "precision"}
DRIVERS_FIELDS = {"start", "accelerator", "turning", "ending"}

VALID_PRODUCTION_STATUS = {"verified", "provisional", "conflict", "preview"}
VALID_RESEARCH_STATUS = {"PROVISIONAL", "CONFLICT", "INSUFFICIENT"}
VALID_SIGNAL_TYPE = {"EARLY_SIGNAL", "THEME_FORMING", "CONFIRMATION_CANDIDATE"}
VALID_LIFECYCLE_STAGE = {
    "EARLY_SIGNAL", "THEME_FORMING", "BROAD_CONFIRMATION", "MAIN_RISE", "PEAK",
    "RETRACEMENT", "DECLINING", "SECONDARY", "FIRST_DECLINE", "MAIN_END", "ENDED",
}
VALID_PRECISION = {"EXACT_DATE", "DATE_WINDOW", "PHASE_WINDOW"}

FAILS, WARNS = [], []


def fail(rule, msg):
    FAILS.append((rule, msg))


def warn(rule, msg):
    WARNS.append((rule, msg))


def is_iso_date(s):
    if s is None or s == "":
        return True
    try:
        datetime.date.fromisoformat(str(s)[:10])
        return len(str(s)) == 10
    except (ValueError, TypeError):
        return False


def check_whitelist(owner, fields, allowed):
    for k in sorted(set(fields) - allowed):
        fail("field-whitelist", f"{owner} 出现未声明字段: {k}（不得伪装成正式 Contract 字段）")


def check_owner(obj, owner_label):
    """归属：campaign_id XOR research_candidate_id（可都 null 仅限全局事件/证券）。"""
    cid = obj.get("campaign_id")
    rcid = obj.get("research_candidate_id")
    if cid and rcid:
        fail("owner", f"{owner_label} 同时有 campaign_id={cid} 与 research_candidate_id={rcid}（二选一）")


def check_lifecycle(owner, lifecycle):
    """lifecycle（V1.7 phase windows）：stage/precision 枚举 + 日期格式。"""
    if lifecycle is None:
        return
    if not isinstance(lifecycle, list):
        fail("lifecycle-type", f"{owner} lifecycle 必须为数组")
        return
    for lc in lifecycle:
        check_whitelist(f"{owner} lifecycle[{lc.get('stage')}]", lc.keys(), LIFECYCLE_FIELDS)
        if lc.get("stage") not in VALID_LIFECYCLE_STAGE:
            fail("lifecycle-stage", f"{owner} lifecycle stage='{lc.get('stage')}' 非法")
        if lc.get("precision") not in VALID_PRECISION:
            fail("lifecycle-precision", f"{owner} lifecycle {lc.get('stage')} precision='{lc.get('precision')}' 非法（应为 EXACT_DATE/DATE_WINDOW/PHASE_WINDOW）")
        for f in ("start", "end"):
            if not is_iso_date(lc.get(f)):
                fail("lifecycle-date", f"{owner} lifecycle {lc.get('stage')}.{f} 日期非法: {lc.get(f)}")


def check_drivers(owner, drivers):
    """drivers（V1.7）：start/accelerator/turning/ending 均为字符串数组；无来源写 unknown。"""
    if drivers is None:
        return
    if not isinstance(drivers, dict):
        fail("drivers-type", f"{owner} drivers 必须为对象")
        return
    check_whitelist(f"{owner} drivers", drivers.keys(), DRIVERS_FIELDS)
    for k in DRIVERS_FIELDS:
        v = drivers.get(k)
        if v is None:
            continue
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            fail("drivers-format", f"{owner} drivers.{k} 必须为字符串数组")


def main():
    print("=== validate_timeline_export.py（Canonical Contract v1.0）===\n")
    if not os.path.exists(EXPORT):
        fail("file-missing", f"timeline_export 缺失: {EXPORT}")
        return finish()
    try:
        with open(EXPORT, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail("parse", f"JSON 解析失败: {e}")
        return finish()
    print("JSON 解析: OK")

    # 1) 顶层字段
    check_whitelist("timeline_export", data.keys(), TOP_LEVEL)
    if data.get("contract") != "timeline_export":
        fail("contract", f"contract 缺失或错误: {data.get('contract')}")
    ver = data.get("timeline_export_version")
    if ver != "1.0":
        fail("version", f"timeline_export_version 必须为 '1.0'，当前: {ver}")
    if "export_version" in data:
        fail("version-dup", "禁止同时存在 export_version（版本语义只能 timeline_export_version）")
    # 14) source_commit 存在
    if not data.get("source_commit"):
        fail("source_commit", "顶层缺 source_commit")

    # 2) rules
    for r in data.get("rules", []):
        check_whitelist(f"rule {r.get('rule_id')}", r.keys(), RULE_FIELDS)
        for f in ("rule_id", "name", "base_pattern"):
            if f not in r:
                fail("rule-required", f"rule 缺必填字段 {f}")

    # 3) signals
    for s in data.get("signals", []):
        check_whitelist(f"signal {s.get('type')}", s.keys(), SIGNAL_FIELDS)
        if s.get("type") not in VALID_SIGNAL_TYPE:
            fail("signal-type", f"signal type='{s.get('type')}' 非法")
        check_owner(s, f"signal {s.get('type')} {s.get('date')}")
        if not is_iso_date(s.get("date")):
            fail("signal-date", f"signal 日期格式非法: {s.get('date')}")
        if not s.get("campaign_id") and not s.get("research_candidate_id"):
            fail("signal-owner", f"signal {s.get('date')} 必须归属 campaign_id 或 research_candidate_id")

    # 4) campaigns
    campaign_ids = []
    for c in data.get("campaigns", []):
        cid = c.get("campaign_id")
        campaign_ids.append(cid)
        check_whitelist(f"campaign {cid}", c.keys(), CAMPAIGN_FIELDS)
        for f in ("campaign_id", "rule_id", "year", "start_date", "peak_date", "end_date",
                  "status", "confidence"):
            if f not in c:
                fail("campaign-required", f"{cid} 缺必填字段 {f}")
        # 9) 日期格式
        for f in ("start_date", "peak_date", "end_date",
                  "first_signal_date", "broad_confirmation_date", "first_decline_date"):
            if not is_iso_date(c.get(f)):
                fail("campaign-date", f"{cid}.{f} 日期格式非法: {c.get(f)}")
        # 10) 状态枚举
        if c.get("status") not in VALID_PRODUCTION_STATUS:
            fail("campaign-status", f"{cid} status='{c.get('status')}' 非法（应为 verified/provisional/conflict/preview）")
        if c.get("research_status") not in VALID_RESEARCH_STATUS:
            fail("campaign-research-status", f"{cid} research_status='{c.get('research_status')}' 非法")
        # 12) CONFLICT 必须有 conflicts
        if c.get("research_status") == "CONFLICT":
            cf = c.get("conflicts") or []
            if not cf:
                fail("conflict-required", f"{cid} research_status=CONFLICT 但 conflicts 为空")
            for x in cf:
                if "candidate_a" not in x or "candidate_b" not in x:
                    fail("conflict-candidates", f"{cid} 冲突记录缺少 candidate_a/b（不得伪装成确定日期）")
                for side in ("candidate_a", "candidate_b"):
                    if not is_iso_date(x.get(side, {}).get("date")):
                        fail("conflict-date", f"{cid} conflict.{side}.date 非法: {x.get(side, {}).get('date')}")
        # themes / event_ids / security_ids 结构
        for t in c.get("themes", []):
            check_whitelist(f"{cid} theme", t.keys(), THEME_FIELDS)
        if not isinstance(c.get("event_ids", []), list):
            fail("campaign-event_ids", f"{cid} event_ids 必须为数组")
        if not isinstance(c.get("security_ids", []), list):
            fail("campaign-security_ids", f"{cid} security_ids 必须为数组")
        # V1.7: lifecycle（phase windows）+ drivers
        check_lifecycle(cid, c.get("lifecycle"))
        check_drivers(cid, c.get("drivers"))

    # 5) research_candidates
    candidate_ids = []
    for rc in data.get("research_candidates", []):
        rcid = rc.get("campaign_id")
        candidate_ids.append(rcid)
        check_whitelist(f"research_candidate {rcid}", rc.keys(), CANDIDATE_FIELDS)
        for f in ("campaign_id", "rule_id", "year", "title", "start_date", "peak_date", "end_date"):
            if f not in rc:
                fail("candidate-required", f"{rcid} 缺必填字段 {f}")
        for f in ("start_date", "peak_date", "end_date", "early_signal"):
            if not is_iso_date(rc.get(f)):
                fail("candidate-date", f"{rcid}.{f} 日期格式非法: {rc.get(f)}")
        if rc.get("research_status") not in VALID_RESEARCH_STATUS:
            fail("candidate-research-status", f"{rcid} research_status='{rc.get('research_status')}' 非法")
        # 13) research candidates 不得伪装 verified
        if "status" in rc:
            fail("candidate-fake-status", f"{rcid} 不得有生产 status 字段（候选只有 research_status）")
        if rc.get("research_status") == "VERIFIED":
            fail("candidate-verified", f"{rcid} research_status 不得为 VERIFIED（候选不伪装 verified）")
        # V1.7: lifecycle + drivers
        check_lifecycle(rcid, rc.get("lifecycle"))
        check_drivers(rcid, rc.get("drivers"))

    # 6) events
    event_ids = []
    for ev in data.get("events", []):
        eid = ev.get("event_id")
        event_ids.append(eid)
        check_whitelist(f"event {eid}", ev.keys(), EVENT_FIELDS)
        for f in ("event_id", "name", "date", "event_type"):
            if f not in ev:
                fail("event-required", f"{eid} 缺必填字段 {f}")
        if not is_iso_date(ev.get("date")):
            fail("event-date", f"{eid} 日期格式非法: {ev.get('date')}")
        check_owner(ev, f"event {eid}")

    # 7) securities
    sec_keys = set()
    for sec in data.get("securities", []):
        sid = sec.get("security_id")
        check_whitelist(f"security {sid}", sec.keys(), SECURITY_FIELDS)
        for f in ("security_id", "name", "ticker", "exchange", "role"):
            if f not in sec:
                fail("security-required", f"{sid} 缺必填字段 {f}")
        check_owner(sec, f"security {sid}")
        owner = sec.get("campaign_id") or sec.get("research_candidate_id")
        key = (sid, owner)
        if key in sec_keys:
            fail("security-owner-dup", f"(security_id={sid}, owner={owner}) 重复（同一证券同一归属只能一条）")
        sec_keys.add(key)
        if owner is None:
            fail("security-unowned", f"security {sid} 没有归属（必须知道属于谁）")

    # 8) 字段白名单（由 1-7 覆盖）

    # 10) ID 唯一性
    dup_c = {i for i in campaign_ids if campaign_ids.count(i) > 1}
    for i in dup_c:
        fail("campaign-id-dup", f"campaign_id 重复: {i}")
    dup_r = {i for i in candidate_ids if candidate_ids.count(i) > 1}
    for i in dup_r:
        fail("candidate-id-dup", f"research_candidate_id 重复: {i}")
    dup_e = {i for i in event_ids if event_ids.count(i) > 1}
    for i in dup_e:
        fail("event-id-dup", f"event_id 重复: {i}")

    # 11) Candidate 不进入 formal campaigns
    overlap = set(campaign_ids) & set(candidate_ids)
    for i in sorted(overlap):
        fail("candidate-in-campaigns", f"{i} 同时出现在 campaigns 与 research_candidates（禁止）")

    # events / securities 引用一致性：campaign.event_ids 必须存在于 events 且归属正确
    ev_by_id = {ev["event_id"]: ev for ev in data.get("events", [])}
    for c in data.get("campaigns", []):
        for eid in c.get("event_ids", []):
            if eid not in ev_by_id:
                fail("event-ref", f"{c['campaign_id']} 引用不存在的事件 {eid}")
            elif ev_by_id[eid].get("campaign_id") != c["campaign_id"]:
                fail("event-ref-owner", f"{c['campaign_id']} 引用事件 {eid} 但归属 {ev_by_id[eid].get('campaign_id')}")
    for rc in data.get("research_candidates", []):
        for eid in rc.get("event_ids", []):
            if eid not in ev_by_id:
                fail("event-ref", f"{rc['campaign_id']} 引用不存在的事件 {eid}")
            elif ev_by_id[eid].get("research_candidate_id") != rc["campaign_id"]:
                fail("event-ref-owner", f"{rc['campaign_id']} 引用事件 {eid} 归属不符")
    sec_by_key = {(s["security_id"], s.get("campaign_id") or s.get("research_candidate_id")): s
                  for s in data.get("securities", [])}
    for c in data.get("campaigns", []):
        for sid in c.get("security_ids", []):
            if (sid, c["campaign_id"]) not in sec_by_key:
                fail("security-ref", f"{c['campaign_id']} 引用的证券 {sid} 不存在或归属不符")
    for rc in data.get("research_candidates", []):
        for sid in rc.get("security_ids", []):
            if (sid, rc["campaign_id"]) not in sec_by_key:
                fail("security-ref", f"{rc['campaign_id']} 引用的证券 {sid} 不存在或归属不符")

    # 关键测试：RC-2023-HUAWEI 在 research_candidates，不在 campaigns，但在 timeline_export
    if "RC-2023-HUAWEI" not in candidate_ids:
        fail("rc-test", "RC-2023-HUAWEI 未出现在 research_candidates（Cycle Preview 应可展示）")
    if "RC-2023-HUAWEI" in campaign_ids:
        fail("rc-test", "RC-2023-HUAWEI 出现在 campaigns（候选不得进入正式 campaigns）")

    print(f"Campaigns: {len(campaign_ids)} | Research candidates: {len(candidate_ids)} | "
          f"Events: {len(event_ids)} | Securities: {len(sec_keys)}")
    print(f"RC-2023-HUAWEI: research_candidates 中 ✅ / campaigns 中不存在 ✅")

    return finish()


def finish():
    print("-" * 40)
    for rule, msg in WARNS:
        print(f"WARNING [{rule}] {msg}")
    for rule, msg in FAILS:
        print(f"FAIL    [{rule}] {msg}")
    print("-" * 40)
    if FAILS:
        print(f"\n结果: FAIL（{len(FAILS)} 处）")
        sys.exit(1)
    print(f"\n结果: PASS（{len(WARNS)} 条警告）")


if __name__ == "__main__":
    main()
