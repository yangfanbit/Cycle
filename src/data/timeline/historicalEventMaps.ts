/**
 * 通用历史事件地图 —— 索引与题材无关的类型（产品侧）。
 *
 * ## 定位
 * 把「题材 → 年份 → 历史事件 → 相关证券 → 证据与行情」从**流感单题材**推广到**多题材**。
 * 每个题材一个独立 JSON（各自版本化、逐字节保留），本模块提供**索引 + 通用类型 + 通用校验**。
 *
 * ## 与 `fluHistoricalEvents.ts` 的关系
 * - `fluHistoricalEvents.ts` 保留为**流感题材的详细适配器**（含流感专属常量与校验）
 * - 本模块提供**跨题材通用**能力；`HistoricalEventMap` 组件消费本模块的类型
 *
 * ## 硬边界（跨题材通用，不得因题材化而丢失）
 * - ★ 事件类别与其免责声明由**索引**的 `display.class_caveats` 提供
 * - ★ `evidence_level` 与 `category` **分离** —— 业务机制核实**不**改变 `category`
 * - ★ 「行情不可得」显式标注，**不得**显示为 0 涨幅
 * - ★ 三条通用免责声明由代码常量提供，**不**进题材 JSON
 */
import indexRaw from '@current/historical_event_maps_index.json';
// ★ 各题材事件数据：**静态 import**（vite/TS 要求；索引只提供展示配置与入口映射）
// ★ v0.18：流感题材升到 v0_7（**只**为 `FLU-2023-H1N1` 补齐对象关联 `C-2023-PHARMA-FLU`；数值零变化）
import fluDoc from '@current/flu_historical_events_v0_7.json';
// ★ v0.26：升到 v0_4 —— POWER-2017 四只标的按合同重算并**验证通过**（WARN→0），
//   参与者 market_data 文案更正为库内实况（2017-04-05 起）；百分比与原 2 位小数值等量
// ★ v0.27：升 v0_5（合同 v2：显式 price_basis + 跳变按证据分类）
import powerDoc from '@current/power_historical_events_v0_5.json';
import mediaDoc from '@current/media_historical_events_v0_1.json';
import roboticsDoc from '@current/robotics_historical_events_v0_1.json';
import autoDoc from '@current/auto_intelligence_historical_events_v0_1.json';
// ★ v0.24：半导体题材升到 v0_2（大基金三期四只标的行情按 theme_market_performance_v1 重算；
//   其余 6 事件百分比数值不变；v0_1 逐字节保留）
// ★ v0.25：升到 v0_4（AUTO 缺口行逐类写原因：非正价格 / 不连续 ≠ 库内无登记）
// ★ v0.26：升到 v0_5（序列范围延至 2026-10-20，覆盖文本刷新，数值不变）
// ★ v0.27：升 v0_6（合同 v2，数值不变）
import semiDoc from '@current/semiconductor_ai_compute_historical_events_v0_6.json';
// ★ v0.25：消费旺季（5 事件）/ 资源品（2 事件）—— 由 `build_theme_map_v0_1.py` 从库内 Campaign 生成
import consumerDoc from '@current/consumer_season_historical_events_v0_3.json';
import resourceDoc from '@current/resource_metal_historical_events_v0_3.json';

/* ------------------------------------------------------ 通用类型 */

export type EventClassCode = string;

export type ParticipantCategory =
  | 'MECHANISM_DIRECT'
  | 'MARKET_PARTICIPANT'
  | 'SPILLOVER'
  | 'COUNTER_EXAMPLE'
  | 'INSUFFICIENT';

/**
 * ★★ 2026-10-18（v0.16）：**反例**（`COUNTER_EXAMPLE`）与**证据不足**（`INSUFFICIENT`）是**两回事**：
 *   - `COUNTER_EXAMPLE`：确进了记录，但与本题材机制**不同轴**，作为**反面参照**保留
 *     （如大众交通＝运营牌照方、与智驾技术链不同轴）；
 *   - `INSUFFICIENT`：参与 / 机制证据**不足**，尚不足以判断。
 * 二者都**不**计入「本题材的可分析行情」—— 但**不得**互相等同。
 */
export const NON_THEME_CATEGORIES = ['COUNTER_EXAMPLE', 'INSUFFICIENT'] as const;

/** 是否属于「本题材方向」的参与者（反例 / 证据不足 → `false`） */
export function isThemeParticipant(p: { category: ParticipantCategory }): boolean {
  return !(NON_THEME_CATEGORIES as readonly string[]).includes(p.category);
}

export type EvidenceLevel = 'REPORT_NAMED' | 'BUSINESS_VERIFIED';

export interface HistoricalParticipant {
  security_id: string;
  ticker: string;
  name: string;
  exchange?: string;
  category: ParticipantCategory;
  evidence_level?: EvidenceLevel;
  reported_move?: string;
  rationale: string;
  source: string;
  note?: string;
  market_data?: string;
  period_return_pct?: number;
  to_high_pct?: number;
  high_date?: string;
  /** ★ 相对基准的「至高点」超额（pp）—— 至高点涨幅 − 基准至高点涨幅 */
  excess_to_high_pp?: number;
  /** ★ 相对基准的「区间」超额（pp）—— 区间涨跌 − 基准区间涨跌（**与至高点超额不同口径**） */
  excess_period_pp?: number;
  business_mechanism?: string;
  business_mechanism_caveat?: string;
}

export interface SecurityPerformance {
  status?: string;
  /** ★ 行情无覆盖 / 数据不足：`insufficient_data_in_window`（既有文件既有形态，类型补齐） */
  error?: string;
  /** ★ v0.24：缺失原因（`no_series` / `no_rows_in_window` / `single_row`），**不代替** error */
  reason?: string;
  /**
   * ★ v0.27（合同 v2）：价格基准声明，**不得隐式**。
   * 当前只有 `adjusted_qfq`（前复权收盘）；旧文件无此字段 → `undefined`（读作「未声明」）。
   */
  price_basis?: string;
  trading_days?: number;
  first?: { date: string; close: number };
  last?: { date: string; close: number };
  high?: { date: string; close: number };
  low?: { date: string; close: number };
  /**
   * ★ v0.24：`power_historical_events_v0_3.json` 用的是**扁平写法**
   * （`high_date` + `high_close`）。两种写法**语义相同**，读取一律走 `highPointOf()`，
   * 否则扁平写法的「高点日」会被静默显示成 `—`。
   */
  high_date?: string;
  high_close?: number;
  period_return_pct?: number;
  to_high_pct?: number;
  max_drawdown_from_high_pct?: number;
  excess_to_high_pp?: number;
  excess_period_pp?: number;
}

/** ★ 高点（兼容 `high:{date,close}` 与扁平 `high_date`/`high_close` 两种既有写法） */
export function highPointOf(st: SecurityPerformance | undefined): { date: string; close: number } | undefined {
  if (!st) return undefined;
  if (st.high) return st.high;
  if (st.high_date) return { date: st.high_date, close: st.high_close as number };
  return undefined;
}

