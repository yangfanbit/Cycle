import {
  allCampaignSecurities,
  allCampaigns,
  events,
  rules,
  sourceById,
  themeById,
  themesOfCampaign,
} from '../index';
import type { HistoricalCampaign } from '../../models';
import { addDaysISO, diffDays, minISO, maxISO, resolveEventForYear } from '../../utils';
import type {
  ExportCandidateV1,
  ExportCampaignV1,
  ExportConflictV1,
  ExportResearchStatus,
  ExportSecurityV1,
  ExportSignalV1,
  TimelineCampaign,
  TimelineDataSource,
  TimelineEventPoint,
  TimelineExportV1,
  TimelinePhaseSegment,
  TimelineResearchEvent,
  TimelineYearData,
} from './timelineTypes';
import { timelineExportData } from './timelinePreview';
import { timelineYears, yearOf } from './yearCoverage';

/**
 * Timeline Data Adapter：把两类来源映射成统一的 TimelineDataSource。
 *
 * - verified：生产数据（data/verified → src/data barrel 聚合 allCampaigns 等）。
 * - preview：Cycle-Research 真实导出（timeline_export_v1，canonical Contract v1.0），
 *   经 validateTimelineExportV1 校验后消费。**预览数据不是生产数据出口**：
 *   不写入 data/verified，不混入 allCampaigns。
 *
 * UI（Timeline / App）只依赖 TimelineDataSource，未来 preview → provisional →
 * verified 的切换只改本层。
 */

/* ---------------- 生命周期分段 ---------------- */

/**
 * 由 start / peak / end / retracement_start 推导生命周期分段。
 * retracement_start 缺省时以 peak → end 中点近似（Adapter 层近似，仅用于渲染）。
 * 分段按序覆盖 start → end，不留空隙；异常输入会被钳制到合法区间。
 */
export function derivePhases(c: {
  start: string;
  end: string;
  peak?: string | null;
  retracement_start?: string | null;
}): TimelinePhaseSegment[] {
  const start = minISO(c.start, c.end);
  const end = maxISO(c.start, c.end);
  const peak =
    c.peak && c.peak >= start && c.peak <= end ? c.peak : null;
  if (!peak) {
    return [{ phase: 'main_rise', start, end }];
  }
  let retracementStart = c.retracement_start && c.retracement_start >= peak && c.retracement_start <= end
    ? c.retracement_start
    : addDaysISO(peak, Math.floor(diffDays(peak, end) / 2));
  if (retracementStart > end) retracementStart = end;
  return [
    { phase: 'main_rise', start, end: peak },
    { phase: 'retracement', start: peak, end: retracementStart },
    { phase: 'declining', start: retracementStart, end },
  ];
}

/** 行情标题的行业前缀（来自 Rule 的 base_sector，避免硬编码行业名） */
const ruleSector = new Map(rules.map((r) => [r.rule_id, r.base_sector]));

/* ---------------- 事件层（两个来源共用日历事件） ---------------- */

function timelineEventsForYear(year: number): TimelineEventPoint[] {
  const points: TimelineEventPoint[] = [];
  for (const ev of events) {
    const r = resolveEventForYear(ev, year);
    if (!r) continue;
    points.push({
      event_id: ev.event_id,
      name: ev.name,
      start: r.start,
      end: r.end,
      event_type: ev.event_type,
      description: ev.description,
      approximate: r.approximate,
      source: 'Cycle 事件日历（data/candidate/events.ts）',
    });
  }
  return points;
}

/* ---------------- verified（生产）数据源 ---------------- */

function verifiedCampaignToTimeline(c: HistoricalCampaign): TimelineCampaign {
  const themeRels = themesOfCampaign(c.campaign_id);
  const themes = themeRels
    .map((ct) => {
      const theme = themeById.get(ct.theme_id);
      return theme ? { name: theme.name, role: ct.role } : null;
    })
    .filter((t): t is NonNullable<typeof t> => t !== null);
  const mainTheme = themes.find((t) => t.role === 'main');
  const securities = allCampaignSecurities
    .filter((cs) => cs.campaign_id === c.campaign_id)
    .map((cs) => ({ name: cs.security_id, role: cs.role }));
  const source = sourceById.get(c.source_id);
  const sector = ruleSector.get(c.rule_id) ?? '行情';
  return {
    campaign_id: c.campaign_id,
    kind: 'campaign',
    rule_id: c.rule_id,
    season_id: c.season_id,
    year: c.campaign_year,
    title: mainTheme ? `${sector} · ${mainTheme.name}` : `${sector} · ${c.season_id}`,
    start: c.start_date,
    end: c.end_date,
    peak: c.peak_date ?? null,
    cross_year: c.cross_year,
    status: 'verified',
    early_signal: null,
    phases: derivePhases({
      start: c.start_date,
      end: c.end_date,
      peak: c.peak_date ?? null,
      retracement_start: null, // 生产数据无此字段：Adapter 以 peak→end 中点近似
    }),
    themes,
    securities,
    events: [],
    signals: [],
    description: c.description,
    sourceNote: source ? `${source.title}（${source.source_type}）` : c.source_id,
  };
}

