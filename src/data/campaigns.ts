import type { CampaignSecurity, CampaignTheme, HistoricalCampaign } from '../models';

/**
 * 历史行情（HistoricalCampaign）。
 *
 * 数据诚信说明：
 * - 仅录入"来源材料明确提到"的题材—年份对应关系（2023汽车=减速器、2024汽车=自动驾驶）。
 * - 材料未提供精确起止日期，下列日期为该规律典型窗口的近似，description 中已注明。
 * - 未编造成交、涨幅等任何量化数据；result 一律记为 unknown，待历史数据验证。
 * - cmp_media_2026_2027 为需求文档中的跨年结构示例，用于验证跨年渲染，非真实历史记录。
 * - 其余规律暂无历史案例资料，UI 显示"历史案例待补充"。
 */
export const campaigns: HistoricalCampaign[] = [
  {
    campaign_id: 'cmp_auto_2023',
    rule_id: 'rule_auto_summer',
    season_id: '2023',
    campaign_year: 2023,
    start_date: '2023-06-01',
    end_date: '2023-08-31',
    cross_year: false,
    strength: 'medium',
    result: 'unknown',
    description:
      '来源材料提及：2023年汽车方向的具体题材为"减速器"。' +
      '起止日期为该规律典型窗口（6—8月）的近似，精确日期、强度与结果待历史数据核实。',
    source_id: 'src_exp_001',
  },
  {
    campaign_id: 'cmp_auto_2024',
    rule_id: 'rule_auto_summer',
    season_id: '2024',
    campaign_year: 2024,
    start_date: '2024-06-01',
    end_date: '2024-08-31',
    cross_year: false,
    strength: 'medium',
    result: 'unknown',
    description:
      '来源材料提及：2024年汽车方向的具体题材为"自动驾驶"。' +
      '起止日期为该规律典型窗口（6—8月）的近似，精确日期、强度与结果待历史数据核实。',
    source_id: 'src_exp_001',
  },
  {
    campaign_id: 'cmp_media_2026_2027',
    rule_id: 'rule_media_year_end',
    season_id: '2026-2027',
    campaign_year: 2026,
    start_date: '2026-11-01',
    end_date: '2027-01-15',
    cross_year: true,
    strength: 'medium',
    result: 'unknown',
    description:
      '跨年结构示例数据（来自项目需求文档），用于验证跨年行情作为一条完整 Campaign ' +
      '在2026与2027两个自然年中的连续渲染。不是真实历史行情记录。',
    source_id: 'src_spec_001',
  },
];

export const campaignThemes: CampaignTheme[] = [
  { campaign_id: 'cmp_auto_2023', theme_id: 'th_auto', role: 'related' },
  { campaign_id: 'cmp_auto_2023', theme_id: 'th_auto_reducer', role: 'main' },
  { campaign_id: 'cmp_auto_2024', theme_id: 'th_auto', role: 'related' },
  { campaign_id: 'cmp_auto_2024', theme_id: 'th_auto_adas', role: 'main' },
  { campaign_id: 'cmp_media_2026_2027', theme_id: 'th_media', role: 'main' },
];

/** V1 暂无考证过的代表股票，保留空表与查询接口 */
export const securities: never[] = [];
export const campaignSecurities: CampaignSecurity[] = [];

export const campaignById = new Map(campaigns.map((c) => [c.campaign_id, c]));

export function campaignsOfRule(ruleId: string): HistoricalCampaign[] {
  return campaigns
    .filter((c) => c.rule_id === ruleId)
    .sort((a, b) => (a.start_date < b.start_date ? -1 : 1));
}

export function themesOfCampaign(campaignId: string): CampaignTheme[] {
  return campaignThemes.filter((ct) => ct.campaign_id === campaignId);
}
