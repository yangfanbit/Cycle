/**
 * 外部季节性题材日历 —— **外部研究线索**的只读适配器。
 *
 * ## 定位（与现有 SeasonalMap 的**明确区分**）
 *
 * | | 现有 SeasonalMap | 本模块 |
 * |---|---|---|
 * | 数据来源 | ThreeC **从历史数据中得到的**窗口 | **外部资料声称的**季节性线索 |
 * | 性质 | 研究结果 | **外部参考**（未经验证） |
 * | 是否可作结论 | 是（受样本门槛约束） | **否** —— 只是线索 |
 *
 * ★ 两者**不得混为一个没有来源区分的指标体系**。本模块的输出**永远**带
 * `sourceKind: 'EXTERNAL_REFERENCE'`，页面必须显示该来源属性。
 *
 * ## 硬边界
 *
 * - 只读（静态 import，无运行时网络）。
 * - **月份级资料只到月份** —— 不补造日级精度（`precision` 恒为 `MONTH`）。
 * - **窗口活跃 ≠ 研究成熟度** —— 两者是**不同维度**，不得合并。
 * - **不**把外部资料的星级 / 强弱转为分数、排名或置信度。
 * - 无映射时**直接展示 `UNMAPPED`**，不隐藏空白、不自动补结论。
 */
// ★ v0.25：升到 v0_2（25 项逐项核验；v0_1 逐字节保留）
import calendarRaw from '@current/external_seasonal_calendar_v0_2.json';

/* ------------------------------------------------------------------ 类型 */

/** 研究成熟度（★ 与「窗口日期状态」分离） */
export type MaturityLevel =
  | 'EXTERNAL_REFERENCE'
  | 'MAPPED'
  | 'OBSERVING'
  | 'PARTIALLY_VALIDATED'
  | 'THREEC_VALIDATED'
  | 'WEAKENED'
  | 'REJECTED';

/** 当前时间与窗口的关系（★ 由实际日期计算，不是预设值） */
export type WindowRelation =
  | 'IN_WINDOW'
  | 'UPCOMING'
  | 'PASSED'
  | 'NO_FIXED_WINDOW'
  | 'INSUFFICIENT_DATE';

export interface ExternalWindow {
  start_month: number;
  end_month: number;
  /** ★ 跨年窗口（如 12 月至次年 2 月）必须为 true */
  cross_year: boolean;
  raw_text: string;
}

/**
 * ★ v0.25：逐项核验结论（v0_2 起）。
 *
 * 六问逐条落地：性质 / 来源可核实性 / 库内证据 / 反例 / 代表标的 / 处置与下一步。
 * ★ `threec_evidence.campaigns_starting_in_window` 是**机械统计**，
 *   `mechanism_matched` 是**研究判断** —— 两者分开记录，不得互相冒充。
 */
export interface ExternalVerification {
  reviewed_at: string;
  nature: string;
  source_check: { report_available: boolean; note: string };
  threec_evidence: {
    macro_theme: string | null;
    theme_campaigns: number;
    campaigns_starting_in_window: number;
    /** ★ 机制吻合的**库内 Campaign**（研究判断，不是机械统计） */
    mechanism_matched_campaigns: string[];
    /** ★ 机制吻合的**地图事件**（已有历史地图时引用事件 id） */
    mechanism_matched_events: string[];
    map_theme_id: string | null;
    note: string;
  };
  counter_evidence: string[];
  representatives: { security_id: string; name: string; role: string; note: string }[];
  disposition: MaturityLevel;
  reason: string;
  next_step: { kind: 'MAP' | 'OBSERVE' | 'DRAFT' | 'NONE'; target: string | null; text: string };
}

export interface ExternalCalendarEntry {
  id: string;
  name: string;
  category: string;
  windows: ExternalWindow[];
  precision: 'MONTH' | 'NONE';
  source_ids: string[];
  source_note: string | null;
  mapping: {
    status: 'MAPPED' | 'UNMAPPED';
    macro_theme: string | null;
    basis: string | null;
    reason: string | null;
  };
  maturity: MaturityLevel;
  evidence_refs: string[];
  observations: string[];
  window_relation_override?: WindowRelation;
  /** ★ v0.25：逐项核验结论（v0_1 无此字段） */
  verification?: ExternalVerification;
  revision: { date: string; change: string }[];
}

export interface ExternalCalendarSource {
  source_id: string;
  title: string;
  kind: string;
  note: string;
}

export interface ExternalCalendarDoc {
  artifact: string;
  artifact_version: string;
  generated_at: string;
  position: string;
  source_reports: ExternalCalendarSource[];
  entries: ExternalCalendarEntry[];
}

