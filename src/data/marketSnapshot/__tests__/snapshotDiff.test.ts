import { describe, it, expect } from 'vitest';
import { diffSnapshots } from '../snapshotDiff';
import type { MarketSnapshot } from '../types';

/**
 * 快照 diff 的不变量测试。
 *
 * 这些测试锁住两件事：
 *  1. **四层变化都要能被检出**（环境 / 对象 / 候选 / 观察），且「无变化」要能正确判定；
 *  2. **语义边界**：输出只含事实，不含任何判断（好坏 / 含义 / 排序 / 评分）。
 */

function makeSnapshot(over: Partial<MarketSnapshot> = {}): MarketSnapshot {
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
      },
    ],
    observations: [],
    historical_candidates: [
      {
        current_object_id: 'CC-A',
        identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-1' },
        structural_status: 'STRUCTURAL_PARTIAL',
        strict_structural_supported: false,
      },
    ],
  };
  return { ...base, ...over };
}

describe('snapshotDiff · 四层变化检出', () => {
  it('★ 同一份快照 → 无变化（unchanged = true，total = 0）', () => {
    const s = makeSnapshot();
    const d = diffSnapshots(s, makeSnapshot());
    expect(d.summary.unchanged).toBe(true);
    expect(d.summary.total).toBe(0);
    expect(d.regime).toEqual([]);
    expect(d.objects.added).toEqual([]);
    expect(d.candidates.statusChanged).toEqual([]);
  });

  it('环境层：regime 维度变化被检出', () => {
    const next = makeSnapshot({
      snapshot_id: 'MS-2026-10-06-01',
      market_regime: {
        broad_index_state: 'UP',
        breadth_state: 'UNKNOWN',
        liquidity_state: 'UNKNOWN',
        risk_appetite_state: 'UNKNOWN',
      },
    });
    const d = diffSnapshots(makeSnapshot(), next);
    expect(d.regime).toEqual([{ dimension: 'broad_index_state', from: 'UNKNOWN', to: 'UP' }]);
    expect(d.summary.regime).toBe(1);
    expect(d.summary.unchanged).toBe(false);
  });

  it('对象层：新增对象被检出', () => {
    const next = makeSnapshot({
      research_objects: [
        ...makeSnapshot().research_objects,
        {
          object_id: 'CC-B',
          object_kind: 'current_candidate',
          display_name: '对象 B',
          declared_phase: 'EARLY_SIGNAL',
          resolution_state: 'RESOLVED',
        },
      ],
    });
    const d = diffSnapshots(makeSnapshot(), next);
    expect(d.objects.added.map((o) => o.object_id)).toEqual(['CC-B']);
    expect(d.objects.removed).toEqual([]);
  });

  it('对象层：移除对象被检出', () => {
    const prev = makeSnapshot({
      research_objects: [
        ...makeSnapshot().research_objects,
        {
          object_id: 'CC-B',
          object_kind: 'current_candidate',
          display_name: '对象 B',
          declared_phase: 'EARLY_SIGNAL',
          resolution_state: 'RESOLVED',
        },
      ],
    });
    const d = diffSnapshots(prev, makeSnapshot());
    expect(d.objects.removed.map((o) => o.object_id)).toEqual(['CC-B']);
  });

  it('对象层：阶段变化被检出（主题形成 → 广泛确认）', () => {
    const next = makeSnapshot({
      research_objects: [{ ...makeSnapshot().research_objects[0], declared_phase: 'BROAD_CONFIRMATION' }],
    });
    const d = diffSnapshots(makeSnapshot(), next);
    expect(d.objects.changed).toEqual([
      {
        object_id: 'CC-A',
        display_name: '对象 A',
        field: 'declared_phase',
        from: 'THEME_FORMING',
        to: 'BROAD_CONFIRMATION',
      },
    ]);
  });

  it('对象层：数组字段只比「集合」，顺序差异不算变化', () => {
    const next = makeSnapshot({
      research_objects: [
        {
          ...makeSnapshot().research_objects[0],
          canonical_drivers: ['TECH_BREAKTHROUGH', 'POLICY_DRIVEN'],
        },
      ],
    });
    const d = diffSnapshots(
      makeSnapshot({
        research_objects: [
          { ...makeSnapshot().research_objects[0], canonical_drivers: ['POLICY_DRIVEN', 'TECH_BREAKTHROUGH'] },
        ],
      }),
      next,
    );
    expect(d.objects.changed).toEqual([]);
  });

  it('候选层：新增 / 移除候选被检出', () => {
    const prev = makeSnapshot();
    const next = makeSnapshot({
      historical_candidates: [
        ...makeSnapshot().historical_candidates,
        {
          current_object_id: 'CC-A',
          identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-2' },
          structural_status: 'STRUCTURAL_SUPPORTED',
        },
      ],
    });
    const added = diffSnapshots(prev, next);
    expect(added.candidates.added.map((c) => c.historical_cycle_id)).toEqual(['C-2']);
    const removed = diffSnapshots(next, prev);
    expect(removed.candidates.removed.map((c) => c.historical_cycle_id)).toEqual(['C-2']);
  });

  it('候选层：同一 (对象 × 历史对象) 的结构状态变化被检出', () => {
    const next = makeSnapshot({
      historical_candidates: [
        {
          current_object_id: 'CC-A',
          identity: { historical_object_kind: 'campaign', historical_cycle_id: 'C-1' },
          structural_status: 'STRUCTURAL_SUPPORTED',
        },
      ],
    });
    const d = diffSnapshots(makeSnapshot(), next);
    expect(d.candidates.statusChanged).toEqual([
      {
        current_object_id: 'CC-A',
        historical_cycle_id: 'C-1',
        from: 'STRUCTURAL_PARTIAL',
        to: 'STRUCTURAL_SUPPORTED',
      },
    ]);
    expect(d.candidates.added).toEqual([]);
    expect(d.candidates.removed).toEqual([]);
  });

  it('观察层：新增 / 移除观察被检出', () => {
    const obs = {
      observation_id: 'OBS-1',
      observation_type: 'POLICY',
      date: '2026-09-14',
      claim: '某部委发布标准',
    };
    const withObs = makeSnapshot({ observations: [obs] });
    const d = diffSnapshots(makeSnapshot(), withObs);
    expect(d.observations.added.map((o) => o.observation_id)).toEqual(['OBS-1']);
    expect(diffSnapshots(withObs, makeSnapshot()).observations.removed.map((o) => o.observation_id)).toEqual([
      'OBS-1',
    ]);
  });
});

