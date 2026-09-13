/**
 * V1.8.1 主题级历史机会视图 —— 主题行（TimelineThemeRow）Adapter。
 *
 * 回答的问题：「历史上这个时间窗口，出现过哪些【主题】，各年分别处于什么阶段？」
 *
 * 层级关系（不得混淆）：
 *   Theme（主主题） → Campaign / Research Candidate（独立行情，可多条同主题）
 *   —— 一行 = 一个主主题；明细仍逐条展示独立 Campaign，不做合并。
 *
 * 严格边界：
 *   - TimelineThemeRow 是【纯 UI / Adapter 视图概念】，不是数据库实体：
 *     不落库、不进 src/models/、不改 schema.sql、不引入 theme_cycles / theme_relations。
 *   - 主题信息完全来自导出数据的既有 themes 字段（name / role）；不新建主题、不改导出。
 *   - 日期口径完全复用 samePeriodCampaigns()（内部即 samePeriodWindow），不另造日期逻辑。
 *   - 阶段口径复用 currentTimeLens 的 historicalPhasesInWindow()（同一套"当年窗口内阶段"语义）。
 *   - 判断不出来时不编造：无 theme → 归入"未标注主题"，无 lifecycle → 阶段未标注。
 */

import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import { samePeriodCampaigns, samePeriodWindow } from './timelineAdapter';
import { historicalPhasesInWindow } from './currentTimeLens';
import { diffDays } from '../../utils';

/* ---------------- 视图模型（非 DB 实体） ---------------- */

/** 单条独立行情（主题行内的明细；一条 = 一个 Campaign 或 Research Candidate，不合并） */
export interface ThemeCampaignEntry {
  campaign_id: string;
  /** 正式 Campaign 或 Research Candidate（RC 保留 badge，不升级状态） */
  kind: 'campaign' | 'candidate';
  title: string;
  year: number;
  status: TimelineCampaign['status'];
  start: string;
  end: string;
  openEnded: boolean;
  /** 该行情在【当年同期窗口】内的主要阶段（历史事实，非当前状态；无 lifecycle → null） */
  phaseLabel: string | null;
  /** 窗口内命中的其余阶段（按 lifecycle 顺序，UI 轻量呈现） */
  phaseAlso: string[];
  /** 该行情自身的主主题（同主题不同年份/角色时对照展示） */
  mainTheme: string | null;
  /** 是否存在【重大】冲突（minor 不升级为告警视觉） */
  hasMajorConflict: boolean;
  /** 原始视图对象（供 UI 经现有 selection 打开 Campaign Detail） */
  campaign: TimelineCampaign;
}

/**
 * 主题行：一行 = 一个主主题在该窗口内的历史表现。
 * 这是 Adapter / UI 视图概念，不是数据库实体（无 theme_cycles / theme_relations）。
 */
export interface TimelineThemeRow {
  /** 主题键：主主题名（未标注主题时使用占位键） */
  themeKey: string;
  /** 展示标题 = 主主题名 */
  title: string;
  /** 出现该主题的年份（升序；同主题可跨多年） */
  years: number[];
  /** 该主题下的全部独立行情（按年份升序；同主题多条不合并） */
  campaigns: ThemeCampaignEntry[];
  /** 该主题在该窗口内的代表阶段（覆盖天数最多者；无 → null） */
  primaryPhase: string | null;
  /** 阶段摘要，如「主升 · 3 个年份」/「阶段未标注」/「无同期行情」 */
  phaseSummary: string;
  /** 相关概念：该主题组内出现过的其余主题名（去重，保持出现顺序；不含自身） */
  relatedConcepts: string[];
  /** 组内出现的数据状态（去重，保持出现顺序） */
  statuses: TimelineCampaign['status'][];
  /** 是否为"未标注主题"占位组（无 theme 信息的兜底，不编造主题名） */
  untitled: boolean;
}

/** 主题级同周期结果（按月） */
export interface ThemeRowsResult {
  /** 选中月份 */
  month: number;
  /** 同期窗口口径标签（如 08-15 ~ 10-15） */
  windowLabel: string;
  rows: TimelineThemeRow[];
  /** 是否当前研究数据未覆盖（无任何主题行） */
  uncovered: boolean;
}

/** 无 theme 信息时的占位主题键 / 标题（明确表达"研究未标注"，不编造主题名） */
export const UNTITLED_THEME_KEY = '__untitled_theme__';
export const UNTITLED_THEME_TITLE = '未标注主题';

/* ---------------- 主题选取 ---------------- */

/**
 * 主主题名：优先 role = main 的第一个，否则第一个主题名。
 * 与 timelineAdapter 内部 mainThemeName() 同口径（此处导出以便测试与复用）。
 */
export function primaryThemeName(c: Pick<TimelineCampaign, 'themes'>): string | null {
  const main = c.themes.find((t) => t.role === 'main');
  return main?.name ?? c.themes[0]?.name ?? null;
}

/** 窗口内主要阶段：覆盖天数最多者（同长取 lifecycle 靠前者，即 hits 中先出现者） */
function primaryPhaseOf(
  c: Pick<TimelineCampaign, 'lifecycle'>,
  win: { start: string; end: string },
): { label: string | null; also: string[] } {
  const hits = historicalPhasesInWindow(c, win);
  let primary: (typeof hits)[number] | null = null;
  for (const h of hits) {
    if (primary === null || h.days > primary.days) primary = h;
  }
  return {
    label: primary ? primary.label : null,
    also: hits.filter((h) => h !== primary).map((h) => h.label),
  };
}

