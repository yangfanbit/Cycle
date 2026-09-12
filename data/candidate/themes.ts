import type { CampaignTheme, Theme } from '../../src/models';

/**
 * 题材库。Base Pattern（底层行业）与 Annual Theme（年度具体题材）分离：
 * 父子层级通过 parent_theme_id 表达。
 */
export const themes: Theme[] = [
  // 底层行业
  { theme_id: 'th_mining', name: '矿产', theme_type: 'sector' },
  { theme_id: 'th_infra', name: '基建', theme_type: 'sector' },
  { theme_id: 'th_power', name: '电力', theme_type: 'sector' },
  { theme_id: 'th_auto', name: '汽车', theme_type: 'sector' },
  { theme_id: 'th_pharma', name: '医药', theme_type: 'sector' },
  { theme_id: 'th_consumption', name: '大消费', theme_type: 'sector' },
  { theme_id: 'th_media', name: '广电 / 传媒', theme_type: 'sector' },
  { theme_id: 'th_education', name: '教育', theme_type: 'sector' },

  // 大消费子题材
  { theme_id: 'th_food', name: '食品饮料', theme_type: 'industry', parent_theme_id: 'th_consumption' },
  { theme_id: 'th_retail', name: '商业零售', theme_type: 'industry', parent_theme_id: 'th_consumption' },
  { theme_id: 'th_tourism', name: '旅游', theme_type: 'industry', parent_theme_id: 'th_consumption' },
  { theme_id: 'th_textile', name: '纺织服装', theme_type: 'industry', parent_theme_id: 'th_consumption' },
  { theme_id: 'th_prepared_food', name: '预制菜', theme_type: 'concept', parent_theme_id: 'th_consumption' },

  // 汽车历年具体题材（Annual Theme，不等于底层行业）
  { theme_id: 'th_auto_reducer', name: '减速器', theme_type: 'concept', parent_theme_id: 'th_auto',
    description: '2023 年汽车方向的具体炒作题材（来源材料提及）。' },
  { theme_id: 'th_auto_adas', name: '自动驾驶', theme_type: 'concept', parent_theme_id: 'th_auto',
    description: '2024 年汽车方向的具体炒作题材（来源材料提及）。' },
  { theme_id: 'th_auto_cockpit', name: '智能座舱', theme_type: 'concept', parent_theme_id: 'th_auto' },
];

/** 行情—题材关联在 campaigns.ts 中随行情一起定义，此处只提供查询辅助 */
export const themeById = new Map(themes.map((t) => [t.theme_id, t]));

export function childrenOf(themeId: string, all: Theme[] = themes): Theme[] {
  return all.filter((t) => t.parent_theme_id === themeId);
}

export type { CampaignTheme };
