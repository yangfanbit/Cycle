/**
 * ★★ 外部季节性线索 ↔ 宏观主题历史 `MAIN_RISE` 窗口的**并排对照**（ThreeC 1.3 · v0.13）。
 *
 * ## 关联方式（唯一、可核对）
 *
 * 仅当外部条目 `mapping.status === 'MAPPED'` 时，用 `mapping.macro_theme` 与
 * **宏观粒度**（`themeAnnualRowsOf(source, 'macro')`）主题行的 `theme` 做**精确字符串相等**匹配。
 * ★ 不做模糊匹配、不做语义推断、不做同义词合并 —— 匹配不上就是「未找到精确匹配」。
 *
 * ## 对照**不是**什么（UI 必须原样声明）
 *
 * - **不是**「事件机制相同」：宏观主题映射只说明**名称归属**，机制可能完全不同。
 * - **不是**统计验证：不计算重合率 / 命中率 / 规律成立率，不生成分数、排名或预测结论。
 * - **不是**替换关系：历史题材事件地图（`HistoricalEventMap`）是另一套视图，两者并存。
 *
 * ## 历史侧口径
 *
 * 完全复用 Research 的投影结果（`AnnualWindow.startFrac` / `endFrac` / `kind`）：
 * - `window`：年内可完整呈现的季节性窗口；
 * - `onset`：长周期（>183 天）只投影**起始位置**一次（极淡标记），
 *   **不**为后续年份制造虚假密度。
 * ★ 本模块**不重算**任何窗口，只做「取出来 + 排好序 + 保留原文」。
 */

import type { ExternalCalendarEntry } from './externalSeasonalCalendar';
import { mainRiseOf, type AnnualWindow, type ThemeAnnualRow } from './themeAnnualWindow';

export interface ComparisonWindow {
  year: number;
  /** `window` = 年内完整窗口；`onset` = 长周期起始标记 */
  kind: 'window' | 'onset';
  startFrac: number;
  endFrac: number;
  objectId: string;
  title: string;
  /** Campaign（正式历史对象）还是 Research Candidate（研究候选） */
  objectKind: 'campaign' | 'candidate';
  /** 原始 MAIN_RISE 起止（**原样**，不裁剪、不补全） */
  mainRise: { start: string; end: string } | null;
}

export type ComparisonStatus =
  /** 已映射且找到同名宏观主题行 → 有历史窗口可对照 */
  | 'matched'
  /** 已映射但**没有**同名主题行（真实空态，不补造） */
  | 'no-exact-theme'
  /** 未映射 → 不尝试关联 */
  | 'not-mapped';

export interface ThemeComparison {
  entryId: string;
  status: ComparisonStatus;
  /** 精确匹配到的宏观主题名（未匹配 → null） */
  theme: string | null;
  /** 该主题的历史窗口（按年份 → 起点排序；`onset` 与 `window` 都保留） */
  windows: ComparisonWindow[];
  /** 涉及年份（升序去重） */
  years: number[];
  /** 该主题下正式 Campaign / Research Candidate 计数（**全部对象**，含未进入窗口的） */
  counts: { campaign: number; candidate: number };
  /**
   * ★★ 历史窗口**实际涉及**的对象数（按 `objectId` 去重）。
   * 不能拿 `windows.length` 当对象数 —— 一个对象跨年可产生多段投影。
   */
  windowCounts: { campaign: number; candidate: number };
  /**
   * 该主题下**未**进入窗口列表的对象（即没有可投影的 `MAIN_RISE`）。
   * ★ 原样列出、逐条带原因；**不得**把它们算进窗口里，也不得从窗口计数里悄悄抹掉。
   */
  objectsOutsideWindows: OutsideWindowObject[];
  /** 空态 / 未映射时的说明（**只陈述事实**） */
  note: string;
}

/** 未进入历史窗口的对象（含**为什么**没进） */
export interface OutsideWindowObject {
  objectId: string;
  title: string;
  objectKind: 'campaign' | 'candidate';
  /** 未进入窗口的原因（逐条判定，不合并、不猜） */
  reason: 'no-main-rise' | 'main-rise-not-projected';
}

function toComparisonWindow(w: AnnualWindow): ComparisonWindow {
  return {
    year: w.year,
    kind: w.kind,
    startFrac: w.startFrac,
    endFrac: w.endFrac,
    objectId: w.object.campaign_id,
    title: w.object.title,
    objectKind: w.object.kind,
    mainRise: w.mainRise,
    // ★ 不补：mainRise 缺失就保持 null（长周期对象也可能没有完整起止）
  };
}

/**
 * ★★ 主函数：为一条外部线索找它的宏观主题历史窗口（纯函数）。
 *
 * @param entry 外部线索
 * @param macroRows **宏观粒度**的主题行（调用方必须传 `granularity='macro'` 的结果，
 *                  不得用首页当前粒度 —— 否则对照会随用户切换粒度而变化）
 */