/**
 * 是否存在重大冲突（仅 major 计为 ⚠；minor 视为同窗口，不升级告警）。
 * 阈值与 conflictSeverity() 一致（> 10 天 = major），此处独立实现以避免耦合导出常量。
 */
function majorConflict(c: TimelineCampaign): boolean {
  if (c.status !== 'conflict') return false;
  return (c.conflicts ?? []).some(
    (x) => Math.abs(diffDays(x.candidate_a.date, x.candidate_b.date)) > 10,
  );
}

/* ---------------- 主函数 ---------------- */

/**
 * 主题级历史机会行（V1.8.1）。
 *
 * 步骤（严格照此，不引入新逻辑）：
 *   1. samePeriodCampaigns(source, month)  →  各年份窗口内的行情/候选
 *   2. Theme Grouping                      →  按 primaryThemeName 归组（多条同主题聚类）
 *   3. Theme Rows                          →  生成行（含 primaryPhase / relatedConcepts / statuses）
 *
 * 不合并独立行情：grouping 只决定"行归属"，每行明细仍是各自的 Campaign。
 * 排序：行内 campaigns 按 (year, start) 升序；行按 (出现年份最早, themeKey) 升序。
 */
export function themeRowsOf(source: TimelineDataSource, month: number): ThemeRowsResult {
  const years = samePeriodCampaigns(source, month);

  interface Group {
    themeKey: string;
    title: string;
    untitled: boolean;
    entries: ThemeCampaignEntry[];
    related: string[];
    seenRelated: Set<string>;
    statuses: TimelineCampaign['status'][];
    years: number[];
  }

  const groups = new Map<string, Group>();
  const order: string[] = [];

  for (const row of years) {
    // 复用 samePeriodWindow：与 samePeriodCampaigns 内部逐字同口径
    const win = samePeriodWindow(row.year, month);
    for (const c of row.campaigns) {
      const main = primaryThemeName(c);
      const key = main ?? UNTITLED_THEME_KEY;
      let g = groups.get(key);
      if (!g) {
        g = {
          themeKey: key,
          title: main ?? UNTITLED_THEME_TITLE,
          untitled: main === null,
          entries: [],
          related: [],
          seenRelated: new Set<string>(),
          statuses: [],
          years: [],
        };
        groups.set(key, g);
        order.push(key);
      }
      const ph = primaryPhaseOf(c, win);
      g.entries.push({
        campaign_id: c.campaign_id,
        kind: c.kind,
        title: c.title,
        year: c.year,
        status: c.status,
        start: c.start,
        end: c.end,
        openEnded: c.openEnded === true,
        phaseLabel: ph.label,
        phaseAlso: ph.also,
        mainTheme: main,
        hasMajorConflict: majorConflict(c),
        campaign: c,
      });
      if (!g.years.includes(row.year)) g.years.push(row.year);
      if (!g.statuses.includes(c.status)) g.statuses.push(c.status);
      for (const t of c.themes) {
        if (t.name === main) continue;
        if (g.seenRelated.has(t.name)) continue;
        g.seenRelated.add(t.name);
        g.related.push(t.name);
      }
    }
  }

  const rows: TimelineThemeRow[] = order.map((key) => {
    const g = groups.get(key)!;
    g.entries.sort((a, b) => (a.year !== b.year ? a.year - b.year : a.start < b.start ? -1 : 1));
    const yearsSorted = [...g.years].sort((a, b) => a - b);

    // 代表阶段：组内覆盖天数最多者（同长取先出现）——按每条命中的阶段天数累加
    const phaseDays = new Map<string, number>();
    const phaseOrder: string[] = [];
    for (const e of g.entries) {
      const win = samePeriodWindow(e.year, month);
      for (const h of historicalPhasesInWindow(e.campaign, win)) {
        if (!phaseDays.has(h.label)) {
          phaseDays.set(h.label, 0);
          phaseOrder.push(h.label);
        }
        phaseDays.set(h.label, phaseDays.get(h.label)! + h.days);
      }
    }
    let primaryPhase: string | null = null;
    let best = -1;
    for (const label of phaseOrder) {
      const d = phaseDays.get(label)!;
      if (d > best) {
        best = d;
        primaryPhase = label;
      }
    }

    const yearCount = yearsSorted.length;
    const phaseSummary =
      primaryPhase === null ? '阶段未标注' : `${primaryPhase} · ${yearCount} 个年份`;

    return {
      themeKey: key,
      title: g.title,
      years: yearsSorted,
      campaigns: g.entries,
      primaryPhase,
      phaseSummary,
      relatedConcepts: g.related,
      statuses: g.statuses,
      untitled: g.untitled,
    };
  });

  // 行排序：出现年份最早者在前；同首年按 themeKey（未标注主题置后）
  rows.sort((a, b) => {
    const ay = a.years[0] ?? 9999;
    const by = b.years[0] ?? 9999;
    if (ay !== by) return ay - by;
    if (a.untitled !== b.untitled) return a.untitled ? 1 : -1;
    return a.themeKey < b.themeKey ? -1 : a.themeKey > b.themeKey ? 1 : 0;
  });

  return {
    month,
    windowLabel: windowLabelOf(years, month),
    rows,
    uncovered: rows.length === 0,
  };
}

/** 窗口口径标签（如 08-15 ~ 10-15）；无年份时退化为「—」 */
function windowLabelOf(years: { year: number }[], month: number): string {
  if (years.length === 0) return '—';
  const w = samePeriodWindow(years[0].year, month);
  return `${w.start.slice(5)} ~ ${w.end.slice(5)}`;
}
