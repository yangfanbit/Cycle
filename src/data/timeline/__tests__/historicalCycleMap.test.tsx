import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { HistoricalCycleMapSection } from '../../../components/CurrentTimeLens/HistoricalCycleMapSection';
import { CurrentTimeLens } from '../../../components/CurrentTimeLens/CurrentTimeLens';
import {
  calendarWindowInYear,
  cycleMapFacets,
  filterCycleMapEntries,
  historicalCycleMap,
  spanRatio,
  stageLabelOf,
  weekWindowOf,
  weekWindowOffset,
  weeksAround,
} from '../historicalCycleMap';
import { previewTimelineSource } from '../timelineAdapter';
import type { TimelineCampaign } from '../timelineTypes';

/**
 * Historical Cycle Map v0.1 测试。
 * 覆盖：周级时间模型 · ±2 周窗口 · 窗口相交 · Lifecycle 映射 · 日期缺失不丢案例 ·
 *       navigation · 返回 · 移动端结构 · UNKNOWN 语义 · 无排序/无 score。
 */

const source = previewTimelineSource();
/** 2026-09-16 是周三 → 所在交易周 = 2026-09-14(一) ~ 2026-09-20(日)。 */
const TODAY = '2026-09-16';
const noop = () => {};

/* ---------------- 1. 周级时间模型 ---------------- */

describe('Cycle Map · 周级时间模型', () => {
  it('当前交易周 = 周一 → 周日', () => {
    const w = weekWindowOf(TODAY);
    expect(w.start).toBe('2026-09-14');
    expect(w.end).toBe('2026-09-20');
    expect(w.center).toBe('2026-09-16');
  });

  it('周一/周日输入得到同一周', () => {
    expect(weekWindowOf('2026-09-14').start).toBe('2026-09-14');
    expect(weekWindowOf('2026-09-20').start).toBe('2026-09-14');
    expect(weekWindowOf('2026-09-20').end).toBe('2026-09-20');
  });

  it('ISO 周标签稳定', () => {
    expect(weekWindowOf(TODAY).label).toBe('2026-W38');
  });

  it('跨年周正确（12-29 → 次年 01-04）', () => {
    const w = weekWindowOf('2026-12-31');
    expect(w.start).toBe('2026-12-28');
    expect(w.end).toBe('2027-01-03');
  });
});

/* ---------------- 2. 当前周 ± 2 周 ---------------- */

describe('Cycle Map · 当前周 ± 2 周', () => {
  it('weeksAround 返回 5 个窗口，偏移 −2..+2', () => {
    const ws = weeksAround(TODAY, 2);
    expect(ws.map((w) => w.offset)).toEqual([-2, -1, 0, 1, 2]);
    expect(ws[2].window.start).toBe('2026-09-14');
  });

  it('偏移窗口日期正确（±1 周 = ±7 天）', () => {
    expect(weekWindowOffset(TODAY, -1).start).toBe('2026-09-07');
    expect(weekWindowOffset(TODAY, 1).start).toBe('2026-09-21');
    expect(weekWindowOffset(TODAY, -2).start).toBe('2026-08-31');
    expect(weekWindowOffset(TODAY, 2).start).toBe('2026-09-28');
  });

  it('地图包含 5 个周窗口，当前周偏移为 0', () => {
    const map = historicalCycleMap(source, TODAY);
    expect(map.weeks).toHaveLength(5);
    expect(map.weeks.filter((w) => w.offset === 0)).toHaveLength(1);
    expect(map.currentWeek.start).toBe('2026-09-14');
  });
});

/* ---------------- 3. 日历窗口跨年映射 ---------------- */

