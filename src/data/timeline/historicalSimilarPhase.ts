/**
 * Historical Similar Phase v1 —— 「生命周期相似」检索（Lifecycle Lens）。
 *
 * ## 与 Historical Same Period 的区别（两者并存，不互相替代）
 * ```
 * Historical Same Period  = Calendar Lens  —— 去年的这个月，历史上发生过什么？
 * Historical Similar Phase = Lifecycle Lens —— 历史上处于**类似生命周期位置**的机会有哪些？
 * ```
 *
 * ## 输入（全部来自既有 Research 数据）
 * 研究对象（Theme / Campaign / Candidate）的：阶段 · Theme Cycle Pattern · Drivers · 证据状态。
 *
 * ## v1 只用三大维度（不做 NLP、不做机器学习、不做预测）
 * 1. **Phase**（最高优先级）：终态阶段相同 > 相邻
 * 2. **Theme Cycle Pattern**：Sequential / Parallel / Hybrid
 * 3. **Drivers**：分类标签重叠（Policy / Industry / Capital / Sentiment / External）
 *
 * ## 输出约束
 * - 最多 **Top 3**；不显示百分比；相似度用「高相似 / 中相似 / 参考」。
 * - 必须给出「为什么类似」。
 * - 找不到足够证据 → **不强行凑数**，输出空态。
 * - UI 必须声明：这是**研究结构相似度**，不是未来走势概率。
 *
 * ## 边界
 * **纯 View / Research Navigation 层**：不写入 DB / schema / export / contracts，
 * 不改变任何 Research 事实；不联网、不取实时数据；不使用未来数据（NO LOOK-AHEAD）。
 */

import type { TimelineDataSource } from './timelineTypes';
import {
  allResearchObjects,
  driverCategoriesOf,
  macroThemeOf,
  patternOf,
  terminalPhaseOf,
  themeCycleViewsOf,
  type DriverCategory,
  type ResearchPhase,
  type ThemeCyclePattern,
  PHASE_ADJACENT,
  PHASE_LABEL,
  PATTERN_LABEL,
  DRIVER_LABEL,
} from './researchAttention';

/** 相似度等级（**不是概率**） */
export type SimilarTier = 'HIGH' | 'MEDIUM' | 'REFERENCE';

export const TIER_LABEL: Record<SimilarTier, string> = {
  HIGH: '高相似',
  MEDIUM: '中相似',
  REFERENCE: '参考',
};

/** 星标表达（等级的可视化；仍然不是概率） */
export const TIER_STARS: Record<SimilarTier, string> = {
  HIGH: '★★★',
  MEDIUM: '★★☆',
  REFERENCE: '★☆☆',
};

export interface SimilarPhaseResult {
  campaign_id: string;
  title: string;
  year: number;
  /** 起止（历史区间，原样透传） */
  start: string;
  end: string;
  kind: 'campaign' | 'candidate';
  phase: ResearchPhase;
  phaseLabel: string;
  pattern: ThemeCyclePattern;
  themeCycleId: string | null;
  macroTheme: string | null;
  drivers: DriverCategory[];
  tier: SimilarTier;
  /** 为什么类似（逐条，直接用于 UI 展示） */
  reasons: string[];
  score: number;
}

export interface SimilarPhaseView {
  /** 参照对象（比较基线）；无数据源 → null */
  target: {
    campaign_id: string;
    title: string;
    year: number;
    phase: ResearchPhase;
    phaseLabel: string;
    pattern: ThemeCyclePattern;
    drivers: DriverCategory[];
  } | null;
  /** 最多 3 个；无匹配 → 空数组（此时 insufficient = true） */
  results: SimilarPhaseResult[];
  insufficient: boolean;
  note: string;
}

/** Phase 分值：相同 3 / 相邻 2 / 无 0（低于 2 不进入结果 —— 不强行凑数） */
function phaseScoreOf(target: ResearchPhase, other: ResearchPhase): number {
  if (target === 'UNKNOWN' || other === 'UNKNOWN') return 0;
  if (target === other) return 3;
  return PHASE_ADJACENT[target].includes(other) ? 2 : 0;
}

/** Pattern 分值：相同 2 / Hybrid 与任一 1 / 其他 0（任一侧未判定 → 0，不猜测） */
function patternScoreOf(a: ThemeCyclePattern, b: ThemeCyclePattern): number {
  if (a === 'UNKNOWN' || b === 'UNKNOWN') return 0;
  if (a === b) return 2;
  if (a === 'HYBRID' || b === 'HYBRID') return 1;
  return 0;
}

function tierOf(phaseScore: number, patternScore: number, driverOverlap: number): SimilarTier {
  const strong = (phaseScore === 3 ? 1 : 0) + (patternScore === 2 ? 1 : 0) + (driverOverlap >= 1 ? 1 : 0);
  if (strong >= 3) return 'HIGH';
  if (strong === 2) return 'MEDIUM';
  return 'REFERENCE';
}

