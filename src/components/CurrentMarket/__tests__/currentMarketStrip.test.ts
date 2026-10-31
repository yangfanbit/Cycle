/**
 * ★★ v0.64 回归：当前市场状态的**空值显示**。
 *
 * 真实缺陷：`CurrentMarketStrip` 原写 `o.aboveMa20 ? '上' : '下'`，而类型允许 `null`
 * （当日没有可比均线）→ `null` 被当成 `false` 显示为「下」，把「不知道」说成「在下方」。
 * 面板其它指标缺值一律显示「—」，唯独均线位置在推断。
 */
import { describe, it, expect } from 'vitest';
import { maPositionLabel } from '../CurrentMarketStrip';

describe('当前市场状态：均线位置三态', () => {
  it('★★ true/false 正常，null 与缺失必须是「—」（不能显示为「下」）', () => {
    expect(maPositionLabel(true)).toBe('上');
    expect(maPositionLabel(false)).toBe('下');
    expect(maPositionLabel(null)).toBe('—');
    expect(maPositionLabel(undefined)).toBe('—');
  });
});
