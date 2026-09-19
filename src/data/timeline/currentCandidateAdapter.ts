/**
 * Current Candidate Adapter（Phase 7）—— 把数据集 + 历史数据源聚合成 **UI 就绪的 View 模型**。
 *
 * ```
 * research/current/current_candidates.json          （离线研究 Artifact）
 *   + exports/timeline_export_v1.json               （历史研究数据）
 *        ↓  currentCandidate（协议 / 解析）
 *        ↓  currentEvidence（Evidence Ledger + Temporal Firewall + 矩阵 + 冲突 + 状态门）
 *        ↓  currentPhaseInference（透明规则引擎）
 *        ↓  currentSimilarity（Similarity v2）
 *   →  CurrentCandidateView[]                        （本模块的产物）
 * ```
 *
 * 每个 View 都**自带可追溯链**：证据台账 → 相位矩阵（含逐维来源）→ 命中的规则 id →
 * 相似案例（含四问答案）→ 研究问题。任何结论都能被追问「为什么」。
 *
 * ## 边界
 * 纯 View / Adapter 层：不写 DB / schema / export / contracts；
 * 不把候选升级为正式 Campaign；不联网；不输出概率 / 评分。
 */

import type { TimelineDataSource } from './timelineTypes';
import {
  type CandidateDriverCategory,
  type CurrentCandidate,
  type CurrentCandidateDataset,
  type CurrentPhase,
  type EvidenceSourceType,
  type NarrativeType,
  type PhaseDimension,
  CANDIDATE_STATUS_LABEL,
  DRIVER_CATEGORIES,
  DIMENSION_LABEL,
  EVIDENCE_SOURCE_LABEL,
  NARRATIVE_TYPE_LABEL,
  PHASE_DIMENSIONS,
  SIGNAL_LEVEL_LABEL,
} from './currentCandidate';
import {
  type ConflictKind,
  type ConflictNote,
  type EvidenceLedger,
  type EvidenceSummary,
  type PhaseEvidenceMatrix,
  AGGREGATE_LEVEL_LABEL,
  CONFLICT_KIND_LABEL,
  candidateStatusGateOf,
  conflictsOf,
  evidenceLedgerOf,
  evidenceSummaryOf,
} from './currentEvidence';
import {
  type CoverageLevel,
  type PhaseInference,
  COVERAGE_LABEL,
  inferCurrentPhase,
} from './currentPhaseInference';
import {
  type CurrentSimilarityView,
  similarPhaseForCandidate,
} from './currentSimilarity';
import { PHASE_LABEL } from './researchAttention';
import { PRE_OBSERVATION_LABEL, PRE_OBSERVATION_HINT } from './preObservation';
import { diffDays } from '../../utils';

/* ================= 0. 快照新鲜度阈值 ================= */

/**
 * 快照「滞后」阈值（自然日）。
 *
 * ThreeC **不是实时系统**：Current Research 由**离线**生成，观察尺度为**周级**，
 * Refresh Loop 是可重复的更新流程，而不是实时行情服务。
 *
 * 因此「距今天 > 0 天」不等于「研究已过期」—— 若按 0 天判定，**365 天中 364 天**
 * 都会显示「当前研究快照已滞后」，把「**不是实时数据**」错误地表达成「**研究已经过期**」。
 *
 * 14 天足以覆盖正常的研究更新周期，作为简单的产品提醒阈值。
 * **不引入动态阈值 / freshness score / 新状态**（仍只有 `stalenessDays` + `stale`）。
 */
export const SNAPSHOT_STALE_THRESHOLD_DAYS = 14;

/* ================= 1. Driver Profile（候选侧） ================= */

/**
 * 证据来源 → Driver Profile 分类（与历史侧 `driverCategoriesOf` 的映射保持一致，
 * 这样两侧的 Driver 重叠才有意义）。
 */
const SOURCE_TO_DRIVER: Partial<Record<EvidenceSourceType, CandidateDriverCategory>> = {
  POLICY: 'POLICY',
  INDUSTRY: 'INDUSTRY',
  COMPANY: 'INDUSTRY',
  MARKET: 'CAPITAL',
  CAPITAL: 'CAPITAL',
  MACRO: 'EXTERNAL',
  SENTIMENT: 'SENTIMENT',
};

