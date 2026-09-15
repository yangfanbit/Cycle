/**
 * Current Phase Inference v1（Phase 7）—— **透明的规则引擎**。
 *
 * ## 为什么不用单一指标
 * 绝不允许写 `涨幅 > X ⇒ EXPANSION` 这类逻辑。阶段必须来自**多维证据组合**：
 * 叙事 / 政策 / 产业 / 市场 / 资金 / 广度 / 公司层，加上「新增信息边际」
 * （用于区分 PEAK 与 EXPANSION —— §11 中 PEAK 的特征是「新增信息边际下降」）。
 *
 * ## 规则是可审计的
 * 每条规则有固定 id 与人类可读说明；命中的规则 id 会暴露给 UI，
 * 因此任何阶段结论都能被追问「为什么」。
 *
 * ## 不编造
 * 证据不足时返回 `UNKNOWN` —— 这是正常结果，不是错误。
 *
 * ## 边界
 * 纯 View / Research Navigation 层：不写 DB / schema / export / contracts；不输出概率。
 */

import {
  DIMENSION_LABEL,
  SIGNAL_LEVEL_LABEL,
  type CurrentCandidate,
  type CurrentPhase,
  type PhaseDimension,
  PHASE_DIMENSIONS,
} from './currentCandidate';
import type { EvidenceLedger, PhaseEvidenceMatrix } from './currentEvidence';
import { phaseMatrixOf } from './currentEvidence';
import { PHASE_LABEL } from './researchAttention';

/** 证据覆盖度（**不是概率**，是「有多少维度有标注」的计数表达） */
export type CoverageLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';

export const COVERAGE_LABEL: Record<CoverageLevel, string> = {
  HIGH: '维度覆盖较全',
  MEDIUM: '维度覆盖中等',
  LOW: '维度覆盖较少',
  UNKNOWN: '无维度标注',
};

export interface PhaseInference {
  /** 推导阶段（权威值；研究声明值并列保留在 declared） */
  phase: CurrentPhase;
  /** 命中的规则 id（可审计） */
  matchedRule: string;
  /** 命中规则的人类可读说明 */
  ruleLabel: string;
  /** 逐条理由（为什么是这个阶段） */
  reasons: string[];
  /** 完整的相位证据矩阵（含每维来源与依据） */
  matrix: PhaseEvidenceMatrix;
  coverage: { knownDimensions: number; totalDimensions: number; level: CoverageLevel };
  /** 研究声明的阶段 */
  declared: CurrentPhase;
  /** 推导值是否与声明一致（不一致时 UI **必须并列显示**，不得静默取一） */
  agreesWithDeclared: boolean;
  /** 声明值 vs 证据派生值的差异（来自矩阵合并） */
  disagreements: string[];
}

const emergingPlus = (l: string): boolean => l === 'EMERGING' || l === 'PRESENT' || l === 'STRONG';
const presentPlus = (l: string): boolean => l === 'PRESENT' || l === 'STRONG';
const inSet = (l: string, set: string[]): boolean => set.includes(l);

/**
 * 可由证据派生的维度。这五个维度若**全部**为 UNKNOWN，说明快照内没有任何证据
 * 支撑（研究声明的 narrative / breadth / information_marginal 不构成证据）
 * → 必须返回 UNKNOWN，不得据此推断阶段。
 */
const EVIDENCE_DERIVED_DIMENSIONS: PhaseDimension[] = [
  'policy',
  'industry',
  'company',
  'market',
  'capital',
];

/** 规则表（顺序即优先级，首个命中者生效） */
interface Rule {
  id: string;
  label: string;
  test: (m: PhaseEvidenceMatrix) => boolean;
  phase: CurrentPhase;
  reason: (m: PhaseEvidenceMatrix) => string;
}

const lv = (m: PhaseEvidenceMatrix, d: PhaseDimension) => m[d].level;

