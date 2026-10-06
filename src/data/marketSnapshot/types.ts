/**
 * Market Snapshot（契约 v0.3）的 **Product 侧读取视图**。
 *
 * 这里**只声明 diff 真正需要的字段** —— 不是对契约的完整镜像。
 * 完整契约见 `docs/MARKET_SNAPSHOT_CONTRACT_v0.3.md`；
 * 结构校验由 Research 侧校验器 + JSON Schema 负责，Product 侧不做重复校验。
 */

export interface SnapshotRegime {
  broad_index_state: string;
  breadth_state: string;
  liquidity_state: string;
  risk_appetite_state: string;
  beta_note?: string;
  evidence_refs?: string[];
}

export interface SnapshotResearchObject {
  object_id: string;
  object_kind: string;
  display_name: string;
  macro_theme?: string;
  declared_phase: string;
  phase_source?: string;
  canonical_drivers?: string[];
  evidence_categories?: string[];
  resolution_state: string;
}

export interface SnapshotObservation {
  observation_id: string;
  observation_type: string;
  date: string;
  claim: string;
  evidence_strength?: string;
  direction?: string;
  /** 该观察关联的**当前研究对象**（`research_objects[].object_id`）；市场级观察可为空 */
  linked_object_id?: string | null;
  source_tier?: string;
  source_title?: string;
}

/** Lifecycle Tracking：某个当前对象的「追加式观察时间线」条目（派生，不落盘） */
export interface LifecycleEntry {
  date: string;
  observation_id: string;
  observation_type: string;
  claim: string;
  evidence_strength?: string;
  direction?: string;
  source_tier?: string;
  source_title?: string;
  /** ★ 哪一期快照**首次**登记了这条观察（同一 id 在多期出现时取最早一期） */
  first_seen_in: string;
}

export interface LifecycleTimeline {
  object_id: string;
  display_name: string;
  entries: LifecycleEntry[];
  count: number;
  first_date: string | null;
  last_date: string | null;
}

export interface SnapshotCandidateIdentity {
  historical_object_kind: string;
  historical_cycle_id: string;
  historical_campaign_id?: string | null;
  historical_research_candidate_id?: string | null;
  historical_theme_cycle_id?: string | null;
}

export interface SnapshotHistoricalCandidate {
  /** ★ v0.3：这条候选是对哪个当前研究对象算的 */
  current_object_id: string;
  identity: SnapshotCandidateIdentity;
  structural_status: string;
  strict_structural_supported?: boolean;
}

export interface MarketSnapshot {
  contract: 'market_snapshot';
  market_snapshot_version: string;
  snapshot_id: string;
  snapshot_date: string;
  status: string;
  market_regime: SnapshotRegime;
  research_objects: SnapshotResearchObject[];
  observations: SnapshotObservation[];
  historical_candidates: SnapshotHistoricalCandidate[];
}

/* ================= diff 结果类型 ================= */

export type RegimeDimension =
  | 'broad_index_state'
  | 'breadth_state'
  | 'liquidity_state'
  | 'risk_appetite_state';

export interface RegimeChange {
  dimension: RegimeDimension;
  from: string;
  to: string;
}

export interface ObjectAdded {
  object_id: string;
  display_name: string;
  declared_phase: string;
  resolution_state: string;
}

export interface ObjectRemoved {
  object_id: string;
  display_name: string;
}

export interface ObjectFieldChange {
  object_id: string;
  display_name: string;
  field: string;
  from: string;
  to: string;
}

export interface CandidateRef {
  current_object_id: string;
  historical_cycle_id: string;
  historical_object_kind: string;
  structural_status: string;
}

export interface CandidateStatusChange {
  current_object_id: string;
  historical_cycle_id: string;
  from: string;
  to: string;
}

export interface ObservationAdded {
  observation_id: string;
  observation_type: string;
  date: string;
  claim: string;
}

export interface ObservationRemoved {
  observation_id: string;
  date: string;
  claim: string;
}

export interface SnapshotDiff {
  from: { snapshot_id: string; snapshot_date: string };
  to: { snapshot_id: string; snapshot_date: string };
  /** 环境层：market_regime 四维变化 */
  regime: RegimeChange[];
  /** 对象层 */
  objects: {
    added: ObjectAdded[];
    removed: ObjectRemoved[];
    changed: ObjectFieldChange[];
  };
  /** 候选层 */
  candidates: {
    added: CandidateRef[];
    removed: CandidateRef[];
    statusChanged: CandidateStatusChange[];
  };
  /** 观察层 */
  observations: {
    added: ObservationAdded[];
    removed: ObservationRemoved[];
  };
  /** 计数汇总（供 UI 显示「本期 N 处变化」） */
  summary: {
    total: number;
    regime: number;
    objects: number;
    candidates: number;
    observations: number;
    /** 四层全部无变化 */
    unchanged: boolean;
  };
}