/** 候选的 Driver Profile：研究声明优先，缺失部分由可用证据来源**确定性派生** */
export function candidateDriversOf(candidate: CurrentCandidate, ledger: EvidenceLedger): CandidateDriverCategory[] {
  const set = new Set<CandidateDriverCategory>(candidate.drivers.map((d) => d.category));
  for (const { item } of ledger.admissible) {
    const cat = SOURCE_TO_DRIVER[item.source_type];
    if (cat) set.add(cat);
  }
  return DRIVER_CATEGORIES.filter((c) => set.has(c));
}

/* ================= 2. 升级条件的透明核对表 ================= */

export interface UpgradeCriterion {
  id: string;
  label: string;
  met: boolean;
  detail: string;
}

/**
 * 「为什么它现在仍是 Current Candidate，而不是正式 Research Campaign」的核对表。
 * 这是 ThreeC 与「AI 投资热点总结器」最大的区别之一：**必须说明缺什么**。
 */
export function upgradeCriteriaOf(
  candidate: CurrentCandidate,
  summary: EvidenceSummary,
  conflicts: ConflictNote[],
  matrix: PhaseEvidenceMatrix,
  phase: CurrentPhase,
): UpgradeCriterion[] {
  const presentPlus = (l: string) => l === 'PRESENT' || l === 'STRONG';
  const activePhase: CurrentPhase[] = ['EARLY_SIGNAL', 'THEME_FORMING', 'BROAD_CONFIRMATION', 'EXPANSION'];
  return [
    {
      id: 'EVIDENCE_COUNT',
      label: '至少 2 条快照内的可用证据',
      met: summary.admissibleCount >= 2,
      detail: `当前可用证据 ${summary.admissibleCount} 条（${AGGREGATE_LEVEL_LABEL[summary.level]}）`,
    },
    {
      id: 'NO_CONFLICT',
      label: '不存在证据方向冲突',
      met: conflicts.length === 0,
      detail: conflicts.length === 0 ? '未检测到方向冲突' : `检测到 ${conflicts.length} 项冲突`,
    },
    {
      id: 'PHASE_ACTIVE',
      label: '阶段属于 早期信号 / 主题形成 / 广泛确认 / 扩张',
      met: activePhase.includes(phase),
      detail: `推导阶段：${PHASE_LABEL[phase]}`,
    },
    {
      id: 'INDUSTRY_OR_COMPANY',
      label: '存在产业层或公司层的明确证据',
      met: presentPlus(matrix.industry.level) || presentPlus(matrix.company.level),
      detail:
        `产业层：${SIGNAL_LEVEL_LABEL[matrix.industry.level]}；` +
        `公司层：${SIGNAL_LEVEL_LABEL[matrix.company.level]}`,
    },
    {
      id: 'BREADTH',
      label: '扩散广度不少于「明确」',
      met: presentPlus(matrix.breadth.level),
      detail: `扩散广度：${SIGNAL_LEVEL_LABEL[matrix.breadth.level]}（研究声明维度）`,
    },
  ];
}

/* ================= 3. Research Questions（研究方向生成） ================= */

/**
 * 生成**研究问题**（不是买卖问题）。
 *
 * 全部由模板 + 现有证据确定性生成：缺哪个维度就问哪个维度，
 * 相似案例存在就问「该阶段历史上出现过什么分歧」。
 * 问题不构成建议、不指向买卖、不预测。
 */
export function researchQuestionsOf(
  candidate: CurrentCandidate,
  matrix: PhaseEvidenceMatrix,
  phase: CurrentPhase,
  conflicts: ConflictNote[],
  similarity: CurrentSimilarityView,
  summary: EvidenceSummary,
): string[] {
  const q: string[] = [];

  q.push(
    `「该方向当前处于${PHASE_LABEL[phase]}」这一判断，最有力的反证会是什么？` +
      '需要哪些事实才能推翻它？',
  );

  if (matrix.policy.level === 'ABSENT' || matrix.policy.level === 'UNKNOWN') {
    q.push('当前是否存在政策 / 监管层面的持续制度变化？还是只有一次性事件？');
  } else {
    q.push('现有政策催化是一次性事件，还是持续性制度变化？后续观察窗口是什么？');
  }

  if (!(matrix.industry.level === 'PRESENT' || matrix.industry.level === 'STRONG')) {
    q.push('产业层（订单 / 产能 / 价格 / 招标）是否已开始验证该叙事？');
  }
  if (!(matrix.company.level === 'PRESENT' || matrix.company.level === 'STRONG')) {
    q.push('是否出现公司层验证（收入 / 订单 / 产能 / 产品注册）？哪些公司最可能先给出验证？');
  }
  if (!(matrix.breadth.level === 'PRESENT' || matrix.breadth.level === 'STRONG')) {
    q.push('市场关注是否已从少数标的扩散到产业链其他环节？扩散路径可能是什么？');
  }
  if (phase === 'EARLY_SIGNAL' || phase === 'THEME_FORMING') {
    q.push('该方向与更大上位叙事（Macro Theme）的边界是什么？会不会被上位叙事吸收？');
  }

  for (const r of similarity.results.slice(0, 2)) {
    q.push(`历史相似案例「${r.title} · ${r.year}」在该阶段出现过哪些主要分歧？后来如何演化？`);
  }
  if (similarity.insufficient) {
    q.push('历史研究数据中缺少同阶段可比案例 —— 需要先补哪一段历史研究才能形成参照？');
  }

  if (conflicts.length > 0) {
    q.push('政策 / 基本面证据与市场证据方向不一致：应如何交叉验证以判断哪一方更接近事实？');
  }
  if (summary.admissibleCount === 0) {
    q.push('该候选目前没有任何可核验证据 —— 应该从哪一类一手来源开始收集？');
  }

  q.push('历史上什么信号出现时，意味着该主题开始失效？本方向是否存在对应的观察指标？');
  return q;
}