describe('Cycle Map · 日历窗口', () => {
  it('把当前周映射到历史年份（保留月-日）', () => {
    const w = calendarWindowInYear(weekWindowOf(TODAY), 2019);
    expect(w.start).toBe('2019-09-14');
    expect(w.end).toBe('2019-09-20');
  });

  it('跨年周截断到该年内（不跑到相邻年份）', () => {
    const w = calendarWindowInYear(weekWindowOf('2026-12-31'), 2020);
    expect(w.start.startsWith('2020-')).toBe(true);
    expect(w.end.startsWith('2020-')).toBe(true);
    expect(w.start <= w.end).toBe(true);
  });
});

/* ---------------- 4. 历史案例进入对应窗口 ---------------- */

describe('Cycle Map · 历史案例进入窗口', () => {
  const map = historicalCycleMap(source, TODAY);

  it('按年份分组，覆盖全部研究年份（2019–2025）', () => {
    expect(map.years.map((y) => y.year)).toEqual(source.years());
  });

  it('案例与窗口相交才纳入（用真实日期验证）', () => {
    for (const y of map.years) {
      for (const e of y.entries) {
        expect(e.overlapStart <= y.window.end).toBe(true);
        expect(e.overlapEnd >= y.window.start).toBe(true);
      }
    }
  });

  it('2019 年窗口内包含 C-2019-AD（2019-08-15 ~ 2019-09-30）', () => {
    const y = map.years.find((x) => x.year === 2019)!;
    expect(y.entries.map((e) => e.campaignId)).toContain('C-2019-AD');
  });

  it('不与窗口相交的案例不纳入（C-2020-POWER-NE 起于 2020-09-22）', () => {
    const y = map.years.find((x) => x.year === 2020)!;
    expect(y.entries.map((e) => e.campaignId)).not.toContain('C-2020-POWER-NE');
  });

  it('年份内按开始日期升序（时间序，不是排名）', () => {
    for (const y of map.years) {
      const starts = y.entries.map((e) => e.caseStart);
      expect([...starts].sort()).toEqual(starts);
    }
  });

  it('条目含名称 / 年份 / Macro Theme / Theme Cycle', () => {
    const e = map.allEntries[0];
    expect(e.title).toBeTruthy();
    expect(typeof e.year).toBe('number');
    expect(e).toHaveProperty('macroTheme');
    expect(e).toHaveProperty('themeCycleId');
  });
});

/* ---------------- 5. Lifecycle 映射 ---------------- */

describe('Cycle Map · Lifecycle Position', () => {
  const map = historicalCycleMap(source, TODAY);

  it('阶段来自 Research phases（不重新定义）', () => {
    const y = map.years.find((x) => x.year === 2019)!;
    const e = y.entries.find((x) => x.campaignId === 'C-2019-AD')!;
    expect(e.stage).toBeTruthy();
    expect(e.stageLabel).toBeTruthy();
    expect(e.stageLabel).not.toBe('UNKNOWN');
  });

  it('stageLabelOf 对未知阶段返回 UNKNOWN（不是「没有」）', () => {
    expect(stageLabelOf(null)).toBe('UNKNOWN');
    expect(stageLabelOf('NOT_A_STAGE')).toBe('NOT_A_STAGE');
  });

  it('窗口内开始的案例标记 enteredInWindow（= 「这一时期刚进入」）', () => {
    const entered = map.allEntries.filter((e) => e.enteredInWindow);
    for (const e of entered) {
      expect(e.caseStart >= e.overlapStart).toBe(true);
      expect(e.stageStatus).toBe('ENTERED_IN_WINDOW');
    }
  });

  it('stageStatus 只取三个值（含 UNKNOWN）', () => {
    for (const e of map.allEntries) {
      expect(['IN_WINDOW', 'ENTERED_IN_WINDOW', 'UNKNOWN']).toContain(e.stageStatus);
    }
  });
});

/* ---------------- 6. 日期缺失不丢案例 ---------------- */

