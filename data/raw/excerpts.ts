import type { RawExcerpt } from '../../src/models';

/**
 * 原始材料摘录（raw 层）。
 *
 * 诚信说明：
 * - 原始材料全文未存档，以下为项目启动时（2026-09-12）由需求材料转述整理的要点摘录，
 *   保留原始经验口吻，不改写为客观事实。
 * - 这些摘录是 src_exp_001 的原文依据，用于审计追溯：任何 candidate Rule /
 *   Campaign 的描述都应能在这里找到对应出处。
 * - 摘录 ≠ 证据结论：材料"提到过"不等于"发生过"，更不等于"规律成立"。
 */
export const rawExcerpts: RawExcerpt[] = [
  {
    excerpt_id: 'exp_001_infra',
    source_id: 'src_exp_001',
    text: '春节前后：基建。（未提供精确日期与历史案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_infra_spring'],
  },
  {
    excerpt_id: 'exp_001_mining',
    source_id: 'src_exp_001',
    text: '春节前后：矿产。（未提供精确日期与历史案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_mining_spring'],
  },
  {
    excerpt_id: 'exp_001_power',
    source_id: 'src_exp_001',
    text: '4月底：电力。（未提供精确日期与历史案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_power_apr'],
  },
  {
    excerpt_id: 'exp_001_auto_window',
    source_id: 'src_exp_001',
    text: '6—8月：汽车。（材料明确给出月份区间，未提供各年案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_auto_summer'],
  },
  {
    excerpt_id: 'exp_001_auto_theme_2023',
    source_id: 'src_exp_001',
    text: '2023 汽车：减速器。',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_auto_summer'],
  },
  {
    excerpt_id: 'exp_001_auto_theme_2024',
    source_id: 'src_exp_001',
    text: '2024 汽车：自动驾驶。',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_auto_summer'],
  },
  {
    excerpt_id: 'exp_001_pharma',
    source_id: 'src_exp_001',
    text: '8月中报后：医药。（未提供精确日期与历史案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_pharma_post_interim'],
  },
  {
    excerpt_id: 'exp_001_consumption',
    source_id: 'src_exp_001',
    text: '国庆后—春节：大消费。（未提供年份案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_consumption_year_end'],
  },
  {
    excerpt_id: 'exp_001_media_window',
    source_id: 'src_exp_001',
    text: '广电：约11月—次年1月15日。',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_media_year_end'],
  },
  {
    excerpt_id: 'exp_001_media_years',
    source_id: 'src_exp_001',
    text: '年底广电：2021、2022、2023。（材料提及年份，未提供各年起止日期、强度与结果）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_media_year_end'],
  },
  {
    excerpt_id: 'exp_001_education',
    source_id: 'src_exp_001',
    text: '国庆后—春节：教育。（未提供年份案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_education_year_end'],
  },
  {
    excerpt_id: 'exp_001_textile',
    source_id: 'src_exp_001',
    text: '国庆后—春节：纺织服装。（未提供年份案例明细）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_textile_year_end'],
  },
  {
    excerpt_id: 'exp_001_disclosure',
    source_id: 'src_exp_001',
    text: '财报披露相关经验窗口。（未指明具体报表期与年份案例）',
    captured_at: '2026-09-12',
    related_rule_ids: ['rule_disclosure_q3'],
  },
];

export const excerptById = new Map(rawExcerpts.map((e) => [e.excerpt_id, e]));
