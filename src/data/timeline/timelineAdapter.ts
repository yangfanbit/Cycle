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
  ExportCampaignV1,
  TimelineCampaign,
  TimelineDataSource,
  TimelineEventPoint,
  TimelineExportV1,
  TimelinePhaseSegment,
  TimelineYearData,
} from './timelineTypes';
import { timelinePreviewExport } from './timelinePreview';

/**
 * Timeline Data Adapter：把两类来源映射成统一的 TimelineDataSource。
 *
 * - verified：生产数据（data/verified → src/data barrel 聚合 allCampaigns 等）。
 * - preview：Cycle-Research 导出（timeline_export_v1 兼容），本地 fixture 或
 *   未来导入的本地文件数据。**预览数据不是生产数据出口**：不写入 data/verified，
 *   不混入 allCampaigns。
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
      return theme ? { id: ct.theme_id, name: theme.name, role: ct.role } : null;
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
      const set = new Set<number>();
      for (const c of timeline) {
        set.add(Number(c.start.slice(0, 4)));
        set.add(Number(c.end.slice(0, 4)));
      }
      return [...set].sort((a, b) => a - b);
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

/* ---------------- export v1 → TimelineCampaign ---------------- */

export function exportCampaignToTimeline(c: ExportCampaignV1): TimelineCampaign {
  const status = c.research_status ?? 'preview';
  return {
    campaign_id: c.campaign_id,
    rule_id: c.rule_id,
    year: c.year,
    season_id: c.season_id,
    title: c.title,
    start: c.start_date,
    end: c.end_date,
    peak: c.peak_date ?? null,
    cross_year: c.start_date.slice(0, 4) !== c.end_date.slice(0, 4),
    status,
    conflicts: c.conflicts,
    early_signal: c.early_signal
      ? { start: c.early_signal.start_date, end: c.early_signal.end_date, label: c.early_signal.label }
      : null,
    phases: derivePhases({
      start: c.start_date,
      end: c.end_date,
      peak: c.peak_date ?? null,
      retracement_start: c.retracement_start ?? null,
    }),
    themes: c.themes.map((t) => ({ name: t.name, role: t.role })),
    securities: (c.securities ?? []).map((s) => ({ name: s.name, role: s.role })),
    description: c.description,
    sourceNote: `Cycle-Research 预览数据（${status}）——非正式历史事实`,
  };
}

/**
 * timeline_export_v1 兼容导入接口。
 * 仅支持本地生成的数据（fetch 传入已解析对象 / 本地 fixture），
 * 不做运行时网络请求——Cycle 保持静态 PWA。
 */
export function timelineSourceFromExportV1(data: TimelineExportV1): TimelineDataSource {
  const timeline = data.campaigns.map(exportCampaignToTimeline);
  return {
    kind: 'preview',
    years() {
      const set = new Set<number>();
      for (const c of timeline) {
        set.add(Number(c.start.slice(0, 4)));
        set.add(Number(c.end.slice(0, 4)));
      }
      return [...set].sort((a, b) => a - b);
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

/** 开发预览数据源：本地 fixture（Cycle-Research 已研究的 2022 / 2023 / 2024 案例） */
export function previewTimelineSource(): TimelineDataSource {
  return timelineSourceFromExportV1(timelinePreviewExport);
}
