/**
 * currentWatchboard.ts —— 「**当前观察台**」的只读派生层（ThreeC 1.2 · Usage-Driven）。
 *
 * ## ★★ 它回答什么，以及**不回答**什么
 *
 * **回答**：现在有哪几个方向在被研究侧观察 · 各自处在什么阶段 · 观察到什么 · **还缺什么**。
 * 一屏看完，不必逐条点开对照。
 *
 * **不回答**：哪个「可能性更高」、哪个「更可能被炒」、该看哪个。
 *
 * ## ★★★ 为什么不做「可能性排序」（这是设计的前提，不是保守）
 *
 * 1. **红线**：`AGENTS.md` §1 明令禁止概率 / 胜率 / 推荐分 / 预测。
 * 2. **样本极小**：当前对象只有 6 个；任何「可能性」都不可验证。
 * 3. **★ 最要紧的一条**：一旦给出排序，它就会**被当作推荐使用** ——
 *    而项目明令禁止荐股。工具无从阻止这种读法，只能**不生产排序**。
 *
 * ## ★ 因此本层的三条纪律
 *
 * - **按「阶段」分组**（封闭枚举），组内按**阶段起点时间序** —— 不是价值序；
 * - **明写「阶段越早 ≠ 越可能」** —— 阶段是**当前状态的分类**，不是可能性；
 * - **「还缺什么」是核心列** —— 它把「提前观察」落到「下一步看什么」，而不是「买什么」。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import raw from '@current/current_candidates.json';
import { PHASE_LABEL, type ResearchPhase } from './researchAttention';

/** 三态证据的取值（封闭） */
export type EvidenceState = 'EMERGING' | 'PRESENT' | 'STRONG' | 'UNKNOWN';

export const EVIDENCE_STATE_LABEL: Record<EvidenceState, string> = {
  EMERGING: '初现',
  PRESENT: '已现',
  STRONG: '强',
  UNKNOWN: '未标注',
};

/** 三态证据的三个维度（与研究侧字段一一对应） */
export const EVIDENCE_DIMENSIONS: { key: 'breadth' | 'information_marginal' | 'narrative'; label: string }[] = [
  { key: 'breadth', label: '广度' },
  { key: 'information_marginal', label: '信息边际' },
  { key: 'narrative', label: '叙事' },
];

export interface WatchboardItem {
  candidateId: string;
  displayName: string;
  macroTheme: string | null;
  /** 阶段（封闭枚举；未知时为 UNKNOWN） */
  phase: ResearchPhase;
  phaseLabel: string;
  /** 阶段窗口起点（可能为 null —— 合法空状态） */
  phaseStart: string | null;
  /** 距今天数（用快照日算，不用「今天」，避免漂移） */
  daysSincePhaseStart: number | null;
  evidence: Record<'breadth' | 'information_marginal' | 'narrative', EvidenceState>;
  narrativeTypes: string[];
  /** ★ 还缺什么：三态中仍为 初现 / 未标注 的维度名 */
  gaps: string[];
  /** 未决问题数（研究侧的 `uncertainty_notes`） */
  openIssues: number;
  /** 研究问题数（继续研究的入口） */
  researchQuestions: number;
  /** 证据条数（计数事实） */
  evidenceCount: number;
  /** 参照历史案例（研究侧已给出，原样透传） */
  referenceCases: string[];
  /** 快照日（研究侧记录该对象状态的日期） */
  snapshotDate: string | null;
}

export interface WatchboardGroup {
  phase: ResearchPhase;
  phaseLabel: string;
  items: WatchboardItem[];
}

export interface WatchboardView {
  /** 按阶段分组；组序 = 生命周期自然序（不是价值序） */
  groups: WatchboardGroup[];
  total: number;
  /** 快照日（取所有对象里最晚的 `snapshot_date`） */
  asOf: string | null;
  /** 三态维度里「初现 / 未标注」的计数（计数事实） */
  gapCounts: Record<string, number>;
}

/** 生命周期自然序 —— 只用于**分组排序**，不代表可能性高低 */
const PHASE_ORDER: ResearchPhase[] = [
  'EARLY_SIGNAL',
  'THEME_FORMING',
  'BROAD_CONFIRMATION',
  'EXPANSION',
  'PEAK',
  'DECLINE',
  'END',
  'UNKNOWN',
];

const STATE_SET: readonly string[] = ['EMERGING', 'PRESENT', 'STRONG', 'UNKNOWN'];

function toState(v: unknown): EvidenceState {
  return typeof v === 'string' && STATE_SET.includes(v) ? (v as EvidenceState) : 'UNKNOWN';
}

