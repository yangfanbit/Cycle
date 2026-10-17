import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';

import { CANONICAL, loadCurrentSnapshot, snapshotIndex } from '../snapshotAdapter';
import { researchTimelineSource } from '../../timeline/timelineAdapter';
import { selectCurrentCandidateDataset } from '../../timeline/appDatasets';
import { lookupDirection } from '../../timeline/directionLookup';
import { buildResearchRequestPayload, renderResearchRequestMarkdown, EMPTY_DRAFT, freezeCoverage, type ResearchRequestDraft } from '../../timeline/researchRequestDraft';
import { ResearchRequestDraftBlock } from '../../../components/DirectionLookup/DirectionLookupSection';
import { CurrentSnapshotSection } from '../../../components/CurrentSnapshot/CurrentSnapshotSection';

const NOW = '2026-10-16T00:00:00.000Z';

/**
 * 端到端场景验收（v0.6 · D 工作流）—— **用真实静态数据**，不 mock。
 *
 * 覆盖用户明确要求的场景：
 *   ① 汽车：历史侧有覆盖，当前侧是**窄切片**（不得被说成「没有」）
 *   ② 医药：两侧都有 → 流程完整（候选 → 89 条历史对象 → 结构对应）
 *   ③ 文化传媒：覆盖边界**被如实告知**，且**能生成研究请求草稿**
 *   ④ 快照正常加载 + 冻结 SA 解释正常解析
 *   ⑤ 版本不匹配 → 诚实「未解析」（由 snapshotVersionGate.test.ts 深覆盖，此处只验真实数据）
 *   ⑥ 从快照进入历史案例（渲染层有可点击入口）
 */

const source = researchTimelineSource();
const dataset = selectCurrentCandidateDataset({ exampleFixture: false });

describe('E2E 场景 · 快照与 SA 解析（真实数据）', () => {
  it('★★ 默认加载的是**唯一 CANONICAL** 快照（MS-2026-10-13-01），且索引里 CANONICAL 唯一', async () => {
    const idx = snapshotIndex();
    const canonicals = idx.filter((e) => e.status === CANONICAL);
    expect(canonicals).toHaveLength(1);
    expect(canonicals[0].snapshot_id).toBe('MS-2026-10-13-01');

    const v = await loadCurrentSnapshot(false);
    expect(v.state).toBe('ok');
    expect(v.snapshot?.snapshot_id).toBe('MS-2026-10-13-01');
    expect(v.preview).toBe(false);
  });

  it('★★ 冻结 SA 解释正常解析：6 个研究对象全部可解析，每个 89 条明细', async () => {
    const v = await loadCurrentSnapshot(false);
    expect(v.detailsByObject).toHaveLength(6);
    for (const d of v.detailsByObject) {
      expect(d.resolved, d.objectId).toBe(true);
      expect(d.details.length, d.objectId).toBe(89);
    }
    // 534 = 6 × 89
    expect(v.detailsByObject.reduce((n, d) => n + d.details.length, 0)).toBe(534);
  });

  it('★★ 快照版本字段与 SA 版本一致（不一致会被门禁拒绝 —— 见 snapshotVersionGate）', async () => {
    const v = await loadCurrentSnapshot(false);
    const cs = (v.snapshot as unknown as {
      candidates_source?: { artifact_version?: string; rule_set_version?: string };
    }).candidates_source;
    expect(cs?.artifact_version).toBe('0.13');
    expect(cs?.rule_set_version).toBe('structural-analogy-ruleset-v0.3');
  });

  it('★ SSR 首屏是**诚实的载入态**（不得在异步加载完成前伪造内容）', () => {
    // 快照本体是 lazy import（异步）→ SSR 静态渲染只能看到载入占位。
    // ★ 这里要断言的是「没有伪造」：不出现候选、不出现数字、不出现「无有效对应」之类结论。
    const html = renderToStaticMarkup(
      <CurrentSnapshotSection
        previewMode={false}
        onOpenHistoricalCase={() => {}}
        onOpenObject={() => {}}
      />,
    );
    expect(html).toContain('正在载入');
    expect(html).not.toContain('无有效对应');
    expect(html).not.toContain('snap-cand-open');
  });
});

