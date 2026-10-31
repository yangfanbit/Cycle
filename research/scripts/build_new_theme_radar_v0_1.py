#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_new_theme_radar_v0_1.py —— 「自动发现的新题材线索」构建器（v0.66 起，v0.67 扩展）。

## 链路

```
公开事件 → 规范化事件（时间口径 / 证据）→ 题材·板块关联（显式词表）
        → 市场反应核验（事件后 3 个交易日，逐板块）→ 状态判定 → 版本化产物 → 产品
```

## v0.67 的三处口径修正（都属「不修就会算错」）

1. **时间口径**：列表页发布日期 ≠ 精确发布时间。只有日期时用**保守规则**——
   事件日是交易日 → 以**当日收盘**为基准、从**次一交易日**起观察 3 天；
   事件日非交易日 → 以**事件前最近交易日收盘**为基准、从事件后首个交易日起观察。
   **事件日当天的涨跌不计入事件后反应**（那可能发生在信息公开之前）。
2. **逐板块观察**：一条事件命中多个板块时，**每个板块独立保存**观察结果，
   不再只算第一个板块却把其余显示成「已核验」。
3. **增量追踪**：读上一版产物合并；`first_seen` 只在首次出现时写，
   新增 `last_seen` / `presence`（源站仍可见 vs 仅历史保留），**不因列表滚动而删除**。

## 硬边界

- 关联只来自 `THEME_KEYWORDS` **逐字短语**（每条带 rationale + DIRECT/PROXY），不做模糊匹配；
- 正文关键词只在**政策工具类**文档里才算关联（会见/会议/发布会中的背景性提及不算）；
- 行情缺失 / 交易日不足 → 写 `gaps`，**不插值、不补 0**；板块无历史成分 → 广度记 `null`；
- 输出是**线索**：不含打分 / 概率 / 收益排序 / 交易信号；`CANDIDATE` 只表示
  「事件后窗口内**相对基准**为正，值得人工复核」，**不表示**绝对收益为正或因果已证实。

## 用法

