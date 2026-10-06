import type {
  CandidateRef,
  CandidateStatusChange,
  MarketSnapshot,
  ObjectAdded,
  ObjectFieldChange,
  ObjectRemoved,
  ObservationAdded,
  ObservationRemoved,
  RegimeChange,
  RegimeDimension,
  SnapshotDiff,
  SnapshotHistoricalCandidate,
  SnapshotResearchObject,
} from './types';

/**
 * 快照 diff —— 比较两份 Market Snapshot，回答**「跟上一次比，变了什么」**。
 *
 * ## 为什么需要
 * 月度节奏下，用户一个月打开一次，关心的不是「现在是什么状态」，
 * 而是**「跟上个月比，变了什么」**。快照契约有 `supersedes` / `superseded_by`（版本链），
 * 但「变化」本身此前**没有任何设计** —— 本模块补上这一层。
 *
 * ## 语义边界（硬约束，不得违反）
 * - ✅ **只陈述事实**：「哪个字段从什么变成了什么」。
 * - ❌ **不做任何判断**：不说「这个变化是好是坏」「意味着什么」「算不算利好」。
 *   那属于 Research 结论，**不在 Product 侧产生**。
 * - ❌ 不产生 score / ranking / probability / prediction。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络、无随机。相同输入必得相同输出。
 */

const REGIME_DIMENSIONS: RegimeDimension[] = [
  'broad_index_state',
  'breadth_state',
  'liquidity_state',
  'risk_appetite_state',
];

/** 参与比较的对象字段（顺序即输出顺序，保证确定性） */
const OBJECT_FIELDS = [
  'declared_phase',
  'resolution_state',
  'macro_theme',
  'canonical_drivers',
  'evidence_categories',
] as const;

type ObjectField = (typeof OBJECT_FIELDS)[number];

/** 数组字段的稳定表示（排序后拼接），避免顺序差异被误报为变化 */
function stableOf(value: unknown): string {
  if (Array.isArray(value)) return [...value].sort().join('|');
  if (value === undefined || value === null) return '';
  return String(value);
}

/** 候选的稳定复合键：同一个当前对象 × 同一个历史对象 */
function candidateKey(c: SnapshotHistoricalCandidate): string {
  return `${c.current_object_id}::${c.identity.historical_cycle_id}`;
}

function toRef(c: SnapshotHistoricalCandidate): CandidateRef {
  return {
    current_object_id: c.current_object_id,
    historical_cycle_id: c.identity.historical_cycle_id,
    historical_object_kind: c.identity.historical_object_kind,
    structural_status: c.structural_status,
  };
}

function byObjectId(list: SnapshotResearchObject[]): Map<string, SnapshotResearchObject> {
  return new Map(list.map((o) => [o.object_id, o]));
}

/**
 * 比较两份快照。
 *
 * @param prev 较早的快照（基线）
 * @param next 较晚的快照
 * @returns 四层变化 + 计数汇总。**只含事实，不含判断。**
 */
export function diffSnapshots(prev: MarketSnapshot, next: MarketSnapshot): SnapshotDiff {
  /* ---------- 1. 环境层：market_regime ---------- */
  const regime: RegimeChange[] = [];
  for (const dim of REGIME_DIMENSIONS) {
    const from = prev.market_regime?.[dim] ?? 'UNKNOWN';
    const to = next.market_regime?.[dim] ?? 'UNKNOWN';
    if (from !== to) regime.push({ dimension: dim, from, to });
  }

  /* ---------- 2. 对象层：research_objects ---------- */
  const prevObjects = byObjectId(prev.research_objects ?? []);
  const nextObjects = byObjectId(next.research_objects ?? []);

  const objectsAdded: ObjectAdded[] = [];
  const objectsRemoved: ObjectRemoved[] = [];
  const objectsChanged: ObjectFieldChange[] = [];

  for (const [id, o] of nextObjects) {
    if (!prevObjects.has(id)) {
      objectsAdded.push({
        object_id: id,
        display_name: o.display_name,
        declared_phase: o.declared_phase,
        resolution_state: o.resolution_state,
      });
    }
  }
  for (const [id, o] of prevObjects) {
    if (!nextObjects.has(id)) {
      objectsRemoved.push({ object_id: id, display_name: o.display_name });
    }
  }
  for (const [id, o] of nextObjects) {
    const before = prevObjects.get(id);
    if (!before) continue;
    for (const field of OBJECT_FIELDS) {
      // `field` 是 SnapshotResearchObject 的已知键，直接索引即可（无需不安全断言）
      const from = stableOf(before[field]);
      const to = stableOf(o[field]);
      if (from !== to) {
        objectsChanged.push({
          object_id: id,
          display_name: o.display_name,
          field,
          from,
          to,
        });
      }
    }
  }

  /* ---------- 3. 候选层：historical_candidates ---------- */
  const prevCands = new Map((prev.historical_candidates ?? []).map((c) => [candidateKey(c), c]));
  const nextCands = new Map((next.historical_candidates ?? []).map((c) => [candidateKey(c), c]));

  const candidatesAdded: CandidateRef[] = [];
  const candidatesRemoved: CandidateRef[] = [];
  const candidatesStatusChanged: CandidateStatusChange[] = [];

  for (const [key, c] of nextCands) {
    if (!prevCands.has(key)) candidatesAdded.push(toRef(c));
  }
  for (const [key, c] of prevCands) {
    if (!nextCands.has(key)) candidatesRemoved.push(toRef(c));
  }
  for (const [key, c] of nextCands) {
    const before = prevCands.get(key);
    if (!before) continue;
    if (before.structural_status !== c.structural_status) {
      candidatesStatusChanged.push({
        current_object_id: c.current_object_id,
        historical_cycle_id: c.identity.historical_cycle_id,
        from: before.structural_status,
        to: c.structural_status,
      });
    }
  }

  /* ---------- 4. 观察层：observations ---------- */
  const prevObs = new Map((prev.observations ?? []).map((o) => [o.observation_id, o]));
  const nextObs = new Map((next.observations ?? []).map((o) => [o.observation_id, o]));

  const observationsAdded: ObservationAdded[] = [];
  const observationsRemoved: ObservationRemoved[] = [];

  for (const [id, o] of nextObs) {
    if (!prevObs.has(id)) {
      observationsAdded.push({
        observation_id: id,
        observation_type: o.observation_type,
        date: o.date,
        claim: o.claim,
      });
    }
  }
  for (const [id, o] of prevObs) {
    if (!nextObs.has(id)) {
      observationsRemoved.push({ observation_id: id, date: o.date, claim: o.claim });
    }
  }

  /* ---------- 5. 汇总 ---------- */
  const objects = objectsAdded.length + objectsRemoved.length + objectsChanged.length;
  const candidates =
    candidatesAdded.length + candidatesRemoved.length + candidatesStatusChanged.length;
  const observations = observationsAdded.length + observationsRemoved.length;
  const total = regime.length + objects + candidates + observations;

  return {
    from: { snapshot_id: prev.snapshot_id, snapshot_date: prev.snapshot_date },
    to: { snapshot_id: next.snapshot_id, snapshot_date: next.snapshot_date },
    regime,
    objects: { added: objectsAdded, removed: objectsRemoved, changed: objectsChanged },
    candidates: {
      added: candidatesAdded,
      removed: candidatesRemoved,
      statusChanged: candidatesStatusChanged,
    },
    observations: { added: observationsAdded, removed: observationsRemoved },
    summary: {
      total,
      regime: regime.length,
      objects,
      candidates,
      observations,
      unchanged: total === 0,
    },
  };
}
