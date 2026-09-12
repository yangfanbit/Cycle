/**
 * 数据层唯一出口（barrel）。
 * 实体数据位于根目录 data/（raw / candidate / verified / validation 四层，
 * 语义见 data/README.md 与 docs/HISTORICAL_VALIDATION.md），
 * 应用代码只从本文件导入，不直接引用 data/ 内部路径。
 */
import type { CampaignTheme, Event, HistoricalCampaign } from '../models';
import { resolveEventForYear } from '../utils';
import { campaignThemes } from '../../data/candidate/campaigns';
import { events } from '../../data/candidate/events';
import { verifiedCampaigns, verifiedCampaignThemes } from '../../data/verified/campaigns';

export * from '../../data/raw/sources';
export * from '../../data/raw/excerpts';
export * from '../../data/candidate/rules';
export * from '../../data/candidate/campaigns';
export * from '../../data/candidate/themes';
export * from '../../data/candidate/events';
export * from '../../data/verified/campaigns';
export * from '../../data/validation/evidence';
export * from '../../data/validation/records';
export * from '../../data/validation/pilot';

/** 锚点事件解析器：供 windowStatus 计算 relative_event 窗口使用 */
export function anchorResolver(eventId: string, seasonYear: number): string | null {
  const event: Event | undefined = events.find((e) => e.event_id === eventId);
  if (!event) return null;
  const resolved = resolveEventForYear(event, seasonYear);
  return resolved ? resolved.start : null;
}

// ============ 行情聚合查询：candidate（当前恒空）+ verified ============
// Preflight 方案 A 后：生产层只存在已核验行情（verified）；
// 未核验线索仅存于 Evidence，不进入行情视图。聚合入口保持不变，
// 未来核验产出写入 data/verified 后应用自动可见。

/** 生产层全部行情 = 已核验历史行情 */
export const allCampaigns: HistoricalCampaign[] = [...verifiedCampaigns];

export const campaignById = new Map(allCampaigns.map((c) => [c.campaign_id, c]));

/** 该规律的已核验历史案例（按开始日期升序；不过滤 failed / weak 年份） */
export function campaignsOfRule(ruleId: string): HistoricalCampaign[] {
  return allCampaigns
    .filter((c) => c.rule_id === ruleId)
    .sort((a, b) => (a.start_date < b.start_date ? -1 : 1));
}

const allCampaignThemes: CampaignTheme[] = [...campaignThemes, ...verifiedCampaignThemes];

export function themesOfCampaign(campaignId: string): CampaignTheme[] {
  return allCampaignThemes.filter((ct) => ct.campaign_id === campaignId);
}
