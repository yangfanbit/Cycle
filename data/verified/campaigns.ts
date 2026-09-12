import type { CampaignTheme, HistoricalCampaign } from '../../src/models';

/**
 * 已人工核验的历史事实（verified 层，Evidence Status = L2）。
 *
 * 录入标准（见 docs/HISTORICAL_VALIDATION.md）：
 * 1. 起止日期经人工逐年核验：date_basis 为 observed，
 *    或 inferred 且 date_confidence >= medium（须注明推断依据）。
 * 2. result / strength 有明确判定依据（引用行情数据或可靠来源）。
 * 3. source_id 可追溯（通常为 market_data / manual_review 型来源）。
 *
 * 当前：0 条。"缺少数据"是合法状态——不得为了填充 verified 层而编造历史事实。
 * 3 条 Pilot 规律（汽车 / 广电 / 大消费）完成人工核验后，记录写入此处，
 * 并在 CHANGELOG.md 留痕。
 */
export const verifiedCampaigns: HistoricalCampaign[] = [];

/** 已核验行情的题材关联（与 verifiedCampaigns 配套） */
export const verifiedCampaignThemes: CampaignTheme[] = [];
