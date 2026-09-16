/**
 * Current Candidate 数据层（Phase 7 — Current Research Discovery v1）。
 *
 * ## 定位
 * `research/current/current_candidates.json`（**离线研究 Artifact**）→ 产品端只读消费。
 * 回答：**「今天这个时间点，我应该去历史资料里研究什么？」**
 * 而不是「明天应该买什么」。
 *
 * ## 关键边界（不得违反）
 * - **纯 View / Adapter 层**：不写 DB / `schema.sql` / export / contracts，
 *   不改变任何 Research 事实，不把候选升级为正式 Campaign。
 * - **不联网**：静态 import，无运行时网络请求（保持静态 PWA）。
 * - **不是评分 / 概率 / 买卖信号**：状态与阶段都是有限枚举，不是数值打分。
 * - **Candidate ≠ Theme**：候选是**研究对象**，可被证伪 / 合并 / 拆分 / 删除。
 * - **命名空间隔离**：候选用 `CC-`（fixture 用 `FX-`）前缀，**禁止** `C-` / `RC-`
 *   （那是正式 Campaign / Research Candidate 的命名空间）。
 *
 * ## 时间语义
 * 所有判断的基准是数据集的 `snapshot_date`（研究快照日），**不是**浏览器当前日期。
 * 证据的时间关系由 `currentEvidence.ts` 的 Temporal Firewall 判定。
 */

import currentCandidatesJson from '@current/current_candidates.json';
import type { ResearchPhase } from './researchAttention';

/* ================= 1. 枚举与标签 ================= */

/** 候选研究生命周期（PROMOTABLE ≠ 上涨确认，仅表示「可考虑进入正式研究」） */
export type CandidateStatus = 'CANDIDATE' | 'WATCH' | 'RESEARCHING' | 'PROMOTABLE' | 'REJECTED';

export const CANDIDATE_STATUS_ORDER: CandidateStatus[] = [
  'CANDIDATE',
  'WATCH',
  'RESEARCHING',
  'PROMOTABLE',
  'REJECTED',
];

export const CANDIDATE_STATUS_LABEL: Record<CandidateStatus, string> = {
  CANDIDATE: '候选（已注意到）',
  WATCH: '保持观察',
  RESEARCHING: '研究中',
  PROMOTABLE: '可考虑升级为正式研究',
  REJECTED: '已否决',
};

/** 当前候选阶段（= 历史 ResearchPhase 去掉 END —— 候选不会「已结束」） */
export type CurrentPhase = Exclude<ResearchPhase, 'END'>;

/** 相位证据矩阵的水平（6 值统一枚举；逐维度语义见 research/current/README.md） */
export type SignalLevel = 'ABSENT' | 'EMERGING' | 'PRESENT' | 'STRONG' | 'WEAKENING' | 'UNKNOWN';

export const SIGNAL_LEVEL_LABEL: Record<SignalLevel, string> = {
  ABSENT: '无',
  EMERGING: '初现',
  PRESENT: '明确',
  STRONG: '强',
  WEAKENING: '转弱',
  UNKNOWN: '未标注',
};

/** 相位证据维度（§10 的 7 维 + `information_marginal`，用于区分 PEAK / EXPANSION） */
export type PhaseDimension =
  | 'narrative'
  | 'policy'
  | 'industry'
  | 'market'
  | 'capital'
  | 'breadth'
  | 'company'
  | 'information_marginal';

export const PHASE_DIMENSIONS: PhaseDimension[] = [
  'narrative',
  'policy',
  'industry',
  'market',
  'capital',
  'breadth',
  'company',
  'information_marginal',
];

export const DIMENSION_LABEL: Record<PhaseDimension, string> = {
  narrative: '叙事主线',
  policy: '政策催化',
  industry: '产业反馈',
  market: '市场关注',
  capital: '资金响应',
  breadth: '扩散广度',
  company: '公司层验证',
  information_marginal: '新增信息边际',
};

