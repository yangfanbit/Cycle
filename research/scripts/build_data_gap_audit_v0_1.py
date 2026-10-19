"""build_data_gap_audit_v0_1.py —— v0.23 数据缺口审计（**只读 · 可复现**）。

## 这一轮做什么

把 `docs/PROJECT_STATE.md` 里长期挂着的三处**已量化缺口**逐条核验，产出**可追溯的裁决表**：

| 缺口 | 实测规模 |
|---|---|
| A · 证券注册表未命中 | **36 条参与者记录 / 17 个不同标识**（全部在流感题材） |
| B · 未登记对象关联 | **57 条参与者记录 / 8 个事件**（流感 5 + 电力 3） |
| C · 大基金三期窗口行情缺口 | **4 只登记标的**（SMIC / AMEC / PIOTECH / HYGON） |

## 硬边界（不得违反）

- **只做裁决，不改数据**：本脚本**不写** DB、快照、canonical export 或题材文件。
  缺口本身是否要改数据，须由后续 Research 轮次按证据决定。
- **不做模糊匹配**：身份一律按**精确 ID / ticker / 交易所披露**核对；
  **不**按名称相似、代码片段或题材推断归属。
- ★ **`YILING` 与 `YILING-002603` 不得自动合并** —— 只**提出**映射，标注为 PROVISIONAL，
  不在本脚本（也不在本轮）落任何合并动作。
- **未获授权的网络入库不做**：C 的行情补齐需要网络抓取，本轮**未执行**，
  `market_data.db` 与便携快照**逐字节未动**。

## 证据来源

- 身份证据：`research/database/cycle_research.db :: securities`（既有原始记录）+ 交易所披露
  （下表 `AUTHORITATIVE_SOURCES`，均为交易所/巨潮一手年报表或上市交易通知）；
- 缺口计数：canonical export（`securities` 注册表 = 各 owner 的 `security_ids` 并集，实测 190==190）、
  题材文件（`historical_event_maps_index.json` 指到的 ACTIVE 版本）、`market_data.db` 实测量程。

用法（仓库根执行）: `python research/scripts/build_data_gap_audit_v0_1.py`
"""
import sys, os, json, re, sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import db

# ★ `db.ROOT` = `research/`；本脚本需要的是**仓库根**（exports / docs 在其下）。
REPO = os.path.dirname(db.ROOT)
GENERATED_AT = "2026-10-19"

OUT = os.path.join(REPO, "research", "research", "reports", "data_gap_audit_v0_1.json")
INDEX = os.path.join(REPO, "research", "current", "historical_event_maps_index.json")
EXPORT = os.path.join(REPO, "exports", "timeline_export_v1.json")