function toPhase(v: unknown): ResearchPhase {
  return typeof v === 'string' && v in PHASE_LABEL ? (v as ResearchPhase) : 'UNKNOWN';
}

function daysBetween(a: string, b: string): number | null {
  const t1 = Date.parse(a);
  const t2 = Date.parse(b);
  if (Number.isNaN(t1) || Number.isNaN(t2)) return null;
  return Math.round((t2 - t1) / 86400000);
}

interface RawCandidate {
  candidate_id?: string;
  display_name?: string;
  macro_theme?: string | null;
  attention_state?: string;
  phase_window?: { start?: string | null; end?: string | null } | null;
  phase_evidence?: Record<string, unknown> | null;
  narrative_types?: string[];
  uncertainty_notes?: string[];
  research_questions?: string[];
  evidence?: unknown[];
  reference_cases?: { campaign_id?: string }[];
  snapshot_date?: string | null;
}

/**
 * 构造观察台视图。
 *
 * @param dataset 可注入（测试用）；缺省读 canonical `current_candidates.json`
 */
export function buildWatchboard(dataset?: { candidates?: RawCandidate[] }): WatchboardView {
  const candidates = (dataset?.candidates ?? (raw as { candidates?: RawCandidate[] }).candidates ?? []);

  const items: WatchboardItem[] = candidates.map((c) => {
    const pe = c.phase_evidence ?? {};
    const ev = {
      breadth: toState(pe.breadth),
      information_marginal: toState(pe.information_marginal),
      narrative: toState(pe.narrative),
    };
    const phase = toPhase(c.attention_state);
    const start = c.phase_window?.start ?? null;
    const snap = c.snapshot_date ?? null;
    return {
      candidateId: c.candidate_id ?? '（无 id）',
      displayName: c.display_name ?? c.candidate_id ?? '（无名称）',
      macroTheme: c.macro_theme ?? null,
      phase,
      phaseLabel: PHASE_LABEL[phase],
      phaseStart: start,
      daysSincePhaseStart: start && snap ? daysBetween(start, snap) : null,
      evidence: ev,
      narrativeTypes: c.narrative_types ?? [],
      // ★ 还缺什么：三态中仍为「初现 / 未标注」的维度 —— 这是「下一步看什么」
      gaps: EVIDENCE_DIMENSIONS.filter((d) => ev[d.key] === 'EMERGING' || ev[d.key] === 'UNKNOWN').map((d) => d.label),
      openIssues: (c.uncertainty_notes ?? []).length,
      researchQuestions: (c.research_questions ?? []).length,
      evidenceCount: (c.evidence ?? []).length,
      referenceCases: (c.reference_cases ?? []).map((r) => r.campaign_id ?? '').filter(Boolean),
      snapshotDate: snap,
    };
  });

  // 按阶段分组；组序 = 生命周期自然序（★ 不是价值序）
  const groups: WatchboardGroup[] = [];
  for (const p of PHASE_ORDER) {
    const g = items.filter((x) => x.phase === p);
    if (!g.length) continue;
    // 组内按**阶段起点时间序**（早的在前）；起点缺失的排在最后，不猜测
    g.sort((a, b) => {
      if (!a.phaseStart && !b.phaseStart) return a.candidateId < b.candidateId ? -1 : 1;
      if (!a.phaseStart) return 1;
      if (!b.phaseStart) return -1;
      return a.phaseStart < b.phaseStart ? -1 : 1;
    });
    groups.push({ phase: p, phaseLabel: PHASE_LABEL[p], items: g });
  }

  const gapCounts: Record<string, number> = {};
  for (const d of EVIDENCE_DIMENSIONS) {
    gapCounts[d.label] = items.filter((x) => x.evidence[d.key] === 'EMERGING' || x.evidence[d.key] === 'UNKNOWN').length;
  }

  const asOf = items.map((x) => x.snapshotDate).filter((x): x is string => !!x).sort().pop() ?? null;

  return { groups, total: items.length, asOf, gapCounts };
}

/** ★ 必须与观察台一同展示的语义边界（防止被读成「可能性排序」） */
export const WATCHBOARD_DISCLAIMER =
  '本表是研究侧**观察状态的陈列**：现在有哪几个方向在被观察、各自处在什么阶段、观察到什么、还缺什么。' +
  '阶段越早**不等于**越可能启动 —— 阶段是当前状态的分类，不是可能性；' +
  '本表按阶段分组（组内按阶段起点时间序），**不评分、不排名**，**非预测**。';
