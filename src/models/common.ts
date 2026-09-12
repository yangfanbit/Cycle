/**
 * 通用类型定义
 * 所有实体字段命名与数据模型文档保持一致（snake_case），
 * 便于未来直接迁移到 SQLite / PostgreSQL。
 */

/** 规律 / 假设的生命周期状态 */
export type RuleStatus =
  | 'candidate'     // 候选（来自经验材料，未验证）
  | 'under_review'  // 研究中
  | 'verified'      // 已验证（V1 不应出现，除非有真实统计来源）
  | 'weak'          // 证据较弱
  | 'rejected'      // 已证伪
  | 'deprecated';   // 废弃

/** 历史行情强度 */
export type CampaignStrength = 'strong' | 'medium' | 'weak';

/** 历史行情结果（必须允许失败 / 弱表现） */
export type CampaignResult = 'positive' | 'neutral' | 'weak' | 'failed' | 'unknown';

/** 统计信息占位：V1 不允许写入未经计算的量化分数 */
export interface StatisticsPlaceholder {
  status: 'not_verified' | 'computed';
  /** 未来 V1.5+ 的可追溯统计字段，全部可选 */
  sample_count?: number;
  launch_date_median?: string;
  launch_date_std?: number;
  average_duration?: number;
  excess_return?: number;
  repeat_rate?: number;
  seasonality_score?: number;
  /** 统计来源说明，computed 时必填 */
  methodology?: string;
}

/** MM-DD 格式的年内日期（不含年份） */
export type MonthDay = string;
