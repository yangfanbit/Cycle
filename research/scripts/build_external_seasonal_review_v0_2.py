#!/usr/bin/env python3
"""build_external_seasonal_review_v0_2.py —— 外部季节性线索的**逐项核验**（v0.25）。

## 这一轮做什么

v0_1 把 25 项外部线索导入为**全部 `EXTERNAL_REFERENCE`**（导入 ≠ 验证）。本脚本对
**全部 25 项**逐项给出：性质 · 来源可核实性 · ThreeC 库内证据（主题子树 / 窗口内
Campaign / 机制是否吻合）· 反例 · 代表标的 · 处置结论与下一步。

## 六问（每项都必须回答）

1. 原始窗口声称什么、来源能否核实？
2. 它属于哪一类（重复季节性炒作 / 年度政策事件 / 财报日历 / 事件驱动 / 无稳定规律）？
3. 库内哪些年份真实出现过相关事件？窗口与机制是什么？
4. 哪些年份 / 反例不支持？样本够不够？
5. 有哪些代表标的，关系性质是什么，窗口行情能否取得？
6. 处置：进入历史地图 / 继续观察 / 部分支持 / 证据不足 / 减弱 / 拒绝？

## 硬纪律

- **原始报告未在仓库或本机** → 不得声称读过；`source_check.report_available = false` 恒为真。
- **窗口吻合 ≠ 机制吻合**：`campaigns_starting_in_window` 是机械统计，
  `mechanism_matched` 才是研究判断；两者**分开记录**，不得互相冒充。
- **MAPPED ≠ 规律成立**：映射只表示「有可跳转的历史对象」。
- **不为了让 25 项好看而提升成熟度**；没有证据就写「证据不足」。
- **代表标的只来自库内已登记对象**，不按涨幅挑。

用法：`python research/scripts/build_external_seasonal_review_v0_2.py`
产物：`research/current/external_seasonal_calendar_v0_2.json`（v0_1 逐字节保留）
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REPO = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from scripts import db  # noqa: E402

SRC = os.path.join(ROOT, "current", "external_seasonal_calendar_v0_1.json")
OUT = os.path.join(ROOT, "current", "external_seasonal_calendar_v0_2.json")
INDEX = os.path.join(ROOT, "current", "historical_event_maps_index.json")
REVIEWED_AT = "2026-10-19"

# ---------------------------------------------------------------- 研究判断（人写）
#
# nature        : 性质分类（见 §六问 2）
# disposition   : 成熟度码（沿用 maturity_model）
# mechanism     : 机制吻合的 Campaign（**研究判断**，非机械统计）
# reason        : 处置依据（必须能对上库内事实）
# next_step     : {kind: MAP|OBSERVE|DRAFT|NONE, target, text}
# counter       : 反例 / 不支持证据
# reps          : 代表标的（只来自库内登记）
J = {
    "EXT-01": dict(
        nature="年度政策事件（中央一号文件）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="文件发布是**制度性日历**，不是题材行情机制；库内根主题**无「农业」**（`农林牧渔` 是 `消费` 下的子主题），"
               "按治理规则⑥不为映射新建 canonical 主题。库内 2 个农林牧渔 Campaign（2018-08 猪价、2021-08 猪周期反转）"
               "**均不起始于 1–2 月** → 无窗口内样本。",
        next_step=dict(kind="DRAFT", target=None,
                       text="可作为「日历事件」带入研究请求草稿；若要检验，需按 1–2 月窗口对农林牧渔标的单独取行情（本轮未做）。"),
        counter=["库内无窗口内（1–2 月）农业 Campaign", "根主题缺失 → 无法与首页宏观主题行对照"],
        reps=[],
    ),
    "EXT-02": dict(
        nature="消费旺季（节日消费）",
        disposition="OBSERVING",
        mechanism=[],
        reason="映射到根主题「消费」（含食品饮料 / 家电 / 服务消费 11 个 Campaign）。**窗口内仅 1 个**（2023-01 量贩零食），"
               "且机制是**渠道变革 + 性价比消费**，与「春节消费」不同轴 → **机制吻合 0 个**。"
               "已建消费题材地图（5 事件），但事件窗口是 Campaign 主升段，**不是** 1–2 月。",
        next_step=dict(kind="MAP", target="CONSUMER_SEASON",
                       text="先看消费题材历史事件（窗口=主升段）；季节性本身**未验证**，需按 1–2 月窗口做专项检验。"),
        counter=["窗口内唯一 Campaign 的机制与春节无关", "消费地图 5 个事件无一起始于 1–2 月"],
        reps=[],
    ),
    "EXT-03": dict(
        nature="年度政策事件（两会）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="两会为**跨主题制度性事件**，不对应单一宏观主题；库内无「两会」对象，也无法用单一主题行对照。"
               "★ 不因「政策」二字就映射到某个根。",
        next_step=dict(kind="DRAFT", target=None,
                       text="仅作日历背景；如需研究，应针对**具体政策方向**（如产业政策）另立研究对象，而非「两会」本身。"),
        counter=["无对应主题 / 无对象 → 无法做窗口内统计"],
        reps=[],
    ),
    "EXT-04": dict(
        nature="财报日历（制度性披露期）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="3–4 月为法定披露期，是**全市场制度性安排**，不是某个题材的行情机制；库内无「财报季」对象。",
        next_step=dict(kind="NONE", target=None,
                       text="不进入历史地图；如需研究「业绩超预期」应另立研究对象（按业绩事件而非日历）。"),
        counter=["全市场现象，无法用单一主题检验"],
        reps=[],
    ),
    "EXT-05": dict(
        nature="行业季节性（外部称「九月效应」）",
        disposition="OBSERVING",
        mechanism=["C-2019-MIL-GROUP-RESTRUCTURE"],
        reason="国防军工子树 2 个 Campaign，**窗口内 1 个**：`C-2019-MIL-GROUP-RESTRUCTURE`（2019-07-01 起，南北船战略性重组）"
               "—— 机制与「军工集团重组催化」**吻合**。但**仅 1 年样本**，且 2020 年军工行情（装备订单）起始于 6 月、"
               "不在 7–9 月 → **不足以支持「九月效应」**。",
        next_step=dict(kind="DRAFT", target=None,
                       text="样本 n=1；建议按 7–9 月窗口对军工集团 / 主机厂做多年份检验后再决定是否建图。"),
        counter=["2020 军工主升段起始于 6 月（窗口外）", "n=1，无法区分「九月效应」与「重组事件驱动」"],
        reps=[{"security_id": "CSSC", "name": "中国船舶", "role": "Campaign 登记 representative",
               "note": "2019 南北船重组事件的直接标的；行情覆盖 2018-03-21 → 2019-11-26"}],
    ),
    "EXT-06": dict(
        nature="行业季节性（科技产品发布季）",
        disposition="OBSERVING",
        mechanism=[],
        reason="电子子树 8 个 Campaign，窗口内（8–9 月）1 个：`C-2024-SEMI-MEMORY`（2024-09-24 起，存储超级周期）。"
               "但其机制是 **AI 需求 + 原厂减产**，与「消费电子新品发布」不同轴 → **机制吻合 0 个**。",
        next_step=dict(kind="OBSERVE", target=None,
                       text="外部未指明公司与产品线，无法构造可检验口径；暂不建图，保留观察。"),
        counter=["窗口内唯一 Campaign 由 AI/供给驱动，与新品发布无关"],
        reps=[],
    ),
    "EXT-07": dict(
        nature="消费旺季（中秋 / 国庆）",
        disposition="OBSERVING",
        mechanism=[],
        reason="消费子树 11 个 Campaign，**窗口内（9–10 月）0 个** → 库内无窗口内样本。",
        next_step=dict(kind="MAP", target="CONSUMER_SEASON",
                       text="可先看消费题材历史事件；季节性本身未验证（无窗口内样本）。"),
        counter=["0 个 Campaign 起始于 9–10 月"],
        reps=[],
    ),
    "EXT-08": dict(
        nature="消费旺季（电商大促）",
        disposition="OBSERVING",
        mechanism=[],
        reason="窗口内（10–11 月）1 个：`C-2019-CONS-AESTHETICS`（2019-11-06，医美/颜值经济）—— 机制与「双十一电商大促」**不同轴**。"
               "→ 机制吻合 0 个。",
        next_step=dict(kind="MAP", target="CONSUMER_SEASON",
                       text="先看消费题材历史事件；「双十一」需按电商 / 快递 / 家电等具体品类单独检验。"),
        counter=["窗口内唯一 Campaign 为医美，不是电商大促"],
        reps=[],
    ),
    "EXT-09": dict(
        nature="行业季节性（供暖 / 能源）",
        disposition="OBSERVING",
        mechanism=[],
        reason="映射到「电力（运营端）」（3 个主题节点 / 2 个 Campaign：2021-09 绿电、2023-01 火电），"
               "**窗口内（11–12 月）0 个**。★ 且「供暖」同时涉及燃料端（煤炭 / 天然气）与供热运营，"
               "现有根主题**不覆盖**燃料端 → 映射本身是**最接近而非同轴**。",
        next_step=dict(kind="DRAFT", target=None,
                       text="需先明确口径（燃料端 vs 运营端）；本轮不建图。"),
        counter=["0 个窗口内 Campaign", "映射为「最接近根」而非同轴（燃料端缺失）"],
        reps=[],
    ),
    "EXT-10": dict(
        nature="市场现象（全市场流动性 / 风险偏好）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="「春季躁动」是**全市场现象**，不对应单一宏观主题；库内无对应对象。"
               "★ 若要用基准指数检验，属**市场层**问题（可用 SH000300），但本轮未做该项统计。",
        next_step=dict(kind="OBSERVE", target=None,
                       text="如需检验，应以 SH000300 的 12–2 月窗口做多年份统计（市场层，不涉及题材）。"),
        counter=["无主题归属；只能作为市场层现象检验"],
        reps=[],
    ),
    "EXT-11": dict(
        nature="行业季节性（冰雪经济）",
        disposition="OBSERVING",
        mechanism=[],
        reason="消费子树 11 个 Campaign，跨年窗口（10–3 月）内 5 个，但机制分别是医美、服务消费修复、量贩零食、以旧换新、白酒 —— "
               "**无一是冰雪经济**（库内**无**冰雪旅游 / 装备对象）→ 机制吻合 0 个。★ 窗口吻合是**假阳性**的典型例子。",
        next_step=dict(kind="DRAFT", target=None,
                       text="库内无冰雪经济对象；如需研究须先由 Research 轮次补该题材对象与标的，不得用消费类对象顶替。"),
        counter=["5 个窗口内 Campaign 全部与冰雪经济无关", "无冰雪旅游 / 装备对象"],
        reps=[],
    ),
    "EXT-12": dict(
        nature="行业季节性（呼吸道传染病季）",
        disposition="PARTIALLY_VALIDATED",
        mechanism=["FLU-2018-SEASONAL", "PUBLICHEALTH-2019-WUHAN", "FLU-2024-SEASONAL"],
        reason="库内有**专门的流感题材地图**（6 事件）与**跨年份比较**（11 个季节窗口）：其中 3 个事件窗口落在 9–1 月内"
               "（2017-09→2018-01、2019-12→2020-01、2024-09→2025-01）。经验基准概率 **1/9 = 11.1%**"
               "（95% Wilson 2.0%–43.5%，分母只含 `comparable === true`）。"
               "★ 唯一 UP 由 `UNKNOWN_PUBLIC_HEALTH` 驱动，`SEASONAL_FLU` 完整可比年 UP = **0** → 只能算**部分验证**。",
        next_step=dict(kind="MAP", target="FLU",
                       text="进入流感题材地图看逐季窗口与经验基准概率（标注「未校准」）。"),
        counter=["`SEASONAL_FLU` 完整可比年 UP = 0；唯一 UP 属公共卫生事件", "n=9，Wilson 区间极宽"],
        reps=[{"security_id": "HUALAN-002007", "name": "华兰生物", "role": "流感地图 2017/2018/2024 季参与标的",
               "note": "疫苗 / 血制品；行情覆盖 2015-01-05 → 2026-01-30"}],
    ),
    "EXT-13": dict(
        nature="行业季节性（暑期档影视 / 旅游 / 游戏）",
        disposition="OBSERVING",
        mechanism=[],
        reason="文化传媒 3 个 Campaign（2018-12 版号、2021-09 元宇宙、2023-03 AI+内容），**窗口内（6–8 月）0 个** → 无窗口内样本。"
               "已有传媒地图（2 事件），但其窗口同样不在 6–8 月。",
        next_step=dict(kind="MAP", target="MEDIA",
                       text="先看传媒题材历史事件；「暑期档」季节性**未验证**（0 个窗口内样本）。"),
        counter=["0 个 Campaign 起始于 6–8 月"],
        reps=[],
    ),
    "EXT-14": dict(
        nature="行业季节性（迎峰度夏）",
        disposition="PARTIALLY_VALIDATED",
        mechanism=["POWER-2017-SUMMER-COUNTEREXAMPLE", "POWER-2022-SUMMER", "POWER-2024-SUMMER-COUNTEREXAMPLE"],
        reason="库内有**电力题材地图**（4 事件）与**跨年份比较**（10 年）：3 个事件窗口落在 5–7 月内（2017 / 2022 / 2024）。"
               "经验基准概率 **1/7 = 14.3%**（95% Wilson 2.6%–51.3%）。★ 结果定义来自源数据 `outcome_rule`"
               "（火电池**全部上涨且全部跑赢基准**才算 UP）→ 只能算**部分验证**，且 2017 两组行情**无法复算**（WARN）。",
        next_step=dict(kind="MAP", target="POWER_SUMMER",
                       text="进入电力题材地图看逐年窗口与经验基准概率（标注「未校准」）。"),
        counter=["2017 反例：窗口内下跌", "`outcome_rule` 严格（需全部跑赢基准），n=7 且 Wilson 极宽"],
        reps=[{"security_id": "HUADIAN", "name": "华电国际", "role": "电力地图 2022/2023/2024 事件参与标的",
               "note": "火电运营；行情覆盖 2022-01-04 → 2024-12-31"}],
    ),
    "EXT-15": dict(
        nature="消费旺季（五一假期）",
        disposition="OBSERVING",
        mechanism=[],
        reason="消费子树 11 个 Campaign，**窗口内（4–5 月）0 个** → 无窗口内样本。",
        next_step=dict(kind="MAP", target="CONSUMER_SEASON",
                       text="先看消费题材历史事件；「五一」季节性未验证。"),
        counter=["0 个 Campaign 起始于 4–5 月"],
        reps=[],
    ),
    "EXT-16": dict(
        nature="行业季节性（制冷 / 降温商品）",
        disposition="OBSERVING",
        mechanism=[],
        reason="窗口内（6–8 月）6 个消费类 Campaign，机制分别为白酒、免税、白电、医美、服务修复 —— "
               "**无一是「降温商品」驱动的季节性**（空调 / 制冷剂等）→ 机制吻合 0 个。",
        next_step=dict(kind="DRAFT", target=None,
                       text="外部未指明品类；如需检验须先确定品类（空调 / 制冷剂 / 啤酒等）再取行情。"),
        counter=["6 个窗口内 Campaign 均为其他机制"],
        reps=[],
    ),
    "EXT-17": dict(
        nature="行业季节性（防汛 / 水利）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="库内 13 个根主题中**无「建筑 / 水利」**，按治理规则⑥不为此新建 canonical 主题；无对象可对照。",
        next_step=dict(kind="DRAFT", target=None,
                       text="库内无对应主题；如需研究须先补主题与对象（Research 轮次）。"),
        counter=["无对应根主题 → 无法对照"],
        reps=[],
    ),
    "EXT-18": dict(
        nature="消费旺季（618 电商）",
        disposition="OBSERVING",
        mechanism=[],
        reason="窗口内（5–6 月）4 个消费类 Campaign（白酒 2016-06、免税 2020-06、白电 2020-06 等），"
               "机制均**不是**「618 电商大促」→ 机制吻合 0 个。",
        next_step=dict(kind="MAP", target="CONSUMER_SEASON",
                       text="先看消费题材历史事件；「618」需按电商 / 快递 / 家电单独检验。"),
        counter=["窗口内 Campaign 由行业周期驱动，非电商大促"],
        reps=[],
    ),
    "EXT-19": dict(
        nature="行业季节性（金九银十，通常指地产销售）",
        disposition="OBSERVING",
        mechanism=[],
        reason="房地产子树 2 个 Campaign（2020-08 三道红线、2022-11 三支箭），**窗口内（9–10 月）0 个** → 无窗口内样本。"
               "★ 且「金九银十」亦可指汽车 / 家电，外部未限定。",
        next_step=dict(kind="DRAFT", target=None,
                       text="口径未限定（地产 / 汽车 / 家电）；本轮不建图，保留观察。"),
        counter=["0 个窗口内 Campaign", "外部口径未限定行业"],
        reps=[],
    ),
    "EXT-20": dict(
        nature="资源品（黄金 / 稀土）",
        disposition="OBSERVING",
        mechanism=[],
        reason="资源子树 8 个 Campaign，**窗口内（10 月）1 个**：`C-2020-RES-LITHIUM`（2020-10-27，锂）—— 机制是**锂**，"
               "与黄金 / 稀土**不同轴** → 机制吻合 0 个。库内 2020 稀土（5 月起）、2024 黄金（2 月起）**都不在 10 月**。"
               "已建资源品地图（2 事件），但其窗口不是 10 月。",
        next_step=dict(kind="MAP", target="RESOURCE_METAL",
                       text="先看资源品历史事件（黄金与稀土机制不同轴）；「10 月」季节性**未验证**。"),
        counter=["窗口内唯一 Campaign 是锂，不是黄金 / 稀土", "黄金与稀土机制不同，原线索合并口径本身有问题"],
        reps=[],
    ),
    "EXT-21": dict(
        nature="政策 / 行业（环保）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="库内 13 个根主题中**无「环保 / 公用事业」**（`电力（运营端）` 是运营端机制，与环保不同轴）；无对象可对照。"
               "多段窗口（3 月；11 月→次年 1 月）本身也说明外部口径不稳定。",
        next_step=dict(kind="DRAFT", target=None,
                       text="库内无对应主题；如需研究须先补主题与对象。"),
        counter=["无对应根主题", "窗口多段且跨年，外部口径不统一"],
        reps=[],
    ),
    "EXT-22": dict(
        nature="行业季节性（教育）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="库内 13 个根主题中**无「教育」**，按治理规则⑥不新建 canonical 主题；无对象可对照。",
        next_step=dict(kind="DRAFT", target=None,
                       text="库内无对应主题；如需研究须先补主题与对象。"),
        counter=["无对应根主题"],
        reps=[],
    ),
    "EXT-23": dict(
        nature="事件驱动（无固定窗口）",
        disposition="MAPPED",
        mechanism=["C-2023-HIEQ-HUMANOID"],
        reason="外部明确「无固定月份，取决于催化事件」→ **不适用季节性检验**。库内高端装备子树 5 个 Campaign，"
               "已有机器人题材地图（1 事件：2023-05→2023-12 人形机器人）。映射只表示**有可跳转的历史对象**，"
               "**不**表示「AI+ / 机器人」存在季节性规律。",
        next_step=dict(kind="MAP", target="ROBOTICS",
                       text="进入机器人题材地图看 2023 人形机器人事件的催化与标的；事件驱动题材**不做**季节性判断。"),
        counter=["无固定窗口 → 无法做季节性统计", "原线索把 AI / 机器人 / 商业航天 / 低空经济合并，机制不同轴"],
        reps=[],
    ),
    "EXT-24": dict(
        nature="事件驱动（展会 / 年度事件，逐年变化）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="外部明确「逐年变化，需有当年具体日期」→ 无当年日期时**无法确定当期状态**（治理规则③禁止伪造固定窗口）；"
               "库内亦无对应主题。",
        next_step=dict(kind="NONE", target=None,
                       text="不进入地图；需要当年具体日程时再议。"),
        counter=["无固定窗口且无当年日期 → 不可检验"],
        reps=[],
    ),
    "EXT-25": dict(
        nature="财报季 / 事件（高送转）",
        disposition="EXTERNAL_REFERENCE",
        mechanism=[],
        reason="「高送转」是**跨行业事件**，不对应单一宏观主题；库内无对应对象。"
               "★ 外部报告称「该效应已减弱」，但 ThreeC **无独立证据** → **不**据此标 `WEAKENED`（治理规则④：外部意见不转结论）。",
        next_step=dict(kind="DRAFT", target=None,
                       text="如需检验，需按「预案公告日」构造事件样本（库内暂无该数据）。"),
        counter=["无主题归属", "外部「已减弱」说法未在 ThreeC 独立验证"],
        reps=[],
    ),
}


# ---------------------------------------------------------------- 证据计算

def theme_tree(conn) -> dict:
    return {r["theme_id"]: r for r in conn.execute("SELECT * FROM themes")}


def descendants(themes: dict, name: str) -> set:
    root = [t for t in themes.values() if t["name"] == name and not t["parent_theme_id"]]
    if not root:
        return set()
    out = {root[0]["theme_id"]}
    changed = True
    while changed:
        changed = False
        for t in themes.values():
            if t["parent_theme_id"] in out and t["theme_id"] not in out:
                out.add(t["theme_id"])
                changed = True
    return out


def in_window(month: int, windows) -> bool:
    for w in windows:
        s, e, cross = w["start_month"], w["end_month"], w["cross_year"]
        if (not cross and s <= month <= e) or (cross and (month >= s or month <= e)):
            return True
    return False


def main() -> int:
    if os.path.exists(OUT):
        print("FAIL: 目标已存在，拒绝覆盖：%s" % os.path.relpath(OUT, REPO))
        return 1
    with open(SRC, encoding="utf-8") as fh:
        src = json.load(fh)
    with open(INDEX, encoding="utf-8") as fh:
        index = json.load(fh)
    map_by_ext = {}
    for m in index["maps"]:
        for eid in m.get("external_entry_ids") or []:
            map_by_ext[eid] = m["theme_id"]

    conn = db.connect()
    themes = theme_tree(conn)
    camps = conn.execute(
        "SELECT c.campaign_id, c.campaign_year, c.start_date, ct.theme_id "
        "FROM campaigns c JOIN campaign_themes ct ON ct.campaign_id=c.campaign_id AND ct.role='main'"
    ).fetchall()

    entries = []
    for e in src["entries"]:
        j = J.get(e["id"])
        if j is None:
            raise SystemExit("FAIL: 缺少 %s 的研究判断" % e["id"])
        macro = e["mapping"].get("macro_theme")
        tree = descendants(themes, macro) if macro else set()
        cands = [c for c in camps if c["theme_id"] in tree]
        inwin = [c for c in cands if c["start_date"] and in_window(int(c["start_date"][5:7]), e["windows"])]

        out = dict(e)
        out["maturity"] = j["disposition"]
        out["evidence_refs"] = sorted({c["campaign_id"] for c in inwin})
        out["observations"] = [
            "%d 年 %s 起：%s（窗口%s）" % (
                c["campaign_year"], c["start_date"], c["campaign_id"],
                "内" if c in inwin else "外")
            for c in sorted(cands, key=lambda x: x["start_date"] or "")
        ]
        out["verification"] = {
            "reviewed_at": REVIEWED_AT,
            "nature": j["nature"],
            "source_check": {
                "report_available": False,
                "note": "原始外部报告**未在仓库或本机找到**（v0_1 已记录）；本项结论**不**基于原报告，"
                        "只基于库内数据与可核实的公开常识，窗口口径直接采自任务指令中的表格。",
            },
            "threec_evidence": {
                "macro_theme": macro,
                "theme_campaigns": len(cands),
                "campaigns_starting_in_window": len(inwin),
                "mechanism_matched_campaigns": [x for x in j["mechanism"] if x.startswith("C-")],
        "mechanism_matched_events": [x for x in j["mechanism"] if not x.startswith("C-")],
                "map_theme_id": map_by_ext.get(e["id"]),
                "note": "★ 「窗口内起始」是机械统计；「机制吻合」是研究判断 —— 两者分开记录，不得互相冒充。",
            },
            "counter_evidence": j["counter"],
            "representatives": j["reps"],
            "disposition": j["disposition"],
            "reason": j["reason"],
            "next_step": j["next_step"],
        }
        out["revision"] = list(e.get("revision") or []) + [{
            "date": REVIEWED_AT,
            "change": "v0_2 逐项核验：成熟度 %s → %s（依据与下一步见 `verification`）"
                      % (e["maturity"], j["disposition"]),
        }]
        entries.append(out)
    conn.close()

    dist = {}
    for e in entries:
        dist[e["maturity"]] = dist.get(e["maturity"], 0) + 1
    mapped = sum(1 for e in entries if e["mapping"]["status"] == "MAPPED")
    with_map = sum(1 for e in entries if e["verification"]["threec_evidence"]["map_theme_id"])

    doc = dict(src)
    doc["artifact_version"] = "0.2"
    doc["generated_at"] = REVIEWED_AT
    doc["supersedes"] = "external_seasonal_calendar_v0_1.json"
    doc["position"] = (
        "★★ v0_2：**25 项已逐项核验**（v0_1 只导入、全部 `EXTERNAL_REFERENCE`）。"
        "每项新增 `verification`：性质 · 来源可核实性 · 库内证据（主题子树 / 窗口内 Campaign / 机制是否吻合）· "
        "反例 · 代表标的 · 处置与下一步。★ `MAPPED` 仍**只**表示「有可跳转的历史对象」，**不**表示规律成立；"
        "`THREEC_VALIDATED` 本轮**没有**任何一项达到（最高为 `PARTIALLY_VALIDATED`）。"
    )
    doc["verification_method"] = {
        "reviewed_at": REVIEWED_AT,
        "questions": [
            "① 原始窗口声称什么、来源能否核实？",
            "② 性质：重复季节性炒作 / 年度政策事件 / 财报日历 / 事件驱动 / 无稳定规律？",
            "③ 库内哪些年份真实出现过相关事件？窗口与机制是什么？",
            "④ 哪些年份 / 反例不支持？样本够不够？",
            "⑤ 有哪些代表标的、关系性质、窗口行情能否取得？",
            "⑥ 处置：进入地图 / 继续观察 / 部分支持 / 证据不足 / 减弱 / 拒绝？",
        ],
        "hard_rules": [
            "★ 原始报告不可得 → 不声称已读；结论只基于库内数据与可核实常识。",
            "★ 窗口吻合 ≠ 机制吻合（两者分开记录）。",
            "★ 不为了让 25 项好看而提升成熟度；没有证据就写「证据不足」。",
            "★ 外部意见（如「高送转已减弱」）不转为 ThreeC 结论。",
        ],
    }
    doc["verification_summary"] = {
        "total": len(entries),
        "distribution": dist,
        "mapped_to_theme": mapped,
        "with_map": with_map,
        "no_map": len(entries) - with_map,
        "note": "★ 成熟度是**研究进展**，不是「题材好坏」。`EXTERNAL_REFERENCE` = 已核验但**无对应主题 / 无对象**，"
                "不是「没做」。",
    }
    doc["entries"] = entries

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
    print("已生成 %s" % os.path.relpath(OUT, REPO))
    print("  分布：%s" % dist)
    print("  有地图可跳转：%d / %d" % (with_map, len(entries)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
