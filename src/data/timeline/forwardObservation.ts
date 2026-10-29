/**
 * 当前前瞻观察（Forward Observation）—— 产品侧只读读取器（v0.33）。
 *
 * ★ 这一层回答的是「**以 as_of 为观察时点，历史上哪些重复模式值得现在就开始看**」，
 *   不是「明天买什么」：产物里没有评分、没有排序、没有目标价。
 *
 * ★★ 三条硬规则（与产物一致，页面不得改写）：
 *   1. 所有窗口/超额都是**价格结果**，不证明因果；「历史响应」≠「未来会涨」；
 *   2. 候选的 `evidence_status` 决定它能说多重的话：
 *      `PRE_OBSERVATION`（前置观察）/ `ALREADY_WARM`（已升温，**不得**当作提前发现）/
 *      `INSUFFICIENT`（证据不足）/ `WATCH_ONLY`（事件驱动，无时间优势）；
 *   3. 概念成分与证券名称都是**当前快照**回溯，存在幸存者/成分变更偏差（产物已逐条写）。
 */
// ★ v0.33.1：v0_2 —— 三段口径（pre / event_day / post5·10·20）+ 事件阶段 + 数据新鲜度
// ★ v0.59：v0_3 修正 `current_performance` 口径（基准按参与者同段日期对齐、
//   `price_as_of` = 实际参与序列最早末日、剔除落后 >5 个交易日的参与者）
// ★ v0.60：v0_4 = 行情刷新到 2026-10-29（口径仍 v0_3，未变）
import raw from '@current/forward_observation_v0_4.json';

export type EvidenceStatus = 'PRE_OBSERVATION' | 'ALREADY_WARM' | 'INSUFFICIENT' | 'WATCH_ONLY'
  | 'DATA_STALE' | 'UNKNOWN';
export type PatternStatus = 'A_REPEATED' | 'B_REPEATED' | 'C_EXPLORATORY';

export interface PatternStats {
  occurrence_count: number;
  response_count: number;
  response_rate: number | null;
  median_lead_days: number | null;
  median_pre_excess_pct?: number | null;
  median_post_excess_pct?: number | null;
  sample_years: number[];
  testable_years?: number[];
  not_testable_years?: number[];
}

export interface ForwardPattern {
  pattern_id: string;
  family: string;
  title: string;
  hypothesis: string;
  status: PatternStatus;
  status_reason?: string;
  stats: PatternStats;
  known_biases: string[];
  years?: {
    year: number; animal: string; lunar_new_year: string; name_matches: number;
    testable: boolean; why_not_testable?: string | null;
    window?: { status?: string; responded?: boolean; median_excess_pct?: number; breadth?: number;
      pre_median_excess_pct?: number | null; post_median_excess_pct?: number | null;
      limit_up_days_total?: number; window?: [string, string] } | null;
    lead_days?: number | null;
  }[];
  events?: {
    event_id: string; event_date: string; published_at: string; label: string; category: string;
    responded?: boolean; lead_days?: number | null;
    window?: { status?: string; median_excess_pct?: number; breadth?: number;
      pre_median_excess_pct?: number | null; post_median_excess_pct?: number | null } | null;
  }[];
  basket?: { concept: string; members: number; members_with_data: number; membership_bias: string };
}

export interface ForwardCandidate {
  candidate_id: string;
  title: string;
  window: { start: string | null; peak: string | null; end: string | null };
  why_now: string;
  evidence_status: EvidenceStatus;
  historical_stats?: Record<string, unknown>;
  current_performance?: { participants_with_data?: number; participants_total?: number;
    stale_participants?: number; median_20d_excess_pct?: number; breadth_20d?: number;
    /** ★ v0_3：实际参与计算的序列中**最早的末日**（不是全库最大值） */
    price_as_of?: string | null; stale?: boolean; stale_note?: string | null;
    /** ★ v0_3：参与者 20 日窗口的并集（基准按每只参与者自己的这段日期对齐） */
    participants_window?: [string, string] | null;
    stale_participants_note?: string | null } | null;
  what_to_watch?: string;
  invalidate_if?: string;
  not_a_candidate_reason?: string;
  fact_vs_assumption?: { fact?: string; assumption?: string };
}

export interface ForwardDoc {
  artifact: string;
  artifact_version: string;
  as_of: string;
  as_of_source: string;
  data_sources: { id: string; used_for: string; status: string; note?: string; endpoint?: string }[];
  benchmark: { series_id: string; name: string; close: number; ret_5d: number | null; ret_10d: number | null; ret_20d: number | null; ret_60d: number | null };
  indices: { series_id: string; name: string; close: number; ret_5d: number | null; ret_20d: number | null; ret_60d: number | null }[];
  sector_scan: { boards_scanned: number; source: string; as_of_note: string; top_20d: { name: string; ret_20d: number; ret_60d: number }[]; bottom_20d: { name: string; ret_20d: number }[] };
  seasonal_windows?: { criterion: string; themes: { theme_id: string; label: string; occurrence_count: number; projected_window: [string, string]; as_of_inside: boolean; current_performance: { median_20d_excess_pct?: number; breadth_20d?: number; participants_with_data?: number } | null }[] };
  patterns: ForwardPattern[];
  candidates: ForwardCandidate[];
  limitations: string[];
}

const doc = raw as unknown as ForwardDoc;

export const FORWARD_OBSERVATION = doc;
export const FORWARD_AS_OF = doc.as_of;
export const FORWARD_ARTIFACT_VERSION = doc.artifact_version;

export const PATTERN_STATUS_LABEL: Record<PatternStatus, string> = {
  A_REPEATED: 'A · 重复性较强',
  B_REPEATED: 'B · 有重复迹象',
  C_EXPLORATORY: 'C · 探索线索',
};

export const EVIDENCE_STATUS_LABEL: Record<EvidenceStatus, string> = {
  PRE_OBSERVATION: '前置观察（窗口未走完、尚未升温）',
  ALREADY_WARM: '已升温（不是提前发现）',
  INSUFFICIENT: '证据不足（不可执行）',
  WATCH_ONLY: '事件驱动（当前无时间优势）',
  DATA_STALE: '数据陈旧（无法确认当前状态）',
  UNKNOWN: '状态未知（缺当前行情）',
};

/** ★ 只有 PRE_OBSERVATION 才允许被页面说成「现在可以看」 */
export function actionableCandidates(): ForwardCandidate[] {
  return doc.candidates.filter((c) => c.evidence_status === 'PRE_OBSERVATION');
}

export function patternById(id: string): ForwardPattern | null {
  return doc.patterns.find((p) => p.pattern_id === id) ?? null;
}
