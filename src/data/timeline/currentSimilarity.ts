/**
 * Current Similarity v2（Phase 7）—— **Historical Campaign × Current Candidate**。
 *
 * `historicalSimilarPhase.ts`（v1）只支持「历史 × 历史」。本模块把它扩展到
 * 「**当前候选 × 历史**」：给定一个 Current Candidate 与历史 TimelineDataSource，
 * 找出历史上**生命周期位置相近**的案例。
 *
 * ## 五层（解释性相似度；不做机器学习、不做文本相似度）
 * | 层 | 内容 | 权重（内部） |
 * |---|---|---|
 * | 1 Lifecycle Phase | 历史案例**曾经历**该阶段 30 / 曾经历相邻阶段 15；都没有 → 不进入结果 | 最高 |
 * | 2 Theme Pattern | 相同 12 / Hybrid 与任一 5 | 中 |
 * | 3 Driver Profile | Policy/Industry/Capital/Macro/Sentiment 标签重叠 × 5 | 中 |
 * | 4 Narrative Structure | **结构化叙事类型**重叠 × 4（不是文字相似） | 中 |
 * | 5 Phase Position | 候选自身在其阶段窗口内的位置 | **不进入分数**（见下） |
 *
 * ### 第 1 层的口径（重要）
 * 比较对象是「候选**当前所处**的阶段」与「历史案例**曾经经过**的阶段」
 * （`stagesPassedOf`），**不是**历史案例的终态阶段 —— 历史案例相对快照都已完成，
 * 用终态阶段去比对一个正在形成的候选，将永远匹配不到早期阶段，失去意义。
 * 因此结果会同时给出：
 *   - 历史案例当时处于该阶段的**日期区间**（② 当时处于什么阶段）
 *   - 该案例后来**如何结束**（④ 后来怎么结束）
 *
 * 第 4 层的意义：即使「AI 医疗」与历史某个「创新药」文字完全不同，
 * 若同为 `INDUSTRY_UPGRADE + POLICY_DRIVEN`，仍能被识别为结构相似。
 *
 * 第 5 层的诚实说明：历史案例相对快照是**已完成**的（progress 恒为 1），
 * 与「候选处于阶段窗口的何处」不可比。因此 v0.1 只用它做**候选侧展示**
 * （`phasePositionOf`），**不参与相似度打分**，更不显示成概率。
 *
 * ## Temporal Firewall（相似度侧）
 * 只允许 **`end <= snapshot_date`** 的历史对象作为参照 —— 否则它的终态阶段
 * 属于快照之后的未来信息，会构成 look-ahead。
 *
 * ## 输出约束
 * - 最多 **Top 3**；**无百分比**；等级为「高相似 / 中相似 / 参考案例」。
 * - 必须给出「为什么类似」。
 * - 找不到足够证据 → 空态，**不强行凑数**。
 * - UI 必须声明：相似的是**阶段与结构**，不是未来走势。
 *
 * ## 边界
 * 纯 View / Research Navigation 层：不写 DB / schema / export / contracts；不联网。
 */

import narrativeAnnotationsJson from '@current/narrative_annotations.json';
import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import {
  allResearchObjects,
  driverCategoriesOf,
  macroThemeOf,
  patternOf,
  stagesPassedOf,
  terminalPhaseOf,
  themeCycleViewsOf,
  DRIVER_LABEL,
  PATTERN_LABEL,
  PHASE_ADJACENT,
  PHASE_LABEL,
  phaseOfStage,
  type DriverCategory,
  type ResearchPhase,
  type ThemeCyclePattern,
} from './researchAttention';
import {
  TIER_LABEL,
  TIER_STARS,
  type SimilarTier,
} from './historicalSimilarPhase';
import { preObservationChainOf } from './preObservation';
import {
  NARRATIVE_TYPE_LABEL,
  type CurrentCandidate,
  type NarrativeType,
} from './currentCandidate';
import { diffDays } from '../../utils';

/* ================= 1. 结构化叙事类型（历史侧标注） ================= */

