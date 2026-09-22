#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Historical Driver Canonicalization v0.3（deterministic，只读）。

**与 v0.1 / v0.2 的关系**
  · **canonical vocabulary 完全不变**（仍为 `research/current/schema.json` 的 `narrativeType` 9 项）；
  · **mapping_status 语义完全不变**（DIRECT / DERIVED / AMBIGUOUS / UNKNOWN / NOT_AVAILABLE）；
  · **映射逻辑完全不变**（命中规则数 → 状态；价格/行情结果 → NOT_AVAILABLE）；
  · **唯一变化 = 关键词表扩展**（`ADDED_RULES`，逐条注明覆盖的 R01 词汇缺口）。
  · v0.1 / v0.2 产物**逐字节保留**，本版本写入独立文件。

**本轮扩展动机（R01 实测）**：v0.1/v0.2 的关键词表在 **17-cycle 时代**校准，
R01-01~R01-06 新增的历史 driver 文本（政策制度 / 供给收缩 / 需求指标 / 估值资金 / 事件催化）
大量落入 `UNKNOWN` → 该 cycle 无 canonical driver → SA 被迫 `INSUFFICIENT_EVIDENCE`。
本版本**只做关键词覆盖补全**，**不改变任何机制判断标准**。

**禁止（沿用 §十五，本版未放宽）**
  · ❌ 新增 driver vocabulary
  · ❌ 从 `event_type` 反推 driver
  · ❌ 从价格 / 涨跌 / 相对收益**结果**反推 driver（`PRICE_ACTION` 排除逻辑保持有效）
  · ❌ 修改 v0.1 / v0.2 产物

产物：
  research/research/reports/historical_driver_canonicalization_v0_3.json
  research/research/reports/historical_driver_evidence_ledger_v0_3.json

