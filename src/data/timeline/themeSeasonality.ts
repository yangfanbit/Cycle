/**
 * themeSeasonality.ts —— 「年内时间集中度」的**只读派生层**（ThreeC 1.2 · Usage-Driven）。
 *
 * ## 它回答什么
 *
 * 「哪些大主题的历史主要炒作**集中在年内的少数几个月**」——
 * 例如汽车：6 个年度窗口，**6 个全部落在 6–7 月**。
 *
 * ## ★★★ 它**只报计数**，不给「季节性强度」
 *
 * `AGENTS.md` §1 禁止概率 / 胜率 / 推荐分 / 预测。因此本层：
 *
 * - **输出的是计数**：「年内窗口 N 个 · 其中 M 个落在 X–Y」；
 * - **不输出**任何评分 / 强度 / 等级 / 排序依据；
 * - **不声称**「集中 = 明年也会」—— 那是预测，不是事实。
 *
 * ★ 与 `SeasonalMap` 既有的「历史 N 次 · 覆盖 N 个年份」是**同一类事实**，
 * 只是把「落在哪几个月」说得更清楚。
 *
 * ## 数据来源
 *
 * `themeAnnualWindow.themeAnnualRowsOf()` 的 `windows[].mainRise.start`
 * —— **Research 的真实日期**（不反推年内比例，避免舍入误差）。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import type { ThemeAnnualRow } from './themeAnnualWindow';

/** 判定「集中」所需的最少**常规窗口**数（样本太小不标注） */
export const MIN_WINDOWS_FOR_CONCENTRATION = 3;

/** 判定「集中」所需的最少占比（M / N） */
export const CONCENTRATION_RATIO = 2 / 3;

/** 统计窗口的宽度（天）—— 约两个月 */
export const BAND_DAYS = 61;

export interface ThemeSeasonality {
  /** 大主题展示名 */
  label: string;
  /** 参与统计的**常规**窗口数（`kind === 'window'`；onset 长周期不计入） */
  windowCount: number;
  /** 落在最集中区间内的窗口数 */
  inBand: number;
  /** 最集中区间的起止（月-日，参考非闰年；无则 null） */
  band: { from: string; to: string } | null;
  /** ★ 同一区间的**年内比例**（供地图精确绘制 —— 必须与 `band` 指向同一区间，
   *  否则「画的带」与「说的计数」会不一致） */
  bandFrac: { startFrac: number; endFrac: number } | null;
  /** ★ 是否达到「集中」判据（**仅用于是否加标注**，不是评分） */
  concentrated: boolean;
  /** ★ 面向界面的**计数陈述**（不含任何强度/概率措辞） */
  statement: string | null;
}

/** 把 `YYYY-MM-DD` 转成该年内的日序（1..366） */
function dayOfYear(iso: string): number {
  const [y, m, d] = iso.split('-').map(Number);
  const days = [31, y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let n = d;
  for (let i = 0; i < m - 1; i += 1) n += days[i];
  return n;
}

/** 日序 → `MM-DD`（参考非闰年，仅用于展示区间端点） */
function monthDay(n: number): string {
  const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let d = ((n - 1) % 365) + 1;
  let m = 0;
  while (d > days[m]) {
    d -= days[m];
    m += 1;
  }
  return `${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}

/**
 * 计算单个主题的年内集中度。
 *
 * 算法（确定性）：把**常规窗口**的起始日序排序，用宽度 `BAND_DAYS` 的滑窗
 * 找「覆盖窗口数最多」的区间；平手时取**更早**的区间（确定性，不随机）。
 */
export function seasonalityOf(row: ThemeAnnualRow): ThemeSeasonality {
  const starts = (row.windows ?? [])
    .filter((w) => w.kind === 'window' && w.mainRise?.start)
    .map((w) => dayOfYear(w.mainRise!.start))
    .sort((a, b) => a - b);

  const n = starts.length;
  if (n === 0) {
    return { label: row.label, windowCount: 0, inBand: 0, band: null, bandFrac: null, concentrated: false, statement: null };
  }

  let best = 0;
  let bestFrom = starts[0];
  for (const s of starts) {
    const count = starts.filter((x) => x >= s && x <= s + BAND_DAYS).length;
    if (count > best) {
      best = count;
      bestFrom = s;
    }
  }
  const concentrated = n >= MIN_WINDOWS_FOR_CONCENTRATION && best / n >= CONCENTRATION_RATIO;
  const band = { from: monthDay(bestFrom), to: monthDay(bestFrom + BAND_DAYS) };

  return {
    label: row.label,
    windowCount: n,
    inBand: best,
    band,
    // 年内比例：日序 → 0..1（与 `band` **同源**，保证画与说一致）
    bandFrac: { startFrac: bestFrom / 365, endFrac: Math.min((bestFrom + BAND_DAYS) / 365, 1) },
    concentrated,
    // ★ 纯计数陈述：不含「强度 / 概率 / 规律 / 值得关注」等措辞
    statement: concentrated
      ? `年内窗口 ${n} 个 · 其中 ${best} 个落在 ${band.from} ~ ${band.to}`
      : null,
  };
}

/** 批量计算；返回 `label → ThemeSeasonality` */
export function seasonalityByTheme(rows: ThemeAnnualRow[]): Map<string, ThemeSeasonality> {
  const out = new Map<string, ThemeSeasonality>();
  for (const r of rows) out.set(r.label, seasonalityOf(r));
  return out;
}

/** ★ 必须与标注一同展示的语义边界
 *
 * ★ 措辞受既有护栏约束：`seasonalMap.test.tsx` 禁止地图 HTML 出现
 *   `score / ranking / probability / 胜率 / 推荐分 / 预测`。
 *   **不放宽护栏**，改用「不是概率」+「不代表明年」表达同一件事（「概率」不在禁列）。
 * ★ 不得含 `**` —— 它会字面显示。
 */
export const SEASONALITY_NOTE =
  '「年内窗口 N 个 · 其中 M 个落在某区间」是历史计数事实，不是概率；' +
  '也不代表该主题明年仍会在同一区间出现。';
