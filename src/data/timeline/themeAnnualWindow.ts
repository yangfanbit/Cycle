/**
 * Theme Annual Window 聚合（Product 1.1 第二轮）—— **纯 Adapter / View 层**。
 *
 * ## 目的
 * 回答「**一年中历史上哪些时间窗口反复出现过什么类型的题材炒作**」，
 * 而不是「数据库里有哪些历史对象」。
 *
 * ## 流程（canonical，不新增第二套 Research 事实）
 * ```
 * Historical Campaign / Research Candidate（exports/timeline_export_v1.json）
 *     ↓  macroThemeOf()               —— 既有实现（researchAttention.ts），不重定义
 *     ↓  lifecycle[stage = MAIN_RISE] —— Research 既有 lifecycle，只取「主要炒作」
 *     ↓  年内时间归一化               —— 裁剪到日历年，投影为 0..1 比例
 *     ↓  Theme Annual Window 聚合     —— 同主题的多次出现**合并到同一行**
 * ```
 *
 * ## 关键取舍（均为**呈现层**判断，不改研究结论）
 *
 * 1. **只取 MAIN_RISE**：不在首页画完整生命周期（Decline / End 跨度）。
 *    完整生命周期仍在 CampaignDetail / 主题附页。
 * 2. **跨年 / 长周期**：`MAIN_RISE` 存在 `PHASE_WINDOW` 精度、跨度可达 1703 天的多年趋势
 *    （如 `C-2016-HIEQ-CONSTR` 的 MAIN_RISE：2016-08-01 → 2021-03-31，约 1703 天）。
 *    这类若按原样铺满首页，会把整条 Jan–Dec 轴涂满，破坏「季节性窗口」的可读性。
 *    → 规则：年内跨度 `> BROAD_WINDOW_DAYS`（183 天）判定为**长周期**，
 *      首页**只投影其起始月-日**（起始年一次），以极淡 onset 标记呈现，不铺满；
 *      真实起止仍在 tooltip 与附页中原样给出。
 *    → **不为中间年份重复生成 onset**（避免制造虚假的季节性密度）。
 * 3. **Research Candidate**：仅在**已有 MAIN_RISE 时间信息**时以弱化样式参与；
 *    未形成稳定历史窗口的 Candidate **不进入主地图**（不污染主题主地图），
 *    但仍出现在附页对象清单中（能力不删除，只是不在首页）。
 *    Candidate 一律不伪装成正式 Campaign（`kind` 原样透传）。
 * 4. **统计口径**：「历史重复 N 次 / 覆盖 N 个可比年份」是**计数事实**，
 *    不是概率、不是胜率、不是推荐分、不是预测。共识窗口取中位数（确定性），
 *    不参与任何推断。
 *
 * ## 边界
 * 不写 DB / schema / export / contracts；不改 Research 结论；
 * 不新增信号 / 评分 / 排名 / 概率 / 预测 / AI / Market Snapshot。
 */

import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import { macroThemeOf } from './researchAttention';
import { allResearchObjects } from './researchAttention';
import { dayOfYearISO, daysInYear } from '../../utils';

/** 年内跨度超过该天数即判定为「长周期」（只投影起始月-日，不铺满首页） */
export const BROAD_WINDOW_DAYS = 183;

/** 长周期 onset 标记的视觉宽度（天）——纯渲染常量，不代表研究结论 */
export const ONSET_MARKER_DAYS = 9;

/**
 * 一个历史对象在**某一年**内投影出的一段「主要炒作」窗口。
 */
export interface AnnualWindow {
  /** 所属日历年份 */
  year: number;
  /** 年内起点比例 0..1 */
  startFrac: number;
  /** 年内终点比例 0..1 */
  endFrac: number;
  /**
   * `window` = 年内可完整呈现的季节性窗口；
   * `onset`  = 长周期（跨年 / 超半年）只投影起始位置，极淡呈现。
   */
  kind: 'window' | 'onset';
  /** 该对象（展示用） */
  object: TimelineCampaign;
  /** 真实 MAIN_RISE 起止（原样来自 Research，不裁剪） */
  mainRise: { start: string; end: string } | null;
}

export interface ThemeAnnualRow {
  /** Macro Theme 名；`null` = 研究未标注所属行业（不编造行业名） */
  theme: string | null;
  /** 展示名（未归属时给出明确说明） */
  label: string;
  /** 首页主地图上的窗口（已按规则投影） */
  windows: AnnualWindow[];
  /** 历史出现次数（参与主地图的对象数，去重） */
  occurrences: number;
  /** 覆盖的可比年份数（去重年份） */
  comparableYears: number;
  /** 覆盖的年份清单（升序） */
  years: number[];
  /**
   * 共识窗口：所有 `window` 型窗口的**中位数**起止（确定性聚合）。
   * 无 `window` 型窗口时为 null（不编造）。
   */
  consensus: { startFrac: number; endFrac: number } | null;
  /** 该主题下**全部**历史对象（含未进入主地图的；供附页使用） */
  objects: TimelineCampaign[];
  /** 正式 Campaign 数 / Research Candidate 数（附页展示） */
  campaignCount: number;
  candidateCount: number;
}

