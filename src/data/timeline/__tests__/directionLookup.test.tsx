import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { researchTimelineSource } from '../timelineAdapter';
import { parseCurrentCandidateDataset } from '../currentCandidate';
import canonicalJson from '@current/current_candidates.json';
import { coveredTerms, lookupDirection } from '../directionLookup';
import { DirectionLookupSection } from '../../../components/DirectionLookup/DirectionLookupSection';

/**
 * 方向查询的不变量测试。
 *
 * ★ 用**真实数据**锁住 2026-10-07 两次使用测试得到的「覆盖地图」：
 *   医药健康 = 两侧都有 · 汽车 = 只有历史 · 文化传媒 = 都没有。
 * 这三种情况正是本模块存在的理由 —— 它们必须被明确区分，而不是都给一个空白。
 */

const source = researchTimelineSource();
const dataset = parseCurrentCandidateDataset(canonicalJson).dataset;

describe('directionLookup · 覆盖地图（真实数据）', () => {
  it('★ 医药健康 → 两侧都有（both）', () => {
    const r = lookupDirection('医药健康', source, dataset);
    expect(r.verdict).toBe('both');
    expect(r.current.length).toBeGreaterThanOrEqual(1);
    expect(r.historical.length).toBeGreaterThanOrEqual(1);
  });

  it('★ 汽车 → 只有历史（historical-only）—— 历史很厚，当前侧为空', () => {
    const r = lookupDirection('汽车', source, dataset);
    expect(r.verdict).toBe('historical-only');
    expect(r.current).toHaveLength(0);
    expect(r.historical.length).toBeGreaterThanOrEqual(5);
    // 命中依据必须可解释
    expect(r.historical[0].matchedOn.length).toBeGreaterThan(0);
  });

  it('★ 文化传媒 → 都没有（none）—— 诚实说覆盖不到', () => {
    const r = lookupDirection('文化传媒', source, dataset);
    expect(r.verdict).toBe('none');
    expect(r.current).toHaveLength(0);
    expect(r.historical).toHaveLength(0);
  });

  it('空查询不返回任何结果（不猜）', () => {
    expect(lookupDirection('   ', source, dataset).verdict).toBe('none');
    expect(lookupDirection('', source, dataset).historical).toHaveLength(0);
  });

  it('命中是大小写不敏感的子串匹配', () => {
    expect(lookupDirection('半导体', source, dataset).historical.length).toBeGreaterThan(0);
    expect(lookupDirection('半导体', source, dataset).verdict).not.toBe('none');
  });
});

describe('directionLookup · ★ 语义边界', () => {
  it('结果里**不得**出现任何结构判定字样（查找 ≠ 结构对应）', () => {
    const blob = JSON.stringify([
      lookupDirection('医药健康', source, dataset),
      lookupDirection('汽车', source, dataset),
      lookupDirection('文化传媒', source, dataset),
    ]).toLowerCase();
    for (const banned of [
      'structural_supported',
      'structural_partial',
      'no_valid_correspondence',
      'theme_only',
      'score',
      'ranking',
      'similarity',
      'probability',
    ]) {
      expect(blob, `不得出现: ${banned}`).not.toContain(banned);
    }
  });

  it('覆盖词表是计数事实，不是排序评分', () => {
    const terms = coveredTerms(source, dataset);
    expect(terms.length).toBeGreaterThan(0);
    for (const t of terms) {
      expect(t.term.length).toBeGreaterThan(0);
      expect(t.historicalCount + t.currentCount).toBeGreaterThan(0);
    }
    // 有当前对象的主题必须排在有历史但无当前的主题之前（当前侧是稀缺资源）
    const withCurrent = terms.findIndex((t) => t.currentCount > 0);
    const withoutCurrent = terms.findIndex((t) => t.currentCount === 0);
    if (withCurrent >= 0 && withoutCurrent >= 0) expect(withCurrent).toBeLessThan(withoutCurrent);
  });
});

describe('DirectionLookupSection · 呈现', () => {
  const html = (extra: Record<string, unknown> = {}) =>
    renderToStaticMarkup(
      <DirectionLookupSection source={source} dataset={dataset} {...extra} />,
    );

  it('默认只显示查询入口与覆盖词表（不预设结论）', () => {
    const h = html();
    expect(h).toContain('查一个方向');
    expect(h).toContain('这是查找，不是结构对应');
    expect(h).toContain('能查什么');
    // 未查询时不显示任何判定文案
    expect(h).not.toContain('两侧都有');
  });

  it('未传回调时不渲染历史案例按钮（不给假出口）', () => {
    expect(html()).not.toContain('打开该历史案例');
  });
});
