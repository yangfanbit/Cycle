/**
 * 历史流感事件地图 —— 只读适配器（产品侧）。
 *
 * ## 定位
 * 从季节性主题入口（外部参考）进入**历史事件**，再点进股票与事件细节。
 * ★ 与 `externalSeasonalCalendar` 的关系：日历给「外部参考窗口」，
 *   本模块给「报道已核到的历史事件」。两者**不**互相证明。
 *
 * ## 硬边界（与数据文件一致）
 * - **历史炒作标的 ≠ 季节性研究股票池**。
 * - ★★ **事件归属必须正确**：`ADJACENT_PUBLIC_HEALTH`（超级真菌 / 不明原因肺炎）
 *   是**邻近传染病**事件，**不得**作为流感季节性的支持证据。
 * - ★ `evidence_level = REPORT_NAMED` 仅证明「是历史市场参与者」，
 *   **不**证明业务与事件机制相关（联环药业对耳念珠菌的澄清即是反例）。
 * - 无行情的标的**如实显示缺失**，不展示为 0 涨幅、不补造数据。
 */
import eventsRaw from '@current/flu_historical_events_v0_2.json';

export type ParticipantCategory =
  | 'MECHANISM_DIRECT'
  | 'MARKET_PARTICIPANT'
  | 'SPILLOVER'
  | 'INSUFFICIENT';

/** ★ 事件类别：直接流感 vs 邻近传染病（不得混为一谈） */
export type EventClass = 'FLU_DIRECT' | 'ADJACENT_PUBLIC_HEALTH';

/** ★ 证据等级：仅报道点名 vs 业务机制已核实 */
export type EvidenceLevel = 'REPORT_NAMED' | 'BUSINESS_VERIFIED';

export interface FluParticipant {
  security_id: string;
  ticker: string;
  name: string;
  exchange?: string;
  category: ParticipantCategory;
  evidence_level?: EvidenceLevel;
  /** 报道当日的涨幅描述（若有） */
  reported_move?: string;
  rationale: string;
  source: string;
  note?: string;
  /** 库内行情覆盖；`undefined`/含「无」表示不可得 */
  market_data?: string;
}

export interface FluEvent {
  event_id: string;
  event_class?: EventClass;
  label: string;
  year: number;
  window_text: string;
  external_window_ref: string | null;
  evidence_basis: string;
  study_state?: string;
  media_label_note?: string;
  catalysts: { date: string; text: string; source: string; note?: string }[];
  participants: FluParticipant[];
  observed_performance: {
    note: string;
    by_security: Record<string, string> | null;
    reported_same_day_moves?: Record<string, string>;
  };
  known_gaps: string[];
}

export interface FluEventsDoc {
  artifact: string;
  artifact_version: string;
  supersedes?: string;
  position: string;
  corrections?: { at: string; what: string; why: string; source?: string; note?: string }[];
  event_classes?: { code: EventClass; label: string; meaning: string }[];
  events: FluEvent[];
  concept_index_availability: Record<string, unknown>;
  research_pool_note: Record<string, string>;
}

export function fluEventsDoc(): FluEventsDoc {
  return eventsRaw as unknown as FluEventsDoc;
}

export function fluEvents(): FluEvent[] {
  return fluEventsDoc().events;
}

export function fluEventById(id: string): FluEvent | undefined {
  return fluEvents().find((e) => e.event_id === id);
}

/** 按事件类别分组（直接流感 / 邻近传染病） */
export function fluEventsByClass(): { cls: EventClass; events: FluEvent[] }[] {
  const order: EventClass[] = ['FLU_DIRECT', 'ADJACENT_PUBLIC_HEALTH'];
  const all = fluEvents();
  return order
    .map((cls) => ({ cls, events: all.filter((e) => (e.event_class ?? 'FLU_DIRECT') === cls) }))
    .filter((g) => g.events.length > 0);
}

/** 该标的在库内**是否**有可分析行情 */
export function hasMarketData(p: FluParticipant): boolean {
  const m = p.market_data;
  return Boolean(m) && !m!.includes('无登记') && !m!.includes('无行情');
}

/**
 * ★ 事件的「可分析行情」只看**非 INSUFFICIENT** 的标的是否有行情。
 *   （`INSUFFICIENT` = 有行情但无同期参与证据，**不得**当作该事件的表现证据。）
 */
export function eventHasAnalysableData(e: FluEvent): boolean {
  return e.participants.some((p) => p.category !== 'INSUFFICIENT' && hasMarketData(p));
}

