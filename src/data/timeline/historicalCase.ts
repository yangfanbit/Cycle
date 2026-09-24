/**
 * Historical Case Experience v0.1 —— Historical Case 视图模型（**纯 Adapter，不推导研究结论**）。
 *
 * ## 定位
 * `TimelineCampaign`（`timeline_export_v1`）+ 可选 Structural Analogy Explanation Artifact
 * → **Historical Case 视图模型**。
 *
 * 回答：**「这个历史机会具体是怎么形成、发展、转向、结束的？」**
 *
 * ## 边界（不得违反）
 * - **不推导**：生命周期 / 驱动机制 / 证据序列全部**原样消费** Research 数据，Product 不重新计算。
 * - **分层命名**：**驱动机制（Mechanism Driver）** ≠ **证据类别（Evidence Category）**。
 *   - 驱动机制 = 研究层机制判断（`POLICY_DRIVEN` / `INDUSTRY_UPGRADE` / …）→ 来自
 *     `historical_driver_canonicalization_v0_1.json`（**按需加载**）
 *   - 证据类别 = 事件来源类别（`POLICY` / `INDUSTRY` / `CAPITAL` / `EXTERNAL`）→ 由事件的
 *     `event_type` **确定性映射**（`timeline_export_v1` 契约内既有口径）
 * - **不伪造缺失**：无数据 → `NOT_AVAILABLE` / 明确空态，**不得**显示成「没有」。
 * - **不联网 / 无 LLM**：canonicalization artifact 走 Vite 动态 import（同源静态 chunk）。
 * - **不改 Research**：只读消费。
 */

import type { TimelineCampaign } from './timelineTypes';
import { campaignDrivers, driverGroupBounds } from './timelineAdapter';

/* ================= 1. 证据类别轴（Evidence Category） ================= */

/** 证据类别取值（= 事件的来源类别，**不是**驱动机制）。 */
export type EvidenceCategory = 'POLICY' | 'INDUSTRY' | 'CAPITAL' | 'EXTERNAL';

export const EVIDENCE_CATEGORY_ORDER: EvidenceCategory[] = [
  'POLICY',
  'INDUSTRY',
  'CAPITAL',
  'EXTERNAL',
];

export const EVIDENCE_CATEGORY_LABEL: Record<EvidenceCategory, string> = {
  POLICY: '政策',
  INDUSTRY: '产业',
  CAPITAL: '资金',
  EXTERNAL: '外部',
};

/**
 * `event_type` → 证据类别（**确定性映射，与仓库既有口径一致**）。
 * `industry` / `news` / `holiday` / `other` **不在**映射内 —— 不猜测。
 */
export const EVENT_TYPE_TO_EVIDENCE_CATEGORY: Record<string, EvidenceCategory> = {
  policy: 'POLICY',
  company: 'INDUSTRY',
  market: 'CAPITAL',
  macro: 'EXTERNAL',
};

/** 由事件集合确定性派生证据类别集合（**不推断**，仅映射已有 event_type）。 */
export function evidenceCategoriesOf(
  events: { event_type: string }[],
): EvidenceCategory[] {
  const set = new Set<EvidenceCategory>();
  for (const e of events) {
    const c = EVENT_TYPE_TO_EVIDENCE_CATEGORY[e.event_type];
    if (c) set.add(c);
  }
  return EVIDENCE_CATEGORY_ORDER.filter((c) => set.has(c));
}

/* ================= 2. 驱动机制轴（Mechanism Driver）—— 按需加载 ================= */

export type MappingStatus = 'DIRECT' | 'DERIVED' | 'AMBIGUOUS' | 'UNKNOWN' | 'NOT_AVAILABLE';

export interface MechanismDriverView {
  /** canonical 机制名（`POLICY_DRIVEN` / `INDUSTRY_UPGRADE` / …）。 */
  driver: string;
  /** 该机制在本 cycle 的映射依据强度。 */
  mappingStatus: MappingStatus;
  /** 支撑该机制的原始 driver 文本（provenance，**原样保留**）。 */
  rawDrivers: string[];
}

interface CanonicalizationDoc {
  per_cycle?: {
    cycle_id: string;
    canonical_drivers?: string[];
    terminal_mechanisms?: string[];
    driving_direct_count?: number;
    driving_derived_count?: number;
  }[];
}

let _canonCache: Map<string, MechanismDriverView[]> | null = null;

/**
 * 按需加载驱动机制（**动态 import → 独立 chunk**）。
 * 失败返回空 Map —— 调用方须显示 `NOT_AVAILABLE`，**不得**显示成「没有机制」。
 */
