import type { PilotPlan } from '../../src/models';

/**
 * V1.5 Pilot：3 条样本规律的核验计划。
 * 用于压力测试核验框架本身（数据结构 / 完整性 / 跨年 / 关系），
 * 核验工作等待人工 Review 后正式开始（见 docs/HISTORICAL_VALIDATION.md）。
 */
export const pilots: PilotPlan[] = [
  {
    pilot_id: 'pilot_auto_summer',
    rule_id: 'rule_auto_summer',
    sample_name: '夏季汽车',
    base_pattern: '汽车',
    test_focus: [
      '季节性行业（calendar 窗口）',
      'Base Pattern 与 Annual Theme 分层（2023减速器 / 2024自动驾驶）',
      '候选 Campaign 日期推断标注（inferred / low）',
    ],
    status: 'planned',
    created_at: '2026-09-12',
  },
  {
    pilot_id: 'pilot_media_year_end',
    rule_id: 'rule_media_year_end',
    sample_name: '年底广电',
    base_pattern: '广电 / 传媒',
    test_focus: [
      '跨年窗口（约11月—次年1月中旬）',
      '小板块 / 题材炒作',
      '仅有年份提及、无细节证据时的处理（不创建 Campaign）',
      '龙头记录（Security，当前为空）',
      'Campaign 生命周期（start / peak / end）',
    ],
    status: 'planned',
    created_at: '2026-09-12',
  },
  {
    pilot_id: 'pilot_consumption_year_end',
    rule_id: 'rule_consumption_year_end',
    sample_name: '国庆后大消费',
    base_pattern: '大消费',
    test_focus: [
      '大行业 / 多 Theme（食品饮料 / 商业零售 / 旅游 / 纺织服装 / 教育 / 传媒）',
      '跨年窗口（国庆后—春节，终点浮动）',
      '一个 Base Pattern 对应多个 Theme',
      '一个时间窗口包含多个相关 Campaign（不得先验归并）',
    ],
    status: 'planned',
    created_at: '2026-09-12',
  },
];

export const pilotByRuleId = new Map(pilots.map((p) => [p.rule_id, p]));
