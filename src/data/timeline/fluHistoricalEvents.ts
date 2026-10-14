/**
 * 历史流感事件地图 —— 只读适配器（产品侧）。
 *
 * ## 定位
 * 从季节性主题入口（外部参考）进入**历史事件**，再点进股票与事件细节。
 * ★ 与 `externalSeasonalCalendar` 的关系：日历给「外部参考窗口」，
 *   本模块给「ThreeC / 报道已核到的历史事件」。两者**不**互相证明。
 *
 * ## 硬边界（与数据文件一致）
 * - **历史炒作标的 ≠ 季节性研究股票池** —— 前者事后重建（可含领涨股），
 *   后者须跨年可比且含未上涨股。★ **不得**用前者单独证明季节性。
 * - 无行情的标的**如实显示缺失**，不展示为 0 涨幅、不补造数据。
 * - 报道是线索，不是结论；`INSUFFICIENT` 类标的作为反面参照留存。
 */
import eventsRaw from '@current/flu_historical_events_v0_1.json';

export type ParticipantCategory =
  | 'MECHANISM_DIRECT'
  | 'MARKET_PARTICIPANT'
  | 'SPILLOVER'
  | 'INSUFFICIENT';

export interface FluParticipant {
  security_id: string;
  ticker: string;
  name: string;
  category: ParticipantCategory;
  rationale: string;
  source: string;
  /** 库内行情覆盖；`null` 表示无登记/无行情 */
  market_data: string | null;
}

export interface FluEvent {
  event_id: string;
  label: string;
  year: number;
  window_text: string;
  external_window_ref: string | null;
  evidence_basis: string;
  catalysts: { date: string; text: string; source: string }[];
  participants: FluParticipant[];
  observed_performance: { note: string; by_security: Record<string, string> | null };
  known_gaps: string[];
}

export interface FluEventsDoc {
  artifact: string;
  artifact_version: string;
  position: string;
  participant_categories: { code: ParticipantCategory; label: string; meaning: string }[];
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

/** 该标的在库内**是否**有可分析行情（market_data 非 null 且非"无"） */
export function hasMarketData(p: FluParticipant): boolean {
  return Boolean(p.market_data) && !p.market_data!.includes('无登记') && !p.market_data!.includes('无行情');
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

/** 「行情不可得」的醒目标识（页面必须显示，不得隐藏） */
export const NO_MARKET_DATA_LABEL = '行情不可得';

/** 事件研究状态（用于页面分组） */
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
  + '历史炒作标的**不等于**季节性研究股票池，**不能**单独用于证明季节性。'
  + '行情不可得的标的如实标注，不补造数据。';

/* ------------------------------------------------------ 校验（供测试） */

export interface FluEventsValidationIssue {
  eventId: string | null;
  field: string;
  message: string;
}

const CATS: readonly string[] = ['MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'INSUFFICIENT'];

/** 结构校验：必填、枚举合法、id 唯一、事件—标的自洽 */
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
      if (!p.rationale || p.rationale.length < 4) {
        push(e.event_id, 'participants.rationale', '标的缺少纳入理由（不得仅凭标签纳入）');
      }
      if (!p.source) push(e.event_id, 'participants.source', '标的缺少来源');
      if (p.market_data == null) push(e.event_id, 'participants.market_data', '标的必须标注 market_data（可为 null 表示不可得）');
    }
    for (const c of e.catalysts ?? []) {
      if (!c.date || !c.text || !c.source) push(e.event_id, 'catalysts', '催化事件缺 date/text/source');
    }
  }
  return issues;
}
