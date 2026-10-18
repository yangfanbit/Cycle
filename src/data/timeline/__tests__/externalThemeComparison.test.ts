/**
 * ★★ 外部线索 × 宏观主题历史窗口对照（v0.13）—— 数据层。
 * 真实数据：外部日历 25 条 + `themeAnnualRowsOf(researchTimelineSource(), 'macro')`。
 */
import { describe, it, expect } from 'vitest';

import { externalCalendarEntries } from '../externalSeasonalCalendar';
import { compareExternalToTheme, fracToMonthLabel } from '../externalThemeComparison';
import { researchTimelineSource } from '../timelineAdapter';
import { themeAnnualRowsOf } from '../themeAnnualWindow';

const all = externalCalendarEntries();
const macroRows = themeAnnualRowsOf(researchTimelineSource(), 'macro');
const entryOf = (id: string) => all.find((e) => e.id === id)!;

describe('外部 × 历史对照 · 精确匹配', () => {
  it('★★ EXT-12 →「医药健康」，且有历史 MAIN_RISE 窗口', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-12'), macroRows);
    expect(cmp.status).toBe('matched');
    expect(cmp.theme).toBe('医药健康');
    expect(cmp.windows.length).toBeGreaterThan(0);
    expect(cmp.years).toContain(2023);
    expect(cmp.counts.campaign + cmp.counts.candidate).toBeGreaterThan(0);
  });

  it('★★ 场景 1 的真值：流感疫苗对象 MAIN_RISE 在 2–3 月，与外部 9–1 月**不同**', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-12'), macroRows);
    const flu = cmp.windows.find((w) => w.objectId === 'C-2023-PHARMA-FLU')!;
    expect(flu).toBeTruthy();
    // 2023-02-20 → 2023-03-20（原样保留，不裁剪）
    expect(flu.mainRise).toEqual({ start: '2023-02-20', end: '2023-03-20' });
    // 投影后的年内位置 ≈ 13.7%–21.6%（即 2 月中–3 月中）
    expect(flu.startFrac).toBeCloseTo(0.137, 2);
    expect(fracToMonthLabel(flu.startFrac)).toBe('2 月');
    // ★ 页面必须能看出差异：外部窗口是 9–1 月，历史窗口落在 2–3 月
    expect(flu.startFrac * 12).toBeGreaterThan(1);   // 2 月之后才开始
  });

  it('★★ 场景 2 的真值：EXT-14 →「电力（运营端）」，2 段历史窗口', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-14'), macroRows);
    expect(cmp.status).toBe('matched');
    expect(cmp.theme).toBe('电力（运营端）');
    const ids = cmp.windows.map((w) => w.objectId);
    expect(ids).toContain('C-2023-POWEROP-THERMAL');
    expect(ids).toContain('C-2021-POWER-GREEN');
    const thermal = cmp.windows.find((w) => w.objectId === 'C-2023-POWEROP-THERMAL')!;
    expect(thermal.mainRise).toEqual({ start: '2023-01-03', end: '2023-05-29' });
    expect(thermal.objectKind).toBe('campaign');
  });

  it('★★ EXT-23：已映射但**无固定窗口** → 历史窗口仍可显示，外部层为空', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-23'), macroRows);
    expect(cmp.status).toBe('matched');
    expect(cmp.theme).toBe('高端装备');
    expect(cmp.windows.length).toBeGreaterThan(0);
  });

  it('★ 历史窗口保留类型（Campaign / Research Candidate）与原始起止', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-23'), macroRows);
    for (const w of cmp.windows) {
      expect(['campaign', 'candidate']).toContain(w.objectKind);
      if (w.mainRise) {
        expect(w.mainRise.start).toMatch(/^\d{4}-\d{2}-\d{2}$/);
        expect(w.mainRise.end).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      }
    }
    // 高端装备下确有 Research Candidate
    expect(cmp.windows.some((w) => w.objectKind === 'candidate')).toBe(true);
  });

  it('★ 窗口按年份 → 起点 → id 排序（确定性）', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-23'), macroRows);
    const keys = cmp.windows.map((w) => `${w.year}-${w.startFrac}-${w.objectId}`);
    expect(keys).toEqual([...keys].sort());
  });
});

