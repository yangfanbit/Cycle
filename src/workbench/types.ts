/** 研究工作台的数据类型（v0.74）。全部字段来自确定性派生产物，不新增事实。 */

export type ItemKind = 'HISTORICAL_OBJECT' | 'POLICY_EVENT' | 'THEME_MAP_EVENT';
export type Uncertainty = 'LOW' | 'MEDIUM' | 'HIGH';

export interface WorkbenchItem {
  id: string;
  kind: ItemKind;
  title: string;
  date: string | null;
  year: number | null;
  themes: string[];
  doc_class?: string | null;
  status?: string | null;
  source: {
    name: string | null;
    publisher: string | null;
    url: string | null;
    source_kind: string;
    source_id?: string | null;
    file?: string | null;
  };
  why: string;
  uncertainty: Uncertainty;
  uncertainty_reason: string;
  board_series: string | null;
  url: string | null;
}

export interface IndexDoc {
  artifact: string;
  artifact_version: string;
  generated_at: string;
  as_of: string;
  source_artifacts: { file: string; sha256_16: string }[];
  caliber: {
    purpose: string;
    effectiveness_definition: string;
    not: string[];
    url_policy: string;
    uncertainty_levels: string;
  };
  counts: { total: number; by_kind: Record<string, number>; with_external_url: number };
  items: WorkbenchItem[];
}

export interface EvalRow {
  board_series: string;
  board: string;
  month: number;
  kind: string;
  tier: string;
  hit_rate: number;
  n_years: number;
  k: number;
  k_source: string;
  wilson_low: number;
  wilson_high: number;
  median_excess_pct: number | null;
  oos_tests: number | null;
  oos_status: string | null;
  evidence_grade: string | null;
  discovery_basis: string | null;
  pit_basis: string | null;
  priority_score: number;
  priority_reason: string;
  usage: 'INTERNAL_EVAL_ONLY';
  calibrated: false;
  is_probability: false;
}

export interface EvalDoc {
  artifact: string;
  artifact_version: string;
  generated_at: string;
  source: { file: string; sha256_16: string; artifact_version?: string; as_of?: string };
  caliber: {
    usage: string;
    purpose: string;
    score_definition: string;
    is_probability: boolean;
    calibrated: boolean;
    not: string[];
    why_allowed: string;
    primary_metrics: string;
  };
  counts: { rows: number; with_oos_tests: number };
  rows: EvalRow[];
}

export type RecordType =
  | 'LEAD' | 'CONFIRM' | 'REJECT' | 'NO_LEAD' | 'BLOCKED' | 'UI_FRICTION';

/** T 时刻冻结的正文 —— 写入后不得修改；更正另建 amend。 */
export interface UseRecord {
  record_id: string;
  frozen_at: string;
  data_as_of: string;
  question: string;
  verdict_at_T: string;
  type: RecordType;
  cluster_id: string;
  artifact_ref: string;
  item_ref?: string | null;
}

/** 事后核对 —— 与正文物理分离（独立 localStorage key、独立导出数组）。 */
export interface PosthocEval {
  record_id: string;
  checked_at: string;
  is_new_correspondence: 'YES' | 'NO' | 'UNVERIFIABLE';
  note: string;
}

/** v0.80 · 人工阶段声明的追加式记录（只在内部评估视图出现）。 */
export interface DeclarationRow {
  declaration_id: string;
  candidate_id: string;
  display_name: string;
  declared_at: string;
  declared_phase: string;
  attention_state: string | null;
  review_round: string | null;
  review_status: string | null;
  basis: string;
  market_anchor: {
    as_of: string;
    basis: string;
    price_data_available_at_declaration: string;
    note: string;
  };
  supersedes: string | null;
  source_ref: string;
}

export interface DeclarationView {
  artifact: string;
  artifact_version: string;
  source: { file: string; sha256_16: string };
  as_of: string;
  append_only: boolean;
  counts: Record<string, number>;
  declarations: DeclarationRow[];
  known_gaps: { id: string; detail: string; blocks: string }[];
  limits: string[];
}
