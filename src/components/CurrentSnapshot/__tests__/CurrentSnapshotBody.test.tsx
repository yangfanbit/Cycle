import { describe, it, expect } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { CurrentSnapshotBody } from '../CurrentSnapshotSection';
import { diffSnapshots } from '../../../data/marketSnapshot/snapshotDiff';
import type { MarketSnapshot } from '../../../data/marketSnapshot/types';
import type { CurrentSnapshotView } from '../../../data/marketSnapshot/snapshotAdapter';

/**
 * 本期快照页面的**呈现不变量**测试。
 *
 * 重点锁住两条设计判断：
 *  1. 「无变化」必须被明确说出来（不是空白）；
 *  2. 「无有效对应」是一等公民 —— 有计数、有说明，不是灰色空态；
 * 外加语义红线：页面不得出现预测 / 建议 / 评分 / 排名类措辞。
 */

function snap(over: Partial<MarketSnapshot> = {}): MarketSnapshot {
  const base: MarketSnapshot = {
    contract: 'market_snapshot',
    market_snapshot_version: '0.3',
    snapshot_id: 'MS-2026-09-15-01',
    snapshot_date: '2026-09-15',
    status: 'DRAFT',
    market_regime: {
      broad_index_state: 'UNKNOWN',
      breadth_state: 'UNKNOWN',
      liquidity_state: 'UNKNOWN',
      risk_appetite_state: 'UNKNOWN',
      beta_note: '未接入行情数据源，四维按诚实空态记 UNKNOWN。',
    },
    research_objects: [
      {
        object_id: 'CC-A',
        object_kind: 'current_candidate',
        display_name: '对象 A',
        macro_theme: '医药健康',
        declared_phase: 'THEME_FORMING',
        resolution_state: 'RESOLVED',
        canonical_drivers: ['POLICY_DRIVEN'],
        evidence_categories: ['POLICY'],
      },
    ],
    observations: [],
    historical_candidates: [
      {
        current_object_id: 'CC-A',
        identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-1' },
        structural_status: 'STRUCTURAL_PARTIAL',
      },
      {
        current_object_id: 'CC-A',
        identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-2' },
        structural_status: 'NO_VALID_CORRESPONDENCE',
      },
      {
        current_object_id: 'CC-A',
        identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-3' },
        structural_status: 'NO_VALID_CORRESPONDENCE',
      },
    ],
  };
  return { ...base, ...over };
}

function view(over: Partial<CurrentSnapshotView> = {}): CurrentSnapshotView {
  const snapshot = snap();
  return {
    state: 'ok',
    preview: false,
    snapshot,
    previous: null,
    diff: null,
    latestDate: snapshot.snapshot_date,
    draftCount: 0,
    detailsByObject: [],
    ...over,
  };
}

const html = (v: CurrentSnapshotView) => renderToStaticMarkup(<CurrentSnapshotBody view={v} />);

describe('CurrentSnapshotBody · 门禁与空态', () => {
  it('★ 无已签发快照时：明确说明原因与下一步，而不是空白', () => {
    const h = html(
      view({ state: 'no-canonical', snapshot: null, draftCount: 2, latestDate: '2026-10-06' }),
    );
    expect(h).toContain('尚无已签发的快照');
    expect(h).toContain('CANONICAL');
    expect(h).toContain('2');
    expect(h).toContain('MONTHLY_RESEARCH_RUNBOOK');
    expect(h).toContain('snapshot=draft');
  });

  it('索引为空时给出首次建立指引', () => {
    const h = html(view({ state: 'empty', snapshot: null, draftCount: 0, latestDate: null }));
    expect(h).toContain('尚未有任何 Market Snapshot');
  });

  it('★ 预览未签发快照时常驻醒目徽章', () => {
    const h = html(view({ preview: true }));
    expect(h).toContain('未签发');
    expect(h).toContain('仅供预览');
  });

  it('已签发时不显示预览徽章', () => {
    expect(html(view({ preview: false }))).not.toContain('仅供预览');
  });
});

describe('CurrentSnapshotBody · 变化是主角', () => {
  it('★ 无变化必须被明确说出来（不是空白）', () => {
    const a = snap();
    const d = diffSnapshots(a, snap({ snapshot_id: 'MS-2' }));
    const h = html(view({ snapshot: a, previous: a, diff: d }));
    expect(h).toContain('无变化');
    expect(h).toContain('没有变化');
  });

  it('有变化时给出总数与分层计数', () => {
    const prev = snap();
    const next = snap({
      snapshot_id: 'MS-2026-10-06-01',
      market_regime: {
        broad_index_state: 'UP',
        breadth_state: 'UNKNOWN',
        liquidity_state: 'UNKNOWN',
        risk_appetite_state: 'UNKNOWN',
      },
    });
    const h = html(view({ snapshot: next, previous: prev, diff: diffSnapshots(prev, next) }));
    expect(h).toContain('处变化');
    expect(h).toContain('市场环境');
    expect(h).toContain('宽基方向');
    expect(h).toContain('上行');
  });

  it('第一份快照时说明「没有可比对象」', () => {
    const h = html(view({ previous: null, diff: null }));
    expect(h).toContain('第一份');
  });
});

