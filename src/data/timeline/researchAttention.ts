/**
 * Research Navigation ViewModel（V2.0）—— Current Time Lens v2 的数据层。
 *
 * ## 定位
 * 回答（且仅此三问）：
 *   A. A股整体环境 —— 现在处于什么位置？
 *   B. 当前 Theme / Theme Cycle —— 当前主题周期是什么状态？
 *   C. Research Attention —— 研究数据覆盖内，哪些方向值得继续研究 / 保持观察 / 仅作历史参考？
 *
 * ## 严格边界（不得越界）
 * - **纯 View / Research Navigation 层**：不写入 DB / schema / export / contracts，
 *   不改变任何 Research 事实。
 * - **只消费 TimelineDataSource**（`exports/timeline_export_v1.json` 或 `data/verified`）：
 *   不联网、不取实时行情 / 资金 / 情绪 / 新闻。
 * - **NO LOOK-AHEAD**：不使用当前日期之后的未来数据；也不把历史年份的数据
 *   伪装成「当前状态」（见 `buildCurrentLensV2` 的 Layer B 诚实空态）。
 * - **不是评分、不是概率、不是买卖信号**：Attention 是状态分类，不是数值打分。
 *
 * ## Parallel-aware
 * 一个 Macro Theme / Theme Cycle 可含多个 Campaign/Candidate，各自处于**不同**阶段
 * （医药：中药 Expansion ‖ 创新药 Decline ‖ 疫情医疗 End）。因此 Theme 状态**不压缩成唯一 phase**，
 * 而由多个 component 计算（见 `themeCycleViewsOf`）。
 */

import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import { diffDays } from '../../utils';

/* ================= 1. 阶段（canonical Research Phase） ================= */

/**
 * 研究阶段（统一 7 值）—— 把导出的 `lifecycle[].stage` 归一到可比对的集合。
 * 映射规则（确定性、可审计）：
 *   EARLY_SIGNAL / THEME_FORMING / BROAD_CONFIRMATION → 同名
 *   MAIN_RISE                                          → EXPANSION
 *   PEAK                                               → PEAK
 *   SECONDARY / FIRST_DECLINE / RETRACEMENT / DECLINING → DECLINE
 *   MAIN_END / ENDED                                   → END
 *
 * ★ 覆盖度不变量：本表必须覆盖 `contracts/timeline_export_v1.md` 的 **全部 11 个**
 *   `VALID_LIFECYCLE_STAGE`。漏映射不会报错，但会让 `phaseOfStage()` **静默退化为 UNKNOWN**
 *   —— 研究明明记录了大写阶段，Product 却显示「阶段未标注」（`UNKNOWN ≠ 未映射`）。
 *   实测漏项：`ENDED`（Contract 成员，当前 export 中出现 2 次）曾缺映射。
 *   由 `releaseGateScenarios.test.tsx` Scenario F 的覆盖度断言机械兜底。
 */
export type ResearchPhase =
  | 'EARLY_SIGNAL'
  | 'THEME_FORMING'
  | 'BROAD_CONFIRMATION'
  | 'EXPANSION'
  | 'PEAK'
  | 'DECLINE'
  | 'END'
  | 'UNKNOWN';

const STAGE_TO_PHASE: Record<string, ResearchPhase> = {
  EARLY_SIGNAL: 'EARLY_SIGNAL',
  THEME_FORMING: 'THEME_FORMING',
  BROAD_CONFIRMATION: 'BROAD_CONFIRMATION',
  MAIN_RISE: 'EXPANSION',
  PEAK: 'PEAK',
  SECONDARY: 'DECLINE',
  FIRST_DECLINE: 'DECLINE',
  RETRACEMENT: 'DECLINE',
  DECLINING: 'DECLINE',
  MAIN_END: 'END',
  ENDED: 'END',
};

/**
 * Contract `VALID_LIFECYCLE_STAGE` 全量（11 项）—— **导出即可见**，供不变量测试机械比对。
 * 任何新增 Contract 阶段都必须同步进 `STAGE_TO_PHASE`，否则覆盖度断言会失败。
 */
