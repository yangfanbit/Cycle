import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalJson from '@current/current_candidates.json';
import { CurrentCandidateSection } from '../../../components/CurrentTimeLens/CurrentCandidateSection';
import {
  SNAPSHOT_STALE_THRESHOLD_DAYS,
  buildCurrentCandidateViews,
} from '../currentCandidateAdapter';
import { parseCurrentCandidateDataset } from '../currentCandidate';
import { previewTimelineSource } from '../timelineAdapter';

/**
 * Current Research Refresh Loop v0.1 + Snapshot Freshness Polish v0.1 —— Product 侧消费测试。
 * 覆盖：snapshot 新鲜度展示 · stale 阈值（>14 天）· 字段语义不混淆 · 历史数据不受影响。
 */

const source = previewTimelineSource();
const parsed = parseCurrentCandidateDataset(canonicalJson);
const noop = () => {};

/** 真实快照日 = `2026-09-15`。 */
const SNAPSHOT_DATE = parsed.dataset.snapshot_date;

/** 按「距快照 N 天」构造 View（`today` 由 snapshot_date 推进 N 天）。 */
function viewsAfterDays(n: number) {
  const today = addDays(SNAPSHOT_DATE, n);
  return buildCurrentCandidateViews(source, parsed.dataset, today, parsed.issues);
}

/** 纯日期加法（测试内自足，不引入产品实现）。 */
function addDays(iso: string, n: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  const t = new Date(Date.UTC(y, m - 1, d + n));
  return t.toISOString().slice(0, 10);
}

/** 距快照 4 天（= 第二次真实使用的情形）→ **不再** stale。 */
const views = viewsAfterDays(4);
/** 距快照 15 天（刚过阈值）→ stale。 */
const staleViews = viewsAfterDays(15);

function render(list: typeof views): string {
  return renderToStaticMarkup(<CurrentCandidateSection list={list} onSelect={noop} />);
}

describe('Current Research · 快照新鲜度', () => {
  it('展示 snapshot_date / 距今天数 / 历史覆盖年份（语义不混淆）', () => {
    const html = render(views);
    expect(html).toContain('研究快照');
    expect(html).toContain(views.snapshotDate);
    expect(html).toContain('距今天');
    expect(html).toContain('历史研究覆盖至');
    expect(html).toContain(String(views.researchCoverageUntil));
  });

  it('阈值 = 14 天（单一常量，不引入新状态）', () => {
    expect(SNAPSHOT_STALE_THRESHOLD_DAYS).toBe(14);
  });

  it('阈值边界：0 / 4 / 7 / 14 天 → stale = false', () => {
    for (const n of [0, 4, 7, 14]) {
      const v = viewsAfterDays(n);
      expect(v.stalenessDays, `${n} 天`).toBe(n);
      expect(v.stale, `${n} 天`).toBe(false);
    }
  });

  it('阈值边界：15 天 → stale = true', () => {
    const v = viewsAfterDays(15);
    expect(v.stalenessDays).toBe(15);
    expect(v.stale).toBe(true);
  });

  it('★ 真实使用情形（距快照 4 天）不再被判为「已滞后」', () => {
    expect(views.stalenessDays).toBe(4);
    expect(views.stale).toBe(false);
    const html = render(views);
    // 正常快照：不出现滞后提示，但仍完整展示元信息
    expect(html).not.toContain('当前研究快照已滞后');
    expect(html).not.toContain('不是实时研究结果');
    expect(html).toContain('研究快照');
    expect(html).toContain(views.snapshotDate);
    expect(html).toContain('距今天');
    expect(html).toContain('4');
  });

  it('stale warning 只在 > 14 天出现，且文案明确「不是实时研究结果」', () => {
    const staleHtml = render(staleViews);
    expect(staleHtml).toContain('当前研究快照已滞后');
    expect(staleHtml).toContain('不是实时研究结果');
    // 0–14 天全都不出现
    for (const n of [0, 4, 7, 14]) {
      expect(render(viewsAfterDays(n)), `${n} 天`).not.toContain('当前研究快照已滞后');
    }
  });

  it('明示数据来源为离线研究（非实时行情 / 非实时新闻）—— 与 stale 无关，始终展示', () => {
    for (const list of [views, staleViews]) {
      const html = render(list);
      expect(html).toContain('离线研究生成');
      expect(html).toContain('非实时行情');
    }
  });

  it('字段语义不变：snapshot_date / stalenessDays 原样保留（未新增字段）', () => {
    expect(views.snapshotDate).toBe(SNAPSHOT_DATE);
    expect(views.stalenessDays).toBe(4);
    expect(views.researchCoverageUntil).toBe(parsed.dataset.research_coverage_until);
    // 未引入 fresh / aging / expired / freshness score 等新状态
    expect(Object.keys(views).sort()).toEqual([
      'fixture',
      'issues',
      'researchCoverageUntil',
      'snapshotDate',
      'stale',
      'stalenessDays',
      'views',
    ]);
  });

  it('缺少 snapshot_date 时不展示候选（Temporal Firewall 无法工作）', () => {
    const empty = { ...parsed.dataset, snapshot_date: '' };
    const v = buildCurrentCandidateViews(source, empty, '2026-09-19', []);
    const html = renderToStaticMarkup(
      <CurrentCandidateSection list={v} onSelect={noop} />,
    );
    expect(html).toContain('缺少 snapshot_date');
  });
});

describe('Current Research · 与历史数据隔离', () => {
  it('候选 ID 使用 CC-* 命名空间，不混入历史 C-* / RC-*', () => {
    for (const c of parsed.dataset.candidates) {
      expect(c.candidate_id.startsWith('CC-')).toBe(true);
      expect(c.candidate_id.startsWith('C-')).toBe(false);
      expect(c.candidate_id.startsWith('RC-')).toBe(false);
    }
  });

  it('5 个候选全部进入 Product View（数量不漂移）', () => {
    expect(views.views).toHaveLength(5);
    expect(views.views.map((v) => v.candidate.candidate_id).sort()).toEqual(
      parsed.dataset.candidates.map((c) => c.candidate_id).sort(),
    );
  });

  it('历史 Timeline 数据不受 Current Research 影响', () => {
    const years = source.years();
    expect(years.length).toBeGreaterThan(0);
    for (const y of years) expect(source.yearData(y).campaigns.length).toBeGreaterThanOrEqual(0);
  });
});
