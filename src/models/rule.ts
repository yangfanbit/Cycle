import type { RuleStatus, StatisticsPlaceholder } from './common';

/** Entity 2: Rule —— 一条待研究的历史规律假设 */
export type RuleType =
  | 'seasonal_sector'  // 季节性行业规律
  | 'event_driven'     // 事件驱动
  | 'disclosure'       // 财报披露相关
  | 'other';

export interface Rule {
  rule_id: string;
  name: string;
  rule_type: RuleType;
  /** 底层行业/方向，如"广电"、"大消费" */
  base_sector: string;
  /** 原始经验描述（保留原文，不改写为客观事实） */
  description: string;
  /** 经验中提到的可能机理（可选） */
  mechanism?: string;
  tags: string[];
  status: RuleStatus;
  source_id: string;
  statistics?: StatisticsPlaceholder;
  created_at: string;
  updated_at: string;
}
