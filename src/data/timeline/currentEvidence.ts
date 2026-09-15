/**
 * Evidence Ledger + Temporal Firewall（Phase 7 — Current Research Discovery v1）。
 *
 * ## 为什么这是本阶段最重要的模块
 * 结论必须**可回溯到证据**。系统不允许输出「这个主题最近很强，所以值得关注」这类
 * 无证据结论；每个候选的每一条判断都必须能追到具体 evidence。
 *
 * ## 职责
 * 1. **Temporal Firewall**：判定每条证据与 `snapshot_date` 的时间关系；
 *    `AFTER_SNAPSHOT` 的证据**不得参与任何判断**（阶段推断 / 状态 / 相似度）。
 * 2. **Evidence Ledger**：把候选的证据分成「可用 / 已隔离 / 日期未知」三档，并交叉校验
 *    数据集声明的 `temporal_relation`。
 * 3. **强度聚合**：用有限枚举（HIGH / MEDIUM / LOW / UNKNOWN）表达证据充分度，
 *    **不使用百分比**（避免伪精确）。
 * 4. **相位证据矩阵**：把证据的 `source_type × strength × direction` **确定性派生**为
 *    维度水平；研究声明值优先，逐维度标注来源。
 * 5. **冲突检测**：结构与证据层面的方向冲突 → `CONFLICTED`，不得显示为可升级状态。
 *
 * ## 边界
 * **纯 View / Research Navigation 层**：不写 DB / schema / export / contracts；
 * 不联网；不做 NLP / 机器学习；不输出概率。
 */

import {
  DIMENSION_LABEL,
  EVIDENCE_SOURCE_LABEL,
  EVIDENCE_STRENGTH_LABEL,
  PHASE_DIMENSIONS,
  TEMPORAL_LABEL,
  type CurrentCandidate,
  type EvidenceItem,
  type EvidenceOrigin,
  type EvidenceSourceType,
  type EvidenceStrength,
  type PhaseDimension,
  type SignalLevel,
  type TemporalRelation,
} from './currentCandidate';

/* ================= 1. Temporal Firewall ================= */

/** 证据日期：优先 `source_date`，否则 `event_date` */
export function evidenceDateOf(item: EvidenceItem): string | null {
  return item.source_date ?? item.event_date ?? null;
}

/**
 * 时间关系（**确定性**，无例外）：
 * ```
 * date === null            → UNKNOWN
 * date  < snapshot         → BEFORE_SNAPSHOT
 * date === snapshot        → AT_SNAPSHOT
 * date  > snapshot         → AFTER_SNAPSHOT   ← 违规，必须隔离
 * ```
 */
export function temporalRelationOf(item: EvidenceItem, snapshotDate: string): TemporalRelation {
  const date = evidenceDateOf(item);
  if (!date || !snapshotDate) return 'UNKNOWN';
  if (date < snapshotDate) return 'BEFORE_SNAPSHOT';
  if (date === snapshotDate) return 'AT_SNAPSHOT';
  return 'AFTER_SNAPSHOT';
}

/** 是否可参与判断：只有「快照之前 / 快照当日」可进入 CURRENT DISCOVERY 判断 */
export function isAdmissible(relation: TemporalRelation): boolean {
  return relation === 'BEFORE_SNAPSHOT' || relation === 'AT_SNAPSHOT';
}

export interface LedgerEntry {
  item: EvidenceItem;
  relation: TemporalRelation;
}

export interface EvidenceLedger {
  snapshotDate: string;
  /** 可参与判断（快照前 / 快照当日） */
  admissible: LedgerEntry[];
  /** 已隔离（快照后才出现）——**不参与任何判断** */
  excluded: LedgerEntry[];
  /** 日期未知（无法判定，按不可用处理） */
  undated: LedgerEntry[];
  /** 数据集声明值与推导值不一致（透明性告警；以推导值为准） */
  declaredMismatch: string[];
}

/** 建立候选的证据台账（Temporal Firewall 在此生效） */
export function evidenceLedgerOf(candidate: CurrentCandidate): EvidenceLedger {
  const snapshotDate = candidate.snapshot_date;
  const admissible: LedgerEntry[] = [];
  const excluded: LedgerEntry[] = [];
  const undated: LedgerEntry[] = [];
  const declaredMismatch: string[] = [];

  for (const item of candidate.evidence) {
    const relation = temporalRelationOf(item, snapshotDate);
    if (item.temporal_relation && item.temporal_relation !== relation) {
      declaredMismatch.push(
        `${item.evidence_id}：声明 ${TEMPORAL_LABEL[item.temporal_relation]}，` +
          `按 snapshot_date(${snapshotDate}) 推导为 ${TEMPORAL_LABEL[relation]}（以推导值为准）`,
      );
    }
    if (relation === 'AFTER_SNAPSHOT') excluded.push({ item, relation });
    else if (relation === 'UNKNOWN') undated.push({ item, relation });
    else admissible.push({ item, relation });
  }

  return { snapshotDate, admissible, excluded, undated, declaredMismatch };
}

