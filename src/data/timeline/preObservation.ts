/**
 * V1.8.2 提前观察区（Historical Pre-observation Window）。
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
 *   Pre-observation Window  →  Early Signal  →  Theme Formation
 * 若无 Early Signal：
 *   Pre-observation Window  →  Theme Formation
 *
 * 严格边界：
 *   - 纯 UI / Adapter 视图层：不落库、不改 src/models/、不改 schema / Research / Export Contract。
 *   - 只消费既有 TimelineCampaign（themes / lifecycle / early_signal / start）。
 *   - 判断不出来时不编造：无 start 则无提前观察区。
 */

import type { TimelineCampaign } from './timelineTypes';
import { addDaysISO } from '../../utils';

/**
 * 提前观察区宽度（自然日）。
 *
 * ⚠️ **仅为研究浏览缓冲（UI research buffer），不代表历史平均领先期。**
 * 这是 V1.8.2 的固定 UI buffer——**不是**历史规律结论、不是统计量、不是预测依据。
 * 若未来要改为由数据推导，必须先在 Research 侧产出口径，不得在本层臆造。
 */
export const historicalPreObservationDays = 30;

/** 提前观察区（[formation - N, formation) 半开区间，截止到形成前一天） */
export interface PreObservationWindow {
  /** 观察区起点（= 形成日 - historicalPreObservationDays） */
  start: string;
  /** 观察区终点（= 形成日前一天；不含形成日本身） */
  end: string;
  /** 观察区天数（恒为 historicalPreObservationDays） */
  days: number;
  /** 形成日（Campaign 起点 / 主题形成边界） */
  formation: string;
}

/** 主题形成的判定边界：优先 lifecycle 中最早的阶段起点，否则 Campaign.start */
export function themeFormationDate(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
): string {
  const stages = c.lifecycle ?? [];
  if (stages.length === 0) return c.start;
  // lifecycle 为按序阶段（start → end 内部覆盖不留空隙），取最早 start
  return stages.reduce((min, s) => (s.start < min ? s.start : min), stages[0].start);
}

/**
 * 计算某 Campaign / 主题的提前观察区。
 *
 * 说明：
 *   - formation 取 themeFormationDate()（lifecycle 最早起点，否则 Campaign.start）；
 *   - 观察区 = [formation - 30, formation - 1]（不含形成日本身，避免与 Campaign 主体重叠）；
 *   - 返回 null 仅当无法推导 start（不编造）。
 */
export function preObservationWindowOf(
  c: Pick<TimelineCampaign, 'start' | 'lifecycle'>,
): PreObservationWindow | null {
  const start = c.start;
  if (!start) return null;
  const formation = themeFormationDate(c) || start;
  const winStart = addDaysISO(formation, -historicalPreObservationDays);
  const winEnd = addDaysISO(formation, -1);
  return {
    start: winStart,
    end: winEnd,
    days: historicalPreObservationDays,
    formation,
  };
}

/**
 * 层级判定：给出该主题在时间轴上的三段式边界（供 UI 展示层级说明）。
 *
 *   pre-observation  →  (early signal?)  →  formation
 *
 * earlySignal 为导出既有字段（可为 null）；为 null 时退化为两段式。
 * 不编造 Early Signal。
 */
export interface PreObservationChain {
  preObservation: PreObservationWindow;
  /** 早期信号区间（导出既有；无则 null，退化为两段式） */
  earlySignal: { start: string; end: string; label?: string } | null;
  /** 主题形成日（= 观察区终点 + 1） */
  formation: string;
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
    hasEarlySignal: es !== null,
  };
}

/**
 * today 是否落在某主题的提前观察区内（供 Current Time Context 使用）。
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

/** 提前观察区的展示标签（UI 统一文案；禁止「买入区 / 布局区 / 信号区」） */
export const PRE_OBSERVATION_LABEL = '历史提前观察区';

/**
 * UI 说明文案（供渲染时直接取用，保证全站措辞一致）。
 * 必须包含「研究浏览缓冲 / 不代表历史平均领先期」的限定。
 */
export const PRE_OBSERVATION_HINT =
  '仅为研究浏览缓冲，不代表历史平均领先期，也不是买入建议。';
