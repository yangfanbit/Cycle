/**
 * Time-based Observation Layer —— 时间型观察层数据层（Phase 7.2）。
 *
 * ## 定位
 * `research/research/reports/time_observation_patterns_v0_1.json`（**离线研究 Artifact**）
 * → 产品端只读消费。回答：
 *
 *   「历史上，一年中的这个时间位置附近，**反复出现过**值得研究的主题启动 / 观察现象吗？」
 *
 * 即：**「什么时候值得看」**。它**不**回答「现在出现了什么」——
 * 后者是 Current Candidate（`currentCandidate.ts`）的职责，两者是两个不同维度，本轮保持独立。
 *
 * ## 关键边界（不得违反）
 * - **纯 View / Adapter**：不写 DB / `schema.sql` / export / contracts；不改 Campaign 定义。
 * - **不是预测器**：不输出未来概率 / 胜率 / 买卖信号 / 目标价 / 评分。
 *   历史复现一律表述为「历史样本中 X / Y 个观测年份」。`historical_ratio` 只可原样保存，
 *   **不得**解释为「今年有 X% 概率」。
 * - **不联网**：静态 import（`@observation` alias），无运行时请求。
 * - **时间语义**：Pattern 的窗口是**日历坐标**（MM-DD），属于历史观察规律；
 *   `proximity` 只描述「今天是否落在该日历窗口附近」，不是市场状态判断。
 * - **Pattern ≠ Campaign**：一条 Pattern 对应多年、多个 Campaign；点击年份进入既有 Campaign Detail。
 * - **日期逻辑只有一套**：复用 `src/utils/date/dateUtils`（`mdToISO` / `isCrossYearMD` /
 *   `compareMD` / `dayOfYearISO` / `yearFraction`），不在本模块另造日历。
 */

import rawArtifact from '@observation/time_observation_patterns_v0_1.json';
import { mdToISO, isCrossYearMD, dayOfYearISO, yearFraction, addDaysISO } from '../../utils';
import { timelineEntryId, type TimelineEntryId } from './entryIdentity';

/* ================= 1. 枚举与文案 ================= */

export type ObservationPatternType =
  | 'SEASONAL'
  | 'CALENDAR_DRIVEN'
  | 'INDUSTRY_CYCLE'
  | 'REPORTING_CYCLE'
  | 'POLICY_CALENDAR'
  | 'MIXED'
  | 'UNKNOWN';

export const PATTERN_TYPE_LABEL: Record<ObservationPatternType, string> = {
  SEASONAL: '季节性',
  CALENDAR_DRIVEN: '日历驱动',
  INDUSTRY_CYCLE: '产业周期',
  REPORTING_CYCLE: '披露周期',
  POLICY_CALENDAR: '政策日历',
  MIXED: '多机制叠加',
  UNKNOWN: '未判定',
};

/** Timeline 纳入判定（研究层结论；产品只呈现 TIMELINE_ELIGIBLE） */
export type TimelineEligibility = 'TIMELINE_ELIGIBLE' | 'RESEARCH_ONLY' | 'REJECTED';

/** 今天与该窗口的关系（纯日历距离，不是市场状态、不是信号） */
export type WindowProximity = 'IN_WINDOW' | 'NEAR_WINDOW' | 'OUTSIDE';

export const PROXIMITY_LABEL: Record<WindowProximity, string> = {
  IN_WINDOW: '当前位于历史观察窗口',
  NEAR_WINDOW: '接近历史观察窗口',
  OUTSIDE: '不在历史观察窗口内',
};

/**
 * 「接近窗口」的邻近缓冲（自然日）。
 *
 * ⚠️ **UI 浏览缓冲，不是统计量、不是预测依据。** 与 `historicalPreObservationDays = 30`
 * 同类性质：用于让用户知道「离观察窗口还有多远」，不代表任何历史领先期。
 */
export const nearWindowDays = 14;