/* ================= 2. 强度聚合（有限枚举，无百分比） ================= */

/** 候选级证据充分度（**不是概率、不是置信度百分比**） */
export type AggregateEvidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

export const AGGREGATE_LEVEL_LABEL: Record<AggregateEvidenceLevel, string> = {
  HIGH: '证据较充分',
  MEDIUM: '证据中等',
  LOW: '证据较少',
  UNKNOWN: '无可用证据',
};

export interface EvidenceSummary {
  level: AggregateEvidenceLevel;
  /** 可用证据条数（快照内） */
  admissibleCount: number;
  /** 已隔离条数（快照后） */
  excludedCount: number;
  /** 日期未知条数 */
  undatedCount: number;
  /** 覆盖的来源类型（去重，保持出现顺序） */
  sourceTypes: EvidenceSourceType[];
  /** 按强度计数（仅可用证据） */
  byStrength: Record<EvidenceStrength, number>;
  /** 人类可读依据（逐条） */
  basis: string[];
}

/**
 * 证据强度聚合规则（**确定性**，可审计）：
 * ```
 * 可用证据 = 0                                    → UNKNOWN
 * STRONG ≥ 2 且 总数 ≥ 3 且 来源类型 ≥ 2           → HIGH
 * STRONG ≥ 1 或 MEDIUM ≥ 2                        → MEDIUM
 * 其余（有可用证据但都很弱）                        → LOW
 * ```
 */
export function evidenceSummaryOf(ledger: EvidenceLedger): EvidenceSummary {
  const items = ledger.admissible.map((e) => e.item);
  const byStrength: Record<EvidenceStrength, number> = { STRONG: 0, MEDIUM: 0, WEAK: 0 };
  const sourceTypes: EvidenceSourceType[] = [];
  for (const it of items) {
    byStrength[it.evidence_strength] += 1;
    if (!sourceTypes.includes(it.source_type)) sourceTypes.push(it.source_type);
  }

  let level: AggregateEvidenceLevel;
  const basis: string[] = [];
  if (items.length === 0) {
    level = 'UNKNOWN';
    basis.push('没有任何处于快照之前的可核验证据');
  } else if (byStrength.STRONG >= 2 && items.length >= 3 && sourceTypes.length >= 2) {
    level = 'HIGH';
    basis.push(`强证据 ${byStrength.STRONG} 条，共 ${items.length} 条，覆盖 ${sourceTypes.length} 类来源`);
  } else if (byStrength.STRONG >= 1 || byStrength.MEDIUM >= 2) {
    level = 'MEDIUM';
    basis.push(
      byStrength.STRONG >= 1
        ? `存在强证据 ${byStrength.STRONG} 条`
        : `中等强度证据 ${byStrength.MEDIUM} 条`,
    );
  } else {
    level = 'LOW';
    basis.push(`可用证据 ${items.length} 条，均为弱证据`);
  }
  if (ledger.excluded.length > 0) {
    basis.push(`另有 ${ledger.excluded.length} 条快照后证据已被隔离，不计入强度`);
  }
  if (ledger.undated.length > 0) {
    basis.push(`另有 ${ledger.undated.length} 条证据日期未知，按不可用处理`);
  }

  return {
    level,
    admissibleCount: items.length,
    excludedCount: ledger.excluded.length,
    undatedCount: ledger.undated.length,
    sourceTypes,
    byStrength,
    basis,
  };
}

/* ================= 3. 相位证据矩阵 ================= */

export interface PhaseEvidenceEntry {
  dimension: PhaseDimension;
  level: SignalLevel;
  origin: EvidenceOrigin;
  /** 人类可读依据 */
  basis: string;
}

export type PhaseEvidenceMatrix = Record<PhaseDimension, PhaseEvidenceEntry>;

/**
 * 证据来源 → 相位维度（**1:1 确定性映射**，不做自然语言推断）。
 * `MACRO` / `SENTIMENT` 没有对应的相位维度，只进入 Driver Profile（相似度第 3 层）。
 */
const SOURCE_TO_DIMENSION: Partial<Record<EvidenceSourceType, PhaseDimension>> = {
  POLICY: 'policy',
  INDUSTRY: 'industry',
  COMPANY: 'company',
  MARKET: 'market',
  CAPITAL: 'capital',
};

