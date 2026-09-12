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