/** 默认文案（研究 Artifact 未提供 label_vocabulary 时的兜底；正常情况下由 Research 提供） */
const DEFAULT_LABELS = {
  window: '历史观察窗口',
  recurrence: '历史复现',
  in_window: PROXIMITY_LABEL.IN_WINDOW,
  near_window: PROXIMITY_LABEL.NEAR_WINDOW,
  none: '当前没有发现处于历史时间观察窗口的模式',
  disclaimer: '这是历史时间聚集现象，不代表今年必然重演，也不是买入或卖出信号。',
};

/* ================= 2. 数据结构 ================= */

export interface PatternWindow {
  /** MM-DD */
  start: string;
  /** MM-DD（若 start > end 则为跨年窗口） */
  end: string;
  widthDays: number;
  /** 中心日期 MM-DD */
  centerDate: string;
  method: string;
  /** 跨年窗口（如 12-20 ~ 01-15） */
  crossYear: boolean;
  /** 展示标签，如「05-27 ~ 06-26」 */
  label: string;
  /** P25–P75 备选口径（并列保留，不挑好看的用） */
  alternativeQuantile?: { start: string; end: string } | null;
}

export interface PatternObservation {
  year: number;
  /** ISO 日期（该年的研究观察起点 = Early Signal） */
  date: string;
  /** MM-DD */
  md: string;
  campaignId: string;
  title: string;
  kind: 'campaign' | 'research_candidate';
  /** 该年锚点是否落在典型窗口内（研究层口径；窗口不存在时为 null） */
  inWindow: boolean | null;
  /** 展示实例身份（campaign_id@年份）——供 Timeline 条目高亮 */
  timelineEntryId: TimelineEntryId;
}

export interface PatternRecurrence {
  matchedCount: number;
  eligibleYears: number;
  matchedYears: number[];
  missedYears: number[];
  /** 研究层原样保存；**不得**在 UI 中解释为未来概率 */
  historicalRatio: number | null;
  label: string;
}

export interface TimeObservationPattern {
  patternId: string;
  sourcePatternId: string;
  patternType: ObservationPatternType;
  title: string;
  description: string;
  themeScope: string;
  themeKey: string;
  anchorType: string;
  centerDate: string;
  window: PatternWindow | null;
  observations: PatternObservation[];
  recurrence: PatternRecurrence;
  stability: { status: string; driftFlag: string | null; medianShiftDays: number | null; note?: string };
  dataQuality: { grade: string; note: string };
  researchStrength: string;
  status: string;
  timelineEligibility: TimelineEligibility;
  timelineEligible: boolean;
  eligibilityReason: string;
  mechanism: { type: string; primary: string; note: string; isLunarDriven: boolean; lunarNote: string };
  limitations: string[];
}

export interface TimeObservationDataset {
  artifact: 'time_observation_patterns';
  version: string;
  snapshotDate: string;
  generatedAt?: string;
  /** 研究层提供的文案词表（Product 渲染，Research 拥有措辞） */
  labels: typeof DEFAULT_LABELS;
  patterns: TimeObservationPattern[];
  /** 宽容解析产生的问题（非致命；严格校验由生成器自检负责） */
  issues: string[];
}

/** 空数据集（Artifact 缺失或不可解析时的诚实兜底：不显示任何窗口） */
export const EMPTY_TIME_OBSERVATION_DATASET: TimeObservationDataset = {
  artifact: 'time_observation_patterns',
  version: '0.1',
  snapshotDate: '',
  labels: DEFAULT_LABELS,
  patterns: [],
  issues: [],
};

/* ================= 3. 日历窗口 helper ================= */

/* eslint-disable @typescript-eslint/no-explicit-any */
const str = (v: unknown): string | null => (typeof v === 'string' && v.length > 0 ? v : null);
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null);

const MD_RE = /^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;
const ISO_RE = /^\d{4}-\d{2}-\d{2}$/;

/** MM-DD 是否合法（含真实月长校验：拒绝 02-30 / 04-31 / 06-31 这类伪合法日期） */
export function isValidMd(md: string): boolean {
  if (!MD_RE.test(md)) return false;
  // 闰年基准做往返校验：Date.UTC 会把非法日期滚动到下一月，据此识别
  return addDaysISO(mdToISO(md, MD_VALIDATE_YEAR), 0) === mdToISO(md, MD_VALIDATE_YEAR);
}