export interface MarketPerformance {
  window: [string, string] | null;
  /** ★ v0.24：行情计算合同版本（`theme_market_performance_v1`）；旧文件无此字段 */
  contract_version?: string;
  is_campaign_ruling: false;
  note: string;
  benchmark: Record<string, SecurityPerformance>;
  by_security: Record<string, SecurityPerformance>;
}

export interface HistoricalEvent {
  event_id: string;
  event_class?: EventClassCode;
  label: string;
  year: number;
  window_text: string;
  external_window_ref: string | null;
  evidence_basis: string;
  study_state?: string;
  /** 流感题材：三个「高峰」概念区分 */
  three_peaks_note?: string;
  /** 多题材：四个不同概念（外部窗口 / peak_date / 催化日 / 个股高点） */
  four_concepts_note?: string;
  /** 媒体标签 vs 可核实催化（分开保存） */
  media_label_note?: string;
  /** Campaign 事实（多题材） */
  campaign_facts?: {
    /** 旧字段（仅 Campaign）；v0.15 起新文件用 `object_id` + `object_kind`（RC 不伪装 Campaign） */
    campaign_id?: string;
    /** ★ v0.15：对象 id（Campaign 或 Research Candidate） */
    object_id?: string;
    /** ★ v0.15：对象类型；缺省按 `campaign_id` 存在视为 campaign */
    object_kind?: 'campaign' | 'candidate';
    status?: string;
    main_rise?: { start: string; end: string; precision?: string } | null;
    start: string | null;
    peak_date: string | null;
    end: string | null;
    note?: string;
  };
  catalysts: { date: string; text: string; source: string; note?: string }[];
  // ★ 研究侧对阶段名的字段是 `stage`（power v0_3 实测），`phase_type` 为历史别名 → 两读
  phases?: { phase_id: string; phase_type?: string; stage?: string; start: string; end: string; description: string }[];
  participants: HistoricalParticipant[];
  observed_performance: {
    note: string;
    by_security: Record<string, string> | null;
    reported_same_day_moves?: Record<string, string>;
  };
  market_performance?: MarketPerformance;
  /**
   * ★ v0.56（Wave 2.1）：官方指数**并列**行情 —— 与 `market_performance` 是**两套口径**，
   *   **不得**合并成同一个收益值、**不得**用它改写 `market_performance` 或事件机制结论。
   *   授权明确前生产产物**不含**该字段（真实派生数值只在本地实验输出）。
   */
  official_index?: OfficialIndexPerformance | null;
  known_gaps: string[];
}

/**
 * ★ v0.56：官方指数并列行情对象。
 *
 * 口径（生成端 `research/scripts/build_official_index_parallel_v0_1.py` 统一实现）：
 * - 区间收益 = 末交易日 close / 首交易日 close − 1
 * - 基准 = 官方 000300 同窗口区间收益；超额 = 本指数 − 基准（pp）
 * - `rows_before_publish` 由**实际获取的完整序列**计算；`backfilled` 是**事件窗口级**标记
 *
 * ★★ `backfilled` 三态：`true` 窗口含发布前数据点（不得作当时可知证据）/
 *    `false` 窗口全在发布日之后 / `null` 无窗口或未知（**不得**当作 false）。
 */
export interface OfficialIndexPerformance {
  provider: string;
  index_code: string;
  index_name: string;
  identity: string;
  identity_note?: string;
  published_from: string;
  base_date: string;
  base_value: number;
  source_first_date: string;
  source_last_date: string;
  rows_before_publish: number;
  backfilled: boolean | null;
  window: [string, string] | null;
  window_actual?: {
    first_trade_date: string; last_trade_date: string;
    first_close: number; last_close: number; trading_days: number;
  } | null;
  period_return_pct: number | null;
  benchmark_index_code: string;
  benchmark_index_name?: string;
  benchmark_return_pct: number | null;
  excess_period_pp: number | null;
  price_basis: string;
  source_url: string;
  benchmark_source_url?: string;
  status?: string;
  error?: string | null;
  calculation_note: string;
  missing_required_fields?: string[];
}

export interface ThemeDisplay {
  title: string;
  aria_label: string;
  badge: string;
  note: string;
  class_order: string[];
  class_caveats?: Record<string, string>;
}

export interface HistoricalEventsDoc {
  artifact: string;
  artifact_version: string;
  theme?: { theme_id: string; label: string };
  position: string;
  corrections?: {
    at: string; what: string; why: string;
    /** ★ v0.24：生成方式（可复现入口）与影响范围 */
    how?: string; effect?: string;
    source?: string; note?: string;
  }[];
  event_classes?: { code: string; label: string; meaning: string }[];
  events: HistoricalEvent[];
  [k: string]: unknown;
}

export interface EventMapIndexEntry {
  theme_id: string;
  label: string;
  file: string;
  external_entry_ids: string[];
  /**
   * ★ v0.15：显式声明「本题材**没有**外部季节性对应线索」。
   * 未声明而 `external_entry_ids` 为空 → 索引校验按问题处理（防「忘了挂」被静默放过）。
   */
  external_link_status?: 'NO_EXTERNAL_COUNTERPART';
  display: ThemeDisplay;
  event_count?: number;
  status?: string;
}

export interface EventMapIndex {
  artifact: string;
  artifact_version: string;
  maps: EventMapIndexEntry[];
  not_included?: { items: { theme_id: string; label: string; reason: string }[] };
}

/* ------------------------------------------------------ 跨年份比较（通用规范类型） */

/**
 * ★★ 跨年份比较的**规范类型**。
 *
 * 设计原则：本模块只做**字段名映射**（把各题材 JSON 里不同名字的同一含义字段归一到一套名字），
 * **不重新推导任何研究结论、不重算任何收益**。因此：
 * - `outcome` 原样保留（未知码原样显示，见 `CROSS_YEAR_OUTCOME_LABEL`）
 * - 缺失字段一律留空（`undefined` / `null`），**不得**补 0
 * - `comparable` 在归一化时由 `outcome` 映射而来，并**显式声明这是映射规则**，不是研究判断
 */
export interface CrossYearSecurityPerf {
  period_return_pct?: number; trading_days?: number;
  first?: { date: string; close?: number };
  last?: { date: string; close?: number };
  high?: { date: string; close?: number };
  to_high_pct?: number; max_drawdown_from_high_pct?: number;
  excess_period_pp?: number; excess_to_high_pp?: number;
  status?: string; note?: string;
}

export interface CrossYearBenchmarkPerf {
  id: string; label?: string; trading_days?: number;
  first?: { date: string; close?: number };
  last?: { date: string; close?: number };
  high?: { date: string; close?: number };
  period_return_pct?: number; to_high_pct?: number; max_drawdown_from_high_pct?: number;
}