# ---------------------------------------------------------------------------
# 权威来源（v0.23 逐条核验，均为交易所披露 / 巨潮一手文件；RL = 检索所得链接）
#   只做「身份确认」——即「该证券代码 ↔ 该证券简称 ↔ 该交易所」；
#   不用于推断其应归属哪个 Campaign。
# ---------------------------------------------------------------------------
AUTHORITATIVE_SOURCES = {
    "DAAN-002030": {
        "title": "广州达安基因股份有限公司 2025 年年度报告摘要",
        "url": "https://disc.static.szse.cn/disc/disk03/finalpage/2026-04-28/7b54b538-c950-482c-9e0c-5d1253e0c431.PDF",
        "published_at": "2026-04-28", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 达安基因 / 股票代码 002030 / 股票上市交易所 深圳证券交易所」",
    },
    "FUAN-300194": {
        "title": "福安药业（集团）股份有限公司 2025 年年度报告摘要",
        "url": "https://disc.static.szse.cn/download/disc/disk03/finalpage/2026-04-27/d8331680-8c6a-4da7-96d3-7f14486b5d45.PDF",
        "published_at": "2026-04-27", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 福安药业 / 股票代码 300194」；2024 年报摘要表列「股票上市交易所 深圳证券交易所」",
    },
    "HAIWANG-000078": {
        "title": "深圳市海王生物工程股份有限公司 2024 年年度报告摘要",
        "url": "https://disc.static.szse.cn/disc/disk03/finalpage/2025-04-28/9565628e-e623-43a0-93cf-71f6c7c8cfd0.PDF",
        "published_at": "2025-04-28", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 海王生物 / 股票代码 000078 / 股票上市交易所 深圳证券交易所」（2026 年简称变更为 ST海王）",
    },
    "HUALAN-002007": {
        "title": "关于华兰生物工程股份有限公司股票上市交易的通知",
        "url": "https://www.szse.cn/disclosure/notice/company/t20040618_508040.html",
        "published_at": "2004-06-18", "publisher": "深圳证券交易所",
        "evidence": "「证券简称为“华兰生物”,证券代码为“002007”」",
    },
    "JIUDIAN-300705": {
        "title": "关于湖南九典制药股份有限公司股票在创业板上市交易的公告",
        "url": "https://www.szse.cn/certificate/secondb/GEMdynamice/t20171009_502176.html",
        "published_at": "2017-10-09", "publisher": "深圳证券交易所",
        "evidence": "「证券简称为“九典制药”,证券代码为“300705”」",
    },
    "LAYNE-002166": {
        "title": "桂林莱茵生物科技股份有限公司 2025 年年度报告摘要",
        "url": "http://static.cninfo.com.cn/finalpage/2026-03-31/1225057506.PDF",
        "published_at": "2026-03-31", "publisher": "巨潮资讯网",
        "evidence": "「股票简称 莱茵生物 / 股票代码 002166 / 股票上市交易所 深圳证券交易所」",
    },
    "LIANHUAN-600513": {
        "title": "江苏联环药业股份有限公司 2025 年年度报告",
        "url": "http://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-04-21/600513_20260421_ALPO.pdf",
        "published_at": "2026-04-21", "publisher": "上海证券交易所",
        "evidence": "「公司代码：600513 / 公司简称：联环药业」；正文「公司股票简况」表含股票代码 600513",
    },
    "LUKANG-600789": {
        "title": "山东鲁抗医药股份有限公司 2025 年年度报告摘要",
        "url": "http://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-04-25/600789_20260425_PRXK.pdf",
        "published_at": "2026-04-25", "publisher": "上海证券交易所",
        "evidence": "「公司代码：600789 / 公司简称：鲁抗医药」",
    },
    "NANWEI-603880": {
        "title": "江苏南方卫材医药股份有限公司 2025 年年度报告",
        "url": "http://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-04-30/603880_20260430_G58L.pdf",
        "published_at": "2026-04-30", "publisher": "上海证券交易所",
        "evidence": "「A股 | 上海证券交易所 | 南卫股份 | 603880」",
    },
    "NEPHARM-000597": {
        "title": "东北制药集团股份有限公司 2025 年年度报告",
        "url": "https://disc.static.szse.cn/disc/disk03/finalpage/2026-04-03/d1d4fbb6-1bee-4e21-98b3-351d94f3027f.PDF",
        "published_at": "2026-04-03", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 东北制药 / 股票代码 000597 / 股票上市证券交易所 深圳证券交易所」",
    },
    "SIHUAN-000518": {
        "title": "江苏四环生物股份有限公司 2024 年年度报告",
        "url": "https://disc.static.szse.cn/disc/disk03/finalpage/2025-04-28/ab78f2c7-052d-4b2b-b6d7-1c9c06d05a44.PDF",
        "published_at": "2025-04-28", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 四环生物 / 股票代码 000518 / 股票上市证券交易所 深圳证券交易所」（2026 年简称变更为 *ST四环）",
    },
    "TAILONG-600222": {
        "title": "河南太龙药业股份有限公司 2024 年年度报告",
        "url": "https://www.sse.com.cn/disclosure/listedinfo/announcement/c/new/2025-04-09/600222_20250409_R8ON.pdf",
        "published_at": "2025-04-09", "publisher": "上海证券交易所",
        "evidence": "文件标题为「河南太龙药业股份有限公司 2024 年年度报告」，代码 600222；正文「公司股票简况」表",
    },
    "TIANKA-002100": {
        "title": "关于新疆天康畜牧生物技术股份有限公司股票上市交易的公告",
        "url": "https://www.szse.cn/disclosure/notice/company/t20061222_508129.html",
        "published_at": "2006-12-22", "publisher": "深圳证券交易所",
        "evidence": "「证券简称为“天康生物”,证券代码为“002100”」",
    },
    "WEIMING-002581": {
        "title": "山东未名生物医药股份有限公司 2021 年年度报告摘要",
        "url": "http://disc.static.szse.cn/download/disc/disk03/finalpage/2022-04-30/c21a7c6d-fc58-41d5-835d-e680c12be876.PDF",
        "published_at": "2022-04-30", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「股票简称 未名医药 / 股票代码 002581 / 股票上市交易所 深圳证券交易所」（2026 年简称变更为 ST未名）",
    },
    "WOHUA-002107": {
        "title": "山东沃华医药科技股份有限公司 2022 年年度报告摘要",
        "url": "http://disc.static.szse.cn/download/disc/disk03/finalpage/2023-03-22/22495868-5a68-4d69-b0fb-f10f7aa9a168.PDF",
        "published_at": "2023-03-22", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「证券代码:002107 证券简称:沃华医药」；表列「股票上市交易所 深圳证券交易所」",
    },
    "XIANGXUE-300147": {
        "title": "关于广州市香雪制药股份有限公司股票在创业板上市交易的公告",
        "url": "https://www.szse.cn/disclosure/notice/company/t20101213_500617.html",
        "published_at": "2010-12-13", "publisher": "深圳证券交易所",
        "evidence": "「证券简称为“香雪制药”,证券代码为“300147”」（2026 年简称变更为 ST香雪）",
    },
    "YILING-002603": {
        "title": "石家庄以岭药业股份有限公司 2018 年年度报告全文",
        "url": "https://disc.static.szse.cn/disc/disk01/finalpage/2019-04-25/89a18b72-e5be-4c24-8ecb-9201d6d1cb4d.PDF",
        "published_at": "2019-04-25", "publisher": "深圳证券交易所（巨潮披露）",
        "evidence": "「证券代码:002603 / 证券简称:以岭药业」；表列「股票上市证券交易所 深圳证券交易所」",
    },
}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def active_theme_files():
    idx = load(INDEX)
    return [(m["theme_id"], m["file"]) for m in idx["maps"] if m.get("status") == "ACTIVE"]