/**
 * 由证据派生维度水平（**确定性**）：
 * ```
 * 该维度无可用证据              → UNKNOWN
 * 含 NEGATIVE 方向证据          → WEAKENING（方向反转优先）
 * 含 STRONG                     → STRONG
 * 含 MEDIUM                     → PRESENT
 * 仅 WEAK                       → EMERGING
 * ```
 */
export function deriveMatrixFromEvidence(
  ledger: EvidenceLedger,
): Partial<Record<PhaseDimension, { level: SignalLevel; basis: string }>> {
  const byDim = new Map<PhaseDimension, EvidenceItem[]>();
  for (const { item } of ledger.admissible) {
    const dim = SOURCE_TO_DIMENSION[item.source_type];
    if (!dim) continue;
    const list = byDim.get(dim);
    if (list) list.push(item);
    else byDim.set(dim, [item]);
  }

  const out: Partial<Record<PhaseDimension, { level: SignalLevel; basis: string }>> = {};
  for (const [dim, items] of byDim) {
    const hasNegative = items.some((i) => i.direction === 'NEGATIVE');
    const hasStrong = items.some((i) => i.evidence_strength === 'STRONG');
    const hasMedium = items.some((i) => i.evidence_strength === 'MEDIUM');
    const level: SignalLevel = hasNegative
      ? 'WEAKENING'
      : hasStrong
        ? 'STRONG'
        : hasMedium
          ? 'PRESENT'
          : 'EMERGING';
    const counts = (['STRONG', 'MEDIUM', 'WEAK'] as EvidenceStrength[])
      .map((s) => `${EVIDENCE_STRENGTH_LABEL[s]}${items.filter((i) => i.evidence_strength === s).length}`)
      .join(' / ');
    out[dim] = {
      level,
      basis:
        `由 ${items.length} 条「${EVIDENCE_SOURCE_LABEL[items[0].source_type]}」证据派生（${counts}）` +
        (hasNegative ? '，其中存在反向证据 → 判为转弱' : ''),
    };
  }
  return out;
}

export interface PhaseMatrixResult {
  matrix: PhaseEvidenceMatrix;
  /** 研究声明值与证据派生值不一致（不隐藏、不静默覆盖） */
  disagreements: string[];
}

/**
 * 合并相位证据矩阵：**研究声明优先**，缺失维度由证据派生，仍缺失 → UNSET(UNKNOWN)。
 * 逐维度记录来源，便于 UI 标注「研究声明 / 由证据派生 / 未标注」。
 */
export function phaseMatrixOf(candidate: CurrentCandidate, ledger: EvidenceLedger): PhaseMatrixResult {
  const derived = deriveMatrixFromEvidence(ledger);
  const disagreements: string[] = [];
  const matrix = {} as PhaseEvidenceMatrix;

  for (const dim of PHASE_DIMENSIONS) {
    const declared = candidate.phase_evidence[dim];
    const fromEvidence = derived[dim];
    if (declared !== undefined) {
      if (fromEvidence && fromEvidence.level !== declared) {
        disagreements.push(
          `${DIMENSION_LABEL[dim]}：研究声明「${declared}」，证据派生「${fromEvidence.level}」` +
            '（保留研究声明，并列出证据依据供复核）',
        );
      }
      matrix[dim] = {
        dimension: dim,
        level: declared,
        origin: 'RESEARCH_DECLARED',
        basis:
          '研究声明值' +
          (fromEvidence ? `；证据派生为 ${fromEvidence.level}（${fromEvidence.basis}）` : '；无对应证据来源'),
      };
    } else if (fromEvidence) {
      matrix[dim] = {
        dimension: dim,
        level: fromEvidence.level,
        origin: 'DERIVED_FROM_EVIDENCE',
        basis: fromEvidence.basis,
      };
    } else {
      matrix[dim] = {
        dimension: dim,
        level: 'UNKNOWN',
        origin: 'UNSET',
        basis: '未标注且无可派生证据（不推断）',
      };
    }
  }

  return { matrix, disagreements };
}

/* ================= 4. 冲突检测 ================= */

export type ConflictKind = 'DECLARED' | 'STRUCTURE' | 'EVIDENCE';

export interface ConflictNote {
  kind: ConflictKind;
  note: string;
}

const presentPlus = (l: SignalLevel): boolean => l === 'PRESENT' || l === 'STRONG';

export const CONFLICT_KIND_LABEL: Record<ConflictKind, string> = {
  DECLARED: '研究声明冲突',
  STRUCTURE: '结构冲突（维度方向不一致）',
  EVIDENCE: '证据方向冲突',
};