interface NarrativeAnnotationFile {
  contract: 'narrative_annotations';
  version: string;
  status: string;
  annotations: { campaign_id: string; narrative_types: string[]; provenance: string }[];
}

const NARRATIVE_ANNOTATIONS = (
  narrativeAnnotationsJson as unknown as NarrativeAnnotationFile
).annotations;

const NARRATIVE_BY_CAMPAIGN = new Map<string, NarrativeType[]>(
  NARRATIVE_ANNOTATIONS.map((a) => [a.campaign_id, a.narrative_types as NarrativeType[]]),
);

/** 历史对象的结构化叙事类型（未标注 → 空数组 → 该层不参与，**不推断**） */
export function narrativeTypesOfCampaign(campaignId: string): NarrativeType[] {
  return NARRATIVE_BY_CAMPAIGN.get(campaignId) ?? [];
}

/** 叙事标注的出处（可逐条复核；无标注 → null） */
export function narrativeProvenanceOf(campaignId: string): string | null {
  return NARRATIVE_ANNOTATIONS.find((a) => a.campaign_id === campaignId)?.provenance ?? null;
}

/* ================= 2. 候选侧的 Pattern / 阶段位置 ================= */

/**
 * 候选的 Theme Cycle Pattern。
 *
 * 候选本身**还没有 Theme Cycle**（它是研究对象，不是周期）。因此按
 * 「该 Macro Theme 历史上已观察到的 cycle 形态」推导：
 * ```
 * macro_theme 为空 / 该 Macro Theme 无历史 cycle → UNKNOWN（不推断）
 * 历史 cycle 形态一致                            → 该形态
 * 不一致                                        → HYBRID
 * ```
 * 这是确定性推导，且依据完全来自既有研究数据，可复核。
 */
export function candidatePatternOf(
  source: TimelineDataSource,
  candidate: CurrentCandidate,
): ThemeCyclePattern {
  if (!candidate.macro_theme) return 'UNKNOWN';
  const cycles = themeCycleViewsOf(source).filter((c) => c.macroTheme === candidate.macro_theme);
  if (cycles.length === 0) return 'UNKNOWN';
  const patterns = new Set(cycles.map((c) => c.pattern));
  if (patterns.size === 1) return [...patterns][0];
  return 'HYBRID';
}

/**
 * 候选在其当前阶段窗口内的位置（**仅候选侧展示；不进入相似度、不是概率**）。
 * 无 `phase_window.start` 或无法确定 end → null（不编造）。
 */
export function phasePositionOf(
  candidate: CurrentCandidate,
  asOf: string,
): { days: number; totalDays: number | null; ratio: number | null } | null {
  const start = candidate.phase_window.start;
  if (!start) return null;
  const end = candidate.phase_window.end;
  if (!end) return { days: Math.max(diffDays(start, asOf), 0), totalDays: null, ratio: null };
  const total = diffDays(start, end);
  const days = Math.max(diffDays(start, asOf), 0);
  return { days, totalDays: total, ratio: total > 0 ? Math.min(days / total, 1) : null };
}

/* ================= 3. 相似度计算 ================= */

/** 内部权重（**不显示为分数 / 百分比**） */
export const SIMILARITY_WEIGHTS = {
  PHASE_SAME: 30,
  PHASE_ADJACENT: 15,
  PATTERN_SAME: 12,
  PATTERN_HYBRID: 5,
  DRIVER_EACH: 5,
  NARRATIVE_EACH: 4,
} as const;

export interface SimilarLayerNote {
  id: 'PHASE' | 'PATTERN' | 'DRIVERS' | 'NARRATIVE';
  label: string;
  matched: boolean;
  detail: string;
}

/** 历史相似案例（必须回答四个问题） */
export interface CurrentSimilarCase {
  campaign_id: string;
  title: string;
  year: number;
  kind: 'campaign' | 'candidate';
  start: string;
  end: string;

  /** ② 当时处于什么阶段？——历史案例**曾经过**的匹配阶段 */
  phase: ResearchPhase;
  phaseLabel: string;
  /** 阶段匹配方式（相同 / 相邻） */
  phaseMatch: PhaseMatchKind;
  phaseMatchLabel: string;
  /** 历史案例当时处于该阶段的日期区间（无 lifecycle 分段 → null） */
  matchedStage: { stage: string; start: string; end: string; precision: string } | null;

