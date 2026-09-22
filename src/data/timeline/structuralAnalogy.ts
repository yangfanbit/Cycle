/**
 * Structural Analogy —— Product Adapter v0.1（ROADMAP Step 2）。
 *
 * ## 定位
 * `research/research/reports/structural_analogy_explanations_v0_4.json`
 * （**Research-derived / Product-facing Artifact**，契约见
 * `docs/PRODUCT_SIMILARITY_ARCHITECTURE_GATE_v0_1.md` §D–§G）
 * → **Product View Model**（只读消费）。
 *
 * 它回答：**「当前结构与历史结构在哪些维度对应？」**
 * 它是 Product 唯一正式的 **Current → Historical Structural Correspondence** 能力。
 *
 * ## 边界（不得违反）
 * - **纯 Adapter**：只做 JSON decoding / 类型定义 / 字段改名 / identity 规范化 /
 *   导航目标映射 / 稳定查找。**不重新计算** Structural Analogy，**不重新判断**任何维度。
 * - **无分数**：不产生 score / ranking / probability / prediction；**不按 Structural Status 重排**。
 * - **不升降级**：Theme Relation 仅为 metadata，**不得**据此升级或降级。
 * - **不推断**：不用事件推断 Driver；不用缺失证据推断「不存在」。
 * - **不混淆状态**：`UNKNOWN` / `NOT_AVAILABLE` 必须**保持可区分**，且**不得**转成 `MISMATCH` / `NO`；
 *   `STRUCTURAL_PARTIAL` **不得**转成 `MATCH`。
 * - **不联网**：数据经 Vite 动态 import 从**同源静态 chunk** 加载（无外网请求、无 LLM）。
 * - **按需加载**：488 KB 的 Explanation Artifact **不进首屏 bundle**，仅在用户展开候选时才加载。
 * - **规则来源唯一**：Structural Analogy Rule Set v0.2（Research 侧）。
 *
 * ## 与其它视角的关系
 * `Calendar Lens`（时间邻近）· `Lifecycle Lens`（`historicalSimilarPhase.ts`）·
 * `Structural Analogy`（本模块）**三者并列、互不替代**。
 * 本模块**不**复用 `currentSimilarity.ts` 的任何判定逻辑（该模块为 `LEGACY / FREEZE`）。
 */


/* ================= 1. 枚举 ================= */

export type StructuralStatus =
  | 'STRUCTURAL_SUPPORTED'
  | 'STRUCTURAL_PARTIAL'
  | 'THEME_ONLY'
  | 'INSUFFICIENT_EVIDENCE'
  | 'NO_VALID_CORRESPONDENCE';

export type DimensionStatus = 'MATCH' | 'PARTIAL' | 'MISMATCH' | 'UNKNOWN' | 'NOT_AVAILABLE';

/** Driver 维度额外允许 `PERIPHERAL_OVERLAP`（**不计为结构支持**）。 */
export type DriverStatus = DimensionStatus | 'PERIPHERAL_OVERLAP';

export type ThemeRelationValue = 'SAME_MACRO_THEME' | 'CROSS_MACRO_THEME';

export type HistoricalObjectKind = 'campaign' | 'research_candidate';

export type DimensionKey =
  | 'lifecycle'
  | 'mechanism_driver'
  | 'evidence_sequence'
  | 'event_structure';

/** 无对应关系 / 资料不足的维度状态（**不得**被压缩成 MISMATCH）。 */
export const INDETERMINATE_DIMENSION_STATUSES: readonly DimensionStatus[] = [
  'UNKNOWN',
  'NOT_AVAILABLE',
];

/* ================= 2. 文案（枚举 → 中文，纯展示映射，不改语义） ================= */

export const STRUCTURAL_STATUS_LABEL: Record<StructuralStatus, string> = {
  STRUCTURAL_SUPPORTED: '结构支持',
  STRUCTURAL_PARTIAL: '结构部分支持',
  THEME_ONLY: '仅主题相关',
  INSUFFICIENT_EVIDENCE: '证据不足',
  NO_VALID_CORRESPONDENCE: '无有效结构对应',
};