export const CONTRACT_LIFECYCLE_STAGES = [
  'EARLY_SIGNAL',
  'THEME_FORMING',
  'BROAD_CONFIRMATION',
  'MAIN_RISE',
  'PEAK',
  'RETRACEMENT',
  'DECLINING',
  'SECONDARY',
  'FIRST_DECLINE',
  'MAIN_END',
  'ENDED',
] as const;

/** 供不变量测试使用的只读映射快照（不得用于业务写入）。 */
export const STAGE_TO_PHASE_SNAPSHOT: Readonly<Record<string, ResearchPhase>> = STAGE_TO_PHASE;

export const PHASE_LABEL: Record<ResearchPhase, string> = {
  EARLY_SIGNAL: '早期信号',
  THEME_FORMING: '主题形成',
  BROAD_CONFIRMATION: '广泛确认',
  EXPANSION: '扩张（主升）',
  PEAK: '峰值',
  DECLINE: '退潮',
  END: '主段结束',
  UNKNOWN: '阶段未标注',
};

export function phaseOfStage(stage: string): ResearchPhase {
  return STAGE_TO_PHASE[stage] ?? 'UNKNOWN';
}

/**
 * 该研究对象**当前所处的阶段**。
 *
 * 规则（确定性）：
 *   1. lifecycle 中存在 `MAIN_END` → `END`（主段结束是**终结标记**：
 *      其后的 SECONDARY 次级行情不改变"该 Campaign 已结束"这一事实）。
 *   2. 否则取 lifecycle 中 start 最晚的阶段。
 *   3. **无 Research lifecycle → `UNKNOWN`**（不编造）。
 *
 * ★ Gate T8（`UNKNOWN ≠ 自动推导具体阶段`）：
 *   **不得**回退到视图分段 `campaign.phases`。`phases` 是 `timelineAdapter.derivePhases()`
 *   由 `start/end` 派生的 **Timeline 视觉分段**（`peak == null` 时无条件产出 `main_rise`），
 *   不是 Research 结论。用它当 Research phase fallback = 在研究明确「阶段不可识别」的对象上
 *   Product 自行推导出一个具体阶段（误导性显示，见 `docs/THREEC_1_0_RELEASE_DEFINITION.md` P0-1）。
 *   视图分段仍归 Timeline 视觉使用，与本函数**职责分离**。
 */
export function terminalPhaseOf(campaign: TimelineCampaign): ResearchPhase {
  const stages = (campaign.lifecycle ?? [])
    .filter((s) => typeof s.start === 'string' && s.start.length > 0)
    .map((s) => ({ ...s, start: s.start as string }))
    .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
  if (stages.length === 0) return 'UNKNOWN';
  if (stages.some((s) => s.stage === 'MAIN_END')) return 'END';
  return phaseOfStage(stages[stages.length - 1].stage);
}

/** lifecycle 中**曾出现**的全部阶段（去重，按生命周期顺序） */
export function stagesPassedOf(campaign: TimelineCampaign): ResearchPhase[] {
  const out: ResearchPhase[] = [];
  for (const s of campaign.lifecycle ?? []) {
    const p = phaseOfStage(s.stage);
    if (p !== 'UNKNOWN' && !out.includes(p)) out.push(p);
  }
  return out;
}

/** 阶段相邻表（用于「相似阶段」的次优先级匹配） */
export const PHASE_ADJACENT: Record<ResearchPhase, ResearchPhase[]> = {
  EARLY_SIGNAL: ['THEME_FORMING'],
  THEME_FORMING: ['EARLY_SIGNAL', 'BROAD_CONFIRMATION'],
  BROAD_CONFIRMATION: ['THEME_FORMING', 'EXPANSION'],
  EXPANSION: ['BROAD_CONFIRMATION', 'PEAK'],
  PEAK: ['EXPANSION', 'DECLINE'],
  DECLINE: ['PEAK', 'END'],
  END: ['DECLINE'],
  UNKNOWN: [],
};

/* ================= 2. Drivers（分类标签重叠，规则化派生） ================= */

