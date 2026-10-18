/**
 * ★★ 历史阶段的**持续时间**计算（ThreeC 1.3 / v0.9）。
 *
 * ## 为什么单独一个模块
 *
 * 「多久」是一个**容易被编造**的数字：只要有一个起止日期，人就倾向于算出一个天数，
 * 哪怕数据其实是「单日锚点」或「阶段窗口（粗粒度）」。这里把判定**显式化**：
 * 哪些情况能算、哪些情况**必须说不能算**。
 *
 * ## 硬规则（由测试钉死）
 *
 * - `end` 为 `null` → **开放区间** → 不算（研究没给结束日，不是「持续到今天」）
 * - `start === end` → **单日锚点** → 不算（这是「记录在某一天」，不是「只持续一天」）
 * - 缺任一日期 → **缺日期** → 不算
 * - 精度为 `PHASE_WINDOW` → **粗粒度** → 不算精确时长（只显示起止）
 * - 起止倒置 → **源数据异常** → 不算
 * - 无法解析 → **日期不可解析** → 不算
 *
 * ★ 上述任一情况都返回**原因码**，由 UI 原样展示 —— **不得**用 0 天 / 缺失符号冒充。
 */

export type DurationUnavailableReason =
  | 'OPEN_INTERVAL'
  | 'SINGLE_DAY'
  | 'MISSING_DATE'
  | 'LOW_PRECISION'
  | 'REVERSED'
  | 'INVALID';

export interface DurationComputed {
  ok: true;
  /** 日历天数（end − start） */
  days: number;
  /** 含首尾的天数（days + 1） */
  inclusiveDays: number;
  /** 折合月数（按 30.44 天/月，**只作可读近似**） */
  months: number;
}

export interface DurationUnavailable {
  ok: false;
  reason: DurationUnavailableReason;
  /** 人类可读说明（UI 直接显示） */
  label: string;
}

export type StageDuration = DurationComputed | DurationUnavailable;

export const DURATION_REASON_LABEL: Record<DurationUnavailableReason, string> = {
  OPEN_INTERVAL: '开放区间（未记录结束日）→ 无法计算时长',
  SINGLE_DAY: '单日锚点（起止同日）→ 无法计算时长',
  MISSING_DATE: '缺日期 → 无法计算时长',
  LOW_PRECISION: '精度为阶段窗口（粗粒度）→ 不给出精确时长',
  REVERSED: '起止倒置（源数据异常）→ 无法计算时长',
  INVALID: '日期不可解析 → 无法计算时长',
};

/** 视为「精度足够算时长」的精度值 */
const DURATION_OK_PRECISION = new Set(['EXACT_DATE', 'DATE_WINDOW']);

const MS_PER_DAY = 86_400_000;

function parseDay(s: string): number | null {
  // 只接受 YYYY-MM-DD（源数据即此格式）；其它格式一律视为不可解析，**不猜**
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
  const t = Date.parse(`${s}T00:00:00Z`);
  return Number.isFinite(t) ? t : null;
}

/**
 * 计算阶段持续时间。
 *
 * @param start     起始日（`YYYY-MM-DD`；`null` = 未记录）
 * @param end       结束日（`null` = 开放区间）
 * @param precision 源数据精度（`EXACT_DATE` / `DATE_WINDOW` / `PHASE_WINDOW` / 缺省）
 */
export function stageDurationOf(
  start: string | null | undefined,
  end: string | null | undefined,
  precision?: string,
): StageDuration {
  if (!start && !end) return { ok: false, reason: 'MISSING_DATE', label: DURATION_REASON_LABEL.MISSING_DATE };
  if (start && !end) return { ok: false, reason: 'OPEN_INTERVAL', label: DURATION_REASON_LABEL.OPEN_INTERVAL };
  if (!start && end) return { ok: false, reason: 'MISSING_DATE', label: DURATION_REASON_LABEL.MISSING_DATE };

  const a = parseDay(start as string);
  const b = parseDay(end as string);
  if (a == null || b == null) return { ok: false, reason: 'INVALID', label: DURATION_REASON_LABEL.INVALID };
  if (a === b) return { ok: false, reason: 'SINGLE_DAY', label: DURATION_REASON_LABEL.SINGLE_DAY };
  if (b < a) return { ok: false, reason: 'REVERSED', label: DURATION_REASON_LABEL.REVERSED };

  // ★ 精度不足：日期可能有，但只到「阶段窗口」粒度 → 不给精确时长
  if (precision && !DURATION_OK_PRECISION.has(precision)) {
    return { ok: false, reason: 'LOW_PRECISION', label: DURATION_REASON_LABEL.LOW_PRECISION };
  }

  const days = Math.round((b - a) / MS_PER_DAY);
  return {
    ok: true,
    days,
    inclusiveDays: days + 1,
    months: days / 30.44,
  };
}

/** 可读时长：`62 天（约 2.0 个月）` */
export function formatDuration(d: StageDuration): string {
  if (!d.ok) return d.label;
  return `${d.days} 天（约 ${d.months.toFixed(1)} 个月）`;
}
