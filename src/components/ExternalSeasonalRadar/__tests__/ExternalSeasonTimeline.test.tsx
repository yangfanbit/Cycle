/**
 * ★★ 外部季节性参考时间轴（v0.12）—— 完整覆盖 / 跨年 / 无窗口 / 来源区分。
 *
 * 全部用仓库真实数据（`external_seasonal_calendar_v0_1.json` 的 25 条）。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { externalCalendarEntries } from '../../../data/timeline/externalSeasonalCalendar';
import {
  buildExternalTimeline,
  dateToMonthFraction,
  fracToMonthFraction,
  monthToMonthFraction,
  segmentsOfWindow,
} from '../../../data/timeline/externalSeasonalTimeline';
import { eventMapByExternalId } from '../../../data/timeline/historicalEventMaps';
import { ExternalSeasonTimeline } from '../ExternalSeasonTimeline';

import { researchTimelineSource } from '../../../data/timeline/timelineAdapter';
import { themeAnnualRowsOf } from '../../../data/timeline/themeAnnualWindow';

const all = externalCalendarEntries();
const macroRows = themeAnnualRowsOf(researchTimelineSource(), 'macro');
const t = buildExternalTimeline(all);
const html = renderToStaticMarkup(
  <ExternalSeasonTimeline
    entries={all}
    allEntries={all}
    categories={['ALL']}
    category="ALL"
    onCategory={() => {}}
    onOpenMap={() => {}}
    macroRows={macroRows}
    today="2026-10-18"
  />,
);
const text = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

describe('外部时间轴 · 完整覆盖', () => {
  it('★★ 25 条全部有位置：23 条上轴 + 2 条无固定窗口', () => {
    expect(t.totals).toMatchObject({
      entries: 25,
      withWindow: 23,
      withoutWindow: 2,
      windows: 24,
      segments: 28,
      crossYearWindows: 4,
      mapped: 16,
      unmapped: 9,
    });
    expect(t.axisRows).toHaveLength(23);
    expect(t.noWindowRows.map((r) => r.entry.id)).toEqual(['EXT-23', 'EXT-24']);
    // 渲染层：23 行 + 2 条无窗口条目
    expect((html.match(/data-est-row=/g) ?? [])).toHaveLength(23);
    expect((html.match(/data-est-nowin-id=/g) ?? [])).toHaveLength(2);
  });

  it('★★ 每条名称都出现在页面上（无遗漏）', () => {
    for (const e of all) {
      expect(text, e.id).toContain(e.name);
    }
  });

  it('★★ 12 个月表头齐全，且填充格数与段数自洽', () => {
    for (let m = 1; m <= 12; m += 1) {
      expect(html).toContain(`>${m}月<`);
    }
    // 每月填充格数 = 该月有窗口的条目数
    for (let m = 1; m <= 12; m += 1) {
      const expected = t.axisRows.filter((r) => r.segments.some((s) => s.months.includes(m))).length;
      const actual = (html.match(new RegExp(`data-month="${m}" data-active="1"`, 'g')) ?? []).length;
      expect(actual, `${m} 月`).toBe(expected);
    }
  });
});

describe('外部时间轴 · 跨年窗口', () => {
  it('★★ EXT-11（10 月至次年 3 月）拆成 [10,11,12] + [1,2,3]', () => {
    const row = t.axisRows.find((r) => r.entry.id === 'EXT-11')!;
    expect(row.segments.map((s) => s.months)).toEqual([[10, 11, 12], [1, 2, 3]]);
    expect(row.segments.every((s) => s.fromCrossYear)).toBe(true);
  });

  it('★★ EXT-21（3 月 + 11 月至次年 1 月）拆成 3 段', () => {
    const row = t.axisRows.find((r) => r.entry.id === 'EXT-21')!;
    expect(row.segments.map((s) => s.months)).toEqual([[3], [11, 12], [1]]);
    // 排序起点 = 第一个窗口的起始月（3），不是 min（1）
    expect(row.firstMonth).toBe(3);
  });

  it('★ 跨年窗口的两段都保留原文（不拼接、不改写）', () => {
    const row = t.axisRows.find((r) => r.entry.id === 'EXT-11')!;
    expect(row.segments[0].rawText).toBe(row.segments[1].rawText);
    expect(row.segments[0].rawText).toContain('次年');
  });

  it('★★ 只输出月份，不产生任何日级日期', () => {
    for (const row of t.axisRows) {
      for (const seg of row.segments) {
        expect(seg.months.every((m) => m >= 1 && m <= 12)).toBe(true);
        expect(JSON.stringify(seg.months)).not.toMatch(/\d{2}-\d{2}/);
      }
    }
    // 页面里不出现「YYYY-MM-DD」形式的日期
    expect(text).not.toMatch(/\d{4}-\d{2}-\d{2}/);
  });

  it('★ 跨年窗口只有 4 条（与源数据一致）', () => {
    const crossIds = all.filter((e) => (e.windows ?? []).some(
      (w) => w.cross_year || w.start_month > w.end_month,
    )).map((e) => e.id);
    expect(crossIds.sort()).toEqual(['EXT-10', 'EXT-11', 'EXT-12', 'EXT-21']);
  });
});

describe('外部时间轴 · 无固定窗口与映射状态', () => {
  it('★★ EXT-23 / EXT-24 在「事件驱动 / 无固定窗口」区，且不显示月份格', () => {
    const nowin = html.slice(html.indexOf('data-est-nowin='));
    expect(nowin).toContain('事件驱动 / 无固定窗口');
    expect(nowin).toContain('EXT-23');
    expect(nowin).toContain('EXT-24');
    // 它们没有月份窗口 → 不上轴
    expect(t.axisRows.some((r) => r.entry.id === 'EXT-23' || r.entry.id === 'EXT-24')).toBe(false);
  });

  it('★★ 9 条 UNMAPPED 正常显示，且不因未映射而被隐藏', () => {
    const unmapped = all.filter((e) => e.mapping.status === 'UNMAPPED');
    expect(unmapped).toHaveLength(9);
    for (const e of unmapped) {
      expect(text, e.id).toContain(e.name);
    }
    expect((html.match(/est-unmapped/g) ?? []).length).toBeGreaterThanOrEqual(9);
  });

  it('★★ 所有条目都带「外部参考」标记（MAPPED 也不例外）', () => {
    // 每条至少有 1 个外部参考徽标 → 25 条
    expect((html.match(/est-ext/g) ?? []).length).toBeGreaterThanOrEqual(25);
    expect(text).toContain('不是');
    expect(text).toContain('ThreeC 的研究结论');
  });
});

describe('外部时间轴 · 历史地图跳转', () => {
  it('★★ 只有索引真有关系时才给跳转；其余明写「未建历史题材地图」', () => {
    const withMap = all.filter((e) => Boolean(eventMapByExternalId(e.id)));
    const withoutMap = all.filter((e) => !eventMapByExternalId(e.id));
    expect(withMap.length).toBe(4);
    expect(withoutMap.length).toBe(21);
    expect((html.match(/est-map-link/g) ?? [])).toHaveLength(4);
    expect((html.match(/est-no-map/g) ?? [])).toHaveLength(21);
    // 跳转按钮带目标题材 id（可被 App 用于选中）
    for (const e of withMap) {
      expect(html).toContain(`data-map-theme="${eventMapByExternalId(e.id)!.theme_id}"`);
    }
  });

  it('★ 未建地图的线索不得出现跳转按钮', () => {
    const noMapBlock = all.filter((e) => !eventMapByExternalId(e.id)).map((e) => e.id);
    expect(noMapBlock).toContain('EXT-01');
    // EXT-01 那一行只有「未建」文案
    const row = html.slice(html.indexOf('data-entry-id="EXT-01"'));
    const rowEnd = row.indexOf('</th>');
    expect(row.slice(0, rowEnd)).toContain('未建历史题材地图');
    expect(row.slice(0, rowEnd)).not.toContain('est-map-link');
  });
});

describe('外部时间轴 · 来源区分', () => {
  it('★★ 明写「外部资料声称」与「ThreeC 的研究结论」，并点名历史季节性地图', () => {
    expect(text).toContain('外部资料声称');
    expect(text).toContain('历史季节性机会地图');
    expect(text).toContain('MAIN_RISE');
    expect(text).toContain('不合并');
  });

  it('★ 徽标沿用既有外部来源标签', () => {
    expect(html).toContain('外部资料参考（未由 ThreeC 验证）');
  });

  it('★ 渲染无字面 Markdown 星号', () => {
    expect(html).not.toContain('**');
  });
});

describe('外部时间轴 · 不给「假按钮」（v0.13）', () => {
  it('★★ 未提供 onOpenMap → 只给事实文本，**不渲染**可点按钮', () => {
    const plain = renderToStaticMarkup(
      <ExternalSeasonTimeline
        entries={all}
        allEntries={all}
        categories={['ALL']}
        category="ALL"
        onCategory={() => {}}
        macroRows={macroRows}
      />,
    );
    expect(plain).not.toContain('est-map-link');
    expect(plain).toContain('本页未接线跳转');
    // 有回调时才出现按钮
    expect(html).toContain('est-map-link');
  });
});

describe('外部时间轴 · 段拆分函数', () => {
  it('★ 非跨年窗口不拆分', () => {
    const segs = segmentsOfWindow({ start_month: 5, end_month: 7, cross_year: false, raw_text: '5–7 月' });
    expect(segs).toHaveLength(1);
    expect(segs[0].months).toEqual([5, 6, 7]);
  });

  it('★ start > end 但未标 cross_year → 仍按跨年处理（防数据漏标）', () => {
    const segs = segmentsOfWindow({ start_month: 11, end_month: 2, cross_year: false, raw_text: '11 月至次年 2 月' });
    expect(segs.map((s) => s.months)).toEqual([[11, 12], [1, 2]]);
  });

  it('★ 单月窗口', () => {
    const segs = segmentsOfWindow({ start_month: 3, end_month: 3, cross_year: false, raw_text: '3 月' });
    expect(segs[0].months).toEqual([3]);
  });
});

/* ================================================================
 * v0.15：公历月日 → 月份坐标（月初落刻度 / 月末落前一格 / 闰年正确）
 * ================================================================ */

