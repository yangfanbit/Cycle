/**
 * Historical Cycle Map v0.1 —— 「当前周 ↔ 历史时间窗口」横向观察视图模型。
 *
 * ## 定位
 * 回答：**「现在这一周，在历史上有没有出现过类似的周期窗口？这些周期在当时处于什么阶段？」**
 *
 * 与其它视角的分工（**不得合并**）：
 * - **Historical Cycle Map** = **时间窗口浏览**（Calendar Window + Lifecycle Position）
 * - **Structural Analogy** = 当前结构与历史结构的**正式对应**
 * - **Lifecycle Lens** = 历史阶段浏览
 *
 * ## 观察分辨率（正式定义）
 * ThreeC 的观察分辨率为 **周级（week-level）**，**不是日级**：
 * - 日期只用于**排序与窗口相交**，**不制造虚假的日期精确度**
 * - 历史案例只要与窗口**相交**即纳入，**不因缺少精确日期而消失**
 * - 用户可见层优先展示「交易周 / 时间窗口 / 生命周期阶段」
 *
 * ## 边界（不得违反）
 * - **不排序**：不产生 similarity score / ranking / probability / Top-N / 「最强」「最像」。
 *   筛选维度只有：时间窗口 / Macro Theme / Theme Cycle / Lifecycle。
 * - **不重定义 Lifecycle**：阶段原样来自 Research `phases`（`timeline_export_v1`）。
 * - **不新建平行数据模型**：只消费既有 export。
 * - **UNKNOWN ≠ 不存在**：无阶段信息 → `UNKNOWN`，**不得**显示成「没有」。
 */

import {
  addDaysISO,
  compareISO,
  diffDays,
  maxISO,
  minISO,
  parseISO,
  toISO,
} from '../../utils';
import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import { LIFECYCLE_STAGE_LABEL } from './historicalCase';

/* ================= 1. 周级时间模型 ================= */

export interface WeekWindow {
  /** 周一（ISO）。 */
  start: string;
  /** 周日（ISO）。 */
  end: string;
  /** 周三（ISO）—— 窗口锚点，用于「同一周」的跨年映射。 */
  center: string;
  /** 展示标签：`2026-W38`。 */
  label: string;
}

/** 周一为一周之始（周级分辨率；与 `marketTodayISO` 的 Asia/Shanghai 基准一致）。 */
function mondayOf(iso: string): string {
  const { y, m, d } = parseISO(iso);
  // getUTCDay：0=周日 … 6=周六 → 距周一的偏移
  const dow = new Date(Date.UTC(y, m - 1, d)).getUTCDay();
  const back = dow === 0 ? 6 : dow - 1;
  return addDaysISO(iso, -back);
}