/** 非闰年基准日序（1–365），用于环形距离计算（不随具体年份漂移） */
const MD_BASE_YEAR = 2025;
/** 闰年基准，仅用于 MM-DD 合法性往返校验（允许 02-29） */
const MD_VALIDATE_YEAR = 2024;
function doyOfMd(md: string): number {
  return dayOfYearISO(mdToISO(md, MD_BASE_YEAR));
}

/** 环形前向距离 to - from（0..364） */
function forwardDays(from: number, to: number): number {
  return (to - from + 365) % 365;
}

/**
 * 日期是否落在 MM-DD 窗口内（**支持跨年窗口**，如 12-20 ~ 01-15）。
 * 这是本模块唯一的「是否在窗口内」判定，UI 与测试必须都走这里。
 */
export function isMdInWindow(md: string, start: string, end: string): boolean {
  if (!isValidMd(md) || !isValidMd(start) || !isValidMd(end)) return false;
  if (!isCrossYearMD(start, end)) return start <= md && md <= end;
  // 跨年：窗口 = [start, 12-31] ∪ [01-01, end]
  return md >= start || md <= end;
}

/**
 * 日期到窗口的日历距离（天）：窗口内 → 0；窗口外 → 到最近边界的环形距离。
 * 跨年窗口同样正确（不依赖年份）。
 */
export function daysFromWindow(md: string, start: string, end: string): number {
  if (isMdInWindow(md, start, end)) return 0;
  const a = doyOfMd(md);
  const s = doyOfMd(start);
  const e = doyOfMd(end);
  return Math.min(forwardDays(e, a), forwardDays(a, s));
}

/**
 * 今天与窗口的关系（纯日历）。
 * - `IN_WINDOW`  窗口内；
 * - `NEAR_WINDOW` 窗口外但距离 ≤ `nearWindowDays`；
 * - `OUTSIDE`    其余。
 */
export function proximityOf(
  md: string,
  start: string,
  end: string,
  nearDays: number = nearWindowDays,
): WindowProximity {
  if (isMdInWindow(md, start, end)) return 'IN_WINDOW';
  return daysFromWindow(md, start, end) <= nearDays ? 'NEAR_WINDOW' : 'OUTSIDE';
}

/** MM-DD 在指定年份轨道上的位置比例（0..1） */
export function mdFractionInYear(md: string, year: number): number {
  return yearFraction(mdToISO(md, year));
}

export interface WindowBandSegment {
  left: number;
  width: number;
  /** 起点在本年之前（跨年窗口的上一年部分） */
  continuesFromPrevYear: boolean;
  /** 终点在本年之后（跨年窗口的下一年部分） */
  continuesIntoNextYear: boolean;
}

/**
 * 把 MM-DD 窗口渲染为**某一年轨道上的色带分段**。
 * 普通窗口 → 一段；跨年窗口 → 两段（年末段 + 年初段），用 continues* 标记，
 * 与既有 `bar cont-prev / cont-next` 视觉语言一致。
 */
export function windowBandsForYear(start: string, end: string, year: number): WindowBandSegment[] {
  if (!isValidMd(start) || !isValidMd(end)) return [];
  const exp = (left: number, right: number, cp: boolean, cn: boolean): WindowBandSegment => ({
    left,
    // 至少留一点可见宽度（点状窗口也能被看到）
    width: Math.max(right - left, 0.004),
    continuesFromPrevYear: cp,
    continuesIntoNextYear: cn,
  });
  if (!isCrossYearMD(start, end)) {
    const left = mdFractionInYear(start, year);
    // 注意：addDaysISO 返回 ISO，必须用 yearFraction（而不是只接受 MM-DD 的 mdFractionInYear）
    const right = yearFraction(addDaysISO(mdToISO(end, year), 1));
    return [exp(left, right, false, false)];
  }
  // 跨年窗口 = [start, 12-31]（延续到次年）+ [01-01, end]（承接上一年）
  const tailFrom = mdFractionInYear(start, year);
  const headTo = yearFraction(addDaysISO(mdToISO(end, year), 1));
  return [exp(tailFrom, 1, false, true), exp(0, headTo, true, false)];
}

/* ================= 4. 解析（宽容） ================= */