def theme_docs():
    out = {}
    for tid, fn in active_theme_files():
        out[tid] = load(os.path.join(REPO, "research", "current", fn))
    return out


# --------------------------------------------------------------------------- A
def audit_registry_miss(docs, export):
    reg = {s["security_id"]: s for s in export.get("securities", []) if s.get("security_id")}
    owners = set()
    for c in export.get("campaigns", []) + export.get("research_candidates", []):
        owners |= set(c.get("security_ids") or [])

    # 原始记录（DB securities）
    conn = sqlite3.connect(os.path.join(REPO, "research", "database", "cycle_research.db"))
    db_rows = {}
    for sid, ticker, name, exch in conn.execute(
            "SELECT security_id, ticker, name, exchange FROM securities"):
        db_rows[sid] = {"ticker": ticker, "name": name, "exchange": exch}

    groups = {}
    for tid, doc in docs.items():
        for e in doc.get("events", []):
            for p in e.get("participants", []):
                sid = p.get("security_id")
                if sid in reg:
                    continue
                g = groups.setdefault(sid, {
                    "original_id": sid, "rows": 0, "themes": set(), "events": set(),
                    "names_in_map": set(),
                })
                g["rows"] += 1
                g["themes"].add(tid)
                g["events"].add(e["event_id"])
                if p.get("name"):
                    g["names_in_map"].add(p["name"])

    items = []
    for sid, g in sorted(groups.items()):
        dbrow = db_rows.get(sid)
        ticker = dbrow["ticker"] if dbrow else None
        suffix = sid.rsplit("-", 1)[1] if "-" in sid else None
        consistent = bool(ticker) and ticker == suffix
        # 候选规范 ID：DB 中**同一 ticker 且同一名称**的**其它** security_id
        cands = sorted(
            s for s, r in db_rows.items()
            if s != sid and r["ticker"] == ticker and r["name"] == (dbrow or {}).get("name")
        )
        cands_in_reg = [s for s in cands if s in reg]
        proposed = cands_in_reg[0] if cands_in_reg else None
        src = AUTHORITATIVE_SOURCES.get(sid)
        if proposed:
            cls = "PROVISIONAL"
            conclusion = (
                f"身份已确认（{dbrow['name']} / {ticker} / {dbrow['exchange']}，交易所披露一致）；"
                f"DB 内存在**同一 ticker + 同一名称**的重复标识 `{proposed}`，且该标识**在** canonical export "
                f"注册表中 → **提出映射** `{sid}` → `{proposed}`（属**重复标识**，非身份不明）。"
                f"★ 依 AGENTS/本轮硬约束，**不自动合并**；落库合并须单独 Research 轮次裁定。"
            )
        else:
            cls = "UNRESOLVED"
            reason_extra = (
                "；且 DB 内**没有**同 ticker 同名称的其它标识"
                if not cands else
                f"；DB 内唯一同名同 ticker 标识 `{cands[0]}` **也不在** export 注册表中"
            )
            conclusion = (
                f"身份已确认（{dbrow['name']} / {ticker} / {dbrow['exchange']}，交易所披露一致）"
                f"，**但没有可映射的规范 ID**{reason_extra} —— "
                f"该证券**未被任何导出对象（Campaign / RC）引用**，故不在 owner-scoped 的 export 注册表内。"
                f"缺口的性质是**注册表覆盖（ownership）缺口**，**不是**标识错误："
                f"要关闭它，须由 Research 轮次按证据决定「该证券是否归属于某个对象」——**本轮不改数据**。"
            )
        items.append({
            "original_id": sid,
            "name": (dbrow or {}).get("name"),
            "ticker": ticker,
            "exchange": (dbrow or {}).get("exchange"),
            "rows": g["rows"],
            "themes": sorted(g["themes"]),
            "events": sorted(g["events"]),
            "names_in_map": sorted(g["names_in_map"]),
            "in_db_securities": dbrow is not None,
            "id_suffix_equals_ticker": consistent,
            "authoritative_source": src if src else None,
            "identity_evidence_sufficient": src is not None,
            "canonical_candidates_same_ticker_name": cands,
            "proposed_canonical_id": proposed,
            "classification": cls,
            "conclusion": conclusion,
        })

    def tally(k):
        return sum(1 for i in items if i["classification"] == k)

    # ★ 自检：每个未命中标识都必须有**权威身份来源**，否则本产物不得静默降级
    missing = [i["original_id"] for i in items if not i["authoritative_source"]]
    if missing:
        raise SystemExit("FAIL 以下未命中标识缺少权威身份来源，必须先核验：%s" % missing)
    bad = [i["original_id"] for i in items if not i["id_suffix_equals_ticker"]]
    if bad:
        raise SystemExit("FAIL 以下标识的后缀与 DB ticker 不一致（需人工复核）：%s" % bad)

    return {
        "before": {"participant_rows": sum(g["rows"] for g in groups.values()),
                   "distinct_security_ids": len(items)},
        "after": {"participant_rows": sum(g["rows"] for g in groups.values()),
                  "distinct_security_ids": len(items)},
        "root_cause": (
            "export 的 `securities` 注册表是 **owner-scoped**（合同 §8：每条必须带 owner；"
            "实测：注册表 190 条 == 各 owner `security_ids` 并集 190 条，两侧零差集）。"
            "17 个标识**全部**存在于 Research DB 的 `securities` 原始记录中（含 ticker / 交易所），"
            "但**未被任何导出对象引用** → 必然落在注册表外。"
        ),
        "classification_tally": {
            "RESOLVED": tally("RESOLVED"), "PROVISIONAL": tally("PROVISIONAL"),
            "UNRESOLVED": tally("UNRESOLVED"),
        },
        "items": items,
    }


