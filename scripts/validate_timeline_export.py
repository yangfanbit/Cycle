"""timeline_export_v1.json 契约校验（validate_timeline_export.py）。

验证（对应 HDP v1 验证目标 8-10 的导出层部分）：
8. timeline_export JSON 可被机器解析（JSON 语法 + 顶层必填字段）
9. timeline export 不生成不存在的 Cycle 字段（字段白名单检查）
10. 2018–2025 数据全部可导出（campaigns 覆盖 2019–2025；2018 反例由 rules 注释承载）

契约字段白名单（timeline_export_version = "1.0"，向后兼容原则：未来只增不改删语义）。

用法: python scripts/validate_timeline_export.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT = os.path.join(ROOT, "exports", "timeline_export_v1.json")

TOP_LEVEL = {
    "contract", "timeline_export_version", "generated_at", "source_commit",
    "project", "purpose", "rules", "signals", "campaigns", "events", "securities",
}
RULE_FIELDS = {"rule_id", "name", "base_pattern", "definition", "observation_window"}
CAMPAIGN_FIELDS = {
    "campaign_id", "rule_id", "year", "start_date", "peak_date", "end_date",
    "status", "confidence", "classification", "strength", "result",
    "themes", "events", "securities",
    # research-only 附加（明确标注，不得伪装成正式字段）
    "research_status", "theme_cycle_id", "first_signal_date",
    "broad_confirmation_date", "first_decline_date", "notes",
}
SIGNAL_FIELDS = {"type", "date", "confidence"}
EVENT_FIELDS = {"event_id", "name", "date", "event_type", "role"}
SECURITY_FIELDS = {"security_id", "name", "ticker", "exchange", "role"}
THEME_FIELDS = {"name", "theme_type", "role"}

FAILS, WARNS = [], []


def fail(rule, msg):
    FAILS.append((rule, msg))


def warn(rule, msg):
    WARNS.append((rule, msg))


def main():
    print("=== validate_timeline_export.py ===\n")
    if not os.path.exists(EXPORT):
        fail("file-missing", f"timeline_export 缺失: {EXPORT}")
        return finish()
    # 8) 机器可解析
    try:
        with open(EXPORT, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        fail("parse", f"JSON 解析失败: {e}")
        return finish()
    print("JSON 解析: OK")

    # 版本与契约
    if data.get("contract") != "timeline_export":
        fail("contract", f"contract 缺失或错误: {data.get('contract')}")
    ver = data.get("timeline_export_version")
    if ver != "1.0":
        fail("version", f"timeline_export_version 必须为 '1.0'，当前: {ver}")
    for k in ("generated_at", "source_commit"):
        if not data.get(k):
            warn("meta", f"顶层缺 {k}")

    # 顶层字段白名单
    extra = set(data.keys()) - TOP_LEVEL
    for k in sorted(extra):
        fail("top-extra", f"顶层出现未声明字段: {k}（不得伪装成正式契约字段）")

    # rules
    for r in data.get("rules", []):
        extra = set(r.keys()) - RULE_FIELDS
        for k in sorted(extra):
            fail("rule-extra", f"rule 出现未声明字段: {k}")

    # campaigns
    years = set()
    for c in data.get("campaigns", []):
        cid = c.get("campaign_id")
        if cid:
            years.add(c.get("year"))
        extra = set(c.keys()) - CAMPAIGN_FIELDS
        for k in sorted(extra):
            fail("campaign-extra", f"{cid} 出现未声明字段: {k}（不得伪装成正式 Campaign 字段）")
        for f in ("campaign_id", "rule_id", "year", "start_date", "peak_date", "end_date", "status", "confidence"):
            if f not in c:
                fail("campaign-required", f"{cid} 缺必填字段 {f}")
        # themes/events/securities 子字段白名单
        for t in c.get("themes", []):
            for k in set(t.keys()) - THEME_FIELDS:
                fail("theme-extra", f"{cid} theme 出现未声明字段: {k}")
        for ev in c.get("events", []):
            for k in set(ev.keys()) - EVENT_FIELDS:
                fail("event-extra", f"{cid} event 出现未声明字段: {k}")
        for s in c.get("securities", []):
            for k in set(s.keys()) - SECURITY_FIELDS:
                fail("security-extra", f"{cid} security 出现未声明字段: {k}")

    # 10) 2019–2025 全部可导出（2018 无 Campaign，由 rules 注释承载反例）
    for y in range(2019, 2026):
        if y not in years:
            fail("year-export", f"{y} 无 campaign 可导出")
    print(f"Campaign 导出: {len(data.get('campaigns', []))} 个（年份 {sorted(years)}）")

    # research-only 字段不能与正式字段混名
    for c in data.get("campaigns", []):
        if "research_status" in c and c.get("status") == c.get("research_status"):
            warn("status-collision", f"{c.get('campaign_id')} status 与 research_status 相同值（应区分）")

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