export interface CrossYearYear {
  year: number;
  season_label?: string;            // 如 "2017/18 季"
  window_type: string;              // 'SEASON_WINDOW_9_1' | 'SEASON_WINDOW_5_7' | 'CAMPAIGN_FULL_PERIOD' | ...
  window?: [string, string] | null;         // 目标窗口
  actual_window?: [string, string] | null;  // 实际可得区间
  coverage?: 'FULL' | 'PARTIAL' | 'NONE';
  event_type?: string; mechanism?: string;
  /**
   * ★ v0.9：源数据的「窗口内是否确有本题材事件」标志（流感有，电力无）。
   * **只透传，不推断** —— 缺字段 → `undefined`（不是 `false`）。
   * 用途：区分「价格结果」与「事件机制」（如 2019/20 季 UP 由非流感事件驱动）。
   */
  in_window_event?: boolean;
  /** ★ v0.9：源数据的驱动说明原文（**不重写、不改写**） */
  driver?: string;
  outcome: string;                  // 见 CROSS_YEAR_OUTCOME_LABEL 码表
  comparable?: boolean | 'partial';
  comparable_reason?: string;
  benchmark?: CrossYearBenchmarkPerf | null;
  by_security?: Record<string, CrossYearSecurityPerf> | null;
  note?: string;
  /** ★ 原始 `campaign_full` 原样保留（不同窗口口径，不在主表渲染，**不得丢失**） */
  campaign_full?: unknown;
}

export interface CrossYearComparison {
  window_basis: string; season_window?: string; target_pool?: string;
  inclusion_principle?: string; benchmark?: string; conclusion_short?: string;
  years: CrossYearYear[]; reading?: string; limitations?: string[];
}

/* ------------------------------------------------------ 题材文档注册表 */

/**
 * ★ 题材 ID → 事件数据文档。
 * 新增题材时在此登记（静态 import），并在索引 JSON 的 `maps` 里加一条配置。
 * ★ 索引里**没有** doc、注册表里**没有** file 的题材 → 不显示（避免空壳）。
 */
const DOCS: Record<string, HistoricalEventsDoc> = {
  FLU: fluDoc as unknown as HistoricalEventsDoc,
  POWER_SUMMER: powerDoc as unknown as HistoricalEventsDoc,
  MEDIA: mediaDoc as unknown as HistoricalEventsDoc,
  ROBOTICS: roboticsDoc as unknown as HistoricalEventsDoc,
  // ★ v0.15：汽车智能化 / 智能驾驶（6 事件 · 22 参与者，赛力斯行情不覆盖窗口→如实留空）
  AUTO_INTELLIGENCE: autoDoc as unknown as HistoricalEventsDoc,
  // ★ v0.16：半导体 / AI 算力 / 存储（7 事件 · 29 参与记录，大基金三期窗口行情不可得→如实留空）
  SEMICONDUCTOR_AI: semiDoc as unknown as HistoricalEventsDoc,
  // ★ v0.25：消费旺季 / 大众消费（5 事件 · 17 参与记录；窗口 = Campaign 主升段，**不是**季节性月份）
  CONSUMER_SEASON: consumerDoc as unknown as HistoricalEventsDoc,
  // ★ v0.25：资源品 / 黄金 · 稀土（2 事件 · 8 参与记录；黄金与稀土机制不同轴）
  RESOURCE_METAL: resourceDoc as unknown as HistoricalEventsDoc,
};

/** 索引条目 + 已加载的题材文档 */
export interface ResolvedEventMap extends EventMapIndexEntry {
  doc: HistoricalEventsDoc;
}

function resolve(entry: EventMapIndexEntry | undefined): ResolvedEventMap | undefined {
  if (!entry) return undefined;
  const doc = DOCS[entry.theme_id];
  if (!doc) return undefined;          // ★ 未登记 → 视为无数据（不显示空壳）
  return { ...entry, doc };
}

/* ------------------------------------------------------ 索引访问 */

export function eventMapIndex(): EventMapIndex {
  return indexRaw as unknown as EventMapIndex;
}

export function eventMapEntries(): EventMapIndexEntry[] {
  return eventMapIndex().maps;
}

export function eventMapByTheme(themeId: string): ResolvedEventMap | undefined {
  return resolve(eventMapEntries().find((m) => m.theme_id === themeId));
}

/** ★ 按外部季节性线索 ID（如 EXT-14）找对应的事件地图；无则返回 undefined（**不显示空壳**） */
export function eventMapByExternalId(entryId: string): ResolvedEventMap | undefined {
  return resolve(eventMapEntries().find((m) => m.external_entry_ids.includes(entryId)));
}

/** 所有**已加载**的题材事件地图（用于校验与测试） */
export function allResolvedEventMaps(): ResolvedEventMap[] {
  return eventMapEntries().map(resolve).filter((x): x is ResolvedEventMap => Boolean(x));
}

/** 未建立事件地图的题材（及其原因） */
export function eventMapsNotIncluded(): { theme_id: string; label: string; reason: string }[] {
  return eventMapIndex().not_included?.items ?? [];
}

/* ------------------------------------------------------ 通用展示常量 */

/** 「行情不可得」的醒目标识（页面必须显示，不得隐藏） */
export const NO_MARKET_DATA_LABEL = '行情不可得';

/** ★★ 业务机制证据的时间边界声明（跨题材通用） */
export const BUSINESS_MECHANISM_CAVEAT =
  '★★ 业务机制证据来自**当前时点**公开资料 —— **不能确定该业务在事件当年的规模**，'
  + '也**不能**证明它是当次行情的驱动因素。'
  + '★★ **不因报道当日涨停、区间涨幅高或概念标签**就提升为直接相关。';

/** ★ 行情段的免责声明（跨题材通用） */
export const MARKET_PERFORMANCE_CAVEAT =
  '★ 以下为**事后行情描述**（区间涨跌 / 至高点 / 回撤 / 相对基准），'
  + '**不是** Campaign 的起止日期或峰值裁定。'
  + '★ 历史炒作参与证据与业务机制**仍须分别看待** —— '
  + '**不得**因个股上涨就提高其相关性等级。';

/** 参与者分类标签（跨题材通用） */
export const PARTICIPANT_CATEGORY_LABEL: Record<ParticipantCategory, string> = {
  MECHANISM_DIRECT: '直接机制相关',
  MARKET_PARTICIPANT: '历史市场参与者',
  SPILLOVER: '间接关联 / 扩散',
  COUNTER_EXAMPLE: '反例（不同轴）',
  INSUFFICIENT: '证据不足',
};

export const EVIDENCE_LEVEL_LABEL: Record<EvidenceLevel, string> = {
  REPORT_NAMED: '仅报道点名',
  BUSINESS_VERIFIED: '业务机制已核实',
};

export const EVENT_STUDY_LABEL: Record<string, string> = {
  HAS_PRICE_DATA: '有可分析行情',
  INSUFFICIENT_COVERAGE: '行情覆盖不足',
  NOT_COMPUTED: '该窗口未计算',
  NO_PRICE_DATA: '事件已核实但核心标的行情不可得',
  NOT_VERIFIED: '本轮未核实',
};