describe('dateToMonthFraction（真实公历映射，v0.15）', () => {
  it('★★ 月初：每月 1 日恰好落在该月刻度线上', () => {
    expect(dateToMonthFraction('2023-02-01')).toBeCloseTo(1, 12);   // 2 月刻度
    expect(dateToMonthFraction('2023-07-01')).toBeCloseTo(6, 12);   // 7 月刻度
    expect(dateToMonthFraction('2023-12-01')).toBeCloseTo(11, 12);  // 12 月刻度
    expect(dateToMonthFraction('2023-01-01')).toBeCloseTo(0, 12);   // 年首
  });

  it('★★ 月末：月末落在下一刻度之前（不等于下一月 1 日）', () => {
    expect(dateToMonthFraction('2023-01-31')!).toBeLessThan(1);     // 2 月刻度前
    expect(dateToMonthFraction('2023-01-31')!).toBeGreaterThan(0.9);
    expect(dateToMonthFraction('2023-12-31')!).toBeLessThan(12);
  });

  it('★★ 闰年：2 月按 29 天占位（2024-02-29 合法且接近 3 月刻度前）', () => {
    expect(dateToMonthFraction('2024-02-29')!).toBeGreaterThan(1.9);
    expect(dateToMonthFraction('2024-02-29')!).toBeLessThan(2);
    // 平年 2 月 28 日与闰年 2 月 29 日都合法且都落在 (1,2) 区间
    expect(dateToMonthFraction('2023-02-28')!).toBeLessThan(2);
    // 闰年 1 月 31 日到 2 月 1 日的跨度只跨 1 天，但 2 月内部占 29 天
    const feb1 = dateToMonthFraction('2024-02-01')!;
    const feb29 = dateToMonthFraction('2024-02-29')!;
    expect(feb29 - feb1).toBeCloseTo(28 / 29, 6);
  });

  it('★ 与 frac 近似的区别：2 月 1 日在 frac*12 下不落刻度，在真实日历下落刻度', () => {
    // frac = (dayOfYear(2/1)-1)/365 = 31/365 → *12 ≈ 1.0192（不落刻度）
    expect(fracToMonthFraction(31 / 365)).toBeCloseTo(1.01918, 4);
    expect(fracToMonthFraction(31 / 365)).not.toBeCloseTo(1, 2);
    // dateToMonthFraction 落刻度
    expect(dateToMonthFraction('2023-02-01')).toBeCloseTo(1, 12);
  });

  it('★ 非法日期返回 null（不猜、不补）', () => {
    expect(dateToMonthFraction('2023-02-30')).toBeNull();
    expect(dateToMonthFraction('2023-13-01')).toBeNull();
    expect(dateToMonthFraction('not-a-date')).toBeNull();
    expect(dateToMonthFraction('')).toBeNull();
  });

  it('★ monthToMonthFraction：月 → 月刻度起点', () => {
    expect(monthToMonthFraction(1)).toBe(0);
    expect(monthToMonthFraction(12)).toBe(11);
  });
});