/** 维度来源（透明性：研究声明 / 由证据派生 / 未标注） */
export type EvidenceOrigin = 'RESEARCH_DECLARED' | 'DERIVED_FROM_EVIDENCE' | 'UNSET';

export const ORIGIN_LABEL: Record<EvidenceOrigin, string> = {
  RESEARCH_DECLARED: '研究声明',
  DERIVED_FROM_EVIDENCE: '由证据派生',
  UNSET: '未标注',
};

export type EvidenceSourceType =
  | 'POLICY'
  | 'INDUSTRY'
  | 'COMPANY'
  | 'MARKET'
  | 'MACRO'
  | 'CAPITAL'
  | 'SENTIMENT'
  | 'OTHER';

export const EVIDENCE_SOURCE_LABEL: Record<EvidenceSourceType, string> = {
  POLICY: 'Policy 政策',
  INDUSTRY: 'Industry 产业',
  COMPANY: 'Company 公司',
  MARKET: 'Market 市场',
  MACRO: 'Macro 宏观',
  CAPITAL: 'Capital 资金',
  SENTIMENT: 'Sentiment 情绪',
  OTHER: 'Other 其他',
};

export type EvidenceStrength = 'STRONG' | 'MEDIUM' | 'WEAK';

export const EVIDENCE_STRENGTH_LABEL: Record<EvidenceStrength, string> = {
  STRONG: '强',
  MEDIUM: '中',
  WEAK: '弱',
};

/** 证据方向（可选；用于结构与证据冲突检测） */
export type EvidenceDirection = 'SUPPORTIVE' | 'NEUTRAL' | 'NEGATIVE' | 'UNKNOWN';

export const EVIDENCE_DIRECTION_LABEL: Record<EvidenceDirection, string> = {
  SUPPORTIVE: '支持',
  NEUTRAL: '中性',
  NEGATIVE: '反向',
  UNKNOWN: '未标注',
};

/** 证据与快照的时间关系（由 Temporal Firewall 判定） */
export type TemporalRelation = 'BEFORE_SNAPSHOT' | 'AT_SNAPSHOT' | 'AFTER_SNAPSHOT' | 'UNKNOWN';

export const TEMPORAL_LABEL: Record<TemporalRelation, string> = {
  BEFORE_SNAPSHOT: '快照之前',
  AT_SNAPSHOT: '快照当日',
  AFTER_SNAPSHOT: '已隔离（快照后）',
  UNKNOWN: '日期未知',
};

/** 结构化叙事类型（不是文本相似度）—— Similarity v2 的第 4 层 */
export type NarrativeType =
  | 'POLICY_DRIVEN'
  | 'INDUSTRY_UPGRADE'
  | 'TECH_BREAKTHROUGH'
  | 'DEMAND_SURGE'
  | 'SUPPLY_CONTRACTION'
  | 'VALUATION_RESET'
  | 'CYCLE_REVERSAL'
  | 'EVENT_CATALYST'
  | 'UNKNOWN';

export const NARRATIVE_TYPE_LABEL: Record<NarrativeType, string> = {
  POLICY_DRIVEN: '政策驱动',
  INDUSTRY_UPGRADE: '产业升级',
  TECH_BREAKTHROUGH: '技术突破',
  DEMAND_SURGE: '需求爆发',
  SUPPLY_CONTRACTION: '供给收缩',
  VALUATION_RESET: '估值重构',
  CYCLE_REVERSAL: '周期反转',
  EVENT_CATALYST: '事件催化',
  UNKNOWN: '未标注',
};

export const DRIVER_CATEGORIES = ['POLICY', 'INDUSTRY', 'CAPITAL', 'SENTIMENT', 'EXTERNAL'] as const;
export type CandidateDriverCategory = (typeof DRIVER_CATEGORIES)[number];

/* ================= 2. 数据结构 ================= */

