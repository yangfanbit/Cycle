/**
 * ★★ 历史题材的**参与标的索引**（ThreeC 1.3 · v0.11）。
 *
 * ## 这是什么
 *
 * 把一份题材事件文档（`HistoricalEventsDoc`）里的 `events[].participants`
 * **按 `security_id` 汇总**成「一只股票在历次事件里出现过几次、每次为什么被纳入」。
 *
 * ## 这不是什么（硬约束，全部由测试与 UI 声明）
 *
 * - **不是概念相关度分数**：不做评分、不做排名、不把「参与过 + 业务相关 + 涨过」合成一个数。
 * - **不是跨事件收益汇总**：不累加、不平均、不比较不同窗口的收益率
 *   （各事件窗口口径不同，合并即偷换口径）。每个事件的行情数字**仍按原口径**逐条呈现。
 * - **不猜身份**：`reported_same_day_moves` 里的代码只有与参与者的 `security_id` 或 `ticker`
 *   **完全相等**才算关联；否则保留为「同期报道点名、尚未关联标的记录」的独立状态。
 * - **不合并证据等级**：`REPORT_NAMED`（同期报道点名）与 `BUSINESS_VERIFIED`（业务机制有独立资料）
 *   是两种不同事实；同一标的跨事件可能是**混合**的，必须逐次呈现，不得取「最高级」当成整只股票的标签。
 *
 * ## 排序
 *
 * 只按**公司名称**（中文 locale）→ `security_id` 稳定排序。
 * **不得**按涨幅、出现次数或任何指标排序（那会变成推荐排名）。
 */

import {
  EVIDENCE_LEVEL_LABEL,
  type EvidenceLevel,
  type HistoricalEvent,
  type HistoricalEventsDoc,
  type HistoricalParticipant,
  type ParticipantCategory,
} from './historicalEventMaps';

/** 一次「该标的出现在某个事件里」的记录（原样保留该次事件的字段） */
export interface SecurityOccurrence {
  eventId: string;
  year: number;
  eventLabel: string;
  eventClass?: string;
  category: ParticipantCategory;
  /** ★ 该**次**的证据等级；缺失 = `undefined`（不猜成 REPORT_NAMED） */
  evidenceLevel?: EvidenceLevel;
  rationale: string;
  source: string;
  note?: string;
  businessMechanism?: string;
  businessMechanismCaveat?: string;
  /** 参与者条目自带的「报道当日涨幅」文本 */
  reportedMove?: string;
  /** 该事件的 `reported_same_day_moves` 里**精确匹配**到的涨幅文本 */
  eventReportedMove?: string;
  /** 该事件 `market_performance.by_security` 是否包含该标的 */
  hasMarketPerformance: boolean;
  marketWindow?: [string, string] | null;
  /** 参与者条目里的行情摘要文本（如「区间 +12.3%」） */
  marketData?: string;
  periodReturnPct?: number;
  toHighPct?: number;
  highDate?: string;
  excessPeriodPp?: number;
  excessToHighPp?: number;
}

export interface ThemeSecurityEntry {
  securityId: string;
  ticker: string;
  /** 展示名：取**最近年份**出现时的名称（同一年取字典序最小），保证确定性 */
  name: string;
  /** 历史上出现过的其它名称（如改名 / ST）—— 不丢，只作别名 */
  aliases: string[];
  exchange?: string;
  eventCount: number;
  /** 出现年份（升序去重） */
  years: number[];
  /** 该标的在本题材里出现过的**全部**证据等级（按枚举顺序，不合并成单一标签） */
  evidenceLevels: EvidenceLevel[];
  categories: ParticipantCategory[];
  occurrences: SecurityOccurrence[];
}

/** 「同期报道点名、但**没有**对应参与者记录」的条目 —— 独立状态，不并入上面的索引 */
export interface UnlinkedReportedMove {
  eventId: string;
  year: number;
  eventLabel: string;
  /** 原文代码（`reported_same_day_moves` 的 key，原样保留，不解析、不猜测） */
  code: string;
  move: string;
  status: 'REPORTED_NOT_LINKED';
  statusLabel: string;
}

export interface ThemeSecurityIndex {
  entries: ThemeSecurityEntry[];
  unlinkedReports: UnlinkedReportedMove[];
  totals: {
    securities: number;
    occurrences: number;
    eventsWithParticipants: number;
    unlinkedReports: number;
  };
}