export const DIMENSION_STATUS_LABEL: Record<DriverStatus, string> = {
  MATCH: '对应',
  PARTIAL: '部分对应',
  MISMATCH: '不对应',
  UNKNOWN: '未知',
  NOT_AVAILABLE: '无可用资料',
  PERIPHERAL_OVERLAP: '仅外围机制重叠',
};

export const THEME_RELATION_LABEL: Record<ThemeRelationValue, string> = {
  SAME_MACRO_THEME: '同一 Macro Theme',
  CROSS_MACRO_THEME: '跨 Macro Theme',
};

export const DIMENSION_LABEL: Record<DimensionKey, string> = {
  lifecycle: '生命周期',
  mechanism_driver: '驱动机制',
  evidence_sequence: '证据顺序',
  event_structure: '事件结构',
};

/* ================= 3. View Model 类型 ================= */

export interface StructuralAnalogyIdentity {
  historicalObjectKind: HistoricalObjectKind;
  /** **统一稳定引用**（始终非空）。 */
  historicalCycleId: string;
  /** **仅真实 Campaign 非空**。 */
  historicalCampaignId: string | null;
  /** **仅 Research Candidate 非空**。 */
  historicalResearchCandidateId: string | null;
  historicalThemeCycleId: string | null;
  identityNote: string;
}

export interface LifecycleDimensionView {
  status: DimensionStatus;
  candidatePhase: string | null;
  historicalStageAtComparablePoint: string | null;
  note: string;
  forbiddenComparison: string;
}

export interface MechanismDriverDimensionView {
  status: DriverStatus;
  quality: string | null;
  overlap: string[];
  axis: string;
  note: string;
}

export interface EvidenceSequenceDimensionView {
  status: DimensionStatus;
  subtype: string | null;
  note: string;
}

export interface EventStructureDimensionView {
  status: DimensionStatus;
  quality: string | null;
  note: string;
}

export interface StructuralAnalogyDimensionsView {
  lifecycle: LifecycleDimensionView;
  mechanismDriver: MechanismDriverDimensionView;
  evidenceSequence: EvidenceSequenceDimensionView;
  eventStructure: EventStructureDimensionView;
}

/** 某维度的**直接依据**（仅此层可作为「为什么该维度是这个状态」的依据）。 */
export interface DimensionEvidenceView {
  lifecycle: ReadonlyArray<Record<string, unknown>>;
  mechanismDriver: ReadonlyArray<Record<string, unknown>>;
  evidenceSequence: ReadonlyArray<Record<string, unknown>>;
  eventStructure: ReadonlyArray<Record<string, unknown>>;
}

/** **背景来源** —— 仅作背景展示，**不得**作为维度判定依据，**不得**做因果推断。 */
export interface BackgroundSourceView {
  source: string;
  value: unknown;
  role: string;
}

export interface ThemeRelationView {
  value: ThemeRelationValue;
  role: string;
  note: string;
}

export interface SupplementaryContextView {
  marketStructure: string;
  temporalStructure: string;
  note: string;
}

/** 历史对象导航目标（**稳定 identity**，非排序结果）。 */
export interface HistoricalNavigationTarget {
  kind: HistoricalObjectKind;
  /** 导航使用的稳定 id：Campaign → `historicalCampaignId`；Research Candidate → `historicalResearchCandidateId`。 */
  id: string;
  /** 当前 Product 是否可导航到 Campaign Detail（Research Candidate **不在** `campaigns` 集合内）。 */
  navigableToCampaign: boolean;
}

export interface StructuralAnalogyExplanationView {
  identity: StructuralAnalogyIdentity;
  snapshotDate: string;
  ruleSetVersion: string;
  structuralStatus: StructuralStatus;
  strictStructuralSupported: boolean;
  themeRelation: ThemeRelationView;
  dimensions: StructuralAnalogyDimensionsView;
  supportedDimensions: DimensionKey[];
  unknownDimensions: DimensionKey[];
  unsupportedDimensions: DimensionKey[];
  whySimilar: string[];
  whyNotSimilar: string[];
  dimensionEvidence: DimensionEvidenceView;
  backgroundSources: BackgroundSourceView[];
  supplementaryContext: SupplementaryContextView;
  /** 稳定导航目标（由 identity 派生，**不含任何排序语义**）。 */
  navigationTarget: HistoricalNavigationTarget;
}