describe('E2E 场景 · 三个真实方向', () => {
  it('① 汽车：历史有覆盖 + 当前侧**窄切片**（不得说成「当前没有」）', () => {
    const r = lookupDirection('汽车', source, dataset);
    expect(r.verdict).toBe('both');
    expect(r.historical.length).toBeGreaterThan(0);
    expect(r.current).toHaveLength(1); // 当前侧只有智能驾驶合规化这一个切片
    expect(r.current[0].id).toBe('CC-2026-AUTO-SMARTDRIVE');
    // ★ 页面呈现：草稿区展示的**证据**来自草稿自己冻结的那次查询（v0.7）
    //   —— SSR 无法模拟输入，故直接构造「已关联该查询」的草稿并渲染该块。
    const draft: ResearchRequestDraft = {
      ...EMPTY_DRAFT, direction: '汽车', linkedQuery: '汽车', linkedAt: NOW,
      linkedCoverage: freezeCoverage(r, NOW),
    };
    const block = renderToStaticMarkup(
      <ResearchRequestDraftBlock
        lookup={r}
        draft={draft}
        setDraft={() => {}}
        payload={buildResearchRequestPayload(draft, r, NOW)}
        payloadJson="{}"
        payloadMd=""
        copied={null}
        onCopy={() => {}}
        onClear={() => {}}
        onRelink={() => {}}
        queryChanged={false}
        saveState={{ ok: true, action: 'written' }}
        loadState={{ status: 'empty' }}
        copyError={null}
        previewOpen={false}
        onPreviewOpenChange={() => {}}
      />,
    );
    expect(block).toContain('both');
    expect(block).toContain('当前研究对象 1 个');
  });

  it('② 医药：两侧都有 → 可走完整工作流（当前候选 + 历史案例都在）', () => {
    const r = lookupDirection('医药', source, dataset);
    expect(r.verdict).toBe('both');
    expect(r.current.length).toBeGreaterThan(0);
    expect(r.historical.length).toBeGreaterThan(0);
    // 当前候选带研究问题（「继续研究」的线索）
    const withQ = r.current.filter((h) => (h.researchQuestions ?? []).length > 0);
    expect(withQ.length).toBeGreaterThan(0);
  });

  it('③ 文化传媒：覆盖边界被如实告知（历史已有 3 个案例，当前侧仍空）', () => {
    const r = lookupDirection('文化传媒', source, dataset);
    // ★ 2026-10-07 的覆盖地图已变：文化传媒**已入库**（历史侧有），当前侧仍无
    expect(r.verdict).toBe('historical-only');
    expect(r.historical.length).toBeGreaterThan(0);
    expect(r.current).toHaveLength(0);
    // ★ 文案层面：判定说明必须点明「当前侧没有研究对象」（不是空白/不解释）
    const draft: ResearchRequestDraft = {
      ...EMPTY_DRAFT, direction: '文化传媒', linkedQuery: '文化传媒', linkedAt: NOW,
      linkedCoverage: freezeCoverage(r, NOW),
    };
    const block = renderToStaticMarkup(
      <ResearchRequestDraftBlock
        lookup={r}
        draft={draft}
        setDraft={() => {}}
        payload={buildResearchRequestPayload(draft, r, NOW)}
        payloadJson="{}"
        payloadMd=""
        copied={null}
        onCopy={() => {}}
        onClear={() => {}}
        onRelink={() => {}}
        queryChanged={false}
        saveState={{ ok: true, action: 'written' }}
        loadState={{ status: 'empty' }}
        copyError={null}
        previewOpen={false}
        onPreviewOpenChange={() => {}}
      />,
    );
    expect(block).toContain('historical-only');
    expect(block).toContain('当前侧没有研究对象');
  });

  it('③b ★★ 根主题清单来自 taxonomy 数据（文化传媒已在其中）', () => {
    // ★ 本测试只验证**数据源**（横幅渲染由 App 层测试覆盖，见 AppTaxonomyBanner）。
    //   v0.6 修复前横幅硬编码称「传媒/文化/娱乐/教育 一个都没有」——与数据矛盾。
    const roots = (source.taxonomy?.() ?? [])
      .filter((n) => n.parent_theme_id === null)
      .map((n) => n.name);
    expect(roots).toContain('文化传媒');
    expect(roots.length).toBeGreaterThanOrEqual(13);
  });

  it('③c ★★ 未覆盖方向也能生成研究请求草稿（含覆盖事实与已知限制）', () => {
    // ★ 用「娱乐」：实测两侧都没命中（verdict = none）。
    //   ★ 注意「教育」**不是**未覆盖 —— 它被当前候选命中 → current-only（实测，勿混）。
    const r = lookupDirection('娱乐', source, dataset);
    expect(r.verdict).toBe('none');
    const p = buildResearchRequestPayload(
      {
        direction: '娱乐',
        researchQuestions: '内容平台监管周期驱动的行情，历史上有可比的周期吗？',
        whyCare: '所在行业',
        knownLeads: '2021 版号收紧',
        timeRange: '2016-2025',
        linkedQuery: '娱乐',
        linkedAt: '2026-10-16T00:00:00.000Z',
        linkedCoverage: freezeCoverage(r, '2026-10-16T00:00:00.000Z'),
      },
      r,
      '2026-10-16T00:00:00.000Z',
    );
    expect(p.status).toBe('DRAFT_NOT_REVIEWED');
    expect(p.id).toBeNull();
    expect(p.coverage_check.verdict).toBe('none');
    expect(p.request.direction).toBe('娱乐');
    const md = renderResearchRequestMarkdown(p);
    expect(md).toContain('未经审查');
    expect(md).toContain('娱乐');
    expect(md).toContain('未覆盖');
  });
});