/* ------------------------------------------------------ 跨年份比较：展示常量 */

/**
 * ★★ 跨年份 outcome 码表 —— **必须用这套中文标签**；未知码**原样显示码值**，不得编造含义。
 */
export const CROSS_YEAR_OUTCOME_LABEL: Record<string, string> = {
  UP: '一致上涨',
  ALL_DOWN: '一致下跌',
  UNDERPERFORM: '整体跑输',
  DIVERGENT: '分化',
  NO_CLEAR_REACTION: '无明显反应',
  NO_EVENT: '无事件',
  INSUFFICIENT_DATA: '数据不足',
  WINDOW_MISMATCH: '窗口不符',
  NOT_COMPARABLE: '不可比',
};

/** 窗口口径（`window_basis`）中文标签；未知口径原样显示 */
export const WINDOW_BASIS_LABEL: Record<string, string> = {
  SEASON_WINDOW_9_1: '9 月–次年 1 月窗口',
  SEASON_WINDOW_5_7: '5–7 月窗口',
  CAMPAIGN_FULL_PERIOD: 'Campaign 全周期',
};

/** 窗口类型（`window_type`）中文标签；未知类型原样显示 */
export const WINDOW_TYPE_LABEL: Record<string, string> = {
  SEASON_WINDOW_9_1: '9–1 月窗口',
  SEASON_WINDOW_5_7: '5–7 月窗口',
  CAMPAIGN_FULL_PERIOD: 'Campaign 全周期',
};

/** ★★ 跨年比较区段必须显示的声明：只描述历史价格表现，不构成季节性结论 / 因果 */
export const CROSS_YEAR_CAVEAT =
  '★ 跨年比较只描述历史价格表现，不构成季节性结论，也不构成因果。';

/** 可比性标签（`comparable` 三态） */
export const COMPARABLE_LABEL: Record<string, string> = {
  true: '可比',
  partial: '部分可比',
  false: '不可比',
};

/* ------------------------------------------------------ 通用计算 */

export function hasMarketData(p: HistoricalParticipant): boolean {
  const m = p.market_data;
  return Boolean(m) && !m!.includes('无登记') && !m!.includes('无行情');
}

/* ------------------------------------------------------ 跨年份比较取值（仅字段名映射） */

function asRecord(v: unknown): Record<string, unknown> | null {
  return v !== null && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
}
function asStr(v: unknown): string | undefined {
  return typeof v === 'string' && v.length > 0 ? v : undefined;
}
function asNum(v: unknown): number | undefined {
  return typeof v === 'number' && Number.isFinite(v) ? v : undefined;
}
function asArr(v: unknown): unknown[] | null {
  return Array.isArray(v) ? v : null;
}
function asStrArr(v: unknown): string[] | undefined {
  const arr = asArr(v);
  if (!arr) return undefined;
  const out = arr.filter((x): x is string => typeof x === 'string' && x.length > 0);
  return out.length ? out : undefined;
}
/** `{date, close}` 取点（缺 close 时只保留 date；缺 date 时返回 undefined） */
function asPoint(date: unknown, close: unknown): { date: string; close?: number } | undefined {
  const d = asStr(date);
  if (!d) return undefined;
  const c = asNum(close);
  return c === undefined ? { date: d } : { date: d, close: c };
}
/** 原始首/末/高点：兼容 `{date, close}` 与 `high_date` + `high_close` 两种写法（仅字段名映射） */
function asHighPoint(r: Record<string, unknown>): { date: string; close?: number } | undefined {
  const nested = asRecord(r.high);
  if (nested) return asPoint(nested.date, nested.close);
  return asPoint(r.high_date, r.high_close);
}

function mapCrossSecurityPerf(raw: unknown): CrossYearSecurityPerf | null {
  const r = asRecord(raw);
  if (!r) return null;
  const first = asRecord(r.first);
  const last = asRecord(r.last);
  return {
    period_return_pct: asNum(r.period_return_pct),
    trading_days: asNum(r.trading_days),
    first: first ? asPoint(first.date, first.close) : undefined,
    last: last ? asPoint(last.date, last.close) : undefined,
    high: asHighPoint(r),
    to_high_pct: asNum(r.to_high_pct),
    max_drawdown_from_high_pct: asNum(r.max_drawdown_from_high_pct),
    excess_period_pp: asNum(r.excess_period_pp),
    excess_to_high_pp: asNum(r.excess_to_high_pp),
    status: asStr(r.status),
    note: asStr(r.note),
  };
}

function mapCrossBenchmarkPerf(raw: unknown, fallbackId: string): CrossYearBenchmarkPerf | null {
  const r = asRecord(raw);
  if (!r) return null;
  const first = asRecord(r.first);
  const last = asRecord(r.last);
  return {
    id: asStr(r.id) ?? fallbackId,
    label: asStr(r.label),
    trading_days: asNum(r.trading_days),
    first: first ? asPoint(first.date, first.close) : undefined,
    last: last ? asPoint(last.date, last.close) : undefined,
    high: asHighPoint(r),
    period_return_pct: asNum(r.period_return_pct),
    to_high_pct: asNum(r.to_high_pct),
    max_drawdown_from_high_pct: asNum(r.max_drawdown_from_high_pct),
  };
}

function mapCrossBySecurity(raw: unknown): Record<string, CrossYearSecurityPerf> | null {
  const r = asRecord(raw);
  if (!r) return null;
  const out: Record<string, CrossYearSecurityPerf> = {};
  for (const [sid, v] of Object.entries(r)) {
    const m = mapCrossSecurityPerf(v);
    if (m) out[sid] = m;
  }
  return Object.keys(out).length ? out : null;
}

/** 标的池：字符串原样用；数组（`{name, security_id}`）→ 拼成一行文本（仅字段名映射） */
function targetPoolText(v: unknown): string | undefined {
  const s = asStr(v);
  if (s) return s;
  const arr = asArr(v);
  if (!arr) return undefined;
  const names = arr
    .map((x) => {
      const r = asRecord(x);
      return r ? (asStr(r.name) ?? asStr(r.security_id)) : asStr(x);
    })
    .filter((x): x is string => Boolean(x));
  return names.length ? names.join(' · ') : undefined;
}

/**
 * ★ 源数据行里**可选**的窗口口径字段（**仅字段名映射**，缺就留空 —— 不猜、不补 0）。
 *
 * 这些字段由研究侧写入（如 `window_type` / `window` / `actual_window` / `coverage` /
 * `comparable` / `comparable_reason`）；Product **只消费**，不推导。
 */