export interface CurrentStructuralProfileView {
  currentPhase: string | null;
  phaseStage: string | null;
  /** **驱动机制**（Mechanism Driver）—— 不是证据类别。 */
  mechanismDrivers: string[];
  /** **证据类别**（Evidence Category）—— 不是驱动机制。 */
  evidenceCategories: string[];
  evidenceSequence: string[];
  evidenceSequenceStatus: string | null;
  eventTypes: string[];
  marketStatus: string;
  temporalStatus: string;
  structuralGaps: string[];
}

export interface StructuralAnalogyCandidateView {
  candidateId: string;
  displayName: string | null;
  macroTheme: string | null;
  currentStructuralProfile: CurrentStructuralProfileView;
  /** 该候选的 structural status 计数（**计数，不是分数**）。 */
  summary: Partial<Record<StructuralStatus, number>>;
  /** ★ **保持 artifact 原始顺序**（稳定 identity 顺序）—— Adapter **不重排**。 */
  explanations: StructuralAnalogyExplanationView[];
}

export interface StructuralAnalogyDataset {
  artifactVersion: string;
  ruleSet: string;
  ruleSetVersion: string;
  snapshotDate: string;
  statusVocabulary: StructuralStatus[];
  dimensionVocabulary: Record<DimensionKey, string[]>;
  /** Driver 分层命名（**证据类别 ≠ 驱动机制**）。 */
  dimensionNaming: {
    evidenceCategoryLabel: string;
    mechanismDriverLabel: string;
    rule: string;
  };
  semantics: Record<string, unknown>;
  candidates: StructuralAnalogyCandidateView[];
}

export const EMPTY_STRUCTURAL_ANALOGY_DATASET: StructuralAnalogyDataset = {
  artifactVersion: 'none',
  ruleSet: '',
  ruleSetVersion: '',
  snapshotDate: '',
  statusVocabulary: [],
  dimensionVocabulary: {
    lifecycle: [],
    mechanism_driver: [],
    evidence_sequence: [],
    event_structure: [],
  },
  dimensionNaming: { evidenceCategoryLabel: '', mechanismDriverLabel: '', rule: '' },
  semantics: {},
  candidates: [],
};

/* ================= 4. 容错读取工具 ================= */

const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === 'object' && v !== null && !Array.isArray(v);

const asString = (v: unknown): string | null => (typeof v === 'string' ? v : null);
const asStringOr = (v: unknown, fallback = ''): string => (typeof v === 'string' ? v : fallback);
const asBool = (v: unknown): boolean => v === true;
const asArray = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const asStringArray = (v: unknown): string[] =>
  asArray(v).filter((x): x is string => typeof x === 'string');

const asStructuralStatus = (v: unknown): StructuralStatus | null =>
  typeof v === 'string' && v in STRUCTURAL_STATUS_LABEL ? (v as StructuralStatus) : null;

const asDriverStatus = (v: unknown): DriverStatus | null =>
  typeof v === 'string' && v in DIMENSION_STATUS_LABEL ? (v as DriverStatus) : null;

const asThemeRelation = (v: unknown): ThemeRelationValue | null =>
  typeof v === 'string' && v in THEME_RELATION_LABEL ? (v as ThemeRelationValue) : null;

const asKind = (v: unknown): HistoricalObjectKind =>
  v === 'research_candidate' ? 'research_candidate' : 'campaign';

const asDimensionKey = (v: unknown): DimensionKey | null =>
  typeof v === 'string' && v in DIMENSION_LABEL ? (v as DimensionKey) : null;

const asDimensionKeys = (v: unknown): DimensionKey[] =>
  asArray(v).map(asDimensionKey).filter((x): x is DimensionKey => x !== null);