function asPatternType(v: unknown): ObservationPatternType {
  const ok: ObservationPatternType[] = [
    'SEASONAL',
    'CALENDAR_DRIVEN',
    'INDUSTRY_CYCLE',
    'REPORTING_CYCLE',
    'POLICY_CALENDAR',
    'MIXED',
    'UNKNOWN',
  ];
  return ok.includes(v as ObservationPatternType) ? (v as ObservationPatternType) : 'UNKNOWN';
}

function asEligibility(v: unknown): TimelineEligibility {
  const ok: TimelineEligibility[] = ['TIMELINE_ELIGIBLE', 'RESEARCH_ONLY', 'REJECTED'];
  return ok.includes(v as TimelineEligibility) ? (v as TimelineEligibility) : 'REJECTED';
}

function parseWindow(raw: any, issues: string[], pid: string): PatternWindow | null {
  const start = str(raw?.start);
  const end = str(raw?.end);
  if (!start || !end) return null;
  if (!isValidMd(start) || !isValidMd(end)) {
    issues.push(`${pid}：窗口日期非法（${start} ~ ${end}）→ 忽略该窗口`);
    return null;
  }
  const crossYear = isCrossYearMD(start, end);
  const widthDays = num(raw?.width_days) ?? (crossYear ? 0 : doyOfMd(end) - doyOfMd(start) + 1);
  const alt = raw?.alternative_quantile_window;
  return {
    start,
    end,
    widthDays,
    centerDate: str(raw?.center_date) ?? '',
    method: str(raw?.method) ?? '',
    crossYear,
    label: `${start} ~ ${end}`,
    alternativeQuantile:
      str(alt?.start) && str(alt?.end) ? { start: alt.start, end: alt.end } : null,
  };
}