/**
 * 驱动因素分类（methodology v1.1 的 5 类）。
 *
 * ⚠ 来源说明（避免"伪分类"）：导出**没有** Policy/Industry/... 的显式标签，
 * 但有 Research 已记录的 `events[].event_type`（`policy` / `company` / `market` / `macro`）。
 * 本层只做**确定性的 1:1 派生**，不做自然语言推断：
 *   policy  → POLICY     （政策 / 监管 / 医保）
 *   company → INDUSTRY   （产业变化：公司事件、产能、产品、合作）
 *   market  → CAPITAL    （市场/资金：市值、指数、板块）
 *   macro   → EXTERNAL   （宏观 / 外部）
 * `SENTIMENT` 在当前 Research 数据中**没有对应字段来源** → 永不产生（不编造）。
 */
export type DriverCategory = 'POLICY' | 'INDUSTRY' | 'CAPITAL' | 'SENTIMENT' | 'EXTERNAL';

const EVENT_TYPE_TO_DRIVER: Record<string, DriverCategory> = {
  policy: 'POLICY',
  company: 'INDUSTRY',
  market: 'CAPITAL',
  macro: 'EXTERNAL',
};

export const DRIVER_LABEL: Record<DriverCategory, string> = {
  POLICY: 'Policy 政策',
  INDUSTRY: 'Industry 产业',
  CAPITAL: 'Capital 资金',
  SENTIMENT: 'Sentiment 情绪',
  EXTERNAL: 'External 外部',
};

const DRIVER_ORDER: DriverCategory[] = ['POLICY', 'INDUSTRY', 'CAPITAL', 'SENTIMENT', 'EXTERNAL'];

/** 该研究对象的 Drivers 分类集合（来自 Research 已记录事件的 event_type；缺 → 空集） */
export function driverCategoriesOf(campaign: TimelineCampaign): DriverCategory[] {
  const set = new Set<DriverCategory>();
  for (const ev of campaign.events ?? []) {
    const cat = EVENT_TYPE_TO_DRIVER[ev.event_type];
    if (cat) set.add(cat);
  }
  return DRIVER_ORDER.filter((c) => set.has(c));
}

/* ================= 3. Theme Cycle（Parallel-aware 归组 + Pattern） ================= */

export type ThemeCyclePattern = 'SEQUENTIAL' | 'PARALLEL' | 'HYBRID' | 'UNKNOWN';

export const PATTERN_LABEL: Record<ThemeCyclePattern, string> = {
  SEQUENTIAL: 'Sequential 顺序推进',
  PARALLEL: 'Parallel 并行展开',
  HYBRID: 'Hybrid 混合',
  UNKNOWN: '未判定',
};

export type AttentionState = 'ACTIVE_RESEARCH' | 'WATCH' | 'HISTORICAL_REFERENCE';

export const ATTENTION_LABEL: Record<AttentionState, string> = {
  ACTIVE_RESEARCH: '当前值得研究',
  WATCH: '保持观察',
  HISTORICAL_REFERENCE: '历史参考',
};

export interface AttentionResult {
  state: AttentionState;
  /** 人类可读理由（逐条说明为何是该状态） */
  reasons: string[];
}

export interface ThemeCycleComponent {
  campaign: TimelineCampaign;
  phase: ResearchPhase;
  attention: AttentionResult;
  drivers: DriverCategory[];
}

export interface ThemeCycleView {
  /** 归组键 = theme_cycle_id；研究未标注时退化为单条 campaign_id（不编造 cycle） */
  key: string;
  themeCycleId: string | null;
  /** Macro Theme 名称（该 cycle 内出现的 industry/sector 且 role=related 的题材） */
  macroTheme: string | null;
  pattern: ThemeCyclePattern;
  components: ThemeCycleComponent[];
  /** 该 cycle 内最高关注度（ACTIVE > WATCH > HISTORICAL_REFERENCE） */
  summaryAttention: AttentionState;
  /** 组件数（含 Campaign 与 Research Candidate） */
  coverage: { start: string; end: string };
}

const ATTENTION_RANK: Record<AttentionState, number> = {
  ACTIVE_RESEARCH: 0,
  WATCH: 1,
  HISTORICAL_REFERENCE: 2,
};

/** 参与「值得继续研究」判定的阶段（methodology：形成 / 确认 / 扩张） */
const ACTIVE_PHASES: ResearchPhase[] = [
  'EARLY_SIGNAL',
  'THEME_FORMING',
  'BROAD_CONFIRMATION',
  'EXPANSION',
];
/** 只作为历史参考的阶段（峰值 / 退潮 / 结束） */
const REFERENCE_PHASES: ResearchPhase[] = ['PEAK', 'DECLINE', 'END'];

