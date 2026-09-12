/** Entity 9: Event —— 日历事件（事件不是规律） */
export type EventType =
  | 'holiday'
  | 'regulatory'
  | 'macro'
  | 'industry'
  | 'market'
  | 'experience';

/**
 * date_rule 说明：
 * - 固定日期: { kind: 'fixed', md: '10-01' }
 * - 日期范围: { kind: 'range', start_md: '04-01', end_md: '04-30' }
 * - 变动日期（如春节）: { kind: 'lunar' | 'computed', approx_md: '02-01', dates: {2026:'02-17',...} }
 */
export type DateRule =
  | { kind: 'fixed'; md: string }
  | { kind: 'range'; start_md: string; end_md: string }
  | { kind: 'variable'; approx_md: string; dates?: Record<number, string>; description?: string };

export interface Event {
  event_id: string;
  name: string;
  event_type: EventType;
  date_rule: DateRule;
  description?: string;
  source_id?: string;
}
