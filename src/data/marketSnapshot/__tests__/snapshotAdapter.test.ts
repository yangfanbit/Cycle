import { describe, it, expect } from 'vitest';
import { CANONICAL, loadCurrentSnapshot, snapshotIndex } from '../snapshotAdapter';

/**
 * 适配器测试 —— 重点是**门禁**：
 * 默认只展示 CANONICAL；全部未签发时必须给出明确空态，而不是空白或悄悄放行。
 */

describe('snapshotAdapter · 索引与门禁', () => {
  it('索引能读到快照，且按日期升序', () => {
    const idx = snapshotIndex();
    expect(idx.length).toBeGreaterThanOrEqual(2);
    const dates = idx.map((e) => e.snapshot_date);
    expect([...dates].sort()).toEqual(dates);
    for (const e of idx) {
      expect(e.snapshot_id).toMatch(/^MS-/);
      expect(e.file).toMatch(/\.json$/);
    }
  });

  it('★ 默认门禁：全部快照未签发时，state = no-canonical（不得放行）', async () => {
    const idx = snapshotIndex();
    const hasCanonical = idx.some((e) => e.status === CANONICAL);
    const v = await loadCurrentSnapshot(false);
    if (!hasCanonical) {
      expect(v.state).toBe('no-canonical');
      expect(v.snapshot).toBeNull();
      expect(v.diff).toBeNull();
      expect(v.draftCount).toBe(idx.length);
      expect(v.latestDate).toBe(idx[idx.length - 1].snapshot_date);
    } else {
      expect(v.state).toBe('ok');
      expect(v.snapshot?.status).toBe(CANONICAL);
    }
  });

  it('★ 预览模式：放宽门禁可拿到最新快照，但必须标记 preview', async () => {
    const idx = snapshotIndex();
    const v = await loadCurrentSnapshot(true);
    expect(v.state).toBe('ok');
    expect(v.snapshot).not.toBeNull();
    expect(v.snapshot?.snapshot_id).toBe(idx[idx.length - 1].snapshot_id);
    const hasCanonical = idx[idx.length - 1].status === CANONICAL;
    expect(v.preview).toBe(!hasCanonical);
  });

  it('预览模式：两份快照能算出 diff（有上一期才有 diff）', async () => {
    const v = await loadCurrentSnapshot(true);
    expect(v.previous).not.toBeNull();
    expect(v.diff).not.toBeNull();
    expect(v.diff?.from.snapshot_id).toBe(v.previous?.snapshot_id);
    expect(v.diff?.to.snapshot_id).toBe(v.snapshot?.snapshot_id);
    // 汇总自洽
    const d = v.diff!;
    expect(d.summary.total).toBe(
      d.summary.regime + d.summary.objects + d.summary.candidates + d.summary.observations,
    );
  });

  it('★ 只读：载入不修改快照内容', async () => {
    const a = await loadCurrentSnapshot(true);
    const b = await loadCurrentSnapshot(true);
    expect(JSON.stringify(a.snapshot)).toBe(JSON.stringify(b.snapshot));
  });
});