/** 重大冲突（> 10 天，与 conflictSeverity 同阈值；minor 不升级） */
export function hasMajorConflict(campaign: TimelineCampaign): boolean {
  if (campaign.status !== 'conflict') return false;
  return (campaign.conflicts ?? []).some(
    (x) => Math.abs(diffDays(x.candidate_a.date, x.candidate_b.date)) > 10,
  );
}

/** 研究证据是否充分（导出无 evidences 表 → 以 Research 已记录事件 / 信号为代理） */
export function hasEvidence(campaign: TimelineCampaign): boolean {
  return (campaign.events?.length ?? 0) > 0 || (campaign.signals?.length ?? 0) > 0;
}

/**
 * Research Attention Gate v1（状态分类，**不是评分 / 概率 / 信号**）。
 *
 * ACTIVE_RESEARCH 需同时满足：
 *   1. 有明确研究对象（正式 Campaign；Research Candidate 一律不进）
 *   2. 阶段 ∈ {EARLY_SIGNAL, THEME_FORMING, BROAD_CONFIRMATION, EXPANSION}
 *   3. 有历史证据（Research 已记录事件 / 信号）
 *   4. 无无法忽略的重大 Conflict
 * WATCH：Candidate / 证据不足 / 重大 Conflict / 阶段不足以确认
 * HISTORICAL_REFERENCE：PEAK / DECLINE / END
 */
export function attentionOf(campaign: TimelineCampaign): AttentionResult {
  const phase = terminalPhaseOf(campaign);
  const reasons: string[] = [`阶段：${PHASE_LABEL[phase]}`];

  if (campaign.kind === 'candidate') {
    reasons.push('Research Candidate：未达正式 Campaign 门槛');
    return { state: 'WATCH', reasons };
  }
  if (hasMajorConflict(campaign)) {
    reasons.push('存在重大日期口径分歧（研究未自行取舍）');
    return { state: 'WATCH', reasons };
  }
  if (!hasEvidence(campaign)) {
    reasons.push('研究证据不足（未记录事件 / 信号）');
    return { state: 'WATCH', reasons };
  }
  // ★ P0 修正（Product / Real Usage v0.1）：
  //   `terminalPhaseOf` 取的是 lifecycle 中**最后记录的阶段**。当研究已记录 `end`
  //   （即该 Campaign **已结束**，`openEnded === false`）时，「最后阶段 = MAIN_RISE」
  //   只说明 **lifecycle 未记录终段**（终段缺失），**不能**据此判定「当前仍在扩张 / 当前值得研究」。
  //   反例（修正前）：`C-2016-PANEL-CYCLE`（end=2017-06-30，早已结束）与 `C-2019-RES-DYE-SHOCK`
  //   均因终段缺失被标为「当前值得研究」→ 属**误导性显示**。
  //   本判定**只用 export 自带字段**（`openEnded` / `end`），不引入 today，也不改动研究结论。
  if (!campaign.openEnded && campaign.end != null) {
    reasons.push('研究已记录结束日期 → 不主张「当前仍在扩张」');
    return { state: 'HISTORICAL_REFERENCE', reasons };
  }
  if (ACTIVE_PHASES.includes(phase)) {
    reasons.push('处于形成 / 确认 / 扩张阶段，且有研究证据');
    return { state: 'ACTIVE_RESEARCH', reasons };
  }
  if (REFERENCE_PHASES.includes(phase)) {
    reasons.push('已进入峰值 / 退潮 / 结束 → 仅作历史参考');
    return { state: 'HISTORICAL_REFERENCE', reasons };
  }
  reasons.push('阶段不足以确认');
  return { state: 'WATCH', reasons };
}

/** Macro Theme = 该研究对象题材中 `theme_type ∈ {industry, sector}` 且 `role = related` 的那个 */
export function macroThemeOf(campaign: TimelineCampaign): string | null {
  const macro = (campaign.themes ?? []).find(
    (t) => t.role === 'related' && (t.theme_type === 'industry' || t.theme_type === 'sector'),
  );
  return macro ? macro.name : null;
}