  /** ③ 当时为什么形成？（研究层已记录的归因 + 分类标签） */
  drivers: DriverCategory[];
  driverNotes: string[];
  narrativeTypes: NarrativeType[];
  narrativeTypesLabel: string;

  /** ④ 后来怎么结束？ */
  terminalPhase: ResearchPhase;
  terminalPhaseLabel: string;

  /** ① 历史上什么时候开始值得关注？（提前观察参考区） */
  preObservation: {
    formation: string;
    formationAnchor: string;
    start: string;
    end: string;
    days: number;
    earlySignal: { start: string; end: string } | null;
  } | null;

  pattern: ThemeCyclePattern;
  macroTheme: string | null;
  tier: SimilarTier;
  stars: string;
  /** 内部排序分数 —— **不得在 UI 中显示为分数 / 百分比** */
  score: number;
  /** 为什么类似（逐条，直接用于 UI） */
  reasons: string[];
  layers: SimilarLayerNote[];
}

export interface CurrentSimilarityView {
  target: {
    candidate_id: string;
    display_name: string;
    phase: ResearchPhase;
    phaseLabel: string;
    pattern: ThemeCyclePattern;
    drivers: DriverCategory[];
    narrativeTypes: NarrativeType[];
  } | null;
  /** 最多 3 个；无匹配 → 空数组（此时 insufficient = true） */
  results: CurrentSimilarCase[];
  insufficient: boolean;
  note: string;
  /** 被 Temporal Firewall 排除的历史对象数（快照时点尚未结束 / 尚未开始） */
  excludedByFirewall: number;
  /** 第 4 层是否生效（候选侧叙事类型已标注） */
  narrativeLayerActive: boolean;
}

/** 阶段匹配方式（相同 / 相邻） */
export type PhaseMatchKind = 'SAME' | 'ADJACENT';

export const PHASE_MATCH_LABEL: Record<PhaseMatchKind, string> = {
  SAME: '曾经历相同阶段',
  ADJACENT: '曾经历相邻阶段',
};

/**
 * 阶段匹配（**确定性**）：候选当前阶段是否落在历史案例**曾经经过**的阶段集合里。
 * 相同 30 / 相邻 15 / 都没有 → null（不进入结果，不强行凑数）。
 */
function phaseMatchOf(
  campaign: TimelineCampaign,
  targetPhase: ResearchPhase,
): { kind: PhaseMatchKind; phase: ResearchPhase; score: number } | null {
  if (targetPhase === 'UNKNOWN') return null;
  const passed = stagesPassedOf(campaign);
  if (passed.includes(targetPhase)) {
    return { kind: 'SAME', phase: targetPhase, score: SIMILARITY_WEIGHTS.PHASE_SAME };
  }
  const adjacent = PHASE_ADJACENT[targetPhase].filter((p) => passed.includes(p));
  if (adjacent.length > 0) {
    return { kind: 'ADJACENT', phase: adjacent[0], score: SIMILARITY_WEIGHTS.PHASE_ADJACENT };
  }
  return null;
}

/** 该 Campaign lifecycle 中处于指定阶段的那一段（取最早一段；无 → null） */
function stageSegmentOf(
  campaign: TimelineCampaign,
  phase: ResearchPhase,
): { stage: string; start: string; end: string; precision: string } | null {
  for (const s of campaign.lifecycle ?? []) {
    if (phaseOfStage(s.stage) === phase) {
      return { stage: s.stage, start: s.start, end: s.end, precision: s.precision };
    }
  }
  return null;
}

function patternScoreOf(a: ThemeCyclePattern, b: ThemeCyclePattern): number {
  if (a === 'UNKNOWN' || b === 'UNKNOWN') return 0;
  if (a === b) return SIMILARITY_WEIGHTS.PATTERN_SAME;
  if (a === 'HYBRID' || b === 'HYBRID') return SIMILARITY_WEIGHTS.PATTERN_HYBRID;
  return 0;
}