/**
 * 生产数据源：verified（allCampaigns = data/verified 聚合）。
 * campaigns 参数仅供测试注入，生产调用不传。
 */
export function verifiedTimelineSource(
  campaignList: HistoricalCampaign[] = allCampaigns,
): TimelineDataSource {
  const timeline = campaignList.map(verifiedCampaignToTimeline);
  return {
    kind: 'verified',
    years() {
      // 统一规则（V1.9.1 Year Coverage）：Campaign 覆盖年份 = start 年 → end 年**连续**
      // （含中间年份）。旧实现只收集起止年份 → 跨年 Campaign 中间年份行缺失（F-MED-5）。
      return timelineYears(timeline.map((c) => ({ start: c.start, end: c.end })));
    },
    yearData(year: number): TimelineYearData {
      const yStart = `${year}-01-01`;
      const yEnd = `${year}-12-31`;
      return {
        year,
        campaigns: timeline.filter((c) => c.start <= yEnd && c.end >= yStart),
        events: timelineEventsForYear(year),
      };
    },
  };
}

/* ---------------- Contract 校验（只验证 Cycle 实际消费的部分） ---------------- */

const TOP_LEVEL_KEYS = [
  'contract',
  'timeline_export_version',
  'generated_at',
  'source_commit',
  'project',
  'rules',
  'signals',
  'campaigns',
  'research_candidates',
  'events',
  'securities',
] as const;

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;
const SIGNAL_TYPES = new Set(['EARLY_SIGNAL', 'THEME_FORMING', 'CONFIRMATION_CANDIDATE']);
const FORMAL_RESEARCH_STATUS: Record<string, string> = {
  PROVISIONAL: 'provisional',
  CONFLICT: 'conflict',
  VERIFIED: 'verified',
};

/**
 * 校验 timeline_export_v1（v1.0 canonical Contract）中 Cycle 实际消费的部分。
 * 不在 Cycle 端重写完整 Research Validator（scripts/validate_timeline_export.py 是接口守门人）。
 * 返回问题清单；空数组 = 通过。
 */
