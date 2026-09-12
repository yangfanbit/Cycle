import type { CampaignResult, CampaignStrength, RuleStatus } from '../models';
import type { WindowPhase } from '../utils';

export const PHASE_LABEL: Record<WindowPhase, string> = {
  ACTIVE: '当前窗口',
  PRE_HEAT: '提前观察',
  NOT_ACTIVE: '尚未进入',
  ENDED: '已过窗口',
};

export const RULE_STATUS_LABEL: Record<RuleStatus, string> = {
  candidate: '候选（待验证）',
  under_review: '研究中',
  verified: '已验证',
  weak: '证据较弱',
  rejected: '已证伪',
  deprecated: '已废弃',
};

export const STRENGTH_LABEL: Record<CampaignStrength, string> = {
  strong: '强',
  medium: '中',
  weak: '弱',
};

export const RESULT_LABEL: Record<CampaignResult, string> = {
  positive: '表现较强',
  neutral: '中性',
  weak: '偏弱',
  failed: '失败',
  unknown: '未知（待验证）',
};

export const RULE_TYPE_LABEL: Record<string, string> = {
  seasonal_sector: '季节性行业',
  event_driven: '事件驱动',
  disclosure: '财报披露',
  other: '其他',
};

export const ROLE_LABEL: Record<string, string> = {
  main: '主题材',
  secondary: '次题材',
  catalyst: '催化',
  related: '相关',
  leader: '龙头',
  second_leader: '二龙',
  follow: '跟风',
  representative: '代表',
};

/** 各底层行业的条形配色（克制、低饱和） */
export const SECTOR_COLORS: Record<string, string> = {
  基建: '#8a7f6a',
  矿产: '#7a6a8a',
  电力: '#5a8a7a',
  汽车: '#5a7a9a',
  医药: '#9a6a6a',
  大消费: '#b08355',
  '广电 / 传媒': '#6a8aaa',
  教育: '#7a9a6a',
  纺织服装: '#aa7a8a',
  '全市场（业绩主线）': '#7a8494',
};

export function sectorColor(baseSector: string): string {
  return SECTOR_COLORS[baseSector] ?? '#7a8494';
}
