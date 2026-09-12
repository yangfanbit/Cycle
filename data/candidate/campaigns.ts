import type { CampaignSecurity, CampaignTheme, HistoricalCampaign } from '../../src/models';

/**
 * 候选行情层（candidate）。
 *
 * Preflight 决策（方案 A，见 docs/HISTORICAL_VALIDATION.md）：
 * - 未核验的行情线索不再以 HistoricalCampaign 形态存在于生产层。
 *   材料提及的年度题材（2023汽车=减速器、2024汽车=自动驾驶）只保留在
 *   data/validation/evidence.ts 的 Evidence 记录中。
 * - 人工核验完成后创建的真实 HistoricalCampaign 直接进入
 *   data/verified/campaigns.ts（L2），不经过本层。
 * - 原跨年结构示例（cmp_media_2026_2027）已迁至 tests/fixtures/（非真实行情，
 *   禁止回到生产层）。
 * - 因此本层数组当前为空——"缺少数据"是合法状态，不为填充而编造。
 *
 * 查询辅助（campaignById / campaignsOfRule / themesOfCampaign）在
 * src/data/index.ts 中聚合 candidate + verified 两层。
 */
export const campaigns: HistoricalCampaign[] = [];
export const campaignThemes: CampaignTheme[] = [];

/** V1 暂无考证过的代表股票，保留空表与查询接口 */
export const securities: never[] = [];
export const campaignSecurities: CampaignSecurity[] = [];
