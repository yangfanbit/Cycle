import { describe, expect, it } from 'vitest';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import {
  researchTimelineSource,
  previewTimelineSource,
  verifiedTimelineSource,
} from '../timelineAdapter';
import { HistoricalPanorama } from '../../../components/HistoricalPanorama/HistoricalPanorama';

/**
 * Product 1.1 —— 首页数据源 + Historical Opportunity Panorama + Today 视觉 回归测试。
 *
 * 锁定三条契约（防止后续轮次无声回退到旧 verified 首页）：
 *   1. 首页**默认**数据源 = canonical Research export（`researchTimelineSource()`），
 *      覆盖 52 Campaign + 27 Research Candidate，而非空置的 `data/verified`；
 *   2. `researchTimelineSource()` 与 `verifiedTimelineSource()` 是**不同**来源，
 *      且 Research Candidate 以 `kind === 'candidate'` 与正式 Campaign 区分（不伪装）；
 *   3. Today 视觉：全景只输出**一根**贯穿细红线（`.today-span`），
 *      **不**输出逐行重复的 `TODAY` 标签（`.today-flag`）。
 */

describe('Product 1.1 · 首页默认数据源 = canonical Research export', () => {
  it('researchTimelineSource() 覆盖 52 Campaign + 27 Research Candidate', () => {
    const src = researchTimelineSource();
    const ids = new Map<string, 'campaign' | 'candidate'>();
    for (const y of src.years()) {
      for (const c of src.yearData(y).campaigns) ids.set(c.campaign_id, c.kind);
    }
    const kinds = [...ids.values()];
    expect(kinds.filter((k) => k === 'campaign')).toHaveLength(52);
    expect(kinds.filter((k) => k === 'candidate')).toHaveLength(27);
    expect(ids.size).toBe(79);
  });

  it('年份覆盖 2015–2025（Historical Universe 实际区间）', () => {
    const years = researchTimelineSource().years();
    expect(years[0]).toBe(2015);
    expect(years[years.length - 1]).toBe(2025);
    expect(years).toHaveLength(11);
  });

  it('默认源与 verified 源不同：verified 当前为空（不得把二者混同）', () => {
    const research = researchTimelineSource();
    const verified = verifiedTimelineSource();
    expect(verified.years()).toEqual([]);
    expect(research.years().length).toBeGreaterThan(0);
  });

  it('research 与 preview 是同一实现的两种命名（语义化更名，不产生第二套数据）', () => {
    expect(previewTimelineSource().years()).toEqual(researchTimelineSource().years());
  });

  it('Research Candidate 保留身份区分：candidate 不伪装成正式 Campaign', () => {
    const src = researchTimelineSource();
    const all = src.years().flatMap((y) => src.yearData(y).campaigns);
    for (const c of all) {
      if (c.campaign_id.startsWith('RC-')) {
        // 候选必须标为 candidate；反之正式 Campaign 不得标为 candidate
        expect(c.kind).toBe('candidate');
      } else if (c.campaign_id.startsWith('C-')) {
        expect(c.kind).toBe('campaign');
      }
    }
    // 候选不得携带「正式 Campaign」才有的已核验身份
    const rc = all.filter((c) => c.kind === 'candidate');
    expect(rc.length).toBeGreaterThan(0);
    expect(rc.every((c) => c.status !== 'verified')).toBe(true);
  });
});

describe('Product 1.1 · Historical Opportunity Panorama 结构', () => {
  const src = researchTimelineSource();
  const render = () =>
    renderToStaticMarkup(
      createElement(HistoricalPanorama, {
        dataSource: src,
        today: '2026-09-24',
        year: 2025,
        selection: null,
        onSelect: () => {},
      }),
    );

  it('渲染历史年份行（纵向 = 年份，横向 = 1–12 月）', () => {
    const html = render();
    // 每一年一行
    expect(html.match(/class="pan-row/g)?.length).toBe(11);
    // 月份轴存在
    expect(html).toContain('1月');
    expect(html).toContain('12月');
    expect(html).toContain('pan-month-row');
  });

  it('生命周期分段沿用既有 phase 语义（不新增阶段）', () => {
    const html = render();
    // 至少出现主升 / 高位回撤 / 退潮 三类既有 phase class 之一，且不出现自造阶段名
    const phases = new Set(
      [...html.matchAll(/pan-bar ph-([a-z_]+)/g)].map((m) => m[1]),
    );
    expect(phases.size).toBeGreaterThan(0);
    for (const p of phases) {
      expect([
        'early_signal',
        'main_rise',
        'peak',
        'retracement',
        'declining',
        'ended',
      ]).toContain(p);
    }
  });

  it('Today = 一根贯穿细红线，且**不**逐行重复 TODAY 标签', () => {
    const html = render();
    expect((html.match(/class="today-span"/g) ?? []).length).toBe(1);
    // 不得出现重复的 TODAY 红标签
    expect(html).not.toContain('today-flag');
    expect(html).not.toContain('>TODAY<');
    // 顶部只有一个日期标记
    expect((html.match(/class="pan-today-mark"/g) ?? []).length).toBe(1);
    expect(html).toContain('09-24');
  });

  it('不引入评分 / 排名 / 概率 / 预测语义', () => {
    const html = render();
    for (const bad of ['score', 'ranking', 'probability', 'prediction', '胜率', '推荐']) {
      expect(html.toLowerCase()).not.toContain(bad.toLowerCase());
    }
  });
});