export async function loadMechanismDrivers(): Promise<Map<string, MechanismDriverView[]>> {
  if (_canonCache) return _canonCache;
  const mod = await import('@observation/historical_driver_canonicalization_v0_1.json');
  const doc = (mod as { default: CanonicalizationDoc }).default;
  const out = new Map<string, MechanismDriverView[]>();
  for (const c of doc.per_cycle ?? []) {
    const rows: MechanismDriverView[] = (c.canonical_drivers ?? []).map((d) => ({
      driver: d,
      // canonicalization 只输出「进入 driver 集合」的项（DIRECT / DERIVED）；
      // 逐条依据强度在 ledger 中，此处按 cycle 级标注（不虚构逐条状态）
      mappingStatus: (c.driving_direct_count ?? 0) > 0 ? 'DIRECT' : 'DERIVED',
      rawDrivers: [],
    }));
    out.set(c.cycle_id, rows);
  }
  _canonCache = out;
  return out;
}

/** 仅供测试：注入已解析的机制表。 */
export function __setMechanismDriversForTest(v: Map<string, MechanismDriverView[]> | null): void {
  _canonCache = v;
}

/* ================= 3. Historical Case 视图模型 ================= */

export interface HistoricalCaseHeader {
  campaignId: string;
  /** 显示标题（如「汽车 · 智能驾驶」）。 */
  title: string;
  start: string;
  end: string;
  openEnded: boolean;
  peak: string | null;
  /** Theme Cycle（research metadata 透传；缺失为 null）。 */
  themeCycleId: string | null;
  /** Macro Theme（由 `theme_type ∈ {industry, sector}` 的题材透传；缺失为 null）。 */
  macroTheme: string | null;
  /** 研究层对象类型：正式 Campaign 或 Research Candidate（**不得混淆**）。 */
  objectKind: 'campaign' | 'research_candidate';
  seasonId: string;
  ruleId: string;
}

export interface LifecycleStageView {
  stage: string;
  label: string;
  /** Contract：`start` / `end` **可为 null**（开放区间；`is_iso_date(None) == True`）—— 不猜测端点。 */
  start: string | null;
  end: string | null;
}

export interface EvidenceSequenceEntry {
  /** 真实日期。 */
  date: string;
  name: string;
  eventType: string;
  /** 该事件所属的生命周期阶段（由日期落在 `phases` 区间内确定性推导；不在任何区间 → null）。 */
  lifecycleStage: string | null;
  lifecycleStageLabel: string | null;
  /** 研究层事件角色（trigger / catalyst / context / follow_up；缺失 null）。 */
  role: string | null;
}

export interface HistoricalCaseView {
  header: HistoricalCaseHeader;
  /**
   * 生命周期分段（**原样**来自 Research 导出的 `lifecycle`）。
   *
   * ★ Gate T8（`UNKNOWN ≠ 自动推导具体阶段`）：
   *   只读 `TimelineCampaign.lifecycle`（= export Research lifecycle）。
   *   Research 未记录生命周期时 → **`[]`**，**不得**用视图分段
   *   （`TimelineCampaign.phases`，adapter 由 `derivePhases()` 派生）顶替。
   */
  lifecycle: LifecycleStageView[];
  /** 早期信号（前置观察，**不是**正式行情起点）。 */
  earlySignal: { start: string; end: string; label: string | null } | null;
  /** 驱动机制（机制判断）。加载完成前为 `null` → 显示加载中。 */
  mechanismDrivers: MechanismDriverView[] | null;
  /** 证据类别（来源类别）。 */
  evidenceCategories: EvidenceCategory[];
  /** 证据序列（按真实日期升序；**保持 UNKNOWN / NOT_AVAILABLE 语义**）。 */
  evidenceSequence: EvidenceSequenceEntry[];
  /** 是否无任何关联事件（用于诚实空态）。 */
  hasNoEvents: boolean;
}

/* ================= 4. 文案 ================= */

export const LIFECYCLE_STAGE_LABEL: Record<string, string> = {
  // ★ product `TimelinePhaseSegment.phase` 使用**小写** LifecyclePhase —— 必须全部覆盖，
  //   否则 UI 会出现中英混用（实测：declining / early_signal 曾回落为原始英文）。
  early_signal: '早期信号',
  main_rise: '主升',
  peak: '峰值',
  retracement: '回撤',
  declining: '衰减',
  ended: '已结束',
  // Research `lifecycle[].stage` 使用**大写**枚举
  EARLY_SIGNAL: '早期信号', THEME_FORMING: '主题形成', BROAD_CONFIRMATION: '扩散确认',
  MAIN_RISE: '主升', PEAK: '峰值', RETRACEMENT: '回撤', SECONDARY: '次级行情',
  DECLINING: '衰减', FIRST_DECLINE: '首次回落', MAIN_END: '主段结束',
  startup: '启动',
  acceleration: '加速',
  diffusion: '扩散',
  secondary_rally: '次级反弹',
  decline: '衰减',
};