/**
 * Theme Cycle Pattern 派生（确定性）。
 * 逐对比较组件时间区间：A 完全先于 B（`A.end <= B.start`）→ 顺序关系；否则 → 并行关系。
 *   全部为顺序 → SEQUENTIAL；存在并行（且无顺序对）→ PARALLEL；两者都有 → HYBRID。
 * 组件数 ≤ 1 → SEQUENTIAL（无可观察的并存关系，按顺序处理，不编造 Parallel）。
 */
export function patternOf(components: { campaign: TimelineCampaign }[]): ThemeCyclePattern {
  if (components.length <= 1) return 'SEQUENTIAL';
  const spans = components
    .map((c) => ({ start: c.campaign.start, end: c.campaign.end }))
    .sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
  let sequential = 0;
  let parallel = 0;
  for (let i = 0; i < spans.length; i += 1) {
    for (let j = i + 1; j < spans.length; j += 1) {
      if (spans[i].end <= spans[j].start) sequential += 1;
      else parallel += 1;
    }
  }
  if (parallel === 0) return 'SEQUENTIAL';
  if (sequential === 0) return 'PARALLEL';
  return 'HYBRID';
}

/* ================= 4. 数据源遍历 ================= */

/** 数据源内全部研究对象（按 campaign_id 去重；跨年 Campaign 在多年 yearData 重复出现） */
export function allResearchObjects(source: TimelineDataSource): TimelineCampaign[] {
  const map = new Map<string, TimelineCampaign>();
  for (const y of source.years()) {
    for (const c of source.yearData(y).campaigns) {
      if (!map.has(c.campaign_id)) map.set(c.campaign_id, c);
    }
  }
  return [...map.values()].sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
}

/** Theme Cycle 归组（Parallel-aware）；组件按 start 升序 */
export function themeCycleViewsOf(source: TimelineDataSource): ThemeCycleView[] {
  const objects = allResearchObjects(source);
  const groups = new Map<string, TimelineCampaign[]>();
  for (const c of objects) {
    const key = c.theme_cycle_id ?? c.campaign_id;
    const list = groups.get(key);
    if (list) list.push(c);
    else groups.set(key, [c]);
  }

  const views: ThemeCycleView[] = [];
  for (const [key, list] of groups) {
    const sorted = list.slice().sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));
    const components: ThemeCycleComponent[] = sorted.map((c) => ({
      campaign: c,
      phase: terminalPhaseOf(c),
      attention: attentionOf(c),
      drivers: driverCategoriesOf(c),
    }));
    const macroTheme = components.map((c) => macroThemeOf(c.campaign)).find((n) => n !== null) ?? null;
    const summaryAttention = components
      .map((c) => c.attention.state)
      .sort((a, b) => ATTENTION_RANK[a] - ATTENTION_RANK[b])[0];
    views.push({
      key,
      themeCycleId: sorted[0].theme_cycle_id ?? null,
      macroTheme,
      pattern: patternOf(components.map((c) => ({ campaign: c.campaign }))),
      components,
      summaryAttention,
      coverage: {
        start: sorted[0].start,
        end: sorted.reduce((mx, c) => (c.end > mx ? c.end : mx), sorted[0].end),
      },
    });
  }
  // 排序：Macro Theme 名升序 → 覆盖起点升序（确定性）
  return views.sort((a, b) => {
    const am = a.macroTheme ?? '\uffff';
    const bm = b.macroTheme ?? '\uffff';
    if (am !== bm) return am < bm ? -1 : 1;
    return a.coverage.start < b.coverage.start ? -1 : 1;
  });
}

/* ================= 5. Current Time Lens v2 视图模型 ================= */

export interface AttentionItem {
  campaign_id: string;
  title: string;
  year: number;
  kind: TimelineCampaign['kind'];
  phase: ResearchPhase;
  phaseLabel: string;
  macroTheme: string | null;
  themeCycleId: string | null;
  drivers: DriverCategory[];
  reasons: string[];
}

