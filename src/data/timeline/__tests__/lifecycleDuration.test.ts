/**
 * ★★ 阶段持续时间的**能算 / 不能算**边界（v0.9）。
 *
 * 核心：只要有一个起止日期，人就倾向于算个天数出来 —— 哪怕数据其实是
 * 「单日锚点」或「阶段窗口」。本文件把「不能算」的每一种情况都钉死。
 */
import { describe, it, expect } from 'vitest';

import {
  DURATION_REASON_LABEL,
  formatDuration,
  stageDurationOf,
} from '../lifecycleDuration';

describe('阶段持续时间', () => {
  it('★ 精度足够（EXACT_DATE）→ 给出天数与近似月数', () => {
    const d = stageDurationOf('2023-01-03', '2023-10-23', 'EXACT_DATE');
    expect(d.ok).toBe(true);
    if (!d.ok) return;
    expect(d.days).toBe(293);
    expect(d.inclusiveDays).toBe(294);
    expect(d.months).toBeCloseTo(9.6, 1);
    expect(formatDuration(d)).toContain('293 天');
    expect(formatDuration(d)).toContain('个月');
  });

  it('★ 精度足够（DATE_WINDOW）→ 也算', () => {
    const d = stageDurationOf('2022-05-01', '2022-07-31', 'DATE_WINDOW');
    expect(d.ok).toBe(true);
    if (d.ok) expect(d.days).toBe(91);
  });

  it('★★ 开放区间（end = null）→ **不算**，并说明原因', () => {
    const d = stageDurationOf('2025-09-01', null, 'EXACT_DATE');
    expect(d.ok).toBe(false);
    if (d.ok) return;
    expect(d.reason).toBe('OPEN_INTERVAL');
    expect(d.label).toContain('开放区间');
    expect(d.label).toContain('无法计算');
  });

  it('★★ 单日锚点（起止同日）→ **不算**（不是「持续 1 天」）', () => {
    const d = stageDurationOf('2024-12-23', '2024-12-23', 'EXACT_DATE');
    expect(d.ok).toBe(false);
    if (d.ok) return;
    expect(d.reason).toBe('SINGLE_DAY');
    expect(d.label).toContain('单日锚点');
    expect(formatDuration(d)).not.toContain('0 天');
  });

  it('★★ 缺日期 → **不算**', () => {
    for (const [s, e] of [[null, null], [null, '2023-01-01'], [undefined, '2023-01-01']] as const) {
      const d = stageDurationOf(s, e, 'EXACT_DATE');
      expect(d.ok).toBe(false);
      if (!d.ok) expect(d.reason).toBe('MISSING_DATE');
    }
  });

  it('★★ 精度为 PHASE_WINDOW（粗粒度）→ 不给精确时长', () => {
    const d = stageDurationOf('2021-01-01', '2021-06-30', 'PHASE_WINDOW');
    expect(d.ok).toBe(false);
    if (d.ok) return;
    expect(d.reason).toBe('LOW_PRECISION');
    expect(d.label).toContain('阶段窗口');
    expect(d.label).toContain('不给出精确时长');
  });

  it('★ 起止倒置 → 源数据异常（不取绝对值假装正常）', () => {
    const d = stageDurationOf('2023-10-23', '2023-01-03', 'EXACT_DATE');
    expect(d.ok).toBe(false);
    if (!d.ok) expect(d.reason).toBe('REVERSED');
  });

  it('★ 日期不可解析 → 不猜', () => {
    for (const [s, e] of [['2023/01/03', '2023-10-23'], ['2023-13-40', '2024-01-01']] as const) {
      const d = stageDurationOf(s, e, 'EXACT_DATE');
      expect(d.ok).toBe(false);
      if (!d.ok) expect(d.reason).toBe('INVALID');
    }
  });

  it('★★ 每个原因都有可读文案（UI 直接显示，不显示裸码）', () => {
    const reasons = Object.keys(DURATION_REASON_LABEL) as (keyof typeof DURATION_REASON_LABEL)[];
    expect(reasons).toHaveLength(6);
    for (const r of reasons) {
      expect(DURATION_REASON_LABEL[r].length).toBeGreaterThan(4);
      expect(DURATION_REASON_LABEL[r]).not.toBe(r);
    }
  });
});
