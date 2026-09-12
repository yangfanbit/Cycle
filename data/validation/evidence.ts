import type { Evidence } from '../../src/models';

/**
 * 证据记录（validation 层）。
 *
 * Evidence 是证据，不是结论：
 * - 只登记"来源说了什么 / 行情数据显示了什么"，由人工核验决定它支撑哪条 Campaign。
 * - 全部来自 src_exp_001 的为 article 型证据（二手经验材料），confidence 一律 low。
 * - date 为 null 表示来源未提供日期——禁止编造。
 * - Preflight 方案 A：证据不引用 candidate Campaign（其已从生产层移除）；
 *   仅关联 rule / theme。人工核验后创建的 verified Campaign 反向引用证据。
 * - 当前无 market_data / official 型证据（未接行情数据源）。
 */
export const evidences: Evidence[] = [
  // ============ Pilot 1：夏季汽车 ============
  {
    evidence_id: 'ev_auto_window',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '经验材料给出汽车方向的关注窗口约为6—8月（材料原文为月份区间，未提供精确起止日期）。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_auto_summer',
  },
  {
    evidence_id: 'ev_auto_theme_2023',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '来源材料提及：2023年汽车方向的年度题材为"减速器"。' +
      '未提供该年行情的起止日期、强度与结果。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_auto_summer',
    theme_id: 'th_auto_reducer',
  },
  {
    evidence_id: 'ev_auto_theme_2024',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '来源材料提及：2024年汽车方向的年度题材为"自动驾驶"。' +
      '未提供该年行情的起止日期、强度与结果。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_auto_summer',
    theme_id: 'th_auto_adas',
  },

  // ============ Pilot 2：年底广电 ============
  {
    evidence_id: 'ev_media_window',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '经验材料给出年底广电窗口：约11月—次年1月15日（跨年，未提供各年精确日期）。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_media_year_end',
  },
  {
    evidence_id: 'ev_media_years',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '来源材料提及2021、2022、2023年年底广电 / 传媒方向存在行情。' +
      '未提供任何一年的具体起止日期、强度、结果与代表标的。' +
      '仅有年份提及，不足以创建 Campaign 记录，待人工核验。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_media_year_end',
    notes: '此为 L1 级证据线索：找到历史证据提及，但历史事实本身尚未核验。',
  },

  // ============ Pilot 3：国庆后大消费 ============
  {
    evidence_id: 'ev_consumption_window',
    source_id: 'src_exp_001',
    evidence_type: 'article',
    description:
      '经验材料给出国庆后至春节的大消费关注窗口（跨年，终点随春节浮动）。' +
      '未提及任何年份的具体案例。',
    date: null,
    confidence: 'low',
    rule_id: 'rule_consumption_year_end',
    notes: 'L0 级：仅有经验窗口描述，尚无任何年份的历史证据。',
  },
];

export const evidenceById = new Map(evidences.map((e) => [e.evidence_id, e]));

export function evidencesOfRule(ruleId: string): Evidence[] {
  return evidences.filter((e) => e.rule_id === ruleId);
}

/**
 * 查询某条 HistoricalCampaign 的支撑证据。
 * 未来 verified Campaign 必须能追溯到至少一条 Evidence（不允许无证据的事实）。
 * 可选 list 参数仅用于测试注入，生产代码从 src/data/index.ts 正常调用。
 */
export function evidencesOfCampaign(campaignId: string, list: Evidence[] = evidences): Evidence[] {
  return list.filter((e) => e.campaign_id === campaignId);
}