describe('外部 × 历史对照 · 空态与未映射', () => {
  it('★★ EXT-17（场景 3）**未映射** → 没有历史窗口、不给关联', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-17'), macroRows);
    expect(cmp.status).toBe('not-mapped');
    expect(cmp.theme).toBeNull();
    expect(cmp.windows).toEqual([]);
    // 常量里 `**未映射**` 是强调标记；比较前去标记
    const plainNote = cmp.note.split('**').join('');
    expect(plainNote).toContain('未映射');
    expect(plainNote).toContain('≠ 库内不存在相关对象');
  });

  it('★★ 已映射但主题行不存在 → 真实空态（不补造窗口）', () => {
    const fake = {
      ...entryOf('EXT-12'),
      mapping: { status: 'MAPPED' as const, macro_theme: '不存在的主题名', basis: null, reason: null },
    };
    const cmp = compareExternalToTheme(fake, macroRows);
    expect(cmp.status).toBe('no-exact-theme');
    expect(cmp.windows).toEqual([]);
    expect(cmp.note).toContain('没有同名宏观主题行');
    expect(cmp.note).toContain('不补造');
  });

  it('★★ 只做**精确**匹配：不给 macro_theme 就不匹配', () => {
    const noTheme = {
      ...entryOf('EXT-12'),
      mapping: { status: 'MAPPED' as const, macro_theme: null, basis: null, reason: null },
    };
    expect(compareExternalToTheme(noTheme, macroRows).status).toBe('not-mapped');
  });

  it('★ 主题为 null 的未标注行不参与匹配（未标注 ≠ 主题名）', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-12'), macroRows);
    expect(cmp.windows.every((w) => w.objectId.length > 0)).toBe(true);
    // 行里有 null 主题行，但它不会命中任何 macro_theme
    expect(macroRows.some((r) => r.theme === null)).toBe(true);
  });
});

/* ================================================================
 * v0.14：历史窗口的**数量语义**（段数 ≠ 对象数；全主题对象数 ≠ 窗口对象数）
 * ================================================================ */

describe('外部×历史对照 · 计数语义（v0.14 修正）', () => {
  it('★★ EXT-05 国防军工：段数 2，但窗口只涉及 1 Campaign + 1 RC（不是 2 + 5）', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-05'), macroRows);
    expect(cmp.status).toBe('matched');
    expect(cmp.windows.length).toBe(2);                 // 投影段数
    expect(cmp.windowCounts.campaign).toBe(1);          // 去重后
    expect(cmp.windowCounts.candidate).toBe(1);         // 去重后
    // 旧文案错误地把全主题计数（2 Campaign + 5 RC）当成窗口计数 —— 现在分开报
    expect(cmp.counts.campaign + cmp.counts.candidate).toBe(7);
    expect(cmp.windowCounts.campaign + cmp.windowCounts.candidate).toBe(2);
    // 未进入窗口的对象逐条列出，且都带原因
    expect(cmp.objectsOutsideWindows.length).toBe(5);
    for (const o of cmp.objectsOutsideWindows) {
      expect(o.reason).toBe('no-main-rise');
      expect(o.objectId.length).toBeGreaterThan(0);
    }
    // note 必须自己说清「段数」与「去重对象数」的区别
    const plain = cmp.note.split('**').join('');
    expect(plain).toContain('投影段数');
    expect(plain).toContain('按对象去重');
    expect(plain).toContain('未进入窗口');
  });

  it('★★ EXT-12 医药健康：4 段窗口 → 3 Campaign + 1 RC；1 个 RC 无 MAIN_RISE', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-12'), macroRows);
    expect(cmp.windows.length).toBe(4);
    expect(cmp.windowCounts.campaign).toBe(3);
    expect(cmp.windowCounts.candidate).toBe(1);
    expect(cmp.objectsOutsideWindows.map((o) => o.objectId)).toEqual(['RC-2021-TCM']);
    expect(cmp.counts.campaign + cmp.counts.candidate).toBe(5);
  });

  it('★★ 跨年对象多段投影：段数 > 对象数时**不得**把段数当对象数', () => {
    // 消费：14 段窗口只涉及 11 Campaign + 2 RC = 13 个对象（至少一个对象有多段）
    const cmp = compareExternalToTheme(entryOf('EXT-02'), macroRows);
    expect(cmp.windows.length).toBe(14);
    expect(cmp.windowCounts.campaign + cmp.windowCounts.candidate).toBeLessThan(14);
    // 每个窗口段都能在去重对象集合里找到
    const ids = new Set(cmp.windows.map((w) => w.objectId));
    expect(ids.size).toBe(cmp.windowCounts.campaign + cmp.windowCounts.candidate);
  });

  it('★ 无 outside 时不显示该块信息（note 不出现「未进入窗口」）', () => {
    const cmp = compareExternalToTheme(entryOf('EXT-14'), macroRows);
    expect(cmp.windows.length).toBe(2);
    expect(cmp.objectsOutsideWindows).toEqual([]);
    expect(cmp.note).not.toContain('未进入窗口');
  });

  it('★ 未映射 / 无主题行：计数全为 0，不出现窗口数字', () => {
    const unmapped = compareExternalToTheme(entryOf('EXT-17'), macroRows);
    expect(unmapped.windowCounts).toEqual({ campaign: 0, candidate: 0 });
    expect(unmapped.objectsOutsideWindows).toEqual([]);
  });
});
