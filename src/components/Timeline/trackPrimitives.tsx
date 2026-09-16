/**
 * Timeline 轨道原语（纯展示）。
 *
 * 从 `Timeline.tsx` 抽出，供 Timeline 各层与「时间型观察层」共用 ——
 * 目的是**避免第二套月份网格 / 今天线实现**（同一视觉口径只有一个来源）。
 * 抽出时行为不变（V1.6 起的比例与文案保持原样）。
 */

import { daysInYear } from '../../utils';

export const MONTHS = [
  '1月',
  '2月',
  '3月',
  '4月',
  '5月',
  '6月',
  '7月',
  '8月',
  '9月',
  '10月',
  '11月',
  '12月',
];

const MONTH_START_FRACTIONS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

/** 各月起点在年内轨道上的比例（闰年 3 月起顺延） */
export function monthFractions(year: number): number[] {
  const diy = daysInYear(year);
  const leap = diy === 366 ? 1 : 0;
  return MONTH_START_FRACTIONS.map((d, i) => (d + (i > 1 ? leap : 0)) / diy);
}

/** 比例 → CSS 百分比（统一三位小数，避免轨道抖动） */
export function pct(f: number): string {
  return `${(f * 100).toFixed(3)}%`;
}

/** 12 个月网格线 */
export function MonthGrid({ year }: { year: number }) {
  return (
    <div className="tl-grid">
      {monthFractions(year).map((f, i) => (
        <div key={i} className="gl" style={{ left: pct(f) }} />
      ))}
    </div>
  );
}

/** 今天竖线（仅在展示年份 = 今天所在年份时渲染，由调用方判定） */
export function TodayLine({ frac }: { frac: number }) {
  return (
    <div className="today-line" style={{ left: pct(frac) }}>
      <span className="today-flag">TODAY</span>
    </div>
  );
}