export function validateTimelineExportV1(data: unknown): string[] {
  const issues: string[] = [];
  if (typeof data !== 'object' || data === null || Array.isArray(data)) {
    return ['顶层必须是 JSON 对象'];
  }
  const obj = data as Record<string, unknown>;

  // 1-2. 顶层白名单（未知字段拒绝；旧字段 export_version / source_project / purpose 已废弃）
  const missingTop: string[] = [];
  for (const key of Object.keys(obj)) {
    if (!(TOP_LEVEL_KEYS as readonly string[]).includes(key)) {
      issues.push(`未知顶层字段 "${key}"（v1.0 白名单外；export_version / source_project / purpose 等旧字段已废弃）`);
    }
  }
  for (const key of TOP_LEVEL_KEYS) {
    if (!(key in obj)) missingTop.push(key);
  }
  if (missingTop.length > 0) {
    // 顶层结构不完整时不再深入（version 等检查依赖字段存在）
    for (const key of missingTop) issues.push(`缺少顶层字段 "${key}"`);
    return issues;
  }

  // 3. version / contract
  if (obj.contract !== 'timeline_export') issues.push('contract 必须为 "timeline_export"');
  if (obj.timeline_export_version !== '1.0') issues.push('timeline_export_version 必须为 "1.0"');

  const arr = (name: string): unknown[] => {
    const v = obj[name];
    if (!Array.isArray(v)) {
      issues.push(`"${name}" 必须为数组`);
      return [];
    }
    return v;
  };

  const campaigns = arr('campaigns');
  const candidates = arr('research_candidates');
  const signals = arr('signals');
  const events = arr('events');
  const securities = arr('securities');
  const ruleRows = arr('rules');

  // 4. campaigns：必填字段 + 状态一致性 + conflict ⇔ conflicts
  const campaignIds = new Set<string>();
  campaigns.forEach((c, i) => {
    const row = c as Record<string, unknown>;
    const tag = `campaigns[${i}]`;
    for (const f of ['campaign_id', 'rule_id', 'year', 'start_date', 'end_date', 'status', 'research_status', 'themes', 'event_ids', 'security_ids', 'conflicts']) {
      if (!(f in row)) issues.push(`${tag} 缺少必填字段 "${f}"`);
    }
    if (typeof row.campaign_id !== 'string' || !row.campaign_id) return;
    campaignIds.add(row.campaign_id);
    const rs = row.research_status as string;
    const expected = FORMAL_RESEARCH_STATUS[rs];
    if (!expected) {
      issues.push(`${tag}（${row.campaign_id}）research_status "${rs}" 不允许出现在正式 Campaign（不编造）`);
    } else if (row.status !== expected) {
      issues.push(`${tag}（${row.campaign_id}）status "${row.status}" 与 research_status "${rs}" 不一致`);
    }
    const conflicts = row.conflicts;
    if (rs === 'CONFLICT' && (!Array.isArray(conflicts) || conflicts.length === 0)) {
      issues.push(`${tag}（${row.campaign_id}）research_status=CONFLICT 必须携带 conflicts（candidate_a/b）`);
    }
    if (rs !== 'CONFLICT' && Array.isArray(conflicts) && conflicts.length > 0) {
      issues.push(`${tag}（${row.campaign_id}）非 CONFLICT 不应携带 conflicts`);
    }
  });

  // 5. research_candidates：必填字段 + 无生产 status + 不得进入 formal campaigns
  const candidateIds = new Set<string>();
  candidates.forEach((c, i) => {
    const row = c as Record<string, unknown>;
    const tag = `research_candidates[${i}]`;
    for (const f of ['campaign_id', 'rule_id', 'year', 'title', 'start_date', 'research_status', 'themes', 'event_ids', 'security_ids', 'conflicts']) {
      if (!(f in row)) issues.push(`${tag} 缺少必填字段 "${f}"`);
    }
    if ('status' in row) {
      issues.push(`${tag} 候选不得携带生产 status 字段（候选只有 research_status）`);
    }
    if (typeof row.campaign_id === 'string' && row.campaign_id) {
      if (campaignIds.has(row.campaign_id)) {
        issues.push(`${tag}（${row.campaign_id}）与 formal campaigns ID 冲突：候选不得进入正式 Campaign`);
      }
      candidateIds.add(row.campaign_id);
    }
  });

  // 6. events：唯一 ID + 日期格式 + 归属回指
  const eventIds = new Set<string>();
  events.forEach((e, i) => {
    const row = e as Record<string, unknown>;
    const tag = `events[${i}]`;
    if (typeof row.event_id !== 'string' || !row.event_id) return;
    if (eventIds.has(row.event_id)) issues.push(`${tag} event_id "${row.event_id}" 重复`);
    eventIds.add(row.event_id);
    if (typeof row.date !== 'string' || !ISO_DATE.test(row.date)) issues.push(`${tag}（${row.event_id}）date 必须为 ISO 日期`);
    if (row.campaign_id != null && !campaignIds.has(row.campaign_id as string)) {
      issues.push(`${tag}（${row.event_id}）campaign_id "${row.campaign_id}" 不存在`);
    }
    if (row.research_candidate_id != null && !candidateIds.has(row.research_candidate_id as string)) {
      issues.push(`${tag}（${row.event_id}）research_candidate_id "${row.research_candidate_id}" 不存在`);
    }
  });

  // 7. signals：归属 XOR（campaign_id XOR research_candidate_id）+ 引用存在
  signals.forEach((s, i) => {
    const row = s as Record<string, unknown>;
    const tag = `signals[${i}]`;
    if (!SIGNAL_TYPES.has(row.type as string)) issues.push(`${tag} type "${row.type}" 不在枚举内`);
    const hasCampaign = row.campaign_id != null;
    const hasCandidate = row.research_candidate_id != null;
    if (hasCampaign === hasCandidate) {
      issues.push(`${tag} 归属必须是 campaign_id XOR research_candidate_id（二选一）`);
    } else if (hasCampaign && !campaignIds.has(row.campaign_id as string)) {
      issues.push(`${tag} campaign_id "${row.campaign_id}" 不存在`);
    } else if (hasCandidate && !candidateIds.has(row.research_candidate_id as string)) {
      issues.push(`${tag} research_candidate_id "${row.research_candidate_id}" 不存在`);
    }
  });

  // 8. securities：必须知道属于谁（每行恰好一个 owner）+ 回指存在
  securities.forEach((s, i) => {
    const row = s as Record<string, unknown>;
    const tag = `securities[${i}]`;
    const hasCampaign = row.campaign_id != null;
    const hasCandidate = row.research_candidate_id != null;
    if (hasCampaign === hasCandidate) {
      issues.push(`${tag}（${row.security_id}）必须归属恰好一个 owner（campaign_id 或 research_candidate_id）`);
    } else if (hasCampaign && !campaignIds.has(row.campaign_id as string)) {
      issues.push(`${tag}（${row.security_id}）campaign_id "${row.campaign_id}" 不存在`);
    } else if (hasCandidate && !candidateIds.has(row.research_candidate_id as string)) {
      issues.push(`${tag}（${row.security_id}）research_candidate_id "${row.research_candidate_id}" 不存在`);
    }
  });

  // 9. campaign / candidate 引用完整性（event_ids / security_ids 必须可解析）
  const securitiesByOwner = new Map<string, Set<string>>();
  securities.forEach((s) => {
    const row = s as ExportSecurityV1;
    const owner = row.campaign_id ?? row.research_candidate_id;
    if (!owner) return;
    if (!securitiesByOwner.has(owner)) securitiesByOwner.set(owner, new Set());
    securitiesByOwner.get(owner)!.add(row.security_id);
  });
  const checkRefs = (row: Record<string, unknown>, id: string, kind: string) => {
    for (const eid of (row.event_ids as string[]) ?? []) {
      if (!eventIds.has(eid)) issues.push(`${kind} ${id} 引用的 event_id "${eid}" 不存在`);
    }
    const owned = securitiesByOwner.get(id) ?? new Set<string>();
    for (const sid of (row.security_ids as string[]) ?? []) {
      if (!owned.has(sid)) issues.push(`${kind} ${id} 引用的 security_id "${sid}" 无归属行（必须 (security_id, owner) 成对）`);
    }
  };
  campaigns.forEach((c) => {
    const row = c as Record<string, unknown>;
    if (typeof row.campaign_id === 'string') checkRefs(row, row.campaign_id, 'campaign');
  });
  candidates.forEach((c) => {
    const row = c as Record<string, unknown>;
    if (typeof row.campaign_id === 'string') checkRefs(row, row.campaign_id, 'research_candidate');
  });

  // rules：rule_id 唯一（Cycle 用于标题前缀）
  const ruleIds = new Set<string>();
  ruleRows.forEach((r, i) => {
    const row = r as Record<string, unknown>;
    if (typeof row.rule_id !== 'string' || !row.rule_id) {
      issues.push(`rules[${i}] 缺少 rule_id`);
    } else if (ruleIds.has(row.rule_id)) {
      issues.push(`rules[${i}] rule_id "${row.rule_id}" 重复`);
    } else {
      ruleIds.add(row.rule_id);
    }
  });

  return issues;
}

