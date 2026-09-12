/** Entity 1: Source —— 信息来源 */
export type SourceType =
  | 'personal'
  | 'article'
  | 'official'
  | 'research'
  | 'market_data'
  | 'quant_verification';

export interface Source {
  source_id: string;
  source_type: SourceType;
  title: string;
  author?: string;
  url?: string;
  published_at?: string; // ISO date
  captured_at: string;   // ISO date
  description?: string;
}

/**
 * 原始材料摘录（raw 层）。
 * 保留来源的原始口吻与要点，用于审计追溯；
 * 不得改写为客观事实，是 Evidence 与候选 Rule 的最上游依据。
 */
export interface RawExcerpt {
  excerpt_id: string;
  source_id: string;
  /** 摘录内容（保留原始表述） */
  text: string;
  captured_at: string;
  /** 相关候选规律 */
  related_rule_ids?: string[];
}