export interface CurrentLensV2 {
  today: string;
  currentYear: number;
  /** A. A股整体环境 —— 数据不足时为 UNKNOWN（严禁由行业 Campaign 推导大盘状态） */
  layerA: { state: 'UNKNOWN'; label: string; note: string };
  /** B. 当前 Theme / Theme Cycle —— 无当前年份数据时必须诚实空态（NO LOOK-AHEAD） */
  layerB: {
    hasCurrentData: boolean;
    coverage: { from: number | null; to: number | null };
    note: string;
    /** 研究覆盖内的 Theme Cycle（**历史参考**，不是当前状态） */
    cycles: ThemeCycleView[];
  };
  /** C. Research Attention —— 研究数据覆盖内的关注度分类（不是评分） */
  layerC: {
    note: string;
    active: AttentionItem[];
    watch: AttentionItem[];
    reference: AttentionItem[];
    referenceTotal: number;
  };
}

const LAYER_A_NOTE =
  'ThreeC 当前没有完整的 A股整体市场周期模型（无指数 / 成交量 / 资金 / 情绪数据源）。' +
  '因此不判断「牛市 / 熊市 / 风险偏好」—— 也不从行业 Campaign 反推大盘状态。';

/**
 * 构建 Current Time Lens v2。
 *
 * **NO LOOK-AHEAD**：`today` 只用于定位日历位置与判断「研究数据是否覆盖当前年份」；
 * 不会把 `today` 之后的数据当作已知，也不会用历史年份数据伪装当前状态。
 */
export function buildCurrentLensV2(source: TimelineDataSource, today: string): CurrentLensV2 {
  const years = source.years();
  const currentYear = Number(today.slice(0, 4));
  const from = years.length > 0 ? years[0] : null;
  const to = years.length > 0 ? years[years.length - 1] : null;

  const cycles = themeCycleViewsOf(source);

  // 当前年份是否有研究数据：该年 yearData 内存在覆盖该年的研究对象
  const hasCurrentData = source.yearData(currentYear).campaigns.length > 0;

  const layerBNote = hasCurrentData
    ? `研究数据已覆盖 ${currentYear}：以下为 ${currentYear} 年度内出现的研究对象（研究记录，不是市场状态判断）。`
    : `暂无 ${currentYear} 当前 Theme Cycle 研究数据。历史研究覆盖至 ${to ?? '—'}。\n` +
      '当前页面保留历史位置与历史参考，不将历史数据伪装成当前状态。这是正常结果，不是错误。';

  const grouped: Record<AttentionState, AttentionItem[]> = {
    ACTIVE_RESEARCH: [],
    WATCH: [],
    HISTORICAL_REFERENCE: [],
  };
  for (const c of allResearchObjects(source)) {
    const att = attentionOf(c);
    const phase = terminalPhaseOf(c);
    grouped[att.state].push({
      campaign_id: c.campaign_id,
      title: c.title,
      year: c.year,
      kind: c.kind,
      phase,
      phaseLabel: PHASE_LABEL[phase],
      macroTheme: macroThemeOf(c),
      themeCycleId: c.theme_cycle_id ?? null,
      drivers: driverCategoriesOf(c),
      reasons: att.reasons,
    });
  }

  const byStartDesc = (a: AttentionItem, b: AttentionItem) =>
    a.year !== b.year ? b.year - a.year : a.campaign_id < b.campaign_id ? -1 : 1;
  grouped.ACTIVE_RESEARCH.sort(byStartDesc);
  grouped.WATCH.sort(byStartDesc);
  grouped.HISTORICAL_REFERENCE.sort(byStartDesc);

  return {
    today,
    currentYear,
    layerA: {
      state: 'UNKNOWN',
      label: 'A股整体周期：Unknown',
      note: LAYER_A_NOTE,
    },
    layerB: {
      hasCurrentData,
      coverage: { from, to },
      note: layerBNote,
      cycles,
    },
    layerC: {
      note:
        `以下基于 ThreeC 研究数据（覆盖至 ${to ?? '—'}）的分类，不是市场状态判断、不是评分、不是概率。` +
        '「当前值得研究」指研究记录内处于形成 / 确认 / 扩张阶段且有证据的案例。',
      active: grouped.ACTIVE_RESEARCH,
      watch: grouped.WATCH,
      reference: grouped.HISTORICAL_REFERENCE,
      referenceTotal: grouped.HISTORICAL_REFERENCE.length,
    },
  };
}