export function compareExternalToTheme(
  entry: ExternalCalendarEntry,
  macroRows: readonly ThemeAnnualRow[],
): ThemeComparison {
  const empty = {
    counts: { campaign: 0, candidate: 0 },
    windowCounts: { campaign: 0, candidate: 0 },
    objectsOutsideWindows: [],
  };

  if (entry.mapping.status !== 'MAPPED' || !entry.mapping.macro_theme) {
    return {
      entryId: entry.id,
      status: 'not-mapped',
      theme: null,
      windows: [],
      years: [],
      ...empty,
      note: '该线索**未映射**到 ThreeC 宏观主题 → 没有可对照的历史窗口。'
        + '（未映射 ≠ 库内不存在相关对象；只是名称层面没有对应根主题。）',
    };
  }

  const theme = entry.mapping.macro_theme;
  // ★ 精确相等；`null` 主题行不参与（未标注大主题不是一个主题名）
  const row = macroRows.find((r) => r.theme !== null && r.theme === theme);

  if (!row) {
    return {
      entryId: entry.id,
      status: 'no-exact-theme',
      theme,
      windows: [],
      years: [],
      ...empty,
      note: `已映射到「${theme}」，但**当前研究数据里没有同名宏观主题行** —— `
        + '因此没有历史窗口可对照。★ 不补造窗口。',
    };
  }

  const windows = row.windows
    .map(toComparisonWindow)
    .sort((a, b) => a.year - b.year || a.startFrac - b.startFrac
      || a.objectId.localeCompare(b.objectId));

  // ★★ 窗口**段数** ≠ 对象数：同一对象跨年可有多个投影段 → 按 objectId 去重
  const inWindow = new Map<string, 'campaign' | 'candidate'>();
  for (const w of windows) {
    if (!inWindow.has(w.objectId)) inWindow.set(w.objectId, w.objectKind);
  }
  const windowCounts = {
    campaign: [...inWindow.values()].filter((k) => k === 'campaign').length,
    candidate: [...inWindow.values()].filter((k) => k === 'candidate').length,
  };

  // 主题下**全部**对象里未进入窗口的 → 原样列出 + 逐条原因。
  // ★ 两种原因都保留：一是没有 MAIN_RISE；二是有 MAIN_RISE 但投影为空（异常路径，
  //   宁可显示出来让人核对，也不悄悄塞进任一侧计数里）。
  const objectsOutsideWindows: OutsideWindowObject[] = row.objects
    .filter((c) => !inWindow.has(c.campaign_id))
    .map((c) => ({
      objectId: c.campaign_id,
      title: c.title,
      objectKind: c.kind,
      reason: (mainRiseOf(c) === null
        ? 'no-main-rise'
        : 'main-rise-not-projected') as OutsideWindowObject['reason'],
    }))
    .sort((a, b) => a.objectId.localeCompare(b.objectId));

  const outside = objectsOutsideWindows.length;
  const note = windows.length === 0
    ? `已映射到「${theme}」，但该主题下**没有可投影的 MAIN_RISE 窗口** —— 历史侧为空。`
      + (outside > 0 ? `（该主题共 ${row.objects.length} 个对象，均无 MAIN_RISE 记录。）` : '')
    : `「${theme}」下有 ${windows.length} 段历史 MAIN_RISE 窗口`
      + `（投影段数；实际涉及 ${windowCounts.campaign} 个 Campaign + `
      + `${windowCounts.candidate} 个 Research Candidate，按对象去重）。`
      + (outside > 0
        ? `另有 ${outside} 个对象因**没有 MAIN_RISE 记录**未进入窗口`
          + `（该主题共 ${row.objects.length} 个对象）。`
        : '');

  return {
    entryId: entry.id,
    status: 'matched',
    theme,
    windows,
    years: [...new Set(windows.map((w) => w.year))].sort((a, b) => a - b),
    counts: {
      campaign: row.campaignCount,
      candidate: row.candidateCount,
    },
    windowCounts,
    objectsOutsideWindows,
    note,
  };
}

/** 把 `0..1` 的年内比例说成「约几月几日」—— **只在需要文字说明时用**，不用于绘图 */
export function fracToMonthLabel(frac: number): string {
  const clamped = Math.min(Math.max(frac, 0), 1);
  const month = Math.min(12, Math.floor(clamped * 12) + 1);
  return `${month} 月`;
}

/** ★ 本对照的语义声明（UI 原样渲染） */
export const THEME_COMPARISON_DISCLAIMER =
  '★★ **宏观主题映射 ≠ 事件机制相同**：这里只按「外部线索的宏观主题名 = 历史主题名」**精确匹配**后'
  + '并排显示两套窗口，**不判断**机制是否一致。'
  + '★★ **并排对照不是统计验证**：不计算重合率 / 命中率 / 规律成立率，'
  + '不生成分数、排名或预测结论。'
  + '★ 历史侧来自 Research 的 `MAIN_RISE` 与既有投影规则（长周期只投影起始位置），'
  + '外部侧保持**月份精度**。两者**不得**合并成一套窗口。';