/* ================= 4. View 模型 ================= */

export interface CandidateConflictView extends ConflictNote {
  kindLabel: string;
}

export interface CurrentCandidateView {
  candidate: CurrentCandidate;
  ledger: EvidenceLedger;
  summary: EvidenceSummary;
  matrix: PhaseEvidenceMatrix;
  inference: PhaseInference;
  conflicts: CandidateConflictView[];
  gate: {
    declared: CurrentCandidate['candidate_status'];
    declaredLabel: string;
    effective: CurrentCandidate['candidate_status'];
    effectiveLabel: string;
    demoted: boolean;
    reasons: string[];
  };
  similarity: CurrentSimilarityView;
  /** Driver Profile（研究声明优先，缺失由证据来源确定性派生） */
  drivers: CandidateDriverCategory[];
  researchQuestions: string[];
  upgradeCriteria: UpgradeCriterion[];

  /** 展示用阶段（= 推导值）与标签 */
  phase: CurrentPhase;
  phaseLabel: string;
  coverage: { level: CoverageLevel; label: string; known: number; total: number };
  /** 一句话解释（研究叙事） */
  oneLiner: string;
  /** 尚未达到「明确」水平的维度（用于「为什么仍只是候选」） */
  missingDimensions: PhaseDimension[];
  /** 是否具备进入研究的最低条件（至少 1 条快照内可用证据） */
  researchReady: boolean;
  /** 是否可直接作为相似度参照（阶段已推导出） */
  similarityReady: boolean;
}

export interface CurrentCandidateListView {
  snapshotDate: string;
  fixture: boolean;
  researchCoverageUntil: number | null;
  views: CurrentCandidateView[];
  /** 解析期发现的问题（非致命） */
  issues: string[];
  /** 快照滞后于今天的自然日数（null = 快照日缺失） */
  stalenessDays: number | null;
  /** 快照是否**超过滞后阈值**（`SNAPSHOT_STALE_THRESHOLD_DAYS`）；UI 据此提示「不是实时研究结果」 */
  stale: boolean;
}

/**
 * 构建全部候选的 View。
 *
 * @param source   历史 TimelineDataSource（相似度检索用）
 * @param dataset  Current Candidate 数据集
 * @param today    A股市场日期（**只用于提示快照滞后天数**，不参与任何研究判断）
 * @param issues   解析期发现的问题（由 `parseCurrentCandidateDataset` 提供，原样透传）
 */
