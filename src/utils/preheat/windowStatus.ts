import type { TimeWindow } from '../../models';
import {
  addDaysISO,
  compareISO,
  dayOfYearISO,
  daysInYear,
  isCrossYearMD,
  mdToISO,
  parseISO,
} from '../date/dateUtils';

/** 窗口相位 */
export type WindowPhase = 'NOT_ACTIVE' | 'PRE_HEAT' | 'ACTIVE' | 'ENDED';

/** 一条规律窗口在具体"季节年"下的实例 */
export interface WindowOccurrence {
  /** 季节起始年。跨年窗口 2026-11-01→2027-01-15 的 seasonYear = 2026 */
  seasonYear: number;
  start: string; // ISO
  end: string;   // ISO
  preheatStart: string; // ISO = start - preheat_days
  crossYear: boolean;
}

/**
 * 将 TimeWindow 实例化为某个季节年的具体日期范围。
 * - calendar / empirical（带 md）：直接计算；end_md < start_md 视为跨年。
 * - relative_event：通过 resolveAnchor 解析锚点后加偏移，跨年与否由实际日期决定。
 * 无法计算的窗口（经验窗口缺 md、锚点缺失等）返回 null，由 UI 用文字展示。
 */
/** 锚点事件日期解析器：由调用方注入，避免 utils 依赖具体数据 */
export type AnchorResolver = (eventId: string, seasonYear: number) => string | null;

export function occurrenceForSeason(
  window: TimeWindow,
  seasonYear: number,
  resolveAnchor?: AnchorResolver,
): WindowOccurrence | null {
  let start: string;
  let end: string;

  if (window.window_type === 'relative_event') {
    // 相对事件窗口：解析锚点日期后加偏移；是否跨年由实际日期决定，
    // 天然支持"春节前→春节后"等任意跨年形态，不写死某类跨年逻辑。
    if (!window.anchor_event || !resolveAnchor) return null;
    if (window.start_offset_days == null || window.end_offset_days == null) return null;
    const anchor = resolveAnchor(window.anchor_event, seasonYear);
    if (!anchor) return null;
    start = addDaysISO(anchor, window.start_offset_days);
    end = addDaysISO(anchor, window.end_offset_days);
  } else {
    if (!window.start_md || !window.end_md) return null;
    start = mdToISO(window.start_md, seasonYear);
    const cross = isCrossYearMD(window.start_md, window.end_md);
    end = mdToISO(window.end_md, cross ? seasonYear + 1 : seasonYear);
  }

  return {
    seasonYear,
    start,
    end,
    preheatStart: addDaysISO(start, -window.preheat_days),
    crossYear: parseISO(end).y > parseISO(start).y,
  };
}

export interface WindowStatusResult {
  phase: WindowPhase;
  occurrence: WindowOccurrence;
  /** 距窗口开始天数（未来窗口为正，已开始为<=0） */
  daysToStart: number;
  /** 距窗口结束天数（未结束为正） */
  daysToEnd: number;
}

/**
 * 计算窗口相对 today 的状态。
 * 会检查 today 上一年 / 当年 / 下一年的实例，确保跨年窗口（如 1 月仍处于
 * 去年 11 月开启的行情中）被正确识别为 ACTIVE。
 */
