"""Pilot 1-C1：基础行情指标函数库。

定位：仅提供**基础**计算函数，供后续 Campaign 日期核验（Pilot 1-C2）使用。
本轮**不**做最终统计模型（无 seasonality_score / win_rate / Sharpe / alpha / probability）。

价格口径纪律：
- 所有函数默认输入为**同一口径**的序列（全 raw 或全 adjusted），不混合。
- 收益计算必须明确口径；函数签名带 price_mode 提示，调用方负责保证单一口径。
- 日期判断优先使用原始价格序列（后复权/前复权仅用于收益计算）。

Breadth：
- 预留 ThemeBreadthSnapshot 接口；因缺少可靠历史成分数据，本轮不生成真值。
"""
import datetime as _dt


def _seq(prices):
    return [float(p) for p in prices if p is not None]


def daily_return(prices, price_mode="raw"):
    """日收益序列：closes[i]/closes[i-1]-1。要求输入为同一 price_mode 的收盘序列。"""
    p = _seq(prices)
    if len(p) < 2:
        return []
    return [p[i] / p[i - 1] - 1.0 for i in range(1, len(p))]


def cumulative_return(prices, price_mode="raw"):
    """累积收益：末值/首值-1。同一口径。"""
    p = _seq(prices)
    if len(p) < 2:
        return 0.0
    return p[-1] / p[0] - 1.0


def rolling_return(prices, window, price_mode="raw"):
    """窗口滚动收益率：每条 = closes[i]/closes[i-window]-1，返回对齐到 i 的列表(=len(prices))。"""
    p = _seq(prices)
    out = [None] * len(p)
    for i in range(len(p)):
        j = i - window + 1
        if j >= 0 and p[j] != 0:
            out[i] = p[i] / p[j] - 1.0
    return out


def relative_return_vs_benchmark(series_prices, bench_prices):
    """相对基准累计超额：cum(series)-cum(bench)。两序列须等长且同口径。"""
    a = _seq(series_prices)
    b = _seq(bench_prices)
    if len(a) < 2 or len(a) != len(b):
        raise ValueError("series 与 benchmark 长度不等或不足")
    ra = a[-1] / a[0] - 1.0
    rb = b[-1] / b[0] - 1.0
    return ra - rb


def drawdown(prices):
    """回撤序列：相对历史峰值的跌幅(≤0)。返回与 prices 同长的列表，首项按 0 计。"""
    p = _seq(prices)
    peak = -float("inf")
    out = []
    for v in p:
        peak = max(peak, v)
        out.append(v / peak - 1.0 if peak else 0.0)
    return out


def max_drawdown(prices):
    dd = drawdown(prices)
    return min(dd) if dd else 0.0


def volume_change(volumes):
    """成交量环比变化序列：vol[i]/vol[i-1]-1。"""
    v = [float(x) for x in volumes if x is not None]
    if len(v) < 2:
        return []
    return [v[i] / v[i - 1] - 1.0 for i in range(1, len(v))]


class ThemeBreadthSnapshot:
    """Breadth 接口占位。

    未来一个 Theme Campaign 可能需要：上涨家数 / 下跌家数 / 涨停家数 / 平均收益 / 中位数收益。
    实现依赖可靠的**历史成分**数据；本轮不生产结果、不编造，仅声明接口。
    特别注意：历史概念成分不能简单使用当前成分股列表（survivorship / look-ahead bias）。
    """

    UP = "up"; DOWN = "down"; LIMIT_UP = "limit_up"; MEAN = "mean"; MEDIAN = "median"

    def __init__(self, series_id, trade_date):
        self.series_id = series_id
        self.trade_date = trade_date
        self._data = None  # 预留：历史成分快照

    def require_history_snapshot(self):
        """Breadth 必须基于当日/当季真实成分快照，禁止用当前成分回填历史。"""
        raise NotImplementedError(
            "Breadth 数据未就绪：需先建立历史成分快照，避免 survivorship/look-ahead bias。")


def as_iso(d):
    """把 date/datetime/str 规整为 ISO YYYY-MM-DD（核验 trade_date 用）。"""
    if isinstance(d, str):
        return d[:10]
    if isinstance(d, (_dt.date, _dt.datetime)):
        return d.isoformat()[:10]
    raise TypeError(f"unsupported date type: {type(d)}")


def is_valid_iso_date(s):
    try:
        _dt.date.fromisoformat(str(s))
        return True
    except (ValueError, TypeError):
        return False