/**
 * 规则（**自上而下，首个命中生效**）：
 *
 * | id | 条件 | 结论 |
 * |---|---|---|
 * | R0 | 叙事与市场都无信号，**或**可由证据派生的维度全部无信号 | UNKNOWN（证据不足，不编造） |
 * | R1 | 叙事转弱 | DECLINE |
 * | R2 | 市场缺失/转弱 且 政策/产业/公司均无明确证据 | DECLINE |
 * | R3 | 叙事强 + 广度强 + 市场强 + 新增信息边际下降/饱和 | PEAK |
 * | R4 | 市场明确+ + 广度明确+ + 叙事明确+ | EXPANSION |
 * | R5 | 产业或公司明确+ ，且市场明确+ | BROAD_CONFIRMATION |
 * | R6 | 叙事明确+ ，且政策/产业/公司初现+ ，且市场初现/明确 | THEME_FORMING |
 * | R7 | 叙事初现 ，且市场无/初现/未标注 | EARLY_SIGNAL |
 * | R8 | 其余 | UNKNOWN |
 */
const RULES: Rule[] = [
  {
    id: 'R0_INSUFFICIENT_EVIDENCE',
    label: '叙事与市场都无信号（或可由证据派生的维度全部无信号）→ 证据不足',
    test: (m) =>
      (inSet(lv(m, 'narrative'), ['ABSENT', 'UNKNOWN']) &&
        inSet(lv(m, 'market'), ['ABSENT', 'UNKNOWN'])) ||
      EVIDENCE_DERIVED_DIMENSIONS.every((d) => lv(m, d) === 'UNKNOWN'),
    phase: 'UNKNOWN',
    reason: () =>
      '快照内没有任何可核验的证据信号（政策 / 产业 / 公司 / 市场 / 资金均未标注），' +
      '不做阶段推断（不编造）。研究声明的叙事 / 广度不构成证据。',
  },
  {
    id: 'R1_NARRATIVE_WEAKENING',
    label: '叙事主线转弱 → 退潮',
    test: (m) => lv(m, 'narrative') === 'WEAKENING',
    phase: 'DECLINE',
    reason: () => '叙事主线已转弱（出现反向证据或共识瓦解迹象），符合退潮特征。',
  },
  {
    id: 'R2_MARKET_ABSENT_WITHOUT_BASIS',
    label: '市场缺失/转弱，且政策、产业、公司层均无明确证据 → 退潮',
    test: (m) =>
      inSet(lv(m, 'market'), ['ABSENT', 'WEAKENING']) &&
      !presentPlus(lv(m, 'policy')) &&
      !presentPlus(lv(m, 'industry')) &&
      !presentPlus(lv(m, 'company')),
    phase: 'DECLINE',
    reason: () => '市场关注缺失或转弱，且基本面 / 政策层没有明确证据支撑，按退潮处理。',
  },
  {
    id: 'R3_PEAK_SATURATION',
    label: '叙事强 + 广度强 + 市场强 + 新增信息边际下降 → 峰值',
    test: (m) =>
      lv(m, 'narrative') === 'STRONG' &&
      lv(m, 'breadth') === 'STRONG' &&
      lv(m, 'market') === 'STRONG' &&
      presentPlus(lv(m, 'information_marginal')),
    phase: 'PEAK',
    reason: () =>
      '叙事高度一致、扩散广度极大、市场关注极高，同时新增信息边际下降 —— 符合峰值特征。',
  },
  {
    id: 'R4_EXPANSION_DIFFUSION',
    label: '市场明确+ + 广度明确+ + 叙事明确+ → 扩张',
    test: (m) => presentPlus(lv(m, 'market')) && presentPlus(lv(m, 'breadth')) && presentPlus(lv(m, 'narrative')),
    phase: 'EXPANSION',
    reason: () => '市场注意力显著上升，且叙事已从少数标的扩散到更广范围 —— 符合扩张特征。',
  },
  {
    id: 'R5_BROAD_CONFIRMATION',
    label: '产业或公司层明确+ ，且市场明确+ → 广泛确认',
    test: (m) => (presentPlus(lv(m, 'industry')) || presentPlus(lv(m, 'company'))) && presentPlus(lv(m, 'market')),
    phase: 'BROAD_CONFIRMATION',
    reason: () => '产业层 / 公司层与市场层同时给出明确证据，属于多源共同验证。',
  },
  {
    id: 'R6_THEME_FORMING',
    label: '叙事明确+ ，且政策/产业/公司初现+ ，且市场初现/明确 → 主题形成',
    test: (m) =>
      presentPlus(lv(m, 'narrative')) &&
      (emergingPlus(lv(m, 'policy')) || emergingPlus(lv(m, 'industry')) || emergingPlus(lv(m, 'company'))) &&
      inSet(lv(m, 'market'), ['EMERGING', 'PRESENT']),
    phase: 'THEME_FORMING',
    reason: () => '叙事主线已经清晰，且出现政策 / 产业 / 公司层证据，市场开始响应。',
  },
  {
    id: 'R7_EARLY_SIGNAL',
    label: '叙事初现，且市场无/初现/未标注 → 早期信号',
    test: (m) => lv(m, 'narrative') === 'EMERGING' && inSet(lv(m, 'market'), ['ABSENT', 'EMERGING', 'UNKNOWN']),
    phase: 'EARLY_SIGNAL',
    reason: () => '叙事刚出现、证据量少，市场尚未明显响应 —— 符合早期信号特征。',
  },
  {
    id: 'R8_UNCLASSIFIED',
    label: '证据组合不满足任何阶段规则 → 不推断',
    test: () => true,
    phase: 'UNKNOWN',
    reason: () => '现有证据组合不满足任何阶段判定规则，保持 UNKNOWN（不强行归类）。',
  },
];

