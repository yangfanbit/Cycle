import type { CampaignTheme, HistoricalCampaign, Source } from '../../src/models';

/**
 * 测试专用 fixture（Preflight 轮从 data/candidate/campaigns.ts 迁出）。
 *
 * 语义边界：
 * - fixtureCrossYearMedia 来自项目需求文档的"跨年结构示例"，不是真实历史行情，
 *   因此禁止进入生产数据层（data/），只允许测试引用。
 * - fixtureCandidateAuto* 是"材料提及题材 + 日期推断"的原候选行情，
 *   按 Preflight 方案 A 从生产层移除：未核验的线索只保留在 Evidence 中，
 *   人工核验后的真实行情进入 data/verified/campaigns.ts。
 * - 本文件中的 rule_id / theme_id 引用生产数据（真实存在），source_id 为
 *   fixture 自带的示例来源（fx_spec_001），不进入生产 sources 注册表。
 */

export const fixtureSpecSource: Source = {
  source_id: 'fx_spec_001',
  source_type: 'personal',
  title: '测试 fixture：需求文档结构示例来源（非生产数据）',
  captured_at: '2026-09-12',
};

/** 需求文档跨年结构示例：2026-11-01 → 2027-01-15（原 cmp_media_2026_2027） */
export const fixtureCrossYearMedia: HistoricalCampaign = {
  campaign_id: 'cmp_media_2026_2027',
  rule_id: 'rule_media_year_end',
  season_id: '2026-2027',
  campaign_year: 2026,
  start_date: '2026-11-01',
  end_date: '2027-01-15',
  peak_date: null,
  cross_year: true,
  strength: 'medium',
  result: 'unknown',
  description: '测试 fixture：需求文档中的跨年结构示例，用于验证跨年渲染与数据结构，不是真实历史行情记录。',
  source_id: 'fx_spec_001',
  start_date_basis: 'unknown',
  end_date_basis: 'unknown',
  date_confidence: 'low',
};

/** 原候选行情（材料提及年度题材，日期为典型窗口推断）：2023 汽车 = 减速器 */
export const fixtureCandidateAuto2023: HistoricalCampaign = {
  campaign_id: 'cmp_auto_2023',
  rule_id: 'rule_auto_summer',
  season_id: '2023',
  campaign_year: 2023,
  start_date: '2023-06-01',
  end_date: '2023-08-31',
  peak_date: null,
  cross_year: false,
  strength: 'medium',
  result: 'unknown',
  description: '测试 fixture：材料提及 2023 年汽车方向题材为减速器；日期为典型窗口近似（inferred/low）。',
  source_id: 'fx_spec_001',
  start_date_basis: 'inferred',
  end_date_basis: 'inferred',
  date_confidence: 'low',
};

/** 原候选行情（材料提及年度题材，日期为典型窗口推断）：2024 汽车 = 自动驾驶 */
export const fixtureCandidateAuto2024: HistoricalCampaign = {
  campaign_id: 'cmp_auto_2024',
  rule_id: 'rule_auto_summer',
  season_id: '2024',
  campaign_year: 2024,
  start_date: '2024-06-01',
  end_date: '2024-08-31',
  peak_date: null,
  cross_year: false,
  strength: 'medium',
  result: 'unknown',
  description: '测试 fixture：材料提及 2024 年汽车方向题材为自动驾驶；日期为典型窗口近似（inferred/low）。',
  source_id: 'fx_spec_001',
  start_date_basis: 'inferred',
  end_date_basis: 'inferred',
  date_confidence: 'low',
};

export const fixtureCampaigns: HistoricalCampaign[] = [
  fixtureCandidateAuto2023,
  fixtureCandidateAuto2024,
  fixtureCrossYearMedia,
];

/** 与 fixtureCampaigns 配套的行情—题材关系（含 Base Pattern related + Annual Theme main） */
export const fixtureCampaignThemes: CampaignTheme[] = [
  { campaign_id: 'cmp_auto_2023', theme_id: 'th_auto', role: 'related' },
  { campaign_id: 'cmp_auto_2023', theme_id: 'th_auto_reducer', role: 'main' },
  { campaign_id: 'cmp_auto_2024', theme_id: 'th_auto', role: 'related' },
  { campaign_id: 'cmp_auto_2024', theme_id: 'th_auto_adas', role: 'main' },
  { campaign_id: 'cmp_media_2026_2027', theme_id: 'th_media', role: 'main' },
];