const asRecordArray = (v: unknown): ReadonlyArray<Record<string, unknown>> =>
  asArray(v).filter(isRecord);

/* ================= 5. 解析（纯解码，不做任何判定） ================= */

function parseIdentity(raw: unknown): StructuralAnalogyIdentity {
  const o = isRecord(raw) ? raw : {};
  const kind = asKind(o.historical_object_kind);
  return {
    historicalObjectKind: kind,
    historicalCycleId: asStringOr(o.historical_cycle_id),
    historicalCampaignId: asString(o.historical_campaign_id),
    historicalResearchCandidateId: asString(o.historical_research_candidate_id),
    historicalThemeCycleId: asString(o.historical_theme_cycle_id),
    identityNote: asStringOr(o.identity_note),
  };
}

/**
 * 由 identity 派生**稳定导航目标**。
 *
 * **只做映射，不做判定**：
 * - `campaign` → 使用 `historicalCampaignId`（真实 Campaign，可导航 Campaign Detail）
 * - `research_candidate` → 使用 `historicalResearchCandidateId`（**不在** `campaigns` 集合内）
 *
 * **不得**把 `historical_campaign_id` 当作万能历史 ID。
 */
export function navigationTargetOf(identity: StructuralAnalogyIdentity): HistoricalNavigationTarget {
  if (identity.historicalObjectKind === 'research_candidate') {
    return {
      kind: 'research_candidate',
      id: identity.historicalResearchCandidateId ?? identity.historicalCycleId,
      navigableToCampaign: false,
    };
  }
  return {
    kind: 'campaign',
    id: identity.historicalCampaignId ?? identity.historicalCycleId,
    navigableToCampaign: identity.historicalCampaignId !== null,
  };
}

function parseExplanation(raw: unknown): StructuralAnalogyExplanationView | null {
  if (!isRecord(raw)) return null;
  const status = asStructuralStatus(raw.structural_status);
  if (status === null) return null;

  const identity = parseIdentity(raw.identity);
  if (!identity.historicalCycleId) return null;

  const d = isRecord(raw.dimensions) ? raw.dimensions : {};
  const lc = isRecord(d.lifecycle) ? d.lifecycle : {};
  const dr = isRecord(d.mechanism_driver) ? d.mechanism_driver : {};
  const sq = isRecord(d.evidence_sequence) ? d.evidence_sequence : {};
  const ev = isRecord(d.event_structure) ? d.event_structure : {};

  const tr = isRecord(raw.theme_relation) ? raw.theme_relation : {};
  const trValue = asThemeRelation(tr.value);

  const de = isRecord(raw.dimension_evidence) ? raw.dimension_evidence : {};
  const sup = isRecord(raw.supplementary_context) ? raw.supplementary_context : {};

  return {
    identity,
    snapshotDate: asStringOr(raw.snapshot_date),
    ruleSetVersion: asStringOr(raw.rule_set_version),
    structuralStatus: status,
    strictStructuralSupported: asBool(raw.strict_structural_supported),
    themeRelation: {
      value: trValue ?? 'CROSS_MACRO_THEME',
      role: asStringOr(tr.role),
      note: asStringOr(tr.note),
    },
    dimensions: {
      lifecycle: {
        status: (asDriverStatus(lc.status) ?? 'NOT_AVAILABLE') as DimensionStatus,
        candidatePhase: asString(lc.candidate_phase),
        historicalStageAtComparablePoint: asString(lc.historical_stage_at_comparable_point),
        note: asStringOr(lc.note),
        forbiddenComparison: asStringOr(lc.forbidden_comparison),
      },
      mechanismDriver: {
        status: asDriverStatus(dr.status) ?? 'NOT_AVAILABLE',
        quality: asString(dr.quality),
        overlap: asStringArray(dr.overlap),
        axis: asStringOr(dr.axis),
        note: asStringOr(dr.note),
      },
      evidenceSequence: {
        status: (asDriverStatus(sq.status) ?? 'NOT_AVAILABLE') as DimensionStatus,
        subtype: asString(sq.subtype),
        note: asStringOr(sq.note),
      },
      eventStructure: {
        status: (asDriverStatus(ev.status) ?? 'NOT_AVAILABLE') as DimensionStatus,
        quality: asString(ev.quality),
        note: asStringOr(ev.note),
      },
    },
    supportedDimensions: asDimensionKeys(raw.supported_dimensions),
    unknownDimensions: asDimensionKeys(raw.unknown_dimensions),
    unsupportedDimensions: asDimensionKeys(raw.unsupported_dimensions),
    whySimilar: asStringArray(raw.why_similar),
    whyNotSimilar: asStringArray(raw.why_not_similar),
    dimensionEvidence: {
      lifecycle: asRecordArray(de.lifecycle),
      mechanismDriver: asRecordArray(de.mechanism_driver),
      evidenceSequence: asRecordArray(de.evidence_sequence),
      eventStructure: asRecordArray(de.event_structure),
    },
    backgroundSources: asArray(raw.background_sources).filter(isRecord).map((b) => ({
      source: asStringOr(b.source),
      value: b.value,
      role: asStringOr(b.role),
    })),
    supplementaryContext: {
      marketStructure: asStringOr(sup.market_structure),
      temporalStructure: asStringOr(sup.temporal_structure),
      note: asStringOr(sup.note),
    },
    navigationTarget: navigationTargetOf(identity),
  };
}