/* ---------------- export v1 → TimelineCampaign ---------------- */

/** 正式 Campaign：research_status（大写研究层）→ Timeline 状态（小写生产兼容） */
function formalStatus(rs: ExportResearchStatus): TimelineCampaign['status'] {
  if (rs === 'VERIFIED') return 'verified';
  if (rs === 'CONFLICT') return 'conflict';
  if (rs === 'PROVISIONAL') return 'provisional';
  throw new Error(`正式 Campaign 不允许 research_status=${rs}（不编造）`);
}

/** Research Candidate：永不映射 verified；PROVISIONAL → preview */
function candidateStatus(rs: ExportResearchStatus): TimelineCampaign['status'] {
  return rs === 'CONFLICT' ? 'conflict' : 'preview';
}

/* ---------------- Conflict 边界候选（视图辅助，不改 TimelineCampaign 模型） ---------------- */

export interface ConflictBoundaryCandidates {
  /** start 存在分歧时的候选日期（升序去重；null = 无分歧） */
  startCandidates: string[] | null;
  peakCandidates: string[] | null;
  endCandidates: string[] | null;
}

/**
 * 从 campaign.conflicts 推导 start / peak / end 的 A/B 候选日期。
 * 仅 status = conflict 时返回非空；候选按日期升序去重（不做任何取舍——
 * 视觉必须同时呈现双方，避免"自动选择 Candidate A/B"）。
 */
export function getConflictBoundaryCandidates(
  c: Pick<TimelineCampaign, 'status' | 'conflicts'>,
): ConflictBoundaryCandidates {
  const empty: ConflictBoundaryCandidates = {
    startCandidates: null,
    peakCandidates: null,
    endCandidates: null,
  };
  if (c.status !== 'conflict' || !c.conflicts || c.conflicts.length === 0) return empty;
  const pick = (field: string): string[] | null => {
    const dates = c
      .conflicts!.filter((x) => x.field === field)
      .flatMap((x) => [x.candidate_a.date, x.candidate_b.date]);
    if (dates.length === 0) return null;
    return [...new Set(dates)].sort();
  };
  return {
    startCandidates: pick('start_date'),
    peakCandidates: pick('peak_date'),
    endCandidates: pick('end_date'),
  };
}

/* ---------------- V1.7：冲突分级 + Peak Window + 驱动因素 + 同周期查询 ---------------- */

