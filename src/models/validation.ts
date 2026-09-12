/**
 * Entity 12: ValidationRecord —— 核验记录。
 *
 * 只记录"事实是否核验"，不计算 seasonality_score 等统计分数。
 *
 * 两个独立维度（见 docs/DATA_GOVERNANCE.md / docs/HISTORICAL_VALIDATION.md）：
 * - evidence_status：掌握了多少历史证据（L0—L4）
 * - verification_status：规律是否已通过统计/多来源验证
 *
 * 关键原则：L2 ≠ 规律成立。
 * 完成历史事实核验（L2）只说明"历史事实已被整理"，
 * 是否构成稳定规律需要统计验证（L3+）才能标记 statistically_supported。
 */

/** 证据等级：掌握了多少历史证据 */
export type EvidenceStatusLevel = 'L0' | 'L1' | 'L2' | 'L3' | 'L4';

/** 验证状态：规律是否已通过验证 */
export type VerificationStatus =
  | 'not_tested'
  | 'under_review'
  | 'statistically_supported'
  | 'cross_validated'
  | 'unsupported';

/**
 * 核验范围。Rule ≠ Campaign，两者不得混淆：
 * - 'rule'：验证整条 Rule（规律假设本身），此时 campaign_id 应省略
 * - 'campaign'：验证具体 HistoricalCampaign 的历史事实，此时 campaign_id 必填
 */
export type ValidationScope = 'rule' | 'campaign';

export interface ValidationRecord {
  validation_id: string;
  /** 核验范围（Rule / Campaign 不得混淆） */
  validation_scope: ValidationScope;
  rule_id: string;
  /** 可选：scope = 'campaign' 时必填（针对单条 Campaign 的核验记录）；scope = 'rule' 时省略 */
  campaign_id?: string;
  evidence_status: EvidenceStatusLevel;
  verification_status: VerificationStatus;
  /** 核验人；人工核验前为 'pending' */
  reviewer: string;
  /** 记录建立日期（ISO date） */
  created_at: string;
  /** 人工核验完成日期（ISO date）；未核验为 null —— 无 reviewer 就不得有 reviewed_at */
  reviewed_at: string | null;
  notes: string;
  /** 核验方法版本，如 'v1.5-manual-skeleton-001'，保证可追溯 */
  method_version: string;
}

/** V1.5 Pilot：样本规律的核验计划（3 条：夏季汽车 / 年底广电 / 国庆后大消费） */
export interface PilotPlan {
  pilot_id: string;
  rule_id: string;
  sample_name: string;
  base_pattern: string;
  /** 本条 Pilot 要验证的框架能力点 */
  test_focus: string[];
  status: 'planned' | 'in_progress' | 'fact_verified' | 'statistically_verified';
  created_at: string;
}
