"""生成各年份年度研究报告 research/annual/{year}.md（基于模板 + 数据库数据）。

用法: python scripts/gen_annual.py [year ...]
不传年份则生成全部年度 2018–2025。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
TEMPLATE = os.path.join(ROOT, "research", "templates", "annual_template.md")
OUT_DIR = os.path.join(ROOT, "research", "annual")

YEARS = sys.argv[1:] or [str(y) for y in range(2018, 2026)]

conn = db.connect()


def get(query, *a):
    return conn.execute(query, a).fetchone()


def getall(query, *a):
    return [dict(r) for r in conn.execute(query, a).fetchall()]


def drift_str(days):
    return "0（=当天）" if days == 0 else f"{days:+d} 天"


def build(year):
    ar = get("SELECT * FROM annual_reviews WHERE rule_id='rule_auto_summer' AND year=?", year)
    if not ar:
        print(f"!! no annual_review for {year}")
        return
    ar = dict(ar)
    camps = getall(
        "SELECT * FROM campaigns WHERE rule_id='rule_auto_summer' AND campaign_year=? ORDER BY campaign_id", year)
    # 证据仅经 campaign_evidences 显式绑定（禁止按年份/日期弱关联）。
    # 每年度：各 Campaign 只带自己的绑定证据；未绑定任何 Campaign 的年度级 contradicting/context 证据单列于反例段。
    bound = getall(
        "SELECT e.evidence_id, e.date, e.evidence_type, e.description, e.evidence_role, e.confidence, "
        "       s.title AS source_title, s.url, s.tier, ce.campaign_id, ce.role AS bridge_role "
        "FROM campaign_evidences ce "
        "JOIN evidences e ON e.evidence_id = ce.evidence_id "
        "LEFT JOIN sources s ON s.source_id = e.source_id "
        "WHERE ce.campaign_id IN (SELECT campaign_id FROM campaigns "
        "                          WHERE rule_id='rule_auto_summer' AND campaign_year=?) "
        "ORDER BY ce.campaign_id, e.date", year)
    unbound = getall(
        "SELECT e.evidence_id, e.date, e.evidence_type, e.description, e.evidence_role, e.confidence, "
        "       s.title AS source_title, s.url, s.tier "
        "FROM evidences e LEFT JOIN sources s ON s.source_id = e.source_id "
        "WHERE e.date LIKE ? "
        "  AND e.evidence_id NOT IN (SELECT evidence_id FROM campaign_evidences) "
        "ORDER BY e.date", f"{year}%")
    phases = []
    themes_yearly = getall(
        "SELECT DISTINCT t.name, t.theme_type, ct.role FROM campaign_themes ct "
        "JOIN themes t ON t.theme_id=ct.theme_id JOIN campaigns c ON c.campaign_id=ct.campaign_id "
        "WHERE c.campaign_year=? AND c.rule_id='rule_auto_summer'", year)

    L = []
    L.append(f"# {year} 汽车（Base Pattern: 汽车）\n")
    L.append(f"> Rule: `rule_auto_summer` · Annual Review 状态：`{ar['status']}`\n")
    L.append("## 年度结论\n")
    L.append(ar["summary"] or "(待补充)")
    if ar["review_notes"]:
        L.append(f"\n**评审备注**：{ar['review_notes']}")
    L.append("\n## Campaign\n")

    if not camps:
        L.append("本年度无符合判定标准的 Campaign（可选判为 no_clear_campaign / 仅行业趋势）。")
        L.append("")
    for c in camps:
        L.append(f"### Campaign {c['campaign_id']}")
        L.append(f"- 时间：{c['start_date']} ~ {c['end_date']}（峰值 {c['peak_date']}）")
        L.append(f"- 窗口漂移：相对 6/1 {drift_str(c['drift_vs_jun01'])}；相对 7/1 {drift_str(c['drift_vs_jul01'])}；相对 8/1 {drift_str(c['drift_vs_aug01'])}")
        L.append(f"- 主题（Annual Theme）：{', '.join(t['name'] for t in themes_yearly if t['role']=='main') or '(未标 main)'}（classification: {c['classification']}）")
        L.append(f"- 启动（start_date_basis）：{c['start_date_basis']}")
        L.append(f"- 结束（end_date_basis）：{c['end_date_basis']}")
        cme = getall("SELECT e.name, ce.role FROM campaign_events ce JOIN events e ON e.event_id=ce.event_id WHERE ce.campaign_id=?", c["campaign_id"])
        if cme:
            cme_str = "; ".join("{} ({})".format(x["name"], x["role"]) for x in cme)
            L.append(f"- 催化（事件）：{cme_str}")
        cse = getall("SELECT s.name, s.ticker, cs.role FROM campaign_securities cs JOIN securities s ON s.security_id=cs.security_id WHERE cs.campaign_id=?", c["campaign_id"])
        if cse:
            cse_str = "; ".join("{} ({}, {})".format(x["name"], x["ticker"], x["role"]) for x in cse)
            L.append(f"- 代表股：{cse_str}")
        L.append(f"- 结果：{c['result']}（strength: {c['strength']}；date_confidence: {c['date_confidence']}）")
        L.append(f"- 描述：{c['description']}")
        if c["research_notes"]:
            L.append(f"- research_notes：{c['research_notes']}")
        L.append("")

    # 行业趋势 / 失败反例（基于年度状态）
    L.append("## 行业趋势 / 失败·反例\n")
    if ar["status"] == "no_clear_campaign":
        L.append("年度判定 `no_clear_campaign`：本窗口未观察到可识别的主题 Campaign，属反例年份（不强行找上涨案例）。")
    elif ar["status"] == "weak":
        L.append("年度判定 `weak`：主题信号弱或偏窗口尾部；板块整体无持续主线，仅事件驱动脉冲。")
    elif ar["status"] == "strong":
        L.append("年度判定 `strong`：存在清晰主题与龙头。仍需注意以反例视角复检（全年窗口提前/延后、二次启动是否退潮）。")
    else:
        L.append(f"年度判定 `{ar['status']}`：需结合 review_notes 补充行业趋势分析。")
    if ar["review_notes"]:
        L.append(f"- 反例视角备注：{ar['review_notes']}")
    L.append("")

    # phases
    if camps:
        all_ph = []
        for c in camps:
            all_ph += getall("SELECT * FROM campaign_phases WHERE campaign_id=?", c["campaign_id"])
    else:
        all_ph = []
    L.append("## Wave / Phase\n")
    if all_ph:
        for p in all_ph:
            L.append(f"- [{p['campaign_id']}] {p['phase_type']}: {p['start_date']} ~ {p['end_date']} — {p['description']}")
        L.append("*注：证据多为线索（Tier4）时置信度低，此处仅记录便于后续核验。*")
    else:
        L.append("（证据不充分，暂不记录）")

    L.append("\n## Evidence\n")
    # 按 Campaign 分组展示各自绑定证据（隔离）
    if camps:
        for c in camps:
            cid = c["campaign_id"]
            cev = [e for e in bound if e["campaign_id"] == cid]
            L.append(f"### Campaign {cid}（绑定 {len(cev)} 条证据）")
            if not cev:
                L.append("（该 Campaign 未绑定独立证据，需补充）")
            for e in cev:
                tier = f"Tier{e['tier']}" if e["tier"] else "?"
                L.append(f"- **{e['source_title'] or e['evidence_id']}**（{tier} · 角色: {e['evidence_role']} · 置信度: {e['confidence']} · {e['date']}）")
                L.append(f"  - URL: {e['url']}")
                L.append(f"  - {e['description']}")
            L.append("")
    # 年度级反例 / 行业证据（未绑定任何 Campaign）
    unbound_disp = [e for e in unbound if e["evidence_role"] in ("contradicting", "context")]
    L.append(f"### 年度反例 / 行业证据（未绑定 Campaign，{len(unbound_disp)} 条）")
    if not unbound_disp:
        L.append("（无）")
    for e in unbound_disp:
        tier = f"Tier{e['tier']}" if e["tier"] else "?"
        L.append(f"- **{e['source_title'] or e['evidence_id']}**（{tier} · 角色: {e['evidence_role']} · 置信度: {e['confidence']} · {e['date']}）")
        L.append(f"  - URL: {e['url']}")
        L.append(f"  - {e['description']}")

    txt = "\n".join(L)
    out = os.path.join(OUT_DIR, f"{year}.md")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(txt)
    print(f"wrote {out}")


for y in YEARS:
    build(y)
conn.close()