function crossYearPassthrough(y: Record<string, unknown>): {
  window_type?: string; window?: [string, string] | null; actual_window?: [string, string] | null;
  coverage?: 'FULL' | 'PARTIAL' | 'NONE'; comparable?: boolean | 'partial'; comparable_reason?: string;
  in_window_event?: boolean; driver?: string;
} {
  const pair = (v: unknown): [string, string] | null => {
    const a = asArr(v);
    if (!a || a.length < 2) return null;
    const x = asStr(a[0]); const y2 = asStr(a[1]);
    return x && y2 ? [x, y2] : null;
  };
  const cov = asStr(y.coverage);
  const cmp = y.comparable;
  const iwe = y.in_window_event;
  return {
    window_type: asStr(y.window_type),
    window: pair(y.window),
    actual_window: pair(y.actual_window),
    coverage: cov === 'FULL' || cov === 'PARTIAL' || cov === 'NONE' ? cov : undefined,
    comparable: typeof cmp === 'boolean' || cmp === 'partial' ? cmp : undefined,
    comparable_reason: asStr(y.comparable_reason),
    // ★ 只透传布尔值；缺失 → undefined（**不得**默认 false，否则「未记录」会被读成「确认没有」）
    in_window_event: typeof iwe === 'boolean' ? iwe : undefined,
    driver: asStr(y.driver),
  };
}

/**
 * ★★ 从题材文档取出**跨年份比较**（规范形态）。
 *
 * 按优先级取值（**只做字段名映射**，不推导结论、不重算收益）：
 *  1. `doc.cross_year_comparison.years: CrossYearYear[]` → 规范形态，直接返回
 *  2. `doc.cross_year_comparison.yearly_5_7: []` → 归一化（电力）
 *  3. `doc.cross_year.years_summary: []` → 归一化（流感；**无 per-security 数值则留空**）
 *  4. 都没有 → `null`（页面**不渲染空壳**）
 *
 * ★ 归一化时的 `comparable` 规则：`outcome !== 'NO_EVENT' && outcome !== 'INSUFFICIENT_DATA'`
 *   —— 这是**映射规则**，不是研究判断。
 */
export function crossYearComparisonOf(doc: HistoricalEventsDoc): CrossYearComparison | null {
  const c = asRecord(doc.cross_year_comparison) ?? asRecord(doc.cross_year);
  if (!c) return null;

  // ① 规范形态
  if (Array.isArray(c.years)) {
    const canonical = c as unknown as CrossYearComparison;
    return { ...canonical, window_basis: asStr(c.window_basis) ?? '' };
  }

  const method = asRecord(c.method);

  // ② 电力：yearly_5_7
  const yearly = asArr(c.yearly_5_7);
  if (yearly) {
    const years: CrossYearYear[] = yearly.map((raw) => {
      const y = asRecord(raw) ?? {};
      const summer = asRecord(y.summer_5_7);
      const bench = summer ? mapCrossBenchmarkPerf(summer.benchmark, 'SH000300') : null;
      const campaign = asRecord(y.campaign_full);
      const outcome = asStr(y.outcome) ?? '';
      const notes: string[] = [];
      const own = asStr(y.note);
      if (own) notes.push(own);
      if (campaign) {
        notes.push('另有 Campaign 全周期口径（' + (asStr(campaign.label) ?? '未命名')
          + '），与 5–7 月窗口**不同口径，不可混用**。');
      }
      const passthrough = crossYearPassthrough(y);
      return {
        year: asNum(y.year) ?? 0,
        season_label: asStr(y.season_label),
        window_type: passthrough.window_type ?? 'SEASON_WINDOW_5_7',
        // ★ 源数据给出目标窗口日期时用源数据；未给出 → null（**不猜**）
        window: passthrough.window ?? null,
        actual_window: passthrough.actual_window ?? (bench?.first?.date && bench?.last?.date
          ? [bench.first.date, bench.last.date] : null),
        coverage: passthrough.coverage,
        event_type: asStr(y.event_type),
        mechanism: asStr(y.mechanism),
        in_window_event: passthrough.in_window_event,
        driver: passthrough.driver,
        outcome,
        comparable: passthrough.comparable
          ?? (outcome !== 'NO_EVENT' && outcome !== 'INSUFFICIENT_DATA'),
        comparable_reason: asStr(y.comparable_reason) ?? passthrough.comparable_reason,
        benchmark: bench,
        by_security: summer ? mapCrossBySecurity(summer.by_security) : null,
        note: notes.length ? notes.join(' ') : undefined,
        campaign_full: campaign ?? undefined,
      };
    });
    return {
      window_basis: 'SEASON_WINDOW_5_7',
      season_window: asStr(c.season_window) ?? asStr(asRecord(method?.window_definitions)?.summer_5_7),
      target_pool: targetPoolText(c.target_pool) ?? targetPoolText(method?.target_pool),
      inclusion_principle: asStr(method?.inclusion_principle),
      benchmark: asStr(asRecord(method?.benchmark)?.series_id),
      conclusion_short: asStr(c.conclusion),
      years,
      reading: asStr(c.reading),
      limitations: asStrArr(method?.known_limitations),
    };
  }

  // ③ 流感：years_summary（★ 源数据给出 per-security 数值时**直接消费**；未给出则留空）
  const summary = asArr(c.years_summary);
  if (summary) {
    const years: CrossYearYear[] = summary.map((raw) => {
      const y = asRecord(raw) ?? {};
      const cmp = y.comparable;
      const bench = mapCrossBenchmarkPerf(y.benchmark, 'SH000300');
      const passthrough = crossYearPassthrough(y);
      const noteBits = [asStr(y.note), asStr(y.driver)].filter(Boolean) as string[];
      return {
        year: asNum(y.year) ?? 0,
        season_label: asStr(y.season_label),
        window_type: passthrough.window_type ?? 'SEASON_WINDOW_9_1',
        window: passthrough.window ?? null,
        actual_window: passthrough.actual_window ?? null,
        coverage: passthrough.coverage,
        event_type: asStr(y.event_type),
        mechanism: asStr(y.mechanism),
        in_window_event: passthrough.in_window_event,
        driver: passthrough.driver,
        outcome: asStr(y.outcome) ?? '',
        comparable: typeof cmp === 'boolean' || cmp === 'partial' ? cmp : undefined,
        comparable_reason: asStr(y.comparable_reason) ?? passthrough.comparable_reason,
        benchmark: bench,
        by_security: mapCrossBySecurity(y.by_security),   // ★ 无则 null（页面显示缺失，**不补 0**）
        note: noteBits.length ? noteBits.join(' ') : undefined,
      };
    });
    const wd = asRecord(method?.window_definition);
    const conclusion = asRecord(c.conclusion);
    return {
      window_basis: 'SEASON_WINDOW_9_1',
      season_window: asStr(c.season_window) ?? asStr(wd?.external_window),
      target_pool: targetPoolText(c.target_pool) ?? targetPoolText(method?.target_pool),
      inclusion_principle: asStr(method?.inclusion_principle),
      conclusion_short: undefined,
      years,
      reading: asStr(c.reading),
      limitations: asStrArr(conclusion?.cannot_conclude),
    };
  }

  return null;
}

/* ------------------------------------------------------ 行情状态（四类，必须可验证区分） */