# --------------------------------------------------------------------------- B
def audit_unregistered_object(docs, export):
    obj_sec = {}
    for c in export.get("campaigns", []) + export.get("research_candidates", []):
        obj_sec[c["campaign_id"]] = set(c.get("security_ids") or [])

    events = []
    total_rows = 0
    for tid, doc in docs.items():
        for e in doc.get("events", []):
            cf = e.get("campaign_facts") or {}
            oid = cf.get("object_id") or cf.get("campaign_id")
            ps = {p.get("security_id") for p in e.get("participants", [])}
            total_rows += len(ps)
            if oid:
                continue
            blob = json.dumps(e, ensure_ascii=False)
            mentioned = sorted(set(re.findall(r"(?:RC|C)-20\d\d[A-Z0-9\-]*", blob)))
            exact = sorted(k for k, v in obj_sec.items() if v and v == ps)
            overlap = sorted(
                ({"object_id": k, "overlap": len(v & ps), "object_size": len(v)}
                 for k, v in obj_sec.items() if (v & ps) and v != ps),
                key=lambda x: -x["overlap"],
            )[:5]
            events.append({
                "theme": tid,
                "event_id": e["event_id"],
                "year": e.get("year"),
                "participant_rows": len(ps),
                "evidence_basis": e.get("evidence_basis"),
                "window_text": e.get("window_text"),
                "campaign_ids_mentioned_in_event": mentioned,
                "objects_with_EXACT_security_ids_equality": exact,
                "top_overlapping_objects": overlap,
                "classification": "UNRESOLVED",
                "reason": (
                    "事件文本**未引用**任何 Campaign / RC id；且参与者 `security_id` 集合与"
                    "**任何**导出对象的 `security_ids` **不相等**（无精确相等者）→ 无证据支持归属，"
                    "**不得**按主题相近或年份相近认定属于同一 Campaign。"
                ),
            })
    events.sort(key=lambda x: (x["theme"], x["event_id"]))
    return {
        "before": {"participant_rows": sum(e["participant_rows"] for e in events),
                   "events": len(events)},
        "after": {"participant_rows": sum(e["participant_rows"] for e in events),
                  "events": len(events)},
        "evidence_standard": (
            "★ 沿用 v0.18 已确立的证据标准：只有当事件的 `evidence_basis` **明确引用**某对象，"
            "**且**其标的集合与该对象 `security_ids` **逐一相等**时，才补对象关联"
            "（v0.18 的 `FLU-2023-H1N1 → C-2023-PHARMA-FLU` 即此标准）。"
        ),
        "classification_tally": {
            "RESOLVED": 0,
            "PROVISIONAL": 0,
            "UNRESOLVED": len(events),
        },
        "events": events,
    }