export const MATURITY_LABEL: Record<MaturityLevel, string> = {
  EXTERNAL_REFERENCE: '外部参考',
  MAPPED: '已映射',
  OBSERVING: '观察中',
  PARTIALLY_VALIDATED: '部分验证',
  THREEC_VALIDATED: 'ThreeC 已验证',
  WEAKENED: '已减弱',
  REJECTED: '已拒绝',
};

export const RELATION_LABEL: Record<WindowRelation, string> = {
  IN_WINDOW: '窗口内',
  UPCOMING: '即将进入',
  PASSED: '窗口已过',
  NO_FIXED_WINDOW: '无固定窗口',
  INSUFFICIENT_DATE: '日期不足',
};

/** ★ 展示时必须声明的来源属性 —— 防止与 ThreeC 历史结论混淆 */
export const EXTERNAL_SOURCE_LABEL = '外部资料参考（未由 ThreeC 验证）';

/* ------------------------------------------------------------------ 读取 */

export function externalCalendarDoc(): ExternalCalendarDoc {
  return calendarRaw as unknown as ExternalCalendarDoc;
}

export function externalCalendarEntries(): ExternalCalendarEntry[] {
  return externalCalendarDoc().entries;
}

export function externalSourceById(id: string): ExternalCalendarSource | undefined {
  return externalCalendarDoc().source_reports.find((s) => s.source_id === id);
}

/* ------------------------------------------------------ 窗口关系计算 */

const ymd = (d: Date) => ({
  y: d.getUTCFullYear(),
  m: d.getUTCMonth() + 1,
  day: d.getUTCDate(),
});

/**
 * 判断 `today` 与**单个窗口**的关系。
 *
 * ★ 跨年处理：`start_month > end_month`（或显式 `cross_year`）时，
 *   窗口跨过 12 月 → 次年。此函数是**纯函数**，便于单测覆盖跨年边界。
 *
 * ★ 精度：只比较**月份**（`precision === 'MONTH'`）——
 *   不引入日级判断，避免把月份精度伪装成日级精度。
 */
export function windowRelationOfWindow(w: ExternalWindow, today: string): WindowRelation {
  const d = new Date(`${today}T00:00:00Z`);
  if (Number.isNaN(d.getTime())) return 'INSUFFICIENT_DATE';
  const m = ymd(d).m;

  const { start_month: s, end_month: e } = w;
  const crosses = w.cross_year || s > e;

  if (!crosses) {
    if (m >= s && m <= e) return 'IN_WINDOW';
    if (m === s - 1) return 'UPCOMING';          // 距窗口起点 1 个月
    return 'PASSED';
  }
  // 跨年：例如 s=12, e=2 → 12月、1月、2月 在窗口内
  if (m >= s || m <= e) return 'IN_WINDOW';
  if (m === s - 1) return 'UPCOMING';            // 11 月 → 12 月窗口即将开始
  return 'PASSED';
}

/**
 * 条目级窗口关系。
 * - `window_relation_override` 优先（用于 `NO_FIXED_WINDOW` / `INSUFFICIENT_DATE`）；
 * - 无窗口（`windows.length === 0`）→ `NO_FIXED_WINDOW`；
 * - 多段窗口取**最"近"**的关系（窗口内 > 即将进入 > 窗口已过）。
 */
export function windowRelationOf(entry: ExternalCalendarEntry, today: string): WindowRelation {
  if (entry.window_relation_override) return entry.window_relation_override;
  if (!entry.windows || entry.windows.length === 0) return 'NO_FIXED_WINDOW';

  const order: WindowRelation[] = ['IN_WINDOW', 'UPCOMING', 'PASSED'];
  const rels = entry.windows.map((w) => windowRelationOfWindow(w, today));
  for (const r of order) if (rels.includes(r)) return r;
  return rels[0] ?? 'INSUFFICIENT_DATE';
}

/** 窗口的原始文本（多段用「；」连接）—— 展示用，保留原始口径 */
export function windowTextOf(entry: ExternalCalendarEntry): string {
  if (!entry.windows || entry.windows.length === 0) return '—（无固定窗口）';
  return entry.windows.map((w) => w.raw_text).join('；');
}

/* ------------------------------------------------------ 校验（可测试） */

export interface CalendarValidationIssue {
  entryId: string | null;
  field: string;
  message: string;
}

const MATURITIES: readonly string[] = [
  'EXTERNAL_REFERENCE', 'MAPPED', 'OBSERVING', 'PARTIALLY_VALIDATED',
  'THREEC_VALIDATED', 'WEAKENED', 'REJECTED',
];

/**
 * 结构校验（★ 供测试与 CI 使用）—— 检查：
 * 必填字段、月份范围合法性、跨年标注一致性、成熟度取值、映射字段自洽。
 * ★ **不**检查「语义是否正确」（那需要人工），只检查「形状与自洽」。
 */
