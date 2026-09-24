import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { researchTimelineSource } from '../timelineAdapter';
import {
  BROAD_WINDOW_DAYS,
  seasonalMapRows,
  seasonalMapSummary,
  mainRiseOf,
  projectMainRise,
  themeAnnualRowsOf,
  themeKey,
} from '../themeAnnualWindow';
import { SeasonalMap } from '../../../components/SeasonalMap/SeasonalMap';
import { MacroThemeSheet } from '../../../components/MacroThemeSheet/MacroThemeSheet';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * Product 1.1 第二轮 —— **首页信息架构**回归测试。
 *
 * 上一轮的「逐年 Panorama」被判定为产品抽象错误（一对象一条、逐年铺开 → 历史数据库浏览器）。
 * 本轮把首页重做为「历史季节性机会地图」，锁定五条契约：
 *
 *   1. 纵轴 = **Macro Theme**（一主题一行），**不是**一 Campaign 一行、也**不是**一年一行；
 *   2. 首页只画 **MAIN_RISE（主要炒作）** 在年内的投影，**不画**完整生命周期 / Decline / End；
 *   3. 跨年长周期**不铺满首页** —— 只投影起始月-日一次；
 *   4. Research Candidate 不伪装成正式 Campaign；无 MAIN_RISE 的对象不污染主地图，
 *      但仍留在附页（能力不删除）；
 *   5. Today = **一根**贯穿细红线 + 表头一个日期标记，**不逐行重复** `TODAY`；
 *      统计是**计数事实**，不含概率 / 胜率 / 推荐分 / 预测。
 */

const src = researchTimelineSource();
const allRows = themeAnnualRowsOf(src);
const mapRows = seasonalMapRows(allRows);

function obj(partial: Partial<TimelineCampaign>): TimelineCampaign {
  return {
    campaign_id: 'X-1',
    title: 'x',
    kind: 'campaign',
    start: '2020-01-01',
    end: '2020-06-01',
    lifecycle: [],
    ...partial,
  } as TimelineCampaign;
}

describe('季节性聚合：纵轴 = 大主题（不是对象、不是年份）', () => {
  it('首页行数远小于历史对象数 —— 首页是地图，不是明细库', () => {
    const allObjects = allRows.reduce((n, r) => n + r.objects.length, 0);
    // Historical Universe 共 79 个研究对象
    expect(allObjects).toBe(79);
    // 一主题一行：行数必须是「几十条」而不是「上百条」
    expect(mapRows.length).toBeLessThan(20);
    expect(mapRows.length).toBeLessThan(allObjects / 4);
  });

  it('一行 = 一个大主题，行 key 唯一（同主题多次出现不拆多行）', () => {
    const keys = mapRows.map(themeKey);
    expect(new Set(keys).size).toBe(keys.length);
    // 同一行的窗口可来自多个对象（同主题聚合观察）
    const multi = mapRows.filter((r) => r.occurrences > 1);
    expect(multi.length).toBeGreaterThan(0);
  });

  it('未标注大主题不编造行业名（中性标签 + 排在最后）', () => {
    const unassigned = allRows.filter((r) => r.theme === null);
    expect(unassigned).toHaveLength(1);
    expect(unassigned[0].label).toBe('未标注大主题');
    expect(themeKey(allRows[allRows.length - 1])).toBe('__unassigned__');
  });

  it('没有任何年内窗口的主题不进入首页地图，但对象仍在附页可达', () => {
    const excluded = allRows.filter((r) => r.windows.length === 0);
    expect(excluded.length).toBeGreaterThan(0);
    for (const r of excluded) {
      expect(mapRows).not.toContain(r);
      // 对象没有被丢弃
      expect(r.objects.length).toBeGreaterThan(0);
    }
    // 合计仍是 79（能力不删除，只是不在首页铺开）
    expect(mapRows.reduce((n, r) => n + r.objects.length, 0) + excluded.reduce((n, r) => n + r.objects.length, 0)).toBe(79);
  });
});