describe('snapshotDiff · 语义边界与确定性', () => {
  it('★ 输出只含事实字段，不含任何判断性字段', () => {
    const next = makeSnapshot({
      snapshot_id: 'MS-2026-10-06-01',
      market_regime: {
        broad_index_state: 'UP',
        breadth_state: 'NORMAL',
        liquidity_state: 'STABLE',
        risk_appetite_state: 'NEUTRAL',
      },
    });
    const d = diffSnapshots(makeSnapshot(), next);
    const keys = JSON.stringify(d).toLowerCase();
    for (const banned of ['score', 'ranking', 'probability', 'prediction', 'signal', 'bullish', 'bearish', 'impact', 'implication']) {
      expect(keys, `不得出现判断性字段: ${banned}`).not.toContain(banned);
    }
  });

  it('★ 确定性：同一对输入调用两次，结果完全一致', () => {
    const a = makeSnapshot();
    const b = makeSnapshot({ snapshot_id: 'MS-2026-10-06-01', snapshot_date: '2026-10-06' });
    expect(JSON.stringify(diffSnapshots(a, b))).toBe(JSON.stringify(diffSnapshots(a, b)));
  });

  it('★ 纯函数：不修改入参', () => {
    const a = makeSnapshot();
    const b = makeSnapshot({ snapshot_id: 'MS-2026-10-06-01' });
    const beforeA = JSON.stringify(a);
    const beforeB = JSON.stringify(b);
    diffSnapshots(a, b);
    expect(JSON.stringify(a)).toBe(beforeA);
    expect(JSON.stringify(b)).toBe(beforeB);
  });

  it('汇总计数 = 四层之和；total 与 unchanged 自洽', () => {
    const next = makeSnapshot({
      snapshot_id: 'MS-2026-10-06-01',
      market_regime: {
        broad_index_state: 'UP',
        breadth_state: 'UNKNOWN',
        liquidity_state: 'UNKNOWN',
        risk_appetite_state: 'UNKNOWN',
      },
      observations: [
        { observation_id: 'OBS-1', observation_type: 'POLICY', date: '2026-09-14', claim: 'x' },
      ],
    });
    const d = diffSnapshots(makeSnapshot(), next);
    const sum = d.summary.regime + d.summary.objects + d.summary.candidates + d.summary.observations;
    expect(d.summary.total).toBe(sum);
    expect(d.summary.unchanged).toBe(d.summary.total === 0);
  });
});