/**
 * 冲突检测（**不强行归纳**：有冲突就必须显示为冲突）。
 *
 * 规则：
 * 1. `DECLARED` —— 数据集 `conflict_notes` 已声明。
 * 2. `STRUCTURE` —— 基本面 / 政策证据支持，但市场关注或叙事走弱。
 * 3. `EVIDENCE` —— 可用证据中同时存在中/强「支持」与中/强「反向」。
 */
export function conflictsOf(
  candidate: CurrentCandidate,
  ledger: EvidenceLedger,
  matrix: PhaseEvidenceMatrix,
): ConflictNote[] {
  const out: ConflictNote[] = [];

  for (const n of candidate.conflict_notes) out.push({ kind: 'DECLARED', note: n });

  const supportiveBasis =
    presentPlus(matrix.policy.level) ||
    presentPlus(matrix.industry.level) ||
    presentPlus(matrix.company.level);
  const marketWeak = matrix.market.level === 'ABSENT' || matrix.market.level === 'WEAKENING';
  const narrativeWeak = matrix.narrative.level === 'WEAKENING';
  if (supportiveBasis && (marketWeak || narrativeWeak)) {
    out.push({
      kind: 'STRUCTURE',
      note:
        '政策 / 产业 / 公司层证据支持，但' +
        (narrativeWeak ? '叙事主线转弱' : '市场关注缺失或转弱') +
        ' —— 方向不一致，不得据此判定为可升级状态。',
    });
  }

  const strongSupport = ledger.admissible.some(
    (e) => e.item.direction === 'SUPPORTIVE' && e.item.evidence_strength !== 'WEAK',
  );
  const strongNegative = ledger.admissible.some(
    (e) => e.item.direction === 'NEGATIVE' && e.item.evidence_strength !== 'WEAK',
  );
  if (strongSupport && strongNegative) {
    out.push({
      kind: 'EVIDENCE',
      note: '可用证据中同时存在中等以上强度的「支持」与「反向」证据。',
    });
  }

  return out;
}

/* ================= 5. 候选状态门（只降不升） ================= */

export interface CandidateStatusGate {
  declared: CurrentCandidate['candidate_status'];
  effective: CurrentCandidate['candidate_status'];
  /** 是否被降级（effective 比 declared 更保守） */
  demoted: boolean;
  reasons: string[];
}

const STATUS_RANK: Record<CurrentCandidate['candidate_status'], number> = {
  REJECTED: 0,
  CANDIDATE: 1,
  WATCH: 2,
  RESEARCHING: 3,
  PROMOTABLE: 4,
};

/** 更保守者（rank 更小） */
function moreConservative(
  a: CurrentCandidate['candidate_status'],
  b: CurrentCandidate['candidate_status'],
): CurrentCandidate['candidate_status'] {
  return STATUS_RANK[a] <= STATUS_RANK[b] ? a : b;
}

/**
 * 状态门：产品端**只降不升**，绝不把研究声明拔高。
 *
 * ```
 * 1. 无可用证据（快照内）        → 不高于 CANDIDATE
 * 2. 存在冲突                    → 不高于 WATCH
 * 3. 阶段推导为 UNKNOWN          → 不高于 WATCH
 * 4. 声明 PROMOTABLE 但可用证据 < 2 → 不高于 RESEARCHING
 * 5. 否则 = 声明值
 * ```
 * 结论：**Conflict 候选永远不可能显示为 PROMOTABLE**。
 */
export function candidateStatusGateOf(
  candidate: CurrentCandidate,
  summary: EvidenceSummary,
  conflicts: ConflictNote[],
  phase: CurrentCandidate['attention_state'],
): CandidateStatusGate {
  const reasons: string[] = [];
  let effective = candidate.candidate_status;

  if (summary.admissibleCount === 0) {
    effective = moreConservative(effective, 'CANDIDATE');
    reasons.push('快照内没有任何可用证据 → 状态不高于「候选」');
  }
  if (conflicts.length > 0) {
    effective = moreConservative(effective, 'WATCH');
    reasons.push(`存在 ${conflicts.length} 项证据冲突 → 状态不高于「保持观察」`);
  }
  if (phase === 'UNKNOWN') {
    effective = moreConservative(effective, 'WATCH');
    reasons.push('阶段无法推断 → 状态不高于「保持观察」');
  }
  if (candidate.candidate_status === 'PROMOTABLE' && summary.admissibleCount < 2) {
    effective = moreConservative(effective, 'RESEARCHING');
    reasons.push('声明可升级，但可用证据少于 2 条 → 降为「研究中」');
  }
  if (effective === candidate.candidate_status) {
    reasons.push('研究声明状态未被降级（未发现冲突 / 证据缺失）');
  }

  return {
    declared: candidate.candidate_status,
    effective,
    demoted: effective !== candidate.candidate_status,
    reasons,
  };
}