describe('CurrentSnapshotBody · 「无对应」是一等公民', () => {
  it('★ 展示「无有效对应」计数与说明，并点明它不是缺陷', () => {
    const h = html(view());
    expect(h).toContain('无有效对应');
    expect(h).toContain('不是缺陷');
    expect(h).toContain('结构不成立');
    // 计数：3 条比对里 1 条部分对应 / 2 条无有效对应
    expect(h).toContain('共 3 条比对');
    expect(h).toContain('有结构对应');
    expect(h).toContain('<strong>1</strong>');
    expect(h).toContain('<strong>2</strong>');
  });

  it('UNKNOWN 维度被说明为「诚实空态」，而非待办', () => {
    const h = html(view());
    expect(h).toContain('诚实空态');
    expect(h).toContain('不猜测');
    expect(h).toContain('4 个维度为「未知」');
  });
});

describe('CurrentSnapshotBody · ★ P0 接通：候选明细可见', () => {
  const withDetails = () =>
    view({
      detailsByObject: [
        {
          objectId: 'CC-A',
          resolved: true,
          profile: {
            currentPhase: 'THEME_FORMING',
            mechanismDrivers: ['POLICY_DRIVEN', 'TECH_BREAKTHROUGH'],
            evidenceCategories: ['POLICY', 'INDUSTRY'],
            structuralGaps: ['candidate_side_2026_market_state_not_available'],
          },
          details: [
            {
              historicalCycleId: 'C-2023-AD',
              historicalObjectKind: 'campaign',
              status: 'STRUCTURAL_SUPPORTED',
              statusLabel: '结构支持',
              themeRelation: 'CROSS_MACRO_THEME',
              themeRelationLabel: '跨大主题',
              dimensions: [
                { key: 'lifecycle', label: '生命周期阶段', status: 'MATCH', statusLabel: '对应' },
                { key: 'mechanism_driver', label: '驱动机制', status: 'MATCH', statusLabel: '对应' },
              ],
              whySimilar: ['生命周期阶段对应（MATCH）', '驱动机制存在交集'],
              whyNotSimilar: ['受历史驱动证据粒度限制'],
            },
            {
              historicalCycleId: 'C-2019-PHARMA-INNOV',
              historicalObjectKind: 'campaign',
              status: 'NO_VALID_CORRESPONDENCE',
              statusLabel: '无有效对应',
              themeRelation: 'SAME_MACRO_THEME',
              themeRelationLabel: '同大主题',
              dimensions: [{ key: 'mechanism_driver', label: '驱动机制', status: 'MISMATCH', statusLabel: '不对应' }],
              whySimilar: [],
              whyNotSimilar: ['机制轴无交集'],
            },
          ],
        },
      ],
    });

  it('★ 计数之外，真的能看见「是哪几条历史对象、为什么」', () => {
    const h = html(withDetails());
    expect(h).toContain('C-2023-AD');
    expect(h).toContain('结构支持');
    expect(h).toContain('跨大主题');
    expect(h).toContain('为什么对应');
    expect(h).toContain('生命周期阶段对应（MATCH）');
    expect(h).toContain('哪里不同');
  });

  it('「无有效对应」同样可查（不是被隐藏）', () => {
    const h = html(withDetails());
    expect(h).toContain('C-2019-PHARMA-INNOV');
    expect(h).toContain('无有效对应');
    expect(h).toContain('机制轴无交集');
  });

  it('★ 历史对象可点击（接通 → 打开该历史案例）', () => {
    const h = renderToStaticMarkup(
      <CurrentSnapshotBody view={withDetails()} onOpenHistoricalCase={() => {}} />,
    );
    expect(h).toContain('<button');
    expect(h).toContain('打开该历史案例');
    // 未传回调时**不渲染按钮**（不给用户假出口）
    const noCb = html(withDetails());
    expect(noCb).not.toContain('打开该历史案例');
  });

  it('★ 展示「还缺什么」（structuralGaps）—— 继续研究的线索', () => {
    const h = html(withDetails());
    expect(h).toContain('当前驱动机制');
    expect(h).toContain('POLICY_DRIVEN');
    expect(h).toContain('当前证据类别');
    expect(h).toContain('还缺什么');
    expect(h).toContain('candidate_side_2026_market_state_not_available');
    expect(h).toContain('机制轴 ≠ 证据类别');
  });

  it('★ 研究对象可点击（接通 → 跳到它的结构对应详情）', () => {
    const h = renderToStaticMarkup(
      <CurrentSnapshotBody view={withDetails()} onOpenObject={() => {}} />,
    );
    expect(h).toContain('跳到该对象的结构对应详情');
    expect(h).toContain('<button');
    // 未传回调时**不渲染按钮**（不给用户假出口）
    expect(html(withDetails())).not.toContain('跳到该对象的结构对应详情');
  });

  it('★ 未解析时明确说「未解析」，且不等于「没有对应」', () => {
    const h = html(
      view({ detailsByObject: [{ objectId: 'CC-A', resolved: false, details: [], profile: null }] }),
    );
    expect(h).toContain('未解析');
    expect(h).toContain('不等于');
  });
});

describe('CurrentSnapshotBody · 语义红线', () => {
  it('★ 页面不含预测 / 建议 / 评分 / 排名类措辞', () => {
    const banned = [
      '建议买入', '建议卖出', '目标价', '大概率', '胜率', '推荐股票',
      '相似度分数', '得分', 'ranking', 'probability', 'prediction', 'score',
    ];
    for (const v of [view(), view({ preview: true }), view({ state: 'no-canonical', snapshot: null })]) {
      const h = html(v);
      for (const b of banned) expect(h, `不得出现: ${b}`).not.toContain(b);
    }
  });

  it('★ 明确声明「不是预测 / 不是买卖建议 / 不是买入机会」', () => {
    const h = html(view());
    expect(h).toContain('不是预测');
    expect(h).toContain('不是买卖建议');
    expect(h).toContain('不是买入机会');
  });
});
