import type { ValidationRecord } from '../../src/models';

/**
 * 核验记录（validation 层）。
 *
 * 只记录"事实是否核验"，不计算任何统计分数。
 * 证据等级与验证状态是两个独立维度：
 * - L2（完成历史事实核验）≠ statistically_supported（规律统计验证成立）。
 * - 当前全部记录 verification_status = not_tested：Pilot 已立项、证据已登记，
 *   但历史事实核验尚未开始（等待人工 Review）。
 * - reviewer = 'pending' 表示尚未分配人工核验人。
 */
const REVIEWED_AT = '2026-09-12';
const METHOD_VERSION = 'v1.5-manual-skeleton-001';

export const validationRecords: ValidationRecord[] = [
  {
    validation_id: 'val_rule_auto_summer',
    rule_id: 'rule_auto_summer',
    evidence_status: 'L1',
    verification_status: 'not_tested',
    reviewer: 'pending',
    reviewed_at: REVIEWED_AT,
    notes:
      'Pilot 1（夏季汽车）。已登记3条 article 证据：经验窗口 + 2023减速器 / 2024自动驾驶两个年度题材。' +
      '候选 Campaign（cmp_auto_2023 / cmp_auto_2024）起止日期为典型窗口推断（inferred / low）。' +
      '待人工逐年核验起止日期、强度、结果后方可升 L2。L1 ≠ 规律成立。',
    method_version: METHOD_VERSION,
  },
  {
    validation_id: 'val_rule_media_year_end',
    rule_id: 'rule_media_year_end',
    evidence_status: 'L1',
    verification_status: 'not_tested',
    reviewer: 'pending',
    reviewed_at: REVIEWED_AT,
    notes:
      'Pilot 2（年底广电）。材料提及2021 / 2022 / 2023三年行情，但无任何年份的日期 / 强度 / 结果细节，' +
      '故未创建对应 Campaign（不编造记录）。跨年窗口（约11月—次年1月中旬）的逐年事实待人工核验。' +
      '注意：材料提及 ≠ 历史事实，须逐年到行情数据中核实。',
    method_version: METHOD_VERSION,
  },
  {
    validation_id: 'val_rule_consumption_year_end',
    rule_id: 'rule_consumption_year_end',
    evidence_status: 'L0',
    verification_status: 'not_tested',
    reviewer: 'pending',
    reviewed_at: REVIEWED_AT,
    notes:
      'Pilot 3（国庆后大消费）。仅有经验窗口描述（国庆后—春节），无任何年份案例证据（L0）。' +
      '核验时注意：大消费为复合 Base Pattern，食品饮料 / 商业零售 / 旅游 / 纺织服装 / 教育 / 传媒等' +
      '子方向可能各自构成独立 Campaign，不得先验地归并为同一行情。',
    method_version: METHOD_VERSION,
  },
];

export const validationByRuleId = new Map(validationRecords.map((r) => [r.rule_id, r]));