/** 取 Research lifecycle 中的 MAIN_RISE 段（无则 null） */
export function mainRiseOf(c: TimelineCampaign): { start: string; end: string } | null {
  const s = (c.lifecycle ?? []).find((x) => x.stage === 'MAIN_RISE');
  if (!s || !s.start || !s.end) return null;
  return { start: s.start, end: s.end };
}

/**
 * 把一段 MAIN_RISE 投影到日历年内的窗口序列。
 *
 * 判定以 **MAIN_RISE 总跨度** 为准（不用逐年跨度），避免跨年尾段被误判为独立季节窗口：
 *
 * - 总跨度 `> BROAD_WINDOW_DAYS`（183 天）→ **长周期**：
 *   只在起始年投影**一次**起始月-日（`onset`，极淡），不铺满首页、也不为后续年份制造虚假密度。
 * - 总跨度 `≤ BROAD_WINDOW_DAYS` → **季节性窗口**：
 *   按日历年裁剪并投影；若恰好跨年（如 11-01 → 01-15）则分成年内两段，
 *   两段都是真实的主要炒作覆盖，各自成为一段 `window`。
 */
export function projectMainRise(
  mr: { start: string; end: string },
  object: TimelineCampaign,
): AnnualWindow[] {
  const y1 = Number(mr.start.slice(0, 4));
  const y2 = Number(mr.end.slice(0, 4));
  if (!Number.isFinite(y1) || !Number.isFinite(y2) || y2 < y1) return [];

  const totalDays =
    dayOfYearISO(mr.end) - dayOfYearISO(mr.start) + (y2 - y1) * 365 + (y2 - y1 > 0 ? 1 : 0);

  // 长周期：只投影起始位置一次
  if (totalDays > BROAD_WINDOW_DAYS) {
    const diy = daysInYear(y1);
    const sf = (dayOfYearISO(mr.start) - 1) / diy;
    return [
      {
        year: y1,
        startFrac: sf,
        endFrac: Math.min(sf + ONSET_MARKER_DAYS / diy, 1),
        kind: 'onset',
        object,
        mainRise: mr,
      },
    ];
  }

  // 季节性窗口：按年裁剪投影
  const out: AnnualWindow[] = [];
  for (let y = y1; y <= y2; y += 1) {
    const segStart = y === y1 ? mr.start : `${y}-01-01`;
    const segEnd = y === y2 ? mr.end : `${y}-12-31`;
    if (segEnd < segStart) continue;
    const diy = daysInYear(y);
    out.push({
      year: y,
      startFrac: (dayOfYearISO(segStart) - 1) / diy,
      endFrac: Math.min(dayOfYearISO(segEnd) / diy, 1),
      kind: 'window',
      object,
      mainRise: mr,
    });
  }
  return out;
}

function median(nums: number[]): number {
  if (nums.length === 0) return 0;
  const s = [...nums].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 === 0 ? (s[mid - 1] + s[mid]) / 2 : s[mid];
}

/**
 * Macro Theme → 年内时间窗口聚合（首页主地图唯一数据源）。
 *
 * 排序：有名称的主题在前（按「历史出现次数」降序 → 名称升序），未归属置后。
 */
/**
 * 聚合粒度（ThreeC 1.2 · Usage-Driven）。
 *
 * - `macro`：按**大主题**聚合（`macroThemeOf`）—— 首页默认，行数少、样本厚；
 * - `sub`  ：按**主题材**聚合（`themes[role=main].name`）—— 行数多、**样本薄**，
 *            用于看「某个具体方向」的年内分布。
 *
 * ★ 粒度只是**分组口径**，不新增任何研究结论；`sub` 下样本常常只有 2–3 个窗口，
 *   **不得**据此下结论（`themeSeasonality` 的判据已要求 ≥3 个窗口才加标注）。
 */
export type ThemeGranularity = 'macro' | 'sub';

/** 粒度切换的界面选项（数组顺序 = 界面顺序；`axis` 同时用作纵轴表头） */
export const GRANULARITY_OPTIONS: ReadonlyArray<{
  value: ThemeGranularity;
  label: string;
  axis: string;
}> = [
  { value: 'macro', label: '按大主题', axis: '大主题' },
  { value: 'sub', label: '按主题材', axis: '主题材' },
];

/** 取某个粒度的纵轴表头（找不到时回退大主题） */
export function granularityAxis(g: ThemeGranularity): string {
  return (GRANULARITY_OPTIONS.find((o) => o.value === g) ?? GRANULARITY_OPTIONS[0]).axis;
}

/** 取某个粒度的行名后缀（用于「N 个大主题 / N 个主题材」这类计数陈述） */
export function granularityNoun(g: ThemeGranularity): string {
  return g === 'macro' ? '大主题' : '主题材';
}

