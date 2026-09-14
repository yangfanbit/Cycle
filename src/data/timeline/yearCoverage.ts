/**
 * Timeline Year Coverage Rule（V1.9.1）—— 统一 `verified` / `preview` 两个数据源的年份生成口径。
 *
 * ## 规则
 * 一个 Campaign / Research Candidate 覆盖的展示年份 =
 * 从 `start_date` 的年份 **连续生成** 到 `end_date` 的年份（**含两端**）。
 * ```
 * 2019-01-02 ~ 2022-10-31   →   [2019, 2020, 2021, 2022]
 * ```
 *
 * ## 为什么必须连续
 * 跨年 Campaign 的时间轴应在**每个中间年份**各有一行（`yearData(y)` 才会在 y 年把它纳入）。
 * 旧 `verifiedTimelineSource().years()` 只收集**起止年份**（`[2019, 2022]`），
 * 与 `previewTimelineSource().years()`（连续区间）口径不一致 →
 * **生产模式下跨年 Campaign 的中间年份行缺失**（Audit Finding F-MED-5，本文件修复）。
 *
 * ## 边界
 * 纯视图层派生（不落库、不进 Export / Contract）；不改 DB / Schema / Campaign 数据。
 */

/**
 * 从日期字符串解析年份。**严格**：必须以 4 位数字开头（`YYYY-MM-DD` / `YYYY`）。
 * 空串 / `NaN` / 非日期 → `null`（不编造年份；注意 `Number('') === 0`，不可直接用 Number）。
 */
export function yearOf(date: string | null | undefined): number | null {
  const m = /^(\d{4})/.exec(String(date ?? '').trim());
  return m ? Number(m[1]) : null;
}

/** 单个区间的年份连续跨度（含两端，升序）。任一端无法解析出年份 → `[]`。 */
export function yearSpan(start: string, end: string): number[] {
  const a = yearOf(start);
  const b = yearOf(end);
  if (a === null || b === null) return [];
  const from = Math.min(a, b);
  const to = Math.max(a, b);
  const out: number[] = [];
  for (let y = from; y <= to; y += 1) out.push(y);
  return out;
}

/** 多个区间（Campaign / Candidate）的年份覆盖并集（升序去重）。 */
export function yearCoverageOf(ranges: readonly { start: string; end: string }[]): number[] {
  const set = new Set<number>();
  for (const r of ranges) {
    for (const y of yearSpan(r.start, r.end)) set.add(y);
  }
  return [...set].sort((x, y) => x - y);
}

/**
 * Timeline 年份（**统一规则**）= 覆盖年份的连续区间（相邻年份自动补齐，UI 年份轴无空洞）。
 *
 * @param ranges     Campaign / Research Candidate 的起止区间（覆盖规则来源）
 * @param extraYears 不由区间派生的「声明年份」——preview 传入研究事件年份，
 *                   以保留「2018 反例年份」这类**无 Campaign 但有历史事件**的年份。
 *                   非法值（`null` / `NaN` / 非整数）自动忽略。
 */
export function timelineYears(
  ranges: readonly { start: string; end: string }[] = [],
  extraYears: readonly (number | null | undefined)[] = [],
): number[] {
  const set = new Set<number>(yearCoverageOf(ranges));
  for (const y of extraYears) {
    if (typeof y === 'number' && Number.isInteger(y)) set.add(y);
  }
  if (set.size === 0) return [];
  const min = Math.min(...set);
  const max = Math.max(...set);
  const out: number[] = [];
  for (let y = min; y <= max; y += 1) out.push(y);
  return out;
}
