import type { TimelineDataSource } from './timelineTypes';
import { allResearchObjects, macroThemeOf } from './researchAttention';
import type { CurrentCandidateDataset } from './currentCandidate';

/**
 * 方向查询（Direction Lookup）—— ThreeC 1.2 · Usage-Driven。
 *
 * ## 这一层解决什么
 * 两次真实使用测试暴露的核心问题：**全库只有 5 个当前研究对象，而历史有 52 个 Campaign。**
 * 用户真正关心的方向**大概率不在这 5 个里** —— 而产品此前**只能展示研究侧选定的对象**，
 * 用户**无法自己问**。
 *
 * 本模块让用户**声明一个方向**，并得到**明确回答**：
 * - 两侧都有 → 走完整工作流
 * - 只有历史（如「汽车」）→ 走历史侧，并**明说当前侧没有**
 * - 都没有（如「文化传媒」）→ **诚实说覆盖不到**
 *
 * ## ★★ 语义边界（硬约束，不得违反）
 * 这是**查找 / 导航**，**不是**结构对应。
 * 「主题名命中」**绝不**意味着 `Structural Correspondence` ——
 * `AGENTS.md` §3 明令：`Theme / Name 相似 ≠ Structural Correspondence`。
 * 因此本模块：
 * - **只做字符串匹配**，不产生任何状态、档位、相似度、评分；
 * - 结果里**不得**出现 `STRUCTURAL_*` 之类的结构判定字样；
 * - 真正的结构对应**唯一**入口仍是 `StructuralAnalogySection`（冻结 SA 解释）。
 *
 * ## 纯函数
 * 无副作用、无 IO、无网络。
 */

export interface DirectionHit {
  kind: 'current' | 'historical';
  id: string;
  title: string;
  /** 命中的**依据**（主题名 / 大主题 / 标题）—— 让匹配可解释、可核对 */
  matchedOn: string[];
  macroTheme: string | null;
  start?: string;
  end?: string;
  /** 仅当前对象：研究问题（工作流最后一步「继续研究」的线索） */
  researchQuestions?: string[];
}

export type DirectionVerdict = 'both' | 'current-only' | 'historical-only' | 'none';

export interface DirectionLookupResult {
  query: string;
  current: DirectionHit[];
  historical: DirectionHit[];
  verdict: DirectionVerdict;
}

function norm(s: string): string {
  return s.trim().toLowerCase();
}

/** 命中判定：查询串是否为该词的一部分（不区分大小写） */
function hits(term: string | null | undefined, q: string): boolean {
  return typeof term === 'string' && term.length > 0 && norm(term).includes(q);
}

/** 某历史对象的所有可匹配词（标题 / 主题名 / 大主题） */
function termsOfHistorical(c: {
  title: string;
  themes: { name: string }[];
  macro: string | null;
}): string[] {
  const out = [c.title];
  for (const t of c.themes) if (t?.name) out.push(t.name);
  if (c.macro) out.push(c.macro);
  return out.filter((s) => typeof s === 'string' && s.length > 0);
}

/**
 * 查询一个方向。
 *
 * @param query   用户输入的方向关键词（如「汽车」「半导体」「文化传媒」）
 * @param source  Timeline 数据源（历史侧）
 * @param dataset 当前研究对象数据集
 */
export function lookupDirection(
  query: string,
  source: TimelineDataSource | null,
  dataset: CurrentCandidateDataset | null,
): DirectionLookupResult {
  const q = norm(query);
  const empty: DirectionLookupResult = { query, current: [], historical: [], verdict: 'none' };
  if (!q) return empty;

  /* ---- 当前侧 ---- */
  const current: DirectionHit[] = [];
  for (const c of dataset?.candidates ?? []) {
    const matched: string[] = [];
    for (const term of [c.display_name, c.macro_theme, c.core_narrative]) {
      if (hits(term, q)) matched.push(term as string);
    }
    if (matched.length === 0) continue;
    current.push({
      kind: 'current',
      id: c.candidate_id,
      title: c.display_name,
      matchedOn: [...new Set(matched)],
      macroTheme: c.macro_theme,
      researchQuestions: c.research_questions ?? [],
    });
  }

  /* ---- 历史侧 ---- */
  const historical: DirectionHit[] = [];
  if (source) {
    for (const c of allResearchObjects(source)) {
      const macro = macroThemeOf(c);
      const matched = termsOfHistorical({ title: c.title, themes: c.themes ?? [], macro }).filter((t) =>
        hits(t, q),
      );
      if (matched.length === 0) continue;
      historical.push({
        kind: 'historical',
        id: c.campaign_id,
        title: c.title,
        matchedOn: [...new Set(matched)],
        macroTheme: macro,
        start: c.start,
        end: c.end,
      });
    }
  }

  const verdict: DirectionVerdict =
    current.length > 0 && historical.length > 0
      ? 'both'
      : current.length > 0
        ? 'current-only'
        : historical.length > 0
          ? 'historical-only'
          : 'none';

  return { query, current, historical, verdict };
}

/** 覆盖词表（供用户知道「能查什么」）—— 计数事实，不是排序或评分 */
export interface CoveredTerm {
  term: string;
  historicalCount: number;
  currentCount: number;
}

export function coveredTerms(
  source: TimelineDataSource | null,
  dataset: CurrentCandidateDataset | null,
): CoveredTerm[] {
  const map = new Map<string, CoveredTerm>();
  const bump = (term: string | null, side: 'h' | 'c') => {
    if (!term) return;
    const e = map.get(term) ?? { term, historicalCount: 0, currentCount: 0 };
    if (side === 'h') e.historicalCount += 1;
    else e.currentCount += 1;
    map.set(term, e);
  };

  if (source) for (const c of allResearchObjects(source)) bump(macroThemeOf(c), 'h');
  for (const c of dataset?.candidates ?? []) bump(c.macro_theme, 'c');

  return [...map.values()].sort(
    (a, b) =>
      b.currentCount - a.currentCount ||
      b.historicalCount - a.historicalCount ||
      a.term.localeCompare(b.term),
  );
}
