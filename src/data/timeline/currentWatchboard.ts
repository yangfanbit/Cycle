/**
 * currentWatchboard.ts —— 「**当前观察台**」的只读派生层（ThreeC 1.2 · Usage-Driven）。
 *
 * ## ★★★ 数据来源（**必须**走这条链路，不得绕过）
 *
 * ```
 * research/current/current_candidates.json          （研究侧声明：attention_state / phase_evidence / …）
 *        ↓  parseCurrentCandidateDataset
 *        ↓  buildCurrentCandidateViews  →  currentPhaseInference（**产品端规则引擎，可审计**）
 * 本模块（只做分组与陈列，**不重新推导任何阶段**）
 * ```
 *
 * ★★ **为什么不能直接读 `attention_state`**（本模块 v0_1 的错误）：
 * `current_candidates.json` 的元信息写明 ——
 * **「阶段由产品端 Phase Evidence Matrix 独立推导，不由研究声明决定」**；
 * 引擎 `PhaseInference` 也写明「推导阶段是**权威值**，研究声明值并列保留在 `declared`」，
 * 且「**不一致时 UI 必须并列显示，不得静默取一**」。
 *
 * 实测（2026-10-08）：6 个当前对象中 **2 个不一致** ——
 * `CC-2026-BCI-MEDTECH` 与 `CC-2026-AUTO-SMARTDRIVE` 的**推导值为 `UNKNOWN`**（证据组合不满足任何阶段规则），
 * 而研究声明为 `THEME_FORMING`。v0_1 把两者都显示成「主题形成」—— **静默取了声明值**。
 *
 * ## ★★ 它回答什么，以及**不回答**什么
 *
 * **回答**：现在有哪几个方向在被观察 · 各自**推导**处于什么阶段 · 观察到什么 · **还缺哪些维度**。
 * **不回答**：哪个「可能性更高」、该看哪个 —— 见下。
 *
 * ## ★★★ 为什么不做「可能性排序」
 *
 * 1. **红线**：`AGENTS.md` §1 禁止概率 / 胜率 / 推荐分 / 预测。
 * 2. **样本极小**：当前对象只有 6 个，任何「可能性」都不可验证。
 * 3. ★ **最要紧**：**一旦给出排序，它就会被当作推荐使用**（= 荐股）；
 *    工具无从阻止这种读法，**只能不生产排序**。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

import canonicalJson from '@current/current_candidates.json';
import { previewTimelineSource } from './timelineAdapter';
import { parseCurrentCandidateDataset, DIMENSION_LABEL, type PhaseDimension } from './currentCandidate';
import { buildCurrentCandidateViews } from './currentCandidateAdapter';
import { PHASE_LABEL, type ResearchPhase } from './researchAttention';
import type { TimelineDataSource } from './timelineTypes';

export interface WatchboardItem {
  candidateId: string;
  displayName: string;
  macroTheme: string | null;
  /** ★ **推导阶段**（权威值，来自产品端规则引擎） */
  phase: ResearchPhase;
  phaseLabel: string;
  /** 研究侧声明的阶段（**并列保留**，不覆盖推导值） */
  declaredPhase: ResearchPhase;
  declaredPhaseLabel: string;
  /** ★ 推导值与声明值是否一致；不一致时 UI **必须**并列显示 */
  agreesWithDeclared: boolean;
  /** 命中的规则 id 与说明（可审计 —— 任何阶段结论都能被追问「为什么」） */
  matchedRule: string;
  ruleLabel: string;
  /** 逐条理由（原样透传引擎输出） */
  reasons: string[];
  /** 维度覆盖度（计数事实） */
  coverage: { level: string; label: string; known: number; total: number };
  /** ★ 还缺什么：尚未达到「明确」水平的维度（**引擎给的**，不是本模块自算） */
  missingDimensions: string[];
  /** 一句话解释（研究叙事，原样透传） */
  oneLiner: string;
  /** 阶段窗口起点（研究侧声明；合法可为 null） */
  phaseStart: string | null;
  /** 距记录日天数（用快照日算，不用「今天」，避免漂移） */
  daysSincePhaseStart: number | null;
  snapshotDate: string | null;
  /** 是否具备进入研究的最低条件（至少 1 条快照内可用证据） */
  researchReady: boolean;
  /** 是否可直接作为相似度参照（阶段已推导出） */
  similarityReady: boolean;
  researchQuestions: number;
}

export interface WatchboardGroup {
  phase: ResearchPhase;
  phaseLabel: string;
  items: WatchboardItem[];
}