export const MAPPING_STATUS_LABEL: Record<MappingStatus, string> = {
  DIRECT: '直接依据',
  DERIVED: '推导依据',
  AMBIGUOUS: '依据不明',
  UNKNOWN: '未知',
  NOT_AVAILABLE: '无可用资料',
};

/* ================= 5. 构造（纯映射，不推导研究结论） ================= */

function macroThemeOf(c: TimelineCampaign): string | null {
  // 契约 §11：`theme_type` 为 research metadata 透传，用于 Macro Theme → Campaign 层级推导。
  const t = c.themes.find((x) => x.theme_type === 'industry' || x.theme_type === 'sector');
  return t ? t.name : null;
}

function lifecycleStageAt(
  date: string,
  phases: TimelineCampaign['phases'],
): { stage: string; label: string } | null {
  for (const p of phases) {
    if (p.start && p.end && date >= p.start && date <= p.end) {
      return { stage: p.phase, label: LIFECYCLE_STAGE_LABEL[p.phase] ?? p.phase };
    }
  }
  return null;
}

/** 由 `TimelineCampaign` 构造 Historical Case 视图模型（**同步部分**）。 */
export function historicalCaseOf(c: TimelineCampaign): HistoricalCaseView {
  const events = [...c.events].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

  return {
    header: {
      campaignId: c.campaign_id,
      title: c.title,
      start: c.start,
      end: c.end,
      openEnded: c.openEnded === true,
      peak: c.peak ?? null,
      themeCycleId: c.theme_cycle_id ?? null,
      macroTheme: macroThemeOf(c),
      objectKind: c.kind === 'candidate' ? 'research_candidate' : 'campaign',
      seasonId: c.season_id,
      ruleId: c.rule_id,
    },
    // ★ Gate T8：**只消费 Research lifecycle**（`c.lifecycle`）。
    //   `c.phases` 是 adapter 由 `derivePhases()` 派生的**视图分段**（Timeline 视觉用），
    //   `peak == null` 时它会无条件产出 `main_rise` —— 用它顶替 Research lifecycle
    //   等于在 Product 层虚构一个研究未确立的阶段。故此处**不得**回退到 `c.phases`。
    //   `start` / `end` 可为 null（开放区间），原样透传。
    lifecycle: (c.lifecycle ?? []).map((s) => ({
      stage: s.stage,
      label: LIFECYCLE_STAGE_LABEL[s.stage] ?? s.stage,
      start: s.start,
      end: s.end,
    })),
    earlySignal: c.early_signal
      ? { start: c.early_signal.start, end: c.early_signal.end, label: c.early_signal.label ?? null }
      : null,
    mechanismDrivers: null, // 由调用方异步填充
    evidenceCategories: evidenceCategoriesOf(events),
    evidenceSequence: events.map((e) => {
      const at = lifecycleStageAt(e.date, c.phases);
      return {
        date: e.date,
        name: e.name,
        eventType: e.event_type,
        lifecycleStage: at?.stage ?? null,
        lifecycleStageLabel: at?.label ?? null,
        role: e.role ?? null,
      };
    }),
    hasNoEvents: events.length === 0,
  };
}

/** 合并已加载的驱动机制（异步补丁，保持其余字段不变）。 */
export function withMechanismDrivers(
  view: HistoricalCaseView,
  table: Map<string, MechanismDriverView[]>,
): HistoricalCaseView {
  return { ...view, mechanismDrivers: table.get(view.header.campaignId) ?? [] };
}

/* ================= 6. Structural Analogy 上下文（从 SA 进入 Case 时携带） ================= */

/**
 * 从 Structural Analogy 进入 Historical Case 时携带的**轻量上下文**。
 * **全部字段原样来自 Explanation Artifact v0.2** —— Product **不重新计算**。
 */
export interface HistoricalCaseAnalogyContext {
  candidateId: string;
  candidateName: string | null;
  structuralStatus: string;
  strictStructuralSupported: boolean;
  themeRelation: { value: string; label: string };
  dimensions: { key: string; label: string; status: string; statusLabel: string }[];
  whySimilar: string[];
  whyNotSimilar: string[];
  /** 未知维度（`UNKNOWN` / `NOT_AVAILABLE`）—— 与 `MISMATCH` **严格区分**。 */
  unknownDimensionLabels: string[];
  snapshotDate: string;
  ruleSetVersion: string;
}

/* ================= 7. Historical Evidence Timeline（统一证据视图 · Rework v0.1） ================= */

/**
 * 归组阶段（**时间位置**，不是因果证明）。
 * `OTHER` = 不落在任何已记录归组窗口内 —— **不强行归因**。
 */
export type AttributionPhase = 'START' | 'ACCELERATE' | 'TURN' | 'END' | 'OTHER';