function parseCandidate(raw: unknown): StructuralAnalogyCandidateView | null {
  if (!isRecord(raw)) return null;
  const candidateId = asString(raw.candidate_id);
  if (!candidateId) return null;

  const p = isRecord(raw.current_structural_profile) ? raw.current_structural_profile : {};
  const summaryRaw = isRecord(raw.summary) ? raw.summary : {};
  const summary: Partial<Record<StructuralStatus, number>> = {};
  for (const [k, v] of Object.entries(summaryRaw)) {
    const s = asStructuralStatus(k);
    if (s !== null && typeof v === 'number') summary[s] = v;
  }

  return {
    candidateId,
    displayName: asString(raw.display_name),
    macroTheme: asString(raw.macro_theme),
    currentStructuralProfile: {
      currentPhase: asString(p.current_phase),
      phaseStage: asString(p.phase_stage),
      mechanismDrivers: asStringArray(p.mechanism_drivers),
      evidenceCategories: asStringArray(p.evidence_categories),
      evidenceSequence: asStringArray(p.evidence_sequence),
      evidenceSequenceStatus: asString(p.evidence_sequence_status),
      eventTypes: asStringArray(p.event_types),
      marketStatus: asStringOr(p.market_status),
      temporalStatus: asStringOr(p.temporal_status),
      structuralGaps: asStringArray(p.structural_gaps),
    },
    summary,
    // ★ **保持 artifact 原始顺序**（稳定 identity 顺序）—— 不排序、不筛选
    explanations: asArray(raw.explanations)
      .map(parseExplanation)
      .filter((x): x is StructuralAnalogyExplanationView => x !== null),
  };
}

/**
 * 解析 Explanation Artifact v0.2 → Product View Model。
 *
 * **纯解码**：未知字段忽略，缺失字段回退到安全默认；**不做任何判定或推断**。
 */