const EVIDENCE_ORDER: EvidenceLevel[] = ['BUSINESS_VERIFIED', 'REPORT_NAMED'];
const CATEGORY_ORDER: ParticipantCategory[] = [
  'MECHANISM_DIRECT', 'MARKET_PARTICIPANT', 'SPILLOVER', 'INSUFFICIENT',
];

/** 中文名称排序（稳定；同名再按 security_id） */
function compareEntries(a: ThemeSecurityEntry, b: ThemeSecurityEntry): number {
  const byName = a.name.localeCompare(b.name, 'zh-Hans-CN');
  if (byName !== 0) return byName;
  return a.securityId.localeCompare(b.securityId);
}

/** 参与者 → 一次出现记录 */
function occurrenceOf(e: HistoricalEvent, p: HistoricalParticipant): SecurityOccurrence {
  const moves = e.observed_performance?.reported_same_day_moves ?? {};
  const mp = e.market_performance;
  const perf = mp?.by_security?.[p.security_id];
  // ★ 只做**精确匹配**：`security_id` 或 `ticker` 与 key 完全相等。
  //   不做大小写/前缀/名称模糊匹配 —— 猜错身份比留空更糟。
  const exactMove = moves[p.security_id] ?? moves[p.ticker];
  return {
    eventId: e.event_id,
    year: e.year,
    eventLabel: e.label,
    eventClass: e.event_class,
    category: p.category,
    evidenceLevel: p.evidence_level,
    rationale: p.rationale,
    source: p.source,
    note: p.note,
    businessMechanism: p.business_mechanism,
    businessMechanismCaveat: p.business_mechanism_caveat,
    reportedMove: p.reported_move,
    eventReportedMove: exactMove,
    hasMarketPerformance: Boolean(perf),
    marketWindow: mp?.window ?? null,
    marketData: p.market_data,
    periodReturnPct: perf?.period_return_pct ?? p.period_return_pct,
    toHighPct: perf?.to_high_pct ?? p.to_high_pct,
    highDate: perf?.high?.date ?? p.high_date,
    excessPeriodPp: perf?.excess_period_pp ?? p.excess_period_pp,
    excessToHighPp: perf?.excess_to_high_pp ?? p.excess_to_high_pp,
  };
}

/**
 * ★★ 主函数：从题材文档生成标的索引（纯函数，确定性）。
 */
export function themeSecurityIndexOf(doc: HistoricalEventsDoc): ThemeSecurityIndex {
  const byId = new Map<string, ThemeSecurityEntry>();
  const unlinkedReports: UnlinkedReportedMove[] = [];
  let occurrences = 0;
  let eventsWithParticipants = 0;

  for (const e of doc.events ?? []) {
    const participants = e.participants ?? [];
    if (participants.length > 0) eventsWithParticipants += 1;

    for (const p of participants) {
      occurrences += 1;
      const occ = occurrenceOf(e, p);
      const existing = byId.get(p.security_id);
      if (!existing) {
        byId.set(p.security_id, {
          securityId: p.security_id,
          ticker: p.ticker,
          name: p.name,
          aliases: [],
          exchange: p.exchange,
          eventCount: 1,
          years: [e.year],
          evidenceLevels: p.evidence_level ? [p.evidence_level] : [],
          categories: [p.category],
          occurrences: [occ],
        });
        continue;
      }
      // ★ 先记住「本次之前」的最晚年份 —— 之后 push 会把 e.year 算进去，
      //   那样 `e.year >= latestYear` 恒真，同一年里就变成「最后遇到的名称获胜」。
      const prevLatestYear = existing.years.length > 0
        ? Math.max(...existing.years)
        : Number.NEGATIVE_INFINITY;

      existing.eventCount += 1;
      if (!existing.years.includes(e.year)) existing.years.push(e.year);
      if (p.evidence_level && !existing.evidenceLevels.includes(p.evidence_level)) {
        existing.evidenceLevels.push(p.evidence_level);
      }
      if (!existing.categories.includes(p.category)) existing.categories.push(p.category);
      existing.occurrences.push(occ);

      // 名称变化：保留别名；展示名取**最近年份**的名称，
      // ★ 同一年出现多个名称时取**字典序最小** —— 与事件出现顺序无关（确定性）。
      if (p.name !== existing.name) {
        if (!existing.aliases.includes(p.name)) existing.aliases.push(p.name);
        const fromNewerYear = e.year > prevLatestYear;
        const sameYearTieBreak = e.year === prevLatestYear
          && p.name.localeCompare(existing.name, 'zh-Hans-CN') < 0;
        if (fromNewerYear || sameYearTieBreak) {
          if (!existing.aliases.includes(existing.name)) existing.aliases.push(existing.name);
          existing.name = p.name;
        }
      }
      if (!existing.exchange && p.exchange) existing.exchange = p.exchange;
    }

    // ★ 报道点名但未关联到参与者的代码：**独立状态**，不并入任何标的
    const moves = e.observed_performance?.reported_same_day_moves ?? {};
    const ids = new Set(participants.map((p) => p.security_id));
    const tickers = new Set(participants.map((p) => p.ticker));
    for (const [code, move] of Object.entries(moves)) {
      if (ids.has(code) || tickers.has(code)) continue;   // 精确匹配 → 已在上面关联
      unlinkedReports.push({
        eventId: e.event_id,
        year: e.year,
        eventLabel: e.label,
        code,
        move,
        status: 'REPORTED_NOT_LINKED',
        statusLabel: '同期报道点名 · 尚未关联标的记录',
      });
    }
  }

  const entries = [...byId.values()].map((x) => ({
    ...x,
    // 别名去重（可能与展示名相同）
    aliases: [...new Set(x.aliases)].filter((n) => n !== x.name),
    years: [...x.years].sort((a, b) => a - b),
    evidenceLevels: EVIDENCE_ORDER.filter((lv) => x.evidenceLevels.includes(lv)),
    categories: CATEGORY_ORDER.filter((c) => x.categories.includes(c)),
    occurrences: [...x.occurrences].sort((a, b) => a.year - b.year || a.eventId.localeCompare(b.eventId)),
  })).sort(compareEntries);

  return {
    entries,
    unlinkedReports,
    totals: {
      securities: entries.length,
      occurrences,
      eventsWithParticipants,
      unlinkedReports: unlinkedReports.length,
    },
  };
}

