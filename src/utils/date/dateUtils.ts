/**
 * 日期工具：统一使用 UTC 毫秒做运算，避免本地时区 / DST 造成误差。
 * 所有对外日期格式均为 ISO 'YYYY-MM-DD'；年内日期为 'MM-DD'。
 */

export interface YMD {
  y: number;
  m: number;
  d: number;
}

export function parseISO(iso: string): YMD {
  const [y, m, d] = iso.split('-').map(Number);
  return { y, m, d };
}

export function toISO({ y, m, d }: YMD): string {
  const mm = String(m).padStart(2, '0');
  const dd = String(d).padStart(2, '0');
  return `${y}-${mm}-${dd}`;
}

export function toUTC(ymd: YMD): number {
  return Date.UTC(ymd.y, ymd.m - 1, ymd.d);
}

export function fromUTC(ts: number): YMD {
  const dt = new Date(ts);
  return { y: dt.getUTCFullYear(), m: dt.getUTCMonth() + 1, d: dt.getUTCDate() };
}

export function addDaysISO(iso: string, days: number): string {
  return toISO(fromUTC(toUTC(parseISO(iso)) + days * 86400000));
}

/** b - a 的天数差 */
export function diffDays(aISO: string, bISO: string): number {
  return Math.round((toUTC(parseISO(bISO)) - toUTC(parseISO(aISO))) / 86400000);
}

export function compareISO(aISO: string, bISO: string): number {
  return diffDays(bISO, aISO) === 0 ? 0 : toUTC(parseISO(aISO)) - toUTC(parseISO(bISO)) < 0 ? -1 : 1;
}

export function isLeapYear(year: number): boolean {
  return (year % 4 === 0 && year % 100 !== 0) || year % 400 === 0;
}

export function daysInYear(year: number): number {
  return isLeapYear(year) ? 366 : 365;
}

const DAYS_BEFORE_MONTH = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];

/** ISO 日期在所属年份中的第几天（1-based） */
export function dayOfYearISO(iso: string): number {
  const { y, m, d } = parseISO(iso);
  return DAYS_BEFORE_MONTH[m - 1] + d + (m > 2 && isLeapYear(y) ? 1 : 0);
}

/** 'MM-DD' + 年份 → 'YYYY-MM-DD' */
export function mdToISO(md: string, year: number): string {
  const [m, d] = md.split('-').map(Number);
  return toISO({ y: year, m, d });
}

/** 比较两个 'MM-DD'，a<b 返回 -1 */
export function compareMD(a: string, b: string): number {
  if (a === b) return 0;
  return a < b ? -1 : 1;
}

/** start_md → end_md 是否为跨年窗口（终点在起点之前，如 11-01 → 01-15） */
export function isCrossYearMD(startMD: string, endMD: string): boolean {
  return compareMD(endMD, startMD) < 0;
}

/** 日期在年内的位置比例（0..1），用于时间轴定位 */
export function yearFraction(iso: string): number {
  const { y } = parseISO(iso);
  return (dayOfYearISO(iso) - 1) / daysInYear(y);
}

/** 今天的 ISO 日期（A股市场日期基准：Asia/Shanghai，不依赖浏览器本地时区） */
export function marketTodayISO(now: Date = new Date()): string {
  // en-CA 区域的年月日格式恰为 'YYYY-MM-DD'；时区固定为市场时区
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now);
}

export function minISO(a: string, b: string): string {
  return compareISO(a, b) <= 0 ? a : b;
}

export function maxISO(a: string, b: string): string {
  return compareISO(a, b) >= 0 ? a : b;
}
