/**
 * ★★ v0.64 回归：前瞻观察的响应率显示 —— 缺失不得写成「0.0%」。
 *
 * 真实缺陷：台海专项分支写 `((p.stats.response_rate ?? 0) * 100).toFixed(1)` →
 * `response_rate === null`（无可计算值）被补成 0，显示「响应率 0.0%」，
 * 等于把「没有数据」说成「一次都没响应」。
 * 通用统计分支（`PatternRow`）原本就显示「—」，两处口径现在统一。
 */
import { describe, it, expect } from 'vitest';
import { rateText } from '../ForwardObservationSection';

describe('前瞻观察：响应率显示', () => {
  it('★★ null / undefined → 「—」（不得表达为零响应）', () => {
    expect(rateText(null)).toBe('—');
    expect(rateText(undefined)).toBe('—');
    expect(rateText(Number.NaN)).toBe('—');
  });

  it('★ 真实的 0 与其它比例照常显示', () => {
    expect(rateText(0)).toBe('0.0%');
    expect(rateText(0.5)).toBe('50.0%');
    expect(rateText(1 / 3)).toBe('33.3%');
  });
});