function reasonLines(
  targetPhase: ResearchPhase,
  otherPhase: ResearchPhase,
  phaseScore: number,
  targetPattern: ThemeCyclePattern,
  otherPattern: ThemeCyclePattern,
  patternScore: number,
  overlap: DriverCategory[],
): string[] {
  const out: string[] = [];
  out.push(
    phaseScore === 3
      ? `阶段相同：${PHASE_LABEL[targetPhase]}`
      : `阶段相邻：${PHASE_LABEL[targetPhase]} → ${PHASE_LABEL[otherPhase]}`,
  );
  if (patternScore === 2) {
    out.push(`Theme Cycle Pattern 相同：${PATTERN_LABEL[targetPattern]}`);
  } else if (patternScore === 1) {
    out.push(`Pattern 接近：${PATTERN_LABEL[targetPattern]} ↔ ${PATTERN_LABEL[otherPattern]}`);
  } else {
    out.push(`Pattern 不同（${PATTERN_LABEL[otherPattern]}），不作为主要依据`);
  }
  out.push(
    overlap.length > 0
      ? `Drivers 有重叠：${overlap.map((d) => DRIVER_LABEL[d]).join('、')}`
      : 'Drivers 无重叠',
  );
  return out;
}

/**
 * 生命周期相似检索。
 *
 * @param source         TimelineDataSource（只用既有研究数据）
 * @param targetId       参照研究对象 campaign_id；null → 取研究数据中**最新**的一条作为参照
 *                       （UI 必须显式标注该参照是"研究数据覆盖内最新案例"，不得表述为当前市场状态）
 */
export function similarPhaseOf(
  source: TimelineDataSource,
  targetId: string | null,
): SimilarPhaseView {
  const objects = allResearchObjects(source);
  const cycles = themeCycleViewsOf(source);
  const cycleByKey = new Map(cycles.map((c) => [c.key, c]));

  const patternById = new Map<string, ThemeCyclePattern>();
  for (const c of objects) {
    const key = c.theme_cycle_id ?? c.campaign_id;
    const view = cycleByKey.get(key);
    patternById.set(c.campaign_id, view ? view.pattern : 'UNKNOWN');
  }

  const emptyNote =
    '当前研究数据不足，未形成可靠的历史参照。可先在 Timeline 或历史同期中选择一个研究对象作为参照。';

  if (objects.length === 0) {
    return { target: null, results: [], insufficient: true, note: emptyNote };
  }

  const targetObj = targetId
    ? objects.find((c) => c.campaign_id === targetId)
    : objects[objects.length - 1]; // allResearchObjects 已按 start 升序 → 末位即最新
  if (!targetObj) {
    return { target: null, results: [], insufficient: true, note: emptyNote };
  }

  const targetPhase = terminalPhaseOf(targetObj);
  const targetPattern = patternById.get(targetObj.campaign_id) ?? 'UNKNOWN';
  const targetDrivers = driverCategoriesOf(targetObj);

  const scored: SimilarPhaseResult[] = [];
  for (const c of objects) {
    if (c.campaign_id === targetObj.campaign_id) continue;
    const phase = terminalPhaseOf(c);
    const ps = phaseScoreOf(targetPhase, phase);
    if (ps < 2) continue; // 阶段既不相同也不相邻 → 不作为相似结果（不强行凑数）
    const pattern = patternById.get(c.campaign_id) ?? 'UNKNOWN';
    const patS = patternScoreOf(targetPattern, pattern);
    const drivers = driverCategoriesOf(c);
    const overlap = drivers.filter((d) => targetDrivers.includes(d));
    const score = ps * 10 + patS * 4 + overlap.length;
    scored.push({
      campaign_id: c.campaign_id,
      title: c.title,
      year: c.year,
      start: c.start,
      end: c.end,
      kind: c.kind,
      phase,
      phaseLabel: PHASE_LABEL[phase],
      pattern,
      themeCycleId: c.theme_cycle_id ?? null,
      macroTheme: macroThemeOf(c),
      drivers,
      tier: tierOf(ps, patS, overlap.length),
      reasons: reasonLines(targetPhase, phase, ps, targetPattern, pattern, patS, overlap),
      score,
    });
  }

  scored.sort((a, b) => {
    if (a.score !== b.score) return b.score - a.score;
    if (a.year !== b.year) return b.year - a.year;
    return a.campaign_id < b.campaign_id ? -1 : 1;
  });

  const results = scored.slice(0, 3); // 最多 Top 3

  return {
    target: {
      campaign_id: targetObj.campaign_id,
      title: targetObj.title,
      year: targetObj.year,
      phase: targetPhase,
      phaseLabel: PHASE_LABEL[targetPhase],
      pattern: targetPattern,
      drivers: targetDrivers,
    },
    results,
    insufficient: results.length === 0,
    note:
      results.length === 0
        ? `在现有研究数据中没有与「${PHASE_LABEL[targetPhase]}」相同或相邻阶段的其他案例。` +
          '不强行给出相似结果 —— 这是研究数据覆盖不足，不是「没有机会」。'
        : '按「阶段 → Theme Cycle Pattern → Drivers 重叠」排序的研究结构相似度，不是未来走势概率。',
  };
}

/** 相似阶段检索的默认参照（研究数据覆盖内最新的一条；UI 需显式标注） */
export function defaultSimilarTargetId(source: TimelineDataSource): string | null {
  const objects = allResearchObjects(source);
  return objects.length > 0 ? objects[objects.length - 1].campaign_id : null;
}