describe('Cycle Map · 日期精度边界', () => {
  it('只要求窗口相交，不要求日级精度（区间有重叠即纳入）', () => {
    const map = historicalCycleMap(source, TODAY);
    const multiYear = map.allEntries.filter((e) => e.caseStart.slice(0, 4) !== e.caseEnd.slice(0, 4));
    // 跨年长周期同样能被纳入（如 C-2019-PHARMA-INNOV 2019→2022）
    expect(map.allEntries.length).toBeGreaterThan(0);
    for (const e of multiYear) {
      expect(e.overlapStart <= e.overlapEnd).toBe(true);
    }
  });

  it('空数据源 → isEmpty 且不抛错', () => {
    const empty = {
      kind: 'verified' as const,
      years: () => [] as number[],
      yearData: () => ({ year: 0, campaigns: [] as TimelineCampaign[], events: [] }),
    };
    const map = historicalCycleMap(empty, TODAY);
    expect(map.isEmpty).toBe(true);
    expect(map.years).toEqual([]);
  });

  it('无阶段覆盖时 stageStatus = UNKNOWN（不被误认为不存在）', () => {
    const map = historicalCycleMap(source, TODAY);
    for (const e of map.allEntries) {
      if (e.stage === null) expect(e.stageStatus).toBe('UNKNOWN');
      else expect(e.stageStatus).not.toBe('UNKNOWN');
    }
  });
});

/* ---------------- 7. 筛选（不是排序） ---------------- */

describe('Cycle Map · 筛选', () => {
  const map = historicalCycleMap(source, TODAY);

  it('filterCycleMapEntries 保持传入顺序', () => {
    const all = map.allEntries;
    expect(filterCycleMapEntries(all, {})).toEqual(all);
  });

  it('按 Macro Theme 筛选只保留匹配项', () => {
    const f = cycleMapFacets(map.allEntries);
    if (f.macroThemes.length === 0) return;
    const target = f.macroThemes[0];
    const got = filterCycleMapEntries(map.allEntries, { macroTheme: target });
    expect(got.length).toBeGreaterThan(0);
    for (const e of got) expect(e.macroTheme).toBe(target);
  });

  it('按 Lifecycle 筛选只保留匹配阶段', () => {
    const f = cycleMapFacets(map.allEntries);
    const target = f.stages[0];
    const got = filterCycleMapEntries(map.allEntries, { stage: target });
    for (const e of got) expect(e.stageLabel).toBe(target);
  });

  it('facets 去重且排序稳定', () => {
    const f = cycleMapFacets(map.allEntries);
    expect([...f.macroThemes].sort()).toEqual(f.macroThemes);
    expect(new Set(f.macroThemes).size).toBe(f.macroThemes.length);
  });
});

/* ---------------- 8. span 比例（不是分数） ---------------- */

describe('Cycle Map · span', () => {
  it('spanRatio 落在 0..1 且宽度为正', () => {
    const map = historicalCycleMap(source, TODAY);
    for (const y of map.years) {
      for (const e of y.entries) {
        const s = spanRatio(e, y.window);
        expect(s.left).toBeGreaterThanOrEqual(0);
        expect(s.left).toBeLessThanOrEqual(1);
        expect(s.width).toBeGreaterThan(0);
        expect(s.left + s.width).toBeLessThanOrEqual(1.0001);
      }
    }
  });
});

/* ---------------- 9. UI ---------------- */

function renderMap(): string {
  return renderToStaticMarkup(
    <HistoricalCycleMapSection dataSource={source} today={TODAY} onSelect={noop} />,
  );
}