/**
 * ★ 按名称 / 代码 / 别名过滤（**纯函数**，供 UI 与测试共用）。
 * 空查询 → 原样返回；不改变排序（不按命中位置重排）。
 */
export function filterSecurityIndex(
  index: ThemeSecurityIndex,
  query: string,
): ThemeSecurityIndex {
  const q = query.trim().toLowerCase();
  if (!q) return index;
  const entries = index.entries.filter((x) =>
    x.name.toLowerCase().includes(q)
    || x.securityId.toLowerCase().includes(q)
    || x.ticker.includes(q)
    || x.aliases.some((a) => a.toLowerCase().includes(q)));
  return {
    ...index,
    entries,
    totals: { ...index.totals, securities: entries.length },
  };
}

/** 证据等级的展示文案（**逐次**呈现，不合成单一标签） */
export function evidenceLabelOf(level?: EvidenceLevel): string {
  return level ? EVIDENCE_LEVEL_LABEL[level] : '（未标注证据等级）';
}

/** 该标的的证据等级摘要（`仅报道点名 ×2 · 业务机制已核实 ×1`）—— 只计数，不分高低 */
export function evidenceSummaryOf(entry: ThemeSecurityEntry): string {
  const counts = new Map<EvidenceLevel | 'UNRECORDED', number>();
  for (const o of entry.occurrences) {
    const k = o.evidenceLevel ?? 'UNRECORDED';
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return EVIDENCE_ORDER
    .filter((lv) => counts.has(lv))
    .map((lv) => `${EVIDENCE_LEVEL_LABEL[lv]} ×${counts.get(lv)}`)
    .concat(counts.has('UNRECORDED') ? [`（未标注）×${counts.get('UNRECORDED')}`] : [])
    .join(' · ');
}

/** ★ 必须随索引一起展示的语义边界（UI 原样渲染） */
export const SECURITY_INDEX_DISCLAIMER =
  '★★ **历史参与 ≠ 业务相关 ≠ 行情上涨**：本表只回答「这只股票在哪些历史事件里被记录过、'
  + '当时为什么被纳入」。`仅报道点名`（REPORT_NAMED）= 同期报道提到它，'
  + '**不等于**业务机制已证实；`业务机制已核实`（BUSINESS_VERIFIED）= 业务有独立资料支持，'
  + '**不等于**该业务驱动了当次行情。★ 本表**不**给概念相关度打分，'
  + '**不**跨事件合并收益率（各事件窗口口径不同），**不**按涨幅或出现次数排序。';
