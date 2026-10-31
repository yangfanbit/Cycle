/**
 * ★★ v0.64 回归：候选详情的命中率显示 —— **0% 与「没有数据」必须区分**。
 *
 * 真实缺陷：`h.hit_rate ? … : '—'` 是 truthy 判断 → `hit_rate === 0`（真实存在、就是 0%）
 * 被显示成「—」，读者会把「一次都没命中」误读成「没有这项数据」。
 * 判据改为显式数值判断；统计口径与排序逻辑不变。
 */
import { describe, it, expect } from 'vitest';
import { pctOrDash } from '../CurrentCandidatesSection';

describe('候选详情：命中率显示', () => {
  it('★★ 0 是有效值 → 「0%」；只有非数值才给「—」', () => {
    expect(pctOrDash(0)).toBe('0%');
    expect(pctOrDash(0.75)).toBe('75%');
    expect(pctOrDash(1)).toBe('100%');
    expect(pctOrDash(0.3333)).toBe('33%');
  });

  it('null / undefined / 非数值 → 「—」（不补 0）', () => {
    expect(pctOrDash(null)).toBe('—');
    expect(pctOrDash(undefined)).toBe('—');
    expect(pctOrDash('0.5')).toBe('—');
    expect(pctOrDash(Number.NaN)).toBe('—');
  });
});
