import { describe, it, expect } from 'vitest';
import {
  THEME_COLOR,
  THEME_ONSET_COLOR,
  UNASSIGNED_COLOR,
  themeColorOf,
  themeOnsetColorOf,
} from '../themeColors';

/**
 * 首页大主题配色的**不变量**测试。
 *
 * 这些是「设计承诺」的机器化表达：如果将来有人把 12 色改成深浅渐变、
 * 或加了一个对比度不足的颜色、或让未知主题静默返回 undefined，
 * 这里会立刻失败。
 */

function relLuminance(hex: string): number {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;
  const f = (c: number) => (c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4));
  return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
}

function contrastWithWhite(hex: string): number {
  return 1.05 / (relLuminance(hex) + 0.05);
}

describe('themeColors · 大主题分类配色', () => {
  it('11 个大主题 + 未标注，主色与浅色表一一对应', () => {
    const themes = Object.keys(THEME_COLOR);
    expect(themes).toHaveLength(11);
    expect(Object.keys(THEME_ONSET_COLOR).sort()).toEqual([...themes].sort());
  });

  it('所有主色互不相同（颜色必须能区分主题，不得重复）', () => {
    const colors = Object.values(THEME_COLOR);
    expect(new Set(colors).size).toBe(colors.length);
  });

  it('★ 对比度不变量：每个主色对白底 ≥ 3:1（9px 细条可见性门槛）', () => {
    for (const [theme, color] of Object.entries(THEME_COLOR)) {
      expect(contrastWithWhite(color), `${theme} ${color}`).toBeGreaterThanOrEqual(3);
    }
    expect(contrastWithWhite(UNASSIGNED_COLOR)).toBeGreaterThanOrEqual(3);
  });

  it('onset 必须是同色相的浅色（比主色更亮），不能比主色更暗', () => {
    for (const theme of Object.keys(THEME_COLOR)) {
      const win = relLuminance(THEME_COLOR[theme]);
      const onset = relLuminance(THEME_ONSET_COLOR[theme]);
      expect(onset, `${theme} onset 应比 win 亮`).toBeGreaterThan(win);
    }
  });

  it('未标注 / 未知主题回落中性灰，不抛错、不返回空', () => {
    expect(themeColorOf(null)).toBe(UNASSIGNED_COLOR);
    expect(themeColorOf('不存在的主题')).toBe(UNASSIGNED_COLOR);
    expect(themeOnsetColorOf(null)).toBe('#C9CED3');
    expect(themeOnsetColorOf('不存在的主题')).toBe('#C9CED3');
  });

  it('已登记主题返回其自身颜色（稳定映射，与年份 / 快照无关）', () => {
    expect(themeColorOf('医药健康')).toBe(THEME_COLOR['医药健康']);
    expect(themeColorOf('资源')).toBe(THEME_COLOR['资源']);
    // 同一次调用两次结果必须一致（无随机、无状态）
    expect(themeColorOf('资源')).toBe(themeColorOf('资源'));
  });
});
