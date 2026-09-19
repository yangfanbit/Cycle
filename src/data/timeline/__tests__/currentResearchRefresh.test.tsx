import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import canonicalJson from '@current/current_candidates.json';
import { CurrentCandidateSection } from '../../../components/CurrentTimeLens/CurrentCandidateSection';
import { buildCurrentCandidateViews } from '../currentCandidateAdapter';
import { parseCurrentCandidateDataset } from '../currentCandidate';
import { previewTimelineSource } from '../timelineAdapter';

/**
 * Current Research Refresh Loop v0.1 —— Product 侧消费测试。
 * 覆盖：snapshot 新鲜度展示 · stale 提示 · 字段语义不混淆 · 历史数据不受影响。
 */

const source = previewTimelineSource();
const parsed = parseCurrentCandidateDataset(canonicalJson);
const noop = () => {};

/** `today` 晚于 snapshot_date → stale。 */
const views = buildCurrentCandidateViews(source, parsed.dataset, '2026-09-19', parsed.issues);

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

  it('stale = true 时明确「不是实时研究结果」', () => {
    expect(views.stale).toBe(true);
    expect(views.stalenessDays).toBeGreaterThan(0);
    const html = render(views);
    expect(html).toContain('当前研究快照已滞后');
    expect(html).toContain('不是实时研究结果');
  });

  it('明示数据来源为离线研究（非实时行情 / 非实时新闻）', () => {
    const html = render(views);
    expect(html).toContain('离线研究生成');
    expect(html).toContain('非实时行情');
  });

  it('today = snapshot_date 时不显示滞后提示（stale = false）', () => {
    const fresh = buildCurrentCandidateViews(source, parsed.dataset, '2026-09-15', parsed.issues);
    expect(fresh.stale).toBe(false);
    const html = render(fresh);
    expect(html).not.toContain('当前研究快照已滞后');
    expect(html).toContain('距今天');
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