/**
 * ★★ 标的在某事件窗口的行情状态 —— **四类互斥**，不得用字符串推断。
 *
 * - `COMPUTED`      该窗口已完成计算（`by_security[sid]` 存在、`trading_days > 0`、覆盖率 ≥ 60%
 *                   **且窗口端点可达**）
 * - `NOT_COMPUTED`  该标的**有**行情登记，但**未在本事件窗口计算**（事件有 `market_performance` 但 `by_security` 无该 id）
 * - `UNAVAILABLE`   所需证券行情**确实不可得**（`market_data` 含「无登记」「无行情」，或 `by_security[sid].status === 'NO_DATA'`）
 * - `INSUFFICIENT`  数据存在但**覆盖不足**（交易日数量不足 **或** 窗口端点不可达）
 *
 * ★ `NOT_COMPUTED` 与 `UNAVAILABLE` 是**不同**的事：前者是「没算」，后者是「算不了」。
 * ★ 任何情况下都**不得**用 0 代表缺失数据。
 */
export type MarketDataStatus = 'COMPUTED' | 'NOT_COMPUTED' | 'UNAVAILABLE' | 'INSUFFICIENT';

/** 覆盖不足的判定阈值：窗口交易日的 60%（★ **只是数量阈值**，不等于「完整窗口已计算」） */
export const MARKET_DATA_COVERAGE_RATIO = 0.6;

/** ★ 窗口端点可达性的容差：窗口端点前后各 5 个交易日 */
export const MARKET_DATA_ENDPOINT_TOLERANCE_TRADING_DAYS = 5;

/** `market_data` 是否**显式**标注为不可得（★ 缺字段 ≠ 不可得，那是「未计算」） */
export function isMarketDataUnavailable(p: HistoricalParticipant | undefined): boolean {
  const m = p?.market_data;
  return Boolean(m) && (m!.includes('无登记') || m!.includes('无行情'));
}

/** 事件窗口的交易日数（以基准为准，缺基准则取窗口内最长标的） */
function windowTradingDays(mp: MarketPerformance | undefined): number {
  if (!mp) return 0;
  const bench = Object.values(mp.benchmark ?? {})[0]?.trading_days ?? 0;
  if (bench > 0) return bench;
  return Object.values(mp.by_security ?? {}).reduce((m, s) => Math.max(m, s.trading_days ?? 0), 0);
}

/**
 * ★★ 标的行情覆盖的**明细**（可验证、可展示）。
 *
 * ★ 设计要点：**「交易日数量」与「窗口端点可达性」分开判定** ——
 *   达到 60% 交易日数量**不等于**完整窗口已计算（例如中途停牌、尾部截断）。
 *   `reasons` 里必须能区分「交易日数量不足」与「窗口端点不可达」。
 * ★ 窗口端点来源：优先 `event.market_performance.window`；为 `null` 时回退用
 *   基准的 `first.date` / `last.date`（并在 `reasons` 里说明用了回退口径）。
 *   **不猜测**窗口日期。
 */
export interface MarketDataCoverage {
  status: MarketDataStatus;
  tradingDays: number;
  /** 窗口交易日数：以基准为准；基准缺失时取窗口内最长标的 */
  windowDays: number;
  /** `tradingDays / windowDays`（`windowDays = 0` 时为 0） */
  ratio: number;
  /** 首笔 ≤ 窗口起点 + 5 个交易日 **且** 末笔 ≥ 窗口终点 − 5 个交易日 */
  endpointsCovered: boolean;
  /** ★ 明确区分「交易日数量不足」与「窗口端点不可达」（也记录口径回退） */
  reasons: string[];
}

/** 按**交易日**（跳过周六日）平移日期；无法解析时返回 `null`（不猜日期） */
function shiftTradingDays(iso: string, n: number): string | null {
  const d = new Date(iso + 'T00:00:00Z');
  if (Number.isNaN(d.getTime())) return null;
  let remaining = Math.abs(n);
  const step = n < 0 ? -1 : 1;
  while (remaining > 0) {
    d.setUTCDate(d.getUTCDate() + step);
    const wd = d.getUTCDay();
    if (wd !== 0 && wd !== 6) remaining -= 1;
  }
  return d.toISOString().slice(0, 10);
}

interface WindowReference {
  start?: string; end?: string;
  /** 事件未登记 `window` → 用了基准首/末笔日期作为口径 */
  usedBenchmarkFallback: boolean;
  /** 窗口端点非基准交易日 → 按基准可达区间收窄 */
  narrowed: boolean;
}

/**
 * 窗口端点参照：优先 `window`；否则回退基准首/末笔。
 * ★ 若**基准自己**也到不了窗口端点（该端点不是交易日 / 全市场停牌），
 *   则把参照收窄到基准可达区间 —— 否则会把「全市场都没交易」误判成个股端点缺失。
 */
function windowReferenceOf(mp: MarketPerformance | undefined): WindowReference {
  if (!mp) return { usedBenchmarkFallback: false, narrowed: false };
  const bench = Object.values(mp.benchmark ?? {})[0];
  const bFirst = bench?.first?.date;
  const bLast = bench?.last?.date;
  let start = mp.window?.[0] ?? bFirst;
  let end = mp.window?.[1] ?? bLast;
  let narrowed = false;
  if (bFirst && start && bFirst > start) { start = bFirst; narrowed = true; }
  if (bLast && end && bLast < end) { end = bLast; narrowed = true; }
  return { start, end, usedBenchmarkFallback: !mp.window, narrowed };
}

/**
 * ★★ 标的在本事件窗口的**行情覆盖**（唯一判定入口）。
 *
 * 判定顺序（**端点与数量分开**）：
 *  1. 无 `by_security[sid]` → `isMarketDataUnavailable(p)` ? `UNAVAILABLE` : `NOT_COMPUTED`
 *  2. `status === 'NO_DATA'` / `trading_days <= 0` / `period_return_pct == null` → `UNAVAILABLE`
 *  3. `ratio < 60%` → `INSUFFICIENT`（reasons 记「交易日覆盖 x% < 60%」）
 *  4. `!endpointsCovered` → `INSUFFICIENT`（reasons 记「窗口端点不可达」）
 *  5. 否则 → `COMPUTED`
 */