用法：python research/scripts/canonicalize_historical_drivers_v0_3.py [--check]
"""
import collections
import io
import json
import os
import re
import sys

ROOT = r"D:/@AW/投资/ThreeC"
REP = f"{ROOT}/research/research/reports"
CHECK = "--check" in sys.argv
OUT_CANON = f"{REP}/historical_driver_canonicalization_v0_3.json"
OUT_LEDGER = f"{REP}/historical_driver_evidence_ledger_v0_3.json"

CANONICAL_DRIVERS = ["POLICY_DRIVEN", "INDUSTRY_UPGRADE", "TECH_BREAKTHROUGH", "DEMAND_SURGE",
                     "SUPPLY_CONTRACTION", "VALUATION_RESET", "CYCLE_REVERSAL",
                     "EVENT_CATALYST", "UNKNOWN"]

# ---------------------------------------------------------------- v0.1 原始关键词表（逐字保留，未修改）
RULES_V01 = {
    "POLICY_DRIVEN": [
        "政策", "规划", "通知", "指导意见", "国常会", "政治局", "工信部", "部委", "发改委", "能源局",
        "医保局", "中医药局", "交通部", "财政部", "税务总局", "五部门", "四部委", "国务院", "国资委",
        "补贴", "试点", "牌照", "法规", "集采", "医保", "标准体系", "标准化", "双碳", "碳达峰", "碳中和",
        "核准", "备案", "平价上网", "新政", "专项行动", "实景实训", "吹风",
    ],
    "TECH_BREAKTHROUGH": [
        "技术", "突破", "首发", "首次", "亮相", "GTC", "量产", "ADS", "天神之眼", "智驾", "算法",
        "刀片电池", "超级电驱", "DE-i", "CPO", "NPO", "1.6T", "800G", "400G", "结构迁移",
        "光引擎", "算电协同", "具身智能", "人形机器人", "脑机接口", "标准体系（2026 版）",
    ],
    "INDUSTRY_UPGRADE": [
        "结构迁移", "升级", "渗透率", "国产化", "规模化", "代际", "产业链", "环节", "全链条",
        "生态", "一体化", "扩围", "迁移", "供应链", "国产替代",
    ],
    "DEMAND_SURGE": [
        "需求", "订单", "销量", "出货", "装机", "景气", "放量", "增长", "翻倍", "出口", "刚需",
        "刚", "营收", "净利润", "业绩", "并网", "招标", "采购", "付费", "试运营", "客座率",
    ],
    "SUPPLY_CONTRACTION": [
        "产能", "供给", "过剩", "涨价", "价格", "库存", "缺芯", "出清", "挤压", "利润", "售价",
        "降价", "成本", "硅料", "多晶硅", "限产",
    ],
    "VALUATION_RESET": [
        "估值", "低估值", "修复", "估值杀", "泡沫", "破万亿", "市值", "倍", "x ", "抱团", "高估值",
        "虹吸", "风格",
    ],
    "CYCLE_REVERSAL": [
        "见顶", "见底", "退潮", "衰减", "回调", "反转", "结束", "出清完成", "分化", "回落", "回撤",
        "震荡", "亏钱效应", "断板", "跌停", "低点", "高点",
    ],
    "EVENT_CATALYST": [
        "发布会", "上市", "展会", "催化", "开工", "启动仪式", "峰会", "论坛", "大会", "嘉年华",
        "跑出圈", "中标", "获批",
    ],
}

# ---------------------------------------------------------------- v0.3 新增关键词（**逐条注明覆盖来源**）
# 每条 value = (关键词, 覆盖说明)。说明记录该词对应的 R01 实测缺口，便于审计。
ADDED_RULES = {
    # 制度 / 监管 / 官方行动 / 产业规划 —— R01 大量使用制度名称而非「政策」二字
    "POLICY_DRIVEN": [
        ("条例", "C-2020-CONS-BEAUTY-CN：《化妆品监督管理条例》"),
        ("规范", "C-2020-CONS-BEAUTY-CN：《化妆品功效宣称评价规范》"),
        ("纲要", "C-2022-CONS-SERVICE-REBOUND / 交通强国建设纲要类文本"),
        ("行动计划", "RC-2024-MIL-COMMERCIAL-SPACE：国家航天局行动计划"),
        ("方案", "C-2019-RES-DYE-SHOCK：化工行业整治提升方案"),
        ("整治", "C-2019-RES-DYE-SHOCK：园区整治 / 环保整治"),
        ("核查", "C-2016-HIEQ-CONSTR：北方环保核查"),
        ("环保", "C-2016-HIEQ-CONSTR：排放不达标强制淘汰"),
        ("指标", "C-2020-RES-RAREEARTH：开采指标 / 冶炼分离指标"),
        ("配额", "供给端行政配额（行政手段）"),
        ("三道红线", "C-2020-RE-DEBT-RISK：房地产金融审慎管理制度"),
        ("审慎管理", "C-2020-RE-DEBT-RISK：房地产金融审慎管理"),
        ("集中度", "C-2020-RE-DEBT-RISK：房地产贷款集中度管理制度"),
        ("保交楼", "R01-05：保交楼政策阶段"),
        ("因城施策", "R01-05：地方调控"),
        ("三支箭", "C-2022-RE-POLICY-THREE：信贷/债券/股权三支箭"),
        ("第二支箭", "C-2022-RE-POLICY-THREE：交易商协会债券融资支持工具"),
        ("交易商协会", "C-2022-RE-POLICY-THREE：第二支箭发行主体"),
        ("疫情防控", "C-2022-CONS-SERVICE-REBOUND：疫情防控措施优化"),
        ("新十条", "C-2022-CONS-SERVICE-REBOUND：新十条"),
        ("措施优化", "C-2022-CONS-SERVICE-REBOUND：措施优化"),
        ("收储", "C-2021-CONS-HOG-REVERSAL：中央冻猪肉储备收储"),
        ("储备", "C-2021-CONS-HOG-REVERSAL：储备调控"),
        ("特别国债", "C-2024-CONS-TRADE-IN：超长期特别国债支持以旧换新"),
        ("财政", "财政资金安排（制度性资金）"),
        ("军民融合", "RC-2015-MIL-REFORM-BULL：军民融合上升为国家战略"),
        ("国家战略", "RC-2015-MIL-REFORM-BULL：上升为国家战略"),
        ("混改", "R01-06：军工混改"),
        ("国企改革", "R01-05：中特估 / 国企改革"),
        ("战略性重组", "C-2019-MIL-GROUP-RESTRUCTURE：南北船战略性重组"),
        ("集团重组", "C-2019-MIL-GROUP-RESTRUCTURE：集团重组"),
        ("资产注入", "军工资产证券化"),
        ("资产证券化", "军工资产证券化"),
        ("军品", "C-2020-MIL-EQUIP-ORDER：军品采购"),
        ("装备采购", "C-2020-MIL-EQUIP-ORDER：装备采购节奏"),
        ("军费", "军费 / 国防预算（政策—军费层）"),
        ("国防预算", "军费 / 国防预算（政策—军费层）"),
        # ★ v0.3-r1 修正：「阅兵」「纪念大会」**不属于 POLICY_DRIVEN** —— 见文件头 REVISIONS。
        #   理由：阅兵是一次性重大纪念活动（事件），不改变任何产业规则（无补贴/准入/配额/采购规则变更）；
        #   且 v0.1 `EVENT_CATALYST` 已含「大会」「峰会」「论坛」「启动仪式」等同类型活动。
        #   → 已移至 EVENT_CATALYST（跨 canonical 重复会制造 DERIVED/AMBIGUOUS 并丢失机制）。
        ("实体清单", "C-2019-SEMI-LOCALIZATION：实体清单"),
        ("出口管制", "C-2022-SEMI-DOWNTURN：对华半导体限制"),
        ("限制", "C-2022-SEMI-DOWNTURN：出口限制"),
        ("大基金", "C-2019-SEMI-LOCALIZATION / C-2020-SEMI-EQUIPMENT：国家集成电路产业投资基金"),
        ("产业投资基金", "产业基金 / 地方产业基金"),
        ("产业基金", "C-2023-HIEQ-HUMANOID：北京市机器人产业基金"),
        ("投资计划", "C-2022-POWER-GRID：国家电网年度投资计划"),
        ("能源局", "（已有）"),
        ("行动计划", "（重复键合并，见上）"),
    ],
    # 供给收缩 —— 事故 / 停产 / 关停 / 限产 / 惜售 / 供应受限（**机制表述**，非价格结果）
    "SUPPLY_CONTRACTION": [
        ("停产", "C-2019-RES-DYE-SHOCK：园区停产 / 延迟复工"),
        ("停工", "供给端停工"),
        ("关闭", "C-2019-RES-DYE-SHOCK：彻底关闭响水化工园区"),
        ("关停", "供给端关停"),
        ("压减", "C-2019-RES-DYE-SHOCK：压减化工生产企业数量"),
        ("削减", "C-2021-RES-CHEM-DUALCTRL：产量削减约 90%"),
        ("整治提升", "C-2019-RES-DYE-SHOCK：整治提升方案"),
        ("惜售", "C-2020-RES-RAREEARTH：持货端锁货惜售"),
        ("锁货", "C-2020-RES-RAREEARTH：锁货惜售"),
        ("现货稀少", "C-2020-RES-RAREEARTH：现货稀少"),
        ("供应受限", "C-2020-RES-LITHIUM：锂矿供应受限"),
        ("供需缺口", "C-2020-RES-LITHIUM：供需缺口扩大"),
        ("口岸关闭", "C-2020-RES-RAREEARTH：中缅口岸关闭"),
        ("进口量", "C-2020-RES-RAREEARTH：缅甸矿进口量下降"),
        ("能耗双控", "C-2021-RES-CHEM-DUALCTRL：能耗双控"),
        ("双控", "C-2021-RES-CHEM-DUALCTRL：能耗双控"),
        ("限电", "C-2021-RES-CHEM-DUALCTRL：限电"),
        ("去化", "产能去化"),
        # ★ v0.3-r2 修正：删除「扩产周期」—— 见文件头 REVISIONS。
        #   理由：① 零增量覆盖（其唯一命中文本「国内晶圆厂进入扩产周期」已被「扩产」完全覆盖）；
        #   ② 方向错误（「产能扩张」在机制上与「供给收缩」相反）；
        #   ③ 它使该文本额外命中 SUPPLY_CONTRACTION → 把本应得到 DEMAND_SURGE 的文本推入 2-命中 DERIVED/None。
        #   「扩产」保留在 DEMAND_SURGE（见 DEMAND_SURGE 段）。
    ],
    # 需求放量 —— 订单 / 预付 / 出货 / 客流 / 门店 / 资本开支（**需求侧指标**）
    "DEMAND_SURGE": [
        ("关联交易", "C-2020-MIL-EQUIP-ORDER：日常关联交易预计公告（订单层代理）"),
        ("预付款", "C-2020-MIL-EQUIP-ORDER：甲方大额预付"),
        ("预付", "C-2020-MIL-EQUIP-ORDER：大额预付"),
        ("合同负债", "C-2020-MIL-EQUIP-ORDER：合同负债（会计口径代理变量）"),
        ("出游", "C-2022-CONS-SERVICE-REBOUND：旅游出游人次"),
        ("人次", "C-2022-CONS-SERVICE-REBOUND：出游人次"),
        ("客流", "服务消费客流"),
        ("门店", "C-2023-CONS-VALUE-RETAIL：量贩零食门店扩张"),
        ("铺开", "C-2023-CONS-VALUE-RETAIL：门店快速铺开"),
        ("渠道", "C-2020-CONS-BEAUTY-CN：线上渠道红利"),
        ("GMV", "C-2020-CONS-BEAUTY-CN：抖音美妆 GMV"),
        ("月活", "C-2023-AI-COMPUTE-SEMI：ChatGPT 月活破亿"),
        ("用户", "需求侧用户规模"),
        ("资本开支", "C-2023-AI-COMPUTE-SEMI：海外算力资本开支上修"),
        # ★ v0.3-r2 裁决：保留「扩产」在 DEMAND_SURGE（方案 A）。依据：
        #   ① 研究自身表述：intake `R01-SEMICONDUCTOR-002` 标题即
        #      「半导体设备与材料国产替代（**晶圆厂扩产 → 「卡脖子」上游**）」→ 扩产 = 上游需求；
        #   ② v0.1 既有惯例：DEMAND_SURGE 已含「装机 / 并网 / 招标 / 采购」等同为
        #      **观察者相对的客户侧动作**（他人动作 → 本行业需求）；
        #   ③ 决定性证据：删除「扩产周期」后，本词使 `C-2020-SEMI-EQUIPMENT` 获得
        #      `DEMAND_SURGE`（与研究标题一致），且**无任何数据损失**；
        #   ④ 已知误命中：`C-2020-PANEL-CYCLE`「2018-2019 年过度扩产后的产能出清」中
        #      「扩产」为**时序前提**而非机制 → 该文本同时命中 POLICY+SUPPLY（2 命中）
        #      → 无论是否保留本词结果均为 `DERIVED/None`，**误命中零数据影响**（已如实记录）。
        ("扩产", "C-2020-SEMI-EQUIPMENT：晶圆厂扩产（客户侧产能投资 → 上游需求）"),
        ("固定资产投资", "C-2018-HIEQ-ROBOT-DOWN / C-2020-HIEQ-AUTOMATION：制造业固定资产投资"),
        ("基站", "C-2019-COMM-5G：5G 基站建设量"),
        ("持仓", "C-2020-MIL-EQUIP-ORDER：公募基金军工持仓（资金需求侧）"),
    ],
    # 产业升级 / 国产替代 / 结构迁移
    "INDUSTRY_UPGRADE": [
        ("自主可控", "C-2019-SEMI-LOCALIZATION：自主可控"),
        ("国产替代", "（已有）"),
        ("业态", "C-2023-CONS-VALUE-RETAIL：渠道业态扩张"),
        ("定价权", "C-2016-CONS-BAIJIU-UPGRADE：外资定价权提升"),
        ("纳入因子", "C-2019-CONS-BAIJIU-CORE：MSCI 提高 A 股纳入因子（制度性资金/结构变化）"),
        ("MSCI", "C-2016-CONS-BAIJIU-UPGRADE / C-2019-CONS-BAIJIU-CORE：MSCI 纳入"),
        ("确定性溢价", "C-2019-CONS-BAIJIU-CORE：确定性溢价叙事"),
    ],
    # 技术突破 —— 组网 / 入轨 / 首飞 / 大模型
    "TECH_BREAKTHROUGH": [
        ("组网", "RC-2024-MIL-COMMERCIAL-SPACE：低轨星座批量组网"),
        ("入轨", "RC-2024-MIL-COMMERCIAL-SPACE：卫星入轨"),
        ("首飞", "RC-2024-MIL-COMMERCIAL-SPACE：朱雀三号首飞"),
        ("可重复使用", "RC-2024-MIL-COMMERCIAL-SPACE：可重复使用火箭"),
        ("大模型", "C-2023-AI-COMPUTE-SEMI：大模型"),
        ("ChatGPT", "C-2023-AI-COMPUTE-SEMI：ChatGPT"),
        ("GPT", "C-2023-AI-COMPUTE-SEMI：GPT-4 / Copilot"),
        ("Copilot", "C-2023-AI-COMPUTE-SEMI：Copilot"),
    ],
    # 估值 / 资金配置 / 风格
    "VALUATION_RESET": [
        ("高股息", "C-2024-FIN-BANK-DIVIDEND：高股息配置"),
        ("红利", "C-2024-FIN-BANK-DIVIDEND：红利资产"),
        ("资产荒", "C-2024-FIN-BANK-DIVIDEND：资产荒"),
        ("低利率", "C-2024-FIN-BANK-DIVIDEND：低利率环境"),
        ("配置", "C-2024-FIN-BANK-DIVIDEND / C-2025-FIN-INSURANCE：资金配置"),
        ("增量资金", "C-2019-CONS-BAIJIU-CORE：外资增量资金"),
        ("外资", "C-2016-CONS-BAIJIU-UPGRADE：外资定价"),
        ("去美元化", "C-2024-RES-GOLD-CB：去美元化 / 货币体系重构"),
        ("央行购金", "C-2024-RES-GOLD-CB：全球央行购金"),
        ("黄金储备", "C-2024-RES-GOLD-CB：中国黄金储备连续上升"),
        ("ETF", "C-2024-RES-GOLD-CB：黄金 ETF 持仓扩张"),
        ("实际利率", "C-2020-RES-NONFERROUS / C-2024-RES-GOLD-CB：实际利率"),
        ("零利率", "C-2020-RES-NONFERROUS：美联储零利率"),
        ("宽松", "C-2020-RES-NONFERROUS：无限量宽松"),
        ("资产端", "C-2025-FIN-INSURANCE：保险资产端"),
        ("负债端", "C-2025-FIN-INSURANCE：保险负债端"),
    ],
    # 周期反转 / 更新替换 / 下行
    "CYCLE_REVERSAL": [
        ("更新周期", "C-2016-HIEQ-CONSTR：设备更新周期"),
        ("替换窗口", "C-2016-HIEQ-CONSTR：更新替换窗口"),
        ("更新替换", "C-2016-HIEQ-CONSTR：更新替换"),
        ("逆周期", "C-2021-CONS-HOG-REVERSAL：逆周期收储"),
        ("周期底部", "C-2020-RES-LITHIUM：锂价历史周期底部"),
        ("下行周期", "C-2022-SEMI-DOWNTURN：半导体下行周期"),
        ("增速放缓", "C-2018-HIEQ-ROBOT-DOWN：行业增速放缓"),
        ("增速转负", "C-2022-SEMI-DOWNTURN：增速转负"),
        ("负增长", "C-2018-HIEQ-ROBOT-DOWN：产量负增长"),
        ("进口同步收缩", "C-2018-HIEQ-ROBOT-DOWN：进口收缩"),
        ("收缩", "需求/进口收缩"),
        ("退坡", "补贴退坡"),
    ],
    # 事件催化 —— 事故 / 大会 / 官方发布
    "EVENT_CATALYST": [
        ("事故", "C-2019-RES-DYE-SHOCK：天嘉宜化工特别重大爆炸事故（离散事件）"),
        ("爆炸", "C-2019-RES-DYE-SHOCK：爆炸事故"),
        ("四中全会", "RC-2024-MIL-COMMERCIAL-SPACE：二十届四中全会"),
        ("十五五", "RC-2024-MIL-COMMERCIAL-SPACE：十五五建议"),
        ("成立", "集团/机构揭牌成立"),
        ("揭牌", "C-2019-MIL-GROUP-RESTRUCTURE：中国船舶集团揭牌"),
        # ★ v0.3-r1 修正：由 POLICY_DRIVEN 移入（原归属为语义错误）
        ("阅兵", "RC-2019-MIL-PARADE-70 / RC-2025-MIL-PARADE-80：阅兵（一次性重大纪念活动，"
                 "intake 原文即标注「重大纪念事件的注意力驱动」/「事件驱动型叙事」）"),
        ("纪念大会", "RC-2025-MIL-PARADE-80：抗战胜利 80 周年纪念大会（v0.1「大会」已覆盖，"
                     "显式列入以便审计）"),
    ],
}

# 合并：v0.1 原表 + 新增（新增词去重后追加，**不删除任何原词**）
RULES = {}
for _k, _v in RULES_V01.items():
    RULES[_k] = list(_v)
for _k, _pairs in ADDED_RULES.items():
    for _kw, _note in _pairs:
        if _kw not in RULES.setdefault(_k, []):
            RULES[_k].append(_kw)

ADDED_INDEX = {k: [kw for kw, _n in v] for k, v in ADDED_RULES.items()}
ADDED_NOTES = {k: {kw: n for kw, n in v} for k, v in ADDED_RULES.items()}

# ---------------------------------------------------------------- v0.3 修订记录（可审计）
REVISIONS = [
    {
        "revision": "v0.3-r1",
        "date": "2026-09-23",
        "change": ("「阅兵」「纪念大会」由 `POLICY_DRIVEN` **移至** `EVENT_CATALYST`"),
        "decision": "「阅兵」= 一次性重大纪念活动（**事件**），**不是**产业政策文本",
        "rationale": [
            "① 形式：阅兵有明确日期、一次性，属重大纪念活动，非规则/制度性文件",
            "② 机制：它不改变任何产业规则（无补贴 / 无准入 / 无配额 / 无采购规则变更）；"
            "intake 原文即标注「重大纪念事件的注意力驱动」「事件驱动型叙事」",
            "③ 词表内部一致性：v0.1 `EVENT_CATALYST` 已含「大会」「峰会」「论坛」「启动仪式」等"
            "同类型大型活动；将阅兵归 POLICY 与「大会」的既有归类自相矛盾",
            "④ 实际损害：跨 canonical 重复命中会使 `RC-2025-MIL-PARADE-80` 落入 `DERIVED`（无 canonical driver）"
            "→ **反而丢失机制**（该 cycle 修正前无任何 canonical driver）",
            "⑤ 禁止反向推理：不得为「让候选拿到 driver」而保留双重归属",
        ],
        "allowed_dual_semantics": False,
        "dual_semantics_rejected_because": [
            "canonical vocabulary 的 9 项是**互斥机制轴**"
            "（`POLICY_DRIVEN` = 规则/制度驱动 vs `EVENT_CATALYST` = 离散事件驱动）",
            "允许同一关键词跨 canonical 会**系统性制造 `DERIVED` / `AMBIGUOUS`**"
            "（v0.3 实测：8 条 `DIRECT→DERIVED`、1 条 `DERIVED→AMBIGUOUS` 均源于跨 canonical 重复）",
            "Rule Set §3.3「不得仅凭 driver 名称相同判定 MATCH」→ 同理不得让同一关键词同时充当两种机制",
        ],
        "unchanged": ["canonical vocabulary（9 项）", "v0.1 / v0.2 产物", "mapping_status 语义", "映射逻辑"],
    },
    {
        "revision": "v0.3-r2",
        "date": "2026-09-23",
        "change": "删除「扩产周期」；保留「扩产」在 `DEMAND_SURGE`",
        "scope": "仅此 2 词；**未处理**其余 5 项 substring collision（增长/负增长 · 整治/整治提升 · "
                 "出口/出口管制 · 采购/装备采购 · 储备/黄金储备）",
        "decision": {
            "扩产": "A —— 可作为 `DEMAND_SURGE` 的有效机制词（客户侧产能投资 → 上游需求）",
            "扩产周期": "D —— 从 canonical keyword mapping 中**删除**",
        },
        "evidence": {
            "hit_texts": 2,
            "扩产_hits": [
                "C-2020-SEMI-EQUIPMENT start#3「国内晶圆厂进入扩产周期」",
                "C-2020-PANEL-CYCLE start#2「2018-2019 年过度扩产后的产能出清，行业集中度提升」",
            ],
            "扩产周期_hits": [
                "C-2020-SEMI-EQUIPMENT start#3「国内晶圆厂进入扩产周期」—— **与「扩产」完全同一文本**",
            ],
        },
        "rationale": {
            "delete_扩产周期": [
                "① **零增量覆盖**：其唯一命中文本已被「扩产」完全覆盖 → 贡献 0 条独有覆盖",
                "② **方向错误**：被归入 `SUPPLY_CONTRACTION`，而「产能扩张」与「供给收缩」机制方向相反",
                "③ **实际损害**：它使该文本额外命中 `SUPPLY_CONTRACTION` → 把本应得到 "
                "`DEMAND_SURGE` 的文本推入 2-命中 `DERIVED`（canon=None）",
                "④ **无替代必要性**：`扩产` 已覆盖该语境；「周期」不携带机制",
            ],
            "keep_扩产_in_DEMAND_SURGE": [
                "① **研究自身表述**：intake `R01-SEMICONDUCTOR-002` 标题即"
                "「半导体设备与材料国产替代（**晶圆厂扩产 → 「卡脖子」上游**）」→ 扩产 = 上游需求",
                "② **v0.1 既有惯例**：`DEMAND_SURGE` 已含「装机 / 并网 / 招标 / 采购」等同为"
                "**观察者相对的客户侧动作**（他人动作 → 本行业需求）",
                "③ **决定性证据**：删除「扩产周期」后，本词使 `C-2020-SEMI-EQUIPMENT` 获得 "
                "`DEMAND_SURGE`（与研究标题一致），且**无任何数据损失**",
                "④ **误命中如实记录**：`C-2020-PANEL-CYCLE`「过度扩产后的产能出清」中「扩产」为"
                "**时序前提**而非机制 → 但该文本同时命中 POLICY+SUPPLY（2 命中）→ 无论保留与否结果均为 "
                "`DERIVED/None` → **零数据影响**",
            ],
            "not_chosen": {
                "扩产→B（其他 canonical）": "无任何 canonical 与「产能扩张」机制方向一致（`SUPPLY_CONTRACTION` 为反方向）",
                "扩产→C/D（删除）": "会使 `C-2020-SEMI-EQUIPMENT` 的 `DEMAND_SURGE` 永久不可见"
                                    "（与其研究标题矛盾），且该文本退化为 `UNKNOWN`（负面变化）",
            },
        },
        "min_impact": {
            "changed_entries": 1,
            "detail": "C-2020-SEMI-EQUIPMENT start#3：hits [DEMAND_SURGE, SUPPLY_CONTRACTION] → [DEMAND_SURGE]；"
                      "status DERIVED → DERIVED（**未变**）；canonical None → DEMAND_SURGE（**改善**）",
            "canonical_driver_changes": "C-2020-SEMI-EQUIPMENT: ['POLICY_DRIVEN'] → ['DEMAND_SURGE','POLICY_DRIVEN']",
            "primary_mechanism_changes": 0,
            "five_state_distribution_changes": "**无**（DIRECT 55 / DERIVED 454 / AMBIGUOUS 2 / UNKNOWN 86 / NOT_AVAILABLE 98 全部不变）",
            "cycles_with_driver": "77 / 79（不变）· campaign 52 / 52（不变）",
            "negative_changes": "**无**",
        },
        "unchanged": ["canonical vocabulary（9 项）", "v0.1 / v0.2 产物", "mapping_status 语义", "映射逻辑",
                      "Rule Set v0.3"],
    },
]

# ---------------------------------------------------------------- 跨 canonical 重复检测（**强制自检**）
# 同一关键词出现在 ≥2 个 canonical driver 中 → 会导致该文本永远无法成为 DIRECT，
# 并系统性制造 DERIVED / AMBIGUOUS。本检查**只报告**，不阻断（既有 v0.1 词表可能本就有重复）。
_KW_OWNER = collections.defaultdict(list)
for _c, _kws in RULES.items():
    for _kw in _kws:
        _KW_OWNER[_kw].append(_c)
CROSS_DUP = {kw: owners for kw, owners in sorted(_KW_OWNER.items()) if len(owners) > 1}
CROSS_DUP_V03 = {kw: owners for kw, owners in CROSS_DUP.items()
                 if kw in {k for v in ADDED_RULES.values() for k, _ in v}}
# 子串包含检测（宽关键词风险）：关键词 A 是关键词 B 的子串且属不同 canonical
# ★ 必须用**全序**排序（长度 + 字典序）—— 仅用 `key=len` 时等长元素顺序受 set 迭代顺序影响，
#   在 PYTHONHASHSEED 随机化下会产出不同顺序 → 破坏逐字节可复现性。
SUBSTR_CONFLICTS = []
_all_kw = sorted({kw for kws in RULES.values() for kw in kws}, key=lambda s: (len(s), s))
for _i, _a in enumerate(_all_kw):
    for _b in _all_kw[_i + 1:]:
        if _a != _b and _a in _b:
            _oa, _ob = set(_KW_OWNER[_a]), set(_KW_OWNER[_b])
            if _oa != _ob:
                SUBSTR_CONFLICTS.append({"shorter": _a, "longer": _b,
                                         "shorter_owner": sorted(_oa), "longer_owner": sorted(_ob)})

# 纯非机制表述（→ NOT_AVAILABLE）—— 与 v0.1 一致
NON_MECHANISM = ["unknown", "暂无", "未知", "无（", "获利盘", "暂定", "（暂定）"]

# ★ §十五：价格 / 行情**结果**描述 —— **不得**作为 driver（与 v0.1 完全一致）
PRICE_ACTION = [
    "涨停", "跌停", "连板", "20cm", "天地板", "断板", "涨", "跌", "走强", "活跃", "爆发",
    "大涨", "回调", "调整", "见顶", "见底", "回撤", "新高", "低点", "高点", "板块", "指数",
    "市值", "涨幅", "倍", "板",
]
DRIVING_BUCKETS = ("start", "accelerator")
TERMINAL_BUCKETS = ("turning", "ending")

REF_RE = re.compile(r"(EV-[A-Z0-9\-]+|E-[A-Z0-9\-]+|S-[A-Z0-9\-]+)")

# ---------------------------------------------------------------- 输入
exp = json.load(io.open(f"{ROOT}/exports/timeline_export_v1.json", encoding="utf-8"))
cur = json.load(io.open(f"{ROOT}/research/current/current_candidates.json", encoding="utf-8"))
EV = {e["event_id"]: e for e in (exp.get("events") or [])}
ALL_OBJ = exp["campaigns"] + exp["research_candidates"]


def oid(o):
    return o.get("campaign_id") or o.get("research_candidate_id")


def macro_theme(o):
    t = next((t for t in (o.get("themes") or [])
              if t.get("role") == "related" and t.get("theme_type") in ("industry", "sector")), None)
    return t["name"] if t else None


# ---------------------------------------------------------------- 逐文本映射（逻辑与 v0.1 逐行一致）
ledger = []
for o in ALL_OBJ:
    cid = oid(o)
    for bucket in ("start", "accelerator", "turning", "ending"):
        for idx, text in enumerate((o.get("drivers") or {}).get(bucket) or []):
            t = str(text)
            low = t.lower()
            hits = []
            for canon, kws in RULES.items():
                for kw in kws:
                    if kw in t or kw.lower() in low:
                        hits.append(canon)
                        break
            hits = [h for h in CANONICAL_DRIVERS if h in hits]
            refs = sorted(set(REF_RE.findall(t)))
            ev_src = []
            for e in [r for r in refs if r.startswith("EV-")]:
                ev = EV.get(e)
                if ev:
                    ev_src.append({"event_id": e, "date": ev.get("date"),
                                   "event_type": ev.get("event_type")})

            if not t.strip() or any(n in t for n in NON_MECHANISM):
                status, canon = "NOT_AVAILABLE", None
                reason = "文本为空或纯非机制表述（不含可编码的驱动机制）"
            elif (len(hits) == 0 and any(p in t for p in PRICE_ACTION)) \
                    or (len(hits) == 1 and hits[0] == "CYCLE_REVERSAL"
                        and any(p in t for p in PRICE_ACTION) and not refs):
                status, canon = "NOT_AVAILABLE", None
                reason = ("价格/行情**结果**描述（非机制）→ 按 §十五 不得作为 driver，"
                          "标记 NOT_AVAILABLE 而非 UNKNOWN")
            elif len(hits) == 0:
                status, canon = "UNKNOWN", None
                reason = "有文本但未命中任何显式规则 → 不强行归类"
            elif len(hits) == 1:
                canon = hits[0]
                if refs:
                    status = "DIRECT"
                    reason = f"命中唯一规则 {canon}，且文本可追溯至 {', '.join(refs)}"
                else:
                    status = "DERIVED"
                    reason = f"命中唯一规则 {canon}，但文本未给出 evidence/event/source 引用 → 降为 DERIVED"
            elif len(hits) >= 4:
                status, canon = "AMBIGUOUS", None
                reason = f"命中 {len(hits)} 条规则（{', '.join(hits)}）→ 无法收敛，保留 AMBIGUOUS，不硬拆"
            else:
                status, canon = "DERIVED", None
                reason = f"命中 {len(hits)} 条规则（{', '.join(hits)}）→ 需综合判断，标记 DERIVED"

            ledger.append({
                "cycle_id": cid, "macro_theme": macro_theme(o), "bucket": bucket, "seq": idx + 1,
                "raw_driver": t, "canonical_driver": canon, "mapping_status": status,
                "matched_rules": hits, "references": refs, "event_refs": ev_src,
                "source_type": "event_reference" if refs else "narrative_text",
                "reason": reason,
            })

# ---------------------------------------------------------------- 汇总
by_status = collections.Counter(x["mapping_status"] for x in ledger)
by_canon = collections.Counter(x["canonical_driver"] for x in ledger if x["canonical_driver"])

cycle_canon = collections.defaultdict(lambda: collections.defaultdict(set))
cycle_terminal = collections.defaultdict(lambda: collections.defaultdict(set))
for x in ledger:
    if x["mapping_status"] in ("DIRECT", "DERIVED") and x["canonical_driver"]:
        tgt = cycle_canon if x["bucket"] in DRIVING_BUCKETS else cycle_terminal
        tgt[x["cycle_id"]][x["canonical_driver"]].add(x["mapping_status"])

per_cycle = []
for o in ALL_OBJ:
    cid = oid(o)
    rows = [x for x in ledger if x["cycle_id"] == cid]
    st = collections.Counter(r["mapping_status"] for r in rows)
    cd = cycle_canon.get(cid, {})
    tm = cycle_terminal.get(cid, {})
    drv_rows = [r for r in rows if r["bucket"] in DRIVING_BUCKETS]
    drv_st = collections.Counter(r["mapping_status"] for r in drv_rows)
    per_cycle.append({
        "cycle_id": cid, "macro_theme": macro_theme(o),
        "raw_driver_count": len(rows), "driving_raw_count": len(drv_rows),
        "canonical_drivers": sorted(cd), "canonical_driver_count": len(cd),
        "terminal_mechanisms": sorted(tm), "terminal_mechanism_count": len(tm),
        "direct_count": st["DIRECT"], "derived_count": st["DERIVED"],
        "ambiguous_count": st["AMBIGUOUS"], "unknown_count": st["UNKNOWN"],
        "not_available_count": st["NOT_AVAILABLE"],
        "driving_direct_count": drv_st["DIRECT"], "driving_derived_count": drv_st["DERIVED"],
        "mapping_completeness": round((st["DIRECT"] + st["DERIVED"]) / len(rows), 4) if rows else 0.0,
        "driving_mapping_completeness": round(
            (drv_st["DIRECT"] + drv_st["DERIVED"]) / len(drv_rows), 4) if drv_rows else 0.0,
    })

driving_by_canon = collections.Counter(
    x["canonical_driver"] for x in ledger
    if x["canonical_driver"] and x["bucket"] in DRIVING_BUCKETS
    and x["mapping_status"] in ("DIRECT", "DERIVED"))

# ---------------------------------------------------------------- v0.2 → v0.3 diff（可审计）
V2C = json.load(io.open(f"{REP}/historical_driver_canonicalization_v0_2.json", encoding="utf-8"))
V2L = json.load(io.open(f"{REP}/historical_driver_evidence_ledger_v0_2.json",
                        encoding="utf-8"))["entries"]
k2 = {(e["cycle_id"], e["bucket"], e["seq"]): e for e in V2L}
changed = []
for e in ledger:
    a = k2.get((e["cycle_id"], e["bucket"], e["seq"]))
    if not a:
        continue
    if a["mapping_status"] != e["mapping_status"] or a["canonical_driver"] != e["canonical_driver"]:
        changed.append({
            "cycle_id": e["cycle_id"], "bucket": e["bucket"], "seq": e["seq"],
            "raw_driver": (e["raw_driver"] or "")[:160],
            "from": {"status": a["mapping_status"], "canonical_driver": a["canonical_driver"]},
            "to": {"status": e["mapping_status"], "canonical_driver": e["canonical_driver"]},
            "matched_rules": e["matched_rules"],
        })
CHG = collections.Counter("%s→%s" % (c["from"]["status"], c["to"]["status"]) for c in changed)

cycles_before = {c["cycle_id"] for c in V2C["per_cycle"] if c["canonical_drivers"]}
cycles_after = {c["cycle_id"] for c in per_cycle if c["canonical_drivers"]}
newly_covered = sorted(cycles_after - cycles_before)
still_missing = sorted({c["cycle_id"] for c in per_cycle} - cycles_after)

canon_doc = {
    "artifact": "historical_driver_canonicalization", "artifact_version": "0.3",
    "generated_by": "research/scripts/canonicalize_historical_drivers_v0_3.py",
    "position": ("Research-only 派生层 —— **不进入** DB / schema.sql / timeline_export_v1.json / "
                 "contracts / src。**不是**投资建议、预测或信号。"),
    "supersedes_note": ("v0.1 / v0.2 产物**逐字节保留**；本版**只扩展关键词覆盖**，"
                        "canonical vocabulary / mapping_status 语义 / 映射逻辑**完全不变**。"),
    "canonical_vocabulary": {
        "source": "research/current/schema.json → narrativeType（复用，**未新增**）",
        "values": CANONICAL_DRIVERS,
    },
    "rules": {
        "v0_1_base_keyword_count": sum(len(v) for v in RULES_V01.values()),
        "added_keyword_count": sum(len(v) for v in ADDED_RULES.values()),
        "total_keyword_count": sum(len(v) for v in RULES.values()),
        "added_rules": {k: [{"keyword": kw, "coverage_note": n} for kw, n in v]
                        for k, v in ADDED_RULES.items()},
        "added_index": ADDED_INDEX,
        "discipline": [
            "❌ 未新增 driver vocabulary",
            "❌ 未使用 event_type 反推 driver",
            "❌ 未使用价格 / 涨跌 / 相对收益结果反推 driver（PRICE_ACTION 排除逻辑保持有效）",
            "❌ 未删除 v0.1 任何原有关键词",
            "❌ 未修改 v0.1 / v0.2 产物",
        ],
    },
    "revisions": REVISIONS,
    "keyword_collision_audit": {
        "cross_canonical_duplicate_keywords_all": CROSS_DUP,
        "cross_canonical_duplicate_keywords_added_in_v0_3": CROSS_DUP_V03,
        "substring_conflicts_across_canonical": SUBSTR_CONFLICTS,
        "note": ("同一关键词归属 ≥2 个 canonical driver → 该文本**永远无法成为 DIRECT**，"
                 "且会系统性制造 `DERIVED` / `AMBIGUOUS`。"
                 "`cross_canonical_duplicate_keywords_added_in_v0_3` 为本轮新增词中的跨 canonical 重复（**应为空**）。"),
    },
    "summary": {
        "objects": len(ALL_OBJ),
        "historical_raw_driver_count": len(ledger),
        "historical_canonical_driver_count": len(by_canon),
        "driving_raw_count": sum(1 for x in ledger if x["bucket"] in DRIVING_BUCKETS),
        "driving_canonical_driver_count": len(driving_by_canon),
        "by_mapping_status": {k: by_status[k] for k in
                              ["DIRECT", "DERIVED", "AMBIGUOUS", "UNKNOWN", "NOT_AVAILABLE"]},
        "by_canonical_driver": dict(by_canon),
        "driving_by_canonical_driver": dict(driving_by_canon),
        "cycles_with_canonical_driver": len(cycles_after),
        "cycles_without_canonical_driver": len(still_missing),
        "cycles_newly_covered_vs_v0_2": len(newly_covered),
    },
    "v0_2_to_v0_3_diff": {
        "changed_entries": len(changed),
        "by_transition": dict(CHG),
        "newly_covered_cycles": newly_covered,
        "still_without_canonical_driver": still_missing,
        "detail": changed,
    },
    "per_cycle": per_cycle,
}

ledger_doc = {
    "artifact": "historical_driver_evidence_ledger", "artifact_version": "0.3",
    "generated_by": "research/scripts/canonicalize_historical_drivers_v0_3.py",
    "position": "Research-only —— 每条 mapping 一行，可追溯 raw_driver → canonical_driver → references。",
    "field_spec": ["cycle_id", "macro_theme", "bucket", "seq", "raw_driver", "canonical_driver",
                   "mapping_status", "matched_rules", "references", "event_refs", "source_type",
                   "reason"],
    "entries": ledger,
}

canon_body = json.dumps(canon_doc, ensure_ascii=False, indent=1) + "\n"
ledger_body = json.dumps(ledger_doc, ensure_ascii=False, indent=1) + "\n"
if CHECK:
    for p, b in ((OUT_CANON, canon_body), (OUT_LEDGER, ledger_body)):
        if not os.path.exists(p) or io.open(p, encoding="utf-8").read() != b:
            raise SystemExit("FAIL —— 产物与重算结果不一致: %s" % p)
    print("PASS —— 产物与重算结果逐字节一致（deterministic）。")
else:
    for p, b in ((OUT_CANON, canon_body), (OUT_LEDGER, ledger_body)):
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(b)
        print("written", p)

print()
print("objects:", len(ALL_OBJ), "| ledger entries:", len(ledger))
print("by_mapping_status:", dict(by_status))
print("canonical_drivers:", dict(by_canon))
print("cycles with canonical driver: %d → %d（v0.2 → v0.3）" % (len(cycles_before), len(cycles_after)))
print("newly covered:", newly_covered)
print("still without canonical driver:", still_missing)
print("v0.2→v0.3 changed entries:", len(changed), dict(CHG))
