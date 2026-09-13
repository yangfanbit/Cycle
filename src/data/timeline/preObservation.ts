/**
 * V1.8.2 / V1.8.2.1 提前观察参考区（Historical Pre-observation Reference Window）。
 *
 * 语义（必须严格遵守）：
 *   「历史上，在主题正式形成前，可以开始关注该方向的时间缓冲区。」
 *
 *   ✗ 不是预测（「N 天后大概率上涨」）
 *   ✗ 不是买入建议（「建议提前 N 天布局」/「最佳埋伏时间」）
 *   ✗ 不是未来信号
 *   ✗ 不是历史统计事实（30 天不是历史平均领先期）
 *
 * 层级（若导出有 Early Signal 则形成清晰三层）：
 *   Pre-observation Reference Window  →  Early Signal  →  Theme Formation  →  Main Rise
 * 若无 Early Signal：
 *   Pre-observation Reference Window  →  Theme Formation
 *
 * 严格边界：
 *   - 纯 UI / Adapter 视图层：不落库、不改 src/models/、不改 schema / Research / Export Contract。
 *   - 只消费既有 TimelineCampaign（themes / lifecycle / early_signal / start）。
 *   - 判断不出来时不编造：无 start 则无提前观察参考区。
 */

import type { TimelineCampaign } from './timelineTypes';
import { addDaysISO } from '../../utils';

/**
 * 提前观察参考区宽度（自然日）。
 *
 * ⚠️ **仅为研究浏览参考（UI / Research browsing buffer），不代表历史平均领先期。**
 * 这是固定 UI buffer——**不是**历史规律结论、不是统计量、不是预测依据、不是买入时间。
 * 若未来要改为由数据推导，必须先在 Research 侧产出口径，不得在本层臆造。
 */
export const historicalPreObservationDays = 30;

/** 主题形成的 stage 名称（Research 层枚举，见 ExportLifecycleStageV1）。 */
const STAGE_THEME_FORMING = 'THEME_FORMING';
const STAGE_BROAD_CONFIRMATION = 'BROAD_CONFIRMATION';

/** 提前观察参考区（[formation - N, formation) 半开区间，截止到形成前一天） */
export interface PreObservationWindow {
  /** 参考区起点（= 形成日 - historicalPreObservationDays） */
  start: string;
  /** 参考区终点（= 形成日前一天；不含形成日本身） */
  end: string;
  /** 参考区天数（恒为 historicalPreObservationDays） */
  days: number;
  /** 形成日（主题形成边界） */
  formation: string;
  /**
   * 形成日锚点来源，便于 UI / 测试核对口径：
   *   'THEME_FORMING'       → 来自 lifecycle 的 THEME_FORMING.start
   *   'BROAD_CONFIRMATION'  → 无 THEME_FORMING 时退化为 BROAD_CONFIRMATION.start
   *   'campaign_start'      → 两者皆无时退化为 Campaign.start
   */
  formationAnchor: 'THEME_FORMING' | 'BROAD_CONFIRMATION' | 'campaign_start';
}

/**
 * 主题形成锚点（Formation Anchor）。
 *
 * ⚠️ 关键语义修正（V1.8.2.1）：**不得**取 lifecycle 最早阶段——lifecycle 通常以
 * EARLY_SIGNAL 开头，取最早值会把「早期信号」误当成「主题形成」。
 *
 * 优先级：
 *   1. lifecycle.stage === 'THEME_FORMING' → 该 stage.start
 *   2. 否则 lifecycle.stage === 'BROAD_CONFIRMATION' → 该 stage.start
 *   3. 否则 Campaign.start
 *   4. 都没有 → null（无法计算，不编造）
 */
export function themeFormationDate(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
): string | null {
  const stages = c.lifecycle ?? [];
  const themeForming = stages.find((s) => s.stage === STAGE_THEME_FORMING);
  if (themeForming?.start) return themeForming.start;
  const broadConfirmation = stages.find((s) => s.stage === STAGE_BROAD_CONFIRMATION);
  if (broadConfirmation?.start) return broadConfirmation.start;
  return c.start || null;
}