export function computeWindowStatus(
  window: TimeWindow,
  todayISO: string,
  resolveAnchor?: AnchorResolver,
): WindowStatusResult | null {
  const y = parseISO(todayISO).y;
  const candidates: WindowOccurrence[] = [];
  for (const seasonYear of [y - 1, y, y + 1]) {
    const occ = occurrenceForSeason(window, seasonYear, resolveAnchor);
    if (occ) candidates.push(occ);
  }
  if (candidates.length === 0) return null;

  const diff = (a: string, b: string) =>
    Math.round((Date.parse(b + 'T00:00:00Z') - Date.parse(a + 'T00:00:00Z')) / 86400000);

  // 1. today 落在某个实例的 [preheatStart, end] 内
  for (const occ of candidates) {
    if (compareISO(occ.preheatStart, todayISO) <= 0 && compareISO(todayISO, occ.end) <= 0) {
      const phase: WindowPhase = compareISO(todayISO, occ.start) < 0 ? 'PRE_HEAT' : 'ACTIVE';
      return {
        phase,
        occurrence: occ,
        daysToStart: diff(todayISO, occ.start),
        daysToEnd: diff(todayISO, occ.end),
      };
    }
  }

  // 2. 本年内刚结束的实例 → ENDED（"已过窗口"语义：今年的窗口刚过去）
  const past = candidates
    .filter((o) => compareISO(o.end, todayISO) < 0)
    .sort((a, b) => compareISO(b.end, a.end));
  const recentPast = past.find((o) => parseISO(o.end).y === y);
  if (recentPast) {
    return {
      phase: 'ENDED',
      occurrence: recentPast,
      daysToStart: diff(todayISO, recentPast.start),
      daysToEnd: diff(todayISO, recentPast.end),
    };
  }

  // 3. 最近的未来实例 → NOT_ACTIVE（尚未进入提前观察）
  const future = candidates
    .filter((o) => compareISO(o.preheatStart, todayISO) > 0)
    .sort((a, b) => compareISO(a.preheatStart, b.preheatStart));
  if (future.length > 0) {
    const occ = future[0];
    return {
      phase: 'NOT_ACTIVE',
      occurrence: occ,
      daysToStart: diff(todayISO, occ.start),
      daysToEnd: diff(todayISO, occ.end),
    };
  }

  // 4. 全部已过且本年无实例 → ENDED（取最近一个）
  const occ = past[0];
  return {
    phase: 'ENDED',
    occurrence: occ,
    daysToStart: diff(todayISO, occ.start),
    daysToEnd: diff(todayISO, occ.end),
  };
}

/** 某窗口在视图年份内需要渲染的分段（支持跨年窗口拆段渲染） */
export interface YearSegment {
  /** 段在视图年份内的起止（已裁剪到年内），ISO */
  start: string;
  end: string;
  /** 该段从前一年延续而来（左端开口） */
  continuesFromPrevYear: boolean;
  /** 该段延续到下一年（右端开口） */
  continuesIntoNextYear: boolean;
  /** 年内位置比例 0..1 */
  startFraction: number;
  endFraction: number;
}

/**
 * 计算任意 [startISO, endISO] 区间在指定视图年份内的分段。
 * 跨年 Campaign / 跨年窗口共用此逻辑：自然年只是显示容器。
 */
export function segmentForYear(startISO: string, endISO: string, year: number): YearSegment | null {
  const yearStart = `${year}-01-01`;
  const yearEnd = `${year}-12-31`;
  if (compareISO(endISO, yearStart) < 0 || compareISO(startISO, yearEnd) > 0) return null;

  const segStart = compareISO(startISO, yearStart) < 0 ? yearStart : startISO;
  const segEnd = compareISO(endISO, yearEnd) > 0 ? yearEnd : endISO;
  const diy = daysInYear(year);
  return {
    start: segStart,
    end: segEnd,
    continuesFromPrevYear: compareISO(startISO, yearStart) < 0,
    continuesIntoNextYear: compareISO(endISO, yearEnd) > 0,
    startFraction: (dayOfYearISO(segStart) - 1) / diy,
    // 结束日占满当天，+1
    endFraction: dayOfYearISO(segEnd) / diy,
  };
}

/** 规律窗口在视图年份内可能需要渲染多段（跨年窗口在年初和年末各一段） */
export function windowSegmentsForYear(
  window: TimeWindow,
  year: number,
  resolveAnchor?: AnchorResolver,
): YearSegment[] {
  const segments: YearSegment[] = [];
  // 本季（seasonYear = year）
  const current = occurrenceForSeason(window, year, resolveAnchor);
  if (current) {
    const seg = segmentForYear(current.start, current.end, year);
    if (seg) segments.push(seg);
  }
  // 上一季跨年到本年的尾段（seasonYear = year - 1 且跨年）
  const prev = occurrenceForSeason(window, year - 1, resolveAnchor);
  if (prev && prev.crossYear) {
    const seg = segmentForYear(prev.start, prev.end, year);
    if (seg) segments.push(seg);
  }
  return segments;
}