/** 轻微分歧阈值：候选间隔 ≤ 10 天视为同一窗口（不画大型 Conflict 视觉） */
export const MINOR_CONFLICT_THRESHOLD_DAYS = 10;

/** 正常峰值窗口半宽：peak ± 7 天（Phase Window 优先于精确日期展示） */
export const PEAK_WINDOW_HALF_DAYS = 7;

/**
 * 冲突分级：
 * - minor：候选间隔 ≤ 阈值（同一 Phase Window 内，如 07-29 vs 08-05）→ 显示窗口，保留详情 A/B；
 * - major：间隔超阈值（跨月份 / 影响生命周期判断，如 04-27 vs 05-23）→ ⚠ Conflict 大型视觉。
 */
export function conflictSeverity(c: ExportConflictV1): 'minor' | 'major' {
  const gap = Math.abs(diffDays(c.candidate_a.date, c.candidate_b.date));
  return gap <= MINOR_CONFLICT_THRESHOLD_DAYS ? 'minor' : 'major';
}

export interface PeakWindow {
  start: string;
  end: string;
  /** 是否为研究分歧窗口（由候选 A/B 构成） */
  disputed: boolean;
}

/**
 * Peak Window（时间轴优先显示窗口而非单一精确日期）：
 * - 轻微峰值冲突（≤ 阈值）：候选 A → B 构成窗口（disputed）；
 * - 严重峰值冲突（> 阈值）：返回 null（由双候选标记 ▲A/▲B 表达）；
 * - Research V1.7 lifecycle PEAK 阶段为真实区间（DATE_WINDOW，start < end）时直接采用；
 * - 其余（EXACT_DATE 单日或无 lifecycle）：peak ± 7 天近似。
 */
export function peakWindowOf(
  c: Pick<TimelineCampaign, 'peak' | 'status' | 'conflicts' | 'lifecycle'>,
): PeakWindow | null {
  const peakConflict =
    c.status === 'conflict' ? (c.conflicts ?? []).find((x) => x.field === 'peak_date') : undefined;
  if (peakConflict) {
    if (conflictSeverity(peakConflict) === 'major') return null;
    return {
      start: minISO(peakConflict.candidate_a.date, peakConflict.candidate_b.date),
      end: maxISO(peakConflict.candidate_a.date, peakConflict.candidate_b.date),
      disputed: true,
    };
  }
  const stage = (c.lifecycle ?? []).find((x) => x.stage === 'PEAK');
  if (stage && stage.start < stage.end) {
    return { start: stage.start, end: stage.end, disputed: false };
  }
  if (!c.peak) return null;
  return {
    start: addDaysISO(c.peak, -PEAK_WINDOW_HALF_DAYS),
    end: addDaysISO(c.peak, PEAK_WINDOW_HALF_DAYS),
    disputed: false,
  };
}

/** 驱动因素四问（Research V1.7 人工归因优先；缺失时基于研究事件时间归组；每组最多 3 个标签） */
export interface CampaignDrivers {
  /** 为什么启动？ */
  start: string[];
  /** 为什么加速？ */
  accelerate: string[];
  /** 为什么转折？ */
  turn: string[];
  /** 为什么结束？ */
  end: string[];
}

const DRIVER_ROLE_WEIGHT: Record<string, number> = {
  trigger: 0,
  catalyst: 1,
  follow_up: 2,
  context: 3,
};

/**
 * 从 Campaign 关联研究事件推导"为什么启动 / 加速 / 转折 / 结束"。
 * Research V1.7 导出携带 drivers（研究层人工归因）时优先采用（原样展示，每组最多 3 条，
 * 不编造、不解读）；无 drivers 字段（生产 verified / 旧导出）时按事件时间归组：
 * 事件按时间顺序归组（每个事件只进最先匹配的组）：
 * - 启动：[start-30, start+15]；
 * - 加速：(start+15, peak-7]（无 peak 时用区间中点近似分界）；
 * - 转折：[peak-10, peak+10]；
 * - 结束：[end-25, end+7]（openEnded 候选无结束 → 不归组）。
 * 无事件落入的组返回空数组（UI 显示"暂无可靠归因"，不编造）。
 */
export interface DriverGroupBounds {
  start: readonly [string, string];
  accelerate: readonly [string, string];
  turn: readonly [string, string];
  /** openEnded 候选无结束 → null（不归组） */
  end: readonly [string, string] | null;
  /** 无 peak 时用于近似转折位置的中点（**仅归组用途**，不对外展示为精确日期） */
  turnPivot: string;
}

/**
 * `campaignDrivers()` 使用的时间归组窗口（**语义与既有实现完全一致，仅抽出以便复用**）。
 *
 * 供 Product 层在同一套窗口下把「单个事件」映射到唯一的归组阶段
 * （`Historical Evidence Timeline`）；**不改变任何归组规则**。
 */