export function validateCalendar(doc: ExternalCalendarDoc): CalendarValidationIssue[] {
  const issues: CalendarValidationIssue[] = [];
  const push = (entryId: string | null, field: string, message: string) =>
    issues.push({ entryId, field, message });

  if (!doc.artifact_version) push(null, 'artifact_version', '缺少 artifact_version');
  if (!Array.isArray(doc.entries) || doc.entries.length === 0) {
    push(null, 'entries', 'entries 缺失或为空');
    return issues;
  }

  const seen = new Set<string>();
  for (const e of doc.entries) {
    const id = e.id ?? '(缺 id)';
    if (!e.id) push(null, 'id', '条目缺少 id');
    else if (seen.has(e.id)) push(e.id, 'id', `id 重复：${e.id}`);
    else seen.add(e.id);

    if (!e.name) push(id, 'name', '缺少 name');
    if (!e.category) push(id, 'category', '缺少 category');
    if (!Array.isArray(e.source_ids) || e.source_ids.length === 0) {
      push(id, 'source_ids', '缺少来源（每条必须可追溯）');
    }
    if (!MATURITIES.includes(e.maturity)) {
      push(id, 'maturity', `非法成熟度：${String(e.maturity)}`);
    }
    if (e.precision !== 'MONTH' && e.precision !== 'NONE') {
      push(id, 'precision', `非法精度：${String(e.precision)}（只允许 MONTH / NONE）`);
    }

    for (const w of e.windows ?? []) {
      if (!Number.isInteger(w.start_month) || w.start_month < 1 || w.start_month > 12) {
        push(id, 'windows.start_month', `月份越界：${String(w.start_month)}`);
      }
      if (!Number.isInteger(w.end_month) || w.end_month < 1 || w.end_month > 12) {
        push(id, 'windows.end_month', `月份越界：${String(w.end_month)}`);
      }
      // ★ 跨年标注必须与月份关系一致（start > end ⇒ 必须 cross_year）
      const shouldCross = w.start_month > w.end_month;
      if (shouldCross && !w.cross_year) {
        push(id, 'windows.cross_year', `start(${w.start_month}) > end(${w.end_month}) 但未标 cross_year`);
      }
      if (!shouldCross && w.cross_year && w.start_month !== w.end_month) {
        push(id, 'windows.cross_year', `标了 cross_year 但 start(${w.start_month}) <= end(${w.end_month})`);
      }
      if (!w.raw_text) push(id, 'windows.raw_text', '缺少原始窗口文本');
    }

    // ★ 映射自洽：MAPPED 必须有 theme + basis；UNMAPPED 必须有 reason
    if (e.mapping?.status === 'MAPPED') {
      if (!e.mapping.macro_theme) push(id, 'mapping.macro_theme', 'MAPPED 但无 macro_theme');
      if (!e.mapping.basis) push(id, 'mapping.basis', 'MAPPED 但无 mapping_basis（映射必须有依据）');
    } else if (e.mapping?.status === 'UNMAPPED') {
      if (!e.mapping.reason) push(id, 'mapping.reason', 'UNMAPPED 但未写明原因');
    } else {
      push(id, 'mapping.status', `非法映射状态：${String(e.mapping?.status)}`);
    }

    if (!Array.isArray(e.revision) || e.revision.length === 0) {
      push(id, 'revision', '缺少变更记录（追加式要求）');
    }
  }
  return issues;
}

/** 日历的「月份 → 条目」索引（用于按月份浏览） */
export function entriesByMonth(entries: ExternalCalendarEntry[] = externalCalendarEntries()) {
  const map = new Map<number, ExternalCalendarEntry[]>();
  for (let m = 1; m <= 12; m += 1) map.set(m, []);
  for (const e of entries) {
    for (const w of e.windows ?? []) {
      const crosses = w.cross_year || w.start_month > w.end_month;
      const months: number[] = [];
      if (!crosses) {
        for (let m = w.start_month; m <= w.end_month; m += 1) months.push(m);
      } else {
        for (let m = w.start_month; m <= 12; m += 1) months.push(m);
        for (let m = 1; m <= w.end_month; m += 1) months.push(m);
      }
      for (const m of months) {
        if (!map.get(m)!.includes(e)) map.get(m)!.push(e);
      }
    }
  }
  return map;
}

/** ★ 本模块的用途说明（页面展示用）—— 明确外部属性 */
export const EXTERNAL_CALENDAR_NOTE =
  '本视图记录**外部资料**声称的季节性窗口与题材线索，**不是** ThreeC 的研究结论。'
  + '窗口是否活跃由当前日期计算；「活跃」**不代表**该题材会上涨，也**不提升**研究成熟度。'
  + '所有条目当前均为**外部参考**（未经 ThreeC 验证）。';
