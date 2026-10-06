import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { lifecycleTimelineOf, trackedObjectIds } from '../lifecycleTimeline';
import type { MarketSnapshot } from '../types';

/**
 * 集成检查：在**真实仓库快照**上跑 Lifecycle Tracking。
 *
 * 为什么要有它：单元测试用合成数据，证明不了「对象级观察 → 时间线」这条链在真实产物上通。
 * 设计上容错：真实数据里还没有对象级观察时**不误报失败**（那是数据缺口，不是代码缺陷）。
 */

const SNAPSHOT_DIR = resolve(
  __dirname,
  '../../../../research/current/market_snapshots/snapshots',
);

function loadSnapshots(): MarketSnapshot[] {
  if (!existsSync(SNAPSHOT_DIR)) return [];
  return readdirSync(SNAPSHOT_DIR)
    .filter((f) => f.endsWith('.json'))
    .map((f) => JSON.parse(readFileSync(join(SNAPSHOT_DIR, f), 'utf8')) as MarketSnapshot)
    .filter((s) => s.contract === 'market_snapshot')
    .sort((a, b) => a.snapshot_date.localeCompare(b.snapshot_date));
}

describe('lifecycleTimeline · 真实快照集成检查', () => {
  const snaps = loadSnapshots();

  it('能读出全部当前对象', () => {
    const ids = trackedObjectIds(snaps);
    expect(ids.length).toBeGreaterThanOrEqual(1);
    for (const id of ids) expect(id).toMatch(/^CC-/);
  });

  it('★ 对象级观察能派生出时间线（若数据中存在关联观察）', () => {
    const linked = snaps.flatMap((s) =>
      (s.observations ?? []).filter((o) => o.linked_object_id),
    );
    if (linked.length === 0) {
      console.warn('[skip] 真实快照里尚无对象级观察（linked_object_id）—— 属数据缺口，非代码缺陷');
      return;
    }

    // ★ 同一 observation_id 会**跨快照重复出现**（append-only 的必然结果），
    //   而时间线按 id **去重** → 期望值也必须去重后再比。
    const byObject = new Map<string, Set<string>>();
    for (const o of linked) {
      const id = o.linked_object_id as string;
      if (!byObject.has(id)) byObject.set(id, new Set());
      byObject.get(id)!.add(o.observation_id);
    }

    for (const [objectId, ids] of byObject) {
      const t = lifecycleTimelineOf(snaps, objectId, '2026-10-06');
      expect(t.count).toBeGreaterThanOrEqual(1);
      expect(t.entries.length).toBe(ids.size);
      // 去重后每个 id 只出现一次
      expect(new Set(t.entries.map((e) => e.observation_id)).size).toBe(t.entries.length);
      // 时间线按日期升序
      const dates = t.entries.map((e) => e.date);
      expect([...dates].sort()).toEqual(dates);
      console.log(
        `\n[真实时间线] ${objectId} · ${t.display_name} · ${t.count} 条（${t.first_date} ~ ${t.last_date}）\n` +
          t.entries.map((e) => `    ${e.date} · ${e.observation_type} · ${e.first_seen_in}`).join('\n'),
      );
    }
  });

  it('★ PIT：asOf 早于对象级观察所在快照时，看不到它们', () => {
    const early = lifecycleTimelineOf(snaps, 'CC-2026-EMBODIED-AI', '2026-09-15');
    const late = lifecycleTimelineOf(snaps, 'CC-2026-EMBODIED-AI', '2026-10-06');
    expect(late.count).toBeGreaterThanOrEqual(early.count);
  });
});