function coverageOf(matrix: PhaseEvidenceMatrix) {
  const known = PHASE_DIMENSIONS.filter((d) => matrix[d].level !== 'UNKNOWN').length;
  const total = PHASE_DIMENSIONS.length;
  const level: CoverageLevel =
    known === 0 ? 'UNKNOWN' : known >= 6 ? 'HIGH' : known >= 4 ? 'MEDIUM' : 'LOW';
  return { knownDimensions: known, totalDimensions: total, level };
}

/**
 * 由相位证据矩阵推导当前阶段（**确定性、可审计**）。
 * 调用方若已持有 ledger / matrix，请使用 `inferPhaseFromMatrix` 以避免重复计算。
 */
export function inferCurrentPhase(candidate: CurrentCandidate, ledger: EvidenceLedger): PhaseInference {
  const { matrix, disagreements } = phaseMatrixOf(candidate, ledger);
  return inferPhaseFromMatrix(candidate, matrix, disagreements);
}

/** 由已构建好的矩阵推导阶段（纯函数） */
export function inferPhaseFromMatrix(
  candidate: CurrentCandidate,
  matrix: PhaseEvidenceMatrix,
  disagreements: string[] = [],
): PhaseInference {
  const rule = RULES.find((r) => r.test(matrix)) ?? RULES[RULES.length - 1];
  const reasons: string[] = [rule.reason(matrix)];

  // 把矩阵中「已标注」的维度逐条列出，作为可复核依据
  for (const d of PHASE_DIMENSIONS) {
    const e = matrix[d];
    if (e.level === 'UNKNOWN') continue;
    reasons.push(`${DIMENSION_LABEL[d]}：${SIGNAL_LEVEL_LABEL[e.level]} — ${e.basis}`);
  }

  const phase = rule.phase;
  const declared = candidate.attention_state;
  if (phase !== declared) {
    reasons.push(
      `推导阶段「${PHASE_LABEL[phase]}」与研究声明「${PHASE_LABEL[declared]}」不一致 —— ` +
        '两者并列保留，不静默取舍。',
    );
  }

  return {
    phase,
    matchedRule: rule.id,
    ruleLabel: rule.label,
    reasons,
    matrix,
    coverage: coverageOf(matrix),
    declared,
    agreesWithDeclared: phase === declared,
    disagreements,
  };
}
