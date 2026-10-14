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
import fluDoc from '@current/flu_historical_events_v0_4.json';
import powerDoc from '@current/power_historical_events_v0_1.json';
import mediaDoc from '@current/media_historical_events_v0_1.json';
import roboticsDoc from '@current/robotics_historical_events_v0_1.json';

/* ------------------------------------------------------ 通用类型 */

export type EventClassCode = string;

export type ParticipantCategory =
  | 'MECHANISM_DIRECT'
  | 'MARKET_PARTICIPANT'
  | 'SPILLOVER'
  | 'INSUFFICIENT';

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
  excess_to_high_pp?: number;
  business_mechanism?: string;
  business_mechanism_caveat?: string;
}

export interface SecurityPerformance {
  status?: string;
  trading_days?: number;
  first?: { date: string; close: number };
  last?: { date: string; close: number };
  high?: { date: string; close: number };
  low?: { date: string; close: number };
  period_return_pct?: number;
  to_high_pct?: number;
  max_drawdown_from_high_pct?: number;
  excess_to_high_pp?: number;
  excess_period_pp?: number;
}

export interface MarketPerformance {
  window: [string, string] | null;
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
    campaign_id: string;
    start: string | null;
    peak_date: string | null;
    end: string | null;
    note?: string;
  };
  catalysts: { date: string; text: string; source: string; note?: string }[];
  phases?: { phase_id: string; phase_type: string; start: string; end: string; description: string }[];
  participants: HistoricalParticipant[];
  observed_performance: {
    note: string;
    by_security: Record<string, string> | null;
    reported_same_day_moves?: Record<string, string>;
  };
  market_performance?: MarketPerformance;
  known_gaps: string[];
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
  corrections?: { at: string; what: string; why: string; source?: string; note?: string }[];
  event_classes?: { code: string; label: string; meaning: string }[];
  events: HistoricalEvent[];
  [k: string]: unknown;
}

export interface EventMapIndexEntry {
  theme_id: string;
  label: string;
  file: string;
  external_entry_ids: string[];
  display: ThemeDisplay;
  event_count?: number;
  status?: string;
}

interface EventMapIndex {
  artifact: string;
  artifact_version: string;
  maps: EventMapIndexEntry[];
  not_included?: { items: { theme_id: string; label: string; reason: string }[] };
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
  INSUFFICIENT: '证据不足 / 反面参照',
};

export const EVIDENCE_LEVEL_LABEL: Record<EvidenceLevel, string> = {
  REPORT_NAMED: '仅报道点名',
  BUSINESS_VERIFIED: '业务机制已核实',
};

export const EVENT_STUDY_LABEL: Record<string, string> = {
  HAS_PRICE_DATA: '有可分析行情',
  NO_PRICE_DATA: '事件已核实但核心标的行情不可得',
  NOT_VERIFIED: '本轮未核实',
};

/* ------------------------------------------------------ 通用计算 */

export function hasMarketData(p: HistoricalParticipant): boolean {
  const m = p.market_data;
  return Boolean(m) && !m!.includes('无登记') && !m!.includes('无行情');
}

/** ★ 只看**非 INSUFFICIENT** 的标的是否有行情（INSUFFICIENT 有行情≠参与证据） */
export function eventHasAnalysableData(e: HistoricalEvent): boolean {
  return e.participants.some((p) => p.category !== 'INSUFFICIENT' && hasMarketData(p));
}

export function eventStudyState(e: HistoricalEvent): string {
  if (e.participants.length === 0 || e.catalysts.length === 0) return 'NOT_VERIFIED';
  return eventHasAnalysableData(e) ? 'HAS_PRICE_DATA' : 'NO_PRICE_DATA';
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

/* ------------------------------------------------------ 通用校验 */

export interface EventMapValidationIssue {
  themeId: string | null;
  eventId: string | null;
  field: string;
  message: string;
}

const CATS: readonly string[] = ['MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'INSUFFICIENT'];
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