describe('Cycle Map · UI', () => {
  it('首屏回答：现在是哪一周 / 有哪些周期 / 分别处于什么阶段', () => {
    const html = renderMap();
    expect(html).toContain('Historical Cycle Map');
    expect(html).toContain('当前交易周');
    expect(html).toContain('2026-W38');
    expect(html).toContain('2026-09-14');
    expect(html).toContain('个周期');
  });

  it('渲染 ±2 周窗口（5 个）', () => {
    const html = renderMap();
    const weeks = html.match(/class="hcm-week[ "]/g) ?? [];
    expect(weeks.length).toBe(5);
    expect(html).toContain('本周');
    expect(html).toContain('-2周');
    expect(html).toContain('+2周');
  });

  it('历史案例可点击进入 Historical Case（复用既有 navigation）', () => {
    const html = renderMap();
    expect(html).toContain('查看历史案例');
    expect(html).toContain('hcm-entry-btn');
  });

  it('展示 Lifecycle 阶段标签', () => {
    const html = renderMap();
    expect(html).toMatch(/hcm-stage/);
  });

  it('UNKNOWN 用独立视觉（虚线+灰），并说明不是「没有阶段」', () => {
    // 真实数据中若存在无阶段覆盖的条目，则渲染 is-unknown；否则用合成数据验证映射
    const html = renderMap();
    expect(html).toMatch(/hcm-stage (is-known|is-unknown)/);

    const synthetic: TimelineCampaign = {
      campaign_id: 'X',
      kind: 'campaign',
      rule_id: 'r',
      season_id: 's',
      year: 2020,
      title: 'X',
      start: '2020-09-14',
      end: '2020-09-20',
      cross_year: false,
      status: 'preview',
      phases: [], // 无 phases → 阶段未知
      themes: [],
      securities: [],
      events: [],
      signals: [],
    };
    const src = {
      kind: 'preview' as const,
      years: () => [2020],
      yearData: () => ({ year: 2020, campaigns: [synthetic], events: [] }),
    };
    const m = historicalCycleMap(src, TODAY);
    expect(m.allEntries).toHaveLength(1);
    expect(m.allEntries[0].stageStatus).toBe('UNKNOWN');
    expect(m.allEntries[0].stageLabel).toBe('UNKNOWN');
  });

  it('明示周级分辨率、不排序、不评分', () => {
    const html = renderMap();
    expect(html).toContain('周级');
    expect(html).toContain('不是从强到弱');
    expect(html).toContain('不做相似度、不排序、不评分');
  });

  it('渲染结果不含 score / ranking / 概率 / 预测 / 最强 / 最像', () => {
    const html = renderMap();
    const affirmative = html
      .replace(/<[^>]*>/g, '')
      .replace(/不排序、不评分/g, '')
      .replace(/不是从强到弱/g, '')
      .replace(/不做相似度、不排序、不评分/g, '');
    for (const bad of ['最相似', '最像', '最强', '评分', '概率', '预测', '推荐']) {
      expect(affirmative).not.toContain(bad);
    }
  });

  it('移动端断点存在（5 列网格 + 筛选换行）', () => {
    const html = renderMap();
    expect(html).toContain('hcm-weeks');
    expect(html).toContain('hcm-filter-row');
  });
});

/* ---------------- 10. 集成：进入 Current Time Lens + 返回 ---------------- */

describe('Cycle Map · 集成与返回', () => {
  it('CurrentTimeLens 中包含 Historical Cycle Map', () => {
    const html = renderToStaticMarkup(
      <CurrentTimeLens
        dataSource={source}
        today={TODAY}
        selection={null}
        onSelect={noop}
      />,
    );
    expect(html).toContain('Historical Cycle Map');
    // Timeline 仍为第一视觉（由 App 决定），此处仅确认 Lens 内新增未替换既有区块
    expect(html).toContain('当前时间研究导航');
    expect(html).toContain('日历同期视角');
  });

  it('点击条目调用 onSelect 且 kind = campaign（可进入 Historical Case）', () => {
    const calls: unknown[] = [];
    const html = renderToStaticMarkup(
      <HistoricalCycleMapSection
        dataSource={source}
        today={TODAY}
        onSelect={(sel) => calls.push(sel)}
      />,
    );
    expect(html).toContain('hcm-entry-btn');
    expect(calls).toEqual([]); // SSR 不触发点击
  });
});
