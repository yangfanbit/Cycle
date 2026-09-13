"""填充交易日历 trading_calendar。

推导规则（见 research/methodology/market_data_validation.md §3）：
无独立日历源时，允许由 benchmark series（沪深300 SH000300）的
distinct trade_date 推导——基准序列天然只含交易日。

- 只填 is_trading_day=1 的交易日（不生成休市日记录）。
- 幂等：已存在的日期跳过，不覆盖。
- 若 benchmark 无数据则 FAIL（不编造日历）。

用法: python scripts/seed_trading_calendar.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

BENCHMARK_SERIES = "SH000300"


def main():
    conn = db.connect()
    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT trade_date FROM market_daily WHERE series_id=? ORDER BY trade_date",
        (BENCHMARK_SERIES,)).fetchall()]
    if not dates:
        print(f"FAIL: benchmark series {BENCHMARK_SERIES} 无数据，无法推导交易日历（不编造）")
        conn.close()
        sys.exit(1)

    before = conn.execute("SELECT COUNT(*) FROM trading_calendar").fetchone()[0]
    for d in dates:
        conn.execute(
            "INSERT OR IGNORE INTO trading_calendar (trade_date, is_trading_day, calendar_type) VALUES (?,1,'cn')",
            (d,))
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM trading_calendar").fetchone()[0]

    # 校验：所有 market_daily.trade_date 必须被日历覆盖
    uncovered = conn.execute(
        """SELECT DISTINCT d.trade_date FROM market_daily d
           LEFT JOIN trading_calendar t ON t.trade_date = d.trade_date
           WHERE t.trade_date IS NULL""").fetchall()
    print(f"benchmark={BENCHMARK_SERIES} 交易日 {len(dates)} 天；日历 {before} → {after}")
    if uncovered:
        print(f"FAIL: {len(uncovered)} 个 market_daily 日期未被日历覆盖: {[r[0] for r in uncovered][:10]}")
        conn.close()
        sys.exit(1)
    print("PASS: 所有 market_daily.trade_date 均被 trading_calendar 覆盖")
    conn.close()


if __name__ == "__main__":
    main()
