import type { CampaignResult, CampaignStrength } from './common';

/**
 * 启动 / 结束日期的判定方式（人工核验机制，见 docs/HISTORICAL_VALIDATION.md）：
 * - observed      人工从行情数据中观察确认
 * - inferred      由窗口/材料推断（近似）
 * - official_event 依据官方事件日期（如披露期）
 * - unknown       未知
 * 禁止伪造精确日期：无法确认时用 unknown + 低 confidence。
 */
export type DateBasis = 'observed' | 'inferred' | 'official_event' | 'unknown';

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
  /** 行情峰值日期；未核验时省略或 null（合法状态，禁止编造） */
  peak_date?: string | null;
  cross_year: boolean;
  strength: CampaignStrength;
  result: CampaignResult;
  description?: string;
  source_id: string;
  /** 启动 / 结束日期判定方式（V1.5 起补充，可选以兼容旧数据） */
  start_date_basis?: DateBasis;
  end_date_basis?: DateBasis;
  /** 日期整体置信度 */
  date_confidence?: 'high' | 'medium' | 'low';
}

/** Entity 8: CampaignSecurity —— 行情与代表股票的关联 */
export interface CampaignSecurity {
  campaign_id: string;
  security_id: string;
  role: 'leader' | 'second_leader' | 'follow' | 'representative';
}
