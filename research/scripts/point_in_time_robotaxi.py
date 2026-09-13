"""Pilot 1-C1.2：2024 Robotaxi Point-in-Time 识别记录 + 测试。

产出：
- research/c2/point_in_time_leaders.csv  （Historical Leader Set 的识别时间记录）
- 三个 Point-in-Time slice（07-08 / 07-10 / 07-15）的候选集合
运行 §15 测试（1-7），不修改 campaigns / annual / rule。
用法: python scripts/point_in_time_robotaxi.py
"""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

ROOT = db.ROOT
CSV_PATH = os.path.join(ROOT, "research", "c2", "point_in_time_leaders.csv")

# Historical Leader Set —— 行情结束后回看得到（复盘用）
LEADERS = [
    dict(security_id="DAZHONGTONG", name="大众交通", identified_date="2024-07-08",
         identification_source="7/8放量+6.12%启动、7/9一字板，无人驾驶-网约车叙事早段(公开盘面/7/9媒体归因)",
         identification_type="market_breadth", confidence="medium",
         notes="识别较早：7/8当日已有可观察异动(低置信主题归因)，7/9一字板获媒体归入无人驾驶"),
    dict(security_id="JINJIANG", name="锦江在线", identified_date="2024-07-09",
         identification_source="7/9无人驾驶概念一字连板（当日市场盘面/媒体复盘报道）",
         identification_type="media_identified", confidence="medium",
         notes="与星网宇达同为首批一字连板的无人驾驶/智能网约车标的"),
    dict(security_id="XINGYUYUDA", name="星网宇达", identified_date="2024-07-09",
         identification_source="7/9无人驾驶概念一字连板（当日市场盘面/媒体复盘报道）",
         identification_type="media_identified", confidence="medium",
         notes="首批无人驾驶概念一字连板标的"),
    dict(security_id="TIANMAI", name="天迈科技", identified_date="2024-07-10",
         identification_source="证券时报7/10报道：天迈科技20cm涨停（无人驾驶+车路云共涨）【E-2024-05】",
         identification_type="media_identified", confidence="high",
         notes="7/10有当日Tier2公开报道直接点名其为无人驾驶热点"),
    dict(security_id="JINLONG", name="金龙汽车", identified_date="2024-07-12",
         identification_source="7/12金龙汽车涨停（无人驾驶客车/萝卜快跑概念公开报道）",
         identification_type="media_identified", confidence="medium",
         notes="识别晚于前四只；7/12涨停获公开归因"),
]

# 时间切片（Point-in-Time Basket）：只有 identified_date <= 切片日 的股票才允许进入
SLICES = {
    "07-08": {"demand": [], "basket": (None, "unavailable"),
              "note": "无可靠公开主题识别：仅大众交通 market_breadth 低置信观察，不足下定义为主题市值 basket"},
    "07-10": {"demand": [l["security_id"] for l in LEADERS if l["identified_date"] <= "2024-07-10"],
              "basket": None, "note": ""},
    "07-15": {"demand": [l["security_id"] for l in LEADERS if l["identified_date"] <= "2024-07-15"],
              "basket": None, "note": ""},
}
SLICES["07-10"]["basket"] = SLICES["07-10"]["demand"]
SLICES["07-15"]["basket"] = SLICES["07-15"]["demand"]


def write_csv():
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["security_id", "name", "identified_date",
                                          "identification_source", "identification_type",
                                          "confidence", "notes"])
        w.writeheader()
        for l in LEADERS:
            w.writerow(l)
    print(f"wrote {CSV_PATH} ({len(LEADERS)} rows)")


def main():
    write_csv()
    for k, v in SLICES.items():
        print(f"Slice {k}: point_in_time_basket = {v['basket']} {v['note']}")
    run_tests()


def run_tests():
    fails = []
    ok = lambda c, m: (print(("PASS " if c else "FAIL ") + m) or (not c and fails.append(m)))
    ident = {l["security_id"]: l for l in LEADERS}

    # ---- T2: identification_source 必须存在 ----
    ok(all(l["identification_source"].strip() for l in LEADERS), "T2 每条 leader 有 identification_source")

    # ---- 切片与 identified_date ----
    all_ids = set(ident.keys())
    for name, sl in SLICES.items():
        basket = sl["basket"]
        if not isinstance(basket, list):  # unavailable / 非列表
            ok(True, f"T1/T3/T4 Slice {name}: basket unavailable 跳过")
            continue
        # T1: identified_date <= 切片研究日
        ok(all(ident[s]["identified_date"] <= {"07-10": "2024-07-10", "07-15": "2024-07-15"}[name]
               for s in basket), f"T1 Slice {name} 各股 identified_date<=切片日")
        # T3: Historical Leader 不自动全量进入 point-in-time set
        ok(set(basket) != all_ids or name == "07-15", f"T3 Slice {name} 非完整Historical Leader(全量)自动进入")
        # T4: 无证据不进入：basket 中每只都在识别表 & identified_date<=切片
        ok(all(s in ident for s in basket), f"T4 Slice {name} 所有basket股在识别表中")

    # ---- T5: 不能用事后识别放入早期切片 ----
    # 金龙 07-12 不得进入 07-08/07-10 切片
    ok("JINLONG" not in (SLICES["07-08"]["basket"] or []) and "JINLONG" not in (SLICES["07-10"]["basket"] or []),
       "T5 金龙(07-12)不进入 07-08/07-10 切片")

    # ---- T6: Campaign 日期不修改 ----
    c = db.connect()
    r = c.execute("SELECT start_date, peak_date, end_date FROM campaigns WHERE campaign_id='C-2024-ROBOTAXI'").fetchone()
    ok(list(r) == ["2024-07-08", "2024-07-29", "2024-07-31"], f"T6 Campaign日期未修改 {list(r)}")
    # ---- T7: annual status 不修改 ----
    st = c.execute("SELECT status FROM annual_reviews WHERE year=2024 AND rule_id='rule_auto_summer'").fetchone()[0]
    ok(st == "medium", f"T7 2024 annual_status 未改 (medium) -> {st}")
    c.close()

    print("== TESTS ==", "ALL PASS" if not fails else ("FAILS: " + str(fails)))


if __name__ == "__main__":
    main()