/**
 * 等级只用「有几个强维度成立」判定 —— 与分数高低无关，避免把分数读成概率。
 * ```
 * 4 个强维度全部成立 → 高相似
 * 3 个成立           → 中相似
 * 其余               → 参考案例
 * ```
 */
function tierOf(strong: number): SimilarTier {
  if (strong >= 4) return 'HIGH';
  if (strong === 3) return 'MEDIUM';
  return 'REFERENCE';
}

/**
 * 当前候选 × 历史案例 的相似检索。
 *
 * @param source      历史 TimelineDataSource（只用既有研究数据）
 * @param candidate   当前候选（阶段应来自 `inferCurrentPhase` 的推导结果）
 * @param phase       候选阶段（推导值）
 * @param drivers     候选的 Driver Profile
 */
export function similarPhaseForCandidate(
  source: TimelineDataSource,
  candidate: CurrentCandidate,
  phase: ResearchPhase,
  drivers: DriverCategory[],
): CurrentSimilarityView {
  const snapshot = candidate.snapshot_date;
  const all = allResearchObjects(source);

  // Temporal Firewall：只允许「相对快照已经结束」的历史对象作参照
  const eligible = all.filter((c) => c.end <= snapshot);
  const excludedByFirewall = all.length - eligible.length;

  const cycles = themeCycleViewsOf(source);
  const patternByKey = new Map(cycles.map((c) => [c.key, c.pattern]));
  const patternById = new Map<string, ThemeCyclePattern>();
  for (const c of all) {
    const key = c.theme_cycle_id ?? c.campaign_id;
    patternById.set(c.campaign_id, patternByKey.get(key) ?? 'UNKNOWN');
  }

  const targetPattern = candidatePatternOf(source, candidate);
  const targetNarratives = candidate.narrative_types;
  const narrativeLayerActive = targetNarratives.length > 0;

  const target = {
    candidate_id: candidate.candidate_id,
    display_name: candidate.display_name,
    phase,
    phaseLabel: PHASE_LABEL[phase],
    pattern: targetPattern,
    drivers,
    narrativeTypes: targetNarratives,
  };

  if (eligible.length === 0) {
    return {
      target,
      results: [],
      insufficient: true,
      note:
        '现有历史研究数据在本次快照时点没有可比对的、已完整结束的案例。' +
        '不强行给出相似结果 —— 这是研究数据覆盖不足，不是「没有机会」。',
      excludedByFirewall,
      narrativeLayerActive,
    };
  }

  const scored: CurrentSimilarCase[] = [];
  for (const c of eligible) {
    const match = phaseMatchOf(c, phase);
    if (!match) continue; // 历史案例从未经历该阶段（及其相邻阶段）→ 不进入结果

    const ps = match.score;
    const otherPattern = patternById.get(c.campaign_id) ?? 'UNKNOWN';
    const patS = patternScoreOf(targetPattern, otherPattern);
    const otherDrivers = driverCategoriesOf(c);
    const driverOverlap = otherDrivers.filter((d) => drivers.includes(d));
    const otherNarratives = narrativeTypesOfCampaign(c.campaign_id);
    const narrativeOverlap = narrativeLayerActive
      ? otherNarratives.filter((n) => targetNarratives.includes(n))
      : [];

    const score =
      ps + patS + driverOverlap.length * SIMILARITY_WEIGHTS.DRIVER_EACH + narrativeOverlap.length * SIMILARITY_WEIGHTS.NARRATIVE_EACH;

    const strong =
      (match.kind === 'SAME' ? 1 : 0) +
      (patS === SIMILARITY_WEIGHTS.PATTERN_SAME ? 1 : 0) +
      (driverOverlap.length >= 1 ? 1 : 0) +
      (narrativeOverlap.length >= 1 ? 1 : 0);
    const terminal = terminalPhaseOf(c);

    const layers: SimilarLayerNote[] = [
      {
        id: 'PHASE',
        label: '生命周期阶段',
        matched: true,
        detail:
          match.kind === 'SAME'
            ? `该案例曾经历相同阶段：${PHASE_LABEL[phase]}`
            : `该案例曾经历相邻阶段：${PHASE_LABEL[match.phase]}（候选当前：${PHASE_LABEL[phase]}）`,
      },
      {
        id: 'PATTERN',
        label: 'Theme Cycle Pattern',
        matched: patS > 0,
        detail:
          patS === SIMILARITY_WEIGHTS.PATTERN_SAME
            ? `相同：${PATTERN_LABEL[targetPattern]}`
            : patS > 0
              ? `接近：${PATTERN_LABEL[targetPattern]} ↔ ${PATTERN_LABEL[otherPattern]}`
              : `不同（历史为 ${PATTERN_LABEL[otherPattern]}），不作为依据`,
      },
      {
        id: 'DRIVERS',
        label: 'Driver Profile',
        matched: driverOverlap.length >= 1,
        detail:
          driverOverlap.length > 0
            ? `重叠：${driverOverlap.map((d) => DRIVER_LABEL[d]).join('、')}`
            : '无重叠',
      },
      {
        id: 'NARRATIVE',
        label: 'Narrative Structure',
        matched: narrativeOverlap.length >= 1,
        detail: !narrativeLayerActive
          ? '候选未标注叙事类型 → 本层不参与（不推断）'
          : narrativeOverlap.length > 0
            ? `重叠：${narrativeOverlap.map((n) => NARRATIVE_TYPE_LABEL[n]).join('、')}`
            : otherNarratives.length === 0
              ? '历史案例未标注叙事类型 → 本层不参与'
              : '无重叠',
      },
    ];

    const chain = preObservationChainOf(c);
    const tier = tierOf(strong);
    scored.push({
      campaign_id: c.campaign_id,
      title: c.title,
      year: c.year,
      kind: c.kind,
      start: c.start,
      end: c.end,
      phase: match.phase,
      phaseLabel: PHASE_LABEL[match.phase],
      phaseMatch: match.kind,
      phaseMatchLabel: PHASE_MATCH_LABEL[match.kind],
      matchedStage: stageSegmentOf(c, match.phase),
      drivers: otherDrivers,
      driverNotes: (c.drivers?.start ?? []).slice(0, 3),
      narrativeTypes: otherNarratives,
      narrativeTypesLabel: otherNarratives.map((n) => NARRATIVE_TYPE_LABEL[n]).join('、'),
      terminalPhase: terminal,
      terminalPhaseLabel: PHASE_LABEL[terminal],
      preObservation: chain
        ? {
            formation: chain.formation,
            formationAnchor: chain.formationAnchor,
            start: chain.preObservation.start,
            end: chain.preObservation.end,
            days: chain.preObservation.days,
            earlySignal: chain.earlySignal
              ? { start: chain.earlySignal.start, end: chain.earlySignal.end }
              : null,
          }
        : null,
      pattern: otherPattern,
      macroTheme: macroThemeOf(c),
      tier,
      stars: TIER_STARS[tier],
      score,
      reasons: layers.filter((l) => l.matched).map((l) => l.detail),
      layers,
    });
  }

  scored.sort((a, b) => {
    if (a.score !== b.score) return b.score - a.score;
    if (a.year !== b.year) return b.year - a.year;
    return a.campaign_id < b.campaign_id ? -1 : 1;
  });
  const results = scored.slice(0, 3);

  return {
    target,
    results,
    insufficient: results.length === 0,
    note:
      results.length === 0
        ? `在本次快照时点，历史研究数据中没有与「${PHASE_LABEL[phase]}」相同或相邻阶段的已完整案例。` +
          '不强行给出相似结果 —— 这是研究数据覆盖不足，不是「没有机会」。'
        : '按「阶段 → Pattern → Drivers → Narrative」排序的**研究结构相似度**，' +
          `等级：${results.map((r) => TIER_LABEL[r.tier]).join(' / ')}。相似的是阶段与结构，**不是未来走势**。`,
    excludedByFirewall,
    narrativeLayerActive,
  };
}
