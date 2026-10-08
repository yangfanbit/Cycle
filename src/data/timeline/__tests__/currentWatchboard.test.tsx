import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import {
  buildWatchboard,
  EVIDENCE_DIMENSIONS,
  WATCHBOARD_DISCLAIMER,
} from '../currentWatchboard';
import { CurrentWatchboardSection } from '../../../components/CurrentWatchboard/CurrentWatchboardSection';

/**
 * 「当前观察台」的不变量测试。
 *
 * ★★ 它锁住的核心不是数字，而是**它不是什么**：
 *
 *   用户要的是「在当下这个时间点，提前看到该看什么」。项目**禁止**概率 / 评分 / 预测，
 *   且**一旦给出排序，它就会被当作推荐使用**（= 荐股）。
 *   因此本组件**按阶段分组**（封闭枚举）+ **组内按时间序** + 核心列是「**还缺什么**」。
 *
 *   若有人把它改成「可能性排序」或加进任何数值分，这些断言会失败。
 */

describe('currentWatchboard · 状态陈列（真实数据）', () => {
  it('覆盖当前全部研究对象，且按阶段分组', () => {
    const wb = buildWatchboard();
    expect(wb.total).toBe(6);
    expect(wb.groups.length).toBeGreaterThanOrEqual(2);
    // 分组内的对象数之和 = 总数（无遗漏、无重复）
    expect(wb.groups.reduce((n, g) => n + g.items.length, 0)).toBe(wb.total);
  });

  it('★ 组序 = 生命周期自然序（不是价值序）', () => {
    const ORDER = ['EARLY_SIGNAL', 'THEME_FORMING', 'BROAD_CONFIRMATION', 'EXPANSION', 'PEAK', 'DECLINE', 'END', 'UNKNOWN'];
    const wb = buildWatchboard();
    const idx = wb.groups.map((g) => ORDER.indexOf(g.phase));
    for (let i = 1; i < idx.length; i += 1) expect(idx[i]).toBeGreaterThan(idx[i - 1]);
  });

  it('★ 组内按**阶段起点时间序**（早的在前），起点缺失者排最后', () => {
    const wb = buildWatchboard();
    for (const g of wb.groups) {
      const dated = g.items.filter((x) => x.phaseStart).map((x) => x.phaseStart as string);
      for (let i = 1; i < dated.length; i += 1) expect(dated[i] >= dated[i - 1]).toBe(true);
      const firstUndated = g.items.findIndex((x) => !x.phaseStart);
      if (firstUndated >= 0) {
        for (let i = firstUndated; i < g.items.length; i += 1) expect(g.items[i].phaseStart).toBeNull();
      }
    }
  });

  it('★ 「还缺什么」来自三态证据里仍为「初现 / 未标注」的维度', () => {
    const wb = buildWatchboard();
    const bci = wb.groups.flatMap((g) => g.items).find((x) => x.candidateId === 'CC-2026-BCI-MEDTECH')!;
    // 该对象：广度=EMERGING、信息边际=EMERGING、叙事=PRESENT
    expect(bci.evidence.breadth).toBe('EMERGING');
    expect(bci.evidence.narrative).toBe('PRESENT');
    expect(bci.gaps).toContain('广度');
    expect(bci.gaps).toContain('信息边际');
    expect(bci.gaps).not.toContain('叙事');

    // 三维均已现的对象 → 缺口为空（不编造缺口）
    const emb = wb.groups.flatMap((g) => g.items).find((x) => x.candidateId === 'CC-2026-EMBODIED-AI')!;
    expect(emb.gaps).toEqual([]);
  });

  it('阶段起点与「距记录日天数」由快照日计算，不用「今天」（避免漂移）', () => {
    const wb = buildWatchboard();
    const bci = wb.groups.flatMap((g) => g.items).find((x) => x.candidateId === 'CC-2026-BCI-MEDTECH')!;
    expect(bci.phaseStart).toBe('2026-06-30');
    expect(bci.snapshotDate).toBe('2026-09-15');
    expect(bci.daysSincePhaseStart).toBe(77);
  });

  it('★ 缺口计数是**计数事实**，覆盖三个维度', () => {
    const wb = buildWatchboard();
    for (const d of EVIDENCE_DIMENSIONS) {
      expect(typeof wb.gapCounts[d.label]).toBe('number');
      expect(wb.gapCounts[d.label]).toBeGreaterThanOrEqual(0);
      expect(wb.gapCounts[d.label]).toBeLessThanOrEqual(wb.total);
    }
  });

  it('★★ 语义边界：视图模型**不含**任何 score / 概率 / 排名字段', () => {
    const wb = buildWatchboard();
    const keys = [
      ...Object.keys(wb),
      ...Object.keys(wb.groups[0]),
      ...Object.keys(wb.groups[0].items[0]),
    ].map((x) => x.toLowerCase());
    for (const banned of ['score', 'rating', 'rank', 'probability', 'prediction', 'weight']) {
      expect(keys.some((x) => x.includes(banned))).toBe(false);
    }
  });

  it('★★ 声明必须写明「不等于」与既定的否定式措辞', () => {
    expect(WATCHBOARD_DISCLAIMER).toContain('不等于');
    expect(WATCHBOARD_DISCLAIMER).toContain('不评分、不排名');
    expect(WATCHBOARD_DISCLAIMER).toContain('非预测');
  });
});

describe('CurrentWatchboardSection · 渲染', () => {
  it('渲染阶段分组、「还缺什么」与语义声明', () => {
    const html = renderToStaticMarkup(<CurrentWatchboardSection />);
    expect(html).toContain('当前观察台');
    expect(html).toContain('主题形成');
    expect(html).toContain('还缺什么');
    expect(html).toContain('脑机接口医疗器械');
    // ★ 声明必须在，且用全库既定的否定式措辞
    expect(html).toContain('不等于');
    expect(html).toContain('不评分、不排名');
    expect(html).toContain('非预测');
    // 不得残留会字面显示的 Markdown 标记
    expect(html).not.toContain('**');
  });

  it('★ 提供「看研究问题」入口（只做导航，不做判定）', () => {
    const html = renderToStaticMarkup(<CurrentWatchboardSection onOpenCandidate={() => {}} />);
    expect(html).toContain('看研究问题');
  });
});