/** ISO-8601 周序号（用于稳定标签，不用于排序）。 */
function isoWeekLabel(iso: string): string {
  const { y, m, d } = parseISO(iso);
  const date = new Date(Date.UTC(y, m - 1, d));
  const day = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((date.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${date.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

/** 窗口锚点 = 起点 + 2 天（周中）。 */
function addISO2(iso: string): string {
  return addDaysISO(iso, 2);
}

/** 包含 `iso` 的交易周（周一 → 周日）。 */
export function weekWindowOf(iso: string): WeekWindow {
  const start = mondayOf(iso);
  const end = addDaysISO(start, 6);
  return { start, end, center: addDaysISO(start, 2), label: isoWeekLabel(start) };
}

/** 相对 `iso` 所在周平移 `weeks` 周（可为负）。 */
export function weekWindowOffset(iso: string, weeks: number): WeekWindow {
  return weekWindowOf(addDaysISO(mondayOf(iso), weeks * 7));
}

/** 默认窗口：**当前周 ± 2 周**（共 5 周）。 */
export function weeksAround(iso: string, n = 2): { window: WeekWindow; offset: number }[] {
  const out: { window: WeekWindow; offset: number }[] = [];
  for (let i = -n; i <= n; i += 1) out.push({ window: weekWindowOffset(iso, i), offset: i });
  return out;
}

/* ================= 2. 日历窗口（跨年映射） ================= */

/**
 * 把「当前周」映射到某个历史年份的同日历窗口。
 *
 * 用**月-日**平移（保留月/日，仅替换年份）—— 这是**周级近似**，
 * 不声称与历史年份的自然周完全对齐（跨年周会截断到年内）。
 */
export function calendarWindowInYear(current: WeekWindow, year: number): WeekWindow {
  const shift = (iso: string): string => {
    const { m, d } = parseISO(iso);
    return toISO({ y: year, m, d });
  };
  const start = shift(current.start);
  const end = shift(current.end);
  // 跨年周（如 12-28 → 次年 01-03）：截断到该年内，避免窗口跑到相邻年份。
  // 该周的「年初段」为该年的 01-01 起，「年末段」为该年 12-31 止；取年初段为起点、
  // 末端落在年内者为终点，保证 start ≤ end。
  if (compareISO(end, start) < 0) {
    const jan1 = toISO({ y: year, m: 1, d: 1 });
    const s = jan1;
    const e = compareISO(end, jan1) < 0 ? jan1 : end;
    return { start: s, end: e, center: addISO2(s), label: `${year}` };
  }
  return { start, end, center: shift(current.center), label: `${year}` };
}

/* ================= 3. Lifecycle Position ================= */

/** 阶段标签（原样复用 Research 阶段枚举；未知 → `UNKNOWN`）。 */
export function stageLabelOf(stage: string | null): string {
  if (!stage) return 'UNKNOWN';
  return LIFECYCLE_STAGE_LABEL[stage] ?? stage;
}

function stageAt(c: TimelineCampaign, date: string): string | null {
  for (const p of c.phases) {
    if (p.start && p.end && date >= p.start && date <= p.end) return p.phase;
  }
  return null;
}

/* ================= 4. Cycle Map 条目 ================= */

export type CycleMapStageStatus = 'IN_WINDOW' | 'ENTERED_IN_WINDOW' | 'UNKNOWN';

export interface CycleMapEntry {
  campaignId: string;
  title: string;
  year: number;
  macroTheme: string | null;
  themeCycleId: string | null;
  objectKind: 'campaign' | 'research_candidate';
  /** 该案例在**窗口锚点**所处的生命周期阶段（原样来自 Research phases）。 */
  stage: string | null;
  stageLabel: string;
  /** `UNKNOWN` 表示窗口锚点不落在任何已记录阶段区间内 —— **不是**「没有阶段」。 */
  stageStatus: CycleMapStageStatus;
  /** 窗口与案例区间的重叠段。 */
  overlapStart: string;
  overlapEnd: string;
  /** 案例区间（用于横向 span 渲染）。 */
  caseStart: string;
  caseEnd: string;
  /** 案例是否在**本窗口内开始**（= 「这一时期刚进入」）。 */
  enteredInWindow: boolean;
  /** 导航目标（复用既有 Campaign Detail 入口）。 */
  navigation: { kind: 'campaign'; id: string };
}

export interface CycleMapYearGroup {
  year: number;
  window: WeekWindow;
  entries: CycleMapEntry[];
}

function macroThemeOf(c: TimelineCampaign): string | null {
  const t = c.themes.find((x) => x.theme_type === 'industry' || x.theme_type === 'sector');
  return t ? t.name : null;
}

/** 单个案例是否与窗口相交（**日期只用于相交判断，不要求精确**）。 */
function intersects(c: TimelineCampaign, win: WeekWindow): boolean {
  return compareISO(c.start, win.end) <= 0 && compareISO(c.end, win.start) >= 0;
}

function entryOf(c: TimelineCampaign, win: WeekWindow): CycleMapEntry {
  const overlapStart = maxISO(c.start, win.start);
  const overlapEnd = minISO(c.end, win.end);
  // 锚点：窗口中心若落在案例区间内 → 用窗口中心；否则用重叠起点（保证在案例内）
  const anchor =
    compareISO(c.start, win.center) <= 0 && compareISO(win.center, c.end) <= 0
      ? win.center
      : overlapStart;
  const stage = stageAt(c, anchor);
  const enteredInWindow = compareISO(c.start, win.start) >= 0 && compareISO(c.start, win.end) <= 0;
  return {
    campaignId: c.campaign_id,
    title: c.title,
    year: c.year,
    macroTheme: macroThemeOf(c),
    themeCycleId: c.theme_cycle_id ?? null,
    objectKind: c.kind === 'candidate' ? 'research_candidate' : 'campaign',
    stage,
    stageLabel: stageLabelOf(stage),
    stageStatus: stage ? (enteredInWindow ? 'ENTERED_IN_WINDOW' : 'IN_WINDOW') : 'UNKNOWN',
    overlapStart,
    overlapEnd,
    caseStart: c.start,
    caseEnd: c.end,
    enteredInWindow,
    navigation: { kind: 'campaign', id: c.campaign_id },
  };
}

/* ================= 5. 构建 ================= */

export interface HistoricalCycleMap {
  /** 当前交易周。 */
  currentWeek: WeekWindow;
  /** 当前周 ± 2 周（周级窗口列表；用于「现在这一周在哪里」）。 */
  weeks: { window: WeekWindow; offset: number; entries: CycleMapEntry[] }[];
  /** 历史年份分组（每个年份取同日历窗口）。 */
  years: CycleMapYearGroup[];
  /** 全部历史条目（按年份、再按开始日期 —— **时间序，不是排名**）。 */
  allEntries: CycleMapEntry[];
  /** 是否完全无历史条目（诚实空态）。 */
  isEmpty: boolean;
}

/**
 * 构建 Historical Cycle Map。
 *
 * **只消费既有 export**（`TimelineDataSource`），不新增 Research 数据。
 * **不排序**：年份升序 + 案例开始日期升序（纯时间序）。
 */
export function historicalCycleMap(source: TimelineDataSource, today: string): HistoricalCycleMap {
  const currentWeek = weekWindowOf(today);
  const weeks = weeksAround(today, 2).map(({ window, offset }) => ({
    window,
    offset,
    entries: source
      .yearData(parseISO(window.start).y)
      .campaigns.filter((c) => intersects(c, window))
      .sort((a, b) => compareISO(a.start, b.start))
      .map((c) => entryOf(c, window)),
  }));

  const years = source.years().map((year) => {
    const window = calendarWindowInYear(currentWeek, year);
    const entries = source
      .yearData(year)
      .campaigns.filter((c) => intersects(c, window))
      .sort((a, b) => compareISO(a.start, b.start))
      .map((c) => entryOf(c, window));
    return { year, window, entries };
  });

  const allEntries = years.flatMap((y) => y.entries);

  return { currentWeek, weeks, years, allEntries, isEmpty: allEntries.length === 0 };
}

/* ================= 6. 筛选（筛选 ≠ 排序） ================= */

export interface CycleMapFilter {
  macroTheme?: string | null;
  themeCycleId?: string | null;
  stage?: string | null;
}

/** 按维度筛选（**保持传入顺序**；不做任何排序）。 */
export function filterCycleMapEntries(
  entries: CycleMapEntry[],
  filter: CycleMapFilter,
): CycleMapEntry[] {
  return entries.filter((e) => {
    if (filter.macroTheme && e.macroTheme !== filter.macroTheme) return false;
    if (filter.themeCycleId && e.themeCycleId !== filter.themeCycleId) return false;
    if (filter.stage && e.stageLabel !== filter.stage) return false;
    return true;
  });
}

/** 可用的筛选值（去重 + 稳定序，用于 UI 选项）。 */
export function cycleMapFacets(entries: CycleMapEntry[]): {
  macroThemes: string[];
  themeCycles: string[];
  stages: string[];
} {
  const mt = new Set<string>();
  const tc = new Set<string>();
  const st = new Set<string>();
  for (const e of entries) {
    if (e.macroTheme) mt.add(e.macroTheme);
    if (e.themeCycleId) tc.add(e.themeCycleId);
    st.add(e.stageLabel);
  }
  return {
    macroThemes: [...mt].sort(),
    themeCycles: [...tc].sort(),
    stages: [...st].sort(),
  };
}

/** 案例相对窗口的横向位置（0..1，用于 span 渲染；**不是分数**）。 */
export function spanRatio(entry: CycleMapEntry, window: WeekWindow): { left: number; width: number } {
  const total = Math.max(1, diffDays(window.start, window.end) + 1);
  const s = diffDays(window.start, entry.overlapStart);
  const e = diffDays(window.start, entry.overlapEnd);
  const left = Math.max(0, Math.min(1, s / total));
  const right = Math.max(0, Math.min(1, (e + 1) / total));
  return { left, width: Math.max(0.04, right - left) };
}
