import type { Event } from '../models';
import { compareISO, mdToISO } from './date/dateUtils';

/**
 * 解析 Event 在指定年份的具体日期 / 日期范围。
 * variable 类型优先查 dates 表（如春节），缺失时用 approx_md 近似并标注 approximate。
 */
export interface ResolvedEvent {
  event: Event;
  year: number;
  start: string; // ISO
  end: string;   // ISO，单日事件 = start
  approximate: boolean;
}

export function resolveEventForYear(event: Event, year: number): ResolvedEvent | null {
  const rule = event.date_rule;
  switch (rule.kind) {
    case 'fixed': {
      const d = mdToISO(rule.md, year);
      return { event, year, start: d, end: d, approximate: false };
    }
    case 'range': {
      const start = mdToISO(rule.start_md, year);
      // 范围也支持跨年（如 12-31 → 01-05），目前事件用不到，预留
      const endYear = compareISO(mdToISO(rule.end_md, year), start) < 0 ? year + 1 : year;
      return { event, year, start, end: mdToISO(rule.end_md, endYear), approximate: false };
    }
    case 'variable': {
      const exact = rule.dates?.[year];
      const d = exact ? mdToISO(exact, year) : mdToISO(rule.approx_md, year);
      return { event, year, start: d, end: d, approximate: !exact };
    }
  }
}