describe('首页只画主要炒作（MAIN_RISE），不画完整生命周期', () => {
  it('每条窗口都来自 lifecycle 的 MAIN_RISE 段', () => {
    for (const r of mapRows) {
      for (const w of r.windows) {
        expect(w.mainRise).not.toBeNull();
        const mr = mainRiseOf(w.object);
        expect(mr).not.toBeNull();
        expect(w.mainRise!.start).toBe(mr!.start);
        expect(w.mainRise!.end).toBe(mr!.end);
      }
    }
  });

  it('无 MAIN_RISE 的对象不进入主地图，但仍留在 row.objects（附页可查）', () => {
    const noMainRise = allRows.flatMap((r) => r.objects.filter((o) => mainRiseOf(o) === null));
    expect(noMainRise.length).toBeGreaterThan(0);
    const onMapIds = new Set(mapRows.flatMap((r) => r.windows.map((w) => w.object.campaign_id)));
    for (const o of noMainRise) expect(onMapIds.has(o.campaign_id)).toBe(false);
  });

  it('窗口比例落在年内科，且不出现 Decline / End 阶段语义', () => {
    for (const r of mapRows) {
      for (const w of r.windows) {
        expect(w.startFrac).toBeGreaterThanOrEqual(0);
        expect(w.endFrac).toBeLessThanOrEqual(1);
        expect(w.endFrac).toBeGreaterThanOrEqual(w.startFrac);
      }
    }
  });
});

describe('跨年大周期：不铺满首页', () => {
  it('年内短窗口 → 单段 window', () => {
    const o = obj({ campaign_id: 'A' });
    const out = projectMainRise({ start: '2020-03-01', end: '2020-05-20' }, o);
    expect(out).toHaveLength(1);
    expect(out[0].kind).toBe('window');
    expect(out[0].year).toBe(2020);
  });

  it('跨年但仍是季节性长度（11-01 → 01-15）→ 年裁剪为两段 window', () => {
    const o = obj({ campaign_id: 'B' });
    const out = projectMainRise({ start: '2020-11-01', end: '2021-01-15' }, o);
    expect(out).toHaveLength(2);
    expect(out.every((w) => w.kind === 'window')).toBe(true);
    expect(out.map((w) => w.year)).toEqual([2020, 2021]);
  });

  it('长周期（> 183 天）→ 只投影起始月-日一次（onset），不为中间年份制造虚假密度', () => {
    const o = obj({ campaign_id: 'C', start: '2016-06-01', end: '2021-01-25' });
    const out = projectMainRise({ start: '2016-06-01', end: '2021-01-25' }, o);
    expect(out).toHaveLength(1);
    expect(out[0].kind).toBe('onset');
    expect(out[0].year).toBe(2016);
    // 不铺满：宽度只是标记级，不是整年
    expect(out[0].endFrac - out[0].startFrac).toBeLessThan(0.05);
  });

  it('阈值边界：恰好 183 天仍按季节性窗口处理', () => {
    const o = obj({ campaign_id: 'D' });
    // 2021-01-01 → 2021-07-03 = 183 天
    const out = projectMainRise({ start: '2021-01-01', end: '2021-07-03' }, o);
    expect(out).toHaveLength(1);
    expect(out[0].kind).toBe('window');
    expect(BROAD_WINDOW_DAYS).toBe(183);
  });

  it('真实数据：多年大周期在首页只出现一次起始标记，真实起止原样保留', () => {
    const long = mapRows
      .flatMap((r) => r.windows)
      .filter((w) => w.object.campaign_id === 'C-2016-HIEQ-CONSTR');
    expect(long).toHaveLength(1);
    expect(long[0].kind).toBe('onset');
    expect(long[0].year).toBe(2016);
    // 首页只投影起始位置，但真实 MAIN_RISE 起止**不被裁剪**（tooltip / 附页给全量）
    const mr = mainRiseOf(long[0].object)!;
    expect(mr.start.slice(0, 4)).toBe('2016');
    expect(mr.end.slice(0, 4)).toBe('2021');
    expect(long[0].mainRise).toEqual(mr);
  });
});

describe('Research Candidate 不伪装成正式 Campaign', () => {
  it('candidate 与 campaign 的身份原样透传', () => {
    for (const r of mapRows) {
      for (const w of r.windows) {
        if (w.object.campaign_id.startsWith('RC-')) expect(w.object.kind).toBe('candidate');
        if (w.object.campaign_id.startsWith('C-')) expect(w.object.kind).toBe('campaign');
      }
    }
  });

  it('附页给出 Campaign / RC 的分别计数（不合并成一个数字）', () => {
    for (const r of allRows) {
      expect(r.campaignCount + r.candidateCount).toBe(r.objects.length);
    }
    expect(allRows.some((r) => r.candidateCount > 0)).toBe(true);
  });
});