export interface WatchboardView {
  /** 按**推导阶段**分组；组序 = 生命周期自然序（不是价值序） */
  groups: WatchboardGroup[];
  total: number;
  /** ★ 推导值与研究声明**不一致**的对象数（计数事实，必须显示） */
  disagreementCount: number;
  asOf: string | null;
  /** 各维度「尚未明确」的对象数（计数事实，不是评分） */
  gapCounts: { dimension: string; count: number }[];
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

function daysBetween(a: string, b: string): number | null {
  const t1 = Date.parse(a);
  const t2 = Date.parse(b);
  if (Number.isNaN(t1) || Number.isNaN(t2)) return null;
  return Math.round((t2 - t1) / 86400000);
}

/**
 * 构造观察台视图。
 *
 * @param opts 可注入（测试用）；缺省消费 canonical 数据集与 canonical export
 */
export function buildWatchboard(opts?: {
  dataset?: unknown;
  source?: TimelineDataSource;
  today?: string;
}): WatchboardView {
  const raw = opts?.dataset ?? canonicalJson;
  const dataset = parseCurrentCandidateDataset(raw).dataset;
  const source = opts?.source ?? previewTimelineSource();
  const today =
    opts?.today ??
    (dataset as { snapshot_date?: string }).snapshot_date ??
    new Date().toISOString().slice(0, 10);

  const views = buildCurrentCandidateViews(source, dataset, today).views;

  const items: WatchboardItem[] = views.map((v) => {
    const c = v.candidate as unknown as {
      candidate_id?: string;
      display_name?: string;
      macro_theme?: string | null;
      phase_window?: { start?: string | null } | null;
      research_questions?: string[];
      snapshot_date?: string | null;
    };
    const start = c.phase_window?.start ?? null;
    const snap = c.snapshot_date ?? null;
    return {
      candidateId: c.candidate_id ?? '（无 id）',
      displayName: c.display_name ?? c.candidate_id ?? '（无名称）',
      macroTheme: c.macro_theme ?? null,
      phase: v.phase as ResearchPhase,
      phaseLabel: v.phaseLabel,
      declaredPhase: v.inference.declared as ResearchPhase,
      declaredPhaseLabel: PHASE_LABEL[v.inference.declared as ResearchPhase] ?? v.inference.declared,
      agreesWithDeclared: v.inference.agreesWithDeclared,
      matchedRule: v.inference.matchedRule,
      ruleLabel: v.inference.ruleLabel,
      reasons: v.inference.reasons,
      coverage: { level: v.coverage.level, label: v.coverage.label, known: v.coverage.known, total: v.coverage.total },
      // ★ 引擎已算好「尚未明确的维度」——本模块**不自行推导**
      missingDimensions: (v.missingDimensions as PhaseDimension[]).map((d) => DIMENSION_LABEL[d] ?? d),
      oneLiner: v.oneLiner,
      phaseStart: start,
      daysSincePhaseStart: start && snap ? daysBetween(start, snap) : null,
      snapshotDate: snap,
      researchReady: v.researchReady,
      similarityReady: v.similarityReady,
      researchQuestions: (c.research_questions ?? []).length,
    };
  });

  // 按**推导阶段**分组；组序 = 生命周期自然序（★ 不是价值序）
  const groups: WatchboardGroup[] = [];
  for (const p of PHASE_ORDER) {
    const g = items.filter((x) => x.phase === p);
    if (!g.length) continue;
    // 组内按**阶段起点时间序**（早的在前）；起点缺失者排最后，不猜测
    g.sort((a, b) => {
      if (!a.phaseStart && !b.phaseStart) return a.candidateId < b.candidateId ? -1 : 1;
      if (!a.phaseStart) return 1;
      if (!b.phaseStart) return -1;
      return a.phaseStart < b.phaseStart ? -1 : 1;
    });
    groups.push({ phase: p, phaseLabel: PHASE_LABEL[p], items: g });
  }

  const dims = Object.keys(DIMENSION_LABEL) as PhaseDimension[];
  const gapCounts = dims
    .map((d) => ({
      dimension: DIMENSION_LABEL[d],
      count: items.filter((x) => x.missingDimensions.includes(DIMENSION_LABEL[d])).length,
    }))
    .filter((x) => x.count > 0);

  const asOf =
    items.map((x) => x.snapshotDate).filter((x): x is string => !!x).sort().pop() ?? null;

  return {
    groups,
    total: items.length,
    disagreementCount: items.filter((x) => !x.agreesWithDeclared).length,
    asOf,
    gapCounts,
  };
}

/** ★ 必须与观察台一同展示的语义边界（防止被读成「可能性排序」） */
export const WATCHBOARD_DISCLAIMER =
  '本表是研究侧**观察状态的陈列**：现在有哪几个方向在被观察、各自**推导**处于什么阶段、观察到什么、还缺哪些维度。' +
  '阶段由产品端规则引擎由证据矩阵**推导**（可审计：每个阶段都能追问命中了哪条规则），' +
  '与研究侧声明不一致时**两者并列**、不静默取一。' +
  '阶段越早**不等于**越可能启动 —— 阶段是当前状态的分类，不是可能性；' +
  '本表按阶段分组（组内按阶段起点时间序），**不评分、不排名**，**非预测**。';