/** Evidence Ledger 的单条（**事实**只写在 `claim`；解释放 core_narrative，推测放 uncertainty_notes） */
export interface EvidenceItem {
  evidence_id: string;
  source_type: EvidenceSourceType;
  source_title?: string | null;
  source_url?: string | null;
  source_date?: string | null;
  event_date?: string | null;
  /** 事实陈述（禁止写入推断） */
  claim: string;
  evidence_strength: EvidenceStrength;
  direction?: EvidenceDirection;
  /** 数据集声明的值；权威值由 Temporal Firewall 重新推导并交叉校验 */
  temporal_relation?: TemporalRelation;
}

export interface CandidateDriver {
  category: CandidateDriverCategory;
  note?: string | null;
}

/** 研究侧声明的可对照历史案例（产品端相似度另行实时计算） */
export interface ReferenceCase {
  campaign_id: string;
  note?: string | null;
}

export interface CurrentCandidate {
  candidate_id: string;
  snapshot_date: string;
  display_name: string;
  macro_theme: string | null;
  theme_type: string | null;
  core_narrative: string;
  candidate_status: CandidateStatus;
  /** 研究**声明**的阶段；产品端另按相位证据矩阵独立推导，不一致时不隐藏 */
  attention_state: CurrentPhase;
  phase_window: { start: string | null; end: string | null };
  /** 研究可只声明无法由证据派生的维度（narrative / breadth / information_marginal） */
  phase_evidence: Partial<Record<PhaseDimension, SignalLevel>>;
  evidence: EvidenceItem[];
  drivers: CandidateDriver[];
  narrative_types: NarrativeType[];
  reference_cases: ReferenceCase[];
  research_questions: string[];
  source_summary?: string | null;
  uncertainty_notes: string[];
  conflict_notes: string[];
  last_updated: string;
}

export interface CurrentCandidateDataset {
  contract: 'current_candidates';
  current_candidates_version: string;
  /** 研究快照日（PIT 基准）——所有判断只能使用 <= 它的证据 */
  snapshot_date: string;
  generated_at?: string;
  generated_by?: string;
  research_coverage_until?: number | null;
  scope?: string;
  note?: string;
  /** true = 示例 fixture，**不是**真实研究数据（UI 必须显式标注） */
  fixture?: boolean;
  candidates: CurrentCandidate[];
}

/** 空数据集（无 canonical 数据时的诚实兜底） */
export const EMPTY_CURRENT_CANDIDATE_DATASET: CurrentCandidateDataset = {
  contract: 'current_candidates',
  current_candidates_version: '1.0',
  snapshot_date: '',
  research_coverage_until: null,
  candidates: [],
};

/* ================= 3. 解析 / 适配 ================= */

export interface ParseResult {
  dataset: CurrentCandidateDataset;
  /** 非致命问题（产品端优雅降级，不因单条脏数据崩溃）；严格校验见 validate_current_research.py */
  issues: string[];
}

/* eslint-disable @typescript-eslint/no-explicit-any */
const str = (v: unknown): string | null => (typeof v === 'string' && v.length > 0 ? v : null);

function asStatus(v: unknown): CandidateStatus {
  return CANDIDATE_STATUS_ORDER.includes(v as CandidateStatus) ? (v as CandidateStatus) : 'CANDIDATE';
}

function asPhase(v: unknown): CurrentPhase {
  const ok: CurrentPhase[] = [
    'EARLY_SIGNAL',
    'THEME_FORMING',
    'BROAD_CONFIRMATION',
    'EXPANSION',
    'PEAK',
    'DECLINE',
    'UNKNOWN',
  ];
  return ok.includes(v as CurrentPhase) ? (v as CurrentPhase) : 'UNKNOWN';
}

function asLevel(v: unknown): SignalLevel {
  const ok: SignalLevel[] = ['ABSENT', 'EMERGING', 'PRESENT', 'STRONG', 'WEAKENING', 'UNKNOWN'];
  return ok.includes(v as SignalLevel) ? (v as SignalLevel) : 'UNKNOWN';
}

