/**
 * ★★ 外部季节性**参考时间轴**的数据层（ThreeC 1.3 · v0.12）。
 *
 * ## 它做什么
 *
 * 把 `externalCalendarEntries()` 的 25 条线索按**月份精度**铺到 1–12 月上：
 * 每条窗口拆成段（跨年窗口拆成「年末段 + 年初段」），并单独列出**无固定窗口**的条目。
 *
 * ## 它**不**做什么
 *
 * - **不推断日级日期**：源数据是 `MONTH` 精度（`start_month` / `end_month`），
 *   这里只输出月份，**不**生成 `MM-DD`。
 * - **不改变映射状态**：`MAPPED` 只表示「外部线索 ↔ ThreeC 宏观主题」的名称映射，
 *   **不是** ThreeC 已验证结论；所有条目在本层一律是**外部参考**。
 * - **不合并**不同条目：一条线索两个窗口（如 EXT-21 的 3 月 + 11–1 月）保留两段。
 *
 * ## 口径
 *
 * 源数据 24 段窗口里 4 段跨年（EXT-10 / EXT-11 / EXT-12 / EXT-21）→ 上轴显示 **28 段**。
 * 这两个数字都必须能被 UI 说清（「24 段窗口，跨年拆分为 28 段」），否则读者会以为少算了。
 */

import type { ExternalCalendarEntry, ExternalWindow } from './externalSeasonalCalendar';

export const MONTHS: readonly number[] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

/** 时间轴上的**一段**（跨年窗口已拆分） */
export interface TimelineSegment {
  /** 该段覆盖的月份（升序、连续） */
  months: number[];
  /** 段起点月 / 终点月（同月窗口 start === end） */
  startMonth: number;
  endMonth: number;
  /** 该段是否属于跨年窗口（拆出来的「年末段」与「年初段」都为 true） */
  fromCrossYear: boolean;
  /** 原始窗口文本（原样引用，如「10 月至次年 3 月」） */
  rawText: string;
}

export interface TimelineRow {
  entry: ExternalCalendarEntry;
  /** 该条目的全部段（1–2 段） */
  segments: TimelineSegment[];
  /** 首次出现的月份（用于排序；无窗口条目为 `null`） */
  firstMonth: number | null;
}

export interface ExternalTimeline {
  /** 有固定月份窗口的条目（按首次月份 → id 排序） */
  axisRows: TimelineRow[];
  /** 无固定窗口的条目（按 id 排序） */
  noWindowRows: TimelineRow[];
  months: readonly number[];
  totals: {
    entries: number;
    withWindow: number;
    withoutWindow: number;
    /** 源数据里的窗口**段数**（跨年前） */
    windows: number;
    /** 上轴后显示的**段数**（跨年拆分后） */
    segments: number;
    crossYearWindows: number;
    mapped: number;
    unmapped: number;
  };
}

/** 是否跨年（`cross_year` 或 start > end —— 两者都视为跨年，防止数据只填了月份） */
export function isCrossYear(w: ExternalWindow): boolean {
  return w.cross_year || w.start_month > w.end_month;
}

/**
 * 把一个窗口拆成 1–2 段（**只做月份拆分，不产生日期**）。
 *
 * 例：`10 月至次年 3 月` → `[10,11,12]` + `[1,2,3]`。
 */
export function segmentsOfWindow(w: ExternalWindow): TimelineSegment[] {
  const { start_month: s, end_month: e, raw_text: raw } = w;
  if (!isCrossYear(w)) {
    const months: number[] = [];
    for (let m = s; m <= e; m += 1) months.push(m);
    return [{ months, startMonth: s, endMonth: e, fromCrossYear: false, rawText: raw }];
  }
  const tail: number[] = [];
  for (let m = s; m <= 12; m += 1) tail.push(m);
  const head: number[] = [];
  for (let m = 1; m <= e; m += 1) head.push(m);
  const out: TimelineSegment[] = [];
  if (tail.length > 0) {
    out.push({ months: tail, startMonth: s, endMonth: 12, fromCrossYear: true, rawText: raw });
  }
  if (head.length > 0) {
    out.push({ months: head, startMonth: 1, endMonth: e, fromCrossYear: true, rawText: raw });
  }
  return out;
}

function segmentsOfEntry(e: ExternalCalendarEntry): TimelineSegment[] {
  return (e.windows ?? []).flatMap(segmentsOfWindow);
}

/**
 * ★★ 主函数：构造外部季节性参考时间轴（纯函数、确定性）。
 *
 * 排序：有窗口的按**首次月份**升序 → `id`；无窗口的按 `id`。
 * ★ 不按「重要程度」「成熟度」排序（源数据里没有这种排序依据，编一个就是伪造）。
 */