function parsePattern(raw: any, dsSnapshot: string, issues: string[]): TimeObservationPattern | null {
  const pid = str(raw?.pattern_id);
  if (!pid) {
    issues.push('丢弃一条 pattern：缺少 pattern_id');
    return null;
  }
  if (!/^TOP-/.test(pid)) {
    issues.push(`${pid}：pattern_id 未使用 TOP- 命名空间`);
  }
  const window = parseWindow(raw?.typical_window, issues, pid);

  const observations: PatternObservation[] = Array.isArray(raw?.observations)
    ? raw.observations
        .map((o: any) => {
          const date = str(o?.date);
          const year = num(o?.year);
          const campaignId = str(o?.campaign_id);
          if (!date || !ISO_RE.test(date) || year === null || !campaignId) {
            issues.push(`${pid}：丢弃一条 observation（缺 year / date / campaign_id 或日期非法）`);
            return null;
          }
          const md = date.slice(5);
          return {
            year,
            date,
            md,
            campaignId,
            title: str(o?.title) ?? campaignId,
            kind: (o?.kind === 'research_candidate' ? 'research_candidate' : 'campaign') as
              | 'campaign'
              | 'research_candidate',
            inWindow:
              window === null
                ? null
                : (o?.in_typical_window ?? isMdInWindow(md, window.start, window.end)),
            timelineEntryId: timelineEntryId(campaignId, year),
          };
        })
        .filter((o: PatternObservation | null): o is PatternObservation => o !== null)
    : [];

  const rec = raw?.recurrence ?? {};
  const recurrence: PatternRecurrence = {
    matchedCount: num(rec.matched_count) ?? 0,
    eligibleYears: num(rec.eligible_years) ?? observations.length,
    matchedYears: Array.isArray(rec.matched_years)
      ? rec.matched_years.filter((y: unknown): y is number => typeof y === 'number')
      : [],
    missedYears: Array.isArray(rec.missed_years)
      ? rec.missed_years.filter((y: unknown): y is number => typeof y === 'number')
      : [],
    historicalRatio: num(rec.historical_ratio),
    label: str(rec.label) ?? '历史样本中的窗口复现情况（不是未来概率）',
  };

  const eligibility = asEligibility(raw?.timeline_eligibility);
  const declaredEligible = raw?.timeline_eligible === true;
  if (declaredEligible !== (eligibility === 'TIMELINE_ELIGIBLE')) {
    issues.push(`${pid}：timeline_eligible 与 timeline_eligibility 不一致（以 timeline_eligibility 为准）`);
  }
  if (eligibility === 'TIMELINE_ELIGIBLE' && window === null) {
    issues.push(`${pid}：声明可进入 Timeline 但没有窗口 → 降级为 RESEARCH_ONLY`);
  }
  const effectiveEligibility: TimelineEligibility =
    eligibility === 'TIMELINE_ELIGIBLE' && window === null ? 'RESEARCH_ONLY' : eligibility;

  const mech = raw?.mechanism ?? {};
  return {
    patternId: pid,
    sourcePatternId: str(raw?.source_pattern_id) ?? '—',
    patternType: asPatternType(raw?.pattern_type),
    title: str(raw?.title) ?? pid,
    description: str(raw?.description) ?? '',
    themeScope: str(raw?.theme_scope) ?? '未标注',
    themeKey: str(raw?.theme_key) ?? '',
    anchorType: str(raw?.anchor_type) ?? 'UNKNOWN',
    centerDate: str(raw?.center_date) ?? window?.start ?? '',
    window,
    observations,
    recurrence,
    stability: {
      status: str(raw?.stability?.status) ?? 'UNKNOWN',
      driftFlag: str(raw?.stability?.drift_flag),
      medianShiftDays: num(raw?.stability?.median_shift_days),
      note: str(raw?.stability?.note) ?? undefined,
    },
    dataQuality: {
      grade: str(raw?.data_quality?.grade) ?? 'UNKNOWN',
      note: str(raw?.data_quality?.note) ?? '',
    },
    researchStrength: str(raw?.research_strength?.grade) ?? 'UNKNOWN',
    status: str(raw?.status) ?? 'REJECTED',
    timelineEligibility: effectiveEligibility,
    timelineEligible: effectiveEligibility === 'TIMELINE_ELIGIBLE',
    eligibilityReason: str(raw?.timeline_eligibility_reason) ?? '',
    mechanism: {
      type: str(mech.type) ?? 'UNKNOWN',
      primary: str(mech.primary_mechanism) ?? 'UNKNOWN',
      note: str(mech.note) ?? '',
      isLunarDriven: mech.is_lunar_driven === true,
      lunarNote: str(mech.lunar_note) ?? '',
    },
    limitations: Array.isArray(raw?.limitations)
      ? raw.limitations.filter((x: unknown): x is string => typeof x === 'string')
      : [],
  };
}

/**
 * 解析 Time Observation Pattern Artifact（宽容解析，不因单条脏数据崩溃）。
 * 严格校验由生成器 `research/scripts/build_time_observation_patterns.py` 的自检负责。
 */
export function parseTimeObservationPatterns(raw: unknown): TimeObservationDataset {
  const issues: string[] = [];
  const obj = (raw ?? {}) as any;
  if (obj.artifact !== 'time_observation_patterns') {
    issues.push(`artifact 应为 time_observation_patterns，实际为 ${String(obj.artifact)}`);
  }
  const snapshotDate = str(obj.snapshot_date) ?? '';
  const list: TimeObservationPattern[] = Array.isArray(obj.patterns)
    ? obj.patterns
        .map((p: any) => parsePattern(p, snapshotDate, issues))
        .filter((p: TimeObservationPattern | null): p is TimeObservationPattern => p !== null)
    : [];

  const seen = new Set<string>();
  for (const p of list) {
    if (seen.has(p.patternId)) issues.push(`pattern_id 重复：${p.patternId}`);
    seen.add(p.patternId);
  }

  const lv = obj.label_vocabulary ?? {};
  return {
    artifact: 'time_observation_patterns',
    version: str(obj.artifact_version) ?? '0.1',
    snapshotDate,
    generatedAt: str(obj.generated_at) ?? undefined,
    labels: {
      window: str(lv.window) ?? DEFAULT_LABELS.window,
      recurrence: str(lv.recurrence) ?? DEFAULT_LABELS.recurrence,
      in_window: str(lv.in_window) ?? DEFAULT_LABELS.in_window,
      near_window: str(lv.near_window) ?? DEFAULT_LABELS.near_window,
      none: str(lv.none) ?? DEFAULT_LABELS.none,
      disclaimer: str(lv.disclaimer) ?? DEFAULT_LABELS.disclaimer,
    },
    patterns: list,
    issues,
  };
}