export const PARTICIPANT_CATEGORY_LABEL: Record<ParticipantCategory, string> = {
  MECHANISM_DIRECT: '直接机制相关',
  MARKET_PARTICIPANT: '历史市场参与者',
  SPILLOVER: '间接关联 / 扩散',
  INSUFFICIENT: '证据不足 / 反面参照',
};

export const EVENT_CLASS_LABEL: Record<EventClass, string> = {
  FLU_DIRECT: '直接流感相关',
  ADJACENT_PUBLIC_HEALTH: '邻近传染病 / 公共卫生事件',
};

export const EVIDENCE_LEVEL_LABEL: Record<EvidenceLevel, string> = {
  REPORT_NAMED: '仅报道点名',
  BUSINESS_VERIFIED: '业务机制已核实',
};

/** ★ 邻近传染病事件的免责声明（页面必须显示） */
export const ADJACENT_EVENT_CAVEAT =
  '★ 本事件**不是流感**机制。可用于研究「市场如何交易公共卫生新闻」，'
  + '**不得**作为流感季节性的支持证据。';

/** 「行情不可得」的醒目标识（页面必须显示，不得隐藏） */
export const NO_MARKET_DATA_LABEL = '行情不可得';

export type EventStudyState = 'HAS_PRICE_DATA' | 'NO_PRICE_DATA' | 'NOT_VERIFIED';

export function eventStudyState(e: FluEvent): EventStudyState {
  if (e.participants.length === 0 || e.catalysts.length === 0) return 'NOT_VERIFIED';
  return eventHasAnalysableData(e) ? 'HAS_PRICE_DATA' : 'NO_PRICE_DATA';
}

export const EVENT_STUDY_LABEL: Record<EventStudyState, string> = {
  HAS_PRICE_DATA: '有可分析行情',
  NO_PRICE_DATA: '事件已核实但核心标的行情不可得',
  NOT_VERIFIED: '本轮未核实',
};

export const FLU_EVENTS_NOTE =
  '本区展示**历史事件**的事后重建（来源：同期报道 + 库内 Campaign）。'
  + '★ 事件按**机制**分类：直接流感相关 vs 邻近传染病（后者不得用于支持流感季节性）。'
  + '历史炒作标的**不等于**季节性研究股票池；「仅报道点名」**不**证明业务机制相关。'
  + '行情不可得的标的如实标注，不补造数据。';

/* ------------------------------------------------------ 校验（供测试） */

export interface FluEventsValidationIssue {
  eventId: string | null;
  field: string;
  message: string;
}

const CATS: readonly string[] = ['MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'INSUFFICIENT'];
const CLASSES: readonly string[] = ['FLU_DIRECT', 'ADJACENT_PUBLIC_HEALTH'];
const LEVELS: readonly string[] = ['REPORT_NAMED', 'BUSINESS_VERIFIED'];

/** 结构校验：必填、枚举合法、id 唯一、事件—标的自洽、★ 事件类别必须显式 */
export function validateFluEvents(doc: FluEventsDoc): FluEventsValidationIssue[] {
  const issues: FluEventsValidationIssue[] = [];
  const push = (eventId: string | null, field: string, message: string) =>
    issues.push({ eventId, field, message });

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
    // ★ 事件类别必须显式（归属正确是本文件的第一要务）
    if (!e.event_class) push(e.event_id, 'event_class', '★ 缺少 event_class（事件归属必须显式）');
    else if (!CLASSES.includes(e.event_class)) {
      push(e.event_id, 'event_class', '非法事件类别: ' + String(e.event_class));
    }
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
      if (!CATS.includes(p.category)) {
        push(e.event_id, 'participants.category', '非法分类: ' + String(p.category));
      }
      if (p.evidence_level && !LEVELS.includes(p.evidence_level)) {
        push(e.event_id, 'participants.evidence_level', '非法证据等级: ' + String(p.evidence_level));
      }
      if (!p.rationale || p.rationale.length < 4) {
        push(e.event_id, 'participants.rationale', '标的缺少纳入理由（不得仅凭标签纳入）');
      }
      if (!p.source) push(e.event_id, 'participants.source', '标的缺少来源');
    }
    for (const c of e.catalysts ?? []) {
      if (!c.date || !c.text || !c.source) push(e.event_id, 'catalysts', '催化事件缺 date/text/source');
    }
  }
  return issues;
}