```
python research/scripts/build_new_theme_radar_v0_1.py --fetch --write --version 2
python research/scripts/build_new_theme_radar_v0_1.py --check     # 只读，不联网
```
"""
from __future__ import annotations

import argparse, hashlib, json, os, re, sqlite3, sys, time, urllib.request
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CURRENT = os.path.join(REPO, "research", "current")
OUT_RE = re.compile(r"new_theme_radar_v0_(\d+)\.json$")
SCAN_DB = os.path.join(REPO, "research", "database", "history_scan.db")
BENCH = "CSI300"

# ─────────────────────────── 事件源（两个栏目，同属发改委） ───────────────────────────
SOURCES = [
    {"id": "NDRC_ZCFB_TZ", "name": "国家发展改革委 · 政策通知", "publisher": "国家发展改革委",
     "list_url": "https://www.ndrc.gov.cn/xxgk/zcfb/tz/", "pages": ["", "index_1.html"],
     "category": "POLICY_NOTICE", "adapter": "NDRC", "date_source": "LIST_PAGE",
     "access_note": "公开 HTML 列表页（服务端渲染）；详情页正文在 div.article_con，附件 PDF/OFD 单列"},
    {"id": "NDRC_XWFB", "name": "国家发展改革委 · 新闻发布", "publisher": "国家发展改革委",
     "list_url": "https://www.ndrc.gov.cn/xwdt/xwfb/", "pages": ["", "index_1.html"],
     "category": "POLICY_NEWS", "adapter": "NDRC", "date_source": "LIST_PAGE",
     "access_note": "公开 HTML 列表页（服务端渲染）；详情页正文在 div.article_con"},
    # ★ v0.69 新增（经真实访问验证）：列表页服务端渲染 45 条/页、日期在 URL 路径
    #   `/art/YYYY/M/D/art_...html`，详情页正文在 `div#zoom`，且 `<meta name="PubDate">`
    #   带**到分钟**的发布时间 → 可用于「有可信发布时间」的时点判定。
    {"id": "NHSA_NOTICE", "name": "国家医疗保障局 · 通知公告", "publisher": "国家医疗保障局",
     "list_url": "https://www.nhsa.gov.cn/col/col109/index.html", "pages": [""],
     "category": "POLICY_NOTICE", "adapter": "NHSA", "date_source": "URL_PATH",
     "access_note": "公开 HTML 列表页（服务端渲染，无分页链接）；日期取自文章路径，"
                    "详情页正文在 div#zoom，PubDate meta 提供到分钟的发布时间"},
]
SRC_BY_ID = {x["id"]: x for x in SOURCES}

# ─────────────────── 显式关键词 → 板块（逐字匹配；ID 取自 history_scan.db） ───────────────────
# relation: DIRECT = 政策直接作用于该环节；PROXY = 首版用相近板块代理（必须说明原因）
THEME_KEYWORDS = [
    # 油气 / 电力（价格机制、市场规则、系统规划）
    ("成品油价格", "BK881180", "石油加工贸易", "DIRECT", "发改委成品油价格调控直接作用于炼化与成品油销售环节"),
    ("油价", "BK881180", "石油加工贸易", "DIRECT", "成品油/原油价格机制调整作用于炼化环节"),
    ("石油天然气", "BK881180", "石油加工贸易", "PROXY", "库内无油气开采板块，用「石油加工贸易」代理油气产业链中下游"),
    ("电价", "BK881145", "电力", "DIRECT", "电价机制与输配电价调整直接影响发电侧收入"),
    ("电力市场", "BK881145", "电力", "DIRECT", "电力市场规则变动影响发电与售电主体"),
    ("电力现货", "BK881145", "电力", "DIRECT", "现货交易规则影响发电侧的结算与收益"),
    ("输电权", "BK881145", "电力", "DIRECT", "输电权交易改变电网与发电侧的收益分配"),
    ("新型电力系统", "BK881145", "电力", "DIRECT", "电力系统建设规划直接作用于电源与电网运营"),
    ("新型能源体系", "BK881145", "电力", "DIRECT", "能源体系规划覆盖电源侧；设备端未单列，故不另绑风电/光伏"),
    # 新能源设备
    ("光伏", "BK881279", "光伏设备", "DIRECT", "光伏政策与装机目标直接作用于设备端"),
    ("风电", "BK881280", "风电设备", "DIRECT", "风电政策与装机目标直接作用于设备端"),
    ("储能", "BK881281", "电池", "PROXY", "储能支持政策主要作用于电池环节；首版用「电池」代理，非储能专营板块"),
    # 算力 / AI
    ("算力", "BK881162", "通信服务", "PROXY", "算力/数据中心政策主要作用于 IDC 与通信服务；首版用「通信服务」代理"),
    ("人工智能", "BK881162", "通信服务", "PROXY", "AI 行动计划主要作用于算力与数据基础设施；首版用「通信服务」代理，非 AI 专用板块"),
    # 半导体 / 汽车 / 农产品
    ("半导体", "BK881121", "半导体", "DIRECT", "集成电路政策直接作用于半导体板块"),
    ("集成电路", "BK881121", "半导体", "DIRECT", "集成电路政策直接作用于半导体板块"),
    ("新能源汽车", "BK881125", "汽车整车", "DIRECT", "新能源汽车政策直接作用于整车环节"),
    ("棉花目标价格", "BK881101", "种植业与林业", "PROXY", "棉花目标价格政策作用于种植端；库内无棉花专营板块，用种植业与林业代理"),
    # ── v0.69：与当前研究主题对应的序列（ID 全部取自 history_scan.db，覆盖到 2026-10-30）──
    ("医疗器械", "BK881144", "医疗器械", "DIRECT", "医疗器械监管/编码/价格政策直接作用于医疗器械板块"),
    ("医用耗材", "BK881144", "医疗器械", "DIRECT", "耗材分类与代码属医疗器械监管范围，直接作用于该板块"),
    ("脑机接口", "BK881144", "医疗器械", "PROXY",
     "库内无脑机接口专营序列；脑机接口器械归入医疗器械监管，故用「医疗器械」代理，非主题本身"),
    ("人形机器人", "CPT_zjqrgn", "机器人概念", "DIRECT", "人形机器人政策/项目直接作用于机器人概念篮子"),
    ("机器人", "CPT_zjqrgn", "机器人概念", "DIRECT", "机器人产业政策/标准直接作用于机器人概念篮子"),
    ("海上风电", "BK881280", "风电设备", "DIRECT", "海上风电项目/规划直接作用于风电设备板块"),
    ("光模块", "BK881129", "通信设备", "DIRECT", "光模块属通信设备行业，订单/技术迁移直接作用于该板块"),
    ("智能驾驶", "CPT_qcdz", "汽车电子", "PROXY",
     "库内无智驾专营序列；智驾产业链主要在汽车电子，故用「汽车电子」代理，非主题本身"),
]
KW_BY_NAME = {k[0]: k for k in THEME_KEYWORDS}

# ─────────────── 当前研究主题 ↔ 可核验序列（用于「与当前研究方向相关的事件」） ───────────────
# ★ 只写**已存在且覆盖可用**的序列；没有合适序列的主题不出现在这里（不强行代理）。
RESEARCH_DIRECTIONS = [
    {"direction": "具身智能与人形机器人", "series": ["CPT_zjqrgn"]},
    {"direction": "海上风电与风电设备", "series": ["BK881280", "CPT_fd"]},
    {"direction": "算电协同 / 算力与光互联", "series": ["BK881162", "BK881129"]},
    {"direction": "智能驾驶与汽车产业", "series": ["BK881125", "CPT_qcdz"]},
    {"direction": "医疗器械与脑机接口", "series": ["BK881144"]},
]
DIRECTION_BY_SERIES = {sid: d["direction"] for d in RESEARCH_DIRECTIONS for sid in d["series"]}

# ─────────────── 事件性质（区分常规重复 / 新催化 / 背景信息） ───────────────
# 只在**证据明确**时分类；判据全部可核（标题 + 文档类型），不做语义猜测。
NATURE_LEGEND = {
    "ROUTINE_RECURRING": "按既有机制周期性重复发布（如成品油价格按调价窗口调整）",
    "NEW_CATALYST": "新出现的政策 / 标准 / 规划 / 名单 / 项目等具体行动",
    "BACKGROUND": "会议、会见、发布会、宣传等背景性信息，无具体产业行动",
    "UNCLASSIFIED": "未满足上述明确判据",
}
ROUTINE_PATTERNS = (
    # (关键词, 说明) —— 成品油价格按 10 个工作日调价窗口重复发布
    ("成品油价格", "成品油价格按既有调价机制周期性发布（上调/下调/不作调整），属常规重复事件"),
)
# ★ 活动/评选类：标题出现这些词时，即使文档类型像政策工具（如「名单」），也只算背景信息
ACTIVITY_WORDS = ("大赛", "评选", "征集", "获奖", "入围", "观摩", "座谈", "恳谈", "宣传")


def nature_of(title, doc_type, links):
    """★ 事件性质：常规重复 / 新催化 / 背景 / 未分类。只在证据明确时给结论。"""
    for kw, note in ROUTINE_PATTERNS:
        if kw in (title or ""):
            return {"kind": "ROUTINE_RECURRING", "basis": "标题含「%s」" % kw, "note": note}
    for w in ACTIVITY_WORDS:
        if w in (title or ""):
            return {"kind": "BACKGROUND", "basis": "标题含活动类词「%s」" % w,
                    "note": "活动/评选/征集/宣传类信息，无具体产业行动 → 不作产业催化"}
    if doc_type == "POLICY_INSTRUMENT":
        return {"kind": "NEW_CATALYST",
                "basis": "文档类型 = POLICY_INSTRUMENT（通知/复函/规划/办法/名单/指导意见等）",
                "note": "属具体政策工具或行动计划，可作为新出现的产业催化候选"}
    if doc_type in ("MEETING", "CEREMONY", "PRESS"):
        return {"kind": "BACKGROUND",
                "basis": "文档类型 = %s" % doc_type,
                "note": "会议/仪式/发布会类，无具体产业行动，不作产业催化"}
    return {"kind": "UNCLASSIFIED", "basis": "未命中上述判据", "note": "不做推断"}


def directions_of(links):
    out = []
    for L in links or []:
        d = DIRECTION_BY_SERIES.get(L["board_series"])
        if d and d not in out:
            out.append(d)
    return out

# ─────────────────── 文档类型（决定「正文命中」是否足以建立关联） ───────────────────
DOC_TYPE_PATTERNS = [
    ("CEREMONY", ("升旗", "党课", "学习教育", "同上一堂课", "展览馆", "主题党日", "升国旗")),
    ("MEETING", ("会见", "座谈会", "圆桌会", "现场会", "推进会", "通报会", "协调会", "工作会",
                 "会议", "研讨会", "论坛", "专题会")),
    ("PRESS", ("新闻发布会", "答记者问", "署名文章", "专访", "发表讲话")),
    ("POLICY_INSTRUMENT", ("通知", "复函", "办法", "规划", "名单", "指导意见", "行动计划",
                           "行动方案", "目录", "清单", "规则", "政策",
                           # ★ v0.69：官方「发布/印发/公布《…》」也是政策工具（医保局常见表述）
                           "发布《", "印发《", "公布《", "发布")),
]
# ★★ v0.67：**只按标题建立关联** —— 政策标题即政策对象。
#   正文/附件里的提及一律只记入 `rejected_links`，不建关联：
#   实测「浦东/深圳/厦门综合改革试点」正文提到人工智能、「化肥保供稳价」正文提到天然气，
#   按正文匹配会造出两个假关联。会议/发布会/仪式中的背景性提及同理不建关联。
QUOTE_MATCH_DOC_TYPES = set()

# ─────────────────── 未关联事件的审查结论（逐条，可核） ───────────────────
# 键 = 标题里的稳定子串；值 = (verdict, note)
REVIEW_OVERRIDES = [
    ("化肥保供稳价", "NO_SERIES_AVAILABLE", "主题明确（化肥保供稳价），但库内没有化肥/农化板块序列 → 不强行映射到相似板块"),
    ("棉花目标价格", "MAPPED_AFTER_REVIEW", "本轮补「棉花目标价格」→ 种植业与林业（PROXY）"),
    ("零碳园区", "NO_SERIES_AVAILABLE", "园区级名单不是可交易板块；库内无「零碳园区/绿电园区」序列 → 保留缺口"),
    ("消费基础设施", "NO_SERIES_AVAILABLE", "消费基础设施横跨零售设施/冷链/充电桩，库内无对应综合序列 → 不强行映射"),
    ("新质生产力", "INCIDENTAL_MENTION", "答记者问，主题为综合概念；正文未给出可绑定单一板块的具体行动"),
    ("服务业扩能提质", "INCIDENTAL_MENTION", "发布会介绍服务业，未给出可绑定单一板块的具体政策工具"),
    ("六张网", "INCIDENTAL_MENTION", "重大工程协调机制，跨多个行业，无单一板块对应"),
    ("六网协同", "INCIDENTAL_MENTION", "同上：跨行业投融资机制，不建立单一板块关联"),
    ("109项重大工程", "INCIDENTAL_MENTION", "综合投资调度，无单一板块对应"),
    ("中欧班列", "INCIDENTAL_MENTION", "十周年成效回顾（发布会），非新增政策行动"),
    ("生态日", "IRRELEVANT", "宣传活动通知，无产业行动"),
    ("节能宣传周", "IRRELEVANT", "宣传活动通知，无产业行动"),
    ("社会信用体系", "IRRELEVANT", "信用体系示范区名单，与行业景气无直接关系"),
    ("公共信用信息基础目录", "IRRELEVANT", "信用信息目录，与行业景气无直接关系"),
    ("法治护航民营经济", "IRRELEVANT", "民营经济法治行动方案，无单一行业指向"),
    ("民营经济促进法", "IRRELEVANT", "典型案例通报，无单一行业指向"),
    ("综合改革试点", "IRRELEVANT", "区域改革经验推广，无单一行业指向"),
    ("投资项目在线审批", "IRRELEVANT", "政务系统数据共享，与行业景气无直接关系"),
    ("无线电频率占用费", "NO_SERIES_AVAILABLE", "收费标准影响分散在运营商/广电，库内无对应细分序列 → 不强行映射"),
    ("南水北调", "NO_SERIES_AVAILABLE", "供水价格核定作用于水利工程，库内无水利/水务板块序列"),
    ("西藏生态安全屏障", "NO_SERIES_AVAILABLE", "区域生态规划，库内无对应板块序列"),
    ("生态保护修复领域中央预算内投资", "NO_SERIES_AVAILABLE", "投资专项管理办法，库内无生态修复板块序列"),
    ("共同富裕示范区经验做法", "IRRELEVANT", "区域经验推广通知，无单一行业指向"),
    ("与埃及有关部门签署", "IRRELEVANT", "外事合作文件，无产业行动与板块指向"),
    ("计划执行报告", "INCIDENTAL_MENTION", "综合经济形势回顾，无单一行业指向"),
    ("信用数智创新发展", "IRRELEVANT", "信用信息化观摩会，与行业景气无直接关系"),
]


def doc_type_of(title):
    for name, kws in DOC_TYPE_PATTERNS:
        if any(k in title for k in kws):
            return name
    return "OTHER"


def review_of(title, status):
    """未关联事件给**可核**的审查结论；已关联的不需要。"""
    if status != "NO_THEME_LINK":
        return None
    for key, verdict, note in REVIEW_OVERRIDES:
        if key in title:
            return {"verdict": verdict, "note": note}
    dt = doc_type_of(title)
    if dt in ("MEETING", "CEREMONY"):
        return {"verdict": "IRRELEVANT",
                "note": "会议/仪式类，无具体产业行动（会见、座谈会、党建等不构成板块关联依据）"}
    if dt == "PRESS":
        return {"verdict": "INCIDENTAL_MENTION",
                "note": "发布会/答记者问，主题词多为背景性提及；无具体政策工具 → 不建关联"}
    return {"verdict": "REVIEWED_NO_KEYWORD",
            "note": "已逐条查看标题与原文，未命中显式关键词表；不按相似名称强行关联"}


# ─────────────────────────── 判定规则（v0.2，冻结在产物里） ───────────────────────────
RULES = {
    "reaction_trading_days": 3,
    "min_observation_trading_days": 3,
    "max_event_age_days": 45,
    "time_rule": ("DATE_ONLY_CONSERVATIVE：只有日期时，事件日为交易日 → 以当日收盘为基准、"
                  "从次一交易日起观察 3 个交易日；事件日非交易日 → 以事件前最近交易日收盘为基准、"
                  "从事件后首个交易日起观察。**事件日当天涨跌不计入事件后反应**"),
    "candidate_meaning": ("事件后窗口内**相对基准**（沪深300）表现为正，值得人工复核；"
                          "**不代表**板块绝对收益为正，**不代表**事件与行情存在因果关系"),
    "candidate_requires": [
        "有逐字关键词命中的板块关联（THEME_KEYWORDS）",
        "该板块行情可核验：observation_trading_days >= 3",
        "该板块相对基准超额 > 0",
        "event_date 距 as_of <= 45 天",
        "★ 多板块事件：要求**全部 DIRECT 板块**超额 > 0（不挑选表现好的板块）",
        "★ 任一必要 DIRECT 板块缺行情记录 / 不可核验 → INSUFFICIENT；观察期不足 → PENDING_MARKET",
    ],
    "quote_match_scope": "正文关键词只在政策工具类文档（通知/复函/规划/办法/名单/指导意见等）中建立关联",
    "not_scored": "不含打分 / 概率 / 收益排序 / 交易信号；状态只是机械筛选，需人工复核",
    "count_semantics": ("`CANDIDATE` 计数是**事件条数**，不是独立新题材数：同一政策/题材在不同日期"
                        "多次发布时，每次事件分别计数；无可靠主题唯一标识 → 不输出「题材数」"),
    "nature_rule": ("事件性质只在**证据明确**时给结论：标题含「成品油价格」→ 常规重复（按既有调价机制）；"
                    "文档类型为政策工具（通知/复函/规划/办法/名单/指导意见等）→ 新催化；"
                    "会议/仪式/发布会 → 背景信息；其余 → 未分类。性质**不影响**状态判定。"),
    "research_direction_rule": ("研究方向对应关系写死在 `RESEARCH_DIRECTIONS`（序列 → 方向），"
                                "只写**已存在且覆盖可用**的序列；没有合适序列的主题不出现，不强行代理"),
}

STATUS_LEGEND = {
    "CANDIDATE": "事件后窗口内**相对基准**为正（值得人工复核；不证明绝对上涨或因果）",
    "WATCH": "有板块关联，但相对表现不支持 / 事件已过窗口 → 只留档",
    "PENDING_MARKET": "事件后交易日不足 3 个，暂不判定",
    "INSUFFICIENT": "行情或关联不足，无法核验",
    "NO_THEME_LINK": "未命中显式关键词表 → 不建立板块关联",
}

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ThreeC-research/0.2"}


# ─────────────────────────── 通用工具 ───────────────────────────
def iso(d):
    if not d:
        return None
    d = str(d)[:10]
    return "%s-%s-%s" % (d[:4], d[4:6], d[6:8]) if "-" not in d else d


def _get(url, retries=2):
    last = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            last = e
            time.sleep(1.0 + i)
    print("  WARN 取数失败 %s（%s）" % (url, type(last).__name__), file=sys.stderr)
    return None


def _clean(s):
    s = re.sub(r"<script.*?</script>", " ", s or "", flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
          .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'"))
    return re.sub(r"\s+", " ", s).strip()


def _block_inner(html, open_re):
    """★ 深度感知地取某个 div 的内部 HTML（正则 `.*?</div>` 会在第一个嵌套 </div> 截断）。"""
    m = re.search(open_re, html)
    if not m:
        return None
    i, depth = m.end(), 1
    for tok in re.finditer(r"<div\b|</div>", html[i:]):
        depth += 1 if tok.group(0) != "</div>" else -1
        if depth == 0:
            return html[i:i + tok.start()]
    return html[i:]


def _div_inner(html, cls_kw):
    """按 class 关键字取 div 内部 HTML（NDRC 用）。"""
    return _block_inner(html, r'<div[^>]*class="[^"]*%s[^"]*"[^>]*>' % cls_kw)


# ─────────────────────────── 抓取 ───────────────────────────
def _parse_list_ndrc(html, src):
    out = []
    for block in re.findall(r"<li[^>]*>(.*?)</li>", html, re.S):
        a = re.search(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]*)"', block, re.S)
        d = re.search(r"<span[^>]*>\s*(\d{4})[/-](\d{1,2})[/-](\d{1,2})\s*</span>", block)
        if not (a and d):
            continue
        href = a.group(1)
        full = href if href.startswith("http") else src["list_url"] + href.lstrip("./")
        out.append({"title": _clean(a.group(2)), "url": full,
                    "date": "%s-%02d-%02d" % (d.group(1), int(d.group(2)), int(d.group(3))),
                    "date_source": "LIST_PAGE", "source_id": src["id"]})
    return out


def _parse_list_nhsa(html, src):
    """★ 医保局列表页**不在锚点里给日期** → 日期取自文章路径 `/art/YYYY/M/D/art_*.html`。
    这是可核验的（点开 URL 即可看到路径日期），因此记 `date_source = URL_PATH`。"""
    out, seen = [], set()
    for href, title in re.findall(r'<a[^>]+href="(/art/[^"]+)"[^>]*title="([^"]+)"', html):
        m = re.search(r"/art/(\d{4})/(\d{1,2})/(\d{1,2})/", href)
        if not m or href in seen:
            continue
        seen.add(href)
        out.append({"title": _clean(title), "url": "https://www.nhsa.gov.cn" + href,
                    "date": "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))),
                    "date_source": "URL_PATH", "source_id": src["id"]})
    return out


PARSE_LIST = {"NDRC": _parse_list_ndrc, "NHSA": _parse_list_nhsa}


def fetch_list():
    """返回 (items, pages, failures)。pages 记录每页实际条目数；失败页**显式**进 failures。"""
    items, pages, failures = [], [], []
    for src in SOURCES:
        for p in src["pages"]:
            url = src["list_url"] + p
            h = _get(url)
            if not h:
                failures.append({"source": src["id"], "url": url, "reason": "HTTP/网络失败"})
                continue
            got = PARSE_LIST[src["adapter"]](h, src)
            if not got:
                failures.append({"source": src["id"], "url": url,
                                 "reason": "页面结构变化或该页无条目"})
            pages.append({"source": src["id"], "url": url, "bytes": len(h), "items": len(got)})
            items.extend(got)
            time.sleep(1.2)
    seen, uniq = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    return uniq, pages, failures


def _article_ndrc(h):
    body = _div_inner(h, "article_con") or _div_inner(h, "TRS_Editor") or ""
    text = _clean(body)
    pub = re.search(r"发布时间[:：]\s*(\d{4})[/-](\d{1,2})[/-](\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?", h)
    published = None
    if pub:
        published = {"date": "%s-%02d-%02d" % (pub.group(1), int(pub.group(2)), int(pub.group(3))),
                     "time": ("%s:%s" % (pub.group(4), pub.group(5))) if pub.group(4) else None,
                     "precision": "MINUTE" if pub.group(4) else "DATE"}
    att = []
    ab = _div_inner(h, "attachment_r") or ""
    for href, name in re.findall(r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>', ab):
        full = href if href.startswith("http") else "https://www.ndrc.gov.cn" + href.lstrip("./")
        att.append({"name": _clean(name), "url": full})
    return text, published, att


def _article_nhsa(h):
    body = _block_inner(h, r'<div[^>]*id="zoom"[^>]*>') or ""
    text = _clean(body)
    published = None
    m = re.search(r'<meta[^>]*name=["\']PubDate["\'][^>]*content=["\']'
                  r'(\d{4})-(\d{1,2})-(\d{1,2})(?:[ T](\d{1,2}):(\d{2}))?', h)
    if m:
        published = {"date": "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3))),
                     "time": ("%s:%s" % (m.group(4), m.group(5))) if m.group(4) else None,
                     "precision": "MINUTE" if m.group(4) else "DATE"}
    return text, published, []


ARTICLE = {"NDRC": _article_ndrc, "NHSA": _article_nhsa}


def fetch_article(url, adapter):
    """取正文 / 附件 / 发布时间。正文取不到就如实标 ATTACHMENT_ONLY 或 NONE。"""
    h = _get(url)
    if not h:
        return {"kind": "NONE", "quote": None, "quote_sha256_16": None,
                "attachments": [], "published": None, "note": "详情页取数失败"}
    text, published, att = ARTICLE[adapter](h)
    if len(text) >= 40:
        # ★★ 哈希必须算**落盘的那一段**（先截断再哈希）
        quote = text[:400]
        return {"kind": "BODY_TEXT", "quote": quote,
                "quote_sha256_16": hashlib.sha256(quote.encode("utf-8")).hexdigest()[:16],
                "attachments": att, "published": published, "note": None}
    if att:
        return {"kind": "ATTACHMENT_ONLY", "quote": None, "quote_sha256_16": None,
                "attachments": att, "published": published,
                "note": "正文在附件（PDF/OFD）内，未解析附件内容 → 只有标题与附件链接可核"}
    return {"kind": "NONE", "quote": None, "quote_sha256_16": None, "attachments": [],
            "published": published, "note": "详情页无正文容器，也无附件"}


# ─────────────────────────── 关联 / 时间 / 行情 ───────────────────────────
def theme_links(title, evidence):
    """逐字匹配 + 文档类型门槛。返回 (links, rejected) —— 被门槛挡掉的也要留痕。"""
    quote = evidence.get("quote") or ""
    dt = doc_type_of(title)
    links, rejected, seen = [], [], set()
    for kw, sid, sname, rel, why in THEME_KEYWORDS:
        in_title, in_quote = kw in (title or ""), kw in quote
        if not (in_title or in_quote):
            continue
        if in_quote and not in_title and dt not in QUOTE_MATCH_DOC_TYPES:
            rejected.append({"keyword": kw, "board_series": sid, "doc_type": dt,
                             "reason": "关键词只出现在正文，且文档类型 %s 不属政策工具 → 不建立关联" % dt})
            continue
        if (sid, kw) in seen:
            continue
        seen.add((sid, kw))
        links.append({"keyword": kw, "matched_in": "TITLE" if in_title else "QUOTE",
                      "board_series": sid, "board_name": sname,
                      "relation": rel, "rationale": why})
    return links, rejected


def _cal(con):
    return sorted({(r[0] if "-" in r[0] else "%s-%s-%s" % (r[0][:4], r[0][4:6], r[0][6:]))
                   for r in con.execute("SELECT trade_date FROM scan_daily WHERE series_id=?", (BENCH,))})


def time_basis_of(event_date, cal, published=None):
    """★★ 可用时点判定。

    有**到分钟**的可信发布时间时，只在**无歧义**的情形下用它：
    - 发布时间 ≥ 15:00（收盘后）→ 基准 = 事件日收盘（事件日为交易日时），观察次日；
    - 发布时间 < 09:30（开盘前）→ 基准 = 事件前最近交易日收盘，**从事件日**起观察；
    - 盘中发布（09:30–15:00）→ 无法判断信息公开时点与收盘的先后 → 退回保守规则。
    只有日期时，一律用保守规则（事件日涨跌**不计入**事件后反应）。
    """
    if not cal:
        return {"rule": "NO_CALENDAR", "basis_day": None, "observe_from": None,
                "note": "无交易日历，无法确定可用基准"}
    is_trading = event_date in cal
    t = (published or {}).get("time")
    precise = bool(t) and (published or {}).get("precision") == "MINUTE"
    if precise:
        try:
            hh, mm = [int(x) for x in t.split(":")[:2]]
        except Exception:
            hh = mm = -1
        if (hh, mm) >= (15, 0):
            if is_trading:
                i = cal.index(event_date)
                return {"rule": "PUBLISHED_AFTER_CLOSE", "basis_day": event_date,
                        "observe_from": cal[i + 1] if i + 1 < len(cal) else None,
                        "note": "发布时间 %s（收盘后）→ 以事件日收盘为基准，从次一交易日起观察" % t}
        elif (0, 0) <= (hh, mm) < (9, 30):
            prior = [d for d in cal if d < event_date]
            if prior:
                start = event_date if is_trading else next((d for d in cal if d > event_date), None)
                return {"rule": "PUBLISHED_BEFORE_OPEN", "basis_day": prior[-1],
                        "observe_from": start,
                        "note": "发布时间 %s（开盘前）→ 以事件前最近交易日收盘为基准，从事件日起观察" % t}
    if is_trading:
        i = cal.index(event_date)
        return {"rule": "DATE_ONLY_CONSERVATIVE_TRADING_DAY", "basis_day": event_date,
                "observe_from": cal[i + 1] if i + 1 < len(cal) else None,
                "note": ("事件日为交易日：以**当日收盘**为基准，从**次一交易日**起观察 —— "
                         "事件日当天的涨跌可能发生在信息公开之前，不计入事件后反应")}
    prior = [d for d in cal if d < event_date]
    after = [d for d in cal if d > event_date]
    return {"rule": "DATE_ONLY_CONSERVATIVE_NON_TRADING_DAY",
            "basis_day": (prior[-1] if prior else None),
            "observe_from": (after[0] if after else None),
            "note": "事件日非交易日：以事件前最近交易日收盘为基准，从事件后首个交易日起观察"}


def market_of(con, cal, sid, basis_day, observe_from, as_of):
    """★ 逐板块：事件后 3 个交易日收盘的绝对收益 / 基准收益 / 相对超额 + 长期 drift。"""
    res = {"board_series": sid, "as_of": as_of, "window": None,
           "board_ret_pct": None, "bench_ret_pct": None, "excess_pp": None,
           "observation_trading_days": 0, "breadth": None, "drift": None,
           "status": "INSUFFICIENT", "gaps": []}
    if not (basis_day and observe_from) or not cal:
        res["gaps"].append("无法确定可用基准日（事件日不在日历内或日历缺失）")
        return res
    n = RULES["reaction_trading_days"]
    i0 = cal.index(observe_from)
    last = min(as_of, cal[-1])
    if cal[i0] > last:
        res["gaps"].append("as_of 早于事件后首个交易日")
        return res
    i1 = min(i0 + n - 1, cal.index(last))
    end_day = cal[i1]
    obs = i1 - i0 + 1
    res.update({"window": [basis_day, end_day], "observation_trading_days": obs})

    def close(series, day):
        # ★★ `industry_board` 存紧凑日期、index 存 dashed → 归一化后再比
        r = con.execute("SELECT close FROM scan_daily WHERE series_id=? AND REPLACE(trade_date,'-','')=?",
                        (series, day.replace("-", ""))).fetchone()
        return r[0] if r and r[0] else None

    b0, b1 = close(sid, basis_day), close(sid, end_day)
    m0, m1 = close(BENCH, basis_day), close(BENCH, end_day)
    if None in (b0, b1, m0, m1):
        res["gaps"].append("板块或基准在窗口内缺收盘价 → 不计算收益（不插值）")
        return res
    br, mr = (b1 / b0 - 1) * 100, (m1 / m0 - 1) * 100
    res.update({"board_ret_pct": round(br, 2), "bench_ret_pct": round(mr, 2),
                "excess_pp": round(br - mr, 2), "status": "OBSERVED"})
    # 长期漂移：**同一个基准日**，终点 as_of；只作背景，不参与判定
    d1, m_last = close(sid, last), close(BENCH, last)
    if None not in (d1, m_last):
        dbr, dmr = (d1 / b0 - 1) * 100, (m_last / m0 - 1) * 100
        res["drift"] = {"window": [basis_day, last], "board_ret_pct": round(dbr, 2),
                        "bench_ret_pct": round(dmr, 2), "excess_pp": round(dbr - dmr, 2),
                        "note": "事件至今的整体漂移（同一基准日），**不参与**候选判定"}
    res["gaps"].append("行业板块无历史成分 → 参与广度无法计算（不以当前成分替代）")
    return res


def classify(event, as_of):
    """状态机。

    ★★ v0.68：候选判定的**必要条件 = 全部 DIRECT 关联板块**。
    原实现先筛 `OBSERVED` 再看超额 → 某个 DIRECT 板块行情缺失时会被忽略，
    另一个板块正超额就能升级（等于挑表现好的板块）。现在按必要性逐个检查：

    - 任一必要 DIRECT 板块**没有独立行情记录** → `INSUFFICIENT`；
    - 任一必要板块**行情不可核验**（缺收盘价 / 无序列）→ `INSUFFICIENT`；
    - 任一必要板块**观察期不足** → `PENDING_MARKET`（不因另一板块已成熟而升级）；
    - 任一必要板块**超额 ≤ 0** → `WATCH`；
    - 全部必要板块满足 → `CANDIDATE`（仅表示**相对**基准为正）。
    """
    links = event["theme_links"]
    if not links:
        return "NO_THEME_LINK", ["事件标题与原文均未命中显式关键词表 → 不建立板块关联（不猜）"]
    ms = event.get("markets") or []
    by_sid = {}
    for m in ms:
        by_sid.setdefault(m["board_series"], m)
    need = list(dict.fromkeys(L["board_series"] for L in links
                              if (L.get("relation") or "DIRECT") == "DIRECT"))
    if not need:      # 只有 PROXY 关联时，退化为「全部关联板块」
        need = list(dict.fromkeys(L["board_series"] for L in links))
    missing = [s for s in need if s not in by_sid]
    if missing:
        return "INSUFFICIENT", ["必要 DIRECT 板块缺少独立行情记录（%s）→ 不升级："
                                "不能只凭其他板块的正超额判定" % "、".join(missing)]
    need_ms = [by_sid[s] for s in need]
    bad = [m for m in need_ms if m["status"] != "OBSERVED"]
    if bad:
        first = bad[0]
        return "INSUFFICIENT", ["必要 DIRECT 板块行情不可核验：%s（%s）→ 不升级"
                                % (first.get("board_name") or first["board_series"],
                                   (first.get("gaps") or ["原因未记录"])[0])]
    min_obs = min(m["observation_trading_days"] for m in need_ms)
    if min_obs < RULES["min_observation_trading_days"]:
        short = min(need_ms, key=lambda m: m["observation_trading_days"])
        return "PENDING_MARKET", ["必要 DIRECT 板块中最小观察期仅 %d 个交易日（< %d，%s）"
                                  "→ 观察窗口不足，暂不判定"
                                  % (min_obs, RULES["min_observation_trading_days"],
                                     short.get("board_name") or short["board_series"])]
    age = (date.fromisoformat(as_of) - date.fromisoformat(event["event_date"])).days
    if age > RULES["max_event_age_days"]:
        return "WATCH", ["事件已过去 %d 天（> %d）→ 不再作为「新」线索，仅留档"
                         % (age, RULES["max_event_age_days"])]
    nonpos = [m for m in need_ms if (m["excess_pp"] or 0) <= 0]
    if nonpos:
        return "WATCH", ["必要 DIRECT 板块 %s 相对基准超额 %+.2fpp ≤ 0 → 相对表现不支持，不升级"
                         % (nonpos[0].get("board_name") or nonpos[0]["board_series"],
                            nonpos[0]["excess_pp"] or 0)]
    return "CANDIDATE", []


def assessment_of_market(m):
    """★ v0.68：**逐板块**的绝对 vs 相对说明。

    多板块事件不得只按第一条已观察板块给一个整体结论 —— 那会与其它板块矛盾。
    每条市场观察各自带 `assessment`，前端逐条展示，可分别核对。
    """
    rel_pos = (m["excess_pp"] or 0) > 0
    abs_pos = (m["board_ret_pct"] or 0) > 0
    if rel_pos and not abs_pos:
        note = ("本板块绝对收益为负（%+.2f%%）；正超额只说明**相对**沪深300更强，"
                "**不证明**事件产生了正向因果效果" % (m["board_ret_pct"] or 0))
    elif rel_pos and abs_pos:
        note = ("本板块绝对收益与相对超额同为正（%+.2f%% / %+.2fpp）；仍只表示事后同向，"
                "**不证明**因果关系" % (m["board_ret_pct"] or 0, m["excess_pp"] or 0))
    else:
        note = "本板块相对超额 %+.2fpp 非正；不构成候选" % (m["excess_pp"] or 0)
    return {"relative_positive": rel_pos, "absolute_positive": abs_pos, "note": note}


def attach_assessments(markets):
    for m in markets or []:
        m["assessment"] = assessment_of_market(m) if m.get("status") == "OBSERVED" else None
    return markets


# ─────────────────────────── 事件装配 ───────────────────────────
def event_id_of(url, source_id):
    m = re.search(r"t(\d{8})_(\d+)[._]html", url)
    if m:
        return "EVT-%s-%s-%s" % (source_id.replace("NDRC_", ""), m.group(1), m.group(2))
    return "EVT-%s-%s" % (source_id.replace("NDRC_", ""),
                          hashlib.sha1(url.encode()).hexdigest()[:12])


def norm_url(u):
    return re.sub(r"[?#].*$", "", u or "").rstrip("/")


def build(fetch=False, prev=None):
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    items, pages, failures = (fetch_list() if fetch else ([], [], []))
    if fetch and not items:
        raise SystemExit("FAIL: 列表页未取到任何条目（检查网络 / 页面结构是否变化）")

    con = sqlite3.connect("file:%s?mode=ro" % SCAN_DB, uri=True) if os.path.exists(SCAN_DB) else None
    cal = _cal(con) if con else []
    as_of = cal[-1] if cal else None

    prev_by_id = {e["event_id"]: e for e in ((prev or {}).get("events") or [])}
    prev_by_url = {norm_url(e["source"]["url"]): e for e in ((prev or {}).get("events") or [])}

    events, carried = [], 0
    for it in items:
        src = SRC_BY_ID[it["source_id"]]
        ev = fetch_article(it["url"], src["adapter"]) if fetch else {
            "kind": "NONE", "quote": None, "quote_sha256_16": None,
            "attachments": [], "published": None, "note": "未抓取"}
        if fetch:
            time.sleep(1.0)
        eid = event_id_of(it["url"], it["source_id"])
        links, rejected = theme_links(it["title"], ev)
        tb = time_basis_of(it["date"], cal, ev.get("published"))
        markets = []
        if con and links:
            done = set()
            for L in links:
                if L["board_series"] in done:      # ★ 同一板块多个关键词命中 → 只算一次
                    continue
                done.add(L["board_series"])
                m = market_of(con, cal, L["board_series"], tb["basis_day"],
                              tb["observe_from"], as_of)
                m["board_name"], m["relation"] = L["board_name"], L["relation"]
                markets.append(m)
        old = prev_by_id.get(eid) or prev_by_url.get(norm_url(it["url"]))
        if old:
            carried += 1
        evt = {
            "event_id": eid,
            "title": it["title"],
            "event_date": it["date"],
            "doc_type": doc_type_of(it["title"]),
            "first_seen": (old or {}).get("first_seen") or now,
            "last_seen": now,
            "seen_count": ((old or {}).get("seen_count") if (old or {}).get("seen_count") is not None
                           else (1 if old else 0)) + 1,
            "presence": "IN_LATEST_LIST",
            "source": {"id": src["id"], "name": src["name"], "publisher": src["publisher"],
                       "url": it["url"], "list_url": src["list_url"],
                       "category": src["category"], "access": "PUBLIC_HTML"},
            "time": {
                "event_date": it["date"],
                "event_date_source": it.get("date_source") or src.get("date_source") or "LIST_PAGE",
                "published_date": (ev.get("published") or {}).get("date"),
                "published_time": (ev.get("published") or {}).get("time"),
                "time_precision": "MINUTE" if (ev.get("published") or {}).get("time") else "DATE_ONLY",
                "reaction_basis": tb["rule"], "basis_day": tb["basis_day"],
                "observe_from": tb["observe_from"], "note": tb["note"],
            },
            "evidence": ev,
            "theme_links": links,
            "rejected_links": rejected,
            "markets": markets,
            "security_mapping": {"status": "NOT_MAPPED",
                                 "reason": "首版只到行业板块级；个股映射需按名称+代码另行核验"},
            # ★ v0.69：事件性质（常规重复 / 新催化 / 背景 / 未分类）+ 与当前研究方向的对应
            "nature": nature_of(it["title"], doc_type_of(it["title"]), links),
            "research_directions": directions_of(links),
        }
        evt["status"], evt["gaps"] = classify(evt, as_of) if as_of else ("INSUFFICIENT", ["无行情基准日"])
        extra = [g for m in markets for g in (m.get("gaps") or []) if g not in evt["gaps"]]
        evt["gaps"] = evt["gaps"] + extra
        # ★ v0.68：绝对/相对说明挂在**每个板块**上，不再给事件一个整体结论
        attach_assessments(evt["markets"])
        evt["review"] = review_of(it["title"], evt["status"])
        events.append(evt)

    # ★ 增量：上一版里本次列表没再出现的事件 → **保留**，标 HISTORICAL_ONLY，
    #   并用**当前 as_of** 重算观察状态（历史记录保留，但状态必须跟着行情基准更新）
    seen_ids = {e["event_id"] for e in events}
    for old in prev_by_id.values():
        if old["event_id"] in seen_ids:
            continue
        keep = json.loads(json.dumps(old))
        keep["presence"] = "HISTORICAL_ONLY"
        keep["last_seen"] = old.get("last_seen") or old.get("first_seen")
        keep["gaps"] = list(keep.get("gaps") or []) + [
            "本次列表页未再出现（可能已翻页下沉）→ 历史记录保留，不视为删除"]
        tb, links = keep.get("time") or {}, keep.get("theme_links") or []
        if con and as_of and links and tb.get("basis_day"):
            ms, done = [], set()
            for L in links:
                if L["board_series"] in done:
                    continue
                done.add(L["board_series"])
                m = market_of(con, cal, L["board_series"], tb.get("basis_day"),
                              tb.get("observe_from"), as_of)
                m["board_name"], m["relation"] = L["board_name"], L["relation"]
                ms.append(m)
            keep["markets"] = attach_assessments(ms)
            keep["status"], base_gaps = classify(keep, as_of)
            keep["gaps"] = base_gaps + keep["gaps"]
            keep.pop("assessment", None)     # 事件级整体说明已废弃（逐板块代替）
        events.append(keep)
    if con:
        con.close()

    seen, uniq = set(), []
    for e in sorted(events, key=lambda x: (x["event_date"], x["event_id"]), reverse=True):
        k = (e["event_date"], re.sub(r"\s+", "", e["title"]))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(e)

    by_status = {}
    for e in uniq:
        by_status[e["status"]] = by_status.get(e["status"], 0) + 1
    dates = [e["event_date"] for e in uniq]
    review_counts = {}
    for e in uniq:
        v = (e.get("review") or {}).get("verdict")
        if v:
            review_counts[v] = review_counts.get(v, 0) + 1
    # ★ 常规重复事件：给出「同一机制重复出现几次」的计数（**不合并、不删除**任何事件）
    routine_groups = {}
    for e in uniq:
        n = e.get("nature") or {}
        if n.get("kind") != "ROUTINE_RECURRING":
            continue
        for kw, _ in ROUTINE_PATTERNS:
            if kw in (e.get("title") or ""):
                routine_groups.setdefault(kw, []).append(e)
                n["repeat_group"] = kw
                break
    for kw, evs in routine_groups.items():
        for e in evs:
            e["nature"]["repeat_count"] = len(evs)
            e["nature"]["repeat_note"] = ("同一机制（%s）在本产物中重复出现 %d 次；"
                                          "每次事件**分别计数**，不合并、不删除" % (kw, len(evs)))
    by_nature = {}
    for e in uniq:
        k = (e.get("nature") or {}).get("kind")
        if k:
            by_nature[k] = by_nature.get(k, 0) + 1
    by_direction = {}
    for e in uniq:
        for d in (e.get("research_directions") or []):
            by_direction[d] = by_direction.get(d, 0) + 1
    prev_name = None
    if prev:
        # artifact_version "0.1" → 文件名 new_theme_radar_v0_1.json（不是 v0_0_1）
        ver = str(prev.get("artifact_version") or "0.1")
        prev_name = "new_theme_radar_v0_%s.json" % ver.split(".")[-1]

    return {
        "artifact": "new_theme_radar", "artifact_version": "0.4",
        "generated_at": now, "as_of": as_of,
        "source_kind": "AUTO_DISCOVERED_EVENT",
        "supersedes": prev_name,
        "coverage": {
            "publishers": sorted({x["publisher"] for x in SOURCES}),
            "sources": [{"id": x["id"], "name": x["name"], "publisher": x["publisher"],
                         "list_url": x["list_url"], "category": x["category"],
                         "pages": x["pages"], "adapter": x["adapter"],
                         "date_source": x["date_source"], "access_note": x["access_note"]}
                        for x in SOURCES],
            "pages_fetched": pages, "failures": failures,
            "date_range": [min(dates), max(dates)] if dates else None,
            "events": len(uniq),
            # ★ 历史保留事件可能来自旧版（source 无 id）→ 用 get，不因缺字段崩
            "by_source": {sid: sum(1 for e in uniq if (e.get("source") or {}).get("id") == sid)
                          for sid in SRC_BY_ID},
            "carried_over": carried,
            "historical_only": sum(1 for e in uniq if e["presence"] == "HISTORICAL_ONLY"),
            "limits": [
                "**单一发布机构（国家发改委）、两个栏目**：政策通知 + 新闻发布，不是全市场新闻挖掘",
                "**类别有限**：只覆盖「政策/通知/规划/价格机制」类发布，不含部委标准、地方政策、公司公告",
                "**正文可得性不同**：政策通知正文常在 PDF/OFD 附件里 → `evidence.kind = ATTACHMENT_ONLY`，只有标题与附件可核",
                "参与广度不可得：行业板块无历史成分 → 只给板块收益与相对基准，不给广度",
                "个股映射未做：首版只到行业板块级，未建立证券级映射",
                "事件日期取列表页标注日；文章页「发布时间」多为日期级（无时分），故采用保守时点规则",
                "**不是预测**：`CANDIDATE` 只是「相对基准为正、值得人工复核」的机械筛选",
            ],
        },
        "rules": RULES, "status_legend": STATUS_LEGEND,
        "nature_legend": NATURE_LEGEND,
        "research_directions": RESEARCH_DIRECTIONS,
        "theme_keywords": [{"keyword": k, "board_series": s, "board_name": n,
                            "relation": r, "rationale": w} for k, s, n, r, w in THEME_KEYWORDS],
        "summary": {"events": len(uniq), "by_status": by_status,
                    "candidates": by_status.get("CANDIDATE", 0),
                    "candidates_are": "EVENTS_NOT_THEMES",
                    "by_presence": {
                        "IN_LATEST_LIST": sum(1 for e in uniq if e["presence"] == "IN_LATEST_LIST"),
                        "HISTORICAL_ONLY": sum(1 for e in uniq if e["presence"] == "HISTORICAL_ONLY")},
                    "review_verdicts": review_counts,
                    "by_nature": by_nature,
                    "by_direction": by_direction,
                    "routine_repeat_groups": {k: len(v) for k, v in routine_groups.items()}},
        "events": uniq,
    }


# ─────────────────────────── 校验 ───────────────────────────
def check():
    files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                   key=lambda f: int(OUT_RE.match(f).group(1)))
    if not files:
        print("FAIL: 事件产物不存在")
        return 1
    path = os.path.join(CURRENT, files[-1])
    d = json.load(open(path, encoding="utf-8"))
    errs = []
    if not d.get("events"):
        errs.append("零事件产物不得通过校验（%s）" % files[-1])
    for e in d.get("events") or []:
        eid = e.get("event_id")
        if not e.get("source", {}).get("url"):
            errs.append("%s 缺来源 URL" % eid)
        if not e.get("event_date"):
            errs.append("%s 缺事件日期" % eid)
        if e.get("status") not in STATUS_LEGEND:
            errs.append("%s 状态非法（%s）" % (eid, e.get("status")))
        title = e.get("title") or ""
        quote = (e.get("evidence") or {}).get("quote") or ""
        # ① 关联可复核：关键词必须真的出现在声明的字段里，且与注册表一致
        for L in e.get("theme_links") or []:
            kw, where = L.get("keyword"), L.get("matched_in")
            reg = KW_BY_NAME.get(kw)
            if not reg:
                errs.append("%s 关联关键词不在注册表（%s）" % (eid, kw))
                continue
            if (reg[1], reg[2], reg[3]) != (L.get("board_series"), L.get("board_name"), L.get("relation")):
                errs.append("%s 关联的板块/关系与注册表不一致（%s）" % (eid, kw))
            if where == "TITLE" and kw not in title:
                errs.append("%s 声称命中标题但关键词不在标题里（%s）" % (eid, kw))
            if where == "QUOTE" and kw not in quote:
                errs.append("%s 声称命中原文但关键词不在原文里（%s）" % (eid, kw))
            if where not in ("TITLE", "QUOTE"):
                errs.append("%s matched_in 非法（%s）" % (eid, where))
            if where == "QUOTE" and e.get("doc_type") not in QUOTE_MATCH_DOC_TYPES:
                errs.append("%s 正文命中但文档类型 %s 不允许建关联" % (eid, e.get("doc_type")))
        # ② 原文哈希可复核
        ev = e.get("evidence") or {}
        if ev.get("quote_sha256_16"):
            if not ev.get("quote"):
                errs.append("%s 有哈希但无原文" % eid)
            elif hashlib.sha256(ev["quote"].encode("utf-8")).hexdigest()[:16] != ev["quote_sha256_16"]:
                errs.append("%s 原文哈希不匹配" % eid)
        # ③ 逐板块：markets 的板块集合必须与 theme_links 一致
        link_sids = [L.get("board_series") for L in (e.get("theme_links") or [])]
        mk_sids = [m.get("board_series") for m in (e.get("markets") or [])]
        if link_sids and d.get("as_of") and sorted(set(link_sids)) != sorted(set(mk_sids)):
            errs.append("%s 行情板块与关联板块不一致（links=%s markets=%s）"
                        % (eid, sorted(set(link_sids)), sorted(set(mk_sids))))
        # ★★ v0.68：每个**必要 DIRECT** 板块都必须有独立行情记录（缺一即不得 CANDIDATE）
        direct_sids = [L.get("board_series") for L in (e.get("theme_links") or [])
                       if (L.get("relation") or "DIRECT") == "DIRECT"]
        for sid in dict.fromkeys(direct_sids):
            if sid not in mk_sids:
                errs.append("%s 必要 DIRECT 板块 %s 缺独立行情记录" % (eid, sid))
        if e.get("status") == "CANDIDATE" and direct_sids:
            for m in (e.get("markets") or []):
                if m.get("board_series") in direct_sids and m.get("status") != "OBSERVED":
                    errs.append("%s 标 CANDIDATE 但 DIRECT 板块 %s 未核验"
                                % (eid, m.get("board_series")))
        # ④b v0.69：来源 / 日期来源 / 事件性质 / 研究方向 必须合法且自洽
        if (e.get("source") or {}).get("id") not in SRC_BY_ID:
            errs.append("%s 来源 ID 不在注册表（%s）" % (eid, (e.get("source") or {}).get("id")))
        if (e.get("time") or {}).get("event_date_source") not in ("LIST_PAGE", "URL_PATH"):
            errs.append("%s 事件日期来源非法（%s）"
                        % (eid, (e.get("time") or {}).get("event_date_source")))
        nat = e.get("nature") or {}
        if nat.get("kind") not in NATURE_LEGEND:
            errs.append("%s 事件性质非法（%s）" % (eid, nat.get("kind")))
        if not nat.get("basis"):
            errs.append("%s 事件性质缺判据" % eid)
        dirs = e.get("research_directions") or []
        valid_dirs = set(DIRECTION_BY_SERIES.values())
        for x in dirs:
            if x not in valid_dirs:
                errs.append("%s 研究方向不在对应表（%s）" % (eid, x))
        # 研究方向必须能由关联序列推出（不能凭关键词直接写）
        for x in dirs:
            if not any(DIRECTION_BY_SERIES.get(L.get("board_series")) == x
                       for L in (e.get("theme_links") or [])):
                errs.append("%s 研究方向 %s 与关联序列不符" % (eid, x))
        # ④ 状态自洽
        if d.get("as_of"):
            want, _ = classify(e, d["as_of"])
            if want != e.get("status"):
                errs.append("%s 状态不自洽（产物 %s vs 规则 %s）" % (eid, e.get("status"), want))
    # ⑤b 常规重复：repeat_count 必须等于同组实际事件数（不得手写）
    grp = {}
    for e in d.get("events") or []:
        n = e.get("nature") or {}
        if n.get("kind") == "ROUTINE_RECURRING" and n.get("repeat_group"):
            grp.setdefault(n["repeat_group"], 0)
            grp[n["repeat_group"]] += 1
    for e in d.get("events") or []:
        n = e.get("nature") or {}
        if n.get("kind") == "ROUTINE_RECURRING":
            want = grp.get(n.get("repeat_group"))
            if want and n.get("repeat_count") != want:
                errs.append("%s repeat_count 不一致（产物 %s vs 实际 %s）"
                            % (e["event_id"], n.get("repeat_count"), want))
    keys = [(e["event_date"], re.sub(r"\s+", "", e["title"])) for e in d.get("events") or []]
    if len(keys) != len(set(keys)):
        errs.append("存在重复事件（同日期 + 同标题）")
    ids = [e["event_id"] for e in d.get("events") or []]
    if len(ids) != len(set(ids)):
        errs.append("event_id 重复")

    # ⑤ 行情逐字段复算（本地有库才算；CI 显式 SKIP）
    if os.path.exists(SCAN_DB) and d.get("as_of"):
        con = sqlite3.connect("file:%s?mode=ro" % SCAN_DB, uri=True)
        cal = _cal(con)
        n = 0
        for e in d.get("events") or []:
            t = e.get("time") or {}
            for m in e.get("markets") or []:
                if m.get("status") != "OBSERVED":
                    continue
                re_m = market_of(con, cal, m["board_series"], t.get("basis_day"),
                                 t.get("observe_from"), d["as_of"])
                for k in ("board_ret_pct", "bench_ret_pct", "excess_pp",
                          "observation_trading_days", "window"):
                    if re_m.get(k) != m.get(k):
                        errs.append("%s/%s 的 %s 不可复算（产物 %s vs 重算 %s）"
                                    % (e["event_id"], m["board_series"], k, m.get(k), re_m.get(k)))
                        break
                n += 1
        con.close()
        print("  行情复算覆盖 %d 条已核验板块观察" % n)
    else:
        print("  SKIP 行情复算：history_scan.db 不存在（CI 不携带 1.3GB 库）")

    if errs:
        print("FAIL: %s" % errs[:6])
        return 1
    print("PASS: 新题材雷达一致（%s · %d 事件 · %s · 历史保留 %d）"
          % (files[-1], len(d["events"]), d["summary"]["by_status"],
             d["summary"]["by_presence"]["HISTORICAL_ONLY"]))
    return 0


def latest_prev():
    files = sorted([f for f in os.listdir(CURRENT) if OUT_RE.match(f)],
                   key=lambda f: int(OUT_RE.match(f).group(1)))
    if not files:
        return None, None
    return files[-1], json.load(open(os.path.join(CURRENT, files[-1]), encoding="utf-8"))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="联网抓取（--write 必需）")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--version", type=int, default=None)
    a = ap.parse_args(argv)

    if a.check:
        return check()

    if a.write and not a.fetch:
        print("FAIL: --write 必须同时给 --fetch —— 否则会把「未抓取的空结果」写成新版本")
        return 2

    prev_file, prev = latest_prev() if a.fetch else (None, None)
    if prev_file:
        print("上一版：%s（%d 事件）→ 增量合并" % (prev_file, len(prev.get("events") or [])))
    doc = build(fetch=a.fetch, prev=prev)
    print("事件 %d 条 · 状态 %s · 历史保留 %d · as_of %s"
          % (len(doc["events"]), doc["summary"]["by_status"],
             doc["summary"]["by_presence"]["HISTORICAL_ONLY"], doc["as_of"]))
    for e in doc["events"][:8]:
        print("  [%-14s] %s %s" % (e["status"], e["event_date"], e["title"][:40]))
    if a.write:
        if a.version is None:
            print("FAIL: --write 需要 --version N")
            return 1
        if not doc["events"]:
            print("FAIL: 本次抓到 0 条事件 → 拒绝写入新版本（不覆盖有效产物）")
            return 1
        out = os.path.join(CURRENT, "new_theme_radar_v0_%d.json" % a.version)
        if os.path.exists(out):
            print("FAIL: 目标已存在：%s" % out)
            return 1
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        print("已生成 %s" % os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