# --------------------------------------------------------------------------- C
FUND3_TARGETS = [
    ("SMIC", "中芯国际", "688981", "sh688981"),
    ("AMEC", "中微公司", "688012", "sh688012"),
    ("PIOTECH", "拓荆科技", "688072", "sh688072"),
    ("HYGON", "海光信息", "688041", "sh688041"),
]

# ★★ v0.23 已执行的数据层补齐记录（授权后 · 既有抓取流程 `fetch_market_batch_v0_3.py`）。
#    数字来自该次运行；快照随后由 `make_market_snapshot.py` 重生成。
FUND3_BACKFILL = {
    "executed": True,
    "fetcher": "research/scripts/fetch_market_batch_v0_3.py",
    "provider": "tencent_gtimg（web.ifzq.gtimg.cn，项目既有抓取流程所用源）",
    "command": ("--only SMIC,AMEC,HYGON,PIOTECH --series "
                "SMIC@2016-01-01~2025-12-31,AMEC@2016-01-01~2025-12-31,"
                "HYGON@2016-01-01~2025-12-31,PIOTECH@2022-01-01~2025-12-31"),
    "range_ceiling": "2025-12-31",
    "fetched": {
        "AMEC": {"symbol": "sh688012", "range": ["2016-01-01", "2025-12-31"], "raw": 1557, "qfq": 1557},
        "HYGON": {"symbol": "sh688041", "range": ["2016-01-01", "2025-12-31"], "raw": 812, "qfq": 812},
        "PIOTECH": {"symbol": "sh688072", "range": ["2022-01-01", "2025-12-31"], "raw": 900, "qfq": 900},
        "SMIC": {"symbol": "sh688981", "range": ["2016-01-01", "2025-12-31"], "raw": 1321, "qfq": 1321},
    },
    "series_registered": {"PIOTECH": "原无 market_series 登记 —— 本轮补登（provider=tencent / symbol=sh688072）"},
    "pre_existing_rows_unchanged": "已逐 (trade_date, price_type) 比对：SMIC/AMEC/HYGON 既有行 **0 变更 / 0 丢失**",
    "snapshot": {
        "regenerated_by": "research/scripts/make_market_snapshot.py",
        "market_daily_rows": "376,401 → 380,771", "market_series_rows": "213 → 214",
        "restore_check": "PASS（逐分片内容哈希一致，含全部 REAL 逐位相同）",
    },
    "fetch_report": "research/research/reports/market_fetch_v0_3_report.json",
    "map_transcription": {
        "status": "UNRESOLVED",
        "reason": ("★ 数据层已补齐，但**题材文档（地图展示）未刷新** —— 且**不应在本轮刷新**："
                   "实测 12 份题材文档的 `max_drawdown_from_high_pct` 等口径**互相不一致**，"
                   "任一单一公式都无法复现（逐一验算：仅 3/12 份可完全复现），"
                   "强行重算＝编造。须由**独立、可复现的转写流程**（新轮次）统一口径后再生效。"),
    },
}


