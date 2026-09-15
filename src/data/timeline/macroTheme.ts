/**
 * Macro Theme 聚合接口（V2.0）—— **仅 View / Adapter 层**。
 *
 * ## 目的
 * 为「Timeline 以 Macro Theme 为一行、Campaign 作为明细」的**未来切换**准备好数据接口。
 * 本轮**不**改变 Timeline 现有视觉（仍以 `role='main'` 的 Sub-theme 成行）。
 *
 * ## 层级来源（全部为既有数据，不新增 schema / DB / export contract）
 * ```
 * Macro Theme   ← 题材中 theme_type ∈ {industry, sector} 且 role = related（导出既有字段透传）
 *     ↓
 * Campaign /    ← 该 Campaign 的其余题材（role = main / secondary / related-concept）
 * Research Candidate
 *     ↓
 * Theme Cycle   ← theme_cycle_id（研究层归组，可含多个 Campaign）
 * ```
 * 另提供 `themeCatalogueRoots()`：从产品侧题材库（`data/candidate/themes.ts`）的
 * `parent_theme_id IS NULL` 推导根主题清单（用于未来把导出题材对齐到产品题材表）。
 *
 * ## 边界
 * **纯 View / Adapter 层**：不写入 DB / schema / export / contracts，
 * 不落库、不进 `src/models/`、不改 `schema.sql`、不改 export contract、不改 Timeline UI。
 * 本轮**不改变 Timeline 现有视觉**（仍以 `role='main'` 的 Sub-theme 成行）。
 */

import { themes as catalogueThemes } from '../../data';
import type { TimelineCampaign, TimelineDataSource } from './timelineTypes';
import { allResearchObjects, macroThemeOf, themeCycleViewsOf } from './researchAttention';

/** Macro Theme 判定与 Theme Cycle 归组复用 researchAttention（单一实现，避免重复定义） */
export { macroThemeOf };

/** 该研究对象的子题材（Macro Theme 之外的题材名，去重、保持出现顺序） */
export function subThemesOf(campaign: TimelineCampaign): string[] {
  const macro = macroThemeOf(campaign);
  const out: string[] = [];
  for (const t of campaign.themes ?? []) {
    if (t.name === macro) continue;
    if (!out.includes(t.name)) out.push(t.name);
  }
  return out;
}

export interface MacroThemeGroup {
  /** Macro Theme 名；`null` → 未归属（研究未标注所属行业） */
  macroTheme: string | null;
  /** 出现过的 theme_type（industry / sector） */
  themeTypes: string[];
  campaigns: TimelineCampaign[];
  /** 该 Macro Theme 下的子题材并集（去重，保持出现顺序） */
  subThemes: string[];
  /** 该 Macro Theme 关联的 Theme Cycle（theme_cycle_id 去重） */
  themeCycleIds: string[];
  /** 覆盖区间（研究记录，非市场判断） */
  coverage: { start: string; end: string };
}

/**
 * Macro Theme → Campaigns 聚合（未来 Timeline 主视图切换的接口）。
 * 未标注 Macro Theme 的对象归入 `macroTheme: null` 组，**不编造**行业名。
 */
export function macroThemeGroupsOf(source: TimelineDataSource): MacroThemeGroup[] {
  const objects = allResearchObjects(source);
  const groups = new Map<string | null, MacroThemeGroup>();

  for (const c of objects) {
    const macro = macroThemeOf(c);
    let g = groups.get(macro);
    if (!g) {
      g = {
        macroTheme: macro,
        themeTypes: [],
        campaigns: [],
        subThemes: [],
        themeCycleIds: [],
        coverage: { start: c.start, end: c.end },
      };
      groups.set(macro, g);
    }
    g.campaigns.push(c);
    if (c.start < g.coverage.start) g.coverage.start = c.start;
    if (c.end > g.coverage.end) g.coverage.end = c.end;
    for (const t of c.themes ?? []) {
      if (t.name === macro) {
        if (t.theme_type && !g.themeTypes.includes(t.theme_type)) g.themeTypes.push(t.theme_type);
        continue;
      }
      if (!g.subThemes.includes(t.name)) g.subThemes.push(t.name);
    }
    const cycle = c.theme_cycle_id ?? null;
    if (cycle && !g.themeCycleIds.includes(cycle)) g.themeCycleIds.push(cycle);
  }

  // 排序：有 Macro Theme 在前（按名称），未归属置后
  return [...groups.values()].sort((a, b) => {
    if (a.macroTheme === null && b.macroTheme !== null) return 1;
    if (a.macroTheme !== null && b.macroTheme === null) return -1;
    const an = a.macroTheme ?? '';
    const bn = b.macroTheme ?? '';
    if (an !== bn) return an < bn ? -1 : 1;
    return a.coverage.start < b.coverage.start ? -1 : 1;
  });
}

/** 该数据源内出现的 Macro Theme 名（去重，升序；不含未归属） */
export function macroThemeNamesOf(source: TimelineDataSource): string[] {
  return macroThemeGroupsOf(source)
    .map((g) => g.macroTheme)
    .filter((n): n is string => n !== null)
    .sort();
}

/**
 * 产品侧题材库的**根主题**（`parent_theme_id` 缺省者）。
 * 用于未来把导出的题材名对齐到产品题材表（本轮只提供接口，不做对齐/改名）。
 */
export function themeCatalogueRoots(): { theme_id: string; name: string; theme_type?: string }[] {
  return catalogueThemes
    .filter((t) => !t.parent_theme_id)
    .map((t) => ({ theme_id: t.theme_id, name: t.name, theme_type: t.theme_type }));
}

/** 产品侧题材库中某根主题的直接子题材（未来下钻用） */
export function themeCatalogueChildren(parentThemeId: string): { theme_id: string; name: string }[] {
  return catalogueThemes
    .filter((t) => t.parent_theme_id === parentThemeId)
    .map((t) => ({ theme_id: t.theme_id, name: t.name }));
}

/**
 * Macro Theme 聚合的层级视图（Macro Theme → Theme Cycle → Campaigns）。
 * 未来 Timeline 切换主单位时可直接消费；本轮不改任何 UI。
 */
export interface MacroThemeTree {
  macroTheme: string | null;
  subThemes: string[];
  themeCycles: {
    key: string;
    themeCycleId: string | null;
    campaigns: TimelineCampaign[];
  }[];
}

export function macroThemeTreeOf(source: TimelineDataSource): MacroThemeTree[] {
  const cycles = themeCycleViewsOf(source);
  return macroThemeGroupsOf(source).map((g) => {
    const own = cycles.filter((v) =>
      v.components.some((comp) => macroThemeOf(comp.campaign) === g.macroTheme),
    );
    return {
      macroTheme: g.macroTheme,
      subThemes: g.subThemes,
      themeCycles: own.map((v) => ({
        key: v.key,
        themeCycleId: v.themeCycleId,
        campaigns: v.components.map((c) => c.campaign),
      })),
    };
  });
}
