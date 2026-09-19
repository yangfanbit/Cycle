#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""apply_taxonomy_t01_v0_1.py —— T01 Historical Universe Taxonomy Gap Resolution（应用器）。

## 目的

一次性补齐 R01 Historical Universe Expansion 所需的 **Macro Theme taxonomy**，
使 `research/scripts/theme_taxonomy.py`（CMTR v1）能够解析 R01-01 ~ R01-06 的主题名称。

## 边界（严格）

- **只写 `themes` 表**。不改 Campaign / Evidence / Lifecycle / 任何其它表。
- **不改既有行**（4 个既有 root 与 15 个既有子主题的语义完全不动）。
- **不改 `theme_taxonomy.py`（CMTR v1）**。
- 不使用第二套 taxonomy resolution。
- 幂等：重复运行结果一致（已存在的行跳过）。

## 设计原则

> **Macro Theme root = 机制家族（mechanism family）**，用于 ThreeC 的**跨族结构比较**。
> 因此 root 的划分依据是**驱动机制是否同族**，而不是「行业分类是否同级」。

- root = 一个可独立比较的机制家族
- 子主题 = 该家族内可分辨的结构
- 深度不限（既有 `TH-AUTO → TH-NEV → TH-TESLA-CHAIN` 已为 3 层）

## 用法

    python research/scripts/apply_taxonomy_t01_v0_1.py --dry-run   # 只打印将执行的变更
    python research/scripts/apply_taxonomy_t01_v0_1.py             # 应用
    python research/scripts/apply_taxonomy_t01_v0_1.py --verify    # 只校验当前状态