/* ================= 5. View Model ================= */

export interface TimeObservationView {
  patternId: string;
  sourcePatternId: string;
  title: string;
  patternTypeLabel: string;
  themeScope: string;
  windowLabel: string;
  window: PatternWindow;
  centerDate: string;

  proximity: WindowProximity;
  proximityLabel: string;
  /** 「今天距窗口还有 N 天」/「窗口内」等，纯日历口径 */
  distanceDays: number;

  /** 「历史样本中 5 / 7 个观测年份」——**不是**未来概率 */
  recurrenceLabel: string;
  matchedCount: number;
  eligibleYears: number;

  observations: PatternObservation[];
  /** 当年轨道上可见的观测（用于在时间轴上点出「这一年的起点落在哪」） */
  explanation: string;
  limitations: string[];
  disclaimer: string;

  /** 探索性标记（样本有限 / 未经人工核验）→ UI 必须显示 */
  exploratory: boolean;
  status: string;
  researchStrength: string;
  dataQualityGrade: string;
  driftFlag: string | null;
  /** 研究层给出的纳入理由（可审计） */
  eligibilityReason: string;
}

export interface TimeObservationCurrentSummary {
  /** 今天所处的模式（可能多个；§26：不人为只保留一个） */
  inWindow: TimeObservationView[];
  near: TimeObservationView[];
  /** 今天与任何窗口都无关时的空态文案（§27：允许「什么都没有」） */
  emptyNote: string | null;
  /** 已进入 Timeline 的窗口总数（用于说明「另有 N 条留在研究层」） */
  total: number;
  researchOnlyCount: number;
}

const STRENGTH_RANK: Record<string, number> = { A: 0, B: 1, C: 2, D: 3, UNKNOWN: 4 };
const QUALITY_RANK: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2, UNKNOWN: 3 };
const PROXIMITY_RANK: Record<WindowProximity, number> = {
  IN_WINDOW: 0,
  NEAR_WINDOW: 1,
  OUTSIDE: 2,
};

function viewOf(p: TimeObservationPattern, today: string, ds: TimeObservationDataset): TimeObservationView | null {
  if (!p.window) return null;
  const md = today.length >= 10 ? today.slice(5) : '';
  const proximity = proximityOf(md, p.window.start, p.window.end);
  const distanceDays = daysFromWindow(md, p.window.start, p.window.end);
  const exploratory = p.researchStrength !== 'A' || p.dataQuality.grade !== 'HIGH' || p.status !== 'STRONG_CANDIDATE';
  return {
    patternId: p.patternId,
    sourcePatternId: p.sourcePatternId,
    title: p.title,
    patternTypeLabel: PATTERN_TYPE_LABEL[p.patternType],
    themeScope: p.themeScope,
    windowLabel: p.window.label,
    window: p.window,
    centerDate: p.centerDate,
    proximity,
    proximityLabel: ds.labels[proximity === 'IN_WINDOW' ? 'in_window' : proximity === 'NEAR_WINDOW' ? 'near_window' : 'none'],
    distanceDays,
    recurrenceLabel: `${ds.labels.recurrence}：${p.recurrence.matchedCount} / ${p.recurrence.eligibleYears} 个观测年份`,
    matchedCount: p.recurrence.matchedCount,
    eligibleYears: p.recurrence.eligibleYears,
    observations: p.observations,
    explanation: p.description,
    limitations: p.limitations,
    disclaimer: ds.labels.disclaimer,
    exploratory,
    status: p.status,
    researchStrength: p.researchStrength,
    dataQualityGrade: p.dataQuality.grade,
    driftFlag: p.stability.driftFlag,
    eligibilityReason: p.eligibilityReason,
  };
}

/**
 * 排序（§25）：先按与今天的关系（窗口内 → 接近 → 较远），
 * 再按数据质量 → 稳定性 → 样本量。
 * **不产生、也不展示任何「推荐分」。**
 */