export function marketDataCoverage(event: HistoricalEvent, securityId: string): MarketDataCoverage {
  const p = event.participants.find((x) => x.security_id === securityId);
  const mp = event.market_performance;
  const st = mp?.by_security?.[securityId];
  const windowDays = windowTradingDays(mp);

  // ① 无本窗口记录：显式不可得 → UNAVAILABLE；否则只是**没算** → NOT_COMPUTED
  if (!st) {
    return isMarketDataUnavailable(p)
      ? {
        status: 'UNAVAILABLE', tradingDays: 0, windowDays, ratio: 0, endpointsCovered: false,
        reasons: ['market_data 显式标注行情不可得（无登记 / 无行情）'],
      }
      : {
        status: 'NOT_COMPUTED', tradingDays: 0, windowDays, ratio: 0, endpointsCovered: false,
        reasons: ['该标的未出现在本事件窗口的 by_security 中（≠ 行情不可得）'],
      };
  }

  const tradingDays = st.trading_days ?? 0;
  const ratio = windowDays > 0 ? tradingDays / windowDays : 0;

  // ② 有记录但本窗口不可用
  if (st.status === 'NO_DATA' || tradingDays <= 0 || st.period_return_pct == null) {
    return {
      status: 'UNAVAILABLE', tradingDays, windowDays, ratio, endpointsCovered: false,
      reasons: ['本窗口无可用行情（status=NO_DATA / 交易日 ≤ 0 / 区间收益缺失）'],
    };
  }

  // ③ 窗口端点可达性（★ 与交易日数量阈值**分开**判定）
  const ref = windowReferenceOf(mp);
  const reasons: string[] = [];
  if (ref.usedBenchmarkFallback && ref.start && ref.end) {
    reasons.push(`事件未登记窗口，回退用基准首/末笔日期（${ref.start} ~ ${ref.end}）作为窗口口径`);
  }
  if (ref.narrowed) {
    reasons.push(`窗口端点非基准交易日，按基准可达区间收窄为（${ref.start ?? '—'} ~ ${ref.end ?? '—'}）`);
  }
  let endpointsCovered = true;
  const firstD = st.first?.date;
  const lastD = st.last?.date;
  if (!ref.start || !ref.end || !firstD || !lastD) {
    // ★ 端点数据缺失 → 不作「不可达」判定（无证据），但如实记录未校验
    reasons.push('首/末笔或窗口端点日期缺失，未校验端点可达性');
  } else {
    const startLimit = shiftTradingDays(ref.start, MARKET_DATA_ENDPOINT_TOLERANCE_TRADING_DAYS);
    const endLimit = shiftTradingDays(ref.end, -MARKET_DATA_ENDPOINT_TOLERANCE_TRADING_DAYS);
    if (startLimit && firstD > startLimit) {
      endpointsCovered = false;
      reasons.push(`窗口起点端点不可达（首笔 ${firstD}，晚于窗口起点 ${ref.start} 后 ${MARKET_DATA_ENDPOINT_TOLERANCE_TRADING_DAYS} 个交易日）`);
    }
    if (endLimit && lastD < endLimit) {
      endpointsCovered = false;
      reasons.push(`窗口终点端点不可达（末笔 ${lastD}，早于窗口终点 ${ref.end} 前 ${MARKET_DATA_ENDPOINT_TOLERANCE_TRADING_DAYS} 个交易日）`);
    }
  }

  // ④ 交易日数量阈值（★ 达到 60% **不等于**完整窗口已计算）
  if (ratio < MARKET_DATA_COVERAGE_RATIO) {
    reasons.push(`交易日覆盖 ${(ratio * 100).toFixed(0)}% < ${MARKET_DATA_COVERAGE_RATIO * 100}%`);
    return { status: 'INSUFFICIENT', tradingDays, windowDays, ratio, endpointsCovered, reasons };
  }
  if (!endpointsCovered) {
    return { status: 'INSUFFICIENT', tradingDays, windowDays, ratio, endpointsCovered, reasons };
  }
  return { status: 'COMPUTED', tradingDays, windowDays, ratio, endpointsCovered, reasons };
}

/** 标的级状态 = 覆盖明细的 `status`（★ 页面与测试都只经此入口） */
export function marketDataStatus(event: HistoricalEvent, securityId: string): MarketDataStatus {
  return marketDataCoverage(event, securityId).status;
}

/** ★ 四类状态的展示文案（页面必须显示，不得隐藏） */
export const MARKET_DATA_STATUS_LABEL: Record<MarketDataStatus, string> = {
  COMPUTED: '该窗口已计算',
  NOT_COMPUTED: '该窗口未计算',
  UNAVAILABLE: NO_MARKET_DATA_LABEL,
  INSUFFICIENT: '覆盖不足',
};

/** ★ 只看**本题材方向**标的（排除反例 / 证据不足）是否有行情登记 */
export function eventHasAnalysableData(e: HistoricalEvent): boolean {
  return e.participants.some((p) => isThemeParticipant(p) && hasMarketData(p));
}

/**
 * ★★ 事件级行情状态 —— **必须基于 `marketDataStatus(event, securityId)` 的实际结果**。
 *
 * ★ 不得再用 `market_data` 字符串推断：某标的**在别的时期**有行情，
 *   不代表它**在本事件窗口**被计算过（这正是旧实现的漏洞）。
 *
 * 判定顺序：
 *  1. 无参与标的 / 无催化 → `NOT_VERIFIED`
 *  2. 任一**合格标的**（`category !== 'INSUFFICIENT'`）为 `COMPUTED` → `HAS_PRICE_DATA`
 *  3. 否则任一为 `INSUFFICIENT` → `INSUFFICIENT_COVERAGE`
 *  4. 否则任一为 `NOT_COMPUTED` → `NOT_COMPUTED`
 *  5. 否则（全为 `UNAVAILABLE` / 无合格标的）→ `NO_PRICE_DATA`
 */
export function eventStudyState(e: HistoricalEvent): string {
  if (e.participants.length === 0 || e.catalysts.length === 0) return 'NOT_VERIFIED';
  const statuses = e.participants
    .filter((p) => isThemeParticipant(p))
    .map((p) => marketDataStatus(e, p.security_id));
  if (statuses.includes('COMPUTED')) return 'HAS_PRICE_DATA';
  if (statuses.includes('INSUFFICIENT')) return 'INSUFFICIENT_COVERAGE';
  if (statuses.includes('NOT_COMPUTED')) return 'NOT_COMPUTED';
  return 'NO_PRICE_DATA';
}

/** 按 `display.class_order` 分组（无该字段时按事件出现顺序） */
export function eventsByClass(
  doc: HistoricalEventsDoc, classOrder?: string[],
): { cls: string; label: string; caveat?: string; events: HistoricalEvent[] }[] {
  const order = classOrder ?? doc.event_classes?.map((c) => c.code) ?? [];
  const labelOf = (code: string) =>
    doc.event_classes?.find((c) => c.code === code)?.label ?? code;
  const caveats = (doc.display_caveats as Record<string, string> | undefined) ?? {};
  const known = order.length ? order : Array.from(new Set(doc.events.map((e) => e.event_class ?? 'UNCLASSIFIED')));
  return known
    .map((cls) => ({
      cls,
      label: labelOf(cls),
      caveat: caveats[cls],
      events: doc.events.filter((e) => (e.event_class ?? 'UNCLASSIFIED') === cls),
    }))
    .filter((g) => g.events.length > 0);
}

/* ------------------------------------------------------ 索引一致性校验 */