def audit_market_gap(docs):
    mconn = sqlite3.connect(os.path.join(REPO, "research", "database", "market_data.db"))
    series = {r[0]: {"name": r[1], "symbol": r[4]} for r in
              mconn.execute("SELECT series_id, name, series_type, provider, symbol FROM market_series")}

    semi = docs.get("SEMICONDUCTOR_AI")
    ev = next((e for e in semi.get("events", []) if e["event_id"] == "SEMI-2024-FUND3"), None)
    window = (ev or {}).get("market_performance", {}).get("window")

    items = []
    for sid, name, ticker, sym in FUND3_TARGETS:
        s = series.get(sid)
        if not s:
            cause = "SERIES_NOT_REGISTERED"
            cov = None
            inwin = 0
        else:
            r = mconn.execute(
                "SELECT MIN(trade_date), MAX(trade_date), COUNT(*) FROM market_daily WHERE series_id=?",
                (sid,)).fetchone()
            cov = {"min": r[0], "max": r[1], "rows": r[2]}
            inwin = mconn.execute(
                "SELECT COUNT(*) FROM market_daily WHERE series_id=? AND price_type='adjusted'"
                " AND trade_date BETWEEN ? AND ?",
                (sid, window[0], window[1])).fetchone()[0] if window else 0
            cause = "FETCH_COVERAGE_GAP" if inwin == 0 else "RESOLVED_BY_BACKFILL"
        ok = inwin > 0
        items.append({
            "security_id": sid, "name": name, "ticker": ticker,
            "intended_series_symbol": sym,
            "series_registered": s is not None,
            "series_symbol": (s or {}).get("symbol"),
            "coverage": cov,
            "window": window,
            "rows_in_window": inwin,
            "root_cause_before_backfill": (
                "SERIES_NOT_REGISTERED" if cause == "SERIES_NOT_REGISTERED" else
                "FETCH_COVERAGE_GAP" if not ok else "FETCH_COVERAGE_GAP（已补齐）"),
            "identity_source": "题材事件 `participants` 登记的 name + ticker（Research 侧原始记录）",
            "data_layer_classification": "RESOLVED" if ok else "UNRESOLVED",
            "classification": "RESOLVED" if ok else "UNRESOLVED",
            "reason": (
                f"窗口 {window[0]} ~ {window[1]} 现有 **{inwin}** 个交易日（adjusted）→ 数据层缺口已关闭。"
                if ok else
                "窗口内仍无数据 —— 需继续抓取（见 backfill 记录）"
            ),
            "follow_up": (
                "★ 地图展示**未**刷新：题材文档的行情转写口径不可复现（见 C.map_transcription），"
                "须由独立可复现的转写流程在后续轮次统一后再生效。"
            ),
        })
    n_ok = sum(1 for i in items if i["classification"] == "RESOLVED")
    return {
        "before": {"securities": len(items), "securities_with_window_data": len(items) - n_ok},
        "after": {"securities": len(items), "securities_with_window_data": n_ok},
        "classification_tally": {
            "RESOLVED": n_ok, "PROVISIONAL": 0, "UNRESOLVED": len(items) - n_ok,
        },
        "follow_up": FUND3_BACKFILL["map_transcription"],
        "backfill": FUND3_BACKFILL,
        "items": items,
    }


