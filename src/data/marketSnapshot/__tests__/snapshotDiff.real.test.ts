import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { diffSnapshots } from '../snapshotDiff';
import type { MarketSnapshot } from '../types';

/**
 * 集成检查：在**真实仓库快照**上跑 diff。
 *
 * 为什么要有这个测试：单元测试用的是合成数据，**证明不了它能在真实产物上跑通**。
 * 1.2d 的验收标准就是「用真实的两份快照跑出 diff」。
 *
 * 设计上容错：真实快照少于 2 份时**跳过**（不误报失败）——
 * 它检查的是「能跑通且自洽」，不是「必须存在某两份特定快照」。
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

describe('snapshotDiff · 真实快照集成检查', () => {
  const snaps = loadSnapshots();

  it('仓库中存在可用的 Market Snapshot（契约 v0.3）', () => {
    expect(snaps.length).toBeGreaterThanOrEqual(1);
    for (const s of snaps) {
      expect(s.contract).toBe('market_snapshot');
      expect(s.market_snapshot_version).toBe('0.3');
    }
  });

  it('★ 两份真实快照能跑出 diff，且汇总自洽', () => {
    if (snaps.length < 2) {
      console.warn('[skip] 真实快照少于 2 份，无法做跨快照 diff');
      return;
    }
    const prev = snaps[snaps.length - 2];
    const next = snaps[snaps.length - 1];
    const d = diffSnapshots(prev, next);

    const sum = d.summary.regime + d.summary.objects + d.summary.candidates + d.summary.observations;
    expect(d.summary.total).toBe(sum);
    expect(d.summary.unchanged).toBe(sum === 0);

    // 候选必须能按「当前对象」聚合 —— 这正是 v0.3 修复要保证的能力
    const perObject = new Map<string, number>();
    for (const c of next.historical_candidates) {
      perObject.set(c.current_object_id, (perObject.get(c.current_object_id) ?? 0) + 1);
    }
    expect(perObject.size).toBe(next.research_objects.length);

    console.log(
      `\n[真实 diff] ${prev.snapshot_id} → ${next.snapshot_id}\n` +
        `  环境 ${d.summary.regime} · 对象 ${d.summary.objects} · 候选 ${d.summary.candidates} · 观察 ${d.summary.observations}\n` +
        `  合计 ${d.summary.total} 处变化 · unchanged=${d.summary.unchanged}\n` +
        `  候选可按对象聚合: ${[...perObject.entries()].map(([k, v]) => `${k}=${v}`).join(' · ')}`,
    );
  });
});