export function buildCurrentCandidateViews(
  source: TimelineDataSource,
  dataset: CurrentCandidateDataset,
  today: string,
  issues: string[] = [],
): CurrentCandidateListView {
  const views: CurrentCandidateView[] = [];

  for (const candidate of dataset.candidates) {
    const ledger = evidenceLedgerOf(candidate);
    const summary = evidenceSummaryOf(ledger);
    const drivers = candidateDriversOf(candidate, ledger);
    const inference = inferCurrentPhase(candidate, ledger);
    const conflicts = conflictsOf(candidate, ledger, inference.matrix).map((c) => ({
      ...c,
      kindLabel: CONFLICT_KIND_LABEL[c.kind as ConflictKind],
    }));
    const gate = candidateStatusGateOf(candidate, summary, conflicts, inference.phase);
    const similarity = similarPhaseForCandidate(source, candidate, inference.phase, drivers);
    const upgradeCriteria = upgradeCriteriaOf(
      candidate,
      summary,
      conflicts,
      inference.matrix,
      inference.phase,
    );

    const missingDimensions = PHASE_DIMENSIONS.filter((d) =>
      ['ABSENT', 'UNKNOWN', 'EMERGING'].includes(inference.matrix[d].level),
    );

    const declaredQuestions = candidate.research_questions;
    const generated = researchQuestionsOf(
      candidate,
      inference.matrix,
      inference.phase,
      conflicts,
      similarity,
      summary,
    );

    views.push({
      candidate,
      ledger,
      summary,
      matrix: inference.matrix,
      inference,
      conflicts,
      gate: {
        declared: gate.declared,
        declaredLabel: CANDIDATE_STATUS_LABEL[gate.declared],
        effective: gate.effective,
        effectiveLabel: CANDIDATE_STATUS_LABEL[gate.effective],
        demoted: gate.demoted,
        reasons: gate.reasons,
      },
      similarity,
      drivers,
      researchQuestions: declaredQuestions.length > 0 ? declaredQuestions : generated,
      upgradeCriteria,
      phase: inference.phase,
      phaseLabel: PHASE_LABEL[inference.phase],
      coverage: {
        level: inference.coverage.level,
        label: COVERAGE_LABEL[inference.coverage.level],
        known: inference.coverage.knownDimensions,
        total: inference.coverage.totalDimensions,
      },
      oneLiner: candidate.core_narrative,
      missingDimensions,
      researchReady: summary.admissibleCount > 0,
      similarityReady: inference.phase !== 'UNKNOWN',
    });
  }

  // 排序：阶段靠前的优先（研究价值顺序），同等阶段按证据充分度，最后按 ID（确定性）
  const PHASE_RANK: Record<CurrentPhase, number> = {
    EARLY_SIGNAL: 0,
    THEME_FORMING: 1,
    BROAD_CONFIRMATION: 2,
    EXPANSION: 3,
    PEAK: 4,
    DECLINE: 5,
    UNKNOWN: 6,
  };
  const LEVEL_RANK: Record<EvidenceSummary['level'], number> = {
    HIGH: 0,
    MEDIUM: 1,
    LOW: 2,
    UNKNOWN: 3,
  };
  views.sort((a, b) => {
    if (PHASE_RANK[a.phase] !== PHASE_RANK[b.phase]) return PHASE_RANK[a.phase] - PHASE_RANK[b.phase];
    if (LEVEL_RANK[a.summary.level] !== LEVEL_RANK[b.summary.level]) {
      return LEVEL_RANK[a.summary.level] - LEVEL_RANK[b.summary.level];
    }
    return a.candidate.candidate_id < b.candidate.candidate_id ? -1 : 1;
  });

  const snapshotDate = dataset.snapshot_date;
  const stalenessDays = snapshotDate ? diffDays(snapshotDate, today) : null;

  return {
    snapshotDate,
    fixture: dataset.fixture === true,
    researchCoverageUntil: dataset.research_coverage_until ?? null,
    views,
    issues: [],
    stalenessDays,
    // ★ 仅在**超过阈值**（`SNAPSHOT_STALE_THRESHOLD_DAYS` = 14 天）时才提示滞后。
    //   0–14 天属正常研究节奏 → 只展示「研究快照 / 距今天 / 覆盖年份 / 离线生成」元信息，
    //   不显示 stale warning。
    stale: stalenessDays !== null && stalenessDays > SNAPSHOT_STALE_THRESHOLD_DAYS,
  };
}

/** 供 UI 复用的文案（保证全站措辞一致） */
export const CURRENT_CANDIDATE_HINT =
  'Current Candidate 是**研究对象**，不是已验证 Theme，也不是正式 Campaign；' +
  '网络与 AI 只作为离线研究数据生成器，不进入运行时。';

export const CURRENT_SIMILARITY_DISCLAIMER =
  `相似的是**阶段与结构**，不是未来走势。等级（高相似 / 中相似 / 参考案例）来自` +
  '「阶段 → Theme Cycle Pattern → Drivers → Narrative 结构」的可解释比对，' +
  '不是概率、不是评分、不是买卖信号。';

export { PRE_OBSERVATION_LABEL, PRE_OBSERVATION_HINT, NARRATIVE_TYPE_LABEL, DIMENSION_LABEL, EVIDENCE_SOURCE_LABEL };

/** 类型再导出，便于 UI 层单点导入 */
export type { EvidenceLedger, EvidenceSummary, PhaseEvidenceMatrix, PhaseInference, CurrentSimilarityView };
export type { NarrativeType };