export function sortTimeObservationViews(
  views: TimeObservationView[],
  patterns: TimeObservationPattern[],
): TimeObservationView[] {
  const byId = new Map(patterns.map((p) => [p.patternId, p]));
  return [...views].sort((a, b) => {
    const d = PROXIMITY_RANK[a.proximity] - PROXIMITY_RANK[b.proximity];
    if (d !== 0) return d;
    const q = (QUALITY_RANK[a.dataQualityGrade] ?? 9) - (QUALITY_RANK[b.dataQualityGrade] ?? 9);
    if (q !== 0) return q;
    const sa = a.driftFlag === 'STABLE' ? 0 : a.driftFlag === 'MILD_DRIFT' ? 1 : 2;
    const sb = b.driftFlag === 'STABLE' ? 0 : b.driftFlag === 'MILD_DRIFT' ? 1 : 2;
    if (sa !== sb) return sa - sb;
    const na = byId.get(a.patternId)?.recurrence.eligibleYears ?? 0;
    const nb = byId.get(b.patternId)?.recurrence.eligibleYears ?? 0;
    if (na !== nb) return nb - na;
    const ra = STRENGTH_RANK[a.researchStrength] ?? 9;
    const rb = STRENGTH_RANK[b.researchStrength] ?? 9;
    if (ra !== rb) return ra - rb;
    return a.patternId < b.patternId ? -1 : 1;
  });
}

export interface TimeObservationLayerModel {
  /** 可进入 Timeline 展示的窗口（TIMELINE_ELIGIBLE 且窗口有效） */
  views: TimeObservationView[];
  /** 今天的关系摘要（可同时命中多条，§26） */
  current: TimeObservationCurrentSummary;
  /** 留在研究层 / 已拒绝的条数（UI 可轻量说明，不显示细节） */
  researchOnlyCount: number;
  rejectedCount: number;
  snapshotDate: string;
  disclaimer: string;
  windowLabel: string;
  recurrenceLabel: string;
  issues: string[];
}

/**
 * 构建 Timeline 时间型观察层的 View Model。
 *
 * @param dataset 解析后的 Artifact（缺省 → canonical；可注入测试数据）
 * @param today   A股市场日期基准（Asia/Shanghai）
 */
export function buildTimeObservationLayer(
  dataset: TimeObservationDataset = defaultTimeObservationDataset(),
  today: string,
): TimeObservationLayerModel {
  const eligiblePatterns = dataset.patterns.filter((p) => p.timelineEligible && p.window !== null);
  const views = sortTimeObservationViews(
    eligiblePatterns
      .map((p) => viewOf(p, today, dataset))
      .filter((v): v is TimeObservationView => v !== null),
    dataset.patterns,
  );

  const current: TimeObservationCurrentSummary = {
    inWindow: views.filter((v) => v.proximity === 'IN_WINDOW'),
    near: views.filter((v) => v.proximity === 'NEAR_WINDOW'),
    emptyNote:
      views.length === 0 || !views.some((v) => v.proximity !== 'OUTSIDE')
        ? dataset.labels.none
        : null,
    total: views.length,
    researchOnlyCount: dataset.patterns.filter((p) => p.timelineEligibility === 'RESEARCH_ONLY').length,
  };

  return {
    views,
    current,
    researchOnlyCount: current.researchOnlyCount,
    rejectedCount: dataset.patterns.filter((p) => p.timelineEligibility === 'REJECTED').length,
    snapshotDate: dataset.snapshotDate,
    disclaimer: dataset.labels.disclaimer,
    windowLabel: dataset.labels.window,
    recurrenceLabel: dataset.labels.recurrence,
    issues: dataset.issues,
  };
}

/* ================= 6. 数据入口 ================= */

/** canonical Artifact（`research/research/reports/time_observation_patterns_v0_1.json`） */
export function defaultTimeObservationDataset(): TimeObservationDataset {
  return parseTimeObservationPatterns(rawArtifact);
}

/** 解析结果（含解析告警，供 UI 透明展示） */
export function defaultTimeObservationParse(): TimeObservationDataset {
  return parseTimeObservationPatterns(rawArtifact);
}
