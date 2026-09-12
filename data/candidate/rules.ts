import type { Rule, TimeWindow } from '../../src/models';

const NOW = '2026-09-12';
const NOT_VERIFIED = { status: 'not_verified' } as const;

/**
 * 候选规律（Rule）。
 * ⚠️ 以下全部来自用户提供的经验材料，status 一律为 candidate，
 * 描述保留原始经验口吻，未改写为"客观事实"，未编造精确日期与胜率。
 * 日期不确定的使用 window_type='empirical' 并在 note 中说明。
 */
export const rules: Rule[] = [
  {
    rule_id: 'rule_infra_spring',
    name: '春节前后基建关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '基建',
    description: '经验材料：春节前后，基建方向容易出现关注窗口（原文为经验判断，未验证）。',
    mechanism: '经验推测：年初政策与开工预期。待验证。',
    tags: ['春节', '基建', '政策预期'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_mining_spring',
    name: '春节前后矿产关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '矿产',
    description: '经验材料：春节前后，矿产方向容易出现关注窗口（原文为经验判断，未验证）。',
    tags: ['春节', '矿产', '资源'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_power_apr',
    name: '4月底电力关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '电力',
    description: '经验材料：4月底附近，电力方向容易出现关注窗口（原文为经验判断，未验证）。',
    mechanism: '经验推测：迎峰度夏前的预期发酵。待验证。',
    tags: ['电力', '夏季'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_auto_summer',
    name: '6—8月汽车关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '汽车',
    description:
      '经验材料：6—8月汽车方向容易出现关注窗口。注意：底层行业（汽车）与每年的具体题材' +
      '（如2023年减速器、2024年自动驾驶）是两个层级，不可混为一谈。',
    tags: ['汽车', '夏季', '题材轮动'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_pharma_post_interim',
    name: '中报后医药关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '医药',
    description: '经验材料：8月中报披露后，医药方向容易出现关注窗口（原文为经验判断，未验证）。',
    tags: ['医药', '中报'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_consumption_year_end',
    name: '国庆后—春节大消费关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '大消费',
    description:
      '经验材料：国庆后至春节，大消费方向容易出现关注窗口（原文为经验判断，未验证）。' +
      '窗口跨年，终点随春节日期浮动。',
    tags: ['大消费', '国庆后', '春节', '跨年'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_media_year_end',
    name: '年底广电 / 传媒关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '广电 / 传媒',
    description:
      '经验材料：年底（约11月起）至次年1月中旬，广电 / 传媒方向容易出现关注窗口' +
      '（原文为经验判断，未验证）。窗口跨年。',
    tags: ['广电', '传媒', '年底', '跨年'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_education_year_end',
    name: '国庆后—春节教育关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '教育',
    description: '经验材料：国庆后至春节，教育方向容易出现关注窗口（原文为经验判断，未验证）。窗口跨年。',
    tags: ['教育', '国庆后', '跨年'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_textile_year_end',
    name: '国庆后—春节纺织服装关注窗口',
    rule_type: 'seasonal_sector',
    base_sector: '纺织服装',
    description: '经验材料：国庆后至春节，纺织服装方向容易出现关注窗口（原文为经验判断，未验证）。窗口跨年。',
    tags: ['纺织服装', '国庆后', '跨年'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
  {
    rule_id: 'rule_disclosure_q3',
    name: '三季报披露期业绩关注窗口',
    rule_type: 'disclosure',
    base_sector: '全市场（业绩主线）',
    description:
      '经验材料：财报披露期附近，市场关注度容易向业绩主线集中（原文为经验判断，未验证）。' +
      '本条以三季报披露期为示例窗口，一季报 / 中报同类窗口待补充。',
    tags: ['财报', '三季报', '业绩'],
    status: 'candidate',
    source_id: 'src_exp_001',
    statistics: { ...NOT_VERIFIED },
    created_at: NOW,
    updated_at: NOW,
  },
];

/**
 * 规律对应的时间窗口。
 * relative_event：锚点 + 偏移，偏移天数为经验估计（见 note）。
 * empirical：带 md 的经验估计窗口，可计算但日期未精确验证。
 */
export const timeWindows: TimeWindow[] = [
  {
    window_id: 'win_infra_spring',
    rule_id: 'rule_infra_spring',
    window_type: 'relative_event',
    anchor_event: 'evt_spring_festival',
    start_offset_days: -20,
    end_offset_days: 30,
    preheat_days: 15,
    note: '相对春节的经验窗口：约节前20天至节后30天。偏移天数为经验估计，待历史数据验证。',
  },
  {
    window_id: 'win_mining_spring',
    rule_id: 'rule_mining_spring',
    window_type: 'relative_event',
    anchor_event: 'evt_spring_festival',
    start_offset_days: -20,
    end_offset_days: 30,
    preheat_days: 15,
    note: '相对春节的经验窗口：约节前20天至节后30天。偏移天数为经验估计，待历史数据验证。',
  },
  {
    window_id: 'win_power_apr',
    rule_id: 'rule_power_apr',
    window_type: 'empirical',
    start_md: '04-20',
    end_md: '05-10',
    preheat_days: 10,
    note: '经验估计窗口：约4月下旬至5月上旬，精确起止日期待验证。',
  },
  {
    window_id: 'win_auto_summer',
    rule_id: 'rule_auto_summer',
    window_type: 'calendar',
    start_md: '06-01',
    end_md: '08-31',
    preheat_days: 15,
    note: '经验材料明确给出6—8月。',
  },
  {
    window_id: 'win_pharma_post_interim',
    rule_id: 'rule_pharma_post_interim',
    window_type: 'empirical',
    start_md: '08-15',
    end_md: '09-30',
    preheat_days: 10,
    note: '经验估计窗口：约8月中报密集披露后至9月底，精确起止日期待验证。',
  },
  {
    window_id: 'win_consumption_year_end',
    rule_id: 'rule_consumption_year_end',
    window_type: 'empirical',
    start_md: '10-08',
    end_md: '01-31',
    preheat_days: 20,
    approximate: true,
    note: '复合窗口（国庆后→春节前）的近似表达：终点随春节逐年浮动，此处以01-31近似展示，非精确结束日；跨年窗口。后续统一支持 mixed anchor window。',
  },
  {
    window_id: 'win_media_year_end',
    rule_id: 'rule_media_year_end',
    window_type: 'empirical',
    start_md: '11-01',
    end_md: '01-15',
    preheat_days: 20,
    note: '经验窗口：约11月至次年1月15日，跨年窗口。',
  },
  {
    window_id: 'win_education_year_end',
    rule_id: 'rule_education_year_end',
    window_type: 'empirical',
    start_md: '10-08',
    end_md: '01-31',
    preheat_days: 20,
    approximate: true,
    note: '复合窗口（国庆后→春节前）的近似表达：终点随春节逐年浮动，此处以01-31近似展示，非精确结束日；跨年窗口。后续统一支持 mixed anchor window。',
  },
  {
    window_id: 'win_textile_year_end',
    rule_id: 'rule_textile_year_end',
    window_type: 'empirical',
    start_md: '10-08',
    end_md: '01-31',
    preheat_days: 20,
    approximate: true,
    note: '复合窗口（国庆后→春节前）的近似表达：终点随春节逐年浮动，此处以01-31近似展示，非精确结束日；跨年窗口。后续统一支持 mixed anchor window。',
  },
  {
    window_id: 'win_disclosure_q3',
    rule_id: 'rule_disclosure_q3',
    window_type: 'empirical',
    start_md: '10-15',
    end_md: '11-15',
    preheat_days: 10,
    note: '经验估计窗口：三季报密集披露期后半段起，精确起止日期待验证。',
  },
];

export const ruleById = new Map(rules.map((r) => [r.rule_id, r]));

export function windowsOfRule(ruleId: string): TimeWindow[] {
  return timeWindows.filter((w) => w.rule_id === ruleId);
}
