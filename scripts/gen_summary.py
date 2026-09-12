"""生成年度级汇总 research/summary/auto_2018_2025.csv 与 .md。

对 2018—2025 每年聚合（纯事实整理，不做统计建模）：
year / annual_status / campaign_count / earliest_start / latest_start /
main_theme / classification / strength / result / major_catalyst / counter_evidence / notes

用法: python scripts/gen_summary.py
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
OUT_DIR = os.path.join(ROOT, "research", "summary")
CSV_OUT = os.path.join(OUT_DIR, "auto_2018_2025.csv")
MD_OUT = os.path.join(OUT_DIR, "auto_2018_2025.md")

YEARS = list(range(2018, 2026))

FIELDS = ["year", "annual_status", "campaign_count", "earliest_start", "latest_start",
          "main_theme", "classification", "strength", "result",
          "major_catalyst", "counter_evidence", "notes"]

conn = db.connect()


def q(query, *args):
    return [dict(r) for r in conn.execute(query, args).fetchall()]


def q1(query, *args):
    r = conn.execute(query, args).fetchone()
    return dict(r) if r else None


def pick(rows):
    """取非空(distinct)值，'|' 连接；空则返回空串。"""
    seen, out = set(), []
    for r in rows:
        for v in r.split("|"):
            v = v.strip()
            if v and v not in seen:
                seen.add(v)
                out.append(v)
    return "|".join(out)


def build_year(year):
    ar = q1("SELECT * FROM annual_reviews WHERE rule_id='rule_auto_summer' AND year=?", year)
    camps = q("SELECT * FROM campaigns WHERE rule_id='rule_auto_summer' AND campaign_year=? ORDER BY start_date", year)
    cids = [c["campaign_id"] for c in camps]

    row = {
        "year": str(year),
        "annual_status": ar["status"] if ar else "unknown",
        "campaign_count": str(len(camps)),
        "earliest_start": min((c["start_date"] for c in camps if c["start_date"]), default=""),
        "latest_start": max((c["start_date"] for c in camps if c["start_date"]), default=""),
    }

    # main_theme（各 Campaign role=main 的主题，不重复）
    themes = []
    if cids:
        themes = q("""SELECT DISTINCT t.name FROM campaign_themes ct
                      JOIN themes t ON t.theme_id=ct.theme_id
                      WHERE ct.campaign_id IN ({}) AND ct.role='main'""".format(
                      ",".join("?" * len(cids))), *cids)
    row["main_theme"] = pick([r["name"] for r in themes]) if isinstance(themes, list) else (themes["name"] if themes else "")

    row["classification"] = pick([c["classification"] for c in camps])
    row["strength"] = pick([c["strength"] for c in camps if c["strength"]])
    row["result"] = pick([c["result"] for c in camps])

    # major_catalyst：各 Campaign trigger/catalyst 事件名
    catalysts = []
    if cids:
        catalysts = q("""SELECT DISTINCT e.name FROM campaign_events ce
                         JOIN events e ON e.event_id=ce.event_id
                         WHERE ce.campaign_id IN ({}) AND ce.role IN ('trigger','catalyst')""".format(
                         ",".join("?" * len(cids))), *cids)
    row["major_catalyst"] = pick([r["name"] for r in catalysts])

    # counter_evidence：绑定在当年 Campaign 上的 contradicting 证据 + 年度未绑定 contradicting 证据
    counters = []
    if cids:
        counters = q("""SELECT DISTINCT e.evidence_id, e.description FROM campaign_evidences ce
                        JOIN evidences e ON e.evidence_id=ce.evidence_id
                        WHERE ce.campaign_id IN ({}) AND e.evidence_role='contradicting'""".format(
                        ",".join("?" * len(cids))), *cids)
    if cids:
        unbound = q("""SELECT DISTINCT e.evidence_id, e.description FROM evidences e
                       WHERE e.date LIKE ? AND e.evidence_role='contradicting'
                         AND e.evidence_id NOT IN (SELECT evidence_id FROM campaign_evidences)""",
                    f"{year}%")
    else:
        unbound = q("""SELECT DISTINCT e.evidence_id, e.description FROM evidences e
                       WHERE e.date LIKE ? AND e.evidence_role='contradicting'""", f"{year}%")
    counter_desc = pick([r["description"] for r in counters] + [r["description"] for r in unbound])
    row["counter_evidence"] = counter_desc

    # notes：年度结论（summary + review_notes）
    notes = ar["summary"] if ar and ar["summary"] else ""
    if ar and ar.get("review_notes"):
        notes = (notes + " | 评审备注：" + ar["review_notes"]).strip()
    row["notes"] = notes
    return row


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = [build_year(y) for y in YEARS]

    with open(CSV_OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"CSV: {CSV_OUT} ({len(rows)} rows)")

    # ---- Markdown ----
    L = []
    L.append("# Auto 2018—2025 年度汇总（rule: rule_auto_summer · Base Pattern: 汽车）\n")
    L.append("> 汇总比较 2018—2025，纯历史事实整理，不做统计建模。")
    L.append("> 证据只取各 Campaign 显式绑定（campaign_evidences）及年度未绑定反例；不按年份/日期弱关联。\n")

    header = "| " + " | ".join(["年份", "annual_status", "Campaign数", "最早启动", "最晚启动"]) + " |"
    sep = "|" + "---|" * 5
    L.append(header)
    L.append(sep)
    for r in rows:
        L.append("| {year} | {annual_status} | {campaign_count} | {earliest_start} | {latest_start} |".format(**r))
    L.append("")

    for r in rows:
        L.append(f"\n## {r['year']} 年\n")
        for f in FIELDS:
            if f == "year":
                continue
            val = r[f]
            if f in ("notes", "counter_evidence", "earliest_start", "latest_start") and len(val) > 400:
                val = val[:400] + "…"
            L.append(f"- **{f}**：{val if val else '—'}")
        L.append("")

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"MD:  {MD_OUT}")


if __name__ == "__main__":
    main()
    conn.close()