决策记录见 `docs/T01_TAXONOMY_GAP_RESOLUTION_v0_1.md`。
"""

from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(ROOT, "research", "database", "cycle_research.db")

DECISION_ROUND = "T01"

# ------------------------------------------------------------------ 决策表
# (theme_id, name, theme_type, parent_theme_id, mechanism_family_note, source_proposal)
NEW_THEMES = [
    # ===== 新增 root（7）=====
    ("TH-HIEQ", "高端装备", "industry", None,
     "机制家族：制造业资本开支 / 设备更新 / 产业政策。与「汽车」（消费+产业政策）、"
     "「电力设备」（电力投资）机制不同。",
     "R01-01 MT001（NEW_MACRO_CANDIDATE）"),
    ("TH-ELEC", "电子", "industry", None,
     "机制家族：国产替代 / 技术周期 / 资本开支。与「信息通信」（通信网络与光互联）"
     "机制不同：电子侧为制造与设计，通信侧为网络与互联。",
     "R01-02 manifest macro_theme_candidates（半导体 / 电子）"),
    ("TH-RES", "资源", "industry", None,
     "机制家族：**供给收缩 / 成本驱动的价格周期**（当前 4 族完全缺失的机制轴）。"
     "覆盖有色金属、贵金属、稀有金属/稀土、基础化工、农化。",
     "R01-03 manifest macro_theme_candidates（有色金属 / 基础化工 / 贵金属 / 稀有金属·稀土 / 农化）"),
    ("TH-CONSUMER", "消费", "industry", None,
     "机制家族：**纯需求端驱动**（当前 4 族完全缺失的机制轴）。"
     "覆盖食品饮料、家用电器、农林牧渔、社会服务。",
     "R01-04 manifest macro_theme_candidates（消费 / 食品饮料 / 家用电器 / 农林牧渔 / 社会服务）"),
    ("TH-FIN", "金融", "industry", None,
     "机制家族：**流动性 / 市场 Beta**（当前 4 族完全缺失的机制轴）。"
     "★ 本族 Beta Contamination 风险最高 —— 独立成族是为了让该风险在结构上可见，"
     "不与「房地产」的地产政策周期混为一族。",
     "R01-05 manifest macro_theme_candidates（金融 / 银行 / 非银金融）"),
    ("TH-REALESTATE", "房地产", "industry", None,
     "机制家族：**地产政策周期 + 地产链需求**。与「金融」的流动性/市场 Beta 机制不同，"
     "故不合并（R00 coverage plan 的「金融/地产」为**任务方向**，非 taxonomy 强制）。",
     "R01-05 manifest macro_theme_candidates（房地产 / 建筑材料）"),
    ("TH-DEFENSE", "国防军工", "industry", None,
     "机制家族：**订单 / 事件驱动**（当前 4 族完全缺失的机制轴）。"
     "驱动变量为采购与订单节奏，而非产业政策文本。",
     "R01-06 manifest macro_theme_candidates（国防军工 / 航空装备 / 航天装备 / 船舶制造 / 军工电子）"),

    # ===== 高端装备 子主题（5）=====
    ("TH-HIEQ-CONSTR", "工程机械", "industry", "TH-HIEQ",
     "设备更新周期 + 基建/地产投资 + 环保排放淘汰。",
     "R01-01 MT004（SUB_THEME）"),
    ("TH-HIEQ-AUTOMATION", "工业自动化", "industry", "TH-HIEQ",
     "制造业固定资产投资与信贷周期 + 自动化渗透率。",
     "R01-01 MT003（SUB_THEME）"),
    ("TH-HIEQ-ROBOT", "机器人", "concept", "TH-HIEQ",
     "本体渗透率 + 技术突破 + 产业政策。★ 独立成 root 会与「汽车」下的 Robotaxi/智能驾驶 "
     "产生跨族冲突，故按 R01-01 的 SUB_THEME 提案置于「高端装备」之下。",
     "R01-01 MT002（SUB_THEME）"),
    ("TH-HIEQ-HUMANOID", "人形机器人", "concept", "TH-HIEQ-ROBOT",
     "2023 起注意力中心自工业机器人迁移至人形机器人（技术展示 → 量产预期 → 订单落地）。",
     "R01-01 candidates 005/007 的 theme_name_candidates"),
    ("TH-HIEQ-RAIL", "轨道交通装备", "industry", "TH-HIEQ",
     "单一买方（国铁集团）采购节奏。R01-01 判定其 2018–2025 未形成可比较的历史机会结构"
     "（exclusion R01-HIEQ-X004），但名称本身为合法的装备子域，故建立以便解析。",
     "R01-01 MT005（SUB_THEME）"),

    # ===== 电子 子主题（4）=====
    ("TH-ELEC-SEMI", "半导体", "industry", "TH-ELEC",
     "国产替代 + 技术周期 + 资本开支。",
     "R01-02 manifest macro_theme_candidates"),
    ("TH-ELEC-SEMI-EQUIP", "半导体设备", "industry", "TH-ELEC-SEMI",
     "设备资本开支周期；属装备制造但与「高端装备」的通用装备机制不同（买方为晶圆厂）。",
     "R01-02 manifest macro_theme_candidates"),
    ("TH-ELEC-SEMI-MAT", "半导体材料", "industry", "TH-ELEC-SEMI",
     "材料国产替代；与「资源」下的基础化工机制不同（买方为晶圆厂，认证壁垒而非价格周期）。",
     "R01-02 manifest macro_theme_candidates"),
    ("TH-ELEC-PANEL", "面板/显示", "industry", "TH-ELEC",
     "重资产价格周期（产能投放 → 价格下行 → 出清）。",
     "R01-02 manifest macro_theme_candidates"),

    # ===== 资源 子主题（5）=====
    ("TH-RES-METAL", "有色金属", "industry", "TH-RES",
     "矿山/冶炼供给 + 地产/新能源/电子需求 + 库存周期。",
     "R01-03 manifest macro_theme_candidates"),
    ("TH-RES-PRECIOUS", "贵金属", "industry", "TH-RES-METAL",
     "货币属性 / 避险 / 实际利率（与工业金属的供需机制不同，但同属有色金属大类）。",
     "R01-03 manifest macro_theme_candidates"),
    ("TH-RES-RARE", "稀有金属/稀土", "industry", "TH-RES-METAL",
     "配额与出口管制（政策）+ 磁材需求。",
     "R01-03 manifest macro_theme_candidates"),
    ("TH-RES-CHEM", "基础化工", "industry", "TH-RES",
     "产能投放 + 需求（地产/纺服/农业）+ 成本（油价）。",
     "R01-03 manifest macro_theme_candidates"),
    ("TH-RES-AGRI", "农化", "industry", "TH-RES-CHEM",
     "化肥/农药：农产品价格 + 出口 + 能耗双控。",
     "R01-03 manifest macro_theme_candidates"),

    # ===== 消费 子主题（4）=====
    ("TH-CONSUMER-FOOD", "食品饮料", "industry", "TH-CONSUMER",
     "需求端 + 渠道 + 提价能力。",
     "R01-04 manifest macro_theme_candidates"),
    ("TH-CONSUMER-APPLIANCE", "家用电器", "industry", "TH-CONSUMER",
     "需求端 + 地产后周期 + 出口。",
     "R01-04 manifest macro_theme_candidates"),
    ("TH-CONSUMER-AGRI", "农林牧渔", "industry", "TH-CONSUMER",
     "养殖/种植供给周期 + 需求。",
     "R01-04 manifest macro_theme_candidates"),
    ("TH-CONSUMER-SERVICE", "社会服务", "industry", "TH-CONSUMER",
     "出行/餐饮/旅游等服务消费需求。",
     "R01-04 manifest macro_theme_candidates"),

    # ===== 金融 子主题（2）=====
    ("TH-FIN-BANK", "银行", "industry", "TH-FIN",
     "息差 + 资产质量 + 低估值防御属性。",
     "R01-05 manifest macro_theme_candidates"),
    ("TH-FIN-NONBANK", "非银金融", "industry", "TH-FIN",
     "★ 券商行情常为市场 Beta 的代理 —— 是否构成独立 Campaign 须严格论证（不得默认成立）。",
     "R01-05 manifest macro_theme_candidates"),

    # ===== 房地产 子主题（2）=====
    ("TH-REALESTATE-DEV", "房地产开发", "industry", "TH-REALESTATE",
     "限购/信贷/保交楼等地产政策周期。",
     "R01-05 manifest macro_theme_candidates"),
    ("TH-REALESTATE-MATERIAL", "建筑材料", "industry", "TH-REALESTATE",
     "地产链需求（水泥/玻璃/管材）。",
     "R01-05 manifest macro_theme_candidates"),

    # ===== 国防军工 子主题（4）=====
    ("TH-DEFENSE-AIR", "航空装备", "industry", "TH-DEFENSE",
     "军机采购与交付节奏。",
     "R01-06 manifest macro_theme_candidates"),
    ("TH-DEFENSE-SPACE", "航天装备", "industry", "TH-DEFENSE",
     "航天发射与卫星组网节奏。",
     "R01-06 manifest macro_theme_candidates"),
    ("TH-DEFENSE-SHIP", "船舶制造", "industry", "TH-DEFENSE",
     "船舶订单与交付周期；军民两用属性（民用造船周期亦在此族）。",
     "R01-06 manifest macro_theme_candidates"),
    ("TH-DEFENSE-ELEC", "军工电子", "concept", "TH-DEFENSE",
     "军工元器件与信息化配套。与「电子」的国产替代机制不同（买方为军方）。",
     "R01-06 manifest macro_theme_candidates"),
]

# 明确**不创建**的名称（保留为 unresolved proposal / 别名 / 已由既有行承接）
NOT_CREATED = [
    ("机器人（作为 root）", "SUB_THEME 已足以承接；独立成 root 会与「汽车」下的 Robotaxi/智能驾驶 跨族冲突"),
    ("半导体（作为 root）", "作为「电子」下的子主题；半导体设备/材料为其下级（3 层）"),
    ("银行 / 非银金融（作为 root）", "「金融」下的子主题；避免机械按行业分类建根"),
    ("贵金属 / 稀有金属·稀土（作为 root）", "「有色金属」下的子主题"),
    ("农化（作为 root）", "「基础化工」下的子主题"),
    ("航空装备 / 航天装备 / 船舶制造 / 军工电子（作为 root）", "「国防军工」下的子主题"),
    ("食品饮料 / 家用电器 / 农林牧渔 / 社会服务（作为 root）", "「消费」下的子主题"),
    ("建筑材料（作为 root）", "「房地产」下的地产链子主题"),
    ("半导体设备 / 半导体材料（作为 root）", "「半导体」下的子主题"),
]


def note_of(mech: str, src: str) -> str:
    return "%s【%s taxonomy 决策｜来源：%s】" % (mech, DECISION_ROUND, src)


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    verify_only = "--verify" in argv

    if not os.path.isfile(DB_PATH):
        print("FAIL 找不到数据库: %s" % DB_PATH)
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    existing = {r["theme_id"]: dict(r) for r in cur.execute("SELECT * FROM themes")}
    print("应用前 themes 行数: %d" % len(existing))

    if verify_only:
        ok = True
        for tid, name, ttype, parent, mech, src in NEW_THEMES:
            row = existing.get(tid)
            if row is None:
                print("  MISSING  %s" % tid)
                ok = False
            elif row["name"] != name or row["theme_type"] != ttype or row["parent_theme_id"] != parent:
                print("  MISMATCH %s" % tid)
                ok = False
        print("verify: %s" % ("PASS" if ok else "FAIL"))
        conn.close()
        return 0 if ok else 1

    to_insert = []
    to_skip = []
    for row in NEW_THEMES:
        tid = row[0]
        if tid in existing:
            to_skip.append(tid)
        else:
            to_insert.append(row)

    print("将新增 %d 行；已存在跳过 %d 行" % (len(to_insert), len(to_skip)))
    for tid, name, ttype, parent, _mech, _src in to_insert:
        print("  + %-24s %-16s %-9s parent=%s" % (tid, name, ttype, parent))
    if to_skip:
        print("  跳过: %s" % ", ".join(to_skip))

    # 父节点必须存在（新增集内或既有集内）
    known = set(existing) | {r[0] for r in to_insert}
    bad = [r for r in to_insert if r[3] is not None and r[3] not in known]
    if bad:
        print("FAIL 父节点不存在: %s" % [r[0] for r in bad])
        conn.close()
        return 1

    # 名称唯一性（CMTR v1 对重名一律视为不可解析，必须避免）
    names_after = {r["name"] for r in existing.values()} | {r[1] for r in to_insert}
    if len(names_after) != len(existing) + len(to_insert):
        dup = sorted(
            n for n in names_after
            if sum(1 for x in list(existing.values()) + list(to_insert) if (x["name"] if isinstance(x, dict) else x[1]) == n) > 1
        )
        print("FAIL 存在重名（CMTR 将无法解析）: %s" % dup)
        conn.close()
        return 1

    if dry:
        print("--dry-run：未写入。")
        conn.close()
        return 0

    for tid, name, ttype, parent, mech, src in to_insert:
        cur.execute(
            "INSERT INTO themes (theme_id, name, theme_type, parent_theme_id, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (tid, name, ttype, parent, note_of(mech, src)),
        )

    # 安全校验：既有行必须逐字节不变
    after = {r["theme_id"]: dict(r) for r in cur.execute("SELECT * FROM themes")}
    for tid, before in existing.items():
        if after.get(tid) != before:
            print("FAIL 既有行被改动: %s" % tid)
            conn.rollback()
            conn.close()
            return 1

    conn.commit()
    print("应用后 themes 行数: %d（新增 %d）" % (len(after), len(after) - len(existing)))

    # 统计
    roots = sorted(r["name"] for r in cur.execute(
        "SELECT name FROM themes WHERE parent_theme_id IS NULL"))
    print("Macro Theme 根节点 (%d): %s" % (len(roots), roots))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
