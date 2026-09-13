"""Pilot 1-C1：注册行情序列（market_series）定义。

规则：
- 只填真实可确认的 symbol；不确定/未核实的代码留空（NULL），不编造。
- 顺序：先建基准与指数，后续 Campaign 日期核验会引用它们。
- 幂等：可重复运行。

用法: python scripts/seed_market_series.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

conn = db.connect()
db.migrate(conn)


def ins(row):
    db.insert(conn, "market_series", row)


SERIES = [
    dict(series_id="SH000300", name="沪深300(基准)", series_type="benchmark", provider="csi",
         symbol="000300.SH", frequency="daily", price_type="raw",
         adjustment_method=None,
         description="A股大盘基准指数，用于 relative_return_vs_benchmark 与日历推导。"),
    dict(series_id="AUTO_SW", name="申万汽车行业指数", series_type="industry_index", provider="sw",
         symbol="801880.SI", frequency="daily", price_type="raw",
         adjustment_method=None,
         description="申万一级行业·汽车，衡量整体汽车板块原始价格走势(候选Auto核验主线1)。"),
    dict(series_id="AUTO_PARTS", name="申万汽车零部件指数", series_type="industry_index", provider="sw",
         symbol=None, frequency="daily", price_type="raw",
         adjustment_method=None,
         description="申万二级·汽车零部件。symbol 待用权威代码二次核实后再填，不编造。"),
    dict(series_id="NEV", name="新能源汽车概念指数", series_type="concept_index", provider="akshare",
         symbol=None, frequency="daily", price_type="raw",
         adjustment_method=None,
         description="新能源汽车概念。概念成分变化大、存在 survivorship bias，仅作参考，symbol 待核实。"),
    dict(series_id="AD_AUTO", name="智能驾驶/无人驾驶概念", series_type="concept_index", provider="akshare",
         symbol=None, frequency="daily", price_type="raw",
         adjustment_method=None,
         description="智能驾驶/无人驾驶概念(2023-2025核验参考)。成分预留，symbol 待核实。"),
    dict(series_id="V2X", name="车路云一体化/车路协同概念", series_type="concept_index", provider="akshare",
         symbol=None, frequency="daily", price_type="raw",
         adjustment_method=None,
         description="车路云/车路协同概念(2024 Campaign A 核验参考)。成分预留，symbol 待核实。"),
    dict(series_id="ROBOTAXI", name="Robotaxi/无人驾驶运营概念", series_type="concept_index", provider="akshare",
         symbol=None, frequency="daily", price_type="raw",
         adjustment_method=None,
         description="Robotaxi/智能网约车概念(2024/2025 Campaign B 核验参考)。成分预留，symbol 待核实。"),
]

for s in SERIES:
    ins(s)

conn.commit()
conn.close()
print(f"Seeded {len(SERIES)} market_series rows (SYMBOL 未核实的留空，不编造)。")