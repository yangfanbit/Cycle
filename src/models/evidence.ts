/**
 * Entity 11: Evidence —— 历史证据。
 *
 * 概念链：Source（来源） → Evidence（证据） → Historical Fact / Campaign（历史事实）。
 * Evidence 是证据，不是结论：它只记录"某来源在某时说了/显示了什么"，
 * 不代表规律成立，也不得被改写成市场事实。
 */
export type EvidenceType =
  | 'market_data'
  | 'article'
  | 'official'
  | 'news'
  | 'manual_review'
  | 'other';

export interface Evidence {
  evidence_id: string;
  source_id: string;
  evidence_type: EvidenceType;
  /** 证据内容描述（保留来源口吻，不改写为客观事实） */
  description: string;
  /** 证据指向的日期；来源未提供时为 null（合法状态，禁止编造） */
  date?: string | null;
  confidence: 'high' | 'medium' | 'low';
  /** 可选关联：候选规律 */
  rule_id?: string;
  /** 可选关联：候选行情 */
  campaign_id?: string;
  /** 可选关联：题材 */
  theme_id?: string;
  notes?: string;
}