def main():
    export = load(EXPORT)
    docs = theme_docs()
    a = audit_registry_miss(docs, export)
    b = audit_unregistered_object(docs, export)
    c = audit_market_gap(docs)

    doc = {
        "artifact": "data_gap_audit",
        "artifact_version": "0.1",
        "generated_at": GENERATED_AT,
        "generated_by": "research/scripts/build_data_gap_audit_v0_1.py",
        "supersedes": None,
        "position": (
            "★ v0.23 数据缺口审计：把 A（证券注册表未命中）· B（未登记对象关联）· "
            "C（大基金三期窗口行情缺口）逐条核验为**可追溯裁决表**。"
            "★ A/B **只读、不改数据**；C 在**用户明确授权后**执行了**数据层补齐**"
            "（既有抓取流程 + 便携快照重生成），但**地图展示（题材文档）未刷新** —— 见 C.map_transcription。"
            "★ 不新增题材、不改 SA 判定、不推断逐证券结构对应。"
        ),
        "hard_constraints": [
            "不按名称相似 / 代码片段 / 题材推断归属（只做精确 ID / ticker / 交易所披露核对）",
            "YILING 与 YILING-002603 不得自动合并（只提出映射，标注 PROVISIONAL）",
            "C 的行情**只能**由既有抓取流程取真值；不得编造价格、不得用相邻日期替换窗口端点",
            "C 的**地图展示值不得手工修改** —— 题材文档转写口径不可复现，须由独立可复现流程（新轮次）统一",
            "不改 canonical export / SA / TO / Driver / schema.sql / 冻结历史轮次",
        ],
        "workflows": {
            "A_registry_miss": a,
            "B_unregistered_object": b,
            "C_market_coverage": c,
        },
        "summary": {
            "A": a["classification_tally"],
            "B": b["classification_tally"],
            "C": c["classification_tally"],
            "resolved_total": a["classification_tally"]["RESOLVED"]
            + b["classification_tally"]["RESOLVED"] + c["classification_tally"]["RESOLVED"],
            "provisional_total": a["classification_tally"]["PROVISIONAL"]
            + b["classification_tally"]["PROVISIONAL"] + c["classification_tally"]["PROVISIONAL"],
            "unresolved_total": a["classification_tally"]["UNRESOLVED"]
            + b["classification_tally"]["UNRESOLVED"]
            + c["classification_tally"]["UNRESOLVED"],
            "c_follow_up_map_transcription": c["follow_up"]["status"],
        },
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")

    print("A: rows=%d ids=%d -> %s" % (a["after"]["participant_rows"],
                                       a["after"]["distinct_security_ids"], a["classification_tally"]))
    print("B: rows=%d events=%d -> %s" % (b["after"]["participant_rows"],
                                          b["after"]["events"], b["classification_tally"]))
    print("C: %s" % (c["classification_tally"],))
    print("summary: %s" % (doc["summary"],))
    print("WROTE %s" % os.path.relpath(OUT, REPO))


if __name__ == "__main__":
    main()
