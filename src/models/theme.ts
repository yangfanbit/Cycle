/** Entity 5: Theme —— 题材（支持父子层级） */
export type ThemeType = 'sector' | 'concept' | 'industry';

export interface Theme {
  theme_id: string;
  name: string;
  theme_type: ThemeType;
  parent_theme_id?: string;
  description?: string;
}

/** Entity 6: CampaignTheme —— 行情与题材的关联 */
export interface CampaignTheme {
  campaign_id: string;
  theme_id: string;
  role: 'main' | 'secondary' | 'catalyst' | 'related';
}
