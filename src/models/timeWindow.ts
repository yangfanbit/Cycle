import type { MonthDay } from './common';

/** Entity 3: TimeWindow —— 规律的时间窗口 */
export type WindowType =
  | 'calendar'        // 固定日期窗口（MM-DD → MM-DD）
  | 'relative_event'  // 相对事件窗口（anchor_event + 偏移天数）
  | 'holiday'         // 节假日相关
  | 'regulatory'      // 监管/披露节点相关
  | 'empirical';      // 经验窗口（无精确日期）

export interface TimeWindow {
  window_id: string;
  rule_id: string;
  window_type: WindowType;
  /** 固定窗口起点，MM-DD。经验窗口可为空 */
  start_md?: MonthDay;
  /** 固定窗口终点，MM-DD。end_md < start_md 表示跨年窗口 */
  end_md?: MonthDay;
  /** 相对窗口锚点事件 id（Event.event_id） */
  anchor_event?: string;
  /** 相对锚点的起点偏移（天，负数为之前） */
  start_offset_days?: number;
  /** 相对锚点的终点偏移（天） */
  end_offset_days?: number;
  /** 提前观察天数（Pre-heat） */
  preheat_days: number;
  /** 窗口描述（经验窗口的文字说明，如"国庆后—春节"） */
  note?: string;
}
