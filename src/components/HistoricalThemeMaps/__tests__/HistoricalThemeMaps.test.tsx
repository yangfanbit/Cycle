/**
 * ★★ 历史题材地图（主入口 · v0.10）—— 渲染事实。
 *
 * 只断言「入口存在、题材来自索引、默认渲染第一个题材、概率区块在对应题材内」。
 * 切换交互由 `HistoricalThemeMaps.interaction.test.tsx`（jsdom）覆盖。
 */
import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  HistoricalThemeMaps,
  HISTORICAL_THEME_MAPS_ID,
  themeMapSummaries,
} from '../HistoricalThemeMaps';
import {
  allResolvedEventMaps,
  eventMapEntries,
} from '../../../data/timeline/historicalEventMaps';
import { ExternalSeasonalRadar } from '../../ExternalSeasonalRadar/ExternalSeasonalRadar';

const maps = allResolvedEventMaps();
const summaries = themeMapSummaries(maps);
const html = renderToStaticMarkup(<HistoricalThemeMaps />);

describe('历史题材地图 · 入口', () => {
  it('★★ 首屏直接呈现，带可跳转的 id 与标题（不必先展开外部线索）', () => {
    expect(html).toContain(`id="${HISTORICAL_THEME_MAPS_ID}"`);
    expect(html).toContain('历史题材地图');
    expect(html).toContain('aria-label="历史题材地图"');
  });

  it('★★ 题材清单**来自索引**（不硬编码 4 个题材）', () => {
    const fromIndex = eventMapEntries().map((e) => e.theme_id);
    expect(summaries.map((s) => s.themeId)).toEqual(fromIndex);
    // 每个题材都有一个 tab
    for (const id of fromIndex) expect(html).toContain(`data-theme-id="${id}"`);
    expect((html.match(/role="tab"/g) ?? [])).toHaveLength(fromIndex.length);
  });

  it('★★ 事件数由 doc 现算，且与总数自洽（当前 6+4+2+1=13）', () => {
    const byId = Object.fromEntries(summaries.map((s) => [s.themeId, s.eventCount]));
    expect(byId.FLU).toBe(6);
    expect(byId.POWER_SUMMER).toBe(4);
    expect(byId.MEDIA).toBe(2);
    expect(byId.ROBOTICS).toBe(1);
    const total = summaries.reduce((a, b) => a + b.eventCount, 0);
    expect(total).toBe(13);
    expect(html).toContain(`<strong>${total}</strong> 个历史事件`);
  });

  it('★ 默认渲染**第一个**题材的地图（含事件与标的区）', () => {
    const first = maps[0];
    expect(html).toContain(`htm-panel-${first.theme_id}`);
    expect(html).toContain(first.display.aria_label);
    // 事件卡与标的区都在（复用既有组件，不是新实现）
    expect(html).toContain('fem-list');
    expect(html).toContain('fem-title');
  });

  it('★★ 流感的经验基准概率区块在流感题材内', () => {
    const fluHtml = renderToStaticMarkup(<HistoricalThemeMaps activeThemeId="FLU" />);
    expect(fluHtml).toContain('data-empirical-probability="1"');
    expect(fluHtml).toContain('探索性经验基准概率');
  });

  it('★★ 电力的经验基准概率区块在电力题材内', () => {
    const powerHtml = renderToStaticMarkup(<HistoricalThemeMaps activeThemeId="POWER_SUMMER" />);
    expect(powerHtml).toContain('data-empirical-probability="1"');
    expect(powerHtml).toContain('1 / 7');
  });

  it('★ 文化传媒 / 机器人无跨年份段 → 不渲染概率区块（不显示空壳）', () => {
    for (const id of ['MEDIA', 'ROBOTICS']) {
      const h = renderToStaticMarkup(<HistoricalThemeMaps activeThemeId={id} />);
      expect(h, id).not.toContain('data-empirical-probability');
    }
  });

  it('★★ 声明与外部雷达的来源区别（两者不互相替代）', () => {
    expect(html).toContain('事后重建');
    expect(html).toContain('外部季节性观察雷达');
    expect(html).toContain('从历史数据得到');
    expect(html).toContain('外部资料声称');
  });

  it('★★ 渲染里没有 Markdown 星号', () => {
    for (const id of ['FLU', 'POWER_SUMMER', 'MEDIA', 'ROBOTICS']) {
      const h = renderToStaticMarkup(<HistoricalThemeMaps activeThemeId={id} />);
      expect(h, id).not.toContain('**');
    }
  });
});

describe('外部雷达 · 不再内嵌地图（避免同一批事件渲染两遍）', () => {
  const radar = renderToStaticMarkup(<ExternalSeasonalRadar today="2026-10-18" />);
  const radarWired = renderToStaticMarkup(
    <ExternalSeasonalRadar today="2026-10-18" onOpenMap={() => {}} />,
  );

  it('★★ 已有地图的线索给出**跳转指针**，而不是整块地图', () => {
    // 未注入 onOpenMap → 只给事实说明，不给按钮（不假装可点）
    expect(radar).toContain('该线索已有');
    expect(radar).toContain('历史事件地图');
    expect(radar).not.toContain('在「历史题材地图」中查看');
    // 注入后 → 出现跳转按钮
    expect(radarWired).toContain('在「历史题材地图」中查看');
    // 内嵌地图的标记不应再出现（地图现在只在独立入口渲染）
    expect(radar).not.toContain('data-cross-year="1"');
  });

  it('★ 雷达本身仍在（外部线索职责不变）', () => {
    expect(radar).toContain('外部季节性观察雷达');
    expect(radar).toContain('外部参考');
  });
});