export function driverGroupBounds(
  c: Pick<TimelineCampaign, 'start' | 'peak' | 'end' | 'openEnded'>,
): DriverGroupBounds {
  const turnPivot = c.peak ?? addDaysISO(c.start, Math.floor(diffDays(c.start, c.end) / 2));
  return {
    start: [addDaysISO(c.start, -30), addDaysISO(c.start, 15)],
    accelerate: [addDaysISO(c.start, 15), addDaysISO(turnPivot, -7)],
    turn: [addDaysISO(turnPivot, -10), addDaysISO(turnPivot, 10)],
    end: c.openEnded ? null : [addDaysISO(c.end, -25), addDaysISO(c.end, 7)],
    turnPivot,
  };
}

export function campaignDrivers(
  c: Pick<TimelineCampaign, 'start' | 'peak' | 'end' | 'openEnded' | 'events' | 'drivers'>,
): CampaignDrivers {
  if (c.drivers) {
    const cap = (xs: string[] | undefined): string[] => (xs ?? []).slice(0, 3);
    return {
      start: cap(c.drivers.start),
      accelerate: cap(c.drivers.accelerator),
      turn: cap(c.drivers.turning),
      end: cap(c.drivers.ending),
    };
  }
  type Ev = { name: string; date: string; role?: string | null };
  const groups: Record<keyof CampaignDrivers, Ev[]> = {
    start: [],
    accelerate: [],
    turn: [],
    end: [],
  };
  const bounds = driverGroupBounds(c);
  const inRange = (d: string, r: readonly [string, string]) => r[0] <= d && d <= r[1];
  for (const ev of c.events) {
    if (inRange(ev.date, bounds.start)) groups.start.push(ev);
    else if (inRange(ev.date, bounds.accelerate)) groups.accelerate.push(ev);
    else if (inRange(ev.date, bounds.turn)) groups.turn.push(ev);
    else if (bounds.end && inRange(ev.date, bounds.end)) groups.end.push(ev);
    // 其余事件不归组（避免牵强归因）
  }
  // 每组最多 3 个标签，trigger / catalyst 优先
  const top = (evs: Ev[]): string[] =>
    [...evs]
      .sort(
        (a, b) =>
          (DRIVER_ROLE_WEIGHT[a.role ?? ''] ?? 9) - (DRIVER_ROLE_WEIGHT[b.role ?? ''] ?? 9),
      )
      .slice(0, 3)
      .map((e) => e.name);
  return {
    start: top(groups.start),
    accelerate: top(groups.accelerate),
    turn: top(groups.turn),
    end: top(groups.end),
  };
}