function asSourceType(v: unknown): EvidenceSourceType {
  const ok: EvidenceSourceType[] = [
    'POLICY',
    'INDUSTRY',
    'COMPANY',
    'MARKET',
    'MACRO',
    'CAPITAL',
    'SENTIMENT',
    'OTHER',
  ];
  return ok.includes(v as EvidenceSourceType) ? (v as EvidenceSourceType) : 'OTHER';
}

function asStrength(v: unknown): EvidenceStrength {
  const ok: EvidenceStrength[] = ['STRONG', 'MEDIUM', 'WEAK'];
  return ok.includes(v as EvidenceStrength) ? (v as EvidenceStrength) : 'WEAK';
}

function asDirection(v: unknown): EvidenceDirection {
  const ok: EvidenceDirection[] = ['SUPPORTIVE', 'NEUTRAL', 'NEGATIVE', 'UNKNOWN'];
  return ok.includes(v as EvidenceDirection) ? (v as EvidenceDirection) : 'UNKNOWN';
}

function asNarrative(v: unknown): NarrativeType {
  const ok: NarrativeType[] = [
    'POLICY_DRIVEN',
    'INDUSTRY_UPGRADE',
    'TECH_BREAKTHROUGH',
    'DEMAND_SURGE',
    'SUPPLY_CONTRACTION',
    'VALUATION_RESET',
    'CYCLE_REVERSAL',
    'EVENT_CATALYST',
    'UNKNOWN',
  ];
  return ok.includes(v as NarrativeType) ? (v as NarrativeType) : 'UNKNOWN';
}

function asDriverCategory(v: unknown): CandidateDriverCategory | null {
  return DRIVER_CATEGORIES.includes(v as CandidateDriverCategory)
    ? (v as CandidateDriverCategory)
    : null;
}

function parseCandidate(raw: any, dsSnapshot: string, issues: string[]): CurrentCandidate | null {
  const candidateId = str(raw?.candidate_id);
  if (!candidateId) {
    issues.push('丢弃一条候选：缺少 candidate_id');
    return null;
  }
  if (/^(C|RC)-/.test(candidateId)) {
    // 命名空间隔离：候选不得混入正式 Campaign / Research Candidate 命名空间
    issues.push(`${candidateId}：候选 ID 不得使用 C- / RC- 前缀（命名空间隔离）`);
  }

  const snapshot = str(raw.snapshot_date) ?? dsSnapshot;
  if (snapshot > dsSnapshot) {
    issues.push(`${candidateId}：candidate.snapshot_date(${snapshot}) 晚于数据集(${dsSnapshot})`);
  }

  const evidence: EvidenceItem[] = Array.isArray(raw?.evidence)
    ? raw.evidence.map((e: any, i: number) => ({
        evidence_id: str(e?.evidence_id) ?? `${candidateId}-E${i + 1}`,
        source_type: asSourceType(e?.source_type),
        source_title: str(e?.source_title),
        source_url: str(e?.source_url),
        source_date: str(e?.source_date),
        event_date: str(e?.event_date),
        claim: str(e?.claim) ?? '',
        evidence_strength: asStrength(e?.evidence_strength),
        direction: asDirection(e?.direction),
        temporal_relation: e?.temporal_relation
          ? (e.temporal_relation as TemporalRelation)
          : undefined,
      }))
    : [];

  const phaseEvidence: Partial<Record<PhaseDimension, SignalLevel>> = {};
  const rawMatrix = raw?.phase_evidence;
  if (rawMatrix && typeof rawMatrix === 'object') {
    for (const d of PHASE_DIMENSIONS) {
      if (rawMatrix[d] !== undefined) phaseEvidence[d] = asLevel(rawMatrix[d]);
    }
  }

  const narrativeTypes: NarrativeType[] = Array.isArray(raw?.narrative_types)
    ? raw.narrative_types.map(asNarrative).filter((n: NarrativeType) => n !== 'UNKNOWN')
    : [];

  return {
    candidate_id: candidateId,
    snapshot_date: snapshot,
    display_name: str(raw?.display_name) ?? candidateId,
    macro_theme: str(raw?.macro_theme),
    theme_type: str(raw?.theme_type),
    core_narrative: str(raw?.core_narrative) ?? '',
    candidate_status: asStatus(raw?.candidate_status),
    attention_state: asPhase(raw?.attention_state),
    phase_window: {
      start: str(raw?.phase_window?.start),
      end: str(raw?.phase_window?.end),
    },
    phase_evidence: phaseEvidence,
    evidence,
    drivers: Array.isArray(raw?.drivers)
      ? raw.drivers
          .map((d: any) => {
            const cat = asDriverCategory(d?.category);
            return cat ? { category: cat, note: str(d?.note) } : null;
          })
          .filter((d: any): d is CandidateDriver => d !== null)
      : [],
    narrative_types: narrativeTypes,
    reference_cases: Array.isArray(raw?.reference_cases)
      ? raw.reference_cases
          .map((r: any) => {
            const id = str(r?.campaign_id);
            return id ? { campaign_id: id, note: str(r?.note) } : null;
          })
          .filter((r: any): r is ReferenceCase => r !== null)
      : [],
    research_questions: Array.isArray(raw?.research_questions)
      ? raw.research_questions.filter((q: unknown): q is string => typeof q === 'string')
      : [],
    source_summary: str(raw?.source_summary),
    uncertainty_notes: Array.isArray(raw?.uncertainty_notes)
      ? raw.uncertainty_notes.filter((q: unknown): q is string => typeof q === 'string')
      : [],
    conflict_notes: Array.isArray(raw?.conflict_notes)
      ? raw.conflict_notes.filter((q: unknown): q is string => typeof q === 'string')
      : [],
    last_updated: str(raw?.last_updated) ?? snapshot,
  };
}