export function parseStructuralAnalogyDataset(raw: unknown): StructuralAnalogyDataset {
  if (!isRecord(raw)) return EMPTY_STRUCTURAL_ANALOGY_DATASET;

  const dn = isRecord(raw.dimension_naming) ? raw.dimension_naming : {};
  const ec = isRecord(dn.evidence_category) ? dn.evidence_category : {};
  const md = isRecord(dn.mechanism_driver) ? dn.mechanism_driver : {};
  const dv = isRecord(raw.dimension_vocabulary) ? raw.dimension_vocabulary : {};

  return {
    artifactVersion: asStringOr(raw.artifact_version),
    ruleSet: asStringOr(raw.rule_set),
    ruleSetVersion: asStringOr(raw.rule_set_version),
    snapshotDate: asStringOr(raw.snapshot_date),
    statusVocabulary: asArray(raw.status_vocabulary)
      .map(asStructuralStatus)
      .filter((x): x is StructuralStatus => x !== null),
    dimensionVocabulary: {
      lifecycle: asStringArray(dv.lifecycle),
      mechanism_driver: asStringArray(dv.mechanism_driver),
      evidence_sequence: asStringArray(dv.evidence_sequence),
      event_structure: asStringArray(dv.event_structure),
    },
    dimensionNaming: {
      evidenceCategoryLabel: asStringOr(ec.label_zh),
      mechanismDriverLabel: asStringOr(md.label_zh),
      rule: asStringOr(dn.rule),
    },
    semantics: isRecord(raw.semantics) ? raw.semantics : {},
    candidates: asArray(raw.candidates)
      .map(parseCandidate)
      .filter((x): x is StructuralAnalogyCandidateView => x !== null),
  };
}

/**
 * 按需加载 Explanation Artifact（**动态 import → 独立 chunk**）。
 *
 * - 同源静态资源：**无外网请求、无 LLM**，仍是静态部署。
 * - **结果缓存**：重复调用不重复加载。
 * - **失败不伪造**：加载失败由调用方显示诚实提示，**不得**退化成「没有结构对应」。
 */
let _cache: StructuralAnalogyDataset | null = null;

export async function loadStructuralAnalogyDataset(): Promise<StructuralAnalogyDataset> {
  if (_cache) return _cache;
  const mod = await import('@observation/structural_analogy_explanations_v0_4.json');
  _cache = parseStructuralAnalogyDataset((mod as { default: unknown }).default);
  return _cache;
}

/** 仅供测试：注入已解析数据集（避免测试依赖异步加载）。 */
export function __setStructuralAnalogyDatasetForTest(ds: StructuralAnalogyDataset | null): void {
  _cache = ds;
}

/* ================= 6. 稳定查找（identity-based，无排序） ================= */

export function structuralAnalogyForCandidate(
  dataset: StructuralAnalogyDataset,
  candidateId: string,
): StructuralAnalogyCandidateView | null {
  return dataset.candidates.find((c) => c.candidateId === candidateId) ?? null;
}

export function explanationByHistoricalCycleId(
  candidate: StructuralAnalogyCandidateView,
  historicalCycleId: string,
): StructuralAnalogyExplanationView | null {
  return candidate.explanations.find((e) => e.identity.historicalCycleId === historicalCycleId) ?? null;
}

/** 按 structural status 分组（**分组，不排序**；组内保持原始顺序）。 */
export function explanationsByStatus(
  candidate: StructuralAnalogyCandidateView,
): Record<StructuralStatus, StructuralAnalogyExplanationView[]> {
  const out = {
    STRUCTURAL_SUPPORTED: [],
    STRUCTURAL_PARTIAL: [],
    THEME_ONLY: [],
    INSUFFICIENT_EVIDENCE: [],
    NO_VALID_CORRESPONDENCE: [],
  } as Record<StructuralStatus, StructuralAnalogyExplanationView[]>;
  for (const e of candidate.explanations) out[e.structuralStatus].push(e);
  return out;
}

/** 维度状态是否为「不确定」（`UNKNOWN` / `NOT_AVAILABLE`）—— **必须与 `MISMATCH` 区分**。 */
export function isIndeterminate(status: DriverStatus): boolean {
  return status === 'UNKNOWN' || status === 'NOT_AVAILABLE';
}

/** 是否达到「结构支持」等级（**仅用于展示分组，不是分数**）。 */
export function isStructuralStatus(status: StructuralStatus): boolean {
  return status === 'STRUCTURAL_SUPPORTED' || status === 'STRUCTURAL_PARTIAL';
}

/** 全部解释条数（用于覆盖度展示）。 */
export function explanationCount(dataset: StructuralAnalogyDataset): number {
  return dataset.candidates.reduce((n, c) => n + c.explanations.length, 0);
}
