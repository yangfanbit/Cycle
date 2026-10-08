import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import { themeAnnualRowsOf, seasonalMapRows, type ThemeAnnualRow } from '../themeAnnualWindow';
import {
  seasonalityOf,
  seasonalityByTheme,
  SEASONALITY_NOTE,
  MIN_WINDOWS_FOR_CONCENTRATION,
} from '../themeSeasonality';
import { SeasonalMap } from '../../../components/SeasonalMap/SeasonalMap';

/**
 * 「年内时间集中度」的不变量测试。
 *
 * ## ★★ 它锁住的是「**只报计数**」
 *
 * 用户问「哪些主题受时间因素影响最显著，可以加个特别标注？」—— 数据支持，且**地图原本已有
 * 「集中 X–Y」（共识窗口中位数）**，但**没说有多少个窗口真的落在那里**：资源（3/4）与汽车（6/6）
 * 看起来一样。本层补的就是这个计数。
 *
 * ★ 红线：只输出**计数**，不给强度 / 评分 / 等级，也不声称「明年也会」。
 */

const rows = seasonalMapRows(themeAnnualRowsOf(researchTimelineSource()));
const byLabel = new Map<string, ThemeAnnualRow>(rows.map((r) => [r.label, r]));

describe('themeSeasonality · 年内集中度（真实数据）', () => {
  it('★★ 汽车：6 个年内窗口**全部**落在约两个月内（样本 6 年）', () => {
    const s = seasonalityOf(byLabel.get('汽车')!);
    expect(s.windowCount).toBe(6);
    expect(s.inBand).toBe(6);
    expect(s.concentrated).toBe(true);
    expect(s.band!.from).toBe('05-23');
    expect(s.band!.to).toBe('07-23');
    expect(s.statement).toBe('年内窗口 6 个 · 其中 6 个落在 05-23 ~ 07-23');
  });

  it('★ 资源 / 金融：3/4 达到判据；电子 / 消费（分散）**不**标注', () => {
    expect(seasonalityOf(byLabel.get('资源')!).concentrated).toBe(true);
    expect(seasonalityOf(byLabel.get('金融')!).concentrated).toBe(true);
    // 分散的：电子 2/6、消费 2/4 → 不标注，且 statement 为 null（不编造）
    const el = seasonalityOf(byLabel.get('电子')!);
    expect(el.windowCount).toBe(6);
    expect(el.inBand).toBe(2);
    expect(el.concentrated).toBe(false);
    expect(el.statement).toBeNull();
    expect(seasonalityOf(byLabel.get('消费')!).concentrated).toBe(false);
  });

  it('★ 样本不足（窗口 < 3）不标注 —— 不靠小样本下结论', () => {
    const gj = seasonalityOf(byLabel.get('国防军工')!);
    expect(gj.windowCount).toBe(2);
    expect(gj.inBand).toBe(2); // 2/2 看起来「全中」，但样本太小
    expect(gj.concentrated).toBe(false);
    expect(gj.statement).toBeNull();
    expect(MIN_WINDOWS_FOR_CONCENTRATION).toBe(3);
  });

  it('无常规窗口 → 不编造区间', () => {
    const s = seasonalityOf(byLabel.get('电力设备')!);
    expect(s.windowCount).toBe(0);
    expect(s.band).toBeNull();
    expect(s.statement).toBeNull();
  });

  it('★ 输出只有**计数**，不含任何强度 / 评分 / 概率字段', () => {
    const s = seasonalityOf(byLabel.get('汽车')!);
    const keys = Object.keys(s).map((x) => x.toLowerCase());
    for (const banned of ['score', 'strength', 'rating', 'rank', 'probability', 'level', 'grade']) {
      expect(keys.some((x) => x.includes(banned))).toBe(false);
    }
  });

  it('★★ 语义边界：必须写明「是历史计数、不是概率、不代表明年」', () => {
    expect(SEASONALITY_NOTE).toContain('历史计数事实');
    expect(SEASONALITY_NOTE).toContain('不是概率');
    expect(SEASONALITY_NOTE).toContain('明年');
    // ★ 既有护栏禁止地图 HTML 出现这些词 —— 措辞必须绕开，**不放宽护栏**
    for (const bad of ['胜率', '推荐分', '预测', '**']) {
      expect(SEASONALITY_NOTE).not.toContain(bad);
    }
  });

  it('批量计算覆盖全部上地图主题', () => {
    const map = seasonalityByTheme(rows);
    expect(map.size).toBe(rows.length);
    expect(map.get('汽车')!.concentrated).toBe(true);
  });
});

describe('SeasonalMap · 集中度标注渲染', () => {
  const html = renderToStaticMarkup(
    <SeasonalMap rows={rows} today="2026-10-08" openTheme={null} onOpenTheme={() => {}} />,
  );

  it('★ 行内标注带**计数**（N 个窗口中的 M 个），不只是区间', () => {
    expect(html).toContain('个年内窗口中的');
    expect(html).toContain('6 个年内窗口中的 6 个');
  });

  it('★ 达到判据的主题有标记；未达到的没有', () => {
    // 标记是 span.sm-seasonal-flag —— 汽车/资源/金融各一个
    const flags = (html.match(/sm-seasonal-flag/g) ?? []).length;
    expect(flags).toBe(3);
  });

  it('★★ 语义边界说明必须与标注同显', () => {
    expect(html).toContain('历史计数事实');
    expect(html).toContain('不代表该主题');
  });
});