/** 形成锚点来源判定（与 themeFormationDate 口径一致，供 UI / 测试使用）。 */
export function formationAnchorOf(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
): PreObservationWindow['formationAnchor'] | null {
  const stages = c.lifecycle ?? [];
  if (stages.find((s) => s.stage === STAGE_THEME_FORMING)?.start) return STAGE_THEME_FORMING;
  if (stages.find((s) => s.stage === STAGE_BROAD_CONFIRMATION)?.start)
    return STAGE_BROAD_CONFIRMATION;
  if (c.start) return 'campaign_start';
  return null;
}

/**
 * 计算某 Campaign / 主题的提前观察参考区。
 *
 * 说明：
 *   - formation 取 themeFormationDate()（THEME_FORMING → BROAD_CONFIRMATION → Campaign.start）；
 *   - 参考区 = [formation - 30, formation - 1]（不含形成日本身，避免与 Campaign 主体重叠）；
 *   - 返回 null 仅当无法推导 formation（不编造）。
 */
export function preObservationWindowOf(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
): PreObservationWindow | null {
  const formation = themeFormationDate(c);
  const anchor = formationAnchorOf(c);
  if (!formation || !anchor) return null;
  const winStart = addDaysISO(formation, -historicalPreObservationDays);
  const winEnd = addDaysISO(formation, -1);
  return {
    start: winStart,
    end: winEnd,
    days: historicalPreObservationDays,
    formation,
    formationAnchor: anchor,
  };
}

/**
 * 层级判定：给出该主题在时间轴上的三段式边界（供 UI 展示层级说明）。
 *
 *   pre-observation reference  →  (early signal?)  →  formation  →  main rise
 *
 * earlySignal 为导出既有字段（可为 null）；为 null 时退化为两段式。
 * 不编造 Early Signal。**Early Signal 与 Formation 是两个独立边界**，
 * 不得把 Early Signal 当作 Formation（见 themeFormationDate 的锚点规则）。
 */
export interface PreObservationChain {
  preObservation: PreObservationWindow;
  /** 早期信号区间（导出既有；无则 null，退化为两段式） */
  earlySignal: { start: string; end: string; label?: string } | null;
  /** 主题形成日（= 参考区终点 + 1） */
  formation: string;
  /** 形成锚点来源（THEME_FORMING / BROAD_CONFIRMATION / campaign_start） */
  formationAnchor: PreObservationWindow['formationAnchor'];
  /** 是否为三段式（含早期信号） */
  hasEarlySignal: boolean;
}

export function preObservationChainOf(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle' | 'early_signal'>,
): PreObservationChain | null {
  const win = preObservationWindowOf(c);
  if (!win) return null;
  const es = c.early_signal ?? null;
  return {
    preObservation: win,
    earlySignal: es
      ? { start: es.start, end: es.end, ...(es.label ? { label: es.label } : {}) }
      : null,
    formation: win.formation,
    formationAnchor: win.formationAnchor,
    hasEarlySignal: es !== null,
  };
}

/**
 * today 是否落在某主题的提前观察参考区内（供 Current Time Context 使用）。
 * 语义严格为「历史研究位置」，调用方必须同时展示「不代表本年度预测」的限定语。
 */
export function isInPreObservation(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
  today: string,
): boolean {
  const win = preObservationWindowOf(c);
  if (!win) return false;
  return win.start <= today && today <= win.end;
}

/** 提前观察参考区的展示标签（UI 统一文案；禁止「买入区 / 布局区 / 信号区」） */
export const PRE_OBSERVATION_LABEL = '提前观察参考区';

/**
 * UI 说明文案（供渲染时直接取用，保证全站措辞一致）。
 * 必须包含「研究浏览参考 / 不代表历史平均领先期」的限定。
 */
export const PRE_OBSERVATION_HINT =
  '仅用于研究浏览参考，不代表历史平均领先期，也不是买入建议。';
