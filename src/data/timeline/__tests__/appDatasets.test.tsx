import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { selectCurrentCandidateDataset } from '../appDatasets';
import { defaultCurrentCandidateDataset } from '../currentCandidate';
import { lookupDirection } from '../directionLookup';
import { researchTimelineSource } from '../timelineAdapter';
import { DirectionLookupSection } from '../../../components/DirectionLookup/DirectionLookupSection';

/**
 * App 层数据集选取的回归测试（v0.6 · DEF-1）。
 *
 * ## 守护的真实缺陷（P0，2026-10-16 D 工作流发现）
 * `App.tsx` 曾给方向查询传 `dataset = null`（默认路径），于是：
 *   - 默认页面上查「汽车」→ 显示「只有历史案例，当前侧没有研究对象」；
 *   - **同页 Watchboard 却展示着汽车当前候选** → 一页两个相反答案。
 * 之所以长期没被发现：所有组件测试都**直接注入** dataset，接线本身无人断言。
 *
 * 本文件把「默认必须是 canonical」变成**可断言的事实**。
 */

const source = researchTimelineSource();

describe('App 数据集选取（DEF-1 接线回归）', () => {
  it('★★ 默认路径必须给 canonical 数据集，**不得**是 null / 空集', () => {
    const ds = selectCurrentCandidateDataset({ exampleFixture: false });
    expect(ds).toBeTruthy();
    expect(ds.candidates.length).toBe(6);
    // 与 canonical 单例同源（单一数据源）
    expect(ds.candidates.map((c) => c.candidate_id).sort())
      .toEqual(defaultCurrentCandidateDataset().candidates.map((c) => c.candidate_id).sort());
  });

  it('★★ 默认数据集下查「汽车」= both（缺陷复现点：曾错报 historical-only）', () => {
    const ds = selectCurrentCandidateDataset({ exampleFixture: false });
    const r = lookupDirection('汽车', source, ds);
    expect(r.verdict, '默认页面查汽车必须能看到当前研究对象').toBe('both');
    expect(r.current.length).toBeGreaterThan(0);
    expect(r.current.map((h) => h.id)).toContain('CC-2026-AUTO-SMARTDRIVE');
  });

  it('★ 传 null 会退化成 historical-only —— 说明「默认必须给数据集」不是空话', () => {
    // 反向证明：这正是曾经的线上行为（保留为对照，防止有人「顺手改回 null」）
    const r = lookupDirection('汽车', source, null);
    expect(r.verdict).toBe('historical-only');
    expect(r.current).toHaveLength(0);
  });

  it('★ `?candidates=example` 仍走 fixture（显式开启路径未被破坏）', () => {
    const ex = selectCurrentCandidateDataset({ exampleFixture: true });
    const def = selectCurrentCandidateDataset({ exampleFixture: false });
    expect(ex.candidates.length).toBeGreaterThan(0);
    // fixture 与 canonical 不是同一份数据
    expect(ex.candidates.map((c) => c.candidate_id).sort())
      .not.toEqual(def.candidates.map((c) => c.candidate_id).sort());
  });

  it('★★ 用 App 默认数据集渲染方向查询：覆盖词表里当前侧计数不为 0', () => {
    const html = renderToStaticMarkup(
      <DirectionLookupSection
        source={source}
        dataset={selectCurrentCandidateDataset({ exampleFixture: false })}
      />,
    );
    // 「历史 N · 当前 M」——当前侧必须真的能数出对象（缺陷时全为 0）
    const currentCounts = [...html.matchAll(/当前 (\d+)/g)].map((m) => Number(m[1]));
    expect(currentCounts.length).toBeGreaterThan(0);
    expect(Math.max(...currentCounts), '默认页面必须有当前研究对象').toBeGreaterThan(0);
  });
});
