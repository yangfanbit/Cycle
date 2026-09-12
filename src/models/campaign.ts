import type { CampaignResult, CampaignStrength } from './common';

/**
 * Entity 4: HistoricalCampaign —— 一次具体的历史行情
 * 跨年行情用 cross_year=true 的单条记录表示，绝不拆成两条。
 */
export interface HistoricalCampaign {
  campaign_id: string;
  rule_id: string;
  /** 行情季标识，如 "2026-2027"（跨年）或 "2024"（年内） */
  season_id: string;
  /** 行情起始年份 */
  campaign_year: number;
  /** ISO 完整日期 YYYY-MM-DD */
  start_date: string;
  end_date: string;
  cross_year: boolean;
  strength: CampaignStrength;
  result: CampaignResult;
  description?: string;
  source_id: string;
}

/** Entity 8: CampaignSecurity —— 行情与代表股票的关联 */
export interface CampaignSecurity {
  campaign_id: string;
  security_id: string;
  role: 'leader' | 'second_leader' | 'follow' | 'representative';
}