describe('统计口径：计数事实，不是概率 / 胜率 / 推荐分 / 预测', () => {
  it('occurrences / comparableYears 是确定性计数', () => {
    for (const r of mapRows) {
      expect(r.occurrences).toBeLessThanOrEqual(r.objects.length);
      expect(r.comparableYears).toBe(r.years.length);
      expect(r.years.length).toBeGreaterThan(0);
      expect(r.years).toEqual([...r.years].sort((a, b) => a - b));
    }
  });

  it('共识窗口是中位数聚合（确定性），无 window 时为 null（不编造）', () => {
    for (const r of mapRows) {
      const wins = r.windows.filter((w) => w.kind === 'window');
      if (wins.length === 0) {
        expect(r.consensus).toBeNull();
        continue;
      }
      expect(r.consensus).not.toBeNull();
      const starts = wins.map((w) => w.startFrac).sort((a, b) => a - b);
      const mid = Math.floor(starts.length / 2);
      const want =
        starts.length % 2 === 0 ? (starts[mid - 1] + starts[mid]) / 2 : starts[mid];
      expect(r.consensus!.startFrac).toBeCloseTo(want, 6);
    }
  });

  it('summary 覆盖 2015–2025 且主题数远小于窗口数', () => {
    const s = seasonalMapSummary(mapRows);
    expect(s.yearFrom).toBe(2015);
    expect(s.yearTo).toBe(2025);
    expect(s.themeCount).toBe(mapRows.length);
    expect(s.objectCount).toBeLessThan(79); // 无 MAIN_RISE 的对象不进图
    expect(s.themeCount).toBeLessThan(s.windowCount);
  });
});

describe('SeasonalMap 渲染契约', () => {
  const html = renderToStaticMarkup(
    createElement(SeasonalMap, {
      rows: mapRows,
      today: '2026-09-24',
      openTheme: null,
      onOpenTheme: () => {},
    }),
  );

  it('一行 = 一个大主题（渲染行数 = 主题数，不是对象数）', () => {
    expect((html.match(/class="sm-row/g) ?? []).length).toBe(mapRows.length);
    expect(mapRows.length).toBeLessThan(20);
  });

  it('横轴 1–12 月', () => {
    expect(html).toContain('1月');
    expect(html).toContain('12月');
    expect(html).toContain('sm-months');
  });

  it('每条形只有 win / onset 两类（不出现 decline / ended 等完整生命周期阶段）', () => {
    const kinds = new Set([...html.matchAll(/class="sm-bar ([a-z]+)/g)].map((m) => m[1]));
    expect(kinds.size).toBeGreaterThan(0);
    for (const k of kinds) expect(['win', 'onset']).toContain(k);
    for (const bad of ['declining', 'ended', 'retracement', 'decline']) {
      expect(html).not.toContain(bad);
    }
  });

  it('Today = 一根贯穿细红线 + 表头一个日期标记，不逐行重复 TODAY', () => {
    expect((html.match(/class="today-span"/g) ?? []).length).toBe(1);
    expect(html).not.toContain('today-flag');
    expect(html).not.toContain('>TODAY<');
    expect((html.match(/class="sm-today-mark"/g) ?? []).length).toBe(1);
    expect(html).toContain('09-24');
  });

  it('展示事实统计：历史 N 次 / 覆盖 N 个年份', () => {
    expect(html).toContain('历史 ');
    expect(html).toContain('个年份');
  });

  it('不引入评分 / 排名 / 概率 / 预测 / 胜率 / 推荐分', () => {
    for (const bad of ['score', 'ranking', 'probability', 'prediction', '胜率', '推荐分', '预测']) {
      expect(html.toLowerCase()).not.toContain(bad.toLowerCase());
    }
  });
});

describe('Macro Theme 附页：数据库级细节只在这里', () => {
  const row = allRows.find((r) => r.objects.length > 1)!;
  const html = renderToStaticMarkup(
    createElement(MacroThemeSheet, { row, onClose: () => {}, onOpenCampaign: () => {} }),
  );

  it('按年份列出该主题下的具体历史对象（可进入完整案例）', () => {
    expect((html.match(/class="ts-year"/g) ?? []).length).toBeGreaterThan(0);
    expect((html.match(/class="ts-open"/g) ?? []).length).toBe(row.objects.length);
  });

  it('完整生命周期与「主要炒作」在附页给出（首页不画的部分在这里保留）', () => {
    expect(html).toContain('主要炒作');
    expect(html).toContain('生命周期');
  });

  it('明确声明：历史记录不是概率 / 胜率 / 推荐分 / 预测', () => {
    expect(html).toContain('不是概率、胜率、推荐分或预测');
  });
});