/**
 * 解析 Current Candidate 数据集。
 * 宽容解析（脏数据记入 `issues` 并降级），**不做**严格门槛 —— 严格校验由
 * `research/scripts/validate_current_research.py` 负责。
 */
export function parseCurrentCandidateDataset(raw: unknown): ParseResult {
  const issues: string[] = [];
  const obj = (raw ?? {}) as any;

  if (obj.contract !== 'current_candidates') {
    issues.push(`contract 应为 current_candidates，实际为 ${String(obj.contract)}`);
  }
  const snapshot = str(obj.snapshot_date) ?? '';
  if (snapshot === '') issues.push('缺少 snapshot_date（Temporal Firewall 无法工作）');

  const list: CurrentCandidate[] = Array.isArray(obj.candidates)
    ? obj.candidates
        .map((c: any) => parseCandidate(c, snapshot, issues))
        .filter((c: CurrentCandidate | null): c is CurrentCandidate => c !== null)
    : [];

  const seen = new Set<string>();
  for (const c of list) {
    if (seen.has(c.candidate_id)) issues.push(`candidate_id 重复：${c.candidate_id}`);
    seen.add(c.candidate_id);
  }

  return {
    dataset: {
      contract: 'current_candidates',
      current_candidates_version: str(obj.current_candidates_version) ?? '1.0',
      snapshot_date: snapshot,
      generated_at: str(obj.generated_at) ?? undefined,
      generated_by: str(obj.generated_by) ?? undefined,
      research_coverage_until:
        typeof obj.research_coverage_until === 'number' ? obj.research_coverage_until : null,
      scope: str(obj.scope) ?? undefined,
      note: str(obj.note) ?? undefined,
      fixture: obj.fixture === true,
      candidates: list,
    },
    issues,
  };
}

/* ================= 4. 数据入口 ================= */

/** canonical 数据集（`research/current/current_candidates.json`；Phase 7.1 起承载第一轮真实候选 5 条） */
export function defaultCurrentCandidateDataset(): CurrentCandidateDataset {
  return parseCurrentCandidateDataset(currentCandidatesJson).dataset;
}

/** canonical 数据集的解析结果（含解析告警，供 UI 透明展示） */
export function defaultCurrentCandidateParse(): ParseResult {
  return parseCurrentCandidateDataset(currentCandidatesJson);
}