export const ATTRIBUTION_PHASE_LABEL: Record<AttributionPhase, string> = {
  START: '启动附近',
  ACCELERATE: '加速段',
  TURN: '转折附近',
  END: '结束附近',
  OTHER: '其他时间位置',
};

export const ATTRIBUTION_QUESTION_LABEL: Record<AttributionPhase, string> = {
  START: '为什么启动？',
  ACCELERATE: '为什么加速？',
  TURN: '为什么转折？',
  END: '为什么结束？',
  OTHER: '其他',
};

/** 归因来源：Research 声明（V1.7 drivers）或按时间归组线索。 */
export type AttributionSource = 'RESEARCH' | 'TIME_GROUPING';

export interface HistoricalEvidenceRow {
  /** 稳定去重键：`date|name`（`TimelineCampaign.events` 无 event_id）。 */
  key: string;
  date: string;
  /** 生命周期阶段（原样来自 Research `phases`）；null = 阶段未知。 */
  lifecycleStage: string | null;
  lifecycleStageLabel: string;
  eventType: string;
  role: string | null;
  name: string;
  attributionPhase: AttributionPhase;
}

export interface AttributionGroupView {
  phase: AttributionPhase;
  question: string;
  phaseLabel: string;
  items: string[];
}

export interface HistoricalEvidenceTimeline {
  /** 按日期升序；**每个事件只出现一次**。 */
  rows: HistoricalEvidenceRow[];
  hasEvents: boolean;
  /** 四问归因（原样来自 `campaignDrivers()`）。 */
  attribution: AttributionGroupView[];
  /** 归因来源（语义不同，UI 必须区分展示）。 */
  attributionSource: AttributionSource;
  /** 是否存在**无阶段**的行（用于「阶段未知」说明）。 */
  hasUnknownStage: boolean;
}

/** 单个事件 → 唯一的归组阶段（复用 `campaignDrivers()` 的**同一套**窗口）。 */
function attributionPhaseOf(
  date: string,
  bounds: ReturnType<typeof driverGroupBounds>,
): AttributionPhase {
  const inRange = (r: readonly [string, string]) => r[0] <= date && date <= r[1];
  if (inRange(bounds.start)) return 'START';
  if (inRange(bounds.accelerate)) return 'ACCELERATE';
  if (inRange(bounds.turn)) return 'TURN';
  if (bounds.end && inRange(bounds.end)) return 'END';
  return 'OTHER'; // 不强行归因
}

/**
 * 构建统一的「历史演化证据」时间线（**Product View Model，不写 DB / schema**）。
 *
 * 去重原则：**每个事件只出现一次**，一行承载
 * 日期 + Lifecycle 阶段 + Event Type + Role + Event Name + 归组阶段。
 */
export function historicalEvidenceTimelineOf(c: TimelineCampaign): HistoricalEvidenceTimeline {
  const bounds = driverGroupBounds(c);
  const seen = new Set<string>();
  const rows: HistoricalEvidenceRow[] = [];

  for (const e of [...c.events].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0))) {
    const key = `${e.date}|${e.name}`;
    if (seen.has(key)) continue; // ★ 去重：同一事件只保留一次
    seen.add(key);
    const at = lifecycleStageAt(e.date, c.phases);
    rows.push({
      key,
      date: e.date,
      lifecycleStage: at?.stage ?? null,
      lifecycleStageLabel: at?.label ?? '阶段未知',
      eventType: e.event_type,
      role: e.role ?? null,
      name: e.name,
      attributionPhase: attributionPhaseOf(e.date, bounds),
    });
  }

  const d = campaignDrivers({
    start: c.start, peak: c.peak ?? null, end: c.end,
    openEnded: c.openEnded === true, events: c.events, drivers: c.drivers,
  });
  const attribution: AttributionGroupView[] = (['START', 'ACCELERATE', 'TURN', 'END'] as const).map(
    (phase) => ({
      phase,
      question: ATTRIBUTION_QUESTION_LABEL[phase],
      phaseLabel: ATTRIBUTION_PHASE_LABEL[phase],
      items: phase === 'START' ? d.start : phase === 'ACCELERATE' ? d.accelerate
        : phase === 'TURN' ? d.turn : d.end,
    }),
  );

  return {
    rows,
    hasEvents: rows.length > 0,
    attribution,
    attributionSource: c.drivers ? 'RESEARCH' : 'TIME_GROUPING',
    hasUnknownStage: rows.some((r) => r.lifecycleStage === null),
  };
}

/** Phase（历史行情阶段）与 Signal（Research 前置观察标记）关系说明（**消除语义误解**）。 */
export const PHASE_SIGNAL_CLARIFICATION =
  '生命周期 = 历史行情阶段（来自 Research `lifecycle`）；研究信号 = Research 层的前置观察标记（来自 `signals`）。两者不是同一套阶段体系。';
