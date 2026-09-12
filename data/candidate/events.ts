import type { Event } from '../../src/models';

/**
 * 日历事件。事件不是规律：
 * "国庆"是 Event；"国庆后消费容易活跃"才是 Rule，两者分开建模。
 *
 * 春节等变动日期通过 date_rule.dates 逐年登记；未登记的年份回退到 approx_md
 * 并标记 approximate。
 */
export const events: Event[] = [
  {
    event_id: 'evt_spring_festival',
    name: '春节',
    event_type: 'holiday',
    date_rule: {
      kind: 'variable',
      approx_md: '02-01',
      dates: {
        2023: '01-22',
        2024: '02-10',
        2025: '01-29',
        2026: '02-17',
        2027: '02-06',
        2028: '01-26',
      },
      description: '农历正月初一，日期逐年变动',
    },
    description: 'A股最重要的季节性锚点之一，节前节后资金与情绪节奏明显不同。',
  },
  {
    event_id: 'evt_two_sessions',
    name: '全国两会',
    event_type: 'regulatory',
    date_rule: { kind: 'range', start_md: '03-03', end_md: '03-11' },
    description: '全国政协与人大会议，通常为3月初，具体会期以官方公告为准。',
  },
  {
    event_id: 'evt_q1_report',
    name: '一季报披露期',
    event_type: 'regulatory',
    date_rule: { kind: 'range', start_md: '04-01', end_md: '04-30' },
    description: '上市公司一季度报告集中披露期（4月）。',
  },
  {
    event_id: 'evt_labor_day',
    name: '五一劳动节',
    event_type: 'holiday',
    date_rule: { kind: 'fixed', md: '05-01' },
  },
  {
    event_id: 'evt_interim_report',
    name: '中报披露期',
    event_type: 'regulatory',
    date_rule: { kind: 'range', start_md: '07-01', end_md: '08-31' },
    description: '上市公司半年度报告披露期（7—8月），8月底为密集披露截止。',
  },
  {
    event_id: 'evt_national_day',
    name: '国庆节',
    event_type: 'holiday',
    date_rule: { kind: 'range', start_md: '10-01', end_md: '10-07' },
    description: '国庆长假，节后往往伴随消费数据与四季度布局窗口。',
  },
  {
    event_id: 'evt_q3_report',
    name: '三季报披露期',
    event_type: 'regulatory',
    date_rule: { kind: 'range', start_md: '10-08', end_md: '10-31' },
    description: '上市公司三季度报告集中披露期（10月）。',
  },
];

export const eventById = new Map(events.map((e) => [e.event_id, e]));