export function buildExternalTimeline(
  entries: readonly ExternalCalendarEntry[],
): ExternalTimeline {
  const rows: TimelineRow[] = entries.map((entry) => {
    const segments = segmentsOfEntry(entry);
    // ★ 用**第一个窗口的起始月**排序（不是所有段的最小月）：
    //   跨年窗口 10–3 的起点是 10 月，若取 min 会被排到 1 月，时间顺序就错了。
    const firstMonth = segments.length > 0 ? segments[0].months[0] : null;
    return { entry, segments, firstMonth };
  });

  const axisRows = rows
    .filter((r) => r.firstMonth !== null)
    .sort((a, b) => (a.firstMonth! - b.firstMonth!) || a.entry.id.localeCompare(b.entry.id));
  const noWindowRows = rows
    .filter((r) => r.firstMonth === null)
    .sort((a, b) => a.entry.id.localeCompare(b.entry.id));

  const windows = entries.reduce((n, e) => n + (e.windows?.length ?? 0), 0);
  const segments = rows.reduce((n, r) => n + r.segments.length, 0);
  const crossYearWindows = entries.reduce(
    (n, e) => n + (e.windows ?? []).filter(isCrossYear).length, 0,
  );

  return {
    axisRows,
    noWindowRows,
    months: MONTHS,
    totals: {
      entries: entries.length,
      withWindow: axisRows.length,
      withoutWindow: noWindowRows.length,
      windows,
      segments,
      crossYearWindows,
      mapped: entries.filter((e) => e.mapping.status === 'MAPPED').length,
      unmapped: entries.filter((e) => e.mapping.status === 'UNMAPPED').length,
    },
  };
}

/** 某一行是否在某月有窗口（供单元格渲染） */
export function isActiveInMonth(row: TimelineRow, month: number): boolean {
  return row.segments.some((s) => s.months.includes(month));
}

/** 该月属于哪一段（用于给段首加标签） */
export function segmentAt(row: TimelineRow, month: number): TimelineSegment | undefined {
  return row.segments.find((s) => s.months.includes(month));
}

/** ★ 本层的口径声明（UI 原样渲染，与 ThreeC 历史地图明确区分） */
export const EXTERNAL_TIMELINE_NOTE =
  '★★ 这是**外部资料声称**的季节性窗口（月份精度），**不是** ThreeC 的研究结论。'
  + '它与上方「历史季节性机会地图」的来源不同：后者来自 Research 历史对象的 `MAIN_RISE`，'
  + '本图来自外部资料条目。★ 两套窗口**不合并**、**不同色**，'
  + '「窗口内」只是时间事实，**不代表**该题材会上涨，也**不提升**研究成熟度。';

/** 跨年窗口的展示说明（数字由数据算，不写死） */
export function crossYearNote(t: ExternalTimeline): string {
  return `共 ${t.totals.windows} 段窗口（其中 ${t.totals.crossYearWindows} 段跨年），`
    + `跨年窗口拆到年末与年初显示 → 轴上共 ${t.totals.segments} 段；`
    + `另有 ${t.totals.withoutWindow} 条无固定窗口（事件驱动），单列在下方。`;
}

/* ================================================================
 * ★★ 月份坐标（v0.14：两层时间轴共用的「一把尺」）
 *
 * 外部层与历史层以前各自算位置：外部用 `(月份-1)/12`，历史用年内日期比例 `frac`。
 * 两者都是 0..1，但「1 月刻度在 0%、frac=0.5 在 50%」意味着 50% 既被读成
 * 「7 月 1 日」又被读成「年中第 182 天」—— 同一把尺两种解释。
 *
 * 现在统一规范成**月份坐标** `mf ∈ [0, 12]`：
 *   - 外部月份窗口只落在整数月边界（`monthToMonthFraction`），保持月份精度；
 *   - 历史 MAIN_RISE 的年内比例经 `fracToMonthFraction` 换算到同一把尺上。
 *
 * ★ 这两个函数是**唯一**允许把「年内日期比例」与「月份」互相换算的地方。
 *   Research 的原始起止日期不被重算、外部月份不被解释成日级 —— 换算只为对齐坐标。
 * ================================================================ */

/** 年内日期比例（0..1）→ 月份坐标（0..12）。例：0 → 1 月起点，6/12=0.5 → 年中 */
export function fracToMonthFraction(frac: number): number {
  return Math.min(Math.max(frac, 0), 1) * 12;
}

/** 月份（1..12）→ 月份坐标起点（0..11）。例：1 → 0（1 月格左缘） */
export function monthToMonthFraction(month: number): number {
  return Math.min(Math.max(month, 1), 12) - 1;
}

/** 月份坐标 → 轨道百分比字符串（0..12 → '0%'..'100%'） */
export function monthFractionToPct(mf: number): string {
  return `${(Math.min(Math.max(mf, 0), 12) / 12) * 100}%`;
}