/** 历史同周期窗口：选中月份 m → [m-1 月 15 日, m+1 月 15 日]（两个月宽，如 9 月 → 08-15 ~ 10-15） */
export function samePeriodWindow(year: number, month: number): { start: string; end: string } {
  const midMonth = (y: number, m: number, day: number) => `${y}-${String(m).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  let prevY = year;
  let prevM = month - 1;
  if (prevM === 0) {
    prevM = 12;
    prevY -= 1;
  }
  let nextY = year;
  let nextM = month + 1;
  if (nextM === 13) {
    nextM = 1;
    nextY += 1;
  }
  return { start: midMonth(prevY, prevM, 15), end: midMonth(nextY, nextM, 15) };
}

export interface SamePeriodYear {
  year: number;
  /** 与同周期窗口相交的 Campaign（正式 + Research Candidate） */
  campaigns: TimelineCampaign[];
}

/**
 * 历史同周期查看：各年份在选中月份窗口内出现过的 Campaign 列表。
 * 仅做日期相交匹配（列表视图，不是统计模型 / 相似度评分）。
 */
export function samePeriodCampaigns(source: TimelineDataSource, month: number): SamePeriodYear[] {
  return source.years().map((year) => {
    const win = samePeriodWindow(year, month);
    const campaigns = source
      .yearData(year)
      .campaigns.filter((c) => c.start <= win.end && c.end >= win.start);
    return { year, campaigns };
  });
}

function mainThemeName(themes: { name: string; role?: string | null }[]): string | null {
  return themes.find((t) => t.role === 'main')?.name ?? themes[0]?.name ?? null;
}

interface ExportContext {
  data: TimelineExportV1;
  ruleBase: Map<string, string>;
  eventById: Map<string, TimelineResearchEvent>;
  securitiesByOwner: Map<string, ExportSecurityV1[]>;
  signalsByCampaign: Map<string, ExportSignalV1[]>;
  signalsByCandidate: Map<string, ExportSignalV1[]>;
}

function buildContext(data: TimelineExportV1): ExportContext {
  const ruleBase = new Map(data.rules.map((r) => [r.rule_id, r.base_pattern ?? r.rule_id]));
  const eventById = new Map<string, TimelineResearchEvent>(
    data.events.map((e) => [e.event_id, { ...e }]),
  );
  const securitiesByOwner = new Map<string, ExportSecurityV1[]>();
  for (const s of data.securities) {
    const owner = s.campaign_id ?? s.research_candidate_id;
    if (!owner) continue;
    if (!securitiesByOwner.has(owner)) securitiesByOwner.set(owner, []);
    securitiesByOwner.get(owner)!.push(s);
  }
  const signalsByCampaign = new Map<string, ExportSignalV1[]>();
  const signalsByCandidate = new Map<string, ExportSignalV1[]>();
  for (const s of data.signals) {
    if (s.campaign_id != null) {
      if (!signalsByCampaign.has(s.campaign_id)) signalsByCampaign.set(s.campaign_id, []);
      signalsByCampaign.get(s.campaign_id)!.push(s);
    } else if (s.research_candidate_id != null) {
      if (!signalsByCandidate.has(s.research_candidate_id)) signalsByCandidate.set(s.research_candidate_id, []);
      signalsByCandidate.get(s.research_candidate_id)!.push(s);
    }
  }
  return { data, ruleBase, eventById, securitiesByOwner, signalsByCampaign, signalsByCandidate };
}

/** 正式 Campaign → TimelineCampaign（Timeline UI 不需要全部 Research 字段） */
function formalCampaignToTimeline(c: ExportCampaignV1, ctx: ExportContext): TimelineCampaign {
  const status = formalStatus(c.research_status);
  const securities = (ctx.securitiesByOwner.get(c.campaign_id) ?? []).map((s) => ({
    name: s.name,
    ticker: s.ticker,
    role: s.role,
  }));
  const events = c.event_ids
    .map((id) => ctx.eventById.get(id))
    .filter((e): e is TimelineResearchEvent => e != null)
    .map((e) => ({ name: e.name, date: e.date, event_type: e.event_type, role: e.role }));
  const signals = (ctx.signalsByCampaign.get(c.campaign_id) ?? []).map((s) => ({
    type: s.type,
    date: s.date,
    confidence: s.confidence,
  }));
  // Early Signal 只取早于正式起点的 EARLY_SIGNAL（与 start 重合的信号不渲染为前置条）
  const early = (ctx.signalsByCampaign.get(c.campaign_id) ?? []).find(
    (s) => s.type === 'EARLY_SIGNAL' && s.date < c.start_date,
  );
  const base = ctx.ruleBase.get(c.rule_id) ?? '行情';
  const main = mainThemeName(c.themes);
  return {
    campaign_id: c.campaign_id,
    kind: 'campaign',
    rule_id: c.rule_id,
    season_id: String(c.year),
    year: c.year,
    title: main ? `${base} · ${main}` : `${base} · ${c.campaign_id}`,
    start: c.start_date,
    end: c.end_date,
    peak: c.peak_date,
    cross_year: c.start_date.slice(0, 4) !== c.end_date.slice(0, 4),
    status,
    conflicts: c.conflicts.length > 0 ? c.conflicts : undefined,
    early_signal: early
      ? { start: early.date, end: c.start_date, label: `Research Early Signal（${early.confidence}）` }
      : null,
    // first_decline_date 作回撤起点；缺省以 peak→end 中点近似（仅渲染）
    phases: derivePhases({
      start: c.start_date,
      end: c.end_date,
      peak: c.peak_date,
      retracement_start: c.first_decline_date ?? null,
    }),
    // 题材透传：theme_type 为导出既有字段（契约 §11 声明），用于 Macro Theme 层级推导
    themes: c.themes.map((t) => ({
      name: t.name,
      role: t.role ?? undefined,
      theme_type: t.theme_type ?? undefined,
    })),
    // Theme Cycle（research metadata 透传；不推断）
    theme_cycle_id: c.theme_cycle_id ?? null,
    securities,
    events,
    signals,
    // Research V1.7 新增字段透传（lifecycle 供 Peak Window / drivers 供详情四问消费）
    lifecycle: c.lifecycle,
    drivers: c.drivers,
    description: c.notes ?? undefined,
    sourceNote: `Cycle-Research timeline_export_v1（commit ${ctx.data.source_commit.slice(0, 7)}，${status}）——非正式历史事实`,
  };
}

/** Research Candidate → TimelineCampaign（kind = candidate，明显区别于正式 Campaign） */
function candidateToTimeline(rc: ExportCandidateV1, ctx: ExportContext): TimelineCampaign {
  const status = candidateStatus(rc.research_status);
  const openEnded = rc.end_date == null;
  const end = rc.end_date ?? `${rc.year}-12-31`;
  const securities = (ctx.securitiesByOwner.get(rc.campaign_id) ?? []).map((s) => ({
    name: s.name,
    ticker: s.ticker,
    role: s.role,
  }));
  const events = rc.event_ids
    .map((id) => ctx.eventById.get(id))
    .filter((e): e is TimelineResearchEvent => e != null)
    .map((e) => ({ name: e.name, date: e.date, event_type: e.event_type, role: e.role }));
  const signals = (ctx.signalsByCandidate.get(rc.campaign_id) ?? []).map((s) => ({
    type: s.type,
    date: s.date,
    confidence: s.confidence,
  }));
  const earlyDate =
    rc.early_signal ??
    (ctx.signalsByCandidate.get(rc.campaign_id) ?? []).find((s) => s.type === 'EARLY_SIGNAL')?.date ??
    null;
  return {
    campaign_id: rc.campaign_id,
    kind: 'candidate',
    rule_id: rc.rule_id,
    season_id: String(rc.year),
    year: rc.year,
    title: rc.title,
    start: rc.start_date,
    end,
    openEnded,
    peak: rc.peak_date,
    cross_year: rc.start_date.slice(0, 4) !== end.slice(0, 4),
    status,
    conflicts: rc.conflicts.length > 0 ? rc.conflicts : undefined,
    early_signal: earlyDate && earlyDate < rc.start_date
      ? { start: earlyDate, end: rc.start_date, label: 'Research Early Signal' }
      : null,
    phases: derivePhases({ start: rc.start_date, end, peak: rc.peak_date, retracement_start: null }),
    // 题材透传：theme_type 为导出既有字段（契约 §11 声明），用于 Macro Theme 层级推导
    themes: rc.themes.map((t) => ({
      name: t.name,
      role: t.role ?? undefined,
      theme_type: t.theme_type ?? undefined,
    })),
    // Theme Cycle（research metadata 透传；不推断）
    theme_cycle_id: rc.theme_cycle_id ?? null,
    securities,
    events,
    signals,
    // Research V1.7 新增字段透传（候选同样携带 lifecycle / drivers）
    lifecycle: rc.lifecycle,
    drivers: rc.drivers,
    description: rc.notes ?? undefined,
    sourceNote: `Cycle-Research Research Candidate（commit ${ctx.data.source_commit.slice(0, 7)}）——未达正式 Campaign 门槛，非正式历史事实`,
  };
}

/**
 * timeline_export_v1（canonical v1.0）→ preview 数据源。
 * 仅支持本地生成的数据（静态 import / 已解析对象），不做运行时网络请求——静态 PWA。
 * 数据非法时抛错（含校验问题清单）。
 */
export function fromTimelineExportV1(data: TimelineExportV1): TimelineDataSource {
  const issues = validateTimelineExportV1(data);
  if (issues.length > 0) {
    throw new Error(`timeline_export_v1 校验失败（${issues.length} 项）：\n- ${issues.join('\n- ')}`);
  }
  const ctx = buildContext(data);
  const formal = data.campaigns.map((c) => formalCampaignToTimeline(c, ctx));
  const candidates = data.research_candidates.map((rc) => candidateToTimeline(rc, ctx));
  // 正式 Campaign 与 Research Candidate 是并列来源：统一进入 yearData.campaigns，
  // 以 kind 区分（Candidate 不进入生产 allCampaigns / campaignById —— 由数据隔离保证）
  const all = [...formal, ...candidates].sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0));

  return {
    kind: 'preview',
    years() {
      // 统一规则（V1.9.1 Year Coverage）：Campaign / Research Candidate 覆盖年份
      // = start 年 → end 年**连续**（含中间年份）——与 verified 源同一规则、同一 helper。
      // 另并入研究事件年份：保留「2018 反例年份」（无 Campaign 但有历史事件）。UI 不硬编码年份。
      return timelineYears(
        all.map((c) => ({ start: c.start, end: c.end })),
        data.events.map((ev) => yearOf(ev.date)),
      );
    },
    yearData(year: number): TimelineYearData {
      const yStart = `${year}-01-01`;
      const yEnd = `${year}-12-31`;
      return {
        year,
        campaigns: all.filter((c) => c.start <= yEnd && c.end >= yStart),
        events: timelineEventsForYear(year),
        researchEvents: data.events.filter((ev) => ev.date.startsWith(`${year}-`)),
      };
    },
  };
}

/** 开发预览数据源：Cycle-Research 真实导出（src/data/timeline/data/timeline_export_v1.json） */
export function previewTimelineSource(): TimelineDataSource {
  return fromTimelineExportV1(timelineExportData);
}