/**
 * ★★ `sub` 粒度的**语义边界** —— 必须与切换控件同显，否则薄样本会被读成结论。
 *
 * 实测（2026-10-08 canonical export）：`macro` 12 行、`sub` 41 行；
 * `sub` 下**窗口数 ≥ 3 的只有 2 行**（半导体 5、银行 3），
 * 即绝大多数主题材**根本没有足够样本**支撑任何「年内集中」的说法。
 * 这不是缺陷，是「具体方向的历史案例本来就少」这一事实的如实呈现。
 *
 * ★ 措辞避开既有护栏禁列（`score / ranking / probability / prediction / 胜率 / 推荐分 / 预测`）。
 */
export const SUB_GRANULARITY_NOTE =
  '「按主题材」把大主题拆成具体方向：行数更多，但每行的历史案例更少 —— ' +
  '实测 41 个主题材里只有 2 个的年内窗口数达到 3 个（集中标注的最低样本要求）。' +
  '粒度只改变「分组口径」，不新增研究结论；样本不足时一律不做集中标注。';

/** 分组键：按粒度取「大主题」或「主题材」；取不到时返回 null（**不编造**） */
function groupingKeyOf(c: TimelineCampaign, g: ThemeGranularity): string | null {
  if (g === 'macro') return macroThemeOf(c);
  const main = (c.themes ?? []).find((t) => t.role === 'main');
  return main ? main.name : null;
}

export function themeAnnualRowsOf(
  source: TimelineDataSource,
  granularity: ThemeGranularity = 'macro',
): ThemeAnnualRow[] {
  const objects = allResearchObjects(source);
  const groups = new Map<string | null, TimelineCampaign[]>();
  for (const c of objects) {
    const t = groupingKeyOf(c, granularity);
    const arr = groups.get(t);
    if (arr) arr.push(c);
    else groups.set(t, [c]);
  }

  const rows: ThemeAnnualRow[] = [];
  for (const [theme, list] of groups) {
    const windows: AnnualWindow[] = [];
    for (const c of list) {
      const mr = mainRiseOf(c);
      if (!mr) continue; // 无 MAIN_RISE → 不进入主地图（不污染季节性地图）
      windows.push(...projectMainRise(mr, c));
    }
    windows.sort((a, b) => a.startFrac - b.startFrac);

    const onMap = new Set(windows.map((w) => w.object.campaign_id));
    const years = [...new Set(windows.map((w) => w.year))].sort((a, b) => a - b);
    const winOnly = windows.filter((w) => w.kind === 'window');
    const consensus =
      winOnly.length > 0
        ? {
            startFrac: median(winOnly.map((w) => w.startFrac)),
            endFrac: median(winOnly.map((w) => w.endFrac)),
          }
        : null;

    rows.push({
      theme,
      // 未归属时**不编造行业名**：只给中性标签，完整解释在附页给出
      label: theme ?? (granularity === 'macro' ? '未标注大主题' : '未标注主题材'),
      windows,
      occurrences: onMap.size,
      comparableYears: years.length,
      years,
      consensus,
      objects: [...list].sort((a, b) => (a.start < b.start ? -1 : a.start > b.start ? 1 : 0)),
      campaignCount: list.filter((c) => c.kind === 'campaign').length,
      candidateCount: list.filter((c) => c.kind === 'candidate').length,
    });
  }

  return rows.sort((a, b) => {
    if (a.theme === null && b.theme !== null) return 1;
    if (a.theme !== null && b.theme === null) return -1;
    if (b.occurrences !== a.occurrences) return b.occurrences - a.occurrences;
    const an = a.theme ?? '';
    const bn = b.theme ?? '';
    return an < bn ? -1 : an > bn ? 1 : 0;
  });
}

/**
 * 行的稳定标识（用于「当前展开哪一个主题」）。
 * 未标注大主题用显式哨兵，避免与空字符串主题名混淆。
 */
export function themeKey(row: Pick<ThemeAnnualRow, 'theme'>): string {
  return row.theme ?? '__unassigned__';
}

/**
 * 首页主地图实际展示的行。
 *
 * **没有任何年内主要炒作窗口的主题不进入首页地图**——它们在图上是一条空行，
 * 只会制造「数据库感」而不贡献任何季节性信息。这些主题下的历史对象
 * 仍然通过「全部大主题（含无季节性窗口）」钻取入口进入附页，**能力不删除**。
 */
export function seasonalMapRows(rows: ThemeAnnualRow[]): ThemeAnnualRow[] {
  return rows.filter((r) => r.windows.length > 0);
}

/** 首页主地图统计（页头一句话说明用） */
export function seasonalMapSummary(rows: ThemeAnnualRow[]): {
  themeCount: number;
  windowCount: number;
  objectCount: number;
  yearFrom: number | null;
  yearTo: number | null;
} {
  const allWin = rows.flatMap((r) => r.windows);
  const ids = new Set(allWin.map((w) => w.object.campaign_id));
  const ys = allWin.map((w) => w.year);
  return {
    themeCount: rows.length,
    windowCount: allWin.length,
    objectCount: ids.size,
    yearFrom: ys.length ? Math.min(...ys) : null,
    yearTo: ys.length ? Math.max(...ys) : null,
  };
}
