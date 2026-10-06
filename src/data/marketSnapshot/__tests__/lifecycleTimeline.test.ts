import { describe, it, expect } from 'vitest';
import {
  findRewrittenObservations,
  lifecycleTimelineOf,
  lifecycleTimelinesOf,
  trackedObjectIds,
} from '../lifecycleTimeline';
import type { MarketSnapshot, SnapshotObservation } from '../types';

/**
 * Lifecycle Tracking 的不变量测试。
 *
 * 三条设计承诺必须被锁住：
 *  1. **PIT 安全**：`asOf` 之前的快照才可见 —— 不得用后一期信息解释前一期；
 *  2. **append-only**：同一 observation_id 只取最早登记的那一期，后续期不得覆盖；
 *  3. **只陈述事实**：时间线条目里不得出现阶段判断 / 评分 / 预测字段。
 */

function obs(over: Partial<SnapshotObservation>): SnapshotObservation {
  return {
    observation_id: 'OBS-1',
    observation_type: 'POLICY',
    date: '2026-09-14',
    claim: '某部委发布标准',
    evidence_strength: 'STRONG',
    direction: 'SUPPORTIVE',
    ...over,
  };
}

function snap(over: Partial<MarketSnapshot>): MarketSnapshot {
  return {
    contract: 'market_snapshot',
    market_snapshot_version: '0.3',
    snapshot_id: 'MS-1',
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
        declared_phase: 'THEME_FORMING',
        resolution_state: 'RESOLVED',
      },
    ],
    observations: [],
    historical_candidates: [],
    ...over,
  };
}

const S1 = snap({
  snapshot_id: 'MS-1',
  snapshot_date: '2026-09-15',
  observations: [
    obs({ observation_id: 'OBS-A1', date: '2026-09-01', claim: 'A 的第一条', linked_object_id: 'CC-A' }),
    obs({ observation_id: 'OBS-MKT', date: '2026-09-02', claim: '市场级观察', linked_object_id: null }),
  ],
});

const S2 = snap({
  snapshot_id: 'MS-2',
  snapshot_date: '2026-10-06',
  observations: [
    obs({ observation_id: 'OBS-A1', date: '2026-09-01', claim: 'A 的第一条', linked_object_id: 'CC-A' }),
    obs({ observation_id: 'OBS-A2', date: '2026-09-28', claim: 'A 的第二条', linked_object_id: 'CC-A' }),
    obs({ observation_id: 'OBS-MKT', date: '2026-09-02', claim: '市场级观察', linked_object_id: null }),
  ],
});

describe('lifecycleTimeline · 派生与分组', () => {
  it('只收该对象的观察，市场级（无 linked_object_id）不计入', () => {
    const t = lifecycleTimelineOf([S1, S2], 'CC-A');
    expect(t.entries.map((e) => e.observation_id)).toEqual(['OBS-A1', 'OBS-A2']);
    expect(t.count).toBe(2);
    expect(t.display_name).toBe('对象 A');
  });

  it('按日期升序，且给出首末日期', () => {
    const t = lifecycleTimelineOf([S2, S1], 'CC-A'); // 乱序输入也要正确
    expect(t.entries.map((e) => e.date)).toEqual(['2026-09-01', '2026-09-28']);
    expect(t.first_date).toBe('2026-09-01');
    expect(t.last_date).toBe('2026-09-28');
  });

  it('无观察的对象返回空时间线（不报错）', () => {
    const t = lifecycleTimelineOf([S1, S2], 'CC-NOPE');
    expect(t.count).toBe(0);
    expect(t.first_date).toBeNull();
    expect(t.last_date).toBeNull();
  });

  it('trackedObjectIds 汇总出现过的对象；lifecycleTimelinesOf 一次派生全部', () => {
    expect(trackedObjectIds([S1, S2])).toEqual(['CC-A']);
    const all = lifecycleTimelinesOf([S1, S2]);
    expect(all).toHaveLength(1);
    expect(all[0].object_id).toBe('CC-A');
  });
});

describe('lifecycleTimeline · ★ PIT 安全（禁 look-ahead）', () => {
  it('asOf = 09-15 时，看不到 10 月那期才登记的第二条观察', () => {
    const early = lifecycleTimelineOf([S1, S2], 'CC-A', '2026-09-15');
    expect(early.entries.map((e) => e.observation_id)).toEqual(['OBS-A1']);
    expect(early.last_date).toBe('2026-09-01');
  });

  it('asOf = 10-06 时才看得到两条（时间线只增不减）', () => {
    const late = lifecycleTimelineOf([S1, S2], 'CC-A', '2026-10-06');
    expect(late.entries.map((e) => e.observation_id)).toEqual(['OBS-A1', 'OBS-A2']);
  });

  it('★ 时间线随 asOf 单调增长（append-only 的直接推论）', () => {
    const a = lifecycleTimelineOf([S1, S2], 'CC-A', '2026-09-15').count;
    const b = lifecycleTimelineOf([S1, S2], 'CC-A', '2026-10-06').count;
    expect(b).toBeGreaterThanOrEqual(a);
  });

  it('trackedObjectIds / lifecycleTimelinesOf 同样遵守 asOf', () => {
    expect(trackedObjectIds([S1, S2], '2026-09-15')).toEqual(['CC-A']);
    expect(lifecycleTimelinesOf([S1, S2], '2026-09-15')[0].count).toBe(1);
  });
});

describe('lifecycleTimeline · ★ append-only', () => {
  it('同一 observation_id 只取**最早**登记的那一期（后续期不得覆盖）', () => {
    const t = lifecycleTimelineOf([S1, S2], 'CC-A');
    const a1 = t.entries.find((e) => e.observation_id === 'OBS-A1');
    expect(a1?.first_seen_in).toBe('MS-1');
    const a2 = t.entries.find((e) => e.observation_id === 'OBS-A2');
    expect(a2?.first_seen_in).toBe('MS-2');
  });

  it('findRewrittenObservations：内容一致 → 无异常', () => {
    expect(findRewrittenObservations([S1, S2])).toEqual([]);
  });

  it('findRewrittenObservations：同一 id 的 claim 被改写 → 被抓出', () => {
    const bad = snap({
      snapshot_id: 'MS-3',
      snapshot_date: '2026-11-06',
      observations: [obs({ observation_id: 'OBS-A1', date: '2026-09-01', claim: '被改写过的叙述', linked_object_id: 'CC-A' })],
    });
    const found = findRewrittenObservations([S1, S2, bad]);
    expect(found).toHaveLength(1);
    expect(found[0].observation_id).toBe('OBS-A1');
    expect(found[0].fields).toContain('claim');
  });
});

describe('lifecycleTimeline · 语义红线', () => {
  it('★ 条目只含事实字段，不含阶段判断 / 评分 / 预测', () => {
    const t = lifecycleTimelineOf([S1, S2], 'CC-A');
    const keys = JSON.stringify(t).toLowerCase();
    for (const banned of ['score', 'ranking', 'probability', 'prediction', 'phase', 'signal']) {
      expect(keys, `不得出现: ${banned}`).not.toContain(banned);
    }
  });
});