/**
 * ★ 最低限度的**索引 ↔ 题材文档**一致性校验。
 *
 * 检查项：
 *   1. `event_count` 与实际 `events` 数一致
 *   2. `external_entry_ids` 非空、条目内唯一、跨条目不重复
 *   3. `theme_id` 在注册表里有对应 doc
 *   4. `display` 必填字段齐全（title / aria_label / badge / note / class_order）
 */
export function validateEventMapIndex(
  index: EventMapIndex = eventMapIndex(),
  docs: Record<string, HistoricalEventsDoc> = DOCS,
): EventMapValidationIssue[] {
  const issues: EventMapValidationIssue[] = [];
  const push = (themeId: string | null, field: string, message: string) =>
    issues.push({ themeId, eventId: null, field, message });

  if (!Array.isArray(index.maps) || index.maps.length === 0) {
    push(null, 'maps', 'maps 缺失或为空'); return issues;
  }

  const usedEntryIds = new Set<string>();
  for (const m of index.maps) {
    const themeId = m.theme_id || null;
    if (!themeId) { push(null, 'theme_id', '缺少 theme_id'); continue; }

    // ③ theme_id → doc
    const doc = docs[themeId];
    if (!doc) push(themeId, 'theme_id', '注册表里没有对应题材文档: ' + themeId);

    // ② external_entry_ids
    // ★ v0.15：并非每个题材都有外部季节性对应线索。允许**显式声明**
    //   `external_link_status: 'NO_EXTERNAL_COUNTERPART'` 的题材留空；
    //   未声明而留空仍按问题处理（防止「忘了挂」被静默放过）。
    const ids = m.external_entry_ids;
    const optedOut = m.external_link_status === 'NO_EXTERNAL_COUNTERPART';
    if ((!Array.isArray(ids) || ids.length === 0) && !optedOut) {
      push(themeId, 'external_entry_ids',
        'external_entry_ids 为空（若确无外部对应线索，请在索引条目显式声明 '
        + 'external_link_status: NO_EXTERNAL_COUNTERPART）');
    } else if (Array.isArray(ids) && ids.length > 0) {
      const dup = Array.from(new Set(ids.filter((id, i) => ids.indexOf(id) !== i)));
      if (dup.length) push(themeId, 'external_entry_ids', 'external_entry_ids 条目内重复: ' + dup.join(','));
      for (const id of ids) {
        if (usedEntryIds.has(id)) push(themeId, 'external_entry_ids', '外部线索 ID 被多个题材占用: ' + id);
        else usedEntryIds.add(id);
      }
    }

    // ④ display 必填字段
    const d = m.display;
    if (!d) {
      push(themeId, 'display', '缺少 display');
    } else {
      for (const f of ['title', 'aria_label', 'badge', 'note'] as const) {
        if (!d[f]) push(themeId, 'display.' + f, 'display 缺必填字段: ' + f);
      }
      if (!Array.isArray(d.class_order) || d.class_order.length === 0) {
        push(themeId, 'display.class_order', 'display.class_order 为空');
      }
    }

    // ① event_count ↔ 实际事件数
    if (doc) {
      const actual = doc.events?.length ?? 0;
      if (m.event_count !== actual) {
        push(themeId, 'event_count', `event_count=${m.event_count} 与实际事件数 ${actual} 不一致`);
      }
    }
  }
  return issues;
}

/* ------------------------------------------------------ 通用校验 */

export interface EventMapValidationIssue {
  themeId: string | null;
  eventId: string | null;
  field: string;
  message: string;
}

const CATS: readonly string[] = ['MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'COUNTER_EXAMPLE', 'INSUFFICIENT'];
const LEVELS: readonly string[] = ['REPORT_NAMED', 'BUSINESS_VERIFIED'];

/** 题材无关的结构校验：必填、枚举、id 唯一、事件—标的自洽、事件类别必须显式 */
export function validateHistoricalEvents(
  doc: HistoricalEventsDoc, themeId: string | null = null,
): EventMapValidationIssue[] {
  const issues: EventMapValidationIssue[] = [];
  const push = (eventId: string | null, field: string, message: string) =>
    issues.push({ themeId, eventId, field, message });

  if (!doc.artifact_version) push(null, 'artifact_version', '缺少版本');
  if (!Array.isArray(doc.events) || doc.events.length === 0) {
    push(null, 'events', 'events 缺失或为空'); return issues;
  }
  const seen = new Set<string>();
  for (const e of doc.events) {
    if (!e.event_id) push(null, 'event_id', '事件缺少 event_id');
    else if (seen.has(e.event_id)) push(e.event_id, 'event_id', 'event_id 重复');
    else seen.add(e.event_id);

    if (!e.label) push(e.event_id, 'label', '缺少 label');
    if (!Number.isInteger(e.year)) push(e.event_id, 'year', 'year 非法');
    if (!e.window_text) push(e.event_id, 'window_text', '缺少 window_text');
    if (!e.evidence_basis) push(e.event_id, 'evidence_basis', '缺少 evidence_basis');
    // ★ 事件类别必须显式（归属正确是首要）
    if (!e.event_class) push(e.event_id, 'event_class', '★ 缺少 event_class（事件归属必须显式）');
    if (!Array.isArray(e.known_gaps) || e.known_gaps.length === 0) {
      push(e.event_id, 'known_gaps', '缺少 known_gaps（不确定性必须显式记录）');
    }

    const pids = new Set<string>();
    for (const p of e.participants ?? []) {
      if (!p.security_id) push(e.event_id, 'participants.security_id', '标的缺少 security_id');
      else if (pids.has(p.security_id)) push(e.event_id, 'participants.security_id', '同事件内标的重复: ' + p.security_id);
      else pids.add(p.security_id);
      if (!p.name) push(e.event_id, 'participants.name', '标的缺少 name');
      if (!p.ticker) push(e.event_id, 'participants.ticker', '标的缺少 ticker');
      if (!CATS.includes(p.category)) push(e.event_id, 'participants.category', '非法分类: ' + String(p.category));
      if (p.evidence_level && !LEVELS.includes(p.evidence_level)) {
        push(e.event_id, 'participants.evidence_level', '非法证据等级: ' + String(p.evidence_level));
      }
      if (!p.rationale || p.rationale.length < 4) {
        push(e.event_id, 'participants.rationale', '标的缺少纳入理由（不得仅凭标签纳入）');
      }
      if (!p.source) push(e.event_id, 'participants.source', '标的缺少来源');
      // ★ 业务机制证据必须带时间边界声明
      if (p.business_mechanism && !p.business_mechanism_caveat) {
        push(e.event_id, 'participants.business_mechanism_caveat', '有业务机制但缺时间边界声明: ' + p.name);
      }
    }
    for (const c of e.catalysts ?? []) {
      if (!c.date || !c.text || !c.source) push(e.event_id, 'catalysts', '催化事件缺 date/text/source');
    }
    if (e.market_performance && e.market_performance.is_campaign_ruling !== false) {
      push(e.event_id, 'market_performance.is_campaign_ruling', '★ 必须显式声明不是 Campaign 裁定');
    }
  }
  return issues;
}
